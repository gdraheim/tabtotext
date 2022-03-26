import unittest
import datetime
import logging
logg = logging.getLogger("TESTS")

import tabtotext

test001 = []
test002 = [{}]
test003 = [{},{}]
test011 = [{"a":None}]
test012 = [{"a":False}]
test013 = [{"a":True}]
test014 = [{"a":""}]
test015 = [{"a":"5678"}]
test016 = [{"a":datetime.date(2021,12,31)}]
test017 = [{"a":123}]
test018 = [{"a":123.4}]

class TabToTextTest(unittest.TestCase):
    def test_101(self):
        text = tabtotext.tabToGFM(test001)
        logg.debug("%s => %s", test001, text)
        cond = ['','']
        self.assertEqual(cond, text.splitlines())
    def test_102(self):
        text = tabtotext.tabToGFM(test002)
        logg.debug("%s => %s", test002, text)
        cond = ['','','']
        self.assertEqual(cond, text.splitlines())
    def test_103(self):
        text = tabtotext.tabToGFM(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['','','','']
        self.assertEqual(cond, text.splitlines())
    def test_111(self):
        text = tabtotext.tabToGFM(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['| a    ', '| -----', '| -    ']
        self.assertEqual(cond, text.splitlines())
    def test_112(self):
        text = tabtotext.tabToGFM(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['| a    ', '| -----', '| (no) ']
        self.assertEqual(cond, text.splitlines())
    def test_113(self):
        text = tabtotext.tabToGFM(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['| a    ', '| -----', '| (yes)']
        self.assertEqual(cond, text.splitlines())
    def test_114(self):
        text = tabtotext.tabToGFM(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['| a    ', '| -----', '|      ']
        self.assertEqual(cond, text.splitlines())
    def test_115(self):
        text = tabtotext.tabToGFM(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['| a    ', '| -----', '| 5678 ']
        self.assertEqual(cond, text.splitlines())
    def test_116(self):
        text = tabtotext.tabToGFM(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['| a         ', '| ----------', '| 2021-12-31']
        self.assertEqual(cond, text.splitlines())
    def test_117(self):
        text = tabtotext.tabToGFM(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['| a    ', '| -----', '| 123  ']
        self.assertEqual(cond, text.splitlines())
    def test_118(self):
        text = tabtotext.tabToGFM(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['| a    ', '| -----', '| 123.4']
        self.assertEqual(cond, text.splitlines())
    def test_201(self):
        text = tabtotext.tabToHTML(test001)
        logg.debug("%s => %s", test001, text)
        cond = ['<table>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_202(self):
        text = tabtotext.tabToHTML(test002)
        logg.debug("%s => %s", test002, text)
        cond = ['<table>', '<tr></tr>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_203(self):
        text = tabtotext.tabToHTML(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['<table>', '<tr></tr>', '<tr></tr>', '<tr></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_211(self):
        text = tabtotext.tabToHTML(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>-</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_212(self):
        text = tabtotext.tabToHTML(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>(no)</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_213(self):
        text = tabtotext.tabToHTML(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>(yes)</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_214(self):
        text = tabtotext.tabToHTML(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td></td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_215(self):
        text = tabtotext.tabToHTML(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>5678</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_216(self):
        text = tabtotext.tabToHTML(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>2021-12-31</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_217(self):
        text = tabtotext.tabToHTML(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>123</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_218(self):
        text = tabtotext.tabToHTML(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['<table>', '<tr><th>a</th></tr>', '<tr><td>123.4</td></tr>', '</table>']
        self.assertEqual(cond, text.splitlines())
    def test_301(self):
        text = tabtotext.tabToJSON(test001)
        logg.debug("%s => %s", test001, text)
        cond = ['----','[', '', ']']
        self.assertEqual(cond, text.splitlines())
    def test_302(self):
        text = tabtotext.tabToJSON(test002)
        logg.debug("%s => %s", test002, text)
        cond = ['----','[',' {},', ']']
        self.assertEqual(cond, text.splitlines())
    def test_303(self):
        text = tabtotext.tabToJSON(test003)
        logg.debug("%s => %s", test003, text)
        cond = ['----','[',' {},', ' {},', ']']
        self.assertEqual(cond, text.splitlines())
    def test_311(self):
        text = tabtotext.tabToJSON(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['----','[', " {'a': null},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_311(self):
        text = tabtotext.tabToJSON(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['----','[', " {'a': null},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_311(self):
        text = tabtotext.tabToJSON(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['----','[', " {'a': null},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_311(self):
        text = tabtotext.tabToJSON(test011)
        logg.debug("%s => %s", test011, text)
        cond = ['----','[', " {'a': null},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_312(self):
        text = tabtotext.tabToJSON(test012)
        logg.debug("%s => %s", test012, text)
        cond = ['----','[', " {'a': false},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_313(self):
        text = tabtotext.tabToJSON(test013)
        logg.debug("%s => %s", test013, text)
        cond = ['----','[', " {'a': true},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_314(self):
        text = tabtotext.tabToJSON(test014)
        logg.debug("%s => %s", test014, text)
        cond = ['----','[', " {'a': \"\"},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_315(self):
        text = tabtotext.tabToJSON(test015)
        logg.debug("%s => %s", test015, text)
        cond = ['----','[', " {'a': \"5678\"},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_316(self):
        text = tabtotext.tabToJSON(test016)
        logg.debug("%s => %s", test016, text)
        cond = ['----','[', " {'a': '2021~12~31'},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_317(self):
        text = tabtotext.tabToJSON(test017)
        logg.debug("%s => %s", test017, text)
        cond = ['----','[', " {'a': 123},", ']']
        self.assertEqual(cond, text.splitlines())
    def test_318(self):
        text = tabtotext.tabToJSON(test018)
        logg.debug("%s => %s", test018, text)
        cond = ['----','[', " {'a': 123.4},", ']']
        self.assertEqual(cond, text.splitlines())

if __name__ == "__main__":
    unittest.main()