#! /usr/bin/make -f

BASEYEAR=2021
FOR=today

FILES = *.py *.cfg
PYTHON3 = python3
PYTHONVERSION = 3.8
COVERAGE3 = $(PYTHON3) -m coverage
TWINE = twine
GIT = git

SCRIPT = tabtotext.py
TAB_TOOLS = tabtools.py
TAB_UTILS = tabtotext.py
TAB_2XLSX = tabtoxlsx.py
TAB_4XLSX = tabxlsx.py

PARALLEL = -j2

default: help

check:
	$(MAKE) frac
	$(MAKE) tabt
	$(MAKE) tabx
chec: ; $(MAKE) check V=--failfast
cc: ; $(MAKE) check "V=-vv --failfast"

tests:
	$(MAKE) f.frac
	$(MAKE) x.tabt
	$(MAKE) y.tabx
	wc -l TEST-*.xml

tabtools.tests: frac
f.frac: ; $(PYTHON3) $(TAB_TOOLS:.py=.tests.py) -v $V  --xmlresults=TEST-$@.xml
f frac: ; $(PYTHON3) $(TAB_TOOLS:.py=.tests.py) -v $V
f_%: ;    $(PYTHON3) $(TAB_TOOLS:.py=.tests.py) -v $V $@ --failfast

tabtotext.tests: tabt
x.tabt: ; $(PYTHON3) $(TAB_UTILS:.py=.tests.py) -v $V  --xmlresults=TEST-$@.xml
x tabt: ; $(PYTHON3) $(TAB_UTILS:.py=.tests.py) -v $V
x_%: ;    $(PYTHON3) $(TAB_UTILS:.py=.tests.py) -v $V $@ --failfast
X_%: ;    $(PYTHON3) $(TAB_UTILS:.py=.tests.py) -vv $V $@ --failfast --keep

tabxlsx.tests: tabx
y.tabx: ; $(PYTHON3) $(TAB_4XLSX:.py=.tests.py) -v $V  --xmlresults=TEST-$@.xml
y tabx: ; $(PYTHON3) $(TAB_4XLSX:.py=.tests.py) -v $V
y_%: ;    $(PYTHON3) $(TAB_4XLSX:.py=.tests.py) -v $V $@ --failfast
Y_%: ;    $(PYTHON3) $(TAB_4XLSX:.py=.tests.py) -vv $V $@ --failfast --keep

verfiles:
	@ grep -l __version__ $(FILES) | grep -v .tests.py | { while read f; do echo $$f; done; } 

version:
	@ grep -l __version__ $(FILES) | { while read f; do : \
	; THISYEAR=`date +%Y -d "$(FOR)"` ; YEARS=$$(expr $$THISYEAR - $(BASEYEAR)) \
        ; WEEKnDAY=`date +%W%u -d "$(FOR)"` ; sed -i \
	-e "/^version /s/[.]-*[0123456789][0123456789][0123456789]*/.$$YEARS$$WEEKnDAY/" \
	-e "/^ *__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$YEARS$$WEEKnDAY\"/" \
	-e "/^ *__version__/s/[.]\\([0123456789]\\)\"/.\\1.$$YEARS$$WEEKnDAY\"/" \
	-e "/^ *__copyright__/s/(C) \\([123456789][0123456789]*\\)-[0123456789]*/(C) \\1-$$THISYEAR/" \
	-e "/^ *__copyright__/s/(C) [123456789][0123456789]* /(C) $$THISYEAR /" \
	$$f; done; }
	@ grep ^__version__ $(FILES) | grep -v .tests.py
	@ ver=`cat $(SCRIPT) | sed -e '/__version__/!d' -e 's/.*= *"//' -e 's/".*//' -e q` \
	; echo "# $(GIT) commit -m v$$ver"
tag:
	@ ver=`grep "version.*=" setup.cfg | sed -e "s/version *= */v/"` \
	; rev=`$(GIT) rev-parse --short HEAD` \
	; echo ": ${GIT} tag $$ver $$rev"

help:
	$(PYTHON3) $(SCRIPT) --help

clean:
	- rm *.pyc 
	- rm -rf __pycache__
	- rm -rf *.tmp
	- rm -rf tmp tmp.files
	- rm TEST-*.xml
	- rm setup.py README
	- rm -rf build dist *.egg-info
	- rm *.cover *,cover

############## https://pypi.org/...


TAB=tabxlsx.tmp
xlsx tabxlsx:
	test ! -d $(TAB) || rm -rf $(TAB)
	mkdir -v $(TAB)
	$(MAKE) $(TAB)/setup.py
	cd $(TAB) && $(PYTHON3) setup.py sdist
	cd $(TAB) && $(TWINE) check dist/*
	@echo "(cd $(TAB) && $(TWINE) upload dist/*)"
tabxlsx.tmp/setup.py: setup.tabxlsx.cfg tabxlsx.py tabxlsx.md tabxlsx.tests.py LICENSE Makefile
	cp -v setup.tabxlsx.cfg $(dir $@)/setup.cfg
	cp -v tabxlsx.py $(dir $@)/
	cp -v tabxlsx.md $(dir $@)/
	cp -v tabxlsx.tests.py $(dir $@)/
	cp -v LICENSE $(dir $@)/tabxlsx.txt
	{ echo '#!/usr/bin/env python3' \
	; echo 'import setuptools' \
	; echo 'setuptools.setup()' ; } > $@
	chmod +x $@
insxlsx:
	$(MAKE) $(TAB)/setup.py
	cd $(TAB) && $(PYTHON3) -m pip install --no-compile --user .
	$(MAKE) showxlsx
showxlsx:
	test -d tmp || mkdir -v tmp
	cd tmp && $(PYTHON3) -m pip show -f $$(sed -e '/^name *=/!d' -e 's/.*= *//' ../setup.tabxlsx.cfg)
unsxlsx: 
	test -d tmp || mkdir -v tmp
	cd tmp && $(PYTHON3) -m pip uninstall -vv --yes $$(sed -e '/^name *=/!d' -e 's/.*= *//' ../setup.tabxlsx.cfg)

README: README.MD Makefile
	cat README.MD | sed -e "/\\/badge/d" -e /^---/q > README
setup.py: Makefile
	{ echo '#!/usr/bin/env python3' \
	; echo 'import setuptools' \
	; echo 'setuptools.setup()' ; } > setup.py
	chmod +x setup.py
setup.py.tmp: Makefile
	echo "import setuptools ; setuptools.setup()" > setup.py

.PHONY: build
build:
	rm -rf build dist *.egg-info
	$(MAKE) $(PARALLEL) README setup.py
	# pip install --root=~/local . -v
	$(PYTHON3) setup.py sdist
	- rm -v setup.py README
	$(TWINE) check dist/*
	: $(TWINE) upload dist/*

ins install:
	$(MAKE) setup.py
	$(PYTHON3) -m pip install --no-compile --user .
	rm -v setup.py
	$(MAKE) show | sed -e "s|[.][.]/[.][.]/[.][.]/bin|$$HOME/.local/bin|"
show:
	test -d tmp || mkdir -v tmp
	cd tmp && $(PYTHON3) -m pip show -f $$(sed -e '/^name *=/!d' -e 's/.*= *//' ../setup.cfg)
uns uninstall: setup.py
	test -d tmp || mkdir -v tmp
	cd tmp && $(PYTHON3) -m pip uninstall -v --yes $$(sed -e '/^name *=/!d' -e 's/.*= *//' ../setup.cfg)
