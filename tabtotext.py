#! /usr/bin/env python3
"""
This script allows to format table-like data (list of dicts).
The various output formats can be read back. The file extension will
usally define the format. ==> ".md" is Github Flavourd Markdown.
".txt" is compressed markdown table, ".wide" is space-only markdown,
".html" is Html Table, ".htm" without table borders, ".xhtml" with xmlns block,
".xlsx" as Excel if openpyxl is available (or tabxlsx fallback),
".tab" is tab-seperated csv, ".tabs" with markdown alignment,
".csv" is semicolon csv, ".list" without headers,
and ".dat" files use $IFS as tabulator (like bash 'read').
"""

__copyright__ = "(C) 2017-2024 Guido Draheim, licensed under the Apache License 2.0"""
__version__ = "1.6.3352"

from typing import Optional, Union, Dict, List, Any, Sequence, Callable, Type, cast, Tuple, Iterable, Iterator, TextIO, NamedTuple
from collections import OrderedDict
from html import escape
from datetime import date as Date
from datetime import datetime as Time
from datetime import timezone as TimeZone
from datetime import timedelta as Plus
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

SECTION = "data"
DATEFMT = "%Y-%m-%d"
TIMEFMT = "%Y-%m-%d.%H%M"
FLOATFMT = "%4.2f"
NORIGHT = False
MINWIDTH = 5
NIX = ""
STRLIST: List[str] = []
COL_SEP = "|"
TABXLSX = False

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

class TabText(NamedTuple):
    data: JSONList
    headers: List[str]

class TabSheet(NamedTuple):
    data: List[JSONDict]
    headers: List[str]
    title: str

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
            return value.astimezone(TimeZone.utc).strftime(datefmt2)
        else:
            return value.strftime(datefmt2)
    if isinstance(value, Date):
        datefmt1 = datefmt if datefmt else DATEFMT
        datefmt2 = datefmt1.replace('-', datedelim)
        return value.strftime(datefmt2)
    return str(value)
def unmatched(value: JSONItem, cond: str) -> bool:
    try:
        if value is None or value is False or value is True:
            if len(cond) >= 2 and cond[:2] in ["==", "=~", "<=", ">="]:
                if cond[2:] in ["1", "True", "true", "yes", "(yes)", "*", "+"]:
                    cond = cond[:2] + "1"
                if cond[2:] in ["0", "False", "false", "no", "(no)", "", "-", "~"]:
                    cond = cond[:2] + "0"
            elif len(cond) >= 1 and cond[:1] in ["<", ">"]:
                if cond[1:] in ["1", "True", "true", "yes", "(yes)", "*", "+"]:
                    cond = cond[:1] + "1"
                if cond[1:] in ["0", "False", "false", "no", "(no)", "", "-", "~"]:
                    cond = cond[:1] + "0"
            if value is True:
                value = 1
            else:
                value = 0
        if isinstance(value, Time) or isinstance(value, Date):
            value = value.strftime(DATEFMT)
        if isinstance(value, int) or isinstance(value, float):
            eps = 0.005  # adding epsilon converts int-value to float-value
            if cond.startswith("=~"):
                return value - eps > float(cond[2:]) or float(cond[2:]) > value + eps
            if cond.startswith("<>"):
                return value - eps < float(cond[2:]) and float(cond[2:]) < value + eps
            if cond.startswith("==") or cond.startswith("=~"):
                return float(value) != float(cond[2:])  # not recommended
            if cond.startswith("<="):
                return value - eps > float(cond[2:])
            if cond.startswith("<"):
                return value + eps >= float(cond[1:])
            if cond.startswith(">="):
                return value + eps < float(cond[2:])
            if cond.startswith(">"):
                return value - eps <= float(cond[1:])
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
        logg.warning("unmatched value %s does not work for cond (*%s)", type(value), cond)
    return False

############################################################
def sec_usec(sec: Optional[str]) -> Tuple[int, int]:
    """ split float value to seconds and microsecond integers"""
    if not sec:
        return 0, 0
    if "." in sec:
        x = float(sec)
        s = int(x)
        u = int((x - s) * 1000000)
        return s, u
    return int(sec), 0

class StrToDate:
    """ parsing iso8601 day formats"""
    def __init__(self, datedelim: str = "-") -> None:
        self.delim = datedelim
        self.is_date = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)[.]?$".replace('-', datedelim))
        self.is_part = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)[^\d].*".replace('-', datedelim))
    def date(self, value: str) -> Optional[Date]:
        got = self.is_date.match(value)
        if got:
            y, m, d = got.group(1), got.group(2), got.group(3)
            return Date(int(y), int(m), int(d))
        return None
    def datepart(self, value: str) -> Optional[Date]:
        got = self.is_part.match(value)
        if got:
            y, m, d = got.group(1), got.group(2), got.group(3)
            return Date(int(y), int(m), int(d))
        return None
    def __call__(self, value: str) -> Union[str, Date, Time]:
        d = self.date(value)
        if d: return d
        p = self.datepart(value)
        if p: return p
        return value
class StrToTime(StrToDate):
    """ parsing iso8601 day or day-and-time formats with zone offsets"""
    def __init__(self, datedelim: str = "-") -> None:
        StrToDate.__init__(self, datedelim)
        self.is_localtime = re.compile(
            r"(\d\d\d\d)-(\d\d)-(\d\d)[.T ](\d\d)[:]?(\d\d)(?:[:](\d\d(?:[.]\d*)?))?$".replace('-', datedelim))
        self.is_zonetime = re.compile(
            r"(\d\d\d\d)-(\d\d)-(\d\d)[.T ](\d\d)[:]?(\d\d)(?:[:](\d\d(?:[.]\d*)?))?[ ]*(Z|UTC|[+-][0-9][0-9])(?:[:]?([0-9][0-9]))?$".replace('-', datedelim))
    def time(self, value: str) -> Optional[Time]:
        got = self.is_localtime.match(value)
        if got:
            y, m, d, H, M, S = got.group(1), got.group(2), got.group(3), got.group(4), got.group(5), got.group(6)
            return Time(int(y), int(m), int(d), int(H), int(M), *sec_usec(S))
        got = self.is_zonetime.match(value)
        if got:
            hh, mm = got.group(7), got.group(8)
            if hh in ["Z", "UTC"]:
                plus = TimeZone.utc
            else:
                plus = TimeZone(Plus(hours=int(hh), minutes=int(mm or 0)))
            y, m, d, H, M, S = got.group(1), got.group(2), got.group(3), got.group(4), got.group(5), got.group(6)
            return Time(int(y), int(m), int(d), int(H), int(M), *sec_usec(S), tzinfo=plus)
        return None
    def __call__(self, value: str) -> Union[str, Date, Time]:
        d = self.date(value)
        if d: return d
        t = self.time(value)
        if t: return t
        return value


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
            if self.formats[col].startswith("{: "):
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
        self.is_int = re.compile(r"([+-]?\d+)$")
        self.is_float = re.compile(r"([+-]?\d+)(?:[.]\d*)?(?:e[+-]?\d+)?$")
        self.is_float_with_frac = re.compile(float_with_frac)
        self.is_float_with_hours = re.compile(float_with_hours)
        self.datedelim = datedelim
        self.None_String = _None_String
        self.False_String = _False_String
        self.True_String = _True_String
        self.toDate = StrToTime(datedelim)
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
                # numbers before empty before strings
                if "@" in sort:
                    col, rename = sort.split("@", 1)
                else:
                    col = sort
                if col in item:
                    value = item[col]
                    if value is None:
                        sortvalue += "\n?"
                    elif value is False:
                        sortvalue += "\n"
                    elif value is True:
                        sortvalue += "\n!"
                    elif isinstance(value, int):
                        val = "%i" % value
                        sortvalue += "\n" + (":" * len(val)) + val
                    elif isinstance(value, float):
                        val = "%.6f" % value
                        sortvalue += "\n" + (":" * val.index(".")) + val
                    elif isinstance(value, Time):
                        sortvalue += "\n" + value.strftime("%Y%m%d.%H%MS")
                    elif isinstance(value, Date):
                        sortvalue += "\n" + value.strftime("%Y%m%d")
                    else:
                        sortvalue += "\n" + str(value)
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
                    num = sortheaders.index(header)
                    return ("@" * len(str(num)) + str(num))
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
            if fmt.startswith("{:") and fmt[-1] == "}" and "%s" in fmt:
                fmt = fmt[2:-1].replace("%s", "{:s}")
            if fmt.startswith("{:%") and fmt[-1] == "}" and fmt[-2] in "sf":
                fmt = fmt.replace("{:%", "{:")
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
              sorts: Sequence[str] = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
              *, noheaders: bool = False, legend: LegendList = [], tab: str = "|", padding: str = " ",
              section: str = NIX) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)
    return tabToGFM(results, sorts, formats, selected, noheaders=noheaders, legend=legend, tab=tab, padding=padding, section=section)
def tabToGFM(result: Iterable[JSONDict],  # ..
             sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
             *, noheaders: bool = False, legend: LegendList = [], tab: str = "|", padding: str = " ",
             section: str = NIX, reorder: ColSortList = []) -> str:
    """ old-style RowSortList and FormatsDict assembled into headers with microsyntax """
    headers: List[str] = []
    sorting: RowSortList = []
    formatter: FormatsDict = {}
    if isinstance(sorts, Sequence) and isinstance(formats, dict):
        sortheaders: List[str] = []
        for header in sorts:
            cols: List[str] = []
            for headercol in header.split("|"):
                if "@" in headercol:
                    name, suffix = headercol.split("@", 1)
                    if suffix:
                        renames = "@" + suffix
                else:
                    name, renames = headercol, ""
                sortheaders += [name]
                if name in formats:
                    cols += [name + ":" + formats[name] + renames]
                else:
                    cols += [name + renames]
            headers += ["|".join(cols)]
        logg.info("headers = %s", headers)
        logg.info("sorting = %s", sortheaders)
        sorting = sortheaders
    else:
        sorting = sorts
        formatter = formats
    return tabtoGFM(result, headers, selected, legend=legend,  # ..
                    noheaders=noheaders, tab=tab, padding=padding,  # ..
                    section=section, reorder=reorder, sorts=sorting, formatter=formatter)

