"""
Bootstrap for use in uwsgi and so
"""

from blacklist.application import create_app, get_config

config = get_config('blacklist.config.Production')
app = create_app(config)
