import logging.handlers
import os

from compatible import file_encoding

FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
# logging
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt='%Y-%m-%d %H:%M:%S'
)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0, parent_dir)

logPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), './logs')
if not os.path.exists(logPath):
    os.makedirs(logPath)

# init report logger
GRADE_REPORT_FILENAME = './logs/QiwuGrade.log'
logPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), GRADE_REPORT_FILENAME)
report_logHandler = logging.handlers.RotatingFileHandler(logPath, backupCount=50, encoding=file_encoding)
report_logger = logging.getLogger("GradeReport")
report_logger.setLevel(logging.INFO)
report_logger.addHandler(report_logHandler)

# init test logger
GRADE_LOG_FILENAME = './logs/QiwuTest.log'
logPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), GRADE_LOG_FILENAME)
test_logHandler = logging.handlers.RotatingFileHandler(logPath, backupCount=50, encoding=file_encoding)
test_logger = logging.getLogger("TestLog")
test_logger.setLevel(logging.INFO)
test_logger.addHandler(test_logHandler)

# init csv logger
CSV_LOG_FILENAME = './logs/QiwuTest.csv'
logPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), CSV_LOG_FILENAME)
csv_logHandler = logging.handlers.RotatingFileHandler(logPath, backupCount=50, encoding=file_encoding)
csv_logger = logging.getLogger("CsvLog")
csv_logger.setLevel(logging.INFO)
csv_logger.addHandler(csv_logHandler)

# disable library logging
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.CRITICAL)
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.WARNING)

# do roll log file
needRoll = os.path.isfile(logPath)
if needRoll:
    report_logHandler.doRollover()
    test_logHandler.doRollover()
    csv_logHandler.doRollover()
