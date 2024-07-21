#! /usr/bin/env python3
""" Subset of tabtotext """

from typing import Optional, Union, Dict, List, Any, Sequence, Callable, Type, cast, Iterable, Iterator
from datetime import date as Date
from datetime import datetime as Time
import re
import logging
from io import StringIO, TextIOWrapper

logg = logging.getLogger("tabToFMT")

JSONItem = Union[str, int, float, bool, Date, Time, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONItem]
JSONList = List[JSONDict]
RowSortList = Union[Sequence[str], Dict[str, str], Callable[[JSONDict], str]]
ColSortList = Union[Sequence[str], Dict[str, str], Callable[[str], str]]
LegendList = Union[Dict[str, str], Sequence[str]]

def tabToFMT(fmt: str, result: JSONList, sorts: RowSortList = [], formats: Dict[str, str] = {}, *,  #
             datedelim: str = '-', legend: LegendList = [],  #
             reorder: ColSortList = [], combine: Dict[str, str] = {}) -> str:
    """ This code is supposed to be copy-n-paste into other files. You can safely try-import from 
        tabtotext or tabtoxlsx to override this function. Only a subset of features is supported. """
    tab = '|'
    if fmt in ["wide", "text"]:
        tab = ''
    if fmt in ["tabs", "tab", "dat", "ifs", "data"]:
        tab = '\t'
    if fmt in ["csv", "scsv", "list"]:
        tab = ';'
    if fmt in ["xls", "sxlx"]:
        tab = ','
    none_string = "~"
    true_string = "(yes)"
    false_string = "(no)"
    minwidth = 5
    floatfmt = "%4.2f"
    noright = fmt in ["dat"]
    noheaders = fmt in ["text", "list"]
    formatright = re.compile("[{]:[^{}]*>[^{}]*[}]")
    formatnumber = re.compile("[{]:[^{}]*[defghDEFGHMQR$%][}]")
    def rightalign(col: str) -> bool:
        if col in formats and not noright:
            if formats[col].startswith(" "):
                return True
            if formatright.search(formats[col]):
                return True
            if formatnumber.search(formats[col]):
                return True
        return False
    def format(name: str, val: JSONItem) -> str:
        if name in formats:
            fmt4 = formats[name]
            if "{:" in fmt4:
                try:
                    return fmt4.format(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", fmt, e)
            if "%s" in fmt4:
                try:
                    return fmt % strJSON(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", fmt, e)
        if isinstance(val, float):
            return floatfmt % val
        return strJSON(val)
    def strJSON(value: JSONItem) -> str:
        if value is None: return none_string
        if value is False: return false_string
        if value is True: return true_string
        if isinstance(value, Time):
            return value.strftime("%Y-%m-%d.%H%M")
        if isinstance(value, Date):
            return value.strftime("%Y-%m-%d")
        return str(value)
    def asdict(item: JSONDict) -> JSONDict:
        if hasattr(item, "_asdict"):
            return item._asdict()  # type: ignore[union-attr, no-any-return, arg-type]
        return item
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in asdict(item).items():
            if name not in cols:
                cols[name] = max(minwidth, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    def sortkey(header: str) -> str:
        if callable(reorder):
            return reorder(header)
        else:
            sortheaders = reorder
            if not sortheaders and not callable(sorts):
                sortheaders = sorts
            if isinstance(sortheaders, dict):
                if header in sortheaders:
                    return sortheaders[header]
            else:
                if header in sortheaders:
                    return "%07i" % sortheaders.index(header)
        return header
    def sortrow(row: JSONDict) -> str:
        item = asdict(row)
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
                    else:
                        sortvalue += "\n" + strJSON(value)
                else:
                    sortvalue += "\n?"
            return sortvalue
    # CSV
    if fmt in ["list", "csv", "scsv", "xlsx", "xls", "tab", "dat", "ifs", "data"]:
        tab1 = tab if tab else ";"
        import csv
        csvfile = StringIO()
        writer = csv.DictWriter(csvfile, fieldnames=sorted(cols.keys(), key=sortkey),
                                restval='~', quoting=csv.QUOTE_MINIMAL, delimiter=tab1)
        if not noheaders:
            writer.writeheader()
        for row in sorted(result, key=sortrow):
            rowvalues: Dict[str, str] = {}
            for name, value in asdict(row).items():
                rowvalues[name] = format(name, value)
            writer.writerow(rowvalues)
        return cast(str, csvfile.getvalue())  # type: ignore[redundant-cast]
    # GFM
    def rightF(col: str, formatter: str) -> str:
        if rightalign(col):
            return formatter.replace("%-", "%")
        return formatter
    def rightS(col: str, formatter: str) -> str:
        if rightalign(col):
            return formatter[:-1] + ":"
        return formatter
    tab2 = (tab + " " if tab else "")
    lines: List[str] = []
    if not noheaders:
        line = [rightF(name, tab2 + "%%-%is" % cols[name]) % name for name in sorted(cols.keys(), key=sortkey)]
        lines += [(" ".join(line)).rstrip()]
        if tab:
            seperators = [(tab2 + "%%-%is" % cols[name]) % rightS(name, "-" * cols[name])
                          for name in sorted(cols.keys(), key=sortkey)]
            lines.append(" ".join(seperators))
    for item in sorted(result, key=sortrow):
        values: Dict[str, str] = {}
        for name, value in asdict(item).items():
            values[name] = format(name, value)
        line = [rightF(name, tab2 + "%%-%is" % cols[name]) % values.get(name, none_string)
                for name in sorted(cols.keys(), key=sortkey)]
        lines.append((" ".join(line)).rstrip())
    return "\n".join(lines) + "\n"
