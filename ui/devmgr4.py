#!/usr/bin/env python
#
# $Revision: 1.48 $ 
# $Date: 2005/01/07 00:25:43 $
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

# Std Lib
import sys
import socket
import time
import os

# Local
from base.g import *
from base import device, service, status, msg, maint, utils
from prnt import cups

# Qt
from qt import *

# Main form
from devmgr4_base import DevMgr4_base

# Alignment forms
from alignform import AlignForm
from paperedgealignform import PaperEdgeAlignForm
from colorcalform import ColorCalForm # 450
from coloradjform import ColorAdjForm # LIDIL

# Misc forms
from bothpensrequiredform import BothPensRequiredForm
from invalidpenconfigform import InvalidPenConfigForm
from loadpaperform import LoadPaperForm
from advancedinfoform import AdvancedInfoForm
from settingsdialog import SettingsDialog
from photopenrequiredform import PhotoPenRequiredForm
from nodevicesform import NoDevicesForm
from aligntype6form1 import AlignType6Form1
from aligntype6form2 import AlignType6Form2
from successform import SuccessForm
from failureform import FailureForm
from aboutdlg import AboutDlg


cur_device_uri = '' # Device URI 
devices = {}    # { Device_URI : device.Device(), ... }
device_vars = {} 
num_devices = 0
cur_device = None


class DummyDevice:
    def __init__( self, device_uri ):
        self.device_uri = device_uri
        
        try:
            self.back_end, self.is_hp, self.bus, self.model, self.serial, self.dev_file, self.host, self.port = \
                device.parseDeviceURI( self.device_uri )
            
        except Error:
            log.warn( "Malformed/non-HP URI: %s" % self.device_uri )
            self.device_state = device.DEVICE_STATE_NOT_FOUND
            raise Error( ERROR_INVALID_DEVICE_URI )
            
        self.device_state = device.DEVICE_STATE_FOUND
        self.is_local = device.isLocal( self.bus )
        self.model, self.model_ui = device.normalizeModelName( self.model )
        self.ds = {}
        self.cups_printers = []
        self.job_id = 0
        
        
        
