"""Fixture-descriptor JSON boundary only; no record-membership changes."""
import json


def normalize_descriptor(value):
    """Preserve JSON values/list order; reject ambiguous converted object keys."""
    def check(item):
        if type(item) is dict:
            keys=set()
            for key,child in item.items():
                if type(key) not in (str,int):
                    raise ValueError('Descriptor keys must be strings or integers')
                encoded=str(key)
                if encoded in keys:
                    raise ValueError('Descriptor object keys collide on the JSON wire')
                keys.add(encoded); check(child)
        elif type(item) in (list,tuple):
            for child in item: check(child)
        elif item is not None and type(item) not in (str,int,float,bool):
            raise ValueError('Descriptor contains a non-JSON value')
    check(value)
    return json.loads(json.dumps(value,allow_nan=False))


def descriptor_equal(actual,expected):
    """Sort only AFTER object keys are strings; preserve scalar encoding types."""
    def wire(item):
        return json.dumps(normalize_descriptor(item),sort_keys=True,separators=(',',':'),allow_nan=False)
    return wire(actual)==wire(expected)
