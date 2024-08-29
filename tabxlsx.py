#! /usr/bin/env python3
""" 
TabXLSX reads and writes Excel xlsx files. It does not depend on other libraries.
The output can be piped as a markdown table or csv-like data as well. A number
of output format options are available but less than the tabtotext.py module."""

__copyright__ = "(C) 2023-2024 Guido Draheim, licensed under the Apache License 2.0"""
__version__ = "1.6.3352"

from typing import Union, List, Dict, cast, Tuple, Optional, TextIO, Iterable, NamedTuple, Mapping, TypeVar, Generic
from datetime import date as Date
from datetime import datetime as Time
from datetime import timedelta as Plus
from datetime import timezone as TimeZone
from io import StringIO, TextIOWrapper
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
import os.path as fs
import os
import re

# The functions in this script mimic those of openpyxl - we only implement what we need for tabtoxlsx
# (actually, we make an export with openpyxl and then we adapt the code here to generate the same bytes)
# from openpyxl import Workbook, load_workbook
# from openpyxl.worksheet.worksheet import Worksheet
# from openpyxl.styles.cell_style import CellStyle as Style
# from openpyxl.styles.alignment import Alignment
# from openpyxl.utils import get_column_letter
# (have a look at 'make_workbook' for the generation part)

from logging import getLogger
logg = getLogger("TABXLSX")

SECTION = "data"
DATEFMT = "%Y-%m-%d"
TIMEFMT = "%Y-%m-%d.%H%M"
FLOATFMT = "%4.2f"
MINWIDTH = 5
MAXCOL = 1000
MAXROWS = 100000
NIX = ""

def get_column_letter(num: int) -> str:
    return chr(ord('A') + (num - 1))

class Alignment:
    horizontal: str
    def __init__(self, *, horizontal: str = NIX) -> None:
        self.horizontal = horizontal

class CellStyle:
    alignment: Alignment
    number_format: str
    protection: str
    def __init__(self, *, number_format: str = NIX, protection: str = NIX) -> None:
        self.alignment = Alignment()
        self.number_format = number_format
        self.protection = protection

CellValue = Union[None, bool, int, float, str, Time, Date]

class Cell:
    value: CellValue
    data_type: str
    alignment: Optional[Alignment]
    number_format: Optional[str]
    protection: Optional[str]
    _xf: int
    _numFmt: int
    def __init__(self) -> None:
        self.value = None
        self.data_type = NIX
        self.alignment = None
        self.number_format = None
        self.protection = None
        self._xf = 0
        self._numFmt = 0
    def __str__(self) -> str:
        return str(self.value)
    def __repr__(self) -> str:
        return str(self.value)

class Dimension:
    width: int
    def __init__(self, *, width: int = 8) -> None:
        self.width = width
class DimensionsHolder:
    columns: Dict[str, Dimension]
    def __init__(self) -> None:
        self.columns = {}
    def __getitem__(self, column: str) -> Dimension:
        if column not in self.columns:
            self.columns[column] = Dimension()
        return self.columns[column]

class Worksheet:
    rows: List[Dict[str, Cell]]
    title: str
    column_dimensions: DimensionsHolder
    _mindim: str
    _maxdim: str
    def __init__(self, title: str = NIX) -> None:
        self.title = title
        self.rows = []
        self.column_dimensions = DimensionsHolder()
    def cell(self, row: int, column: int) -> Cell:
        atrow = row - 1
        name = get_column_letter(column) + str(row)
        while atrow >= len(self.rows):
            self.rows.append({})
        if name not in self.rows[atrow]:
            self.rows[atrow][name] = Cell()
        return self.rows[atrow][name]
    def __getitem__(self, name: str) -> Cell:
        m = re.match("([A-Z]+)([0-9]+)", name)
        if not m:
            logg.error("can not check %s", name)
            raise ValueError(name)
        atrow = int(m.group(2)) - 1
        while atrow >= len(self.rows):
            self.rows.append({})
        if name not in self.rows[atrow]:
            self.rows[atrow][name] = Cell()
        return self.rows[atrow][name]

class Workbook:
    sheets: List[Worksheet]
    current: int
    def __init__(self) -> None:
        self.sheets = [Worksheet()]
        self.current = 0
    @property
    def active(self) -> Worksheet:
        return self.sheets[self.current]
    def create_sheet(self) -> Worksheet:
        ws = Worksheet()
        self.current = len(self.sheets)
        self.sheets.append(ws)
        return ws
    def save(self, filename: str) -> None:
        save_workbook(filename, self)

