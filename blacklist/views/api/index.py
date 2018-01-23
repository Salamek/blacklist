# -*- coding: utf-8 -*-

import re

from flask import jsonify, request, url_for, render_template

from blacklist.models.blacklist import Blacklist
from blacklist.tasks.blacklist import log_block, log_api
from blacklist.blueprints import api_index

from urllib.request import urlopen
from urllib.parse import urljoin


__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"


@api_index.route('/doc', methods=['GET'])
def get_doc():
    return render_template('api.index.doc.html')


@api_index.route('/image/<int:blacklist_id>', methods=['GET'])
def get_image(blacklist_id):
    working_images = 2

    item = Blacklist.query.filter(Blacklist.id == blacklist_id).first_or_404()

    url = item.dns
    if not url.startswith('http'):
        url = 'http://{}'.format(url)

    # Find all images on website
    try:
        website = urlopen(url)
    except:
        return jsonify({'message': 'Failed to load page for test images'}), 500
    html = website.read()
    pat = re.compile(b'<img [^>]*src="([^"]+)')
    images = pat.findall(html)

    # Find working_images for testing
    images_absolute = []
    for image in images:
        image_absolute = urljoin(url, image.decode('UTF-8'))
        try:
            image = urlopen(image_absolute)
            info = image.info()
            if info and info['Content-Type'].startswith('image'):
                images_absolute.append(image_absolute)

                if len(images_absolute) >= working_images:
                    break
        except:
            pass

    return jsonify(images_absolute), 200


@api_index.route('/blocks/<int:blacklist_id>', methods=['POST'])
def log_blocks(blacklist_id):

    if 'tests' not in request.json or 'success' not in request.json:
        return jsonify({'error': 'Wrong arguments'}), 400

    tests = int(request.json['tests'])
    success = int(request.json['success'])

    log_block.delay(blacklist_id, request.remote_addr, tests, success)

    return jsonify({}), 200


@api_index.route('/blacklist', methods=['GET'], defaults={'page': 1})
@api_index.route('/blacklist/page/<int:page>', methods=['GET'])
def get_blacklist(page):
    data = Blacklist.query.filter().order_by(Blacklist.created.desc())

    log_api.delay(request.remote_addr)

    if 'per_page' in request.args:
        per_page = int(request.args['per_page'])
    else:
        per_page = data.count()

    paginator = data.paginate(page, per_page)

    data_ret = []
    for row in paginator.items:
        last_pdf = row.pdfs.first()

        data_ret.append({
            'id': row.id,
            'dns': row.dns,
            'bank_account': row.bank_account,
            'has_thumbnail': row.thumbnail,
            'thumbnail': url_for('static', filename='img/thumbnails/thumbnail_{}.png'.format(row.id), _external=True) if row.thumbnail else None,
            'signed': last_pdf.signed,
            'ssl': last_pdf.ssl,
            'dns_date_published': row.dns_date_published,
            'dns_date_removed': row.dns_date_removed,
            'bank_account_date_published': row.bank_account_date_published,
            'bank_account_date_removed': row.bank_account_date_removed,
            'note': row.note,
            'updated': row.updated,
            'created': row.created
        })

        if 'reveal_agent_identity' in request.args and request.args['reveal_agent_identity']:
            data_ret[-1]["agent"] = "bureš"

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
        'next': url_for('api.index.get_blacklist', page=paginator.next_num, _external=True),
        'prev': url_for('api.index.get_blacklist', page=paginator.prev_num, _external=True)
    }
    return jsonify(ret), 200
