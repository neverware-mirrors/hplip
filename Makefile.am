#
#  Makefile.am - toplevel hplip automake input file
# 
#  (c) 2004-2005 Copyright Hewlett-Packard Development Company, LP
#

# Generic rules
%.py: %.ui
	$(PYUIC) -x -o $@ $<

SUBDIRS = prnt/hpijs

hplipdir = $(datadir)/hplip
hpliplibexecdir = $(libexecdir)/hplip

hplipdocdir = $(datadir)/doc/$(PACKAGE)
dist_hplipdoc_DATA =  hplip_readme.html hplip_overview.png COPYING

dist_hplip_DATA = hplip.conf
dist_hpliplibexec_SCRIPTS = hpssd.py __init__.py hplip.sh

cmddir = $(hpliplibexecdir)
dist_cmd_SCRIPTS = align.py info.py print.py toolbox.py clean.py colorcal.py photo.py unload.py probe.py rpu.py testpage.py makeuri.py check.py

# hp backend.
cupsdir = $(CUPS_BACKEND_PATH)
cups_PROGRAMS = hp
hp_SOURCES = backend/hp/hp.c 

# hpiod
sbin_PROGRAMS = hpiod
hpiod_SOURCES = io/hpiod/hpiod.cpp io/hpiod/channel.cpp io/hpiod/device.cpp io/hpiod/mlc.cpp io/hpiod/system.cpp io/hpiod/jddevice.cpp io/hpiod/jetdirect.cpp\
    io/hpiod/channel.h io/hpiod/device.h io/hpiod/hpiod.h io/hpiod/mlc.h io/hpiod/system.h

# base
basedir = $(hpliplibexecdir)/base
dist_base_SCRIPTS = base/maint.py base/codes.py base/g.py base/mfpdtf2.py base/pml.py base/status.py base/async.py \
    base/database.py base/__init__.py base/mfpdtf.py base/service.py base/utils.py base/async_qt.py \
    base/device.py base/logger.py base/msg.py base/slp.py base/exif.py base/strings.py

# ptest
noinst_PROGRAMS = ptest
ptest_SOURCES = pcard/ptest.c pcard/ptest.h pcard/fat.c pcard/fat.h 

# data
xmldir = $(hplipdir)/data/xml
imagesdir = $(hplipdir)/data/images
pcldir = $(hplipdir)/data/pcl
ldldir = $(hplipdir)/data/ldl
psdir = $(hplipdir)/data/ps
icondir = $(hplipdir)/data
dist_ps_DATA = data/ps/testpage.ps.gz data/ps/clean_page.pdf.gz
dist_xml_DATA = data/xml/models.xml
images_DATA = data/images/images.tgz
dist_pcl_DATA = data/pcl/align1_8xx.pcl.gz data/pcl/align1_9xx.pcl.gz data/pcl/align2_8xx.pcl.gz data/pcl/align3_8xx.pcl.gz data/pcl/align4_8xx.pcl.gz \
    data/pcl/align5_8xx.pcl.gz data/pcl/align2_9xx.pcl.gz data/pcl/align3_9xx.pcl.gz data/pcl/align4_450.pcl.gz data/pcl/align6_450.pcl.gz \
    data/pcl/colorcal1_450.pcl.gz data/pcl/colorcal2_450.pcl.gz data/pcl/crbcal.pcl.gz data/pcl/crcaldone.pcl.gz data/pcl/crcbcal.pcl.gz data/pcl/crccal.pcl.gz \
    data/pcl/crcpcal.pcl.gz data/pcl/crpcal.pcl.gz 
dist_ldl_DATA = data/ldl/cb2pcal.ldl.gz data/ldl/cb2pcal_done.ldl.gz data/ldl/cbbcal.ldl.gz data/ldl/cbccal.ldl.gz data/ldl/cbccal_done.ldl.gz data/ldl/cbcpcal.ldl.gz \
    data/ldl/cbpcal.ldl.gz

