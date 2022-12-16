#! /usr/bin/python3

from typing import Optional, Union, Dict, List, Any, Sequence
from tabtotext import JSONList
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
import logging
logg = logging.getLogger("TESTS")


try:
    from tabtoxlsx import saveToXLSX, readFromXLSX  # type: ignore
    skipXLSX = False
except Exception as e:
    logg.warning("skipping tabtoxlsx: %s", e)
    skipXLSX = True
    def saveToXLSX(filename: str, result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {},  #
                   legend: Union[Dict[str, str], Sequence[str]] = []) -> None:
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
class Item:
   a: str
   b: int
   def foo(self, a: str) -> None:
       pass

#######################################################################

test001: JSONList = []
test002: JSONList = [{}]
# test003: JSONList = [{}, {}]
test003: JSONList = [{"a": "x"}]
test004: JSONList = [{"a": "x", "b": "y"}]
test005: JSONList = [{"a": "x", "b": "y"}, {"a": "u", "b": "v"}]
test006: JSONList = [{"b": "y", "a": "x"}, {"b": "v", "a": "u"}]
test007: JSONList = [{"b": "y", "a": "x"}, {"b": "v"}]
test007Q: JSONList = [{"b": "y", "a": "x"}, {"b": "v", "a": None}]
test008: JSONList = [{"a": "x"}, {"b": "v"}]
test008Q: JSONList = [{"b": None, "a": "x"}, {"b": "v", "a": None}]
test009: JSONList = [{}, {"b": "v"}]
test009Q: JSONList = [{"b": None}, {"b": "v"}]
test011: JSONList = [{"a": None}]
test011Q: JSONList = []
test012: JSONList = [{"a": False}]
test013: JSONList = [{"a": True}]
test014: JSONList = [{"a": ""}]
test015: JSONList = [{"a": "5678"}]
test015Q: JSONList = [{"a": 5678}]
test016: JSONList = [{"a": 123}]
test017: JSONList = [{"a": 123.4}]
test018: JSONList = [{"a": datetime.date(2021, 12, 31)}]
test018Q: JSONList = [{"a": datetime.datetime(2021, 12, 31, 0, 0)}]
test019Q: JSONList = [{"a": datetime.date(2021, 12, 31)}]
test019: JSONList = [{"a": datetime.datetime(2021, 12, 31, 23, 34, 45)}]

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
    def test_101(self) -> None:
        text = tabtotext.tabToGFM(test001)
        logg.debug("%s => %s", test001, text)
        cond = ['', '']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, [])
    def test_102(self) -> None:
        text = tabtotext.tabToGFM(test002)
        logg.debug("%s => %s", test002, text)
        cond = ['', '', '']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, [])
    def test_103(self) -> None:
        text = tabtotext.tabToGFM(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['| a    ', '| -----', '| x    ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test003)
    def test_104(self) -> None:
        text = tabtotext.tabToGFM(test004)
        logg.debug("%s => %s", test004, text)
        cond = ['| a     | b    ', '| ----- | -----', '| x     | y    ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test004)
    def test_105(self) -> None:
        text = tabtotext.tabToGFM(test005)
        logg.debug("%s => %s", test005, text)
        cond = ['| a     | b    ', '| ----- | -----', '| x     | y    ', '| u     | v    ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test005)
    def test_106(self) -> None:
        text = tabtotext.tabToGFM(test006)
        logg.debug("%s => %s", test006, text)
        cond = ['| a     | b    ', '| ----- | -----', '| x     | y    ', '| u     | v    ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test006)
    def test_107(self) -> None:
        text = tabtotext.tabToGFM(test007)
        logg.debug("%s => %s", test007, text)
        cond = ['| a     | b    ', '| ----- | -----', '| x     | y    ', '| ~     | v    ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test007Q)
    def test_108(self) -> None:
        text = tabtotext.tabToGFM(test008)
        logg.debug("%s => %s", test008, text)
        cond = ['| a     | b    ', '| ----- | -----', '| x     | ~    ', '| ~     | v    ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test008Q)
    def test_109(self) -> None:
        text = tabtotext.tabToGFM(test009)
        logg.debug("%s => %s", test009, text)
        cond = ['| b    ', '| -----', '| ~    ', '| v    ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test009Q)
    def test_111(self) -> None:
        text = tabtotext.tabToGFM(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['| a    ', '| -----', '| ~    ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test011)
    def test_112(self) -> None:
        text = tabtotext.tabToGFM(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['| a    ', '| -----', '| (no) ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test012)
    def test_113(self) -> None:
        text = tabtotext.tabToGFM(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['| a    ', '| -----', '| (yes)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test013)
    def test_114(self) -> None:
        text = tabtotext.tabToGFM(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['| a    ', '| -----', '|      ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test014)
    def test_115(self) -> None:
        text = tabtotext.tabToGFM(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['| a    ', '| -----', '| 5678 ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test015Q)
    def test_116(self) -> None:
        text = tabtotext.tabToGFM(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['| a    ', '| -----', '| 123  ']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test016)
    def test_117(self) -> None:
        text = tabtotext.tabToGFM(test017)
        logg.debug("%s => %s", test018, text)
        cond = ['| a     ', '| ------', '| 123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test017)
    def test_118(self) -> None:
        text = tabtotext.tabToGFM(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['| a         ', '| ----------', '| 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test018)
    def test_119(self) -> None:
        text = tabtotext.tabToGFM(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['| a         ', '| ----------', '| 2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test019Q)
    def test_121(self) -> None:
        text = tabtotext.tabToGFM(test011, legend="a result")
        logg.debug("%s => %s", test011, text)
        cond = ['| a    ', '| -----', '| ~    ', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test011)
    def test_122(self) -> None:
        text = tabtotext.tabToGFM(test012, legend="a result")
        logg.debug("%s => %s", test012, text)
        cond = ['| a    ', '| -----', '| (no) ', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test012)
    def test_123(self) -> None:
        text = tabtotext.tabToGFM(test013, legend="a result")
        logg.debug("%s => %s", test013, text)
        cond = ['| a    ', '| -----', '| (yes)', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test013)
    def test_124(self) -> None:
        text = tabtotext.tabToGFM(test014, legend="a result")
        logg.debug("%s => %s", test014, text)
        cond = ['| a    ', '| -----', '|      ', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test014)
    def test_125(self) -> None:
        text = tabtotext.tabToGFM(test015, legend="a result")
        logg.debug("%s => %s", test015, text)
        cond = ['| a    ', '| -----', '| 5678 ', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test015Q)
    def test_126(self) -> None:
        text = tabtotext.tabToGFM(test016, legend="a result")
        logg.debug("%s => %s", test016, text)
        cond = ['| a    ', '| -----', '| 123  ', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test016)
    def test_127(self) -> None:
        text = tabtotext.tabToGFM(test017, legend="a result")
        logg.debug("%s => %s", test018, text)
        cond = ['| a     ', '| ------', '| 123.40', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test017)
    def test_128(self) -> None:
        text = tabtotext.tabToGFM(test018, legend="a result")
        logg.debug("%s => %s", test018, text)
        cond = ['| a         ', '| ----------', '| 2021-12-31', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test018)
    def test_129(self) -> None:
        text = tabtotext.tabToGFM(test019, legend="a result")
        logg.debug("%s => %s", test019, text)
        cond = ['| a         ', '| ----------', '| 2021-12-31', '', '- a result']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test019Q)
    def test_131(self) -> None:
        text = tabtotext.tabToGFM(test011, legend=["a result", "was found"])
        logg.debug("%s => %s", test011, text)
        cond = ['| a    ', '| -----', '| ~    ', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test011)
    def test_132(self) -> None:
        text = tabtotext.tabToGFM(test012, legend=["a result", "was found"])
        logg.debug("%s => %s", test012, text)
        cond = ['| a    ', '| -----', '| (no) ', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test012)
    def test_133(self) -> None:
        text = tabtotext.tabToGFM(test013, legend=["a result", "was found"])
        logg.debug("%s => %s", test013, text)
        cond = ['| a    ', '| -----', '| (yes)', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test013)
    def test_134(self) -> None:
        text = tabtotext.tabToGFM(test014, legend=["a result", "was found"])
        logg.debug("%s => %s", test014, text)
        cond = ['| a    ', '| -----', '|      ', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test014)
    def test_135(self) -> None:
        text = tabtotext.tabToGFM(test015, legend=["a result", "was found"])
        logg.debug("%s => %s", test015, text)
        cond = ['| a    ', '| -----', '| 5678 ', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test015Q)
    def test_136(self) -> None:
        text = tabtotext.tabToGFM(test016, legend=["a result", "was found"])
        logg.debug("%s => %s", test016, text)
        cond = ['| a    ', '| -----', '| 123  ', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test016)
    def test_137(self) -> None:
        text = tabtotext.tabToGFM(test017, legend=["a result", "was found"])
        logg.debug("%s => %s", test017, text)
        cond = ['| a     ', '| ------', '| 123.40', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test017)
    def test_138(self) -> None:
        text = tabtotext.tabToGFM(test018, legend=["a result", "was found"])
        logg.debug("%s => %s", test018, text)
        cond = ['| a         ', '| ----------', '| 2021-12-31', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test018)
    def test_139(self) -> None:
        text = tabtotext.tabToGFM(test019, legend=["a result", "was found"])
        logg.debug("%s => %s", test019, text)
        cond = ['| a         ', '| ----------', '| 2021-12-31', '', '- a result', '- was found']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test019Q)

    def test_201(self) -> None:
        text = tabtotext.tabToHTML(test001)
        logg.debug("%s => %s", test001, text)
        cond = ['<table>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_202(self) -> None:
        text = tabtotext.tabToHTML(test002)
        logg.debug("%s => %s", test002, text)
        cond = ['<table>', '<tr></tr>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_203(self) -> None:
        text = tabtotext.tabToHTML(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>x</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_204(self) -> None:
        text = tabtotext.tabToHTML(test004)
        logg.debug("%s => %s", test004, text)
        cond = ['<table>',  # -
                '<tr><th>a</th><th>b</th></tr>',  # -
                '<tr><td>x</td><td>y</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_205(self) -> None:
        text = tabtotext.tabToHTML(test005)
        logg.debug("%s => %s", test005, text)
        cond = ['<table>',  # -
                '<tr><th>a</th><th>b</th></tr>',  # -
                '<tr><td>x</td><td>y</td></tr>',  # -
                '<tr><td>u</td><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_206(self) -> None:
        text = tabtotext.tabToHTML(test006)
        logg.debug("%s => %s", test006, text)
        cond = ['<table>',  # -
                '<tr><th>a</th><th>b</th></tr>',  # -
                '<tr><td>x</td><td>y</td></tr>',  # -
                '<tr><td>u</td><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_207(self) -> None:
        text = tabtotext.tabToHTML(test007)
        logg.debug("%s => %s", test007, text)
        cond = ['<table>',  # -
                '<tr><th>a</th><th>b</th></tr>',  # -
                '<tr><td>x</td><td>y</td></tr>',  # -
                '<tr><td></td><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_208(self) -> None:
        text = tabtotext.tabToHTML(test008)
        logg.debug("%s => %s", test008, text)
        cond = ['<table>',  # -
                '<tr><th>a</th><th>b</th></tr>',  # -
                '<tr><td>x</td><td></td></tr>',  # -
                '<tr><td></td><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_209(self) -> None:
        text = tabtotext.tabToHTML(test009)
        logg.debug("%s => %s", test009, text)
        cond = ['<table>',  # -
                '<tr><th>b</th></tr>',  # -
                '<tr><td></td></tr>',  # -
                '<tr><td>v</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_211(self) -> None:
        text = tabtotext.tabToHTML(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>~</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_212(self) -> None:
        text = tabtotext.tabToHTML(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>(no)</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_213(self) -> None:
        text = tabtotext.tabToHTML(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>(yes)</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_214(self) -> None:
        text = tabtotext.tabToHTML(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td></td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_215(self) -> None:
        text = tabtotext.tabToHTML(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>5678</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_216(self) -> None:
        text = tabtotext.tabToHTML(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>123</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_217(self) -> None:
        text = tabtotext.tabToHTML(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>123.40</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_218(self) -> None:
        text = tabtotext.tabToHTML(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>2021-12-31</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_219(self) -> None:
        text = tabtotext.tabToHTML(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>2021-12-31</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_221(self) -> None:
        text = tabtotext.tabToHTML(test011, legend="a result")
        logg.debug("%s => %s", test011, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>~</td></tr>', '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_222(self) -> None:
        text = tabtotext.tabToHTML(test012, legend="a result")
        logg.debug("%s => %s", test012, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>(no)</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_223(self) -> None:
        text = tabtotext.tabToHTML(test013, legend="a result")
        logg.debug("%s => %s", test013, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>(yes)</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_224(self) -> None:
        text = tabtotext.tabToHTML(test014, legend="a result")
        logg.debug("%s => %s", test014, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td></td></tr>', '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_225(self) -> None:
        text = tabtotext.tabToHTML(test015, legend="a result")
        logg.debug("%s => %s", test015, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>5678</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_226(self) -> None:
        text = tabtotext.tabToHTML(test016, legend="a result")
        logg.debug("%s => %s", test016, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>123</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_227(self) -> None:
        text = tabtotext.tabToHTML(test017, legend="a result")
        logg.debug("%s => %s", test017, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>123.40</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_228(self) -> None:
        text = tabtotext.tabToHTML(test018, legend="a result")
        logg.debug("%s => %s", test018, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>2021-12-31</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_229(self) -> None:
        text = tabtotext.tabToHTML(test019, legend="a result")
        logg.debug("%s => %s", test019, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>2021-12-31</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_231(self) -> None:
        text = tabtotext.tabToHTML(test011, legend=["a result", "was found"])
        logg.debug("%s => %s", test011, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>~</td></tr>', '</table>',
                '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_232(self) -> None:
        text = tabtotext.tabToHTML(test012, legend=["a result", "was found"])
        logg.debug("%s => %s", test012, text)
        cond = ['<table>', '<tr><th>a</th></tr>',
                '<tr><td>(no)</td></tr>', '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_233(self) -> None:
        text = tabtotext.tabToHTML(test013, legend=["a result", "was found"])
        logg.debug("%s => %s", test013, text)
        cond = ['<table>', '<tr><th>a</th></tr>',
                '<tr><td>(yes)</td></tr>', '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_234(self) -> None:
        text = tabtotext.tabToHTML(test014, legend=["a result", "was found"])
        logg.debug("%s => %s", test014, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td></td></tr>', '</table>',
                '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_235(self) -> None:
        text = tabtotext.tabToHTML(test015, legend=["a result", "was found"])
        logg.debug("%s => %s", test015, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>5678</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_236(self) -> None:
        text = tabtotext.tabToHTML(test016, legend=["a result", "was found"])
        logg.debug("%s => %s", test016, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>123</td></tr>', '</table>',
                '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_237(self) -> None:
        text = tabtotext.tabToHTML(test017, legend=["a result", "was found"])
        logg.debug("%s => %s", test017, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>123.40</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_238(self) -> None:
        text = tabtotext.tabToHTML(test018, legend=["a result", "was found"])
        logg.debug("%s => %s", test018, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>2021-12-31</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())
    def test_239(self) -> None:
        text = tabtotext.tabToHTML(test019, legend=["a result", "was found"])
        logg.debug("%s => %s", test019, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>2021-12-31</td></tr>',
                '</table>', '', '<ul>', '<li>a result</li>', '<li>was found</li>', '</ul>']
        self.assertEqual(cond, text.splitlines())

    def test_301(self) -> None:
        text = tabtotext.tabToCSV(test001)
        logg.debug("%s => %s", test001, text)
        cond = ['']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, [])
    def test_302(self) -> None:
        text = tabtotext.tabToCSV(test002)
        logg.debug("%s => %s", test002, text)
        cond = ['', '', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, [])
    def test_303(self) -> None:
        text = tabtotext.tabToCSV(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['a', 'x', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test003)
    def test_304(self) -> None:
        text = tabtotext.tabToCSV(test004)
        logg.debug("%s => %s", test004, text)
        cond = ['a;b', 'x;y', ]
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test004)
    def test_305(self) -> None:
        text = tabtotext.tabToCSV(test005)
        logg.debug("%s => %s", test005, text)
        cond = ['a;b', 'x;y', 'u;v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test005)
    def test_306(self) -> None:
        text = tabtotext.tabToCSV(test006)
        logg.debug("%s => %s", test006, text)
        cond = ['a;b', 'x;y', 'u;v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test006)
    def test_307(self) -> None:
        text = tabtotext.tabToCSV(test007)
        logg.debug("%s => %s", test007, text)
        cond = ['a;b', 'x;y', '~;v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test007Q)
    def test_308(self) -> None:
        text = tabtotext.tabToCSV(test008)
        logg.debug("%s => %s", test008, text)
        cond = ['a;b', 'x;~', '~;v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test008Q)
    def test_309(self) -> None:
        text = tabtotext.tabToCSV(test009)
        logg.debug("%s => %s", test009, text)
        cond = ['b', '~', 'v']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test009Q)
    def test_311(self) -> None:
        text = tabtotext.tabToCSV(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['a', '~']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test011)
    def test_312(self) -> None:
        text = tabtotext.tabToCSV(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['a', '(no)']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test012)
    def test_313(self) -> None:
        text = tabtotext.tabToCSV(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['a', '(yes)']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test013)
    def test_314(self) -> None:
        text = tabtotext.tabToCSV(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['a', '""']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test014)
    def test_315(self) -> None:
        text = tabtotext.tabToCSV(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['a', '5678']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test015Q)
    def test_316(self) -> None:
        text = tabtotext.tabToCSV(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['a', '123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        if data[0]['a'] == "123":
            data[0]['a'] = 123
        self.assertEqual(data, test016)
    def test_317(self) -> None:
        text = tabtotext.tabToCSV(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['a', '123.40']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        if data[0]['a'] == "123.40":
            data[0]['a'] = 123.4
        self.assertEqual(data, test017)
    def test_318(self) -> None:
        text = tabtotext.tabToCSV(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['a', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test018)
    def test_319(self) -> None:
        text = tabtotext.tabToCSV(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['a', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadCSV(text)
        self.assertEqual(data, test018)  # test019
    def test_321(self) -> None:
        """ legend is ignored for CSV """
        text = tabtotext.tabToCSV(test011, legend="a result")
        logg.debug("%s => %s", test011, text)
        cond = ['a', '~']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test011)
    def test_331(self) -> None:
        """ legend is ignored for CSV """
        text = tabtotext.tabToCSV(test011, legend=["a result", "was found"])
        logg.debug("%s => %s", test011, text)
        cond = ['a', '~']
        self.assertEqual(cond, text.splitlines())
        csvdata = tabtotext.loadCSV(text)
        data = csvdata
        self.assertEqual(data, test011)

    def test_401(self) -> None:
        text = tabtotext.tabToJSON(test001)
        logg.debug("%s => %s", test001, text)
        cond = ['[', '', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test001)
    def test_402(self) -> None:
        text = tabtotext.tabToJSON(test002)
        logg.debug("%s => %s", test002, text)
        cond = ['[', ' {}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test002)
    def test_403(self) -> None:
        text = tabtotext.tabToJSON(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['[', ' {"a": "x"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test003)
    def test_404(self) -> None:
        text = tabtotext.tabToJSON(test004)
        logg.debug("%s => %s", test004, text)
        cond = ['[', ' {"a": "x", "b": "y"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test004)
    def test_405(self) -> None:
        text = tabtotext.tabToJSON(test005)
        logg.debug("%s => %s", test005, text)
        cond = ['[', ' {"a": "x", "b": "y"},', ' {"a": "u", "b": "v"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test005)
    def test_406(self) -> None:
        text = tabtotext.tabToJSON(test006)
        logg.debug("%s => %s", test006, text)
        cond = ['[', ' {"a": "x", "b": "y"},', ' {"a": "u", "b": "v"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test006)
    def test_407(self) -> None:
        text = tabtotext.tabToJSON(test007)
        logg.debug("%s => %s", test007, text)
        cond = ['[', ' {"a": "x", "b": "y"},', ' {"b": "v"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test007)
    def test_408(self) -> None:
        text = tabtotext.tabToJSON(test008)
        logg.debug("%s => %s", test008, text)
        cond = ['[', ' {"a": "x"},', ' {"b": "v"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test008)
    def test_409(self) -> None:
        text = tabtotext.tabToJSON(test009)
        logg.debug("%s => %s", test009, text)
        cond = ['[', ' {},', ' {"b": "v"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test009)
    def test_411(self) -> None:
        text = tabtotext.tabToJSON(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['[', ' {"a": null}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test011)
    def test_412(self) -> None:
        text = tabtotext.tabToJSON(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['[', ' {"a": false}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test012)
    def test_413(self) -> None:
        text = tabtotext.tabToJSON(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['[', ' {"a": true}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test013)
    def test_414(self) -> None:
        text = tabtotext.tabToJSON(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['[', ' {"a": ""}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test014)
    def test_415(self) -> None:
        text = tabtotext.tabToJSON(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['[', ' {"a": "5678"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test015)
    def test_416(self) -> None:
        text = tabtotext.tabToJSON(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['[', ' {"a": 123}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test016)
    def test_417(self) -> None:
        text = tabtotext.tabToJSON(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['[', ' {"a": 123.40}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test017)
    def test_418(self) -> None:
        text = tabtotext.tabToJSON(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['[', ' {"a": "2021-12-31"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test018)
    def test_419(self) -> None:
        text = tabtotext.tabToJSON(test019)
        logg.debug("%s => %s", test019, text)
        cond = ['[', ' {"a": "2021-12-31"}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test018)  # test019
    def test_421(self) -> None:
        """ legend is ignored for JSON output """
        text = tabtotext.tabToJSON(test011, legend="a result")
        logg.debug("%s => %s", test011, text)
        cond = ['[', ' {"a": null}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test011)
    def test_431(self) -> None:
        """ legend is ignored for JSON output """
        text = tabtotext.tabToJSON(test011, legend=["a result", "was found"])
        logg.debug("%s => %s", test011, text)
        cond = ['[', ' {"a": null}', ']']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadJSON(text)
        self.assertEqual(data, test011)

    def test_490(self) -> None:
        data = json.loads("[]")
        self.assertEqual(data, [])
    def test_491(self) -> None:
        data = json.loads("[{}]")
        self.assertEqual(data, [{}])
    def test_492(self) -> None:
        try:
            data = json.loads("[{},]")
            self.assertEqual(data, [{}])
        except json.decoder.JSONDecodeError as e:
            self.assertIn("Expecting value", str(e))




    def test_500(self) -> None:
        item = Item("x", 2)
        text = tabtotext.tabToGFMx(item)
        logg.debug("%s => %s", test004, text)
        cond = ['| a     | b    ', '| ----- | -----', '| x     | 2    ']
        self.assertEqual(cond, text.splitlines())
    def test_501(self) -> None:
        item = Item("x", 2)
        text = tabtotext.tabToGFMx([item])
        logg.debug("%s => %s", test004, text)
        cond = ['| a     | b    ', '| ----- | -----', '| x     | 2    ']
        self.assertEqual(cond, text.splitlines())

    @unittest.skipIf(skipXLSX, "no openpyxl")
    def test_771(self) -> None:
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
    def test_772(self) -> None:
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
    def test_773(self) -> None:
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
    def test_774(self) -> None:
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
    def test_775(self) -> None:
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
    def test_776(self) -> None:
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
    def test_777(self) -> None:
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
    def test_778(self) -> None:
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
    def test_779(self) -> None:
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
    def test_781(self) -> None:
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
    def test_782(self) -> None:
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
    def test_783(self) -> None:
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
    def test_784(self) -> None:
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
    def test_785(self) -> None:
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
    def test_786(self) -> None:
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
    def test_787(self) -> None:
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
    def test_788(self) -> None:
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
    def test_789(self) -> None:
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
    cmdline.add_option("-v", "--verbose", action="count", default=0)
    opt, args = cmdline.parse_args()
    logging.basicConfig(level=max(0, logging.WARNING - 10 * opt.verbose))
    if not args:
        args = ["x_*"]
    suite = unittest.TestSuite()
    for arg in args:
        if arg.startswith("x_"):
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
    Runner = unittest.TextTestRunner
    result = Runner(verbosity=opt.verbose).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
