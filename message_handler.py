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
        logger.info("Received Match Data")
        matches = json.loads(message)
        if isinstance(matches, dict):
            try:
                self.firebase.update_team_match_data(matches)
            except:
                logger.error("Error with updating tmd")
        elif isinstance(matches, list):
            for tmd in matches:
                try:
                    self.firebase.update_team_match_data(tmd)
                except:
                    logger.error("Error with updating tmd")
        else:
            logger.error("message is not a dict or list")

    def handle_super(self, message):
        logger.info("Received Super Data")
        matches = json.loads(message)
        if isinstance(matches, dict):
            try:
                self.firebase.update_super_match_data(matches)
            except:
                logger.error("Error with updating smd")
        elif isinstance(matches, list):
            for smd in matches:
                try:
                    self.firebase.update_super_match_data(smd)
                except:
                    logger.error("Error with updating smd")
        else:
            logger.error("message is not a dict or list")

    def handle_dt_feedback(self, message):
        logger.info("Received Drive Team Feedback")
        matches = json.loads(message)
        if isinstance(matches, dict):
            try:
                self.firebase.update_team_dt_feedback(matches)
            except:
                logger.error("Error with updating tdtf")
        elif isinstance(matches, list):
            for tdtf in matches:
                try:
                    self.firebase.update_team_dt_feedback(tdtf)
                except:
                    logger.error("Error with updating tdtf")
        else:
            logger.error("message is not a dict or list")

    def handle_pit(self, message):
        logger.info("Received Pit Data")
        pits = json.loads(message)
        if isinstance(pits, dict):
            try:
                self.firebase.update_team_pit_data(pits)
            except:
                logger.error("Error with updating tpd")
        elif isinstance(pits, list):
            for tpd in pits:
                try:
                    self.firebase.update_team_pit_data(tpd)
                except:
                    logger.error("Error with updating tpd")
        else:
            logger.error("message is not a dict or list")
