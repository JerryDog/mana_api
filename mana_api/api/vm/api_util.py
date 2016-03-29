# -*- coding: utf-8 -*-
import urlparse
import json
import base64
import random
import string
from mana_api.config import C2_CHANGE_VIR_WINDOWS_PWD_SCRIPT, C2_CHANGE_VIR_PWD_SCRIPT
from mana_api.config import logging
import paramiko




logger = logging.getLogger(__name__)


# 自定义异常
class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)



# 处理 openstack 错误返回, 参数为 resp 对象，返回结果为字典
def openstack_error(resp):
    # {"conflictingRequest": {"message": "Cannot 'reboot' while instance is in task_state powering-off", "code": 409}}
    result = {"code": resp.status, "reason": resp.reason}
    data = resp.read()
    if data:
        logger.debug('Openstack Resp: %s' % data)
        dd = json.loads(data)
        msg = dd.values()[0]["message"]
        result["msg"] = msg
    return result

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
def chg_win_pwd(instance, pwd):
    pwd_str = base64.urlsafe_b64decode(pwd.encode())
    result, user_data = update_user_data(instance, pwd_str)
    if not result:
        LOG = "Failed %s" % user_data
        return False, LOG
    script_name = C2_CHANGE_VIR_WINDOWS_PWD_SCRIPT
    exe = "%s %s %s" %(script_name, instance.instance_name, user_data)
    print "runScript--->host_ip:%s,exe:%s" % (instance.host_ip, exe)
    try:
        LOG=conn(instance.host_ip,exe)
    except Exception,ex:
        print Exception, ":", ex
        LOG = "SSH exception:%s" % str(ex)
        return False, LOG
    return True, LOG


# 更改 linux 密码
def chg_linux_pwd(instance, pwd):
    script_name = C2_CHANGE_VIR_PWD_SCRIPT
    exe="%s %s %s" %(script_name, instance.instance_name, pwd)
    print "runScript--->host_ip:%s,exe:%s" % (instance.host_ip, exe)
    try:
        LOG = conn(instance.host_ip, exe)
    except Exception,ex:
        print Exception,":",ex
        LOG="SSH exception:%s" % str(ex)
        return False, LOG
    return True, LOG


# ssh 链接
def conn(host,command,user="root",pwd=None,port=22):
    ssh=paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print "host:%s,command:%s,user:%s,pwd:%s,port:%s" % (host,command,user,pwd,port)
    PRIVATE_KEY='/root/.ssh/id_rsa'
    ssh.connect(host,port,user,pwd,key_filename=PRIVATE_KEY)
    stdin,stdout,stderr=ssh.exec_command(command)
    error=stderr.readlines()
    output=stdout.readlines()
    ssh.close()
    if not error:
        return output
    else:
        errot_list=json.dumps(error)
        print "An error happened by:%s" % errot_list
        return error


def update_user_data(instance, pwd):
    data_base64 = instance.get_user_data()
    if not data_base64:
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
    instance.set_user_data(data_new_base64)
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