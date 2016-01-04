#!/usr/bin/env python
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


_VERSION = '1.1'

# Std Lib
import sys
import os
import struct

# Request codes
GET_REQUEST = 0x00
GET_NEXT_REQUEST = 0x01
GET_BLOCK_REQUEST = 0x02
GET_NEXT_BLOCK_REQUEST = 0x03
SET_REQUEST = 0x04
ENABLE_TRAP_REQUEST = 0x05
DISABLE_TRAP_REQUEST = 0x06
TRAP_REQUEST = 0x07

# Reply codes
GET_REPLY = 0x80
GET_NEXT_REPLY = 0x81
BLOCK_REPLY = 0x82
NEXT_BLOCK_REPLY = 0x83
SET_REPLY = 0x84
ENABLE_TRAP_REPLY = 0x85
DISABLE_TRAP_REPLY = 0x85

# PML Reply error codes
ERROR_OK = 0x00
ERROR_OK_END_OF_SUPPORTED_OBJECTS = 0x01
ERROR_OK_NEAREST_LEGAL_VALUE_SUBSITUTED = 0x02
ERROR_MAX_OK = 0x7f
ERROR_UNKNOWN_REQUEST = 0x80
ERROR_BUFFER_OVERFLOW = 0x81
ERROR_COMMAND_EXECUTION = 0x82
ERROR_UNKNOWN_OID = 0x83
ERROR_OBJ_DOES_NOT_SUPPORT_SPECIFIED_ACTION = 0x84
ERROR_INVALID_OR_UNSUPPORTED_VALUE = 0x85
ERROR_PAST_END_OF_SUPPORTED_OBJS = 0x86
ERROR_ACTION_CANNOT_BE_PERFORMED_NOW = 0x87
ERROR_SYNTAX = 0x88

# Data types
TYPE_MASK = 0xfc
TYPE_OBJECT_IDENTIFIER = 0x00
TYPE_ENUMERATION = 0x04
TYPE_SIGNED_INTEGER = 0x08
TYPE_REAL = 0x0C
TYPE_STRING = 0x10
TYPE_BINARY = 0x14
TYPE_ERROR_CODE = 0x18
TYPE_NULL_VALUE = 0x1c
TYPE_COLLECTION = 0x20
TYPE_UNKNOWN = 0xff

# Misc. constants
MAX_VALUE_LEN = 1023
MAX_OID_LEN = 32
MAX_DATALEN = 4096




def buildPMLGetPacket( oid ): # String dotted notation
    oid = ''.join( [ chr(int( b.strip() )) for b in oid.split( '.' ) ] )
    return struct.pack( '>BBB%ss' % len(oid), 
                        GET_REQUEST, 
                        TYPE_OBJECT_IDENTIFIER, 
                        len(oid), oid )
 
def buildPMLGetPacketEx( oid ): # OID identifier dict
    return buildPMLGetPacket( oid['oid'] )
 
def buildEmbeddedPMLSetPacket( oid, value, data_type ):
    return ''.join( [ 'PML\x20', buildPMLSetPacket( oid, value, data_type ) ] )

def buildPMLSetPacket( oid, value, data_type ): # String dotted notation
    oid = ''.join( [ chr(int(b.strip())) for b in oid.split( '.' ) ] )
    
    if data_type in ( TYPE_ENUMERATION, TYPE_SIGNED_INTEGER, TYPE_COLLECTION ):
        data = struct.pack( ">i", int(value) )

        if value > 0: 
            while len( data ) > 0 and data[0] == '\x00':
                data = data[ 1:]
        else:
            while len(data) > 1 and data[0] == '\xff' and data[1] == '\xff':
                data = data[ 1:]

        data = struct.pack( ">BB%ds" % len(data), data_type, len(data), data )
    
    elif data_type == TYPE_REAL:
        data = struct.pack( ">BBf", data_type, struct.calcsize( "f" ), float(value) )
    
    elif data_type == TYPE_STRING:
        data = struct.pack( ">BBBB%ss" % len( value ), data_type, len( value ) + 2, 0x01, 0x15, value )
    
    elif data_type == TYPE_BINARY:
        data = struct.pack( ">BB%ss" % len( value ), data_type, len( value ), ''.join( [ chr(x) for x in value ] ) )
    
    p = struct.pack( '>BBB%ss%ss' % ( len(oid), len(data) ),
                    SET_REQUEST, 
                    TYPE_OBJECT_IDENTIFIER, 
                    len(oid), oid,
                    data )
    
    return p

