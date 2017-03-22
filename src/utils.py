def make_ascii_from_json(input):
    if isinstance(input, dict):
        return dict((make_ascii_from_json(k), make_ascii_from_json(v)) for (k, v) in iter(input.items()))
    elif isinstance(input, list):
        return map(lambda i: make_ascii_from_json(i), input)
    # elif isinstance(input, unicode):
    #    return input.encode('utf-8')
    else:
        return input
