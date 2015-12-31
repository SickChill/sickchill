import threading
import curl

class StressTestThread(threading.Thread):
    def __init__(self, url):
        threading.Thread.__init__(self)
        self.url = url
        self.baseline = self._get()
        self.success = True # so far so good

    def _get(self):
        return curl.Curl().get(self.url)

    def run(self):
        for i in range(10):
            v = self._get()
            if v != self.baseline:
                self.success = False
                if self.url.endswith('simload'):
                    print(v)

api_url = 'localhost:8081/api/df5d7e6a00f9a7d0b190777ac988f2c0/?cmd='

# this command uses regular row_type on DBConnection
ta = StressTestThread(api_url + 'simload')

# this command uses dict row_type on DBConnection
tb = StressTestThread(api_url + 'backlog')

ta.start()
tb.start()
ta.join()
tb.join()
print(ta.success)
print(tb.success)
