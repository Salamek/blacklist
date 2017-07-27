from flask import jsonify, Blueprint, request, url_for, current_app, render_template
from task import create_celery
from database import db, Role, Blacklist
import urllib.request
import sys
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

import re


__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"

api = Blueprint('api', __name__)

@api.route('/doc', methods=['GET'])
def get_doc():
    return render_template('api_doc.html')


@api.route('/image/<int:blacklist_id>')
def get_image(blacklist_id):
    working_images = 2

    item = Blacklist.query.filter(Blacklist.id == blacklist_id).first_or_404()

    url = item.dns
    if not url.startswith('http'):
        url = 'http://{}'.format(url)

    # Find all images on website
    website = urllib.request.urlopen(url)
    html = website.read()
    if (sys.version_info > (3, 0)):
        pat = re.compile(rb'<img [^>]*src="([^"]+)')
    else:
        pat = re.compile(r'<img [^>]*src="([^"]+)')
    images = pat.findall(html)

    # Find working_images for testing
    images_absolute = []
    for image in images:
        image_absolute = urljoin(url, image.decode('UTF-8'))
        try:
            image = urllib.request.urlopen(image_absolute)
            info = image.info()
            if info and info['Content-Type'].startswith('image'):
                images_absolute.append(image_absolute)

                if len(images_absolute) >= working_images:
                    break
        except:
            pass

    return jsonify(images_absolute), 200

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
