#!/usr/bin/env python
#
# $Revision: 1.3 $ 
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
from base import device, pml, mfpdtf
from scan import scl
from scanner import *


class PMLScanner(Scanner):

    def __init__( self, dev_obj=None, device_uri=None, printer_name=None ):
        self.scanner_type = 2
        Scanner.__init__( self, dev_obj, device_uri, printer_name )
        
        self.device.setPML( pml.OID_SCAN_ABC_THRESHOLDS, [ 0xe6, 0x00 ] )
        self.device.setPML( pml.OID_UPLOAD_TIMEOUT, 45 )
        self.device.setPML( pml.OID_SCAN_UPLOAD_ERROR, 0 )
        self.device.setPML( pml.OID_SCAN_SHARPENING_COEFFICIENT, 0x37 )
        self.device.setPML( pml.OID_SCAN_NEUTRAL_CLIP_THRESHOLDS, [ 0xFA, 0x05 ] )
        
        self.getScanResolutions()
        self.upload_state = 0
        self.already_restarted = False
        self.start_next_batch_early = True
        self.end_of_data = False
        
        self.error_xlator = {   
                                pml.UPLOAD_ERROR_SCANNER_JAM : SANE_STATUS_JAMMED,
                                pml.UPLOAD_ERROR_MLC_CHANNEL_CLOSED : SANE_STATUS_CANCELLED,
                                pml.UPLOAD_ERROR_STOPPED_BY_HOST : SANE_STATUS_CANCELLED,
                                pml.UPLOAD_ERROR_STOP_KEY_PRESSED : SANE_STATUS_CANCELLED,
                                pml.UPLOAD_ERROR_NO_DOC_IN_ADF : SANE_STATUS_NO_DOCS,
                                pml.UPLOAD_ERROR_COVER_OPEN : SANE_STATUS_COVER_OPEN,
                                pml.UPLOAD_ERROR_DOC_LOADED : SANE_STATUS_NO_DOCS,
                                pml.UPLOAD_ERROR_DEVICE_BUSY : SANE_STATUS_DEVICE_BUSY,
                            }
        
        self.getADFCapabilites()
    
    # Errors
    
    def currentError( self ):
        data, data_type, error_code = self.device.getPML( pml.OID_SCAN_UPLOAD_ERROR )    
        return self.error_xlator.get( data, SANE_STATUS_GOOD )

    # Status

    def currentStatus( self ):
        data, data_type, error_code = self.device.getPML( pml.OID_SCANNER_STATUS )    
        if data & pml.SCANNER_STATUS_FEEDER_JAM:
            return SANE_STATUS_JAMMED
        elif data & pml.SCANNER_STATUS_FEEDER_OPEN:
            return SANE_STATUS_COVER_OPEN
        elif data & pml.SCANNER_STATUS_FEEDER_EMPTY:
            if self.adf_mode == ADF_MODE_ADF and self.before_scan:
                return SANE_STATUS_GOOD
            else:
                return SANE_STATUS_NO_DOCS
        elif data & pml.SCANNER_STATUS_INVALID_MEDIA_SIZE:
            return SANE_STATUS_INVAL
        elif data:
            return SANE_STATUS_IO_ERROR
        else:
            return SANE_STATUS_GOOD
            

    # ADF capabilities
    def getADFCapabilites( self ):
        pass

    # Data type
    
    def setDataTypeLineArt( self ):
        self.device.setPML( pml.OID_SCAN_PIXEL_DATA_TYPE, pml.DATA_TYPE_LINEART )
    
    def setDataTypeColor( self ):
        self.device.setPML( pml.OID_SCAN_PIXEL_DATA_TYPE, pml.DATA_TYPE_COLOR )
        
    def setDataTypeGrayscale( self ):
        self.device.setPML( pml.OID_SCAN_PIXEL_DATA_TYPE, pml.DATA_TYPE_GRAYSCALE )
            
    # Resolution and resolution range
        
    def getScanResolutions( self ):
        scan_res_pat = re.compile( r"\((\d+)\)x\((\d+)\)*", re.IGNORECASE )
        data, data_type, error_code = self.device.getPML( pml.OID_SCAN_RESOLUTION_RANGE )
        self.scan_res = []
        for xy in scan_res_pat.findall( data ):
            self.scan_res.append( ( int(xy[0]), int(xy[1]) ) )
        log.debug( "Scan resolutions: %s" % self.scan_res )
        return self.scan_res
    
    def setXYResolution( self, x, y ):  # dpi
        # TODO: Make sure valid
        value = struct.pack( ">II", x<<16, y<<16 )
        value = [ ord(x) for x in value ]
        self.device.setPML( pml.OID_SCAN_RESOLUTION, value )

    # Compression

    def setCompressionJPEG( self ):
        self.device.setPML( pml.OID_SCAN_COMPRESSION, pml.SCAN_COMPRESSION_JPEG )
        
    def setCompressionNone( self ):
        self.device.setPML( pml.OID_SCAN_COMPRESSION, pml.SCAN_COMPRESSION_NONE )
        
    #def setCompressionPacked( self ):
    
    def setCompressionFactor( self, factor=50 ):
        self.device.setPML( pml.OID_SCAN_COMPRESSION_FACTOR, factor ) 

    
    def getUploadState( self ):
        self.upload_state, data_type, error_code = self.device.getPML( pml.OID_SCAN_UPLOAD )
    
    # Scan
    
            
            
    def reserveScanner( self ):
        pass # TODO: SCAN TOKEN
        #if 0:
        #    RESERVE_TOKEN = [ 0, 1, 0, 1, 0, 1 ,0 ,1, 0, 1, 0, 1, 0, 1, 0, 1 ]
        #    self.device.setPML( pml.OID_SCAN_TOKEN, RESERVE_TOKEN ) 
        
    def unreserveScanner( self ):
        pass
        #if 0:
        #    RESET_TOKEN = [ 0, 0, 0, 0, 0, 0 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0 ]
        #    self.device.setPML( pml.OID_SCAN_TOKEN, RESET_TOKEN ) 
        
        
    def checkScannerReadyAfterStart( self ):
        log.debug( "Waiting for upload active state..." )
        t1 = time.time() + 30
        
        while True:
            self.getUploadState()
            log.debug( "Scan upload state = %d" % self.upload_state )
            
            if self.upload_state == pml.UPLOAD_STATE_ACTIVE: 
                break
            #elif data in ( pml.UPLOAD_STATE_ABORTED, pml.UPLOAD_STATE_DONE ): 
            #    self.device.setPML( pml.OID_SCAN_UPLOAD_ERROR, 0 )
            #    self.device.setPML( pml.OID_SCAN_UPLOAD, pml.UPLOAD_STATE_IDLE )
            #    self.device.setPML( pml.OID_SCAN_UPLOAD, pml.UPLOAD_STATE_START )
                
            
            time.sleep(0.5)
            
            if time.time() > t1:
                raise Error( ERROR_INTERNAL )

                
    def startScan( self ):
        self.getUploadState()
        
        if self.upload_state == pml.UPLOAD_STATE_IDLE or not self.already_restarted:
            self.device.setPML( pml.OID_SCAN_UPLOAD, pml.UPLOAD_STATE_START )  
        
        self.already_restarted = False
    
    def isDocumentLoaded( self ):
        raise NotImplemented

    def unloadDocument( self ):
        raise NotImplemented
        
    def changeDocument( self ):
        raise NotImplemented
        
    def noDocumentsCondition( self ):
        raise NotImplemented
            
    def advanceDocument( self ):
        result = SANE_STATUS_GOOD
        try:
        
            if self.before_scan:
                self.already_post_adv_doc = False
                result = self.currentStatus()
                if result != SANE_STATUS_GOOD or self.already_pre_adv_doc:
                    raise Error(0)
                
                self.already_pre_adv_doc = True
                        
            else:
                if self.already_post_adv_doc:
                    raise Error(0)
                
                self.already_pre_adv_doc = False
                self.already_post_adv_doc = True
                
            if self.before_scan:
                self.current_page += 1
                self.current_side = 1
                
            elif self.current_side > 0:
                self.getUploadState()
                
                if self.upload_state == pml.UPDATE_STATE_IDLE:
                    self.current_page = 0
                    self.current_side = 0
                    
                    if self.batch_scan:
                        if self.end_of_data:
                            self.no_docs_condition_pending = True
                    result = SANE_STATUS_NO_DOCS
                    raise Error(0)
                    
            if not self.before_scan and not self.end_of_data:
                result = SANE_STATUS_NO_DOCS
        
        except Error:
            if result != SANE_STATUS_GOOD:
                self.already_post_adv_doc = False
                self.already_pre_adv_doc = False
                self.current_page = 0
                self.current_side = 0
        
        return result   
            
                
    
    def scanCallback( self ): # Return True to complete scan
        self.getUploadState()
        
        if self.scan_done or ( self.upload_state == pml.UPLOAD_STATE_ACTIVE and not self.end_of_data ):
            return self.scan_done
        
        if self.upload_state == pml.UPLOAD_STATE_NEWPAGE:
            if not self.batch_scan:
                self.resetScanner()
            
            elif self.start_next_batch_early:
                self.device.setPML( pml.OID_SCAN_UPLOAD, pml.UPLOAD_STATE_START )    
                self.already_restarted = True
        
        self.scan_done = True
        
        return self.scan_done
    
    # SANE
    def sane_read( self ):
        log.debug( "(PML) sane_read" )
        if self.use_mfpdtf:
            self.end_of_data = mfpdtf.readChannelToStream( self.device, self.channel_id, self.stream, True, self.scanCallback )
        else:
            pass # TODO

    def scanToFile( self, file_name ):
        return Scanner.scanToFile( self, file_name, self.scanCallback )
    
    def scanToBuffer( self ):
        return Scanner.scanToBuffer( self, self.scanCallback )

    def resetScanner( self ):
        self.device.setPML( pml.OID_SCAN_UPLOAD, pml.UPLOAD_STATE_IDLE )
    
    #def close( self ):
        # Reset scan token
        #self.device.setPML( pml.OID_SCAN_UPLOAD, pml.UPLOAD_STATE_IDLE )
        
        #if 0:
        #    RESET_TOKEN = [ 0, 0, 0, 0, 0, 0 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0 ]
        #    self.device.setPML( pml.OID_SCAN_TOKEN, RESET_TOKEN ) 
        
        #Scanner.close( self )
        

    # Document management
    
    #def advanceDocument( self ):
