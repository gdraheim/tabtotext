# TabToText 

The input is any table-like data (list of dicts), supporting atleast JSON data types plus date/time.

The output is highly configurable. The output data type includes xlsx (Excel) in a second variant
based on openpyxl. The default output shows markdown tables. Further options are csv, json, toml
and others. It is easily possible to rearrange columns and their sorting for the output. Each
data item can be formatted specifically.

## table-like data

For input data it is possible to use base types for list and dict with Any value as they
get converted to str on ouput.

    data = [{"a": 1}, {"b": "foobar"}, {"c": True}]
    print(tabtotext(data))
    
    | a   | b      | c
    | --- | ------ | ----
    | 1   |        |
    |     | foobar |
    |     |        | (yes)

Instead of a List as input it is possible to use any Iterable. Instead of using a Dict elements it is possible to use NamedTuple and Dataclass row elements.

Beyond bool, int, float, str types there is special support for Date and Time values. The support for None varies for each output data format.

## select and sorting

Just provide the columns to be put into the output as the second argument of `tabtotext()`. This selects these columns and sorts the output lines on them.

    data = [{"a": 1}, {"b": "foobar"}, {"c": True}, {"b": "extra"} ]
    print(tabtotext(data, ["b", "a", "c"]))
    
    | b      | c     | a
    | ------ | ----- | ----
    | extra  |       |
    | foobar |       |
    |        | (yes) |
    |        |       | 1

## formatting

After each column name it is possible to add a formatter following python's str.format. 
Any empty ":" represents a right-aligned format.

    data = [{"a": 1}, {"b": "foobar"}, {"c": True}, {"b": "extra"} ]
    print(tabtotext(data, ["b:", "a:s", "c:.2f"]))
    
    | b      | c     | a
    | ------ | ----- | ----
    |  extra |       |
    | foobar |       |
    |        | True  |
    |        |       | 1.00


## output 

Most of the time the data will be printed to the terminal. Saving to a file is
required as well and this includes a number of binary formats like xlsx Excel.
For usage in a shell pipelines the stream output may also be other text-based 
formats that can be used as input for other tools.

    data = [{"a": 1}, {"b": "foobar"}, {"c": True}, {"b": "extra"} ]
    print_tabtotext("wide", data, ["b:", "a:s", "c:.2f"]))
    
    b      c     a
    extra  ~     ~ 
    foobar ~     ~ 
    ~      True  ~
    ~      ~     1.00

If the output specifier contains a dot (.) or slash (/) then the converted table is 
not printed but written to a file as given. The output format is detected from the
file extension. There are options to force to print or force to write the data.

    data = [{"a": 1}, {"b": "foobar"}, {"c": True}, {"b": "extra"} ]
    print_tabtotext("data.csv", data, ["b:", "a:s", "c:.2f"]))
    
    : 4 results data.csv

    > cat data.csv
    b;c;a
    extra;;
    foobar;;
    ;True;
    ;;1.00
    
The "4" hints on four rows of data and "results" says there is a header line. 

## cli options

The first argument of `print_tabtotext()` is taylored to have just one cli option `-o` that
can serve both as a format parameter for printing to to the terminal, or diverting the
output to a file with that format type.

    cmdline.add_option("-o", "--output", metavar="(FILE.)TYPE", 
                       help="output filename.format or just format (md,wide,csv,xlsx)")
    cmdline.add_option("-l", "--select", metavar="COLUMN:FORMAT", action="append",
                       help="select and sort by columns with optionally formatted items")
