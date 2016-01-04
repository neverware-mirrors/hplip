# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2006 Hewlett-Packard Development Company, L.P.
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

from __future__ import division

# StdLib
import struct, xml.parsers.expat, cStringIO

# Local
from g import *
from codes import *
import pml, utils


"""
status dict structure:
    { 'revision' :     STATUS_REV_00 .. STATUS_REV_04,
      'agents' :       [ list of pens/agents/supplies (dicts) ],
      'top-door' :     TOP_DOOR_NOT_PRESENT | TOP_DOOR_CLOSED | TOP_DOOR_OPEN,
      'status-code' :  STATUS_...,
      'supply-door' :  SUPPLY_DOOR_NOT_PRESENT | SUPPLY_DOOR_CLOSED | SUPPLY_DOOR_OPEN.
      'duplexer' :     DUPLEXER_NOT_PRESENT | DUPLEXER_DOOR_CLOSED | DUPLEXER_DOOR_OPEN,
      'photo_tray' :   PHOTO_TRAY_NOT_PRESENT | PHOTO_TRAY_ENGAGED | PHOTO_TRAY_NOT_ENGAGED,
      'in-tray1' :     IN_TRAY_NOT_PRESENT | IN_TRAY_CLOSED | IN_TRAY_OPEN (| IN_TRAY_DEFAULT | IN_TRAY_LOCKED)*,
      'in-tray2' :     IN_TRAY_NOT_PRESENT | IN_TRAY_CLOSED | IN_TRAY_OPEN (| IN_TRAY_DEFAULT | IN_TRAY_LOCKED)*,
      'media-path' :   MEDIA_PATH_NOT_PRESENT | MEDIA_PATH_CUT_SHEET | MEDIA_PATH_BANNER | MEDIA_PATH_PHOTO,
    }

    * S:02 only

agent dict structure: (pens/supplies/agents/etc)
    { 'kind' :           AGENT_KIND_NONE ... AGENT_KIND_ADF_KIT,
      'type' :           TYPE_BLACK ... AGENT_TYPE_UNSPECIFIED,      # aka color
      'health' :         AGENT_HEALTH_OK ... AGENT_HEALTH_UNKNOWN,
      'level' :          0 ... 100,
      'level-trigger' :  AGENT_LEVEL_TRIGGER_SUFFICIENT_0 ... AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
    }
"""



# 'revision'
STATUS_REV_00 = 0x00
STATUS_REV_01 = 0x01
STATUS_REV_02 = 0x02
STATUS_REV_03 = 0x03
STATUS_REV_04 = 0x04
STATUS_REV_V  = 0xff
STATUS_REV_UNKNOWN = 0xfe

vstatus_xlate  = {'busy' : STATUS_PRINTER_BUSY,
                   'idle' : STATUS_PRINTER_IDLE,
                   'prnt' : STATUS_PRINTER_PRINTING,
                   'offf' : STATUS_PRINTER_TURNING_OFF,
                   'rprt' : STATUS_PRINTER_REPORT_PRINTING,
                   'cncl' : STATUS_PRINTER_CANCELING,
                   'iost' : STATUS_PRINTER_IO_STALL,
                   'dryw' : STATUS_PRINTER_DRY_WAIT_TIME,
                   'penc' : STATUS_PRINTER_PEN_CHANGE,
                   'oopa' : STATUS_PRINTER_OUT_OF_PAPER,
                   'bnej' : STATUS_PRINTER_BANNER_EJECT,
                   'bnmz' : STATUS_PRINTER_BANNER_MISMATCH,
                   'phmz' : STATUS_PRINTER_PHOTO_MISMATCH,
                   'dpmz' : STATUS_PRINTER_DUPLEX_MISMATCH,
                   'pajm' : STATUS_PRINTER_MEDIA_JAM,
                   'cars' : STATUS_PRINTER_CARRIAGE_STALL,
                   'paps' : STATUS_PRINTER_PAPER_STALL,
                   'penf' : STATUS_PRINTER_PEN_FAILURE,
                   'erro' : STATUS_PRINTER_HARD_ERROR,
                   'pwdn' : STATUS_PRINTER_POWER_DOWN,
                   'fpts' : STATUS_PRINTER_FRONT_PANEL_TEST,
                   'clno' : STATUS_PRINTER_CLEAN_OUT_TRAY_MISSING}

