#!/usr/bin/env python
#
# $Revision: 1.5 $ 
# $Date: 2004/11/17 21:36:01 $
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
import struct
import cStringIO

# Local
from g import *
from codes import *
    
# Page flags
NEW_PAGE =            0x01
END_PAGE  =           0x02
NEW_DOCUMENT =        0x04
END_DOCUMENT =        0x08
END_STREAM  =         0x10
RESERVED_20 =         0x20
RESERVED_40 =         0x40
RESERVED_80 =         0x80

MFPDTF_RASTER_BITMAP  = 0
MFPDTF_RASTER_GRAYMAP = 1
MFPDTF_RASTER_MH      = 2
MFPDTF_RASTER_MR      = 3
MFPDTF_RASTER_MMR     = 4
MFPDTF_RASTER_RGB     = 5
MFPDTF_RASTER_YCC411  = 6
MFPDTF_RASTER_JPEG    = 7
MFPDTF_RASTER_PCL     = 8
MFPDTF_RASTER_NOT     = 9


DT_UNKNOWN       = 0
DT_FAX_IMAGES    = 1
DT_SCANNED_IMAGES= 2
DT_DIAL_STRINGS  = 3
DT_DEMO_PAGES    = 4
DT_SPEED_DIALS   = 5
DT_FAX_LOGS      = 6
DT_CFG_PARMS     = 7
DT_LANG_STRS     = 8
DT_JUNK_FAX_CSIDS= 9  
DT_REPORT_STRS   = 10  
DT_FONTS         = 11
DT_TTI_BITMAP    = 12
DT_COUNTERS      = 13
DT_DEF_PARMS     = 14  
DT_SCAN_OPTIONS  = 15
DT_FW_JOB_TABLE  = 17

RT_START_PAGE = 0
RT_RASTER = 1
RT_END_PAGE = 2

FIXED_HEADER_SIZE = 8
IMAGE_VARIANT_HEADER_SIZE = 10
SOP_RECORD_SIZE = 35
RASTER_RECORD_SIZE = 3
EOP_RECORD_SIZE = 11
RECORD_TYPE_SIZE = 1

PAGE_FLAG_NEW_PAGE = 0x01
PAGE_FLAG_END_PAGE = 0x02
PAGE_FLAG_NEW_DOC = 0x04
PAGE_FLAG_END_DOC = 0x08
PAGE_FLAG_END_STREAM = 0x10

STATE_READ_DATA, STATE_END, STATE_FIXED_HEADER, \
STATE_VARIANT_HEADER, STATE_RECORD, STATE_ERROR = range(6)

