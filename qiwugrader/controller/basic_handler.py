# -*- coding:utf-8 -*-
from abc import abstractmethod
import time
from random import randint

__metaclass__ = type


class BasicHandler:

    chat_key_expire_in = 300

    NEW_LINE_ESCAPE = u'叕n'.encode('utf-8')

    def __init__(self, robot_id='unknown'):
        # handler id
        self.id = robot_id

        # handler post replacement
        self.replacement = None
        # message cache dict
        self.msg = {}
        # user active time dictionary
        self.active = {}

        self.filter_duplicate = False
        self.last_chat = {}

        self.robot_nickname = None

        self._handles_image = False

        self.logger = None

    def set_logging(self, logger):
        self.logger = logger

    def set_replacement(self, replacement):
        self.replacement = {}
        if replacement:
            for value in replacement:
                self.replacement[value.encode('utf-8')] = replacement[value]

    def can_handle_image(self, from_name=None):
        return self._handles_image

    def get_robot_nickname(self, from_name=None):
        return self.robot_nickname

    # pre process and returns if we need to handle this message
    def pre_chat(self, from_name, msg):
        if msg is None or msg == '':
            return False
        if self.filter_duplicate:
            if from_name in self.last_chat and self.last_chat[from_name] == msg:
                return False
            self.last_chat[from_name] = msg
        return True

    @abstractmethod
    def process_chat(self, from_name, msg, skip_welcome=True, max_wait=None, login_wait=None):
        return ''

    def post_chat(self, from_name, result):
        if self.replacement and len(self.replacement) > 0:
            for replace in self.replacement:
                if result.find(replace) != -1:
                    res = randint(0, len(self.replacement[replace]) - 1)
                    result = self.replacement[replace][res].encode('utf-8')

        return result

    def handle_chat(self, from_name, msg, max_wait=None, login_wait=None, msg_id=None):
        if msg_id is None:
            msg_id = msg
        # pre process and check if we really need to handle this message
        handle_chat = self.pre_chat(from_name, msg)
        if handle_chat:
            self.active[from_name] = time.time()

            # process the message and give a response
            result = self.process_chat(from_name, msg, max_wait=max_wait, login_wait=login_wait)
            self.msg[msg_id] = result

            # post chat stuff
            modified_result = self.post_chat(from_name, result)
            if modified_result is not None:
                result = modified_result

            if result and result != '':
                return result

        return ''
