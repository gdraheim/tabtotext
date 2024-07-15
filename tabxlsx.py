#! /usr/bin/env python3
""" 
TabXLSX reads and writes Excel xlsx files. It does not depend on other libraries.
The output can be piped as a markdown table or csv-like data as well."""

from typing import Union, List, Dict, Tuple, Optional, TextIO, Iterable, cast
from datetime import date as Date
from datetime import datetime as Time
from datetime import timedelta as Plus
from io import StringIO, TextIOWrapper
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
import os.path as fs
import re

# Actually, we implement what we need for tabtoxlsx
# from openpyxl import Workbook, load_workbook
# from openpyxl.worksheet.worksheet import Worksheet
# from openpyxl.styles.cell_style import CellStyle as Style
# from openpyxl.styles.alignment import Alignment
# from openpyxl.utils import get_column_letter

from logging import getLogger
logg = getLogger("tabxlsx")

DATEFMT = "%Y-%m-%d"
TIMEFMT = "%Y-%m-%d.%H%M"
FLOATFMT = "%4.2f"
MINWIDTH = 4
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
    alignment: Optional[Alignment]
    number_format: Optional[str]
    protection: Optional[str]
    _xf: int
    _numFmt: int
    def __init__(self) -> None:
        self.value = None
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

_timeformats = ['d.mm.yy', 'yyyy-mm-dd', 'yyyy-mm-dd hh:mm', 'yyyy-mm-dd h:mm:ss']
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
        with zipfile.open("xl/worksheets/sheet1.xml") as xmlfile:
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
                                if ("}" + data.tag).endswith("v"):
                                    v = data.text or ""
                                elif ("}" + data.tag).endswith("is"):
                                    for block in data:
                                        x += block.text or ""
                            logg.debug("r = %s | s = %s | t =%s | v = %s| x = %s", r, s, t, v, x)
                            if t in ["b"]:
                                value = True if v == "1" else False
                            elif t in ["inlineStr"]:
                                value = x
                            elif t in ["s"]:
                                value = sharedStrings[int(v)]
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

                            if r:
                                ws[r].value = value
    return workbook

def read2_workbook(filename: str) -> Tuple[List[Dict[str, CellValue]], List[str]]:
    workbook = load_workbook(filename)
    return data2_workbook(workbook)
def read_workbook(filename: str) -> List[Dict[str, CellValue]]:
    workbook = load_workbook(filename)
    return data_workbook(workbook)
def data_workbook(workbook: Workbook) -> List[Dict[str, CellValue]]:
    data, _ = data2_workbook(workbook)
    return data
def data2_workbook(workbook: Workbook) -> Tuple[List[Dict[str, CellValue]], List[str]]:
    ws = workbook.active
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
    return data, cols

def currency() -> str:
    """ make dependent on locale ? """
    currency_dollar = 0x024
    currency_pound = 0x0A3
    currency_symbol = 0x0A4  # in iso-8859-1 it shows the euro sign
    currency_yen = 0x0A5
    currency_euro = 0x20AC
    return chr(currency_euro)

def write_workbook(filename: str, data: Iterable[Dict[str, CellValue]], headers: List[str] = []) -> None:
    workbook = make_workbook(data, headers)
    save_workbook(filename, workbook)
