#
#  Makefile.am - prnt automake input file
# 
#  (c) 2004 Copyright Hewlett-Packard Development Company, LP
#

hplipdir = $(datadir)/hplip
prntdir = $(datadir)/hplip/prnt
cupsextdir = $(datadir)/hplip/prnt/cupsext

hplip_DATA =

prnt_SCRIPTS = cups.py __init__.py ldl.py pcl.py 

noinst_SCRIPTS = cupsext/setup.py cupsext/cupsext.c

noinst_DATA = build-cupsext

build-cupsext: 
	cd cupsext; \
	python setup.py build

install-data-hook:
	cd cupsext; \
	if [ "$(DESTDIR)" = "" ]; then \
	   python setup.py install; \
	else \
	   python setup.py install --root=$(DESTDIR) --prefix=$(prefix); \
	fi

uninstall-hook:
#	cd cupsext; \
#	python setup.py uninstall

copy:
	cp -r $(prnt_SCRIPTS) $(COPY_DEST)
	mkdir -p $(COPY_DEST)/cupsext
	cp -r $(noinst_SCRIPTS) $(COPY_DEST)/cupsext
	cp -rL $(DIST_SOURCES) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)

.PHONY: copy
