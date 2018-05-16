import threading
import multiprocessing
from abc import abstractmethod
from time import sleep

from grader import Grader
from model.shared_counter import SharedCounter


class GraderSkeleton:

    def __init__(self, shared_counter, test_config, kwargs):
        self.grader = Grader()

        self.shared_counter = shared_counter
        self.test_config = test_config
        self.loop = kwargs.get('loop', 1)
        self.spawn_interval = kwargs.get('spawn_interval', 0)

    def init(self):
        pass

    @abstractmethod
    def grade(self):
        pass


class GraderThread(GraderSkeleton, threading.Thread):

    def __init__(self, shared_counter, test_config, **kwargs):
        super(GraderThread, self).__init__(shared_counter, test_config, kwargs)
        threading.Thread.__init__(self)

    def init(self):
        self.grader.init(self.test_config)

    def grade(self):
        if self.grader.test() > 0:
            self.shared_counter.increment()

    def run(self):
        while self.loop > 0:
            self.grade()
            self.loop -= 1
            sleep(self.spawn_interval)


class GraderProcess(GraderSkeleton, multiprocessing.Process):

    def __init__(self, shared_counter, test_config, **kwargs):
        super(GraderProcess, self).__init__(shared_counter, test_config, kwargs)
        multiprocessing.Process.__init__(self)

        self.internal_counter = SharedCounter()

    def grade(self):
        threads = []

        session_count = 0
        while session_count < self.loop:
            grader_thread = GraderThread(self.internal_counter, self.test_config)
            grader_thread.init()

            threads.append(grader_thread)
            session_count += 1

        for grader_thread in threads:
            grader_thread.start()

            # Wait for spawn interval
            sleep(self.spawn_interval)

        for grader_thread in threads:
            grader_thread.join()

        self.shared_counter.increment(self.internal_counter.value())

    def run(self):
        self.grade()