REVISION_2_TYPE_MAP = {0 : AGENT_TYPE_NONE,
                        1 : AGENT_TYPE_BLACK,
                        2 : AGENT_TYPE_CYAN,
                        3 : AGENT_TYPE_MAGENTA,
                        4 : AGENT_TYPE_YELLOW,
                        5 : AGENT_TYPE_BLACK,
                        6 : AGENT_TYPE_CYAN,
                        7 : AGENT_TYPE_MAGENTA,
                        8 : AGENT_TYPE_YELLOW,
                       }

STATUS_BLOCK_UNKNOWN = {'revision' : STATUS_REV_UNKNOWN,
                         'agents' : [],
                         'status-code' : STATUS_UNKNOWN,
                       }

NUM_PEN_POS = {STATUS_REV_00 : 16,
                STATUS_REV_01 : 16,
                STATUS_REV_02 : 16,
                STATUS_REV_03 : 18,
                STATUS_REV_04 : 22}

PEN_DATA_SIZE = {STATUS_REV_00 : 8,
                  STATUS_REV_01 : 8,
                  STATUS_REV_02 : 4,
                  STATUS_REV_03 : 8,
                  STATUS_REV_04 : 8}

STATUS_POS = {STATUS_REV_00 : 14,
               STATUS_REV_01 : 14,
               STATUS_REV_02 : 14,
               STATUS_REV_03 : 16,
               STATUS_REV_04 : 20}

def parseSStatus(s, z=''):
    Z_SIZE = 6

    z1 = []
    if len(z) > 0:
        z_fields = z.split(',')

        for z_field in z_fields:

            if len(z_field) > 2 and z_field[:2] == '05':
                z1s = z_field[2:]
                z1 = [int(x, 16) for x in z1s]

    s1 = [int(x, 16) for x in s]

    revision = s1[1]

    assert STATUS_REV_00 <= revision <= STATUS_REV_04

    top_door = bool(s1[2] & 0x8L) + s1[2] & 0x1L
    supply_door = bool(s1[3] & 0x8L) + s1[3] & 0x1L
    duplexer = bool(s1[4] & 0xcL) +  s1[4] & 0x1L
    photo_tray = bool(s1[5] & 0x8L) + s1[5] & 0x1L

    if revision == STATUS_REV_02:
        in_tray1 = bool(s1[6] & 0x8L) + s1[6] & 0x1L
        in_tray2 = bool(s1[7] & 0x8L) + s1[7] & 0x1L
    else:
        in_tray1 = bool(s1[6] & 0x8L)
        in_tray2 = bool(s1[7] & 0x8L)

    media_path = bool(s1[8] & 0x8L) + (s1[8] & 0x1L) + ((bool(s1[18] & 0x2L))<<1)
    status_pos = STATUS_POS[revision]
    status_byte = (s1[status_pos]<<4) + s1[status_pos + 1]
    stat = status_byte + STATUS_PRINTER_BASE

    pens, pen, c, d = [], {}, NUM_PEN_POS[revision]+1, 0
    num_pens = s1[NUM_PEN_POS[revision]]
    log.debug("Num pens=%d" % num_pens)
    index = 0
    pen_data_size = PEN_DATA_SIZE[revision]

    for p in range(num_pens):
        info = long(s[c : c + pen_data_size], 16)

        pen['index'] = index

        if pen_data_size == 4:
            pen['type'] = REVISION_2_TYPE_MAP.get(int((info & 0xf000L) >> 12L), 0)
            if index < (num_pens / 2):
                pen['kind'] = AGENT_KIND_HEAD
            else:
                pen['kind'] = AGENT_KIND_SUPPLY

            pen['level-trigger'] = int ((info & 0x0e00L) >> 9L)
            pen['health'] = int((info & 0x0180L) >> 7L)
            pen['level'] = int(info & 0x007fL)
            pen['id'] = 0x1f

        elif pen_data_size == 8:
            pen['kind'] = bool(info & 0x80000000L) + ((bool(info & 0x40000000L))<<1L)
            pen['type'] = int((info & 0x3f000000L) >> 24L)
            pen['id'] = int((info & 0xf80000) >> 19L)
            pen['level-trigger'] = int((info & 0x70000L) >> 16L)
            pen['health'] = int((info & 0xc000L) >> 14L)
            pen['level'] = int(info & 0xffL)

        else:
            log.error("Pen data size error")

        if len(z1) > 0:
            pen['dvc'] = long(z1s[d+1:d+5], 16)
            pen['virgin'] = bool(z1[d+5] & 0x8L)
            pen['hp-ink'] = bool(z1[d+5] & 0x4L)
            pen['known'] = bool(z1[d+5] & 0x2L)
            pen['ack'] = bool(z1[d+5] & 0x1L)

        index += 1
        pens.append(pen)
        pen = {}
        c += pen_data_size
        d += Z_SIZE

    return {'revision' :    revision,
             'agents' :      pens,
             'top-door' :    top_door,
             'status-code' : stat,
             'supply-door' : supply_door,
             'duplexer' :    duplexer,
             'photo-tray' :  photo_tray,
             'in-tray1' :    in_tray1,
             'in-tray2' :    in_tray2,
             'media-path' :  media_path,
           }



