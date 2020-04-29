# -*- coding:utf-8 -*-
import time

from qiwugrader.request.chat_robot import ChatRobot
from qiwugrader.request.chat_robot_redis import ChatRobotRedis
from qiwugrader.controller.config_file_handler import YamlConfigFileHandler

from qiwugrader.grader.compatible import to_str

__author__ = 'Feliciano'


class pMsgHandler:

    robot_name = 'mimi2'

    def __init__(self, server_config: YamlConfigFileHandler, logger):
        self.server = server_config
        self.logging = logger

        self.tokens = {}
        self.nicknames = {}
        self.active = {}
        self.msg = {}

        self.access_token = ''
        self.token_expire = 0

        if self.server.get_config('server').get('chat_type', None) == 'java':
            self.handler = ChatRobotRedis(self.server.get_config('server'), self.server)
        else:
            self.handler = ChatRobot(self.server.get_config('server'), self.server)
        self.handler.set_logging(self.logging)

    # Pre process and returns if we need to handle this message
    def pre_chat(self, from_name, msg):
        if msg == '' or msg is None:
            return False

        if msg.startswith(u'logout'):
            if from_name in self.tokens:
                # Restart the conversation actively
                del self.tokens[from_name]
                self.logging.debug(from_name + ' logged out')
                return False
            else:
                # If the conversation is already ended, ignore the message
                return False

        # Remove expired token
        if from_name in self.active:
            if time.time() - self.active[from_name] > 300:
                del self.tokens[from_name]

        return True

    # Process the message, and returns response
    def process_chat(self, from_name, msg, max_wait=None, login_wait=None):
        start_time = time.time()

        result = ''
        skip_first = False

        # Refresh active time
        self.active[from_name] = time.time()

        # If token exist, set chat key. Or login to chat robot
        if from_name in self.tokens:
            chat_key = self.tokens[from_name]
            self.handler.set_chat_key(chat_key)
            self.logging.debug('Existed user {0} chat with chatkey {1}'.format(from_name, chat_key))
        else:
            chat_key = self.handler.login(self.robot_name)
            if chat_key is None:
                return result

            self.tokens[from_name] = chat_key
            skip_first = True
            self.logging.debug('New user {0} login with chatkey {1}'.format(from_name, chat_key))

            result = self.handler.wait_for_welcome()
            result_str = to_str(result)
            self.logging.info('<process_chat>[{3}] Login Res: {0} Length: {1} for chatkey {2}'.format(result_str, str(len(result_str)), chat_key, time.time()-start_time))

            if login_wait:
                time.sleep(login_wait)

        self.logging.info('<process_chat>[{0}] User Ask with chatkey {1}'.format(time.time() - start_time, chat_key))

        # Send question
        result = self.handler.chat_with_check(msg)

        self.logging.info('<process_chat>[{0}] User Ask {1}'.format(time.time() - start_time, result))

        # If send action doesn't have reply, wait for a reply
        if len(result) == 0:
            result = self.handler.wait_for_reply()

        self.logging.info('<process_chat>[{0}] Got Answer {1}'.format(time.time() - start_time, result))

        # Post process result string
        '''
        result = result.replace('\n', ' ')
        result = result.replace('\r', ' ')
        result = result.replace('Marco', str(self.nicknames[from_name]))
        result = result.strip()
        '''
        # print 'Res: ' + result

        return result

    def handle_chat(self, from_name, msg, login_wait=None):
        start = time.time()
        # Pre process and check if we really need to handle this message
        if self.pre_chat(from_name, msg):
            # Process the message and give a response
            result = self.process_chat(from_name, msg, login_wait=login_wait)

            self.logging.debug('Robot Response: {0} for chatkey {1} in {2}'.format(result, from_name, time.time() - start))

            if result and result != '':
                return result

        return ''
