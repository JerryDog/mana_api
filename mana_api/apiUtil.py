# -*- coding: utf-8 -*-
from __future__ import division
from flask import g
from flask import jsonify
from functools import wraps
from mana_api import db
from mana_api.models import netflow, netrate_project, pm_relation, pm_variable, pm_firmware, \
    pm_expense, pm_monitors, expense_virtual, pm_contact_list, pm_orders
from config import logging
import datetime
import json
import httplib
import urlparse
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)

# 自定义异常
class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Resp(object):
    def __init__(self, status, msg):
        self.status = status
        self.reason = msg
        self.msg = msg

    def read(self):
        return self.msg

def http_request(url, body=None, headers=None, method="POST"):
    logger.debug("REQ: ")
    logger.debug("url: " + str(url))
    url_list = urlparse.urlparse(url)
    try:
        con = httplib.HTTPConnection(url_list.netloc, timeout=15)
        path = url_list.path
        if url_list.query:
            path = path + "?" + url_list.query

        logger.debug("header:" + str(headers))
        logger.debug("method: " + method)
        logger.debug("body: " + str(body))
        logger.debug("")
        con.request(method, path, body, headers)
        res = con.getresponse()
    except Exception, e:
        res = Resp(500, str(e))
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

    def get_tenants(self):
        tenants = []
        for k,v in self.proj_dict.items():
            tenants.append({"id": k, "name": v})
        return tenants

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


def getUserProjByToken(tenant_id=None):
    # 获取 user 对象，必须要指定 tenant_id 是为了拿正确的 endpoint
    if g.token == g.admin_token:
        user = User(g.token, 'admin', {g.admin_proj: 'admin'})
        return user

    # 获取项目字典
    headers1 = {"X-Auth-Token": g.token}
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
    if not tenant_id:
        tenant_id = project_dict.keys()[0]
    body2 = '{"auth": {"tenantId": "%s", "token": {"id": "%s"}}}' % (tenant_id, g.token)
    try:
        resp = http_request(url2, body=body2, headers=headers2)
        dd = json.loads(resp.read())
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
    select_by_project = pm_relation.query.filter(
        pm_relation.tenant_id == tenant_id
    ).all()
    if not select_by_project:
        return {"code": 200, "msg": "", "total_count": 0, "pm_servers": []}
    db_query = []
    for i in select_by_project:
        match_obj = pm_variable.query.filter(
            pm_variable.snid == i.snid,
            pm_variable.region == region
        ).first()
        if match_obj:
            db_query.append(match_obj)

    total_count = len(db_query)
    db_query = db_query[f:t]

    pm = []
    for i in db_query:
        asset_id, manufacturer, state, create_at = get_stat_by_snid(i.snid)
        update_at = i.update_at.strftime('%Y-%m-%d %H:%M:%S') if i.update_at else None
        pm.append({
            "snid": i.snid,
            "host_name": i.host_name,
            "os_type": i.os_type,
            "region": i.region,
            "status": i.status,
            "cpu_num": i.cpu_num,
            "mem_size": i.mem_size,
            "disk_size": i.disk_size,
            "ip": i.ip,
            "ilo_state": i.ilo_state,
            "state": state,
            "asset_id": asset_id,
            "tenant_id": tenant_id,
            "manufacturer": manufacturer,
            "create_at": create_at,
            "update_at": update_at
        })
        del asset_id, manufacturer, state, create_at

    return {"code": 200, "msg": "", "total_count": total_count, "pm_servers": pm}


# 根据系统序列号获取物理机状态和可用状态
def get_stat_by_snid(snid):
    pm_ilo_obj = pm_firmware.query.filter_by(snid=snid).first()
    if not pm_ilo_obj:
        return None, None, None, None
    asset_id = pm_ilo_obj.asset_id
    manufacturer = pm_ilo_obj.manufacturer
    state = pm_ilo_obj.state
    create_at = pm_ilo_obj.create_at.strftime('%Y-%m-%d %H:%M:%S') if pm_ilo_obj.create_at else None
    return asset_id, manufacturer, state, create_at


# 根据系统序列号获取用户名密码和 ilo_ip
def get_info_by_snid(snids):
    # 系统序列号是一个 list
    all_pm_info = []
    for s in snids.split(','):
        pm_ilo_obj = pm_variable.query.filter_by(snid=s).first()
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
        db.session.query(pm_variable).filter(pm_variable.snid == snid).update({
            pm_variable.status: "starting"
        })
        db.session.commit()
    elif act == "off":
        db.session.query(pm_variable).filter(pm_variable.system_snid == snid).update({
            pm_variable.status: "stopping"
        })
        db.session.commit()
    else:
        pass


