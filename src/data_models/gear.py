from .data_model import DataModel


class Gear(DataModel):
    def __init__(self, d=None):
        self.location = ""
        self.placed = False
        self.dropped = False
        if d is not None:
            self.set(d)
