import pytest
from frozencounter import FrozenCounter, FrozenInstanceError


def test_init():
    c = FrozenCounter({1: 2})
    assert isinstance(c, FrozenCounter)


def test_setter():
    c = FrozenCounter({1: 2})
    with pytest.raises(FrozenInstanceError):
        c[1] += 2


def test_missing_key():
    c = FrozenCounter({1: 2})
    c[1]
    c[0]


def test_copy():
    c = FrozenCounter({1: 2})
    d = c.copy()
    assert c == d
    assert c is not d


def test_hash():
    c = FrozenCounter({1: 2})
    d = FrozenCounter({1: 2})
    assert hash(c) == hash(d)
    assert hash(frozenset((1, 2))) != hash(c)


def test_inplace_operation():
    c = FrozenCounter({1: 2})
    d = c
    c += FrozenCounter({2: 3})
    assert c == FrozenCounter({1: 2, 2: 3})
    assert d == FrozenCounter({1: 2})


def test_setitem():
    c = FrozenCounter({1: 2})
    with pytest.raises(FrozenInstanceError):
        c[2] = 3
    with pytest.raises(FrozenInstanceError):
        c[1] = 3
