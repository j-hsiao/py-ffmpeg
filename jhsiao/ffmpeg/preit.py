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
