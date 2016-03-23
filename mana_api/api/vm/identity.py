# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from flask import g
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.apiUtil import http_request, getUserProjByToken
from mana_api.api.vm.api_util import openstack_error
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
        if res.status == 200 or res.status == 203:
            dd = json.loads(res.read())
            return jsonify(dd), 200
        else:
            return jsonify(openstack_error(res)), res.status
    except Exception, e:
        logger.exception('Error with get token')
        return jsonify({"code": 400, "msg": "%s" % e}), 400


@zt_api.route('/region_tenant', methods=['GET'])
def get_region_tenant():
    user = getUserProjByToken()
    result = {"code": 200, "msg": "", "regions": user.get_regions(), "tenants": user.get_tenants()}
    return jsonify(result), 200