def make_workbook(data: Iterable[Dict[str, CellValue]], headers: List[str] = []) -> Workbook:
    sortheaders: List[str] = []
    formattings: Dict[str, str] = {}
    for header in headers:
        if ":" in header:
            name, fmt = header.split(":", 1)
            sortheaders += [name]
            formattings[name] = fmt
    def strNone(value: CellValue) -> str:
        if isinstance(value, Time):
            return value.strftime(TIMEFMT)
        if isinstance(value, Date):
            return value.strftime(DATEFMT)
        return str(value)
    def sortkey(header: str) -> str:
        if header in sortheaders:
            return "%07i" % sortheaders.index(header)
        return header
    def sortrow(row: Dict[str, CellValue]) -> str:
        def asdict(item: Dict[str, CellValue]) -> Dict[str, CellValue]:
            if hasattr(item, "_asdict"):
                return item._asdict()  # type: ignore[union-attr, no-any-return, arg-type, attr-defined]
            return item
        item = asdict(row)
        sorts = sortheaders
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
                        sortvalue += "\n%020i" % value
                    elif isinstance(value, Time):
                        sortvalue += "\n" + value.strftime(TIMEFMT)
                    elif isinstance(value, Date):
                        sortvalue += "\n" + value.strftime(DATEFMT)
                    else:
                        sortvalue += "\n" + str(value)
                else:
                    sortvalue += "\n?"
            return sortvalue
        return ""
    rows: List[Dict[str, CellValue]] = []
    cols: Dict[str, int] = {}
    for item in data:
        for name, value in item.items():
            paren = 0
            if name not in cols:
                cols[name] = max(MINWIDTH, len(name))
            cols[name] = max(cols[name], len(strNone(value)))
        rows.append(item)
    row = 0
    workbook = Workbook()
    ws = workbook.active
    ws.title = "data"
    col = 0
    for name in sorted(cols.keys(), key=sortkey):
        ws.cell(row=1, column=col + 1).value = name
        ws.cell(row=1, column=col + 1).alignment = Alignment(horizontal="right")
        col += 1
    for item in sorted(rows, key=sortrow):
        row += 1
        values: Dict[str, CellValue] = dict([(name, "") for name in cols.keys()])
        for name, value in item.items():
            values[name] = value
        col = 0
        for name in sorted(cols.keys(), key=sortkey):
            value = values[name]
            at = {"column": col + 1, "row": row + 1}
            if value is None:
                pass
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
                if name in formattings and "$}" in formattings[name]:
                    ws.cell(**at).number_format = "#,##0.00" + currency()
            else:
                ws.cell(**at).value = value
                ws.cell(**at).value = value
                ws.cell(**at).alignment = Alignment(horizontal="left")
                ws.cell(**at).number_format = "General"
            col += 1
    return workbook

# ...........................................................
def unmatched(value: CellValue, cond: str) -> bool:
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