def createBarGraph( percent, AGENT_type, w=100, h=18 ):
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
    if AGENT_type == status.AGENT_TYPE_BLACK:
        b = QBrush( QColor( Qt.black ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_CMY:
        h3 = h/3
        b = QBrush( QColor( Qt.cyan ) )
        pp.fillRect( 0, 0, fw, h3, b )
        b = QBrush( QColor( Qt.magenta ) )
        pp.fillRect( 0, h3, fw, 2*h3, b )
        b = QBrush( QColor( Qt.yellow ) )
        pp.fillRect( 0, 2*h3, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_KCM:
        h3 = h/3
        b = QBrush( QColor( Qt.cyan ).light() )
        pp.fillRect( 0, 0, fw, h3, b )
        b = QBrush( QColor( Qt.magenta ).light() )
        pp.fillRect( 0, h3, fw, 2*h3, b )
        b = QBrush( QColor( Qt.yellow ).light() )
        pp.fillRect( 0, 2*h3, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_GGK: 
        b = QBrush( QColor( Qt.gray ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_YELLOW:
        b = QBrush( QColor( Qt.yellow ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_MAGENTA:
        b = QBrush( QColor( Qt.magenta ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_CYAN:
        b = QBrush( QColor( Qt.cyan ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_CYAN_LOW:
        b = QBrush( QColor( 225, 246, 255 ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_YELLOW_LOW:
        b = QBrush( QColor( 255, 253, 225 ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_MAGENTA_LOW:
        b = QBrush( QColor( 255, 225, 240 ) )
        pp.fillRect( 0, 0, fw, h, b )
    elif AGENT_type == status.AGENT_TYPE_BLUE:
        b = QBrush( QColor( 0, 0, 255 ) )
        pp.fillRect( 0, 0, fw, h, b )

    # draw black frame
    pp.drawRect( 0, 0, w, h )
    
    if percent > 75 and AGENT_type in \
      ( status.AGENT_TYPE_BLACK, status.AGENT_TYPE_BLUE ):
        pp.setPen( Qt.white )
    
    # 75% ticks
    w1 = 3*w/4
    h6 = h/6
    pp.drawLine( w1, 0, w1, h6 )
    pp.drawLine( w1, h, w1, h-h6 )

    if percent > 50 and AGENT_type in \
      ( status.AGENT_TYPE_BLACK, status.AGENT_TYPE_BLUE ):
        pp.setPen( Qt.white )

    # 50% ticks
    w2 = w/2
    h4 = h/4
    pp.drawLine( w2, 0, w2, h4 )
    pp.drawLine( w2, h, w2, h-h4 )

    if percent > 25 and AGENT_type in \
      ( status.AGENT_TYPE_BLACK, status.AGENT_TYPE_BLUE ):
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
    def __init__(self, initial_device_uri=None, parent=None, name=None, fl = 0 ):
        DevMgr4_base.__init__( self, parent, name, fl )
        
        log.debug( "Initializing toolbox UI" )
        
        self.StatusHistoryList.setSorting(-1) 
        
        self.initial_device_uri = initial_device_uri
        
        self.hpiod_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.hpiod_sock.connect( ( prop.hpiod_host, prop.hpiod_port ) )
        
        self.service = service.Service()

        self.DeviceList.setAutoArrange( False )
        self.warning_pix = QPixmap( os.path.join( prop.image_dir, "warning.png" ) )
        self.error_pix = QPixmap( os.path.join( prop.image_dir, "error.png" ) )
        self.ok_pix = QPixmap( os.path.join( prop.image_dir, "ok.png" ) )
        self.user_config = os.path.expanduser( '~/.hplip.conf' )
        
        self.cmd_print = ''
        self.cmd_pcard = ''
        self.cmd_fax   = ''
        self.cmd_scan  = ''
        self.cmd_copy  = ''
        
        self.email_alerts = False
        self.email_address = ''
        self.smtp_server = ''
        self.popup_alerts = True
        
        self.cleaning_level = 0

        if os.path.exists( self.user_config ):
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
                self.popup_alerts  = config.getboolean( "alerts", 'popup-alerts' )
                
            if config.has_section( "maint" ):
                self.cleaning_level = config.getint( "maint", 'cleaning-level' )
            
        
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
        log.debug( "Popup alerts: %s" % self.popup_alerts )
        log.debug( "Cleaning level: %d" % self.cleaning_level )
        
        self.update_called = False

        QTimer.singleShot( 0, self.initialUpdate )
        
    def initialUpdate( self ):
        self.rescan( False )
        
        if self.initial_device_uri is not None:
            self.activateItem( self.initial_device_uri )
            self.UpdateStatusTab()
            self.Tabs.setCurrentPage( 1 )
        
    def closeEvent( self, event ):
        self.cleanup()
        event.accept()

    def rescan( self, make_history ):
        self.ToggleFunctionButtons( False )
        self.deviceRefreshAll.setEnabled( False )
        
        self.refreshDeviceList( make_history )
        global num_devices

        if num_devices == 0:
            self.deviceRescanAction.setEnabled( False )
            dlg = NoDevicesForm( self, "", True )
            dlg.show()
        else:
            self.deviceRescanAction.setEnabled( True )
        
        self.deviceRefreshAll.setEnabled( True )
       
    def cleanup( self ):
        pass
        
    def DeviceList_currentChanged(self,a0):
        
        global cur_device
        global cur_device_uri
        
        cur_device_uri = self.DeviceList.currentItem().device_uri
        cur_device = devices[ cur_device_uri ]
        
        self.updateDevice()
        

    def updateDevice( self ): 
        self.update_called = True
        QApplication.setOverrideCursor( QCursor(Qt.WaitCursor) )
        self.setCaption( "%s - HP Device Manager" % cur_device.model_ui ) 
        log.debug( "Device URI=%s" % cur_device_uri )

        try:
            cur_device.ds = self.service.queryDevice( cur_device_uri, cur_device.device_state )
        except Error:
            cur_device.ds['device-state'] = device.DEVICE_STATE_NOT_FOUND
            
        cur_device.device_state = cur_device.ds.get( 'device-state', device.DEVICE_STATE_NOT_FOUND )
        
        global device_vars
        device_vars = { 'URI'        : cur_device_uri, 
                        'DEVICE_URI' : cur_device_uri, 
                        'SANE_URI'   : cur_device_uri.replace( 'hp:', 'hpaio:' ),
                        'PRINTER'    : cur_device.cups_printers[0],
                        'HOME'       : prop.home_dir,
                      } 
                      
        self.UpdateTabs()

        #print "DEVICE STATE = %d" % device_state
        
        if cur_device.device_state == device.DEVICE_STATE_JUST_FOUND: #  Just found
            # Remove (X)
            icon = self.createPixmap( cur_device, True, False )
            self.DeviceList.currentItem().setPixmap( icon )
            #cur_device.open()
        elif cur_device.device_state == device.DEVICE_STATE_NOT_FOUND: # Not found
            # Add (X)
            icon = self.createPixmap( cur_device, False, False )
            self.DeviceList.currentItem().setPixmap( icon )
                    
        #cur_device.device_state = device_state
        
        QApplication.restoreOverrideCursor()
        

    default_pics = { 'deskjet'    : 'default_deskjet.png',
                     'business'   : 'default_business_inkjet.png',
                     'psc'        : 'default_psc.png',
                     'laserjet'   : 'default_laserjet.png',
                     'officejet'  : 'default_officejet.png',
                     'photosmart' : 'default_photosmart.png',
                     'default'    : 'default_printer.png',
                    }
    
    
    def createPixmap( self, dev, avail=False, warning=False, ok=False ):
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
    
        if not avail:
            p.drawPixmap( 0, 0, self.error_pix )
            
        elif warning:
            p.drawPixmap( 0, 0, self.warning_pix )
            
        elif ok:
            p.drawPixmap( 0, 0, self.ok_pix )
                    
        p.end()
    
        return icon
    
    def refreshDeviceList( self, make_history ):
        log.debug( "Rescanning device list..." )
        global num_devices
        QApplication.setOverrideCursor( QCursor(Qt.WaitCursor) )
        self.DeviceList.clear()
        prev_devices = devices.copy()
        devices.clear()
        printer_list = cups.getPrinters()
        num_printers = len( printer_list )
        
        num_devices = 0
        
        if num_printers > 0:
            pb = QProgressBar( ) #self.statusBar() )
            pb.setTotalSteps( num_printers )
            self.statusBar().addWidget( pb )
            pb.show()

            first = True
            self.devices = {}
            
            printer_num = 0
            for printer in printer_list:
                
                pb.setProgress( printer_num )
                printer_num += 1
                qApp.processEvents(0)
                
                if not printer.device_uri.startswith( 'hp' ):
                    continue

                log.debug( utils.bold( "%s %s %s" % ( "*"*20, printer.device_uri, "*"*20 ) ) )

                try:
                    devices[printer.device_uri]
                except KeyError: 
                    
                    try:
                        d = DummyDevice( printer.device_uri )
                    except Error:
                        continue
                    else:
                        d.cups_printers.append( printer.name ) 
                        
                        prev_device = prev_devices.get( d.device_uri, None )
                        
                        if prev_device is not None:
                            prev_device_state = prev_device.device_state
                        else:
                            prev_device_state = device.DEVICE_STATE_NOT_FOUND
                        
                        #print "PREV DEVICE STATE = %d" % prev_device_state
                        
                        try:
                            d.ds = self.service.queryDevice( d.device_uri, prev_device_state, make_history )
                        except Error:
                            d.ds['device_state'] = device.DEVICE_STATE_NOT_FOUND
                            
                        device_state = d.ds.get( 'device-state', device.DEVICE_STATE_NOT_FOUND )
                        d.device_state = device_state
                        
                        icon = self.createPixmap( d, device_state in ( device.DEVICE_STATE_FOUND, \
                                                                       device.DEVICE_STATE_JUST_FOUND ), False )
                        
                        device_item = IconViewItem( self.DeviceList, d.model_ui, 
                                                    icon, d.device_uri )
                        
                        d.clean_type = int( d.ds.get( 'clean-type', 0 ) )
                        d.align_type = int( d.ds.get( 'align-type', 0 ) )
                        d.color_cal_type = int( d.ds.get( 'color-cal-type', 0 ) )
                        d.scan_type = int( d.ds.get( 'scan-type', 0 ) )
                        d.pcard_type = int( d.ds.get( 'pcard-type', 0 ) )
                        d.fax_type = int( d.ds.get( 'fax-type', 0 ) )
                        d.copy_type = int( d.ds.get( 'copy-type', 0 ) )
                        d.status_type = int( d.ds.get( 'status-type', 0 ) )

                        devices[ d.device_uri ] = d
        
                        num_devices += 1
                        
                else:
                    devices[printer.device_uri].cups_printers.append( printer.name ) 
                    

            pb.hide()
            self.statusBar().removeWidget( pb )
            
            self.DeviceList.setCurrentItem( self.DeviceList.firstItem() )
            self.DeviceList.adjustSize()

        self.DeviceList.updateGeometry()
        QApplication.restoreOverrideCursor()
        
    
    def activateItem( self, device_uri ):
        log.debug( "Activate device: %s" % device_uri )
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

    def UpdateTabs( self ):
        self.UpdateFunctionsTab()
        self.UpdateStatusTab()
        self.UpdateSuppliesTab()
        self.UpdateMaintTab()
        self.UpdateInfoTab()
            
    def UpdateFunctionsTab( self ):
        self.ToggleFunctionButtons( cur_device.device_state in \
            ( device.DEVICE_STATE_FOUND, device.DEVICE_STATE_JUST_FOUND ) )
            
    def ToggleFunctionButtons( self, toggle ):
        if toggle:
            self.PrintButton.setEnabled( True )
            self.ScanButton.setEnabled( cur_device.scan_type )
            self.PCardButton.setEnabled( cur_device.pcard_type )
            self.SendFaxButton.setEnabled( cur_device.fax_type )
            self.MakeCopiesButton.setEnabled( cur_device.copy_type )
        else:
            self.PrintButton.setEnabled( False )
            self.ScanButton.setEnabled( False )
            self.PCardButton.setEnabled( False )
            self.SendFaxButton.setEnabled( False )
            self.MakeCopiesButton.setEnabled( False )
        
    def UpdateStatusTab( self ):
        try:
            cur_device.hist = self.service.getHistory( cur_device_uri )
        except Error:
            log.error( "History query failed." )
        
        last_event = cur_device.hist[0]
        self.StatusHistoryList.clear()
        
        for x in cur_device.hist:
            QListViewItem( self.StatusHistoryList, 
                           time.strftime( "%a, %d %b %Y", x[:9] ),
                           time.strftime( "%H:%M:%S", x[:9] ),
                           x[10], str(x[9]), str(x[11]), x[12] )

        self.StatusText.setText( last_event[12] )
        self.StatusCode.setText( str( last_event[11] ) )

        self.StatusDate.setText( time.strftime( "%a, %d %b %Y", 
                                 last_event[:9] ) )

        self.StatusTime.setText( time.strftime( "%H:%M:%S", 
                                 last_event[:9] ) )

        self.StatusJobID.setText( str( last_event[9] ) )
        
        last_event_code = int( last_event[11] )
        self.CancelJobButton.setEnabled( False )
        
        if last_event_code == EVENT_DEVICE_NOT_FOUND:
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "error.png" ) ) )
        
        elif last_event_code in ( EVENT_PRINTER_PRINTING, EVENT_START_PRINT_JOB ): # Printing started
            self.StatusIcon.clear()
            self.CancelJobButton.setEnabled( True )
        
        elif last_event_code in ( EVENT_PRINTER_IDLE, # Printing ended or other job started
                                        EVENT_START_SCAN_JOB,
                                        EVENT_START_FAX_JOB,
                                        EVENT_START_COPY_JOB,
                                        EVENT_START_PCARD_JOB, ):
            
            self.CancelJobButton.setEnabled( False )
            self.StatusIcon.clear()
            icon = self.createPixmap( cur_device, True, False )
            self.DeviceList.currentItem().setPixmap( icon )
            
        elif last_event_code in ( EVENT_END_PRINT_JOB, # Printing ended or other job ended
                                        EVENT_END_SCAN_JOB,
                                        EVENT_END_FAX_JOB,
                                        EVENT_END_COPY_JOB,
                                        EVENT_END_PCARD_JOB, ):
            
            
            self.CancelJobButton.setEnabled( False )
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "ok.png" ) ) )
            icon = self.createPixmap( cur_device, True, False, False )
            self.DeviceList.currentItem().setPixmap( icon )

            
        elif last_event_code == EVENT_PRINTER_CANCELING: # Print canceled
            self.CancelJobButton.setEnabled( False )
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "warning.png" ) ) )
            icon = self.createPixmap( cur_device, True, True )
            self.DeviceList.currentItem().setPixmap( icon )
        
        elif EVENT_PRINTER_CANCELING < last_event_code <=  EVENT_PRINTER_PEN_CLEANING: # Print error
            self.CancelJobButton.setEnabled( True )
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "warning.png" ) ) )
            icon = self.createPixmap( cur_device, True, True )
            self.DeviceList.currentItem().setPixmap( icon )

        else: # Other error
            self.StatusIcon.setPixmap( QPixmap( os.path.join( prop.image_dir, "warning.png" ) ) )
            icon = self.createPixmap( cur_device, True, True )
            self.DeviceList.currentItem().setPixmap( icon )
        
    
    
    def UpdateSuppliesTab( self ):
        self.SuppliesList.clear()
        
        if cur_device.device_state in ( device.DEVICE_STATE_FOUND, device.DEVICE_STATE_JUST_FOUND ) and \
            cur_device.status_type > 0:
            
            s = cur_device.ds
            a = 1
            while True:
                
                try:
                    agent_type = int( s[ 'agent%d-type' % a ] )
                except KeyError:
                    break
                else:
                    agent_kind = int( s[ 'agent%d-kind' % a ] )
                    agent_ack = s[ 'agent%d-ack' % a ]
                    agent_dvc = int( s[ 'agent%d-dvc' % a ] )
                    agent_health = int( s[ 'agent%d-health' % a ] )
                    agent_hp_ink = s['agent%d-hp-ink' % a ]
                    agent_known = s[ 'agent%d-known' % a ]
                    agent_level = int( s[ 'agent%d-level' % a ] )
                    agent_level_trigger = int( s[ 'agent%d-level-trigger' % a ] )
                    agent_sku = s[ 'agent%d-sku' % a ]
                    agent_virgin = s[ 'agent%d-virgin' % a ]
                    agent_desc = s [ 'agent%d-desc' % a ]
                    agent_health_desc = s [ 'agent%d-health-desc' % a ]
                
                    if agent_health == status.AGENT_HEALTH_OK and \
                        agent_kind in ( status.AGENT_KIND_SUPPLY, status.AGENT_KIND_HEAD_AND_SUPPLY ):
                        
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
        self.ToggleMaintButtons( cur_device.device_state in \
            ( device.DEVICE_STATE_FOUND, device.DEVICE_STATE_JUST_FOUND ) )
            
            
    def ToggleMaintButtons( self, toggle ):
        if toggle:
            self.CleanPensButton.setEnabled( cur_device.clean_type )
            self.AlignPensButton.setEnabled( cur_device.align_type )
            self.ColorCalibrationButton.setEnabled( cur_device.color_cal_type )
            self.PrintTestPageButton.setEnabled( True )
        else:
            self.CleanPensButton.setEnabled( False )
            self.AlignPensButton.setEnabled( False )
            self.ColorCalibrationButton.setEnabled( False )
            self.PrintTestPageButton.setEnabled( False )

            
    def UpdateInfoTab( self ):
        self.DeviceURI.setText( cur_device.device_uri )
        self.Model.setText( cur_device.model )
        self.CUPSPrinters.setText( ','.join( cur_device.cups_printers ) )
        
        if cur_device.device_state in ( device.DEVICE_STATE_FOUND, device.DEVICE_STATE_JUST_FOUND ):
            self.AdvancedInfoButton.setEnabled( True )
            try:
                self.SerialNo.setText( cur_device.ds.get( 'serial-number', '' ) )
            except Error:
                log.error( "Unable to get serial number." )
                self.SerialNo.setText( "" )
        else:
            self.SerialNo.setText( "" )
            self.AdvancedInfoButton.setEnabled( False )
            
        
    def eventUI( self, event_code, event_type, 
                 error_string_short, error_string_long, 
                 retry_timeout, job_id, device_uri ):
        
        log.debug( "Event: code=%d type=%s string=%s timeout=%d id=%d uri=%s" % 
                 ( event_code, event_type,  error_string_short, retry_timeout, job_id, device_uri ) )
        
        if event_code == EVENT_UI_SHOW_TOOLBOX:
            self.rescan( True ) 
        
        elif self.activateItem( device_uri ):
            cur_device.job_id = job_id

            self.UpdateStatusTab()
            self.Tabs.setCurrentPage( 1 )
            


    def CancelJobButton_clicked( self ):
        self.service.cancelJob( cur_device.job_id, cur_device_uri )
        

    def settingsConfigure_activated(self, tab_to_show=0 ):
        dlg = SettingsDialog( self.cleaning_level, self )

        dlg.PopupCheckBox.setChecked( self.popup_alerts )
        dlg.EmailCheckBox.setChecked( self.email_alerts )
        dlg.EmailAddress.setText( self.email_address )
        dlg.SMTPServer.setText( self.smtp_server )
        
        dlg.PrintCommand.setText( self.cmd_print )
        dlg.ScanCommand.setText( self.cmd_scan )
        dlg.AccessPCardCommand.setText( self.cmd_pcard )
        dlg.SendFaxCommand.setText( self.cmd_fax )
        dlg.MakeCopiesCommand.setText( self.cmd_copy )
        
        dlg.TabWidget.setCurrentPage( tab_to_show )

        if dlg.exec_loop() == QDialog.Accepted:
                                  
            self.cmd_print = str( dlg.PrintCommand.text() )
            self.cmd_scan = str( dlg.ScanCommand.text() )
            self.cmd_pcard = str( dlg.AccessPCardCommand.text() )
            self.cmd_fax   = str( dlg.SendFaxCommand.text() )
            self.cmd_copy  = str( dlg.MakeCopiesCommand.text() )
            
            self.email_alerts = bool( dlg.EmailCheckBox.isChecked() )
            self.popup_alerts = bool( dlg.PopupCheckBox.isChecked() )
            self.email_address = str( dlg.EmailAddress.text() )
            self.smtp_server = str( dlg.SMTPServer.text() )
            
            self.cleaning_level = dlg.cleaning_level
            
            self.service.setAlerts( self.popup_alerts,
                                    self.email_alerts,
                                    self.email_address,
                                    self.smtp_server,
                                  )
            
            
            config = ConfigParser.ConfigParser()
            
            if os.path.exists( self.user_config ):
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
            config.set( "alerts", 'popup-alerts', self.popup_alerts )
            
            if not config.has_section( 'maint' ):
                config.add_section( 'maint' )
                
            config.set( "maint", 'cleaning-level', self.cleaning_level )

            fp = file( self.user_config, 'w' )
            config.write( fp )
            fp.close()

            
    
    def update_spinner( self ):
        pass
    
    def loadPlainPaper( self ):
        if LoadPaperForm( self ).exec_loop() == QDialog.Accepted:
            return True
        return False
        
    def enterAlignmentNumber( self, letter, hortvert, colors, line_count, choice_count ):
        dlg = AlignForm( self, letter, hortvert, colors, line_count, choice_count )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.value
        else:
            return False, 0
                            
    def enterPaperEdge( self, maximum ):
        dlg = PaperEdgeAlignForm( self )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.value
        else:
            return False, 0
    
    def colorAdj( self, line, maximum ):
        dlg = ColorAdjForm( self, line )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.value
        else:
            return False, 0
            
    def colorCal( self ):
        dlg = ColorCalForm( self )
        if dlg.exec_loop() == QDialog.Accepted:
            return True, dlg.value
        else:
            return False, 0

    def bothPensRequired( self ):
        BothPensRequiredForm( self ).exec_loop()
        
    def invalidPen( self ):
        InvalidPenConfigForm( self ).exec_loop()
        
    def photoPenRequired( self ):
        PhotoPenRequiredForm( self ).exec_loop()

    def aioUI1( self ):
        dlg = AlignType6Form1( self )
        if dlg.exec_loop() == QDialog.Accepted:
            return True,dlg.print_page # Next >
        else:
            return False,False #Printpage
        
        
    def aioUI2( self ):
        AlignType6Form2( self ).exec_loop()

    def AlignPensButton_clicked( self ):
        d = device.Device( self.hpiod_sock, cur_device_uri )
        d.open()
        state = False;
        
        align_type = cur_device.align_type
        
        if align_type == 1: # Auto
            state = maint.AlignType1( d, self.loadPlainPaper )

        elif align_type == 2: # 8xx
            state = maint.AlignType2( d, self.loadPlainPaper, self.enterAlignmentNumber,
                              self.bothPensRequired, self.update_spinner )

        elif align_type == 3: #9xx
            state = maint.AlignType3( d, self.loadPlainPaper, self.enterAlignmentNumber,
                              self.enterPaperEdge, self.update_spinner, align_type )

        elif align_type in [ 4, 5, 7 ]: # LIDIL 0.3.8, LIDIL 0.4.3, xBow VIP
            state = maint.AlignxBow( d, align_type, self.loadPlainPaper, self.enterAlignmentNumber, self.enterPaperEdge, self.invalidPen, self.colorAdj,self.update_spinner )

        elif align_type == 6: # xBow AiO
            state = maint.AlignType6( d, self.aioUI1, self.aioUI2, self.loadPlainPaper )

        elif align_type == 8: # 450
            state = maint.AlignType8( d, self.loadPlainPaper, self.enterAlignmentNumber,
                              self.update_spinner )

        elif align_type == 9: #9xx without edge alignment
            state = maint.AlignType3( d, self.loadPlainPaper, self.enterAlignmentNumber,
                              self.enterPaperEdge, self.update_spinner, align_type )                      
                                                            
        d.close()
        if state:
            SuccessForm( self ).exec_loop()
        
    
    def ColorCalibrationButton_clicked( self ):
        #color_cal_type = int( cur_device.ds.get( 'color-cal-type', 0 ) )
        color_cal_type = cur_device.color_cal_type
        state = False
        d = device.Device( self.hpiod_sock, cur_device_uri )
        d.open()

        if color_cal_type == 1: # 450
            state = maint.colorCalType1( d, self.loadPlainPaper, self.colorCal,
                                 self.photoPenRequired, update_spinner )
        
        d.close()        

        if state:
            SuccessForm( self ).exec_loop()

            
    def PrintTestPageButton_clicked( self ):
        d = device.Device( self.hpiod_sock, cur_device_uri )
        d.open()
    
        print_file = os.path.join( prop.home_dir, 'data', 'ps', 'testpage.ps.gz' )

        if self.loadPlainPaper():
            d.printParsedGzipPostscript( print_file )

        d.close()
            
        #SuccessForm( self ).exec_loop()
        

    def CleanPensButton_clicked( self ):
        d = device.Device( self.hpiod_sock, cur_device_uri )
        d.open()
        state = False
        
        clean_type = cur_device.clean_type
        log.debug( "Clean: Type=%d, Level=%d" % ( clean_type, self.cleaning_level ) )
        
        if clean_type == 1: # PCL
            if self.cleaning_level == 0:
                maint.cleanType1( d )
            elif self.cleaning_level == 1:
                maint.primeType1( d )
            elif self.cleaning_level == 2:
                maint.wipeAndSpitType1( d )
        
        elif clean_type == 2: # LIDIL
            if self.cleaning_level == 0:
                maint.cleanType2( d )
            elif self.cleaning_level == 1:
                maint.primeType2( d )
            elif self.cleaning_level == 2:
                maint.wipeAndSpitType2( d )
                
                
        elif clean_type == 3: # PCL alignment with Printout
            state = self.loadPlainPaper() 
            if state:
                if self.cleaning_level == 0:
                    maint.cleanType1( d )
                elif self.cleaning_level == 1:
                    maint.primeType1( d )
                elif self.cleaning_level == 2:
                    maint.wipeAndSpitType1( d )
            
                                               
        d.close()

        if state:
            SuccessForm( self ).exec_loop()
        

    def deviceRescanAction_activated( self ):
        self.deviceRescanAction.setEnabled( False )
        self.updateDevice()
        self.deviceRescanAction.setEnabled( True )
        
    def deviceRefreshAll_activated(self):
        self.rescan( True )

    def DeviceList_clicked(self,a0):
        if not self.update_called:
            self.updateDevice()
        self.update_called = False
        

    def AdvancedInfoButton_clicked( self ):
        AdvancedInfoForm( cur_device, self, None, 0, 1  ).exec_loop()
        
    def PrintButton_clicked(self):
        self.RunCommand( self.cmd_print )

    def ScanButton_clicked(self):
        self.RunCommand( self.cmd_scan )
        
    def PCardButton_clicked(self):
        self.RunCommand( self.cmd_pcard )
        
    def SendFaxButton_clicked(self):
        #self.RunCommand( self.cmd_fax )
        FailureForm( "Sorry, this feature is currently not implemented.", self ).exec_loop()
        
    def MakeCopiesButton_clicked(self):
        #self.RunCommand( self.cmd_copy )
        FailureForm( "Sorry, this feature is currently not implemented.", self ).exec_loop()
        
    def ConfigureFeaturesButton_clicked(self):
        self.settingsConfigure_activated( 3 )

    def RunCommand( self, cmd, macro_char='%' ):
        self.ToggleFunctionButtons( False )
        if len( cmd ) == 0:
            FailureForm( "Unable to run command. No command specified. Use <i>Configure...</i> to specify a command to run.", self ).exec_loop()
            log.error( "No command specified. Use settings to configure commands." )
        else:
            log.debug( cmd )
            cmd = ''.join( [ device_vars.get( x, x ) for x in cmd.split( macro_char ) ] )
            log.debug( cmd )
            
            path = cmd.split()[0]
            args = cmd.split()
            
            log.debug( path )
            log.debug( args )
            
            os.spawnvp( os.P_NOWAIT, path, args )
        self.UpdateFunctionsTab()

        
    def helpAbout(self):
        dlg = AboutDlg( self )
        dlg.VersionText.setText( prop.version )
        dlg.exec_loop()
