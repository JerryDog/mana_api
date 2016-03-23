# -*- coding: utf-8 -*-
from __future__ import division
from mana_api.models import netflow, netrate_project, pm_servers, pm_ilo_list, \
    pm_accounts, pm_monitors, expense_virtual
from config import logging
from mana_api import db
from flask import g
import datetime
import base64
import json
import httplib
import urlparse

logger = logging.getLogger(__name__)


def http_request(url, body=None, headers=None, method="POST"):
    url_list = urlparse.urlparse(url)
    con = httplib.HTTPConnection(url_list.netloc, timeout=15)
    path = url_list.path
    if url_list.query:
        path = path + "?" + url_list.query
    logger.debug("REQ: ")
    logger.debug("url: " + str(path))
    logger.debug("header:" + str(headers))
    logger.debug("method: " + method)
    logger.debug("body: " + str(body))
    con.request(method, path, body, headers)
    res = con.getresponse()
    logger.debug("RESP: status:" + str(res.status) + ", reason:" + res.reason)
    return res


class User(object):
    def __init__(self, token=None, username=None, proj_dict=None, endpoints=None):
        # endpoints 为 serviceCatalog， 是个列表
        self.token = token
        self.username = username
        self.proj_dict = proj_dict
        self.endpoints = endpoints

    def get_endpoint(self, region, node_type):
        # 获取 api 地址
        for e in self.endpoints:
            if e["name"] == node_type:
                for i in e["endpoints"]:
                    if i["region"] == region:
                        return i["publicURL"]

    def get_regions(self):
        regions = []
        try:
            for e in self.endpoints:
                for i in e["endpoints"]:
                    if i["region"] not in regions:
                        regions.append(i["region"])
        except:
            logger.exception('Error with get_regions')
            regions = []
        return regions


def getUserProjByToken(token):
    if token == g.admin_token:
        user = User(token, 'admin', {g.admin_proj: 'admin'})
        return user

    # 获取项目字典
    headers1 = {"X-Auth-Token": token}
    url1 = urlparse.urljoin('http://' + g.uri + '/', '/v2.0/tenants')
    project_dict = {}
    try:
        res = http_request(url1, headers=headers1, method="GET")
        tenants = json.loads(res.read())
        for p in tenants["tenants"]:
            project_dict[p["id"]] = p["name"]
    except:
        logger.exception('Error with get_tenants')
        return None

    # 获取新的 token
    headers2 = {"Content-type": "application/json"}
    url2 = urlparse.urljoin('http://' + g.uri + '/', '/v2.0/tokens')
    body2 = '{"auth": {"tenantId": "%s", "token": {"id": "%s"}}}' % (project_dict.keys()[0], token)
    try:
        res = http_request(url2, body=body2, headers=headers2)
        dd = json.loads(res.read())
        apitoken = dd['access']['token']['id']
        #user_id = dd['access']['user']['id']
        username = dd['access']['user']['username']
        endpoints = dd['access']['serviceCatalog']
        user = User(apitoken, username, project_dict, endpoints)
        return user
    except Exception, e:
        logger.exception('Error with get new token')
        return None



def today():
    _today = datetime.datetime.now().strftime('%Y-%m-%d %%H:%M:%S')
    return _today


def get_monthly_flow(project_id, region=None, month=None):
    if not month and not region:
        db_query = netflow.query.filter(
            netflow.project_id == project_id
        ).all()
    elif month and not region:
        db_query = netflow.query.filter(
            netflow.project_id == project_id,
            netflow.date == month
        ).all()
    elif not month and region:
        db_query = netflow.query.filter(
            netflow.project_id == project_id,
            netflow.region == region
        ).all()
    else:
        db_query = netflow.query.filter(
            netflow.project_id == project_id,
            netflow.region == region,
            netflow.date == month,
        ).all()

    monthly_data = []
    for i in db_query:
        max_in_rate_date = i.max_in_rate_date.strftime('%Y-%m-%d %H:%M:%S') if i.max_in_rate_date else ''
        max_out_rate_date = i.max_out_rate_date.strftime('%Y-%m-%d %H:%M:%S') if i.max_out_rate_date else ''
        monthly_data.append({"date": i.date,
                             "total_in": i.total_in,
                             "total_out": i.total_out,
                             "max_in_rate": i.max_in_rate,
                             "max_in_rate_date": max_in_rate_date,
                             "max_out_rate": i.max_out_rate,
                             "max_out_rate_date": max_out_rate_date,
                             "region": i.region,
                             "project_id": i.project_id
                             })

    return {"monthly_data": monthly_data}


