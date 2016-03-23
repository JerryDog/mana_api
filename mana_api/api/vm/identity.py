# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from flask import g
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.apiUtil import http_request
import urlparse
import json

logger = logging.getLogger(__name__)


@zt_api.route('/tokens', methods=['POST'])
def get_tokens():
    body = json.dumps(request.json)
    headers = {"Content-type": "application/json"}
    method = request.method
    try:
        url = urlparse.urljoin('http://' + g.uri + '/', '/v2.0/tokens')
        res = http_request(url, body=body, headers=headers, method=method)
        dd = json.loads(res.read())
        return jsonify(dd), 200
    except Exception, e:
        logger.exception('Error with get token')
        return jsonify({"code": 400, "msg": "%s" % e}), 400


@zt_api.route('/region_tenant', methods=['GET'])
def get_region_tenant():
    result = {"code": 200, "msg": "", "regions": g.user.get_regions(), "tenants": g.user.get_tenants()}
    return jsonify(result), 200