def save_workbook(filename: str, workbook: Workbook) -> None:
    xmlns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    xmlns_r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    xmlns_p = "http://schemas.openxmlformats.org/package/2006/relationships"
    xmlns_w = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    xmlns_s = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
    xmlns_t = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
    xmlns_c = "http://schemas.openxmlformats.org/package/2006/content-types"
    NUMFMT = 164
    numFmts: List[str] = ["yyyy-mm-dd h:mm:ss"]
    for sheet in workbook.sheets:
        sheet._mindim = ""
        sheet._maxdim = ""
        for row in sheet.rows:
            for cellname, cell in row.items():
                if not sheet._mindim:
                    sheet._mindim = cellname
                    sheet._maxdim = cellname
                if cellname < sheet._mindim:
                    sheet._mindim = cellname
                if cellname > sheet._maxdim:
                    sheet._maxdim = cellname
                if cell.number_format:
                    if cell.number_format in ["General"]:
                        continue
                    if cell.number_format not in numFmts:
                        numFmts.append(cell.number_format)
                    cell._numFmt = NUMFMT + numFmts.index(cell.number_format)
    cellXfs: List[str] = []
    for sheet in workbook.sheets:
        for row in sheet.rows:
            for cell in row.values():
                numFmtId = cell._numFmt
                applyAlignment = 0
                xml_alignment = ""
                if cell.alignment and cell.alignment.horizontal:
                    applyAlignment = 1
                    horizontal = cell.alignment.horizontal
                    xml_alignment = F'<alignment horizontal="{horizontal}"/>'
                xml_xf = F'<xf'
                xml_xf += F' numFmtId="{numFmtId}"'
                xml_xf += F' fontId="0"'
                xml_xf += F' fillId="0"'
                xml_xf += F' borderId="0"'
                xml_xf += F' applyAlignment="{applyAlignment}"'
                xml_xf += F' pivotButton="0"'
                xml_xf += F' quotePrefix="0"'
                xml_xf += F' xfId="0"'
                xml_xf += '>'
                xml_xf += xml_alignment
                xml_xf += F'</xf>'
                if xml_xf not in cellXfs:
                    cellXfs.append(xml_xf)
                cell._xf = cellXfs.index(xml_xf) + 1
    style_xml = F'<styleSheet xmlns="{xmlns}">'
    style_xml += F'<numFmts count="{len(numFmts)}">'
    for num, fmtCode in enumerate(numFmts):
        numFmtId = NUMFMT + num
        style_xml += F'<numFmt numFmtId="{numFmtId}" formatCode="{fmtCode}"/>'
    style_xml += F'</numFmts>'
    style_xml += F'<fonts count="1"><font><name val="Calibri"/>'
    style_xml += F'<family val="2"/><color theme="1"/><sz val="11"/>'
    style_xml += F'<scheme val="minor"/></font></fonts>'
    # style_xml += f'<fills count="1" /><fill><patternFill/></fill></fills>'
    style_xml += f'<fills count="2"><fill><patternFill/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
    style_xml += F'<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
    style_xml += F'<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    style_xml += F'<cellXfs count="{len(cellXfs)+1}">'
    style_xml += F'<xf numFmtId="0" fontId="0" fillId="0" borderId="0" pivotButton="0" quotePrefix="0" xfId="0"/>'
    for xf in cellXfs:
        style_xml += xf
    style_xml += F'</cellXfs>'
    style_xml += F'<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0" hidden="0"/></cellStyles>'
    style_xml += F'<tableStyles count="0" defaultTableStyle="TableStyleMedium9" defaultPivotStyle="PivotStyleLight16"/>'
    style_xml += F'</styleSheet>'
    workbook_xml = F'<workbook xmlns="{xmlns}">'
    workbook_xml += F'<workbookPr/>'
    workbook_xml += F'<workbookProtection/>'
    # workbook_xml += F'<bookViews/>'
    workbook_xml += F'<bookViews><workbookView visibility="visible" minimized="0" showHorizontalScroll="1" showVerticalScroll="1" showSheetTabs="1" tabRatio="600" firstSheet="0" activeTab="0" autoFilterDateGrouping="1"/></bookViews>'
    workbook_xml += F'<sheets>'
    worksheets: List[str] = []
    for sheet in workbook.sheets:
        wxml = F'<worksheet xmlns="{xmlns}">'
        wxml += '<sheetPr><outlinePr summaryBelow="1" summaryRight="1"/><pageSetUpPr/></sheetPr>'
        wxml += F'<dimension ref="{sheet._mindim}:{sheet._maxdim}"/>'
        wxml += '<sheetViews><sheetView workbookViewId="0"><selection activeCell="A1" sqref="A1"/></sheetView></sheetViews>'
        wxml += '<sheetFormatPr baseColWidth="8" defaultRowHeight="15"/>'
        if sheet.column_dimensions.columns:
            wxml += F'<cols>'
            for nam, col in sheet.column_dimensions.columns.items():
                wxml += F'<col width="{col.width}" customWidth="1" min="1" max="1"/>'
            wxml += F'</cols>'
        wxml += F'<sheetData>'
        for num, row in enumerate(sheet.rows):
            if not row: continue  # empty
            wxml += F'<row r="{num+1}">'
            for r, cell in row.items():
                if cell.value is None:
                    continue
                elif isinstance(cell.value, str):
                    if cell.data_type in ["", "f"] and cell.value.startswith("="):
                        s = cell._xf
                        f = cell.value[1:]
                        wxml += F'<c r="{r}" s="{s}">'
                        wxml += F'<f>{f}</f>'
                        wxml += F'</c>'
                    else:
                        s = cell._xf
                        t = "inlineStr"
                        wxml += F'<c r="{r}" s="{s}" t="{t}">'
                        wxml += F'<is><t>{cell.value}</t></is>'
                        wxml += F'</c>'
                else:
                    value: Union[int, float]
                    t = "n"
                    if isinstance(cell.value, bool):
                        value = 1 if cell.value else 0
                        t = 'b'
                    elif isinstance(cell.value, Time):
                        value = cell.value.toordinal() - 693594.
                        seconds = cell.value.hour * 3600 + cell.value.minute * 60 + cell.value.second
                        value += seconds / 86400.
                    elif isinstance(cell.value, Date):
                        value = cell.value.toordinal() - 693594.
                    else:
                        value = cell.value
                    s = cell._xf
                    # wxml += F'<c r="{r}" s="{s}">'
                    wxml += F'<c r="{r}" s="{s}" t="{t}">'
                    wxml += F'<v>{value}</v>'
                    wxml += F'</c>'
            wxml += F'</row>'
        wxml += F'</sheetData>'
        wxml += F'<pageMargins left="0.75" right="0.75" top="1" bottom="1" header="0.5" footer="0.5"/>'
        wxml += F'</worksheet>'
        worksheets.append(wxml)
        workbook_xml += F'<sheet xmlns:r="{xmlns_r}" name="{sheet.title}"'
        workbook_xml += F' sheetId="{len(worksheets)}"'
        workbook_xml += F' state="visible"'
        workbook_xml += F' r:id="rId{len(worksheets)}"/>'
    workbook_xml += F'</sheets>'
    workbook_xml += F'<definedNames/><calcPr calcId="124519" fullCalcOnLoad="1"/>'
    workbook_xml += F'</workbook>'
    theme_xml = F'<?xml version="1.0"?>' + "\n"
    theme_xml = F'<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">'
    theme_xml = F'<a:themeElements/><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>'
    with ZipFile(filename, "w", compression=ZIP_DEFLATED) as zipfile:
        worksheetfilelist = []
        rels_xml = F'<Relationships xmlns="{xmlns_p}">'
        for num, xml in enumerate(worksheets):
            worksheetfile = F'worksheets/sheet{num+1}.xml'
            worksheet_Id = F'rId{num+1}'
            rels_xml += F'<Relationship Type="{xmlns_w}"'
            rels_xml += F' Target="/xl/{worksheetfile}" Id="{worksheet_Id}"/>'
            with zipfile.open("xl/" + worksheetfile, "w") as xmlfile:
                xmlfile.write(xml.encode('utf-8'))
            worksheetfilelist += [worksheetfile]
        stylefile = F"styles.xml"
        style_Id = F'rId{len(worksheets)+1}'
        rels_xml += F'<Relationship Type="{xmlns_s}"'
        rels_xml += F' Target="{stylefile}" Id="{style_Id}"/>'
        with zipfile.open("xl/" + stylefile, "w") as xmlfile:
            xmlfile.write(style_xml.encode('utf-8'))
        themefile = F"theme/theme1.xml"
        theme_Id = F'rId{len(worksheets)+2}'
        rels_xml += F'<Relationship Type="{xmlns_t}"'
        rels_xml += F' Target="{themefile}" Id="{theme_Id}"/>'
        with zipfile.open("xl/" + themefile, "w") as xmlfile:
            xmlfile.write(theme_xml.encode('utf-8'))
        rels_xml += F'</Relationships>'
        workbookfile = "workbook.xml"
        with zipfile.open("xl/" + workbookfile, "w") as xmlfile:
            xmlfile.write(workbook_xml.encode('utf-8'))
        relsfile = "_rels/workbook.xml.rels"
        with zipfile.open("xl/" + relsfile, "w") as xmlfile:
            xmlfile.write(rels_xml.encode('utf-8'))
        apps_xml = F'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Microsoft Excel</Application><AppVersion>3.0</AppVersion></Properties>'
        appsfile = "docProps/app.xml"
        core_xml = F'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"><dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">openpyxl</dc:creator><dcterms:created xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="dcterms:W3CDTF">2024-07-09T21:58:37Z</dcterms:created><dcterms:modified xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="dcterms:W3CDTF">2024-07-09T21:58:37Z</dcterms:modified></cp:coreProperties>'
        corefile = "docProps/core.xml"
        with zipfile.open(appsfile, "w") as xmlfile:
            xmlfile.write(apps_xml.encode('utf-8'))
        with zipfile.open(corefile, "w") as xmlfile:
            xmlfile.write(core_xml.encode('utf-8'))
        init_xml = F'<Relationships xmlns="{xmlns_p}">'
        init_xml += F'<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/{workbookfile}" Id="rId1"/>'
        init_xml += F'<Relationship Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml" Id="rId2"/>'
        init_xml += F'<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml" Id="rId3"/>'
        init_xml += F'</Relationships>'
        initfile = "_rels/.rels"
        with zipfile.open(initfile, "w") as xmlfile:
            xmlfile.write(init_xml.encode('utf-8'))
        content_xml = F'<Types xmlns="{xmlns_c}">'
        content_xml += '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        content_xml += '<Default Extension="xml" ContentType="application/xml"/>'
        content_xml += '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        content_xml += '<Override PartName="/xl/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
        content_xml += '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        content_xml += '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        # content_xml += '<Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for worksheetfile in worksheetfilelist:
            content_xml += F'<Override PartName="/xl/{worksheetfile}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        content_xml += '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        content_xml += '</Types>'
        contentfile = "[Content_Types].xml"
        with zipfile.open(contentfile, "w") as xmlfile:
            xmlfile.write(content_xml.encode('utf-8'))

