# -*- coding:utf-8 -*-
# from gevent import monkey; monkey.patch_all();
import requests
import time
import logging
import json

import urllib3

from requests.adapters import HTTPAdapter

from qiwugrader.request.chat_robot import ChatRobot as BasicChatRobot

__author__ = 'Feliciano'

sessions = requests.Session()
sessions.mount('http://', HTTPAdapter(pool_connections=1024, pool_maxsize=2048))


class ChatRobotRedis(BasicChatRobot):

    CONNECT_TIMEOUT = .5
    LOGIN_TIMEOUT = 1.5
    LOGIN_MAX_RETRY = 3

    def __init__(self, engine_config, robot_config, bot_username=None):
        super(ChatRobotRedis, self).__init__(engine_config, robot_config, bot_username)
        self.session = sessions
        self.bot_dynamic_keywords_key = robot_config.get_config("bot_dynamic_keywords_key", None)

    def _request_engine(self, data, timeout=1):
        try:
            r = self.session.post(self.to_uri(), json=data, proxies=self.proxy, timeout=(self.CONNECT_TIMEOUT, timeout))
            # self.logger.info('<chat_robot_redis> elapsed {} {} {}'.format(data['action'], r.elapsed.total_seconds(), data['chat_key']))
            return r
        except requests.exceptions.ConnectTimeout as e:
            self.logger.error('<chat_robot_redis> failed to connect node    ', e)
        return None

    def _handle_engine_response(self, r, action):
        if r is None:
            self.logger.error('Engine {} {} error: {}'.format(self.host, action, r))
            return None

        if r.status_code != requests.codes.ok:
            return None

        r_json = r.json()
        if r_json['retcode'] != 0:
            self.logger.error('Engine {} {} error: {}'.format(self.host, action, r_json))
            return None

        return r_json

    # login to the chat engine
    @DeprecationWarning
    def login(self, chat_key):
        chat_key = self.generate_chat_key(chat_key)

        login_data = {
            'action': 'START',
            'chat_key': chat_key,
            'username': self.username,
            'nickname': self.nickname,
            'format': 'json',
        }

        r = self._send_request(login_data, 5)
        if r is None:
            return None
        res = self._handle_engine_response(r, 'login')
        if res is None:
            return None

        result = json.loads(res['payload'])
        self.chat_key = str(result['chatEvent']['chat_key'])

        return self.chat_key

    def login_and_wait(self, uid):
        chat_key = self.generate_chat_key(uid)

        login_data = {
            'action': 'START',
            'chat_key': chat_key,
            'username': self.username,
            'nickname': self.nickname,
            'format': 'json',
            'waiting_time': self.max_wait * 1000,
        }

        retry = 0
        r = None
        while not r and retry < self.MAX_RETRY_TIMES:
            try:
                r = self._send_request(login_data, self.LOGIN_TIMEOUT)
                if r is None:
                    login_data['chat_key'] = self.generate_chat_key(uid)
                retry += 1
            except Exception as e:
                self.logger.error('Failed to login', e)
                login_data['chat_key'] = self.generate_chat_key(uid)

        res = self._handle_engine_response(r, 'login')
        if res:
            result = json.loads(res['payload'])
            self.chat_key = str(result['chatEvent']['chat_key'])

            if 'reply' in result:
                if 'text' in result['reply']:
                    reply = str(result['reply']['text'])
                    return reply

        return ''

    # send user message to the chat engine
    def chat(self, msg, max_wait):
        status_code = 0
        for c in ChatRobotRedis.FILTER_CHARACTERS:
            msg = msg.replace(c, '')

        if len(self.chat_key) == 0:
            return status_code, 'Please login first'

        chat_data = {
            'action': 'SEND',
            'chat_key': self.chat_key,
            'text': msg,
            'nickname': self.nickname,
            'format': 'json',
            'waiting_time': max_wait * 1000,
        }

        retry = 0
        r = None
        try:
            while not r and retry < self.MAX_RETRY_TIMES:
                r = self._send_request(chat_data, max_wait)
                retry += 1
        except Exception as e:
            self.logger.error('Failed to send', e)

        res = self._handle_engine_response(r, 'send')

        status_code = -1
        if res:
            status_code = r.status_code
            if status_code == requests.codes.ok:
                if len(r.text) > 0:
                    result = json.loads(res['payload'])
                    if 'listLength' in result:
                        self.logger.info('Send question {} Engine current list length: {}'.format(chat_data['chat_key'], str(result['listLength'])))
                        if 'false' == result['listLength'] or result['listLength'] is None:
                            self.logger.warning('Send question action list length error')
                            status_code = -2
                    if 'reply' in result:
                        return status_code, result['reply']['text'].strip()
                else:
                    self.logger.debug('Send quesetion action received 0 body')
            else:
                self.logger.warning('Send question action failed, status {0}'.format(r.status_code))
        return status_code, ''

    # get chat engine reply
    def reply(self):
        if len(self.chat_key) == 0:
            return 'Please login first'

        duration = time.time()

        reply_data = {
            'action': 'RECEIVE',
            'chat_key': self.chat_key,
            'format': 'json',
        }

        r = self._send_request(reply_data)

        if r is None:
            self.logger.warning('Receive answer action error')
            return ''
        elif 'retcode' not in r.json() or r.json()['retcode'] != 0:
            self.logger.warning('Receive answer action error, no retcode for: ' + r.text)
            return ''

        if r.status_code == requests.codes.ok:
            if len(r.text) > 0 and r.json()['payload'] != '':
                result = json.loads(r.json()['payload'])
                if 'text' in result:
                    reply = result['text']
                    if len(reply) > 0:
                        reply = reply.strip()

                    duration = time.time() - duration
                    if duration > 1:
                        self.logger.warning('Action receive used: ' + str(duration))
                    return reply
        else:
            self.logger.warning('Receive answer action failed')
        return ''

    # send user message to the chat engine with security check
    def chat_with_check(self, msg, max_wait=None):
        max_wait = max_wait or self.max_wait
        status, result = self.chat(msg, max_wait)

        if status != requests.codes.ok:
            self.logger.error('{0} question send failed {1}'.format(self.get_debug_info(), status))
            # TODO: Make it an exception
            result = ''
        return result

    def wait_for_reply(self, wait_time=None):
        wait_time = wait_time or self.max_wait

        query_time = time.time()

        result = self.reply()

        while len(result) == 0\
                and (time.time()-query_time) < wait_time:
            result = self.reply()
            time.sleep(0.05)

        if len(result) == 0:
            self.logger.error('{0} get reply time out {1}'.format(self.get_debug_info(), wait_time))

        self.logger.debug('Waited for {:.5f} seconds'.format(time.time() - query_time))

        return result

    def manipulate_keywords_on_engine_slave(self, word_list=None, method='GET'):
        """
        get or set engine robot keywords
        :param word_list:
        :param method: GEt / POST
        :return: When GET, if the bot has auto generate tag, returns ordered word_list was set, otherwise all keywords in payload
        When POST, set the word list to keywords unit and returns all keywords in payload, otherwise returns Error
        """
        print('manipulate keywords on engine slave is called')
        protocol = self.protocol + '://'
        gateway = self.host + ':'
        port = '46009'
        api = '/api/v1/bot/keywords'
        url = protocol + gateway + port + api
        id_url = protocol + gateway + port + '/api/get/bot'
        bot_id_response = requests.get(id_url, params={'botName': self.username})
        bot_id_js = bot_id_response.json()
        if 'payload' not in bot_id_js:
            return 'NoSuchBot'
        payload = bot_id_js['payload']
        payload_js = json.loads(payload)
        bot_id = payload_js['id']

        if 'GET' == method:
            auto_gen = '#auto_generated_keywords'
            r = requests.get(url=url, params={'userId': bot_id})
            js = r.json()
            keywords = js['payload']
            index = keywords.find(auto_gen)
            if index >= 0:
                words = keywords[index + len(auto_gen):-1]
                get_word_list = words.split('\n')
                for i in range(0, len(get_word_list)):
                    get_word_list[i] = get_word_list[i][1:get_word_list[i].find('|')]
                get_word_list.remove('')
                js['payload'] = ""
                js['auto_generated_keywords'] = get_word_list
            return js

        elif 'POST' == method:
            if 'auto_generated_keywords' == self.bot_dynamic_keywords_key:
                r = requests.post(url=url, json={'userId': bot_id, 'keywords': word_list})
                js = r.json()
                return js
            else:
                return "NoDynamic"
        else:
            return "FunctionRequestError"






