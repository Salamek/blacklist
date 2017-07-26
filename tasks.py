# -*- encoding: utf-8 -*-
from task import create_celery
from application import create_application
from database import Blacklist, db
import subprocess
import os

app = create_application()
celery = create_celery(app)


@celery.task(name="tasks.simple_task")
def simple_task(argument):
    print(argument)
    return argument

@celery.task(name="tasks.generate_thumbnail")
def generate_thumbnail(blacklist_id):
    blacklist_detail = Blacklist.query.filter_by(id=blacklist_id).first()
    file_path = os.path.join(app.config['THUMBNAIL_FOLDER'], 'thumbnail_{}.png'.format(blacklist_detail.id))
    subprocess.Popen(["wkhtmltoimage", '--width', '1280', blacklist_detail.dns, file_path])
    blacklist_detail.thumbnail = True
    db.session.add(blacklist_detail)
    db.session.commit()
