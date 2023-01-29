#! /usr/bin/python3
"""
This script reimplements the queries/*.sql that have been used in Userlist.sh
but instead of using the Postgres API it uses the Crowd API.

// Please be aware the --appuser/--password represent crowd-application credentials (not a build user)
"""

from typing import Optional, Union, Dict, List, Any, Sequence, Callable, Collection, Sized, Type, cast
from html import escape
from datetime import date as Date
from datetime import datetime as Time
from datetime import timezone
import os
import re
import logging
import json
from io import StringIO


logg = logging.getLogger("TABTOTEXT")

DATEFMT = "%Y-%m-%d"
FLOATFMT = "%4.2f"
NORIGHT = False
MINWIDTH = 5

JSONData = Union[str, int, float, bool, Date, Time, None]

JSONBase = Union[str, int, float, bool]
JSONItem = Union[str, int, float, bool, Date, Time, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONItem]
JSONList = List[JSONDict]
JSONDictList = Dict[str, JSONList]
JSONDictDict = Dict[str, JSONDict]

# dataclass support

class DataItem:
    """ Use this as the base class for dataclass types """
    def __index__(self, name: str) -> JSONItem:
        return cast(JSONItem, getattr(self, name))
DataList = List[DataItem]

def _is_dataitem(obj: Any) -> bool:
    if isinstance(obj, DataItem):
        return True
    if hasattr(obj, '__dataclass_fields__'):
        return True
    return False
def _dataitem_asdict(obj: DataItem, dict_factory: Type[Dict[str, Any]] = dict) -> JSONDict:
    if hasattr(obj, "keys"):
        return cast(JSONDict, obj)
    result: JSONDict = dict_factory()
    annotations: Dict[str, str] = obj.__class__.__dict__.get('__annotations__', {})
    for name in annotations:
        result[name] = cast(JSONItem, getattr(obj, name))
    return result

# helper functions

_None_String = "~"
_False_String = "(no)"
_True_String = "(yes)"

def setNoRight(value: bool) -> None:
    global NORIGHT
    NORIGHT = value

def strDateTime(value: Any, datedelim: str = '-') -> str:
    if value is None:
        return _None_String
    if isinstance(value, Time):
        if "Z" in DATEFMT:
            return value.astimezone(timezone.utc).strftime(DATEFMT.replace('-', datedelim))
        else:
            return value.strftime(DATEFMT.replace('-', datedelim))
    if isinstance(value, Date):
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
    def __init__(self, datedelim: str = '-') -> None:
        self.is_date = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)$".replace('-', datedelim))
        self.is_time = re.compile(
            r"(\d\d\d\d)-(\d\d)-(\d\d)[T](\d\d):(\d\d):(\d:\d)(?:[.]\d*)(?:[A-Z][A-Z][A-Z][A-Z]?)$".replace('-', datedelim))
        self.is_hour = re.compile(
            r"(\d\d\d\d)-(\d\d)-(\d\d)[Z .](\d\d):?(\d\d)?$".replace('-', datedelim))
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
            if "Z" in val:
                return Time(int(as_time.group(1)), int(as_time.group(2)), int(as_time.group(3)),
                            int(as_time.group(4)), int(as_time.group(5)), int(as_time.group(6)), tzinfo=timezone.utc)
            else:
                return Time(int(as_time.group(1)), int(as_time.group(2)), int(as_time.group(3)),
                            int(as_time.group(4)), int(as_time.group(5)), int(as_time.group(6)))
        as_hour = self.is_hour.match(val)
        if as_hour:
            if "Z" in val:
                return Time(int(as_hour.group(1)), int(as_hour.group(2)), int(as_hour.group(3)),
                            int(as_hour.group(4)), int(as_hour.group(5)), tzinfo=timezone.utc)
            else:
                return Time(int(as_hour.group(1)), int(as_hour.group(2)), int(as_hour.group(3)),
                            int(as_hour.group(4)), int(as_hour.group(5)))
        as_date = self.is_date.match(val)
        if as_date:
            return Date(int(as_date.group(1)), int(as_date.group(2)), int(as_date.group(3)))
        return val  # str

