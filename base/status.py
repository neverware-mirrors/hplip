#!/usr/bin/env python
#
# $Revision: 1.17 $ 
# $Date: 2005/01/06 22:41:39 $
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



# Local
from g import *
from codes import *

"""
status dict structure:
    { 'revision' :     STATUS_REV_00 .. STATUS_REV_04,
      'agents' :       [ list of pens/agents (dicts) ],  
      'top-door' :     TOP_DOOR_NOT_PRESENT | TOP_DOOR_CLOSED | TOP_DOOR_OPEN,
      'status' :       STATUS_*,
      'supply-door' :  SUPPLY_DOOR_NOT_PRESENT | SUPPLY_DOOR_CLOSED | SUPPLY_DOOR_OPEN.
      'duplexer' :     DUPLEXER_NOT_PRESENT | DUPLEXER_DOOR_CLOSED | DUPLEXER_DOOR_OPEN,
      'photo_tray' :   PHOTO_TRAY_NOT_PRESENT | PHOTO_TRAY_ENGAGED | PHOTO_TRAY_NOT_ENGAGED, 
      'in-tray1' :     IN_TRAY_NOT_PRESENT | IN_TRAY_CLOSED | IN_TRAY_OPEN (| IN_TRAY_DEFAULT | IN_TRAY_LOCKED)*, 
      'in-tray2' :     IN_TRAY_NOT_PRESENT | IN_TRAY_CLOSED | IN_TRAY_OPEN (| IN_TRAY_DEFAULT | IN_TRAY_LOCKED)*, 
      'media-path' :   MEDIA_PATH_NOT_PRESENT | MEDIA_PATH_CUT_SHEET | MEDIA_PATH_BANNER | MEDIA_PATH_PHOTO,
           } 
           
    * S:02 only

agent dict structure:
    { 'kind' :           AGENT_KIND_NONE ... AGENT_KIND_HEAD_AND_SUPPLY,
      'type' :           TYPE_BLACK ... TYPE_GGK,
      'health' :         AGENT_HEALTH_OK ... AGENT_HEALTH_FAILED,
      'level' :          0 ... 100,
      'level-trigger' :  AGENT_LEVEL_TRIGGER_SUFFICIENT_0 ... AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
      }
"""   



# status info

# 'revision'
STATUS_REV_00 = 0x00
STATUS_REV_01 = 0x01
STATUS_REV_02 = 0x02
STATUS_REV_03 = 0x03
STATUS_REV_04 = 0x04
STATUS_REV_V  = 0xff
STATUS_REV_UNKNOWN = 0xfe

# 'top_door' (lid)
TOP_DOOR_NOT_PRESENT = 0
TOP_DOOR_CLOSED = 1
TOP_DOOR_OPEN = 2

# 'supply_door'
SUPPLY_DOOR_NOT_PRESENT = 0
SUPPLY_DOOR_CLOSED = 1
SUPPLY_DOOR_OPEN = 2

# 'media_path'
MEDIA_PATH_NOT_PRESENT = 0 # S:00 means banner not present
MEDIA_PATH_CUT_SHEET = 1 # S:01 means banner present/engaged
MEDIA_PATH_BANNER = 2
MEDIA_PATH_PHOTO = 3

# 'photo_tray'(S:03 photo/hagaki)
PHOTO_TRAY_NOT_PRESENT = 0
PHOTO_TRAY_NOT_ENGAGED = 1
PHOTO_TRAY_ENGAGED = 2

# 'duplexer' (S:02 cleanout)
DUPLEXER_NOT_PRESENT = 0
DUPLEXER_DOOR_CLOSED = 1
DUPLEXER_DOOR_OPEN = 2

# 'in_tray1' & 'in_tray2'
IN_TRAY_NOT_PRESENT = 0
IN_TRAY_PRESENT = 1 # for !S:02, test for > IN_TRAY_NOT_PRESENT
IN_TRAY_DEFAULT = 2 # S:02 only
IN_TRAY_LOCKED = 3 # S:02 only

