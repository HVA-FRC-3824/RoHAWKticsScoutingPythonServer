from multiprocessing import Process, Pipe, Lock as PLock
from threading import Event, Thread, Lock as TLock
import time


class Looper:
    '''Parent class to set up looping threads/processes
    '''
    kDefaultLoopTime = 0.1

    def __init__(self):
        self.running = False
        self.loop_time = self.kDefaultLoopTime

    def set_loop_time(self, loop_time):
        '''Sets the minimum time for a loop

        Args:
            loop_time (float): minimum time in seconds for each loop
        '''
        self.loop_time = loop_time

    def tstart(self):
        '''Starts a looping thread
        '''
        self.event = None
        self.tlock = TLock()
        self.t = Thread(target=self.tloop)
        self.t.start()

    def pstart(self):
        '''Starts a looping process
        '''
        self.pipe, other_pipe = Pipe()
        self.plock = PLock()
        self.p = Process(target=self.ploop, args=(other_pipe,))
        self.p.start()

    def tloop(self):
        '''Runs the thread loop
        '''
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
        self.on_tend()

    def ploop(self, pipe):
        '''Runs the process loop
        '''
        self.running = True
        self.on_pstart()
        while self.running:
            if pipe.poll():
                message = pipe.recv()
                if message == "stop":
                    self.stop()
                else:
                    self.on_ploop(message)
            else:
                pass
        self.on_pend()

    def on_tstart(self):
        '''Runs once before the thread loop
        '''
        pass

    def on_tend(self):
        '''Runs once after the thread loop
        '''
        pass

    def on_pstart(self):
        '''Runs once before the process loop
        '''
        pass

    def on_pend(self):
        '''Runs once after the process loop
        '''
        pass

    def on_tloop(self):
        '''Runs on each loop of the thread

        Raises:
            NotImplementedError: if the derivative class does not implement
            this function and is running a thread loop
        '''
        raise NotImplementedError("on_tloop")

    def on_ploop(self, message):
        '''Runs on each loop of the process

        Raises:
            NotImplementedError: if the derivative class does not implement
            this function and is running a process loop
        '''
        raise NotImplementedError("on_ploop")

    def stop(self):
        '''Stops the thread or process
        '''
        self.running = False
        if hasattr(self, 't'):
            if self.event is not None:
                self.event.set()
            self.t.join()
        if hasattr(self, 'p'):
            self.pipe.send("stop")
            self.p.join()
            if self.p.is_alive():
                self.p.terminate()
