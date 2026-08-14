
## TABXLSX - minimal Excel support

TabXLSX reads and writes Excel xlsx files. It is a single file implementation
that does not depend on other libraries. The output defaults to a markdown table 
and csv-like output is available as well. This allows piping the data into other scripts.

A number of output format options are available but less than the tabtotext.py module. 
The export to xlsx was orginally written with openpyx1 for tabtotext but it is possible 
to write simple xlsx tables just with Python's `zipfile` and  `xml.etree` builtin modules. 
That is also faster.

### import tabxlsx

The tabxlsx.py script can be used as a library.

* use `readFromXLSX("file.xlsx") -> data` to get data out of an Excel file
* use `tabtextfileXLSX("file.xlsx") -> (data, headers)` to get data and header info
* use `tabtoXLSX("file.xlsx", data, headers, selected)` to write data into an Excel file

and there are generic function that allow to write CSV and Markdown tables. These will
run the xlsx output/input when the filename endswith ".xlsx" or ".xls".

* use `tabtextfile("file.csv") -> (data, headers)` to get data and header from csv files
* use `tabtextfile("file.md") -> (data, headers)` to get it for markdown tables in text
* use `print_tabtotext("file.csv", data, headers, selected)` to write a csv file
* use `print_tabtotext("file.md", data, headers, selected)` for markdown tables
* use `print_tabtotext("", data, headers, selected, defaultformat="csv")` to stdout

The code itself mimics that of openpyx1. 
* use `load_workbook(filename)` to get a `Workbook` data frame from a file
* use `make_workbook(data, headers)`to create a `Workbook` from the provided data
* use `Workbook.save(filename)` to save the data to an xlsx file
* and `workbook.create_sheet().cell(1,1).alignment = Alignment(horizontal="right")`
* and of course `workbook.active.cell(1,2).value = 1` with Python's basic data types

The `headers` arguments defines the default order and formatting of the provided
input data, which is `List[Dict[str, CellValue]]`, so each row does not have an
implicit order. Using `["b:.2f", "a"]` shows the `"b"` values first formatted with
two digits after the decimal point. Then the `"a"` column follows, and then the rest 
in alphabetic order.

### run tabxlsx.py

Use `tabxlsx.py --help` for the latest options when running the script as a command
line tool. The first argument is usually some `data.xlsx` but it can also be `.csv`
or `.md` file - the input parser gets selected from the file extension automatically.

Additional arguments are the columns to be `selected` for output - being a subset of
the data from the input file. Just like with `headers` each column can be formatted
in the style of Python's `string.format()`. The `selected` columns fall back to known
formatting if not provided - including Date/Time columns which are generally
recognized in all library parts.

Use `"@csv"` to ensure output as CSV instead of the default markdown tables. For
the markdown tables, the columns of each row have the same width mich makes the
data easier to read. Alternative @-formats are available as well, e.g. `"@wide"`
or `"@data"` with the latter being tab-seperated CSV.

* use `./tabxlsx.py data.xlsx -o data.csv` # to convert from xlsx to csv
* use `./tabxlsx.py data.csv -o data.xlsx` # to convert from csv to xslx
* use `./tabxlsx.py data.xlsx @csv` # to show the xlsx data as csv lines
* use `./tabxlsx.py data.xlsx a b @csv` # but only the input columns a and b
* use `./tabxlsx.py data.xlsx b:2.f a` # format the b number for a 2-column table
* use `./tabxlsx.py data.xlsx a --unique` # get one column out, remove duplicates

Converting to and from `"@json"` is supported as well but it spoils the column order.


### development

The code is just a fraction of the `"tabtotext.py"` formatting engine. The main
channel for distribution of that single `"tabxlsx.py"`script is via pypi.org. You
can use `pip download tabxlsx` to download the latest script to any target system.

* https://pypi.org/project/tabxlsx/

As the script does not have any dependencies, it can be copied around as is. Feel
free to integrate it into your own Python project. Note that there is also a
`unittest`-based `"tabxlsx.tests.py"` code that can ensure backward-compatibility 
if you start extending the tabxlsx code.

* https://github.com/gdraheim/tabtotext
* https://github.com/gdraheim/timetrack-odoo

The original implementation in tabtoxlsx was based on openpyx1. The resulting xlsx
files were inspected how to write them with just Python's internal `zipfile`. The
xlsx reader is using `zipfile` and Python's internal `xml.etree`. This should be
portable to JPython and IronPython as well. And tests showed tabxlsx to be 10x
faster than openpyx1 for small datasets. For large datasets it is 3-4x faster.

| test_9888 (--bigfile=1000000) | time
| ----------------------------- | ----
| 100000 numbers tabxlsx write xlsx time | 00'02.548209
| 100000 numbers openpyxl write xlsx time | 00'09.300701
| 1.000.000 numbers tabxlsx write xlsx time  | 00'27.265536
| 1.000.000 numbers openpyxl write xlsx time | 01'31.813367
| 1.000.000 numbers read xls and write json | 00'41.019995
| 1.000.000 numbers read xlsx and write json | 00'55.683582


Have fun!










