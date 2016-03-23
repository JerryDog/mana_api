# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from mana_api.api import zt_api
from mana_api.config import logging
from flask import render_template
import sys
import json
from mana_api.apiUtil import get_pm_monitor_statics

reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)


@zt_api.route('/pm_monitor/<system_snid>/', methods=['GET'])
def pm_monitor(system_snid):
    return render_template('metric.html', system_snid=system_snid)


@zt_api.route('/pm_monitor/statics/<metric>/<system_snid>/<duration>/', methods=['POST'])
def pm_monitor_statics(metric, system_snid, duration):

    logger.info('Request: get pm monitor data '
                'metric => %s '
                'system_snid => %s '
                'duration => %s ' % (metric, system_snid, duration))

    try:
        result = get_pm_monitor_statics(metric, system_snid, duration)
        return json.dumps(result)
    except:
        logger.exception('Error with get pm monitor: %s, %s, %s' % (
            metric, system_snid, duration
        ))
        return json.dumps({"code": 400, "msg": "Error with get pm monitor"}), 400