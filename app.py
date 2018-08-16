import sys
import time
from time import sleep

import multiprocessing

from grader_multitask import GraderThread
from grader_multitask import GraderProcess

from grader import Grader
from model.shared_counter import SharedCounter

from controller.config_file_handler import YamlConfigFileHandler

from init import init_log_file
from init import report_logger

from dns_cache import _set_dns_cache

GRADER_VERSION = '1.4.0'

if __name__ == '__main__':
    report_logger.info("QiwuGrader ver {0}".format(GRADER_VERSION))

    # use dns cache
    _set_dns_cache()

    # test configuration file name
    test_config_file_name = 'test.yml'
    # number of sessions per hour
    test_session = 1
    # test session length (seconds)
    test_length = 5

    # Parse parameters from the command line
    test_config_file_name_list = []
    argv = sys.argv[1:]

    for yml in sys.argv[1:]:
        if yml.endswith('.yml'):
            test_config_file_name_list.append(yml)
            argv.remove(yml)

    if len(argv) >= 1:
        test_session = int(argv[0])

    if len(argv) == 2:
        test_length = int(argv[1])

    def run(test_config_file_name):
        test_config = YamlConfigFileHandler(test_config_file_name)

        if test_session == 1:  # single session grade
            # init_log_file()

            grader = Grader()
            grader.init(test_config)
            grader.test()
        elif test_session > 1:  # multi session grade
            # calculate thread spawn interval
            spawn_interval = test_length / (test_session * 1.0)

            # determine grader class
            use_process = False
            handler_count = test_session
            session_per_handler = 1
            Handler_Class = GraderThread

            # use process to speed up grade
            if test_session > 512:
                use_process = True
                handler_count = multiprocessing.cpu_count()
                session_per_handler = test_session / handler_count
                Handler_Class = GraderProcess

            # count the number of spawned sessions
            session_count = 0

            # thread safe success counter
            success_count = SharedCounter()

            # process time counter
            process_time = time.time()

            # thread group
            threads = []

            # if not use_process and test_session <= 100:
            #     init_log_file()

            report_logger.info("Testing {0} sessions in {1} seconds, interval: {2}, using class {3}"
                               .format(test_session, test_length, spawn_interval, Handler_Class.__name__))
            report_logger.info("Warming up ...")

            warm_up_time = time.time()
            # Spawn threads
            while session_count < handler_count:
                grader_handler = Handler_Class(success_count, test_config,
                                               loop=session_per_handler, spawn_interval=spawn_interval * handler_count)
                grader_handler.init()

                threads.append(grader_handler)
                session_count += 1

            report_logger.info("Warm up process finished in {0} seconds".format(time.time() - warm_up_time))

            launch_time = time.time()
            # Start threads
            for grader_handler in threads:
                grader_handler.start()

                # Wait for spawn interval
                sleep(spawn_interval)

            report_logger.info("{0} sessions started in {1}".format(
                int(session_count * session_per_handler), time.time() - launch_time))

            # Wait for all threads to finish
            for grader_handler in threads:
                grader_handler.join()

            report_logger.info(
                "Result: {0} / {1} passed. Total time: {2}".format(
                    success_count.value(), int(session_count * session_per_handler),
                    time.time() - process_time
                )
            )


    # Test all configs
    if not test_config_file_name_list:
        test_config_file_name_list.append('test.yml')

    # if test_session == 1:  # single session grade
    roll_log_file = init_log_file()

    for test_config_file_name in test_config_file_name_list:
        run(test_config_file_name)
        if test_config_file_name != test_config_file_name_list[-1]:
            report_logger.info('=====' * 20)
            if test_session == 1:
                roll_log_file()
