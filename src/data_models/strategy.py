from data_models.data_model import DataModel


class Strategy(DataModel):
    def __init__(self, d=None):
        DataModel.__init__(self)
        self.name = ""
        self.filepath = ""
        self.url = ""
        self.notes = ""
        self.path_json = ""

        if d is not None:
            self.set(d)
