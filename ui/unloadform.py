#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Revision: 1.13 $ 
# $Date: 2004/12/06 17:48:53 $
# $Author: dwelch $
#
#
# (c) Copyright 2001-2004 Hewlett-Packard Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#


from base.g import *
from base import utils, device, msg
from prnt import cups
from pcard import photocard

import sys
import os, os.path
import socket

from qt import *

from unloadform_base import UnloadForm_base
from imagepropertiesdlg import ImagePropertiesDlg
from unloadprogressdlg import UnloadProgressDlg
from choosedevicedlg import ChooseDeviceDlg
from successform import SuccessForm
from failureform import FailureForm


progress_dlg = None

class IconViewItem( QIconViewItem ):
    def __init__( self, parent, path, pixmap, mime_type, mime_subtype, size, exif_info={} ):
        dirname, filename=os.path.split( path )
        QIconViewItem.__init__( self, parent, filename, pixmap )
        self.mime_type = mime_type
        self.mime_subtype = mime_subtype
        self.path = path
        self.dirname = dirname
        self.filename = filename
        self.exif_info = exif_info
        self.size = size
        self.thumbnail_set = False
        

class UnloadForm(UnloadForm_base):
    def __init__(self, bus='usb', device_uri=None, printer_name=None, parent = None,name = None,fl = 0):
        UnloadForm_base.__init__(self,parent,name,fl)
        
        if device_uri and printer_name:
            log.error( "You may not specify both a printer (-p) and a device (-d)." )
            device_uri, printer_name = None, None
            
        if not device_uri and not printer_name:
            timeout = 5
            ttl = 4
            format = 'default'
            hpssd_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            hpssd_sock.connect( ( prop.hpssd_host, prop.hpssd_port ) )
            
            fields, data = msg.xmitMessage( hpssd_sock, 
                                            "ProbeDevicesFiltered",
                                            None, 
                                            { 
                                                'bus' : bus,
                                                'timeout' : timeout,
                                                'ttl' : ttl,
                                                'format' : format,
                                                'filter' : 'pcard',
                                                    
                                            } 
                                          )
            
            hpssd_sock.close()  
            temp = data.splitlines()            
            probed_devices = []
            for t in temp:
                probed_devices.append( t.split(',')[0] )
            cups_printers = cups.getPrinters()
            log.debug( probed_devices )
            log.debug( cups_printers )
            max_deviceid_size, x, devices = 0, 0, {} 
            
            for d in probed_devices:
                printers = []
                for p in cups_printers:
                    if p.device_uri == d:
                        printers.append( p.name )
                devices[x] = ( d, printers )
                x += 1
                max_deviceid_size = max( len(d), max_deviceid_size )
            
            if x == 0:
                from nodevicesform import NoDevicesForm
                dlg = NoDevicesForm( self )
                dlg.exec_loop()
                sys.exit(0)
                
            elif x == 1:
                log.info( "Using device: %s" % devices[0][0] )
                device_uri = devices[0][0]
            else:                
                dlg = ChooseDeviceDlg( devices )
                dlg.exec_loop()
                device_uri = dlg.device_uri
        
        
        try:
            self.pc = photocard.PhotoCard( None, device_uri, printer_name )
        except Error, e:
            log.error( "An error occured: %s" % e[0] )
            FailureForm( "Unable to mount photocard. Could not connect to device.", self ).exec_loop()
            sys.exit(0)
        
        if self.pc.device.device_uri is None and printer_name:
            log.error( "Printer '%s' not found." % printer_name )
            FailureForm( 'Printer %s not found' % printer_name, self ).exec_loop()
            sys.exit(0)
            
        if self.pc.device.device_uri is None and device_uri:
            log.error( "Malformed/invalid device-uri: %s" % device_uri )
            FailureForm( "Malformed/invalid device-uri: %s" % device_uri, self ).exec_loop()
            sys.exit(0)
            
        
        try:
            self.pc.mount()
        except Error:
            log.error( "Unable to mount photo card on device. Check that device is powered on and photo card is correctly inserted." )
            FailureForm( "Unable to mount photo card on <b>%s</b>. Check that device is powered on and photo card is correctly inserted." % device_uri, self ).exec_loop()
            self.pc.umount()
            sys.exit(0)
            
        disk_info = self.pc.info()
        self.pc.write_protect = disk_info[8]
        
        if self.pc.write_protect:
            log.warning( "Photo card is write protected." )
            
        log.info( "Photocard on device %s mounted" % self.pc.device_uri )
        
        if not self.pc.write_protect:
            log.info( "DO NOT REMOVE PHOTO CARD UNTIL YOU EXIT THIS PROGRAM" )
        
        self.unload_dir = os.path.normpath( os.path.expanduser( '~' ) )
        os.chdir( self.unload_dir )
        self.UnloadDirectoryEdit.setText( self.unload_dir )
        
        self.unload_list = self.pc.get_unload_list()
        self.DeviceText.setText( self.pc.device.device_uri )
        
        self.image_icon_map = { 'tiff' : 'tif.png',
                                'bmp'  : 'bmp.png',
                                'jpeg' : 'jpg.png',
                                'gif'  : 'gif.png',
                                'unknown' : 'unknown.png',
                                }
        self.video_icon_map = { 'unknown' : 'movie.png',
                                'mpeg'    : 'mpg.png',
                                }
                                
        self.total_number = 0
        self.total_size = 0
        
        self.removal_option = 0
        
        self.UpdateStatusBar()
        #self.load_icon_view()
        QTimer.singleShot( 0, self.initialUpdate )
        
        if self.pc.write_protect:
            self.FileRemovalGroup.setEnabled( False )
            self.LeaveAllRadio.setEnabled( False )
            self.RemoveSelectedRadio.setEnabled( False )
            self.RemoveAllRadio.setEnabled( False )
        
    def initialUpdate( self ):
        self.load_icon_view( first_load=True )
    
    def load_icon_view( self, first_load ):
        if first_load:
            self.IconView.clear()
        
        num_items = len( self.unload_list )
        pb = QProgressBar( ) 
        pb.setTotalSteps( num_items )
        self.statusBar().addWidget( pb )
        pb.show()
        item_num = 0
        
        for f in self.unload_list:
            filename = f[0]
            size = f[1]
            
            pb.setProgress( item_num )
            item_num += 1
            qApp.processEvents(0)
            

            typ, subtyp = self.pc.classify_file( filename ).split('/')
            
            #if not first_load and typ == 'image' and subtyp in ( 'jpeg', 'tiff' ):
            if not first_load and typ == 'image' and subtyp == 'jpeg':
                exif_info = self.pc.get_exif_path( filename )
            
                if len(exif_info) > 0:
                    if 'JPEGThumbnail' in exif_info:
                        pixmap = QPixmap()
                        pixmap.loadFromData( exif_info['JPEGThumbnail'], "JPEG" )
                        del exif_info['JPEGThumbnail']
                        dname, fname=os.path.split( filename )
                        item = self.IconView.findItem( fname, 0 )
                        if item is not None:
                            item.setPixmap( pixmap )
                            item.thumbnail_set = True
                            #self.IconView.adjustItems()
                            #self.IconView.slotUpdate()
                            
                            
                        continue
                    
                    #elif 'TIFFThumbnail' in exif_info: 
                        # can't handle TIFF in Qt?
                    #    del exif_info['TIFFThumbnail']
                    #    if first_load:
                    #        IconViewItem( self.IconView, filename, 
                    #                      QPixmap( os.path.join( prop.image_dir, 'tif.png' ) ), 
                    #                      typ, subtyp, size, exif_info )
                    #    else:
                    #        pass
                            
                    #    continue
                        
                        
            elif first_load:
                if typ == 'image':
                    f = os.path.join( prop.image_dir, self.image_icon_map.get( subtyp, 'unknown.png' ) )
                elif typ == 'video':
                    f = os.path.join( prop.image_dir, self.video_icon_map.get( subtyp, 'movie.png' ) )
                elif typ == 'audio':
                    f = os.path.join( prop.image_dir, 'sound.png' )
                else:
                    f = os.path.join( prop.image_dir, 'unknown.png' )
                    
                IconViewItem( self.IconView, filename, QPixmap(f), typ, subtyp, size )
                #self.IconView.slotUpdate()

        
        pb.hide()
        self.statusBar().removeWidget( pb )
        self.IconView.adjustItems()
        

    def UpdateStatusBar( self ):
        if self.total_number == 0:
            self.statusBar().message( "No files selected" )
        elif self.total_number == 1:
            self.statusBar().message( "1 file selected, %s" % utils.format_bytes( self.total_size, True ) )
        else:
            self.statusBar().message( "%d files selected, %s" % ( self.total_number, utils.format_bytes(self.total_size, True ) ) )
    
    def SelectAllButton_clicked( self ):
        self.IconView.selectAll( 1 )

    def SelectNoneButton_clicked( self ):
        self.IconView.selectAll( 0 )   

    def IconView_doubleClicked( self, a0 ):
        #self.Display( a0 )
        pass
        
    def UnloadDirectoryBrowseButton_clicked( self ):
        self.unload_dir = str( QFileDialog.getExistingDirectory( self.unload_dir, self ) )
        self.UnloadDirectoryEdit.setText( self.unload_dir )
        os.chdir( self.unload_dir )
        print os.getcwd()
        
    def UnloadButton_clicked( self ):
        unload_list = []
        i = self.IconView.firstItem()
        total_size = 0
        while i is not None:
            
            if i.isSelected():
                unload_list.append( ( i.path, i.size, i.mime_type, i.mime_subtype ) )
                total_size += i.size
            i = i.nextItem()

        global progress_dlg
        progress_dlg = QProgressDialog( "Unloading Files...", "Cancel", total_size, self, 'progress', True )
        #progress_dlg = UnloadProgressDlg( self, 'UnloadProgress', True )
        #progress_dlg.ProgressBar.setTotalSteps( total_size )
        #progress_dlg.setProgress(0)
        progress_dlg.setMinimumDuration( 0 )
        progress_dlg.show()
        #qApp.processEvents(0)
        
        if self.removal_option == 0:
            self.pc.unload( unload_list, self.UpdateUnloadProgressDlg, None, True )
        elif self.removal_option == 1: # remove selected
            self.pc.unload( unload_list, self.UpdateUnloadProgressDlg, None, False )
        else: # remove all
            self.pc.unload( unload_list, self.UpdateUnloadProgressDlg, None, False )
            # TODO: Remove remainder of files
        
        progress_dlg.close()
        
        SuccessForm( self ).exec_loop()
        
        #self.close()

    def UpdateUnloadProgressDlg( self, src, trg, size ):
        global progress_dlg
        progress_dlg.setProgress( progress_dlg.progress() + size )
        progress_dlg.setLabelText( src )
        #progress_dlg.FilenameText.setText( '<b>' + src + '</b>' )
        #progress_dlg.ProgressBar.setProgress( progress_dlg.ProgressBar.progress() + size )
        qApp.processEvents()
        
        return progress_dlg.wasCanceled()
    
    def IconView_rightButtonClicked( self, item, pos ):
        popup = QPopupMenu( self )
        #popup.insertItem( "Display...", self.PopupDisplay ) 
        popup.insertItem( "Properties", self.PopupProperties )
        if item.mime_type == 'image' and item.mime_subtype == 'jpeg' and not item.thumbnail_set:
            popup.insertItem( "Show Thumbnail", self.showThumbNail )
        popup.popup( pos )
        
        
    def PopupDisplay( self ):
        self.Display( self.IconView.currentItem() )
        
    def PopupProperties( self ):
        self.Properties( self.IconView.currentItem() )
        
    def showThumbNail( self ):
        item = self.IconView.currentItem()
        exif_info = self.pc.get_exif_path( os.path.join( item.dirname, item.filename ) )
            
        if len(exif_info) > 0:
            if 'JPEGThumbnail' in exif_info:
                pixmap = QPixmap()
                pixmap.loadFromData( exif_info['JPEGThumbnail'], "JPEG" )
                del exif_info['JPEGThumbnail']
                item.setPixmap( pixmap )
        
                self.IconView.adjustItems()
        
        item.thumbnail_set = True    
        
    def Display( self, item ):
        pass
        # cp over file (does this even make sense to do this at this point?)
        # display with imagemagick?
        
    def Properties( self, item ):
        if not item.exif_info:
            item.exif_info = self.pc.get_exif_path( os.path.join( item.dirname, item.filename ) )
    
        ImagePropertiesDlg( item.filename, item.dirname, 
                            '/'.join( [ item.mime_type, item.mime_subtype ] ),
                            utils.format_bytes(item.size, True), 
                            item.exif_info, self ).exec_loop()
        
        
        
    def IconView_selectionChanged( self ):
        self.total_number = 0
        self.total_size = 0
        i = self.IconView.firstItem()
        
        while i is not None:
            
            if i.isSelected():
                self.total_number += 1
                self.total_size += i.size
            
            i = i.nextItem()
        
        self.UpdateStatusBar()
    

    def IconView_clicked(self,a0,a1):
        pass

    def IconView_clicked(self,a0):
        pass

    def IconView_currentChanged(self,a0):
        pass
        
    def FileRemovalGroup_clicked( self, a0 ):
        self.removal_option = a0
        
    def ShowThumbnailsButton_clicked(self):
        self.ShowThumbnailsButton.setEnabled( False )
        self.load_icon_view( first_load=False )

        
        
        
        
