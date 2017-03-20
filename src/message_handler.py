from multiprocessing import Lock as PLock
from threading import Lock as TLock
from threading import Event
import logging
import json

from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class MessageHandler:
    '''Singleton that handles when a message is received either through bluetooth
       or sockets.
    '''

    # Singleton
    shared_state = {}

    def __init__(self):
        self.__dict__ = self.shared_state
        if not hasattr(self, 'instance'):
            self.tlock = TLock()
            self.plock = PLock()
            self.update_queue = []
            self.partial_match_updates = {}
            self.partial_match_time = {}
            self.pong = False
            self.event = Event()

            self.instance = True

    def handle_message(self, message):
        '''decodes the message

        Args:
            message (`str`): the received message
        '''
        self.tlock.acquire()
        self.plock.acquire()
        
        message_dict = json.loads(message)

        if message_dict['message_type'] == 'update':
            if message_dict['update_type'] == 'partial_match':
                match_number = int(message_dict['match_number'])
                team_number = int(message_dict['team_number'])
                if match_number not in partial_match_updates:
                    partial_match_updates[match_number] = []
                # Basically makes this list a set
                if team_number not in partial_match_updates[match_number]:
                    partial_match_updates[match_number].append(team_number)
                    partial_match_time[match_number] = time.time()

                # Once all 6 teams are in request the calculations
                # TODO: handle if not all 6 teams come in within a certain period of time
                if len(partial_match_updates[match_number]) >= 6:
                    del partial_match_time[match_number]
                    update = {"update_type": "match", "match_number": match_number, "update_attempt": 1}
                    if update not in update_queue:
                        self.update_queue.append(update)
                    
            elif message_dict['update_type'] == 'super_match':
                update = {"update_type": "super", "match_number": message_dict['match_number']}
                if update not in update_queue:
                        self.update_queue.append(update)
            elif message_dict['update_type'] == 'pilot_match':
                update = {"update_type": "pilot", "match_number": message_dict['match_number']}
                if update not in update_queue:
                        self.update_queue.append(update)
            else:
                logger.error("Unknown update type")
        elif message_dict['message_type'] == 'pong':
            logger.info('Pong received')
            self.pong = True

        self.tlock.release()
        self.plock.release()
        return response

    def updates_available(self):
        return len(self.update_queue) > 0

    def get_next_update(self):
        update = self.update_queue[0]
        del self.update_queue[0]
        return update

    # 10 minutes given
    def get_partial_matches_timeout(self, timeout=600):
        now = time.time()
        timed_out_partial_matches = {}
        for match_number, t in partial_match_time.items():
            if now - t > timeout:
                yield match_number, partial_match_updates[match_number]