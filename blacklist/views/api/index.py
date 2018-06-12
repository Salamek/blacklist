# -*- coding: utf-8 -*-

import requests
from lxml import etree as ElTr
from flask import jsonify, request, url_for, render_template, send_from_directory, current_app

from blacklist.extensions import cache
from blacklist.tools.helpers import fix_url
from blacklist.models.blacklist import Blacklist, Pdf
from blacklist.tasks.blacklist import log_block, log_api
from blacklist.blueprints import api_index

from urllib.parse import urljoin


__author__ = "Adam Schubert"
__date__ = "$26.7.2017 19:33:05$"


@api_index.route('/doc', methods=['GET'])
def get_doc():
    return render_template('api.index.doc.html')


@api_index.route('/image/<int:blacklist_id>', methods=['GET'])
@cache.cached(timeout=360)
def get_image(blacklist_id: int):
    working_images = 2

    item = Blacklist.query.filter(Blacklist.id == blacklist_id).first_or_404()

    url = fix_url(item.dns)

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

    images_raw = []

    # Lets try find standard images
    for image in root.iter('img'):
        images_raw.append(image.get('src'))

    # Lets try find favicons cos idiotic websites written in javascript
    for image in root.findall(".//link[@rel='icon']"):
        images_raw.append(image.get('href'))

    # And favicons with idiotic IE syntax
    for image in root.findall(".//link[@rel='shortcut icon']"):
        images_raw.append(image.get('href'))

    # Find working_images for testing
    images_absolute = []
    for image_src in images_raw:

        # Check if image we found is loaded from checked DNS
        if 'http' in image_src and item.dns not in image_src:
            continue

        # Use resolved url only when it is same domain as blocked DNS
        if item.dns in website.url:
            image_absolute = urljoin(website.url, image_src)
        else:
            image_absolute = urljoin(url, image_src)

        try:
            image_head = requests.head(image_absolute, allow_redirects=True)
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


@api_index.route('/thumbnail/<int:blacklist_id>.png', methods=['GET'])
def get_thumbnail(blacklist_id: int):

    blacklist = Blacklist.query.filter_by(id=blacklist_id).first()
    if not blacklist:
        return jsonify({
            'message': 'Blacklist with ID {} not found.'.format(blacklist_id)
        }), 400

    return send_from_directory(current_app.config['THUMBNAIL_STORAGE_FOLDER'], filename='thumbnail_{}.png'.format(blacklist.id)), 200


@api_index.route('/pdf/<string:pdf_sum>.pdf', methods=['GET'])
def get_pdf(pdf_sum: str):

    pdf = Pdf.query.filter_by(sum=pdf_sum).first()
    if not pdf:
        return jsonify({
            'message': 'PDF with sum {} not found.'.format(pdf_sum)
        }), 400

    return send_from_directory(current_app.config['PDF_STORAGE_FOLDER'], filename='{}.pdf'.format(pdf.sum)), 200


@api_index.route('/blacklist', methods=['GET'], defaults={'page': 1})
@api_index.route('/blacklist/page/<int:page>', methods=['GET'])
def get_blacklist(page: int):
    log_api.delay(request.remote_addr)

    blacklist_filter = []
    if 'dns' in request.args:
        blacklist_filter.append(Blacklist.dns.like("%{}%".format(request.args['dns'])))

    if 'redirects_to' in request.args:
        blacklist_filter.append(Blacklist.redirects_to.like("%{}%".format(request.args['redirects_to'])))

    if 'a' in request.args:
        blacklist_filter.append(Blacklist.a.like("%{}%".format(request.args['a'])))

    if 'aaaa' in request.args:
        blacklist_filter.append(Blacklist.aaaa.like("%{}%".format(request.args['aaaa'])))

    if 'bank_account' in request.args:
        blacklist_filter.append(Blacklist.bank_account.like("%{}%".format(request.args['bank_account'])))

    data = Blacklist.query.filter(*blacklist_filter).order_by(Blacklist.created.desc())

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
            'thumbnail': url_for('api.index.get_thumbnail', blacklist_id=row.id, _external=True) if row.thumbnail else None,
            'signed': last_pdf.signed,
            'ssl': last_pdf.ssl,
            'dns_date_published': row.dns_date_published,
            'dns_date_removed': row.dns_date_removed,
            'bank_account_date_published': row.bank_account_date_published,
            'bank_account_date_removed': row.bank_account_date_removed,
            'note': row.note,
            'redirects_to': row.redirects_to,
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
