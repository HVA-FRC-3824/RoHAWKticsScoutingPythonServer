from .data_model import DataModel


class Gear(DataModel):
    def __init__(self, **kwargs):
        self.location = ""
        self.placed = False
        self.dropped = False

        self.set(**kwargs)
