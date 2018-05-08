# -*- coding:utf-8 -*-
import time

from model import chat_robot

from compatible import to_str

__author__ = 'Feliciano'


class pMsgHandler:

    robot_name = 'mimi2'

    ERROR_REPLY = u'服务器抛出了一个问题，请稍后重试'.encode('utf-8')
    TIMEOUT_REPLY = u'服务器忙，请稍后'.encode('utf-8')

    def __init__(self, server_config, logger):
        self.server = server_config
        self.logging = logger

        self.tokens = {}
        self.nicknames = {}
        self.active = {}
        self.msg = {}

        self.access_token = ''
        self.token_expire = 0

    # Pre process and returns if we need to handle this message
    def pre_chat(self, from_name, msg):
        if msg == '' or msg is None:
            return False

        if msg.startswith(u'logout'):
            if self.tokens.has_key(from_name):
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
    def process_chat(self, from_name, msg):
        handler = chat_robot.ChatRobot(self.server, self.logging)

        result = ''
        skip_first = False

        # Refresh active time
        self.active[from_name] = time.time()

        # If token exist, set chat key. Or login to chat robot
        if from_name in self.tokens:
            chat_key = self.tokens[from_name]
            handler.set_chatkey(chat_key)
            self.logging.debug('Existed user {0} chat with chatkey {1}'.format(from_name, chat_key))
        else:
            chat_key = handler.login(self.robot_name)
            self.tokens[from_name] = chat_key
            skip_first = True
            self.logging.debug('New user {0} login with chatkey {1}'.format(from_name, chat_key))

            result = handler.wait_for_welcome()
            result = to_str(result)
            self.logging.info('Login Res: {0} Length: {1} for chatkey {2}'.format(result, str(len(result)), chat_key))

        self.logging.debug('User ask: {0} with chatkey'.format(msg.encode('utf-8'), chat_key))

        if skip_first and len(result) != 0:
            time.sleep(handler.wait_duration)
            result = ''

        # Send question
        result = handler.chat_with_check(msg)

        # If send action doesn't have reply, wait for a reply
        if len(result) == 0:
            result = handler.wait_for_reply()

        if len(result) == 0:
            result = self.TIMEOUT_REPLY

        # Post process result string
        '''
        result = result.replace('\n', ' ')
        result = result.replace('\r', ' ')
        result = result.replace('Marco', str(self.nicknames[from_name]))
        result = result.strip()
        '''
        # print 'Res: ' + result

        return result

    def handle_chat(self, from_name, msg):
        # Pre process and check if we really need to handle this message
        if self.pre_chat(from_name, msg):
            # Process the message and give a response
            result = self.process_chat(from_name, msg)

            self.logging.debug('Robot Response: {0}'.format(result))

            if result and result != '':
                return result

        return ''
