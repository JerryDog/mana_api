# -*- coding: utf-8 -*-
__author__ = 'liujiahua'
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask import abort
from flask import request
from flask import jsonify
from config import KEYSTONE, DATABASE, DATABASE_CLOUD
from flask import g
import urlparse
import json
import re
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_BINDS'] = {
    'cloud': DATABASE_CLOUD
}

db = SQLAlchemy(app)


@app.errorhandler(401)
def page_not_found(error):
    return 'Unauthorized', 401

from apiUtil import http_request

@app.before_request
def before_request():
    token = request.headers.get("X-Auth-Token")
    g.party = request.headers.get("Sp-Agent", "default")
    g.admin_token = KEYSTONE[g.party]['admin_token']
    g.uri = KEYSTONE[g.party]['uri']
    g.admin_proj = KEYSTONE[g.party]['admin_proj']
    # 静态文件和监控数据不用验证，直接通过
    if re.match('/mana_api/pm_monitor', request.path):
        token = g.token = g.admin_token
    if re.match('/static', request.path):
        token = g.token = g.admin_token
    if re.match('/mana_api/tokens', request.path):
        token = g.token = g.admin_token
    if not token:
        abort(401)
    else:
        if validatedToken(token):
            g.token = token  # 不带 tenant_id 的 token
            pass
        else:
            return jsonify({"error": "invalid token"}), 400


def validatedToken(token):
    try:
        if token == g.admin_token:
            return True
        headers = {"X-Auth-Token": "%s" % g.admin_token}
        url = urlparse.urljoin('http://' + g.uri + '/', '/v2.0/tokens/%s' % token)
        res = http_request(url, headers=headers, method='GET')
        dd = json.loads(res.read())
        if dd.has_key('access'):
            return True
        else:
            return False
    except:
        return False


#from mana_api import models
#api = Api(app)
#
#class HelloWorld(Resource):
#
#    def get(self):
#        return {'hello': 'world'}
#
#api.add_resource(HelloWorld, '/')
#from unify.api.identity import identity_bp

#app.register_blueprint(identity_bp, url_prefix='/identity')
from mana_api.api import zt_api

app.register_blueprint(zt_api, url_prefix='/mana_api')