# $HB0$NC0,ff,DN,IDLE,CUT,K0,C0,DP,NR,KP092,CP041
#     0    1  2  3    4   5  6  7  8  9     10
def parseVStatus(s):
    pens, pen, c = [], {}, 0
    fields = s.split(',')
    for p in fields[0]:
        if c == 0:
            assert p == '$'
            c += 1
        elif c == 1:
            if p in ('a', 'A'):
                pen['type'], pen['kind'] = AGENT_TYPE_NONE, AGENT_KIND_NONE
            c += 1
        elif c == 2:
            pen['health'] = AGENT_HEALTH_OK
            pen['kind'] = AGENT_KIND_HEAD_AND_SUPPLY
            if   p in ('b', 'B'): pen['type'] = AGENT_TYPE_BLACK
            elif p in ('c', 'C'): pen['type'] = AGENT_TYPE_CMY
            elif p in ('d', 'D'): pen['type'] = AGENT_TYPE_KCM
            elif p in ('u', 'U'): pen['type'], pen['health'] = AGENT_TYPE_NONE, AGENT_HEALTH_MISINSTALLED
            c += 1
        elif c == 3:
            if p == '0': pen['state'] = 1
            else: pen['state'] = 0

            pen['level'] = 0
            i = 8

            while True:
                try:
                    f = fields[i]
                except IndexError:
                    break
                else:
                    if f[:2] == 'KP' and pen['type'] == AGENT_TYPE_BLACK:
                        pen['level'] = int(f[2:])
                    elif f[:2] == 'CP' and pen['type'] == AGENT_TYPE_CMY:
                        pen['level'] = int(f[2:])
                i += 1

            pens.append(pen)
            pen = {}
            c = 0

    if fields[2] == 'DN':
        top_lid = 1
    else:
        top_lid = 2

    stat = vstatus_xlate.get(fields[3].lower(), STATUS_PRINTER_IDLE)

    return {'revision' :   STATUS_REV_V,
             'agents' :     pens,
             'top-lid' :    top_lid,
             'status-code': stat,
             'supply-lid' : SUPPLY_DOOR_NOT_PRESENT,
             'duplexer' :   DUPLEXER_NOT_PRESENT,
             'photo-tray' : PHOTO_TRAY_NOT_PRESENT,
             'in-tray1' :   IN_TRAY_NOT_PRESENT,
             'in-tray2' :   IN_TRAY_NOT_PRESENT,
             'media-path' : MEDIA_PATH_CUT_SHEET, # ?
           }

def parseStatus(DeviceID):
    if 'VSTATUS' in DeviceID:
         return parseVStatus(DeviceID['VSTATUS'])
    elif 'S' in DeviceID:
        return parseSStatus(DeviceID['S'], DeviceID.get('Z', ''))
    else:
        return STATUS_BLOCK_UNKNOWN



def LaserJetDeviceStatusToPrinterStatus(device_status, printer_status, detected_error_state):
    stat = STATUS_PRINTER_IDLE

    if device_status in (pml.DEVICE_STATUS_WARNING, pml.DEVICE_STATUS_DOWN):

        if detected_error_state & pml.DETECTED_ERROR_STATE_LOW_PAPER_MASK and \
            not (detected_error_state & pml.DETECTED_ERROR_STATE_NO_PAPER_MASK):
            stat = STATUS_PRINTER_LOW_PAPER

        elif detected_error_state & pml.DETECTED_ERROR_STATE_NO_PAPER_MASK:
            stat = STATUS_PRINTER_OUT_OF_PAPER

        elif detected_error_state & pml.DETECTED_ERROR_STATE_DOOR_OPEN_MASK:
            stat = STATUS_PRINTER_DOOR_OPEN

        elif detected_error_state & pml.DETECTED_ERROR_STATE_JAMMED_MASK:
            stat = STATUS_PRINTER_MEDIA_JAM

        elif detected_error_state & pml.DETECTED_ERROR_STATE_OUT_CART_MASK:
            stat = STATUS_PRINTER_NO_TONER

        elif detected_error_state & pml.DETECTED_ERROR_STATE_LOW_CART_MASK:
            stat = STATUS_PRINTER_LOW_TONER

        elif detected_error_state == pml.DETECTED_ERROR_STATE_SERVICE_REQUEST_MASK:
            stat = STATUS_PRINTER_SERVICE_REQUEST

        elif detected_error_state & pml.DETECTED_ERROR_STATE_OFFLINE_MASK:
            stat = STATUS_PRINTER_OFFLINE

    else:

        if printer_status == pml.PRINTER_STATUS_IDLE:
            stat = STATUS_PRINTER_IDLE

        elif printer_status == pml.PRINTER_STATUS_PRINTING:
            stat = STATUS_PRINTER_PRINTING

        elif printer_status == pml.PRINTER_STATUS_WARMUP:
            stat = STATUS_PRINTER_WARMING_UP

    return stat

