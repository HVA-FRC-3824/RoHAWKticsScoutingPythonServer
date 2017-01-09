from multiprocessing import Lock as PLock
from threading import Lock as TLock
import logging
import json
from firebase_com import FirebaseCom
from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class MessageHandler:
    '''Singleton that handles when a message is received either through bluetooth
       or sockets.
    '''

    MATCH_HEADER = 'M'
    SUPER_HEADER = 'S'
    FEEDBACK_HEADER = 'F'
    PIT_HEADER = 'P'
    SYNC_HEADER = 'R'
    STRATEGY_HEADER = 'T'
    MATCH_STRATEGY_HEADER = 'A'

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
        '''decodes the message

        Args:
            message (`str`): the received message
        '''
        self.tlock.acquire()
        self.plock.acquire()
        response = None
        if message[0] == self.MATCH_HEADER:
            self.handle_match(message[1:])
        elif message[0] == self.SUPER_HEADER:
            self.handle_super(message[1:])
        elif message[0] == self.FEEDBACK_HEADER:
            self.handle_dt_feedback(message[1:])
        elif message[0] == self.PIT_HEADER:
            self.handle_pit(message[1:])
        elif message[0] == self.SYNC_HEADER:
            response = self.handle_sync()
        elif message[0] == self.STRATEGY_HEADER:
            self.handle_strategy(message[1:])
        elif message[0] == self.MATCH_STRATEGY_HEADER:
            self.handle_match_strategy(message[1:])
        self.tlock.release()
        self.plock.release()
        return response

    def handle_match(self, message):
        '''decodes the message to one or more `TeamMatchData`

        Args:
            message (`str`): the received message
        '''
        logger.debug("Received Match Data")
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
        '''decodes the message to one or more `SuperMatchData`

        Args:
            message (`str`): the received message
        '''
        logger.debug("Received Super Data")
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
        '''decodes the message to one or more `TeamDTFeedback`

        Args:
            message (`str`): the received message
        '''
        logger.debug("Received Drive Team Feedback")
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
        '''decodes the message to one or more `TeamPitData`

        Args:
            message (`str`): the received message
        '''
        logger.debug("Received Pit Data")
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

    def handle_strategy(self, message):
        '''decodes the message to one or more `Strategy`

        Args:
            message (`str`): the received message
        '''
        logger.debug("Received Strategy Data")
        strategies = json.loads(message)
        if isinstance(strategies, dict):
            try:
                self.firebase.update_strategy(strategies)
            except:
                logger.error("Error with updating strategy")
        elif isinstance(strategies, list):
            for strategy in strategies:
                try:
                    self.firebase.update_strategy(strategy)
                except:
                    logger.error("Error with updating strategies")
        else:
            logger.error("message is not a dict or list")

    def handle_match_strategy(self, message):
        '''decodes the message to one or more `MatchStrategy`

        Args:
            message (`str`): the received message
        '''
        logger.debug("Received Match Strategy Data")
        strategies = json.loads(message)
        if isinstance(strategies, dict):
            try:
                self.firebase.update_match_strategy(strategies)
            except:
                logger.error("Error with updating match strategies")
        elif isinstance(strategies, list):
            for strategy in strategies:
                try:
                    self.firebase.update_match_strategy(strategy)
                except:
                    logger.error("Error with updating match stratgies")
        else:
            logger.error("message is not a dict or list")

    def handle_sync(self):
        '''creates a response for a sync request'''
        logger.debug("Received sync request")
        data = {}

        data['match'] = []
        for tmd in self.firebase.get_all_team_match_data().values():
            data['match'].append(tmd.to_dict())

        data['pit'] = []
        for tpd in self.firebase.get_all_team_pit_data().values():
            data['pit'].append(tpd.to_dict())

        data['super'] = []
        for smd in self.firebase.get_all_super_match_data().values():
            data['super'].append(smd.to_dict())

        data['calc'] = []
        for tcd in self.firebase.get_all_team_calculated_data().values():
            data['calc'].append(tcd.to_dict())

        data['1st'] = []
        for tpa in self.firebase.get_all_first_pick_abilities().values():
            data['1st'].append(tpa.to_dict())

        data['2nd'] = []
        for tpa in self.firebase.get_all_second_pick_abilities().values():
            data['2nd'].append(tpa.to_dict())

        data['3rd'] = []
        for tpa in self.firebase.get_all_third_pick_abilities().values():
            data['3rd'].append(tpa.to_dict())

        data['current'] = []
        for trd in self.firebase.get_all_current_team_rankings().values():
            data['current'].append(trd.to_dict())

        data['predicted'] = []
        for trd in self.firebase.get_all_predicted_team_rankings().values():
            data['predicted'].append(trd.to_dict())

        data['accuracy'] = []
        for sa in self.firebase.get_all_scout_accuracy().values():
            data['accuracy'].append(sa.to_dict())

        data['strategy'] = []
        for strategy in self.firebase.get_all_strategies().values():
            data['strategy'].append(strategy.to_dict())

        data['match_strategy'] = []
        for strategy in self.firebase.get_all_match_strategies().values():
            data['match_strategy'].append(strategy.to_dict())
        return "R" + json.dumps(data)
