"""Hold an object for later reference."""
class Holder(object):
    """Hold an object for later reference."""
    def __init__(self):
        self.r = None
    def __call__(self, result):
        self.r = result
        return result
