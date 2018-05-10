import threading
from grader import Grader


class GraderThread(threading.Thread):

    def __init__(self, shared_counter, test_config):
        super(GraderThread, self).__init__()
        self.grader = Grader()

        self.shared_counter = shared_counter
        self.test_config = test_config

    def init(self):
        self.grader.init(self.test_config)

    def grade(self):
        if self.grader.test() > 0:
            self.shared_counter.increment()

    def run(self):
        self.grade()
