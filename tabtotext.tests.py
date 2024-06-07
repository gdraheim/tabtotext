#! /usr/bin/env python3

__copyright__ = "(C) 2017-2023 Guido Draheim, licensed under the Apache License 2.0"""
__version__ = "1.6.2266"

from typing import Optional, Union, Dict, List, Any, Sequence, Callable
from tabtotext import JSONList, JSONItem, DataList, DataItem
import tabtotext
import unittest
import datetime
import sys
from fnmatch import fnmatchcase as fnmatch
import os
import os.path as path
import shutil
import json
import inspect
from dataclasses import dataclass
from io import StringIO

import logging
logg = logging.getLogger("TESTS")

try:
    from tabtools import currency_default
    def X(line: str) -> str:
        return line.replace("$", chr(currency_default))
except ImportError as e:
    def X(line: str) -> str:
        return line

try:
    from tabtoxlsx import saveToXLSX, readFromXLSX  # type: ignore
    from tabtotext import RowSortList, ColSortList, LegendList
    skipXLSX = False
except Exception as e:
    logg.warning("skipping tabtoxlsx: %s", e)
    skipXLSX = True
    def saveToXLSX(filename: str, result: JSONList, sorts: RowSortList = [], formats: Dict[str, str] = {},  #
                   legend: LegendList = [],  #
                   reorder: ColSortList = []) -> None:
        pass
    def readFromXLSX(filename: str) -> JSONList:
        return []

def get_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back  # type: ignore
    return frame.f_code.co_name  # type: ignore
def get_caller_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back.f_back  # type: ignore
    return frame.f_code.co_name  # type: ignore

@dataclass
class Item1(DataItem):
    b: JSONItem

@dataclass
class Item2(DataItem):
    a: str
    b: int
    def foo(self, a: str) -> None:
        pass

#######################################################################

test003: JSONList = []
test004: JSONList = [{}]
# test004: JSONList = [{}, {}]
test005: JSONList = [{"a": "x"}]
test006: JSONList = [{"a": "x", "b": "y"}]
test007: JSONList = [{"b": "y", "a": "x"}, {"b": "v"}]
test007Q: JSONList = [{"b": "y", "a": "x"}, {"b": "v", "a": None}]
test008: JSONList = [{"a": "x"}, {"b": "v"}]
test008Q: JSONList = [{"b": None, "a": "x"}, {"b": "v", "a": None}]
test009: JSONList = [{}, {"b": "v"}]
test009Q: JSONList = [{"b": None}, {"b": "v"}]
test011: JSONList = [{"b": None}]
test011Q: JSONList = []
test012: JSONList = [{"b": False}]
test013: JSONList = [{"b": True}]
test014: JSONList = [{"b": ""}]
test015: JSONList = [{"b": "5678"}]
test015Q: JSONList = [{"b": 5678}]
test016: JSONList = [{"b": 123}]
test017: JSONList = [{"b": 123.4}]
test018: JSONList = [{"b": datetime.date(2021, 12, 31)}]
test018Q: JSONList = [{"b": datetime.datetime(2021, 12, 31, 0, 0)}]
test019Q: JSONList = [{"b": datetime.date(2021, 12, 31)}]
test019: JSONList = [{"b": datetime.datetime(2021, 12, 31, 23, 34, 45)}]

data011: DataList = [Item1(None)]
data012: DataList = [Item1(False)]
data013: DataList = [Item1(True)]
data014: DataList = [Item1("")]
data015: DataList = [Item1("5678")]
data016: DataList = [Item1(123)]
data017: DataList = [Item1(123.4)]
data018: DataList = [Item1(datetime.date(2021, 12, 31))]
data019: DataList = [Item1(datetime.datetime(2021, 12, 31))]

