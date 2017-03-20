from data_models.data_model import DataModel
from .tba_individual_score_breakdown import TBAIndividualScoreBreakdown


class TBAScoreBreakdown(DataModel):
    def __init__(self, d=None):
        self.blue = TBAIndividualScoreBreakdown()
        self.red = TBAIndividualScoreBreakdown()
        if d is not None:
        	self.set(d)