def tabtoGFM(data: Iterable[JSONDict], headers: List[str] = [], selected: List[str] = [],  # ..
             *, legend: LegendList = [], minwidth: int = 0, noheaders: bool = False, unique: bool = False,
             tab: str = "|", padding: str = " ", section: str = NIX,
             reorder: ColSortList = [], sorts: RowSortList = [], formatter: FormatsDict = {}) -> str:
    logg.debug("tabtoGFM:")
    minwidth = minwidth or MINWIDTH
    renameheaders: Dict[str, str] = {}
    showheaders: List[str] = []
    sortheaders: List[str] = []
    formats: Dict[str, str] = {}
    combine: Dict[str, List[str]] = {}
    freehdrs: Dict[str, str] = {}
    for header in headers:
        combines = ""
        for headercol in header.split("|"):
            if "@" in headercol:
                selcol, rename = headercol.split("@", 1)
            else:
                selcol, rename = headercol, ""
            if "{" in selcol and "{:" not in selcol:
                names3: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon3, brace3 = freepart.find(":"), freepart.find("}")
                    if brace3 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end3 = brace3 if colon3 == -1 else min(colon3, brace3)
                    name3 = freepart[:end3]
                    names3.append(name3)
                name = " ".join(names3)
                freehdrs[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            showheaders += [name]  # headers make a default column order
            if rename:
                sortheaders += [name]  # headers does not sort anymore
            if not combines:
                combines = name
            elif combines not in combine:
                combine[combines] = [name]
            elif name not in combine[combines]:
                combine[combines] += [name]
            if rename:
                renameheaders[name] = rename
    logg.debug("renameheaders = %s", renameheaders)
    logg.debug("sortheaders = %s", sortheaders)
    logg.debug("formats = %s", formats)
    logg.debug("combine = %s", combine)
    logg.debug("freehdrs = %s", freehdrs)
    combined: Dict[str, List[str]] = {}
    renaming: Dict[str, str] = {}
    filtered: Dict[str, str] = {}
    selcols: List[str] = []
    freecols: Dict[str, str] = {}
    for selecheader in selected:
        combines = ""
        for selec in selecheader.split("|"):
            if "@" in selec:
                selcol, rename = selec.split("@", 1)
            else:
                selcol, rename = selec, ""
            if "{" in selcol and "{:" not in selcol:
                names4: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon4, brace4 = freepart.find(":"), freepart.find("}")
                    if brace4 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end4 = brace4 if colon4 == -1 else min(colon4, brace4)
                    name4 = freepart[:end4]
                    names4.append(name4)
                name = " ".join(names4)
                freecols[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                fmts = form if "{" in form else ("{:" + form + "}")
                formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            if "<" in name:
                name, cond = name.split("<", 1)
                filtered[name] = "<" + cond
            elif ">" in name:
                name, cond = name.split(">", 1)
                filtered[name] = ">" + cond
            elif "=" in name:
                name, cond = name.split("=", 1)
                filtered[name] = "=" + cond
            selcols.append(name)
            if rename:
                renaming[name] = rename
            if not combines:
                combines = name
            elif combines not in combined:
                combined[combines] = [name]
            elif combines not in combined[combines]:
                combined[combines] += [name]
    logg.debug("combined = %s", combined)
    logg.debug("renaming = %s", renaming)
    logg.debug("filtered = %s", filtered)
    logg.debug("selcols = %s", selcols)
    logg.debug("freecols = %s", freecols)
    if not selected:
        combined = combine  # argument
        freecols = freehdrs
        renaming = renameheaders
        logg.debug("combined : %s", combined)
        logg.debug("freecols : %s", freecols)
        logg.debug("renaming : %s", renaming)
    newsorts: Dict[str, str] = {}
    colnames: Dict[str, str] = {}
    for name, rename in renaming.items():
        if "@" in rename:
            newname, newsort = rename.split("@", 1)
        elif rename and rename[0].isalpha():
            newname, newsort = rename, ""
        else:
            newname, newsort = "", rename
        if newname:
            colnames[name] = newname
            if name in formats:
                formats[newname] = formats[name]
        if newsort:
            newsorts[name] = newsort
    logg.debug("newsorts = %s", newsorts)
    logg.debug("colnames = %s", colnames)
    if sorts:
        sortcolumns = sorts
    else:
        sortcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols or sortheaders)]
        if newsorts:
            for num, name in enumerate(sortcolumns):
                if name not in newsorts:
                    newsorts[name] = ("@" * len(str(num)) + str(num))
            sortcolumns = sorted(newsorts, key=lambda x: newsorts[x])
            logg.debug("sortcolumns : %s", sortcolumns)
        else:
            logg.debug("sortcolumns = %s", sortcolumns)
    format: FormatJSONItem
    if formatter and isinstance(formatter, FormatJSONItem):
        format = formatter
    else:
        logg.debug("formats = %s | tab=%s", formats, tab)
        format = FormatGFM(formats, tab=tab)
    selcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols)]
    selheaders = [(name if name not in colnames else colnames[name]) for name in (showheaders)]
    sortkey = ColSortCallable(selcolumns or sorts or selheaders, reorder)
    sortrow = RowSortCallable(sortcolumns)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for num, item in enumerate(data):
        row: JSONDict = {}
        if "#" in selcols:
            row["#"] = num + 1
            cols["#"] = len(str(num + 1))
        skip = False
        for name, value in item.items():
            selname = name
            if name in renameheaders and renameheaders[name] in selcols:
                selname = renameheaders[name]
            if selcols and selname not in selcols and "*" not in selcols:
                continue
            try:
                if name in filtered:
                    skip = skip or unmatched(value, filtered[name])
            except: pass
            colname = selname if selname not in colnames else colnames[selname]
            row[colname] = value
            oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
            cols[colname] = max(oldlen, len(format(colname, value)))
        for freecol, freeformat in freecols.items():
            try:
                freenames = freecol.split(" ")
                freeitem: JSONDict = dict([(freename, _None_String) for freename in freenames])
                for name, value in item.items():
                    itemname = name
                    if name in renameheaders and renameheaders[name] in freenames:
                        itemname = renameheaders[name]
                    if itemname in freenames:
                        freeitem[itemname] = format(name, value)
                value = freeformat.format(**freeitem)
                colname = freecol if freecol not in colnames else colnames[freecol]
                row[colname] = value
                oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
                cols[colname] = max(oldlen, len(value))
            except Exception as e:
                logg.info("formatting '%s' at %s bad for:\n\t%s", freeformat, e, item)
        if not skip:
            rows.append(row)
    ws = ("", " ", "  ", "   ", "    ", "     ", "      ", "       ", "        ")  # " "*(0...8)
    colo = tuple(sorted(cols.keys(), key=sortkey))  # ordered column names
    colw = tuple((cols[col] for col in colo))  # widths of cols ordered
    colr = tuple((format.right(col) for col in colo))  # rightalign of cols ordered
    tab2 = tab[0] + padding if tab else ""
    rtab = padding + tab[1] if len(tab) > 1 else ""
    lines: List[str] = []
    if section:
        lines += [F"## {section}\n"]
    if not noheaders:
        hpad = [(ws[w] if w < 9 else (" " * w)) for w in ((colw[m] - len(col)) for m, col in enumerate(colo))]
        line = [tab2 + (hpad[m] + col if colr[m] else col + hpad[m]) for m, col in enumerate(colo)]
        if rtab:
            lines += [(padding.join(line)) + rtab]
        else:
            lines += [(padding.join(line)).rstrip()]
        if tab and padding:
            seps = ["-" * colw[m] for m, col in enumerate(colo)]
            seperators = [tab2 + (seps[m][:-1] + ":" if colr[m] else seps[m]) for m, col in enumerate(colo)]
            lines += [padding.join(seperators) + rtab]
    old: Dict[str, str] = {}
    same: List[str] = []
    for item in sorted(rows, key=sortrow):
        values: Dict[str, str] = {}
        for name, value in item.items():
            values[name] = format(name, value)
        vals = [values.get(col, _None_String) for col in colo]
        vpad = [(ws[w] if w < 9 else (" " * w)) for w in ((colw[m] - len(vals[m])) for m, col in enumerate(colo))]
        line = [tab2 + (vpad[m] + vals[m] if colr[m] else vals[m] + vpad[m]) for m, col in enumerate(colo)]
        if unique:
            same = [sel for sel in selcols if sel in values and sel in old and values[sel] == old[sel]]
        if not selcols or same != selcols:
            if rtab:
                lines.append((padding.join(line)) + rtab)
            else:
                lines.append((padding.join(line)).rstrip())
        old = values
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

def loadGFM(text: str, datedelim: str = '-', tab: str = '|', section: str = NIX) -> JSONList:
    parser = DictParserGFM(datedelim=datedelim, tab=tab, section=section)
    return list(parser.loads(text))
def readFromGFM(filename: str, datedelim: str = '-', tab: str = '|', section: str = NIX) -> JSONList:
    parser = DictParserGFM(datedelim=datedelim, tab=tab, section=section)
    return list(parser.load(filename))
def tabtextfileGFM(filename: str, datedelim: str = '-', tab: str = '|', section: str = NIX) -> TabText:
    parser = DictParserGFM(datedelim=datedelim, tab=tab, section=section)
    data = list(parser.load(filename))
    return TabText(data, parser.headers)
def tablistfileGFM(filename: str, datedelim: str = '-', tab: str = '|', section: str = NIX) -> List[TabSheet]:
    parser = DictParserGFM(datedelim=datedelim, tab=tab, section=section)
    return parser.loadtablist(filename)
def tablistGFM(text: str, datedelim: str = '-', tab: str = '|', section: str = NIX) -> List[TabSheet]:
    parser = DictParserGFM(datedelim=datedelim, tab=tab, section=section)
    return parser.readtablist(text.splitlines())

class DictParserGFM(DictParser):
    def __init__(self, section: str = NIX, *, datedelim: str = '-', tab: str = '|') -> None:
        self.convert = ParseJSONItem(datedelim)
        self.tab = tab
        self.section = section
        self.headers = STRLIST
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
                    self.headers = cols
                    continue
                if at == "header":
                    newcols = [name.strip() for name in line.split(tab)]
                    if len(newcols) != len(cols):
                        logg.error("header divider has not the same length")
                        at = "data"  # promote anyway
                        continue
                    at = "divider"
                if at == "divider":
                    ok = True
                    for col in newcols:
                        if not col: continue
                        if not re.match(r"^ *:*--*:* *$", col):
                            logg.warning("no header divider: %s", col)
                            ok = False
                    if not ok:
                        at = "data"
                        # fallthrough
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
    def loadtablist(self, filename: str, *, tab: Optional[str] = None) -> List[TabSheet]:
        return self.readtablist(open(filename), tab=tab)
    def readtablist(self, lines: Iterable[str], *, tab: Optional[str] = None) -> List[TabSheet]:
        tab = "|" if tab is None else tab
        tabs: List[TabSheet] = []
        data: List[JSONDict] = []
        # must have headers
        lookingfor = "headers"
        headers: List[str] = []
        title = ""
        for line in lines:
            if not line.strip() or (tab and not line.startswith(tab)):
                if headers:
                    if not title:
                        title = "-%s" % (len(tabs) + 1)
                    tabs.append(TabSheet(data, headers, title))
                    title = ""
                    headers = []
                data = []
                lookingfor = "headers"
                if line.startswith("## "):
                    title = line[3:].strip()
                continue
            vals = line.split(tab)
            if tab:
                del vals[0]
            if lookingfor == "headers":
                headers = [header.strip() for header in vals]
                lookingfor = "divider"
                continue
            elif lookingfor == "divider":
                lookingfor = "data"
                if re.match(r"^ *:*--*:* *$", vals[0]):
                    continue
            record: JSONDict = {}
            for col, val in enumerate(vals):
                v = val.strip()
                if v == _None_String:
                    record[headers[col]] = None
                elif v == _False_String:
                    record[headers[col]] = False
                elif v == _True_String:
                    record[headers[col]] = True
                else:
                    try:
                        record[headers[col]] = int(v)
                    except:
                        record[headers[col]] = self.convert.toDate(v)
            data.append(record)
        if headers:
            if not title:
                title = "-%s" % (len(tabs) + 1)
            tabs.append(TabSheet(data, headers, title))
        return tabs

# ================================= #### HTML
class FormatHTML(NumFormatJSONItem):
    def __init__(self, formats: Dict[str, str] = {}):
        NumFormatJSONItem.__init__(self, formats)

