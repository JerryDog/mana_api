# -*- coding: utf-8 -*-
# 星云延伸功能，如改密码，限速，创建私网
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.apiUtil import getUserProjByToken
from mana_api.api.vm.api_util import MyError, chg_linux_pwd, chg_win_pwd
from .tools.compute import InstanceManager

logger = logging.getLogger(__name__)

@zt_api.route('/chgPwd/<tenant_id>/<region>/<uuid>/<pwd>', methods=['GET'])
def chg_pwd(tenant_id, region, uuid, pwd):
    if not tenant_id or not region:
        return jsonify({"code": 400, "msg": "Could not find tenant_id or region"}), 400

    # 禁止跨项目操作
    user = getUserProjByToken(tenant_id)
    if not user or tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    try:
        client = InstanceManager(token=user.token, endpoint=user.get_endpoint(region, 'nova'))
        instance = client.nova_show(uuid)
        chg_linux_pwd(instance, pwd)
        chg_win_pwd(instance, pwd)
    except MyError, e:
        logger.exception('MyError raised')
        return jsonify({"code": 400, "msg": '%s' % e.value}), 400
    except:
        logger.exception('Error with get vm_servers')
        return jsonify({"code": 400, "msg": "Error with get chg_pwd"}), 400