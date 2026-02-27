class PreIt(object):
    """Iterate with ability to insert data at front.

    Items in `self.pre` list are returned first during iteration.  This
    acts as a stack so items at the end of the list are iterated first.
    """
    def __init__(self, it):
        self.it = iter(it)
        self.pre = []

    def push(self, item):
        """Push an item to pre and return self."""
        self.pre.append(item)
        return self

    def extend(self, item):
        """Push items to pre and return self."""
        self.pre.extend(item)
        return self

    def __iter__(self):
        pre = self.pre
        it = self.it
        try:
            while 1:
                if pre:
                    yield pre.pop()
                else:
                    yield next(it)
        except StopIteration:
            return


class RewindIt(object):
    """Allow rewinding."""
    def __init__(self, it):
        self.it = iter(it)
        self.history = []
        self.pos = 0

    def rewind(self, amount=None):
        if amount is None:
            self.pos = 0
        else:
            self.pos -= amount
            if self.pos < 0:
                self.pos = 0
        return self

    def __iter__(self):
        history = self.history
        it = self.it
        while 1:
            if self.pos < len(history):
                obj = self.history[self.pos]
            else:
                try:
                    obj = next(it)
                except StopIteration:
                    return
                self.history.append(obj)
            self.pos += 1
            yield obj

if __name__ == '__main__':
    it = PreIt('asdf')
    outer = []
    inner = []
    for thing in it:
        outer.append(thing)
        if thing == 's':
            for x in it.push(thing):
                inner.append(x)
                if x == 'f':
                    it.pre.append(x)
                    break

    print(outer)
    print(inner)
    assert outer == ['a', 's', 'f']
    assert inner == ['s', 'd', 'f']

    outer = []
    inner = []
    it = RewindIt('asdf')
    for thing in it:
        outer.append(thing)
        if thing == 's':
            for x in it.rewind(1):
                inner.append(x)
                if x == 'f':
                    it.rewind(1)
                    break
    print(outer)
    print(inner)
    assert outer == ['a', 's', 'f']
    assert inner == ['s', 'd', 'f']
