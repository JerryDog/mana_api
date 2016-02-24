# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from flask import jsonify
from flask import request
from mana_api.api import zt_api
from mana_api.config import logging
from mana_api.apiUtil import get_monthly_flow, today, get_flow
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)

@zt_api.route('/flow', methods=['GET'])
def flow():
    """
    :param start: 查询开始时间
    :param end: 查询结束时间
    :param project_id: 租户id
    :param region: 区域
    """
    now = today()
    start = request.args.get('start', None)
    end = request.args.get('end', None) or now
    project_id = request.args.get('project_id')
    region = request.args.get('region', None)
    if not project_id:
        return jsonify({"code": 400, "msg": "Bad Request"}), 400

    logger.info('Request: url => flow '
                'start => %s '
                'end => %s '
                'project_id => %s '
                'region => %s' % (start, end, project_id, region))
    try:
        result = get_flow(project_id, region, start, end)
        return jsonify(result)
    except Exception, e:
        logger.error('Error with get flow, reason: %s' % e)
        return jsonify({"code": 400, "msg": "%s" % e}), 400

@zt_api.route('/flow_monthly', methods=['GET'])
def flow_monthly():
    """
    :param project_id: 租户id
    :param region: 区域
    :param month: 月份, 格式 %Y-%m( 没有就返回这个项目的全部 )
    """
    project_id = request.args.get('project_id')
    region = request.args.get('region', None)
    month = request.args.get('month', None)

    if not project_id:
        return jsonify({"code": 400, "msg": "Bad Request"}), 400

    logger.info('Request: url => flow_monthly '
                'month => %s '
                'project_id => %s '
                'region => %s' % (month, project_id, region))

    try:
        result = get_monthly_flow(project_id, region, month)
        return jsonify(result)
    except Exception, e:
        logger.error('Error with get flow_monthly, reason: %s' % e)
        return jsonify({"code": 400, "msg": "%s" % e}), 400