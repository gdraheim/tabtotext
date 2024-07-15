#! /usr/bin/env python3
"""
This script allows to format table-like data (list of dicts).
The various output formats can be read back.
"""

__copyright__ = "(C) 2017-2024 Guido Draheim, licensed under the Apache License 2.0"""
__version__ = "1.6.3283"

from typing import Optional, Union, Dict, List, Any, Sequence, Callable, Type, cast, Iterable, Iterator, TextIO, NamedTuple
from collections import OrderedDict
from html import escape
from datetime import date as Date
from datetime import datetime as Time
from datetime import timezone
from abc import abstractmethod
import os
import sys
import re
import logging
import json
from io import StringIO, TextIOWrapper
logg = logging.getLogger("TABTOTEXT")

try:
    from tabtools import Frac4, fracfloat, float_with_frac, float_with_hours
except ImportError as e:  # pragma: no cover
    logg.warning("can not import tabtools, fallback to Frac4 with {.2f}, %s", e)
    class Frac4:  # type: ignore[no-redef]
        def __init__(self, value: float) -> None:
            self.value = value
        def __format__(self, fmt: str) -> str:
            value = self.value
            if fmt and fmt[-1] in "HhqQMR$":
                fmt = ".2f"
            num = "{:" + fmt + "}"
            return fmt.format(value)
    def fracfloat(value: str) -> float:
        return float(value)


DATEFMT = "%Y-%m-%d"
TIMEFMT = "%Y-%m-%d.%H%M"
FLOATFMT = "%4.2f"
NORIGHT = False
MINWIDTH = 5
NIX = ""
COL_SEP = "|"

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
    def __getitem__(self, name: str) -> JSONItem:
        return cast(JSONItem, getattr(self, name))
    def replace(self, **values: str) -> JSONDict:
        return _dataitem_replace(self, values)  # type: ignore[arg-type]

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
def _dataitem_replace(obj: DataItem, values: JSONDict, dict_factory: Type[Dict[str, Any]] = dict) -> JSONDict:
    result: JSONDict = dict_factory()
    annotations: Dict[str, str] = obj.__class__.__dict__.get('__annotations__', {})
    for name in annotations:
        if name in values:
            result[name] = values[name]
        else:
            result[name] = cast(JSONItem, getattr(obj, name))
    return result

# helper functions

_None_String = "~"
_False_String = "(no)"
_True_String = "(yes)"

def setNoRight(value: bool) -> None:
    global NORIGHT
    NORIGHT = value

def str77(value: JSONItem, maxlength: int = 77) -> str:
    assert maxlength > 10
    if value is None:
        return _None_String
    val = str(value)
    if len(val) > maxlength:
        return val[:(maxlength - 10)] + "..." + val[-7:]
    return val
def str40(value: JSONItem) -> str:
    return str77(value, 40)
def str27(value: JSONItem) -> str:
    return str77(value, 27)
def str18(value: JSONItem) -> str:
    return str77(value, 18)

def strNone(value: Any, datedelim: str = '-', datefmt: Optional[str] = None) -> str:
    return strJSONItem(value, datedelim, datefmt)
def strJSONItem(value: JSONItem, datedelim: str = '-', datefmt: Optional[str] = None) -> str:
    if value is None:
        return _None_String
    if value is False:
        return _False_String
    if value is True:
        return _True_String
    if isinstance(value, Time):
        datefmt1 = datefmt if datefmt else DATEFMT
        datefmt2 = datefmt1.replace('-', datedelim)
        if "Z" in DATEFMT:
            return value.astimezone(timezone.utc).strftime(datefmt2)
        else:
            return value.strftime(datefmt2)
    if isinstance(value, Date):
        datefmt1 = datefmt if datefmt else DATEFMT
        datefmt2 = datefmt1.replace('-', datedelim)
        return value.strftime(datefmt2)
    return str(value)
def unmatched(value: JSONItem, cond: str) -> bool:
    try:
        if value is None:
            if cond in ["<>"]:
                return True
        elif value is False:
            if cond in ["==1", "==True", "==true", "==yes", "==(yes)"]:
                return True
            if cond in ["<>0", "<>False", "<>false", "<>no", "<>(no)"]:
                return True
        elif value is True:
            if cond in ["<>0", "<>False", "<>false", "<>no", "<>(no)"]:
                return True
            if cond in ["==1", "==True", "==true", "==yes", "==(yes)"]:
                return True
        elif isinstance(value, int):
            if cond.startswith("==") or cond.startswith("=~"):
                return value != int(cond[2:])
            if cond.startswith("<>"):
                return value == int(cond[2:])
            if cond.startswith("<="):
                return value > int(cond[2:])
            if cond.startswith("<"):
                return value >= int(cond[1:])
            if cond.startswith(">="):
                return value < int(cond[2:])
            if cond.startswith(">"):
                return value <= int(cond[1:])
        elif isinstance(value, float):
            if cond.startswith("=~"):
                return value-0.01 > float(cond[2:]) or float(cond[2:]) > value+0.01 
            if cond.startswith("<>"):
                return value-0.01 < float(cond[2:]) and float(cond[2:]) < value+0.01 
            if cond.startswith("==") or cond.startswith("=~"):
                return value != float(cond[2:]) # not recommended
            if cond.startswith("<="):
                return value > float(cond[2:])
            if cond.startswith("<"):
                return value >= float(cond[1:])
            if cond.startswith(">="):
                return value < float(cond[2:])
            if cond.startswith(">"):
                return value <= float(cond[1:])
        elif isinstance(value, Time):
            if cond.startswith("==") or cond.startswith("=~"):
                return value.strftime(TIMEFMT) != cond[2:]
            if cond.startswith("<>"):
                return value.strftime(TIMEFMT) == cond[2:]
            if cond.startswith("<="):
                return value.strftime(TIMEFMT) > cond[2:]
            if cond.startswith("<"):
                return value.strftime(TIMEFMT) >= cond[1:]
            if cond.startswith(">="):
                return value.strftime(TIMEFMT) < cond[2:]
            if cond.startswith(">"):
                return value.strftime(TIMEFMT) <= cond[1:]
        elif isinstance(value, Date):
            if cond.startswith("==") or cond.startswith("=~"):
                return value.strftime(DATEFMT) != cond[2:]
            if cond.startswith("<>"):
                return value.strftime(DATEFMT) == cond[2:]
            if cond.startswith("<="):
                return value.strftime(DATEFMT) > cond[2:]
            if cond.startswith("<"):
                return value.strftime(DATEFMT) >= cond[1:]
            if cond.startswith(">="):
                return value.strftime(DATEFMT) < cond[2:]
            if cond.startswith(">"):
                return value.strftime(DATEFMT) <= cond[1:]
        else:
            if cond.startswith("=~"):
                return str(value) != cond[2:]
            if cond.startswith("=="):
                return str(value) != cond[2:]
            if cond.startswith("<>"):
                return str(value) == cond[2:]
            if cond.startswith("<="):
                return str(value) > cond[2:]
            if cond.startswith("<"):
                return str(value) >= cond[1:]
            if cond.startswith(">="):
                return str(value) < cond[2:]
            if cond.startswith(">"):
                return str(value) <= cond[1:]
    except Exception as e:
        logg.warning("unmatched value type %s does not work for cond %s", type(value), cond)
    return False

class DictParser:
    @abstractmethod
    def load(self, filename: str) -> Iterator[JSONDict]:
        while False:
            yield {}
    @abstractmethod
    def loads(self, text: str) -> Iterator[JSONDict]:
        while False:
            yield {}

class FormatJSONItem:
    @abstractmethod
    def __call__(self, col: str, val: JSONItem) -> str:
        return ""
    def right(self, col: str) -> bool:
        return False

FormatsDict = Union[FormatJSONItem, Dict[str, str]]

class BaseFormatJSONItem(FormatJSONItem):
    def __init__(self, formats: Dict[str, str], **kwargs: Any) -> None:
        self.formats = formats
        self.datedelim = '-'
        self.datefmt = DATEFMT
        self.kwargs = kwargs
        self.formatleft = re.compile("[{]:[^{}]*<[^{}]*[}]")
        self.formatright = re.compile("[{]:[^{}]*>[^{}]*[}]")
        self.formatnumber = re.compile("[{]:[^{}]*[defghDEFGHMQR$%][}]")
    def right(self, col: str) -> bool:
        if col in self.formats and not NORIGHT:
            if self.formats[col].startswith(" "):
                return True
            if self.formatleft.search(self.formats[col]):
                return False
            if self.formatright.search(self.formats[col]):
                return True
            if self.formatnumber.search(self.formats[col]):
                return True
        return False
    def __call__(self, col: str, val: JSONItem) -> str:
        return self.item(val)
    def item(self, val: JSONItem) -> str:
        return strJSONItem(val, self.datedelim, self.datefmt)