def tabToHTMLx(result: Union[JSONList, JSONDict, DataList, DataItem],  # ..
               sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
               *, legend: LegendList = [], section: str = NIX, combine: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToHTML(results, sorts, formats, selected, legend=legend, section=section, combine=combine)
def tabToHTML(result: Iterable[JSONDict],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
              *, legend: LegendList = [], tab: str = "|", padding: str = " ", xmlns: str = "",
              section: str = NIX, combine: Dict[str, str] = {},  # [target]->[attach]
              reorder: ColSortList = []) -> str:
    """ old-style RowSortList and FormatsDict assembled into headers with microsyntax """
    headers: List[str] = []
    sorting: RowSortList = []
    formatter: FormatsDict = {}
    combined: List[str] = []
    if isinstance(sorts, Sequence) and isinstance(formats, dict):
        sortheaders: List[str] = []
        for header in sorts:
            logg.info(" = header = %s", header)
            cols: List[str] = []
            for headercol in header.split("|"):
                if "@" in headercol:
                    name, suffix = headercol.split("@", 1)
                    if suffix:
                        renames = "@" + suffix
                else:
                    name, renames = headercol, ""
                sortheaders += [name]
                if name in formats:
                    cols += [name + ":" + formats[name] + renames]
                else:
                    cols += [name + renames]
                if name in combine:
                    adds = combine[name]
                    if adds in formats:
                        cols += [adds + ":" + formats[adds]]
                    else:
                        cols += [adds]
                    combined += [adds]
            headers += ["|".join(cols)]
        logg.debug("headers = %s", headers)
        logg.debug("combine < %s", combine)
        logg.info("sorting = %s", sortheaders)
        sorting = sortheaders
    else:
        sorting = sorts
        formatter = formats
    return tabtoHTML(result, headers, selected,  # ..
                     legend=legend, tab=tab, padding=padding, xmlns=xmlns, section=section,  # ..
                     reorder=reorder, sorts=sorting, formatter=formatter)

def tabtoHTML(data: Iterable[JSONDict], headers: List[str] = [], selected: List[str] = [],  # ..
              *, legend: LegendList = [], tab: str = "|", padding: str = " ", minwidth: int = 0,
              noheaders: bool = False, xmlns: str = "", section: str = NIX,
              reorder: ColSortList = [], sorts: RowSortList = [], formatter: FormatsDict = {}) -> str:
    logg.debug("tabtoHTML")
    minwidth = minwidth or MINWIDTH
    renameheaders: Dict[str, str] = {}
    showheaders: List[str] = []
    sortheaders: List[str] = []
    formats: Dict[str, str] = {}
    combine: Dict[str, List[str]] = {}
    freehdrs: Dict[str, str] = {}
    for header in headers:
        combines = ""
        for selheader in header.split("|"):
            if "@" in selheader:
                selcol, rename = selheader.split("@", 1)
            else:
                selcol, rename = selheader, ""
            if "{" in selcol and "{:" not in selcol:
                names3: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon3, brace3 = freepart.find(":"), freepart.find("}")
                    if brace3 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end3 = brace3 if colon3 == -1 else min(colon3, brace3)
                    name3 = freepart[:end3]
                    names3.append(name3)
                col = " ".join(names3)
                freehdrs[col] = selcol
            elif ":" in selcol:
                col, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[col] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                col = selcol
            showheaders += [col]  # headers make a default column order
            if rename:
                sortheaders += [col]  # headers does not sort anymore
            if not combines:
                combines = col
            elif combines not in combine:
                combine[combines] = [col]
            elif col not in combine[combines]:
                combine[combines] += [col]
            if rename:
                renameheaders[col] = rename
    logg.debug("renameheaders = %s", renameheaders)
    logg.debug("sortheaders = %s", sortheaders)
    logg.debug("formats = %s", formats)
    logg.debug("combine = %s", combine)
    logg.debug("freehdrs = %s", freehdrs)
    logg.debug("combine > %s", combine)
    combined: Dict[str, List[str]] = {}
    renaming: Dict[str, str] = {}
    filtered: Dict[str, str] = {}
    selcols: List[str] = []
    freecols: Dict[str, str] = {}
    for selecheader in selected:
        combines = ""
        for selec in selecheader.split("|"):
            if "@" in selec:
                selcol, rename = selec.split("@", 1)
            else:
                selcol, rename = selec, ""
            if "{" in selcol and "{:" not in selcol:
                names4: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon4, brace4 = freepart.find(":"), freepart.find("}")
                    if brace4 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end4 = brace4 if colon4 == -1 else min(colon4, brace4)
                    name4 = freepart[:end4]
                    names4.append(name4)
                col = " ".join(names4)
                freecols[col] = selcol
            elif ":" in selcol:
                col, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[col] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                col = selcol
            if "<" in col:
                col, cond = col.split("<", 1)
                filtered[col] = "<" + cond
            elif ">" in col:
                col, cond = col.split(">", 1)
                filtered[col] = ">" + cond
            elif "=" in col:
                col, cond = col.split("=", 1)
                filtered[col] = "=" + cond
            selcols.append(col)
            if rename:
                renaming[col] = rename
            if not combines:
                combines = col
            elif combines not in combined:
                combined[combines] = [col]
            elif combines not in combined[combines]:
                combined[combines] += [col]
    logg.debug("combined = %s", combined)
    logg.debug("renaming = %s", renaming)
    logg.debug("filtered = %s", filtered)
    logg.debug("selcols = %s", selcols)
    logg.debug("freecols = %s", freecols)
    if not selected:
        combined = combine  # argument
        freecols = freehdrs
        renaming = renameheaders
        logg.debug("combined : %s", combined)
        logg.debug("freecols : %s", freecols)
        logg.debug("renaming : %s", renaming)
    newsorts: Dict[str, str] = {}
    colnames: Dict[str, str] = {}
    for col, rename in renaming.items():
        if "@" in rename:
            newname, newsort = rename.split("@", 1)
        elif rename and rename[0].isalpha():
            newname, newsort = rename, ""
        else:
            newname, newsort = "", rename
        if newname:
            colnames[col] = newname
            if col in formats:
                formats[newname] = formats[col]
        if newsort:
            newsorts[col] = newsort
    logg.debug("newsorts = %s", newsorts)
    logg.debug("colnames = %s", colnames)
    if sorts:
        sortcolumns = sorts
    else:
        sortcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols or sortheaders)]
        if newsorts:
            for num, col in enumerate(sortcolumns):
                if col not in newsorts:
                    newsorts[col] = ("@" * len(str(num)) + str(num))
            sortcolumns = sorted(newsorts, key=lambda x: newsorts[x])
            logg.debug("sortcolumns : %s", sortcolumns)
    format: FormatJSONItem
    if formatter and isinstance(formatter, FormatJSONItem):
        format = formatter
    else:
        logg.debug("formats = %s |")
        format = FormatHTML(formats)
    selcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols)]
    selheaders = [(name if name not in colnames else colnames[name]) for name in (showheaders)]
    sortkey = ColSortCallable(selcolumns or sorts or selheaders, reorder)
    sortrow = RowSortCallable(sortcolumns)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for num, item in enumerate(data):
        row: JSONDict = {}
        if "#" in selcols:
            row["#"] = num + 1
            cols["#"] = len(str(num + 1))
        skip = False
        for col, value in item.items():
            selname = col
            if col in renameheaders and renameheaders[col] in selcols:
                selname = renameheaders[col]
            if selcols and selname not in selcols and "*" not in selcols:
                continue
            try:
                if col in filtered:
                    skip = skip or unmatched(value, filtered[col])
            except: pass
            colname = selname if selname not in colnames else colnames[selname]
            row[colname] = value
            oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
            cols[colname] = max(oldlen, len(format(colname, value)))
        for freecol, freeformat in freecols.items():
            try:
                freenames = freecol.split(" ")
                freeitem: JSONDict = dict([(freename, _None_String) for freename in freenames])
                for col, value in item.items():
                    itemname = col
                    if col in renameheaders and renameheaders[col] in freenames:
                        itemname = renameheaders[col]
                    if itemname in freenames:
                        freeitem[itemname] = format(col, value)
                value = freeformat.format(**freeitem)
                colname = freecol if freecol not in colnames else colnames[freecol]
                row[colname] = value
                oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
                cols[colname] = max(oldlen, len(value))
            except Exception as e:
                logg.info("formatting '%s' at %s bad for:\n\t%s", freeformat, e, item)
        if not skip:
            rows.append(row)
    combining = []
    for combines in combined:
        combining += combined[combines]
    for col in combined:
        if col not in cols:  # if target does not exist in dataset
            for added in combined[col]:
                combining.remove(added)  # the shown combined column seperately
    colo = tuple(sorted(cols.keys(), key=sortkey))  # ordered column names
    colr = tuple(((' style="text-align: right"' if format.right(col) else "") for col in colo))
    lines = []
    if not noheaders:
        headers = []
        for m, col in enumerate(colo):
            if col in combining:
                continue
            html = "<th%s>%s</th>" % (colr[m], escape(col))
            if col in combined:
                for adds in combined[col]:
                    if adds in cols:
                        html = html.replace("</th>", "<br />%s</th>" % escape(adds))
            headers += [html]
        lines.append("<tr>" + "".join(headers) + "</tr>")
    for item in sorted(rows, key=sortrow):
        values: Dict[str, str] = dict([(name, "") for name in cols.keys()])  # initialized with all columns to empty string
        for col, value in item.items():
            values[col] = format(col, value)
        cells = []
        for m, col in enumerate(colo):
            if col in combining:
                continue
            html = "<td%s>%s</td>" % (colr[m], escape(values[col]))
            if col in combined:
                for adds in combined[col]:
                    if adds in cols:
                        html = html.replace("</td>", "<br />%s</td>" % escape(values[adds]))
            cells += [html]
        lines.append("<tr>" + "".join(cells) + "</tr>")
    table = "<table>"
    end = ""
    if tab:
        table = table.replace(">", ' border="%x">' % len(tab))
    if padding:
        table = table.replace(">", ' cellpadding="%s">' % (8 * len(padding)))
    if xmlns:
        if "http://" not in xmlns:
            xmlns = "http://www.w3.org/" + xmlns
        table = '<html xmlns="%s">\n' % xmlns + table
        end = '</html>'
    if section:
        table += "<caption>%s</caption>" % escape(section)
    return table + "\n" + "\n".join(lines) + "\n</table>\n" + legendToHTML(legend, sorts, reorder) + end

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

def loadHTML(text: str, datedelim: str = '-', section: str = NIX) -> JSONList:
    parser = DictParserHTML(datedelim, section=section)
    return list(parser.loads(text))
def readFromHTML(filename: str, datedelim: str = '-', section: str = NIX) -> JSONList:
    parser = DictParserHTML(datedelim, section=section)
    return list(parser.load(filename))
def tabtextfileHTML(filename: str, datedelim: str = '-', section: str = NIX) -> TabText:
    parser = DictParserHTML(datedelim, section=section)
    data = list(parser.load(filename))
    return TabText(data, parser.headers)

class DictParserHTML(DictParser):
    def __init__(self, datedelim: str = '-', section: str = NIX, convert_charrefs: bool = True) -> None:
        self.convert = ParseJSONItem(datedelim)
        self.convert_charrefs = convert_charrefs
        self.section = section  # actually ignored
        self.headers = STRLIST
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
        self.headers = parser.th

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
               sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
               *, datedelim: str = '-', legend: LegendList = [], section: str = NIX) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToJSON(results, sorts, formats, selected, datedelim=datedelim, legend=legend, section=section)
def tabToJSON(result: Iterable[JSONDict],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
              *, datedelim: str = '-', padding: str = " ", legend: LegendList = [],  #
              section: str = NIX, reorder: ColSortList = []) -> str:
    """ old-style RowSortList and FormatsDict assembled into headers with microsyntax """
    headers: List[str] = []
    sorting: RowSortList = []
    formatter: FormatsDict = {}
    if isinstance(sorts, Sequence) and isinstance(formats, dict):
        sortheaders: List[str] = []
        for header in sorts:
            cols: List[str] = []
            for headercol in header.split("|"):
                if "@" in headercol:
                    name, suffix = headercol.split("@", 1)
                    if suffix:
                        renames = "@" + suffix
                else:
                    name, renames = headercol, ""
                sortheaders += [name]
                if name in formats:
                    cols += [name + ":" + formats[name] + renames]
                else:
                    cols += [name + renames]
            headers += ["|".join(cols)]
        logg.info("headers = %s", headers)
        logg.info("sorting = %s", sortheaders)
        sorting = sortheaders
    else:
        sorting = sorts
        formatter = formats
    return tabtoJSON(result, headers, selected,  # ..
                     legend=legend, datedelim=datedelim, padding=padding,  # ..
                     section=section, reorder=reorder, sorts=sorting, formatter=formatter)