# pcard 
pcarddir = $(hpliplibexecdir)/pcard
pcardextdir = $(pcarddir)/pcardext
dist_pcard_SCRIPTS = pcard/__init__.py pcard/photocard.py
dist_noinst_SCRIPTS = pcard/pcardext/setup.py pcard/pcardext/pcardext.c \
    prnt/cupsext/setup.py prnt/cupsext/cupsext.c 
noinst_DATA = build-pcardext build-cupsext

# prnt
prntdir = $(hpliplibexecdir)/prnt
cupsextdir = $(prntdir)/cupsext
dist_prnt_SCRIPTS = prnt/cups.py prnt/__init__.py prnt/ldl.py prnt/pcl.py prnt/colorcal.py 
#noinst_SCRIPTS = prnt/cupsext/setup.py prnt/cupsext/cupsext.c build-cupsext
#noinst_DATA = build-cupsext

# scan
scandir = $(hpliplibexecdir)/scan
dist_scan_SCRIPTS = scan/__init__.py scan/pml_scanner.py scan/sane.py scan/scanner.py scan/scl.py scan/scl_scanner.py

# ip library
noinst_LTLIBRARIES = libhpip.la
libhpip_la_SOURCES = ip/xconvolve.c ip/xfax.c ip/xgrayout.c ip/xjpg_dct.c ip/xjpg_fix.c ip/xpad.c ip/xrotate.c ip/xskel.c ip/xtiff.c \
    ip/ipmain.c ip/xchgbpp.c ip/xcrop.c ip/xgamma.c ip/xjpg_dec.c ip/xjpg_huf.c ip/xpcx.c ip/xsaturation.c ip/xtable.c ip/xtonemap.c \
    ip/xbi2gray.c ip/xcolrspc.c ip/xfakemono.c ip/xgray2bi.c ip/xinvert.c ip/xjpg_enc.c ip/xmatrix.c ip/xpnm.c ip/xscale.c ip/xthumb.c ip/xyxtract.c \
    ip/hpip.h ip/ipdefs.h ip/xform.h ip/xjpg_dct.h ip/xjpg_huf.h ip/xjpg_mrk.h

# sane backend
BASENAME=sane-hpaio
MAJORVER=1
MINORVER=0
AGEVER=0
SONOVER=lib$(BASENAME).so
SOSHORT=$(SONOVER).$(MAJORVER)
SOLONG=$(SOSHORT).$(MINORVER).$(AGEVER)
sanedir = $(libdir)/sane
sane_LTLIBRARIES = libsane-hpaio.la
libsane_hpaio_la_SOURCES = scan/sane/hpaio.c scan/sane/mfpdtf.c scan/sane/pml.c scan/sane/scl.c scan/sane/io.c scan/sane/hpaio.h scan/sane/pml.h scan/sane/saneopts.h scan/sane/io.h \
      scan/sane/mfpdtf.h scan/sane/sane.h scan/sane/scl.h scan/sane/tables.h
libsane_hpaio_la_LDFLAGS = -version-info $(MAJORVER):$(MINORVER):$(AGEVER) 
# The following is a interlibrary dependency that must be compiled first.
libsane_hpaio_la_LIBADD = libhpip.la

# ui
uidir = $(hpliplibexecdir)/ui
dist_ui_SCRIPTS = ui/alignform.py \
    ui/colorcalform_base.py ui/colorcalform.py ui/coloradjform_base.py ui/coloradjform.py ui/devmgr4_base.py ui/devmgr4.py \
    ui/__init__.py ui/loadpaperform_base.py ui/loadpaperform.py \
    ui/paperedgealignform_base.py ui/paperedgealignform.py \
    ui/settingsdialog_base.py ui/settingsdialog.py ui/aligntype6form1.py ui/aligntype6form1_base.py ui/aligntype6form2_base.py \
    ui/aligntype6form2.py ui/nodevicesform_base.py ui/nodevicesform.py ui/unloadform.py ui/unloadform_base.py \
    ui/imagepropertiesdlg_base.py ui/imagepropertiesdlg.py ui/choosedevicedlg.py \
    ui/aboutdlg.py ui/aboutdlg_base.py ui/waitform.py ui/waitform_base.py ui/cleaningform_base.py ui/cleaningform.py \
    ui/cleaningform2_base.py ui/cleaningform2.py ui/colorcalform2_base.py ui/colorcalform2.py