def tabWithDateTime() -> None:
    global DATEFMT
    DATEFMT = "%Y-%m-%dT%H:%M:%S"

def tabWithDateHour() -> None:
    global DATEFMT
    DATEFMT = "%Y-%m-%d.%H%M"

def tabWithDateZulu() -> None:
    global DATEFMT
    DATEFMT = "%Y-%m-%dZ%H%M"

def tabWithDateOnly() -> None:
    global DATEFMT
    DATEFMT = "%Y-%m-%d"

def tabToGFMx(result: Union[JSONList, JSONDict, DataList, DataItem], sorts: Sequence[str] = [], formats: Dict[str, str] = {},  #
              legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)
    return tabToGFM(results, sorts, formats, legend=legend)
def tabToGFM(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}, *,  #
             legend: Union[Dict[str, str], Sequence[str]] = [], tab: str = "|",  #
             reorder: Union[None, Sequence[str], Callable[[str], str]] = None) -> str:
    def sortkey(header: str) -> str:
        if callable(reorder):
            return reorder(header)
        else:
            sortheaders = reorder or sorts
            if header in sortheaders:
                return "%07i" % sortheaders.index(header)
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
            if "{:" in formats[col]:
                try:
                    return formats[col].format(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", formats[col], e)
            if isinstance(val, float):
                m = re.search(r"%\d(?:[.]\d)f", formats[col])
                if m:
                    try:
                        return formats[col] % val
                    except Exception as e:
                        logg.debug("format <%s> does not apply: %e", formats[col], e)
            if "%s" in formats[col]:
                try:
                    return formats[col] % strNone(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", formats[col], e)
            logg.debug("unknown format '%s' for col '%s'", formats[col], col)
        if isinstance(val, float):
            return FLOATFMT % val
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
    line = [rightF(name, tab + " %%-%is" % cols[name]) % name for name in sorted(cols.keys(), key=sortkey)]
    lines = [" ".join(line)]
    seperators = [(tab + " %%-%is" % cols[name]) % rightS(name, "-" * cols[name]) for name in sorted(cols.keys(), key=sortkey)]
    lines.append(" ".join(seperators))
    for item in sorted(result, key=sortrow):
        values: Dict[str, str] = {}
        for name, value in item.items():
            values[name] = format(name, value)
        line = [rightF(name, tab + " %%-%is" % cols[name]) % values.get(name, _None_String)
                for name in sorted(cols.keys(), key=sortkey)]
        lines.append(" ".join(line))
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
    return "\n" + "".join(["- %s\n" % line.strip() for line in lines if line and line.strip()])

def loadGFM(text: str, datedelim: str = '-', tab: str = '|') -> JSONList:
    data: JSONList = []
    convert = ParseJSONItem(datedelim)
    at = "start"
    for row in text.splitlines():
        line = row.strip()
        if not line or line.startswith("#"):
            continue
        if tab in "\t" and row.startswith(tab):
            line = tab + line  # was removed by strip()
        if line.startswith(tab) or (tab in "\t" and tab in line):
            if at == "start":
                cols = [name.strip() for name in line.split(tab)]
                at = "header"
                continue
            if at == "header":
                newcols = [name.strip() for name in line.split(tab)]
                if len(newcols) != len(cols):
                    logg.error("header divider has not the same lenght")
                    at = "data"  # promote anyway
                    continue
                ok = True
                for col in newcols:
                    if not col: continue
                    if not re.match(r"^ *:*--*:* *$", col):
                        logg.warning("no header divider: %s", col)
                        ok = False
                if not ok:
                    cols = [cols[i] + " " + newcols[i] for i in range(len(cols))]
                    continue
                else:
                    at = "data"
                    continue
            if at == "data":
                values = [field.strip() for field in line.split(tab)]
                record = []
                for value in values:
                    record.append(convert.toJSONItem(value.strip()))
                newrow = dict(zip(cols, record))
                if "" in newrow:
                    del newrow[""]
                data.append(newrow)
        else:
            logg.warning("unrecognized line: %s", line.replace(tab, "|"))
    return data


def tabToHTMLx(result: Union[JSONList, JSONDict, DataList, DataItem], sorts: Sequence[str] = [], formats: Dict[str, str] = {},  #
               legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToHTML(results, sorts, formats, legend=legend)
def tabToHTML(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}, *,  #
              legend: Union[Dict[str, str], Sequence[str]] = [],  #
              reorder: Union[None, Sequence[str], Callable[[str], str]] = None) -> str:
    def sortkey(header: str) -> str:
        if callable(reorder):
            return reorder(header)
        else:
            sortheaders = reorder or sorts
            if header in sortheaders:
                return "%07i" % sortheaders.index(header)
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
            if "{:" in formats[col]:
                try:
                    return formats[col].format(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", formats[col], e)
            if "%s" in formats[col]:
                try:
                    return formats[col] % strNone(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", formats[col], e)
            logg.debug("unknown format '%s' for col '%s'", formats[col], col)
        if isinstance(val, float):
            return FLOATFMT % val
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
        values: Dict[str, str] = dict([(name, "") for name in cols.keys()])  # initialized with all columns to empty string
        for name, value in item.items():
            values[name] = format(name, value)
        line = [rightTD(name, "<td>%s</td>" % escape(values[name])) for name in sorted(cols.keys(), key=sortkey)]
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
    return "\n<ul>\n" + "".join(["<li>%s</li>\n" % escape(line.strip()) for line in lines if line and line.strip()]) + "</ul>"

def tabToJSONx(result: Union[JSONList, JSONDict, DataList, DataItem], sorts: Sequence[str] = [], formats: Dict[str, str] = {},  #
               datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToJSON(results, sorts, formats, datedelim=datedelim, legend=legend)
def tabToJSON(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}, *,  #
              datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = [],  #
              reorder: Union[None, Sequence[str], Callable[[str], str]] = None) -> str:
    if legend:
        logg.debug("legend is ignored for JSON output")
    def sortkey(header: str) -> str:
        if callable(reorder):
            return reorder(header)
        else:
            sortheaders = reorder or sorts
            if header in sortheaders:
                return "%07i" % sortheaders.index(header)
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
        if val is None:
            return "null"
        if isinstance(val, float):
            return FLOATFMT % val
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

def tabToYAMLx(result: Union[JSONList, JSONDict, DataList, DataItem], sorts: Sequence[str] = [], formats: Dict[str, str] = {},  #
               datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToYAML(results, sorts, formats, datedelim=datedelim, legend=legend)
def tabToYAML(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}, *,  #
              datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = [],  #
              reorder: Union[None, Sequence[str], Callable[[str], str]] = None) -> str:
    if legend:
        logg.debug("legend is ignored for YAML output")
    def sortkey(header: str) -> str:
        if callable(reorder):
            return reorder(header)
        else:
            sortheaders = reorder or sorts
            if header in sortheaders:
                return "%07i" % sortheaders.index(header)
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
        if val is None:
            return "null"
        if isinstance(val, float):
            return FLOATFMT % val
        if isinstance(val, (Date, Time)):
            return '%s' % strDateTime(val, datedelim)
        return json.dumps(val)
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    is_simple = re.compile("^\\w[\\w_-]*$")
    def as_name(name: str) -> str:
        return (name if is_simple.match(name) else '"%s"' % name)
    lines = []
    for item in sorted(result, key=sortrow):
        values: JSONDict = {}
        for name, value in item.items():
            values[name] = format(name, value)
        line = ['%s: %s' % (as_name(name), values[name]) for name in sorted(cols.keys(), key=sortkey) if name in values]
        lines.append("- " + "\n  ".join(line))
    return "data:\n" + "\n".join(lines) + "\n"

def loadYAML(text: str, datedelim: str = '-') -> JSONList:
    data: JSONList = []
    convert = ParseJSONItem(datedelim)
    convert.None_String = "null"
    convert.True_String = "true"
    convert.False_String = "false"
    at = "start"
    record: JSONDict = {}
    for row in text.splitlines():
        line = row.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("data:"):
            if at == "start":
                at = "data"
            continue
        if at not in ["data"]:
            continue
        if line.startswith("-") or line.startswith(" -"):
            if record:
                data.append(record)
                record = {}
            line = line.strip()[1:]
        m = re.match(r" *(\w[\w\d.-]*) *: *\"([^\"]*)\" *", line)
        if m:
            record[m.group(1)] = m.group(2)
            continue
        m = re.match(r" *(\w[\w\d.-]*) *: *(.*)", line)
        if m:
            record[m.group(1)] = convert.toJSONItem(m.group(2).strip())
            continue
        m = re.match(r" *\"([^\"]+)\" *: *\"([^\"]*)\" *", line)
        if m:
            record[m.group(1)] = m.group(2)
            continue
        m = re.match(r" *\"([^\"]+)\" *: *(.*)", line)
        if m:
            record[m.group(1)] = convert.toJSONItem(m.group(2).strip())
            continue
        logg.error("can not parse: %s", line)
    if record:
        data.append(record)
    return data

def tabToTOMLx(result: Union[JSONList, JSONDict, DataList, DataItem], sorts: Sequence[str] = [], formats: Dict[str, str] = {},  #
               datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToTOML(results, sorts, formats, datedelim=datedelim, legend=legend)
def tabToTOML(result: JSONList, sorts: Sequence[str] = [], formats: Dict[str, str] = {}, *,  #
              datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = [],  #
              reorder: Union[None, Sequence[str], Callable[[str], str]] = None) -> str:
    if legend:
        logg.debug("legend is ignored for TOML output")
    def sortkey(header: str) -> str:
        if callable(reorder):
            return reorder(header)
        else:
            sortheaders = reorder or sorts
            if header in sortheaders:
                return "%07i" % sortheaders.index(header)
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
        if val is None:
            return "null"
        if isinstance(val, float):
            return FLOATFMT % val
        if isinstance(val, (Date, Time)):
            return '%s' % strDateTime(val, datedelim)
        return json.dumps(val)
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    is_simple = re.compile("^\\w[\\w_-]*$")
    def as_name(name: str) -> str:
        return (name if is_simple.match(name) else '"%s"' % name)
    lines = []
    for item in sorted(result, key=sortrow):
        values: JSONDict = {}
        for name, value in item.items():
            if value is not None:
                values[name] = format(name, value)
        line = ['%s = %s' % (as_name(name), values[name]) for name in sorted(cols.keys(), key=sortkey) if name in values]
        lines.append("[[data]]\n" + "\n".join(line))
    return "\n".join(lines) + "\n"

def loadTOML(text: str, datedelim: str = '-') -> JSONList:
    data: JSONList = []
    convert = ParseJSONItem(datedelim)
    convert.None_String = "null"
    convert.True_String = "true"
    convert.False_String = "false"
    at = "start"
    record: JSONDict = {}
    for row in text.splitlines():
        line = row.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[[data]]"):
            if at == "start":
                at = "data"
            if record:
                data.append(record)
                record = {}
            continue
        if at not in ["data"]:
            continue
        m = re.match(r" *(\w[\w\d.-]*) *= *\"([^\"]*)\" *", line)
        if m:
            record[m.group(1)] = m.group(2)
            continue
        m = re.match(r" *(\w[\w\d.-]*) *= *(.*)", line)
        if m:
            record[m.group(1)] = convert.toJSONItem(m.group(2).strip())
            continue
        m = re.match(r" *\"([^\"]+)\" *= *\"([^\"]*)\" *", line)
        if m:
            record[m.group(1)] = m.group(2)
            continue
        m = re.match(r" *\"([^\"]+)\" *= *(.*)", line)
        if m:
            record[m.group(1)] = convert.toJSONItem(m.group(2).strip())
            continue
        logg.error("can not parse: %s", line)
    if record:
        data.append(record)
    return data

def tabToCSVx(result: Union[JSONList, JSONDict, DataList, DataItem], sorts: Sequence[str] = [], formats: Dict[str, str] = {},  #
              datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToCSV(results, sorts, formats, datedelim=datedelim, legend=legend)
def tabToCSV(result: JSONList, sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}, *,  #
             datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = [], tab: str = ";",  #
             reorder: Union[None, Sequence[str], Callable[[str], str]] = None) -> str:
    if legend:
        logg.debug("legend is ignored for CSV output")
    def sortkey(header: str) -> str:
        if callable(reorder):
            return reorder(header)
        else:
            sortheaders = reorder or sorts
            if header in sortheaders:
                return "%07i" % sortheaders.index(header)
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
            if "{:" in formats[col]:
                try:
                    return formats[col].format(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", formats[col], e)
            if "%s" in formats[col]:
                try:
                    return formats[col] % strNone(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", formats[col], e)
            logg.debug("unknown format '%s' for col '%s'", formats[col], col)
        if isinstance(val, (Date, Time)):
            return '%s' % strDateTime(val, datedelim)
        if isinstance(val, float):
            return FLOATFMT % val
        return strNone(val)
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    lines = []
    for item in sorted(result, key=sortrow):
        values: JSONDict = dict([(name, _None_String) for name in cols.keys()])
        for name, value in item.items():
            values[name] = format(name, value)
        lines.append(values)
    import csv
    # csvfile = open(csv_filename, "w")
    csvfile = StringIO()
    writer = csv.DictWriter(csvfile, fieldnames=sorted(cols.keys(), key=sortkey), restval='ignore',
                            quoting=csv.QUOTE_MINIMAL, delimiter=tab)
    writer.writeheader()
    for line in lines:
        writer.writerow(line)
    return csvfile.getvalue()

def loadCSV(text: str, datedelim: str = '-', tab: str = ";") -> JSONList:
    import csv
    csvfile = StringIO(text)
    reader = csv.DictReader(csvfile, restval='ignore',
                            quoting=csv.QUOTE_MINIMAL, delimiter=tab)
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

def tabToFMTx(output: str, result: Union[JSONList, JSONDict, DataList, DataItem], sorts: Sequence[str] = [], formats: Dict[str, str] = {},  #
              datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToFMT(output, results, sorts, formats, datedelim=datedelim, legend=legend)
def tabToFMT(output: str, result: JSONList, sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}, *,  #
             datedelim: str = '-', legend: Union[Dict[str, str], Sequence[str]] = [],  #
             reorder: Union[None, Sequence[str], Callable[[str], str]] = None) -> str:
    if output.lower() in ["md", "markdown"]:
        return tabToGFM(result=result, sorts=sorts, formats=formats, reorder=reorder)
    if output.lower() in ["html"]:
        return tabToHTML(result=result, sorts=sorts, formats=formats, reorder=reorder)
    if output.lower() in ["json"]:
        return tabToJSON(result=result, sorts=sorts, formats=formats, reorder=reorder, datedelim=datedelim)
    if output.lower() in ["yaml"]:
        return tabToYAML(result=result, sorts=sorts, formats=formats, reorder=reorder, datedelim=datedelim)
    if output.lower() in ["toml"]:
        return tabToTOML(result=result, sorts=sorts, formats=formats, reorder=reorder, datedelim=datedelim)
    if output.lower() in ["wide"]:
        return tabToGFM(result=result, sorts=sorts, formats=formats, reorder=reorder, tab='')
    if output.lower() in ["tabs"]:
        return tabToGFM(result=result, sorts=sorts, formats=formats, reorder=reorder, tab='\t')
    if output.lower() in ["tab"]:
        return tabToCSV(result=result, sorts=sorts, formats=formats, reorder=reorder, datedelim=datedelim, tab='\t')
    if output.lower() in ["csv"]:
        return tabToCSV(result=result, sorts=sorts, formats=formats, reorder=reorder, datedelim=datedelim, tab=';')
    # including the legend
    if output.lower() in ["htm"]:
        return tabToHTML(result=result, sorts=sorts, formats=formats, reorder=reorder, legend=legend)
    return tabToGFM(result=result, sorts=sorts, formats=formats, reorder=reorder, legend=legend)
