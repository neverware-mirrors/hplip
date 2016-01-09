#!/usr/bin/env python
#
# $Revision: 1.66 $ 
# $Date: 2005/04/14 19:36:44 $
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
# Authors: Don Welch, Pete Parks
#

# Std Lib
import sys
import socket
import time
import os

# Local
from base.g import *
from base import device, service, status, msg, maint, utils
from prnt import cups
from base.codes import *

# Qt
from qt import *

# Main form
from devmgr4_base import DevMgr4_base

# Alignment forms
from alignform import AlignForm
from aligntype6form1 import AlignType6Form1
from aligntype6form2 import AlignType6Form2
from paperedgealignform import PaperEdgeAlignForm
from colorcalform import ColorCalForm # Type 1 color cal
from coloradjform import ColorAdjForm  # Type 5 and 6 color adj
from colorcalform2 import ColorCalForm2 # Type 2 color cal

# Misc forms
from loadpaperform import LoadPaperForm
from settingsdialog import SettingsDialog
from nodevicesform import NoDevicesForm
from aboutdlg import AboutDlg
from cleaningform import CleaningForm
from cleaningform2 import CleaningForm2
from waitform import WaitForm

MIN_AUTO_REFRESH_RATE = 5
MAX_AUTO_REFRESH_RATE = 360
DEF_AUTO_REFRESH_RATE = 30


class DummyDevice:
    def __init__( self, device_uri ):
        self.device_uri = device_uri

        try:
            self.back_end, self.is_hp, self.bus, self.model, self.serial, self.dev_file, self.host, self.port = \
                device.parseDeviceURI( self.device_uri )

        except Error:
            log.warn( "Malformed/non-HP URI: %s" % self.device_uri )
            self.device_state = DEVICE_STATE_NOT_FOUND
            raise Error( ERROR_INVALID_DEVICE_URI )

        self.device_state = DEVICE_STATE_FOUND
        self.status_code = STATUS_PRINTER_IDLE
        self.error_state = ERROR_STATE_CLEAR
        self.polling = True
        self.is_local = device.isLocal( self.bus )
        self.model, self.model_ui = device.normalizeModelName( self.model )
        self.ds = {}
        self.mq = {}
        self.cups_printers = []
        self.last_event = None
        self.types_cached = False


class JobListViewItem( QListViewItem ):
    def __init__( self, parent, printer, job_id, state, user, title ):
        QListViewItem.__init__( self, parent, printer, str( job_id ), state, user, title )
        self.job_id = job_id
        self.printer = printer


