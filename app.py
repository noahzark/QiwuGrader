import sys
import time
from time import sleep

from grader_thread import GraderThread
from grader import Grader
from model.shared_counter import SharedCounter

from controller.config_file_handler import YamlConfigFileHandler

from init import report_logger

GRADER_VERSION = '1.1.3'

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
        # Spawn threads
        while session_count < test_session:
            grader_thread = GraderThread(success_count, test_config)
            threads.append(grader_thread)
            grader_thread.start()

            session_count += 1

            # Wait for spawn interval
            sleep(spawn_interval)

        report_logger.info("{0} sessions started".format(session_count))

        # Wait for all threads to finish
        for grader_thread in threads:
            grader_thread.join()

        report_logger.info(
            "Result: {0} / {1} passed. Total ime: {0}".format(
                success_count.value(), session_count,
                time.time() - process_time
            )
        )