def get_flow(project_id, region, start, end):
    if not start and not region:
        db_query = netrate_project.query.filter(
            netrate_project.project_id == project_id
        ).all()
    elif start and not region:
        db_query = netrate_project.query.filter(
            netrate_project.project_id == project_id,
            netrate_project.begin_rate_date >= start,
            netrate_project.end_rate_date <= end
        ).all()
    elif not start and region:
        db_query = netrate_project.query.filter(
            netrate_project.project_id == project_id,
            netrate_project.region == region
        ).all()
    else:
        db_query = netrate_project.query.filter(
            netrate_project.project_id == project_id,
            netrate_project.region == region,
            netrate_project.begin_rate_date >= start,
            netrate_project.end_rate_date <= end
        ).all()

    data = []
    for i in db_query:
        data.append({
            "date": i.date.strftime('%Y-%m-%d'),
            "in_rate": i.in_rate,
            "out_rate": i.out_rate,
            "begin_rate_date": i.begin_rate_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_rate_date": i.end_rate_date.strftime('%Y-%m-%d %H:%M:%S'),
            "region": i.region,
            "project_id": i.project_id
        })
    return {"data": data}


# 返回所有物理机列表
def get_pm(tenant_id, region, f, t):
    if tenant_id and not region:
        db_query = pm_servers.query.filter(
            pm_servers.tenant_id == tenant_id
        ).all()
    elif region and not tenant_id:
        db_query = pm_servers.query.filter(
            pm_servers.region == region
        ).all()
    elif not region and not tenant_id:
        db_query = pm_servers.query.all()
    else:
        db_query = pm_servers.query.filter(
            pm_servers.tenant_id == tenant_id,
            pm_servers.region == region
        ).all()

    total_count = len(db_query)
    db_query = db_query[f:t]

    pm = []
    for i in db_query:
        status, available = get_stat_by_snid(i.system_snid)
        create_at = i.create_at.strftime('%Y-%m-%d %H:%M:%S') if i.create_at else None
        update_at = i.update_at.strftime('%Y-%m-%d %H:%M:%S') if i.update_at else None
        pm.append({
            "system_snid": i.system_snid,
            "asset_id": i.asset_id,
            "host_name": i.host_name,
            "system_type": i.system_type,
            "cpu_num": i.cpu_num,
            "mem_size": i.mem_size,
            "disk_size": i.disk_size,
            "ip": i.ip,
            "tenant_id": i.tenant_id,
            "tenant_name": base64.encodestring(i.tenant_name),
            "region": i.region,
            "manufacturer": i.manufacturer,
            "deleted": i.deleted,
            "status": status,
            "available": available,
            "create_at": create_at,
            "update_at": update_at
        })
        del status, available, create_at, update_at

    return {"code": 200, "msg": "", "total_count": total_count, "pm_servers": pm}


# 根据系统序列号获取物理机状态和可用状态
def get_stat_by_snid(snid):
    pm_ilo_obj = pm_ilo_list.query.filter_by(system_snid=snid).first()
    if not pm_ilo_obj:
        return "unavailable", 0
    available = pm_ilo_obj.available
    status = pm_ilo_obj.status
    return status, available


