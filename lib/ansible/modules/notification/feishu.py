#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2023, RocDove <rocdove@sina.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- RocDove
module: feishu
short_description: Send an feishu message
description:
- This module is useful for sending feishu msessage from playbooks.
version_added: '0.1'
options:
  webhook:
    description:
      - Business id.
    required: true
  secret:
    description:
      - application secret.
    required: true
  ats:
    description:
      - Member ID list (message recipient, multiple recipients separated by '|', up to 10).
      - "Special case: Specify @all to send to all members of the enterprise application."
      -  When toparty, touser, totag is empty, the default value is @all.
  msg:
    description:
      - The message body.
    required: true
'''

EXAMPLES = r'''
# Send a msg.
- wechat:
    webhook: 'https://open.feishu.cn/open-apis/bot/v2/hook/xxx'
    secret: "xxx"
    msg: Ansible task finished

# Send a msg at user.
- wechat:
    webhook: 'https://open.feishu.cn/open-apis/bot/v2/hook/xxx'
    secret: "xxx"
    ats: "userB|userA"
    msg: Ansible task finished
'''


RETURN = """
msg:
  description: The message you attempted to send
  returned: always
  type: str
  sample: "Ansible task finished"
ats:
  description: send user id
  returned: success
  type: str
  sample: "ZhangSan"
feishu_error:
  description: Error message gotten from FeiShu Robot API
  returned: failure
  type: str
  sample: "Bad Request: message text is empty"
"""

# ===========================================
# FeiShu robot webhook module specific support methods.
#

import hashlib
import base64
import hmac
import time
import requests
import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url

class FeishuRobot(object):


    # 机器人webhook
    # chatGPT_url = 'https://open.feishu.cn/open-apis/bot/v2/hook/a60b609c-90b2-45b1-a132-5b7412af290a'
    # secret = 'uhxwTfPtdjncjntHSiZDJc'

    def __init__(self, module, webhook, secret):
        """
        初始化
        :param module:  Ansible module
        :param webhook: robot webhook url
        :param secret:  加签密钥
        :param ats:     @人员列表
        :param msg:     消息内容
        """

        self.module = module
        self.webhook = webhook
        self.secret = secret

        if self.module.check_mode:
            # In check mode, exit before actually sending the message
            module.exit_json(changed=False)

    def gen_sign(self, timestamp):
        secret = self.secret
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')

        return sign

    # 发送文本消息
    def sendTextmessage(self, content, ats):
        url = self.webhook
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        timestamp = int(time.time())
        sign = self.gen_sign(timestamp)
        payload_message = {
            "timestamp": "{}".format(timestamp),
            "sign": "{}".format(sign),
            "msg_type": "text",
            "content": {
            	# @ 单个用户 <at user_id="ou_xxx">名字</at>
                "text": content
                # @ 所有人 <at user_id="all">所有人</at>
                # "text": content + "<at user_id=\"all\">test</at>"
            }
        }
        response = requests.post(url=url, data=json.dumps(payload_message), headers=headers)
        return response.json


def main():
    module = AnsibleModule(
        argument_spec=dict(
            webhook=dict(required=True, type='str', no_log=True),
            secret=dict(required=True, type='str', no_log=True),
            ats=dict(required=False, type='str'),
            msg=dict(required=True, type='str'),
        ),
        supports_check_mode=True
    )

    webhook = module.params["webhook"]
    secret = module.params["secret"]
    ats = module.params["ats"]
    msg = module.params["msg"]

    try:
        robot = FeishuRobot(module, webhook, secret)
        robot.sendTextmessage(msg, ats)

    except Exception as e:
        module.fail_json(msg="unable to send msg: %s" % msg, feishu_error=to_native(e), exception=traceback.format_exc())

    changed = True
    module.exit_json(changed=changed, ats=ats, msg=msg)

if __name__ == '__main__':
    main()