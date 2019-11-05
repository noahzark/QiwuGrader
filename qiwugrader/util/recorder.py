import time
from datetime import date, datetime
import json


class RecorderDot:

    def __init__(self, dot_name, last_dot_time):
        last_dot_time = last_dot_time or time.time()
        timestamp = time.time()
        self.dot_name = dot_name
        self.dot_datetime = datetime.fromtimestamp(timestamp)
        self.interval = timestamp - last_dot_time

    @staticmethod
    def json_serial(obj):
        if isinstance(obj, (RecorderDot)):
            return 'date: {} {}={:.4f}'.format(obj.dot_datetime, obj.dot_name, obj.interval)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))


class TimeRecoder:

    def __init__(self, name):
        self.name = name
        self.dots = []
        self.last_dot_time = None
        self.record_start = time.time()

    def dot(self, dot_name):
        dot = RecorderDot(dot_name, self.last_dot_time)
        self.dots.append(dot)
        self.last_dot_time = time.time()

    def get_total_time(self):
        return time.time() - self.record_start

    def debug_print(self):
        for dot in self.dots:
            print(json.dumps(dot, default=RecorderDot.json_serial))

    def __str__(self):
        return '{}\n{}\ntotal: {:.4f}'.format(
            self.name,
            json.dumps(self.dots, indent=4, default=RecorderDot.json_serial),
            self.get_total_time()
        )


debug_recorder = TimeRecoder('Debug')

if __name__ == "__main__":
    start = time.time()

    for i in range(1, 10000):
        debug_recorder.dot('test' + str(i))

    print(str(debug_recorder))
    print(time.time() - start)

