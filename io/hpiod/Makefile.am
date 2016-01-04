#
#  Makefile.am - HP I/O backend daemon (hpiod) automake input file
# 
#  (c) 2004 Copyright Hewlett-Packard Development Company, LP
#

sbin_PROGRAMS = hpiod

hpiod_SOURCES = hpiod.cpp channel.cpp device.cpp mlc.cpp system.cpp jddevice.cpp jetdirect.cpp\
	channel.h device.h hpiod.h mlc.h system.h

copy:
	cp -rL $(hpiod_SOURCES) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)

.PHONY: copy