# Map from ISO 10175/10180 to HPLIP types
COLORANT_INDEX_TO_AGENT_TYPE_MAP = {
                                    'other' :   AGENT_TYPE_UNSPECIFIED,
                                    'unknown' : AGENT_TYPE_UNSPECIFIED,
                                    'blue' :    AGENT_TYPE_BLUE,
                                    'cyan' :    AGENT_TYPE_CYAN,
                                    'magenta':  AGENT_TYPE_MAGENTA,
                                    'yellow' :  AGENT_TYPE_YELLOW,
                                    'black' :   AGENT_TYPE_BLACK,
                                   }

MARKER_SUPPLES_TYPE_TO_AGENT_KIND_MAP = {
    pml.OID_MARKER_SUPPLIES_TYPE_OTHER :              AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_UNKNOWN :            AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_TONER :              AGENT_KIND_TONER_CARTRIDGE,
    pml.OID_MARKER_SUPPLIES_TYPE_WASTE_TONER :        AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_INK :                AGENT_KIND_SUPPLY,
    pml.OID_MARKER_SUPPLIES_TYPE_INK_CART :           AGENT_KIND_HEAD_AND_SUPPLY,
    pml.OID_MARKER_SUPPLIES_TYPE_INK_RIBBON :         AGENT_KIND_HEAD_AND_SUPPLY,
    pml.OID_MARKER_SUPPLIES_TYPE_WASTE_INK :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_OPC :                AGENT_KIND_DRUM_KIT,
    pml.OID_MARKER_SUPPLIES_TYPE_DEVELOPER :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER_OIL :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_SOLID_WAX :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_RIBBON_WAX :         AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_WASTE_WAX :          AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER :              AGENT_KIND_MAINT_KIT,
    pml.OID_MARKER_SUPPLIES_TYPE_CORONA_WIRE :        AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER_OIL_WICK :     AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_CLEANER_UNIT :       AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER_CLEANING_PAD : AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_TRANSFER_UNIT :      AGENT_KIND_TRANSFER_KIT,
    pml.OID_MARKER_SUPPLIES_TYPE_TONER_CART :         AGENT_KIND_TONER_CARTRIDGE,
    pml.OID_MARKER_SUPPLIES_TYPE_FUSER_OILER :        AGENT_KIND_UNKNOWN,
    pml.OID_MARKER_SUPPLIES_TYPE_ADF_MAINT_KIT :      AGENT_KIND_ADF_KIT,
}


