#!/usr/bin/env python
#
# $Revision: 1.6 $ 
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

# Local
from base.g import *



ESC = '\x1b'
RESET = ( '', 'E', '' ) 
CLEAR_ERRORS = ( '*', 'o', 'E' )
RECALIBRATE =       ( '*', 'u', 'R', '0' )
SET_CALIBRATE_MODE_AUTO = ( '*', 'u', 'G', '0' )
LOCK =              ( '*', 'f', 'H', '1' )
LOCK_TIMEOUT =      ( '*', 'f', 'I' )
UNLOCK =            ( '*', 'f', 'H', '0' )
START_SCAN =        ( '*', 'f', 'S', '0' )
SET_EXCLUSION_AREA = ( '*', 'm', 'A' )
SET_PRESCAN =       ( '*', 'm', 'B', '1' )
SET_NUM_IMAGES_FOUND = ( '*', 'm', 'P' )


ADF_START_SCAN =            ( '*', 'u', 'S', '0' )
ADF_PRELOAD_DOCUMENT_1ST =  ( '*', 'f', 'C', '0' )
ADF_PRELOAD_DOCUMENT_ALL =  ( '*', 'f', 'C', '1' )
ADF_CHANGE_DOCUMENT =       ( '*', 'u', 'X', '0' )
CHANGE_DOC_SIMPLEX = 0
CHANGE_DOC_DUPLEX = 2
CHANGE_DOC_DUPLEX_SIDE = 12

ADF_UNLOAD_DOCUMENT =       ( '*', 'u', 'U', '0' )
ADF_BACKGROUND_CHANGE =     ( '*', 'u', 'Y', '0' )
ADF_SCAN_OFFSETS_NONE =     ( '*', 'm', 'O', '0' )
ADF_SCAN_OFFSETS_LETTER =   ( '*', 'm', 'O', '1' )
ADF_SCAN_OFFSETS_A4 =       ( '*', 'm', 'O', '2' )

XPA_START_SCAN =  ( '*', 'u', 'D', '0' )
XPA_ENABLE =      ( '*', 'u', 'H', '0' )
XPA_DISABLE =     ( '*', 'u', 'H', '1' )

SET_COMPRESS_NONE =   ( '*', 'a', 'C', '1' ) # no inq
SET_COMPRESS_JPEG =   ( '*', 'a', 'C', '2' ) # no inq
SET_COMPRESS_PACKED = ( '*', 'a', 'C', '1' ) # no inq

SET_COMPRESS_FACTOR = ( '*', 'm', 'Q' ) # no inq

SET_PACKETIZED_DATA = ( '*', 'm', 'S' )
SET_MFPDTF = ( '*', 'm', 'S' ) # no inq

SET_DATA_TYPE =                   ( '*', 'a', 'T' )
SET_DATA_TYPE_LINEART =           ( '*', 'a', 'T', '0' )
SET_DATA_TYPE_BW_DITHER =         ( '*', 'a', 'T', '3' )
SET_DATA_TYPE_BW_GRAYSCALE =      ( '*', 'a', 'T', '4' )
SET_DATA_TYPE_COLOR =             ( '*', 'a', 'T', '5' )
SET_DATA_TYPE_COLOR_THRESHOLD =   ( '*', 'a', 'T', '6' )
SET_DATA_TYPE_COLOR_DITHER =      ( '*', 'a', 'T', '7' )
SET_DATA_TYPE_FAST_BW_THRES =     ( '*', 'a', 'T', '50' )
SET_DATA_TYPE_FAST_BW_DITHER =    ( '*', 'a', 'T', '51' )
SET_DATA_TYPE_FAST_BW_GRAYSCALE = ( '*', 'a', 'T', '52' )

SET_DATA_WIDTH =         ( '*', 'a', 'G' )
SET_DATA_WIDTH_1BIT =    ( '*', 'a', 'G', '1' )
SET_DATA_WIDTH_4BIT =    ( '*', 'a', 'G', '4' )
SET_DATA_WIDTH_8BIT =    ( '*', 'a', 'G', '8' )
SET_DATA_WIDTH_10BIT =   ( '*', 'a', 'G', '10' )
SET_DATA_WIDTH_12BIT =   ( '*', 'a', 'G', '12' )
SET_DATA_WIDTH_24BIT =   ( '*', 'a', 'G', '24' )
SET_DATA_WIDTH_30BIT =   ( '*', 'a', 'G', '30' )
SET_DATA_WIDTH_36BIT =   ( '*', 'a', 'G', '36' )

SET_X_RES =         ( '*', 'a', 'R' )
SET_Y_RES =         ( '*', 'a', 'S' )
SET_X_SCALE =       ( '*', 'a', 'E' )
SET_Y_SCALE =       ( '*', 'a', 'F' )
SET_X_POS =         ( '*', 'f', 'X' )
SET_Y_POS =         ( '*', 'f', 'Y' )
SET_X_EXTENT =      ( '*', 'f', 'P' )
SET_Y_EXTENT =      ( '*', 'f', 'Q' )

