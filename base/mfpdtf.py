#!/usr/bin/env python
#
# $Revision: 1.7 $ 
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
SOP_RECORD_SIZE = 36
RASTER_RECORD_SIZE = 4
EOP_RECORD_SIZE = 12

PAGE_FLAG_NEW_PAGE = 0x01
PAGE_FLAG_END_PAGE = 0x02
PAGE_FLAG_NEW_DOC = 0x04
PAGE_FLAG_END_DOC = 0x08
PAGE_FLAG_END_STREAM = 0x10


def parseFixedHeader( buffer ):
    fmt = "<IHBB"
    block_len, header_len, data_type, page_flags = struct.unpack( fmt, buffer[:8] )
    page_flags = page_flags & 0x1f
    return block_len, header_len, data_type, page_flags
    
def parseImageVariantHeader( buffer, data_type ):
    if data_type == DT_SCANNED_IMAGES:
        fmt = "<BBHHHH"
        major_ver, minor_ver, src_pages, copies_per_page, zoom, jpeg_q_factor = struct.unpack( fmt, buffer[:10] )
        return major_ver, minor_ver, src_pages, copies_per_page, zoom, jpeg_q_factor
    elif data_type == DT_FAX_IMAGES:
        pass
    
def parseRecord( buffer ):
    record_type = struct.unpack( "<B", buffer[0] )[0]
    
    if record_type == RT_START_PAGE:
        fmt = "<BBHHHIIIHHIII"
        id, encoding, page_num, black_ppr, black_bpp, black_rpp, black_hort_dpi, black_vert_dpi, cmy_ppr, cmy_bpp, cmy_rpp, cmy_hort_dpi, cmy_vert_dpi = \
            struct.unpack( fmt, buffer[:SOP_RECORD_SIZE] )
        assert id == record_type
        return id, (encoding, page_num, black_ppr, black_bpp, black_rpp, black_hort_dpi, black_vert_dpi, cmy_ppr, cmy_bpp, cmy_rpp, cmy_hort_dpi, cmy_vert_dpi)
        
    elif record_type == RT_RASTER:
        fmt = "<BBH"
        id, unused, data_size = struct.unpack( fmt, buffer[:RASTER_RECORD_SIZE])
        assert id == record_type
        return id, (unused, data_size)
        
    elif record_type == RT_END_PAGE:
        fmt = "<BBBBII"
        id, unused1, unused2, unused3, black_rows, cmy_rows = struct.unpack( fmt, buffer[:EOP_RECORD_SIZE] )
        assert id == record_type
        return id, (unused1, unused2, unused3, black_rows, cmy_rows)
        
    log.error( "Error: Invalid record type: %d" % record_type )
    raise Error( ERROR_INTERNAL )



