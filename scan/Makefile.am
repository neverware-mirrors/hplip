#
#  Makefile.am - scan automake input file
# 
#  (c) 2004 Copyright Hewlett-Packard Development Company, LP
#

hplipdir = $(libexecdir)/hplip/scan

hplip_SCRIPTS = __init__.py pml_scanner.py sane.py scanner.py scl.py scl_scanner.py

copy:
	cp -rL $(hplip_SCRIPTS) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)

.PHONY: copy
