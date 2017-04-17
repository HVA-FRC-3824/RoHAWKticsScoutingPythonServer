from data_models.data_model import DataModel
from .tba_alliances import TBAAlliances
from .tba_score_breakdown import TBAScoreBreakdown


class TBAMatch(DataModel):
    def __init__(self, d):
        self.actual_time = 0
        self.alliances = TBAAlliances()
        self.comp_level = ""
        self.event_key = ""
        self.key = ""
        self.match_number = -1
        self.predicted_time = 0
        self.score_breakdown = TBAScoreBreakdown()
        self.set_number = 0
        self.time = 0
        self.videos = []
        self.winning_alliance = ""

        self.set(d)