def StatusType3( dev, parsedID ): # LaserJet Status (PML/SNMP)
    dev.openPML()
    result_code, on_off_line = dev.getPML( pml.OID_ON_OFF_LINE, pml.INT_SIZE_BYTE )
    result_code, sleep_mode = dev.getPML( pml.OID_SLEEP_MODE, pml.INT_SIZE_BYTE )
    result_code, printer_status = dev.getPML( pml.OID_PRINTER_STATUS, pml.INT_SIZE_BYTE )
    result_code, device_status = dev.getPML( pml.OID_DEVICE_STATUS, pml.INT_SIZE_BYTE )
    result_code, cover_status = dev.getPML( pml.OID_COVER_STATUS, pml.INT_SIZE_BYTE )
    result_code,  value = dev.getPML( pml.OID_DETECTED_ERROR_STATE )
    
    try:
        detected_error_state = struct.unpack( 'B', value[0])[0]
    except IndexError:
        detected_error_state = pml.DETECTED_ERROR_STATE_OFFLINE_MASK
    
    agents, x = [], 1

    while True:
        log.debug( "%s Agent: %d %s" % ("*"*10, x, "*"*10))
        log.debug("OID_MARKER_SUPPLIES_TYPE_%d:" % x)
        oid = ( pml.OID_MARKER_SUPPLIES_TYPE_x % x, pml.OID_MARKER_SUPPLIES_TYPE_x_TYPE )
        result_code, value = dev.getPML( oid, pml.INT_SIZE_BYTE )

        if result_code != ERROR_SUCCESS or value is None:
            log.debug("End of supply information.")
            break

        for a in MARKER_SUPPLES_TYPE_TO_AGENT_KIND_MAP:
            if value == a:
                agent_kind = MARKER_SUPPLES_TYPE_TO_AGENT_KIND_MAP[a]
                break
        else:
            agent_kind = AGENT_KIND_UNKNOWN

        # TODO: Deal with printers that return -1 and -2 for level and max (LJ3380)
        
        log.debug("OID_MARKER_SUPPLIES_LEVEL_%d:" % x)
        oid = ( pml.OID_MARKER_SUPPLIES_LEVEL_x % x, pml.OID_MARKER_SUPPLIES_LEVEL_x_TYPE )
        result_code, agent_level = dev.getPML( oid )

        if result_code != ERROR_SUCCESS:
            log.debug("Failed")
            break
            
        log.debug( 'agent%d-level: %d' % ( x, agent_level ) )
        log.debug("OID_MARKER_SUPPLIES_MAX_%d:" % x)
        oid = ( pml.OID_MARKER_SUPPLIES_MAX_x % x, pml.OID_MARKER_SUPPLIES_MAX_x_TYPE )
        result_code, agent_max = dev.getPML( oid )
        
        if agent_max == 0: agent_max = 1

        if result_code != ERROR_SUCCESS:
            log.debug("Failed")
            break

        log.debug( 'agent%d-max: %d' % ( x, agent_max ) )
        log.debug("OID_MARKER_SUPPLIES_COLORANT_INDEX_%d:" % x)
        oid = ( pml.OID_MARKER_SUPPLIES_COLORANT_INDEX_x % x, pml.OID_MARKER_SUPPLIES_COLORANT_INDEX_x_TYPE )
        result_code, colorant_index = dev.getPML( oid )

        if result_code != ERROR_SUCCESS: # 3080, 3055 will fail here
            log.debug("Failed")
            agent_type = AGENT_TYPE_BLACK
            #break
        else:
            log.debug("Colorant index: %d" % colorant_index)

            log.debug("OID_MARKER_COLORANT_VALUE_%d" % x)
            oid = ( pml.OID_MARKER_COLORANT_VALUE_x % colorant_index, pml.OID_MARKER_COLORANT_VALUE_x_TYPE )
            result_code, colorant_value = dev.getPML( oid )
    
            if result_code != ERROR_SUCCESS:
                log.debug("Failed. Defaulting to black.")
                agent_type = AGENT_TYPE_BLACK
            #else:
            if 1:
                if agent_kind in (AGENT_KIND_MAINT_KIT, AGENT_KIND_ADF_KIT,
                                  AGENT_KIND_DRUM_KIT, AGENT_KIND_TRANSFER_KIT):
        
                    agent_type = AGENT_TYPE_UNSPECIFIED
        
                else:
                    agent_type = AGENT_TYPE_BLACK
        
                    if result_code != ERROR_SUCCESS:
                        log.debug("OID_MARKER_SUPPLIES_DESCRIPTION_%d:" % x)
                        oid = (pml.OID_MARKER_SUPPLIES_DESCRIPTION_x % x, pml.OID_MARKER_SUPPLIES_DESCRIPTION_x_TYPE)
                        result_code, colorant_value = dev.getPML( oid )
                        
                        if result_code != ERROR_SUCCESS:
                            log.debug("Failed")
                            break
        
                        if colorant_value is not None:
                            log.debug("colorant value: %s" % colorant_value)
                            colorant_value = colorant_value.lower().strip()
        
                            for c in COLORANT_INDEX_TO_AGENT_TYPE_MAP:
                                if colorant_value.find(c) >= 0:
                                    agent_type = COLORANT_INDEX_TO_AGENT_TYPE_MAP[c]
                                    break
                            else:
                                agent_type = AGENT_TYPE_BLACK
        
                    else: # SUCCESS
                        if colorant_value is not None:
                            log.debug("colorant value: %s" % colorant_value)
                            agent_type = COLORANT_INDEX_TO_AGENT_TYPE_MAP.get( colorant_value, None )
        
                        if agent_type == AGENT_TYPE_NONE:
                            if agent_kind == AGENT_KIND_TONER_CARTRIDGE:
                                agent_type = AGENT_TYPE_BLACK
                            else:
                                agent_type = AGENT_TYPE_UNSPECIFIED
    
        log.debug("OID_MARKER_STATUS_%d:" % x)
        oid = ( pml.OID_MARKER_STATUS_x % x, pml.OID_MARKER_STATUS_x_TYPE )
        result_code, agent_status = dev.getPML( oid )

        if result_code != ERROR_SUCCESS:
            log.debug("Failed")
            agent_trigger = AGENT_LEVEL_TRIGGER_SUFFICIENT_0
            agent_health = AGENT_HEALTH_OK
        else:
            agent_trigger = AGENT_LEVEL_TRIGGER_SUFFICIENT_0

            if agent_status is None:
                agent_health = AGENT_HEALTH_OK

            elif agent_status == pml.OID_MARKER_STATUS_OK:
                agent_health = AGENT_HEALTH_OK

            elif agent_status == pml.OID_MARKER_STATUS_MISINSTALLED:
                agent_health = AGENT_HEALTH_MISINSTALLED

            elif agent_status in ( pml.OID_MARKER_STATUS_LOW_TONER_CONT,
                                   pml.OID_MARKER_STATUS_LOW_TONER_STOP ):

                agent_health = AGENT_HEALTH_OK
                agent_trigger = AGENT_LEVEL_TRIGGER_MAY_BE_LOW

            else:
                agent_health = AGENT_HEALTH_OK

        agent_level = int(agent_level/agent_max * 100)

        log.debug("agent%d: kind=%d, type=%d, health=%d, level=%d, level-trigger=%d" % \
            (x, agent_kind, agent_type, agent_health, agent_level, agent_trigger))


        agents.append({'kind' : agent_kind,
                       'type' : agent_type,
                       'health' : agent_health,
                       'level' : agent_level,
                       'level-trigger' : agent_trigger,})

        x += 1
    

    log.debug("on_off_line=%d" % on_off_line)
    log.debug("sleep_mode=%d" % sleep_mode)
    log.debug("printer_status=%d" % printer_status)
    log.debug("device_status=%d" % device_status)
    log.debug("cover_status=%d" % cover_status)
    log.debug("detected_error_state=%d (0x%x)" % (detected_error_state, detected_error_state))

    stat = LaserJetDeviceStatusToPrinterStatus(device_status, printer_status, detected_error_state)

    log.debug("Printer status=%d" % stat)

    if stat == STATUS_PRINTER_DOOR_OPEN:
        supply_door = 0
    else:
        supply_door = 1

    return {'revision' :    STATUS_REV_UNKNOWN,
             'agents' :      agents,
             'top-door' :    cover_status,
             'status-code' : stat,
             'supply-door' : supply_door,
             'duplexer' :    1,
             'photo-tray' :  0,
             'in-tray1' :    1,
             'in-tray2' :    1,
             'media-path' :  1,
           }

