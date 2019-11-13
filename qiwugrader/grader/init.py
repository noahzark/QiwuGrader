import logging.handlers
import os
import sys

from qiwugrader.grader.compatible import file_encoding


FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
# logging
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# init report logger
report_logger = logging.getLogger("GradeReport")
report_logger.setLevel(logging.INFO)

# init test logger
test_logger = logging.getLogger("TestLog")
test_logger.setLevel(logging.INFO)

# init csv logger
csv_logger = logging.getLogger("CsvLog")
csv_logger.setLevel(logging.INFO)

# disable library logging
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.CRITICAL)
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.WARNING)


def init_log_file():
    from datetime import datetime
    time_str = str(datetime.now()).replace(' ', '_').replace(':', '-')

    path = os.path.abspath(os.getcwd())
    log_path = os.path.join(path, 'logs')
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    grade_report_filename = 'QiwuGrade-{0}.log'.format(time_str)
    log_file_path = os.path.join(log_path, grade_report_filename)
    report_log_handler = logging.handlers.RotatingFileHandler(log_file_path, backupCount=50, encoding=file_encoding)
    report_logger.addHandler(report_log_handler)

    grade_log_filename = 'QiwuTest-{0}.log'.format(time_str)
    log_file_path = os.path.join(log_path, grade_log_filename)
    test_log_handler = logging.handlers.RotatingFileHandler(log_file_path, backupCount=50, encoding=file_encoding)
    test_logger.addHandler(test_log_handler)

    csv_log_filename = 'QiwuTest-{0}.csv'.format(time_str)
    log_file_path = os.path.join(log_path, csv_log_filename)
    csv_log_handler = logging.handlers.RotatingFileHandler(log_file_path, backupCount=50, encoding=file_encoding)
    csv_logger.addHandler(csv_log_handler)

    def roll_log_file():
        report_log_handler.doRollover()
        test_log_handler.doRollover()
        csv_log_handler.doRollover()

    # do roll log file
    need_roll = os.path.isfile(log_path)

    # don't roll since we are using time as the filename now
    if False and need_roll:
        roll_log_file()
    return roll_log_file
