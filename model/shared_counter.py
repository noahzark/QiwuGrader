import time
from multiprocessing import Process, Value, Lock


class SharedCounter(object):
    def __init__(self, init_val=0):
        self.val = Value('i', init_val)
        self.lock = Lock()

    def increment(self, v=1):
        with self.lock:
            self.val.value += v

    def increment_without_lock(self):
        self.val.value += 1

    def value(self):
        with self.lock:
            return self.val.value


def func(counter):
    for i in range(50):
        time.sleep(0.01)
        counter.increment()
        #counter.increment_without_lock()


def counter_test(session_count):

    import time
    counter = SharedCounter(0)

    print("Testing {0} sessions, interval: {1}".format(session_count, 0.01))
    print("Warming up ...")

    warm_up_time = time.time()
    procs = [Process(target=func, args=(counter,)) for i in range(session_count)]
    print("Warm up process finished in {0} seconds".format(time.time() - warm_up_time))

    launch_time = time.time()
    for p in procs: p.start()
    print("{0} sessions started in {1}".format(session_count, time.time() - launch_time))

    for p in procs: p.join()
    print("{0} sessions finished in {1}".format(session_count, time.time() - launch_time))

    return counter.value()

if __name__ == '__main__':
    print(counter_test(8))