_dateformats = ['d.mm.yy', 'yyyy-mm-dd']
_timeformats = ['yyyy-mm-dd hh:mm', 'yyyy-mm-dd h:mm:ss']
def load_workbook(filename: str) -> Workbook:
    workbook = Workbook()
    ws = workbook.active
    with ZipFile(filename) as zipfile:
        sharedStrings: List[str] = []
        try:
            with zipfile.open("xl/sharedStrings.xml") as xmlfile:
                xml = ET.parse(xmlfile)
                for item in xml.getroot():
                    if ("}" + item.tag).endswith("}si"):
                        text = ""
                        for block in item:
                            if ("}" + block.tag).endswith("}t"):
                                text += block.text or ""
                        sharedStrings += [text]
        except KeyError as e:
            logg.debug("do not use sharedStrings.xml: %s", e)
        formatcodes: Dict[str, str] = {}
        numberformat: Dict[str, str] = {}
        with zipfile.open("xl/styles.xml") as xmlfile:
            xml = ET.parse(xmlfile)
            for item in xml.getroot():
                if ("}" + item.tag).endswith("numFmts"):
                    for fmt in item:
                        numFmtId = fmt.get("numFmtId", "?")
                        formatcode = fmt.get("formatCode", "?")
                        logg.debug("numFmtId %s formatCode %s", numFmtId, formatcode)
                        formatcodes[numFmtId] = formatcode
                if ("}" + item.tag).endswith("cellXfs"):
                    style = 0
                    for xfs in item:
                        numFmtId = xfs.get("numFmtId", "?")
                        logg.debug("numFmtId %s", numFmtId)
                        if numFmtId in formatcodes:
                            numberformat[str(style)] = formatcodes[numFmtId]
                        style += 1
        sheetnames: Dict[str, str] = {}
        with zipfile.open("xl/workbook.xml") as xmlfile:
            xml = ET.parse(xmlfile)
            for item in xml.getroot():
                if ("}" + item.tag).endswith("}sheets"):
                    for sheet in item:
                        sheetname = sheet.get("name", "")
                        sheetId = sheet.get("sheetId", "")
                        if sheetId and sheetname:
                            sheetnames[sheetId] = sheetname
        namelist = zipfile.namelist()
        for sheetnumber in range(1, 99):
            sheetId = str(sheetnumber)
            sheetfilename = F"xl/worksheets/sheet{sheetId}.xml"
            if sheetnumber > 1:
                if sheetfilename not in namelist:
                    break
                ws = Worksheet()
                workbook.sheets.append(ws)
            if sheetId in sheetnames:
                ws.title = sheetnames[sheetId]
            with zipfile.open(sheetfilename) as xmlfile:
                xml = ET.parse(xmlfile)
                for item in xml.getroot():
                    if ("}" + item.tag).endswith("}sheetData"):
                        for rowdata in item:
                            row = int(rowdata.get("row", "0"))
                            for cell in rowdata:
                                value: CellValue = None
                                t = cell.get("t", "n")
                                s = cell.get("s", "0")
                                r = cell.get("r")
                                v = ""
                                x = ""
                                for data in cell:
                                    if ("}" + data.tag).endswith("}v"):
                                        v = data.text or ""
                                    elif ("}" + data.tag).endswith("}is"):
                                        for block in data:
                                            x += block.text or ""
                                    elif ("}" + data.tag).endswith("}f"):
                                        x = "=" + (data.text or "")
                                        t = "f"
                                logg.debug("r = %s | s = %s | t =%s | v = %s| x = %s", r, s, t, v, x)
                                if t in ["b"]:
                                    value = True if v == "1" else False
                                elif t in ["f", "inlineStr", ]:
                                    value = x
                                elif t in ["s"]:
                                    value = sharedStrings[int(v)]
                                # elif v in [""]:
                                #     value = ""
                                elif "." not in v:
                                    value = int(v)
                                else:
                                    value1 = float(v)
                                    value = value1
                                    if s in numberformat:
                                        numfmt = numberformat[s]
                                        logg.debug("value %s numberformat %s", value, numfmt)
                                        if numfmt in _timeformats:
                                            value0 = int(value1)
                                            value2 = Time.fromordinal(value0 + 693594)
                                            value3 = int(((value1 - value0) * 86400) + 0.4)
                                            value = value2 + Plus(seconds=value3)
                                            t = "d"
                                        elif numfmt in _dateformats:
                                            value0 = int(value1)
                                            value2 = Time.fromordinal(value0 + 693594)
                                            value = value2.date()
                                            t = "d"

                                if r:
                                    ws[r].value = value
                                    ws[r].data_type = t
    return workbook

