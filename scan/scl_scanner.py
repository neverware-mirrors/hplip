#!/usr/bin/env python
#
# $Revision: 1.5 $ 
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

class SCLScanner( Scanner ):

    def __init__( self, dev_obj=None, device_uri=None, printer_name=None ):
        self.scanner_type = 1
        Scanner.__init__( self, dev_obj, device_uri, printer_name )
        
        self.channel_id = self.device.checkOpenChannel( 'hp-scan' )
        self.reset()
        self.clearErrorStack()
        self.use_mfpdtf = False
        
        self.pixels_per_scan_line = self.device.inquireSCLDeviceParam( scl.INQUIRE_PIXELS_PER_SCAN_LINE )
        self.bytes_per_scan_line = self.device.inquireSCLDeviceParam( scl.INQUIRE_BYTES_PER_SCAN_LINE )
        self.pixels_per_inch = self.device.inquireSCLDeviceParam( scl.INQUIRE_DEVICE_PIXELS_PER_INCH )
        self.native_optical_res = self.device.inquireSCLDeviceParam( scl.INQUIRE_NATIVE_OPTICAL_RESOLUTION )
        self.num_scan_lines = self.device.inquireSCLDeviceParam( scl.INQUIRE_NUM_SCAN_LINES )
        
        log.debug( "Device params: (px/scanline=%d, bytes/scanline=%d, px/inch=%d, optical=%d, numlines=%d)" % 
                 ( self.pixels_per_scan_line, self.bytes_per_scan_line, self.pixels_per_inch, 
                   self.native_optical_res, self.num_scan_lines ) )
                   
        self.max_x_extent = self.getMaxXExtent()
        self.min_x_extent = self.getMinXExtent()
        self.max_y_extent = self.getMaxYExtent()
        self.min_y_extent = self.getMinXExtent()
        
        log.debug( "Max/min extents: (%d,%d) - (%d,%d)" % 
            (self.min_x_extent, self.min_y_extent, self.max_x_extent, self.max_y_extent ) )
    
        self.error_xlator = {   scl.ERROR_COMMAND_FORMAT_ERROR : SANE_STATUS_UNSUPPORTED,
                                scl.ERROR_UNRECOGNIZED_COMMAND : SANE_STATUS_UNSUPPORTED,
                                scl.ERROR_PARAMETER_ERROR : SANE_STATUS_UNSUPPORTED,
                                scl.ERROR_ILLEGAL_WINDOW : SANE_STATUS_UNSUPPORTED,
                                scl.ERROR_NO_MEMORY : SANE_STATUS_NO_MEM,
                                scl.ERROR_SCANNER_HEAD_LOCKED : SANE_STATUS_JAMMED,
                                scl.ERROR_CANCELLED : SANE_STATUS_CANCELLED,
                                scl.ERROR_PEN_DOOR_OPEN : SANE_STATUS_JAMMED,
                                scl.ERROR_ADF_PAPER_JAM : SANE_STATUS_JAMMED,
                                scl.ERROR_HOME_POSITION_MISSING : SANE_STATUS_JAMMED,
                                scl.ERROR_PAPER_NOT_LOADED : SANE_STATUS_NO_DOCS,
                                scl.ERROR_ORIGINAL_ON_GLASS : SANE_STATUS_JAMMED, 
                            }
                              
        self.status_xlator = {
                                scl.ADF_FEED_STATUS_OK : SANE_STATUS_GOOD,
                                scl.ADF_FEED_STATUS_BUSY : SANE_STATUS_GOOD,
                                scl.ADF_FEED_STATUS_PAPER_JAM : SANE_STATUS_JAMMED,
                                scl.ADF_FEED_STATUS_ORIGINAL_ON_GLASS : SANE_STATUS_JAMMED,
                                scl.ADF_FEED_STATUS_PORTRAIT_FEED : SANE_STATUS_UNSUPPORTED,
                            }
        
        self.getADFCapabilites()
    
    
    # Errors
    
    def clearErrorStack( self ):
        self.device.sendSCLCmd( *scl.CLEAR_ERRORS )

    def currentError( self ):
        if self.device.inquireSCLDeviceParam( scl.INQUIRE_CURRENT_ERROR_STACK ) > 0:
            value = self.device.inquireSCLDeviceParam( scl.INQUIRE_CURRENT_ERROR )
            return self.error_xlator( value, scl.SANE_STATUS_IO_ERROR )
        else:
            return SANE_STATUS_GOOD
    
            
    # Status

    def currentStatus( self ):
        value = self.device.inquireSCLDeviceParam( scl.INQUIRE_ADF_FEED_STATUS )
        return self.status_xlator.get( value, SANE_STATUS_GOOD )
    
    
        
    # Reset
    
    def reset( self ):
        self.device.sendSCLCmd( *scl.RESET )
        
        
    # ADF capabilities
    def getADFCapabilites( self ):
    
        self.flatbed = self.device.inquireSCLPseudoMaximum( scl.PSEUDO_FLATBED_Y_RESOLUTION )
        value = self.device.inquireSCLDeviceParam( scl.INQUIRE_ADF_CAPABILITY )
        
        #if value == 0:
        #    self.adf_mode = ADF_MODE_FLATBED
        #elif self.flatbed == 0:
        
        if value == 0:
            self.adf_mode = ADF_MODE_FLATBED
        else:
            self.adf_mode = ADF_MODE_ADF #ADF_MODE_AUTO | ADF_MODE_FLATBED | ADF_MODE_ADF
            
        #log.debug( "flatbed=%d, adf_mode=%d" % ( self.flatbed, self.adf_mode ) )
        print "Flatbed/ADF:"
        print self.flatbed
        print self.adf_mode
        
        
        
    
        
    # X Resolution
    
    def setXResolution( self, x ):
        self.device.sendSCLCmd( value=x, *scl.SET_X_RES )
        self.x_res = x
    
    def getXResolution( self ):
        self.x_res = self.device.inquireSCLMaximum( *scl.SET_X_RES )
        return self.x_res

    # X Extent
    
    def getMaxXExtent( self ):
        self.max_x_extent = self.device.inquireSCLMaximum( *scl.SET_X_EXTENT )
        return self.max_x_extent
        
    def getMinXExtent( self ):
        self.min_x_extent = self.device.inquireSCLMinimum( *scl.SET_X_EXTENT )
        return self.min_x_extent
        
    def getXExtent( self ):
        self.x_extent = self.device.inquireSCLPresent( *scl.SET_X_EXTENT )
        return self.x_extent
    
    def setXExtent( self, x ):
        if self.min_x_extent <= x <= self.max_x_extent:
            self.device.sendSCLCmd( value=x, *scl.SET_X_EXTENT )
        
    # X Pos
    
    def getXPos( self ):
        self.x_pos = self.device.inquireSCLPresent( *scl.SET_X_POS )
        return self.x_pos
        
    def setXPos( self, x ):
        if self.min_x_extent <= x <= self.max_x_extent:
            self.device.sendSCLCmd( value=x, *scl.SET_X_POS )
            self.x_pos = x
    
    # Y Resolution
    
    def setYResolution( self, y ):
        self.device.sendSCLCmd( value=y, *scl.SET_Y_RES )
        self.y_res = y
    
    def getYResolution( self ):
        self.y_res = self.device.inquireSCLMaximum( *scl.SET_Y_RES )
        return self.y_res

    # Y Extent
    
    def getMaxYExtent( self ):
        self.max_y_extent = self.device.inquireSCLMaximum( *scl.SET_Y_EXTENT )
        return self.max_y_extent
        
    def getMinYExtent( self ):
        self.min_y_extent = self.device.inquireSCLMinimum( *scl.SET_Y_EXTENT )
        return self.min_x_extent

    def getYExtent( self ):
        self.y_extent = self.device.inquireSCLPresent( *scl.SET_Y_EXTENT )
        return self.x_extent
    
    def setYExtent( self, y ):
        if self.min_y_extent <= y <= self.max_y_extent:
            self.device.sendSCLCmd( value=y, *scl.SET_Y_EXTENT )

    # Y Pos
    
    def getYPos( self ):
        self.y_pos = self.device.inquireSCLPresent( *scl.SET_Y_POS )
        return self.y_pos
        
    def setYPos( self, y ):
        if self.min_y_extent <= y <= self.max_y_extent:
            self.device.sendSCLCmd( value=y, *scl.SET_Y_POS )
            self.y_pos = y

    # Lock and unlock

    def lock( self ):
        self.device.sendSCLCmd( *scl.LOCK )
        
    def setLockTimeout( self, timeout=0 ):
        self.device.sendSCLCmd( value=timeout, *scl.LOCK_TIMEOUT )
    
    def unlock( self ):
        self.device.sendSCLCmd( *scl.UNLOCK )
        
    def getSessionID( self ):
        self.session_id = self.device.inquireSCLDeviceParam( scl.INQUIRE_SESSION_ID )
        return self.session_id
        
    # Data type
    
    def setDataTypeLineArt( self ):
        self.device.sendSCLCmd( *scl.SET_DATA_TYPE_LINEART )
    
    def setDataTypeColor( self ):
        self.device.sendSCLCmd( *scl.SET_DATA_TYPE_COLOR )
        
    def setDataTypeGrayscale( self ):
        self.device.sendSCLCmd( *scl.SET_DATA_TYPE_BW_GRAYSCALE )
    
    # Compression
    
    def setCompressionJPEG( self ):
        self.device.sendSCLCmd( *scl.SET_COMPRESS_JPEG )
        
    def setCompressionNone( self ):
        self.device.sendSCLCmd( *scl.SET_COMPRESS_NONE )
        
    def setCompressionPacked( self ):
        self.device.sendSCLCmd( *scl.SET_COMPRESS_PACKED )
    
    def setCompressionFactor( self, factor=50 ):
        self.device.sendSCLCmd( value=factor, *scl.SET_COMPRESS_FACTOR )

    # Data width
    
    def setDataWidth( self, bpp ):
        self.device.sendSCLCmd( value=bpp, *scl.SET_DATA_WIDTH )
    
    def setDataWidth1bit( self ):
        self.device.sendSCLCmd( *scl.SET_DATA_WIDTH_1BIT )

    def setDataWidth8bit( self ):
        self.device.sendSCLCmd( *scl.SET_DATA_WIDTH_8BIT )

    def setDataWidth16bit( self ):
        self.device.sendSCLCmd( *scl.SET_DATA_WIDTH_16BIT )

    def setDataWidth24bit( self ):
        self.device.sendSCLCmd( *scl.SET_DATA_WIDTH_24BIT )
    
    def setDataWidth36bit( self ):
        self.device.sendSCLCmd( *scl.SET_DATA_WIDTH_36BIT )

    # MFPDTF
    
    def setMFPDTF( self, b ):
        self.use_mfpdtf = b
        if b: b=2
        else: b=0
        self.device.sendSCLCmd( value=b, *scl.SET_MFPDTF )
    
        
    # Misc

    def setIntensityLevel( self, i ):
        if -127 <= i <= 127:
            self.device.sendSCLCmd( value=i, *scl.SET_INTENSITY_LEVEL )
        
    def lampTestOn( self ):
        self.device.sendSCLCmd( *scl.LIGHT_SOURCE_TEST_ON )
    
    def lampTestOff( self ):
        self.device.sendSCLCmd( *scl.LIGHT_SOURCE_TEST_OFF )
        
        
    # Document management
    
    def noDocs( self ):
        self.current_page = 0
        self.current_side = 0
        
        if self.before_scan:
            if self.adf_mode == ADF_MODE_ADF:
                return SANE_STATUS_NO_DOCS
                
        
        elif self.batch_scan:
            if self.end_of_data:
                self.no_docs_condition_pending = True
        
            return SANE_STATUS_NO_DOCS
            
        return SANE_STATUS_GOOD
    
            
    def unloadDoc( self ):
        self.device.sendSCLCmd(value=0, *scl.ADF_UNLOAD_DOCUMENT )
    
    def changeDocumentDuplexSide( self ):
        self.device.sendSCLCmd( value=scl.CHANGE_DOC_DUPLEX_SIDE, *scl.ADF_CHANGE_DOCUMENT )
    
    def changeDoc( self, doc_loaded ):
        if doc_loaded and self.before_scan and self.adf_mode != ADF_MODE_FLATBED:
            if self.duplex:
                self.device.sendSCLCmd( value=scl.CHANGE_DOC_DUPLEX, *scl.ADF_CHANGE_DOCUMENT )
            else:
                self.device.sendSCLCmd( value=scl.CHANGE_DOC_SIMPLEX, *scl.ADF_CHANGE_DOCUMENT )
    
        self.already_pre_adv_doc = True
        self.current_page += 1
        self.current_side = 1
    
        
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
                
                
            doc_loaded = self.device.inquireSCLDeviceParam( scl.INQUIRE_ADF_DOCUMENT_LOADED )
                
            if self.current_side == 1:
                
                if self.duplex:
                    self.changeDocumentDuplexSide()
                    self.already_pre_adv_doc = True
                    self.current_side = 2
                    
                elif self.unload_after_scan and not self.before_scan:
                    self.unloadDoc()
                    
                    if not doc_loaded:
                        result = self.noDocs()
                        raise Error(0)

                    
                elif doc_loaded:
                    self.changeDoc( doc_loaded )
                    
                else:
                    self.unloadDoc()
                    result = self.noDocs()
                    raise Error(0)
                    
                    
                
            elif self.current_side == 2:
                self.changeDocumentDuplexSide()
                
                if doc_loaded:
                    self.changeDoc( doc_loaded )
                    
                self.unloadDoc()
                result = self.noDocs()
                raise Error(0)
                
                            
            if not self.before_scan and not self.current_page:
                result = SANE_STATUS_NO_DOCS
                raise Error(0)
                    
    
        except Error:
            if result != SANE_STATUS_GOOD:
                self.already_post_adv_doc = False
                self.already_pre_adv_doc = False
                self.current_page = 0
                self.current_side = 0
        
        return result   

        
    

    # Scan

    def startScan( self ):
        log.debug( "*** SCLScanner.startScan()" )
        self.device.sendSCLCmd( *scl.ADF_START_SCAN )
      
    def isDocumentLoaded( self ):
        return self.device.inquireSCLDeviceParam( scl.INQUIRE_ADF_DOCUMENT_LOADED )

    def unloadDocument( self ):
        raise NotImplemented
        
    def changeDocument( self ):
        raise NotImplemented
        
    def noDocumentsCondition( self ):
        raise NotImplemented

    def openScanChannel( self ):
        log.debug( "*** SCLScanner.openScanChannel()" )
        self.channel_id = self.device.checkOpenChannel( 'HP-SCAN' )

    def reserveScanner( self ):
        log.debug( "*** SCLScanner.reserveScanner()" )
        #pass # todo check sessionid
        
    def unreserveScanner( self ):
        #raise NotImplemented
        #pass
        log.debug( "*** SCLScanner.unreserveScanner()" )

    def resetScanner( self ):
        log.debug( "*** SCLScanner.resetScanner()" )
        self.reset()
