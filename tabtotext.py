#! /usr/bin/python3
"""
This script reimplements the queries/*.sql that have been used in Userlist.sh
but instead of using the Postgres API it uses the Crowd API.

// Please be aware the --appuser/--password represent crowd-application credentials (not a build user)
"""

from typing import Optional, Union, Dict, List, Any, Sequence
from html import escape
from datetime import date as Date
from datetime import datetime as Time
import os
import re
import logging
import json
from io import StringIO

logg = logging.getLogger("TABTOTEXT")

DATEFMT = "%Y-%m-%d"
NORIGHT = False
MINWIDTH = 5

JSONItem = Union[str, int, float, bool, Date, Time, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONItem]
JSONList = List[JSONDict]
JSONDictList = Dict[str, JSONList]
JSONDictDict = Dict[str, JSONDict]

_None_String = "~"
_False_String = "(no)"
_True_String = "(yes)"

def setNoRight(value: bool) -> None:
    global NORIGHT
    NORIGHT = value

def strDateTime(value: Any, datedelim: str = '-') -> str:
    if value is None:
        return _None_String
    if isinstance(value, (Date, Time)):
        return value.strftime(DATEFMT.replace('-', datedelim))
    return str(value)
def strNone(value: Any, datedelim: str = '-') -> str:
    if value is None:
        return _None_String
    if value is False:
        return _False_String
    if value is True:
        return _True_String
    return strDateTime(value, datedelim)

class ParseJSONItem:
    def __init__(self, datedelim = '-') -> None:
        self.is_date = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)$".replace('-', datedelim))
        self.is_time = re.compile(
            r"(\d\d\d\d)-(\d\d)-(\d\d)[T](\d\d):(\d\d):(\d:\d)(?:[.]\d*)(?:[A-Z][A-Z][A-Z][A-Z]?)$".replace('-', datedelim))
        self.is_int = re.compile(r"([+-]?\d+)$")
        self.is_float = re.compile(r"([+-]?\d+)(?:[.]\d*)?(?:e[+-]?\d+)?$")
        self.datedelim = datedelim
        self.None_String = _None_String
        self.False_String = _False_String
        self.True_String = _True_String
    def toJSONItem(self, val: str) -> JSONItem:
        """ generic conversion of string to data types - it may do too much """
        if val == self.None_String:
            return None
        if val == self.False_String:
            return False
        if val == self.True_String:
            return True
        if self.is_int.match(val):
            return int(val)
        if self.is_float.match(val):
            return float(val)
        return self.toDate(val)
    def toDate(self, val: str) -> JSONItem:
        """ the json.loads parser detects most data types except Date/Time """
        as_time = self.is_time.match(val)
        if as_time:
            return Time(int(as_time.group(1)), int(as_time.group(2)), int(as_time.group(3)),
                        int(as_time.group(4)), int(as_time.group(5)), int(as_time.group(6)))
        as_date = self.is_date.match(val)
        if as_date:
            return Date(int(as_date.group(1)), int(as_date.group(2)), int(as_date.group(3)))
        return val # str

