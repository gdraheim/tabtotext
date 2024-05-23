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

import logging
logg = logging.getLogger("TESTS")

from tabtofmt import RowSortList, ColSortList, LegendList, tabToFMT

def get_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back  # type: ignore
    return frame.f_code.co_name  # type: ignore
def get_caller_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back.f_back  # type: ignore
    return frame.f_code.co_name  # type: ignore

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
    def test_5003(self) -> None:
        text = tabToFMT("csv", test003)
        logg.debug("%s => %s", test003, text)
        cond = ['']
        self.assertEqual(cond, text.splitlines())
    def test_5004(self) -> None:
        text = tabToFMT("csv", test004)
        logg.debug("%s => %s", test004, text)
        cond = ['', '', ]
        self.assertEqual(cond, text.splitlines())
    def test_5005(self) -> None:
        text = tabToFMT("csv", test005)
        logg.debug("%s => %s", test005, text)
        cond = ['a', 'x', ]
        self.assertEqual(cond, text.splitlines())
    def test_5006(self) -> None:
        text = tabToFMT("csv", test006)
        logg.debug("%s => %s", test006, text)
        cond = ['a;b', 'x;y', ]
        self.assertEqual(cond, text.splitlines())
    def test_5007(self) -> None:
        text = tabToFMT("csv", test007)
        logg.debug("%s => %s", test007, text)
        cond = ['a;b', 'x;y', '~;v']
        self.assertEqual(cond, text.splitlines())
    def test_5008(self) -> None:
        text = tabToFMT("csv", test008)
        logg.debug("%s => %s", test008, text)
        cond = ['a;b', 'x;~', '~;v']
        self.assertEqual(cond, text.splitlines())
    def test_5009(self) -> None:
        text = tabToFMT("csv", test009)
        logg.debug("%s => %s", test009, text)
        cond = ['b', '~', 'v']
        self.assertEqual(cond, text.splitlines())
    def test_5011(self) -> None:
        text = tabToFMT("csv", test011)
        logg.debug("%s => %s", test011, text)
        cond = ['b', '~']
        self.assertEqual(cond, text.splitlines())
    def test_5012(self) -> None:
        text = tabToFMT("csv", test012)
        logg.debug("%s => %s", test012, text)
        cond = ['b', '(no)']
        self.assertEqual(cond, text.splitlines())
    def test_5013(self) -> None:
        text = tabToFMT("csv", test013)
        logg.debug("%s => %s", test013, text)
        cond = ['b', '(yes)']
        self.assertEqual(cond, text.splitlines())
    def test_5014(self) -> None:
        text = tabToFMT("csv", test014)
        logg.debug("%s => %s", test014, text)
        cond = ['b', '""']
        self.assertEqual(cond, text.splitlines())
    def test_5015(self) -> None:
        text = tabToFMT("csv", test015)
        logg.debug("%s => %s", test015, text)
        cond = ['b', '5678']
        self.assertEqual(cond, text.splitlines())
    def test_5016(self) -> None:
        text = tabToFMT("csv", test016)
        logg.debug("%s => %s", test016, text)
        cond = ['b', '123']
        self.assertEqual(cond, text.splitlines())
    def test_5017(self) -> None:
        text = tabToFMT("csv", test017)
        logg.debug("%s => %s", test017, text)
        cond = ['b', '123.40']
        self.assertEqual(cond, text.splitlines())
    def test_5018(self) -> None:
        text = tabToFMT("csv", test018)
        logg.debug("%s => %s", test018, text)
        cond = ['b', '2021-12-31']
        self.assertEqual(cond, text.splitlines())
    def test_5019(self) -> None:
        text = tabToFMT("csv", test019)
        logg.debug("%s => %s", test019, text)
        cond = ['b', '2021-12-31.2334']
        self.assertEqual(cond, text.splitlines())
    def test_7003(self) -> None:
        text = tabToFMT("",test003)
        logg.debug("%s => %s", test003, text)
        cond = ['', '']
        self.assertEqual(cond, text.splitlines())
    def test_7004(self) -> None:
        text = tabToFMT("",test004)
        logg.debug("%s => %s", test004, text)
        cond = ['', '', '']
        self.assertEqual(cond, text.splitlines())
    def test_7005(self) -> None:
        text = tabToFMT("",test005)
        logg.debug("%s => %s", test005, text)
        cond = ['| a', '| -----', '| x']
        self.assertEqual(cond, text.splitlines())
    def test_7006(self) -> None:
        text = tabToFMT("",test006)
        logg.debug("%s => %s", test006, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | y']
        self.assertEqual(cond, text.splitlines())
    def test_7007(self) -> None:
        text = tabToFMT("",test007)
        logg.debug("%s => %s", test007, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | y', '| ~     | v']
        self.assertEqual(cond, text.splitlines())
    def test_7008(self) -> None:
        text = tabToFMT("",test008)
        logg.debug("%s => %s", test008, text)
        cond = ['| a     | b', '| ----- | -----', '| x     | ~', '| ~     | v']
        self.assertEqual(cond, text.splitlines())
    def test_7009(self) -> None:
        text = tabToFMT("",test009)
        logg.debug("%s => %s", test009, text)
        cond = ['| b', '| -----', '| ~', '| v']
        self.assertEqual(cond, text.splitlines())
    def test_7011(self) -> None:
        text = tabToFMT("",test011)
        logg.debug("%s => %s", test011, text)
        cond = ['| b', '| -----', '| ~']
        self.assertEqual(cond, text.splitlines())
    def test_7012(self) -> None:
        text = tabToFMT("",test012)
        logg.debug("%s => %s", test012, text)
        cond = ['| b', '| -----', '| (no)']
        self.assertEqual(cond, text.splitlines())
    def test_7013(self) -> None:
        text = tabToFMT("",test013)
        logg.debug("%s => %s", test013, text)
        cond = ['| b', '| -----', '| (yes)']
        self.assertEqual(cond, text.splitlines())
    def test_7014(self) -> None:
        text = tabToFMT("",test014)
        logg.debug("%s => %s", test014, text)
        cond = ['| b', '| -----', '|']
        self.assertEqual(cond, text.splitlines())
    def test_7015(self) -> None:
        text = tabToFMT("",test015)
        logg.debug("%s => %s", test015, text)
        cond = ['| b', '| -----', '| 5678']
        self.assertEqual(cond, text.splitlines())
    def test_7016(self) -> None:
        text = tabToFMT("",test016)
        logg.debug("%s => %s", test016, text)
        cond = ['| b', '| -----', '| 123']
        self.assertEqual(cond, text.splitlines())
        data = tabtotext.loadGFM(text)
        self.assertEqual(data, test016)
    def test_7017(self) -> None:
        text = tabToFMT("",test017)
        logg.debug("%s => %s", test017, text)
        cond = ['| b', '| ------', '| 123.40']
        self.assertEqual(cond, text.splitlines())
    def test_7018(self) -> None:
        text = tabToFMT("",test018)
        logg.debug("%s => %s", test018, text)
        cond = ['| b', '| ----------', '| 2021-12-31']
        self.assertEqual(cond, text.splitlines())
    def test_7019(self) -> None:
        text = tabToFMT("",test019)
        logg.debug("%s => %s", test019, text)
        cond = ['| b', '| ---------------', '| 2021-12-31.2334']
        self.assertEqual(cond, text.splitlines())


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