# .....................................................................
class TabText(NamedTuple):
    data: List[Dict[str, CellValue]]
    headers: List[str]

def readFromXLSX(filename: str, section: str = NIX) -> List[Dict[str, CellValue]]:
    return tabtextfileXLSX(filename, section=section).data
def tabtextfileXLSX(filename: str, section: str = NIX) -> TabText:
    workbook = load_workbook(filename)
    return tabtext_workbook(workbook, section=section)
def data_workbook(workbook: Workbook, section: str = NIX) -> List[Dict[str, CellValue]]:
    data, _ = tabtext_workbook(workbook, section=section)
    return data
def tabtext_workbook(workbook: Workbook, section: str = NIX) -> TabText:
    tablist = tablist_workbook(workbook)
    tabtext = TabText([], [])
    if tablist:  # always true
        tabtext = TabText(tablist[0].data, tablist[0].headers)
        if section:
            for tab in tablist:
                if tab.title == section:
                    tabtext = TabText(tab.data, tab.headers)
    return tabtext

class TabSheet(NamedTuple):
    data: List[Dict[str, CellValue]]
    headers: List[str]
    title: str

def tablistfileXLSX(filename: str) -> List[TabSheet]:
    workbook = load_workbook(filename)
    return tablist_workbook(workbook)
def tablist_workbook(workbook: Workbook, section: str = NIX) -> List[TabSheet]:
    tab = []
    for ws in workbook.sheets:
        title = ws.title
        cols: List[str] = []
        for col in range(MAXCOL):
            header = ws.cell(row=1, column=col + 1)
            if header.value is None:
                break
            name = header.value
            if name is None:
                break
            cols.append(str(name))
        logg.debug("xlsx found %s cols\n\t%s", len(cols), cols)
        data: List[Dict[str, CellValue]] = []
        for atrow in range(MAXROWS):
            record = []
            found = 0
            for atcol in range(len(cols)):
                cell = ws.cell(row=atrow + 2, column=atcol + 1)
                if cell.data_type in ["f"]:
                    continue
                value = cell.value
                # logg.debug("[%i,%si] cell.value = %s", atcol, atrow, value)
                if value is not None:
                    found += 1
                if isinstance(value, str) and value == " ":
                    value = ""
                record.append(value)
            if not found:
                break
            newrow = dict(zip(cols, record))
            data.append(newrow)  # type: ignore[arg-type]
        tab.append(TabSheet(data, cols, title))
    return tab


def currency() -> str:
    """ make dependent on locale ? """
    currency_dollar = 0x024
    currency_pound = 0x0A3
    currency_symbol = 0x0A4  # in iso-8859-1 it shows the euro sign
    currency_yen = 0x0A5
    currency_euro = 0x20AC
    return chr(currency_euro)

def tabtoXLSX(filename: str, data: Iterable[Dict[str, CellValue]], headers: List[str] = [], selected: List[str] = [], minwidth: int = 0, section: str = NIX) -> str:
    workbook = make_tabtoXLSX(data, headers, selected, minwidth, section)
    save_workbook(filename, workbook)
    return "TABXLSX"