# 根据 tenant_id 获取这个项目所有的每个月的计费
def get_pm_accounts(tenant_id):
    # 获取物理机的 dict
    db_query_pm = pm_expense.query.filter(
        pm_expense.tenant_id == tenant_id
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
    db_query = pm_expense.query.filter(
        pm_expense.tenant_id == tenant_id,
        pm_expense.region == region,
        pm_expense.update_at >= start,
        pm_expense.update_at <= end
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

# 新增物理机
def add_pm(data):
    # snid,Assetid,hostname,os_type,ip,tenant_id,region,ilo,remark,Manufacturer,cpu_num,mem_size,disk_size
    snid = data.get('snid', None)
    asset_id = data.get('asset_id', None)
    host_name = data.get('host_name', None)
    os_type = data.get('os_type', None)
    ip = data.get('ip', None)
    region = data.get('region', None)
    ilo_ip = data.get('ilo_ip', None)
    ilo_user = data.get('ilo_user', None)
    ilo_passwd = data.get('ilo_passwd', None)
    ilo_state = data.get('ilo_state', 0)
    remark = data.get('remark', None)
    manufacturer = data.get('manufacturer', None)
    cpu_num = data.get('cpu_num', None)
    mem_size = data.get('mem_size', None)
    disk_size = data.get('disk_size', None)

    if not snid or not asset_id  or not region:
        raise MyError('sind|asset_id|region required')

    check_snid_asset_id(snid, asset_id)

    # 通过了所有条件判断，开始向 DB 录入数据
    # pm_firmware 录入
    now = datetime.datetime.now()
    new_pm_firmware = pm_firmware(snid=snid, asset_id=asset_id, manufacturer=manufacturer,
                                  create_at=now)
    db.session.add(new_pm_firmware)
    db.session.commit()

    # pm_variable 录入
    new_pm_variable = pm_variable(snid=snid, host_name=host_name, os_type=os_type,
                                  region=region, cpu_num=cpu_num, mem_size=mem_size,
                                  disk_size=disk_size, ip=ip, ilo_ip=ilo_ip,ilo_state=ilo_state, remark=remark)
    if ilo_user:
        new_pm_firmware.ilo_user = ilo_user
    if ilo_passwd:
        new_pm_firmware.ilo_passwd = ilo_passwd
    db.session.add(new_pm_variable)
    db.session.commit()

    # pm_relation 录入
    new_pm_relation = pm_relation(snid=snid, tenant_id=g.admin_proj)
    db.session.add(new_pm_relation)
    db.session.commit()

    return {"code": 200, "msg": "add success"}


# 查询 snid 与 asset_id 是否有重复
def check_snid_asset_id(snid, asset_id):
    check_snid = pm_firmware.query.filter(
        pm_firmware.snid == snid
    ).first()

    check_asset_id = pm_firmware.query.filter(
        pm_firmware.asset_id == asset_id
    ).first()

    if check_snid:
        raise MyError('snid already exist')
    if check_asset_id:
        raise MyError('asset_id already exist')


# 获取单台物理机信息
def get_single_pm(snid):
    asset_id, manufacturer, state, create_at = get_stat_by_snid(snid)
    i = pm_variable.query.filter(
        pm_variable.snid == snid
    ).first()
    if not i:
        return {"code": 200, "msg": "", "pm_server": []}
    update_at = i.update_at.strftime('%Y-%m-%d %H:%M:%S') if i.update_at else None
    j = pm_relation.query.filter(
        pm_relation.snid == snid
    ).first()
    tenant_id = j.tenant_id if j else None
    pm_server = {
            "snid": i.snid,
            "host_name": i.host_name,
            "os_type": i.os_type,
            "region": i.region,
            "status": i.status,
            "cpu_num": i.cpu_num,
            "mem_size": i.mem_size,
            "disk_size": i.disk_size,
            "ip": i.ip,
            "ilo_state": i.ilo_state,
            "state": state,
            "asset_id": asset_id,
            "tenant_id": tenant_id,
            "manufacturer": manufacturer,
            "create_at": create_at,
            "update_at": update_at
    }
    return {"code": 200, "msg": "", "pm_server": pm_server}


# 修改物理机
def pm_update(snid, data):
    deny_list = ['tenant_id', 'state', 'manufacturer', 'create_at', 'snid', 'asset_id']
    for i in deny_list:
        try:
            data.pop(i)
        except KeyError:
            continue
    db.session.query(pm_variable).filter(pm_variable.snid == snid).update(data)
    db.session.commit()
    return {"code": 200, "msg": "update success"}


# 新增项目下联系人(单个新增)
def add_contact_single(tenant_id, data):
    email = data.get('email', None)
    phone = data.get('phone', None)
    name = data.get('name', None)
    new_contact = pm_contact_list(tenant_id=tenant_id, email=email, phone=phone, name=name)
    db.session.add(new_contact)
    db.session.commit()
    return {"code": 200, "msg": "add success"}


# 删除项目下联系人列表
def delete_contact_list(ids):
    for i in ids.split(','):
        me = pm_contact_list.query.filter(
            pm_contact_list.id == i
        ).first()
        db.session.delete(me)
    db.session.commit()
    return {"code": 200, "msg": "delete success"}

# 获取项目下联系人列表
def get_contact_list(tenant_id):
    db_query = pm_contact_list.query.filter(
        pm_contact_list.tenant_id == tenant_id
    ).all()
    contact_list = []
    for i in db_query:
        contact_list.append({
            "id": i.id,
            "tenant_id": i.tenant_id,
            "email": i.email,
            "phone": i.phone,
            "name": i.name
        })

    return {"code": 200, "msg": "", "contact_list": contact_list}


# 实体机退库
def _pm_refund(data):
    snids = data.get('snids', None)
    if not snids:
        raise MyError('sind required')

    code = 200
    msg = "all success"
    detail = []
    for s in snids.split(','):
        pm_obj = pm_variable.query.filter(
            pm_variable.snid == s
        ).first()
        if not pm_obj:
            code = 404
            msg = "pm server not found"
            detail.append({"code": code, "msg": msg, "snid": s})
            continue
        if pm_obj.status != "stop":
            code = 403
            msg = "please stop pm server first"
            detail.append({"code": code, "msg": msg, "snid": s})
            continue
        db.session.query(pm_relation).filter(pm_relation.snid == s).update({
            pm_relation.tenant_id: g.admin_proj
        })
        detail.append({"code": 200, "msg": "success", "snid": s})
    db.session.commit()
    return {"code": code, "msg": msg, "detail": detail}

# 定义只有管理员才可以访问的api
def admin_required(func):
    @wraps(func)
    def is_admin(*args, **kwargs):
        if g.username == 'admin':
            ret = func(*args, **kwargs)
        else:
            ret = jsonify({"code": 403, "msg": "Only admin have access permissions"}), 403
        return ret
    return is_admin


############# 以下为物理机订单部分 #################
def sendmail(subject, mailto, msg):
    import smtplib
    from email.mime.text import MIMEText
    sender = 'pm_order@ztgame.com'
    #邮件信息
    try:
        _msg =MIMEText(msg)
        _msg['Subject'] = subject
        _msg['to'] = ';'.join(mailto)
        _msg['From'] = sender

        #连接发送服务器
        smtp = smtplib.SMTP('localhost')
        #发送
        smtp.sendmail(sender,mailto, _msg.as_string())
        smtp.quit()
        return 'send mail success'
    except:
        logger.exception('Error with sendmail, mailto: %s; msg:%s' % (mailto, msg))
        return 'send mail failed'


# 获取订单
def _get_orders(tenant_id, order_type):
    if order_type == '0':
        # 未完成订单
        msg = 'unfinished orders'
        db_query = pm_orders.query.filter(
            pm_orders.dest_project == tenant_id,
            pm_orders.state == 'unfinished'
        ).all()
    if order_type == '1':
        # 已完成订单
        msg = 'finished orders'
        db_query = pm_orders.query.filter(
            pm_orders.dest_project == tenant_id,
            pm_orders.state == 'finished'
        ).all()
    if order_type == '2':
        # 我拒绝的订单
        msg = 'refused orders'
        db_query = pm_orders.query.filter(
            pm_orders.dest_project == tenant_id,
            pm_orders.state == 'refused'
        ).all()
    if order_type == '3':
        # 我发起的订单
        msg = 'new order by me'
        db_query = pm_orders.query.filter(
            pm_orders.resource_project == tenant_id
        ).all()
    if order_type == '4':
        # 所有订单
        msg = 'all orders'
        db_query1 = pm_orders.query.filter(
            pm_orders.resource_project == tenant_id
        ).all()
        db_query2 = pm_orders.query.filter(
            pm_orders.dest_project == tenant_id
        ).all()
        db_query = db_query1 + db_query2
    total_count = len(db_query)
    orders = []
    for i in db_query:
        create_at = pm_orders.create_at.strftime('%Y-%m-%d %H:%M:%S') if pm_orders.create_at else None
        update_at = pm_orders.update_at.strftime('%Y-%m-%d %H:%M:%S') if pm_orders.update_at else None
        orders.append({
            "id": i.id,
            "snids": i.snids,
            "resource_project": i.resource_project,
            "dest_project": i.dest_project,
            "user": i.user,
            "state": i.state,
            "warnning_times": i.warnning_times,
            "create_at": create_at,
            "update_at": update_at
        })
    return {"code": 200, "msg": msg, "total_count": total_count,  "orders": orders}


# 新增订单
def _add_order(tenant_id, data):
    snids = data.get('snids', None)
    dest_project = data.get('dest_project', None)

    # 获取收件人
    contact_obj = pm_contact_list.query.filter(
        pm_contact_list.tenant_id == dest_project
    ).all()
    contact_list = [i.email for i in contact_obj]
    mailto = ','.join(contact_list)

    if not snids or not dest_project:
        raise MyError('snids|dest_project required')

    # 更新物理机状态为 changing
    for i in snids.split(','):
        pm_obj = pm_firmware.query.filter(
            pm_firmware.snid == i
        ).first()
        if not pm_obj:
            raise MyError('pm server %s does not exist' % i)
        if pm_obj.state == 'changing':
            raise MyError('pm server %s is changing' % i)
        db.session.query(pm_firmware).filter(pm_firmware.snid == i).update({
            pm_firmware.state: "changing"
        })

    # order表插入新的订单
    now = datetime.datetime.now()
    new_order = pm_orders(snids=snids, resource_project=tenant_id,
                          dest_project=dest_project, user=g.username,
                          create_at=now)
    db.session.add(new_order)
    db.session.commit()

    # 发通知邮件
    subject = '物理机项目变更通知'
    msg = """
    物理机编号：%s, \n
    请求用户：%s, \n
    请登陆云上云系统接收或拒绝该订单
    """ % (snids, g.username)
    send_result = sendmail(subject, mailto, msg.decode('utf-8'))
    return {"code": 200, "msg": "add success", "sendmail": send_result}


# 用户接收或者拒绝订单
def _process_orders(tenant_id, data):
    order_ids = data.get('order_ids', None)
    accept = data.get('accept', 0)
    if not order_ids or not accept:
        raise MyError('order_ids|accept required')

    _state = 'finished' if accept == 1 else 'refused'

    # 开始处理订单
    detail = []
    for i in order_ids.split(','):
        order_obj = pm_orders.query.filter(
            pm_orders.dest_project == tenant_id,
            pm_orders.id == i,
            pm_orders.state == 'unfinished'
        ).first()
        if not order_obj:
            detail.append({
                "code": 404,
                "msg": "order not found",
                "order_id": i,
                "sendmail": "do-nothing"
            })
            continue
        try:
            for s in order_obj.snids.split(','):
                db.session.query(pm_firmware).filter(pm_firmware.snid == s).update({
                    pm_firmware.state: 'active'
                })
                db.session.query(pm_relation).filter(pm_relation.snid == s).update({
                    pm_relation.tenant_id: tenant_id
                })
            db.session.query(pm_orders).filter(pm_orders.id == i).update({
                    pm_orders.state: _state
            })
            db.session.commit()

            # 获取收件人,并发送邮件
            contact_obj = pm_contact_list.query.filter(
                pm_contact_list.tenant_id == order_obj.resource_project
            ).all()
            contact_list = [i.email for i in contact_obj]
            mailto = ','.join(contact_list)
            subject = '物理机转移订单确认通知'.decode('utf-8') if accept == 1 \
                else '物理机转移订单拒收通知'.decode('utf-8')
            msg = """
            订单号：%s,
            订单状态：%s
            """ % (i, _state)
            mail_result = sendmail(subject, mailto, msg.decode('utf-8'))

            detail.append({
                "code": 200,
                "msg": "success",
                "order_id": i,
                "sendmail": mail_result
            })
        except Exception, e:
            logger.exception('Error with order processing, order_id: %s' % i)
            detail.append({
                "code": 400,
                "msg": "%s" % e,
                "order_id": i,
                "sendmail": "do-nothing"
            })

    return {"code": 200, "msg": "Order processing success", "detail": detail}