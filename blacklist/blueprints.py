# -*- coding: utf-8 -*-

"""All Flask blueprints for the entire application.

All blueprints for all views go here. They shall be imported by the views themselves and by application.py. Blueprint
URL paths are defined here as well.
"""

from flask import Blueprint


def _factory(name: str, partial_module_string: str, url_prefix: str=None) -> Blueprint:
    """Generates blueprint objects for view modules.

    Positional arguments:
    partial_module_string -- string representing a view module without the absolute path (e.g. 'home.index' for
        blacklist.views.home.index).
    url_prefix -- URL prefix passed to the blueprint.

    Returns:
    Blueprint instance for a view module.
    """
    import_name = 'blacklist.views.{}'.format(partial_module_string)
    template_folder = 'templates'
    blueprint = Blueprint(name, import_name, template_folder=template_folder, url_prefix=url_prefix)
    return blueprint


home_index = _factory('home_index', 'home.index')
sign_index = _factory('sign_index', 'sign.index', '/sign')
api_index = _factory('api_index', 'api.index', '/api')

blacklist_index = _factory('blacklist_index', 'blacklist.index', '/blacklist')
crawl_index = _factory('crawl_index', 'crawl.index', '/crawl')
user_index = _factory('user_index', 'user.index', '/user')
download_index = _factory('download_index', 'download.index', '/download')
statistics_index = _factory('statistics_index', 'statistics.index', '/statistics')


all_blueprints = (
    home_index,
    sign_index,
    api_index,
    blacklist_index,
    crawl_index,
    user_index,
    download_index,
    statistics_index
)