# don't use these: ?
SET_X_POS_DECI =    ( '*', 'a', 'X' )
SET_Y_POS_DECI =    ( '*', 'a', 'Y' )
SET_X_EXTENT_DECI = ( '*', 'a', 'P' )
SET_Y_EXTENT_DECI = ( '*', 'a', 'Q' )

SET_BW_DITHER_PATTERN_USER =           ( '*', 'a', 'J', '-1' )
SET_BW_DITHER_PATTERN_COARSE_FATTING = ( '*', 'a', 'J', '0' )
SET_BW_DITHER_PATTERN_FINE_FATTING =   ( '*', 'a', 'J', '1' )
SET_BW_DITHER_PATTERN_BAYER =          ( '*', 'a', 'J', '2' )
SET_BW_DITHER_PATTERN_VERT_LINE =      ( '*', 'a', 'J', '3' )

SET_COLOR_DITHER_PATTERN_USER =           ( '*', 'u', 'J', '-1' )
SET_COLOR_DITHER_PATTERN_COARSE_FATTING = ( '*', 'u', 'J', '0' )

SET_MATRIX_COEFFIECIENTS_USER_BW =    ( '*', 'u', 'T', '-2' )
SET_MATRIX_COEFFIECIENTS_USER_COLOR = ( '*', 'u', 'T', '-1' )
SET_MATRIX_COEFFIECIENTS_RGB =        ( '*', 'u', 'T', '0' )
SET_MATRIX_COEFFIECIENTS_BW_NTSC =    ( '*', 'u', 'T', '1' )
SET_MATRIX_COEFFIECIENTS_PASS_THRU =  ( '*', 'u', 'T', '2' )
SET_MATRIX_COEFFIECIENTS_RED =        ( '*', 'u', 'T', '3' )
SET_MATRIX_COEFFIECIENTS_BLUE =       ( '*', 'u', 'T', '4' )
SET_MATRIX_COEFFIECIENTS_XPA_RGB =    ( '*', 'u', 'T', '5' )
SET_MATRIX_COEFFIECIENTS_SRGB =       ( '*', 'u', 'T', '5' )
SET_MATRIX_COEFFIECIENTS_XPA_BW =     ( '*', 'u', 'T', '6' )

SET_TONE_MAP =        ( '*', 'u', 'K' )
INVERSE_IMAGE =       ( '*', 'a', 'I' )
MIRROR_IMAGE_ON =     ( '*', 'a', 'M', '1' )
MIRROR_IMAGE_OFF =    ( '*', 'a', 'M', '0' )
SET_INTENSITY_LEVEL = ( '*', 'a', 'L' )
SET_FILTER =          ( '*', 'u', 'F' )
SET_CONTRAST =        ( '*', 'a', 'K' )
SET_AUTO_BACKGROUND = ( '*', 'a', 'B' )

LIGHT_SOURCE_TEST_ON =  ( '*', 'f', 'L', '1' )
LIGHT_SOURCE_TEST_OFF = ( '*', 'f', 'L', '0' )

SET_DOWNLOAD_TYPE = ( '*', 'a', 'D' )
DOWNLOAD =          ( '*', 'a', 'W' ) # host to scanner
UPLOAD =            ( '*', 's', 'U' ) # scanner to host
SET_SPEED =         ( '*', 'u', 'E' )

SET_BYTE_ORDER_BIG =    ( '*', 'u', 'B', '0' )
SET_BYTE_ORDER_LITTLE = ( '*', 'u', 'B', '1' )

INQUIRE_PRESENT_CMD =     ( '*', 's', 'R' )
INQUIRE_MINIMUM_CMD =     ( '*', 's', 'L' )
INQUIRE_MAXIMUM_CMD =     ( '*', 's', 'H' )
INQUIRE_DEVICE_PARM_CMD = ( '*', 's', 'E' )

# Device inquiry
INQUIRE_PIXELS_PER_SCAN_LINE = 1024
INQUIRE_BYTES_PER_SCAN_LINE = 1025
INQUIRE_DEVICE_PIXELS_PER_INCH = 1028
INQUIRE_NATIVE_OPTICAL_RESOLUTION = 1029
INQUIRE_NUM_SCAN_LINES = 1026
INQUIRE_FIRMWARE_DATE_CODE = 4
INQUIRE_SESSION_ID = 505
INQUIRE_HP_MODEL_11 = 18
INQUIRE_HP_MODEL_12 = 19
INQUIRE_ADF_FEED_STATUS = 23
INQUIRE_ADF_CAPABILITY = 24
INQUIRE_ADF_DOCUMENT_LOADED = 25
INQUIRE_ADF_READY_TO_UNLOAD = 27
INQUIRE_CURRENT_ERROR_STACK = 257 
INQUIRE_CURRENT_ERROR = 259
INQUIRE_SESSION_ID = 505
INQUIRE_BULB_WARM_UP_STATUS = 506
INQUIRE_ADF_READY_TO_LOAD = 1027
INQUIRE_DEVICE_PIXELS_PER_INCH = 1028

