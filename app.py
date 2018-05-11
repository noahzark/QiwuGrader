import sys
import time
from time import sleep

from grader_thread import GraderThread
from grader import Grader
from model.shared_counter import SharedCounter

from controller.config_file_handler import YamlConfigFileHandler

from init import report_logger

GRADER_VERSION = '1.2.2'

if __name__ == '__main__':
    report_logger.info("QiwuGrader ver {0}".format(GRADER_VERSION))

    # test configuration file name
    test_config_file_name = 'test.yml'
    # number of sessions per hour
    test_session = 1
    # test session length (seconds)
    test_length = 5

    # Parse parameters from the command line
    if len(sys.argv) >= 2:
        test_config_file_name = sys.argv[1]
    if len(sys.argv) >= 3:
        test_session = int(sys.argv[2])
    if len(sys.argv) == 4:
        test_length = int(sys.argv[3])

    test_config = YamlConfigFileHandler(test_config_file_name)

    if test_session == 1:  # single session grade
        grader = Grader()
        grader.test(test_config)
    elif test_session > 1:  # multi session grade
        # calculate thread spawn interval
        spawn_interval = test_length / (test_session * 1.0)
        # count the number of spawned sessions
        session_count = 0
        # thread safe success counter
        success_count = SharedCounter()
        # process time counter
        process_time = time.time()
        # thread group
        threads = []

        report_logger.info("Testing {0} sessions in {1} seconds, interval: {2}".format(test_session, test_length, spawn_interval))
        report_logger.info("Warming up ...")

        warm_up_time = time.time()

        # avoid dots to speed up
        append = threads.append
        # Spawn threads
        while session_count < test_session:
            grader_thread = GraderThread(success_count, test_config)
            grader_thread.init()
            append(grader_thread)

            session_count += 1

        report_logger.info("Warm up process finished in {0} seconds".format(time.time() - warm_up_time))

        launch_time = time.time()
        need_sleep = 0
        if spawn_interval > 0.001:
            need_sleep = 1

        # Start threads
        for grader_thread in threads:
            grader_thread.start()

            # Wait for spawn interval
            need_sleep and sleep(spawn_interval)

        report_logger.info("{0} sessions started in {1}".format(session_count, time.time() - launch_time))

        # Wait for all threads to finish
        for grader_thread in threads:
            grader_thread.join()

        report_logger.info(
            "Result: {0} / {1} passed. Total time: {2}".format(
                success_count.value(), session_count,
                time.time() - process_time
            )
        )
