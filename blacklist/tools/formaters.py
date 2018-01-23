
def format_bytes(num, suffix='B'):
    """
    Format bytes to human readable string
    @param num:
    @param suffix:
    @return:
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def fix_url(url):
    """
    Fixes url
    :param url: 
    :return: 
    """
    if not url.startswith('http'):
        url = 'http://{}'.format(url)
    return url


def format_boolean(bool_to_format):
    """
    Formats boolean
    :param bool_to_format: 
    :return: 
    """
    return '<div class="label label-success">Yes</div>' if bool_to_format else '<div class="label label-danger">No</div>'