# SCL error codes (INQUIRE_CURRENT_ERROR)
ERROR_COMMAND_FORMAT_ERROR = 0
ERROR_UNRECOGNIZED_COMMAND = 1
ERROR_PARAMETER_ERROR = 2
ERROR_ILLEGAL_WINDOW = 3
ERROR_SCALING_ERROR = 4
ERROR_DITHER_ID_ERROR = 5
ERROR_TONE_MAP_ID_ERROR = 6
ERROR_LAMP_ERROR = 7
ERROR_MATRIX_ID_ERROR = 8
ERROR_CAL_STRIP_PARAM_ERROR = 9
ERROR_GROSS_CALIBRATION_ERROR = 10
ERROR_NO_MEMORY = 500
ERROR_SCANNER_HEAD_LOCKED = 501
ERROR_CANCELLED = 502
ERROR_PEN_DOOR_OPEN = 503
ERROR_ADF_PAPER_JAM = 1024
ERROR_HOME_POSITION_MISSING = 1025
ERROR_PAPER_NOT_LOADED = 1026
ERROR_ORIGINAL_ON_GLASS = 1027

# INQUIRE_ADF_FEED_STATUS
ADF_FEED_STATUS_OK = 0
ADF_FEED_STATUS_BUSY = 1000
ADF_FEED_STATUS_PAPER_JAM = 1024
ADF_FEED_STATUS_ORIGINAL_ON_GLASS = 1027
ADF_FEED_STATUS_PORTRAIT_FEED = 1028

PSEUDO_FLATBED_Y_RESOLUTION = 11323


def _inquireID( punc, letter1, letter2, dummy1=None, dummy2=None ):
    return ( 0x2800 +( ( ord(letter1) - 0x5f ) << 5 ) + ( ord(letter2) - 0x3f ) )

def buildSCLCmd( punc, letter1, letter2, value='', data=None  ):
    if data is None:
        return ''.join( [ ESC, punc, letter1, str(value), letter2 ] )
        
    assert letter2 in ( 'w', 'W' )
    return ''.join( [ ESC, punc, letter1, str(len(data)), letter2, data ] )

def buildSCLInquireMinimum( punc, letter1, letter2, dummy1=None, dummy2=None ):
    id = _inquireID( punc, letter1, letter2 )
    return ( buildSCLCmd( value=id, *INQUIRE_MINIMUM_CMD ), id )

def buildSCLInquireMaximum( punc, letter1, letter2, dummy1=None, dummy2=None ):
    id = _inquireID( punc, letter1, letter2 )
    return ( buildSCLCmd( value=id, *INQUIRE_MAXIMUM_CMD ), id )

def buildSCLInquirePresent( punc, letter1, letter2, dummy1=None, dummy2=None ):
    id = _inquireID( punc, letter1, letter2 )
    return ( buildSCLCmd( value=id, *INQUIRE_PRESENT_CMD ), id )
    
def buildSCLInquireDeviceParam( id ):
    return ( buildSCLCmd( value=id, *INQUIRE_DEVICE_PARM_CMD ), id )

inquire_pat = re.compile( r's*(\d*)[d,g,k,p](\d*)([v,w,n])(.*)', re.IGNORECASE )
    
def parseSCLInquire( data ):
    s = inquire_pat.search(data)
    
    if s is not None:
        id = int( s.group(1) )
        value = s.group(2) # size of data if typ is 'W'
        typ = s.group(3)
    
        if typ in ( 'n', 'N' ):
            log.warn( "Got null SCL inquire response." )
            # if NULL SCL resp, return None
            return None, id, type, ''
        
        if typ in ( 'w', 'W' ):
            value = int(value)
            data = s.group(4)[:value]
        else:
            data = None
        
        return value, id, typ, data
    
    else:    
        return 0, 0, 0, ''
    

    
if __name__ == "__main__":
    """p = buildSCLCmd( data='abc', *DOWNLOAD )
    print repr(p)
    assert p == '\x1b*a3Wabc'
    p = buildSCLCmd( value='90', *SET_COMPRESS_FACTOR )
    print repr(p)
    assert p == '\x1b*m90Q'
    p = buildSCLInquireMaximum( *SET_X_RES )[0]
    print repr(p)
    assert p == '\x1b*s10323H'
    p = buildSCLInquireMinimum( *SET_X_RES )[0]
    print repr(p)
    assert p == '\x1b*s10323L'
    p = buildSCLInquirePresent( *SET_X_RES )[0]
    print repr(p)
    assert p == '\x1b*s10323R'
    val, id, typ, data = parseSCLInquire( '\x1bs*1028k300V' )
    #print val, id, typ, data
    assert id == 1028
    assert val == '300'
    assert typ == 'V'
    assert data == None
    """
    print _inquireID( '*', 'a', 'R' )
