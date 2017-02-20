from .data_model import DataModel


class StrategySuggestion(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)

        self.key = ""
        self.offense_text = ""
        self.defense_text = ""

        if d is not None:
            self.set(d)
