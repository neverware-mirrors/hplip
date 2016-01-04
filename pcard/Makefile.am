#
#  Makefile.am - photo card automake input file
# 
#  (c) 2004 Copyright Hewlett-Packard Development Company, LP
#

noinst_PROGRAMS = ptest

hplipdir = $(datadir)/hplip
pcarddir = $(datadir)/hplip/pcard
pcardextdir = $(datadir)/hplip/pcard/pcardext

hplip_DATA =

ptest_SOURCES = ptest.c ptest.h fat.c fat.h 

noinst_SCRIPTS = pcardext/setup.py pcardext/pcardext.c
pcard_SCRIPTS = __init__.py photocard.py

noinst_DATA = build-pcardext

build-pcardext: 
	cd pcardext; \
	python setup.py build

install-data-hook:
	cd pcardext; \
	if [ "$(DESTDIR)" = "" ]; then \
	   python setup.py install; \
	else \
	   python setup.py install --root=$(DESTDIR) --prefix=$(prefix); \
	fi

copy:
	cp -r $(pcard_SCRIPTS) $(COPY_DEST)
	cp -rL $(ptest_SOURCES) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)
	mkdir -p $(COPY_DEST)/pcardext
	cp -r $(noinst_SCRIPTS) $(COPY_DEST)/pcardext

.PHONY: copy


