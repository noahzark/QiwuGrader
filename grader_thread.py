import threading
from grader import Grader


class GraderThread(threading.Thread):

    def __init__(self, shared_counter, test_config):
        super(GraderThread, self).__init__()
        self.grader = Grader()

        self.shared_counter = shared_counter
        self.test_config = test_config

    def run(self):
        if self.grader.test(self.test_config) > 0:
            self.shared_counter.increment()
