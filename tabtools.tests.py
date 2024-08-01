#! /usr/bin/env python3

__copyright__ = "(C) 2022-2024 Guido Draheim, licensed under the Apache License 2.0"""
__version__ = "1.1.3321"

from tabtools import *
import sys
import os
import unittest
import logging
from fnmatch import fnmatchcase as fnmatch

logg = logging.getLogger("TEST")

X1 = chr(norm_frac_1_4)
X2 = chr(norm_frac_1_2)
X3 = chr(norm_frac_3_4)
Q1 = chr(norm_frac_1_5)
Q2 = chr(norm_frac_2_5)
Q3 = chr(norm_frac_3_5)
Q4 = chr(norm_frac_4_5)
R1 = chr(norm_frac_1_6)
R2 = chr(norm_frac_1_3)
R3 = chr(norm_frac_1_2)
R4 = chr(norm_frac_2_3)
R5 = chr(norm_frac_5_6)

USD = chr(currency_dollar)
EUR = chr(currency_euro)
YEN = chr(currency_yen)
BPD = chr(currency_pound)
CUR = chr(currency_symbol)

K = 1024
M = 1024 * 1024

def rep(val: str) -> str:
    val = val.replace("1/4", X1).replace("1/2", X2).replace("3/4", X3)
    val = val.replace("1/5", Q1).replace("2/5", Q2).replace("3/5", Q3)
    val = val.replace("4/5", Q4).replace("1/6", R1).replace("2/6", R2)
    val = val.replace("3/6", R3).replace("4/6", R4).replace("5/6", R5)
    val = val.replace("1/3", R2).replace("2/3", R4)
    val = val.replace("EUR", EUR).replace("CUR", CUR)
    val = val.replace("YEN", YEN).replace("BPD", BPD)
    return val