def createBarGraph( percent, agent_type, w=100, h=18 ):
    fw = w/100*percent
    px = QPixmap( w, h )
    pp = QPainter( px )
    pp.setBackgroundMode( Qt.OpaqueMode )
    pp.setPen( Qt.black )

    pp.setBackgroundColor( Qt.white )

    # erase the background
    b = QBrush( QColor( Qt.white ) ) 
    pp.fillRect( 0, 0, w, h, b )

    # fill in the bar
    if agent_type in ( AGENT_TYPE_BLACK, AGENT_TYPE_UNSPECIFIED ):
        b = QBrush( QColor( Qt.black ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif agent_type == AGENT_TYPE_CMY:
        h3 = h/3
        b = QBrush( QColor( Qt.cyan ) )
        pp.fillRect( 0, 0, fw, h3, b )
        b = QBrush( QColor( Qt.magenta ) )
        pp.fillRect( 0, h3, fw, 2*h3, b )
        b = QBrush( QColor( Qt.yellow ) )
        pp.fillRect( 0, 2*h3, fw, h, b )
    elif agent_type == AGENT_TYPE_KCM:
        h3 = h/3
        b = QBrush( QColor( Qt.cyan ).light() )
        pp.fillRect( 0, 0, fw, h3, b )
        b = QBrush( QColor( Qt.magenta ).light() )
        pp.fillRect( 0, h3, fw, 2*h3, b )
        b = QBrush( QColor( Qt.yellow ).light() )
        pp.fillRect( 0, 2*h3, fw, h, b )
    elif agent_type == AGENT_TYPE_GGK: 
        b = QBrush( QColor( Qt.gray ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif agent_type == AGENT_TYPE_YELLOW:
        b = QBrush( QColor( Qt.yellow ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif agent_type == AGENT_TYPE_MAGENTA:
        b = QBrush( QColor( Qt.magenta ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif agent_type == AGENT_TYPE_CYAN:
        b = QBrush( QColor( Qt.cyan ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif agent_type == AGENT_TYPE_CYAN_LOW:
        b = QBrush( QColor( 225, 246, 255 ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif agent_type == AGENT_TYPE_YELLOW_LOW:
        b = QBrush( QColor( 255, 253, 225 ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif agent_type == AGENT_TYPE_MAGENTA_LOW:
        b = QBrush( QColor( 255, 225, 240 ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif agent_type == AGENT_TYPE_BLUE:
        b = QBrush( QColor( 0, 0, 255 ) )
        pp.fillRect( 0, 0, fw, h, b )

    # draw black frame
    pp.drawRect( 0, 0, w, h )

    if percent > 75 and agent_type in \
      ( AGENT_TYPE_BLACK, AGENT_TYPE_UNSPECIFIED, AGENT_TYPE_BLUE ):
        pp.setPen( Qt.white )

    # 75% ticks
    w1 = 3*w/4
    h6 = h/6
    pp.drawLine( w1, 0, w1, h6 )
    pp.drawLine( w1, h, w1, h-h6 )

    if percent > 50 and agent_type in \
      ( AGENT_TYPE_BLACK, AGENT_TYPE_UNSPECIFIED, AGENT_TYPE_BLUE ):
        pp.setPen( Qt.white )

    # 50% ticks
    w2 = w/2
    h4 = h/4
    pp.drawLine( w2, 0, w2, h4 )
    pp.drawLine( w2, h, w2, h-h4 )

    if percent > 25 and agent_type in \
      ( AGENT_TYPE_BLACK, AGENT_TYPE_UNSPECIFIED, AGENT_TYPE_BLUE ):
        pp.setPen( Qt.white )

    # 25% ticks
    w4 = w/4
    pp.drawLine( w4, 0, w4, h6 )
    pp.drawLine( w4, h, w4, h-h6 )

    return px



class IconViewItem( QIconViewItem ):
    def __init__( self, parent, text, pixmap, device_uri, is_avail=True ):
        QIconViewItem.__init__( self, parent, text, pixmap )
        self.device_uri = device_uri
        self.is_avail = is_avail


class devmgr4(DevMgr4_base):
    def __init__(self, cleanup=None, initial_device_uri=None, parent=None, name=None, fl = 0 ):
        DevMgr4_base.__init__( self, parent, name, fl )
        
        
        log.debug( "Initializing toolbox UI" )
        self.cleanup = cleanup
        
        # Make some adjustments to the UI
        self.StatusHistoryList.setSorting( -1 ) 
        self.AdvInfoList.setSorting( -1 )
        self.SuppliesList.setSorting( -1 )
        self.PrintJobList.setSorting( 1 ) # Sort on job ID column
        self.DeviceList.setAutoArrange( False )
        self.StatusHistoryList.setColumnWidth( 0, 16 )
        self.StatusHistoryList.setColumnText( 0, ' ' )
        self.StatusHistoryList.setColumnWidthMode( 1, QListView.Maximum )
        self.StatusHistoryList.setColumnWidthMode( 2, QListView.Maximum )
        self.StatusHistoryList.setColumnWidthMode( 3, QListView.Maximum )
        self.StatusHistoryList.setColumnWidthMode( 4, QListView.Maximum )
        self.StatusHistoryList.setColumnWidthMode( 5, QListView.Maximum )
        self.StatusHistoryList.setColumnWidthMode( 6, QListView.Maximum )

        self.PrintJobList.setColumnWidth( 0, 150 )
        self.PrintJobList.setColumnWidthMode( 0, QListView.Maximum )
        self.PrintJobList.setColumnWidth( 1, 60 )
        self.PrintJobList.setColumnWidthMode( 1, QListView.Maximum )
        self.PrintJobList.setColumnWidth( 2, 80 )
        self.PrintJobList.setColumnWidthMode( 2, QListView.Maximum )
        self.PrintJobList.setColumnWidth( 3, 100 )
        self.PrintJobList.setColumnWidthMode( 3, QListView.Maximum )
        self.PrintJobList.setColumnWidth( 4, 200 )
        self.PrintJobList.setColumnWidthMode( 4, QListView.Maximum )

        self.AdvInfoList.setColumnWidth( 0, 200 )
        self.AdvInfoList.setColumnWidthMode( 0, QListView.Maximum )
        self.AdvInfoList.setColumnWidth( 1, 500 )
        self.AdvInfoList.setColumnWidthMode( 1, QListView.Maximum )

        self.initial_device_uri = initial_device_uri

        self.hpiod_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.hpiod_sock.connect( ( prop.hpiod_host, prop.hpiod_port ) )

        self.service = service.Service()

        self.warning_pix = QPixmap( os.path.join( prop.image_dir, "warning.png" ) )
        self.error_pix = QPixmap( os.path.join( prop.image_dir, "error.png" ) )
        self.ok_pix = QPixmap( os.path.join( prop.image_dir, "ok.png" ) )
        self.lowink_pix = QPixmap( os.path.join( prop.image_dir, 'inkdrop.png' ) )
        self.busy_pix = QPixmap( os.path.join( prop.image_dir, 'busy.png' ) )

        self.warning_pix_small = QPixmap( os.path.join( prop.image_dir, "warning_small.png" ) )
        self.error_pix_small = QPixmap( os.path.join( prop.image_dir, "error_small.png" ) )
        self.ok_pix_small = QPixmap( os.path.join( prop.image_dir, "ok_small.png" ) )
        self.lowink_pix_small = QPixmap( os.path.join( prop.image_dir, 'inkdrop_small.png' ) )
        self.busy_pix_small = QPixmap( os.path.join( prop.image_dir, 'busy_small.png' ) )

        self.blank_lcd = os.path.join( prop.image_dir, "panel_lcd.xpm" )
        self.Panel.setPixmap( QPixmap( self.blank_lcd ) )

        self.STATUS_HISTORY_ICONS = { ERROR_STATE_CLEAR : None,
                                      ERROR_STATE_BUSY : self.busy_pix_small,
                                      ERROR_STATE_ERROR : self.error_pix_small,
                                      ERROR_STATE_LOW_SUPPLIES : self.lowink_pix_small,
                                      ERROR_STATE_OK : self.ok_pix_small,
                                      ERROR_STATE_WARNING : self.warning_pix_small,
                                    } 

        self.STATUS_ICONS = { ERROR_STATE_CLEAR : None,
                              ERROR_STATE_BUSY : self.busy_pix,
                              ERROR_STATE_ERROR : self.error_pix,
                              ERROR_STATE_LOW_SUPPLIES : self.lowink_pix,
                              ERROR_STATE_OK : self.ok_pix,
                              ERROR_STATE_WARNING : self.warning_pix, 
                            } 

        self.JOB_STATES = { 3 : self.__tr( "Pending" ),
                            4 : self.__tr( "On hold" ),
                            5 : self.__tr( "Printing" ),
                            6 : self.__tr( "Stopped" ),
                            7 : self.__tr( "Canceled" ),
                            8 : self.__tr( "Aborted" ),
                            9 : self.__tr( "Completed" ),
                           }


        self.user_config = os.path.expanduser( '~/.hplip.conf' )

        self.cmd_print = ''
        self.cmd_pcard = ''
        self.cmd_fax   = ''
        self.cmd_scan  = ''
        self.cmd_copy  = ''

        self.email_alerts = False
        self.email_address = ''
        self.smtp_server = ''

        self.auto_refresh = True
        self.auto_refresh_rate = DEF_AUTO_REFRESH_RATE

        if os.path.exists( self.user_config ):
            if not utils.path_exists_safely( self.user_config ):
                self.FailureUI( self.__tr( "<p><b>%s has insecure permissions, and was not read for security reasons.</b>" % self.user_config ) )
            else:    
                config = ConfigParser.ConfigParser()
                config.read( self.user_config )

                if config.has_section( "commands" ):
                    self.cmd_print = config.get( "commands", "print" )
                    self.cmd_pcard = config.get( "commands", "pcard" )
                    self.cmd_fax   = config.get( "commands", "fax" )
                    self.cmd_scan  = config.get( "commands", "scan" )
                    self.cmd_copy  = config.get( "commands", "copy" )

                if config.has_section( "alerts" ):
                    self.email_alerts  = config.getboolean( "alerts", 'email-alerts' )
                    self.email_address = config.get( "alerts", 'email-address'  )
                    self.smtp_server   = config.get( "alerts", 'smtp-server' )

                if config.has_section( "refresh" ):
                    self.auto_refresh = config.getboolean( "refresh", "enable" )
                    self.auto_refresh_rate = config.getint( "refresh", "rate" )


        cmd_print, cmd_scan, cmd_pcard, cmd_copy, cmd_fax = utils.deviceDefaultFunctions()

        if len( self.cmd_print ) == 0:
            self.cmd_print = cmd_print

        if len( self.cmd_scan ) == 0:
            self.cmd_scan = cmd_scan

        if len( self.cmd_pcard ) == 0:
            self.cmd_pcard = cmd_pcard

        if len( self.cmd_copy ) == 0:
            self.cmd_copy = cmd_copy

        if len( self.cmd_fax ) == 0:
            self.cmd_fax = cmd_fax

        log.debug( "Print command: %s" % self.cmd_print )
        log.debug( "PCard command: %s" % self.cmd_pcard )
        log.debug( "Fax command: %s" % self.cmd_fax )
        log.debug( "Copy command: %s " % self.cmd_copy )
        log.debug( "Scan command: %s" % self.cmd_scan )
        log.debug( "Email alerts: %s" % self.email_alerts )
        log.debug( "Email address: %s" % self.email_address )
        log.debug( "SMTP server: %s" % self.smtp_server )
        log.debug( "Auto refresh: %s" % self.auto_refresh )
        log.debug( "Auto refresh rate: %s" % self.auto_refresh_rate )

        if not self.auto_refresh:
            self.autoRefresh.toggle()

        self.update_called = False

        self.cur_device_uri = '' # Device URI 
        self.devices = {}    # { Device_URI : device.Device(), ... }
        self.device_vars = {} 
        self.num_devices = 0
        self.cur_device = None

        QTimer.singleShot( 0, self.InitialUpdate )

    def InitialUpdate( self ):
        self.RescanDevices( True )

        self.refresh_timer = QTimer(self, "RefreshTimer")
        self.connect( self.refresh_timer, SIGNAL('timeout()'), self.TimedRefresh )

        if MIN_AUTO_REFRESH_RATE <= self.auto_refresh_rate <= MAX_AUTO_REFRESH_RATE:
            self.refresh_timer.start( self.auto_refresh_rate * 1000 ) 

    def TimedRefresh( self ):
        if self.auto_refresh and self.cur_device.polling:
            log.debug( "Refresh timer..." )
            self.CleanupChildren()
            self.UpdateDevice()

    def autoRefresh_toggled(self,a0):
        self.auto_refresh = bool( a0 )
        self.SaveConfig()

    def closeEvent( self, event ):
        self.Cleanup()
        event.accept()

    def RescanDevices( self, make_history ):
        self.deviceRefreshAll.setEnabled( False )
        self.DeviceListRefresh( make_history )
        self.deviceRescanAction.setEnabled( True )
        self.deviceRefreshAll.setEnabled( True )

    def Cleanup( self ):
        self.CleanupChildren()
        if self.cleanup is not None:
            self.cleanup()

    def CleanupChildren( self ):
        log.debug( "Cleaning up child processes." )
        try:
            os.waitpid(-1, os.WNOHANG )
        except OSError:
            pass
    
    def DeviceList_currentChanged(self,a0):
        self.cur_device_uri = self.DeviceList.currentItem().device_uri
        self.cur_device = self.devices[ self.cur_device_uri ]

        self.UpdateDevice()

    def DeviceList_rightButtonClicked( self, item, pos ):
        popup = QPopupMenu( self )

        if item is not None:
            if self.cur_device.error_state == ERROR_STATE_CLEAR:
                popup.insertItem( self.__tr( "Print..." ), self.PrintButton_clicked )

                if self.cur_device.scan_type:
                    popup.insertItem( self.__tr( "Scan..." ), self.ScanButton_clicked )

                if self.cur_device.pcard_type:
                    popup.insertItem( self.__tr( "Access Photo Cards..." ), self.PCardButton_clicked )

                if self.cur_device.fax_type:
                    popup.insertItem( self.__tr( "Send Fax..." ), self.SendFaxButton_clicked )

                if self.cur_device.copy_type:
                    popup.insertItem( self.__tr( "Make Copies..." ), self.MakeCopiesButton_clicked )

                popup.insertSeparator()

            popup.insertItem( self.__tr( "Refresh Device" ), self.UpdateDevice )

        popup.insertItem( self.__tr( "Refresh All" ), self.deviceRefreshAll_activated )

        popup.popup( pos )

    def UpdateDevice( self, check_state=True ): 
        log.debug( utils.bold( "Update: %s %s %s" % ( "*"*20, self.cur_device_uri, "*"*20 ) ) )
        self.update_called = True
        cd = self.cur_device
        self.setCaption( "%s - HP Device Manager" % cd.model_ui ) 
        log.debug( "Device URI=%s" % self.cur_device_uri )

        if check_state: # get "live" status of printer
            try:
                # Check device status and create appropriate history
                self.cur_device.ds = self.service.queryDevice( self.cur_device_uri, 
                                                               self.cur_device.device_state, 
                                                               self.cur_device.status_code,
                                                               True )
            except Error:
                self.cur_device.ds['device-state'] = DEVICE_STATE_NOT_FOUND

            cd.device_state = self.cur_device.ds.get( 'device-state', DEVICE_STATE_NOT_FOUND )

        if not self.cur_device.types_cached:
            try:
                self.cur_device.mq = self.service.queryModel( cd.model )
            except Error:
                log.error( "Model %s not found in models.xml" % cd.model )

            mq = self.cur_device.mq
            self.cur_device.clean_type = int( mq.get( 'clean-type', 0 ) )
            self.cur_device.align_type = int( mq.get( 'align-type', 0 ) )
            self.cur_device.color_cal_type = int( mq.get( 'color-cal-type', 0 ) )
            self.cur_device.scan_type = int( mq.get( 'scan-type', 0 ) )
            self.cur_device.pcard_type = int( mq.get( 'pcard-type', 0 ) )
            self.cur_device.fax_type = int( mq.get( 'fax-type', 0 ) )
            self.cur_device.copy_type = int( mq.get( 'copy-type', 0 ) )
            self.cur_device.status_type = int( mq.get( 'status-type', 0 ) )
            self.cur_device.tech_type = int( mq.get( 'tech-type', 0 ) )
            self.cur_device.embedded_server_type = int( mq.get( 'embedded-server-type', 0 ) )

            self.cur_device.types_cached = True


        self.UpdateHistory() # get status_code and error_state from history

        log.debug( "Device state = %d" % cd.device_state )
        log.debug( "Status code = %d" % cd.status_code )
        log.debug( "Error state = %d" % cd.error_state )

        icon = self.CreatePixmap( self.cur_device, cd.error_state )
        self.DeviceList.currentItem().setPixmap( icon )

        if not self.rescanning:
            self.UpdateTabs()

            self.device_vars = { 
                'URI'        : self.cur_device_uri, 
                'DEVICE_URI' : self.cur_device_uri, 
                'SANE_URI'   : self.cur_device_uri.replace( 'hp:', 'hpaio:' ),
                'PRINTER'    : self.cur_device.cups_printers[0],
                'HOME'       : prop.home_dir,
                               }


    default_pics = { 'deskjet'    : 'default_deskjet.png',
                     'business'   : 'default_business_inkjet.png',
                     'psc'        : 'default_psc.png',
                     'laserjet'   : 'default_laserjet.png',
                     'officejet'  : 'default_officejet.png',
                     'photosmart' : 'default_photosmart.png',
                     'default'    : 'default_printer.png',
                    }


    def CreatePixmap( self, dev, error_state, tech_type=status.TECH_TYPE_NONE ): 
        model_lower = dev.model.lower()
        f = os.path.join( prop.image_dir, dev.model.replace( '/', '_' ) + ".png" )

        if not os.path.exists( f ):
            for p in devmgr4.default_pics:
                if model_lower.find( p ) >= 0:
                    f = devmgr4.default_pics[ p ]
                    break
                else:
                    f = devmgr4.default_pics[ 'default' ]

            f = os.path.join( prop.image_dir, f )

        dev.pic_file = f

        pix = QPixmap( f )

        icon = QPixmap( pix.width(), pix.height() )
        p = QPainter( icon )
        p.eraseRect( 0, 0, icon.width(), icon.height() )
        p.drawPixmap( 0, 0, pix )

        if error_state == ERROR_STATE_ERROR:
            p.drawPixmap( 0, 0, self.error_pix )

        elif error_state == ERROR_STATE_WARNING:
            p.drawPixmap( 0, 0, self.warning_pix )

        elif error_state == ERROR_STATE_BUSY:
            p.drawPixmap( 0, 0, self.busy_pix )

        elif error_state == ERROR_STATE_OK:
            p.drawPixmap( 0, 0, self.ok_pix )

        elif error_state == ERROR_STATE_LOW_SUPPLIES:
            if tech_type in (TECH_TYPE_MONO_INK, TECH_TYPE_COLOR_INK ):
                p.drawPixmap( 0, 0, self.lowink_pix )
            elif tech_type in (TECH_TYPE_MONO_LASER, TECH_TYPE_COLOR_LASER ):
                pass

        p.end()

        return icon

    def DeviceListRefresh( self, make_history ):
        log.debug( "Rescanning device list..." )
        self.rescanning = True
        self.DeviceList.clear()
        self.devices.clear()
        self.make_history = make_history
        self.printer_list = cups.getPrinters()
        self.num_printers = len( self.printer_list )

        self.num_devices = 0

        if self.num_printers > 0:
            self.pb = QProgressBar( self.statusBar(), 'ProgressBar' )
            self.pb.setTotalSteps( self.num_printers )
            self.statusBar().addWidget( self.pb )
            self.pb.show()

            self.devices = {}
            self.printer_num = 0

            self.scan_timer = QTimer(self, "ScanTimer")
            self.connect( self.scan_timer, SIGNAL('timeout()'), 
                          self.ContinueDeviceListRefresh )

            self.scan_timer.start( 0 ) 

    def ContinueDeviceListRefresh( self ):
        if self.printer_num == self.num_printers:

            self.scan_timer.stop()
            self.disconnect( self.scan_timer, SIGNAL('timeout()'), 
                             self.ContinueDeviceListRefresh )

            self.scan_timer = None
            del self.scan_timer

            self.pb.hide()
            self.statusBar().removeWidget( self.pb )

            self.DeviceList.adjustItems()
            self.DeviceList.updateGeometry()

            self.rescanning = False

            self.DeviceList.setCurrentItem( self.DeviceList.firstItem() )

            if self.num_devices == 1:
                self.UpdateDevice( False )

            elif self.num_devices == 0:
                dlg = NoDevicesForm( self, "", True )
                dlg.show()

            return

        printer = self.printer_list[ self.printer_num ]
        self.pb.setProgress( self.printer_num )
        self.printer_num += 1

        if not printer.device_uri.startswith( 'hp' ):
            return

        log.debug( utils.bold( "Refresh: %s %s %s" % ( "*"*20, printer.device_uri, "*"*20 ) ) )

        try:
            self.devices[ printer.device_uri ]
        except KeyError: 

            try:
                d = DummyDevice( printer.device_uri )
            except Error:
                return
            else:
                d.cups_printers.append( printer.name ) 
                icon = self.CreatePixmap( d, ERROR_STATE_CLEAR )
                i = IconViewItem( self.DeviceList, d.model_ui, icon, d.device_uri )

                self.devices[ d.device_uri ] = d
                self.cur_device = d
                self.cur_device_uri = d.device_uri

                self.num_devices += 1
                self.DeviceList.setCurrentItem( i )

        else:
            self.devices[ printer.device_uri ].cups_printers.append( printer.name ) 


    def ActivateDevice( self, device_uri ):
        log.debug( utils.bold( "Activate: %s %s %s" % ( "*"*20, device_uri, "*"*20 ) ) )
        d = self.DeviceList.firstItem()
        found = False

        while d is not None:

            if d.device_uri == device_uri:
                found = True
                self.DeviceList.setSelected( d, True )
                self.Tabs.setCurrentPage( 0 )
                break

            d = d.nextItem()

        return found

    def UpdatePrintJobsTab( self ):
        self.PrintJobList.clear()
        num_jobs = 0
        jobs = cups.getJobs()

        for j in jobs:

            if j.dest in self.cur_device.cups_printers:

                JobListViewItem( self.PrintJobList, j.dest, j.id, 
                                 self.JOB_STATES[ j.state ], j.user, j.title )

                num_jobs += 1

        self.CancelPrintJobButton.setEnabled( num_jobs > 0 )

    def PrintJobList_currentChanged( self, item ):
        pass

    def CancelPrintJobButton_clicked(self):
        item = self.PrintJobList.currentItem()
        if item is not None:
            self.service.cancelJob( item.job_id, self.cur_device_uri )

    def UpdateTabs( self ):
        self.UpdateFunctionsTab()
        self.UpdateStatusTab()
        self.UpdateSuppliesTab()
        self.UpdateMaintTab()
        self.UpdateInfoTab()
        self.UpdatePrintJobsTab()
        self.UpdatePanelTab()

    def UpdatePanelTab( self ):
        ds = self.cur_device.ds

        if ds['panel'] == 1:
            line1 = ds['panel-line1']
            line2 = ds['panel-line2']
        else:
            line1 = self.__tr( "Front panel display" )
            line2 = self.__tr( "unavailable" )

        pm = QPixmap( self.blank_lcd )

        p = QPainter()
        p.begin( pm )
        p.setPen( QColor( 0, 0, 0 ) )
        p.setFont( self.font() )
        #p.setFont( QFont( "LCD", 12 ) )

        x, y_line1, y_line2 = 10, 17, 33

        # TODO: Scroll long lines
        p.drawText( x, y_line1, line1 )
        p.drawText( x, y_line2, line2 )
        p.end()

        self.Panel.setPixmap( pm )


    def UpdateFunctionsTab( self ):
        self.ToggleFunctionButtons( self.cur_device.device_state in \
            ( DEVICE_STATE_FOUND, DEVICE_STATE_JUST_FOUND ) )

    def ToggleFunctionButtons( self, toggle ):
        if toggle:
            self.PrintButton.setEnabled( True )
            self.ScanButton.setEnabled( self.cur_device.scan_type )
            self.PCardButton.setEnabled( self.cur_device.pcard_type )
            self.SendFaxButton.setEnabled( self.cur_device.fax_type )
            self.MakeCopiesButton.setEnabled( self.cur_device.copy_type )
        else:
            self.PrintButton.setEnabled( False )
            self.ScanButton.setEnabled( False )
            self.PCardButton.setEnabled( False )
            self.SendFaxButton.setEnabled( False )
            self.MakeCopiesButton.setEnabled( False )

    def UpdateHistory( self ):
        cd = self.cur_device
        try:
            cd.hist = self.service.getHistory( self.cur_device_uri )
            cd.hist.reverse()
        except Error:
            log.error( "History query failed." )
            cd.last_event = None
            cd.error_state = ERROR_STATE_ERROR
            cd.status_code = STATUS_UNKNOWN
        else:
            cd.last_event = cd.hist[-1]
            cd.status_code = int( cd.last_event[11] )
            cd.error_state = STATUS_TO_ERROR_STATE_MAP.get( cd.status_code, ERROR_STATE_CLEAR )



    def UpdateStatusTab( self ):
        cd = self.cur_device
        last_event = cd.last_event

        self.StatusHistoryList.clear()

        if last_event is None:
            self.UpdateHistory()
            last_event = cd.last_event

        for x in cd.hist:
            job_id = x[9]
            code = x[11]

            if job_id == 0:
                i = QListViewItem( self.StatusHistoryList, '', 
                                   time.strftime( "%x", x[:9] ),
                                   time.strftime( "%H:%M:%S", x[:9] ),
                                   '', '', str(code), x[12] )

            else:
                i = QListViewItem( self.StatusHistoryList, '',
                               time.strftime( "%x", x[:9] ),
                               time.strftime( "%H:%M:%S", x[:9] ),
                               x[10], str(job_id), str(code), x[12] )

            error_state = STATUS_TO_ERROR_STATE_MAP.get( code, ERROR_STATE_CLEAR )
            status_pix = self.STATUS_HISTORY_ICONS[ error_state ]

            if status_pix is not None:
                i.setPixmap( 0, status_pix )


        self.StatusText.setText( last_event[12] )
        self.StatusText2.setText( last_event[13] )

        if cd.error_state == ERROR_STATE_CLEAR:
            self.StatusIcon.clear()

        elif cd.error_state == ERROR_STATE_OK:
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "ok.png" ) ) )

        elif cd.error_state == ERROR_STATE_WARNING:
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "warning.png" ) ) )

        elif cd.error_state == ERROR_STATE_LOW_SUPPLIES:
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "warning.png" ) ) )

        elif cd.error_state == ERROR_STATE_ERROR:
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "error.png" ) ) )

        elif cd.error_state == ERROR_STATE_BUSY:
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "busy.png" ) ) )


    def UpdateSuppliesTab( self ):
        self.SuppliesList.clear()

        if self.cur_device.status_type != STATUS_TYPE_NONE:
            s = self.cur_device.ds
            a = 1
            while True:

                try:
                    agent_type = int( s[ 'agent%d-type' % a ] )
                except KeyError:
                    break
                else:
                    agent_kind = int( s[ 'agent%d-kind' % a ] )
                    agent_health = int( s[ 'agent%d-health' % a ] )
                    agent_level = int( s[ 'agent%d-level' % a ] )
                    agent_sku = s[ 'agent%d-sku' % a ]
                    agent_desc = s [ 'agent%d-desc' % a ]
                    agent_health_desc = s [ 'agent%d-health-desc' % a ]

                    if agent_health == AGENT_HEALTH_OK and \
                        agent_kind in ( AGENT_KIND_SUPPLY, 
                                        AGENT_KIND_HEAD_AND_SUPPLY, 
                                        AGENT_KIND_TONER_CARTRIDGE,
                                        AGENT_KIND_MAINT_KIT,
                                        AGENT_KIND_ADF_KIT,
                                        AGENT_KIND_INT_BATTERY ):

                        x = QListViewItem( self.SuppliesList,
                                           agent_desc,
                                           agent_sku, )

                        x.setPixmap( 2, createBarGraph( agent_level, agent_type ) )

                    else:
                        QListViewItem( self.SuppliesList,
                                       agent_desc,
                                       agent_sku,
                                       agent_health_desc, )


                a += 1



    def UpdateMaintTab( self ):
        self.ToggleMaintButtons( self.cur_device.device_state in \
            ( DEVICE_STATE_FOUND, DEVICE_STATE_JUST_FOUND ) )


    def ToggleMaintButtons( self, toggle ):
        if toggle:
            self.CleanPensButton.setEnabled( self.cur_device.clean_type )
            self.AlignPensButton.setEnabled( self.cur_device.align_type )
            self.ColorCalibrationButton.setEnabled( self.cur_device.color_cal_type )
        else:
            self.CleanPensButton.setEnabled( False )
            self.AlignPensButton.setEnabled( False )
            self.ColorCalibrationButton.setEnabled( False )

    def ToggleInfoButtons( self, toggle ):
        if toggle:
            self.PrintTestPageButton.setEnabled( True )
            self.OpenEmbeddedBrowserButton.setEnabled( 
                self.cur_device.embedded_server_type and self.cur_device.bus == 'net' )
        else:
            self.PrintTestPageButton.setEnabled( False )
            self.OpenEmbeddedBrowserButton.setEnabled( False )


    def UpdateInfoTab( self ):
        self.ToggleInfoButtons( self.cur_device.device_state in \
            ( DEVICE_STATE_FOUND, DEVICE_STATE_JUST_FOUND ) )

        self.AdvInfoList.clear()

        ds_keys = self.cur_device.ds.keys()
        ds_keys.sort()
        ds_keys.reverse()
        for key,i in zip( ds_keys, range(len(ds_keys))):
            QListViewItem( self.AdvInfoList, key, str(self.cur_device.ds[key] ))

        mq_keys = self.cur_device.mq.keys()
        mq_keys.sort()
        mq_keys.reverse()
        for key,i in zip( mq_keys, range(len(mq_keys))):
            QListViewItem( self.AdvInfoList, key, str(self.cur_device.mq[key] ))

        QListViewItem( self.AdvInfoList, 'cups-printers', ','.join( self.cur_device.cups_printers ) )
        QListViewItem( self.AdvInfoList, 'serial-number', self.cur_device.ds.get( 'serial-number', '?' ) )
        QListViewItem( self.AdvInfoList, 'model-name', self.cur_device.model )
        QListViewItem( self.AdvInfoList, 'device-uri', self.cur_device.device_uri )


    def EventUI( self, event_code, event_type, 
                 error_string_short, error_string_long, 
                 retry_timeout, job_id, device_uri ):

        log.debug( "Event: code=%d type=%s string=%s timeout=%d id=%d uri=%s" % 
                 ( event_code, event_type,  error_string_short, retry_timeout, job_id, device_uri ) )


        if self.ActivateDevice( device_uri ):
            self.cur_device.status_code = event_code 
            self.UpdateDevice( False )
            self.Tabs.setCurrentPage( 1 )


    def settingsConfigure_activated(self, tab_to_show=0 ):
        dlg = SettingsDialog( self )

        dlg.EmailCheckBox.setChecked( self.email_alerts )
        dlg.EmailAddress.setText( self.email_address )
        dlg.SMTPServer.setText( self.smtp_server )

        dlg.PrintCommand.setText( self.cmd_print )
        dlg.ScanCommand.setText( self.cmd_scan )
        dlg.AccessPCardCommand.setText( self.cmd_pcard )
        dlg.SendFaxCommand.setText( self.cmd_fax )
        dlg.MakeCopiesCommand.setText( self.cmd_copy )

        dlg.AutoRefreshRate.setValue( self.auto_refresh_rate )

        dlg.TabWidget.setCurrentPage( tab_to_show )

        if dlg.exec_loop() == QDialog.Accepted:

            self.cmd_print = str( dlg.PrintCommand.text() )
            self.cmd_scan = str( dlg.ScanCommand.text() )
            self.cmd_pcard = str( dlg.AccessPCardCommand.text() )
            self.cmd_fax   = str( dlg.SendFaxCommand.text() )
            self.cmd_copy  = str( dlg.MakeCopiesCommand.text() )

            self.email_alerts = bool( dlg.EmailCheckBox.isChecked() )
            self.email_address = str( dlg.EmailAddress.text() )
            self.smtp_server = str( dlg.SMTPServer.text() )

            new_refresh_value = int( dlg.AutoRefreshRate.value() )

            if new_refresh_value != self.auto_refresh_rate:
                self.auto_refresh_rate = new_refresh_value
                self.refresh_timer.changeInterval( self.auto_refresh_rate * 1000 )

            self.SetAlerts()
            self.SaveConfig()


    def SetAlerts( self ):
        self.service.setAlerts( self.email_alerts,
                                self.email_address,
                                self.smtp_server,
                              )

    def SaveConfig( self ):
        config = ConfigParser.ConfigParser()

        if utils.path_exists_safely( self.user_config ):
            fp = file( self.user_config, 'r' )
            config.read( self.user_config )
            fp.close()

        if not config.has_section( 'commands' ):
            config.add_section( 'commands' )

        config.set( 'commands', 'print', self.cmd_print )
        config.set( 'commands', 'pcard', self.cmd_pcard )
        config.set( 'commands', 'fax',   self.cmd_fax )
        config.set( 'commands', 'scan',  self.cmd_scan )
        config.set( 'commands', 'copy',  self.cmd_copy )

        if not config.has_section( 'alerts' ):
            config.add_section( 'alerts' )

        config.set( "alerts", 'email-alerts', self.email_alerts )
        config.set( "alerts", 'email-address', self.email_address  )
        config.set( "alerts", 'smtp-server', self.smtp_server )

        if not config.has_section( 'maint' ):
            config.add_section( 'maint' )

        if not config.has_section( 'refresh' ):
            config.add_section( 'refresh' )

        config.set( 'refresh', 'enable', self.auto_refresh )
        config.set( 'refresh', 'rate', self.auto_refresh_rate )

        # TODO: Check to make sure file write succeeded
        fp = file( self.user_config, 'w' )

        # Fix permissions
        try:
            os.chmod( self.user_config, 0600 )
        except (IOError, OSError ):
            pass

        config.write( fp )
        fp.close()


    def SuccessUI( self ):
        QMessageBox.information( self, 
                             self.caption(),
                             self.__tr( "<p><b>The operation completed successfully.</b>" ),
                              QMessageBox.Ok, 
                              QMessageBox.NoButton, 
                              QMessageBox.NoButton )

    def FailureUI( self, error_text ):
        QMessageBox.critical( self, 
                             self.caption(),
                             error_text,
                              QMessageBox.Ok, 
                              QMessageBox.NoButton, 
                              QMessageBox.NoButton )

    def WarningUI( self, msg ):
        QMessageBox.warning( self, 
                             self.caption(),
                             msg,
                              QMessageBox.Ok, 
                              QMessageBox.NoButton, 
                              QMessageBox.NoButton )



    def update_spinner( self ):
        pass

    def LoadPaperUI( self ):
        if LoadPaperForm( self ).exec_loop() == QDialog.Accepted:
            return True
        return False

    def AlignmentNumberUI( self, letter, hortvert, colors, line_count, choice_count ):
        dlg = AlignForm( self, letter, hortvert, colors, line_count, choice_count )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.value
        else:
            return False, 0

    def PaperEdgeUI( self, maximum ):
        dlg = PaperEdgeAlignForm( self )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.value
        else:
            return False, 0

    def ColorAdjUI( self, line, maximum=0 ):
        dlg = ColorAdjForm( self, line )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.value
        else:
            return False, 0

    def ColorCalUI( self ):
        dlg = ColorCalForm( self )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.value
        else:
            return False, 0

    def ColorCalUI2( self ):
        dlg = ColorCalForm2( self )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.value
        else:
            return False, 0


    def BothPensRequiredUI( self ):
        self.WarningUI( self.__tr( "<p><b>Both cartridges are required for alignment.</b><p>Please install both cartridges and try again." ) )

    def InvalidPenUI( self ):
        self.WarningUI( self.__tr( "<p><b>One or more cartiridges are missing from the printer.</b><p>Please install cartridge(s) and try again." ) )

    def PhotoPenRequiredUI( self ):
        self.WarningUI( self.__tr( "<p><b>Both the photo and color cartridges must be inserted into the printer to perform color calibration.</b><p>If you are planning on printing with the photo cartridge, please insert it and try again." ) )

    def PhotoPenRequiredUI2( self ):
        self.WarningUI( self.__tr( "<p><b>Both the photo (regular photo or photo blue) and color cartridges must be inserted into the printer to perform color calibration.</b><p>If you are planning on printing with the photo or photo blue cartridge, please insert it and try again." ) )


    def AioUI1( self ):
        dlg = AlignType6Form1( self )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.print_page # Next >
        else:
            return False, False # Printpage


    def AioUI2( self ):
        AlignType6Form2( self ).exec_loop()

    def AlignPensButton_clicked( self ):
        d = device.Device( self.hpiod_sock, self.cur_device_uri )
        d.open()
        ok = False;

        align_type = self.cur_device.align_type

        if align_type == 1: # Auto
            ok = maint.AlignType1( d, self.LoadPaperUI )

        elif align_type == 2: # 8xx
            ok = maint.AlignType2( d, self.LoadPaperUI, self.AlignmentNumberUI,
                                   self.BothPensRequiredUI, self.update_spinner )

        elif align_type == 3: #9xx
            ok = maint.AlignType3( d, self.LoadPaperUI, self.AlignmentNumberUI,
                                   self.PaperEdgeUI, self.update_spinner, align_type )

        elif align_type in [ 4, 5, 7 ]: # LIDIL 0.3.8, LIDIL 0.4.3, xBow VIP
            ok = maint.AlignxBow( d, align_type, self.LoadPaperUI, self.AlignmentNumberUI,
                                  self.PaperEdgeUI, self.InvalidPenUI, self.ColorAdjUI, 
                                  self.update_spinner )

        elif align_type == 6: # xBow AiO
            ok = maint.AlignType6( d, self.AioUI1, self.AioUI2, self.LoadPaperUI )

        elif align_type == 8: # 450
            ok = maint.AlignType8( d, self.LoadPaperUI, self.AlignmentNumberUI,
                              self.update_spinner )

        elif align_type == 9: #9xx without edge alignment
            ok = maint.AlignType3( d, self.LoadPaperUI, self.AlignmentNumberUI,
                              self.PaperEdgeUI, self.update_spinner, align_type )                      

        d.close()

        if ok:
            self.SuccessUI()


    def ColorCalibrationButton_clicked( self ):
        color_cal_type = self.cur_device.color_cal_type
        ok = False
        d = device.Device( self.hpiod_sock, self.cur_device_uri )
        d.open()

        if color_cal_type == 1: # 450
            ok = maint.colorCalType1( d, self.LoadPaperUI, self.ColorCalUI,
                                 self.PhotoPenRequiredUI, update_spinner )

        elif color_cal_type == 2: # BIJ1200, ...
            ok = maint.colorCalType2( d, self.LoadPaperUI, self.ColorCalUI2,
                                         self.InvalidPenUI, update_spinner )

        elif color_cal_type == 3: # PS8750, DJ57xx
            ok = maint.colorCalType3( d, self.LoadPaperUI, self.ColorAdjUI,
                                         self.PhotoPenRequiredUI2, update_spinner )

        d.close()        

        if ok:
            self.SuccessUI()


    def PrintTestPageButton_clicked( self ):
        d = device.Device( self.hpiod_sock, self.cur_device_uri )
        d.open()

        print_file = os.path.join( prop.home_dir, 'data', 'ps', 'testpage.ps.gz' )

        if self.LoadPaperUI():
            d.printParsedGzipPostscript( print_file )
            self.SuccessUI()

        d.close()


    def CleanUI1( self ):
        return CleaningForm( self, 1 ).exec_loop() == QDialog.Accepted

    def CleanUI2( self ):
        return CleaningForm( self, 2 ).exec_loop() == QDialog.Accepted

    def CleanUI3( self ):
        CleaningForm2( self ).exec_loop()
        return True

    def WaitUI( self, seconds ):
        WaitForm( seconds, self ).exec_loop()


    def CleanPensButton_clicked( self ):
        d = device.Device( self.hpiod_sock, self.cur_device_uri )

        clean_type = self.cur_device.clean_type
        log.debug( "Clean: Type=%d" % clean_type )

        if clean_type == 1: # PCL
            maint.cleaning( d, clean_type, maint.cleanType1, maint.primeType1, 
                            maint.wipeAndSpitType1, self.LoadPaperUI,
                            self.CleanUI1, self.CleanUI2, self.CleanUI3,
                            self.WaitUI )

        elif clean_type == 2: # LIDIL
            maint.cleaning( d, clean_type, maint.cleanType2, maint.primeType2, 
                            maint.wipeAndSpitType2, self.LoadPaperUI,
                            self.CleanUI1, self.CleanUI2, self.CleanUI3,
                            self.WaitUI )

        elif clean_type == 3: # PCL alignment with Printout
            maint.cleaning( d, clean_type, maint.cleanType1, maint.primeType1, 
                            maint.wipeAndSpitType1, self.LoadPaperUI,
                            self.CleanUI1, self.CleanUI2, self.CleanUI3,
                            self.WaitUI )


    def deviceRescanAction_activated( self ):
        self.deviceRescanAction.setEnabled( False )
        self.UpdateDevice()
        self.deviceRescanAction.setEnabled( True )

    def deviceRefreshAll_activated(self):
        self.RescanDevices( True )

    def DeviceList_clicked(self,a0):
        pass

    def OpenEmbeddedBrowserButton_clicked(self):
        import webbrowser
        url = "http://%s" % self.cur_device.host
        log.debug( "URL = %s" % url )
        webbrowser.open_new( url )

    def AdvancedInfoButton_clicked( self ):
        AdvancedInfoForm( self.cur_device, self, None, 0, 1  ).exec_loop()

    def PrintButton_clicked(self):
        self.RunCommand( self.cmd_print )

    def ScanButton_clicked(self):
        self.RunCommand( self.cmd_scan )

    def PCardButton_clicked(self):
        self.RunCommand( self.cmd_pcard )

    def SendFaxButton_clicked(self):
        #self.RunCommand( self.cmd_fax )
        self.FailureUI( self.__tr( "<p><b>Sorry, the send fax feature is currently not implemented.</b>" ) )

    def MakeCopiesButton_clicked(self):
        #self.RunCommand( self.cmd_copy )
        self.FailureUI( self.__tr( "<p><b>Sorry, the make copies feature is currently not implemented.</b>" ) )

    def ConfigureFeaturesButton_clicked(self):
        self.settingsConfigure_activated( 3 )

    def RunCommand( self, cmd, macro_char='%' ):
        self.ToggleFunctionButtons( False )
        if len( cmd ) == 0:
            self.FailureUI( self.__tr( "<p><b>Unable to run command. No command specified.</b><p>Use <pre>Configure...</pre> to specify a command to run." ) )
            log.error( "No command specified. Use settings to configure commands." )
        else:
            log.debug( cmd )
            cmd = ''.join( [ self.device_vars.get( x, x ) for x in cmd.split( macro_char ) ] )
            log.debug( cmd )

            path = cmd.split()[0]
            args = cmd.split()

            log.debug( path )
            log.debug( args )
            
            self.CleanupChildren()
            os.spawnvp( os.P_NOWAIT, path, args )
            
            
        self.ToggleFunctionButtons( True )


    def helpAbout(self):
        dlg = AboutDlg( self )
        dlg.VersionText.setText( prop.version )
        dlg.exec_loop()

    def __tr(self,s,c = None):
        return qApp.translate("DevMgr4",s,c)