class ParseJSONItem:
    def __init__(self, datedelim: str = '-') -> None:
        self.is_date = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)$".replace('-', datedelim))
        self.is_time = re.compile(
            r"(\d\d\d\d)-(\d\d)-(\d\d)[T](\d\d):(\d\d):(\d:\d)(?:[.]\d*)(?:[A-Z][A-Z][A-Z][A-Z]?)$".replace('-', datedelim))
        self.is_hour = re.compile(
            r"(\d\d\d\d)-(\d\d)-(\d\d)[Z .](\d\d):?(\d\d)?$".replace('-', datedelim))
        self.is_int = re.compile(r"([+-]?\d+)$")
        self.is_float = re.compile(r"([+-]?\d+)(?:[.]\d*)?(?:e[+-]?\d+)?$")
        self.is_float_with_frac = re.compile(float_with_frac)
        self.is_float_with_hours = re.compile(float_with_hours)
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
        if self.is_float_with_frac.match(val):
            return fracfloat(val)
        if self.is_float_with_hours.match(val):
            return fracfloat(val)
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

# ================================= sorting

RowSortList = Union[Sequence[str], Dict[str, str], Callable[[JSONDict], str]]

class RowSortCallable:
    """ The column names in the sorts-list are used here for one of their 
        functions as sorting the rows of the table by returning a sort-string
        from the record. You can override that with a callable but then it
        can not be used anymore with its double function to also move the
        sort-columns to the left of the table. See 'reorder' below."""
    def __init__(self, sorts: RowSortList, datedelim: str = '-') -> None:
        """ only a few tabto-functions have a local datedelim to pass"""
        self.sorts = sorts
        self.datedelim = datedelim
    def __call__(self, item: JSONDict) -> str:
        """ makes the class to be of type Callable[[JSONDict], str] """
        sorts = self.sorts
        if callable(sorts):
            return sorts(item)
        else:
            sortvalue = ""
            for sort in sorts:
                if sort in item:
                    value = item[sort]
                    if value is None:
                        sortvalue += "\n?"
                    elif value is False:
                        sortvalue += "\n"
                    elif value is True:
                        sortvalue += "\n!"
                    elif isinstance(value, int):
                        sortvalue += "\n%020i" % value
                    elif isinstance(value, float):
                        sortvalue += "\n%020.6f" % value
                    else:
                        sortvalue += "\n" + strJSONItem(value, self.datedelim)
                else:
                    sortvalue += "\n?"
            return sortvalue

ColSortList = Union[Sequence[str], Dict[str, str], Callable[[str], str]]

class ColSortCallable:
    """ The column names in the sorts-list always had a double function: sorting
        the rows, and the sorting columns are reordered to the left of the table.
        The latter can be overridden by specifying a reorder-list of colum names,
        plus that one can be a function that returns the reordering key. """
    def __init__(self, sorts: RowSortList, reorder: ColSortList = []) -> None:
        self.sorts = sorts
        self.reorder = reorder
    def __call__(self, header: str) -> str:
        """ makes the class to be of type Callable[[str], str] """
        reorder = self.reorder
        if callable(reorder):
            return reorder(header)
        else:
            sortheaders = reorder
            sorts = self.sorts
            if not sortheaders and not callable(sorts):
                sortheaders = sorts
            if isinstance(sortheaders, dict):
                if header in sortheaders:
                    return sortheaders[header]
            else:
                if header in sortheaders:
                    return "%07i" % sortheaders.index(header)
        return header

LegendList = Union[Dict[str, str], Sequence[str]]

# ================================= #### GFM
class NumFormatJSONItem(BaseFormatJSONItem):
    def __init__(self, formats: Dict[str, str] = {}, tab: str = '|'):
        BaseFormatJSONItem.__init__(self, formats)
        self.floatfmt = FLOATFMT
    def __call__(self, col: str, val: JSONItem) -> str:
        if col in self.formats:
            fmt = self.formats[col]
            if "{:" in fmt:
                for fmt4 in fmt.split("|"):
                    val4 = val
                    q = fmt4.rindex("}")
                    if q > 0 and fmt4[q - 1] in "hHqQM$":
                        val4 = Frac4(val)  # type: ignore[assignment,arg-type]
                    try:
                        return fmt4.format(val4)
                    except Exception as e:
                        logg.debug("format <%s> does not apply: %s", fmt, e)
            # only a few percent-formatting variants are supported
            if isinstance(val, float):
                m = re.search(r"%\d(?:[.]\d)f", fmt)
                if m:
                    try:
                        return fmt % val
                    except Exception as e:
                        logg.debug("format <%s> does not apply: %e", fmt, e)
            if "%s" in fmt:
                try:
                    return fmt % self.item(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", fmt, e)
            logg.debug("unknown format '%s' for col '%s'", fmt, col)
        if isinstance(val, float):
            return self.floatfmt % val
        return self.item(val)
class FormatGFM(NumFormatJSONItem):
    def __init__(self, formats: Dict[str, str] = {}, tab: str = '|'):
        NumFormatJSONItem.__init__(self, formats)
        self.tab = tab
    def __call__(self, col: str, val: JSONItem) -> str:
        if not self.tab:
            return NumFormatJSONItem.__call__(self, col, val)
        if self.tab == '|':
            rep = '!'
        else:
            rep = '|'
        return NumFormatJSONItem.__call__(self, col, val).replace(self.tab, rep)

def tabToGFMx(result: Union[JSONList, JSONDict, DataList, DataItem],  # ..
              sorts: Sequence[str] = [], formats: FormatsDict = {}, selects: List[str] = [], # ..
              *, noheaders: bool = False, legend: LegendList = [], tab: str = "|",  #
              ) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)
    return tabToGFM(results, sorts, formats, selects, noheaders=noheaders, legend=legend, tab=tab)
def tabToGFM(result: Iterable[JSONDict],  # ..
             sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [], # ..
             *, noheaders: bool = False, legend: LegendList = [], tab: str = "|",  #
             reorder: ColSortList = []) -> str:
    filtered: Dict[str, str] = {}
    selected: List[str] = []
    for selec in [sel if "@" not in sel else sel.split("@", 1)[0] for sel in selects]:
        if ":" in selec:
            name, form = selec.split(":", 1)
            if isinstance(formats, dict):
                formats[name] = form if "{" in form else ("{:" + form + "}")
        else:
            name = selec
        if "<" in name:
            name, cond = name.split(">", 1)
            filtered[name] = ">" + cond
        elif ">" in name:
            name, cond = name.split("<", 1)
            filtered[name] = "<" + cond
        elif "~" in name:
            name, cond = name.split("=", 1)
            filtered[name] = "=" + cond
        selected.append(name)
    format: FormatJSONItem
    if isinstance(formats, FormatJSONItem):
        format = formats
    else:
        format = FormatGFM(formats, tab=tab)
    sortkey = ColSortCallable(sorts, reorder)
    sortrow = RowSortCallable(sorts)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for item in result:
        row: JSONDict = {}
        for name, value in item.items():
            if selected and name not in selected and "*" not in selected:
               continue
            try:
                if name in filtered and unmatched(value, filtered[name]):
                    continue
            except: pass
            row[name] = value
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
        rows.append(row)
    def rightF(col: str, formatter: str) -> str:
        if format.right(col):
            return formatter.replace("%-", "%")
        return formatter
    def rightS(col: str, formatter: str) -> str:
        if format.right(col):
            return formatter[:-1] + ":"
        return formatter
    tab2 = tab + " " if tab else ""
    lines: List[str] = []
    if not noheaders:
        line = [rightF(name, tab2 + "%%-%is" % cols[name]) % name for name in sorted(cols.keys(), key=sortkey)]
        lines += [(" ".join(line)).rstrip()]
        if tab:
            seperators = [(tab2 + "%%-%is" % cols[name]) % rightS(name, "-" * cols[name])
                          for name in sorted(cols.keys(), key=sortkey)]
            lines.append(" ".join(seperators))
    for item in sorted(rows, key=sortrow):
        values: Dict[str, str] = {}
        for name, value in item.items():
            values[name] = format(name, value)
        line = [rightF(name, tab2 + "%%-%is" % cols[name]) % values.get(name, _None_String)
                for name in sorted(cols.keys(), key=sortkey)]
        lines.append((" ".join(line)).rstrip())
    return "\n".join(lines) + "\n" + legendToGFM(legend, sorts, reorder)