class zeit2jiraTest(unittest.TestCase):
    def test_100(self) -> None:
        numm = Frac4(0)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0:00")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.0)
    def test_101(self) -> None:
        numm = Frac4(0.25)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0:15")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_102(self) -> None:
        numm = Frac4(0.50)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0:30")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.50)
    def test_103(self) -> None:
        numm = Frac4(0.75)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0:45")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.75)
    def test_104(self) -> None:
        numm = Frac4(0.99)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1:00")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.0)
    def test_110(self) -> None:
        numm = Frac4(1)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1:00")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.0)
    def test_111(self) -> None:
        numm = Frac4(1.25)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1:15")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.25)
    def test_112(self) -> None:
        numm = Frac4(1.50)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1:30")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.50)
    def test_113(self) -> None:
        numm = Frac4(1.75)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1:45")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.75)
    def test_114(self) -> None:
        numm = Frac4(1.99)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("2:00")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 2)
    def test_120(self) -> None:
        numm = Frac4(12)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12:00")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12)
    def test_121(self) -> None:
        numm = Frac4(12.25)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12:15")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12.25)
    def test_122(self) -> None:
        numm = Frac4(12.50)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12:30")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12.50)
    def test_123(self) -> None:
        numm = Frac4(12.75)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12:45")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12.75)
    def test_124(self) -> None:
        numm = Frac4(12.99)
        data = "{:H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13:00")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 13.00)
    def test_173(self) -> None:
        numm = Frac4(12.75)
        data = "{:04H}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0012:45")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12.75)
    # ..............................
    def test_200(self) -> None:
        numm = Frac4(0)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0h")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.0)
    def test_201(self) -> None:
        numm = Frac4(0.25)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/4h")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_202(self) -> None:
        numm = Frac4(0.50)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/2h")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.50)
    def test_203(self) -> None:
        numm = Frac4(0.75)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("3/4h")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.75)
    def test_204(self) -> None:
        numm = Frac4(0.9)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1h")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.0)
    def test_210(self) -> None:
        numm = Frac4(1)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1h")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.0)
    def test_211(self) -> None:
        numm = Frac4(1.25)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/4")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.25)
    def test_212(self) -> None:
        numm = Frac4(1.50)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/2")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.50)
    def test_213(self) -> None:
        numm = Frac4(1.75)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13/4")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 1.75)
    def test_214(self) -> None:
        numm = Frac4(1.9)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("2h")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 2)
    def test_220(self) -> None:
        numm = Frac4(12)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12h")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12)
    def test_221(self) -> None:
        numm = Frac4(12.25)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/4")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12.25)
    def test_222(self) -> None:
        numm = Frac4(12.50)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/2")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12.50)
    def test_223(self) -> None:
        numm = Frac4(12.75)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("123/4")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12.75)
    def test_224(self) -> None:
        numm = Frac4(12.9)
        data = "{:h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13h")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 13.00)
    def test_273(self) -> None:
        numm = Frac4(12.75)
        data = "{:04h}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("00123/4")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 12.75)
    # ..............................
    def test_300(self) -> None:
        numm = Frac4(0)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0)
    def test_301(self) -> None:
        numm = Frac4(0.25)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/4")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_302(self) -> None:
        numm = Frac4(0.50)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/2")
        self.assertEqual(want, data)
    def test_303(self) -> None:
        numm = Frac4(0.75)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("3/4")
        self.assertEqual(want, data)
    def test_304(self) -> None:
        numm = Frac4(0.9)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1.")
        self.assertEqual(want, data)
    def test_310(self) -> None:
        numm = Frac4(1)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1.")
        self.assertEqual(want, data)
    def test_311(self) -> None:
        numm = Frac4(1.25)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/4")
        self.assertEqual(want, data)
    def test_312(self) -> None:
        numm = Frac4(1.50)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/2")
        self.assertEqual(want, data)
    def test_313(self) -> None:
        numm = Frac4(1.75)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13/4")
        self.assertEqual(want, data)
    def test_314(self) -> None:
        numm = Frac4(1.9)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("2.")
        self.assertEqual(want, data)
    def test_320(self) -> None:
        numm = Frac4(12)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12.")
        self.assertEqual(want, data)
    def test_321(self) -> None:
        numm = Frac4(12.25)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/4")
        self.assertEqual(want, data)
    def test_322(self) -> None:
        numm = Frac4(12.50)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/2")
        self.assertEqual(want, data)
    def test_323(self) -> None:
        numm = Frac4(12.75)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("123/4")
        self.assertEqual(want, data)
    def test_324(self) -> None:
        numm = Frac4(12.9)
        data = "{:q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13.")
        self.assertEqual(want, data)
    def test_373(self) -> None:
        numm = Frac4(12.75)
        data = "{:04q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("00123/4")
        self.assertEqual(want, data)
    # ..............................
    def test_400(self) -> None:
        numm = Frac4(0)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0M")
        self.assertEqual(want, data)
    def test_401(self) -> None:
        numm = Frac4(0.25 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/4M")
        self.assertEqual(want, data)
    def test_402(self) -> None:
        numm = Frac4(0.50 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/2M")
        self.assertEqual(want, data)
    def test_403(self) -> None:
        numm = Frac4(0.75 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("3/4M")
        self.assertEqual(want, data)
    def test_404(self) -> None:
        numm = Frac4(0.9 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1.M")
        self.assertEqual(want, data)
    def test_410(self) -> None:
        numm = Frac4(1 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1.M")
        self.assertEqual(want, data)
    def test_411(self) -> None:
        numm = Frac4(1.25 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/4M")
        self.assertEqual(want, data)
    def test_412(self) -> None:
        numm = Frac4(1.50 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/2M")
        self.assertEqual(want, data)
    def test_413(self) -> None:
        numm = Frac4(1.75 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13/4M")
        self.assertEqual(want, data)
    def test_414(self) -> None:
        numm = Frac4(1.9 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("2.M")
        self.assertEqual(want, data)
    def test_420(self) -> None:
        numm = Frac4(12 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12.M")
        self.assertEqual(want, data)
    def test_421(self) -> None:
        numm = Frac4(12.25 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/4M")
        self.assertEqual(want, data)
    def test_422(self) -> None:
        numm = Frac4(12.50 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/2M")
        self.assertEqual(want, data)
    def test_423(self) -> None:
        numm = Frac4(12.75 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("123/4M")
        self.assertEqual(want, data)
    def test_424(self) -> None:
        numm = Frac4(12.9 * M)
        data = "{:M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13.M")
        self.assertEqual(want, data)
    def test_473(self) -> None:
        numm = Frac4(12.75 * M)
        data = "{:04M}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("00123/4M")
        self.assertEqual(want, data)
    # ..............................
    def test_500(self) -> None:
        numm = Frac4(0)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0")
        self.assertEqual(want, data)
    def test_501(self) -> None:
        numm = Frac4(0.2)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/5")
        self.assertEqual(want, data)
    def test_502(self) -> None:
        numm = Frac4(0.4)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("2/5")
        self.assertEqual(want, data)
    def test_503(self) -> None:
        numm = Frac4(0.6)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("3/5")
        self.assertEqual(want, data)
    def test_504(self) -> None:
        numm = Frac4(0.8)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("4/5")
        self.assertEqual(want, data)
    def test_505(self) -> None:
        numm = Frac4(0.9)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1.")
        self.assertEqual(want, data)
    def test_510(self) -> None:
        numm = Frac4(1)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1.")
        self.assertEqual(want, data)
    def test_511(self) -> None:
        numm = Frac4(1.2)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/5")
        self.assertEqual(want, data)
    def test_512(self) -> None:
        numm = Frac4(1.4)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12/5")
        self.assertEqual(want, data)
    def test_513(self) -> None:
        numm = Frac4(1.6)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13/5")
        self.assertEqual(want, data)
    def test_514(self) -> None:
        numm = Frac4(1.8)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("14/5")
        self.assertEqual(want, data)
    def test_515(self) -> None:
        numm = Frac4(1.9)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("2.")
        self.assertEqual(want, data)
    def test_520(self) -> None:
        numm = Frac4(12)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12.")
        self.assertEqual(want, data)
    def test_521(self) -> None:
        numm = Frac4(12.2)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/5")
        self.assertEqual(want, data)
    def test_522(self) -> None:
        numm = Frac4(12.4)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("122/5")
        self.assertEqual(want, data)
    def test_523(self) -> None:
        numm = Frac4(12.6)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("123/5")
        self.assertEqual(want, data)
    def test_524(self) -> None:
        numm = Frac4(12.8)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("124/5")
        self.assertEqual(want, data)
    def test_525(self) -> None:
        numm = Frac4(12.9)
        data = "{:Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13.")
        self.assertEqual(want, data)
    def test_573(self) -> None:
        numm = Frac4(12.6)
        data = "{:04Q}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("00123/5")
        self.assertEqual(want, data)
    # ..............................
    def test_600(self) -> None:
        numm = Frac4(0)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0")
        self.assertEqual(want, data)
    def test_601(self) -> None:
        numm = Frac4(0.15)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/6")
        self.assertEqual(want, data)
    def test_602(self) -> None:
        numm = Frac4(0.3)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/3")
        self.assertEqual(want, data)
    def test_603(self) -> None:
        numm = Frac4(0.5)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1/2")
        self.assertEqual(want, data)
    def test_604(self) -> None:
        numm = Frac4(0.65)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("2/3")
        self.assertEqual(want, data)
    def test_605(self) -> None:
        numm = Frac4(0.8)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("5/6")
        self.assertEqual(want, data)
    def test_606(self) -> None:
        numm = Frac4(0.95)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1.")
        self.assertEqual(want, data)
    def test_610(self) -> None:
        numm = Frac4(1)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("1.")
        self.assertEqual(want, data)
    def test_611(self) -> None:
        numm = Frac4(1.15)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/6")
        self.assertEqual(want, data)
    def test_612(self) -> None:
        numm = Frac4(1.3)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/3")
        self.assertEqual(want, data)
    def test_613(self) -> None:
        numm = Frac4(1.5)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("11/2")
        self.assertEqual(want, data)
    def test_614(self) -> None:
        numm = Frac4(1.65)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12/3")
        self.assertEqual(want, data)
    def test_615(self) -> None:
        numm = Frac4(1.8)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("15/6")
        self.assertEqual(want, data)
    def test_616(self) -> None:
        numm = Frac4(1.95)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("2.")
        self.assertEqual(want, data)
    def test_620(self) -> None:
        numm = Frac4(12)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("12.")
        self.assertEqual(want, data)
    def test_621(self) -> None:
        numm = Frac4(12.15)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/6")
        self.assertEqual(want, data)
    def test_622(self) -> None:
        numm = Frac4(12.3)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/3")
        self.assertEqual(want, data)
    def test_623(self) -> None:
        numm = Frac4(12.5)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("121/2")
        self.assertEqual(want, data)
    def test_624(self) -> None:
        numm = Frac4(12.65)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("122/3")
        self.assertEqual(want, data)
    def test_625(self) -> None:
        numm = Frac4(12.8)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("125/6")
        self.assertEqual(want, data)
    def test_626(self) -> None:
        numm = Frac4(12.95)
        data = "{:R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("13.")
        self.assertEqual(want, data)
    def test_673(self) -> None:
        numm = Frac4(12.5)
        data = "{:04R}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("00121/2")
        self.assertEqual(want, data)
    # ..............................
    def test_900(self) -> None:
        numm = Frac4(0)
        data = "{:$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.00EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.00)
    def test_901(self) -> None:
        numm = Frac4(0.25)
        data = "{:$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.25EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_902(self) -> None:
        numm = Frac4(0.50)
        data = "{:$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.50EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.50)
    def test_903(self) -> None:
        numm = Frac4(0.6666)
        data = "{:$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.66EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.66)
    def test_910(self) -> None:
        numm = Frac4(0)
        data = "{:US$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.00$")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.00)
    def test_911(self) -> None:
        numm = Frac4(0.25)
        data = "{:US$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.25$")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_912(self) -> None:
        numm = Frac4(0.50)
        data = "{:US$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.50$")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.50)
    def test_913(self) -> None:
        numm = Frac4(0.6666)
        data = "{:US$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.66$")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.66)
    def test_930(self) -> None:
        numm = Frac4(0)
        data = "{:EU$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.00EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.00)
    def test_931(self) -> None:
        numm = Frac4(0.25)
        data = "{:EU$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.25EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_932(self) -> None:
        numm = Frac4(0.50)
        data = "{:EU$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.50EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.50)
    def test_933(self) -> None:
        numm = Frac4(0.6666)
        data = "{:EU$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.66EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.66)
    def test_940(self) -> None:
        numm = Frac4(0)
        data = "{:EC$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.00EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.00)
    def test_941(self) -> None:
        numm = Frac4(0.25)
        data = "{:EC$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.25EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_942(self) -> None:
        numm = Frac4(0.50)
        data = "{:EC$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.50EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.50)
    def test_943(self) -> None:
        numm = Frac4(0.6666)
        data = "{:EC$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.66EUR")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.66)
    def test_950(self) -> None:
        numm = Frac4(0)
        data = "{:JP$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.00YEN")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.00)
    def test_951(self) -> None:
        numm = Frac4(0.25)
        data = "{:JP$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.25YEN")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_952(self) -> None:
        numm = Frac4(0.50)
        data = "{:JP$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.50YEN")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.50)
    def test_953(self) -> None:
        numm = Frac4(0.6666)
        data = "{:JP$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.66YEN")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.66)
    def test_960(self) -> None:
        numm = Frac4(0)
        data = "{:CN$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.00YEN")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.00)
    def test_961(self) -> None:
        numm = Frac4(0.25)
        data = "{:CN$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.25YEN")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_962(self) -> None:
        numm = Frac4(0.50)
        data = "{:CN$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.50YEN")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.50)
    def test_963(self) -> None:
        numm = Frac4(0.6666)
        data = "{:CN$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.66YEN")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.66)
    def test_970(self) -> None:
        numm = Frac4(0)
        data = "{:BP$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.00BPD")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0)
    def test_971(self) -> None:
        numm = Frac4(0.25)
        data = "{:BP$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.25BPD")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.25)
    def test_972(self) -> None:
        numm = Frac4(0.50)
        data = "{:BP$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.50BPD")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.50)
    def test_973(self) -> None:
        numm = Frac4(0.6666)
        data = "{:BP$}".format(numm)  # type: ignore[str-format]
        logg.info("data = %s", data)
        want = rep("0.66BPD")
        self.assertEqual(want, data)
        back = fracfloat(data)
        self.assertEqual(back, 0.66)

