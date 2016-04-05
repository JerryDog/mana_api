# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from flask import g
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api import apiUtil
from mana_api.apiUtil import MyError
import sys


reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)


@zt_api.route('/pm_order/<tenant_id>', methods=['GET'])
def get_orders(tenant_id):
    # 获取订单列表
    get_type = request.args.get('type', '4')
    try:
        result = apiUtil._get_orders(tenant_id, get_type)
        return jsonify(result)
    except:
        logger.exception('Error with get order list')
        return jsonify({"code": 400, "msg": "Error with get order list"}), 400


@zt_api.route('/pm_order/<tenant_id>', methods=['POST'])
def add_order(tenant_id):
    data = request.json
    if not data:
        return jsonify({"code": 400, "msg": "Bad request, could not find json data"}), 400

    try:
        result = apiUtil._add_order(tenant_id, data)
        return jsonify(result)
    except MyError, e:
        logger.exception('MyError raise')
        return jsonify({"code": 400, "msg": '%s' % e.value}), 400
    except:
        logger.exception('Error with add order')
        return jsonify({"code": 400, "msg": "Error with add order"}), 400



@zt_api.route('/pm_order/<tenant_id>', methods=['PUT'])
def process_orders(tenant_id):
    # 用户接受或拒绝订单
    data = request.json
    if not data:
        return jsonify({"code": 400, "msg": "Bad request, could not find json data"}), 400

    try:
        result = apiUtil._process_orders(tenant_id, data)
        return jsonify(result)
    except MyError, e:
        logger.exception('MyError raise')
        return jsonify({"code": 400, "msg": '%s' % e.value}), 400
    except:
        logger.exception('Error with process orders')
        return jsonify({"code": 400, "msg": "Error with process orders"}), 400