def tabtoJSON(data: Iterable[JSONDict], headers: List[str] = [], selected: List[str] = [],  # ..
              *, legend: LegendList = [], padding: str = " ", minwidth: int = 0, datedelim: str = '-',
              section: str = NIX, reorder: ColSortList = [], sorts: RowSortList = [], formatter: FormatsDict = {}) -> str:
    minwidth = minwidth or MINWIDTH
    logg.debug("tabtoJSON:")
    renameheaders: Dict[str, str] = {}
    showheaders: List[str] = []
    sortheaders: List[str] = []
    formats: Dict[str, str] = {}
    freehdrs: Dict[str, str] = {}
    for header in headers:
        combines = ""
        for selheader in header.split("|"):
            if "@" in selheader:
                selcol, rename = selheader.split("@", 1)
            else:
                selcol, rename = selheader, ""
            if "{" in selcol and "{:" not in selcol:
                names3: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon3, brace3 = freepart.find(":"), freepart.find("}")
                    if brace3 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end3 = brace3 if colon3 == -1 else min(colon3, brace3)
                    name3 = freepart[:end3]
                    names3.append(name3)
                name = " ".join(names3)
                freehdrs[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            showheaders += [name]  # headers make a default column order
            if rename:
                sortheaders += [name]  # headers does not sort anymore
            if rename:
                renameheaders[name] = rename
    logg.debug("renameheaders = %s", renameheaders)
    logg.debug("sortheaders = %s", sortheaders)
    logg.debug("formats = %s", formats)
    logg.debug("freehdrs = %s", freehdrs)
    renaming: Dict[str, str] = {}
    filtered: Dict[str, str] = {}
    selcols: List[str] = []
    freecols: Dict[str, str] = {}
    for selecheader in selected:
        combines = ""
        for selec in selecheader.split("|"):
            if "@" in selec:
                selcol, rename = selec.split("@", 1)
            else:
                selcol, rename = selec, ""
            if "{" in selcol and "{:" not in selcol:
                names4: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon4, brace4 = freepart.find(":"), freepart.find("}")
                    if brace4 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end4 = brace4 if colon4 == -1 else min(colon4, brace4)
                    name4 = freepart[:end4]
                    names4.append(name4)
                name = " ".join(names4)
                freecols[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            if "<" in name:
                name, cond = name.split("<", 1)
                filtered[name] = "<" + cond
            elif ">" in name:
                name, cond = name.split(">", 1)
                filtered[name] = ">" + cond
            elif "=" in name:
                name, cond = name.split("=", 1)
                filtered[name] = "=" + cond
            selcols.append(name)
            if rename:
                renaming[name] = rename
    logg.debug("renaming = %s", renaming)
    logg.debug("filtered = %s", filtered)
    logg.debug("selcols = %s", selcols)
    logg.debug("freecols = %s", freecols)
    if not selected:
        freecols = freehdrs
        renaming = renameheaders
        logg.debug("freecols : %s", freecols)
        logg.debug("renaming : %s", renaming)
    newsorts: Dict[str, str] = {}
    colnames: Dict[str, str] = {}
    for name, rename in renaming.items():
        if "@" in rename:
            newname, newsort = rename.split("@", 1)
        elif rename and rename[0].isalpha():
            newname, newsort = rename, ""
        else:
            newname, newsort = "", rename
        if newname:
            colnames[name] = newname
            if name in formats:
                formats[newname] = formats[name]
        if newsort:
            newsorts[name] = newsort
    logg.debug("newsorts = %s", newsorts)
    logg.debug("colnames = %s", colnames)
    if sorts:
        sortcolumns = sorts
    else:
        sortcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols or sortheaders)]
        if newsorts:
            for num, name in enumerate(sortcolumns):
                if name not in newsorts:
                    newsorts[name] = ("@" * len(str(num)) + str(num))
            sortcolumns = sorted(newsorts, key=lambda x: newsorts[x])
            logg.debug("sortcolumns : %s", sortcolumns)
    format: FormatJSONItem
    if formatter and isinstance(formatter, FormatJSONItem):
        format = formatter
    else:
        logg.debug("formats = %s | datedelim=%s", formats, datedelim)
        format = FormatJSON(formats, datedelim=datedelim)
    if legend:
        logg.debug("legend is ignored for JSON output")
    selcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols)]
    selheaders = [(name if name not in colnames else colnames[name]) for name in (showheaders)]
    sortkey = ColSortCallable(selcolumns or sorts or selheaders, reorder)
    sortrow = RowSortCallable(sortcolumns)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for num, item in enumerate(data):
        row: JSONDict = {}
        if "#" in selcols:
            row["#"] = num + 1
            cols["#"] = len(str(num + 1))
        skip = False
        for name, value in item.items():
            selname = name
            if name in renameheaders and renameheaders[name] in selcols:
                selname = renameheaders[name]
            if selcols and selname not in selcols and "*" not in selcols:
                continue
            try:
                if name in filtered:
                    skip = skip or unmatched(value, filtered[name])
            except: pass
            colname = selname if selname not in colnames else colnames[selname]
            row[colname] = value
            oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
            cols[colname] = max(oldlen, len(format(colname, value)))
        for freecol, freeformat in freecols.items():
            try:
                freenames = freecol.split(" ")
                freeitem: JSONDict = dict([(freename, _None_String) for freename in freenames])
                for name, value in item.items():
                    itemname = name
                    if name in renameheaders and renameheaders[name] in freenames:
                        itemname = renameheaders[name]
                    if itemname in freenames:
                        freeitem[itemname] = format(name, value)
                value = freeformat.format(**freeitem)
                colname = freecol if freecol not in colnames else colnames[freecol]
                row[colname] = value
                oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
                cols[colname] = max(oldlen, len(value))
            except Exception as e:
                logg.info("formatting '%s' at %s bad for:\n\t%s", freeformat, e, item)
        if not skip:
            rows.append(row)
    colo = tuple(sorted(cols.keys(), key=sortkey))  # ordered column names
    pad = " " * len(padding)
    comma = "," + pad
    lines = []
    for item in sorted(rows, key=sortrow):
        values: JSONDict = {}
        for name, value in item.items():
            values[name] = format(name, value)
        line = ['"%s":%s%s' % (name, pad, values[name]) for name in colo if name in values]
        lines.append(" {" + comma.join(line) + "}")
    newlist = "[\n"
    endlist = "\n]"
    if section:
        newlist = '{"%s":%s[\n' % (section.replace('"', "'"), pad)
        endlist = "\n]}"
    return newlist + ",\n".join(lines) + endlist

def loadJSON(text: str, datedelim: str = '-', section: str = NIX) -> JSONList:
    parser = DictParserJSON(datedelim=datedelim, section=section)
    return list(parser.loads(text))
def readFromJSON(filename: str, datedelim: str = '-', section: str = NIX) -> JSONList:
    parser = DictParserJSON(datedelim=datedelim, section=section)
    return list(parser.load(filename))
def tabtextfileJSON(filename: str, datedelim: str = '-', section: str = NIX) -> TabText:
    return TabText(readFromJSON(filename, datedelim=datedelim, section=section), [])
def tablistfileJSON(filename: str, datedelim: str = '-', section: str = NIX) -> List[TabSheet]:
    parser = DictParserJSON(datedelim=datedelim, section=section)
    return parser.loadtablist(filename)

class DictParserJSON(DictParser):
    def __init__(self, section: str = NIX, *, datedelim: str = '-') -> None:
        self.convert = ParseJSONItem(datedelim)
        self.section = section
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
    def loadtablist(self, filename: str) -> List[TabSheet]:
        tabs: List[TabSheet] = []
        jsondata = json.load(open(filename))
        if isinstance(jsondata, dict):
            jsondict = jsondata
        else:
            jsondict = {(self.section or SECTION): jsondata}
        for listname, jsonlist in jsondict.items():
            listdata: List[JSONDict] = []
            if isinstance(jsonlist, Iterable):
                for nextgroup in jsonlist:
                    if isinstance(nextgroup, dict):
                        newgroup: JSONDict = {}
                        for nam, jsonval in nextgroup.items():
                            if isinstance(jsonval, str):
                                newgroup[nam] = self.convert.toDate(jsonval)
                            else:
                                newgroup[nam] = jsonval
                        listdata.append(newgroup)
            tabs.append(TabSheet(listdata, [], listname))
        return tabs

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
               sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
               *, datedelim: str = '-', padding: str = " ", legend: LegendList = [], section: str = NIX) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToYAML(results, sorts, formats, datedelim=datedelim, padding=padding, legend=legend, section=section)
def tabToYAML(result: Iterable[JSONDict],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
              *, datedelim: str = '-', padding: str = " ", legend: LegendList = [], section: str = NIX,
              reorder: ColSortList = []) -> str:
    """ old-style RowSortList and FormatsDict assembled into headers with microsyntax """
    headers: List[str] = []
    sorting: RowSortList = []
    formatter: FormatsDict = {}
    if isinstance(sorts, Sequence) and isinstance(formats, dict):
        sortheaders: List[str] = []
        for header in sorts:
            cols: List[str] = []
            for headercol in header.split("|"):
                if "@" in headercol:
                    name, suffix = headercol.split("@", 1)
                    if suffix:
                        renames = "@" + suffix
                else:
                    name, renames = headercol, ""
                sortheaders += [name]
                if name in formats:
                    cols += [name + ":" + formats[name] + renames]
                else:
                    cols += [name + renames]
            headers += ["|".join(cols)]
        logg.info("headers = %s", headers)
        logg.info("sorting = %s", sortheaders)
        sorting = sortheaders
    else:
        sorting = sorts
        formatter = formats
    return tabtoYAML(result, headers, selected,  # ..
                     legend=legend, datedelim=datedelim, padding=padding,  # ..
                     section=section, reorder=reorder, sorts=sorting, formatter=formatter)

