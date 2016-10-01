'''Data Package.

This class is used for unpacking a received data package.

:copyright: 2016, Jeroen van der Heijden (Transceptor Technology)
'''

import struct
import qpack
from . import protomap


class DataPackage(object):

    __slots__ = ('pid', 'length', 'tipe', 'checkbit', 'data')

    struct_datapackage = struct.Struct('<IHBB')

    _MAP = (
        lambda data: None,
        lambda data: qpack.unpackb(data, decode='utf-8'),
        lambda data: data,
    )

    def __init__(self, barray):
        self.length, self.pid, self.tipe, self.checkbit = \
            self.__class__.struct_datapackage.unpack_from(barray, offset=0)
        self.length += self.__class__.struct_datapackage.size
        self.data = None

    def extract_data_from(self, barray):
        try:
            self.data = self.__class__._MAP[protomap.MAP_RES_DTYPE[self.tipe]](
                barray[self.__class__.struct_datapackage.size:self.length])
        finally:
            del barray[:self.length]
