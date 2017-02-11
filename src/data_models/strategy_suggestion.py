from .data_model import DataModel


class StrategySuggestion(DataModel):
    def __init__(self, **kwargs):

        self.key = ""
        self.offense_text = ""
        self.defense_text = ""
        self.last_modified = -1

        self.set(**kwargs)
