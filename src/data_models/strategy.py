from data_models.data_model import DataModel


class Strategy(DataModel):
    def __init__(self, **kwargs):
        self.name = ""
        self.filepath = ""
        self.url = ""
        self.notes = ""
        self.path_json = ""
        self.updated = -1

        self.set(**kwargs)