# 'status'
STATUS_UNKNOWN = 999
STATUS_IDLE = 1000
STATUS_BUSY = 1001
STATUS_PRINTING = 1002
STATUS_TURNING_OFF = 1003
STATUS_REPORT_PRINTING = 1004
STATUS_CANCELING = 1005
STATUS_IO_STALL = 1006
STATUS_DRY_WAIT_TIME = 1007
STATUS_PEN_CHANGE = 1008
STATUS_OUT_OF_PAPER = 1009
STATUS_BANNER_EJECT_NEEDED = 1010
STATUS_BANNER_MISMATCH = 1011
STATUS_PHOTO_MISMATCH = 1012
STATUS_DUPLEX_MISMATCH = 1013
STATUS_MEDIA_JAM = 1014
STATUS_CARRIAGE_STALL = 1015
STATUS_PAPER_STALL = 1016
STATUS_PEN_FAILURE = 1017
STATUS_HARD_ERROR = 1018
STATUS_POWER_DOWN = 1019
STATUS_FRONT_PANEL_TEST = 1020
STATUS_CLEAN_OUT_TRAY_MISSING = 1021
STATUS_OUTPUT_BIN_FULL = 1022
STATUS_MEDIA_SIZE_MISMATCH = 1023
STATUS_MANUAL_DUPLEX_BLOCK = 1024
STATUS_SERVICE_STALL = 1025
STATUS_OUT_OF_INK = 1026
STATUS_LIO_ERROR = 1027
STATUS_PUMP_STALL = 1028
STATUS_TRAY2_MISSING = 1029
STATUS_DUPLEXER_MISSING = 1030
STATUS_REAR_TRAY_MISSING = 1031
STATUS_PEN_NOT_LATCHED = 1032
STATUS_BATTERY_VERY_LOW = 1033
STATUS_SPITTOON_FULL = 1034
STATUS_OUTPUT_TRAY_CLOSED = 1035
STATUS_MANUAL_FEED_BLOCKED = 1036
STATUS_REAR_FEED_BLOCKED = 1037
STATUS_TRAY2_OUT_OF_PAPER = 1038
STATUS_UNABLE_TO_LOAD_FROM_LOCKED_TRAY = 1039
STATUS_NON_HP_APPROVED_INK = 1040
STATUS_PEN_PAPER_CALIBRATION = 1041
STATUS_MEDIA_TYPE_MISMATCH = 1042
STATUS_CUSTOM_MEDIA_MISMATCH = 1043
STATUS_PEN_CLEANING = 1044
STATUS_PEN_CHECKING = 1045


# agent info

# 'kind'
AGENT_KIND_NONE = 0
AGENT_KIND_HEAD = 1
AGENT_KIND_SUPPLY = 2
AGENT_KIND_HEAD_AND_SUPPLY = 3

# 'type'
AGENT_TYPE_NONE = 0
AGENT_TYPE_BLACK = 1
AGENT_TYPE_CMY = 2
AGENT_TYPE_KCM = 3
AGENT_TYPE_CYAN = 4
AGENT_TYPE_MAGENTA = 5
AGENT_TYPE_YELLOW = 6
AGENT_TYPE_CYAN_LOW = 7
AGENT_TYPE_MAGENTA_LOW = 8
AGENT_TYPE_YELLOW_LOW = 9
AGENT_TYPE_GGK = 10
AGENT_TYPE_BLUE = 11
AGENT_TYPE_ERROR = 0x3f

REVISION_2_TYPE_MAP = { 0 : AGENT_TYPE_NONE,
                        1 : AGENT_TYPE_BLACK,
                        2 : AGENT_TYPE_CYAN,
                        3 : AGENT_TYPE_MAGENTA,
                        4 : AGENT_TYPE_YELLOW,
                        5 : AGENT_TYPE_BLACK,
                        6 : AGENT_TYPE_CYAN,
                        7 : AGENT_TYPE_MAGENTA,
                        8 : AGENT_TYPE_YELLOW,
                       }
                            


