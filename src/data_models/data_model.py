class DataModel:
    '''Base class for the data models that allows them to easily convert to `dict` which
       can be converted to json
    '''
    def __init__(self):
        self.last_modified = 0

    def to_dict(self):
        '''Converts the object to a `dict`

        Returns:
            `dict` representation of the object
        '''
        d = dict((key, value) for key, value in iter(self.__dict__.items())
                 if not callable(value) and not key.startswith('__'))

        for key, value in iter(d.items()):
            if isinstance(value, DataModel) or isinstance(value, obj):
                d[key] = value.to_dict()
            elif isinstance(value, list):
                d[key] = []
                for v in value:
                    if isinstance(v, DataModel) or isinstance(v, obj):
                        d[key].append(v.to_dict())
                    else:
                        d[key].append(v)
            elif isinstance(value, dict):
                d[key] = {}
                for k, v in value.items():
                    if isinstance(v, DataModel) or isinstance(v, obj):
                        d[key][k] = v.to_dict()
                    else:
                        d[key][k] = v
        return d

    def set(self, d):
        '''Sets the values from the `dict` d'''
        for a, b in iter(d.items()):

            if isinstance(b, (list, tuple)):
                #TODO: figure out how to use original data model constructor
                setattr(self, a, [obj(x) if isinstance(x, dict) else x for x in b])
            elif isinstance(b, dict):
                if isinstance(self.__dict__[a], DataModel):
                    self.__dict__[a] = self.__dict__[a].__class__(b)
                else:
                    setattr(self, a, obj(b))
            else:
                setattr(self, a, b)


class obj:
    def __init__(self, d):
        for a, b in iter(d.items()):
            if isinstance(b, (list, tuple)):
                setattr(self, a, [obj(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, obj(b) if isinstance(b, dict) else b)

    def to_dict(self):
        '''Converts the object to a `dict`

        Returns:
            `dict` representation of the object
        '''
        d = dict((key, value) for key, value in iter(self.__dict__.items())
                 if not callable(value) and not key.startswith('__'))

        for key, value in iter(d.items()):
            if isinstance(value, DataModel) or isinstance(value, obj):
                d[key] = value.to_dict()
            elif isinstance(value, list):
                d[key] = []
                for v in value:
                    if isinstance(v, DataModel) or isinstance(v, obj):
                        d[key].append(v.to_dict())
                    else:
                        d[key].append(v)
            elif isinstance(value, dict):
                d[key] = {}
                for k, v in value.items():
                    if isinstance(v, DataModel) or isinstance(v, obj):
                        d[key][k] = v.to_dict()
                    else:
                        d[key][k] = v
        return d
