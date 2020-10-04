import pytest
from gmet import gmet

def test_getInseeCode():
        assert gmet.getInseeCode("paris")[0] == "750560"
        assert gmet.getInseeCode("paris", "751070")[0] == "751070"
        assert gmet.getInseeCode("bordeaux")[0] == "330630"
        assert gmet.getInseeCode("bordeaux", "450410")[0] == "450410"

def test_getInseeCode_exception1():
    with pytest.raises(ValueError):
        gmet.getInseeCode("nomatch")

def test_getInseeCode_exception2():
    with pytest.raises(ValueError):
        gmet.getInseeCode("bordeaux", "993366")