def readChannelToStream( device, channel_id, stream, single_read=True, callback=None ):
    STATE_END, STATE_FIXED_HEADER, STATE_VARIANT_HEADER, STATE_RECORD = range(4)
    state, total_bytes, block_remaining, header_remaining, data_remaining = 1, 0, 0, 0, 0
    endScan = False
    while state != STATE_END:
        log.debug( "**** State %d ****" % state )
        if state == STATE_FIXED_HEADER: 
            
            if endScan:
                state = STATE_END
                break
            
            if data_remaining == 0:
                fields, data = device.readChannel( channel_id )
                data_remaining = len(data)
                if callback is not None:
                    endScan = callback()
            
            block_len, header_len, data_type, page_flags = parseFixedHeader( data )
            block_remaining, header_remaining = block_len-FIXED_HEADER_SIZE, header_len-FIXED_HEADER_SIZE
            log.debug( "Fixed header: (datalen=%d(0x%x),blocklen=%d(0x%x),headerlen=%d(0x%x),datatype=0x%x,pageflags=0x%x)" % 
                ( len(data), len(data), block_len, block_len, header_len, header_len, data_type, page_flags ) )
            data_remaining -= FIXED_HEADER_SIZE
            data = data[FIXED_HEADER_SIZE:]
            state = STATE_RECORD
            log.debug( "Data: data=%d,block=%d,header=%d" % ( data_remaining, block_remaining, header_remaining ) )
            
            if page_flags & PAGE_FLAG_END_STREAM:
                state = STATE_END
                break
            
            if header_remaining > 0:
                state = STATE_VARIANT_HEADER
            
        
        elif state == STATE_VARIANT_HEADER:
            if data_type == DT_SCANNED_IMAGES:
                major_ver, minor_ver, src_pages, copies_per_page, zoom, jpeg_q_factor = parseImageVariantHeader( data, data_type )
                log.debug( "Variant header: (major/minor=%d/%d,src_pages=%d,copies_per_page=%d,zoom=%d,jpeg_q_factor=%d" % 
                    (major_ver, minor_ver, src_pages, copies_per_page, zoom, jpeg_q_factor) )
                data = data[IMAGE_VARIANT_HEADER_SIZE:]
                block_remaining -= IMAGE_VARIANT_HEADER_SIZE
                header_remaining -= IMAGE_VARIANT_HEADER_SIZE
                data_remaining -= IMAGE_VARIANT_HEADER_SIZE
                
            elif data_type == DT_FAX_IMAGES:
                log.error( "Unsupported data type" )
            
            else:
                log.error( "Unsupported data type" )
                
            log.debug( "Data: data=%d,block=%d,header=%d" % ( data_remaining, block_remaining, header_remaining ) )
            
            if header_remaining > 0:
                log.error( "Header size error." )
                state = STATE_END
                continue
            
            state = STATE_RECORD
            if block_remaining == 0:
                state = STATE_FIXED_HEADER
            continue
        
        elif state == STATE_RECORD:
            record_type, record = parseRecord( data )
            
            if record_type == RT_START_PAGE:
                encoding, page_num, black_ppr, black_bpp, black_rpp, black_hort_dpi, black_vert_dpi, \
                    cmy_ppr, cmy_bpp, cmy_rpp, cmy_hort_dpi, cmy_vert_dpi = record
                log.debug( "Start page record: (encoding=0x%x, page=%d)" % ( encoding, page_num ) )
                data = data[SOP_RECORD_SIZE:]
                block_remaining -= SOP_RECORD_SIZE
                data_remaining -= SOP_RECORD_SIZE
                if block_remaining != 0:
                    log.error( "Block size error." )
                    state = STATE_END
                    continue

                if single_read:
                    state = STATE_END
                else:                    
                    state = STATE_FIXED_HEADER
                    log.debug( "Data: data=%d,block=%d,header=%d" % ( data_remaining, block_remaining, header_remaining ) )
                continue
                
            elif record_type == RT_RASTER:
                unused, data_size = record
                log.debug( "Raster record: (data size=%d(0x%x))" % ( data_size, data_size ) )
                data = data[RASTER_RECORD_SIZE:]
                block_remaining -= RASTER_RECORD_SIZE
                data_remaining -= RASTER_RECORD_SIZE
                log.debug( "Data: data=%d,block=%d,header=%d" % ( data_remaining, block_remaining, header_remaining ) )

                if block_remaining > 0 and data_remaining > 0:
                    log.debug( "Writing remainder of data..." )
                    data_len = len(data)
                    log.debug( "Data len=%d(0x%x)" % (data_len,data_len))
                    stream.write( data[ :block_remaining ] )
                    block_remaining -= data_len
                    data_remaining -= data_len
                    
                    if data_remaining != 0:
                        log.error( "Data size error" )
                        state = STATE_END
                        continue
                    
                while block_remaining > 0:
                    if endScan:
                        #state = STATE_END
                        break
                        
                    log.debug( "Reading more data from device..." )
                    fields, data = device.readChannel( channel_id )
                    
                    if callback is not None:
                        endScan = callback()

                    data_len = len(data)
                    log.debug( "Data len=%d(0x%x)" % (data_len,data_len) )
                    stream.write( data[ :block_remaining ] )
                    total_bytes += data_len
                    block_remaining -= data_len
                
                if block_remaining != 0:
                    log.error( "Block size error." )
                    state = STATE_END
                    continue
                
                state = STATE_FIXED_HEADER
                continue
                
            elif record_type == RT_END_PAGE:
                unused1, unused2, unused3, black_rows, cmy_rows = record
                log.debug( "End page record: (black_rows=%d,cmy_rows=%d)" % ( black_rows, cmy_rows ) )
                data = data[EOP_RECORD_SIZE:]
                block_remaining -= EOP_RECORD_SIZE
                data_remaining -= EOP_RECORD_SIZE
                if block_remaining != 0:
                    log.error( "Block size error." )
                log.debug( "Data: data=%d,block=%d,header=%d" % ( data_remaining, block_remaining, header_remaining ) )

                if page_flags & PAGE_FLAG_END_DOC or \
                   page_flags & PAGE_FLAG_END_STREAM:
                    state = STATE_END
                else:
                    state = STATE_FIXED_HEADER
                continue

    log.debug( "Read %d bytes" % total_bytes )
    return endScan 
    

def buildFixedHeader():
    pass
    
def buildVariantHeader():
    pass
    
def buildRecord():
    pass
    