# 'health'
AGENT_HEALTH_OK = 0
AGENT_HEALTH_MISINSTALLED = 1
AGENT_HEALTH_INCORRECT = 2
AGENT_HEALTH_FAILED = 3

# 'level'
AGENT_LEVEL_TRIGGER_SUFFICIENT_0 = 0
AGENT_LEVEL_TRIGGER_SUFFICIENT_1 = 1
AGENT_LEVEL_TRIGGER_SUFFICIENT_2 = 2
AGENT_LEVEL_TRIGGER_SUFFICIENT_3 = 3
AGENT_LEVEL_TRIGGER_SUFFICIENT_4 = 4
AGENT_LEVEL_TRIGGER_MAY_BE_LOW = 5
AGENT_LEVEL_TRIGGER_PROBABLY_OUT = 6
AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT = 7

STATUS_UNKNOWN = { 'revision' : STATUS_REV_UNKNOWN,
                   'agents' : [],
                   'status' : STATUS_UNKNOWN  
                 }


status_xlate  =  { 0x01 : STATUS_BUSY,
                   0x00 : STATUS_IDLE,
                   0x02 : STATUS_PRINTING,
                   0x03 : STATUS_TURNING_OFF,
                   0x04 : STATUS_REPORT_PRINTING,
                   0x05 : STATUS_CANCELING,
                   0x06 : STATUS_IO_STALL,
                   0x07 : STATUS_DRY_WAIT_TIME,
                   0x08 : STATUS_PEN_CHANGE,
                   0x09 : STATUS_OUT_OF_PAPER,
                   0x0a : STATUS_BANNER_EJECT_NEEDED,
                   0x0b : STATUS_BANNER_MISMATCH,
                   0x0c : STATUS_PHOTO_MISMATCH,
                   0x0d : STATUS_DUPLEX_MISMATCH,
                   0x0e : STATUS_MEDIA_JAM,
                   0x0f : STATUS_CARRIAGE_STALL,
                   0x10 : STATUS_PAPER_STALL,
                   0x11 : STATUS_PEN_FAILURE,
                   0x12 : STATUS_HARD_ERROR,
                   0x13 : STATUS_POWER_DOWN,
                   0x14 : STATUS_FRONT_PANEL_TEST,
                   0x15 : STATUS_CLEAN_OUT_TRAY_MISSING,
                   0x16 : STATUS_OUTPUT_BIN_FULL,
                   0x17 : STATUS_MEDIA_SIZE_MISMATCH,
                   0x18 : STATUS_MANUAL_DUPLEX_BLOCK,
                   0x19 : STATUS_SERVICE_STALL,
                   0x1a : STATUS_OUT_OF_INK,
                   0x1b : STATUS_LIO_ERROR,
                   0x1c : STATUS_PUMP_STALL,
                   0x1d : STATUS_TRAY2_MISSING,
                   0x1e : STATUS_DUPLEXER_MISSING,
                   0x1f : STATUS_REAR_TRAY_MISSING,
                   0x20 : STATUS_PEN_NOT_LATCHED,
                   0x21 : STATUS_BATTERY_VERY_LOW,
                   0x22 : STATUS_SPITTOON_FULL,
                   0x23 : STATUS_OUTPUT_TRAY_CLOSED,
                   0x24 : STATUS_MANUAL_FEED_BLOCKED,
                   0x25 : STATUS_REAR_FEED_BLOCKED,
                   0x26 : STATUS_TRAY2_OUT_OF_PAPER,
                   0x27 : STATUS_UNABLE_TO_LOAD_FROM_LOCKED_TRAY,
                   0x28 : STATUS_NON_HP_APPROVED_INK,
                   0x29 : STATUS_PEN_PAPER_CALIBRATION,
                   0x2a : STATUS_MEDIA_TYPE_MISMATCH,
                   0x2b : STATUS_CUSTOM_MEDIA_MISMATCH,
                   0x2c : STATUS_PEN_CLEANING,
                   0x2d : STATUS_PEN_CHECKING,
                 }
                   

