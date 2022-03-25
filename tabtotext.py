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
from datetime import date
from datetime import datetime as date_time
import os
import re
import logging
import json
import zipfile
from io import BytesIO, StringIO

logg = logging.getLogger("TABTOTEXT")

DATEFMT = "%Y-%m-%d"
NORIGHT = False

JSONItem = Union[str, int, float, bool, date, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONItem]
JSONList = List[JSONDict]
JSONDictList = Dict[str, JSONList]
JSONDictDict = Dict[str, JSONDict]

def setNoRight(value: bool) -> None:
    global NORIGHT
    NORIGHT = value

def strNone(value: Any) -> str:
    if value is None:
        return "-"
    if value is False:
        return "(no)"
    if value is True:
        return "(yes)"
    if isinstance(value, date_time):
        return value.strftime(DATEFMT)
    return str(value)

def tabToGFMx(result: Union[JSONList, JSONDict], sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        result = [result]
    return tabToGFM(result)
def tabToGFM(result: JSONList, sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}) -> str:
    def sortkey(header: str) -> str:
        if header in sorts:
            return str(sorts.index(header))
        return header
    def sortrow(item: JSONDict) -> str:
        sortvalue = ""
        for sort in sorts:
            if sort in item:
                value = item[sort]
                if isinstance(value, int):
                    sortvalue += "\n%020i" % value
                elif isinstance(value, date_time):
                    sortvalue += "\n" + value.strftime(DATEFMT)
                else:
                    sortvalue += "\n" + str(value)
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
def tabToHTMLx(result: Union[JSONList, JSONDict], sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        result = [result]
    return tabToGFM(result)
def tabToHTML(result: JSONList, sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}) -> str:
    def sortkey(header: str) -> str:
        if header in sorts:
            return str(sorts.index(header))
        return header
    def sortrow(item: JSONDict) -> str:
        sortvalue = ""
        for sort in sorts:
            if sort in item:
                value = item[sort]
                if isinstance(value, int):
                    sortvalue += "\n%020i" % value
                elif isinstance(value, date_time):
                    sortvalue += "\n" + value.strftime(DATEFMT)
                else:
                    sortvalue += "\n" + str(value)
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
