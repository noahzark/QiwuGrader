# -*- coding: utf-8 -*-
import time
import re
import json

from controller.config_file_handler import YamlConfigFileHandler
from controller.private_msg_handler import pMsgHandler
from controller.single_dialogue_handler import SingleDialogueHandler

from model.string_helper import id_generator

from grader.init import test_logger
from grader.init import report_logger
from grader.init import csv_logger

from grader.compatible import to_str
from grader.compatible import write_utf_bom

try:
    basestring
except NameError:
    basestring = str


class Grader():

    ERROR_REPLY = u'服务器通信错误。'.encode('utf-8')

    def __init__(self):
        self.config = {}

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
        self.answers = {}

    def test_robot(self, name, questions, answers):
        if self.test_type == 'api':
            test_service = SingleDialogueHandler(self.config)
        else:
            test_service = pMsgHandler(self.server, test_logger)

        uid = "grader_" + id_generator(10)

        test_service.robot_name = name

        if self.print_csv:
            write_utf_bom()

        # items_op = getattr(questions, "iteritems", None)
        # question_items = callable(items_op) and questions.iteritems() or questions.items()

        grade = 0
        total_time = 0
        for i, question in questions.items():
            process_time = time.time()
            # turn question into a string and handle chat
            if type(question) == int:
                question_str = str(question)
            else:
                question_str = question
            response = test_service.handle_chat(uid, question_str, login_wait=self.question_interval)
            chat_key = None
            if hasattr(test_service, 'tokens'):
                chat_key = test_service.tokens[uid]
            process_time = time.time() - process_time

            correct = True
            answer_str = 'No answer found for question {0}'.format(i)
            if answers and i in answers:
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
                    if response.find(answer_str) != -1:
                        correct = True
            else:
                if response == self.ERROR_REPLY:
                    correct = False

            if correct:
                grade += 1
            total_time += process_time

            if self.print_csv:
                csv_string = "Question {0},{1}".format(i, to_str(question.encode('utf-8')).replace(",", "，"))
                csv_string += "," + to_str(response).replace(",", "，")
                csv_string += "," + to_str(answer_str).replace(",", "，")
                csv_string += "," + (correct and "Passed" or "Wrong")
                csv_string += "," + "Processed in {:.5f} seconds".format(process_time)
                csv_logger.info(csv_string)

            if self.print_info:
                if self.print_conversation:
                    if self.print_details:
                        question_str = to_str(question_str.encode('utf-8'))
                        test_logger.info("Question {0}: {1}".format(i, question_str))

                        response = to_str(response)
                        if chat_key:
                            test_logger.info("Chatkey: {1} Response: {0}".format(response, chat_key))
                        else:
                            test_logger.info("Response :" + response)

                        if self.print_correct_answer or not correct:
                            answer_str = to_str(answer_str)
                            test_logger.info("Answer: " + answer_str)

                        test_logger.info(correct and "Passed" or "Wrong")
                        test_logger.info("Processed in {:.5f} seconds".format(process_time))
                        test_logger.info("=============")
                    else:
                        test_logger.info("Question {0}: {1} in {2} seconds".format(i, correct and "Passed" or "Wrong", process_time))
                        if not correct:
                            test_logger.info("Answer: " + response)
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

    def init(self, config):
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

        self.questions = config.get_config("questions", self.questions)
        self.answers = config.get_config("answers", self.answers)

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
                success, time_used = self.test_robot(robot, self.questions, self.answers)
                success_count += success and 1 or 0
                total_time += success and time_used or 0
            except Exception as e:
                test_logger.exception(e)

        return success_count, total_time
