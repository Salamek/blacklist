import flask

from blacklist.models.blacklist import Blacklist
from blacklist.blueprints import download_index

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"


@download_index.route('/', methods=['GET'])
def get_download():
    return flask.render_template('download.index.download.html')


@download_index.route('/hosts', methods=['GET'])
def get_hosts():
    items = Blacklist.query.yield_per(1000)

    def generate():
        for item in items:
            if item.a:
                yield "{} {}\n".format(item.a, item.dns)
            if item.aaaa:
                yield "{} {}\n".format(item.aaaa, item.dns)

    return flask.Response(
        flask.stream_with_context(generate()),
        mimetype="text/plain",
        headers={"Content-disposition":
                 "attachment; filename=hosts"})

