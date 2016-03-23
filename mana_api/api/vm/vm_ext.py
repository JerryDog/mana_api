# -*- coding: utf-8 -*-
# 星云延伸功能，如改密码，限速，创建私网
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.apiUtil import getUserProjByToken
from mana_api.api.vm.api_util import get_new_token, nova_show, MyError

logger = logging.getLogger(__name__)

@zt_api.route('/chgPwd/<tenant_id>/<region>/<uuid>/<pwd>', methods=['GET'])
def chg_pwd(tenant_id, region, uuid, pwd):
    token = request.headers.get("X-Auth-Token")
    if not tenant_id or not region:
        return jsonify({"code": 400, "msg": "Could not find tenant_id or region"}), 400
    new_token = get_new_token(token, tenant_id)
    # 禁止跨项目操作
    user = getUserProjByToken(new_token)
    if not user or tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    try:
        host_info = nova_show(new_token, user.get_endpoint(region, "nova"), uuid)
        host_ip = host_info["host_ip"]
        instance_name = host_info["instance_name"]
    except MyError, e:
        logger.exception('MyError raised')
        return jsonify({"code": 400, "msg": '%s' % e.value}), 400
    except:
        logger.exception('Error with get vm_servers')
        return jsonify({"code": 400, "msg": "Error with get chg_pwd"}), 400