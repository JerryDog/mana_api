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

KEYSTONE = {
    "default": {
        "uri": "222.73.243.57:5000",
        "admin_token": "c8442ce938bb8b0b4267",
        "admin_proj": "e58c78fe826f4f0b890767a3e0781019"
    },
    "scloudm": {
        "uri": "222.73.243.57:5000",
        "admin_token": "c8442ce938bb8b0b4267",
        "admin_proj": "e58c78fe826f4f0b890767a3e0781019"
    }
}


DATABASE = 'mysql://root:@localhost/netflow'
DATABASE_CLOUD = 'mysql://root:@localhost/cloud'


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(pathname)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='E:/mana_api/logs/all.log',
                    filemode='a')



# change password
C2_CHANGE_VIR_WINDOWS_PWD_SCRIPT = "python /opt/minion/extmods/modules/chg_win_pwd"
C2_CHANGE_VIR_PWD_SCRIPT="python /opt/minion/extmods/modules/chg_pwd"

