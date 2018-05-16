# -*- coding:utf-8 -*-
import requests
import time

from compatible import to_str

__author__ = 'Feliciano'


class ChatRobot:

    ERROR_REPLY = u'服务器通信错误。'.encode('utf-8')

    MAX_RETRY_TIMES = 5

    def __init__(self, server_config, logging):
        self.protocol = server_config["protocol"]
        self.host = server_config["host"]
        self.port = server_config["port"]
        self.endpoint = server_config["api"]

        self.nickname = server_config.get("nickname", "landey").encode('utf-8')
        self.welcome = server_config.get("welcome", "").encode('utf-8')
        self.wait_duration = float(server_config.get("wait_duration", 0.2))
        self.max_wait = float(server_config.get("max_wait", 10))

        self.proxy = None
        proxy_str = server_config.get("proxy", "")
        end_pos = proxy_str.find("://")
        if end_pos != -1:
            proxy_type = proxy_str[:end_pos]
            if proxy_type == 'http' or proxy_type == 'https' or proxy_type == 'ftp':
                self.proxy = {
                    proxy_type: proxy_str
                }

        self.chat_key = ''

        self.logging = logging

    def set_chatkey(self, chat_key):
        self.chat_key = chat_key

    def to_uri(self):
        return '{0}://{1}:{2}{3}'.format(self.protocol, self.host, self.port, self.endpoint)

    def login(self, robot='mimi2'):
        login_data = {
            'action': 'start',
            'aipioneer_username': robot,
            'nickname': self.nickname,
            'format': 'json'
        }

        r = requests.post(self.to_uri(), data=login_data, proxies=self.proxy)
        result = r.json()

        self.chat_key = str(result['chat_key'])

        return self.chat_key

    def chat(self, msg):
        if len(self.chat_key) == 0:
            return -1, 'Please login first'

        chat_data = {
            'action': 'send',
            'chat_key': self.chat_key,
            'format': 'json',
            'message': msg,
        }

        result = ''

        r = requests.post(self.to_uri(), data=chat_data, proxies=self.proxy)
        if r.status_code == requests.codes.ok:
            if len(r.text) > 0:
                response = r.json()
                if 'reply' in result:
                    result = response['reply'].encode('utf-8').strip()
        else:
            self.logging.error('Send question action failed')
            result = self.ERROR_REPLY

        return r.status_code, result

    def chat_with_check(self, msg):
        retry = 0
        status = -1
        result = self.ERROR_REPLY

        while retry < self.MAX_RETRY_TIMES and status != requests.codes.ok:
            status, result = self.chat(msg)
            retry += 1

        if retry == self.MAX_RETRY_TIMES:
            self.logging.error('Question send failed')
            # TODO: Make it an exception
            result = self.ERROR_REPLY

        return result

    def reply(self):
        if len(self.chat_key) == 0:
            return 'Please login first'

        reply_data = {
            'action': 'receive',
            'chat_key': self.chat_key,
            'format': 'json',
        }

        r = requests.post(self.to_uri(), data=reply_data, proxies=self.proxy)

        if r.status_code == requests.codes.ok:
            if len(r.text) > 0:
                result = r.json()
                if 'reply' in result:
                    return result['reply'].encode('utf-8').strip()
        else:
            self.logging.warning('Receive answer action failed')

        return b''

    def wait_for_reply(self):
        query_time = time.time()

        result = self.reply()

        while len(result) == 0\
                and (time.time()-query_time) < self.max_wait:
            self.logging.debug('No response, wait. waited {0} max {1}'.format(time.time()-query_time, self.max_wait))

            time.sleep(self.wait_duration)
            # query_time += self.wait_duration

            result = self.reply()

        if len(result) == 0:
            self.logging.error('Server reply time out')
            result = self.ERROR_REPLY

        self.logging.info('Waited for {:.5f} seconds'.format(time.time()-query_time))

        return result

    def wait_for_this_reply(self, content):
        result = self.wait_for_reply()

        retry = 0

        content = to_str(content)
        while to_str(result).find(content) == -1 \
                and retry < self.MAX_RETRY_TIMES:
            result = self.wait_for_reply()
            retry += 1
        if to_str(result).find(content) == -1:
            self.logging.error("System welcome does not include welcome words in your configuration!")
            # exit()
        return result

    def wait_for_welcome(self):
        return self.wait_for_this_reply(self.welcome)