def tabtoYAML(data: Iterable[JSONDict], headers: List[str] = [], selected: List[str] = [],  # ..
              *, legend: LegendList = [], padding: str = " ", minwidth: int = 0, datedelim: str = '-',  #
              section: str = NIX, reorder: ColSortList = [], sorts: RowSortList = [], formatter: FormatsDict = {}) -> str:
    minwidth = minwidth or MINWIDTH
    logg.debug("tabtoYAML:")
    renameheaders: Dict[str, str] = {}
    showheaders: List[str] = []
    sortheaders: List[str] = []
    formats: Dict[str, str] = {}
    freehdrs: Dict[str, str] = {}
    for header in headers:
        combines = ""
        for selheader in header.split("|"):
            if "@" in selheader:
                selcol, rename = selheader.split("@", 1)
            else:
                selcol, rename = selheader, ""
            if "{" in selcol and "{:" not in selcol:
                names3: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon3, brace3 = freepart.find(":"), freepart.find("}")
                    if brace3 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end3 = brace3 if colon3 == -1 else min(colon3, brace3)
                    name3 = freepart[:end3]
                    names3.append(name3)
                name = " ".join(names3)
                freehdrs[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            showheaders += [name]  # headers make a default column order
            if rename:
                sortheaders += [name]  # headers does not sort anymore
            if rename:
                renameheaders[name] = rename
    logg.debug("renameheaders = %s", renameheaders)
    logg.debug("sortheaders = %s", sortheaders)
    logg.debug("formats = %s", formats)
    logg.debug("freehdrs = %s", freehdrs)
    renaming: Dict[str, str] = {}
    filtered: Dict[str, str] = {}
    selcols: List[str] = []
    freecols: Dict[str, str] = {}
    for selecheader in selected:
        combines = ""
        for selec in selecheader.split("|"):
            if "@" in selec:
                selcol, rename = selec.split("@", 1)
            else:
                selcol, rename = selec, ""
            if "{" in selcol and "{:" not in selcol:
                names4: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon4, brace4 = freepart.find(":"), freepart.find("}")
                    if brace4 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end4 = brace4 if colon4 == -1 else min(colon4, brace4)
                    name4 = freepart[:end4]
                    names4.append(name4)
                name = " ".join(names4)
                freecols[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            if "<" in name:
                name, cond = name.split("<", 1)
                filtered[name] = "<" + cond
            elif ">" in name:
                name, cond = name.split(">", 1)
                filtered[name] = ">" + cond
            elif "=" in name:
                name, cond = name.split("=", 1)
                filtered[name] = "=" + cond
            selcols.append(name)
            if rename:
                renaming[name] = rename
    logg.debug("renaming = %s", renaming)
    logg.debug("filtered = %s", filtered)
    logg.debug("selcols = %s", selcols)
    logg.debug("freecols = %s", freecols)
    if not selected:
        freecols = freehdrs
        renaming = renameheaders
        logg.debug("freecols : %s", freecols)
        logg.debug("renaming : %s", renaming)
    newsorts: Dict[str, str] = {}
    colnames: Dict[str, str] = {}
    for name, rename in renaming.items():
        if "@" in rename:
            newname, newsort = rename.split("@", 1)
        elif rename and rename[0].isalpha():
            newname, newsort = rename, ""
        else:
            newname, newsort = "", rename
        if newname:
            colnames[name] = newname
            if name in formats:
                formats[newname] = formats[name]
        if newsort:
            newsorts[name] = newsort
    logg.debug("newsorts = %s", newsorts)
    logg.debug("colnames = %s", colnames)
    if sorts:
        sortcolumns = sorts
    else:
        sortcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols or sortheaders)]
        if newsorts:
            for num, name in enumerate(sortcolumns):
                if name not in newsorts:
                    newsorts[name] = ("@" * len(str(num)) + str(num))
            sortcolumns = sorted(newsorts, key=lambda x: newsorts[x])
            logg.debug("sortcolumns : %s", sortcolumns)
    format: FormatJSONItem
    if formatter and isinstance(formatter, FormatJSONItem):
        format = formatter
    else:
        logg.debug("formats = %s | datedelim=%s", formats, datedelim)
        format = FormatYAML(formats, datedelim=datedelim)
    if legend:
        logg.debug("legend is ignored for YAML output")
    selcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols)]
    selheaders = [(name if name not in colnames else colnames[name]) for name in (showheaders)]
    sortkey = ColSortCallable(selcolumns or sorts or selheaders, reorder)
    sortrow = RowSortCallable(sortcolumns)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for num, item in enumerate(data):
        row: JSONDict = {}
        if "#" in selcols:
            row["#"] = num + 1
            cols["#"] = len(str(num + 1))
        skip = False
        for name, value in item.items():
            selname = name
            if name in renameheaders and renameheaders[name] in selcols:
                selname = renameheaders[name]
            if selcols and selname not in selcols and "*" not in selcols:
                continue
            try:
                if name in filtered:
                    skip = skip or unmatched(value, filtered[name])
            except: pass
            colname = selname if selname not in colnames else colnames[selname]
            row[colname] = value
            oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
            cols[colname] = max(oldlen, len(format(colname, value)))
        for freecol, freeformat in freecols.items():
            try:
                freenames = freecol.split(" ")
                freeitem: JSONDict = dict([(freename, _None_String) for freename in freenames])
                for name, value in item.items():
                    itemname = name
                    if name in renameheaders and renameheaders[name] in freenames:
                        itemname = renameheaders[name]
                    if itemname in freenames:
                        freeitem[itemname] = format(name, value)
                value = freeformat.format(**freeitem)
                colname = freecol if freecol not in colnames else colnames[freecol]
                row[colname] = value
                oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
                cols[colname] = max(oldlen, len(value))
            except Exception as e:
                logg.info("formatting '%s' at %s bad for:\n\t%s", freeformat, e, item)
        if not skip:
            rows.append(row)
    colo = tuple(sorted(cols.keys(), key=sortkey))  # ordered column names
    pad = " " * len(padding)
    is_simple = re.compile("^\\w[\\w_-]*$")
    def as_name(name: str) -> str:
        return (name if is_simple.match(name) else '"%s"' % name)
    lines = []
    for item in sorted(rows, key=sortrow):
        values: JSONDict = {}
        for name, value in item.items():
            values[name] = format(name, value)
        line = ['%s:%s%s' % (as_name(name), pad, values[name]) for name in colo if name in values]
        lines.append("- " + "\n  ".join(line))
    section = section or SECTION
    return F"{section}:\n" + "\n".join(lines) + "\n"

def loadYAML(text: str, datedelim: str = '-', section: str = NIX) -> JSONList:
    parser = DictParserYAML(datedelim=datedelim, section=section)
    return list(parser.loads(text))
def readFromYAML(filename: str, datedelim: str = '-', section: str = NIX) -> JSONList:
    parser = DictParserYAML(datedelim=datedelim, section=section)
    return list(parser.load(filename))
def tabtextfileYAML(filename: str, datedelim: str = '-', section: str = NIX) -> TabText:
    return TabText(readFromYAML(filename, datedelim), [])

def DictReaderYAML(rows: Iterable[str], *, datedelim: str = '-', section: str = NIX) -> Iterator[JSONDict]:
    parser = DictParserYAML(datedelim=datedelim, section=section)
    return parser.read(rows)

class DictParserYAML(DictParser):
    def __init__(self, section: str = NIX, *, datedelim: str = '-') -> None:
        self.convert = ParseJSONItem(datedelim)
        self.convert.None_String = "null"
        self.convert.True_String = "true"
        self.convert.False_String = "false"
        self.section = section
    def load(self, filename: str) -> Iterator[JSONDict]:
        return self.read(open(filename))
    def loads(self, text: str) -> Iterator[JSONDict]:
        return self.read(text.splitlines())
    def read(self, rows: Iterable[str], section: str = NIX) -> Iterator[JSONDict]:
        section = self.section or SECTION
        at = "start"
        record: JSONDict = {}
        for row in rows:
            line = row.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(F"{section}:"):
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
               sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
               *, datedelim: str = '-', legend: LegendList = [], section: str = NIX) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToTOML(results, sorts, formats, selected, datedelim=datedelim, legend=legend, section=section)
def tabToTOML(result: Iterable[JSONDict],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
              *, datedelim: str = '-', padding: str = " ", legend: LegendList = [],  #
              section: str = NIX, reorder: ColSortList = []) -> str:
    """ old-style RowSortList and FormatsDict assembled into headers with microsyntax """
    headers: List[str] = []
    sorting: RowSortList = []
    formatter: FormatsDict = {}
    if isinstance(sorts, Sequence) and isinstance(formats, dict):
        sortheaders: List[str] = []
        for header in sorts:
            cols: List[str] = []
            for headercol in header.split("|"):
                if "@" in headercol:
                    name, suffix = headercol.split("@", 1)
                    if suffix:
                        renames = "@" + suffix
                else:
                    name, renames = headercol, ""
                sortheaders += [name]
                if name in formats:
                    cols += [name + ":" + formats[name] + renames]
                else:
                    cols += [name + renames]
        logg.info("headers = %s", headers)
        logg.info("sorting = %s", sortheaders)
        sorting = sortheaders
    else:
        sorting = sorts
        formatter = formats
    return tabtoTOML(result, headers, selected,  # ..
                     legend=legend, padding=padding, datedelim=datedelim,  # ..
                     section=section, reorder=reorder, sorts=sorting, formatter=formatter)

def tabtoTOML(data: Iterable[JSONDict], headers: List[str] = [], selected: List[str] = [],  # ..
              *, legend: LegendList = [], padding: str = " ", minwidth: int = 0, datedelim: str = '-',
              section: str = NIX, reorder: ColSortList = [], sorts: RowSortList = [], formatter: FormatsDict = {}) -> str:
    minwidth = minwidth or MINWIDTH
    logg.debug("tabtoGFM:")
    renameheaders: Dict[str, str] = {}
    showheaders: List[str] = []
    sortheaders: List[str] = []
    formats: Dict[str, str] = {}
    freehdrs: Dict[str, str] = {}
    for header in headers:
        combines = ""
        for selheader in header.split("|"):
            if "@" in selheader:
                selcol, rename = selheader.split("@", 1)
            else:
                selcol, rename = selheader, ""
            if "{" in selcol and "{:" not in selcol:
                names3: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon3, brace3 = freepart.find(":"), freepart.find("}")
                    if brace3 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end3 = brace3 if colon3 == -1 else min(colon3, brace3)
                    name3 = freepart[:end3]
                    names3.append(name3)
                name = " ".join(names3)
                freehdrs[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            showheaders += [name]  # headers make a default column order
            if rename:
                sortheaders += [name]  # headers does not sort anymore
            if rename:
                renameheaders[name] = rename
    logg.debug("renameheaders = %s", renameheaders)
    logg.debug("sortheaders = %s", sortheaders)
    logg.debug("formats = %s", formats)
    logg.debug("freehdrs = %s", freehdrs)
    renaming: Dict[str, str] = {}
    filtered: Dict[str, str] = {}
    selcols: List[str] = []
    freecols: Dict[str, str] = {}
    for selecheader in selected:
        combines = ""
        for selec in selecheader.split("|"):
            if "@" in selec:
                selcol, rename = selec.split("@", 1)
            else:
                selcol, rename = selec, ""
            if "{" in selcol and "{:" not in selcol:
                names4: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon4, brace4 = freepart.find(":"), freepart.find("}")
                    if brace4 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end4 = brace4 if colon4 == -1 else min(colon4, brace4)
                    name4 = freepart[:end4]
                    names4.append(name4)
                name = " ".join(names4)
                freecols[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            if "<" in name:
                name, cond = name.split("<", 1)
                filtered[name] = "<" + cond
            elif ">" in name:
                name, cond = name.split(">", 1)
                filtered[name] = ">" + cond
            elif "=" in name:
                name, cond = name.split("=", 1)
                filtered[name] = "=" + cond
            selcols.append(name)
            if rename:
                renaming[name] = rename
    logg.debug("renaming = %s", renaming)
    logg.debug("filtered = %s", filtered)
    logg.debug("selcols = %s", selcols)
    logg.debug("freecols = %s", freecols)
    if not selected:
        freecols = freehdrs
        renaming = renameheaders
        logg.debug("freecols : %s", freecols)
        logg.debug("renaming : %s", renaming)
        reorders: Dict[str, str] = {}
    newsorts: Dict[str, str] = {}
    colnames: Dict[str, str] = {}
    for name, rename in renaming.items():
        if "@" in rename:
            newname, newsort = rename.split("@", 1)
        elif rename and rename[0].isalpha():
            newname, newsort = rename, ""
        else:
            newname, newsort = "", rename
        if newname:
            colnames[name] = newname
            if name in formats:
                formats[newname] = formats[name]
        if newsort:
            newsorts[name] = newsort
    logg.debug("newsorts = %s", newsorts)
    logg.debug("colnames = %s", colnames)
    if sorts:
        sortcolumns = sorts
    else:
        sortcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols or sortheaders)]
        if newsorts:
            for num, name in enumerate(sortcolumns):
                if name not in newsorts:
                    newsorts[name] = ("@" * len(str(num)) + str(num))
            sortcolumns = sorted(newsorts, key=lambda x: newsorts[x])
            logg.debug("sortcolumns : %s", sortcolumns)
    format: FormatJSONItem
    if formatter and isinstance(formatter, FormatJSONItem):
        format = formatter
    else:
        logg.debug("formats = %s | datedelim=%s", formats, datedelim)
        format = FormatTOML(formats, datedelim=datedelim)
    if legend:
        logg.debug("legend is ignored for TOML output")
    selcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols)]
    selheaders = [(name if name not in colnames else colnames[name]) for name in (showheaders)]
    sortkey = ColSortCallable(selcolumns or sorts or selheaders, reorder)
    sortrow = RowSortCallable(sortcolumns)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for num, item in enumerate(data):
        row: JSONDict = {}
        if "#" in selcols:
            row["#"] = num + 1
            cols["#"] = len(str(num + 1))
        skip = False
        for name, value in item.items():
            selname = name
            if name in renameheaders and renameheaders[name] in selcols:
                selname = renameheaders[name]
            if selcols and selname not in selcols and "*" not in selcols:
                continue
            try:
                if name in filtered:
                    skip = skip or unmatched(value, filtered[name])
            except: pass
            colname = selname if selname not in colnames else colnames[selname]
            row[colname] = value
            oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
            cols[colname] = max(oldlen, len(format(colname, value)))
        for freecol, freeformat in freecols.items():
            try:
                freenames = freecol.split(" ")
                freeitem: JSONDict = dict([(freename, _None_String) for freename in freenames])
                for name, value in item.items():
                    itemname = name
                    if name in renameheaders and renameheaders[name] in freenames:
                        itemname = renameheaders[name]
                    if itemname in freenames:
                        freeitem[itemname] = format(name, value)
                value = freeformat.format(**freeitem)
                colname = freecol if freecol not in colnames else colnames[freecol]
                row[colname] = value
                oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
                cols[colname] = max(oldlen, len(value))
            except Exception as e:
                logg.info("formatting '%s' at %s bad for:\n\t%s", freeformat, e, item)
        if not skip:
            rows.append(row)
    colo = tuple(sorted(cols.keys(), key=sortkey))  # ordered column names
    pad = " " * len(padding)
    is_simple = re.compile("^\\w[\\w_-]*$")
    def as_name(name: str) -> str:
        return (name if is_simple.match(name) else '"%s"' % name)
    lines = []
    for item in sorted(rows, key=sortrow):
        values: JSONDict = {}
        for name, value in item.items():
            if value is not None:
                values[name] = format(name, value)
        line = ['%s%s=%s%s' % (as_name(name), pad, pad, values[name])
                for name in colo if name in values]
        lines.append("[[data]]\n" + "\n".join(line))
    return "\n".join(lines) + "\n"

