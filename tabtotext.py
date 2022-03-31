#! /usr/bin/python3
"""
This script reimplements the queries/*.sql that have been used in Userlist.sh
but instead of using the Postgres API it uses the Crowd API.

// Please be aware the --appuser/--password represent crowd-application credentials (not a build user)
"""

from typing import Optional, Union, Dict, List, Any, Sequence
from requests import Session, Response
from urllib.parse import quote_plus as qq
from html import escape
from datetime import date as Date
from datetime import datetime as Time
import os
import re
import logging
import json
from io import BytesIO, StringIO

logg = logging.getLogger("TABTOTEXT")

DATEFMT = "%Y-%m-%d"
NORIGHT = False

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
def scanNone(val: str) -> JSONItem:
    if val == _None_String:
        return None
    if val == _False_String:
        return False
    if val == _True_String:
        return True
    return val

def tabToGFMx(result: Union[JSONList, JSONDict], sorts: Sequence[str] = [], formats: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        result = [result]
    return tabToGFM(result)
def tabToGFM(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}) -> str:
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
            paren = 0
            if name not in cols:
                cols[name] = max(5, len(name))
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
    return "\n".join(lines) + "\n"

def tabToHTMLx(result: Union[JSONList, JSONDict], sorts: Sequence[str] = [], formats: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        result = [result]
    return tabToHTML(result)
def tabToHTML(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}) -> str:
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
                cols[name] = max(5, len(name))
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
    return "<table>\n" + "\n".join(lines) + "\n</table>\n"

def tabToJSONx(result: Union[JSONList, JSONDict], sorts: Sequence[str] = [], formats: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        result = [result]
    return tabToJSON(result)
def tabToJSON(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}, datedelim: str = '-') -> str:
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
            return '"%s"' % strDateTime(val, datedelim)
        return json.dumps(val)
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            if name not in cols:
                cols[name] = max(5, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    lines = []
    for item in sorted(result, key=sortrow):
        values: JSONDict = dict([(name, "") for name in cols.keys()])
        # logg.debug("values = %s", values)
        for name, value in item.items():
            values[name] = format(name, value)
        line = ['"%s": %s' % (name, values[name]) for name in sorted(cols.keys(), key=sortkey)]
        lines.append(" {" + ", ".join(line) + "}")
    return "[\n" + ",\n".join(lines) + "\n]"

def loadJSON(text: str, datedelim: str = '-') -> JSONList:
    is_date = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)$".replace('-', datedelim))
    is_time = re.compile(
        r"(\d\d\d\d)-(\d\d)-(\d\d)[T](\d\d):(\d\d):(\d:\d)(?:[.]\d*)(?:[A-Z][A-Z][A-Z][A-Z]?)$".replace('-', datedelim))
    jsondata = json.loads(text)
    data: JSONList = jsondata
    for record in data:
        for key in record.keys():
            val = record[key]
            if not isinstance(val, str):
                continue
            as_time = is_time.match(val)
            if as_time:
                record[key] = Time(int(as_time.group(1)), int(as_time.group(2)), int(as_time.group(3)),  #
                                   int(as_time.group(4)), int(as_time.group(5)), int(as_time.group(6)))
            as_date = is_date.match(val)
            if as_date:
                record[key] = Date(int(as_date.group(1)), int(as_date.group(2)), int(as_date.group(3)))
    return data

def tabToCSV(result: JSONList, sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}, datedelim: str = '-') -> str:
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
                cols[name] = max(5, len(name))
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
    is_date = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)$".replace('-', datedelim))
    is_time = re.compile(
        r"(\d\d\d\d)-(\d\d)-(\d\d)[T](\d\d):(\d\d):(\d:\d)(?:[.]\d*)(?:[A-Z][A-Z][A-Z][A-Z]?)$".replace('-', datedelim))
    import csv
    csvfile = StringIO(text)
    reader = csv.DictReader(csvfile, restval='ignore',
                            quoting=csv.QUOTE_MINIMAL, delimiter=";")
    data: JSONList = []
    for row in reader:
        newrow: JSONDict = dict(row)
        for key in newrow.keys():
            val: JSONItem = scanNone(row[key])
            newrow[key] = val
            if isinstance(val, str):
                as_time = is_time.match(val)
                if as_time:
                    newrow[key] = Time(int(as_time.group(1)), int(as_time.group(2)), int(as_time.group(3)),
                                       int(as_time.group(4)), int(as_time.group(5)), int(as_time.group(6)))
                as_date = is_date.match(val)
                if as_date:
                    newrow[key] = Date(int(as_date.group(1)), int(as_date.group(2)), int(as_date.group(3)))
        data.append(newrow)
    return data