def make_tabtoXLSX(data: Iterable[Dict[str, CellValue]], headers: List[str] = [], selected: List[str] = [], minwidth: int = 0, section: str = NIX) -> Workbook:
    minwidth = minwidth or MINWIDTH
    logg.debug("tabtoXLSX:")
    renameheaders: Dict[str, str] = {}
    showheaders: List[str] = []
    sortheaders: List[str] = []
    formats: Dict[str, str] = {}
    combine: Dict[str, List[str]] = {}
    for header in headers:
        combines = ""
        for selheader in header.split("|"):
            if "@" in selheader:
                selcol, rename = selheader.split("@", 1)
            else:
                selcol, rename = selheader, ""
            if ":" in selcol:
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
    combined: Dict[str, List[str]] = {}
    renaming: Dict[str, str] = {}
    selcols: List[str] = []
    for selecheader in selected:
        combines = ""
        for selec in selecheader.split("|"):
            if "@" in selec:
                selcol, rename = selec.split("@", 1)
            else:
                selcol, rename = selec, ""
            if ":" in selcol:
                name, form = selcol.split(":", 1)
                if isinstance(formats, dict):
                    fmts = form if "{" in form else ("{:" + form + "}")
                    formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
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
    logg.debug("selcols = %s", selcols)
    if not selected:
        combined = combine  # argument
        renaming = renameheaders
        logg.debug("combined : %s", combined)
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
        if newsort:
            newsorts[name] = newsort
    logg.debug("newsorts = %s", newsorts)
    logg.debug("colnames = %s", colnames)
    sortcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols or sortheaders)]
    if newsorts:
        for num, name in enumerate(sortcolumns):
            if name not in newsorts:
                newsorts[name] = ("@" * len(str(num)) + str(num))
        sortcolumns = sorted(newsorts, key=lambda x: newsorts[x])
        logg.debug("sortcolumns : %s", sortcolumns)
    if selcols:
        selheaders = [(name if name not in colnames else colnames[name]) for name in (selcols)]
    else:
        selheaders = [(name if name not in colnames else colnames[name]) for name in (showheaders)]
    def strNone(value: CellValue) -> str:
        if isinstance(value, Time):
            return value.strftime(TIMEFMT)
        if isinstance(value, Date):
            return value.strftime(DATEFMT)
        return str(value)
    def sortkey(header: str) -> str:
        if header in selheaders:
            num = selheaders.index(header)
            return ("@" * len(str(num)) + str(num))
        return header
    def sortrow(row: Dict[str, CellValue]) -> str:
        def asdict(item: Dict[str, CellValue]) -> Dict[str, CellValue]:
            if hasattr(item, "_asdict"):
                return item._asdict()  # type: ignore[union-attr, no-any-return, arg-type, attr-defined]
            return item
        item = asdict(row)
        sorts = sortcolumns
        if sorts:
            # numbers before empty before strings
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
        return ""
    rows: List[Dict[str, CellValue]] = []
    cols: Dict[str, int] = {}
    for num, item in enumerate(data):
        row: Dict[str, CellValue] = {}
        if "#" in headers:
            item["#"] = num + 1
            cols["#"] = len(str(num + 1))
        for name, value in item.items():
            selname = name
            if name in renameheaders and renameheaders[name] in selcols:
                selname = renameheaders[name]
            if selcols and selname not in selcols and "*" not in selcols:
                continue
            colname = selname if selname not in colnames else colnames[selname]
            row[colname] = value  # do not format the value here!
            oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
            cols[colname] = max(oldlen, len(strNone(value)))
        rows.append(row)
    sortedrows = list(sorted(rows, key=sortrow))
    sortedcols = list(sorted(cols.keys(), key=sortkey))
    return make_workbook(sortedrows, sortedcols, cols, formats, section=section)


def make_workbook(rows: List[Dict[str, CellValue]],
                  cols: List[str], colwidth: Dict[str, int],
                  formats: Dict[str, str], section: str = NIX) -> Workbook:
    row = 0
    workbook = Workbook()
    ws = workbook.active
    ws.title = section or SECTION
    col = 0
    for name in cols:
        ws.cell(row=1, column=col + 1).value = name
        ws.cell(row=1, column=col + 1).alignment = Alignment(horizontal="right")
        if name in colwidth:
            ws.column_dimensions[get_column_letter(col + 1)].width = colwidth[name]
        col += 1
    for item in rows:
        row += 1
        values: Dict[str, CellValue] = dict([(name, "") for name in cols])
        for name, value in item.items():
            values[name] = value
        col = 0
        for name in cols:
            value = values[name]
            at = {"column": col + 1, "row": row + 1}
            if value is None:
                ws.cell(**at).value = ""
                ws.cell(**at).alignment = Alignment(horizontal="left")
                ws.cell(**at).number_format = "General"
            elif isinstance(value, Time):
                ws.cell(**at).value = value
                ws.cell(**at).alignment = Alignment(horizontal="right")
                ws.cell(**at).number_format = "yyyy-mm-dd hh:mm"
            elif isinstance(value, Date):
                ws.cell(**at).value = value
                ws.cell(**at).alignment = Alignment(horizontal="right")
                ws.cell(**at).number_format = "yyyy-mm-dd"
            elif isinstance(value, int):
                ws.cell(**at).value = value
                ws.cell(**at).alignment = Alignment(horizontal="right")
                ws.cell(**at).number_format = "#,##0"
            elif isinstance(value, float):
                ws.cell(**at).value = value
                ws.cell(**at).alignment = Alignment(horizontal="right")
                ws.cell(**at).number_format = "#,##0.00"
                if name in formats and "$}" in formats[name]:
                    ws.cell(**at).number_format = "#,##0.00" + currency()
            else:
                ws.cell(**at).value = value
                ws.cell(**at).alignment = Alignment(horizontal="left")
                ws.cell(**at).number_format = "General"
            col += 1
    return workbook

# ...........................................................
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

