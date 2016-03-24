# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.api.vm.api_util import MyError, openstack_error
from .tools.compute import InstanceManager
from mana_api.apiUtil import getUserProjByToken
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
    tenant_id = request.args.get('tenant_id', None)
    region = request.args.get('region', None)

    if not tenant_id or not region:
        return jsonify({"code": 400, "msg": "Could not find tenant_id or region"}), 400

    # 禁止跨项目操作
    user = getUserProjByToken(tenant_id)
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
        client = InstanceManager(token=user.token, endpoint=user.get_endpoint(region, "nova"))
        instance_collection = client.nova_list(f, t)
        total_count = len(instance_collection)
        vm_servers = []
        for i in instance_collection:
            instance = {
                "instance_name": i.name,
                "instance_id": i.id,
                "cpu_num": i.cpu,
                "mem_size": i.mem,
                "disk_size": i.disk,
                "lan_ip_set": i.lan_ip,
                "wan_ip_set": i.wan_ip,
                "status": i.status,
                "create_at": i.create_at,
                "update_at": i.update_at
            }
            vm_servers.append(instance)
        return jsonify({"code": 200, "msg": "", "total_count": total_count, "vm_servers": vm_servers})
    except MyError, e:
        logger.exception('MyError raised')
        return jsonify({"code": 400, "msg": '%s' % e.value}), 400
    except:
        logger.exception('Error with get vm_servers')
        return jsonify({"code": 400, "msg": "Error with get vm_servers"}), 400


@zt_api.route('/vm_act/<tenant_id>/<region>', methods=['POST'])
def vm_action(tenant_id, region):
    if not tenant_id or not region:
        return jsonify({"code": 400, "msg": "Could not find tenant_id or region or server_id"}), 400

    # 禁止跨项目操作
    user = getUserProjByToken(tenant_id)
    if not user or tenant_id not in user.proj_dict.keys():
        return jsonify({"code": 403, "msg": "project is not yours"}), 403

    body = request.json
    server_ids = body.get('servers')
    try:
        instance = InstanceManager(token=user.token, endpoint=user.get_endpoint(region, 'nova'))
        code = 200
        message = 'success'
        detail = []
        for i in server_ids.split(','):
            resp = instance.do(body, i)
            if resp.status != 202:
                _result = {"code": 200, "msg": "success", "server_id": i}
            else:
                code = 400
                message = 'failed'
                _result = openstack_error(resp)
                _result['server_id'] = i
            detail.append(_result)
        return jsonify({"code": code, "msg": message, "detail": detail}), code
    except MyError, e:
        logger.exception('MyError raised')
        return jsonify({"code": 400, "msg": '%s' % e.value}), 400
    except:
        logger.exception('Error with vm action')
        return jsonify({"code": 400, "msg": "Error with vm action"}), 400


