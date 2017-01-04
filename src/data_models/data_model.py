class DataModel:
    def to_dict(self):
        d = dict((key, value) for key, value in iter(self.__dict__.items())
                 if not callable(value) and not key.startswith('__'))

        for key, value in iter(d.items()):
            if isinstance(value, DataModel):
                d[key] = value.to_dict()
        return d
