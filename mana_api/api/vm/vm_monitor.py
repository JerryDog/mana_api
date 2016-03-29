# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
from mana_api.api import zt_api
from mana_api.config import logging
from flask import render_template
import sys
import json
from .tools.telemetry import get_vm_monitor_statics

reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)


@zt_api.route('/vm_monitor/<region>/<uuid>/', methods=['GET'])
def vm_monitor(region, uuid):
    return render_template('vm_metric.html', region=region, uuid=uuid)


@zt_api.route('/vm_monitor/statics/<region>/<metric>/<uuid>/<duration>/', methods=['POST'])
def vm_monitor_statics(region, metric, uuid, duration):

    logger.info('Request: get pm monitor data '
                'metric => %s '
                'system_snid => %s '
                'duration => %s ' % (metric, uuid, duration))

    try:
        result = get_vm_monitor_statics(metric, uuid, duration, region)
        return json.dumps(result)
    except:
        logger.exception('Error with get pm monitor: %s, %s, %s' % (
            metric, uuid, duration
        ))
        return json.dumps({"code": 400, "msg": "Error with get pm monitor"}), 400