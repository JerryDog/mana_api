# -*- coding: utf-8 -*-
from flask import g
import time
import urllib
import json
from mana_api.apiUtil import http_request, getUserProjByToken
from mana_api.api.vm.api_util import MyError
from compute import InstanceManager


PERIOD={
    "3h":300,
    "1d":900,
    "7d":3600,
    "30d":21600,
}

DUR={
    "3h":3*3600,
    "1d":24*3600,
    "7d":7*24*3600,
    "30d":30*24*3600,
}


def msecs2utc(msecs):
    timeArray = time.localtime(msecs)
    otherStyleTime = time.strftime("%Y-%m-%dT%H:%M:%SZ", timeArray)
    return otherStyleTime


# 获取虚拟机监控数据
def statistics(endpoint, metric, duration, res_id):
    headers = {"X-Auth-Token": g.token, "Content-type":"application/json" }
    now=int(time.time())
    duration_sec = DUR[duration]
    period_start = msecs2utc(now-8*3600-duration_sec)
    data1={
        "Meteric": metric,
        "RES_ID": res_id,
        "period": PERIOD[duration],
        "period_start":urllib.quote(period_start,''),
    }
    url = endpoint + "/v2/meters/%(Meteric)s/statistics?q.field=resource_id&q.field=timestamp&q.op=eq&" \
        "q.op=gt&q.type=&q.type=&q.value=%(RES_ID)s&q.value=%(period_start)s&period=%(period)s" % data1
    res = http_request(url, headers=headers, method='GET')
    if res.status == 500:
        raise MyError('Error with get vm statistics, reason: %s' % res.read())
    dd = json.loads(res.read())
    return dd


def get_vm_monitor_statics(metric, uuid, duration, region):
    user = getUserProjByToken(g.admin_proj)
    endpoint = user.get_endpoint(region, 'ceilometer')
    mana = InstanceManager(token=user.token, endpoint=user.get_endpoint(region, 'nova'))
    RTN=[]
    if "network" in metric:
        pass
        #ports=NetworkFlowManager().getNetInfoByUUID(UUID,NEUTRON_DB(region))
        #for port in ports:
            #obj = {}
            #obj["name"] = port["ip_address"]
            #ifaceId = ifaceID(UUID,port["id"],int(vir.id))
            #print "ifaceid:",ifaceId
            #obj["data"] = statistics(region, metric.replace("_", "."), duration, ifaceId)
            #RTN.append(obj)
    elif "disk" in metric:
        obj={}
        obj["name"] = mana.nova_show(uuid).name
        obj["data"] = statistics(endpoint, metric.replace("_", "."), duration, uuid)
        RTN.append(obj)
    elif "cpu_util" == metric:
        obj={}
        obj["name"] = mana.nova_show(uuid).name
        obj["data"] = statistics(endpoint, metric, duration, uuid)
        RTN.append(obj)
    return RTN