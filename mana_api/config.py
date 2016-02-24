__author__ = 'liujiahua'
import logging
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

#############################################################################
# Identity Service Endpoint
#############################################################################


AUTH_PUBLIC_URI = '192.168.39.170:5000'
ADMIN_TOKEN = '60feb5797e974a89af19e9a40f04ac07'
ADMIN_PROJ = '74d4bda6aa1c466d8cb1f2b8eac79567'
DATABASE = 'mysql://root:@localhost/netflow'
DATABASE_CLOUD = 'mysql://root:@localhost/cloud'


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(pathname)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='E:/mana_api/logs/all.log',
                    filemode='a')


