from data_models.data_model import DataModel
from .tba_alliance import TBAAlliance


class TBAAlliances(DataModel):
    def __init__(self, d=None):
        self.blue = TBAAlliance()
        self.red = TBAAlliance()
        if d is not None:
        	self.set(d)