def loadTOML(text: str, datedelim: str = '-', section: str = NIX) -> JSONList:
    parser = DictParserTOML(datedelim=datedelim, section=section)
    return list(parser.loads(text))
def readFromTOML(filename: str, datedelim: str = '-', section: str = NIX) -> JSONList:
    parser = DictParserTOML(datedelim=datedelim, section=section)
    return list(parser.load(filename))
def tabtextfileTOML(filename: str, datedelim: str = '-', section: str = NIX) -> TabText:
    return TabText(readFromTOML(filename, datedelim, section=section), [])

class DictParserTOML(DictParser):
    def __init__(self, section: str = NIX, *, datedelim: str = '-') -> None:
        self.convert = ParseJSONItem(datedelim)
        self.convert.None_String = "null"
        self.convert.True_String = "true"
        self.convert.False_String = "false"
        self.section = section
    def load(self, filename: str) -> Iterator[JSONDict]:
        return self.read(open(filename))
    def loads(self, text: str) -> Iterator[JSONDict]:
        return self.read(text.splitlines())
    def read(self, rows: Iterable[str]) -> Iterator[JSONDict]:
        section = self.section or SECTION
        at = "start"
        record: JSONDict = {}
        for row in rows:
            line = row.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(F"[[{section}]]"):
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
              sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
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
    return tabToCSV(results, sorts, formats, selected, datedelim=datedelim, noheaders=noheaders, legend=legend)
def tabToCSV(result: Iterable[JSONDict],  # ..
             sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
             *, datedelim: str = '-', noheaders: bool = False, legend: LegendList = [], tab: str = ";",
             reorder: ColSortList = []) -> str:
    """ old-style RowSortList and FormatsDict assembled into headers with microsyntax """
    headers: List[str] = []
    sorting: RowSortList = []
    formatter: FormatsDict = {}
    if isinstance(sorts, Sequence) and isinstance(formats, dict):
        sortheaders: List[str] = []
        for header in sorts:
            cols: List[str] = []
            for headercol in header.split("|"):
                if "@" in headercol:
                    name, suffix = headercol.split("@", 1)
                    if suffix:
                        renames = "@" + suffix
                else:
                    name, renames = headercol, ""
                sortheaders += [name]
                if name in formats:
                    cols += [name + ":" + formats[name] + renames]
                else:
                    cols += [name + renames]
            headers += ["|".join(cols)]
        logg.info("headers = %s", headers)
        logg.info("sorting = %s", sortheaders)
        sorting = sortheaders
    else:
        sorting = sorts
        formatter = formats
    return tabtoCSV(result, headers, selected,  # ..
                    legend=legend, datedelim=datedelim, noheaders=noheaders, tab=tab,  # ..
                    reorder=reorder, sorts=sorting, formatter=formatter)

def tabtoCSV(data: Iterable[JSONDict], headers: List[str] = [], selected: List[str] = [],  # ..
             *, legend: LegendList = [], minwidth: int = 0, datedelim: str = '-', noheaders: bool = False, unique: bool = False, tab: str = ";",
             reorder: ColSortList = [], sorts: RowSortList = [], formatter: FormatsDict = {}) -> str:
    minwidth = minwidth or MINWIDTH
    logg.debug("tabtoCSV:")
    renameheaders: Dict[str, str] = {}
    showheaders: List[str] = []
    sortheaders: List[str] = []
    formats: Dict[str, str] = {}
    combine: Dict[str, List[str]] = {}
    freehdrs: Dict[str, str] = {}
    for header in headers:
        combines = ""
        for selheader in header.split("|"):
            if "@" in selheader:
                selcol, rename = selheader.split("@", 1)
            else:
                selcol, rename = selheader, ""
            if "{" in selcol and "{:" not in selcol:
                names3: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon3, brace3 = freepart.find(":"), freepart.find("}")
                    if brace3 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end3 = brace3 if colon3 == -1 else min(colon3, brace3)
                    name3 = freepart[:end3]
                    names3.append(name3)
                name = " ".join(names3)
                freehdrs[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            showheaders += [name]
            if rename:
                sortheaders += [name]  # default sort by named headers (rows)
            if not combines:
                combines = name
            elif combines not in combine:
                combine[combines] = [name]
            elif name not in combine[combines]:
                combine[combines] += [name]
            if rename:
                renameheaders[name] = rename
    logg.debug("showheaders = %s", showheaders)
    logg.debug("renameheaders = %s", renameheaders)
    logg.debug("sortheaders = %s", sortheaders)
    logg.debug("formats = %s", formats)
    logg.debug("combine = %s", combine)
    logg.debug("freehdrs = %s", freehdrs)
    combined: Dict[str, List[str]] = {}
    renaming: Dict[str, str] = {}
    filtered: Dict[str, str] = {}
    selcols: List[str] = []
    freecols: Dict[str, str] = {}
    for selecheader in selected:
        combines = ""
        for selec in selecheader.split("|"):
            if "@" in selec:
                selcol, rename = selec.split("@", 1)
            else:
                selcol, rename = selec, ""
            if "{" in selcol and "{:" not in selcol:
                names4: List[str] = []
                freeparts = selcol.split("{")
                for freepart in freeparts[1:]:
                    colon4, brace4 = freepart.find(":"), freepart.find("}")
                    if brace4 == -1:
                        logg.error("no closing '}' for '{%s' in %s", freepart, selcol)
                        continue
                    end4 = brace4 if colon4 == -1 else min(colon4, brace4)
                    name4 = freepart[:end4]
                    names4.append(name4)
                name = " ".join(names4)
                freecols[name] = selcol
            elif ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            if "<" in name:
                name, cond = name.split("<", 1)
                filtered[name] = "<" + cond
            elif ">" in name:
                name, cond = name.split(">", 1)
                filtered[name] = ">" + cond
            elif "=" in name:
                name, cond = name.split("=", 1)
                filtered[name] = "=" + cond
            selcols.append(name)
            if rename:
                renaming[name] = rename
            if not combines:
                combines = name
            elif combines not in combined:
                combined[combines] = [name]
            elif combines not in combined[combines]:
                combined[combines] += [name]
    logg.debug("combined = %s", combined)
    logg.debug("renaming = %s", renaming)
    logg.debug("filtered = %s", filtered)
    logg.debug("selcols = %s", selcols)
    logg.debug("freecols = %s", freecols)
    if not selected:
        combined = combine  # argument
        freecols = freehdrs
        renaming = renameheaders
        logg.debug("combined : %s", combined)
        logg.debug("freecols : %s", freecols)
        logg.debug("renaming : %s", renaming)
    newsorts: Dict[str, str] = {}
    colnames: Dict[str, str] = {}
    for name, rename in renaming.items():
        if "@" in rename:
            newname, newsort = rename.split("@", 1)
        elif rename and rename[0].isalpha():
            newname, newsort = rename, ""
        else:
            newname, newsort = "", rename
        if newname:
            colnames[name] = newname
            if name in formats:
                formats[newname] = formats[name]
        if newsort:
            newsorts[name] = newsort
    logg.debug("newsorts = %s", newsorts)
    logg.debug("colnames = %s", colnames)
    if sorts:
        sortcolumns = sorts
    else:
        sortcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols or sortheaders)]
        if newsorts:
            for num, name in enumerate(sortcolumns):
                if name not in newsorts:
                    newsorts[name] = ("@" * len(str(num)) + str(num))
            sortcolumns = sorted(newsorts, key=lambda x: newsorts[x])
            logg.debug("sortcolumns : %s", sortcolumns)
    format: FormatJSONItem
    if formatter and isinstance(formatter, FormatJSONItem):
        format = formatter
    else:
        logg.debug("formats = %s | datedelim=%s", formats, datedelim)
        format = FormatCSV(formats, datedelim=datedelim)
    if legend:
        logg.debug("legend is ignored for CSV output")
    selcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols)]
    selheaders = [(name if name not in colnames else colnames[name]) for name in (showheaders)]
    sortkey = ColSortCallable(selcolumns or sorts or selheaders, reorder)
    sortrow = RowSortCallable(sortcolumns)
    rows: List[JSONDict] = []
    cols: Dict[str, int] = {}
    for num, item in enumerate(data):
        row: JSONDict = {}
        if "#" in selcols:
            row["#"] = num + 1
            cols["#"] = len(str(num + 1))
        skip = False
        for name, value in item.items():
            selname = name
            if name in renameheaders and renameheaders[name] in selcols:
                selname = renameheaders[name]
            if selcols and selname not in selcols and "*" not in selcols:
                continue
            try:
                if name in filtered:
                    skip = skip or unmatched(value, filtered[name])
            except: pass
            colname = selname if selname not in colnames else colnames[selname]
            row[colname] = value
            oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
            cols[colname] = max(oldlen, len(format(colname, value)))
        for freecol, freeformat in freecols.items():
            try:
                freenames = freecol.split(" ")
                freeitem: JSONDict = dict([(freename, _None_String) for freename in freenames])
                for name, value in item.items():
                    itemname = name
                    if name in renameheaders and renameheaders[name] in freenames:
                        itemname = renameheaders[name]
                    if itemname in freenames:
                        freeitem[itemname] = format(name, value)
                value = freeformat.format(**freeitem)
                colname = freecol if freecol not in colnames else colnames[freecol]
                row[colname] = value
                oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
                cols[colname] = max(oldlen, len(value))
            except Exception as e:
                logg.info("formatting '%s' at %s bad for:\n\t%s", freeformat, e, item)
        if not skip:
            rows.append(row)
    old: Dict[str, str] = {}
    same: List[str] = []
    lines = []
    for item in sorted(rows, key=sortrow):
        values: Dict[str, str] = dict([(name, _None_String) for name in cols.keys()])
        for name, value in item.items():
            values[name] = format(name, value)
        if unique:
            same = [sel for sel in selcols if sel in values and sel in old and values[sel] == old[sel]]
        if not selcols or same != selcols:
            lines.append(values)
        old = values
    colo = tuple(sorted(cols.keys(), key=sortkey))  # ordered column names
    import csv
    # csvfile = open(csv_filename, "w")
    csvfile = StringIO()
    writer = csv.DictWriter(csvfile, fieldnames=colo, restval='ignore',
                            quoting=csv.QUOTE_MINIMAL, delimiter=tab)
    if not noheaders:
        writer.writeheader()
    for line in lines:
        writer.writerow(line)
    return csvfile.getvalue()

def loadCSV(text: str, datedelim: str = '-', tab: str = ";") -> JSONList:
    parser = DictParserCSV(datedelim=datedelim, tab=tab)
    return list(parser.loads(text))
def readFromCSV(filename: str, datedelim: str = '-', tab: str = ";") -> JSONList:
    parser = DictParserCSV(datedelim=datedelim, tab=tab)
    return list(parser.load(filename))
def tabtextfileCSV(filename: str, datedelim: str = '-', tab: str = ";") -> TabText:
    parser = DictParserCSV(datedelim=datedelim, tab=tab)
    data = list(parser.load(filename))
    return TabText(data, parser.headers)

