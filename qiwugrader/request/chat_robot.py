# -*- coding:utf-8 -*-

import requests
import time
import logging

import gevent
# from gevent import monkey; monkey.patch_all()

from qiwugrader.request.basic_request import BasicRequest

from qiwugrader.util.string_helper import allowed_chat_key
from qiwugrader.util.string_helper import id_generator

__author__ = 'Feliciano'


class ChatRobot(BasicRequest):

    CHAT_KEY_RANDOM_SPLITTER = '___'
    CHAT_KEY_APP_SPLITTER = '###'

    MAX_RETRY_TIMES = 5

    wait_duration = 0.1

    chat_key = ''
    logger = logging

    FILTER_CHARACTERS = ['&', ',', '\'', '\"']

    def __init__(self, engine_config, robot_config, bot_username=None):
        self.protocol = engine_config.get("protocol")
        self.host = engine_config.get("host")
        self.port = engine_config.get("port")
        self.endpoint = engine_config.get("api")
        self.max_wait = engine_config.get("max_wait", 10)

        robot_server_config = robot_config.get_config("server", None)
        if robot_server_config is not None and 'max_wait' in robot_server_config:
            self.max_wait = robot_server_config['max_wait']

        # parse the proxy string
        self.proxy = None
        proxy_str = engine_config.get("proxy", None)
        if proxy_str is not None:
            end_pos = proxy_str.find("://")
            if end_pos != -1:
                proxy_type = proxy_str[:end_pos]
                if proxy_type == 'http' or proxy_type == 'https' or proxy_type == 'ftp':
                    self.proxy = {
                        proxy_type: proxy_str
                    }

        nickname = robot_config.get_config('nickname', None)
        self.nickname = nickname and nickname or 'landey'

        welcome = robot_config.get_config("welcome", '')
        self.welcome = welcome and welcome or ''
        self.username = bot_username
        if not self.username:
            self.username = robot_config.get_config('username') or robot_config.get_config('usernames')
        if not isinstance(self.username, str):
            self.username = self.username[0]

        self.use_static_chatkey = robot_config.get_config("static_chatkey")

        self.session = requests.Session()

    def set_logging(self, logger):
        self.logger = logger

    def set_chat_key(self, chat_key):
        self.chat_key = chat_key

    def get_debug_info(self):
        return 'Robot {0} at server {1}'.format(self.username, self.host)

    def _send_request(self, data, timeout=5):
        # return self._request_engine(data, timeout)

        glet = gevent.spawn(self._request_engine, data, timeout)
        gevent.wait([glet])
        return glet.value

    def _request_engine(self, data, timeout=1):
        try:
            r = self.session.post(self.to_uri(), data=data, proxies=self.proxy, timeout=timeout)
            return r
        except Exception as e:
            self.logger.exception(e)
            return None

    def generate_chat_key(self, uid):
        chat_key = self.use_static_chatkey and allowed_chat_key(uid) or ''

        # add separator and random id to prevent duplicate message
        if chat_key.find(ChatRobot.CHAT_KEY_RANDOM_SPLITTER) != -1:
            chat_key = chat_key + ChatRobot.CHAT_KEY_APP_SPLITTER + id_generator(20)
        else:
            chat_key = chat_key + ChatRobot.CHAT_KEY_RANDOM_SPLITTER + id_generator(20)

        return chat_key

    # login to the chat engine
    def login(self, chat_key):
        chat_key = self.generate_chat_key(chat_key)

        login_data = {
            'action': 'start',
            'chat_key': chat_key,
            'aipioneer_username': self.username,
            'nickname': self.nickname,
            'format': 'json'
        }

        r = self._send_request(login_data, self.max_wait)
        if r is None:
            self.logger.error('Engine {} login error'.format(self.host))
            return None

        result = r.json()
        self.chat_key = str(result['chat_key'])

        return self.chat_key

    # send user message to the chat engine
    def chat(self, msg, max_wait):
        status_code = 0
        for c in ChatRobot.FILTER_CHARACTERS:
            msg = msg.replace(c, '')

        if len(self.chat_key) == 0:
            return status_code, 'Please login first'

        chat_data = {
            'action': 'send',
            'chat_key': self.chat_key,
            'format': 'json',
            'message': msg,
        }
        r = self._send_request(chat_data)
        status_code = -1
        if r is None:
            self.logger.error('Engine {} send action error'.format(self.host))
            return status_code, ''

        status_code = r.status_code
        if r.status_code == requests.codes.ok:
            if len(r.text) > 0:
                result = r.json()
                del r
                if 'listlength' in result:
                    self.logger.debug('Engine current list length: ' + str(result['listlength']))
                    if 'false' == result['listlength'] or not result['listlength']:
                        self.logger.warning('Send question action list length error')
                        status_code = -2
                if 'reply' in result:
                    return status_code, result['reply'].strip()
                if 'wait' in result:
                    return status_code, ''
            else:
                self.logger.debug('Send quesetion action received 0 body')

        self.logger.warning('Send question action failed, status {0}'.format(r.status_code))
        return status_code, ''

    # send user message to the chat engine with security check
    def chat_with_check(self, msg, max_wait=10):
        retry = 0
        status = -1
        result = ''

        while retry < self.MAX_RETRY_TIMES and status != requests.codes.ok:
            status, result = self.chat(msg, max_wait)
            retry += 1

        if retry == self.MAX_RETRY_TIMES and status != requests.codes.ok:
            self.logger.error('{0} question send failed {1}'.format(self.get_debug_info(), status))
            # TODO: Make it an exception
            result = 'Question send failed'

        return result

    # get chat engine reply
    def reply(self):
        if len(self.chat_key) == 0:
            return 'Please login first'

        duration = time.time()

        reply_data = {
            'action': 'receive',
            'chat_key': self.chat_key,
            'format': 'json',
        }

        r = self._send_request(reply_data)
        if r is None:
            self.logger.warning('Receive answer action error')
            return ''

        if r.status_code == requests.codes.ok:
            if len(r.text) > 0:
                result = r.json()
                if 'reply' in result:
                    reply = result['reply']
                    if len(reply) > 0:
                        reply = reply.strip()

                    duration = time.time() - duration
                    if duration > 1:
                        self.logger.warning('Action receive used: ' + str(duration))
                    return reply
        else:
            self.logger.warning('Receive answer action failed')
        return ''

    # wait a valid reply from server until timeout
    def wait_for_reply(self, wait_time=None):
        wait_time = wait_time or self.max_wait

        query_time = time.time()

        result = self.reply()

        while len(result) == 0\
                and (time.time()-query_time) < wait_time:
            time.sleep(self.wait_duration)
            result = self.reply()

        if len(result) == 0:
            self.logger.error('{0} get reply time out {1}'.format(self.get_debug_info(), wait_time))

        self.logger.debug('Waited for {:.5f} seconds'.format(time.time() - query_time))

        return result

    # wait a specific reply from the server
    def wait_for_this_reply(self, content):
        result = self.wait_for_reply()

        retry = 0
        last_success = ''

        while result.find(content) == -1 and retry < self.MAX_RETRY_TIMES:
            if len(result) !=0:
                last_success = result
                print(('<chat_robot> {0} got reply {1}, but ignored since not {2}'.format(self.get_debug_info(), result, content)))
            result = self.wait_for_reply()
            retry += 1

        if retry == self.MAX_RETRY_TIMES and len(result) == 0:
            result = last_success

        return result

    def wait_for_welcome(self):
        return self.wait_for_this_reply(self.welcome)
