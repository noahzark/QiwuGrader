# -*- coding: utf-8 -*-
import time
import re
import json
import os
import xlrd
import random

from qiwugrader.controller.config_file_handler import YamlConfigFileHandler
from qiwugrader.controller.private_msg_handler import pMsgHandler
from qiwugrader.controller.single_dialogue_handler import SingleDialogueHandler

from qiwugrader.util.string_helper import id_generator

from qiwugrader.grader.init import test_logger
from qiwugrader.grader.init import report_logger
from qiwugrader.grader.init import csv_logger

from qiwugrader.grader.compatible import to_str

from qiwugrader.util.string_helper import StringExtractor, AnswerTokenType
import requests

from qiwugrader.request.single_dialogue import SingleDialogue

try:
    basestring
except NameError:
    basestring = str


class Grader:

    ERROR_REPLY = u'服务器通信错误。'.encode('utf-8')
    TIMEOUT_REPLY = u'请让我再想想。'
    REQUEST_TIMEOUT = SingleDialogue.REQUEST_TIMEOUT.encode('utf-8')
    REQUEST_ERROR_REPLY = SingleDialogue.ERROR_REPLY.encode('utf-8')

    def __init__(self):
        self.config = None

        self.server = None

        self.test_type = 'knowledge'

        self.shuffle_session = False

        self.pause_on_error = False
        self.suspend_on_error = False

        self.print_csv = False
        self.question_interval = 1.0

        self.print_info = True
        self.print_conversation = True
        self.print_details = True
        self.print_correct_answer = True

        self.robots = None
        self.questions = {}
        self.sessions = {}
        self.answers = {}

        self.uid_prefix = 'Console.Test.'

    def test_robot(self, name, questions, answers, sessions=None):
        if sessions is None:
            sessions = {}

        if self.test_type == 'api':
            test_service = SingleDialogueHandler(self.config)
        else:
            test_service = pMsgHandler(self.config, test_logger)

        uid = self.uid_prefix + id_generator(20)
        last_session = 1

        test_service.robot_name = name

        # items_op = getattr(questions, "iteritems", None)
        # question_items = callable(items_op) and questions.iteritems() or questions.items()

        grade = 0
        total_time = 0
        for i, question in questions.items():
            if sessions.get(i, -1) != last_session:
                uid = self.uid_prefix + id_generator(20)
                last_session = sessions.get(i, -1)

            process_time = time.time()
            # turn question into a string and handle chat
            if type(question) == int:
                question_str = str(question)
            else:
                question_str = question
            response = test_service.handle_chat(uid, question_str, login_wait=0)
            data = None
            response = to_str(response)
            if response.find(AnswerTokenType.QUERY_ATTACH.value) != -1 \
                    or response.find(StringExtractor.DATA_ATTACH_SEPARATOR):
                try:
                    data, response = self.handle_string(response)
                except Exception:
                    test_logger.info("Failed to retrive data")

            chat_key = None
            if hasattr(test_service, 'tokens') and uid in test_service.tokens:
                chat_key = test_service.tokens[uid]
            process_time = time.time() - process_time

            correct = True
            if response.find(self.TIMEOUT_REPLY) == 0:
                correct = False
            if response == self.REQUEST_TIMEOUT:
                correct = False
            if response == self.REQUEST_ERROR_REPLY:
                correct = False

            answer_str = 'No answer found for question {0}'.format(i)
            if correct and answers and i in answers and answers[i]:
                response = to_str(response)
                # if data:
                #     temp_res = response
                #     response = data
                #     data = temp_res

                answer = answers[i]
                correct = False

                if isinstance(answer, dict):
                    if 'multi' in answer:
                        answer_str = json.dumps(answer, ensure_ascii=False).encode('utf-8')
                        for j, item in enumerate(answer['multi']):
                            if response.find(item.encode('utf-8')) != -1:
                                correct = True
                                break
                    if 'regex' in answer:
                        answer_str = answer['regex'].encode('utf-8')
                        match_obj = re.match(answer_str, response)
                        if match_obj:
                            correct = True
                else:
                    answer_str = answer.encode('utf-8')
                    if response.find(to_str(answer_str)) != -1:
                        correct = True

            if correct:
                grade += 1
            total_time += process_time

            if self.print_csv:
                csv_string = str(last_session)
                csv_string += ",Question {0}".format(i)
                csv_string += "," + uid
                csv_string += "," + to_str(question.encode('utf-8')).replace(",", "，")
                csv_string += "," + to_str(response).replace(",", "，")
                csv_string += "," + to_str(answer_str).replace(",", "，")
                csv_string += "," + (correct and "Passed" or "Wrong")
                csv_string += "," + "{:.5f}".format(process_time)
                if data:
                    csv_string += "," + str(len(data))
                    csv_string += "," + data
                csv_logger.info(csv_string)

            if self.print_info:
                if self.print_conversation:
                    if self.print_details:
                        question_str = to_str(question_str.encode('utf-8'))
                        test_logger.info("Session {0} Question {1}: {2}".format(last_session, i, question_str))

                        response = to_str(response)
                        if chat_key:
                            test_logger.info("Chatkey: {0})".format(chat_key))
                        test_logger.info("Response :" + response)

                        if self.print_correct_answer or not correct:
                            answer_str = to_str(answer_str)
                            test_logger.info("Answer: " + answer_str)

                        test_logger.info((correct and "Passed" or "Wrong") + " for " + uid)
                        test_logger.info("Processed in {:.5f} seconds".format(process_time))
                        test_logger.info("=============")
                    else:
                        test_logger.info("Question {0}: {1} in {2} seconds".format(i, correct and "Passed" or "Wrong", process_time))
                        if not correct:
                            test_logger.info("Answer: " + to_str(response))
                elif not correct:
                    test_logger.warning("Q {0} WA vc: {1}".format(i, to_str(response)))
                    # print ("Q {0} Wrong answer: {1}".format(i, response))

            if not correct and self.suspend_on_error:
                break

            if not correct and self.pause_on_error:
                test_logger.info("Pause thread for 10 seconds due to incorrect response")
                time.sleep(10)

            if self.question_interval > 0.1:
                time.sleep(self.question_interval)
        # end of question loop
        if self.print_csv:
            csv_logger.info("{0},{1} / {2},{3},{4}".format(name, grade, len(questions), total_time, total_time/len(questions)))

        report_logger.info("{0} grade: {1} / {2}\ntime: {3} avg: {4}".format(name, grade, len(questions), total_time, total_time/len(questions)))
        return grade == len(questions) and True or False, total_time

    def shuffle_sessions(self):
        temp_map = {}
        for i in range(1, len(self.questions) + 1):
            session_question_answer = temp_map.get(self.sessions[i], [])
            if i in self.answers:
                session_question_answer.append({
                    'session': self.sessions[i],
                    'question': self.questions[i],
                    'answer': self.answers[i]
                })
            else:
                session_question_answer.append({
                    'session': self.sessions[i],
                    'question': self.questions[i]
                })
            temp_map[self.sessions[i]] = session_question_answer

        temp_map_keys = []
        for temp_map_key in temp_map.keys():
            temp_map_keys.append(temp_map_key)

        random.shuffle(temp_map_keys)

        self.sessions = {}
        self.questions = {}
        self.answers = {}

        session_count = 0
        for temp_map_key in temp_map_keys:
            temp_session = temp_map[temp_map_key]
            for session in temp_session:
                self.sessions[session_count] = session['session']
                self.questions[session_count] = session['question']
                if 'answer' in temp_map:
                    self.answers[session_count] = session['answer']
                session_count += 1

    def init_xlsx(self, input_file):
        workbook = xlrd.open_workbook(input_file)
        worksheet = workbook.sheet_by_name(workbook.sheet_names()[0])
        self.questions = {}
        last_session = 0
        for i in range(2, worksheet.nrows + 1):
            session_cell = worksheet.cell_value(i - 1, 0)
            if session_cell:
                last_session = int(session_cell)
            self.sessions[i - 1] = last_session

            self.questions[i - 1] = worksheet.cell_value(i - 1, 1)
            if worksheet.ncols > 2:
                answer = worksheet.cell_value(i - 1, 2)
                self.answers[i - 1] = answer
        self.print_csv = True

    def init_json(self, input_file):
        with open(input_file, encoding='utf-8') as fp:
            input_json = json.load(fp)
            i = 1
            for question in input_json:
                labels = question['labels']
                self.questions[i] = question['sentence']

                nlus = []
                for label in labels:
                    nlus.append('{}={} '.format(label['sign'][0]['type'], label['sign'][0]['text']))

                self.answers[i] = ' '.join(nlus).strip()

                i += 1

    def init_txt(self, input_file):
        with open(input_file, encoding='utf-8') as fp:
            input_txt = fp.readlines()

        slot_regex = re.compile(r'<([a-zA-Z_]*)>')
        slots = {}

        if input_txt:
            for l in input_txt:
                ss = slot_regex.findall(l)
                for s in ss:
                    slots[s] = []

        print(slots)
        workbook = xlrd.open_workbook(input_file.replace('txt', 'config.xlsx'))
        worksheet = workbook.sheet_by_name(workbook.sheet_names()[0])

        for col in range(0, worksheet.ncols):
            target = worksheet.cell_value(0, col)

            if target not in slots:
                print('useless column:', target)
                continue

            for row in range(1, worksheet.nrows):
                v = worksheet.cell_value(row, col)
                if not v:
                    break
                slots[target].append(v)

        for slot in slots:
            if len(slots[slot]) == 0:
                print('none value for <' + slot + '>')

        import time
        start = time.time()
        sentences = {}

        for l in input_txt:
            def func(temp_s, answer_s=''):
                temp_ss = slot_regex.findall(temp_s)
                if len(temp_ss) == 0:
                    sentences[temp_s] = answer_s.strip()
                else:
                    temp_slot = temp_ss[0]
                    targets = slots[temp_slot]
                    for temp_target in targets:
                        func(temp_s.replace('<' + temp_slot + '>', str(temp_target)),
                             answer_s + ' {}={}'.format(temp_slot, temp_target))

            func(l.strip())

        print('generated', len(sentences), 'sentences')
        print('used', time.time() - start, 'seconds')
        start = time.time()

        csv_format = '{},{},{}\n'
        with open(input_file.replace('txt', 'csv'), mode='w', encoding='utf-8') as f:
            f.write(csv_format.format('session', 'ask', 'answer'))

            i = 1
            for sentence in sentences:
                self.questions[i] = sentence
                self.answers[i] = sentences[sentence]

                f.write(csv_format.format(i, sentence, sentences[sentence]))

                i += 1

        print('wrote', i, 'lines')
        print('used', time.time() - start, 'seconds')

    def init(self, config: YamlConfigFileHandler):
        assert(isinstance(config, YamlConfigFileHandler))
        self.config = config

        self.test_type = config.get_config('type', self.test_type)

        self.server = config.get_config("server", self.server)

        options = config.get_config("options", {
            'shuffle_session': self.shuffle_session,
            'pause_on_error': self.pause_on_error,
            'suspend_on_error': self.suspend_on_error,
            'question_interval': self.question_interval
        })
        self.shuffle_session = options.get('shuffle_session', self.shuffle_session)
        self.pause_on_error = options.get('pause_on_error', self.pause_on_error)
        self.suspend_on_error = options.get('suspend_on_error', self.suspend_on_error)
        self.question_interval = options.get('question_interval', self.question_interval)

        robots = []
        if self.test_type == 'knowledge':
            robots = config.get_config("usernames", None)
            if not robots:
                robots = config.get_config("username", None)
        elif self.test_type == 'api':
            robots = config.get_config('name', 'Unknown')

        if isinstance(robots, basestring):
            self.robots = [robots]
        else:
            self.robots = robots

        questions_xlsx = config.filename.replace('.yml', '.xlsx')
        questions_json = config.filename.replace('.yml', '.json')
        questions_txt = config.filename.replace('.yml', '.txt')

        if os.path.exists(questions_xlsx):
            self.init_xlsx(questions_xlsx)
        elif os.path.exists(questions_json):
            self.init_json(questions_json)
        elif os.path.exists(questions_txt):
            self.init_txt(questions_txt)
        else:
            self.questions = config.get_config("questions", self.questions)
            self.answers = config.get_config("answers", self.answers)

        if self.shuffle_session:
            self.shuffle_sessions()

        configuration = config.get_config("output", {
            'print_info': self.print_info,
            'print_conversation': self.print_conversation,
            'print_details': self.print_details,
            'print_correct_answer': self.print_correct_answer,
            'print_csv': self.print_csv
        })
        self.print_info = configuration.get('print_info', self.print_info)
        self.print_conversation = configuration.get('print_conversation', self.print_conversation)
        self.print_details = configuration.get('print_details', self.print_details)
        self.print_correct_answer = configuration.get('print_correct_answer', self.print_correct_answer)
        self.print_csv = configuration.get('print_csv', self.print_csv)

        self.uid_prefix = config.get_config('uid_prefix', self.uid_prefix)

        if self.questions and len(self.questions) > 0:
            report_logger.info("grader ready, there are {0} questions".format(len(self.questions)))

    def test(self):
        success_count = 0
        total_time = 0

        if len(self.questions) == 0:
            return 1

        if self.robots is None or len(self.robots) == 0:
            report_logger.error("Couldn't find username to test, grader exit")
            return 0

        for i, robot in enumerate(self.robots):
            if self.print_info:
                test_logger.info("Testing robot {0}".format(robot))

            try:
                success, time_used = self.test_robot(robot, self.questions, self.answers, self.sessions)
                success_count += success and 1 or 0
                total_time += success and time_used or 0
            except Exception as e:
                test_logger.exception(e)

        return success_count, total_time

    def handle_string(self, result):
        extra_data = {}
        result = to_str(result)

        # extract image data
        pic_token, result = StringExtractor.extract_type(AnswerTokenType.IMAGE_ATTACH, result)

        # extract extra data
        data_token, result = StringExtractor.extract_type(AnswerTokenType.QUERY_ATTACH, result)
        if data_token:
            data_url = self.config.get_config('data_url', None)
            if data_url:
                r = requests.get(
                    data_url,
                    headers={'key': data_token},
                    timeout=2
                )
                extra_data = r.json()
            else:
                test_logger.warning("No data url found")

        data, result = StringExtractor.extract_json(result)
        if data:
            extra_data.update(json.loads(data))

        result = StringExtractor.extract_dialogue_stat(result, extra_data)

        result = StringExtractor.listen_silence(result, extra_data)

        result = StringExtractor.end_session(result, extra_data)

        result = StringExtractor.cut_answer(result)

        business, result = StringExtractor.extract_business_identify(result)

        if 'slots' in extra_data:
            extra_data = extra_data['slots']
            slots = []
            for item in extra_data:
                if item['name'] == 'chat_key':
                    continue
                if item['name'] == 'query_text':
                    continue
                if item['name'] == 'action_name':
                    continue
                if item['name'] == 'bot_name':
                    continue
                slots.append('%s=%s' % (item['name'], item['value']))
            slots.sort()
            extra_data = ' '.join(slots)
        else:
            extra_data = str(extra_data)

        return extra_data, result
