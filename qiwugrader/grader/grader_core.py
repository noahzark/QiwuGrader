# -*- coding: utf-8 -*-
import time
import re
import json
import os
import xlrd

from qiwugrader.controller.config_file_handler import YamlConfigFileHandler
from qiwugrader.controller.private_msg_handler import pMsgHandler
from qiwugrader.controller.single_dialogue_handler import SingleDialogueHandler

from qiwugrader.util.string_helper import id_generator

from qiwugrader.grader.init import test_logger
from qiwugrader.grader.init import report_logger
from qiwugrader.grader.init import csv_logger

from qiwugrader.grader.compatible import to_str
from qiwugrader.grader.compatible import write_utf_bom

from qiwugrader.request.single_dialogue import SingleDialogue

try:
    basestring
except NameError:
    basestring = str


class Grader():

    ERROR_REPLY = u'服务器通信错误。'.encode('utf-8')
    TIMEOUT_REPLY = u'请让我再想想。'.encode('utf-8')
    REQUEST_TIMEOUT = SingleDialogue.REQUEST_TIMEOUT.encode('utf-8')
    REQUEST_ERROR_REPLY = SingleDialogue.ERROR_REPLY.encode('utf-8')

    def __init__(self):
        self.config = None

        self.server = None

        self.test_type = 'knowledge'

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

    def test_robot(self, name, questions, answers, sessions=None):
        if sessions is None:
            sessions = {}

        if self.test_type == 'api':
            test_service = SingleDialogueHandler(self.config)
        else:
            test_service = pMsgHandler(self.config, test_logger)

        uid = "grader_" + id_generator(20)
        last_session = 1

        test_service.robot_name = name

        # items_op = getattr(questions, "iteritems", None)
        # question_items = callable(items_op) and questions.iteritems() or questions.items()

        grade = 0
        total_time = 0
        for i, question in questions.items():
            if sessions.get(i, -1) != last_session:
                uid = "grader_" + id_generator(20)
                last_session = sessions.get(i)

            process_time = time.time()
            # turn question into a string and handle chat
            if type(question) == int:
                question_str = str(question)
            else:
                question_str = question
            response = test_service.handle_chat(uid, question_str, login_wait=self.question_interval)
            data = None
            if self.print_csv:
                data, response = self.handle_string(response)

            chat_key = None
            if hasattr(test_service, 'tokens') and uid in test_service.tokens:
                chat_key = test_service.tokens[uid]
            process_time = time.time() - process_time

            correct = True
            if response == self.TIMEOUT_REPLY:
                correct = False
            if response == self.REQUEST_TIMEOUT:
                correct = False
            if response == self.REQUEST_ERROR_REPLY:
                correct = False

            answer_str = 'No answer found for question {0}'.format(i)
            if answers and i in answers and answers[i]:
                check_target = data or response

                answer = answers[i]
                correct = False

                if isinstance(answer, dict):
                    if 'multi' in answer:
                        answer_str = json.dumps(answer, ensure_ascii=False).encode('utf-8')
                        for j, item in enumerate(answer['multi']):
                            if check_target.find(item.encode('utf-8')) != -1:
                                correct = True
                                break
                    if 'regex' in answer:
                        answer_str = answer['regex'].encode('utf-8')
                        match_obj = re.match(answer_str, check_target)
                        if match_obj:
                            correct = True
                else:
                    answer_str = answer.encode('utf-8')
                    if check_target.find(to_str(answer_str)) != -1:
                        correct = True
            else:
                if response == self.ERROR_REPLY:
                    correct = False

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
                    csv_string += "," + data
                csv_logger.info(csv_string)

            if self.print_info:
                if self.print_conversation:
                    if self.print_details:
                        question_str = to_str(question_str.encode('utf-8'))
                        test_logger.info("Session {0} Question {1}: {2}".format(last_session, i, question_str))

                        response = to_str(response)
                        if chat_key:
                            test_logger.info("Chatkey: {1} Response: {0}".format(response, chat_key))
                        else:
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
                    test_logger.warning("Q {0} Wrong answer: {1}".format(i, to_str(response)))
                    # print ("Q {0} Wrong answer: {1}".format(i, response))

            if not correct and self.suspend_on_error:
                break

            if self.question_interval > 0.1:
                time.sleep(self.question_interval)
        # end of question loop
        if self.print_csv:
            csv_logger.info("{0},{1} / {2},{3},{4}".format(name, grade, len(questions), total_time, total_time/len(questions)))

        report_logger.info("{0} grade: {1} / {2}\ntime: {3} avg: {4}".format(name, grade, len(questions), total_time, total_time/len(questions)))
        return grade == len(questions) and True or False, total_time

    def init(self, config: YamlConfigFileHandler):
        assert(isinstance(config, YamlConfigFileHandler))
        self.config = config

        self.test_type = config.get_config('type', self.test_type)

        self.server = config.get_config("server", self.server)

        options = config.get_config("options", {
            'suspend_on_error': self.suspend_on_error,
            'question_interval': self.question_interval
        })
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
        if not os.path.exists(questions_xlsx):
            self.questions = config.get_config("questions", self.questions)
            self.answers = config.get_config("answers", self.answers)
        else:
            workbook = xlrd.open_workbook(questions_xlsx)
            worksheet = workbook.sheet_by_name(workbook.sheet_names()[0])
            self.questions = {}
            for i in range(2, worksheet.nrows+1):
                self.sessions[i-1] = int(worksheet.cell_value(i-1, 0))
                self.questions[i-1] = worksheet.cell_value(i-1, 1)
                if worksheet.ncols > 2:
                    answer = worksheet.cell_value(i-1, 2)
                    self.answers[i-1] = answer
            self.print_csv = True

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
        from qiwugrader.util.string_helper import StringExtractor, AnswerTokenType
        import requests
        extra_data = {}
        result = to_str(result)

        # extract image data
        pic_token, result = StringExtractor.extract_type(AnswerTokenType.IMAGE_ATTACH, result)

        # extract extra data
        data_token, result = StringExtractor.extract_type(AnswerTokenType.QUERY_ATTACH, result)
        if data_token:
            data_url = self.config.get_config('data_url', 'http://robot-service-test.chewrobot.com/api/chat/data')
            if data_url:
                extra_data = requests.get(
                    data_url,
                    headers={'key': data_token}
                ).json()
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
                slots.append('%s=%s' % (item['name'], item['value']))
            slots.sort()
            extra_data = ' '.join(slots)
        else:
            extra_data = str(extra_data)

        return extra_data, result