class TabToTextTest(unittest.TestCase):
    def caller_testname(self) -> str:
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1 + 1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix: Optional[str] = None) -> str:
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testdir(self, testname: Optional[str] = None, keep: bool = False) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp." + testname
        if path.isdir(newdir) and not keep:
            shutil.rmtree(newdir)
        if not path.isdir(newdir):
            os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname: Optional[str] = None) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp." + testname
        if path.isdir(newdir):
            shutil.rmtree(newdir)
        return newdir
    #
    def test_1018(self) -> None:
        item = "abcdefghijklmnopqrstuvwxyz123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        text = tabtotext.str18(item)
        logg.debug("%s => %s", item, text)
        cond = 'abcdefgh...TUVWXYZ'
        self.assertEqual(cond, text)
        self.assertEqual(len(text), 18)
        item = "abcdefghijklmnopqr"
        text = tabtotext.str18(item)
        logg.debug("%s => %s", item, text)
        cond = item
        self.assertEqual(cond, text)
        self.assertEqual(len(text), 18)
        item = "abcdefghijklmnopqrs"
        text = tabtotext.str18(item)
        logg.debug("%s => %s", item, text)
        cond = "abcdefgh...mnopqrs"
        self.assertEqual(cond, text)
        self.assertEqual(len(text), 18)
    def test_1027(self) -> None:
        item = "abcdefghijklmnopqrstuvwxyz123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        text = tabtotext.str27(item)
        logg.debug("%s => %s", item, text)
        cond = 'abcdefghijklmnopq...TUVWXYZ'
        self.assertEqual(cond, text)
        self.assertEqual(len(text), 27)
        item = "abcdefghijklmnopqruvwxyzABC"
        text = tabtotext.str27(item)
        logg.debug("%s => %s", item, text)
        cond = item
        self.assertEqual(cond, text)
        self.assertEqual(len(text), 27)
        item = "abcdefghijklmnopqruvwxyzABCD"
        text = tabtotext.str27(item)
        logg.debug("%s => %s", item, text)
        cond = "abcdefghijklmnopq...xyzABCD"
        self.assertEqual(cond, text)
        self.assertEqual(len(text), 27)
    def test_1040(self) -> None:
        item = "abcdefghijklmnopqrstuvwxyz123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        text = tabtotext.str40(item)
        logg.debug("%s => %s", item, text)
        cond = 'abcdefghijklmnopqrstuvwxyz1234...TUVWXYZ'
        self.assertEqual(cond, text)
        self.assertEqual(len(text), 40)
        item = "abcdefghijklmnopqruvwxyz123456789ABCDEFG"
        text = tabtotext.str40(item)
        logg.debug("%s => %s", item, text)
        cond = item
        self.assertEqual(cond, text)
        self.assertEqual(len(text), 40)
        item = "abcdefghijklmnopqruvwxyz123456789ABCDEFGH"
        text = tabtotext.str40(item)
        logg.debug("%s => %s", item, text)
        cond = "abcdefghijklmnopqruvwxyz123456...BCDEFGH"
        self.assertEqual(cond, text)
        self.assertEqual(len(text), 40)
    def test_2000(self) -> None:
        hr = tabtotext.TabHeaders(["b", "a"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a")
        self.assertEqual(hr.cols[1].formats, "b")
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "b")
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["b"])
    def test_2005(self) -> None:
        hr = tabtotext.TabHeaders(["b:i", "a:s"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a:s")
        self.assertEqual(hr.cols[1].formats, "b:i")
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "b")
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["b"])
    def test_2010(self) -> None:
        hr = tabtotext.TabHeaders(["b", "a@c"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].formats, "a")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["a"])
    def test_2015(self) -> None:
        hr = tabtotext.TabHeaders(["b:i", "a:s@c"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b:i")
        self.assertEqual(hr.cols[1].formats, "a:s")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["a"])
    def test_2020(self) -> None:
        hr = tabtotext.TabHeaders(["b", "a@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a")
        self.assertEqual(hr.cols[1].formats, "b")
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "b")
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["b"])
    def test_2025(self) -> None:
        hr = tabtotext.TabHeaders(["b:i", "a:s@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a:s")
        self.assertEqual(hr.cols[1].formats, "b:i")
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "b")
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["b"])
    def test_2030(self) -> None:
        hr = tabtotext.TabHeaders(["b@2", "a@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].formats, "a")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "a")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["a"])
    def test_2035(self) -> None:
        hr = tabtotext.TabHeaders(["b:i@2", "a:s@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b:i")
        self.assertEqual(hr.cols[1].formats, "a:s")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "a")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["a"])
    def test_2040(self) -> None:
        hr = tabtotext.TabHeaders(["b@2", "a@c@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].formats, "a")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["a"])
    def test_2045(self) -> None:
        hr = tabtotext.TabHeaders(["b:i@2", "a:s@c@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b:i")
        self.assertEqual(hr.cols[1].formats, "a:s")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["a"])
    def test_2050(self) -> None:
        hr = tabtotext.TabHeaders(["b@2", "a", "c@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].formats, "c")
        self.assertEqual(hr.cols[2].formats, "a")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[2].title(), "a")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["a"])
    def test_2055(self) -> None:
        hr = tabtotext.TabHeaders(["b:i@2", "a:s", "c:x@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b:i")
        self.assertEqual(hr.cols[1].formats, "c:x")
        self.assertEqual(hr.cols[2].formats, "a:s")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[2].title(), "a")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["a"])
    def test_2060(self) -> None:
        hr = tabtotext.TabHeaders(["b@2", "a", "c@-3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].formats, "a")
        self.assertEqual(hr.cols[2].formats, "c")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "a")
        self.assertEqual(hr.cols[2].title(), "c")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["a"])
        self.assertEqual(hr.cols[2].fields, ["c"])
    def test_2061(self) -> None:
        hr = tabtotext.TabHeaders(["b@2", "a", "c@~3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].formats, "a")
        self.assertEqual(hr.cols[2].formats, "c")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "a")
        self.assertEqual(hr.cols[2].title(), "c")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["a"])
        self.assertEqual(hr.cols[2].fields, ["c"])
    def test_2065(self) -> None:
        hr = tabtotext.TabHeaders(["b:i@2", "a:s", "c:x@-3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b:i")
        self.assertEqual(hr.cols[1].formats, "a:s")
        self.assertEqual(hr.cols[2].formats, "c:x")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "a")
        self.assertEqual(hr.cols[2].title(), "c")
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["a"])
        self.assertEqual(hr.cols[2].fields, ["c"])

    def test_2070(self) -> None:
        hr = tabtotext.TabHeaders(["b@-2", "a", "c@-3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a")
        self.assertEqual(hr.cols[1].formats, "c")
        self.assertEqual(hr.cols[2].formats, "b")
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[2].title(), "b")  
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["b"])
    def test_2071(self) -> None:
        hr = tabtotext.TabHeaders(["b@-2", "a", "c@~3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a")
        self.assertEqual(hr.cols[1].formats, "c")
        self.assertEqual(hr.cols[2].formats, "b")
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[2].title(), "b")  
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["b"]) 
    def test_2072(self) -> None:
        hr = tabtotext.TabHeaders(["b@~2", "a", "c@~3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a")
        self.assertEqual(hr.cols[1].formats, "c")
        self.assertEqual(hr.cols[2].formats, "b") 
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[2].title(), "b")  
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["b"])
    def test_2075(self) -> None:
        hr = tabtotext.TabHeaders(["b:i@-2", "a:s", "c:x@-3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a:s")
        self.assertEqual(hr.cols[1].formats, "c:x")
        self.assertEqual(hr.cols[2].formats, "b:i")
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "c")
        self.assertEqual(hr.cols[2].title(), "b")  
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["b"])
    def test_2080(self) -> None:
        hr = tabtotext.TabHeaders(["b@-2", "a@e", "c@d@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "c")
        self.assertEqual(hr.cols[1].formats, "a")
        self.assertEqual(hr.cols[2].formats, "b")
        self.assertEqual(hr.cols[0].title(), "d")
        self.assertEqual(hr.cols[1].title(), "e")
        self.assertEqual(hr.cols[2].title(), "b")  
        self.assertEqual(hr.cols[0].fields, ["c"])
        self.assertEqual(hr.cols[1].fields, ["a"])
        self.assertEqual(hr.cols[2].fields, ["b"])   
    def test_2085(self) -> None:
        hr = tabtotext.TabHeaders(["b:i@-2", "a:s@e", "c:x@d@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "c:x")
        self.assertEqual(hr.cols[1].formats, "a:s")
        self.assertEqual(hr.cols[2].formats, "b:i")
        self.assertEqual(hr.cols[0].title(), "d")
        self.assertEqual(hr.cols[1].title(), "e")
        self.assertEqual(hr.cols[2].title(), "b")  
        self.assertEqual(hr.cols[0].fields, ["c"])
        self.assertEqual(hr.cols[1].fields, ["a"])
        self.assertEqual(hr.cols[2].fields, ["b"])   
    def test_2090(self) -> None:
        hr = tabtotext.TabHeaders(["b@-2@", "a@e", "c@-1@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].formats, "c")
        self.assertEqual(hr.cols[2].formats, "a")
        self.assertEqual(hr.cols[0].title(), "-2")
        self.assertEqual(hr.cols[1].title(), "-1")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["a"])     
    def test_2095(self) -> None:
        hr = tabtotext.TabHeaders(["b:i@-2@", "a:s@e", "c:x@-1@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b:i")
        self.assertEqual(hr.cols[1].formats, "c:x")
        self.assertEqual(hr.cols[2].formats, "a:s")
        self.assertEqual(hr.cols[0].title(), "-2")
        self.assertEqual(hr.cols[1].title(), "-1")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["a"])  
    def test_2110(self) -> None:
        hr = tabtotext.TabHeaders(["{b}@-2@", "{a}@e", "{c}@-1@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "{b}")
        self.assertEqual(hr.cols[1].formats, "{c}")
        self.assertEqual(hr.cols[2].formats, "{a}")
        self.assertEqual(hr.cols[0].title(), "-2")
        self.assertEqual(hr.cols[1].title(), "-1")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["a"])  
    def test_2115(self) -> None:
        hr = tabtotext.TabHeaders(["{b:i}@-2@", "{a:s}@e", "{c:x}@-1@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "{b:i}")
        self.assertEqual(hr.cols[1].formats, "{c:x}")
        self.assertEqual(hr.cols[2].formats, "{a:s}")
        self.assertEqual(hr.cols[0].title(), "-2")
        self.assertEqual(hr.cols[1].title(), "-1")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c"])
        self.assertEqual(hr.cols[2].fields, ["a"])  
    def test_2120(self) -> None:
        hr = tabtotext.TabHeaders(["{b}@-2@", "{a}@e", "{c}/{d}@-1@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "{b}")
        self.assertEqual(hr.cols[1].formats, "{c}/{d}")
        self.assertEqual(hr.cols[2].formats, "{a}")
        self.assertEqual(hr.cols[0].title(), "-2")
        self.assertEqual(hr.cols[1].title(), "-1")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c", "d"])
        self.assertEqual(hr.cols[2].fields, ["a"])  
    def test_2125(self) -> None:
        hr = tabtotext.TabHeaders(["{b:i}@-2@", "{a:s}@e", "{c:x}/{d:x}@-1@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "{b:i}")
        self.assertEqual(hr.cols[1].formats, "{c:x}/{d:x}")
        self.assertEqual(hr.cols[2].formats, "{a:s}")
        self.assertEqual(hr.cols[0].title(), "-2")
        self.assertEqual(hr.cols[1].title(), "-1")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c", "d"])
        self.assertEqual(hr.cols[2].fields, ["a"])  
    def test_2130(self) -> None:
        hr = tabtotext.TabHeaders(["{b}@-2@", "{a}@e", "{c}/{d}/{e}@-1@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "{b}")
        self.assertEqual(hr.cols[1].formats, "{c}/{d}/{e}")
        self.assertEqual(hr.cols[2].formats, "{a}")
        self.assertEqual(hr.cols[0].title(), "-2")
        self.assertEqual(hr.cols[1].title(), "-1")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c", "d", "e"])
        self.assertEqual(hr.cols[2].fields, ["a"])
    def test_2135(self) -> None:
        hr = tabtotext.TabHeaders(["{b:i}@-2@", "{a:s}@e", "{c:x}/{d:x}/{e:x}@-1@3"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "{b:i}")
        self.assertEqual(hr.cols[1].formats, "{c:x}/{d:x}/{e:x}")
        self.assertEqual(hr.cols[2].formats, "{a:s}")
        self.assertEqual(hr.cols[0].title(), "-2")
        self.assertEqual(hr.cols[1].title(), "-1")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c", "d", "e"])
        self.assertEqual(hr.cols[2].fields, ["a"])
    def test_2140(self) -> None:
        hr = tabtotext.TabHeaders(["{b}", "{a}@e", "{c}/{d}/{e}"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "{b}")
        self.assertEqual(hr.cols[1].formats, "{c}/{d}/{e}")
        self.assertEqual(hr.cols[2].formats, "{a}")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c|d|e")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c", "d", "e"])
        self.assertEqual(hr.cols[2].fields, ["a"])    
    def test_2145(self) -> None:
        hr = tabtotext.TabHeaders(["{b:i}", "{a:s}@e", "{c:x}/{d:x}/{e:x}"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "{b:i}")
        self.assertEqual(hr.cols[1].formats, "{c:x}/{d:x}/{e:x}")
        self.assertEqual(hr.cols[2].formats, "{a:s}")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c|d|e")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c", "d", "e"])
        self.assertEqual(hr.cols[2].fields, ["a"])       
    def test_2150(self) -> None:
        hr = tabtotext.TabHeaders(["b", "a@e", "c|d|e"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].formats, "c|d|e")
        self.assertEqual(hr.cols[2].formats, "a")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c|d|e")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c", "d", "e"])
        self.assertEqual(hr.cols[2].fields, ["a"])    
    def test_2155(self) -> None:
        hr = tabtotext.TabHeaders(["b:i", "a:s@e", "c:x|d:x|e:x"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "b:i")
        self.assertEqual(hr.cols[1].formats, "c:x|d:x|e:x")
        self.assertEqual(hr.cols[2].formats, "a:s")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].title(), "c|d|e")
        self.assertEqual(hr.cols[2].title(), "e")  
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].fields, ["c", "d", "e"])
        self.assertEqual(hr.cols[2].fields, ["a"])       
    def test_2220(self) -> None:
        hr = tabtotext.TabHeaders(["b", "a@3:1"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a")
        self.assertEqual(hr.cols[1].formats, "b")
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "b")
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["b"])
        self.assertEqual(hr.cols[0].order(), "3")
        self.assertEqual(hr.cols[1].order(), "b")
        self.assertEqual(hr.cols[0].sorts(), "1")
        self.assertEqual(hr.cols[1].sorts(), "b")
    def test_2225(self) -> None:
        hr = tabtotext.TabHeaders(["b:i", "a:s@3:1"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[0].formats, "a:s")
        self.assertEqual(hr.cols[1].formats, "b:i")
        self.assertEqual(hr.cols[0].title(), "a")
        self.assertEqual(hr.cols[1].title(), "b")
        self.assertEqual(hr.cols[0].fields, ["a"])
        self.assertEqual(hr.cols[1].fields, ["b"])
        self.assertEqual(hr.cols[0].order(), "3")
        self.assertEqual(hr.cols[1].order(), "b")
        self.assertEqual(hr.cols[0].sorts(), "1")
        self.assertEqual(hr.cols[1].sorts(), "b")
    def test_2230(self) -> None:
        hr = tabtotext.TabHeaders(["b@1:3", "a@3:1"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[1].formats, "a")
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].title(), "a")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].fields, ["a"])
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].order(), "3")
        self.assertEqual(hr.cols[0].order(), "1")
        self.assertEqual(hr.cols[1].sorts(), "1")
        self.assertEqual(hr.cols[0].sorts(), "3") # !!
    def test_2235(self) -> None:
        hr = tabtotext.TabHeaders(["b:i@1:3", "a:s@3:1"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[1].formats, "a:s")
        self.assertEqual(hr.cols[0].formats, "b:i")
        self.assertEqual(hr.cols[1].title(), "a")
        self.assertEqual(hr.cols[0].title(), "b")
        self.assertEqual(hr.cols[1].fields, ["a"])
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].order(), "3")
        self.assertEqual(hr.cols[0].order(), "1")
        self.assertEqual(hr.cols[1].sorts(), "1")
        self.assertEqual(hr.cols[0].sorts(), "3") # !!
    def test_2240(self) -> None:
        hr = tabtotext.TabHeaders(["b@c@1:3", "a@@3:1"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[1].formats, "a")
        self.assertEqual(hr.cols[0].formats, "b")
        self.assertEqual(hr.cols[1].title(), "a")
        self.assertEqual(hr.cols[0].title(), "c")
        self.assertEqual(hr.cols[1].fields, ["a"])
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].order(), "3")
        self.assertEqual(hr.cols[0].order(), "1")
        self.assertEqual(hr.cols[1].sorts(), "1")
        self.assertEqual(hr.cols[0].sorts(), "3") # !!
    def test_2245(self) -> None:
        hr = tabtotext.TabHeaders(["b:i@c@1:3", "a:s@@3:1"])
        logg.info("%i cols", len(hr.cols))
        for i, header in enumerate(hr.cols):
            logg.info("%4i %s", i, hr.cols[i])
        self.assertEqual(hr.cols[1].formats, "a:s")
        self.assertEqual(hr.cols[0].formats, "b:i")
        self.assertEqual(hr.cols[1].title(), "a")
        self.assertEqual(hr.cols[0].title(), "c")
        self.assertEqual(hr.cols[1].fields, ["a"])
        self.assertEqual(hr.cols[0].fields, ["b"])
        self.assertEqual(hr.cols[1].order(), "3")
        self.assertEqual(hr.cols[0].order(), "1")
        self.assertEqual(hr.cols[1].sorts(), "1")
        self.assertEqual(hr.cols[0].sorts(), "3") # !!
    #
    def test_5003(self) -> None:
        text = tabtotext.tabToCSV(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, [])
    def test_5004(self) -> None:
        text = tabtotext.tabToCSV(test004)
        logg.debug("%s => %s", test004, text)
        cond = ['', '', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, [])
    def test_5005(self) -> None:
        text = tabtotext.tabToCSV(test005)
        logg.debug("%s => %s", test005, text)
        cond = ['a', 'x', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test005)
    def test_5006(self) -> None:
        text = tabtotext.tabToCSV(test006)
        logg.debug("%s => %s", test006, text)
        cond = ['a;b', 'x;y', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test006)
    def test_5007(self) -> None:
        text = tabtotext.tabToCSV(test007)
        logg.debug("%s => %s", test007, text)
        cond = ['a;b', 'x;y', '~;v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test007Q)
    def test_5008(self) -> None:
        text = tabtotext.tabToCSV(test008)
        logg.debug("%s => %s", test008, text)
        cond = ['a;b', 'x;~', '~;v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test008Q)
    def test_5009(self) -> None:
        text = tabtotext.tabToCSV(test009)
        logg.debug("%s => %s", test009, text)
        cond = ['b', '~', 'v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test009Q)
    def test_5011(self) -> None:
        text = tabtotext.tabToCSV(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['b', '~']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test011)
    def test_5012(self) -> None:
        text = tabtotext.tabToCSV(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['b', '(no)']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test012)
    def test_5013(self) -> None:
        text = tabtotext.tabToCSV(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['b', '(yes)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test013)
    def test_5014(self) -> None:
        text = tabtotext.tabToCSV(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['b', '""']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test014)
    def test_5015(self) -> None:
        text = tabtotext.tabToCSV(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['b', '5678']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test015Q)
    def test_5016(self) -> None:
        text = tabtotext.tabToCSV(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['b', '123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        if data[0]['b'] == "123":
            data[0]['b'] = 123
        self.assertEqual(data, test016)
    def test_5017(self) -> None:
        text = tabtotext.tabToCSV(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['b', '123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        if data[0]['b'] == "123.40":
            data[0]['b'] = 123.4
        self.assertEqual(data, test017)
    def test_5018(self) -> None:
        text = tabtotext.tabToCSV(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['b', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test018)
    def test_5019(self) -> None:
        text = tabtotext.tabToCSV(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['b', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test018)  # test019
    def test_5021(self) -> None:
        """ legend is ignored for CSV """
        text = tabtotext.tabToCSV(test011, legend="a result")
        logg.debug("%s => %s", test011, text)
        cond = ['b', '~']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test011)
    def test_5031(self) -> None:
        """ legend is ignored for CSV """
        text = tabtotext.tabToCSV(test011, legend=["a result", "was found"])
        logg.debug("%s => %s", test011, text)
        cond = ['b', '~']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test011)
    def test_5044(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToCSV(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1;y', '2;x']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5045(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToCSV(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['b;a;c', '1;y;~', '2;x;~', '~;~;h', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': 'y', 'b': 1, 'c': None}, {'a': 'x', 'b': 2, 'c': None}, {'a': None, 'b': None, 'c': "h"}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5046(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToCSV(itemlist, sorts=['b', 'a'], reorder=['a', 'b'])
        logg.debug("%s => %s", test004, text)
        cond = ['a;b;c', 'y;1;~', 'x;2;~', '~;~;h', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': 'y', 'b': 1, 'c': None}, {'a': 'x', 'b': 2, 'c': None}, {'a': None, 'b': None, 'c': "h"}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5051(self) -> None:
        text = tabtotext.tabToCSVx(data011)
        logg.debug("%s => %s", data011, text)
        cond = ['b', '~']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test011)
    def test_5052(self) -> None:
        text = tabtotext.tabToCSVx(data012)
        logg.debug("%s => %s", data012, text)
        cond = ['b', '(no)']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test012)
    def test_5053(self) -> None:
        text = tabtotext.tabToCSVx(data013)
        logg.debug("%s => %s", data013, text)
        cond = ['b', '(yes)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test013)
    def test_5054(self) -> None:
        text = tabtotext.tabToCSVx(data014)
        logg.debug("%s => %s", data014, text)
        cond = ['b', '""']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test014)
    def test_5055(self) -> None:
        text = tabtotext.tabToCSVx(data015)
        logg.debug("%s => %s", data015, text)
        cond = ['b', '5678']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test015Q)
    def test_5056(self) -> None:
        text = tabtotext.tabToCSVx(data016)
        logg.debug("%s => %s", data016, text)
        cond = ['b', '123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        if data[0]['b'] == "123":
            data[0]['b'] = 123
        self.assertEqual(data, test016)
    def test_5057(self) -> None:
        text = tabtotext.tabToCSVx(data017)
        logg.debug("%s => %s", data017, text)
        cond = ['b', '123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        if data[0]['b'] == "123.40":
            data[0]['b'] = 123.4
        self.assertEqual(data, test017)
    def test_5058(self) -> None:
        text = tabtotext.tabToCSVx(data018)
        logg.debug("%s => %s", data018, text)
        cond = ['b', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test018)
    def test_5059(self) -> None:
        text = tabtotext.tabToCSVx(data019)
        logg.debug("%s => %s", data019, text)
        cond = ['b', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test018)  # test019

    def test_5071(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": ' {:}'}
        headers = ['b', 'a']
        text = tabtotext.tabToCSV(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1; y', '2; x']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': ' y', 'b': 1}, {'a': ' x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5072(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": ' %s'}
        headers = ['b', 'a']
        text = tabtotext.tabToCSV(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1; y', '2; x']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': ' y', 'b': 1}, {'a': ' x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5073(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": '(%s)', "b": "%.2f"}
        headers = ['b', 'a']
        text = tabtotext.tabToCSV(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1;(y)', '2;(x)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': '(y)', 'b': 1}, {'a': '(x)', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5074(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": '({:})', "b": "{:.2f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToCSV(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1.00;(y)', '2.00;(x)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': '(y)', 'b': 1}, {'a': '(x)', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5075(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '({:})', "b": "%.2f"}
        headers = ['b', 'a']
        text = tabtotext.tabToCSV(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1.00;(y)', '2.00;(x)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': '(y)', 'b': 1}, {'a': '(x)', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5076(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '({:})', "b": "{:.3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToCSV(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1.000;(y)', '2.000;(x)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': '(y)', 'b': 1}, {'a': '(x)', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5077(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '({:5s})', "b": "{:3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToCSV(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1.000000;(y    )', '2.000000;(x    )']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': '(y    )', 'b': 1.0}, {'a': '(x    )', 'b': 2.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5078(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:5s}"', "b": "{:3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToCSV(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1.000000;"""y    """', '2.000000;"""x    """']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': '"y    "', 'b': 1.0}, {'a': '"x    "', 'b': 2.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5079(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 22.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:>5s}"', "b": "{:>3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToCSV(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['b;a', '1.000000;"""    y"""', '22.000000;"""    x"""']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': '"    y"', 'b': 1.0}, {'a': '"    x"', 'b': 22.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)

    def test_5200(self) -> None:
        try:
            import yaml  # type: ignore[import]
            cond = ['data:', '- a: "x"', '- b: "v"']
            text = "\n".join(cond)
            data = yaml.safe_load(text)
            logg.debug("%s => %s", text, data)
            back = {'data': test008}
            self.assertEqual(back, data)
        except ImportError as e:
            logg.info("yaml %s - %s", "ImportError", e)
            raise unittest.SkipTest("no yaml lib")
    def test_5201(self) -> None:
        try:
            import yaml  # type: ignore[import]
            cond = ['data:', '- a: "x"', '  b: null', '- a: null', '  b: "v"']
            text = "\n".join(cond)
            data = yaml.safe_load(text)
            logg.debug("%s => %s", text, data)
            back = {'data': test008Q}
            self.assertEqual(back, data)
        except ImportError as e:
            logg.info("yaml %s - %s", "ImportError", e)
            raise unittest.SkipTest("no yaml lib")
    def test_5202(self) -> None:
        try:
            import yaml  # type: ignore[import]
            cond = ['data:', '- a: "x"', '  b: "y"']
            text = "\n".join(cond)
            data = yaml.safe_load(text)
            logg.debug("%s => %s", text, data)
            back = {'data': test006}
            self.assertEqual(back, data)
        except ImportError as e:
            logg.info("yaml %s - %s", "ImportError", e)
            raise unittest.SkipTest("no yaml lib")
    def test_5204(self) -> None:
        try:
            import yaml  # type: ignore[import]
            cond = ['# some comment', 'data:', '- b: false', ]
            text = "\n".join(cond)
            data = yaml.safe_load(text)
            logg.debug("%s => %s", text, data)
            back = {'data': test012}
            self.assertEqual(back, data)
        except ImportError as e:
            logg.info("yaml %s - %s", "ImportError", e)
            raise unittest.SkipTest("no yaml lib")
    def test_5205(self) -> None:
        try:
            import toml  # type: ignore[import]
            cond = ['[[data]]', 'a = "x"', 'b = "y"']
            text = "\n".join(cond)
            data = toml.loads(text)
            logg.debug("%s => %s", text, data)
            back = {'data': test006}
            self.assertEqual(back, data)
        except ImportError as e:
            logg.info("toml %s - %s", "ImportError", e)
            raise unittest.SkipTest("no toml lib")
    def test_5206(self) -> None:
        try:
            import toml  # type: ignore[import]
            cond = ['[[data]]', 'a = "x"', 'b = null', '[[data]]', 'a = null', '  b = "v"']
            text = "\n".join(cond)
            data = toml.loads(text)
            logg.debug("%s => %s", text, data)
            back = {'data': test008Q}
            self.assertEqual(back, data)
        except ImportError as e:
            logg.info("toml %s - %s", "ImportError", e)
            raise unittest.SkipTest("no toml lib")
        except ValueError as e:
            logg.debug("toml %s - %s", "ValueError", e)
            raise unittest.SkipTest("toml can not encode null")
    def test_5207(self) -> None:
        try:
            import toml  # type: ignore[import]
            cond = ['[[data]]', 'b = 2021-12-31']
            text = "\n".join(cond)
            data = toml.loads(text)
            logg.debug("%s => %s", text, data)
            back = {'data': test018}
            self.assertEqual(back, data)
        except ImportError as e:
            logg.info("toml %s - %s", "ImportError", e)
            raise unittest.SkipTest("no toml lib")
    def test_5208(self) -> None:
        try:
            import toml
            cond = ['[[data]]', 'b = 2021-12-31T23:34:45']
            text = "\n".join(cond)
            data = toml.loads(text)
            logg.debug("%s => %s", text, data)
            back = {'data': test019}
            self.assertEqual(back, data)
        except ImportError as e:
            logg.info("toml %s - %s", "ImportError", e)
            raise unittest.SkipTest("no toml lib")
    def test_5209(self) -> None:
        try:
            import toml
            cond = ['# some comment', '[[data]]', 'b = false']
            text = "\n".join(cond)
            data = toml.loads(text)
            logg.debug("%s => %s", text, data)
            back = {'data': test012}
            self.assertEqual(back, data)
        except ImportError as e:
            logg.info("toml %s - %s", "ImportError", e)
            raise unittest.SkipTest("no toml lib")
    def test_5211(self) -> None:
        text = tabtotext.tabToYAML(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['data:', '- b: null']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test011)
    def test_5212(self) -> None:
        text = tabtotext.tabToYAML(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['data:', '- b: false']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test012)
    def test_5213(self) -> None:
        text = tabtotext.tabToYAML(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['data:', '- b: true']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test013)
    def test_5214(self) -> None:
        text = tabtotext.tabToYAML(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['data:', '- b: ""']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test014)
    def test_5215(self) -> None:
        text = tabtotext.tabToYAML(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['data:', '- b: "5678"']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test015)
    def test_5216(self) -> None:
        text = tabtotext.tabToYAML(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['data:', '- b: 123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test016)
    def test_5217(self) -> None:
        text = tabtotext.tabToYAML(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['data:', '- b: 123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test017)
    def test_5218(self) -> None:
        text = tabtotext.tabToYAML(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['data:', '- b: 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test018)
    def test_5219(self) -> None:
        text = tabtotext.tabToYAML(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['data:', '- b: 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test018)  # test019
    def test_5221(self) -> None:
        text = tabtotext.tabToTOML(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['[[data]]', '']  # toml can not encode null
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test011Q)
    def test_5222(self) -> None:
        text = tabtotext.tabToTOML(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['[[data]]', 'b = false']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test012)
    def test_5223(self) -> None:
        text = tabtotext.tabToTOML(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['[[data]]', 'b = true']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test013)
    def test_5224(self) -> None:
        text = tabtotext.tabToTOML(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['[[data]]', 'b = ""']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test014)
    def test_5225(self) -> None:
        text = tabtotext.tabToTOML(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['[[data]]', 'b = "5678"']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test015)
    def test_5226(self) -> None:
        text = tabtotext.tabToTOML(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['[[data]]', 'b = 123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test016)
    def test_5227(self) -> None:
        text = tabtotext.tabToTOML(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['[[data]]', 'b = 123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test017)
    def test_5228(self) -> None:
        text = tabtotext.tabToTOML(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['[[data]]', 'b = 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test018)
    def test_5229(self) -> None:
        text = tabtotext.tabToTOML(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['[[data]]', 'b = 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test018)  # test019

    def test_5241(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 3}]
        text = tabtotext.tabToYAML(itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['data:', '- a: "x"', '  b: 2', '- a: "y"', '  b: 3', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        want = [{'a': 'x', 'b': 2}, {'a': 'y', 'b': 3}]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5242(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 3}]
        text = tabtotext.tabToTOMLx(itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['[[data]]', 'a = "x"', 'b = 2', '[[data]]', 'a = "y"', 'b = 3', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        want = [{'a': 'x', 'b': 2}, {'a': 'y', 'b': 3}]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5243(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToYAML(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['data:', '- b: 1', '  a: "y"', '- b: 2', '  a: "x"', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        want = [{'a': "y", 'b': 1}, {'a': "x", 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5244(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToTOML(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['[[data]]', 'b = 1', 'a = "y"', '[[data]]', 'b = 2', 'a = "x"', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5245(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToYAML(itemlist, sorts=['b', 'a'], reorder=['a', 'b'])
        logg.debug("%s => %s", test004, text)
        cond = ['data:', '- a: "y"', '  b: 1', '- a: "x"', '  b: 2', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        want = [{'a': "y", 'b': 1}, {'a': "x", 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5246(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToTOML(itemlist, sorts=['b', 'a'], reorder=['a', 'b'])
        logg.debug("%s => %s", test004, text)
        cond = ['[[data]]', 'a = "y"', 'b = 1', '[[data]]', 'a = "x"', 'b = 2', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5247(self) -> None:
        item1 = Item2("x", 2)
        item2 = Item2("y", 3)
        itemlist: DataList = [item1, item2]
        text = tabtotext.tabToYAMLx(itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['data:', '- a: "x"', '  b: 2', '- a: "y"', '  b: 3', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        want = [{'a': 'x', 'b': 2}, {'a': 'y', 'b': 3}]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5248(self) -> None:
        item1 = Item2("x", 2)
        item2 = Item2("y", 3)
        itemlist: DataList = [item1, item2]
        text = tabtotext.tabToTOMLx(itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['[[data]]', 'a = "x"', 'b = 2', '[[data]]', 'a = "y"', 'b = 3', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        want = [{'a': 'x', 'b': 2}, {'a': 'y', 'b': 3}]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)

    def test_5251(self) -> None:
        text = tabtotext.tabToYAMLx(data011)
        logg.debug("%s => %s", data011, text)
        cond = ['data:', '- b: null']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test011)
    def test_5252(self) -> None:
        text = tabtotext.tabToYAMLx(data012)
        logg.debug("%s => %s", data012, text)
        cond = ['data:', '- b: false']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test012)
    def test_5253(self) -> None:
        text = tabtotext.tabToYAMLx(data013)
        logg.debug("%s => %s", data013, text)
        cond = ['data:', '- b: true']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test013)
    def test_5254(self) -> None:
        text = tabtotext.tabToYAMLx(data014)
        logg.debug("%s => %s", data014, text)
        cond = ['data:', '- b: ""']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test014)
    def test_5255(self) -> None:
        text = tabtotext.tabToYAMLx(data015)
        logg.debug("%s => %s", data015, text)
        cond = ['data:', '- b: "5678"']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test015)
    def test_5256(self) -> None:
        text = tabtotext.tabToYAMLx(data016)
        logg.debug("%s => %s", data016, text)
        cond = ['data:', '- b: 123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test016)
    def test_5257(self) -> None:
        text = tabtotext.tabToYAMLx(data017)
        logg.debug("%s => %s", data017, text)
        cond = ['data:', '- b: 123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test017)
    def test_5258(self) -> None:
        text = tabtotext.tabToYAMLx(data018)
        logg.debug("%s => %s", data018, text)
        cond = ['data:', '- b: 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test018)
    def test_5259(self) -> None:
        text = tabtotext.tabToYAMLx(data019)
        logg.debug("%s => %s", data019, text)
        cond = ['data:', '- b: 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        self.assertEqual(data, test018)  # test019
    def test_5261(self) -> None:
        text = tabtotext.tabToTOMLx(data011)
        logg.debug("%s => %s", data011, text)
        cond = ['[[data]]', '']  # toml can not encode null
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test011Q)
    def test_5262(self) -> None:
        text = tabtotext.tabToTOMLx(data012)
        logg.debug("%s => %s", data012, text)
        cond = ['[[data]]', 'b = false']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test012)
    def test_5263(self) -> None:
        text = tabtotext.tabToTOMLx(data013)
        logg.debug("%s => %s", data013, text)
        cond = ['[[data]]', 'b = true']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test013)
    def test_5264(self) -> None:
        text = tabtotext.tabToTOMLx(data014)
        logg.debug("%s => %s", data014, text)
        cond = ['[[data]]', 'b = ""']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test014)
    def test_5265(self) -> None:
        text = tabtotext.tabToTOMLx(data015)
        logg.debug("%s => %s", data015, text)
        cond = ['[[data]]', 'b = "5678"']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test015)
    def test_5266(self) -> None:
        text = tabtotext.tabToTOMLx(data016)
        logg.debug("%s => %s", data016, text)
        cond = ['[[data]]', 'b = 123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test016)
    def test_5267(self) -> None:
        text = tabtotext.tabToTOMLx(data017)
        logg.debug("%s => %s", data017, text)
        cond = ['[[data]]', 'b = 123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test017)
    def test_5268(self) -> None:
        text = tabtotext.tabToTOMLx(data018)
        logg.debug("%s => %s", data018, text)
        cond = ['[[data]]', 'b = 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test018)
    def test_5269(self) -> None:
        text = tabtotext.tabToTOMLx(data019)
        logg.debug("%s => %s", data019, text)
        cond = ['[[data]]', 'b = 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        self.assertEqual(data, test018)  # test019

    def test_5500(self) -> None:
        data = json.loads("[]")
        self.assertEqual(data, [])
    def test_5501(self) -> None:
        data = json.loads("[{}]")
        self.assertEqual(data, [{}])
    def test_5502(self) -> None:
        try:
            data = json.loads("[{},]")
            self.assertEqual(data, [{}])
        except json.decoder.JSONDecodeError as e:
            self.assertIn("Expecting value", str(e))
    # note that json can not encode comments
    def test_5503(self) -> None:
        text = tabtotext.tabToJSON(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['[', '', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test003)
    def test_5504(self) -> None:
        text = tabtotext.tabToJSON(test004)
        logg.debug("%s => %s", test004, text)
        cond = ['[', ' {}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test004)
    def test_5505(self) -> None:
        text = tabtotext.tabToJSON(test005)
        logg.debug("%s => %s", test005, text)
        cond = ['[', ' {"a": "x"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test005)
    def test_5506(self) -> None:
        text = tabtotext.tabToJSON(test006)
        logg.debug("%s => %s", test006, text)
        cond = ['[', ' {"a": "x", "b": "y"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test006)
    def test_5507(self) -> None:
        text = tabtotext.tabToJSON(test007)
        logg.debug("%s => %s", test007, text)
        cond = ['[', ' {"a": "x", "b": "y"},', ' {"b": "v"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test007)
    def test_5508(self) -> None:
        text = tabtotext.tabToJSON(test008)
        logg.debug("%s => %s", test008, text)
        cond = ['[', ' {"a": "x"},', ' {"b": "v"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test008)
    def test_5509(self) -> None:
        text = tabtotext.tabToJSON(test009)
        logg.debug("%s => %s", test009, text)
        cond = ['[', ' {},', ' {"b": "v"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test009)
    def test_5511(self) -> None:
        text = tabtotext.tabToJSON(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['[', ' {"b": null}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test011)
    def test_5512(self) -> None:
        text = tabtotext.tabToJSON(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['[', ' {"b": false}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test012)
    def test_5513(self) -> None:
        text = tabtotext.tabToJSON(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['[', ' {"b": true}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test013)
    def test_5514(self) -> None:
        text = tabtotext.tabToJSON(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['[', ' {"b": ""}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test014)
    def test_5515(self) -> None:
        text = tabtotext.tabToJSON(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['[', ' {"b": "5678"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test015)
    def test_5516(self) -> None:
        text = tabtotext.tabToJSON(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['[', ' {"b": 123}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test016)
    def test_5517(self) -> None:
        text = tabtotext.tabToJSON(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['[', ' {"b": 123.40}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test017)
    def test_5518(self) -> None:
        text = tabtotext.tabToJSON(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['[', ' {"b": "2021-12-31"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test018)
    def test_5519(self) -> None:
        text = tabtotext.tabToJSON(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['[', ' {"b": "2021-12-31"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test018)  # test019
    def test_5521(self) -> None:
        """ legend is ignored for JSON output """
        text = tabtotext.tabToJSON(test011, legend="a result")
        logg.debug("%s => %s", test011, text)
        cond = ['[', ' {"b": null}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test011)
    def test_5531(self) -> None:
        """ legend is ignored for JSON output """
        text = tabtotext.tabToJSON(test011, legend=["a result", "was found"])
        logg.debug("%s => %s", test011, text)
        cond = ['[', ' {"b": null}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test011)
    def test_5544(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToJSON(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['[', ' {"b": 1, "a": "y"},', ' {"b": 2, "a": "x"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5545(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToJSON(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['[', ' {"b": 1, "a": "y"},', ' {"b": 2, "a": "x"},', ' {"c": "h"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, {'c': "h"}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5546(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToJSON(itemlist, sorts=['b', 'a'], reorder=['a', 'b'])
        logg.debug("%s => %s", test004, text)
        cond = ['[', ' {"a": "y", "b": 1},', ' {"a": "x", "b": 2},', ' {"c": "h"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, {'c': "h"}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_5551(self) -> None:
        text = tabtotext.tabToJSONx(data011)
        logg.debug("%s => %s", data011, text)
        cond = ['[', ' {"b": null}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test011)
    def test_5552(self) -> None:
        text = tabtotext.tabToJSONx(data012)
        logg.debug("%s => %s", data012, text)
        cond = ['[', ' {"b": false}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test012)
    def test_5553(self) -> None:
        text = tabtotext.tabToJSONx(data013)
        logg.debug("%s => %s", data013, text)
        cond = ['[', ' {"b": true}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test013)
    def test_5554(self) -> None:
        text = tabtotext.tabToJSONx(data014)
        logg.debug("%s => %s", data014, text)
        cond = ['[', ' {"b": ""}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test014)
    def test_5555(self) -> None:
        text = tabtotext.tabToJSONx(data015)
        logg.debug("%s => %s", data015, text)
        cond = ['[', ' {"b": "5678"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test015)
    def test_5556(self) -> None:
        text = tabtotext.tabToJSONx(data016)
        logg.debug("%s => %s", data016, text)
        cond = ['[', ' {"b": 123}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test016)
    def test_5557(self) -> None:
        text = tabtotext.tabToJSONx(data017)
        logg.debug("%s => %s", data017, text)
        cond = ['[', ' {"b": 123.40}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test017)
    def test_5558(self) -> None:
        text = tabtotext.tabToJSONx(data018)
        logg.debug("%s => %s", data018, text)
        cond = ['[', ' {"b": "2021-12-31"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test018)
    def test_5559(self) -> None:
        text = tabtotext.tabToJSONx(data019)
        logg.debug("%s => %s", data019, text)
        cond = ['[', ' {"b": "2021-12-31"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test018)  # test019

    def test_7003(self) -> None:
        text = tabtotext.tabToGFM(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['', '']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, [])
    def test_7004(self) -> None:
        text = tabtotext.tabToGFM(test004)
        logg.debug("%s => %s", test004, text)
        cond = ['', '', '']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, [])
    def test_7005(self) -> None:
        text = tabtotext.tabToGFM(test005)
        logg.debug("%s => %s", test005, text)
        cond = ['| a', '| -----', '| x']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test005)
    def test_7006(self) -> None:
        text = tabtotext.tabToGFM(test006)
        logg.debug("%s => %s", test006, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | y']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test006)
    def test_7007(self) -> None:
        text = tabtotext.tabToGFM(test007)
        logg.debug("%s => %s", test007, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | y', '| ~     | v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test007Q)
    def test_7008(self) -> None:
        text = tabtotext.tabToGFM(test008)
        logg.debug("%s => %s", test008, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | ~', '| ~     | v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test008Q)
    def test_7009(self) -> None:
        text = tabtotext.tabToGFM(test009)
        logg.debug("%s => %s", test009, text)
        cond = ['| b', '| -----', '| ~', '| v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test009Q)
    def test_7011(self) -> None:
        text = tabtotext.tabToGFM(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['| b', '| -----', '| ~']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test011)
    def test_7012(self) -> None:
        text = tabtotext.tabToGFM(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['| b', '| -----', '| (no)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test012)
    def test_7013(self) -> None:
        text = tabtotext.tabToGFM(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['| b', '| -----', '| (yes)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test013)
    def test_7014(self) -> None:
        text = tabtotext.tabToGFM(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['| b', '| -----', '|']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test014)
    def test_7015(self) -> None:
        text = tabtotext.tabToGFM(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['| b', '| -----', '| 5678']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test015Q)
    def test_7016(self) -> None:
        text = tabtotext.tabToGFM(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['| b', '| -----', '| 123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test016)
    def test_7017(self) -> None:
        text = tabtotext.tabToGFM(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['| b', '| ------', '| 123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test017)
    def test_7018(self) -> None:
        text = tabtotext.tabToGFM(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['| b', '| ----------', '| 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test018)
    def test_7019(self) -> None:
        text = tabtotext.tabToGFM(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['| b', '| ----------', '| 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test019Q)
    def test_7021(self) -> None:
        text = tabtotext.tabToGFM(test011, legend="a result")
        logg.debug("%s => %s", test011, text)
        cond = ['| b', '| -----', '| ~', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test011)
    def test_7022(self) -> None:
        text = tabtotext.tabToGFM(test012, legend="a result")
        logg.debug("%s => %s", test012, text)
        cond = ['| b', '| -----', '| (no)', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test012)
    def test_7023(self) -> None:
        text = tabtotext.tabToGFM(test013, legend="a result")
        logg.debug("%s => %s", test013, text)
        cond = ['| b', '| -----', '| (yes)', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test013)
    def test_7024(self) -> None:
        text = tabtotext.tabToGFM(test014, legend="a result")
        logg.debug("%s => %s", test014, text)
        cond = ['| b', '| -----', '|', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test014)
    def test_7025(self) -> None:
        text = tabtotext.tabToGFM(test015, legend="a result")
        logg.debug("%s => %s", test015, text)
        cond = ['| b', '| -----', '| 5678', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test015Q)
    def test_7026(self) -> None:
        text = tabtotext.tabToGFM(test016, legend="a result")
        logg.debug("%s => %s", test016, text)
        cond = ['| b', '| -----', '| 123', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test016)
    def test_7027(self) -> None:
        text = tabtotext.tabToGFM(test017, legend="a result")
        logg.debug("%s => %s", test018, text)
        cond = ['| b', '| ------', '| 123.40', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test017)
    def test_7028(self) -> None:
        text = tabtotext.tabToGFM(test018, legend="a result")
        logg.debug("%s => %s", test018, text)
        cond = ['| b', '| ----------', '| 2021-12-31', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test018)
    def test_7029(self) -> None:
        text = tabtotext.tabToGFM(test019, legend="a result")
        logg.debug("%s => %s", test019, text)
        cond = ['| b', '| ----------', '| 2021-12-31', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test019Q)
    def test_7031(self) -> None:
        text = tabtotext.tabToGFM(test011, legend=["a result", "was found"])
        logg.debug("%s => %s", test011, text)
        cond = ['| b', '| -----', '| ~', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test011)
    def test_7032(self) -> None:
        text = tabtotext.tabToGFM(test012, legend=["a result", "was found"])
        logg.debug("%s => %s", test012, text)
        cond = ['| b', '| -----', '| (no)', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test012)
    def test_7033(self) -> None:
        text = tabtotext.tabToGFM(test013, legend=["a result", "was found"])
        logg.debug("%s => %s", test013, text)
        cond = ['| b', '| -----', '| (yes)', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test013)
    def test_7034(self) -> None:
        text = tabtotext.tabToGFM(test014, legend=["a result", "was found"])
        logg.debug("%s => %s", test014, text)
        cond = ['| b', '| -----', '|', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test014)
    def test_7035(self) -> None:
        text = tabtotext.tabToGFM(test015, legend=["a result", "was found"])
        logg.debug("%s => %s", test015, text)
        cond = ['| b', '| -----', '| 5678', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test015Q)
    def test_7036(self) -> None:
        text = tabtotext.tabToGFM(test016, legend=["a result", "was found"])
        logg.debug("%s => %s", test016, text)
        cond = ['| b', '| -----', '| 123', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test016)
    def test_7037(self) -> None:
        text = tabtotext.tabToGFM(test017, legend=["a result", "was found"])
        logg.debug("%s => %s", test017, text)
        cond = ['| b', '| ------', '| 123.40', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test017)
    def test_7038(self) -> None:
        text = tabtotext.tabToGFM(test018, legend=["a result", "was found"])
        logg.debug("%s => %s", test018, text)
        cond = ['| b', '| ----------', '| 2021-12-31', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test018)
    def test_7039(self) -> None:
        text = tabtotext.tabToGFM(test019, legend=["a result", "was found"])
        logg.debug("%s => %s", test019, text)
        cond = ['| b', '| ----------', '| 2021-12-31', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test019Q)

    def test_7044(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToGFM(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['| b     | a', '| ----- | -----', '| 1     | y', '| 2     | x']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7045(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToGFM(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['| b     | a     | c', '| ----- | ----- | -----',
                '| 1     | y     | ~', '| 2     | x     | ~', '| ~     | ~     | h', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': 'y', 'b': 1, 'c': None}, {'a': 'x', 'b': 2, 'c': None}, {'a': None, 'b': None, 'c': "h"}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7046(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToGFM(itemlist, sorts=['b', 'a'], reorder=['a', 'b'])
        logg.debug("%s => %s", test004, text)
        cond = ['| a     | b     | c', '| ----- | ----- | -----',
                '| y     | 1     | ~', '| x     | 2     | ~', '| ~     | ~     | h', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': 'y', 'b': 1, 'c': None}, {'a': 'x', 'b': 2, 'c': None}, {'a': None, 'b': None, 'c': "h"}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7048(self) -> None:
        item = Item2("x", 2)
        text = tabtotext.tabToGFMx(item)
        logg.debug("%s => %s", test004, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | 2']
        self.assertEqual(cond, text.splitlines())
    def test_7049(self) -> None:
        item = Item2("x", 2)
        itemlist: DataList = [item]
        text = tabtotext.tabToGFMx(itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | 2']
        self.assertEqual(cond, text.splitlines())
    def test_7051(self) -> None:
        text = tabtotext.tabToGFMx(data011)
        logg.debug("%s => %s", data011, text)
        cond = ['| b', '| -----', '| ~']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test011)
    def test_7052(self) -> None:
        text = tabtotext.tabToGFMx(data012)
        logg.debug("%s => %s", data012, text)
        cond = ['| b', '| -----', '| (no)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test012)
    def test_7053(self) -> None:
        text = tabtotext.tabToGFMx(data013)
        logg.debug("%s => %s", data013, text)
        cond = ['| b', '| -----', '| (yes)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test013)
    def test_7054(self) -> None:
        text = tabtotext.tabToGFMx(data014)
        logg.debug("%s => %s", data014, text)
        cond = ['| b', '| -----', '|']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test014)
    def test_7055(self) -> None:
        text = tabtotext.tabToGFMx(data015)
        logg.debug("%s => %s", data015, text)
        cond = ['| b', '| -----', '| 5678']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test015Q)
    def test_7056(self) -> None:
        text = tabtotext.tabToGFMx(data016)
        logg.debug("%s => %s", data016, text)
        cond = ['| b', '| -----', '| 123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test016)
    def test_7057(self) -> None:
        text = tabtotext.tabToGFMx(data017)
        logg.debug("%s => %s", data017, text)
        cond = ['| b', '| ------', '| 123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test017)
    def test_7058(self) -> None:
        text = tabtotext.tabToGFMx(data018)
        logg.debug("%s => %s", data018, text)
        cond = ['| b', '| ----------', '| 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test018)
    def test_7059(self) -> None:
        text = tabtotext.tabToGFMx(data019)
        logg.debug("%s => %s", data019, text)
        cond = ['| b', '| ----------', '| 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test019Q)

    def test_7071(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": ' {:}'}
        headers = ['b', 'a']
        text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['| b     |     a', '| ----- | ----:', '| 1     |     y', '| 2     |     x']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7072(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": ' %s'}
        headers = ['b', 'a']
        text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['| b     |     a', '| ----- | ----:', '| 1     |     y', '| 2     |     x']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7073(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": '"%s"', "b": "%.2f"}
        headers = ['b', 'a']
        text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['| b     | a', '| ----- | -----', '| 1     | "y"', '| 2     | "x"']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7074(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": '"{:}"', "b": "{:.2f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['|     b | a', '| ----: | -----', '|  1.00 | "y"', '|  2.00 | "x"']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7075(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:}"', "b": "%.2f"}
        headers = ['b', 'a']
        text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['| b     | a', '| ----- | -----', '| 1.00  | "y"', '| 2.00  | "x"']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7076(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:}"', "b": "{:.2f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['|     b | a', '| ----: | -----', '|  1.00 | "y"', '|  2.00 | "x"']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7077(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:}"', "b": "{:$}"}
        headers = ['b', 'a']
        text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['|     b | a', '| ----: | -----', X('| 1.00$ | "y"'), X('| 2.00$ | "x"')]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7078(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:5s}"', "b": "{:3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['|        b | a', '| -------: | -------', '| 1.000000 | "y    "', '| 2.000000 | "x    "']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': '"y    "', 'b': 1.0}, {'a': '"x    "', 'b': 2.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7079(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 22.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:>5s}"', "b": "{:>3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['|         b |       a', '| --------: | ------:', '|  1.000000 | "    y"', '| 22.000000 | "    x"']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        want = [{'a': '"    y"', 'b': 1.0}, {'a': '"    x"', 'b': 22.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)

    def test_7403(self) -> None:
        text = tabtotext.tabToHTML(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['<table>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7404(self) -> None:
        text = tabtotext.tabToHTML(test004)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr></tr>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7405(self) -> None:
        text = tabtotext.tabToHTML(test005)
        logg.debug("%s => %s", test005, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7406(self) -> None:
        text = tabtotext.tabToHTML(test006)
        logg.debug("%s => %s", test006, text)
        cond = ['<table>',  # -
                '<tr><th>a</th><th>b</th></tr>',  # -
                '<tr><td>x</td><td>y</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7407(self) -> None:
        text = tabtotext.tabToHTML(test007)
        logg.debug("%s => %s", test007, text)
        cond = ['<table>',  # -
                '<tr><th>a</th><th>b</th></tr>',  # -
                '<tr><td>x</td><td>y</td></tr>',  # -
                '<tr><td></td><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7408(self) -> None:
        text = tabtotext.tabToHTML(test008)
        logg.debug("%s => %s", test008, text)
        cond = ['<table>',  # -
                '<tr><th>a</th><th>b</th></tr>',  # -
                '<tr><td>x</td><td></td></tr>',  # -
                '<tr><td></td><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7409(self) -> None:
        text = tabtotext.tabToHTML(test009)
        logg.debug("%s => %s", test009, text)
        cond = ['<table>',  # -
                '<tr><th>b</th></tr>',  # -
                '<tr><td></td></tr>',  # -
                '<tr><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7411(self) -> None:
        text = tabtotext.tabToHTML(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>~</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7412(self) -> None:
        text = tabtotext.tabToHTML(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>(no)</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7413(self) -> None:
        text = tabtotext.tabToHTML(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>(yes)</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7414(self) -> None:
        text = tabtotext.tabToHTML(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td></td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7415(self) -> None:
        text = tabtotext.tabToHTML(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>5678</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7416(self) -> None:
        text = tabtotext.tabToHTML(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>123</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7417(self) -> None:
        text = tabtotext.tabToHTML(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>123.40</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7418(self) -> None:
        text = tabtotext.tabToHTML(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>2021-12-31</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7419(self) -> None:
        text = tabtotext.tabToHTML(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>2021-12-31</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7421(self) -> None:
        text = tabtotext.tabToHTML(test011, legend="a result")
        logg.debug("%s => %s", test011, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>~</td></tr>', '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7422(self) -> None:
        text = tabtotext.tabToHTML(test012, legend="a result")
        logg.debug("%s => %s", test012, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>(no)</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7423(self) -> None:
        text = tabtotext.tabToHTML(test013, legend="a result")
        logg.debug("%s => %s", test013, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>(yes)</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7424(self) -> None:
        text = tabtotext.tabToHTML(test014, legend="a result")
        logg.debug("%s => %s", test014, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td></td></tr>', '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7425(self) -> None:
        text = tabtotext.tabToHTML(test015, legend="a result")
        logg.debug("%s => %s", test015, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>5678</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7426(self) -> None:
        text = tabtotext.tabToHTML(test016, legend="a result")
        logg.debug("%s => %s", test016, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>123</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7427(self) -> None:
        text = tabtotext.tabToHTML(test017, legend="a result")
        logg.debug("%s => %s", test017, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>123.40</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7428(self) -> None:
        text = tabtotext.tabToHTML(test018, legend="a result")
        logg.debug("%s => %s", test018, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>2021-12-31</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7429(self) -> None:
        text = tabtotext.tabToHTML(test019, legend="a result")
        logg.debug("%s => %s", test019, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>2021-12-31</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7431(self) -> None:
        text = tabtotext.tabToHTML(test011, legend=["a result", "was found"])
        logg.debug("%s => %s", test011, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>~</td></tr>', '</table>',
                '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7432(self) -> None:
        text = tabtotext.tabToHTML(test012, legend=["a result", "was found"])
        logg.debug("%s => %s", test012, text)
        cond = ['<table>', '<tr><th>b</th></tr>',
                '<tr><td>(no)</td></tr>', '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7433(self) -> None:
        text = tabtotext.tabToHTML(test013, legend=["a result", "was found"])
        logg.debug("%s => %s", test013, text)
        cond = ['<table>', '<tr><th>b</th></tr>',
                '<tr><td>(yes)</td></tr>', '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7434(self) -> None:
        text = tabtotext.tabToHTML(test014, legend=["a result", "was found"])
        logg.debug("%s => %s", test014, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td></td></tr>', '</table>',
                '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7435(self) -> None:
        text = tabtotext.tabToHTML(test015, legend=["a result", "was found"])
        logg.debug("%s => %s", test015, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>5678</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7436(self) -> None:
        text = tabtotext.tabToHTML(test016, legend=["a result", "was found"])
        logg.debug("%s => %s", test016, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>123</td></tr>', '</table>',
                '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7437(self) -> None:
        text = tabtotext.tabToHTML(test017, legend=["a result", "was found"])
        logg.debug("%s => %s", test017, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>123.40</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7438(self) -> None:
        text = tabtotext.tabToHTML(test018, legend=["a result", "was found"])
        logg.debug("%s => %s", test018, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>2021-12-31</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7439(self) -> None:
        text = tabtotext.tabToHTML(test019, legend=["a result", "was found"])
        logg.debug("%s => %s", test019, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>2021-12-31</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_7444(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToHTML(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b</th><th>a</th></tr>',
                '<tr><td>1</td><td>y</td></tr>', '<tr><td>2</td><td>x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7445(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToHTML(itemlist, sorts=['b', 'a'])
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b</th><th>a</th><th>c</th></tr>', '<tr><td>1</td><td>y</td><td></td></tr>',
                '<tr><td>2</td><td>x</td><td></td></tr>', '<tr><td></td><td></td><td>h</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': 'y', 'b': 1, 'c': None}, {'a': 'x', 'b': 2, 'c': None}, {'a': None, 'b': None, 'c': 'h'}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7446(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToHTML(itemlist, sorts=['b', 'a'], reorder=['a', 'b'])
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>a</th><th>b</th><th>c</th></tr>', '<tr><td>y</td><td>1</td><td></td></tr>',
                '<tr><td>x</td><td>2</td><td></td></tr>', '<tr><td></td><td></td><td>h</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': 'y', 'b': 1, 'c': None}, {'a': 'x', 'b': 2, 'c': None}, {'a': None, 'b': None, 'c': 'h'}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7451(self) -> None:
        text = tabtotext.tabToHTMLx(data011)
        logg.debug("%s => %s", data011, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>~</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7452(self) -> None:
        text = tabtotext.tabToHTMLx(data012)
        logg.debug("%s => %s", data012, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>(no)</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7453(self) -> None:
        text = tabtotext.tabToHTMLx(data013)
        logg.debug("%s => %s", data013, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>(yes)</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7454(self) -> None:
        text = tabtotext.tabToHTMLx(data014)
        logg.debug("%s => %s", data014, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td></td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7455(self) -> None:
        text = tabtotext.tabToHTMLx(data015)
        logg.debug("%s => %s", data015, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>5678</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7456(self) -> None:
        text = tabtotext.tabToHTMLx(data016)
        logg.debug("%s => %s", data016, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>123</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7457(self) -> None:
        text = tabtotext.tabToHTMLx(data017)
        logg.debug("%s => %s", data017, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>123.40</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7458(self) -> None:
        text = tabtotext.tabToHTMLx(data018)
        logg.debug("%s => %s", data018, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>2021-12-31</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7459(self) -> None:
        text = tabtotext.tabToHTMLx(data019)
        logg.debug("%s => %s", data019, text)
        cond = ['<table>', '<tr><th>b</th></tr>', '<tr><td>2021-12-31</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())

    def test_7471(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": ' {:}'}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b</th><th style="text-align: right">a</th></tr>',  # ,
                '<tr><td>1</td><td style="text-align: right"> y</td></tr>',  # ,
                '<tr><td>2</td><td style="text-align: right"> x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7472(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": ' %s'}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b</th><th style="text-align: right">a</th></tr>',  # ,
                '<tr><td>1</td><td style="text-align: right"> y</td></tr>',  # ,
                '<tr><td>2</td><td style="text-align: right"> x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7473(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": '"%s"', "b": "%.2f"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b</th><th>a</th></tr>',  # ,
                '<tr><td>1</td><td>&quot;y&quot;</td></tr>',  # ,
                '<tr><td>2</td><td>&quot;x&quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7474(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": '"{:}"', "b": "{:.2f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">b</th><th>a</th></tr>',  # ,
                '<tr><td style="text-align: right">1.00</td><td>&quot;y&quot;</td></tr>',  # ,
                '<tr><td style="text-align: right">2.00</td><td>&quot;x&quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7475(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:}"', "b": "%.2f"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b</th><th>a</th></tr>',  # ,
                '<tr><td>1.00</td><td>&quot;y&quot;</td></tr>',  # ,
                '<tr><td>2.00</td><td>&quot;x&quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7476(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:}"', "b": "{:.2f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">b</th><th>a</th></tr>',  # ,
                '<tr><td style="text-align: right">1.00</td><td>&quot;y&quot;</td></tr>',  # ,
                '<tr><td style="text-align: right">2.00</td><td>&quot;x&quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7477(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:}"', "b": "{:$}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">b</th><th>a</th></tr>',  # ,
                X('<tr><td style="text-align: right">1.00$</td><td>&quot;y&quot;</td></tr>'),  # ,
                X('<tr><td style="text-align: right">2.00$</td><td>&quot;x&quot;</td></tr>'), '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7478(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:5s}"', "b": "{:3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">b</th><th>a</th></tr>',  # ,
                '<tr><td style="text-align: right">1.000000</td><td>&quot;y    &quot;</td></tr>',  # ,
                '<tr><td style="text-align: right">2.000000</td><td>&quot;x    &quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y    "', 'b': 1.0}, {'a': '"x    "', 'b': 2.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7479(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 22.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:>5s}"', "b": "{:>3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">b</th><th style="text-align: right">a</th></tr>',  # ,
                '<tr><td style="text-align: right">1.000000</td><td style="text-align: right">&quot;    y&quot;</td></tr>',  # ,
                '<tr><td style="text-align: right">22.000000</td><td style="text-align: right">&quot;    x&quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"    y"', 'b': 1.0}, {'a': '"    x"', 'b': 22.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7503(self) -> None:
        text = tabtotext.tabToHTML(test003, combine={'a': 'b'})
        logg.debug("%s => %s", test003, text)
        cond = ['<table>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7504(self) -> None:
        text = tabtotext.tabToHTML(test004, combine={'a': 'b'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr></tr>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7505(self) -> None:
        text = tabtotext.tabToHTML(test005, combine={'a': 'b'})
        logg.debug("%s => %s", test005, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7506(self) -> None:
        text = tabtotext.tabToHTML(test006, combine={'a': 'b'})
        logg.debug("%s => %s", test006, text)
        cond = ['<table>',  # -
                '<tr><th>a<br />b</th></tr>',  # -
                '<tr><td>x<br />y</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7507(self) -> None:
        text = tabtotext.tabToHTML(test007, combine={'a': 'b'})
        logg.debug("%s => %s", test007, text)
        cond = ['<table>',  # -
                '<tr><th>a<br />b</th></tr>',  # -
                '<tr><td>x<br />y</td></tr>',  # -
                '<tr><td><br />v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7508(self) -> None:
        text = tabtotext.tabToHTML(test008, combine={'a': 'b'})
        logg.debug("%s => %s", test008, text)
        cond = ['<table>',  # -
                '<tr><th>a<br />b</th></tr>',  # -
                '<tr><td>x<br /></td></tr>',  # -
                '<tr><td><br />v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7509(self) -> None:
        text = tabtotext.tabToHTML(test009, combine={'a': 'b'})
        logg.debug("%s => %s", test009, text)
        cond = ['<table>',  # -
                '<tr><th>b</th></tr>',  # -
                '<tr><td></td></tr>',  # -
                '<tr><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())

    def test_7523(self) -> None:
        text = tabtotext.tabToHTML(test003, combine={'a': 'b'})
        logg.debug("%s => %s", test003, text)
        cond = ['<table>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7524(self) -> None:
        text = tabtotext.tabToHTML(test004, combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr></tr>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7525(self) -> None:
        text = tabtotext.tabToHTML(test005, combine={'b': 'a'})
        logg.debug("%s => %s", test005, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7526(self) -> None:
        text = tabtotext.tabToHTML(test006, combine={'b': 'a'})
        logg.debug("%s => %s", test006, text)
        cond = ['<table>',  # -
                '<tr><th>b<br />a</th></tr>',  # -
                '<tr><td>y<br />x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7527(self) -> None:
        text = tabtotext.tabToHTML(test007, combine={'b': 'a'})
        logg.debug("%s => %s", test007, text)
        cond = ['<table>',  # -
                '<tr><th>b<br />a</th></tr>',  # -
                '<tr><td>y<br />x</td></tr>',  # -
                '<tr><td>v<br /></td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7528(self) -> None:
        text = tabtotext.tabToHTML(test008, combine={'b': 'a'})
        logg.debug("%s => %s", test008, text)
        cond = ['<table>',  # -
                '<tr><th>b<br />a</th></tr>',  # -
                '<tr><td><br />x</td></tr>',  # -
                '<tr><td>v<br /></td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_7529(self) -> None:
        text = tabtotext.tabToHTML(test009, combine={'b': 'a'})
        logg.debug("%s => %s", test009, text)
        cond = ['<table>',  # -
                '<tr><th>b</th></tr>',  # -
                '<tr><td></td></tr>',  # -
                '<tr><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())

    def test_7544(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToHTML(itemlist, sorts=['b', 'a'], combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b<br />a</th></tr>',
                '<tr><td>1<br />y</td></tr>', '<tr><td>2<br />x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7545(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToHTML(itemlist, sorts=['b', 'a'], combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b<br />a</th><th>c</th></tr>', '<tr><td>1<br />y</td><td></td></tr>',
                '<tr><td>2<br />x</td><td></td></tr>', '<tr><td><br /></td><td>h</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': 'y', 'b': 1, 'c': None}, {'a': 'x', 'b': 2, 'c': None}, {'b': None, 'c': 'h'}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)

    def test_7554(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        text = tabtotext.tabToHTML(itemlist, sorts=['b', 'a'], combine={'a': 'b'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>a<br />b</th></tr>',
                '<tr><td>y<br />1</td></tr>', '<tr><td>x<br />2</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7555(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}, {'c': 'h'}]
        text = tabtotext.tabToHTML(itemlist, sorts=['b', 'a'], combine={'a': 'b'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>a<br />b</th><th>c</th></tr>', '<tr><td>y<br />1</td><td></td></tr>',
                '<tr><td>x<br />2</td><td></td></tr>', '<tr><td><br /></td><td>h</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': 'y', 'b': 1, 'c': None}, {'a': 'x', 'b': 2, 'c': None}, {'a': None, 'c': 'h'}, ]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)

    def test_7571(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": ' {:}'}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats, combine={'a': 'b'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">a<br />b</th></tr>',  # ,
                '<tr><td style="text-align: right"> y<br />1</td></tr>',  # ,
                '<tr><td style="text-align: right"> x<br />2</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': ' y', 'b': 1}, {'a': ' x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7572(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": ' %s'}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats, combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b<br />a</th></tr>',  # ,
                '<tr><td>1<br /> y</td></tr>',  # ,
                '<tr><td>2<br /> x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': ' y', 'b': 1}, {'a': ' x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7573(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": '"%s"', "b": "%.2f"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats, combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b<br />a</th></tr>',  # ,
                '<tr><td>1<br />&quot;y&quot;</td></tr>',  # ,
                '<tr><td>2<br />&quot;x&quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7574(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        formats = {"a": '"{:}"', "b": "{:.2f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats, combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">b<br />a</th></tr>',  # ,
                '<tr><td style="text-align: right">1.00<br />&quot;y&quot;</td></tr>',  # ,
                '<tr><td style="text-align: right">2.00<br />&quot;x&quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7575(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:}"', "b": "%.2f"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats, combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>b<br />a</th></tr>',  # ,
                '<tr><td>1.00<br />&quot;y&quot;</td></tr>',  # ,
                '<tr><td>2.00<br />&quot;x&quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7576(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:}"', "b": "{:.2f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats, combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">b<br />a</th></tr>',  # ,
                '<tr><td style="text-align: right">1.00<br />&quot;y&quot;</td></tr>',  # ,
                '<tr><td style="text-align: right">2.00<br />&quot;x&quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7577(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:}"', "b": "{:$}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats, combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">b<br />a</th></tr>',  # ,
                X('<tr><td style="text-align: right">1.00$<br />&quot;y&quot;</td></tr>'),  # ,
                X('<tr><td style="text-align: right">2.00$<br />&quot;x&quot;</td></tr>'), '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7578(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:5s}"', "b": "{:3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats, combine={'b': 'a'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">b<br />a</th></tr>',  # ,
                '<tr><td style="text-align: right">1.000000<br />&quot;y    &quot;</td></tr>',  # ,
                '<tr><td style="text-align: right">2.000000<br />&quot;x    &quot;</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"y    "', 'b': 1.0}, {'a': '"x    "', 'b': 2.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_7579(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 22.}, {'a': "y", 'b': 1.}]
        formats = {"a": '"{:>5s}"', "b": "{:>3f}"}
        headers = ['b', 'a']
        text = tabtotext.tabToHTML(itemlist, ['b', 'a'], formats, combine={'a': 'b'})
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th style="text-align: right">a<br />b</th></tr>',  # ,
                '<tr><td style="text-align: right">&quot;    y&quot;<br />1.000000</td></tr>',  # ,
                '<tr><td style="text-align: right">&quot;    x&quot;<br />22.000000</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadHTML(text)
        want = [{'a': '"    y"', 'b': 1.0}, {'a': '"    x"', 'b': 22.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)

    def test_8003(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test003, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test003, text)
        cond = ['']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, [])
    def test_8004(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test004, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['', '', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, [])
    def test_8005(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test005, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test005, text)
        cond = ['a', 'x', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test005)
    def test_8006(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test006, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test006, text)
        cond = ['a;b', 'x;y', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test006)
    def test_8007(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test007, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test007, text)
        cond = ['a;b', 'x;y', '~;v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test007Q)
    def test_8008(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test008, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test008, text)
        cond = ['a;b', 'x;~', '~;v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test008Q)
    def test_8009(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test009, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test009, text)
        cond = ['b', '~', 'v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test009Q)
    def test_8011(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test011, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test011, text)
        cond = ['b', '~']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test011)
    def test_8012(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test012, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test012, text)
        cond = ['b', '(no)']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test012)
    def test_8013(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test013, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test013, text)
        cond = ['b', '(yes)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test013)
    def test_8014(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test014, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test014, text)
        cond = ['b', '""']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test014)
    def test_8015(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test015, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test015, text)
        cond = ['b', '5678']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test015Q)
    def test_8016(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test016, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test016, text)
        cond = ['b', '123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        if data[0]['b'] == "123":
            data[0]['b'] = 123
        self.assertEqual(data, test016)
    def test_8017(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test017, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test017, text)
        cond = ['b', '123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        if data[0]['b'] == "123.40":
            data[0]['b'] = 123.4
        self.assertEqual(data, test017)
    def test_8018(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test018, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test018, text)
        cond = ['b', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test018)
    def test_8019(self) -> None:
        out = StringIO()
        res = tabtotext.print_tabtotext(out, test019, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test019, text)
        cond = ['b', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test018)  # test019

    def test_8690(self) -> None:
        item = Item2("x", 2)
        text = tabtotext.tabToFMTx("def", item)
        logg.debug("%s => %s", test004, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | 2']
        self.assertEqual(cond, text.splitlines())
    def test_8691(self) -> None:
        item = Item2("x", 2)
        itemlist: DataList = [item]
        text = tabtotext.tabToFMTx("def", itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | 2']
        self.assertEqual(cond, text.splitlines())
    def test_8692(self) -> None:
        item1 = Item2("x", 2)
        item2 = Item2("y", 3)
        itemlist: DataList = [item1, item2]
        text = tabtotext.tabToFMTx("html", itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>', '<tr><th>a</th><th>b</th></tr>',
                '<tr><td>x</td><td>2</td></tr>',
                '<tr><td>y</td><td>3</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_8693(self) -> None:
        item1 = Item2("x", 2)
        item2 = Item2("y", 3)
        itemlist: DataList = [item1, item2]
        text = tabtotext.tabToFMTx("csv", itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['a;b', 'x;2', 'y;3']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        want = [{'a': 'x', 'b': 2}, {'a': 'y', 'b': 3}]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_8694(self) -> None:
        item1 = Item2("x", 2)
        item2 = Item2("y", 3)
        itemlist: DataList = [item1, item2]
        text = tabtotext.tabToFMTx("json", itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['[', ' {"a": "x", "b": 2},', ' {"a": "y", "b": 3}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        want = [{'a': 'x', 'b': 2}, {'a': 'y', 'b': 3}]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_8695(self) -> None:
        item1 = Item2("x", 2)
        item2 = Item2("y", 3)
        itemlist: DataList = [item1, item2]
        text = tabtotext.tabToFMTx("yaml", itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['data:', '- a: "x"', '  b: 2', '- a: "y"', '  b: 3', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadYAML(text)
        want = [{'a': 'x', 'b': 2}, {'a': 'y', 'b': 3}]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_8696(self) -> None:
        item1 = Item2("x", 2)
        item2 = Item2("y", 3)
        itemlist: DataList = [item1, item2]
        text = tabtotext.tabToFMTx("toml", itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['[[data]]', 'a = "x"', 'b = 2', '[[data]]', 'a = "y"', 'b = 3', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadTOML(text)
        want = [{'a': 'x', 'b': 2}, {'a': 'y', 'b': 3}]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_8698(self) -> None:
        item1 = Item2("x", 2)
        item2 = Item2("y", 3)
        itemlist: DataList = [item1, item2]
        text = tabtotext.tabToFMTx("tabs", itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['\t a     \t b', '\t ----- \t -----', '\t x     \t 2', '\t y     \t 3']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text, tab='\t')
        want = [{'a': 'x', 'b': 2}, {'a': 'y', 'b': 3}]
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_8699(self) -> None:
        item1 = Item2("x", 2)
        item2 = Item2("y", 3)
        itemlist: DataList = [item1, item2]
        text = tabtotext.tabToFMTx("wide", itemlist)
        logg.debug("%s => %s", test004, text)
        cond = ['a     b', 'x     2', 'y     3']
        self.assertEqual(cond, text.splitlines())

    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9771(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test011)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 4000)
        self.assertGreater(5000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test011Q)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9772(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test012)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 4000)
        self.assertGreater(5000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test012)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9773(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test013)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 4000)
        self.assertGreater(5000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test013)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9774(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test014)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 4000)
        self.assertGreater(5000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test014)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9775(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test015)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 4000)
        self.assertGreater(5000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test015)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9776(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test016)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 4000)
        self.assertGreater(5000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test016)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9777(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test017)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 4000)
        self.assertGreater(5000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test017)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9778(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test018)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 4000)
        self.assertGreater(5000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test018Q)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9779(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test019)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 4000)
        self.assertGreater(5000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test019)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9781(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test011, legend="a result")
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 5000)
        self.assertGreater(6000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test011Q)
        # self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9782(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test012, legend="a result")
        sz = path.getsize(filename)
        self.assertGreater(sz, 5000)
        self.assertGreater(6000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test012)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9783(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test013, legend="a result")
        sz = path.getsize(filename)
        self.assertGreater(sz, 5000)
        self.assertGreater(6000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test013)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9784(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test014, legend="a result")
        sz = path.getsize(filename)
        self.assertGreater(sz, 5000)
        self.assertGreater(6000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test014)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9785(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test015, legend="a result")
        sz = path.getsize(filename)
        self.assertGreater(sz, 5000)
        self.assertGreater(6000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test015)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9786(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test016, legend="a result")
        sz = path.getsize(filename)
        self.assertGreater(sz, 5000)
        self.assertGreater(6000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test016)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9787(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test017, legend="a result")
        sz = path.getsize(filename)
        self.assertGreater(sz, 5000)
        self.assertGreater(6000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test017)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9788(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test018, legend="a result")
        sz = path.getsize(filename)
        self.assertGreater(sz, 5000)
        self.assertGreater(6000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test018Q)
        self.rm_testdir()
    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_9789(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        saveToXLSX(filename, test019, legend="a result")
        sz = path.getsize(filename)
        self.assertGreater(sz, 5000)
        self.assertGreater(6000, sz)
        data = readFromXLSX(filename)
        self.assertEqual(data, test019)
        self.rm_testdir()

if __name__ == "__main__":
    # unittest.main()
    from optparse import OptionParser
    cmdline = OptionParser("%s test...")
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="more verbose logging")
    cmdline.add_option("-^", "--quiet", action="count", default=0, help="less verbose logging")
    cmdline.add_option("--failfast", action="store_true", default=False,
                       help="Stop the test run on the first error or failure. [%default]")
    cmdline.add_option("--xmlresults", metavar="FILE", default=None,
                       help="capture results as a junit xml file [%default]")
    opt, args = cmdline.parse_args()
    logging.basicConfig(level=max(0, logging.WARNING - 10 * opt.verbose + 10 * opt.quiet))
    if not args:
        args = ["test_*"]
    suite = unittest.TestSuite()
    for arg in args:
        if len(arg) > 2 and arg[0].isalpha() and arg[1] == "_":
            arg = "test_" + arg[2:]
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if "*" not in arg: arg += "*"
                if arg.startswith("_"): arg = arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # running
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "wb")
    if xmlresults:
        import xmlrunner  # type: ignore[import]
        Runner = xmlrunner.XMLTestRunner
        result = Runner(xmlresults).run(suite)
        logg.info(" XML reports written to %s", opt.xmlresults)
    else:
        Runner = unittest.TextTestRunner
        result = Runner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
