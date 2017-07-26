# -*- encoding: utf-8 -*-
from task import create_celery
from application import create_application

celery = create_celery(create_application())