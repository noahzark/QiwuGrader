import requests
import hashlib
import time

from qiwugrader.request.basic_request import BasicRequest
from qiwugrader.controller.single_dialogue_handler import SingleDialogueHandler


class ChatApi(BasicRequest):

    def __init__(self, host, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.host = host

    def cal_verify(self, uid, timestamp):
        tmp = ''.join([self.app_secret, uid, str(timestamp)])
        return hashlib.md5(tmp.encode('utf-8')).hexdigest()

    def chat(self, uid, msg):
        timestamp = int(time.time() * 1000)

        payload = {
            'appkey': self.app_key,
            'timestamp': timestamp,
            'uid': uid,
            'verify': self.cal_verify(uid, timestamp),
            'msg': msg
        }

        result = requests.post(self.to_uri('/api/chat'), data=payload).json()
        return result['msg']


class ChatApiHandler(SingleDialogueHandler):

    def __init__(self, service_config):
        super(ChatApiHandler, self).__init__('ChatApi')

        self.id = 'Single-' + service_config.get_config('name')

        server_config = service_config.get_config('server')
        self.handler = ChatApi(server_config['server'], server_config['appkey'], server_config['appsecret'])
        self.set_replacement(service_config.get_config('post-replacement'))


if __name__ == '__main__':
    chat_api = ChatApi('robot-service-test.centaurstech.com', 'qiwurobot', '123456')
