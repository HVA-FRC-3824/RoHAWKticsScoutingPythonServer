from .data_model import DataModel


class StrategySuggestion(DataModel):
    def __init__(self, **kwargs):
        DataModel.__init__(self)

        self.key = ""
        self.offense_text = ""
        self.defense_text = ""

        self.set(**kwargs)
