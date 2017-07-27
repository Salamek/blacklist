# -*- encoding: utf-8 -*-
from task import create_celery
from application import create_application
from database import Blacklist, ApiLog, BlockingLog, db
import subprocess
import os

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


@celery.task(name="tasks.generate_thumbnail")
def generate_thumbnail(blacklist_id):
    blacklist_detail = Blacklist.query.filter_by(id=blacklist_id).first()
    file_path = os.path.join(app.config['THUMBNAIL_FOLDER'], 'thumbnail_{}.png'.format(blacklist_detail.id))
    subprocess.Popen(["xvfb-run", "--", "wkhtmltoimage", '--width', '1280', blacklist_detail.dns, file_path])
    blacklist_detail.thumbnail = True
    db.session.add(blacklist_detail)
    db.session.commit()
