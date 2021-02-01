import hashlib
import datetime
import random
import sys
import string


def random_password() -> str:
    return hashlib.md5(str(random.randint(0, sys.maxsize)).encode('UTF-8')).hexdigest()


def fix_url(url: str) -> str:
    """
    Fixes url
    :param url:
    :return:
    """
    if not url.startswith('http'):
        url = 'http://{}'.format(url)
    return url


def parse_czech_date(date_garbage: str) -> datetime.datetime:
    clean_date = date_garbage.translate(str.maketrans('', '', string.whitespace))
    date_format = "%d.%m.%Y"
    return datetime.datetime.strptime(clean_date, date_format)