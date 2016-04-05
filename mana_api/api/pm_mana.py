# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from flask import g
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.apiUtil import get_pm, get_info_by_snid, update_stat_after_act, \
    get_pm_accounts, get_pm_accounts_detail, getUserProjByToken, add_pm, \
    MyError, get_single_pm, pm_update, get_contact_list, admin_required, add_contact_single, \
    delete_contact_list
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
    tenant_id = request.args.get('tenant_id', None)

    # 禁止跨项目操作
    user = getUserProjByToken(tenant_id)
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


@zt_api.route('/pm_act/<tenant_id>', methods=['POST'])
def pm_act(tenant_id):
    if not request.json:
        return jsonify({"error": "Bad request, no json data"}), 400
    act = request.json.get('act', None)  # act 只能是 on  off  reset
    username = request.json.get('username', None)
    snids = request.json.get('snids', None)
    if not act or not username or not snids or not tenant_id:
        return jsonify({"code": 400, "msg": "Bad request, no json data"}), 400

    # 禁止跨项目操作
    user = getUserProjByToken(tenant_id)
    if tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    all_pm_info = get_info_by_snid(snids=snids)

    logger.info('Request: execute pm action '
                'username => %s '
                'act => %s '
                'system_snid => %s '
                'tenant_id => %s' % (username, act, snids, tenant_id))

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
    user = getUserProjByToken(tenant_id)
    if tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    logger.info('Request: curl -i -H "X-Auth-Token: %s" '
                '-X GET "http://api.scloudm.com/mana_api/pm_bill?tenant_id=%s"' % (g.token, tenant_id))

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
    user = getUserProjByToken(tenant_id)
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


@zt_api.route('/pm/<snid>', methods=['GET'])
def pm_get(snid):
    # 获取单台物理机，新增物理机前判断是否存在
    try:
        result = get_single_pm(snid)
        return jsonify(result)
    except:
        logger.exception('Error with get single pm')
        return jsonify({"code": 400, "msg": "Error with get single pm"}), 400


@zt_api.route('/pm_add', methods=['POST'])
@admin_required
def pm_add():
    # 单台物理机录入
    add_data = request.json
    if not add_data:
        return jsonify({"code": 400, "msg": "Bad request, could not find json data"}), 400
    try:
        result = add_pm(add_data)
        return jsonify(result)
    except MyError, e:
        logger.exception('MyError raise')
        return jsonify({"code": 400, "msg": '%s' % e.value}), 400
    except:
        logger.exception('Error with add pm server')
        return jsonify({"code": 400, "msg": "Error with add pm server"}), 400



@zt_api.route('/pm_update/<snid>', methods=['PUT'])
@admin_required
def pm_modify(snid):
    # 修改物理机
    update_data = request.json
    if not update_data:
        return jsonify({"code": 400, "msg": "Bad request, could not find json data"}), 400

    try:
        result = pm_update(snid, update_data)
        return jsonify(result)
    except:
        logger.exception('Error with update pm server')
        return jsonify({"code": 400, "msg": "Error with update pm server"}), 400


@zt_api.route('/pm_contact/<tenant_id>', methods=['POST'])
def add_contact(tenant_id):
    # 新增邮件联系人列表
    data = request.json
    if not data:
        return jsonify({"code": 400, "msg": "Bad request, could not find json data"}), 400
    try:
        result = add_contact_single(tenant_id, data)
        return jsonify(result)
    except:
        logger.exception('Error with add contact')
        return jsonify({"code": 400, "msg": "Error with add contact"}), 400


@zt_api.route('/pm_contact/<tenant_id>', methods=['DELETE'])
def delete_contact(tenant_id):
    # 删除邮件联系人列表
    ids = request.args.get('ids', None)
    if not ids:
        return jsonify({"code": 400, "msg": "Bad request, could not find id to delete"}), 400
    try:
        result = delete_contact_list(ids)
        return jsonify(result)
    except:
        logger.exception('Error with delete contact')
        return jsonify({"code": 400, "msg": "Error with delete contact"}), 400


@zt_api.route('/pm_contact/<tenant_id>', methods=['GET'])
def get_contact(tenant_id):
    # 获取邮件联系人列表
    try:
        result = get_contact_list(tenant_id)
        return jsonify(result)
    except:
        logger.exception('Error with get contact list')
        return jsonify({"code": 400, "msg": "Error with get contact list"}), 400

