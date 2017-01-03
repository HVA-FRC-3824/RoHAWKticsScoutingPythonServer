from .data_model import DataModel
from .team import Team
from firebase_com import FirebaseCom


class Alliance(DataModel):
    def __init__(self, *args):
        if len(args) > 0:
            if isinstance(args[0], Team):
                self.teams = args
            elif isinstance(args[0], int):
                self.teams = []
                firebase = FirebaseCom()
                for arg in args:
                    self.teams.append(firebase.get_team(arg))
