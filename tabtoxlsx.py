#! /usr/bin/python3
from typing import Optional, Union, Dict, List, Any, Sequence
from tabtotext import JSONList, JSONDict, tabToGFM, strNone

from openpyxl import Workbook
from openpyxl.styles.cell_style import CellStyle as Style
from openpyxl.styles.alignment import Alignment
from openpyxl.styles.numbers import NumberFormat, builtin_format_id
from openpyxl.utils import get_column_letter

import datetime
DayOrTime = (datetime.date, datetime.datetime)

MINWIDTH = 7

import logging
logg = logging.getLogger("TABTOXLSX")

def set_cell(ws, row, col, value, style):
    coordinate = { "column": col+1, "row": row+1 }
    ws.cell(**coordinate).value = value
    # ws.cell(**coordinate).font = style.font
    # ws.cell(**coordinate).fill = style.fill
    # ws.cell(**coordinate).border = style.border
    ws.cell(**coordinate).alignment = style.alignment
    ws.cell(**coordinate).number_format = style.number_format
    ws.cell(**coordinate).protection = style.protection
def set_width(ws, col, width):
    ws.column_dimensions[get_column_letter(col+1)].width = width


def saveToXLSXx(filename:str, result: Union[JSONList, JSONDict], sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        result = [result]
    return saveToXLSX(filename, result)

def saveToXLSX(filename: str, result: JSONList, sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}) -> str:
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
                elif isinstance(value, DayOrTime):
                    sortvalue += "\n" + value.strftime(DATEFMT)
                else:
                    sortvalue += "\n" + str(value)
            else:
                sortvalue += "\n-"
        return sortvalue
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in item.items():
            paren = 0
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(strNone(value)))
    #
    row = 0
    workbook = Workbook()
    ws = workbook.active
    style = Style()
    text_style = Style()
    text_style.number_format = 'General'
    text_style.alignment = Alignment(horizontal = 'left')
    date_style = Style()
    date_style.number_format = 'd.mm.yy'
    date_style.alignment = Alignment(horizontal = 'right')
    numm_style = Style()
    numm_style.number_format = '#,##0.00'
    numm_style.alignment = Alignment(horizontal = 'right')
    col = 0
    for name in sorted(cols.keys(), key=sortkey):
        set_cell(ws, row, col, name, text_style)
        set_width(ws, col, cols[name])
        col += 1
    row += 1
    for item in sorted(result, key=sortrow):
        values: JSONDict = dict([(name, "") for name in cols.keys()])
        for name, value in item.items():
            values[name] = value
        col = 0
        for name in sorted(cols.keys(), key=sortkey):
            value = values[name]
            if value is None:
                pass
            elif isinstance(value, DayOrTime):
                set_cell(ws, row, col, value, date_style)
            elif isinstance(value, (int, float)):
                set_cell(ws, row, col, value, numm_style)
            else:
                set_cell(ws, row, col, value, text_style)
            col += 1
        row += 1
    workbook.save(filename)