def setup_panel_translator():
    printables = list(
"""0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~""")

    map = {}
    for x in [chr(x) for x in range(0,256)]:
        if x in printables:
            map[x] = x
        else:
            map[x] = '\x20'

    map.update({'\x10' : '\xab',
                    '\x11' : '\xbb',
                    '\x12' : '\xa3',
                    '\x13' : '\xbb',
                    '\x80' : '\xab',
                    '\x81' : '\xbb',
                    '\x82' : '\x2a',
                    '\x83' : '\x2a',
                    '\x85' : '\x2a',
                    '\xa0' : '\xab',
                    '\x1f' : '\x3f',
                    '='    : '\x20',
                })

    frm, to = '', ''
    map_keys = map.keys()
    map_keys.sort()
    for x in map_keys:
        frm = ''.join([frm, x])
        to = ''.join([to, map[x]])

    global PANEL_TRANSLATOR_FUNC
    PANEL_TRANSLATOR_FUNC = utils.Translator(frm, to)

PANEL_TRANSLATOR_FUNC = None
setup_panel_translator()


def PanelCheck(dev):
    line1, line2 = '', ''
    try:
        dev.openPML()
    except Error:
        pass
    else:

        oids = [(pml.OID_HP_LINE1, pml.OID_HP_LINE2),
                 (pml.OID_SPM_LINE1, pml.OID_SPM_LINE2)]

        for oid1, oid2 in oids:
            result, line1 = dev.getPML(oid1)

            if result < pml.ERROR_MAX_OK:
                line1 = PANEL_TRANSLATOR_FUNC(line1).rstrip()

                if '\x0a' in line1:
                    line1, line2 = line1.split('\x0a', 1)
                    break

                result, line2 = dev.getPML(oid2)

                if result < pml.ERROR_MAX_OK:
                    line2 = PANEL_TRANSLATOR_FUNC(line2).rstrip()
                    break

        #dev.closePML()

    return bool(line1 or line2), line1 or '', line2 or ''


