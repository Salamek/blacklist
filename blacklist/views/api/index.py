# -*- coding: utf-8 -*-

import requests
from lxml import etree as ElTr
from flask import jsonify, request, url_for, render_template

from blacklist.models.blacklist import Blacklist
from blacklist.tasks.blacklist import log_block, log_api
from blacklist.blueprints import api_index

from urllib.parse import urljoin


__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"


@api_index.route('/doc', methods=['GET'])
def get_doc():
    return render_template('api.index.doc.html')


@api_index.route('/image/<int:blacklist_id>', methods=['GET'])
def get_image(blacklist_id: int):
    working_images = 2

    item = Blacklist.query.filter(Blacklist.id == blacklist_id).first_or_404()

    url = item.dns
    if not url.startswith('http'):
        url = 'http://{}'.format(url)

    # Find all images on website
    try:
        website = requests.get(url)
    except Exception as e:
        return jsonify({
            'message': 'Failed to load page for test images',
            'url': url,
            'e': str(e)
        }), 500

    parser = ElTr.HTMLParser(recover=True)
    el = ElTr.ElementTree(ElTr.fromstring(website.text, parser))
    root = el.getroot()
    images = root.iter('img')

    # Find working_images for testing
    images_absolute = []
    for image in images:
        image_absolute = urljoin(website.url, image.get('src'))
        try:
            image_head = requests.head(image_absolute)
            if image_head.headers['content-type'].startswith('image'):
                images_absolute.append(image_absolute)

                if len(images_absolute) >= working_images:
                    break
        except Exception:
            pass

    return jsonify(images_absolute), 200


@api_index.route('/blocks/<int:blacklist_id>', methods=['POST'])
def log_blocks(blacklist_id: int):

    if 'tests' not in request.json or 'success' not in request.json:
        return jsonify({'error': 'Wrong arguments'}), 400

    tests = int(request.json['tests'])
    success = int(request.json['success'])

    log_block.delay(blacklist_id, request.remote_addr, tests, success)

    return jsonify({}), 200


@api_index.route('/blacklist', methods=['GET'], defaults={'page': 1})
@api_index.route('/blacklist/page/<int:page>', methods=['GET'])
def get_blacklist(page: int):
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