def buildPMLSetPacketEx( oid, value ): # OID identifier dict
    return buildPMLSetPacket( oid['oid'], value, oid['type'] )
    

def parsePMLPacket( p, expected_data_type=TYPE_UNKNOWN ):
    pos, state = 0, 1
    #print "Parser:", repr(p)
    data_type = TYPE_UNKNOWN
    error_state = False
    while state:
        
        #print repr(p[pos])
        
        if state == 1: # reply and error code
            reply, error_code = struct.unpack( ">BB", p[ pos : pos + 2 ] )
            state, pos = 2, pos + 2
            
            if error_code > ERROR_MAX_OK:
                error_state = True
        
        elif state == 2: # data type and length
            data_type, length = struct.unpack( ">BB", p[ pos : pos + 2 ] )
            state, pos = 3, pos + 2
            
            if error_state:
                
                if expected_data_type in ( TYPE_COLLECTION, TYPE_ENUMERATION, 
                                    TYPE_SIGNED_INTEGER, TYPE_BINARY ): 
                    data = 0
                
                elif expected_data_type == TYPE_REAL: 
                    data = 0.0
                
                else: 
                    data = ''
                
                break
            
        
        elif state == 3: # data
            data = p[pos : pos + length ]
            state, pos = 0, pos + length
            
            if data_type == TYPE_OBJECT_IDENTIFIER:
                state = 2
                continue
            
            elif data_type == TYPE_STRING:
                if length > 0:
                    symbol_set, data = struct.unpack( ">H%ss" % ( length - 2 ), data )
                else:
                    data = ''
            
            elif data_type == TYPE_BINARY:
                data = [ ord(b) for b in data ]
            
            elif data_type == TYPE_ENUMERATION:
                if length > 0:
                    data = struct.unpack( ">i", "%s%s" % ( '\x00' * ( 4 - length ), data )  )[0]
                else:
                    data = 0
            
            elif data_type == TYPE_REAL:
                if length > 0:
                    data = struct.unpack( ">f", data )[0]
                else:
                    data = 0.0
            
            elif data_type ==  TYPE_SIGNED_INTEGER:
                if length > 0:
                    pad = '\x00'
                    if ord( data[0] ) & 0x80: pad = '\xff' # negative number
                    data = struct.unpack( ">i", "%s%s" % ( pad * ( 4 - length ), data )  )[0]
                else:
                    data = 0

            elif data_type == TYPE_COLLECTION:
                if length > 0:
                    data = struct.unpack( ">i", "%s%s" % ( '\x00' * ( 4 - length ), data )  )[0]
                else:
                    data = 0
            
            elif data_type == TYPE_ERROR_CODE:
                data = struct.unpack( ">B", data )[0]
                
            elif data_type == TYPE_NULL_VALUE:
                data = None
            
            #state = 0
            break
    
    return data, data_type, error_code        
    
    
#
# OIDs
#



