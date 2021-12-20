# -*- coding: utf-8 -*-

from qiwugrader.controller.config_file_handler import YamlConfigFileHandler
from qiwugrader.controller.basic_handler import BasicHandler
from qiwugrader.request.single_dialogue import SingleDialogue
from qiwugrader.util.string_helper import allowed_bot_msg_filter, id_generator
from qiwugrader.request.chat_robot import ChatRobot

from qiwugrader.grader.init import test_logger as logger

from qiwugrader.grader.compatible import to_str

import json


class SingleDialogueHandler(BasicHandler):

    RESTART_MESSAGE = u'logout'

    def __init__(self, service_config):
        super(SingleDialogueHandler, self).__init__('SingleChat')
        self.id = 'Single-' + service_config.get_config('name')
        self.handler = SingleDialogue(service_config)
        self.set_replacement(service_config.get_config('post-replacement'))
        self.app_key = service_config.get_config('name').replace('_', '-')

        self.session = {}

    def pre_chat(self, from_name, msg):
        if super(SingleDialogueHandler, self).pre_chat(from_name, msg):
            # TODO: add length limit
            return True
        return False

    # Process the message, and returns response
    def process_chat(self, from_name, msg, skip_welcome=True, max_wait=None, login_wait=None):
        if msg.find('START_ROBOT') > -1:
            return '你好'

        uid = from_name

        if msg == 'reset':
            del self.session[uid]
            return 'RESET'

        msg = allowed_bot_msg_filter(msg)

        if uid not in self.session:
            self.session[uid] = str(uid) + ChatRobot.CHAT_KEY_RANDOM_SPLITTER + id_generator(20)

        # Get reply
        data = {
            'uid': to_str(from_name.encode('utf-8')),
            'msg': to_str(msg.encode('utf-8')),
            'chat_key': self.session[uid],
            'chatKey': '',
            'appkey': self.app_key,
            'nickname': 'tester',
            'new_session': 'false',
            'max_wait': '20'
        }
        result = self.handler.chat(data)
        if isinstance(result, dict):
            result = json.dumps(result)
        return result.encode('utf-8')


def single_dialogue_chat_service(service_name, config_dir='./configs/single/'):
    service_config = YamlConfigFileHandler(config_dir + service_name + '.yml')
    handler = SingleDialogueHandler(service_config)
    handler.set_logging(logger)

    return handler
