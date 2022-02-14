#! /usr/bin/python3
"""
This script reimplements the queries/*.sql that have been used in Userlist.sh
but instead of using the Postgres API it uses the Crowd API.

// Please be aware the --appuser/--password represent crowd-application credentials (not a build user)
"""

from typing import Optional, Union, Dict, List, Any
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

DATEFMT="%Y-%m-%d"

def strNone(value : Any) -> str:
    if value is None:
        return "-"
    if value is False:
        return "(no)"
    if value is True:
        return "(yes)"
    if isinstance(value, date_time):
        return value.strftime(DATEFMT)
    return str(value)

def tabToGFM(result : Union[List[Dict[str, Any]], Dict[str, Any]], sorts = ["email"], parens = []) -> str:
    if isinstance(result, Dict):
        result = [ result ]
    def sortkey(header):
        if header in sorts:
            return str(sorts.index(header))
        return header
    def sortrow(item):
        sortvalue = ""
        for sort in sorts:
            if sort in item:
                if isinstance(item[sort], int):
                    sortvalue += "\n%020i" % item[sort]
                elif isinstance(item[sort], date_time):
                    sortvalue += "\n"+item[sort].strftime(DATEFMT)
                else:
                    sortvalue += "\n"+str(item[sort])
            else:
                sortvalue += "\n-"
        return sortvalue
    def px(col, val):
        if col in parens:
           return "(%s)" % val
        return val
    cols : Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            if name not in cols:
                cols[name] = max(5, len(name))
            cols[name] = max(cols[name], len(str(value)))
    templates = [ "| %%-%is" % cols[name] for name in sorted(cols.keys(), key = sortkey ) ]
    template = " ".join(templates)
    logg.debug("template [%s] = %s", len(templates), template)
    logg.debug("colskeys [%s] = %s", len(cols.keys()), sorted(cols.keys(), key = sortkey))
    lines = [ template % tuple(sorted(cols.keys(), key = sortkey)) ]
    seperators = [ ("-" * cols[name]) for name in sorted(cols.keys(), key = sortkey) ]
    lines.append( template % tuple(seperators))
    for item in sorted(result, key = sortrow):
        values = dict([ (name, "") for name in cols.keys()])
        # logg.debug("values = %s", values)
        for name, value in item.items():
            values[name] = value
        line = template % tuple([ strNone(px(name, values[name])) for name in sorted(cols.keys(), key = sortkey) ])
        lines.append(line)
    return "\n".join(lines) + "\n"
def tabToHTML(result : Union[List[Dict[str, Any]], Dict[str, Any]], sorts = ["email"], parens = []) -> str:
    if isinstance(result, Dict):
        result = [ result ]
    def sortkey(header):
        if header in sorts:
            return str(sorts.index(header))
        return header
    def sortrow(item):
        sortvalue = ""
        for sort in sorts:
            if sort in item:
                if isinstance(item[sort], int):
                    sortvalue += "\n%020i" % item[sort]
                elif isinstance(item[sort], date_time):
                    sortvalue += "\n"+item[sort].strftime(DATEFMT)
                else:
                    sortvalue += "\n"+str(item[sort])
            else:
                sortvalue += "\n-"
        return sortvalue
    def px(col, val):
        if col in parens:
           return "(%s)" % val
        return val
    cols : Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            if name not in cols:
                cols[name] = max(5, len(name))
            cols[name] = max(cols[name], len(str(value)))
    line = [ ("<th>%s</th>" % escape(name)) for name in sorted(cols.keys(), key = sortkey) ]
    lines = [ "<tr>" +  "".join(line) + "</tr>" ]
    for item in sorted(result, key = sortrow):
        values = dict([ (name, "") for name in cols.keys()])
        # logg.debug("values = %s", values)
        for name, value in item.items():
            values[name] = value
        line = [ ("<td>%s</td>" % escape(strNone(px(name, values[name])))) for name in sorted(cols.keys(), key = sortkey) ]
        lines.append( "<tr>" + "".join(line) + "</tr>" )
    return "<table>\n" + "\n".join(lines) + "\n</table>\n"
