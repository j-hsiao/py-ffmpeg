__all__ = ['cv2', 'np']
import sys

class LazyImport(object):
    def __init__(self, module):
        self.__modulename = module
        self.__module = sys.modules.get(module, None)

    def __getattr__(self, name):
        try:
            val = getattr(self.__module, name)
        except AttributeError:
            if self.__module is not None:
                raise
            self.__module = __import__(self.__modulename)
            val = getattr(self.__module, name)
        setattr(self, name, val)
        return val

    def __repr__(self):
        return 'LazyImport({!r})'.format(self.__modulename)

cv2 = LazyImport('cv2')
np = LazyImport('numpy')
