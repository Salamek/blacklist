#!/bin/bash
celery worker -A celery_worker.celery --loglevel=INFO
