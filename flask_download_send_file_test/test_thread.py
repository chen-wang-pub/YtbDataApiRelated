import threading
import time


class t(threading.Thread):
    def __init__(self, name):
        super(t, self).__init__()
        self.name = name
        self.timeout = 10
        self.start_time = time.time()
        self.finished = False

    def run(self) -> None:
        while True:
            time.sleep(3)
            print('{}'.format(self.name))
            if time.time() - self.start_time > self.timeout:
                print('{} end'.format(self.name))
                self.finished = True
                break
if __name__ == '__main__':

    #thread_list = []
    for i in range(3):
        ti = t(str(i))
        #thread_list.append(ti)
        ti.start()

    #time.sleep(5)
    #for th in thread_list:
        #print(th.is_alive())