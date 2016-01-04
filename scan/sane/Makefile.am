#
#  Makefile.am - hp sane backend automake input file
# 
#  (c) 2004 Copyright Hewlett-Packard Development Company, LP
#

BASENAME=sane-hpaio
MAJORVER=1
MINORVER=0
AGEVER=0
SONOVER=lib$(BASENAME).so
SOSHORT=$(SONOVER).$(MAJORVER)
SOLONG=$(SOSHORT).$(MINORVER).$(AGEVER)

sanedir = /usr/lib/sane

lib_LTLIBRARIES = libsane-hpaio.la

libsane_hpaio_la_SOURCES = hpaio.c mfpdtf.c pml.c scl.c system.c \
hpaio.h pml.h saneopts.h system.h \
mfpdtf.h sane.h scl.h tables.h

libsane_hpaio_la_LDFLAGS = -version-info $(MAJORVER):$(MINORVER):$(AGEVER) 

# The following is a interlibrary dependency that must be compiled first.
libsane_hpaio_la_LIBADD = ../../ip/libhpip.la

install-exec-hook:
#
#       Do full install if not rpm_install.
	if [ "$(rpm_install)" = "no" ]; then \
	   ln -sf $(libdir)/$(SOLONG) $(sanedir)/$(SONOVER); \
	   ln -sf $(libdir)/$(SOLONG) $(sanedir)/$(SOSHORT); \
	   ln -sf $(libdir)/$(SOLONG) $(sanedir)/$(SOLONG); \
	   if ! grep ^hpaio /etc/sane.d/dll.conf >/dev/null 2>/dev/null ; then \
	      echo "Adding hpaio entry to /etc/sane.d/dll.conf." ; \
	      echo hpaio >>/etc/sane.d/dll.conf ; \
	   fi \
	fi

uninstall-hook:
#	cd cupsext; \
#	python setup.py uninstall

copy:
	cp -rL $(libsane_hpaio_la_SOURCES) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)

.PHONY: copy