NUM_PEN_POS = { STATUS_REV_00 : 16,
                STATUS_REV_01 : 16,
                STATUS_REV_02 : 16,
                STATUS_REV_03 : 18,
                STATUS_REV_04 : 22 } 

PEN_DATA_SIZE = { STATUS_REV_00 : 8,
                  STATUS_REV_01 : 8,
                  STATUS_REV_02 : 4,
                  STATUS_REV_03 : 8,
                  STATUS_REV_04 : 8 } 

def parseSStatus( s, z='' ):
    #PEN_DATA_SIZE = 8
    Z_SIZE = 6

    z1 = []
    if len(z) > 0:
        z_fields = z.split(',')

        for z_field in z_fields:
            
            if len(z_field) > 2 and z_field[:2] == '05':
                z1s = z_field[2:]
                z1 = [ int(x, 16) for x in z1s ]

    s1 = [ int(x, 16) for x in s ]
    revision = s1[1]

    assert STATUS_REV_00 <= revision <= STATUS_REV_04

    top_door = bool( s1[2] & 0x8L ) + s1[2] & 0x1L
    supply_door = bool( s1[3] & 0x8L ) + s1[3] & 0x1L
    duplexer = bool( s1[4] & 0xcL ) +  s1[4] & 0x1L
    photo_tray = bool( s1[5] & 0x8L ) + s1[5] & 0x1L

    if revision == STATUS_REV_02:
        in_tray1 = bool( s1[6] & 0x8L ) + s1[6] & 0x1L
        in_tray2 = bool( s1[7] & 0x8L ) + s1[7] & 0x1L
    else:
        in_tray1 = bool( s1[6] & 0x8L )
        in_tray2 = bool( s1[7] & 0x8L )

    media_path = bool( s1[8] & 0x8L ) + ( s1[8] & 0x1L ) + ( ( bool( s1[18] & 0x2L ) )<<1 )
    status_byte = ( s1[16]<<4 ) + s1[17]
    status = status_xlate.get( status_byte, STATUS_IDLE )

    pens, pen, c, d = [], {}, NUM_PEN_POS[ revision ]+1, 0
    num_pens = s1[ NUM_PEN_POS[ revision ] ]

    index = 0
    #print num_pens
    pen_data_size = PEN_DATA_SIZE[revision]
    
    #print 'num_pens:', num_pens
    
    for p in range( num_pens ):
        #print
        #print 'slice:',s[c:c+pen_data_size ]
    
        info = long( s[c:c+pen_data_size], 16 )
        #print 'hex info:', '%x' % info, '(%d)' % info
        #print 'index:', index
        
        pen[ 'index' ] = index
        
        if revision == STATUS_REV_02: # 4 bytes
            pen[ 'type' ] = REVISION_2_TYPE_MAP.get( int( ( info & 0xf000L ) >> 12L ), 0 )
            #print 'type:', pen[ 'type' ]
            if index < (num_pens / 2):
                pen[ 'kind' ] = AGENT_KIND_HEAD
            else:
                pen[ 'kind' ] = AGENT_KIND_SUPPLY
            #print 'kind', pen[ 'kind' ]
            
            pen[ 'level-trigger' ] = int ( ( info & 0x0e00L ) >> 9L )
            pen[ 'health' ] = int( ( info & 0x0180L ) >> 7L )
            pen[ 'level' ] = int( info & 0x007fL )
            
        else: # 8 bytes
            pen[ 'kind' ] = bool( info & 0x80000000L ) + ( ( bool( info & 0x40000000L ) )<<1L )
            pen[ 'type' ] = int( ( info & 0x3f000000L ) >> 24L )
            pen[ 'level-trigger' ] = int( ( info & 0x70000L ) >> 16L )
            pen[ 'health' ] = int( ( info & 0xc000L ) >> 14L )
            pen[ 'level' ] = int( info & 0xffL )
        
        if len(z1) > 0:
            pen[ 'dvc' ] = long( z1s[d+1:d+5], 16 )
            pen[ 'virgin' ] = bool( z1[ d+5 ] & 0x8L )
            pen[ 'hp-ink' ] = bool( z1[ d+5 ] & 0x4L )
            pen[ 'known' ] = bool( z1[ d+5 ] & 0x2L )
            pen[ 'ack' ] = bool( z1[ d+5 ] & 0x1L )

        index += 1
        pens.append( pen )
        pen = {}
        c += pen_data_size
        d += Z_SIZE

    return { 'revision' :    revision,
             'agents' :      pens,  
             'top-door' :    top_door,  
             'status' :      status,
             'supply-door' : supply_door, 
             'duplexer' :    duplexer,
             'photo-tray' :  photo_tray, 
             'in-tray1' :    in_tray1, 
             'in-tray2' :    in_tray2, 
             'media-path' :  media_path,
           } 

