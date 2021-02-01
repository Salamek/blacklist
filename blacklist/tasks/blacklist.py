import subprocess
import os
import flask
import hashlib
import datetime
import tabula
import csv
import PyPDF2
import requests
import dns.resolver
from flask_celery import single_instance
from sqlalchemy import or_
from logging import getLogger
from blacklist.extensions import celery, db
from blacklist.tools.helpers import fix_url, parse_czech_date
from blacklist.models.blacklist import BlockingLog, ApiLog, Pdf, Blacklist
from blacklist.tools.Validators import Validators

try:
    from PIL import Image
except ImportError:
    import Image

LOG = getLogger(__name__)


@celery.task(bind=True)
def log_block(task_id: str, blacklist_id: int, remote_addr: str, tests: int, success: int) -> None:
    blocking_log = BlockingLog()
    blocking_log.blacklist_id = blacklist_id
    blocking_log.remote_addr = remote_addr
    blocking_log.tests = tests
    blocking_log.success = success
    db.session.add(blocking_log)
    db.session.commit()


@celery.task(bind=True)
def log_api(task_id: str, remote_addr: str) -> None:
    found = ApiLog.query.filter_by(remote_addr=remote_addr, date=datetime.datetime.now().date()).first()
    if not found:
        found = ApiLog()
        found.remote_addr = remote_addr
        found.date = datetime.datetime.now()
        found.requests = 1
    else:
        found.requests = found.requests + 1

    db.session.add(found)
    db.session.commit()


@celery.task(bind=True)
@single_instance
def crawl_blacklist(task_id: str=None) -> None:

    # Find next PDF version
    max_version_found = None

    last_version_found = Pdf.query.order_by(Pdf.version.desc()).first()
    if last_version_found:
        last_version = last_version_found.version
    else:
        last_version = 1

    LOG.info('Version max: {}'.format(flask.current_app.config['BLACKLIST_VERSION_TRY_MAX']))

    for check_version in range(last_version, last_version + flask.current_app.config['BLACKLIST_VERSION_TRY_MAX']):
        try:
            LOG.info('Trying version {}'.format(check_version))
            test_url = flask.current_app.config['BLACKLIST_SOURCE'].format(version=check_version)
            r = requests.head(test_url, timeout=60)
            r.raise_for_status()
            max_version_found = max(check_version, max_version_found) if max_version_found else check_version
        except requests.HTTPError:
            # If ve found max version and get error after it, it means that we are overshooting, no need to continue
            if max_version_found:
                LOG.info(
                    'Error thrown for version {0} and version {1} was previously found -> using version {1}'.format(
                        check_version,
                        max_version_found
                    )
                )
                break

    if max_version_found is None:
        raise Exception('No suitable version of PDF found to download, maybe you will need to raise BLACKLIST_VERSION_TRY_MAX in config')

    latest_version_url = flask.current_app.config['BLACKLIST_SOURCE'].format(version=max_version_found)
    LOG.info('Found PDF {}'.format(latest_version_url))
    response = requests.get(latest_version_url)
    pdf_content = response.content

    pdf_sum = hashlib.sha256(pdf_content).hexdigest()

    # We dont have this PDF yet, parse it
    pdf = Pdf.query.filter_by(sum=pdf_sum).first()
    if pdf:
        LOG.info('This PDF is already crawled ID:{}'.format(pdf.id))
        pdf.updated = datetime.datetime.now()
    else:
        # Store PDF
        file_path = os.path.join(flask.current_app.config['PDF_STORAGE_FOLDER'], '{}.pdf'.format(pdf_sum))
        with open(file_path, 'wb') as f:
            f.write(pdf_content)

        pdf_toread = PyPDF2.PdfFileReader(open(file_path, "rb"))
        pdf_info = pdf_toread.getDocumentInfo()

        tabula_result = tabula.read_pdf(file_path, spreadsheet=True, pages='all')

        csv_parsed = tabula_result.to_csv(encoding="utf-8")

        pdf = Pdf()
        pdf.sum = pdf_sum
        pdf.name = os.path.basename(response.url)
        pdf.signed = False  # !FIXME Check signature
        pdf.ssl = response.url.startswith('https')  # We dont need better check,  urlopen checks SSL cert validity
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

            dns = row[1].strip().lower()  # Required
            if not Validators.is_valid_hostname(dns):
                continue

            dns_date_published = parse_czech_date(row[2].strip()) if row[2].strip() else None
            dns_date_removed = parse_czech_date(row[3].strip()) if row[3].strip() else None
            bank_account = row[4].strip()
            bank_account_date_published = parse_czech_date(row[5].strip()) if row[5].strip() else None
            bank_account_date_removed = parse_czech_date(row[6].strip()) if row[6].strip() else None

            blacklist = Blacklist.query.filter_by(dns=dns).first()
            if not blacklist:
                blacklist = Blacklist()
                blacklist.dns = dns
                blacklist.last_crawl = None
                blacklist.thumbnail = False
            blacklist.bank_account = bank_account if bank_account else None
            blacklist.dns_date_published = dns_date_published
            blacklist.dns_date_removed = dns_date_removed
            blacklist.bank_account_date_published = bank_account_date_published
            blacklist.bank_account_date_removed = bank_account_date_removed

            pdf.blacklist.append(blacklist)

            db.session.add(blacklist)

    db.session.add(pdf)
    db.session.commit()

    # trigger crawl_dns_info
    crawl_dns_info.delay(False)


@celery.task(bind=True)
def crawl_dns_info(task_id: str=None, only_new: bool=False) -> None:
    from_date = datetime.datetime.today() - datetime.timedelta(days=7)

    if only_new:
        blacklist_details = Blacklist.query.filter_by(last_crawl=None)
    else:
        blacklist_details = Blacklist.query.filter(or_(
            Blacklist.last_crawl < from_date,
            Blacklist.last_crawl == None,  # noqa: E711
            Blacklist.thumbnail == False
        ))

    for blacklist_detail in blacklist_details:
        try:
            thumbnail_folder = flask.current_app.config['THUMBNAIL_STORAGE_FOLDER']
            file_path = os.path.join(thumbnail_folder, '{}.png'.format(blacklist_detail.id))
            thumbnail_file_path = os.path.join(thumbnail_folder, 'thumbnail_{}.png'.format(blacklist_detail.id))
            LOG.debug('Saving screenshot to {}'.format(file_path))
            subprocess.call(["xvfb-run", "--auto-servernum", "--", "wkhtmltoimage", '--width', '1280', blacklist_detail.dns, file_path])

            LOG.debug('Saving thumbnail to {}'.format(thumbnail_file_path))
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
            LOG.warning('Failed to obtain DNS thumbnail: {}'.format(e))

        # Check redirect URL
        check_url = fix_url(blacklist_detail.dns)
        try:
            result = requests.get(check_url)
            blacklist_detail.redirects_to = result.url
        except Exception:
            blacklist_detail.redirects_to = None

        # Check A record
        try:
            answers = dns.resolver.query(blacklist_detail.dns, 'A')
            blacklist_detail.a = str(answers[0])
        except Exception:
            blacklist_detail.a = None

        # Check AAAA record
        try:
            answers = dns.resolver.query(blacklist_detail.dns, 'AAAA')
            blacklist_detail.aaaa = str(answers[0])
        except Exception:
            blacklist_detail.aaaa = None

        blacklist_detail.last_crawl = datetime.datetime.now()
        db.session.add(blacklist_detail)
        db.session.commit()