BATTERY_HEALTH_MAP = {0 : AGENT_HEALTH_OK,
                       1 : AGENT_HEALTH_OVERTEMP,
                       2 : AGENT_HEALTH_CHARGING,
                       3 : AGENT_HEALTH_MISINSTALLED,
                       4 : AGENT_HEALTH_FAILED,
                      }


BATTERY_TRIGGER_MAP = {0 : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                        1 : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                        2 : AGENT_LEVEL_TRIGGER_PROBABLY_OUT,
                        3 : AGENT_LEVEL_TRIGGER_SUFFICIENT_4,
                        4 : AGENT_LEVEL_TRIGGER_SUFFICIENT_2,
                        5 : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                       }

BATTERY_PML_TRIGGER_MAP = {
        (100, 80)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
        (79,  60)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_1,
        (59,  40)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_2,
        (39,  30)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_3,
        (29,  20)  : AGENT_LEVEL_TRIGGER_SUFFICIENT_4,
        (19,  10)  : AGENT_LEVEL_TRIGGER_MAY_BE_LOW,
        (9,    5)  : AGENT_LEVEL_TRIGGER_PROBABLY_OUT,
        (4,   -1)  : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
        }

        
def BatteryCheck(dev, status_block):
    try_dynamic_counters = False
    
    try:
        try:
            dev.openPML()
        except Error:
            log.error("PML channel open failed.")
            try_dynamic_counters = True
        else:
            result, battery_level = dev.getPML(pml.OID_BATTERY_LEVEL)
            result, power_mode =  dev.getPML(pml.OID_POWER_MODE)
    
            if battery_level is not None and \
                power_mode is not None:
    
                if power_mode & pml.POWER_MODE_BATTERY_LEVEL_KNOWN and \
                    battery_level >= 0:
    
                    for x in BATTERY_PML_TRIGGER_MAP:
                        if x[0] >= battery_level > x[1]:
                            battery_trigger_level = BATTERY_PML_TRIGGER_MAP[x]
                            break
    
                    if power_mode & pml.POWER_MODE_CHARGING:
                        agent_health = AGENT_HEALTH_CHARGING
    
                    elif power_mode & pml.POWER_MODE_DISCHARGING:
                        agent_health = AGENT_HEALTH_DISCHARGING
    
                    else:
                        agent_health = AGENT_HEALTH_OK
    
                    status_block['agents'].append({
                                                    'kind'   : AGENT_KIND_INT_BATTERY,
                                                    'type'   : AGENT_TYPE_UNSPECIFIED,
                                                    'health' : agent_health,
                                                    'level'  : battery_level,
                                                    'level-trigger' : battery_trigger_level,
                                                    })
                else:
                    status_block['agents'].append({
                                                    'kind'   : AGENT_KIND_INT_BATTERY,
                                                    'type'   : AGENT_TYPE_UNSPECIFIED,
                                                    'health' : AGENT_HEALTH_UNKNOWN,
                                                    'level'  : 0,
                                                    'level-trigger' : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                                                    })
    
            else:
                try_dynamic_counters = True

    finally:
        dev.closePML()

    if try_dynamic_counters:

        try:
            try:
                battery_health = dev.getDynamicCounter(200)
                battery_trigger_level = dev.getDynamicCounter(201)
                battery_level = dev.getDynamicCounter(202)

                status_block['agents'].append({
                                                'kind'   : AGENT_KIND_INT_BATTERY,
                                                'type'   : AGENT_TYPE_UNSPECIFIED,
                                                'health' : BATTERY_HEALTH_MAP[battery_health],
                                                'level'  : battery_level,
                                                'level-trigger' : BATTERY_TRIGGER_MAP[battery_trigger_level],
                                                })
            except Error:
                status_block['agents'].append({
                                                'kind'   : AGENT_KIND_INT_BATTERY,
                                                'type'   : AGENT_TYPE_UNSPECIFIED,
                                                'health' : AGENT_HEALTH_UNKNOWN,
                                                'level'  : 0,
                                                'level-trigger' : AGENT_LEVEL_TRIGGER_SUFFICIENT_0,
                                                })
        finally:
            dev.closePrint()
            