vstatus_xlate  = { 'busy' : STATUS_BUSY,
                   'idle' : STATUS_IDLE,
                   'prnt' : STATUS_PRINTING,
                   'offf' : STATUS_TURNING_OFF,
                   'rprt' : STATUS_REPORT_PRINTING,
                   'cncl' : STATUS_CANCELING,
                   'iost' : STATUS_IO_STALL,
                   'dryw' : STATUS_DRY_WAIT_TIME,
                   'penc' : STATUS_PEN_CHANGE,
                   'oopa' : STATUS_OUT_OF_PAPER,
                   'bnej' : STATUS_BANNER_EJECT_NEEDED,
                   'bnmz' : STATUS_BANNER_MISMATCH,
                   'phmz' : STATUS_PHOTO_MISMATCH,
                   'dpmz' : STATUS_DUPLEX_MISMATCH,
                   'pajm' : STATUS_MEDIA_JAM,
                   'cars' : STATUS_CARRIAGE_STALL,
                   'paps' : STATUS_PAPER_STALL,
                   'penf' : STATUS_PEN_FAILURE,
                   'erro' : STATUS_HARD_ERROR,
                   'pwdn' : STATUS_POWER_DOWN,
                   'fpts' : STATUS_FRONT_PANEL_TEST,
                   'clno' : STATUS_CLEAN_OUT_TRAY_MISSING }

# $HB0$NC0,ff,DN,IDLE,CUT,K0,C0,DP,NR,KP092,CP041
#     0    1  2  3    4   5  6  7  8  9     10
def parseVStatus( s ):
    pens, pen, c = [], {}, 0 
    fields = s.split(',')
    for p in fields[0]:
        if c == 0:
            assert p == '$'
            c += 1
        elif c == 1:
            if p in ( 'a', 'A' ): 
                pen[ 'type' ], pen[ 'kind' ] = AGENT_TYPE_NONE, AGENT_KIND_NONE
            c += 1
        elif c == 2:
            pen[ 'health' ] = AGENT_HEALTH_OK
            pen[ 'kind' ] = AGENT_KIND_HEAD_AND_SUPPLY
            if   p in ( 'b', 'B' ): pen[ 'type' ] = AGENT_TYPE_BLACK
            elif p in ( 'c', 'C' ): pen[ 'type' ] = AGENT_TYPE_CMY
            elif p in ( 'd', 'D' ): pen[ 'type' ] = AGENT_TYPE_KCM
            elif p in ( 'u', 'U' ): pen[ 'type' ], pen[ 'health' ] = AGENT_TYPE_NONE, AGENT_HEALTH_MISINSTALLED
            c += 1
        elif c == 3:
            if p == '0': pen[ 'state' ] = 1
            else: pen[ 'state' ] = 0
            
            pen[ 'level' ] = 0
            i = 8

            while True:
                try:
                    f = fields[i]
                except IndexError:
                    break
                else:
                    if f[:2] == 'KP' and pen[ 'type' ] == AGENT_TYPE_BLACK:
                        pen[ 'level' ] = int( f[2:] )
                    elif f[:2] == 'CP' and pen[ 'type' ] == AGENT_TYPE_CMY:
                        pen[ 'level' ] = int( f[2:] )
                i += 1
                
            pens.append( pen )
            pen = {}
            c = 0

    if fields[2] == 'DN':
        top_lid = 1
    else:
        top_lid = 2
        
    status = vstatus_xlate.get( fields[3].lower(), STATUS_IDLE )

    return { 'revision' :   STATUS_REV_V,
             'agents' :     pens,  
             'top-lid' :    top_lid,  
             'status' :     status,
             'supply-lid' : SUPPLY_DOOR_NOT_PRESENT,
             'duplexer' :   DUPLEXER_NOT_PRESENT, 
             'photo-tray' : PHOTO_TRAY_NOT_PRESENT, 
             'in-tray1' :   IN_TRAY_NOT_PRESENT, 
             'in-tray2' :   IN_TRAY_NOT_PRESENT, 
             'media-path' : MEDIA_PATH_CUT_SHEET, # ?
           } 
             
