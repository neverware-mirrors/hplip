#
#  Makefile.am - base automake input file
# 
#  (c) 2004 Copyright Hewlett-Packard Development Company, LP
#

hplipdir = $(libexecdir)/hplip/base

hplip_SCRIPTS = maint.py codes.py g.py mfpdtf2.py pml.py status.py async.py \
    database.py __init__.py mfpdtf.py service.py utils.py async_qt.py \
    device.py logger.py msg.py slp.py exif.py strings.py

copy:
	cp -rL $(hplip_SCRIPTS) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)

.PHONY: copy
