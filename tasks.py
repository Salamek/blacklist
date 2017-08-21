# -*- encoding: utf-8 -*-
from task import create_celery

try:
    from PIL import Image
except ImportError:
    import Image

from application import create_application
from database import Blacklist, ApiLog, BlockingLog, Pdf, db
from sqlalchemy import or_
import subprocess
import hashlib
import os
import tabula
import csv
import datetime
import PyPDF2
from tools.Validators import Validators

try:
    from urllib2 import urlopen, HTTPError
except ImportError:
    from urllib.request import urlopen, HTTPError


app = create_application()
celery = create_celery(app)


@celery.task(name="tasks.log_block")
def log_block(blacklist_id, remote_addr, tests, success):
    blocking_log = BlockingLog()
    blocking_log.blacklist_id = blacklist_id
    blocking_log.remote_addr = remote_addr
    blocking_log.tests = tests
    blocking_log.success = success
    db.session.add(blocking_log)
    db.session.commit()


@celery.task(name="tasks.log_api")
def log_api(remote_addr):
    found = ApiLog.query.filter_by(remote_addr=remote_addr).first()
    if not found:
        found = ApiLog()
        found.remote_addr = remote_addr
        found.requests = 1
    else:
        found.requests = found.requests + 1

    db.session.add(found)
    db.session.commit()


@celery.task(name="tasks.crawl_blacklist")
def crawl_blacklist():
    date_format = "%d.%m.%Y"

    # Find next PDF version
    version_try_max = 5
    max_version_found = 0

    last_version_found = Pdf.query.order_by(Pdf.version.desc()).first()
    if last_version_found:
        last_version = last_version_found.version
    else:
        last_version = 1

    for check_version in range(last_version, last_version + version_try_max):
        try:
            urlopen(app.config['BLACKLIST_SOURCE'].format(version=check_version))
            max_version_found = max(check_version, max_version_found)
        except HTTPError:
            pass

    response = urlopen(app.config['BLACKLIST_SOURCE'].format(version=max_version_found))
    pdf_content = response.read()

    pdf_sum = hashlib.sha256(pdf_content).hexdigest()

    # We dont have this PDF yet, parse it
    pdf = Pdf.query.filter_by(sum=pdf_sum).first()
    if pdf:
        print('This PDF is already crawled ID:{}'.format(pdf.id))
        pdf.updated = datetime.datetime.now()
    else:
        # Store PDF
        file_path = os.path.join(app.config['PDF_STORAGE'], '{}.pdf'.format(pdf_sum))
        with open(file_path, 'wb') as f:
            f.write(pdf_content)

        pdf_toread = PyPDF2.PdfFileReader(open(file_path, "rb"))
        pdf_info = pdf_toread.getDocumentInfo()

        csv_parsed = tabula.read_pdf(file_path, spreadsheet=True).to_csv(encoding="utf-8")

        pdf = Pdf()
        pdf.sum = pdf_sum
        pdf.name = os.path.basename(response.geturl())
        pdf.signed = False  # !FIXME Check signature
        pdf.ssl = response.geturl().startswith('https')  # We dont need better check,  urlopen checks SSL cert validity
        pdf.parsed = csv_parsed
        pdf.size = os.path.getsize(file_path)
        pdf.title = pdf_info.title if pdf_info.title else pdf_info.subject
        pdf.author = pdf_info.author
        pdf.creator = pdf_info.creator
        pdf.format = '?'  # FIXME
        pdf.pages = pdf_toread.getNumPages()
        pdf.version = max_version_found

        csv_data = csv.reader(csv_parsed.splitlines(), delimiter=',')
        for row in csv_data:
            # table item have 7 cols
            if len(row) != 7:
                continue

            dns = row[1].strip()  # Required
            if not Validators.is_valid_hostname(dns):
                continue

            dns_date_published = datetime.datetime.strptime(row[2].strip(), date_format) if row[2].strip() else None
            dns_date_removed = datetime.datetime.strptime(row[3].strip(), date_format) if row[3].strip() else None
            bank_account = row[4].strip()
            bank_account_date_published = datetime.datetime.strptime(row[5].strip(), date_format) if row[
                5].strip() else None
            bank_account_date_removed = datetime.datetime.strptime(row[6].strip(), date_format) if row[
                6].strip() else None

            blacklist = Blacklist.query.filter_by(dns=dns).first()
            if not blacklist:
                blacklist = Blacklist()
                blacklist.dns = dns
                blacklist.last_crawl = None
            blacklist.bank_account = bank_account
            blacklist.dns_date_published = dns_date_published
            blacklist.dns_date_removed = dns_date_removed
            blacklist.bank_account_date_published = bank_account_date_published
            blacklist.bank_account_date_removed = bank_account_date_removed

            pdf.blacklist.append(blacklist)

            db.session.add(blacklist)

    db.session.add(pdf)
    db.session.commit()

    # trigger crawl_dns_info
    celery.send_task('tasks.crawl_dns_info', args=(False,))


@celery.task(name="tasks.crawl_dns_info")
def crawl_dns_info(only_new=False):
    from_date = datetime.datetime.today() - datetime.timedelta(days=7)

    if only_new:
        blacklist_details = Blacklist.query.filter_by(last_crawl=None)
    else:
        blacklist_details = Blacklist.query.filter(or_(Blacklist.last_crawl < from_date, Blacklist.last_crawl == None))

    for blacklist_detail in blacklist_details:
        try:
            file_path = os.path.join(app.config['THUMBNAIL_FOLDER'], '{}.png'.format(blacklist_detail.id))
            thumbnail_file_path = os.path.join(app.config['THUMBNAIL_FOLDER'], 'thumbnail_{}.png'.format(blacklist_detail.id))
            subprocess.call(["xvfb-run", "--", "wkhtmltoimage", '--width', '1280', blacklist_detail.dns, file_path])

            size = (100, 200)
            image = Image.open(file_path)
            image.thumbnail(size, Image.ANTIALIAS)
            background = Image.new('RGBA', size, (255, 255, 255, 0))
            background.paste(
                image, (int((size[0] - image.size[0]) // 2), int((size[1] - image.size[1]) // 2))
            )
            background.save(thumbnail_file_path)

            blacklist_detail.thumbnail = True
        except Exception as e:
            print('Failed to obtain DNS thumbnail: {}'.format(e))
            blacklist_detail.thumbnail = False

        blacklist_detail.last_crawl = datetime.datetime.now()
        db.session.add(blacklist_detail)
    db.session.commit()
