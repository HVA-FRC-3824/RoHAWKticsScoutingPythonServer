from .data_model import DataModel
from .team import Team
from firebase_com import FirebaseCom


class Alliance(DataModel):
    '''Data Model for holding information about 3 teams that form an alliance

    Args:
        args (`list`): a list of team numbers or `Team` objects
    '''
    def __init__(self, *args):
        if len(args) > 0:
            if isinstance(args[0], Team):
                self.teams = args
            elif isinstance(args[0], int):
                self.teams = []
                firebase = FirebaseCom()
                for arg in args:
                    self.teams.append(firebase.get_team(arg))
