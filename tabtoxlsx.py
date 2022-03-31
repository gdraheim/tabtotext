#! /usr/bin/python3
from typing import Optional, Union, Dict, List, Any, Sequence

from tabtotext import JSONList, JSONDict, tabToGFM

import logging
logg = logging.getLogger("TABTOXLSX")

def tabToXLSXx(result: Union[JSONList, JSONDict], sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}) -> str:
    if isinstance(result, Dict):
        result = [result]
    return tabToXLSX(result)

def tabToXLSX(result: JSONList, sorts: Sequence[str] = ["email"], formats: Dict[str, str] = {}) -> str:
    logg.error("writing xlsx is not implemented!")
    return tabToGFM(result)