# 根据系统序列号获取用户名密码和 ilo_ip
def get_info_by_snid(snid):
    # 系统序列号是一个 list
    all_pm_info = []
    for s in snid.split(','):
        pm_ilo_obj = pm_ilo_list.query.filter_by(system_snid=s).first()
        if not pm_ilo_obj:
            this_pm = [None, None, None, s]
        else:
            user = pm_ilo_obj.ilo_user
            passwd = pm_ilo_obj.ilo_passwd
            ilo_ip = pm_ilo_obj.ilo_ip
            this_pm = [user, passwd, ilo_ip, s]
        all_pm_info.append(this_pm)
    return all_pm_info


# 在对物理机开关机后更新DB
def update_stat_after_act(act, snid):
    if act == "on":
        db.session.query(pm_ilo_list).filter(pm_ilo_list.system_snid == snid).update({
            pm_ilo_list.status: "starting"
        })
        db.session.commit()
    elif act == "off":
        db.session.query(pm_ilo_list).filter(pm_ilo_list.system_snid == snid).update({
            pm_ilo_list.status: "stopping"
        })
        db.session.commit()
    else:
        pass


# 根据 tenant_id 获取这个项目所有的每个月的计费
def get_pm_accounts(tenant_id):
    # 获取物理机的 dict
    db_query_pm = pm_accounts.query.filter(
        pm_accounts.tenant_id == tenant_id
    ).all()
    daily_list_pm = []
    for i in db_query_pm:
        daily_dict = {"month": i.update_at.strftime('%Y-%m'),
                      "price": i.price,
                      "region": i.region,
                      "pm_id": i.system_snid}
        daily_list_pm.append(daily_dict)
        del daily_dict
    # 将物理机每天的数据按月按区域分类
    pm_month_dict = {}
    for d in daily_list_pm:
        if pm_month_dict.has_key(d.get('month') + '#' + d.get('region')):
            pm_month_dict[d.get('month') + '#' + d.get('region')]["pm_price"] += d.get('price')
            if d.get('pm_id') not in pm_month_dict[d.get('month') + '#' + d.get('region')]["pm_ids"]:
                pm_month_dict[d.get('month') + '#' + d.get('region')]["pm_ids"].append(d.get('pm_id'))
        else:
            pm_month_dict[d.get('month') + '#' + d.get('region')] = {}
            pm_month_dict[d.get('month') + '#' + d.get('region')]["pm_ids"] = [d.get('pm_id')]
            pm_month_dict[d.get('month') + '#' + d.get('region')]["pm_price"] = d.get('price')
            pm_month_dict[d.get('month') + '#' + d.get('region')]["month"] = d.get('month')
            pm_month_dict[d.get('month') + '#' + d.get('region')]["region"] = d.get('region')

    for k in pm_month_dict:
        pm_month_dict[k]["pm_counts"] = len(pm_month_dict[k]["pm_ids"])

    # 获取虚拟机的 dict
    db_query_vm = expense_virtual.query.filter(
        expense_virtual.projectID == tenant_id
    ).all()
    daily_list_vm = []
    for i in db_query_vm:
        if i.month < 10:
            m = '0%s' % i.month
        else:
            m = i.month
        daily_dict = {"month": '%s-%s' % (i.year, m),
                      "price": i.value,
                      "region": i.locationID,
                      "vm_id": i.serverID}
        daily_list_vm.append(daily_dict)
        del daily_dict
    # 将虚拟机每天的数据按月按区域分类
    vm_month_dict = {}
    for d in daily_list_vm:
        if vm_month_dict.has_key(d.get('month') + '#' + d.get('region')):
            vm_month_dict[d.get('month') + '#' + d.get('region')]["vm_price"] += d.get('price')
            if d.get('vm_id') not in vm_month_dict[d.get('month') + '#' + d.get('region')]["vm_ids"]:
                vm_month_dict[d.get('month') + '#' + d.get('region')]["vm_ids"].append(d.get('vm_id'))
        else:
            vm_month_dict[d.get('month') + '#' + d.get('region')] = {}
            vm_month_dict[d.get('month') + '#' + d.get('region')]["vm_ids"] = [d.get('vm_id')]
            vm_month_dict[d.get('month') + '#' + d.get('region')]["vm_price"] = d.get('price')
            vm_month_dict[d.get('month') + '#' + d.get('region')]["month"] = d.get('month')
            vm_month_dict[d.get('month') + '#' + d.get('region')]["region"] = d.get('region')

    for k in vm_month_dict:
        vm_month_dict[k]["vm_counts"] = len(vm_month_dict[k]["vm_ids"])

    # 获取带宽的 dict
    flow = get_monthly_flow(tenant_id).get('monthly_data')
    if flow:
        flow_dict = {}
        for f in flow:
            flow_dict[f.get('date') + '#' + f.get('region')] = f
    else:
        flow_dict = {}

    # 将 pm_month_dict vm_month_dict flow_dict 汇总
    unit_fmt = lambda x: x / 1024 / 1024 * 8
    month_dict = {}
    for i in vm_month_dict:
        month_dict[i] = {}
        if pm_month_dict.has_key(i):
            month_dict[i]['pm_price'] = pm_month_dict[i]['pm_price']
            month_dict[i]['pm_counts'] = pm_month_dict[i]['pm_counts']
        else:
            month_dict[i]['pm_price'] = 0
            month_dict[i]['pm_counts'] = 0

        if flow_dict.has_key(i):
            month_dict[i]['max_in_rate'] = round(unit_fmt(flow_dict[i]['max_in_rate']), 2)
            month_dict[i]['max_out_rate'] = round(unit_fmt(flow_dict[i]['max_out_rate']), 2)
        else:
            month_dict[i]['max_in_rate'] = 0
            month_dict[i]['max_out_rate'] = 0
        month_dict[i]['vm_price'] = float(vm_month_dict[i]['vm_price'])  # decimal转float
        month_dict[i]['vm_counts'] = vm_month_dict[i]['vm_counts']
        month_dict[i]['month'] = vm_month_dict[i]['month']
        month_dict[i]['region'] = vm_month_dict[i]['region']

    # 补上物理机有的虚拟机没有的 key
    for p in pm_month_dict:
        if not month_dict.has_key(p):
            month_dict[p] = {}
            month_dict[p]['month'] = pm_month_dict[p]['month']
            month_dict[p]['region'] = pm_month_dict[p]['region']
            month_dict[p]['pm_price'] = pm_month_dict[p]['pm_price']
            month_dict[p]['pm_counts'] = pm_month_dict[p]['pm_counts']
            month_dict[p]['vm_price'] = 0
            month_dict[p]['vm_counts'] = 0
            if flow_dict.has_key(p):
                month_dict[p]['max_in_rate'] = round(unit_fmt(flow_dict[p]['max_in_rate']), 2)
                month_dict[p]['max_out_rate'] = round(unit_fmt(flow_dict[p]['max_out_rate']), 2)
            else:
                month_dict[p]['max_in_rate'] = 0
                month_dict[p]['max_out_rate'] = 0

    month_list = []
    for key in month_dict:
        month_list.append(month_dict[key])
    month_list.sort(key=lambda todayListSort: todayListSort['month'])
    month_list.reverse()

    # 给2比杉杉返回一个连续月份的 list，方便她循环
    try:
        nearest_month = month_list[0]["month"]
        months = [nearest_month]
        farthest_month = month_list[-1:][0]["month"]
        delta = datetime.timedelta(days=10)
        cursor_month = datetime.datetime.strptime(nearest_month + '-01', '%Y-%m-%d')
        while cursor_month.strftime('%Y-%m-%d')[:7] != farthest_month:
            cursor_month -= delta
            if cursor_month.strftime('%Y-%m-%d')[:7] not in months:
                months.append(cursor_month.strftime('%Y-%m-%d')[:7])
    except:
        logger.exception('Error with get months list')
        months = []
    return {"accounts": month_list, "code": 200, "msg": "", "months": months}