# Supported funcs
OID_DEVICE_SUPPORTED_FUNCTIONS = { 'oid' : '1.1.2.67', 'type' : TYPE_COLLECTION }
DEVICE_SUPPORTED_FUNCTIONS_SCAN =                 0x00002
DEVICE_SUPPORTED_FUNCTIONS_SCAN_SIMPLEX =         0x00004
DEVICE_SUPPORTED_FUNCTIONS_SCAN_DUPLEX =          0x00008
DEVICE_SUPPORTED_FUNCTIONS_COPY =                 0x00010
DEVICE_SUPPORTED_FUNCTIONS_COPY_SIMPLEX_SIMPLEX = 0x00020
DEVICE_SUPPORTED_FUNCTIONS_COPY_SIMPLEX_DUPLEX =  0x00040
DEVICE_SUPPORTED_FUNCTIONS_COPY_DUPLEX_SIMPLEX =  0x00080
DEVICE_SUPPORTED_FUNCTIONS_COPY_DUPLEX_DUPLEX =   0x00100
DEVICE_SUPPORTED_FUNCTIONS_COPY_COLLATION =       0x00200
DEVICE_SUPPORTED_FUNCTIONS_PRINT =                0x00400
DEVICE_SUPPORTED_FUNCTIONS_AUTO_FEED_SIMPLEX =    0x00800
DEVICE_SUPPORTED_FUNCTIONS_AUTO_FEED_DUPLEX =     0x01000
DEVICE_SUPPORTED_FUNCTIONS_FAX_SEND =             0x02000
DEVICE_SUPPORTED_FUNCTIONS_FAX_RECV =             0x04000
DEVICE_SUPPORTED_FUNCTIONS_MASS_STORAGE =         0x08000
DEVICE_SUPPORTED_FUNCTIONS_STREAMING_SAVE =       0x10000
DEVICE_SUPPORTED_FUNCTIONS_FAX_CONFIG =           0x20000
DEVICE_SUPPORTED_FUNCTIONS_FAX_CFG_SPEEDDIAL =    0x40000
DEVICE_SUPPORTED_FUNCTIONS_FAX_CFG_GROUPDIAL =    0x80000


    
OID_SERIAL_NUMBER = { "oid" : "1.1.3.3", "type" : TYPE_STRING, "desc" : r"""Identifies the serial number for the device. If theSERIAL-NUMBER object is set by the user, then setting theobject does not need to be protected. If the SERIAL-NUMBERobject is set at the factory, then the SERVICE-PASSWORD objectmust be set correctly before the SERIAL-NUMBER object iswritable. If this is a writable object, the POS should indicatethe maximum supported string length. If possible, encode theserial number in a symbol set (like Roman-8) that matches theASCII character set and limit the characters used to ASCIIcharacters.""", "use" : r"""Allows applications to track assets by serial number. Allows manufacturing lines to program the serial number into NVRAM.""" }

OID_PrinterDetectedErrorState = { 'oid' : '3.3.5.1.2', 'type' : TYPE_BINARY }


OID_DEVICE_STATUS = { 'oid' : '3.3.2.1.5.1', 'type' : TYPE_ENUMERATION }
OID_PRINTER_STATUS = { 'oid' : '3.3.5.1.1', 'type' : TYPE_ENUMERATION }
#OID_SLEEP_MODE = { "oid" : "1.1.1.2", "type" : TYPE_ENUMERATION, "desc" : r"""Returns eTrue if the device is in energy saving sleep mode,otherwise returns eFalse. Setting SLEEP-MODE to eFalse causesthe device to wake up, if it is in sleep mode. SettingSLEEP-MODE to eTrue causes the device to go into sleep mode.""", "use" : r"""Used by applications to determine/control device sleep mode.""" }

OID_SLEEP_MODE = { "oid" : "1.1.1.2", "type" : TYPE_ENUMERATION, "desc" : r"""Returns eTrue if the device is in energy saving sleep mode,otherwise returns eFalse. Setting SLEEP-MODE to eFalse causesthe device to wake up, if it is in sleep mode. SettingSLEEP-MODE to eTrue causes the device to go into sleep mode.""", "use" : r"""Used by applications to determine/control device sleep mode.""" }

OID_A2 = { 'oid' : '3.3.2.1.1.1', 'type' : TYPE_SIGNED_INTEGER }

OID_SUPPLIESLEVEL_1 = { 'oid' : '2.11.1.1.9.1.1', 'type' : TYPE_SIGNED_INTEGER }
OID_SUPPLIESDESC_1 = { 'oid' : '2.11.1.1.6.1.1', 'type' : TYPE_STRING }
OID_SUPPLIESMAXCAP_1 = { 'oid' : '2.11.1.1.8.1.1', 'type' : TYPE_SIGNED_INTEGER }

OID_TRAY_LEVEL_1 = { 'oid' : '2.8.2.1.10.1.1', 'type' : TYPE_SIGNED_INTEGER }
OID_TRAY_LEVEL_2 = { 'oid' : '2.8.2.1.10.1.2', 'type' : TYPE_SIGNED_INTEGER }
OID_TRAY_LEVEL_3 = { 'oid' : '2.8.2.1.10.1.3', 'type' : TYPE_SIGNED_INTEGER }

