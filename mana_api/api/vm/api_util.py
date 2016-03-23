# -*- coding: utf-8 -*-
import urlparse
import json
import base64
import random
import string
from flask import g
from mana_api.config import C2_CHANGE_VIR_WINDOWS_PWD_SCRIPT
from mana_api.config import logging
from mana_api.apiUtil import http_request

logger = logging.getLogger(__name__)


# 自定义异常
class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


# 由星云过来的 token 再去获取一个有 endpoint 的token
def get_new_token(tenant_id):
    headers = {"Content-type": "application/json"}
    url = urlparse.urljoin('http://' + g.uri + '/', '/v2.0/tokens')
    body = '{"auth": {"tenantId": "%s", "token": {"id": "%s"}}}' % (tenant_id, g.token)
    try:
        res = http_request(url, body=body, headers=headers)
        dd = json.loads(res.read())
        apitoken = dd['access']['token']['id']
        return apitoken
    except Exception, e:
        return 'ConnError, %s' % e


# 获取项目列表
def get_tenants():
    headers = {"X-Auth-Token": g.token}
    url = urlparse.urljoin('http://' + g.uri + '/', '/v2.0/tenants')
    try:
        res = http_request(url, headers=headers, method="GET")
        dd = json.loads(res.read())
        return dd
    except Exception, e:
        logger.exception('Error with get_tenants')
        return None


# 虚拟机状态统一
STATUS = {
    "ACTIVE": "active",
    "BUILD": "building",
    "DELETED": "deleted",
    "ERROR": "error",
    "HARD_REBOOT": "initialized",
    "MIGRATING": "initialized",
    "PASSWORD": "initialized",
    "PAUSED": "paused",
    "REBOOT": "initialized",
    "REBUILD": "building",
    "RESCUE": "rescued",
    "RESIZE": "resized",
    "REVERT_RESIZE": "resized",
    "VERIFY_RESIZE": "resized",
    "SHELVED": "paused",
    "SHELVED_OFFLOADED": "paused",
    "SHUTOFF": "stopped",
    "SOFT_DELETED": "soft-delete",
    "SUSPENDED": "suspend",
    "UNKNOWN": "error"
}


# 更改 windows 密码
def chg_win_pwd(uuid, instance_name, pwd, host_ip, region):
    pwd_str = base64.urlsafe_b64decode(pwd.encode())
    result, user_data = update_user_data(uuid, pwd_str, region)
    if not result:
        LOG = "Failed %s" % user_data
        return False, LOG
    script_name = C2_CHANGE_VIR_WINDOWS_PWD_SCRIPT
    exe = "%s %s %s" %(script_name, instance_name, user_data)
    print "runScript--->host_ip:%s,exe:%s" % (host_ip, exe)
    try:
        LOG=c2_ssh.conn(host_ip,exe)
    except Exception,ex:
        print Exception, ":", ex
        LOG = "SSH exception:%s" % str(ex)
        return False, LOG
    return True, LOG

def update_user_data(uuid, pwd, region):
    data_base64 = InstanceManager().getUserdata(NOVA_DB(region), uuid)
    if data_base64 == 'NULL':
        LOG = "can not get userdata by uuid"
        return False, LOG
    #sudo: can't use yaml dump to reserve load file,so create new!!!
    #if data_base64 == 'NULL':
    #    data_new_base64 = createNewUserdata(pwd)
    #else:
    #    data_str = base64.base64.urlsafe_b64encode(data_base64)
    #    try:
    #        data_yaml = yaml.load(data_str)
    #    except Exception,ex:
    #        LOG = "can not analyze userdata with a yaml file by uuid"
    #        return False, LOG
    #    if data_yaml.has_key('chpasswd'):
    #        data_new_base64 = setPwdToUserdata(data_yaml, pwd)
    #    else:
    #        data_new_base64_ = addPwdToUserdata(data_yaml, pwd)
    data_new_base64 = create_new_user_data(pwd)
    InstanceManager().setUserdata(NOVA_DB(region), uuid, data_new_base64, region)
    return True, data_new_base64

def create_new_user_data(pwd):
    serialNum = "".join(random.sample(string.ascii_letters + string.digits, 8))
    sample = """
        #cloud-config
        chpasswd:
            list: |
                Administrator: %s
            SerialNum: %s
        """
    data = sample % (pwd, serialNum)
    data_base64 = base64.urlsafe_b64encode(data)
    return data_base64