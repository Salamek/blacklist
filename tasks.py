# -*- encoding: utf-8 -*-
from task import create_celery
from application import create_application
celery = create_celery(create_application())


@celery.task(name="tasks.simple_task")
def simple_task(argument):
    print(argument)
    return argument

@celery.task(name="tasks.generate_thumbnail")
def generate_thumbnail(blacklist_id):
    print(blacklist_id)