class DictParserCSV(DictParser):
    def __init__(self, *, datedelim: str = '-', tab: str = ";") -> None:
        self.convert = ParseJSONItem(datedelim)
        self.tab = tab
        self.headers = STRLIST
    def load(self, filename: str, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        return self.reads(open(filename), tab=tab)
    def loads(self, text: str, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        return self.reads(StringIO(text), tab=tab)
    def reads(self, csvfile: TextIOWrapper, *, tab: Optional[str] = None) -> Iterator[JSONDict]:
        tab = tab if tab is not None else self.tab
        import csv
        reader = csv.DictReader(csvfile, restval='ignore',
                                quoting=csv.QUOTE_MINIMAL, delimiter=tab)
        for row in reader:
            newrow: JSONDict = dict(row)
            for key, val in newrow.items():
                if isinstance(val, str):
                    newrow[key] = self.convert.toJSONItem(val)
            yield newrow
        if reader.fieldnames is not None:
            self.headers = list(reader.fieldnames)

# .......................................................................................

def print_tabtotext(output: Union[TextIO, str], data: Iterable[JSONDict],  # ..
                    headers: List[str] = [], selected: List[str] = [], legend: List[str] = [],  # ..
                    *, datedelim: Optional[str] = None, tab: Optional[str] = None, padding: Optional[str] = None,
                    xmlns: Optional[str] = None, minwidth: int = 0, section: str = NIX,
                    noheaders: bool = False, unique: bool = False, defaultformat: str = "") -> str:
    if isinstance(output, TextIO) or isinstance(output, StringIO):
        out = output
        fmt = defaultformat
        done = "stream"
    elif "." in output:
        fmt = extension(output) or defaultformat
        if fmt in ["xls", "xlsx", "XLS", "XLSX"]:
            try:
                if TABXLSX:
                    import tabxlsx
                    return tabxlsx.tabtoXLSX(output, data, headers, selected)  # type: ignore[arg-type]
                else:
                    import tabtoxlsx
                    return tabtoxlsx.tabtoXLSX(output, data, headers, selected, legend=legend)
            except Exception as e:
                if not TABXLSX:
                    import tabxlsx
                    return tabxlsx.tabtoXLSX(output, data, headers, selected)  # type: ignore[arg-type]
                else:
                    logg.error("could not write %s: %s", output, e)
        out = open(output, "wt", encoding="utf-8")
        done = output
    else:
        fmt = output
        out = sys.stdout
        done = output
    lines = tabtotext(data, headers, selected, legend=legend, fmt=fmt,
                      datedelim=datedelim, tab=tab, padding=padding,
                      xmlns=xmlns, minwidth=minwidth, section=section,
                      noheaders=noheaders, unique=unique, defaultformat=defaultformat)
    results: List[str] = []
    for line in lines:
        results.append(line)
        out.write(line)
    if noheaders or "@noheaders" in selected or "@dat" in selected:
        return ""
    return ": %s results %s" % (len(results), done)

def tabtotext(data: Iterable[JSONDict],  # ..
              headers: List[str] = [], selected: List[str] = [], legend: List[str] = [],  # ..
              *, fmt: str = "", datedelim: Optional[str] = None, tab: Optional[str] = None, padding: Optional[str] = None,
              xmlns: Optional[str] = None, minwidth: int = 0, section: str = NIX,
              noheaders: bool = False, unique: bool = False, defaultformat: str = "") -> str:
    spec: Dict[str, str] = dict(cast(Tuple[str, str], (x, "") if "=" not in x else x.split("=", 1))
                                for x in selected if x.startswith("@"))
    selected = [x for x in selected if not x.startswith("@")]
    fmt = fmt if fmt not in ["", "-"] else defaultformat
    xmlns = "" if xmlns is None else xmlns
    datedelim = "-" if datedelim is None else datedelim
    padding = " " if padding is None else padding
    tab = "|" if tab is None else tab
    # formats
    if fmt in ["html"] or "@html" in spec:
        fmt = "HTML"
    if fmt in ["htm"] or "@htm" in spec:
        fmt = "HTML"
        tab = ""
        padding = ""
    if fmt in ["xhtm"] or "@xhtm" in spec:
        fmt = "HTML"
        tab = ""
        padding = ""
        xmlns = "1999/xhtml"
    if fmt in ["xhtml"] or "@xhtml" in spec:
        fmt = "HTML"
        xmlns = "1999/xhtml"
    if fmt in ["json"] or "@json" in spec:
        fmt = "JSON"
    if fmt in ["jsn"] or "@jsn" in spec:
        fmt = "JSON"
        padding = ""
    if fmt in ["yaml"] or "@yaml" in spec:
        fmt = "YAML"
    if fmt in ["yml"] or "@yml" in spec:
        fmt = "YAML"
        padding = ""
    if fmt in ["toml"] or "@toml" in spec:
        fmt = "TOML"
    if fmt in ["tml"] or "@tml" in spec:
        fmt = "TOML"
        padding = ""
    if fmt in ["md"] or "@md" in spec:
        fmt = "GFM"  # nopep8
    if fmt in ["markdown"] or "@markdown" in spec:
        fmt = "GFM"
        tab = "||"  # nopep8
    if fmt in ["md2"] or "@md2" in spec:
        fmt = "GFM"
        minwidth = 2  # nopep8
    if fmt in ["md3"] or "@md3" in spec:
        fmt = "GFM"
        minwidth = 3  # nopep8
    if fmt in ["md4"] or "@md4" in spec:
        fmt = "GFM"
        minwidth = 4  # nopep8
    if fmt in ["md5"] or "@md5" in spec:
        fmt = "GFM"
        minwidth = 5  # nopep8
    if fmt in ["md6"] or "@md6" in spec:
        fmt = "GFM"
        minwidth = 6  # nopep8
    if fmt in ["wide"] or "@wide" in spec:
        fmt = "GFM"
        tab = ""  # nopep8
    if fmt in ["txt"] or "@txt" in spec:
        fmt = "GFM"
        padding = ""  # nopep8
    if fmt in ["text"] or "@text" in spec:
        fmt = "GFM"
        padding = ""
        noheaders = True  # nopep8
    if fmt in ["tabs"] or "@tabs" in spec:
        fmt = "GFM"
        tab = "\t"
        padding = ""  # nopep8
    if fmt in ["tab"] or "@tab" in spec:
        fmt = "CSV"
        tab = "\t"  # nopep8
    if fmt in ["data"] or "@data" in spec:
        fmt = "CSV"
        tab = "\t"
        noheaders = True  # nopep8
    if fmt in ["ifs"] or "@ifs" in spec:
        fmt = "CSV"
        tab = os.environ.get("IFS", "\t")  # nopep8
    if fmt in ["dat"] or "@dat" in spec:
        fmt = "CSV"
        tab = os.environ.get("IFS", "\t")
        noheaders = True  # nopep8
    if fmt in ["csv", "scsv"] or "@csv" in spec or "@scsv" in spec:
        fmt = "CSV"
        tab = ";"  # nopep8
    if fmt in ["list"] or "@list" in spec:
        fmt = "CSV"
        tab = ";"
        noheaders = True  # nopep8
    if fmt in ["xlsx", "xls"] or "@xlsx" in spec or "@xls" in spec:
        fmt = "XLS"
        tab = ","  # nopep8
    # override
    if "@delimiter" in spec:
        tab = spec["@delimiter"]
    elif "@delim" in spec:
        tab = spec["@delim"]
    elif "@semicolon" in spec:
        tab = ";"
    elif "@colon" in spec:
        tab = ":"
    elif "@cut" in spec:
        tab = "\t"
    elif "@notab" in spec:
        tab = ""
    if "@datedelim" in spec:
        datedelim = spec["@datedelim"] or "-"
    if "@nopadding" in spec:
        padding = ""
    if "@noheaders" in spec:
        noheaders = True
    if "@unique" in spec:
        unique = True
    if "@nolegend" in spec:
        legend = []
    assert isinstance(tab, str)  # mypy 0.9
    # render
    if fmt == "HTML":
        return tabtoHTML(data, headers, selected, legend=legend, tab=tab, padding=padding, xmlns=xmlns, minwidth=minwidth, section=section)
    if fmt == "JSON":
        return tabtoJSON(data, headers, selected, datedelim=datedelim, padding=padding, minwidth=minwidth, section=section)
    if fmt == "YAML":
        return tabtoYAML(data, headers, selected, datedelim=datedelim, padding=padding, minwidth=minwidth, section=section)
    if fmt == "TOML":
        return tabtoTOML(data, headers, selected, datedelim=datedelim, padding=padding, minwidth=minwidth, section=section)
    if fmt == "CSV":
        return tabtoCSV(data, headers, selected, datedelim=datedelim, tab=tab, noheaders=noheaders, unique=unique, minwidth=minwidth)
    if fmt == "XLS":
        return tabtoCSV(data, headers, selected, datedelim=datedelim, tab=tab, noheaders=noheaders, unique=unique, minwidth=minwidth)
    return tabtoGFM(data, headers, selected, legend=legend, tab=tab, padding=padding, noheaders=noheaders, unique=unique, minwidth=minwidth, section=section)

def tabToFMTx(output: str, result: Union[JSONList, JSONDict, DataList, DataItem],  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
              *, legend: LegendList = [], datedelim: str = '-', tab: str = "|", padding: str = " ",
              xmlns: str = "", section: str = NIX,
              noheaders: bool = False, combine: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        results = [result]
    elif _is_dataitem(result):
        results = [_dataitem_asdict(cast(DataItem, result))]
    elif hasattr(result, "__len__") and len(cast(List[Any], result)) and (_is_dataitem(cast(List[Any], result)[0])):
        results = list(_dataitem_asdict(cast(DataItem, item)) for item in cast(List[Any], result))
    else:
        results = cast(JSONList, result)  # type: ignore[redundant-cast]
    return tabToFMT(output, results, sorts, formats, selected, legend=legend,
                    datedelim=datedelim, tab=tab, padding=padding,
                    xmlns=xmlns, section=section,
                    noheaders=noheaders, combine=combine)
def tabToFMT(fmt: str, data: JSONList,  # ..
             sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
             *, legend: LegendList = [], datedelim: str = '-', tab: str = "|", padding: str = " ",
             xmlns: str = "", section: str = NIX,
             noheaders: bool = False, reorder: ColSortList = [], combine: Dict[str, str] = {}) -> str:
    # formats
    if fmt in ["html"]:
        fmt = "HTML"  # nopep8
    if fmt in ["htm"]:
        fmt = "HTML"
        tab = ""
        padding = ""  # nopep8
    if fmt in ["xhtm"]:
        fmt = "HTML"
        tab = ""
        padding = ""
        xmlns = "1999/xhtml"
    if fmt in ["xhtml"]:
        fmt = "HTML"
        xmlns = "1999/xhtml"
    if fmt in ["json"]:
        fmt = "JSON"  # nopep8
    if fmt in ["jsn"]:
        fmt = "JSON"
        padding = ""  # nopep8
    if fmt in ["yaml"]:
        fmt = "YAML"  # nopep8
    if fmt in ["yml"]:
        fmt = "YAML"
        padding = ""  # nopep8
    if fmt in ["toml"]:
        fmt = "TOML"  # nopep8
    if fmt in ["tml"]:
        fmt = "TOML"
        padding = ""  # nopep8
    if fmt in ["md"]:
        fmt = "GFM"  # nopep8
    if fmt in ["markdown"]:
        fmt = "GFM"
        tab = "||"  # nopep8
    if fmt in ["md2", "md3", "md4", "md5", "md6"]:
        fmt = "GFM"  # nopep8
    if fmt in ["txt"]:
        fmt = "GFM"
        padding = ""  # nopep8
    if fmt in ["text"]:
        fmt = "GFM"
        padding = ""
        noheaders = True  # nopep8
    if fmt in ["wide"]:
        fmt = "GFM"
        tab = ""  # nopep8
    if fmt in ["tabs"]:
        fmt = "GFM"
        tab = "\t"  # nopep8
    if fmt in ["tab"]:
        fmt = "CSV"
        tab = "\t"  # nopep8
    if fmt in ["data"]:
        fmt = "CSV"
        tab = "\t"
        noheaders = True  # nopep8
    if fmt in ["ifs"]:
        fmt = "CSV"
        tab = os.environ.get("IFS", "\t")  # nopep8
    if fmt in ["dat", "ifs"]:
        fmt = "CSV"
        tab = os.environ.get("IFS", "\t")
        noheaders = True  # nopep8
    if fmt in ["csv", "scsv"]:
        fmt = "CSV"
        tab = ";"  # nopep8
    if fmt in ["list"]:
        fmt = "CSV"
        tab = ";"
        noheaders = True  # nopep8
    if fmt in ["xlsx", "xls"]:
        fmt = "XLS"
        tab = ","  # nopep8
    # render
    if fmt == "HTML":
        return tabToHTML(data, sorts, formats, selected, tab=tab, xmlns=xmlns, padding=padding, legend=legend, section=section)
    if fmt == "JSON":
        return tabToJSON(data, sorts, formats, selected, padding=padding, datedelim=datedelim, section=section)
    if fmt == "YAML":
        return tabToYAML(data, sorts, formats, selected, padding=padding, datedelim=datedelim, section=section)
    if fmt == "TOML":
        return tabToTOML(data, sorts, formats, selected, padding=padding, datedelim=datedelim, section=section)
    if fmt == "CSV":
        return tabToCSV(data, sorts, formats, selected, datedelim=datedelim, tab=tab, noheaders=noheaders)
    if fmt == "XLS":
        return tabToCSV(data, sorts, formats, selected, datedelim=datedelim, tab=tab, noheaders=noheaders)
    return tabToGFM(data, sorts, formats, selected, legend=legend, tab=tab, padding=padding, noheaders=noheaders, section=section)

def saveToFMT(filename: str, fmt: str, result: JSONList,  # ..
              sorts: RowSortList = [], formats: FormatsDict = {}, selected: List[str] = [],  # ..
              *, datedelim: str = '-', legend: LegendList = [], reorder: ColSortList = []) -> str:
    fmt = fmt or extension(filename) or ""
    dat = tabToFMT(fmt, result, sorts, formats, selected, datedelim=datedelim, legend=legend, reorder=reorder)
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

def extension(filename: str) -> Optional[str]:
    _, ext = os.path.splitext(filename.lower())
    if ext: return ext[1:]
    return None

def readFromFile(filename: str, fmt: str = NIX, defaultfileformat: str = NIX) -> JSONList:
    tabtext = tabtextfile(filename, fmt, defaultfileformat=defaultfileformat)
    return tabtext.data
def readFromFMT(fmt: str, filename: str, defaultformat: str = NIX) -> JSONList:
    tabtext = tabtextfileFMT(fmt, filename, defaultformat=defaultformat)
    return tabtext.data
def tabtextfile(filename: str, fmt: str = NIX, *, tab: Optional[str] = None, section: str = NIX, defaultfileformat: str = NIX) -> TabText:
    if not fmt:
        fmt = extension(filename) or defaultfileformat
        if not fmt:
            logg.warning("could not detect format of '%s'", filename)
            return TabText([], [])
    # assert fmt
    return tabtextfileFMT(fmt, filename, tab=tab, defaultformat=defaultfileformat)
def tabtextfileFMT(fmt: str, filename: str, *, tab: Optional[str] = None, section: str = NIX, defaultformat: str = NIX) -> TabText:
    if not fmt:
        fmt = extension(filename) or NIX
        if not fmt:
            fmt = defaultformat
        if not fmt:
            return TabText([], [])
    if fmt.lower() in ["md", "markdown"]:
        return tabtextfileGFM(filename, tab='|' if tab is None else tab, section=section)
    if fmt.lower() in ["html", "htm", "xhtml"]:
        return tabtextfileHTML(filename, section=section)
    if fmt.lower() in ["json", "jsn"]:
        return tabtextfileJSON(filename, section=section)
    if fmt.lower() in ["yaml", "yml"]:
        return tabtextfileYAML(filename, section=section)
    if fmt.lower() in ["toml", "tml"]:
        return tabtextfileTOML(filename, section=section)
    if fmt.lower() in ["tab"]:
        return tabtextfileCSV(filename, tab='\t' if tab is None else tab)
    if fmt.lower() in ["csv", "scsv"]:
        return tabtextfileCSV(filename, tab=';' if tab is None else tab)
    if fmt.lower() in ["xlsx", "xls"]:
        try:
            if TABXLSX:
                import tabxlsx
                found1 = tabxlsx.tablistfileXLSX(filename)  # type: ignore[return-value]
                if section:
                    for tabsheet1 in found1:
                        if tabsheet1.title == section:
                            return TabText(cast(JSONList, tabsheet1.data), tabsheet1.headers)
                elif found1:
                    return TabText(cast(JSONList, found1[0].data), found1[0].headers)
            else:
                import tabtoxlsx
                found2 = tabtoxlsx.tablistfileXLSX(filename)
                if section:
                    for tabsheet2 in found1:
                        if tabsheet2.title == section:
                            return TabText(cast(JSONList, tabsheet2.data), tabsheet2.headers)
                elif found2:
                    return TabText(cast(JSONList, found2[0].data), found2[0].headers)
        except Exception as e:
            if not TABXLSX:
                import tabxlsx
                found3 = tabxlsx.tablistfileXLSX(filename)  # type: ignore[return-value]
                if section:
                    for tabsheet3 in found1:
                        if tabsheet3.title == section:
                            return TabText(cast(JSONList, tabsheet3.data), tabsheet3.headers)
                elif found2:
                    return TabText(cast(JSONList, found3[0].data), found3[0].headers)
            else:
                logg.error("could not load xslx: %s", e)
        return TabText([], [])
    logg.debug(" tabtextfileFMT  - unrecognized input format %s: %s", fmt, filename)
    return TabText([], [])

def tablistfile(filename: str, fmt: str = NIX, *, tab: Optional[str] = None, defaultfileformat: str = NIX) -> List[TabSheet]:
    if not fmt:
        fmt = extension(filename) or defaultfileformat
        if not fmt:
            logg.warning("could not detect format of '%s'", filename)
            return []
    # assert fmt
    return tablistfileFMT(fmt, filename, tab=tab, defaultformat=defaultfileformat)
def tablistfileFMT(fmt: str, filename: str, *, tab: Optional[str] = None, section: str = NIX, defaultformat: str = NIX) -> List[TabSheet]:
    if not fmt:
        fmt = extension(filename) or NIX
        if not fmt:
            fmt = defaultformat
        if not fmt:
            return []
    if fmt.lower() in ["md", "markdown"]:
        return tablistfileGFM(filename, tab='|' if tab is None else tab, section=section)
    if fmt.lower() in ["html", "htm", "xhtml"]:
        tabtext = tabtextfileHTML(filename, section=section)
        return [TabSheet(tabtext.data, tabtext.headers, section or SECTION)]
    if fmt.lower() in ["json", "jsn"]:
        return tablistfileJSON(filename, section=section)
    if fmt.lower() in ["yaml", "yml"]:
        tabtext = tabtextfileYAML(filename, section=section)
        return [TabSheet(tabtext.data, tabtext.headers, section or SECTION)]
    if fmt.lower() in ["toml", "tml"]:
        tabtext = tabtextfileTOML(filename, section=section)
        return [TabSheet(tabtext.data, tabtext.headers, section or SECTION)]
    if fmt.lower() in ["tab"]:
        tabtext = tabtextfileCSV(filename, tab='\t' if tab is None else tab)
        return [TabSheet(tabtext.data, tabtext.headers, section or SECTION)]
    if fmt.lower() in ["csv", "scsv"]:
        tabtext = tabtextfileCSV(filename, tab=';' if tab is None else tab)
        return [TabSheet(tabtext.data, tabtext.headers, section or SECTION)]
    if fmt.lower() in ["xlsx", "xls"]:
        try:
            if TABXLSX:
                import tabxlsx
                found1 = tabxlsx.tablistfileXLSX(filename)  # type: ignore[return-value]
                return cast(List[TabSheet], found1)
            else:
                import tabtoxlsx
                found2 = tabtoxlsx.tablistfileXLSX(filename)
                return found2
        except Exception as e:
            if not TABXLSX:
                import tabxlsx
                found3 = tabxlsx.tablistfileXLSX(filename)  # type: ignore[return-value]
                return cast(List[TabSheet], found3)
            else:
                logg.error("could not load xslx: %s", e)
        return []
    logg.debug(" tablistfileFMT  - unrecognized input format %s: %s", fmt, filename)
    return []

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
    FMT = fmt or extension(OUTPUT) or "md"
    if OUTPUT in ["", "-", "CON"]:
        print(tabToFMT(FMT, data, formats=formats, sorts=sorts, reorder=reorder, datedelim=datedelim, legend=legend))
    elif OUTPUT:
        if FMT in ["xls", "xlsx"]:
            if TABXLSX:
                import tabxlsx
                tabxlsx.tabtoXLSX(OUTPUT, data, sorts)  # type: ignore[arg-type]
            else:
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
    fileformat = fileformat or extension(filename) or "md"
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
    hint = "Use @dat to print only"
    prog = os.path.basename(__file__)
    cmdline = OptionParser(
        prog + " file(.csv|.json|.xlsx) [column...] [@format...]", epilog=__doc__ + hint, version=__version__)
    cmdline.formatter.max_help_position = 30
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="more verbose logging")
    cmdline.add_option("-^", "--quiet", action="count", default=0, help="less verbose logging")
    cmdline.add_option("-X", "--tabxlsx", action="store_true", default=False,
                       help="quick xlsx with tabxlsx instead of openpyxl")
    cmdline.add_option("-m", "--minwidth", metavar="N", default=0,
                       help="override minwith of  cells for format")
    cmdline.add_option("-d", "--datedelim", metavar="C", default=None,
                       help="override date delimiter for format")
    cmdline.add_option("-p", "--padding", metavar="C", default=None,
                       help="override cell padding for format")
    cmdline.add_option("-t", "--tabulator", metavar="C", default=None,
                       help="override tabulator for format")
    cmdline.add_option("-T", "--asciitab", action="store_true", default=False,
                       help="use ascii HT tabulator (csv,md,tab,wide)")
    cmdline.add_option("-N", "--notab", action="store_true", default=False,
                       help="do not use tabulator (csv,md,tab,wide)")
    cmdline.add_option("-P", "--nopadding", action="store_true", default=False,
                       help="do not use padding (csv,md,tab,wide,html)")
    cmdline.add_option("-D", "--noheaders", action="store_true", default=False,
                       help="do not print headers (csv,md,tab,wide)")
    cmdline.add_option("-U", "--unique", action="store_true", default=False,
                       help="remove same lines in sorted list (csv,md,...)")
    cmdline.add_option("-L", "--labels", metavar="LIST", action="append", default=[],
                       help="add columns to show (a|b:.2f)")
    cmdline.add_option("-i", "--inputformat", metavar="FMT", default="",
                       help="fix input format (instead of autodetection)")
    cmdline.add_option("-o", "--output", "--format", metavar="FMT", default="",
                       help="(file.)json|yaml|html|wide|md|htm|tab|csv")
    opt, args = cmdline.parse_args()
    logging.basicConfig(level=max(0, logging.WARNING - 10 * opt.verbose + 10 * opt.quiet))
    TABXLSX = opt.tabxlsx
    if not args:
        cmdline.print_help()
    else:
        selected = []
        filename = args[0]
        if len(args) > 1:
            selected = args[1:] + opt.labels
        else:
            selected = opt.labels
        minwidth = int(opt.minwidth)
        padding = opt.padding if not opt.nopadding else ""
        tab = "\t" if opt.asciitab else opt.tabulator if not opt.notab else ""
        tabtext = tabtextfile(filename, opt.inputformat)
        done = print_tabtotext(opt.output, tabtext.data, tabtext.headers, selected,
                               datedelim=opt.datedelim, tab=tab, padding=padding,
                               noheaders=opt.noheaders, unique=opt.unique, minwidth=minwidth)
        if done:
            logg.log(DONE, " %s", done)