def parseStatus( DeviceID ):
    if 'VSTATUS' in DeviceID:
         return parseVStatus( DeviceID[ 'VSTATUS' ] )
    elif 'S' in DeviceID:
        return parseSStatus( DeviceID[ 'S' ], DeviceID.get( 'Z', '' ) )
    else:
        return STATUS_UNKNOWN


AGENT_CONFIG_NONE = 0
AGENT_CONFIG_BLACK_ONLY = 1
AGENT_CONFIG_PHOTO_ONLY = 2
AGENT_CONFIG_COLOR_ONLY = 3
AGENT_CONFIG_COLOR_AND_BLACK = 4
AGENT_CONFIG_COLOR_AND_PHOTO = 5
AGENT_CONFIG_INVALID = 99

# this works for 2 pen products that allow 1 or 2 pens inserted 
# from: k, kcm, cmy    
def getPenConfiguration( s ): # s=status dict from parsed device ID
    pen1_type = s['agents'][0]['type']
    pen2_type = s['agents'][1]['type']
    one_pen = False
    
    if pen1_type == AGENT_TYPE_NONE and pen2_type == AGENT_TYPE_NONE:
        #log.debug( "No pens" )
        return AGENT_CONFIG_NONE
    
    if pen1_type == AGENT_TYPE_NONE or pen2_type == AGENT_TYPE_NONE:
        #log.debug( "1 pen" )
        
        if pen1_type == AGENT_TYPE_BLACK or pen2_type == AGENT_TYPE_BLACK:
            #log.debug( "Black pen only" )
            return AGENT_CONFIG_BLACK_ONLY
        
        elif pen1_type == AGENT_TYPE_CMY or pen2_type == AGENT_TYPE_CMY:
            #log.debug( "Color pen only" )
            return AGENT_CONFIG_COLOR_ONLY
        
        elif pen1_type == AGENT_TYPE_KCM or pen2_type == AGENT_TYPE_KCM:
            #log.debug( "Photo pen only" )
            return AGENT_CONFIG_PHOTO_ONLY
            
        else:
            #log.debug( "Invalid pen config" )
            return AGENT_CONFIG_INVALID
            
    else:
        if pen1_type == AGENT_TYPE_BLACK or pen2_type == AGENT_TYPE_BLACK:
            #log.debug( "Color and black pens" )
            return AGENT_CONFIG_COLOR_AND_BLACK
        
        elif pen1_type == AGENT_TYPE_KCM or pen2_type == AGENT_TYPE_KCM:
            #log.debug( "Color and photo pens" )
            return AGENT_CONFIG_COLOR_AND_PHOTO
            
        else:
            #log.debug( "Invalid pen config" )
            return PEN_CONFIG_INVALID
        