OID_CONSUMABLE_STATUS_SERIAL_NUMBER = { "oid" : "1.4.1.10.1.1.3.1", "type" : TYPE_STRING, "desc" : r"""This object is used to report the serial number for thisconsumable.""", "use" : r"""This cartridge serial number can be used for inventory andauthentication purposes.""" }
OID_CONSUMABLE_STATUS_CAPACITY_UNITS = { "oid" : "1.4.1.10.1.1.4.1", "type" : TYPE_ENUMERATION, "desc" : r"""This object is used to report the usage units used by theCONSUMABLE-STATUS-TOTAL-CAPACITY object.""", "use" : r"""""" }
OID_CONSUMABLE_STATUS_TOTAL_CAPACITY = { "oid" : "1.4.1.10.1.1.5.1", "type" : TYPE_SIGNED_INTEGER, "desc" : r"""This object is used to report the total capacity of a newconsumable of this type. The PML objectCONSUMABLE-STATUS-CAPACITY-UNITS can be used to determine theunits of measure for this PML object.""", "use" : r"""This marking agent capacity value can be used along with otherusage data to estimate the number of pages remaining in areceptacle/cartridge.""" }


# Alignment/cleaning/color calibration
OID_ZCA = { 'oid' : '1.4.1.8.5.4.1', 'type' : TYPE_SIGNED_INTEGER }
OID_AGENT2_VERTICAL_ALIGNMENT = { 'oid' : '1.4.1.5.3.2.5', 'type' : TYPE_SIGNED_INTEGER }
OID_AGENT2_HORIZONTAL_ALIGNMENT = { 'oid' : '1.4.1.5.3.2.6', 'type' : TYPE_SIGNED_INTEGER }
OID_AGENT1_BIDIR_ADJUSTMENT = { 'oid' : '1.4.1.5.3.1.7', 'type' : TYPE_SIGNED_INTEGER }
OID_AGENT2_BIDIR_ADJUSTMENT = { 'oid' : '1.4.1.5.3.2.7', 'type' : TYPE_SIGNED_INTEGER }
OID_MARKING_AGENTS_INITIALIZED = { 'oid' : '1.4.1.5.1.4', 'type' : TYPE_COLLECTION }
OID_AUTO_ALIGNMENT = { 'oid' : '1.1.5.2', 'type' : TYPE_ENUMERATION }
OID_AGENT3_VERTICAL_ALIGNMENT = { "oid" : "1.4.1.5.3.3.5", "type" : TYPE_SIGNED_INTEGER, "desc" : r"""Indicates the distance in centipoints to vertically adjust thethird marking agent relative to the first marking agent.Positive numbers move the second marking agent lower on theprinted page. Negative numbers move the second marking agenthigher on the printed page.""", "use" : r"""Use to align the marking agents in a product with multiplemarking agents.""" }
OID_AGENT3_HORIZONTAL_ALIGNMENT = { "oid" : "1.4.1.5.3.3.6", "type" : TYPE_SIGNED_INTEGER, "desc" : r"""Indicates the distance in centipoints to horizontally adjustthe third marking agent relative to the first marking agent.Positive numbers move the second marking agent to the right onthe printed page. Negative numbers move the second markingagent to the left on the printed page.""", "use" : r"""Use to align the marking agents in a product with multiplemarking agents.""" }
OID_AGENT3_BIDIR_ADJUSTMENT = { "oid" : "1.4.1.5.3.3.7", "type" : TYPE_SIGNED_INTEGER, "desc" : r"""Indicates the distance in centipoints to adjust the startingprint position for marking agent 3 when printing in the reversedirection. See AGENT1-BIDIR-ADJUSTMENT for a description.""", "use" : r"""""" }
OID_COLOR_CALIBRATION_SELECTION = { "oid" : "1.4.1.5.1.9", "type" : TYPE_SIGNED_INTEGER, "desc" : r"""This object is used to select the color calibration printpattern. The driver will provide the color calibration printpattern number based on the user's selection. The selectionaffects the supply drop volumes associated with the markingagents. The selection's effect lasts until the next selectionor change of marking agents. The color calibration is an N x Npattern. The selection must be in the (inclusive) range 1 toN^2 (N-squared). An out-of-range value will be ignored by theprinter and will cause a PML error to be reported""", "use" : r"""This object is expected to be used after the driver hasrequested the printer to print the color calibration pattern.However, the object may be used in isolation too (i.e., thereis no need for the pattern to be printed and there is norestriction on the time-frame when the object can be used). Theselection will take effect at the next job boundary (i.e.,starting from the next job). Caveat: If the printer is powereddown before the selection takes effect, the selection will belost and previous calibration will remain in effect.""" }

