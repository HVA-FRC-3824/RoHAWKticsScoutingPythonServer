from multiprocessing import Lock as PLock
from threading import Lock as TLock
import logging
import json
from firebase_com import FirebaseCom
from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class MessageHandler:
    # Singleton
    shared_state = {}

    def __init__(self):
        self.__dict__ = self.shared_state
        if not hasattr(self, 'instance'):
            self.tlock = TLock()
            self.plock = PLock()
            self.firebase = FirebaseCom()
            self.instance = True

    def handle_message(self, message):
        self.tlock.acquire()
        self.plock.acquire()
        if message[0] == 'M':
            self.handle_match(message[1:])
        elif message[0] == 'S':
            self.handle_super(message[1:])
        elif message[0] == 'F':
            self.handle_dt_feedback(message[1:])
        elif message[0] == 'P':
            self.handle_pit(message[1:])
        self.tlock.release()
        self.plock.release()

    def handle_match(self, message):
        logger.d("Received Match Data")
        matches = json.loads(message)
        for tmd in matches:
            if not self.firebase.update_tmd(tmd):
                logger.e("Error with updating tmd")

    def handle_super(self, message):
        logger.d("Received Super Data")
        matches = json.loads(message)
        for smd in matches:
            if not self.firebase.update_smd(smd):
                logger.e("Error with updating smd")

    def handle_dt_feedback(self, message):
        logger.d("Received Drive Team Feedback")
        matches = json.loads(message)
        for tdtf in matches:
            if not self.firebase.update_tdtf(tdtf):
                logger.e("Error with updating tdtf")

    def handle_pit(self, message):
        logger.d("Received Pit Data")
        pits = json.loads(message)
        for tpd in pits:
            if not self.firebase.update_tpd(tpd):
                logger.e("Error with updating tpd")
