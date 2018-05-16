import threading
import multiprocessing

from grader import Grader


class GraderSkeleton:

    def __init__(self, shared_counter, test_config):
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


class GraderThread(GraderSkeleton, threading.Thread):

    def __init__(self, shared_counter, test_config):
        super(GraderThread, self).__init__(shared_counter, test_config)
        threading.Thread.__init__(self)


class GraderProcess(GraderSkeleton, multiprocessing.Process):

    def __init__(self, shared_counter, test_config):
        super(GraderProcess, self).__init__(shared_counter, test_config)
        multiprocessing.Process.__init__(self)
