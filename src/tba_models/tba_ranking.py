from data_models.data_model import DataModel
from .tba_record import TBARecord


class TBARanking(DataModel):
    def __init__(self, d):
        self.dq = 0
        self.extra_stats = []
        self.matches_played = 0
        self.qual_average = None
        self.rank = -1
        self.record = TBARecord()
        self.sort_orders = []
        self.team_key = ""
        self.set(d)