def print_tabtotext(output: Union[TextIO, str], data: Iterable[Dict[str, CellValue]],  # ..
                    headers: List[str] = [], selects: List[str] = [], defaultformat: str = "") -> str:
    """ This code is supposed to be copy-n-paste into other files. You can safely try-import from 
        tabtotext or tabtoxlsx to override this function. Only a subset of features is supported. """
    def detectfileformat(filename: str) -> Optional[str]:
        _, ext = fs.splitext(filename.lower())
        if ext in [".txt", ".md", ".markdown"]:
            return "md"
        if ext in [".csv", ".scsv"]:
            return "csv"
        if ext in [".dat", ".tcsv"]:
            return "tab"
        if ext in [".xls", ".xlsx"]:
            return "xlsx"
        return None
    #
    if isinstance(output, TextIO) or isinstance(output, StringIO):
        out = output
        fmt = defaultformat
        done = "stream"
    elif "." in output:
        fmt = detectfileformat(output) or defaultformat
        if fmt in ["xls", "xlsx"]:
            write_workbook(output, data, headers)
            return "XLSX"
        out = open(output, "wt", encoding="utf-8")
        done = output
    else:
        fmt = output or defaultformat
        out = sys.stdout
        done = output
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
    minwidth = 5
    floatfmt = "%4.2f"
    noright = fmt in ["data"]
    noheaders = fmt in ["data", "text", "list"]
    formatleft = re.compile("[{]:[^{}]*<[^{}]*[}]")
    formatright = re.compile("[{]:[^{}]*>[^{}]*[}]")
    formatnumber = re.compile("[{]:[^{}]*[defghDEFGHMQR$%][}]")
    formats: Dict[str, str] = {}
    sortheaders: List[str] = []
    for header in [sel if "@" not in sel else sel.split("@", 1)[0] for sel in headers]:
        if ":" in header:
            name, fmt = header.split(":", 1)
            formats[name] = fmt
        else:
            name = header
        sortheaders += [name]
    renaming: Dict[str, str] = {}
    filtered: Dict[str, str] = {}
    selected: List[str] = []
    for selec in selects:
        if "@" in selec:
            selcols, rename = selec.split("@", 1)
        else:
            selcols, rename = selec, ""
        for selcol in selcols.split("|"):
            if ":" in selcol:
                name, form = selcol.split(":", 1)
                fmt = form if "{" in form else ("{:" + form + "}")
                formats[name] = fmt.replace("i}", "n}").replace("u}", "n}").replace("r}", "s}").replace("a}", "s}")
            else:
                name = selcol
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
            if rename:
                renaming[selcol] = rename
                rename = "" # only the first
    logg.debug("sortheaders = %s | formats = %s", sortheaders, formats)
    # .......................................
    def rightalign(col: str) -> bool:
        if col in formats and not noright:
            if formats[col].startswith(" "):
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
            fmt4 = formats[name]
            if "{:" in fmt4:
                try:
                    return fmt4.format(val)
                except Exception as e:
                    logg.debug("format <%s> does not apply: %s", fmt, e)
            if "%s" in fmt4:
                try:
                    return fmt % strValue(val)
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
    for item in data:
        row: Dict[str, CellValue] = {}
        for name, value in asdict(item).items():
            if selected and name not in selected and "*" not in selected:
               continue
            try:
                if name in filtered and unmatched(value, filtered[name]):
                    continue
            except: pass
            row[name] = value
            if name not in cols:
                cols[name] = max(minwidth, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
        rows.append(row)
    def sortkey(header: str) -> str:
        if header in sortheaders:
            return "%07i" % sortheaders.index(header)
        return header
    def sortrow(row: Dict[str, CellValue]) -> str:
        item = asdict(row)
        sorts = sortheaders
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
                        sortvalue += "\n%020i" % value
                    else:
                        sortvalue += "\n" + strValue(value)
                else:
                    sortvalue += "\n?"
            return sortvalue
        return "XLSX"
    # CSV
    if fmt in ["list", "csv", "scsv", "xlsx", "xls", "tab", "dat", "ifs", "data"]:
        tab1 = tab if tab else ";"
        import csv
        writer = csv.DictWriter(out, fieldnames=sorted(cols.keys(), key=sortkey),
                                restval='~', quoting=csv.QUOTE_MINIMAL, delimiter=tab1)
        if not noheaders:
            writer.writeheader()
        for row in sorted(data, key=sortrow):
            rowvalues: Dict[str, str] = {}
            for name, value in asdict(row).items():
                rowvalues[name] = format(name, value)
            writer.writerow(rowvalues)
        return "CSV"
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
        print(" ".join(line).rstrip(), file=out)
        if tab:
            seperators = [(tab2 + "%%-%is" % cols[name]) % rightS(name, "-" * cols[name])
                          for name in sorted(cols.keys(), key=sortkey)]
            print(" ".join(seperators).rstrip(), file=out)
    for item in sorted(data, key=sortrow):
        values: Dict[str, str] = {}
        for name, value in asdict(item).items():
            values[name] = format(name, value)
        line = [rightF(name, tab2 + "%%-%is" % cols[name]) % values.get(name, none_string)
                for name in sorted(cols.keys(), key=sortkey)]
        print((" ".join(line)).rstrip(), file=out)
    return "GFM"

def read_tabtotext(input: Union[TextIO, str], defaultformat: str = "") -> List[Dict[str, CellValue]]:
    data, cols = read2_tabtotext(input, defaultformat)
    return data
def read2_tabtotext(input: Union[TextIO, str], defaultformat: str = "") -> Tuple[List[Dict[str, CellValue]], List[str]]:
    def detectfileformat(filename: str) -> Optional[str]:
        _, ext = fs.splitext(filename.lower())
        if ext in [".txt", ".md", ".markdown"]:
            return "md"
        if ext in [".csv", ".scsv"]:
            return "csv"
        if ext in [".dat", ".tcsv"]:
            return "tab"
        if ext in [".xls", ".xlsx"]:
            return "xlsx"
        return None
    #
    if isinstance(input, TextIO) or isinstance(input, StringIO):
        inp = input
        fmt = defaultformat
        done = "stream"
    elif "." in input:
        fmt = detectfileformat(input) or defaultformat
        if fmt in ["xls", "xlsx"]:
            return read2_workbook(input)
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
    lead = tab if fmt in ["md", "markdown"] else ""
    #
    none_string = "~"
    true_string = "(yes)"
    false_string = "(no)"
    floatfmt = "%4.2f"
    noright = fmt in ["data"]
    noheaders = fmt in ["data", "text", "list"]
    formatleft = re.compile("[{]:[^{}]*<[^{}]*[}]")
    formatright = re.compile("[{]:[^{}]*>[^{}]*[}]")
    formatnumber = re.compile("[{]:[^{}]*[defghDEFGHMQR$%][}]")
    # must have headers
    lookingfor = "headers"
    headers: List[str] = []
    data: List[Dict[str, CellValue]] = []
    for line in inp:
        if lead and not line.startswith(lead):
           break
        vals = line.split(tab)
        if lead:
            del vals[0]
        if lookingfor == "headers":
            headers = [header.strip() for header in vals]
            lookingfor = "seperator"
            continue
        elif lookingfor == "seperator":
            lookingfor = "data"
            continue
        record: Dict[str, CellValue] = {}
        for col, val in enumerate(vals):
            if val.strip() == none_string:
                record[headers[col]] = None
            elif val.strip() == false_string:
                record[headers[col]] = False
            elif val.strip() == true_string:
                record[headers[col]] = True
            else:
                try:
                    record[headers[col]] = int(val)
                except:
                    try:
                        record[headers[col]] = float(val)
                    except:
                        try:
                            record[headers[col]] = Time.strptime("%Y-%m%d.%H%M", val)
                        except:
                            try:
                                record[headers[col]] = Time.strptime("%Y-%m%d", val).date()
                            except:
                                record[headers[col]] = val.strip()
        data.append(record)
    return (data, headers)


if __name__ == "__main__":
    from logging import basicConfig, ERROR
    from optparse import OptionParser
    import sys
    cmdline = OptionParser("tab-xlsx [-options] input.xlsx [output.xlsx]", epilog=__doc__)
    cmdline.add_option("-v", "--verbose", action="count", default=0)
    cmdline.add_option("-^", "--quiet", action="count", default=0, help="less verbose logging")
    cmdline.add_option("-L", "--labels", "--label-columns", metavar="LIST", action="append",  # ..
                       help="select columns to show (a,x=b)", default=[])
    cmdline.add_option("-i", "--inputformat", metavar="FMT", help="fix input format (instead of autodetection)", default="")
    cmdline.add_option("-o", "--format", metavar="FMT", help="data|text|list|wide|md|tab|csv or file", default="")
    cmdline.add_option("--ifs", action="store_true", help="-o ifs: $IFS-seperated table")
    cmdline.add_option("--dat", action="store_true", help="-o dat: tab-seperated table (with headers)")
    cmdline.add_option("--data", action="store_true", help="-o data: tab-seperated without headers")
    cmdline.add_option("--text", action="store_true", help="-o text: space-seperated without headers")
    cmdline.add_option("--list", action="store_true", help="-o text: semicolon-seperated without headers")
    cmdline.add_option("--wide", action="store_true", help="-o wide: aligned space-separated table")
    cmdline.add_option("--md", "--markdown", action="store_true", help="-o md: aligned markdown table (with |)")
    cmdline.add_option("--tabs", action="store_true", help="-o tabs: aligned tab-seperated table (instead of |)")
    cmdline.add_option("--tab", action="store_true", help="-o tab: aligned tab-seperated table (like --dat)")
    cmdline.add_option("--csv", "--scsv", action="store_true", help="-o csv: semicolon-seperated table")
    cmdline.add_option("--xls", "--xlsx", action="store_true", help="-o xls: for filename.xlsx (else csv)")
    opt, args = cmdline.parse_args()
    basicConfig(level=max(0, ERROR - 10 * opt.verbose + 10 * opt.quiet))
    if not args:
        cmdline.print_help()
        logg.error("no input filename given")
        sys.exit(1)
    data, headers = read2_tabtotext(args[0], defaultformat="xlsx")
    logg.debug("data = %s", data)
    if len(args) > 1:
        output = args[1]
        defaultformat = ""
    elif "."in opt.format:
        output = opt.format
        defaultformat = ""
    else:
        output = ""
        defaultformat = opt.format
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
        if opt.tabs:
            defaultformat = "tabs"
        if opt.tab:
            defaultformat = "tab"
        if opt.csv:
            defaultformat = "csv"
        if opt.xls:
            defaultformat = "xls"
    print_tabtotext(output, data, headers, opt.labels, defaultformat=defaultformat)