# 返回一个月的第一天和最后一天的时间
def get_time(month):
    import calendar
    y, m = month.split('-')
    week, last_day = calendar.monthrange(int(y), int(m))
    start = '%s-01 00:00:00' % month
    end = '%s-%s 23:59:59' % (month, last_day)
    return start, end


# 根据 tenant_id, region, month 列出这个月这个区域详细的每台机器的花费
def get_pm_accounts_detail(tenant_id, region, month):
    start, end = get_time(month)
    db_query = pm_accounts.query.filter(
        pm_accounts.tenant_id == tenant_id,
        pm_accounts.region == region,
        pm_accounts.update_at >= start,
        pm_accounts.update_at <= end
    ).all()
    if not db_query:
        return {"accounts_detail": []}

    pm_dict = {}
    for d in db_query:
        if pm_dict.has_key(d.system_snid):
            pm_dict[d.system_snid]['price'] += d.price
        else:
            pm_dict[d.system_snid] = {}
            pm_dict[d.system_snid]['system_snid'] = d.system_snid
            pm_dict[d.system_snid]['price'] = d.price

    month_pm_list = []
    for key in pm_dict:
        month_pm_list.append(pm_dict[key])

    return {"accounts_detail": month_pm_list}


# 获取物理机监控项的监控数据
# 先定义一个类来处理DB里的info字段的json字符串
class Storage(dict):
    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]


