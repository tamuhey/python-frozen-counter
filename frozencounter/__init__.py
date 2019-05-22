import _collections_abc
import sys
import heapq as _heapq
from collections import Counter
from collections.abc import Mapping
from operator import eq as _eq
from operator import itemgetter as _itemgetter
import platform

from decorator import decorator


class FrozenInstanceError(AttributeError):
    msg = "can't assign item"
    args = [msg]


@decorator
def raise_frozen_error(f, msg=None, *args, **kwargs):
    if msg:
        raise FrozenInstanceError(msg)
    raise FrozenInstanceError()


class FrozenCounter(Mapping):
    """Frozen type collections.Counter"""

    def __init__(self, *args, **kwds):
        """Create a new, empty FrozenCounter object.  And if given, count elements
        from an input iterable.  Or, initialize the count from another mapping
        of elements to their counts.

        >>> c = FrozenCounter()                           # a new, empty counter
        >>> c = FrozenCounter('gallahad')                 # a new counter from an iterable
        >>> c = FrozenCounter({'a': 4, 'b': 2})           # a new counter from a mapping
        >>> c = FrozenCounter(a=4, b=2)                   # a new counter from keyword args

        """
        self._counter = Counter(*args, **kwds)

    def most_common(self, n=None):
        """Same as Counter.most_common

        >>> FrozenCounter('abcdeabcdabcaba').most_common(3)
        [('a', 5), ('b', 4), ('c', 3)]

        """
        return self._counter.most_common(n)

    def elements(self):
        """Same as Counter.elements

        >>> c = FrozenCounter('ABCABC')
        >>> sorted(c.elements())
        ['A', 'A', 'B', 'B', 'C', 'C']

        # Knuth's example for prime factors of 1836:  2**2 * 3**3 * 17**1
        >>> prime_factors = FrozenCounter({2: 2, 3: 3, 17: 1})
        >>> product = 1
        >>> for factor in prime_factors.elements():     # loop over factors
        ...     product *= factor                       # and multiply them
        >>> product
        1836

        Note, if an element's count has been set to zero or is a negative
        number, elements() will ignore it.

        """
        return self._counter.elements()

    def update(self, *args, **kwds) -> "FrozenCounter":
        """Like Counter.update() but returns newly created FrozenCounter.

        Source can be an iterable, a dictionary, or another Counter instance.

        >>> c = FrozenCounter('which')
        >>> d = c.update('witch')           # add elements from another iterable
        >>> e = Counter('watch')
        >>> f = c.update(e)                 # add elements from another counter
        >>> f['h']                      # four 'h' in which, witch, and watch
        3

        """
        # The regular dict.update() operation makes no sense here because the
        # replace behavior results in the some of original untouched counts
        # being mixed-in with all of the other counts for a mismash that
        # doesn't have a straight-forward interpretation in most counting
        # contexts.  Instead, we implement straight-addition.  Both the inputs
        # and outputs are allowed to contain zero and negative counts.

        new_counter = self._counter.copy()
        new_counter.update(*args, **kwds)
        return new_counter

    def subtract(self, *args, **kwds) -> "FrozenCounter":
        """Like Counter.subtract, but returns FrozenCounter

        Source can be an iterable, a dictionary, or another Counter instance.

        >>> c = FrozenCounter('which')
        >>> d = c.subtract('witch')             # subtract elements from another iterable
        >>> e = d.subtract(Counter('watch'))    # subtract elements from another counter
        >>> e['h']                          # 2 in which, minus 1 in witch, minus 1 in watch
        0
        >>> e['w']                          # 1 in which, minus 1 in witch, minus 1 in watch
        -1

        """
        new_counter: Counter = self._counter.copy()
        new_counter.subtract(*args, **kwds)
        return FrozenCounter(new_counter)

    def copy(self):
        "Return a shallow copy."
        return self.__class__(self._counter)

    def __reduce__(self):
        return self.__class__, (dict(self._counter),)

    # pylint: disable=no-value-for-parameter
    @raise_frozen_error(msg="'FrozenCounter' doesn't support item deletion")
    def __delitem__(self, *args, **kwargs):
        pass

    def __repr__(self):
        if not self:
            return "%s()" % self.__class__.__name__
        try:
            items = ", ".join(map("%r: %r".__mod__, self.most_common()))
            return "%s({%s})" % (self.__class__.__name__, items)
        except TypeError:
            # handle case where values are not orderable
            return "{0}({1!r})".format(self.__class__.__name__, dict(self))

    # Multiset-style mathematical operations discussed in:
    #       Knuth TAOCP Volume II section 4.6.3 exercise 19
    #       and at http://en.wikipedia.org/wiki/Multiset
    #
    # Outputs guaranteed to only include positive counts.
    #
    # To strip negative and zero counts, add-in an empty counter:
    #       c += Counter()

    def __add__(self, other: "FrozenCounter") -> "FrozenCounter":
        """Same as Counter.__add__

        >>> FrozenCounter('abbb') + FrozenCounter('bcc')
        FrozenCounter({'b': 4, 'c': 2, 'a': 1})

        """
        if not isinstance(other, FrozenCounter):
            return NotImplemented
        result = self._counter + other._counter
        return FrozenCounter(result)

    def __sub__(self, other: "FrozenCounter") -> "FrozenCounter":
        """Same as Counter.__sub__

        >>> FrozenCounter('abbbc') - FrozenCounter('bccd')
        FrozenCounter({'b': 2, 'a': 1})

        """
        if not isinstance(other, FrozenCounter):
            return NotImplemented
        result = self._counter - other._counter
        return FrozenCounter(result)

    def __or__(self, other: "FrozenCounter") -> "FrozenCounter":
        """Union is the maximum of value in either of the input counters.

        >>> FrozenCounter('abbb') | FrozenCounter('bcc')
        FrozenCounter({'b': 3, 'c': 2, 'a': 1})

        """
        if not isinstance(other, FrozenCounter):
            return NotImplemented
        result = self._counter | other._counter
        return FrozenCounter(result)

    def __and__(self, other: "FrozenCounter") -> "FrozenCounter":
        """Intersection is the minimum of corresponding counts.

        >>> FrozenCounter('abbb') & FrozenCounter('bcc')
        FrozenCounter({'b': 1})

        """
        if not isinstance(other, FrozenCounter):
            return NotImplemented
        result = self._counter & other._counter
        return FrozenCounter(result)

    def __pos__(self) -> "FrozenCounter":
        "Adds an empty counter, effectively stripping negative and zero counts"
        return FrozenCounter(+self._counter)

    def __neg__(self) -> "FrozenCounter":
        """Subtracts from an empty counter.  Strips positive and zero counts,
        and flips the sign on negative counts.

        """
        return FrozenCounter(-self._counter)

    def __eq__(self, other):
        """

        >>> c = FrozenCounter({1:2})
        >>> d = FrozenCounter({1:2})
        >>> assert c == d
        >>> e = FrozenCounter({2:3})
        >>> assert not c == e

        """
        return self._counter == other._counter

    def __ne__(self, other):
        """

        >>> c = FrozenCounter({1:2})
        >>> d = FrozenCounter({1:2})
        >>> assert not c != d
        >>> e = FrozenCounter({2:3})
        >>> assert c != e

        """
        return self._counter != other._counter

    def __contains__(self, key):
        """
        
        >>> c = FrozenCounter({1:2})
        >>> assert 1 in c
        >>> assert 2 not in c

        """
        return self._counter.__contains__(key)

    def keys(self):
        """

        >>> c = FrozenCounter({1:2,3:4})
        >>> assert set(c.keys()) == set((1,3))
        """
        return self._counter.keys()

    def items(self):
        """
        
        >>> c = FrozenCounter({1:2,3:4})
        >>> assert set(c.items()) == set(((1,2),(3,4)))
        """
        return self._counter.items()

    def values(self):
        """
        
        >>> c = FrozenCounter({1:2,3:4})
        >>> assert set(c.values()) == set((2,4))
        """
        return self._counter.values()

    def get(self, k, default=None):
        """
        
        >>> c = FrozenCounter({1:2,3:4})
        >>> assert c.get(1) == 2
        >>> assert c.get(2,-1) == -1
        >>> assert c.get(10) is None
        """
        return self._counter.get(k, default)

    def __getitem__(self, obj):
        return self._counter.__getitem__(obj)

    def __iter__(self):
        return self._counter.__iter__()

    def __len__(self):
        return self._counter.__len__()

    def __hash__(self):
        return hash((FrozenCounter, frozenset(self._counter.items())))

    @raise_frozen_error()
    def __setitem__(self, *args, **kwargs):
        pass


if sys.version_info >= (3, 7):
    from typing import _alias, T_co, FrozenSet

    TFrozenCounter = _alias(FrozenCounter, T_co, inst=False)

elif sys.version_info >= (3, 6):
    from typing import Dict, T, _generic_new

    class TFrozenCounter(FrozenCounter, Dict[T, int], extra=FrozenCounter):
        __slots__ = ()

        def __new__(cls, *args, **kwds):
            if cls._gorg is FrozenCounter:
                return FrozenCounter(*args, **kwds)
            return _generic_new(FrozenCounter, cls, *args, **kwds)
