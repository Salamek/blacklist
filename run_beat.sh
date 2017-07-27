#!/bin/bash
celery beat -A celery_worker.celery --loglevel=INFO