def fmt_info(info):
    info_to_json = json.loads(info)
    s = Storage(info_to_json)
    s.network = [Storage(i) for i in s.network]
    return s


def get_pm_monitor_statics(metric, system_snid, duration):
    now = datetime.datetime.now()

    DUR = {
        '3h': (now - datetime.timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
        '1d': (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
        '7d': (now - datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),
        '30d': (now - datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    }

    UNIT = {
        'cpu_util': '%',
        'disk_read': 'B/s',
        'disk_write': 'B/s'
    }
    db_query = pm_monitors.query.filter(
        pm_monitors.system_snid == system_snid,
        pm_monitors.update_at >= DUR[duration]
    ).order_by(pm_monitors.update_at).all()

    if not db_query:
        return [{"data": [], "name": ""}]

    data_list = []
    if metric == 'cpu_util' or metric == 'disk_read' or metric == 'disk_write':
        for d in db_query:
            info = fmt_info(d.info)
            point_dict = {
                "min": info.__getattr__(metric),
                "max": info.__getattr__(metric),
                "period_start": d.update_at.strftime('%Y-%m-%dT%H:%M:%S'),
                "avg": info.__getattr__(metric),
                "sum": info.__getattr__(metric),
                "unit": UNIT[metric]
            }
            data_list.append(point_dict)
        return [{"data": data_list, "name": "%s" % system_snid}]

    if metric == 'network_in' or metric == 'network_out':
        all_network_dict = {}
        # key 为 IP
        for d in db_query:
            info = fmt_info(d.info)
            for i in info.network:
                if all_network_dict.has_key(i.ip_addr):
                    all_network_dict[i.ip_addr].append({
                        "min": i.__getattr__(metric),
                        "max": i.__getattr__(metric),
                        "period_start": d.update_at.strftime('%Y-%m-%dT%H:%M:%S'),
                        "avg": i.__getattr__(metric),
                        "sum": i.__getattr__(metric),
                        "unit": "B/s"
                    })
                else:
                    all_network_dict[i.ip_addr] = [{
                        "min": i.__getattr__(metric),
                        "max": i.__getattr__(metric),
                        "period_start": d.update_at.strftime('%Y-%m-%dT%H:%M:%S'),
                        "avg": i.__getattr__(metric),
                        "sum": i.__getattr__(metric),
                        "unit": "B/s"
                    }]

        result = []
        for ip in all_network_dict:
            result.append({
                "data": all_network_dict[ip],
                "name": ip
            })
        return result
