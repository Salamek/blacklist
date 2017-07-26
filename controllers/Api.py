from flask import jsonify, Blueprint, request, url_for, current_app, render_template
from task import create_celery
from database import db, Role, Blacklist
__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

api = Blueprint('api', __name__)

@api.route('/doc', methods=['GET'])
def get_doc():
    return render_template('api_doc.html')


@api.route('/blacklist', methods=['GET'], defaults={'page': 1})
@api.route('/blacklist/page/<int:page>', methods=['GET'])
def get_blacklist(page):
    data = Blacklist.query.filter().order_by(Blacklist.created.desc())

    if 'per_page' in request.args:
        per_page = int(request.args['per_page'])
    else:
        per_page = data.count()

    paginator = data.paginate(page, per_page)

    data_ret = []
    for row in paginator.items:
        data_ret.append({
            'id': row.id,
            'dns': row.dns,
            'bank_account': row.bank_account,
            'has_thumbnail': row.thumbnail,
            'thumbnail': url_for('static', filename='img/thumbnails/thumbnail_{}.png'.format(row.id), _external=True) if row.thumbnail else None,
            'signed': row.signed,
            'ssl': row.ssl,
            'date': row.date,
            'note': row.note,
            'updated': row.updated,
            'created': row.created
        })

    ret = {
        'has_next': paginator.has_next,
        'has_prev': paginator.has_prev,
        'next_num': paginator.next_num,
        'prev_num': paginator.prev_num,
        'page': paginator.page,
        'pages': paginator.pages,
        'per_page': paginator.per_page,
        'total': paginator.total,
        'data': data_ret,
        'next': url_for('api.get_blacklist', page=paginator.next_num, _external=True),
        'prev': url_for('api.get_blacklist', page=paginator.prev_num, _external=True)
    }
    return jsonify(ret), 200
