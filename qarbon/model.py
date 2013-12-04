from functools import partial
from qarbon.external.enum import Enum as _Enum


def __type(name, __type__=object, **metadata):
    metadata['__type__'] = __type__
    metadata['__name__'] = name
    return metadata

Int = partial(__type, __type__=int)
Float = partial(__type, __type__=float)
Str = partial(__type, __type__=str)
Bool = partial(__type, __type__=bool)


def Enum(name, dtype=_Enum, **metadata):
    if not issubclass(dtype, _Enum):
        raise TypeError("dtype must be an Enum")
    return __type(name, __type__=dtype, **metadata)
