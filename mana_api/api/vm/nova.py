# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.apiUtil import getUserProjByToken
from mana_api.api.vm.api_util import nova_list, get_new_token
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)


@zt_api.route('/vm', methods=['GET'])
def vm():
    """
    :param project_id: 租户id
    :param region: 区域
    :param  f: 起始位置
    :param  t: 结束位置
    :return: 返回虚拟机列表
    """
    token = request.headers.get("X-Auth-Token")
    tenant_id = request.args.get('tenant_id', None)
    region = request.args.get('region', None)

    if not tenant_id or not region:
        return jsonify({"code": 400, "msg": "Could not find tenant_id or region"}), 400

    new_token = get_new_token(token, tenant_id)
    # 禁止跨项目操作
    user = getUserProjByToken(new_token)
    if not user or tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    f = request.args.get('f', None)
    f = int(f) if f else f
    t = request.args.get('t', None)
    t = int(t) if t else t
    logger.info('Request: get vm servers list '
                'tenant_id => %s '
                'region => %s '
                'from => %s '
                'to => %s' % (tenant_id, region, f, t))

    try:
        result = nova_list(new_token, user.get_endpoint(region, "nova"), f, t)
        return jsonify(result)
    except:
        logger.exception('Error with get vm_servers')
        return jsonify({"code": 400, "msg": "Error with get vm_servers"}), 400




