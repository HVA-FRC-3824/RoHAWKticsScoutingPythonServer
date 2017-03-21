from .data_model import DataModel


class QualitativeResult(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.zscore = 0.0
        self.rank = -1

        if d is not None:
            self.set(d)