if __name__ == "__main__":
    # unittest.main()
    from optparse import OptionParser
    cmdline = OptionParser("%prog [t_]test...")
    cmdline.add_option("-v", "--verbose", action="count", default=0, help="more verbose logging")
    cmdline.add_option("-^", "--quiet", action="count", default=0, help="less verbose logging")
    cmdline.add_option("--failfast", action="store_true", default=False,
                       help="Stop the test run on the first error or failure. [%default]")
    cmdline.add_option("--xmlresults", metavar="FILE", default=None,
                       help="capture results as a junit xml file [%default]")
    opt, args = cmdline.parse_args()
    logging.basicConfig(level=max(0, logging.WARNING - 10 * opt.verbose + 10 * opt.quiet))
    if not args:
        args = ["test_*"]
    suite = unittest.TestSuite()
    for arg in args:
        if len(arg) > 2 and arg[0].isalpha() and arg[1] == "_":
            arg = "test_" + arg[2:]
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if "*" not in arg: arg += "*"
                if arg.startswith("_"): arg = arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # running
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "wb")
    if xmlresults:
        import xmlrunner  # type: ignore[import]
        Runner = xmlrunner.XMLTestRunner
        result = Runner(xmlresults).run(suite)
        logg.info(" XML reports written to %s", opt.xmlresults)
    else:
        Runner = unittest.TextTestRunner
        result = Runner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
