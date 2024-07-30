## TABTOTEXT

The tabtotext functions are using a universal format to store a table.

    The table is a List of records. (see python typing.List)
    Each record is a Dict of items. (see python typing.Dict)
    Each item is a Union of basic types including str, int, float, date.

The item type is useful when handling JSON data so that the actual type names are

    JSONItem = Union[str, int, float, bool, date, None, Dict[str, Any], List[Any]]
    JSONDict = Dict[str, JSONItem]
    JSONList = List[JSONDict]

Note that an Item can also contain more structured values but that is NOT considered
for the conversion process of tabtotext. It is just useful when getting json.loads
data printing them with the tabtotext utility just easily.

### tabToGFM markdown

GFM is the github-flavoured Markdown format. This reference is needed because the
original Markdown format did NOT define a table markup. This has been an extension
and it was impelemented differently in different markdown tools. However the Github
style has ensured a defacto standardization.

### tabToHTML confluence

The html format here is ready to be uploaded to Confluence as a wiki page.

### tabToJSON storage

The tabToJSON format is extended over the python "json" library as it can handle
date / datetime items. The loadJSON routine can load back the textual representation.
Note that tabToJSON is a thin layer over json.loads and json.dumps routines.

### tabToCSV storage

The tabToCSV format is extended over the python "csv" library as it can handle
date / datetime items. The loadCSV routine can load back the textual representation.
Note that tabToCSV is a thin layer csv.DictReader and csv.DictWriter routines.

### tabToTOML storage

Unlink JSON, the TOML spec does already know about DateTime elements.
Here's an implementation without tomllib. Note that tomllib is part
of the Python standard library since 3.11.

### Extended format()

The "formats" argument to each tabToFunction allows to provide string.format()
specifications in the style of "{:2d}".

There is an extension that can handle "{:h}" representing a float with the
fraction given in quarters. So you have "1/4" ane "1/2" and "3/4" with their
latin-1 (extended-ascii) 0x00Bx unicode code points. The full strHours (.00) 
is encoded with "h". If you use the formatter "{:q}" then the full number is 
encoded with ".". Addtionally, there is a formatter with "{:M}" scaling the
number by Mibi down and then using strHours with "." full encoding. Using
some "{:H}" however converts to clock values like "2:15" and using "{:$}"
will convert to the default currency like "2.25€".

## tabxlsx and tabtotext()

In the newer implementions there is no "formats" argument anymore but an
addition "selects" to help with print_tabtotext. And there is Excel support
available in tabxlsx.py that does not require openpyxl. This file is
installed as a seperate module "pip install tabxlsx" however (or 
via 'make insxlsx' from development).

At a later time, this will be the basis of a seperate tabtotext project.