def tabToGFMx(result: Union[JSONList, JSONDict], sorts: Sequence[str] = [], formats: Dict[str, str] = {}, legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        result = [result]
    return tabToGFM(result, sorts, formats, legend)
def tabToGFM(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}, legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    def sortkey(header: str) -> str:
        if header in sorts:
            return "%07i" % sorts.index(header)
        return header
    def sortrow(item: JSONDict) -> str:
        sortvalue = ""
        for sort in sorts:
            if sort in item:
                value = item[sort]
                if isinstance(value, int):
                    sortvalue += "\n%020i" % value
                else:
                    sortvalue += "\n" + strDateTime(value)
            else:
                sortvalue += "\n-"
        return sortvalue
    def format(col: str, val: JSONItem) -> str:
        if col in formats:
            if isinstance(val, float):
                m = re.search(r"%\d(?:[.]\d)f", formats[col])
                if m:
                    try:
                        return formats[col] % val
                    except:
                        pass
            if "%s" in formats[col]:
                try:
                    return formats[col] % strNone(val)
                except:
                    pass
            logg.info("unknown format '%s' for col '%s'", formats[col], col)
        return strNone(val)
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            paren = 0
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    def rightF(col: str, formatter: str) -> str:
        if col in formats and formats[col].startswith(" ") and not NORIGHT:
            return formatter.replace("%-", "%")
        return formatter
    def rightS(col: str, formatter: str) -> str:
        if col in formats and formats[col].startswith(" ") and not NORIGHT:
            return formatter[:-1] + ":"
        return formatter
    templates = [rightF(name, "| %%-%is" % cols[name]) for name in sorted(cols.keys(), key=sortkey)]
    template = " ".join(templates)
    logg.debug("template [%s] = %s", len(templates), template)
    logg.debug("colskeys [%s] = %s", len(cols.keys()), sorted(cols.keys(), key=sortkey))
    lines = [template % tuple(sorted(cols.keys(), key=sortkey))]
    seperators = [rightS(name, "-" * cols[name]) for name in sorted(cols.keys(), key=sortkey)]
    lines.append(template % tuple(seperators))
    for item in sorted(result, key=sortrow):
        values: JSONDict = dict([(name, "") for name in cols.keys()])
        # logg.debug("values = %s", values)
        for name, value in item.items():
            values[name] = value
        line = template % tuple([format(name, values[name]) for name in sorted(cols.keys(), key=sortkey)])
        lines.append(line)
    return "\n".join(lines) + "\n" + legendToGFM(legend, sorts)

def legendToGFM(legend: Union[Dict[str, str], Sequence[str]], sorts: Sequence[str] = []) -> str:
    def sortkey(header: str) -> str:
        if header in sorts:
            return "%07i" % sorts.index(header)
        return header
    if isinstance(legend, dict):
        lines = []
        for key in sorted(legend.keys(), key=sortkey):
            line = "%s: %s" % (key, legend[key])
            lines.append(line)
        return listToGFM(lines)
    elif isinstance(legend, str):
        return listToGFM([legend])
    else:
        return listToGFM(legend)

def listToGFM(lines: Sequence[str]) -> str:
    if not lines: return ""
    return "\n" + "".join(["- %s\n" % line.strip() for line in lines if line.strip()])

def loadGFM(text: str, datedelim: str = '-') -> JSONList:
    data: JSONList = []
    convert = ParseJSONItem(datedelim)
    at = "start"
    for row in text.splitlines():
        line = row.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("|"):
            if at == "start":
                cols = [name.strip() for name in line.split("|")]
                at = "header"
                continue
            if at == "header":
                newcols = [name.strip() for name in line.split("|")]
                if len(newcols) != len(cols):
                    logg.error("header divider has not the same lenght")
                    at = "data" # promote anyway
                    continue
                ok = True
                for col in newcols:
                    if not col: continue
                    if not re.match(r"^ *:*--*:* *$", col):
                        logg.warning("no header divider: %s", col)
                        ok = False
                if not ok:
                   cols = [ cols[i] + " " + newcols[i] for i in range(cols) ]
                   continue
                else:
                   at = "data"
                   continue
            if at == "data":
                values = [field.strip() for field in line.split("|")]
                record = []
                for value in values:
                    record.append(convert.toJSONItem(value.strip()))
                newrow = dict(zip(cols, record))
                del newrow[""]
                data.append(newrow)
    return data


def tabToHTMLx(result: Union[JSONList, JSONDict], sorts: Sequence[str] = [], formats: Dict[str, str] = {}, legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        result = [result]
    return tabToHTML(result, sorts, formats, legend)
def tabToHTML(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}, legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    def sortkey(header: str) -> str:
        if header in sorts:
            return "%07i" % sorts.index(header)
        return header
    def sortrow(item: JSONDict) -> str:
        sortvalue = ""
        for sort in sorts:
            if sort in item:
                value = item[sort]
                if isinstance(value, int):
                    sortvalue += "\n%020i" % value
                else:
                    sortvalue += "\n" + strDateTime(value)
            else:
                sortvalue += "\n-"
        return sortvalue
    def format(col: str, val: JSONItem) -> str:
        if col in formats:
            if "%s" in formats[col]:
                try:
                    return formats[col] % strNone(val)
                except:
                    pass
            logg.info("unknown format '%s' for col '%s'", formats[col], col)
        return strNone(val)
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    def rightTH(col: str, value: str) -> str:
        if col in formats and formats[col].startswith(" ") and not NORIGHT:
            return value.replace("<th>", '<th style="text-align: right">')
        return value
    def rightTD(col: str, value: str) -> str:
        if col in formats and formats[col].startswith(" ") and not NORIGHT:
            return value.replace("<td>", '<td style="text-align: right">')
        return value
    line = [rightTH(name, "<th>%s</th>" % escape(name)) for name in sorted(cols.keys(), key=sortkey)]
    lines = ["<tr>" + "".join(line) + "</tr>"]
    for item in sorted(result, key=sortrow):
        values: JSONDict = dict([(name, "") for name in cols.keys()])
        # logg.debug("values = %s", values)
        for name, value in item.items():
            values[name] = value
        line = [rightTD(name, "<td>%s</td>" % escape(format(name, values[name]))) for name in sorted(cols.keys(), key=sortkey)]
        lines.append("<tr>" + "".join(line) + "</tr>")
    return "<table>\n" + "\n".join(lines) + "\n</table>\n" + legendToHTML(legend, sorts)

def legendToHTML(legend: Union[Dict[str, str], Sequence[str]], sorts: Sequence[str] = []) -> str:
    def sortkey(header: str) -> str:
        if header in sorts:
            return "%07i" % sorts.index(header)
        return header
    if isinstance(legend, dict):
        lines = []
        for key in sorted(legend.keys(), key=sortkey):
            line = "%s: %s" % (key, legend[key])
            lines.append(line)
        return listToHTML(lines)
    elif isinstance(legend, str):
        return listToHTML([legend])
    else:
        return listToHTML(legend)

def listToHTML(lines: Sequence[str]) -> str:
    if not lines: return ""
    return "\n<ul>\n" + "".join(["<li>%s</li>\n" % escape(line.strip()) for line in lines if line.strip()]) + "</ul>"

def tabToJSONx(result: Union[JSONList, JSONDict], sorts: Sequence[str] = [], formats: Dict[str, str] = {}, datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        result = [result]
    return tabToJSON(result, sorts, formats, datedelim, legend)
def tabToJSON(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}, datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if legend:
        logg.debug("legend is ignored for JSON output")
    def sortkey(header: str) -> str:
        if header in sorts:
            return "%07i" % sorts.index(header)
        return header
    def sortrow(item: JSONDict) -> str:
        sortvalue = ""
        for sort in sorts:
            if sort in item:
                value = item[sort]
                if isinstance(value, int):
                    sortvalue += "\n%020i" % value
                else:
                    sortvalue += "\n" + strDateTime(value, datedelim)
            else:
                sortvalue += "\n-"
        return sortvalue
    def format(col: str, val: JSONItem) -> str:
        if col in ["NumCount"]:
            logg.warning("%s (%s) = %s", col, type(val), val)
        if val is None:
            return "null"
        if isinstance(val, (Date, Time)):
            return '"%s"' % strDateTime(val, datedelim)
        return json.dumps(val)
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    lines = []
    for item in sorted(result, key=sortrow):
        values: JSONDict = {}
        # logg.debug("values = %s", values)
        for name, value in item.items():
            values[name] = format(name, value)
        line = ['"%s": %s' % (name, values[name]) for name in sorted(cols.keys(), key=sortkey) if name in values]
        lines.append(" {" + ", ".join(line) + "}")
    return "[\n" + ",\n".join(lines) + "\n]"

def loadJSON(text: str, datedelim: str = '-') -> JSONList:
    convert = ParseJSONItem(datedelim)
    jsondata = json.loads(text)
    data: JSONList = jsondata
    for record in data:
        for key, val in record.items():
            if isinstance(val, str):
                record[key] = convert.toDate(val)
    return data

def tabToCSV(result: JSONList, sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}, datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if legend:
        logg.debug("legend is ignored for CSV output")
    def sortkey(header: str) -> str:
        if header in sorts:
            return "%07i" % sorts.index(header)
        return header
    def sortrow(item: JSONDict) -> str:
        sortvalue = ""
        for sort in sorts:
            if sort in item:
                value = item[sort]
                if isinstance(value, int):
                    sortvalue += "\n%020i" % value
                else:
                    sortvalue += "\n" + strDateTime(value, datedelim)
            else:
                sortvalue += "\n-"
        return sortvalue
    def format(col: str, val: JSONItem) -> str:
        if col in formats:
            if "%s" in formats[col]:
                try:
                    return formats[col] % strNone(val)
                except:
                    pass
            logg.info("unknown format '%s' for col '%s'", formats[col], col)
        if isinstance(val, (Date, Time)):
            return '%s' % strDateTime(val, datedelim)
        return strNone(val)
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    lines = []
    for item in sorted(result, key=sortrow):
        values: JSONDict = dict([(name, "") for name in cols.keys()])
        # logg.debug("values = %s", values)
        for name, value in item.items():
            values[name] = format(name, value)
        lines.append(values)
    import csv
    # csvfile = open(csv_filename, "w")
    csvfile = StringIO()
    writer = csv.DictWriter(csvfile, fieldnames=sorted(cols.keys(), key=sortkey), restval='ignore',
                            quoting=csv.QUOTE_MINIMAL, delimiter=";")
    writer.writeheader()
    for line in lines:
        writer.writerow(line)
    return csvfile.getvalue()

def loadCSV(text: str, datedelim: str = '-') -> JSONList:
    import csv
    csvfile = StringIO(text)
    reader = csv.DictReader(csvfile, restval='ignore',
                            quoting=csv.QUOTE_MINIMAL, delimiter=";")
    #
    convert = ParseJSONItem(datedelim)
    data: JSONList = []
    for row in reader:
        newrow: JSONDict = dict(row)
        for key, val in newrow.items():
            if isinstance(val, str):
                newrow[key] = convert.toJSONItem(val)
        data.append(newrow)
    return data
