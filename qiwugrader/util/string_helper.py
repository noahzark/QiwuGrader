# coding=utf8
from enum import Enum
import re
import string
import random
import pprint
import uuid


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    # return ''.join(random.choice(chars) for _ in range(size))
    return str(uuid.uuid1().hex)


def id_generator4(size=6, chars=string.ascii_uppercase + string.digits):
    # return ''.join(random.choice(chars) for _ in range(size))
    return str(uuid.uuid4())


def num(s):
    try:
        return int(s)
    except ValueError:
        return None


def chinese_to_answer_dict(answers, dictionary):
    for dict_key in answers:
        for answer in answers[dict_key]:
            dictionary[answer] = dict_key


ALLOWED_EXTENSIONS = set(['txt', 'jpg'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


CHAT_KEY_FILTER = r"[^a-zA-Z0-9\-\_\.@#]+"
UID_MAX_LENGTH = 80


def allowed_chat_key(chat_key):
    # only allow digits and characters
    filtered = re.sub(CHAT_KEY_FILTER, "", chat_key)
    # only support chat_key length up to 80
    return filtered[:UID_MAX_LENGTH]


def contains_illegal_char(chat_key):
    return re.search(CHAT_KEY_FILTER, chat_key)


CHAT_BOT_MSG_FILTER = '[^\u4E00-\u9FA5A-Za-z0-9_!?,.！？，。:：×÷+-~\s（）]'


def allowed_bot_msg_filter(msg):
    return re.sub(CHAT_BOT_MSG_FILTER, '', msg)


class UTF8PrettyPrinter(pprint.PrettyPrinter):

    def format(self, obj, context, max_levels, level):
        if isinstance(obj, str):
            return obj.encode('utf8'), True, False
        return pprint.PrettyPrinter.format(self, obj, context, max_levels, level)


class AnswerTokenType(Enum):

    QUERY_ATTACH = r'嬲'
    IMAGE_ATTACH = r'啚'


class StringExtractor:
    UUID_FORMAT = '([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    DIALOGUE_STATE_FORMAT = '[0-1]'
    BUSINESS_IDENTIFIER = '事務{([a-zA-Z0-9_]+)}'

    # DIALOGUE END REPLY
    FAIL_HANDLE_SEPARATOR = r'止めてください'
    END_SESSION_SEPARATOR = r'さようなら'

    DATA_ATTACH_SEPARATOR = r'嫐'
    DIALOGUE_STATE_ATTACH = r'焱'
    VOICE_SEPARATOR = r'囡'
    CUT_SEPARATOR = r'歮'
    LISTEN_SILENCE_SEPARATOR = r'黙れ'
    LISTEN_SILENCE_SEPARATOR_2 = r'黙'

    def __init__(self):
        pass

    @staticmethod
    def extract_type(token_type, data):
        if data.find(token_type.value) != -1:
            matches = list(re.finditer(token_type.value + StringExtractor.UUID_FORMAT, data))

            if len(matches):
                match = matches[0]
                return match.group(1), data.replace(match.group(0), '')
        return '', data

    @staticmethod
    def extract(data):
        for token_type in AnswerTokenType:
            extracted, modified_words = StringExtractor.extract_type(token_type, data)
            if extracted:
                return token_type, extracted, modified_words

        return None, '', data

    @staticmethod
    def extract_json(words):
        if words.find(StringExtractor.DATA_ATTACH_SEPARATOR) != -1:
            split_result = words.split(StringExtractor.DATA_ATTACH_SEPARATOR)
            modified_words = split_result[0]
            extracted = split_result[1]
            append = extracted[extracted.rfind('}')+1:]
            extracted = extracted[:extracted.rfind('}')+1]
            return extracted, modified_words + append
        return None, words

    @staticmethod
    def extract_dialogue_stat(words, extra_data):
        if words.find(StringExtractor.DIALOGUE_STATE_ATTACH) != -1:
            matches = list(re.finditer(StringExtractor.DIALOGUE_STATE_ATTACH + StringExtractor.DIALOGUE_STATE_FORMAT, words))
            if len(matches):
                match = matches[0]
                modified_words = words.replace(match.group(0), '')
                if match.group(0).find('1') != -1:
                    extra_data['dialogue_status'] = True
                    return modified_words
                return modified_words
        return words

    @staticmethod
    def extract_voice(words):
        # has bug don't use it
        if words.find(StringExtractor.VOICE_SEPARATOR) != -1:
            voice = words.split(StringExtractor.VOICE_SEPARATOR)[0]
            return voice, words.replace(StringExtractor.VOICE_SEPARATOR, '')
        return None, words

    @staticmethod
    def extract_business_identify(words):
        matches = list(re.finditer(StringExtractor.BUSINESS_IDENTIFIER, words))
        if len(matches):
            match = matches[0]
            return match.group(1), words.replace(match.group(0), '')
        return None, words

    @staticmethod
    def listen_silence(words, extra_data):
        if words is None:
            return words
        if words.find(StringExtractor.LISTEN_SILENCE_SEPARATOR) != -1:
            extra_data['close_mic'] = True
            return words.replace(StringExtractor.LISTEN_SILENCE_SEPARATOR, '')
        if words.find(StringExtractor.LISTEN_SILENCE_SEPARATOR_2) != -1:
            extra_data['close_mic'] = True
            return words.replace(StringExtractor.LISTEN_SILENCE_SEPARATOR_2, '')
        return words

    @staticmethod
    def end_session(words, extra_data):
        if words is None:
            return words
        if words.find(StringExtractor.FAIL_HANDLE_SEPARATOR) != -1:
            extra_data['fail_handle'] = True
            return words.replace(StringExtractor.FAIL_HANDLE_SEPARATOR, '')
        if words.find(StringExtractor.END_SESSION_SEPARATOR) != -1:
            extra_data['end_session'] = True
            return words.replace(StringExtractor.END_SESSION_SEPARATOR, '')
        return words

    @staticmethod
    def cut_answer(words):
        if words is None:
            return words
        pos = words.find(StringExtractor.CUT_SEPARATOR)
        if pos != -1:
            return words.split(StringExtractor.CUT_SEPARATOR)[0]
        return words


if __name__ == "__main__":
    print((allowed_chat_key("asdpoifu+_+_#$%^)&%&12345@@@1234")))

    print((allowed_bot_msg_filter("123+321-1×以5÷1等于多少")))

    print((AnswerTokenType.QUERY_ATTACH.value))

    test_cases = [
        '你好，我是订票机器人。 您想飞到哪个城市？    为您查到如下航班信息：叕n有1张成人票(如果需要更改机票的人数信息，请告诉需要几张成人票，几张儿童票和几张婴儿票)嫐{"start_airport":"HRB","tickets":[{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T10:55:00+0800"],"aircraft":["73A","738"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","3:10"],"number":["FM9174","FM9171"],"carrier":["上海航空","上海航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T07:45:00+0800"],"hasBeenTranslated":true,"carrier_code":["FM","FM"],"departure_city_code":["HRB","PVG"]},{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T16:05:00+0800"],"aircraft":["73A","738"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","4:45"],"number":["FM9174","FM9173"],"carrier":["上海航空","上海航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T11:20:00+0800"],"hasBeenTranslated":true,"carrier_code":["FM","FM"],"departure_city_code":["HRB","PVG"]},{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T19:00:00+0800"],"aircraft":["73A","320"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","4:45"],"number":["MU9174","MU5611"],"carrier":["中国东方航空","中国东方航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T14:15:00+0800"],"hasBeenTranslated":true,"carrier_code":["MU","MU"],"departure_city_code":["HRB","PVG"]}],"voice_words":"为您查到如下航班信息：","return_trip":"true","destination_airport":"SHA"} 要订这张票吗？    为您查到如下航班信息：叕n有1张成人票(如果需要更改机票的人数信息，请告诉需要几张成人票，几张儿童票和几张婴儿票)嫐{"start_airport":"HRB","tickets":[{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T19:00:00+0800"],"aircraft":["73A","320"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","4:45"],"number":["MU9174","MU5611"],"carrier":["中国东方航空","中国东方航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T14:15:00+0800"],"hasBeenTranslated":true,"carrier_code":["MU","MU"],"departure_city_code":["HRB","PVG"]},{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T16:05:00+0800"],"aircraft":["73A","738"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","4:45"],"number":["FM9174","FM9173"],"carrier":["上海航空","上海航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T11:20:00+0800"],"hasBeenTranslated":true,"carrier_code":["FM","FM"],"departure_city_code":["HRB","PVG"]},{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T10:55:00+0800"],"aircraft":["73A","738"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","3:10"],"number":["FM9174","FM9171"],"carrier":["上海航空","上海航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T07:45:00+0800"],"hasBeenTranslated":true,"carrier_code":["FM","FM"],"departure_city_code":["HRB","PVG"]}],"voice_words":"为您查到如下航班信息：","return_trip":"true","destination_airport":"SHA"} 要订这张票吗？    为您查到如下航班信息：叕n有1张成人票(如果需要更改机票的人数信息，请告诉需要几张成人票，几张儿童票和几张婴儿票)嫐{"start_airport":"HRB","tickets":[{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T19:00:00+0800"],"aircraft":["73A","320"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","4:45"],"number":["MU9174","MU5611"],"carrier":["中国东方航空","中国东方航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T14:15:00+0800"],"hasBeenTranslated":true,"carrier_code":["MU","MU"],"departure_city_code":["HRB","PVG"]},{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T16:05:00+0800"],"aircraft":["73A","738"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","4:45"],"number":["FM9174","FM9173"],"carrier":["上海航空","上海航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T11:20:00+0800"],"hasBeenTranslated":true,"carrier_code":["FM","FM"],"departure_city_code":["HRB","PVG"]},{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T10:55:00+0800"],"aircraft":["73A","738"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","3:10"],"number":["FM9174","FM9171"],"carrier":["上海航空","上海航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T07:45:00+0800"],"hasBeenTranslated":true,"carrier_code":["FM","FM"],"departure_city_code":["HRB","PVG"]}],"voice_words":"为您查到如下航班信息：","return_trip":"true","destination_airport":"SHA"} 要订这张票吗？    为您查到如下航班信息：叕n有1张成人票(如果需要更改机票的人数信息，请告诉需要几张成人票，几张儿童票和几张婴儿票)嫐{"start_airport":"HRB","tickets":[{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T19:00:00+0800"],"aircraft":["73A","320"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","4:45"],"number":["MU9174","MU5611"],"carrier":["中国东方航空","中国东方航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T14:15:00+0800"],"hasBeenTranslated":true,"carrier_code":["MU","MU"],"departure_city_code":["HRB","PVG"]},{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T16:05:00+0800"],"aircraft":["73A","738"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","4:45"],"number":["FM9174","FM9173"],"carrier":["上海航空","上海航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T11:20:00+0800"],"hasBeenTranslated":true,"carrier_code":["FM","FM"],"departure_city_code":["HRB","PVG"]},{"arrival_city_code":["PVG","HRB"],"arrival_time":["2018-05-23T22:20:00+0800","2018-05-24T10:55:00+0800"],"aircraft":["73A","738"],"arrival_airport":["上海浦东国际机场","哈尔滨太平国际机场"],"cabin":["经济舱","经济舱"],"departure_airport_code":["HRB","PVG"],"arrival_airport_code":["PVG","HRB"],"duration":["5:20","3:10"],"number":["FM9174","FM9171"],"carrier":["上海航空","上海航空"],"departure_airport":["哈尔滨太平国际机场","上海浦东国际机场"],"price":"1169","departure_time":["2018-05-23T17:00:00+0800","2018-05-24T07:45:00+0800"],"hasBeenTranslated":true,"carrier_code":["FM","FM"],"departure_city_code":["HRB","PVG"]}],"voice_words":"为您查到如下航班信息：","return_trip":"true","destination_airport":"SHA"} 要订这张票吗？ 很高兴和你聊天，下次见。',
        "asdfasdfasfd啚ab8141b4-31ad-45de-b0f6-579fc61baaa1asd歮fasdfasdfa",
        "asdfasdfasfd嬲ab8141b4-31ad-45de-b0f6-579fc61baaa1asdfasdfasdfa嫐123456",
        "asdfasdfasfd嬲ab41b4-31ad-45de-b0f6-579fc61baaa1asdfasdfasdfa嫐12345歮6",
        "asdfasdfasfd嫐{this is a json} fuccccccc歮",
        "asdfasdfasfd焱1asdf19asd歮1f8",
        "asdfasdfasfd囡1asdf19asd1歮f8",
        "事務{MUSCIC_TEST}所{MUSIC}"
    ]

    import json

    for test_case in test_cases:
        extracted_type, extracted_token, result = StringExtractor.extract(test_case)
        print((extracted_type, extracted_token))
        print(result)
        print(('Json: ' + json.dumps(StringExtractor.extract_json(test_case))))
        print(('State: ' + str(StringExtractor.extract_dialogue_stat(test_case, {}))))
        print(('Voice: ' + str(StringExtractor.extract_voice(test_case))))
        print(('Cut: ' + str(StringExtractor.cut_answer(test_case))))
        print(('Business: ' + str(StringExtractor.extract_business_identify(test_case))))
        print()
