hpijsdocdir = $(docdir)/$(PACKAGE)
ppddir = $(datadir)/ppd/HP

#APDKLABEL=JetReady_PreMerge_11-08-04 
APDKLABEL=HPLIP-0_9_2_3
APDKCOMMON=slimhost/source/common
APDKOPEN=slimhost/source/open
APDKDEBUG=slimhost/source/debug

FOOMATICLABEL=foomatic-3_0-branch

if FOOMATIC_INSTALL
foomatichook = install-foomatic
unfoomatichook = uninstall-foomatic
rip = foomatic-rip
if CUPS_INSTALL
cupshook = install-cups
uncupshook = uninstall-cups
else
cupshook =
uncupshook =
endif
else
foomatichook =
unfoomatichook = 
rip =
cupshook =
uncupshook =
endif

bin_PROGRAMS = hpijs
hpijs_SOURCES = hpijs.cpp ijs_server.c ijs.c models.cpp breaks_open.cpp \
	dj9xxvip.cpp dj9xx.cpp capture.cpp colormatch.cpp colormatcher_open.cpp \
	compression.cpp context.cpp create_so.cpp creator.cpp \
	dj600.cpp dj630.cpp dj660.cpp dj690.cpp dj6xx.cpp dj8xx.cpp dj600_maps.cpp \
	dj660_maps.cpp dj690_maps.cpp dj895_maps.cpp dj895_maps2.cpp dj970_maps.cpp \
	dj970_maps2.cpp dj970_maps3.cpp filterhpa.cpp apollo21xx.cpp apollo2560.cpp apollo2xxx.cpp \
	dj8x5.cpp psp100.cpp phobos_cmaps.cpp dj350.cpp halftoner.cpp halftoner_open.cpp \
	globals.cpp header.cpp htmtxhi.cpp pmselect.cpp \
	job.cpp printer.cpp registry.cpp scaler.cpp \
	scaler_open.cpp script.cpp systemservices.cpp services.cpp \
	translator.cpp version.cpp versioncode.cpp \
	djgenericvip.cpp dj540.cpp dj850.cpp dj850_maps.cpp dj890.cpp \
	apollo21xx.h apollo2560.h apollo2xxx.h colormatch.h colormatcher_open.h \
	compression.h config.h context.h dj350.h dj400.h dj540.h \
	dj600.h dj630.h dj660.h dj690.h dj6xx.h dj8x5.h dj8xx.h dj850.h dj890.h dj9xx.h dj9xxvip.h \
	ernieplatform.h filterhpa.h global_types.h halftoner.h font.h debug.h \
	halftoner_open.h header.h hpijs.h hpprint_c_api.h \
	hpprintapi.h hptypes.h htfed.h ijs.h ijs_server.h internal.h \
	interp.h interp_data_50.h io_defs.h job.h models.h modes.h pmselect.h \
	printer.h psp100.h resources.h scaler_open.h scaler_prop.h script.h services.h \
	systemservices.h unistd_.h ijs_client.h djgenericvip.h ljmono.h ljmono.cpp \
	dj3320.cpp dj3320.h dj3320_cmap.cpp dj3600.cpp dj3600.h dj3600_cmap.cpp ldlencap.h \
	ljcolor.cpp ljcolor.h pscript.h hpiom.c hpiom.h \
	printerproxy.cpp printerfactory.cpp printerproxy.h printerfactory.h \
	ljjetready.cpp ljjetready.h jdatadbf.c jccolor.c README_LIBJPG ljfastraster.cpp ljfastraster.h \
	jinclude.h jpegint.h

hpijsdoc_DATA	= hpijs_readme.html gs_hpijs.png COPYING
bin_SCRIPTS = $(rip)

EXTRA_DIST = $(doc_DATA) ppd foomatic-rip hpijs-ppd gdevijs-krgb-1.1.patch

install-data-hook: $(foomatichook) $(cupshook)
uninstall-hook: $(unfoomatichook) $(uncupshook)

