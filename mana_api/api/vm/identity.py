# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.apiUtil import getUserProjByToken
from mana_api.api.vm.api_util import get_new_token

logger = logging.getLogger(__name__)

@zt_api.route('/regions', methods=['GET'])
def get_regions():
    token = request.headers.get("X-Auth-Token")
    tenant_id = request.args.get('tenant_id', None)
    if not tenant_id:
        return jsonify({"code": 400, "msg": "Could not find tenant_id"}), 400

    new_token = get_new_token(token, tenant_id)
    # 禁止跨项目操作
    user = getUserProjByToken(new_token)
    if not user or tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    logger.info('Request: get regions list '
                'tenant_id => %s ' % tenant_id)

    result = {"code": 200, "msg": "", "regions": user.get_regions()}
    return jsonify(result), 200