# Scanning
OID_DOWNLOAD_TIMEOUT = { 'oid' : '1.1.1.17', 'type' : TYPE_UNKNOWN }
OID_UPLOAD_TIMEOUT = { 'oid' : '1.1.1.18', 'type' : TYPE_SIGNED_INTEGER }
OID_SCAN_ABC_THRESHOLDS = { "oid" : "1.2.2.1.14", "type" : TYPE_BINARY, "desc" : r"""A C structure containing the following fields: typedef struct { ubyte ceiling; /* upper threshold */ ubyte floor; /* lower threshold */ } scan_abc_thresholds_t; where ubyte is an unsigned byte (0-255).""", "use" : r"""Used by host to set Automatic Background Control thresholds inthe device.""" }
OID_SCAN_UPLOAD_ERROR = { "oid" : "1.2.2.1.6", "type" : TYPE_SIGNED_INTEGER, "desc" : r"""Error status of the image scanning upload session.""", "use" : r"""Provides the reason for the premature termination of imagescanning upload activity.""" }
OID_SCAN_SHARPENING_COEFFICIENT = { "oid" : "1.2.2.1.15", "type" : TYPE_SIGNED_INTEGER, "desc" : r"""Sets the sharpening coefficient used in scanning and imageprocessing. If the device does not support the given value,then it will select the nearest supported value and return<OKNearestLegalValueSubstituted>. The list of supported valuesshould be documented in the device POS.""", "use" : r"""Used by host to set the sharpening coefficient in the device.""" }
OID_SCAN_NEUTRAL_CLIP_THRESHOLDS = { "oid" : "1.2.2.1.39", "type" : TYPE_BINARY, "desc" : r"""A C structure containing the following fields: typedef struct {ubyte luminance; ubyte chrominance; } scan_neutral_clip_t;where ubyte is an unsigned byte (0-255).""", "use" : r"""Used by host to set neutral clip thresholds in the device on aper job basis.""" }
OID_SCAN_RESOLUTION = { 'oid' : '1.2.2.1.2', 'type' : TYPE_BINARY }
OID_SCAN_RESOLUTION_RANGE = { 'oid' : '1.2.2.2.3', 'type' : TYPE_STRING }

OID_SCAN_UPLOAD =       { 'oid' : '1.2.2.1.12', 'type' : TYPE_ENUMERATION }
UPLOAD_STATE_IDLE       = 1
UPLOAD_STATE_START      = 2
UPLOAD_STATE_ACTIVE     = 3
UPLOAD_STATE_ABORTED    = 4
UPLOAD_STATE_DONE       = 5
UPLOAD_STATE_NEWPAGE    = 6

# Scan data type
OID_SCAN_PIXEL_DATA_TYPE = { 'oid' : '1.2.2.1.3', 'type' : TYPE_ENUMERATION }
DATA_TYPE_LINEART = 1
DATA_TYPE_GRAYSCALE = 8
DATA_TYPE_COLOR = 24

OID_SCANNER_STATUS = { 'oid' : '1.2.2.2.1', 'type' : TYPE_SIGNED_INTEGER } # OID_NOT_READY_SOURCE_SCANNER
SCANNER_STATUS_UNKNOWN_ERROR = 0x01
SCANNER_STATUS_INVALID_MEDIA_SIZE = 0x02
SCANNER_STATUS_FEEDER_OPEN = 0x04
SCANNER_STATUS_FEEDER_JAM = 0x08
SCANNER_STATUS_FEEDER_EMPTY = 0x10

# Scan compression
OID_SCAN_COMPRESSION = { 'oid' : '1.2.2.1.4', 'type' : TYPE_ENUMERATION }
SCAN_COMPRESSION_NONE = 1
SCAN_COMPRESSION_DEFAULT = 2
SCAN_COMPRESSION_MH = 3
SCAN_COMPRESSION_MR = 4
SCAN_COMPRESSION_MMR = 5
SCAN_COMPRESSION_JPEG = 6
SCAN_COMPRESSION_JPEGLS = 7
OID_SCAN_COMPRESSION_FACTOR = { 'oid' : '1.2.2.1.5', 'type' : TYPE_SIGNED_INTEGER }

OID_PAGES_REMAINING = { 'oid' : '1.4.1.10.5.1.1.1', 'type' : TYPE_SIGNED_INTEGER }
    
    