dist_noinst_DATA = ui/unloadform_base.ui ui/colorcalform2_base.ui ui/settingsdialog_base.ui ui/aligntype6form1_base.ui \
    ui/aboutdlg_base.ui ui/imagepropertiesdlg_base.ui ui/paperedgealignform_base.ui ui/aligntype6form2_base.ui \
    ui/nodevicesform_base.ui ui/cleaningform_base.ui ui/colorcalform_base.ui ui/devmgr4_base.ui ui/loadpaperform_base.ui \
    ui/cleaningform2_base.ui ui/waitform_base.ui ui/coloradjform_base.ui

build-pcardext: 
	cd pcard/pcardext; \
	python setup.py build

build-cupsext: 
	cd prnt/cupsext; \
	python setup.py build

maintainer-clean-local:
	(cd ui && for i in *.ui ; do rm -f $${i%.ui}.py ; done)

install-exec-hook:
#
#       Do full install if not rpm_install.
	if [ "$(rpm_install)" = "no" ]; then \
	   ln -sf ../$(SOLONG) $(DESTDIR)$(sanedir)/$(SONOVER); \
	   ln -sf ../$(SOLONG) $(DESTDIR)$(sanedir)/$(SOSHORT); \
	   ln -sf ../$(SOLONG) $(DESTDIR)$(sanedir)/$(SOLONG); \
	   if [ -f $(DESTDIR)/etc/sane.d/dll.conf ]; then \
	      if ! grep ^hpaio $(DESTDIR)/etc/sane.d/dll.conf >/dev/null 2>/dev/null ; then \
	         echo "Adding hpaio entry to /etc/sane.d/dll.conf." ; \
	         echo hpaio >>$(DESTDIR)/etc/sane.d/dll.conf ; \
	      fi \
	   fi \
	fi

install-data-hook:
	$(mkinstalldirs) $(DESTDIR)$(imagesdir)
	tar xzvf "$(CURDIR)/data/images/images.tgz" -C "$(DESTDIR)$(imagesdir)"
	if [ "$(ICON_FILE)" = "hplip.desktop" ]; then \
	   echo -e "[Desktop Entry]" > $(srcdir)/$(ICON_FILE); \
	   echo -e "Version=0.6" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Type=Application" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Name=HP Device Manager" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "GenericName=HP Device Manager" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Comment=View device status, ink levels and perform maintenance." >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Exec=$(hpliplibexecdir)/toolbox" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Icon=$(imagesdir)/HPmenu.png" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Terminal=false" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Categories=Application;Utility;" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "X-KDE-StartupNotify=false" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "StartupNotify=false" >> $(srcdir)/$(ICON_FILE); \
	fi
	if [ "$(ICON_FILE)" = "hplip" ]; then \
	   echo -e "?package(xbase):command=\"$(hpliplibexecdir)/toolbox\" icon=\"$(imagesdir)/HPmenu.png\" \\" > $(srcdir)/$(ICON_FILE); \
	   echo -e "                needs=\"X11\" section=\"Application/Utility\" title=\"HPLIP\" \\" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "                longtitle=\"HPLIP Device Manager\" \\" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "                mimetypes=\"\" accept_url=\"false\" multiple_files=\"true\"" >> $(srcdir)/$(ICON_FILE); \
	fi
	$(INSTALL_DATA)  $(srcdir)/$(ICON_FILE) $(DESTDIR)$(icondir); \
	rm -f $(srcdir)/$(ICON_FILE)
