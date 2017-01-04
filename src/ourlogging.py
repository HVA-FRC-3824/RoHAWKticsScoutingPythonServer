import logging
import logging.handlers
import os
import sys
from colors import color


class GroupWriteRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def _open(self):
        prevumask = os.umask(0o000)
        rtv = logging.handlers.RotatingFileHandler._open(self)
        os.umask(prevumask)
        return rtv


class AnsiColorFormatter(logging.Formatter):
    def __init__(self, msgfmt=None, datefmt=None):
        self.formatter = logging.Formatter(msgfmt)

    def format(self, record):

        s = self.formatter.format(record)

        if record.levelname == 'CRITICAL':
            s = color(s, fg='red', style='negative')
        elif record.levelname == 'ERROR':
            s = color(s, fg='red')
        elif record.levelname == 'WARNING':
            s = color(s, fg='yellow')
        elif record.levelname == 'DEBUG':
            s = color(s, fg='blue')
        elif record.levelname == 'INFO':
            pass

        return s


def setup_logging(fn):

    fmt = '%(relativeCreated)s - %(threadName)s - %(filename)s - %(levelname)s - %(message)s'
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    logfn = '../log/%s.log' % os.path.split(fn)[-1].split('.')[0]
    fh_ = GroupWriteRotatingFileHandler(logfn, maxBytes=1024 * 1024 * 5, backupCount=10)
    fh_.setLevel(logging.DEBUG)
    # Normally our Python scripts steady-state at 3.8%. With memory log buffering, this will increase.
    # Can be 5.0% after running arm_test.py now.
    fh = logging.handlers.MemoryHandler(1024 * 1024 * 10, logging.ERROR, fh_)

    previous_handler = root.hasHandlers()

    formatter = logging.Formatter(fmt)
    fh_.setFormatter(formatter)
    root.addHandler(fh)

    if not previous_handler:
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # create formatter and add it to the handlers
        ch.setFormatter(AnsiColorFormatter(fmt))

        # add the handlers to logger
        root.addHandler(ch)

    def my_excepthook(excType, excValue, traceback, logger=logging):
        logger.error("Logging an uncaught exception",
                     exc_info=(excType, excValue, traceback))

    sys.excepthook = my_excepthook
