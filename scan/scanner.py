#!/usr/bin/env python
#
# $Revision: 1.7 $ 
# $Date: 2004/11/17 21:41:20 $
# $Author: dwelch $
#
# (c) Copyright 2003-2004 Hewlett-Packard Development Company, L.P.
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
import re
import struct
import time

# Local
from base.g import *
from base.codes import *
from base import device, pml, mfpdtf2
from scan import scl

# SANE error codes from sane.h

SANE_STATUS_GOOD = 0           
SANE_STATUS_UNSUPPORTED = 1
SANE_STATUS_CANCELLED = 2   
SANE_STATUS_DEVICE_BUSY = 3 
SANE_STATUS_INVAL = 4       
SANE_STATUS_EOF = 5
SANE_STATUS_JAMMED = 6      
SANE_STATUS_NO_DOCS = 7 
SANE_STATUS_COVER_OPEN = 8  
SANE_STATUS_IO_ERROR = 9    
SANE_STATUS_NO_MEM = 10     
SANE_STATUS_ACCESS_DENIED = 11

# ADF modes
ADF_MODE_AUTO      = 0x01
ADF_MODE_FLATBED   = 0x02
ADF_MODE_ADF       = 0x04

class Scanner:
    
    def __init__( self, dev_obj=None, device_uri=None, printer_name=None ):
        
        if dev_obj is None:
            self.device = device.Device( None, device_uri, printer_name )
            self.device.open()
            self.close_device = True
        else:
            self.device = dev_obj
            self.close_device = False

        self.max_x_extent = 0
        self.min_x_extent = 0
        self.x_extent = 0
        self.x_res = 0
        self.x_pos = 0
        self.max_y_extent = 0
        self.min_y_extent = 0
        self.y_extent = 0
        self.y_res = 0
        self.y_pos = 0
        self.channel_id = 0
        self.use_mfpdtf = True
        
        self.current_page = 0
        self.current_side = 0
        self.stream = None
        self.adf_mode = ADF_MODE_AUTO
        self.unload_after_scan = False
        self.no_docs_condition_pending = False
        
        self.adf_supports_duplex = False
        data, data_type, error_code  = self.device.getPML( pml.OID_DEVICE_SUPPORTED_FUNCTIONS )
        
        #log.debug( '%s,0x%x' % ( repr(data), error_code ) )
        
        if data & pml.DEVICE_SUPPORTED_FUNCTIONS_SCAN_DUPLEX:
            self.adf_supports_duplex = True

            
    # Private
    def scanToFile( self, file_name, callback=None ):
        
        log.debug( "*** Scanner.scanToFile()" )
        num_bytes = 0
        self.stream = file( file_name, 'w' )
        self.sane_init()
        self.sane_start()
        
        while not self.end_of_data:
            num_bytes += self.sane_read()
            
        self.sane_close()
        
        self.stream.close()
        return num_bytes
    
    # Private
    def scanToBuffer( self ):
        import cStringIO
        self.stream = cStringIO.cStringIO()
        self.sane_start()
        
        while not self.end_of_data:
            self.sane_read()
        
        self.sane_close()
        
        return self.stream.getvalue()

    # SANE
    def sane_init( self ):
        log.debug( "*** Scanner.sane_init()" )
        #if self.use_mfpdtf:
        self.mfpdtf = mfpdtf2.MFPDTF( self.device, self.channel_id, self.stream )
        #else:
        #    self.stream = ''
            
    # SANE
    def sane_start( self ):
        log.debug( "*** Scanner.sane_start()" )
        if self.no_docs_condition_pending:
                self.no_docs_condition_pending = False
                #state = STATE_END
                return
            
        self.no_docs_condition_pending = False
        self.already_post_adv_doc = False
        self.already_pre_adv_doc = False
        self.batch_scan = False
        self.end_of_data = False

        self.before_scan = True
        self.openScanChannel()
        self.reserveScanner()
        self.checkScannerReadyBeforeStart()
        self.startScan()
        self.checkScannerReadyAfterStart()
        #self.advanceDocument()
        self.before_scan = False
        
    # SANE
    def sane_read( self, maxlen=8192 ):
        log.debug( "*** Scanner.sane_read()" )
        if self.use_mfpdtf:
            #self.end_of_data = mfpdtf.readChannelToStream( self.device, self.channel_id, self.stream, True, None )
            num_bytes, self.end_of_data = self.mfpdtf.read()
        
            #if len( data ):
            #    self.stream.write( self.mfpdtf.read( maxlen ) )
            #    return SANE_STATUS_GOOD
            #else:
            if self.end_of_data:
                return SANE_STATUS_EOF
        
        else:
            pass # TODO
            
        return num_bytes
            
        
    # SANE
    def sane_cancel( self ):
        pass
        
        
    if 0:
        def scan( self, stream ):
            STATE_START, STATE_ADV_DOC, STATE_SCAN_DONE, STATE_READ_MFPDTF_SCAN_DATA, STATE_READ_RAW_SCAN_DATA, STATE_END = range(6)
            state = STATE_START
            num_bytes = 0
            
            while state != STATE_END:
                
                if state == STATE_START:
                    
                    #self.before_scan = True
                    
                    if self.no_docs_condition_pending:
                        self.no_docs_condition_pending = False
                        state = STATE_END
                    
                    self.no_docs_condition_pending = False
                    self.already_post_adv_doc = False
                    self.already_pre_adv_doc = False
                    self.batch_scan = False
                    self.end_of_data = False
    
                    self.openScanChannel()
                    self.reserveScanner()
                    self.checkScannerReadyBeforeStart()
                    self.startScan()
                    self.checkScannerReadyAfterStart()
                    
                    state = STATE_ADV_DOC
                    
                    
                elif state == STATE_ADV_DOC:
                    
                    self.before_scan = True
                    
                    self.advanceDocument()
                    
                    if self.use_mfpdtf:
                        state = STATE_READ_MFPDTF_SCAN_DATA
                    else:
                        state = STATE_READ_RAW_SCAN_DATA
                    
                    self.before_scan = False
    
                    
                elif state == STATE_READ_MFPDTF_SCAN_DATA:
                    num_bytes = mfpdtf.readChannelToStream( self.device, self.channel_id, stream, callback )
                    
                    state = STATE_ADV_DOC
                    
                elif state == STATE_READ_RAW_SCAN_DATA:
                    num_bytes = self.device.readChannelToStream( self.channel_id, stream )
                    
                    state = STATE_ADV_DOC
    
                    
                elif state == STATE_SCAN_DONE:
                
                    self.unreserveScanner()
                    self.resetScanner()
                    
                    state = STATE_END
                
                
    # SANE
    def sane_close( self ):    
        log.debug( "*** Scanner.sane_close()" )
        self.unreserveScanner()
        self.resetScanner()

    def close( self ):
        if self.close_device:
            self.device.close()
   


    def isDocumentLoaded( self ):
        raise NotImplemented
    
    def unloadDocument( self ):
        raise NotImplemented
        
    def changeDocument( self ):
        raise NotImplemented
        
    def noDocumentsCondition( self ):
        raise NotImplemented
        
    def openScanChannel( self ):
        self.channel_id = self.device.checkOpenChannel( 'hp-scan' )

    def reserveScanner( self ):
        raise NotImplemented
        
    def unreserveScanner( self ):
        raise NotImplemented
        
    def checkScannerReadyBeforeStart( self ):
        pass
        
    def checkScannerReadyAfterStart( self ):
        pass

    def startScan( self ):
        raise NotImplemented

    def resetScanner( self ):
        #self.reset()
        raise NotImplemented
    
    
 

