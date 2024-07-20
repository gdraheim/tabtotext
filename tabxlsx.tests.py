#! /usr/bin/env python3

__copyright__ = "(C) 2017-2024 Guido Draheim, licensed under the Apache License 2.0"""
__version__ = "1.6.3283"

from typing import Optional, Union, Dict, List, Any, Sequence, Callable, Iterable, cast
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
from zipfile import ZipFile
from dataclasses import dataclass
from io import StringIO

import logging
logg = logging.getLogger("XLSX")

try:
    from tabtools import currency_default
    def X(line: str) -> str:
        return line.replace("$", chr(currency_default))
except ImportError as e:
    def X(line: str) -> str:
        return line

from tabxlsx import print_tabtotext, CellValue
from tabxlsx import load_workbook, save_workbook, write_workbook, read_workbook
from tabtotext import loadCSV, loadGFM

def get_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back  # type: ignore
    return frame.f_code.co_name  # type: ignore
def get_caller_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back.f_back  # type: ignore
    return frame.f_code.co_name  # type: ignore

JSONDict = Dict[str, CellValue]
JSONList = List[JSONDict]

def rev(data: List[JSONDict]) -> JSONList:
    return list(reversed(data))

class DataItem:
    """ Use this as the base class for dataclass types """
    def __getitem__(self, name: str) -> CellValue:
        return cast(CellValue, getattr(self, name))

DataList = List[DataItem]

@dataclass
class Item1(DataItem):
    b: CellValue

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
test019q: JSONList = [{"b": datetime.datetime(2021, 12, 31, 23, 34)}]
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