# this works for 2 pen products that allow 1 or 2 pens inserted
# from: k, kcm, cmy, ggk
def getPenConfiguration(s): # s=status dict from parsed device ID
    pens = [p['type'] for p in s['agents']]

    if utils.all(pens, lambda x : x==AGENT_TYPE_NONE):
        return AGENT_CONFIG_NONE

    if AGENT_TYPE_NONE in pens:

        if AGENT_TYPE_BLACK in pens:
            return AGENT_CONFIG_BLACK_ONLY

        elif AGENT_TYPE_CMY in pens:
            return AGENT_CONFIG_COLOR_ONLY

        elif AGENT_TYPE_KCM in pens:
            return AGENT_CONFIG_PHOTO_ONLY

        elif AGENT_TYPE_GGK in pens:
            return AGENT_CONFIG_GREY_ONLY

        else:
            return AGENT_CONFIG_INVALID

    else:
        if AGENT_TYPE_BLACK in pens and AGENT_TYPE_CMY in pens:
            return AGENT_CONFIG_COLOR_AND_BLACK

        elif AGENT_TYPE_CMY in pens and AGENT_TYPE_KCM in pens:
            return AGENT_CONFIG_COLOR_AND_PHOTO

        elif AGENT_TYPE_CMY in pens and AGENT_TYPE_GGK in pens:
            return AGENT_CONFIG_COLOR_AND_GREY

        else:
            return AGENT_CONFIG_INVALID


def getFaxStatus(dev):
    tx_active, rx_active = False, False
    
    try:
        dev.openPML()
    
        result_code, tx_state = dev.getPML(pml.OID_FAXJOB_TX_STATUS)
        
        if result_code == ERROR_SUCCESS:
            if tx_state not in (pml.FAXJOB_TX_STATUS_IDLE, pml.FAXJOB_TX_STATUS_DONE):
                tx_active = True
        
        result_code, rx_state = dev.getPML(pml.OID_FAXJOB_RX_STATUS)

        if result_code == ERROR_SUCCESS:
            if rx_state not in (pml.FAXJOB_RX_STATUS_IDLE, pml.FAXJOB_RX_STATUS_DONE):
                rx_active = True
    
    finally:
        dev.closePML()
        
    return tx_active, rx_active
    

def StatusType6(dev): #  LaserJet Status (XML)
    info_device_status = cStringIO.StringIO()
    info_ssp = cStringIO.StringIO()
    
    dev.getEWSUrl("/hp/device/info_device_status.xml", info_device_status)
    dev.getEWSUrl("/hp/device/info_ssp.xml", info_ssp)
    
    info_device_status = info_device_status.getvalue()
    info_ssp = info_ssp.getvalue()
    
    device_status = {}
    ssp = {}
    
    if info_device_status:
        device_status = utils.XMLToDictParser().parseXML(info_device_status)
        log.debug_block("info_device_status", info_device_status)

    if info_ssp:
        ssp = utils.XMLToDictParser().parseXML(info_ssp)
        log.debug_block("info_spp", info_ssp)
    
    status_code = device_status.get('devicestatuspage-devicestatus-statuslist-status-code', 0)
    black_supply_level = device_status.get('devicestatuspage-suppliesstatus-blacksupply-percentremaining', 0)
    black_supply_low = ssp.get('suppliesstatuspage-blacksupply-lowreached', 0)
    agents = []
    
    agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                     'type' : AGENT_TYPE_BLACK,
                     'health' : 0,
                     'level' : black_supply_level,
                     'level-trigger' : 0,
                  })
    
    if dev.tech_type == TECH_TYPE_COLOR_LASER:
        cyan_supply_level = device_status.get('devicestatuspage-suppliesstatus-cyansupply-percentremaining', 0)
        agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                         'type' : AGENT_TYPE_CYAN,
                         'health' : 0,
                         'level' : cyan_supply_level,
                         'level-trigger' : 0,
                      })

        magenta_supply_level = device_status.get('devicestatuspage-suppliesstatus-magentasupply-percentremaining', 0)
        agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                         'type' : AGENT_TYPE_MAGENTA,
                         'health' : 0,
                         'level' : magenta_supply_level,
                         'level-trigger' : 0,
                      })

        yellow_supply_level = device_status.get('devicestatuspage-suppliesstatus-yellowsupply-percentremaining', 0)
        agents.append({  'kind' : AGENT_KIND_TONER_CARTRIDGE,
                         'type' : AGENT_TYPE_YELLOW,
                         'health' : 0,
                         'level' : yellow_supply_level,
                         'level-trigger' : 0,
                      })

    return {'revision' :    STATUS_REV_UNKNOWN,
             'agents' :      agents,
             'top-door' :    0,
             'status-code' : 0,
             'supply-door' : 0,
             'duplexer' :    1,
             'photo-tray' :  0,
             'in-tray1' :    1,
             'in-tray2' :    1,
             'media-path' :  1,
           }     
    
        
    
    
    
    
