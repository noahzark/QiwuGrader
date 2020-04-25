import threading
import multiprocessing
from abc import abstractmethod
from time import sleep

from qiwugrader.grader.grader_core import Grader
from qiwugrader.model.shared_counter import SharedCounter


class GraderSkeleton:

    def __init__(self, shared_counter, test_config, time_counter, kwargs):
        self.shared_counter = shared_counter
        self.time_counter = time_counter

        self.test_config = test_config

        # how many times need to run the test
        self.loop = kwargs.get('loop', 1)
        # how long each thread is spawned
        self.spawn_interval = kwargs.get('spawn_interval', 0)

    def init(self):
        pass

    @abstractmethod
    def grade(self):
        pass

    def get_question_number(self):
        return 0


class GraderThread(GraderSkeleton, threading.Thread):

    def __init__(self, shared_counter, test_config, time_counter=SharedCounter(val_type='d'), **kwargs):
        super(GraderThread, self).__init__(shared_counter, test_config, time_counter, kwargs)
        threading.Thread.__init__(self)

        # initialize grader
        self.grader = Grader()

    def init(self):
        self.grader.init(self.test_config)

    def grade(self):
        # calculate result
        success_count, success_time = self.grader.test()
        if success_count > 0:
            self.shared_counter.increment()
            self.time_counter.increment(success_time)

    def run(self):
        while self.loop > 0:
            self.grade()
            self.loop -= 1

            # only sleep when we need to do next grade
            if self.loop > 0:
                sleep(self.spawn_interval)

    def get_question_number(self):
        return len(self.grader.questions)


class GraderProcess(GraderSkeleton, multiprocessing.Process):

    def __init__(self, shared_counter, test_config, time_counter=SharedCounter(val_type='d'), **kwargs):
        super(GraderProcess, self).__init__(shared_counter, test_config, time_counter, kwargs)
        multiprocessing.Process.__init__(self)

        # use an internal counter to reduce global success counter locks
        self.internal_counter = SharedCounter()
        self.internal_timer = SharedCounter(val_type='d')

        self.question_count = 0

    def grade(self):
        # warm up threads
        threads = []

        session_count = 0
        while session_count < self.loop:
            grader_thread = GraderThread(self.internal_counter, self.test_config, self.internal_timer)
            grader_thread.init()

            threads.append(grader_thread)
            session_count += 1
            self.question_count = grader_thread.get_question_number()

        # do real grade
        for grader_thread in threads:
            grader_thread.start()

            # wait for spawn interval
            sleep(self.spawn_interval)

        # wait for threads
        for grader_thread in threads:
            grader_thread.join()

        # calculate success count in the end
        self.shared_counter.increment(self.internal_counter.value())
        self.time_counter.increment(self.internal_timer.value())

    def run(self):
        self.grade()

    def get_question_number(self):
        return self.question_count