def legendToGFM(legend: LegendList, sorts: RowSortList = [], reorder: ColSortList = []) -> str:
    sortkey = ColSortCallable(sorts, reorder)
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
    parser = DictParserGFM(datedelim=datedelim, tab=tab)
    return list(parser.loads(text))
def readFromGFM(filename: str, datedelim: str = '-', tab: str = '|') -> JSONList:
    parser = DictParserGFM(datedelim=datedelim, tab=tab)
    return list(parser.load(filename))

class DictParserGFM(DictParser):
    def __init__(self, *, datedelim: str = '-', tab: str = '|') -> None:
        self.convert = ParseJSONItem(datedelim)
        self.tab = tab
    def load(self, filename: str, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        return self.read(open(filename))
    def loads(self, text: str, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        return self.read(text.splitlines())
    def read(self, rows: Iterable[str], *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        tab = tab if tab is not None else self.tab
        at = "start"
        for row in rows:
            line = row.strip()
            if not line or line.startswith("#"):
                continue
            if not line or line.startswith("- "):
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
                        logg.error("header divider has not the same length")
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
                        record.append(self.convert.toJSONItem(value.strip()))
                    newrow = dict(zip(cols, record))
                    if "" in newrow:
                        del newrow[""]
                    yield newrow
            else:
                logg.warning("unrecognized line: %s", line.replace(tab, "|"))

# ================================= #### HTML
class FormatHTML(NumFormatJSONItem):
    def __init__(self, formats: Dict[str, str] = {}):
        NumFormatJSONItem.__init__(self, formats)

def tabToHTMLx(result: Union[JSONList, JSONDict, DataList, DataItem],  # .. 
               sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [], # ..
               *, legend: LegendList = [], combine: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToHTML(results, sorts, formats, selects, legend=legend, combine=combine)
def tabToHTML(result: Iterable[JSONDict],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
              *, legend: LegendList = [], combine: Dict[str, str] = {},  # [target]->[attach]
              reorder: ColSortList = []) -> str:
    filtered: Dict[str, str] = {}
    selected: List[str] = []
    for selec in [sel if "@" not in sel else sel.split("@", 1)[0] for sel in selects]:
        if ":" in selec:
            name, form = selec.split(":", 1)
            if isinstance(formats, dict):
                formats[name] = form if "{" in form else ("{:" + form + "}")
        else:
            name = selec
        if "<" in name:
            name, cond = name.split(">", 1)
            filtered[name] = ">" + cond
        elif ">" in name:
            name, cond = name.split("<", 1)
            filtered[name] = "<" + cond
        elif "~" in name:
            name, cond = name.split("=", 1)
            filtered[name] = "=" + cond
        selected.append(selec)
    format: FormatJSONItem
    if isinstance(formats, FormatJSONItem):
        format = formats
    else:
        format = FormatHTML(formats)
    sortkey = ColSortCallable(sorts, reorder)
    sortrow = RowSortCallable(sorts)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for item in result:
        row: JSONDict = {}
        for name, value in item.items():
            if selected and name not in selected and "*" not in selected:
               continue
            try:
                if name in filtered and unmatched(value, filtered[name]):
                    continue
            except: pass
            row[name] = value
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
        rows.append(row)
    def rightTH(col: str, value: str) -> str:
        if format.right(col):
            return value.replace("<th>", '<th style="text-align: right">')
        return value
    def rightTD(col: str, value: str) -> str:
        if format.right(col):
            return value.replace("<td>", '<td style="text-align: right">')
        return value
    combined = list(combine.values())
    for name in combine:
        if name not in cols:  # if target does not exist in dataset
            combined.remove(combine[name])  # the shown combined column seperately
    headers = []
    for name in sorted(cols.keys(), key=sortkey):
        if name in combined:
            continue
        if name in combine and combine[name] in cols:
            headers += [rightTH(name, "<th>{}<br />{}</th>".format(escape(name), escape(combine[name])))]
        else:
            headers += [rightTH(name, "<th>{}</th>".format(escape(name)))]
    lines = ["<tr>" + "".join(headers) + "</tr>"]
    for item in sorted(rows, key=sortrow):
        values: Dict[str, str] = dict([(name, "") for name in cols.keys()])  # initialized with all columns to empty string
        for name, value in item.items():
            values[name] = format(name, value)
        cells = []
        for name in sorted(cols.keys(), key=sortkey):
            if name in combined:
                continue
            if name in combine and combine[name] in cols:
                cells += [rightTD(name, "<td>{}<br />{}</td>".format(escape(values[name]), escape(values[combine[name]])))]
            else:
                cells += [rightTD(name, "<td>{}</td>".format(escape(values[name])))]
        lines.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>\n" + "\n".join(lines) + "\n</table>\n" + legendToHTML(legend, sorts, reorder)

def legendToHTML(legend: LegendList, sorts: RowSortList = [], reorder: ColSortList = []) -> str:
    sortkey = ColSortCallable(sorts, reorder)
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

def readFromHTML(filename: str, datedelim: str = '-') -> JSONList:
    parser = DictParserHTML(datedelim)
    return list(parser.load(filename))
def loadHTML(text: str, datedelim: str = '-') -> JSONList:
    parser = DictParserHTML(datedelim)
    return list(parser.loads(text))

class DictParserHTML(DictParser):
    def __init__(self, datedelim: str = '-', convert_charrefs: bool = True) -> None:
        self.convert = ParseJSONItem(datedelim)
        self.convert_charrefs = convert_charrefs
    def load(self, filename: str, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        return self.read(open(filename))
    def loads(self, text: str, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        return self.read(text.splitlines())
    def read(self, rows: Iterable[str]) -> Iterator[JSONDict]:
        import html.parser
        class MyHTMLParser(html.parser.HTMLParser):
            def __init__(self, *, convert_charrefs: bool = True) -> None:
                html.parser.HTMLParser.__init__(self, convert_charrefs=convert_charrefs)
                self.found: List[JSONDict] = []
                self.th: List[str] = []
                self.td: List[JSONItem] = []
                self.val: Optional[str] = None
                self.th2: List[str] = []
                self.td2: List[JSONItem] = []
                self.val2: Optional[str] = None
            def tr(self) -> Iterator[JSONDict]:
                found = self.found.copy()
                self.found = []
                for record in found:
                    yield record
            def handle_data(self, data: str) -> None:
                tagged = self.get_starttag_text() or ""
                if tagged.startswith("<th"):
                    self.val = data
                if tagged.startswith("<td"):
                    self.val = data
                if tagged.startswith("<br"):
                    self.val2 = data
            def handle_endtag(self, tag: str) -> None:
                if tag == "th":
                    self.th += [self.val or str(len(self.th) + 1)]
                    self.val = None
                    if self.val2:
                        self.th2 += [self.val2 or str(len(self.th2) + 1)]
                        self.val2 = None
                if tag == "td":
                    tagged = self.get_starttag_text() or ""
                    val = self.val
                    if "right" in tagged and val and val.startswith(" "):
                        val = val[1:]
                    self.td += [val]
                    self.val = None
                    if self.val2:
                        self.td2 += [self.val2 or str(len(self.td2) + 1)]
                        self.val2 = None
                if tag == "tr" and self.td:
                    made = zip(self.th, self.td)
                    item = dict(made)
                    if self.th2:
                        made2 = zip(self.th2, self.td2)
                        item.update(dict(made2))
                    self.found += [item]
                    self.td = []
                    self.td2 = []
        parser = MyHTMLParser(convert_charrefs=self.convert_charrefs)
        for row in rows:
            parser.feed(row)
            for record in parser.tr():
                for key, val in record.items():
                    if isinstance(val, str):
                        record[key] = self.convert.toJSONItem(val)
                yield record

# ================================= #### JSON
class FormatJSON(BaseFormatJSONItem):
    def __init__(self, formats: Dict[str, str] = {}, datedelim: str = '-'):
        BaseFormatJSONItem.__init__(self, formats)
        self.floatfmt = FLOATFMT
        self.datedelim = datedelim
        self.None_String = "null"
    def __call__(self, col: str, val: JSONItem) -> str:
        if val is None:
            return self.None_String
        if isinstance(val, float):
            return self.floatfmt % val
        if isinstance(val, (Date, Time)):
            return '"%s"' % self.item(val)
        return json.dumps(val)

def tabToJSONx(result: Union[JSONList, JSONDict, DataList, DataItem],  # ..
               sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
               *, datedelim: str = '-', legend: LegendList = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToJSON(results, sorts, selects, formats, datedelim=datedelim, legend=legend)
def tabToJSON(result: Iterable[JSONDict],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
              *, datedelim: str = '-', legend: LegendList = [],  #
              reorder: ColSortList = []) -> str:
    filtered: Dict[str, str] = {}
    selected: List[str] = []
    for selec in [sel if "@" not in sel else sel.split("@", 1)[0] for sel in selects]:
        if ":" in selec:
            name, form = selec.split(":", 1)
            if isinstance(formats, dict):
                formats[name] = form if "{" in form else ("{:" + form + "}")
        else:
            name = selec
        if "<" in name:
            name, cond = name.split(">", 1)
            filtered[name] = ">" + cond
        elif ">" in name:
            name, cond = name.split("<", 1)
            filtered[name] = "<" + cond
        elif "~" in name:
            name, cond = name.split("=", 1)
            filtered[name] = "=" + cond
        selected.append(selec)
    format: FormatJSONItem
    if isinstance(formats, FormatJSONItem):
        format = formats
    else:
        format = FormatJSON(formats, datedelim=datedelim)
    if legend:
        logg.debug("legend is ignored for JSON output")
    sortkey = ColSortCallable(sorts, reorder)
    sortrow = RowSortCallable(sorts, datedelim)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for item in result:
        row: JSONDict = {}
        for name, value in item.items():
            if selected and name not in selected and "*" not in selected:
               continue
            try:
                if name in filtered and unmatched(value, filtered[name]):
                    continue
            except: pass
            row[name] = value
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
        rows.append(row)
    lines = []
    for item in sorted(rows, key=sortrow):
        values: JSONDict = {}
        for name, value in item.items():
            values[name] = format(name, value)
        line = ['"%s": %s' % (name, values[name]) for name in sorted(cols.keys(), key=sortkey) if name in values]
        lines.append(" {" + ", ".join(line) + "}")
    return "[\n" + ",\n".join(lines) + "\n]"

def readFromJSON(filename: str, datedelim: str = '-') -> JSONList:
    parser = DictParserJSON(datedelim)
    return list(parser.load(filename))
def loadJSON(text: str, datedelim: str = '-') -> JSONList:
    parser = DictParserJSON(datedelim)
    return list(parser.loads(text))

class DictParserJSON(DictParser):
    def __init__(self, datedelim: str = '-') -> None:
        self.convert = ParseJSONItem(datedelim)
    def read(self, rows: Iterable[str], newline: str = '\n') -> Iterator[JSONDict]:
        return self.loads(newline.join(rows))
    def loads(self, text: str) -> Iterator[JSONDict]:
        jsondata = json.loads(text)
        data: List[JSONDict] = jsondata
        for record in data:
            for key, val in record.items():
                if isinstance(val, str):
                    record[key] = self.convert.toDate(val)
            yield record
    def load(self, filename: str) -> Iterator[JSONDict]:
        jsondata = json.load(open(filename))
        data: List[JSONDict] = jsondata
        for record in data:
            for key, val in record.items():
                if isinstance(val, str):
                    record[key] = self.convert.toDate(val)
            yield record

# ================================= #### YAML
class FormatYAML(FormatJSON):
    def __init__(self, formats: Dict[str, str] = {}, datedelim: str = '-'):
        FormatJSON.__init__(self, formats, datedelim)
    def __call__(self, col: str, val: JSONItem) -> str:
        if val is None:
            return self.None_String
        if isinstance(val, (Date, Time)):
            return '%s' % self.item(val)
        return FormatJSON.__call__(self, col, val)

def tabToYAMLx(result: Union[JSONList, JSONDict, DataList, DataItem],  # ..
               sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
               *, datedelim: str = '-', legend: LegendList = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToYAML(results, sorts, formats, datedelim=datedelim, legend=legend)
def tabToYAML(result: Iterable[JSONDict],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
              *, datedelim: str = '-', legend: LegendList = [],  #
              reorder: ColSortList = []) -> str:
    filtered: Dict[str, str] = {}
    selected: List[str] = []
    for selec in [sel if "@" not in sel else sel.split("@", 1)[0] for sel in selects]:
        if ":" in selec:
            name, form = selec.split(":", 1)
            if isinstance(formats, dict):
                formats[name] = form if "{" in form else ("{:" + form + "}")
        else:
            name = selec
        if "<" in name:
            name, cond = name.split(">", 1)
            filtered[name] = ">" + cond
        elif ">" in name:
            name, cond = name.split("<", 1)
            filtered[name] = "<" + cond
        elif "~" in name:
            name, cond = name.split("=", 1)
            filtered[name] = "=" + cond
        selected.append(selec)
    format: FormatJSONItem
    if isinstance(formats, FormatJSONItem):
        format = formats
    else:
        format = FormatYAML(formats, datedelim=datedelim)
    if legend:
        logg.debug("legend is ignored for YAML output")
    sortkey = ColSortCallable(sorts, reorder)
    sortrow = RowSortCallable(sorts, datedelim)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for item in result:
        row: JSONDict = {}
        for name, value in item.items():
            if selected and name not in selected and "*" not in selected:
               continue
            try:
                if name in filtered and unmatched(value, filtered[name]):
                    continue
            except: pass 
            row[name] = value
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
        rows.append(row)
    is_simple = re.compile("^\\w[\\w_-]*$")
    def as_name(name: str) -> str:
        return (name if is_simple.match(name) else '"%s"' % name)
    lines = []
    for item in sorted(rows, key=sortrow):
        values: JSONDict = {}
        for name, value in item.items():
            values[name] = format(name, value)
        line = ['%s: %s' % (as_name(name), values[name]) for name in sorted(cols.keys(), key=sortkey) if name in values]
        lines.append("- " + "\n  ".join(line))
    return "data:\n" + "\n".join(lines) + "\n"

def loadYAML(text: str, datedelim: str = '-') -> JSONList:
    parser = DictParserYAML(datedelim=datedelim)
    return list(parser.loads(text))
def readFromYAML(filename: str, datedelim: str = '-') -> JSONList:
    parser = DictParserYAML(datedelim=datedelim)
    return list(parser.load(filename))
def DictReaderYAML(rows: Iterable[str], *, datedelim: str = '-') -> Iterator[JSONDict]:
    parser = DictParserYAML(datedelim=datedelim)
    return parser.read(rows)

class DictParserYAML(DictParser):
    def __init__(self, *, datedelim: str = '-') -> None:
        self.convert = ParseJSONItem(datedelim)
        self.convert.None_String = "null"
        self.convert.True_String = "true"
        self.convert.False_String = "false"
    def load(self, filename: str) -> Iterator[JSONDict]:
        return self.read(open(filename))
    def loads(self, text: str) -> Iterator[JSONDict]:
        return self.read(text.splitlines())
    def read(self, rows: Iterable[str]) -> Iterator[JSONDict]:
        at = "start"
        record: JSONDict = {}
        for row in rows:
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
                    yield record
                    record = {}
                line = line.strip()[1:]
            m = re.match(r" *(\w[\w\d.-]*) *: *\"([^\"]*)\" *", line)
            if m:
                record[m.group(1)] = m.group(2)
                continue
            m = re.match(r" *(\w[\w\d.-]*) *: *(.*)", line)
            if m:
                record[m.group(1)] = self.convert.toJSONItem(m.group(2).strip())
                continue
            m = re.match(r" *\"([^\"]+)\" *: *\"([^\"]*)\" *", line)
            if m:
                record[m.group(1)] = m.group(2)
                continue
            m = re.match(r" *\"([^\"]+)\" *: *(.*)", line)
            if m:
                record[m.group(1)] = self.convert.toJSONItem(m.group(2).strip())
                continue
            logg.error("can not parse: %s", line)
        # end for
        if record:
            yield record

# ================================= #### TOML
class FormatTOML(FormatJSON):
    def __init__(self, formats: Dict[str, str] = {}, datedelim: str = '-'):
        FormatJSON.__init__(self, formats, datedelim)
    def __call__(self, col: str, val: JSONItem) -> str:
        if val is None:
            return self.None_String
        if isinstance(val, (Date, Time)):
            return '%s' % self.item(val)
        return FormatJSON.__call__(self, col, val)

def tabToTOMLx(result: Union[JSONList, JSONDict, DataList, DataItem],  # ..
               sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
               *, datedelim: str = '-', legend: LegendList = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToTOML(results, sorts, formats, selects, datedelim=datedelim, legend=legend)
def tabToTOML(result: Iterable[JSONDict],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
              *, datedelim: str = '-', legend: LegendList = [],  #
              reorder: ColSortList = []) -> str:
    filtered: Dict[str, str] = {}
    selected: List[str] = []
    for selec in [sel if "@" not in sel else sel.split("@", 1)[0] for sel in selects]:
        if ":" in selec:
            name, form = selec.split(":", 1)
            if isinstance(formats, dict):
                formats[name] = form if "{" in form else ("{:" + form + "}")
        else:
            name = selec
        if "<" in name:
            name, cond = name.split(">", 1)
            filtered[name] = ">" + cond
        elif ">" in name:
            name, cond = name.split("<", 1)
            filtered[name] = "<" + cond
        elif "~" in name:
            name, cond = name.split("=", 1)
            filtered[name] = "=" + cond
        selected.append(selec)
    format: FormatJSONItem
    if isinstance(formats, FormatJSONItem):
        format = formats
    else:
        format = FormatTOML(formats, datedelim=datedelim)
    if legend:
        logg.debug("legend is ignored for TOML output")
    sortkey = ColSortCallable(sorts, reorder)
    sortrow = RowSortCallable(sorts, datedelim)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for item in result:
        row: JSONDict = {}
        for name, value in item.items():
            if selected and name not in selected and "*" not in selected:
               continue
            try:
                if name in filtered and unmatched(value, filtered[name]):
                    continue
            except: pass 
            row[name] = value
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
        rows.append(row)
    is_simple = re.compile("^\\w[\\w_-]*$")
    def as_name(name: str) -> str:
        return (name if is_simple.match(name) else '"%s"' % name)
    lines = []
    for item in sorted(rows, key=sortrow):
        values: JSONDict = {}
        for name, value in item.items():
            if value is not None:
                values[name] = format(name, value)
        line = ['%s = %s' % (as_name(name), values[name]) for name in sorted(cols.keys(), key=sortkey) if name in values]
        lines.append("[[data]]\n" + "\n".join(line))
    return "\n".join(lines) + "\n"

def loadTOML(text: str, datedelim: str = '-') -> JSONList:
    parser = DictParserTOML(datedelim=datedelim)
    return list(parser.loads(text))
def readFromTOML(filename: str, datedelim: str = '-') -> JSONList:
    parser = DictParserTOML(datedelim=datedelim)
    return list(parser.load(filename))

class DictParserTOML(DictParser):
    def __init__(self, *, datedelim: str = '-') -> None:
        self.convert = ParseJSONItem(datedelim)
        self.convert.None_String = "null"
        self.convert.True_String = "true"
        self.convert.False_String = "false"
    def load(self, filename: str) -> Iterator[JSONDict]:
        return self.read(open(filename))
    def loads(self, text: str) -> Iterator[JSONDict]:
        return self.read(text.splitlines())
    def read(self, rows: Iterable[str]) -> Iterator[JSONDict]:
        at = "start"
        record: JSONDict = {}
        for row in rows:
            line = row.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[[data]]"):
                if at == "start":
                    at = "data"
                if record:
                    yield record
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
                record[m.group(1)] = self.convert.toJSONItem(m.group(2).strip())
                continue
            m = re.match(r" *\"([^\"]+)\" *= *\"([^\"]*)\" *", line)
            if m:
                record[m.group(1)] = m.group(2)
                continue
            m = re.match(r" *\"([^\"]+)\" *= *(.*)", line)
            if m:
                record[m.group(1)] = self.convert.toJSONItem(m.group(2).strip())
                continue
            logg.error("can not parse: %s", line)
        # end for
        if record:
            yield record

# ================================= #### TOML
class FormatCSV(NumFormatJSONItem):
    def __init__(self, formats: Dict[str, str] = {}, datedelim: str = '-'):
        NumFormatJSONItem.__init__(self, formats, datedelim)

class xFormatCSV(NumFormatJSONItem):
    def __init__(self, formats: Dict[str, str] = {}, datedelim: str = '-'):
        BaseFormatJSONItem.__init__(self, formats)
        self.formats = formats
        self.datedelim = datedelim
        self.floatfmt = FLOATFMT
    def __call__(self, col: str, val: JSONItem) -> str:
        if col in self.formats:
            if "{:" in self.formats[col]:
                try:
                    return self.formats[col].format(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", self.formats[col], e)
            if "%s" in self.formats[col]:
                try:
                    return self.formats[col] % self.item(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", self.formats[col], e)
            logg.debug("unknown format '%s' for col '%s'", self.formats[col], col)
        if isinstance(val, (Date, Time)):
            return '%s' % strJSONItem(val, self.datedelim)
        if isinstance(val, float):
            return self.floatfmt % val
        return self.item(val)

def tabToCSVx(result: Union[JSONList, JSONDict, DataList, DataItem],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
              *, datedelim: str = '-', noheaders: bool = False,  #
              legend: LegendList = []) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToCSV(results, sorts, formats, selects, datedelim=datedelim, noheaders=noheaders, legend=legend)
def tabToCSV(result: Iterable[JSONDict], # ..
             sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
             *, datedelim: str = '-', noheaders: bool = False, legend: LegendList = [], tab: str = ";",
             reorder: ColSortList = []) -> str:
    filtered: Dict[str, str] = {}
    selected: List[str] = []
    for selec in [sel if "@" not in sel else sel.split("@", 1)[0] for sel in selects]:
        if ":" in selec:
            name, form = selec.split(":", 1)
            if isinstance(formats, dict):
                formats[name] = form if "{" in form else ("{:" + form + "}")
        else:
            name = selec
        if "<" in name:
            name, cond = name.split(">", 1)
            filtered[name] = ">" + cond
        elif ">" in name:
            name, cond = name.split("<", 1)
            filtered[name] = "<" + cond
        elif "~" in name:
            name, cond = name.split("=", 1)
            filtered[name] = "=" + cond
        selected.append(selec)
    format: FormatJSONItem
    if isinstance(formats, FormatJSONItem):
        format = formats
    else:
        format = FormatCSV(formats, datedelim=datedelim)
    if legend:
        logg.debug("legend is ignored for CSV output")

    sortkey = ColSortCallable(sorts, reorder)
    sortrow = RowSortCallable(sorts, datedelim)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for num, item in enumerate(result):           
        row: JSONDict = {}
        if "#" in selected:
            row["#"] = num
        for name, value in item.items():
            if selected and name not in selected and "*" not in selected:
               continue
            try:
                if name in filtered and unmatched(value, filtered[name]):
                    continue
            except: pass
            row[name] = value
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
        rows.append(row)
    lines = []
    for item in sorted(rows, key=sortrow):
        values: JSONDict = dict([(name, _None_String) for name in cols.keys()])
        for name, value in item.items():
            values[name] = format(name, value)
        lines.append(values)
    import csv
    # csvfile = open(csv_filename, "w")
    csvfile = StringIO()
    writer = csv.DictWriter(csvfile, fieldnames=sorted(cols.keys(), key=sortkey), restval='ignore',
                            quoting=csv.QUOTE_MINIMAL, delimiter=tab)
    if not noheaders:
        writer.writeheader()
    for line in lines:
        writer.writerow(line)
    return csvfile.getvalue()

def readFromCSV(filename: str, datedelim: str = '-', tab: str = ";") -> JSONList:
    parser = DictParserCSV(datedelim=datedelim, tab=tab)
    return list(parser.load(filename))
def loadCSV(text: str, datedelim: str = '-', tab: str = ";") -> JSONList:
    parser = DictParserCSV(datedelim=datedelim, tab=tab)
    return list(parser.loads(text))

class DictParserCSV(DictParser):
    def __init__(self, *, datedelim: str = '-', tab: str = ";") -> None:
        self.convert = ParseJSONItem(datedelim)
        self.tab = tab
    def load(self, filename: str, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        return self.reads(open(filename), tab=tab)
    def loads(self, text: str, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        return self.reads(StringIO(text), tab=tab)
    def reads(self, csvfile: TextIOWrapper, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        tab = tab if tab is not None else self.tab
        import csv
        for row in csv.DictReader(csvfile, restval='ignore',
                                  quoting=csv.QUOTE_MINIMAL, delimiter=tab):
            newrow: JSONDict = dict(row)
            for key, val in newrow.items():
                if isinstance(val, str):
                    newrow[key] = self.convert.toJSONItem(val)
            yield newrow

def tabToFMTx(output: str, result: Union[JSONList, JSONDict, DataList, DataItem], # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
              *, datedelim: str = '-', legend: LegendList = [], combine: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToFMT(output, results, sorts, formats, selects, datedelim=datedelim, legend=legend, combine=combine)
def tabToFMT(fmt: str, result: JSONList,  # ..
             sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
             *, datedelim: str = '-', legend: LegendList = [],  #
             reorder: ColSortList = [], combine: Dict[str, str] = {}) -> str:
    fmt = fmt or ""
    if fmt.lower() in ["md", "markdown"]:
        return tabToGFM(result, sorts, formats, selects, reorder=reorder, legend=legend)
    if fmt.lower() in ["html", "htm"]:
        return tabToHTML(result, sorts, formats, selects, reorder=reorder, legend=legend, combine=combine)
    if fmt.lower() in ["json", "jsn"]:
        return tabToJSON(result, sorts, formats, selects, reorder=reorder, datedelim=datedelim)
    if fmt.lower() in ["yaml", "yml"]:
        return tabToYAML(result, sorts, formats, selects, reorder=reorder, datedelim=datedelim)
    if fmt.lower() in ["toml", "tml"]:
        return tabToTOML(result, sorts, formats, selects, reorder=reorder, datedelim=datedelim)
    if fmt.lower() in ["wide"]:
        return tabToGFM(result, sorts, formats, selects, reorder=reorder, tab='')
    if fmt.lower() in ["text"]:
        return tabToGFM(result, sorts, formats, selects, reorder=reorder, tab='', noheaders=True)
    if fmt.lower() in ["tabs"]:
        return tabToGFM(result, sorts, formats, selects, reorder=reorder, tab='\t')
    if fmt.lower() in ["tab"]:
        return tabToCSV(result, sorts, formats, selects, reorder=reorder, datedelim=datedelim, tab='\t')
    if fmt.lower() in ["data"]:
        return tabToCSV(result, sorts, formats, selects, reorder=reorder, datedelim=datedelim, tab='\t', noheaders=True)
    if fmt.lower() in ["ifs", "dat"]:
        return tabToCSV(result, sorts, formats, selects, reorder=reorder, datedelim=datedelim, tab=os.environ.get("IFS", "\t"), noheaders=True)
    if fmt.lower() in ["csv", "scsv"]:
        return tabToCSV(result, sorts, formats, selects, reorder=reorder, datedelim=datedelim, tab=';')
    if fmt.lower() in ["list"]:
        return tabToCSV(result, sorts, formats, selects, reorder=reorder, datedelim=datedelim, tab=';', noheaders=True)
    if fmt.lower() in ["xlsx", "xls"]:
        return tabToCSV(result, sorts, formats, selects, reorder=reorder, datedelim=datedelim, tab=',')
    return tabToGFM(result, sorts, formats, selects, reorder=reorder, legend=legend)

def saveToFMT(filename: str, fmt: str, result: JSONList,  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selects: List[str] = [],  # ..
              *, datedelim: str = '-', legend: LegendList = [], reorder: ColSortList = []) -> str:
    fmt = fmt or detectfileformat(filename) or ""
    dat = tabToFMT(fmt, result, sorts, formats, selects, datedelim=datedelim, legend=legend, reorder=reorder)
    if filename:
        with open(filename, "w") as f:
            f.write(dat)
        return filename
    return NIX

def editprog() -> str:
    return os.environ.get("EDIT", "mcedit")
def htmlprog() -> str:
    return os.environ.get("BROWSER", "chrome")
def xlsxprog() -> str:
    return os.environ.get("XLSVIEW", "oocalc")
def viewFMT(fmt: str) -> str:
    if fmt in ["xls", "xlsx"]:
        return xlsxprog()
    if fmt in ["htm", "html"]:
        return htmlprog()
    return editprog()

def detectfileformat(filename: str) -> Optional[str]:
    _, ext = os.path.splitext(filename.lower())
    if ext in [".txt", ".md", ".markdown"]:
        return "md"
    if ext in [".csv", ".scsv"]:
        return "csv"
    if ext in [".dat", ".tcsv"]:
        return "tab"
    if ext in [".jsn", ".json"]:
        return "json"
    if ext in [".yml", ".yaml"]:
        return "yaml"
    if ext in [".tml", ".toml"]:
        return "toml"
    if ext in [".htm", ".html", ".xhtml"]:
        return "html"
    if ext in [".xls", ".xlsx"]:
        return "xlsx"
    return None
def detectcontentformat(filename: str) -> Optional[str]:
    first = b""
    with open(filename, "rb") as f:
        for x in range(255):
            c = f.read(1)
            if not c:
                break
            if c in [b"|"]:
                return "md"
            if c in [b";"]:
                return "csv"
            if c in [b"\t"]:
                return "tab"
            if c in [b"<"]:
                return "html"
            if c in [b"{"]:
                return "json"
            if c in [b":"]:
                return "yaml"
            if c in [b"["]:
                return "toml"
            if c.isalnum() or ord(c) <= 0x20:
                logg.debug("buff %c [%i]", ord(c), ord(c))
                first += c
                if first == b"PK\03\04":
                    return "xlsx"
                continue
            else:
                logg.debug("skip %c [%i]", ord(c), ord(c))
    return None

def readFromFile(filename: str, fmt: str = NIX, defaultfileformat: str = NIX) -> JSONList:
    if not fmt:
        fmt = detectfileformat(filename) or detectcontentformat(filename) or defaultfileformat
        if not fmt:
            logg.warning("could not detect format of '%s'", filename)
            return []
    # assert fmt
    return readFromFMT(fmt, filename, defaultfileformat)
def readFromFMT(fmt: str, filename: str, defaultformat: str = NIX) -> JSONList:
    if not fmt:
        fmt = detectfileformat(filename) or NIX
        if not fmt:
            fmt = defaultformat
        if not fmt:
            return []
    if fmt.lower() in ["md", "markdown"]:
        return readFromGFM(filename)
    if fmt.lower() in ["html", "htm"]:
        return readFromHTML(filename)
    if fmt.lower() in ["json", "jsn"]:
        return readFromJSON(filename)
    if fmt.lower() in ["yaml", "yml"]:
        return readFromYAML(filename)
    if fmt.lower() in ["toml"]:
        return readFromTOML(filename)
    if fmt.lower() in ["tab"]:
        return readFromCSV(filename, tab='\t')
    if fmt.lower() in ["csv", "scsv"]:
        return readFromCSV(filename, tab=';')
    if fmt.lower() in ["xlsx", "xls"]:
        import tabtoxlsx
        return tabtoxlsx.readFromXLSX(filename)
    logg.debug(" readFromFMT  - unrecognized input format %s: %s", fmt, filename)
    return []

# ----------------------------------------------------------------------
# backporting the select-style outer interface

def _pos_num(pre: str, num: int) -> str:
    if num <= 9:
        return "%s%01i" % (pre, num)
    elif num <= 999:
        return "%s%s%03i" % (pre, pre, num)
    elif num <= 999999:
        return "%s%s%s%06i" % (pre, pre, pre, num)
    else:
        return "%s%s%s%s%09i" % (pre, pre, pre, pre, num)
def _neg_num(pre: str, num: int) -> str:
    if num <= 9:
        return "%s%01i" % (pre, 9 - num)
    elif num <= 999:
        return "%s%s%03i" % (pre, ".", 999 - num)
    elif num <= 999999:
        return "%s%s%06i" % (pre, "..", 999999 - num)
    else:
        return "%s%s%09i" % (pre, "...", 999999999 - num)
class TabColSpec(NamedTuple):
    fields: List[str]
    formats: str
    renamed: str
    reorder: str
    sorting: str
    def title(self, sep: Optional[str] = None) -> str:
        sep = sep or COL_SEP  # "|"
        return self.renamed or sep.join(self.fields)
    def order(self) -> str:
        return self.reorder or self.title()
    def sorts(self) -> str:
        return self.sorting or self.order()
def parse_colspec(header: str, sep: Optional[str] = None) -> TabColSpec:
    """ parse a select-style header - combining field names and formatting """
    sep = sep or COL_SEP  # "|"
    if ":" not in header and "@" not in header and "{" not in header:
        return TabColSpec(header.split(sep), header, "", "", "")
    if ":@" in header:
        formats, renames = header.rsplit(":@", 1)
        if "@" in renames:
            renamed, reorder = renames.rsplit("@", 1)
            if "@" in renamed:
                sorting = reorder
                renamed, reorder = renamed.rsplit("@", 1)
            elif ":" in reorder:
                reorder, sorting = reorder.rsplit(":", 1)
            else:
                sorting = ""
        elif ":" in renames:
            renamed, sorting = renames.rsplit(":", 1)
            reorder = ""
        elif renames.isdigit():
            renamed, reorder, sorting = "", renames, ""
            sorting = ""
        elif renames and renames[0] in "-~" and renames[1:].isdigit():
            renamed, reorder = "", _neg_num("~", int(renames[1:]))
            sorting = ""
        else:
            renamed, reorder, sorting = renames, "", ""
    elif "@" in header:
        parts = header.split("@")
        if len(parts) >= 4:
            sorting = parts[-1]
            reorder = parts[-2]
            renamed = parts[-3]
            formats = "@".join(parts[:-4])
        elif len(parts) == 3:
            reorder = parts[-1]
            renamed = parts[-2]
            formats = parts[-3]
            if ":" in reorder:
                reorder, sorting = reorder.rsplit(":", 1)
            elif reorder.isdigit():
                sorting = ""
            elif reorder and reorder[0] in "-~" and reorder[1:].isdigit():
                reorder = _neg_num("~", int(reorder[1:]))
            else:
                sorting = ""
        elif len(parts) == 2:
            sorting = ""
            formats, renames = parts
            if ":" in renames:
                renamed, sorting = renames.rsplit(":", 1)
                if renamed.isdigit():
                    reorder, renamed = renamed, ""
                else:
                    reorder = ""
            elif renames.isdigit():
                renamed, reorder, sorting = "", renames, ""
            elif renames and renames[0] in "-~" and renames[1:].isdigit():
                sorting = ""
                renamed, reorder = "", _neg_num("~", int(renames[1:]))
            else:
                renamed, reorder, sorting = renames, "", ""
        else:  # unreachable
            formats = header
            renamed, reorder, sorting = "", "", ""

    else:
        formats = header
        reorder, renamed, sorting = "", "", ""
    fields: List[str] = []
    if "{" in formats and "}" in formats and "{:" not in formats:
        # we need to parse the formatter to get the field names
        parts = formats.split("{")
        renames = ""
        for part in parts:
            if "}" in part:
                spec, rest = part.split("}", 1)
                if ":" in spec:
                    field, _ = spec.split(":", 1)
                else:
                    field = spec
                fields += [field]
                if not renames:
                    renames = field
                else:
                    renames += sep + field
        if not renamed:
            renamed = renames
    else:
        for part in formats.split(sep):
            if ":" in part:
                field, _ = part.split(":", 1)
            else:
                field = part
            fields += [field]
    return TabColSpec(fields, formats, renamed, reorder, sorting)

class TabHeaderCols:
    cols: List[TabColSpec]
    fieldspec: Dict[str, List[TabColSpec]]
    sep = COL_SEP
    def __init__(self, headers: List[str], **kwargs: str) -> None:
        self.fieldspec = {}
        self.cols = []
        self.set(headers)
    def set(self, headers: List[str]) -> None:
        cols: Dict[str, TabColSpec] = {}
        for header in headers:
            colspec = parse_colspec(header)
            if not colspec.reorder:
                colspec = colspec._replace(reorder=_pos_num(":", len(cols) + 1))
            cols[colspec.order()] = colspec
            for field in colspec.fields:
                if field not in self.fieldspec:
                    self.fieldspec[field] = []
                self.fieldspec[field].append(colspec)
        self.cols = [cols[order] for order in sorted(cols.keys())]
class TabHeaders(TabHeaderCols):
    def sorts(self) -> List[str]:
        """ convert to old-style tabToFMT(sorts=) """
        spec: Dict[str, str] = {}
        for col in self.cols:
            for num, field in enumerate(col.fields):
                # spec[field] = col.sorts()
                spec["%s %03i %s" % (col.sorts(), num, field)] = field
        return [spec[sorts] for sorts in sorted(spec)]
    def order(self) -> Dict[str, str]:
        """ convert to old-style tabToFMT(sorts=) """
        spec: Dict[str, str] = {}
        for col in self.cols:
            field = col.fields[0]
            spec[field] = col.order()
        return spec
    def formats(self, defaults: TabHeaderCols) -> Dict[str, str]:
        """ convert to old-style TabToFMT(headers=) """
        spec: Dict[str, str] = {}
        sep = self.sep
        for col in self.cols:
            formatlist = col.formats.split(sep)
            for formats in formatlist:
                if ":" in formats:
                    name, form = formats.split(":", 1)
                    if "{" in name:
                        name0, name1 = name.rsplit("{", 1)
                        spec[name1] = name0 + "{:" + form
                    elif "%s" in form:  # fixme: old-style
                        spec[name] = form.replace("%s", "{:s}")
                    elif "{:" in form:  # fixme: old-style
                        spec[name] = form
                    else:
                        # modulo formatting has "d", "i", "u" for decimal numbers
                        form = form.replace("i", "n").replace("u", "n")
                        form = form.replace("r", "s").replace("a", "s")
                        spec[name] = "{:" + form + "}"
        for col in defaults.cols:
            formatlist = col.formats.split(sep)
            for formats in formatlist:
                if ":" in formats:
                    name, form = formats.split(":", 1)
                    if "{" in name:
                        name0, name1 = name.rsplit("{", 1)
                        if name1 not in spec:
                            spec[name1] = name0 + "{:" + form
                    elif "%s" in form:  # fixme: old-style
                        spec[name] = form.replace("%s", "{:s}")
                    elif "{:" in form:  # fixme: old-style
                        spec[name] = form
                    else:
                        # modulo formatting has "d", "i", "u" for decimal numbers
                        form = form.replace("i", "n").replace("u", "n")
                        form = form.replace("r", "s").replace("a", "s")
                        if name not in spec:
                            spec[name] = "{:" + form + "}"
        return spec
    def combine(self) -> Dict[str, str]:
        """ convert to old-style TabToFMT(combine=) """
        spec: Dict[str, str] = {}
        sep = self.sep
        for col in self.cols:
            formatlist = col.formats.split(sep)
            if len(formatlist) > 1:
                formats = formatlist[0]
                if ":" in formats:
                    name, form = formats.split(":", 1)
                    if "{" in name:
                        _, target = name.rsplit("{", 1)
                    else:
                        target = name
                else:
                    target = formats
                for formats in formatlist[1:]:
                    if ":" in formats:
                        name, form = formats.split(":", 1)
                        if "{" in name:
                            _, combine = name.rsplit("{", 1)
                        else:
                            combine = name
                    else:
                        combine = formats
                    spec[target] = combine
        return spec
    def update(self, defaults: TabHeaderCols) -> None:
        """ update formats but keep selection including sorts/orders """
        for old, col in enumerate(self.cols):
            for field in col.fields:
                if field in defaults.fieldspec:
                    fieldspec = defaults.fieldspec[field][0]
                    if ":" in col.formats:
                        pass
                    elif ":" in fieldspec.formats:
                        newcol = col._replace(formats=fieldspec.formats)
                        self.cols[old] = newcol

def print_tabtotext(output: Union[TextIO, str], data: Iterable[JSONDict], # ..
        formats: List[str] = [], selects: List[str] = [], legend: List[str] = [],  # ..
        *, defaultformat: str = "") -> str:
    if isinstance(output, TextIO) or isinstance(output, StringIO):
        out = output
        fmt = defaultformat
        done = "stream"
    elif "." in output:
        fmt = detectfileformat(output) or defaultformat
        out = open(output, "wt", encoding="utf-8")
        done = output
    else:
        fmt = output
        out = sys.stdout
        done = output
    selected = TabHeaders(selects)
    form = TabHeaders(formats)
    form.update(selected)
    logg.info(" cols = %s", "|".join([str(col) for col in form.cols]))
    sorts = form.sorts()
    forms = form.formats(selected)
    selec = selected.order()
    order = form.order()
    combine = form.combine()
    logg.info("sorts = %s", sorts)
    logg.info("forms = %s", forms)
    logg.info("selec = %s", selec)
    logg.info("order = %s", order)
    logg.info("combine = %s", combine)
    results: List[str] = []
    lines = tabToFMT(fmt, list(data), sorts, forms, selec, reorder=order, combine=combine, legend=legend)
    for line in lines:
        results.append(line)
        out.write(line)
    return ": %s results %s" % (len(results), done)

# ----------------------------------------------------------------------
def tab_formats_from(columns: str) -> Dict[str, str]:
    styles = {}
    for elem in columns.split(","):
        if elem and ":" in elem:
            name, style = elem.split(":", 1)
            if not name:
                continue
            if "=" in name:
                name = name.split("=", 1)[0]
            if "{:" in style:
                styles[name] = style
            elif style.startswith("%") and len(style) > 1:
                styles[name] = "{:" + style[1:] + "}"
            else:
                styles[name] = "{:" + style + "}"
    return styles

def tab_sorts_from(columns: str) -> List[str]:
    return list(tab_selects_from(columns).keys())

def tab_selects_from(columns: str) -> Dict[str, str]:
    cols = OrderedDict()
    for col in columns.split(","):
        if not col:
            pass
        elif "=" in col:
            name, orig = col.split("=", 1)
            if ":" in orig:
                cols[name] = orig.split(":", 1)[0]
            else:
                cols[name] = orig
        elif ":" in col:
            name, style = col.split(":", 1)
            cols[name] = name
        else:
            cols[col] = col
    return cols


def tabToTabX(data: JSONList, selects: Union[str, Sequence[str], Dict[str, str]] = {}) -> JSONList:
    if isinstance(selects, str):
        return tabToTab(data, tab_selects_from(selects))
    else:
        return tabToTab(data, selects)

def tabToTab(data: JSONList, selects: Union[Sequence[str], Dict[str, str]] = {}) -> JSONList:
    if hasattr(selects, "items"):
        return tabToCustomTab(data, cast(Dict[str, str], selects))
    else:
        return tabToCustomTab(data, dict(zip(selects, selects)))

def tabToCustomTab(data: JSONList, selects: Dict[str, str] = {}) -> JSONList:
    if not selects:
        return data
    newdata: JSONList = []
    for item in data:
        newitem: JSONDict = {}
        for name, col in selects.items():
            if "{" in col and "}" in col:
                newitem[name] = col.format(item)
            elif col in item:
                newitem[name] = item[col]
            elif col in [".", "#"]:
                newitem[name] = len(newdata) + 1
        newdata.append(newitem)
    return newdata

def tabToPrint(result: JSONList, OUTPUT: str = NIX, fmt: str = NIX,  # ...
               sorts: RowSortList = [],  # ...
               formats: FormatsDict = {},  # ...
               selects: Union[Sequence[str], Dict[str, str]] = {},  # ...
               datedelim: str = '-', legend: LegendList = [],  # ...
               reorder: ColSortList = []) -> str:
    data = tabToTab(result, selects)
    FMT = fmt or detectfileformat(OUTPUT) or "md"
    if OUTPUT in ["", "-", "CON"]:
        print(tabToFMT(FMT, data, formats=formats, sorts=sorts, reorder=reorder, datedelim=datedelim, legend=legend))
    elif OUTPUT:
        if FMT in ["xls", "xlsx"]:
            import tabtoxlsx
            if isinstance(formats, FormatJSONItem):
                tabtoxlsx.saveToXLSX(OUTPUT, data, sorts=sorts, reorder=reorder, legend=legend)
            else:
                tabtoxlsx.saveToXLSX(OUTPUT, data, formats=formats, sorts=sorts, reorder=reorder, legend=legend)
        else:
            with open(OUTPUT, "w") as f:
                f.write(tabToFMT(FMT, data, formats=formats, sorts=sorts, reorder=reorder, datedelim=datedelim, legend=legend))
        return "%s written   %s '%s'" % (FMT, viewFMT(FMT), OUTPUT)
    return ""

def tabToPrintWith(result: JSONList, output: str = NIX, fmt: str = NIX,  # ...
                   sorts: Union[str, RowSortList] = NIX,  # ...
                   formats: Union[str, FormatsDict] = NIX,  # ...
                   *, selects: str = NIX,  # ...
                   datedelim: str = '-', legend: LegendList = [],  # ...
                   reorder: ColSortList = []) -> str:
    sorts2: RowSortList = []
    if isinstance(sorts, str):
        sorts2 = tab_sorts_from(sorts)
    else:
        sorts2 = sorts
    formats2: FormatsDict = {}
    if isinstance(formats, FormatJSONItem):
        formats2 = formats
    elif isinstance(formats, str):
        formats2 = tab_formats_from(formats)
        if selects:
            formats2.update(tab_formats_from(selects))
    else:
        formats2 = formats
        if selects:
            formats2.update(tab_formats_from(selects))
    selecs = tab_selects_from(selects)
    if selecs and not reorder:
        reorder = list(selecs.keys())
    logg.info("using formats %s", formats)
    logg.info("using sorts = %s", sorts)
    logg.info("using selecs = %s", selecs)
    return tabToPrint(result, output, fmt, formats=formats2, sorts=sorts2, reorder=reorder, selects=selecs, datedelim=datedelim, legend=legend)

def tabFileToPrintWith(filename: str, fileformat: str, output: str = NIX, fmt: str = NIX,  # ...
                       selects: str = NIX, sorts: Union[str, RowSortList] = NIX,  # ...
                       formats: Union[str, FormatsDict] = NIX,  # ...
                       datedelim: str = '-', legend: LegendList = [],  # ...
                       reorder: ColSortList = []) -> str:
    fileformat = fileformat or detectfileformat(filename) or detectcontentformat(filename) or "md"
    if not fileformat:
        logg.error("could not detect format of '%s'", filename)
        return ""
    logg.info("reading %s %s", fileformat, filename)
    result = readFromFMT(fileformat, filename)
    return tabToPrintWith(result, output, fmt, selects=selects, sorts=sorts, formats=formats, reorder=reorder, datedelim=datedelim, legend=legend)

if __name__ == "__main__":
    DONE = (logging.WARNING + logging.ERROR) // 2
    logging.addLevelName(DONE, "DONE")
    from optparse import OptionParser
    cmdline = OptionParser("%prog [help|filename.json|filename.html]...", epilog=__doc__, version=__version__)
    cmdline.formatter.max_help_position = 30
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="more verbose logging")
    cmdline.add_option("-^", "--quiet", action="count", default=0, help="less verbose logging")
    cmdline.add_option("-S", "--sort-by", "--sort-columns", metavar="LIST", action="append",  # ..
                       help="reorder columns for sorting (a,x)", default=[])
    cmdline.add_option("-L", "--labels", "--label-columns", metavar="LIST", action="append",  # ..
                       help="select columns to show (a,x=b)", default=[])
    cmdline.add_option("-F", "--formats", "--format-columns", metavar="LIST", action="append",  # ..
                       help="apply formatting to columns (a:.2f,b:_d)", default=[])
    cmdline.add_option("-i", "--inputformat", metavar="FMT", help="fix input format (instead of autodetection)", default="")
    cmdline.add_option("-o", "--format", metavar="FMT", help="json|yaml|html|wide|md|htm|tab|csv", default="")
    cmdline.add_option("-O", "--output", metavar="CON", default="-", help="redirect output to filename")
    opt, args = cmdline.parse_args()
    logging.basicConfig(level=max(0, logging.WARNING - 10 * opt.verbose + 10 * opt.quiet))
    if not args:
        cmdline.print_help()
    else:
        for arg in args:
            if arg in ["help"]:
                cmdline.print_help()
                print("\nCommands:")
                previous = ""
                for line in open(__file__):
                    if previous.strip().replace("elif arg", "if arg").startswith("if arg in"):
                        if "#" in line:
                            print(previous.strip().split(" arg in")[1], line.strip().split("#")[1])
                        else:
                            print(previous.strip().split(" arg in")[1], line.strip())
                previous = line
                raise SystemExit()
            # ....
            done = tabFileToPrintWith(arg, opt.inputformat, opt.output, opt.format, selects=",".join(opt.labels),  # ..
                                      sorts=",".join(opt.sort_by), formats=",".join(opt.formats))
            if done:
                logg.log(DONE, " %s", done)
