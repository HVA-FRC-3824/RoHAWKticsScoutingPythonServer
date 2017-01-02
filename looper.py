from multiprocessing import Process, Pipe, Lock as PLock
from threading import Event, Thread, Lock as TLock
import time


class Looper:
    kDefaultLoopTime = 0.1

    def __init__(self):
        self.running = False
        self.loop_time = self.kDefaultLoopTime

    def set_loop_time(self, loop_time):
        self.loop_time = loop_time

    def tstart(self):
        self.event = None
        self.tlock = TLock()
        self.t = Thread(target=self.tloop)
        self.t.start()

    def pstart(self):
        self.pipe, other_pipe = Pipe()
        self.plock = PLock()
        self.p = Process(target=self.ploop, args=(other_pipe,))
        self.p.start()

    def tloop(self):
        self.running = True
        self.on_tstart()
        while self.running:
            start_time = time.time()
            self.on_tloop()
            end_time = time.time()
            delta_time = end_time - start_time
            if self.loop_time - delta_time > 0 and self.running:
                self.event = Event()
                self.event.wait(timeout=self.loop_time - delta_time)
                self.event = None

    def ploop(self, pipe):
        self.running = True
        self.on_pstart()
        while self.running:
            message = pipe.recv()
            if message == "stop":
                self.stop()
            else:
                self.on_ploop(message)

    def on_tstart(self):
        pass

    def on_pstart(self):
        pass

    def on_tloop(self):
        raise NotImplementedError("on_tloop")

    def on_ploop(self):
        raise NotImplementedError("on_ploop")

    def stop(self):
        self.running = False
        if hasattr(self, 't'):
            if self.event is not None:
                self.event.set()
            self.t.join(timeout=5)
        if hasattr(self, 'p'):
            self.pipe.send("stop")
            self.p.join(timeout=5)
            if self.p.is_alive():
                self.p.terminate()
