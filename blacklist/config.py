# -*- coding: utf-8 -*-

from celery.schedules import crontab


class HardCoded(object):
    """Constants used throughout the application.

    All hard coded settings/data that are not actual/official configuration options for Flask, Celery, or their
    extensions goes here.
    """
    ADMINS = ['adam.schubert@sg1-game.net']
    DB_MODELS_IMPORTS = ('blacklist',)  # Like CELERY_IMPORTS in CeleryConfig.
    ENVIRONMENT = property(lambda self: self.__class__.__name__)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPPORTED_LANGUAGES = {'cs': 'Čeština', 'en': 'English'}
    LANGUAGE = 'cs'

    BLACKLIST_SOURCE = 'https://www.mfcr.cz/assets/cs/media/Zverejnovane-udaje-ze-Seznamu-nepovolenych-internetovych-her_v{version}.pdf'
    BLACKLIST_VERSION_TRY_MAX = 200  # !FIXME Haha poor MF server...


class CeleryConfig(HardCoded):
    """Configurations used by Celery only."""
    CELERYD_PREFETCH_MULTIPLIER = 1
    CELERYD_TASK_SOFT_TIME_LIMIT = 20 * 60  # Raise exception if task takes too long.
    CELERYD_TASK_TIME_LIMIT = 30 * 60  # Kill worker if task takes way too long.
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_ACKS_LATE = True
    CELERY_DISABLE_RATE_LIMITS = True
    CELERY_IMPORTS = ('blacklist',)
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TASK_RESULT_EXPIRES = 10 * 60  # Dispose of Celery Beat results after 10 minutes.
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_TRACK_STARTED = True
    CELERY_DEFAULT_QUEUE = 'blacklist'

    CELERY_BEAT_SCHEDULE = {
        'blacklist-every-hour': dict(task='blacklist.crawl_blacklist', schedule=crontab(minute='0')),
    }


class CacheConfig(CeleryConfig):
    CACHE_TYPE = 'redis'
    CACHE_KEY_PREFIX = 'blacklist'


class Config(CacheConfig):
    """Default Flask configuration inherited by all environments. Use this for development environments."""
    DEBUG = True
    TESTING = False
    SECRET_KEY = "i_don't_want_my_cookies_expiring_while_developing"
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/blacklist.db'
    REDIS_URL = 'redis://127.0.0.1/0'
    CELERY_BROKER_URL = 'redis://127.0.0.1/0'
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1/0'
    SOCKET_IO_MESSAGE_QUEUE = 'redis://127.0.0.1/0'
    CACHE_REDIS_URL = 'redis://127.0.0.1/0'
    PORT = 5000
    HOST = '0.0.0.0'


class Testing(Config):
    TESTING = True
    CELERY_ALWAYS_EAGER = True
    REDIS_URL = 'redis://127.0.0.1/1'
    CELERY_BROKER_URL = 'redis://127.0.0.1/1'
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1/1'
    SOCKET_IO_MESSAGE_QUEUE = 'redis://127.0.0.1/1'
    CACHE_REDIS_URL = 'redis://127.0.0.1/1'


class Production(Config):
    DEBUG = False
    SECRET_KEY = None  # To be overwritten by a YAML file.
    SQLALCHEMY_DATABASE_URI = None
    PORT = None  # To be overwritten by a YAML file.
    HOST = None  # To be overwritten by a YAML file.
    PDF_STORAGE_FOLDER = '/home/blacklist/pdfs'
    THUMBNAIL_STORAGE_FOLDER = '/home/blacklist/thumbnails'
