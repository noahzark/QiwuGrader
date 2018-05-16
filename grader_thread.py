import threading
import multiprocessing

from grader import Grader


class GraderSkeleton:

    def __init__(self, shared_counter, test_config, loop=1):
        self.grader = Grader()

        self.shared_counter = shared_counter
        self.test_config = test_config
        self.loop = 1

    def init(self):
        self.grader.init(self.test_config)

    def grade(self):
        if self.grader.test() > 0:
            self.shared_counter.increment()

    def run(self):
        while self.loop > 0:
            self.grade()
            self.loop -= 1


class GraderThread(GraderSkeleton, threading.Thread):

    def __init__(self, shared_counter, test_config, **kwargs):
        super(GraderThread, self).__init__(shared_counter, test_config, kwargs)
        threading.Thread.__init__(self)


class GraderProcess(GraderSkeleton, multiprocessing.Process):

    def __init__(self, shared_counter, test_config, **kwargs):
        super(GraderProcess, self).__init__(shared_counter, test_config, kwargs)
        multiprocessing.Process.__init__(self)
