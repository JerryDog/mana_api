# coding: utf-8
import httplib
import urlparse
import json
import re
from mana_api.config import AUTH_PUBLIC_URI
from mana_api.config import logging

logger = logging.getLogger(__name__)


def http_request(url, body=None, headers=None, method="POST"):
    url_list = urlparse.urlparse(url)
    con = httplib.HTTPConnection(url_list.netloc, timeout=15)
    path = url_list.path
    if url_list.query:
        path = path + "?" + url_list.query
    con.request(method, path, body, headers)
    res = con.getresponse()
    return res


# 由星云过来的 token 再去获取一个有 endpoint 的token
def get_new_token(token, tenant_id):
    headers = {"Content-type": "application/json"}
    url = urlparse.urljoin('http://' + AUTH_PUBLIC_URI + '/', '/v2.0/tokens')
    body = '{"auth": {"tenantId": "%s", "token": {"id": "%s"}}}' % (tenant_id, token)
    try:
        res = http_request(url, body=body, headers=headers)
        dd = json.loads(res.read())
        apitoken = dd['access']['token']['id']
        return apitoken
    except Exception, e:
        return 'ConnError, %s' % e


# endpoint 为 api 访问的地址，以 region 过滤出来的
def nova_list(token, endpoint, f, t):
    headers = {"X-Auth-Token": '%s' % token, "Content-type": "application/json"}
    url = endpoint + '/servers/detail'
    res = http_request(url, headers=headers, method='GET')
    dd = json.loads(res.read())
    logger.info('scloudm response: %s' % dd)
    vm_servers = []
    for item in dd["servers"]:
        lan_ip, wan_ip = addresses_to_wan_lan(item["addresses"])
        flavor = item.get('flavor', None)
        if flavor:
            flavor_id = flavor.get('id', None)
        else:
            flavor_id = None
        disk, mem, cpu = get_flavor(token, endpoint, flavor_id)
        instance = {
            "instance_name": item["name"],
            "instance_id": item["id"],
            "cpu_num": cpu,
            "mem_size": mem,
            "disk_size": disk,
            "lan_ip_set": lan_ip,
            "wan_ip_set": wan_ip,
            "status": item["status"].lower(),
            "create_at": item["created"].replace('T', ' ').replace('Z', ''),
            "update_at": item["updated"].replace('T', ' ').replace('Z', '')
        }
        vm_servers.append(instance)
    return {"code": 200, "msg": "", "vm_servers": vm_servers[f:t]}


# 获取主机类型明细
def get_flavor(token, endpoint, flavor_id):
    if not flavor_id:
        return None, None, None
    headers = {"X-Auth-Token": '%s' % token, "Content-type": "application/json"}
    url = endpoint + '/flavors/​​' + flavor_id
    res = http_request(url, headers=headers, method='GET')
    dd = json.loads(res.read())
    disk = dd["flavor"]["disk"]
    mem = dd["flavor"]["ram"]
    cpu = dd["flavor"]["vcpus"]
    return disk, mem, cpu


# 区分外网 ip 和内网 ip, 返回列表形式
def addresses_to_wan_lan(addresses):
    '''
    u'addresses': {
                u'test': [
                    {
                        u'OS-EXT-IPS-MAC: mac_addr': u'fa: 16: 3e: 13: 69: 95',
                        u'version': 4,
                        u'addr': u'10.240.2.26',
                        u'OS-EXT-IPS: type': u'fixed'
                    }
                ],
                u'ZR-WT-604': [
                    {
                        u'OS-EXT-IPS-MAC: mac_addr': u'fa: 16: 3e: be: c6: 11',
                        u'version': 4,
                        u'addr': u'210.51.35.93',
                        u'OS-EXT-IPS: type': u'fixed'
                    }
                ]
            }
    :param addresses:
    :return:
    '''
    if not addresses:
        return None, None

    lan_ip = {}
    wan_ip = {}
    for key in addresses:
        lan_ip[key] = []
        wan_ip[key] = []
        for i in addresses[key]:
            ip = i.get('addr', None)
            if re.match('10\.', ip) or re.match('172\.', ip):
                lan_ip[key].append(ip)
            else:
                wan_ip[key].append(ip)
    for k, v in lan_ip.items():
        if not v:
            lan_ip.pop(k)
    for k, v in wan_ip.items():
        if not v:
            wan_ip.pop(k)
    return lan_ip, wan_ip