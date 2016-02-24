# coding: utf-8
import httplib
import urlparse
import json
from mana_api.config import AUTH_PUBLIC_URI


def http_request(url, body=None, headers=None, method="POST"):
    url_list = urlparse.urlparse(url)
    con = httplib.HTTPConnection(url_list.netloc, timeout = 15)
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
    headers = {"X-Auth-Token": '%s' % token, "Content-type": "application/json" }
    url = endpoint + '/servers/detail'
    res = http_request(url, headers=headers, method='GET')
    dd = json.loads(res.read())
    return {"code": 200, "msg": "", "vm_servers": dd["servers"][f:t]}