def print_tabtotext(output: Union[TextIO, str], data: Iterable[Dict[str, CellValue]],  # ..
                    headers: List[str] = [], selected: List[str] = [],
                    *, tab: Optional[str] = None, padding: Optional[str] = None, minwidth: int = 0, section: str = NIX,
                    noheaders: bool = False, unique: bool = False, defaultformat: str = "") -> str:
    """ This code is supposed to be copy-n-paste into other files. You can safely try-import from 
        tabtotext or tabtoxlsx to override this function. Only a subset of features is supported. """
    spec: Dict[str, str] = dict(cast(Tuple[str, str], (x, "") if "=" not in x else x.split("=", 1))
                                for x in selected if x.startswith("@"))
    selected = [x for x in selected if not x.startswith("@")]
    minwidth = minwidth or MINWIDTH
    padding = " " if padding is None else padding
    tab = "|" if tab is None else tab
    def extension(filename: str) -> Optional[str]:
        _, ext = fs.splitext(filename.lower())
        if ext: return ext[1:]
        return None
    #
    if isinstance(output, TextIO) or isinstance(output, StringIO):
        out = output
        fmt = defaultformat
        done = "stream"
    elif "." in output:
        fmt = extension(output) or defaultformat
        if fmt in ["xls", "xlsx"]:
            tabtoXLSX(output, data, headers, selected, section=section)
            return "XLSX"
        out = open(output, "wt", encoding="utf-8")
        done = output
    else:
        fmt = output or defaultformat
        out = sys.stdout
        done = output
    #
    if fmt in ["md", "markdown"] or "@md" in spec or "@markdown" in spec:
        fmt = "GFM"  # nopep8
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
    if fmt in ["ifs"] or "@dat" in spec or "@ifs" in spec:
        fmt = "CSV"
        tab = os.environ.get("IFS", "\t")  # nopep8
    if fmt in ["dat"] or "@dat" in spec or "@ifs" in spec:
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
    if fmt in ["json"] or "@json" in spec:
        fmt = "JSON"
    if fmt in ["jsn"] or "@jsn" in spec:
        fmt = "JSON"
        padding = ""
    if fmt in ["xlsx", "xls"] or "@xlsx" in spec or "@xls" in spec:
        fmt = "XLS"
        tab = ","  # nopep8
    # override
    if "@tab" in spec:
        tab = spec["@tab"]
    if "@notab" in spec:
        tab = ""
    if "@nopadding" in spec:
        padding = ""
    if "@noheaders" in spec:
        noheaders = True
    if "@unique" in spec:
        unique = True
    #
    none_string = "~"
    true_string = "(yes)"
    false_string = "(no)"
    floatfmt = "%4.2f"
    noright = fmt in ["data"]
    noheaders = noheaders or fmt in ["data", "text", "list"]
    formatleft = re.compile("[{]:[^{}]*<[^{}]*[}]")
    formatright = re.compile("[{]:[^{}]*>[^{}]*[}]")
    formatnumber = re.compile("[{]:[^{}]*[defghDEFGHMQR$%][}]")
    # parsing the microsyntax of headers and selected columns ["colname:{:.2f}$@newname"]
    formats: Dict[str, str] = {}
    renameheaders: Dict[str, str] = {}
    showheaders: List[str] = []
    sortheaders: List[str] = []
    for header in headers:
        for selheader in header.split("|"):
            if "@" in selheader:
                selcol, rename = selheader.split("@", 1)
            else:
                selcol, rename = selheader, ""
            if ":" in selcol:
                name, form = selcol.split(":", 1)
                fmts = form if "{" in form else ("{:" + form + "}")
                formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            showheaders += [name]
            if rename:
                sortheaders += [name]  # default sort by named headers (rows)
            if rename:
                renameheaders[name] = rename
    renaming: Dict[str, str] = {}
    selcols: List[str] = []
    for selecheader in selected:
        for selec in selecheader.split("|"):
            if "@" in selec:
                selcol, rename = selec.split("@", 1)
            else:
                selcol, rename = selec, ""
            if ":" in selcol:
                name, form = selcol.split(":", 1)
                fmts = form if "{" in form else ("{:" + form + "}")
                formats[name] = fmts.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
            selcols.append(name)
            if rename:
                renaming[name] = rename
    if not selected:
        renaming = renameheaders
    logg.debug("sortheaders = %s | formats = %s", sortheaders, formats)
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
    sortcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols or sortheaders)]
    if newsorts:
        for num, name in enumerate(sortcolumns):
            if name not in newsorts:
                newsorts[name] = ("@" * len(str(num)) + str(num))
        sortcolumns = sorted(newsorts, key=lambda x: newsorts[x])
        logg.debug("sortcolumns : %s", sortcolumns)
    else:
        logg.debug("sortcolumns = %s", sortcolumns)
    selcolumns = [(name if name not in colnames else colnames[name]) for name in (selcols)]
    selheaders = [(name if name not in colnames else colnames[name]) for name in (showheaders)]
    # .......................................
    def rightalign(col: str) -> bool:
        if col in formats and not noright:
            if formats[col].startswith(" "):
                return True
            if formats[col].startswith("{: "):
                return True
            if formatleft.search(formats[col]):
                return False
            if formatright.search(formats[col]):
                return True
            if formatnumber.search(formats[col]):
                return True
        return False
    def strValue(value: CellValue) -> str:
        if value is None: return none_string
        if value is False: return false_string
        if value is True: return true_string
        if isinstance(value, Time):
            return value.strftime("%Y-%m-%d.%H%M")  # TIMEFMT
        if isinstance(value, Date):
            return value.strftime("%Y-%m-%d")  # DATEFMT
        return str(value)
    def format(name: str, val: CellValue) -> str:
        if name in formats:
            fmt = formats[name]
            if fmt.startswith("{:") and fmt[-1] == "}" and "%s" in fmt:
                fmt = fmt[2:-1].replace("%s", "{:s}")
            if fmt.startswith("{:%") and fmt[-1] == "}" and fmt[-2] in "sf":
                fmt = fmt.replace("{:%", "{:")
            if "{:" in fmt:
                try:
                    return fmt.format(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", fmt, e)
        if isinstance(val, float):
            return floatfmt % val
        return strValue(val)
    def asdict(item: Dict[str, CellValue]) -> Dict[str, CellValue]:
        if hasattr(item, "_asdict"):
            return item._asdict()  # type: ignore[union-attr, no-any-return, arg-type, attr-defined]
        return item
    rows: List[Dict[str, CellValue]] = []
    cols: Dict[str, int] = {}
    for num, item in enumerate(data):
        row: Dict[str, CellValue] = {}
        if "#" in selcols:
            row["#"] = num + 1
            cols["#"] = len(str(num + 1))
        for name, value in asdict(item).items():
            selname = name
            if name in renameheaders and renameheaders[name] in selcols:
                selname = renameheaders[name]
            if selcols and selname not in selcols and "*" not in selcols:
                continue
            colname = selname if selname not in colnames else colnames[selname]
            row[colname] = value
            oldlen = cols[colname] if colname in cols else max(minwidth, len(colname))
            cols[colname] = max(oldlen, len(format(colname, value)))
        rows.append(row)
    def sortkey(header: str) -> str:
        headers = selcolumns or selheaders
        if header in headers:
            num = headers.index(header)
            return ("@" * len(str(num)) + str(num))
        return header
    def sortrow(row: Dict[str, CellValue]) -> str:
        item = asdict(row)
        sorts = sortcolumns
        if sorts:
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
                        val = "%i" % value
                        sortvalue += "\n" + (":" * len(val)) + val
                    elif isinstance(value, float):
                        val = "%.6f" % value
                        sortvalue += "\n" + (":" * val.index(".")) + val
                    else:
                        sortvalue += "\n" + strValue(value)
                else:
                    sortvalue += "\n?"
            return sortvalue
        return ""
    # print ..........................................
    colo = tuple(sorted(cols.keys(), key=sortkey))  # ordered column names
    same = []
    # JSON
    if fmt in ["JSON"]:
        import json
        pad = " " * len(padding)
        comma = "," + pad
        lines: List[str] = []
        for row in sorted(rows, key=sortrow):
            line: List[str] = []
            for name in colo:
                if name in row:
                    value = row[name]
                    if isinstance(value, Date) or isinstance(value, Time):
                        line += ['"%s":%s"%s"' % (name, pad, str(value))]
                    else:
                        line += ['"%s":%s%s' % (name, pad, json.dumps(value))]
            lines.append(" {" + comma.join(line) + "}")
        newlist = "[\n"
        endlist = "\n]"
        if section:
            newlist = '{"%s":%s[\n' % (section.replace('"', "'"), pad)
            endlist = "\n]}"
        out.write(newlist + ",\n".join(lines) + endlist)
        return "JSON"
    # CSV
    if fmt in ["CSV"]:
        tab1 = tab if tab else ";"
        import csv
        writer = csv.DictWriter(out, fieldnames=colo, restval='~',
                                quoting=csv.QUOTE_MINIMAL, delimiter=tab1)
        if not noheaders:
            writer.writeheader()
        old: Dict[str, str] = {}
        for row in sorted(rows, key=sortrow):
            rowvalues: Dict[str, str] = {}
            for name, value in asdict(row).items():
                rowvalues[name] = format(name, value)
            if unique:
                same = [sel for sel in selcols if sel in rowvalues and sel in old and rowvalues[sel] == old[sel]]
            if not selcols or same != selcols:
                writer.writerow(rowvalues)
            old = rowvalues
        return "CSV"
    # GFM
    ws = ("", " ", "  ", "   ", "    ", "     ", "      ", "       ", "        ")  # " "*(0...8)
    colw = tuple((cols[col] for col in colo))  # widths of cols ordered
    colr = tuple((rightalign(col) for col in colo))  # rightalign of cols ordered
    tab2 = (tab + padding if tab else "")
    if section:
        print(F"## {section}\n", file=out)
    if not noheaders:
        hpad = [(ws[w] if w < 9 else (" " * w)) for w in ((colw[m] - len(col)) for m, col in enumerate(colo))]
        line = [tab2 + (hpad[m] + col if colr[m] else col + hpad[m]) for m, col in enumerate(colo)]
        print(padding.join(line).rstrip(), file=out)
        if tab and padding:
            seps = ["-" * colw[m] for m, col in enumerate(colo)]
            seperators = [tab2 + (seps[m][:-1] + ":" if colr[m] else seps[m]) for m, col in enumerate(colo)]
            print(padding.join(seperators).rstrip(), file=out)
    oldvalues: Dict[str, str] = {}
    for item in sorted(rows, key=sortrow):
        values: Dict[str, str] = {}
        for name, value in asdict(item).items():
            values[name] = format(name, value)
        vals = [values.get(col, none_string) for col in colo]
        vpad = [(ws[w] if w < 9 else (" " * w)) for w in ((colw[m] - len(vals[m])) for m, col in enumerate(colo))]
        line = [tab2 + (vpad[m] + vals[m] if colr[m] else vals[m] + vpad[m]) for m, col in enumerate(colo)]
        if unique:
            same = [sel for sel in selcols if sel in values and sel in oldvalues and values[sel] == oldvalues[sel]]
        if not selcols or same != selcols:
            print((padding.join(line)).rstrip(), file=out)
        oldvalues = values
    return "GFM"

def tabtextfile(input: Union[TextIO, str], section: str = NIX, defaultformat: str = "") -> TabText:
    tablist = tablistfile(input, defaultformat=defaultformat)
    tabtext = TabText([],[])
    if tablist:
        tabtext = TabText(tablist[0].data, tablist[0].headers)
        if section:
            for tab in tablist:
                if tab.title == section:
                    tabtext = TabText(tab.data, tab.headers)
    return tabtext
def tablistfile(input: Union[TextIO, str], defaultformat: str = "") -> List[TabSheet]:
    def extension(filename: str) -> Optional[str]:
        _, ext = fs.splitext(filename.lower())
        if ext: return ext[1:]
        return None
    #
    if isinstance(input, TextIO) or isinstance(input, StringIO):
        inp = input
        fmt = defaultformat
        done = "stream"
    elif "." in input:
        fmt = extension(input) or defaultformat
        if fmt in ["xls", "xlsx"]:
            return tablistfileXLSX(input)
        inp = open(input, "rt", encoding="utf-8")
        done = input
    else:
        fmt = input or defaultformat
        inp = sys.stdin
        done = input
    #
    tab = '|'
    if fmt in ["wide", "text"]:
        tab = ''
    if fmt in ["tabs", "tab", "dat", "ifs", "data"]:
        tab = '\t'
    if fmt in ["csv", "scsv", "list"]:
        tab = ';'
    if fmt in ["xls", "sxlx"]:
        tab = ','
    #
    none_string = "~"
    true_string = "(yes)"
    false_string = "(no)"
    tabs: List[TabSheet] = []
    if fmt in ["jsn", "json"]:
        import json
        time = StrToTime()
        jsondata = json.load(inp)
        if isinstance(jsondata, dict):
            jsondict = jsondata
        else:
            jsondict = {"data": jsondata}
        for listname, jsonlist in jsondict.items():
            listdata: List[Dict[str, CellValue]] = []
            if isinstance(jsonlist, Iterable):
                for nextgroup in jsonlist:
                    if isinstance(nextgroup, dict):
                        newgroup: Dict[str, CellValue] = {}
                        for nam, jsonval in nextgroup.items():
                            if isinstance(jsonval, str):
                                newgroup[nam] = time(jsonval)
                            else:
                                newgroup[nam] = jsonval
                        listdata.append(newgroup)
            tabs.append(TabSheet(listdata, [], listname))
        return tabs
    data: List[Dict[str, CellValue]] = []
    if fmt in ["csv", "scsv", "tab"]:
        import csv
        time = StrToTime()
        reader = csv.DictReader(inp, delimiter=tab)
        for nextrecord in reader:
            # newrecord: Dict[str, CellValue] = cast(Dict[str, CellValue], nextrecord.copy())
            newrecord: Dict[str, CellValue] = {}
            for nam, val in nextrecord.items():
                v = val.strip()
                if v == none_string:
                    newrecord[nam] = None
                elif v == false_string:
                    newrecord[nam] = False
                elif v == true_string:
                    newrecord[nam] = True
                else:
                    try:
                        newrecord[nam] = int(v)
                    except:
                        try:
                            newrecord[nam] = float(v)
                        except:
                            newrecord[nam] = time(v)
            data.append(newrecord)
        return [TabSheet(data, list(reader.fieldnames if reader.fieldnames else []), SECTION)]
    # must have headers
    lookingfor = "headers"
    headers: List[str] = []
    title = ""
    for line in inp:
        if tab and not line.startswith(tab):
            if headers:
                if not title:
                    title = "-%s" % (len(tabs)+1)
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
        record: Dict[str, CellValue] = {}
        for col, val in enumerate(vals):
            v = val.strip()
            if v == none_string:
                record[headers[col]] = None
            elif v == false_string:
                record[headers[col]] = False
            elif v == true_string:
                record[headers[col]] = True
            else:
                try:
                    record[headers[col]] = int(v)
                except:
                    try:
                        record[headers[col]] = float(v)
                    except:
                        try:
                            record[headers[col]] = Time.strptime(v, "%Y-%m-%d.%H%M")
                        except Exception as e:
                            if ".23" in v:
                                logg.error("no date? = %s = %s", v, e)
                            try:
                                record[headers[col]] = Time.strptime(v, "%Y-%m-%d").date()
                            except:
                                record[headers[col]] = v
        data.append(record)
    if headers:
        if not title:
            title = "-%s" % (len(tabs)+1)
        tabs.append(TabSheet(data, headers, title))
    return tabs


if __name__ == "__main__":
    from logging import basicConfig, ERROR
    from optparse import OptionParser
    import sys
    prog = os.path.basename(__file__)
    cmdline = OptionParser(prog + " [-options] input(.xlsx|.csv) [column...]", epilog=__doc__)
    cmdline.formatter.max_help_position = 29
    cmdline.add_option("-1", "-2", "-3", "-x", dest="page", action="store_true")
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="increase logging level")
    cmdline.add_option("-^", "--quiet", action="count", default=0, help="decrease logging level")
    cmdline.add_option("-m", "--minwidth", metavar="N", default=0,
                       help="override minwith of  cells for format")
    cmdline.add_option("-p", "--padding", metavar="C", default=None,
                       help="override cell padding for format")
    cmdline.add_option("-t", "--tabulator", metavar="C", default=None,
                       help="override tabulator for format")
    cmdline.add_option("-T", "--asciitab", action="store_true", default=False,
                       help="use ascii HT tabulator (csv,md,tab,wide)")
    cmdline.add_option("-N", "--notab", action="store_true", default=False,
                       help="do not use tabulator (csv,md,tab,wide)")
    cmdline.add_option("-P", "--nopadding", action="store_true", default=False,
                       help="do not use padding (csv,md,tab,wide)")
    cmdline.add_option("-D", "--noheaders", action="store_true", default=False,
                       help="do not print headers (csv,md,tab,wide)")
    cmdline.add_option("-U", "--unique", action="store_true", default=False,
                       help="remove same lines in sorted --labels")
    cmdline.add_option("-i", "--input", metavar="CSV", default="",
                       help="fix input format (instead of autodetection)")
    cmdline.add_option("-o", "--output", metavar="CSV", default="",
                       help="data|text|md|tab|csv or file.csv (see below)")
    cmdline.add_option("--ifs", action="store_true", help="-o ifs: $IFS-seperated table (with headers)")
    cmdline.add_option("--dat", action="store_true", help="-o dat: $IFS-seperated table (without headers)")
    cmdline.add_option("--data", action="store_true", help="-o data: tab-seperated without headers")
    cmdline.add_option("--text", action="store_true", help="-o text: space-seperated without headers")
    cmdline.add_option("--list", action="store_true", help="-o text: semicolon-seperated without headers")
    cmdline.add_option("--wide", action="store_true", help="-o wide: aligned space-separated table")
    cmdline.add_option("--md", action="store_true", help="-o md: aligned markdown table (with '|' delim)")
    cmdline.add_option("--markdown", action="store_true", help="-o markdown: markdown with extra '|' at end")
    cmdline.add_option("--tabs", action="store_true", help="-o tabs: aligned tab-seperated table (not '|')")
    cmdline.add_option("--tab", action="store_true", help="-o tab: aligned tab-seperated table (like --dat)")
    cmdline.add_option("--csv", "--scsv", action="store_true", help="-o csv: semicolon-seperated csv table")
    cmdline.add_option("--xls", "--xlsx", action="store_true", help="-o xls: for filename.xlsx (else comma-csv)")
    opt, args = cmdline.parse_args()
    basicConfig(level=max(0, ERROR - 10 * opt.verbose + 10 * opt.quiet))
    if not args:
        cmdline.print_help()
        logg.error("no input filename given")
        sys.exit(1)
    minwidth = int(opt.minwidth)
    padding = opt.padding if not opt.nopadding else ""
    tab = "\t" if opt.asciitab else opt.tabulator if not opt.notab else ""
    filename = args[0]
    if len(args) > 1:
        selected = args[1:]
    else:
        selected = []
    if "." in opt.output:
        output = opt.output
        defaultformat = ""
    else:
        output = ""
        defaultformat = opt.output
    if not defaultformat:
        if opt.ifs:
            defaultformat = "ifs"
        if opt.dat:
            defaultformat = "dat"
        if opt.data:
            defaultformat = "data"
        if opt.text:
            defaultformat = "text"
        if opt.list:
            defaultformat = "list"
        if opt.wide:
            defaultformat = "wide"
        if opt.md:
            defaultformat = "md"
        if opt.markdown:
            defaultformat = "markdown"
        if opt.tabs:
            defaultformat = "tabs"
        if opt.tab:
            defaultformat = "tab"
        if opt.csv:
            defaultformat = "csv"
        if opt.xls:
            defaultformat = "xls"
    tablist = tablistfile(filename, defaultformat="xlsx")
    if len(tablist) == 0:
        logg.error("no data in file %s", filename)
    elif len(tablist) == 1:
        tabsheet = tablist[0]
        print_tabtotext(output, tabsheet.data, tabsheet.headers, selected, padding=padding, tab=tab,
                    noheaders=opt.noheaders, unique=opt.unique, minwidth=minwidth,
                    defaultformat=defaultformat)
    else:
        for tabtext in tablist:
            logg.debug("headers = %s", tabtext.headers)
            logg.debug("data = %s", tabtext.data)
            print_tabtotext(output, tabtext.data, tabtext.headers, selected, padding=padding, tab=tab,
                        noheaders=opt.noheaders, unique=opt.unique, minwidth=minwidth, section=tabtext.title,
                        defaultformat=defaultformat)
