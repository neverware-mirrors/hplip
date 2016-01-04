#
#  Makefile.am - ip automake input file
# 
#  (c) 2004 Copyright Hewlett-Packard Development Company, LP
#

lib_LTLIBRARIES = libhpip.la

libhpip_la_SOURCES = xconvolve.c xfax.c xgrayout.c xjpg_dct.c xjpg_fix.c xpad.c xrotate.c xskel.c xtiff.c \
ipmain.c xchgbpp.c xcrop.c xgamma.c xjpg_dec.c xjpg_huf.c xpcx.c xsaturation.c xtable.c xtonemap.c \
xbi2gray.c xcolrspc.c xfakemono.c xgray2bi.c xinvert.c xjpg_enc.c xmatrix.c xpnm.c xscale.c xthumb.c xyxtract.c \
hpip.h ipdefs.h xform.h xjpg_dct.h xjpg_huf.h xjpg_mrk.h

libhpip_la_LDFLAGS = -version-info 0:1:0

copy:
	cp -rL $(libhpip_la_SOURCES) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)

.PHONY: copy