#
#       Do full install if not rpm_install.
	if [ "$(rpm_install)" = "no" ]; then \
	   if [ -d $(DESTDIR)$(ICON_PATH) ]; then \
	      ln -sf $(icondir)/$(ICON_FILE) $(DESTDIR)$(ICON_PATH)/$(ICON_FILE); \
	   fi \
	fi
#
#       Install pcard extension.
	cd pcard/pcardext; \
	if [ "$(DESTDIR)" = "" ]; then \
	   python setup.py install --prefix=$(prefix); \
	else \
	   python setup.py install --root=$(DESTDIR) --prefix=$(prefix); \
	fi
#
#       Install cups extension.
	cd prnt/cupsext; \
	if [ "$(DESTDIR)" = "" ]; then \
	   python setup.py install --prefix=$(prefix); \
	else \
	   python setup.py install --root=$(DESTDIR) --prefix=$(prefix); \
	fi
##
#       Remove .py extensions in destdir and if not rpm_install create hp-xxx commands in bindir.
	for i in $(dist_cmd_SCRIPTS); do \
	    newname=$${i%.*}; \
	    mv $(DESTDIR)$(hpliplibexecdir)/$$i $(DESTDIR)$(hpliplibexecdir)/$$newname; \
	    if [ "$(rpm_install)" = "no" ]; then \
	      ln -sf ../share/$(PACKAGE)/$$newname $(DESTDIR)$(bindir)/hp-$$newname; \
	    fi \
	done
#
#       Edit hpiod.conf in destdir.
	echo -e "\n[$(PACKAGE)]\nversion=$(VERSION)\njdprobe=0\n" >> $(DESTDIR)$(hplipdir)/$(PACKAGE).conf
	echo -e "[dirs]\nhome=$(hpliplibexecdir)\n" >> $(DESTDIR)$(hplipdir)/$(PACKAGE).conf
#
#       Edit hpiod.sh in destdir.
	sed 's:HPIODDIR=:HPIODDIR=$(sbindir):' < $(DESTDIR)$(hplipdir)/$(PACKAGE).sh > $(DESTDIR)$(hplipdir)/$(PACKAGE).tmp; \
	sed 's:HPSSDDIR=:HPSSDDIR=$(sbindir):' < $(DESTDIR)$(hplipdir)/$(PACKAGE).tmp > $(DESTDIR)$(hplipdir)/$(PACKAGE); \
	rm -f $(DESTDIR)$(hplipdir)/$(PACKAGE).tmp
#
#       Do full install if not rpm_install. Also only run chkconfig/install_initd if DESTDIR="". 
	$(mkinstalldirs) $(DESTDIR)/etc/hp;
	$(INSTALL_DATA) $(DESTDIR)$(hplipdir)/$(PACKAGE).conf $(DESTDIR)/etc/hp;
	if [ "$(rpm_install)" = "no" ]; then \
	   if [ -d $(DESTDIR)/etc/init.d ]; then \
	      $(INSTALL_SCRIPT) $(DESTDIR)$(hplipdir)/$(PACKAGE) $(DESTDIR)/etc/init.d; \
	      if [ "$(DESTDIR)" = "" ]; then \
	         if [ -x $(LSB_INSTALL_PATH)/install_initd ]; then \
	            $(LSB_INSTALL_PATH)/install_initd $(PACKAGE); \
	         else \
	            $(CHKCONFIG_PATH)/chkconfig $(PACKAGE) reset; \
	         fi \
	      fi \
	   fi \
	fi

#
# Add prerequisites for testing (or building?) "make install DESTDIR=/build".
test-destdir:
	$(mkinstalldirs) $(DESTDIR)/etc/init.d
	$(mkinstalldirs) $(DESTDIR)/etc/sane.d
	touch $(DESTDIR)/etc/sane.d/dll.conf
	$(mkinstalldirs) $(DESTDIR)/usr/lib/sane
	$(mkinstalldirs) $(DESTDIR)/usr/share/applications

.PHONY: build-pcardext build-cupsext

