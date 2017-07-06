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
        for key, val in iter(d.items()):
            if isinstance(val, (list, tuple)):
                # TODO: figure out how to use original data model constructor
                if key + "_type" in self.__dict__:
                    setattr(self, key, [self.__dict__[key + "_type"](x) for x in val])
                else:
                    setattr(self, key, [obj(x) if isinstance(x, dict) else x for x in val])
            elif isinstance(val, dict):
                if isinstance(self.__dict__[key], DataModel):
                    self.__dict__[key] = self.__dict__[key].__class__(val)
                else:
                    setattr(self, key, obj(val))
            else:
                setattr(self, key, val)

    @classmethod
    def get_csv_field_names(cls) -> list:
        l = []
        o = cls()
        for key, val in iter(o.__dict__.items()):
            if isinstance(val, (DataModel, obj)):
                temp = val.get_csv_field_names()
                for temp_val in temp:
                    l.append(key + '_' + temp_val)
            elif isinstance(val, list):
                if key + "_type" in o.__dict__:
                    temp = o.__dict__[key + "_type"]().get_csv_field_names()
                    for temp_val in temp:
                        l.append(key + '_' + temp_val)
                else:
                    l.append(key)
            else:
                l.append(key)
        return l

    def to_csv_row(self) -> dict:
        '''convert data model to csv row'''
        d = {}
        for key, val in iter(self.__dict__.items()):
            if isinstance(val, (DataModel, obj)):
                temp = val.to_csv_row()
                for temp_key, temp_val in iter(temp.items()):
                    d[key + '_' + temp_key] = temp_val
            elif isinstance(val, list):
                if len(val) > 0 and isinstance(val[0], (DataModel, obj)):
                    for temp in val:
                        t = temp.to_csv_row()
                        for temp_key, temp_val in t.items():
                            if key + '_' + temp_key not in d:
                                d[key + '_' + temp_key] = 0
                            d[key + '_' + temp_key] += temp_val
            else:
                d[key] = val
        return d


class obj:
    def __init__(self, d):
        for key, val in iter(d.items()):
            if isinstance(val, (list, tuple)):
                # TODO: figure out how to use original data model constructor
                if key + "_type" in self.__dict__:
                    setattr(self, key, [self.__dict__[key + "_type"](x) for x in val])
                else:
                    setattr(self, key, [obj(x) if isinstance(x, dict) else x for x in val])
            elif isinstance(val, dict):
                if isinstance(self.__dict__[key], DataModel):
                    self.__dict__[key] = self.__dict__[key].__class__(val)
                else:
                    setattr(self, key, obj(val))
            else:
                setattr(self, key, val)

    def to_dict(self):
        '''Converts the object to a `dict`

        Returns:
            `dict` representation of the object
        '''
        d = dict((key, value) for key, value in iter(self.__dict__.items())
                 if not callable(value) and not key.startswith('__'))

        for key, value in iter(d.items()):
            if isinstance(value, (DataModel, obj)):
                d[key] = value.to_dict()
            elif isinstance(value, list):
                d[key] = []
                for v in value:
                    if isinstance(v, (DataModel, obj)):
                        d[key].append(v.to_dict())
                    else:
                        d[key].append(v)
            elif isinstance(value, dict):
                d[key] = {}
                for k, v in value.items():
                    if isinstance(v, (DataModel, obj)):
                        d[key][k] = v.to_dict()
                    else:
                        d[key][k] = v
        return d

    @classmethod
    def get_csv_field_names(cls) -> list:
        l = []
        o = cls()
        for key, val in iter(o.__dict__.items()):
            if isinstance(val, (DataModel, obj)):
                temp = val.get_csv_field_names()
                for temp_val in temp:
                    l.append(key + '_' + temp_val)
            elif isinstance(val, list):
                if key + "_type" in o.__dict__:
                    temp = o.__dict__[key + "_type"]().get_csv_field_names()
                    for temp_val in temp:
                        l.append(key + '_' + temp_val)
                else:
                    l.append(key)
            else:
                l.append(key)
        return l

    def to_csv_row(self) -> dict:
        '''convert data model to csv row'''
        d = {}
        for key, val in iter(self.__dict__.items()):
            if isinstance(val, (DataModel, obj)):
                temp = val.to_csv_row()
                for temp_key, temp_val in iter(temp.items()):
                    d[key + '_' + temp_key] = temp_val
            elif isinstance(val, list):
                if len(val) > 0 and isinstance(val[0], (DataModel, obj)):
                    for temp in val:
                        t = temp.to_csv_row()
                        for temp_key, temp_val in t.items():
                            if key + '_' + temp_key not in d:
                                d[key + '_' + temp_key] = 0
                            d[key + '_' + temp_key] += temp_val
            else:
                d[key] = val
        return d
