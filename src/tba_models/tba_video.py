from data_models.data_model import DataModel


class TBAVideo(DataModel):
    def __init__(self, d):
        self.key = ""
        self.type = ""
        self.set(d)
