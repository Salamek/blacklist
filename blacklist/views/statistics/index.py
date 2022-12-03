import flask
import hashlib
import datetime
from flask_babel import format_date, gettext
from sqlalchemy.sql import func
from blacklist.models.blacklist import Pdf, BlockingLog, ApiLog
import pygal
from pygal.style import DarkSolarizedStyle
from blacklist.blueprints import statistics_index
from blacklist.extensions import db

__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"


@statistics_index.route('/', methods=['GET'])
def get_statistics():
    data = db.session.query(
        func.sum(BlockingLog.success).label("success_all"),
        func.sum(BlockingLog.tests).label("tests_all")
    ).one_or_none()

    class BlockingPieStyle(DarkSolarizedStyle):
        colors = ('#d9534f', '#5cb85c')

    blocking_success_chart = pygal.Pie(
        width=1200,
        height=400,
        explicit_size=True,
        title='Blocking',
        inner_radius=.4,
        style=BlockingPieStyle
    )

    blocked = data.tests_all - data.success_all if data.tests_all and data.success_all else None
    blocking_success_chart.add('Blocked', blocked)
    blocking_success_chart.add('Not blocked', data.success_all)

    blacklist_grow_chart = pygal.Bar(
        width=1200,
        height=400,
        explicit_size=True,
        title='Blacklist grow',
        style=DarkSolarizedStyle
    )

    blacklist_grow_x_labels = []
    blacklist_grow_data_items = []
    blacklist_grow_data_pages = []

    for item in Pdf.query.order_by(Pdf.created.asc()):
        blacklist_grow_x_labels.append(format_date(item.created))
        blacklist_grow_data_items.append(item.blacklist.count())
        blacklist_grow_data_pages.append(item.pages)
    blacklist_grow_chart.add('Items', blacklist_grow_data_items)
    blacklist_grow_chart.add('Pages', blacklist_grow_data_pages)

    blacklist_grow_chart.x_labels = blacklist_grow_x_labels

    api_usage_day_limit = 30
    api_usage_chart = pygal.Bar(
        width=1200,
        height=400,
        explicit_size=True,
        title=gettext('API Usage for last %(days)s days', days=api_usage_day_limit),
        style=DarkSolarizedStyle
    )

    from_date = datetime.datetime.today() - datetime.timedelta(days=api_usage_day_limit)
    days = db.session.query(
        func.sum(ApiLog.requests).label("requests_all"),
        ApiLog.date
    ).filter(ApiLog.date >= from_date).group_by(ApiLog.date).order_by(ApiLog.date.asc())

    api_usage_x_labels = []
    api_usage_data = []
    for item in days:
        api_usage_x_labels.append(format_date(item.date))
        api_usage_data.append(item.requests_all)
    api_usage_chart.add('Requests', api_usage_data)

    api_usage_chart.x_labels = api_usage_x_labels

    api_ip_usage_day_limit = 30
    api_ip_usage_chart = pygal.Bar(
        width=1200,
        height=400,
        explicit_size=True,
        title=gettext('API IP usage for last %(days)s days (Real IP encoded by sha256)', days=api_ip_usage_day_limit),
        style=DarkSolarizedStyle
    )

    from_date = datetime.datetime.today() - datetime.timedelta(days=api_ip_usage_day_limit)
    ips = db.session.query(
        func.sum(ApiLog.requests).label("requests_all"),
        ApiLog.remote_addr
    ).filter(ApiLog.date >= from_date).group_by(ApiLog.remote_addr).order_by("requests_all")

    api_ip_usage_x_labels = []
    api_ip_usage_data = []
    for item in ips:
        api_ip_usage_x_labels.append(hashlib.sha256(item.remote_addr.encode()).hexdigest())
        api_ip_usage_data.append(item.requests_all)
    api_ip_usage_chart.add('Requests', api_ip_usage_data)

    api_ip_usage_chart.x_labels = api_ip_usage_x_labels

    return flask.render_template('statistics.index.statistics.html',
                                 blocking_success_chart=blocking_success_chart,
                                 blacklist_grow_chart=blacklist_grow_chart,
                                 api_usage_chart=api_usage_chart,
                                 api_ip_usage_chart=api_ip_usage_chart
                                 )
