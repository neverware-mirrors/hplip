#
#  Makefile.am - hp cups backend automake input file
# 
#  (c) 2004 Copyright Hewlett-Packard Development Company, LP
#

cupsdir = $(CUPS_BACKEND_PATH)

cups_PROGRAMS = hp
hp_SOURCES = hp.c 

copy:
	cp -rL $(hp_SOURCES) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)

.PHONY: copy


