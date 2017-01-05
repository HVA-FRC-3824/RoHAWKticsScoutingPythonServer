class DataModel:
    '''Base class for the data models that allows them to easily convert to `dict` which
       can be converted to json
    '''
    def to_dict(self):
        '''Converts the object to a `dict`

        Returns:
            `dict` representation of the object
        '''
        d = dict((key, value) for key, value in iter(self.__dict__.items())
                 if not callable(value) and not key.startswith('__'))

        for key, value in iter(d.items()):
            if isinstance(value, DataModel):
                d[key] = value.to_dict()
        return d
