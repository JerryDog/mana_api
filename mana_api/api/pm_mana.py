# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.apiUtil import get_pm, get_info_by_snid, update_stat_after_act, \
    get_pm_accounts, get_pm_accounts_detail, getUserProjByToken
import sys
import os

reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)


@zt_api.route('/pm', methods=['GET'])
def pm():
    """
    :param project_id: 租户id
    :param region: 区域
    :param  f: 起始位置
    :param  t: 结束位置
    :return: 返回物理机列表
    """
    token = request.headers.get("X-Auth-Token")
    tenant_id = request.args.get('tenant_id', None)

    # 禁止跨项目操作
    user = getUserProjByToken(token)
    if tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "无权限操作该项目".decode('utf-8')}), 403

    region = request.args.get('region', None)
    f = request.args.get('f', None)
    f = int(f) if f else f
    t = request.args.get('t', None)
    t = int(t) if t else t
    logger.info('Request: get pm servers list '
                'tenant_id => %s '
                'region => %s '
                'from => %s '
                'to => %s' % (tenant_id, region, f, t))

    try:
        result = get_pm(tenant_id, region, f, t)
        return jsonify(result)
    except:
        logger.exception('Error with get pm_servers')
        return jsonify({"code": 400, "msg": "Error with get pm_servers"}), 400


@zt_api.route('/pm_act', methods=['POST'])
def pm_act():
    if not request.json:
        return jsonify({"error": "Bad request, no json data"}), 400
    token = request.headers.get("X-Auth-Token")
    tenant_id = request.json.get('tenant_id', None)
    act = request.json.get('act', None)  # act 只能是 on  off  reset
    username = request.json.get('username', None)
    system_snid = request.json.get('system_snid', None)
    if not act or not username or not system_snid or not tenant_id:
        return jsonify({"code": 400, "msg": "Bad request, no json data"}), 400

    # 禁止跨项目操作
    user = getUserProjByToken(token)
    if tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    all_pm_info = get_info_by_snid(snid=system_snid)

    logger.info('Request: execute pm action '
                'username => %s '
                'act => %s '
                'system_snid => %s '
                'tenant_id => %s' % (username, act, system_snid, tenant_id))

    try:
        result = {"code": 200, "msg": "success", "detail": []}
        for a in all_pm_info:
            res = os.system('ipmitool -I lanplus -U %s -P %s -H %s power %s' % (a[0], a[1], a[2], act))
            logger.info('ipmitool -I lanplus -U %s -P %s -H %s power %s' % (a[0], a[1], a[2], act))
            if res != 0:
                result["code"] = 400
                result["msg"] = "failed"
                result["detail"].append({"code": 400, "msg": "failed", "snid": a[3]})
            else:
                result["detail"].append({"code": 200, "msg": "success", "snid": a[3]})
            update_stat_after_act(act, a[3])
        return jsonify(result)
    except:
        logger.exception('Error with execute act %s' % act)
        return jsonify({"code": 400, "msg": "Sys Error with execute act %s" % act}), 400


@zt_api.route('/pm_bill', methods=['GET'])
def pm_bill():
    tenant_id = request.args.get('tenant_id', None)
    if not tenant_id:
         return jsonify({"code": 400, "msg": "Bad request, tenant_id required"}), 400

    # 禁止跨项目操作
    token = request.headers.get("X-Auth-Token")
    user = getUserProjByToken(token)
    if tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    logger.info('Request: get pm accounts '
                'tenant_id => %s ' % tenant_id)

    try:
        result = get_pm_accounts(tenant_id)
        return jsonify(result)
    except:
        logger.exception('Error with get pm_accounts')
        return jsonify({"code": 400, "msg": "Error with get pm_accounts"}), 400


@zt_api.route('/pm_bill_detail', methods=['GET'])
def pm_bill_detail():
    tenant_id = request.args.get('tenant_id', None)
    region = request.args.get('region', None)
    month = request.args.get('month', None)
    if not month or not region or not tenant_id:
        return jsonify({"code": 400, "msg": "Bad request, lost params"}), 400

    # 禁止跨项目操作
    token = request.headers.get("X-Auth-Token")
    user = getUserProjByToken(token)
    if tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    logger.info('Request: get pm accounts detail'
                'tenant_id => %s '
                'region => %s '
                'month => %s '% (tenant_id, region, month))

    try:
        result = get_pm_accounts_detail(tenant_id, region, month)
        return jsonify(result)
    except:
        logger.exception('Error with get pm_accounts_detail')
        return jsonify({"code": 400, "msg": "Error with get pm_accounts_detail"}), 400