class MFPDTF:
    
    
    def __init__( self, device, channel_id, stream ):
        #self.buffer = ''
        self.buffer = cStringIO.StringIO()
        self.device = device
        self.channel_id = channel_id
        self.state = STATE_READ_DATA
        self.stream = stream # output stream
        self.block_remaining = 0
        self.header_remaining = 0
        #self.data_written = 0
        self.data_remaining = 0
        
        self.state_table = { STATE_ERROR : self._errorState,
                             STATE_FIXED_HEADER : self._fixedHeaderState,
                             STATE_READ_DATA : self._readDataState,
                             STATE_RECORD : self._dataRecordState,
                             STATE_VARIANT_HEADER : self._variantHeaderState,
                           }
                           
        self.state_str = {   STATE_ERROR : "ERROR",
                             STATE_FIXED_HEADER : "FIXED HEADER",
                             STATE_READ_DATA : "READ DATA",
                             STATE_RECORD : "DATA RECORD",
                             STATE_VARIANT_HEADER : "VARIANT HEADER",
                           }
                           
        self.record_table = { RT_START_PAGE : self._startPageRecord,
                              RT_RASTER : self._rasterDataRecord,
                              RT_END_PAGE : self._endPageRecord,
                            }
        
        self.variant_table = { DT_FAX_IMAGES : self._faxImageVariant,
                               DT_SCANNED_IMAGES : self._scanImageVariant,
                             }
    
    
    def write( self ):
        pass

    # Assumptions:
    # 1. Always read and process 1 full block (empty the buffer)
    # 2. The device always writes a full block on each read
    # 3. Blocks always start with fixed headers 
    # 4. Blocks can contain multiple data records
    # 5. Reads will generally only return <= 8K
    # 6. Any reduction in delievered buffer lengths to SANE
    #    will be done by the caller. 
    # 7. If the initial read did not read the whole block,
    #    read until it does
    
    def read( self ): 
        self.end_scan = False
        self.block_remaining = 0
        self.header_remaining = 0
        self.buffer_remaining = 0
        self.data_remaining = 0
        self.num_bytes = 0
        self.state = STATE_READ_DATA
        self.next_state = STATE_FIXED_HEADER
        
        while self.state != STATE_END:
            
            if self.end_scan:
                self.state = STATE_END
                break
            
            #if self.block_remaining > 0 and len( self.buffer ) == 0:
            #    self.next_state = self.state
            #    self.state = STATE_READ_DATA
                
            log.debug( "**** State: %s ****" % self.state_str[ self.state ] )
            
            log.debug( "Block/header: buffer=%d(0x%x),block=%d(0x%x),header=%d(0x%x)" % 
                     ( self.buffer_remaining, self.buffer_remaining, self.block_remaining, 
                       self.block_remaining, self.header_remaining, self.header_remaining ) )

            self.state_table.get( self.state, self._errorState )()
            
            log.debug( "Block/header: buffer=%d(0x%x),block=%d(0x%x),header=%d(0x%x)" % 
                     ( self.buffer_remaining, self.buffer_remaining, self.block_remaining, 
                       self.block_remaining, self.header_remaining, self.header_remaining ) )
        
        assert self.block_remaining == 0
        assert self.buffer_remaining == 0
        
        return self.num_bytes, self.end_scan
        
        
    def _readDataState( self ):
        fields, buffer = self.device.readChannel( self.channel_id )
        self.buffer.reset()
        self.buffer.truncate()
        self.buffer.write( buffer )
        self.buffer.reset()
        self.buffer_remaining = len( buffer )
        log.debug( "Read Data: buffer=%d(0x%x)"  % ( self.buffer_remaining, self.buffer_remaining ) )
        
        if self.buffer_remaining == 0:
            log.debug( "Zero read -> EOS." )
            self.end_scan = True
            return
    
        #if self.callback is not None:
        #    self.end_scan = self.callback()
        
        self.state = self.next_state

            
    #
    # FIXED HEADER 
    #
        

    def _fixedHeaderState( self ):
        block_len, header_len, self.data_type, self.page_flags = struct.unpack( "<IHBB", self.buffer.read( FIXED_HEADER_SIZE ) )
        self.page_flags &= 0x1f
        
        if block_len != self.buffer_remaining:
            log.warn( "Block/buffer size mismatch (%d/%d)" % ( block_len, self.buffer_remaining ) )
        
        if block_len > self.buffer_remaining:
            log.warn( "Block length exceeds read buffer length. Additional read(s) required." )
        
        self.buffer_remaining -= FIXED_HEADER_SIZE
        self.block_remaining = block_len - FIXED_HEADER_SIZE
        self.header_remaining = header_len - FIXED_HEADER_SIZE
        
        log.debug( "Fixed header: buffer=%d(0x%x), blocklen=%d(0x%x), headerlen=%d(0x%x), datatype=0x%x, pageflags=0x%x" % 
            ( self.buffer_remaining, self.buffer_remaining, block_len, block_len, header_len, header_len, self.data_type, self.page_flags ) )
        
        if self.page_flags & PAGE_FLAG_END_STREAM:
            log.debug( "EOS Page Flag -> EOS" )
            #self.end_scan = True
            #return
        
        if self.header_remaining > 0:
            self.state = STATE_VARIANT_HEADER
        else:
            self.state = STATE_RECORD
        

    #
    # VARIANT HEADER
    #
    
    def _faxImageVariant( self ):
        log.error( "Fax type not supported" )
        self.state = STATE_ERROR
    

    def _scanImageVariant( self ):
        major_ver, minor_ver, src_pages, copies_per_page, zoom, jpeg_q_factor = \
                struct.unpack( "<BBHHHH", self.buffer.read( IMAGE_VARIANT_HEADER_SIZE ) )
        
        self.buffer_remaining -= IMAGE_VARIANT_HEADER_SIZE
        self.block_remaining -= IMAGE_VARIANT_HEADER_SIZE
        self.header_remaining -= IMAGE_VARIANT_HEADER_SIZE
        
        log.debug( "Variant image header: (major/minor=%d/%d, src_pages=%d, copies_per_page=%d, zoom=%d, jpeg_q_factor=%d" % 
            ( major_ver, minor_ver, src_pages, copies_per_page, zoom, jpeg_q_factor ) )
        
                    
    
    def _variantHeaderState( self ):
        self.variant_table.get( self.data_type, self._errorState )()

        if self.header_remaining > 0:
            log.error( "Header size error." )
            self.state = STATE_ERROR
          
        elif self.block_remaining == 0:
            self.state = STATE_FIXED_HEADER

        else:
            self.state = STATE_RECORD
        
    
    # 
    # DATA RECORD
    #
    
    def _startPageRecord( self ): # ID=0
        encoding, page_num, black_ppr, black_bpp, black_rpp, black_hort_dpi, \
        black_vert_dpi, cmy_ppr, cmy_bpp, cmy_rpp, cmy_hort_dpi, cmy_vert_dpi = \
            struct.unpack( "<BHHHIIIHHIII", self.buffer.read( SOP_RECORD_SIZE ) )

        self.buffer_remaining -= SOP_RECORD_SIZE
        self.block_remaining -= SOP_RECORD_SIZE

        log.debug( "*** SOP *** ( encoding=0x%x, page=%d )" % ( encoding, page_num ) )
        
        
    
    def _rasterDataRecord( self ): # ID=1
        unused, data_size = struct.unpack( "<BH", self.buffer.read( RASTER_RECORD_SIZE ) )
        
        log.debug( "*** RASTER *** ( data size=%d(0x%x) )" % ( data_size, data_size ) )
        
        self.block_remaining -= RASTER_RECORD_SIZE
        self.buffer_remaining -= RASTER_RECORD_SIZE
        
        assert self.block_remaining == self.buffer_remaining
        
        self.stream.write( self.buffer.read( self.block_remaining ) )
        self.num_bytes += self.block_remaining
        
        self.buffer.reset()
        self.buffer.truncate()
        
        self.block_remaining = 0
        self.buffer_remaining = 0
        
        #bytes_written = self.buffer_remaining - self.block_remaining 
        #log.debug( "Wrote %d(0x%x) bytes" % ( bytes_written, bytes_written ) )
        
        #assert bytes_written == data_size
        #self.buffer = ''    
    

    def _endPageRecord( self ): # ID=2
        unused1, unused2, unused3, black_rows, cmy_rows = \
            struct.unpack( "<BBBII", self.buffer.read( EOP_RECORD_SIZE ) )

        self.block_remaining -= EOP_RECORD_SIZE
        self.buffer_remaining -= EOP_RECORD_SIZE
        
        log.debug( "*** EOP *** ( black_rows=%d, cmy_rows=%d )" % ( black_rows, cmy_rows ) )
            

    def _dataRecordState( self ):
        record_type = struct.unpack( "<B", self.buffer.read( RECORD_TYPE_SIZE ) )[0]
        self.buffer_remaining -= RECORD_TYPE_SIZE
        self.block_remaining -= RECORD_TYPE_SIZE

        self.record_table.get( record_type, self._errorState )()
        
        if self.page_flags & PAGE_FLAG_END_DOC or \
            self.page_flags & PAGE_FLAG_END_STREAM:
            #self.state = STATE_END
            self.end_scan = True
        
        #elif self.block_remaining == 0 and self.buffer_remaining > 0:
        #    self.state = STATE_FIXED_HEADER
        
        #elif self.block_remaining == 0 and self.buffer_remaining == 0:
        #    self.state = STATE_END
        
        #elif self.block_remaining > 0 and self.buffer_remaining == 0:
        #    self.state = STATE_READ
        
        #elif self.block_remaining > 0 and self.buffer_remaining > 0:  
        #    self.state = STATE_RECORD
        else:
            self.state = STATE_END
        
                
    def _errorState( self ):
        raise Error( ERROR_INTERNAL )
            

        
    # fixed header (8 bytes):
    # 
    # +----------------------------+
    # |                            |
    # | block len (32 bits)        |
    # | length of entire read      |
    # | block of data              |
    # +----------------------------+
    # |                            |
    # | header length (16 bits)    |
    # | length of fixed and        |
    # | variant header (if any)    |
    # | ==8 if no variant (fixed   |
    # |   only                     |
    # | >8 if variant header       |
    # |                            |
    # +----------------------------+
    # |                            |
    # | data type (8 bits)         |
    # | data type of data record(s)|
    # |                            |
    # +----------------------------+
    # |                            |
    # | page flags (8 bits)        |
    # |                            |
    # +----------------------------+
    #
    # followed by variant header and/or 
    # data record(s)...
    #
    # image header variant (10 bytes)
    # 
    # +----------------------------+
    # |                            |
    # | major ver (8 bits)         |
    # |                            |
    # +----------------------------+
    # |                            |
    # | minor ver (8 bits)         |
    # |                            |
    # +----------------------------+
    # |                            |
    # | source pages (16 bits)     |
    # |                            |
    # +----------------------------+
    # |                            |
    # | copies/page (16 bits)      |
    # |                            |
    # +----------------------------+
    # |                            |
    # | zoom factor (16 bits)      |
    # |                            |
    # +----------------------------+
    # |                            |
    # | jpeg Q factor (16 bits)    |
    # |                            |
    # +----------------------------+
    #
    # start page record (36 bytes)
    # 
    # +----------------------------+
    # |                            |
    # | id = 0 (8 bits)            |
    # |                            |
    # +----------------------------+
    # |                            |
    # | encoding (8 bits)          |
    # |                            |
    # +----------------------------+
    # |                            |
    # | page num (16 bits)         |
    # |                            |
    # +----------------------------+
    # |                            |
    # | black data desc (16 bytes) |
    # |                            |
    # +----------------------------+
    # |                            |
    # | cmy data desc (16 bytes)   |
    # |                            |
    # +----------------------------+
    #
    # black and cmy desc (16 bytes ea):
    # 
    # +----------------------------+
    # |                            |
    # | pixels/row (16 bits)       |
    # |                            |
    # +----------------------------+
    # |                            |
    # | bits/pixel (16 bits)       |
    # |                            |
    # +----------------------------+
    # |                            |
    # | rows this page (32 bits)   |
    # |                            |
    # +----------------------------+
    # |                            |
    # | hort dpi (32 bits)         |
    # |                            |
    # +----------------------------+
    # |                            |
    # | vert dpi (32 bits)         |
    # |                            |
    # +----------------------------+
    #
    #
    # raster data record (4 bytes + data)
    # 
    # +----------------------------+
    # |                            |
    # | id = 1 (8 bits)            |
    # |                            |
    # +----------------------------+
    # |                            |
    # | unused (8 bits)            |
    # |                            |
    # +----------------------------+
    # |                            |
    # | data bytes (n) (16 bits)   |
    # |                            |
    # +----------------------------+
    # |                            |
    # | data (n bytes)             |
    # |                            |
    # +----------------------------+
    #
    #
    # end page record (12 bytes)
    # 
    # +----------------------------+
    # |                            |
    # | id = 2 (8 bits)            |
    # |                            |
    # +----------------------------+
    # |                            |
    # | unused (24 bits)           |
    # |                            |
    # +----------------------------+
    # |                            |
    # | rows of black (32 bits)    |
    # |                            |
    # +----------------------------+
    # |                            |
    # | rows of cmy (32 bits)      |
    # |                            |
    # +----------------------------+
    #
    
    if 0:
        def buildFixedHeader():
            pass
            
        def buildVariantHeader():
            pass
            
        def buildRecord():
            pass
            
