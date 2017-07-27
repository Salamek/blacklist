import flask.json
import decimal

from controllers.Api import api
from controllers.Home import home
from controllers.User import user
from controllers.Blacklist import blacklist
from controllers.Crawl import crawl
from database import db
from flask import Flask, url_for, request
from flask_migrate import Migrate

from raven.contrib.flask import Sentry
from flask_babel import Babel

def create_application():
    sentry = Sentry()

    app = Flask(__name__)
    app.config.from_object('config.Blacklist')

    migrate = Migrate(app, db)

    babel = Babel(app)

    # sentry = Sentry(app)
    # Convert decimals to floats in JSON

    def url_for_other_page(page):
        args = request.view_args.copy()
        args['page'] = page
        return url_for(request.endpoint, **args)
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page

    class APIoTJSONEncoder(flask.json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, decimal.Decimal):
                # Convert decimal instances to float.
                return float(obj)
            return super(APIoTJSONEncoder, self).default(obj)

    app.json_encoder = APIoTJSONEncoder

    db.init_app(app)
    sentry.init_app(app)
    app.sentry = sentry

    app.register_blueprint(home)
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(user, url_prefix='/user')
    app.register_blueprint(blacklist, url_prefix='/blacklist')
    app.register_blueprint(crawl, url_prefix='/crawl')

    return app