class TabXlsxTest(unittest.TestCase):
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
    def test_4103(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test003, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test003, text)
        cond = ['']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, [])
    def test_4104(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test004, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['', '', ]
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, [])
    def test_4105(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test005, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test005, text)
        cond = ['a', 'x', ]
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, test005)
    def test_4106(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test006, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test006, text)
        cond = ['a;b', 'x;y', ]
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, test006)
    def test_4107(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test007, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test007, text)
        cond = ['a;b', 'x;y', '~;v']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, test007Q)
    def test_4108(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test008, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test008, text)
        cond = ['a;b', 'x;~', '~;v']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, test008Q)
    def test_4109(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test009, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test009, text)
        cond = ['b', '~', 'v']
        self.assertEqual(cond, text.splitlines())
        data =loadCSV(text)
        self.assertEqual(data, test009Q)
    def test_4111(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test011, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test011, text)
        cond = ['b', '~']
        self.assertEqual(cond, text.splitlines())
        csvdata = loadCSV(text)
        data = csvdata
        self.assertEqual(data, test011)
    def test_4112(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test012, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test012, text)
        cond = ['b', '(no)']
        self.assertEqual(cond, text.splitlines())
        csvdata = loadCSV(text)
        data = csvdata
        self.assertEqual(data, test012)
    def test_4113(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test013, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test013, text)
        cond = ['b', '(yes)']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, test013)
    def test_4114(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test014, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test014, text)
        cond = ['b', '""']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, test014)
    def test_4115(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test015, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test015, text)
        cond = ['b', '5678']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, test015Q)
    def test_4116(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test016, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test016, text)
        cond = ['b', '123']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        if data[0]['b'] == "123":
            data[0]['b'] = 123
        self.assertEqual(data, test016)
    def test_4117(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test017, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test017, text)
        cond = ['b', '123.40']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        if data[0]['b'] == "123.40":
            data[0]['b'] = 123.4
        self.assertEqual(data, test017)
    def test_4118(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test018, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test018, text)
        cond = ['b', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, test018)
    def test_4119(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test019, defaultformat="csv")
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test019, text)
        cond = ['b', '2021-12-31.2334']
        self.assertEqual(cond, text.splitlines())
        data = loadCSV(text)
        self.assertEqual(data, test019q)


    def test_6103(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test003)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test003, text)
        cond = ['', '']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, [])
    def test_6104(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test004)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['', '', '']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, [])
    def test_6105(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test005)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test005, text)
        cond = ['| a', '| -----', '| x']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test005)
    def test_6106(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test006)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test006, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | y']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test006)
    def test_6107(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test007)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test007, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | y', '| ~     | v']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test007Q)
    def test_6108(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test008)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test008, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | ~', '| ~     | v']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test008Q)
    def test_6109(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test009)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test009, text)
        cond = ['| b', '| -----', '| ~', '| v']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test009Q)
    def test_6111(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test011)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test011, text)
        cond = ['| b', '| -----', '| ~']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test011)
    def test_6112(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test012)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test012, text)
        cond = ['| b', '| -----', '| (no)']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test012)
    def test_6113(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test013)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test013, text)
        cond = ['| b', '| -----', '| (yes)']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test013)
    def test_6114(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test014)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test014, text)
        cond = ['| b', '| -----', '|']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test014)
    def test_6115(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test015)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test015, text)
        cond = ['| b', '| -----', '| 5678']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test015Q)
    def test_6116(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test016)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test016, text)
        cond = ['| b', '| -----', '| 123']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test016)
    def test_6117(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test017)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test017, text)
        cond = ['| b', '| ------', '| 123.40']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test017)
    def test_6118(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test018)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test018, text)
        cond = ['| b', '| ----------', '| 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test018)
    def test_6119(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, test019)  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test019, text)
        cond = ['| b', '| ---------------', '| 2021-12-31.2334']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        self.assertEqual(data, test019q)
    def test_6144(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b', 'a'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['| b     | a', '| ----- | -----', '| 1     | y', '| 2     | x']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_6171(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b', 'a: {:}'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['| b     |     a', '| ----- | ----:', '| 1     |     y', '| 2     |     x']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_6172(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b', 'a: %s'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['| b     |     a', '| ----- | ----:', '| 1     |     y', '| 2     |     x']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': 'y', 'b': 1}, {'a': 'x', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_6173(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b:<.2n', 'a:"%s"'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['| b     | a', '| ----- | -----', '| 1     | "y"', '| 2     | "x"']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_6174(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2}, {'a': "y", 'b': 1}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b:{:.2f}', 'a:"{:}"'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['|     b | a', '| ----: | -----', '|  1.00 | "y"', '|  2.00 | "x"']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_6175(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b:{:<.2f}', 'a:"{:}"'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        # text = tabtotext.tabToGFM(itemlist, ['b', 'a'], formats)
        logg.debug("%s => %s", test004, text)
        cond = ['| b     | a', '| ----- | -----', '| 1.00  | "y"', '| 2.00  | "x"']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_6176(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b:{:.2f}', 'a:"{:}"'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['|     b | a', '| ----: | -----', '|  1.00 | "y"', '|  2.00 | "x"']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    @unittest.expectedFailure
    def test_6177(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b:{:$}', 'a:"{:}"'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['|     b | a', '| ----: | -----', X('| 1.00$ | "y"'), X('| 2.00$ | "x"')]
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': '"y"', 'b': 1}, {'a': '"x"', 'b': 2}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_6178(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 2.}, {'a': "y", 'b': 1.}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b:{:3f}', 'a:"{:5s}"'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['|        b | a', '| -------: | -------', '| 1.000000 | "y    "', '| 2.000000 | "x    "']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': '"y    "', 'b': 1.0}, {'a': '"x    "', 'b': 2.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)
    def test_6179(self) -> None:
        itemlist: JSONList = [{'a': "x", 'b': 22.}, {'a': "y", 'b': 1.}]
        out = StringIO()
        res = print_tabtotext(out, itemlist, ['b:{:>3f}', 'a:"{:>5s}"'])
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", test004, text)
        cond = ['|         b |       a', '| --------: | ------:', '|  1.000000 | "    y"', '| 22.000000 | "    x"']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        want = [{'a': '"    y"', 'b': 1.0}, {'a': '"    x"', 'b': 22.0}, ]  # order of rows swapped
        logg.info("%s => %s", want, data)
        self.assertEqual(want, data)

    date_for_6220: JSONList = [{"a": "x", "b": 0}, {"b": 2}]
    def test_6220(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, self.date_for_6220, ["b", "a"])  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", res, text)
        cond = ['| b     | a', '| ----- | -----', '| 0     | x', '| 2     | ~']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        del data[1]["a"]
        self.assertEqual(data, self.date_for_6220)
    date_for_6221: JSONList = [{"a": "x", "b": 3}, {"b": 2}]
    def test_6221(self) -> None:
        out = StringIO()
        res = print_tabtotext(out, self.date_for_6221, ["b", "a"])  # defaultformat="markdown"
        logg.info("print_tabtotext %s", res)
        text = out.getvalue()
        logg.debug("%s => %s", res, text)
        cond = ['| b     | a', '| ----- | -----', '| 2     | ~', '| 3     | x']
        self.assertEqual(cond, text.splitlines())
        data = loadGFM(text)
        del data[0]["a"]
        self.assertEqual(rev(data), self.date_for_6221)  # type: ignore[arg-type]

    def test_9771(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test011)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(5000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test011Q)
        self.rm_testdir()
    def test_9772(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test012)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(5000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test012)
        self.rm_testdir()
    def test_9773(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test013)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(5000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test013)
        self.rm_testdir()
    def test_9774(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test014)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(5000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test014)
        self.rm_testdir()
    def test_9775(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test015)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(5000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test015)
        self.rm_testdir()
    def test_9776(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test016)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(5000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test016)
        self.rm_testdir()
    def test_9777(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test017)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(5000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test017)
        self.rm_testdir()
    def test_9778(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test018)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(5000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test018Q)
        self.rm_testdir()
    def test_9779(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test019)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(5000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test019)
        self.rm_testdir()
    def test_9781(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test011)
        sz = path.getsize(filename)
        logg.info("generated [%s] %s", sz, filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(6000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test011Q)
        # self.rm_testdir()
    def test_9782(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test012)
        sz = path.getsize(filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(6000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test012)
        logg.info("data = %s", data)
        self.rm_testdir()
    def test_9783(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test013)
        sz = path.getsize(filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(6000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test013)
        self.rm_testdir()
    def test_9784(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test014)
        sz = path.getsize(filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(6000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test014)
        self.rm_testdir()
    def test_9785(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test015)
        sz = path.getsize(filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(6000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test015)
        self.rm_testdir()
    def test_9786(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test016)
        sz = path.getsize(filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(6000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test016)
        self.rm_testdir()
    def test_9787(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test017)
        sz = path.getsize(filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(6000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test017)
        self.rm_testdir()
    def test_9788(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test018)
        sz = path.getsize(filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(6000, sz)
        data = read_workbook(filename)
        self.assertEqual(data, test018Q)
        self.rm_testdir()
    def test_9789(self) -> None:
        tmp = self.testdir()
        filename = path.join(tmp, "output.xlsx")
        write_workbook(filename, test019)
        sz = path.getsize(filename)
        self.assertGreater(sz, 3000)
        self.assertGreater(6000, sz)
        #
        with ZipFile(filename) as zipped:
            with zipped.open("xl/worksheets/sheet1.xml") as zipdata:
                xmldata = zipdata.read()
                logg.info("xmldata = %s", xmldata)
        #
        data = read_workbook(filename)
        self.assertEqual(data, test019)
        # self.rm_testdir()

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
