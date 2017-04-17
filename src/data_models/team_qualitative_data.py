from .data_model import DataModel
from .qualitative_result import QualitativeResult


class TeamQualitativeData(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.team_number = -1
        self.speed = QualitativeResult()
        self.torque = QualitativeResult()
        self.control = QualitativeResult()
        self.defense = QualitativeResult()

        if d is not None:
            self.set(d)
