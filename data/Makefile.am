#
#  Makefile.am - data automake input file
# 
#  (c) 2004 Copyright Hewlett-Packard Development Company, LP
#

xmldir = $(datadir)/hplip/data/xml
imagesdir = $(datadir)/hplip/data/images
pcldir = $(datadir)/hplip/data/pcl
ldldir = $(datadir)/hplip/data/ldl
psdir = $(datadir)/hplip/data/ps
icondir = $(datadir)/hplip/data

ps_DATA = \
    ps/testpage.ps.gz

xml_DATA = \
    xml/models.xml

noinst_DATA = \
    images/images.tgz

pcl_DATA = \
    pcl/align1_8xx.pcl.gz \
    pcl/align1_9xx.pcl.gz \
    pcl/align2_8xx.pcl.gz \
    pcl/align3_8xx.pcl.gz \
    pcl/align4_8xx.pcl.gz \
    pcl/align5_8xx.pcl.gz \
    pcl/align2_9xx.pcl.gz \
    pcl/align3_9xx.pcl.gz \
    pcl/align4_450.pcl.gz \
    pcl/align6_450.pcl.gz \
    pcl/colorcal1_450.pcl.gz \
    pcl/colorcal2_450.pcl.gz \
    pcl/crbcal.pcl.gz \
    pcl/crcaldone.pcl.gz \
    pcl/crcbcal.pcl.gz \
    pcl/crccal.pcl.gz \
    pcl/crcpcal.pcl.gz \
    pcl/crpcal.pcl.gz 

ldl_DATA = \
    ldl/cb2pcal.ldl.gz \
    ldl/cb2pcal_done.ldl.gz \
    ldl/cbbcal.ldl.gz \
    ldl/cbccal.ldl.gz \
    ldl/cbccal_done.ldl.gz \
    ldl/cbcpcal.ldl.gz \
    ldl/cbpcal.ldl.gz 

install-data-hook:
	$(mkinstalldirs) $(DESTDIR)$(imagesdir)
	cd $(DESTDIR)$(imagesdir); tar xzvf $(CURDIR)/images/images.tgz
	if [ "$(ICON_FILE)" = "hplip.desktop" ]; then \
	   echo -e "[Desktop Entry]" > $(srcdir)/$(ICON_FILE); \
	   echo -e "Version=0.6" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Type=Application" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Name=HP Device Manager" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "GenericName=HP Device Manager" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Comment=View device status, ink levels and perform maintenance." >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Exec=$(libexecdir)/hplip/toolbox" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Icon=$(imagesdir)/HPmenu.png" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Terminal=false" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "Categories=Application;Utility;" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "X-KDE-StartupNotify=false" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "StartupNotify=false" >> $(srcdir)/$(ICON_FILE); \
	fi
	if [ "$(ICON_FILE)" = "hplip" ]; then \
	   echo -e "?package(xbase):command=\"$(libexecdir)/hplip/toolbox\" icon=\"$(imagesdir)/HPmenu.png\" \\" > $(srcdir)/$(ICON_FILE); \
	   echo -e "                needs=\"X11\" section=\"Application/Utility\" title=\"HPLIP\" \\" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "                longtitle=\"HPLIP Device Manager\" \\" >> $(srcdir)/$(ICON_FILE); \
	   echo -e "                mimetypes=\"\" accept_url=\"false\" multiple_files=\"true\"" >> $(srcdir)/$(ICON_FILE); \
	fi
	$(INSTALL_DATA)  $(srcdir)/$(ICON_FILE) $(DESTDIR)$(icondir); \
	rm -f $(srcdir)/$(ICON_FILE)
#
#       Do full install if not rpm_install.
	if [ "$(rpm_install)" = "no" ]; then \
	   if [ -d $(ICON_PATH) ]; then \
	      ln -sf $(DESTDIR)$(icondir)/$(ICON_FILE) $(ICON_PATH)/$(ICON_FILE); \
	   fi \
	fi

copy:
	mkdir -p $(COPY_DEST)/xml
	cp -r $(xml_DATA) $(COPY_DEST)/xml
	mkdir -p $(COPY_DEST)/images
	cp -r $(noinst_DATA) $(COPY_DEST)/images
	mkdir -p $(COPY_DEST)/pcl
	cp -r $(pcl_DATA) $(COPY_DEST)/pcl
	mkdir -p $(COPY_DEST)/ldl
	cp -r $(ldl_DATA) $(COPY_DEST)/ldl
	mkdir -p $(COPY_DEST)/ps
	cp -r $(ps_DATA) $(COPY_DEST)/ps
	cp -rL $(DIST_SOURCES) $(EXTRA_DIST) $(DIST_COMMON) $(COPY_DEST)

.PHONY: copy