install-foomatic:
	$(mkinstalldirs) $(DESTDIR)$(ppddir)
	rm -f $(DESTDIR)$(ppddir)/HP*.ppd*
	rm -f $(DESTDIR)$(ppddir)/hp*.ppd*
	$(INSTALL_DATA) ppd/* $(DESTDIR)$(ppddir)
	gzip -f $(DESTDIR)$(ppddir)/*

uninstall-foomatic:
	rm -f $(DESTDIR)$(ppddir)/HP*.ppd*
	rm -f $(DESTDIR)$(ppddir)/hp*.ppd*

install-cups:
	rm -f $(DESTDIR)$(CUPS_PPD_PATH)/HP*.ppd* $(DESTDIR)$(CUPS_PPD_PATH)/foomatic/HP/HP*.ppd*
	rm -f $(DESTDIR)$(CUPS_PPD_PATH)/hp*.ppd* $(DESTDIR)$(CUPS_PPD_PATH)/foomatic/HP/hp*.ppd*
	rm -f $(DESTDIR)$(CUPS_PPD_PATH)/foomatic-ppds
	$(mkinstalldirs) $(DESTDIR)$(CUPS_PPD_PATH)
	ln -s $(datadir)/ppd $(DESTDIR)$(CUPS_PPD_PATH)/foomatic-ppds
	rm -f $(DESTDIR)$(CUPS_FILTER_PATH)/foomatic-rip
	$(mkinstalldirs) $(DESTDIR)$(CUPS_FILTER_PATH)
	ln -s $(bindir)/foomatic-rip $(DESTDIR)$(CUPS_FILTER_PATH)/foomatic-rip

uninstall-cups:
	rm -f $(DESTDIR)$(CUPS_PPD_PATH)/foomatic-ppds
	rm -f $(DESTDIR)$(CUPS_FILTER_PATH)/foomatic-rip

get-apdk: 
	cvs -z3 -d:pserver:$(USER)@elkhorn1.boi.hp.com:/shared/data/ccvs/repository co -r $(APDKLABEL) $(APDKCOMMON)
	cvs -z3 -d:pserver:$(USER)@elkhorn1.boi.hp.com:/shared/data/ccvs/repository co -r $(APDKLABEL) $(APDKOPEN)
	cvs -z3 -d:pserver:$(USER)@elkhorn1.boi.hp.com:/shared/data/ccvs/repository co -r $(APDKLABEL) $(APDKDEBUG)
	cp -f $(APDKCOMMON)/*.cpp $(APDKCOMMON)/*.h $(APDKCOMMON)/*.c $(APDKCOMMON)/README_LIBJPG ./
	cp -f $(APDKOPEN)/*.cpp $(APDKOPEN)/*.h ./
	cp -f $(APDKDEBUG)/*.cpp $(APDKDEBUG)/*.h ./
	rm -rf slimhost

get-apdk-tip: 
	cvs -z3 -d:pserver:$(USER)@elkhorn1.boi.hp.com:/shared/data/ccvs/repository co $(APDKCOMMON)
	cvs -z3 -d:pserver:$(USER)@elkhorn1.boi.hp.com:/shared/data/ccvs/repository co $(APDKOPEN)
	cvs -z3 -d:pserver:$(USER)@elkhorn1.boi.hp.com:/shared/data/ccvs/repository co $(APDKDEBUG)
	cp -f $(APDKCOMMON)/*.cpp $(APDKCOMMON)/*.h $(APDKCOMMON)/*.c $(APDKCOMMON)/README_LIBJPG ./
	cp -f $(APDKOPEN)/*.cpp $(APDKOPEN)/*.h ./
	cp -f $(APDKDEBUG)/*.cpp $(APDKDEBUG)/*.h ./
	rm -rf slimhost

get-ppd: 
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co -r $(FOOMATICLABEL) foomatic-db-engine
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co -r $(FOOMATICLABEL) foomatic-filters
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co -r $(FOOMATICLABEL) foomatic-db
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co foomatic-db-hpijs
	cd foomatic-db-hpijs; \
	./make_configure; \
	./configure; \
	make inplace
	cd foomatic-filters; \
	./make_configure; \
	./configure; \
	make inplace
	cd foomatic-db-engine; \
	./make_configure; \
	./configure; \
	make inplace
	./hpijs-ppd
	cp foomatic-filters/foomatic-rip ./
	rm -rf foomatic-db-engine
	rm -rf foomatic-filters
	rm -rf foomatic-db
	rm -rf foomatic-db-hpijs
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/all_in_one/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/business_inkjet/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/color_laser/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/designjet/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/mono_laser/
	cp www.linuxprinting.org/download/PPD/HP/all_in_one/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/business_inkjet/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/color_laser/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/designjet/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/mono_laser/* ppd/
	rm -fr www.linuxprinting.org

get-ppd-tip:
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co foomatic-db-engine
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co foomatic-filters
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co foomatic-db
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co foomatic-db-hpijs
	cd foomatic-db-hpijs; \
	./make_configure; \
	./configure; \
	make inplace
	cd foomatic-filters; \
	./make_configure; \
	./configure; \
	make inplace
	cd foomatic-db-engine; \
	./make_configure; \
	./configure; \
	make inplace
	./hpijs-ppd
	cp foomatic-filters/foomatic-rip ./
	rm -rf foomatic-db-engine
	rm -rf foomatic-filters
	rm -rf foomatic-db
	rm -rf foomatic-db-hpijs
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/all_in_one/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/business_inkjet/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/color_laser/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/designjet/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/mono_laser/
	cp www.linuxprinting.org/download/PPD/HP/all_in_one/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/business_inkjet/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/color_laser/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/designjet/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/mono_laser/* ppd/
	rm -fr www.linuxprinting.org

get-ppd-user:
	CVS_RSH=ssh cvs -z3 -d:ext:$(USER)@cvs.linuxprinting.org:/var/lib/cvs co foomatic-db-engine
	CVS_RSH=ssh cvs -z3 -d:ext:$(USER)@cvs.linuxprinting.org:/var/lib/cvs co foomatic-filters
	CVS_RSH=ssh cvs -z3 -d:ext:$(USER)@cvs.linuxprinting.org:/var/lib/cvs co foomatic-db
	CVS_RSH=ssh cvs -z3 -d:ext:$(USER)@cvs.linuxprinting.org:/var/lib/cvs co foomatic-db-hpijs
	cd foomatic-db-hpijs; \
	./make_configure; \
	./configure; \
	make inplace
	cd foomatic-filters; \
	./make_configure; \
	./configure; \
	make inplace
	cd foomatic-db-engine; \
	./make_configure; \
	./configure; \
	make inplace
	./hpijs-ppd
	cp foomatic-filters/foomatic-rip ./
	rm -rf foomatic-db-engine
	rm -rf foomatic-filters
	rm -rf foomatic-db
	rm -rf foomatic-db-hpijs
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/all_in_one/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/business_inkjet/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/color_laser/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/designjet/
	wget -nv -r -l1 -np -erobots=off -A.ppd http://www.linuxprinting.org/download/PPD/HP/mono_laser/
	cp www.linuxprinting.org/download/PPD/HP/all_in_one/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/business_inkjet/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/color_laser/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/designjet/* ppd/
	cp www.linuxprinting.org/download/PPD/HP/mono_laser/* ppd/
	rm -fr www.linuxprinting.org

get-foomatic:
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co -r $(FOOMATICLABEL) foomatic-db-engine
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co -r $(FOOMATICLABEL) foomatic-filters
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co foomatic-db
	cvs -z3 -d:pserver:anonymous@cvs.linuxprinting.org:/usr/local/cvs co foomatic-db-hpijs

test-ppd:
	cd foomatic-db-hpijs; \
	./make_configure; \
	./configure; \
	make inplace
	cd foomatic-filters; \
	./make_configure; \
	./configure; \
	make inplace
	cd foomatic-db-engine; \
	./make_configure; \
	./configure; \
	make inplace
	./hpijs-ppd
	cp foomatic-filters/foomatic-rip ./

copy:
#	cp -r $(DIST_SOURCES) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)
	cp -rL $(hpijs_SOURCES) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)

.PHONY: copy

