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

    def set(self, d):
        '''Sets the values from the `dict` d'''
        for key, value in iter(d.items()):
            if isinstance(value, dict):
                self.__dict__[key] = self._dict__[key].__class__(**value)
            elif isinstance(value, list):
                _class = self.__dict__["_"+key+"_type"].__class__
                for v in value:
                    self.__dict__[key].append(_class(**value))
            else:
                self.__dict__[key] = value
