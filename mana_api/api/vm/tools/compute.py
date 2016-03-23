# -*- coding: utf-8 -*-
import json
import re
from mana_api.api.vm.api_util import MyError
from mana_api.config import logging
from mana_api.apiUtil import http_request

logger = logging.getLogger(__name__)


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

    lan_ip = []
    wan_ip = []
    for key in addresses:
        for i in addresses[key]:
            ip = i.get('addr', None)
            if re.match('10\.', ip) or re.match('172\.', ip):
                lan_ip.append(ip)
            else:
                wan_ip.append(ip)

    lan_ip_str = ','.join(lan_ip)
    wan_ip_str = ','.join(wan_ip)
    return lan_ip_str, wan_ip_str


class Base(object):
    def __init__(self, token=None, endpoint=None):
        self.token = token
        self.endpoint = endpoint
        if not self.endpoint:
            raise MyError('无效的区域'.decode('utf-8'))
        self.headers = {"X-Auth-Token": '%s' % self.token, "Content-type": "application/json"}


class Instance(Base):
    def __init__(self, info, **kwargs):
        super(Instance, self).__init__(**kwargs)
        self.info = info
        self.name = info['name']
        self.id = info['id']
        self.status = info['status']
        self.create_at = info['created'].replace('T', ' ').replace('Z', '')
        self.update_at = info["updated"].replace('T', ' ').replace('Z', '')
        flavor = info.get('flavor', None)
        self.flavor_id = flavor.get('id', None) if flavor else None
        self.disk, self.mem, self.cpu = self.get_flavor()
        self.lan_ip, self.wan_ip = addresses_to_wan_lan(info['addresses'])

    # 获取主机类型明细
    def get_flavor(self):
        if not self.flavor_id:
            return None, None, None
        url = self.endpoint + '/flavors' + '/' + self.flavor_id
        res = http_request(url, headers=self.headers, method='GET')
        dd = json.loads(res.read())
        disk = dd["flavor"]["disk"]
        mem = int(dd["flavor"]["ram"]/1024)
        cpu = dd["flavor"]["vcpus"]
        return disk, mem, cpu


class InstanceManager(Base):
    def __init__(self, **kwargs):
        # 这个 token 是重新获取的新 token
        super(InstanceManager, self).__init__(**kwargs)

    def nova_list(self, f, t):
        url = self.endpoint + '/servers/detail'
        res = http_request(url, headers=self.headers, method='GET')
        dd = json.loads(res.read())
        logger.info('scloudm response: %s' % dd)
        servers_list = dd["servers"]
        instances = [Instance(i, token=self.token, endpoint=self.endpoint) for i in servers_list[f:t]]
        return instances

    # 获取单台主机信息
    def nova_show(self, uuid):
        url = self.endpoint + '/servers/' + uuid
        res = http_request(url, headers=self.headers, method='GET')
        dd = json.loads(res.read())
        logger.info('scloudm response: %s' % dd)
        instance = Instance(dd, token=self.token, endpoint=self.endpoint)
        return instance


    # 获取主机类型明细
    def get_flavor(self, flavor_id):
        if not flavor_id:
            return None, None, None
        url = self.endpoint + '/flavors' + '/' + flavor_id
        res = http_request(url, headers=self.headers, method='GET')
        dd = json.loads(res.read())
        disk = dd["flavor"]["disk"]
        mem = int(dd["flavor"]["ram"]/1024)
        cpu = dd["flavor"]["vcpus"]
        return disk, mem, cpu