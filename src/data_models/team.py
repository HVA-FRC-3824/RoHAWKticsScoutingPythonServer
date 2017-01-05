from .data_model import DataModel


class Team(DataModel):
    def __init__(self):
        '''All the data for a team (contains several other data models)'''
        self.team_number = -1

        self.completed_matches = {}
        self.info = None
        self.pit = None
        self.drive_team_feedback = None
        self.calc = None

        self.current_ranking = None
        self.predicted_ranking = None

        self.first_pick = None
        self.second_pick = None
        self.third_pick = None
