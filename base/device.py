#!/usr/bin/env python
#
# $Revision: 1.56 $ 
# $Date: 2005/05/12 18:38:55 $
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
import socket
import re
import gzip
import os.path
import time
import struct

# Local
from g import *
from codes import *
import msg, utils, status, pml, slp
from prnt import pcl, ldl, cups
from scan import scl


DEFAULT_READ_TIMEOUT = 45

pat_deviceuri = re.compile( r"""(.*?):/(.*?)/(\S*?)\?(?:serial=(\S*)|device=(\S*)|ip=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[^&]*))(?:&port=(\d))?""", re.IGNORECASE )

# Pattern to check for ; at end of CTR fields
# Note: If ; not present, CTR value is invalid
pat_dynamic_ctr = re.compile( r"""CTR:\d*\s.*;""", re.IGNORECASE )


def parseDeviceID( device_id ):
    d= {}
    x = [ y.strip() for y in device_id.strip().split( ';' ) if y ]    

    for z in x:
        y = z.split(':')
        try:
            d.setdefault( y[0].strip(), y[1] )
        except IndexError:
            d.setdefault( y[0].strip(), None )

    d.setdefault( 'MDL', '' )
    d.setdefault( 'SN',  '' )

    if 'MODEL' in d:
        d[ 'MDL' ] = d[ 'MODEL' ]
        del d[ 'MODEL' ]

    if 'SERIAL' in d:
        d[ 'SN' ] = d[ 'SERIAL' ]
        del d[ 'SERIAL' ]

    elif 'SERN' in d:
        d[ 'SN' ] = d[ 'SERN' ]
        del d[ 'SERN' ]

    if d[ 'SN' ].startswith( 'X' ):
        d[ 'SN' ] = ''

    return d


def parseDynamicCounter( ctr_field, convert_to_int=True ):
    counter, value = ctr_field.split(' ')
    try:
        counter = int( counter.lstrip('0') or '0' )
        if convert_to_int:
            value = int( value.lstrip('0') or '0' )
    except ValueError:
        if convert_to_int:
            counter, value = 0, 0
        else:
            counter, value = 0, ''

    return counter, value


def parseDeviceURI( device_uri ):
    m = pat_deviceuri.match( device_uri )

    if m is None:
        raise Error( ERROR_INVALID_DEVICE_URI )

    back_end = m.group(1).lower() or ''
    is_hp = ( back_end in ( 'hp', 'hpfax' ) )
    bus = m.group(2).lower() or ''

    if bus not in ( 'usb', 'net', 'bt', 'fw', 'par' ):
        raise Error( ERROR_INVALID_DEVICE_URI )

    model = m.group(3).replace( ' ', '_' )  or ''
    serial = m.group(4) or ''
    dev_file = m.group(5) or ''
    host = m.group(6) or ''
    port = m.group(7) or 1

    if bus == 'net':
        try:
            port = int( port )
        except (ValueError, TypeError):
            port = 1

        if port == 0:
            port = 1

    return back_end, is_hp, bus, model, serial, dev_file, host, port


AGENT_types = { AGENT_TYPE_NONE        : 'invalid',
                AGENT_TYPE_BLACK       : 'black',
                AGENT_TYPE_CMY         : 'cmy',
                AGENT_TYPE_KCM         : 'kcm',
                AGENT_TYPE_CYAN        : 'cyan',
                AGENT_TYPE_MAGENTA     : 'magenta',
                AGENT_TYPE_YELLOW      : 'yellow',
                AGENT_TYPE_CYAN_LOW    : 'photo_cyan',
                AGENT_TYPE_MAGENTA_LOW : 'photo_magenta',
                AGENT_TYPE_YELLOW_LOW  : 'photo_yellow',
                AGENT_TYPE_GGK         : 'photo_gray',
                AGENT_TYPE_BLUE        : 'photo_blue',
                AGENT_TYPE_UNSPECIFIED : 'unspecified', # Kind=5,6
            }

AGENT_kinds = { AGENT_KIND_NONE            : 'invalid',
                AGENT_KIND_HEAD            : 'head',
                AGENT_KIND_SUPPLY          : 'supply',
                AGENT_KIND_HEAD_AND_SUPPLY : 'cartridge',
                AGENT_KIND_TONER_CARTRIDGE : 'toner',
                AGENT_KIND_MAINT_KIT       : 'maint_kit', # fuser
                AGENT_KIND_ADF_KIT         : 'adf_kit',
                AGENT_KIND_DRUM_KIT        : 'drum_kit',
                AGENT_KIND_TRANSFER_KIT    : 'transfer_kit',
                AGENT_KIND_INT_BATTERY     : 'battery',
                AGENT_KIND_UNKNOWN         : 'unknown',
              }

AGENT_healths = { AGENT_HEALTH_OK           : 'ok',
                  AGENT_HEALTH_MISINSTALLED : 'misinstalled',
                  AGENT_HEALTH_INCORRECT    : 'incorrect',
                  AGENT_HEALTH_FAILED       : 'failed',
                  AGENT_HEALTH_OVERTEMP     : 'overtemp', # battery
                  AGENT_HEALTH_CHARGING     : 'charging', # battery
                  AGENT_HEALTH_DISCHARGING  : 'discharging', # battery
                }


AGENT_levels = { AGENT_LEVEL_TRIGGER_MAY_BE_LOW : 'low',
                 AGENT_LEVEL_TRIGGER_PROBABLY_OUT : 'low',
                 AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT : 'out',
               }

def OpenConnection():
    hpiod_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    hpiod_sock.connect( ( prop.hpiod_host, prop.hpiod_port ) )
    return hpiod_sock


MODEL_UI_REPLACEMENTS = { 'laserjet'   : 'LaserJet',
                          'psc'        : 'PSC',
                          'officejet'  : 'Officejet',
                          'deskjet'    : 'Deskjet',
                          'hp'         : 'HP',
                          'business'   : 'Business',
                          'inkjet'     : 'Inkjet',
                          'photosmart' : 'Photosmart',
                          'color'      : 'Color',
                          'series'     : 'series',
                          'printer'    : 'Printer',
                          'mfp'        : 'MFP',
                          'mopier'     : 'Mopier',
                        }


def normalizeModelName( model ):
    if not model.lower().startswith( 'hp' ):
        z = 'HP ' + model.replace( '_', ' ')
    else:
        z = model.replace( '_', ' ')

    y = []
    for x in z.split():
        xx = x.lower()
        y.append( MODEL_UI_REPLACEMENTS.get( xx, xx ) )

    model_ui = ' '.join( y )

    return model, model_ui

def isLocal( bus ):
    return bus in ( 'par', 'usb', 'fw', 'bt' )


class Device:

    def __init__( self, hpiod_sock=None, device_uri=None, printer_name=None, xmit_callback=None ):
        self.io_state = IO_STATE_HP_NOT_AVAIL
        self.device_id = None
        self.channels = {}
        self.status = {}
        self.pens = []
        self.deviceID = ''
        self.cups_printers = []
        self.model = ''
        self.model_ui = ''
        self.serial = ''
        self.back_end = ''
        self.dev_file = ''
        self.is_hp = False
        self.event_code = STATUS_UNKNOWN
        self.event_type = ''
        self.error_string_short = ''
        self.error_string_long = ''
        self.retry_timeout = 30
        self.job_id = -1
        self.hist = []
        self.mq = {}
        self.ds = {}
        self.close_hpiod_socket = False
        self.is_local = False
        self.host = ''
        self.port = 1
        self.pcard_mounted = False

        if xmit_callback is None:
            self.xmitMessage = self.__xmitMessage
        else:
            self.xmitMessage = xmit_callback

        printers = cups.getPrinters()

        if device_uri is None:
            self.device_uri = None
            for p in printers:
                if p.name.lower() == printer_name.lower():
                    self.device_uri = p.device_uri
                    break

        else:
            self.device_uri = device_uri

        if self.device_uri is None:
            log.warn( "Unknown printer name: %s" % printer_name )
            raise Error( ERROR_INTERNAL )

        try:
            self.back_end, self.is_hp, self.bus, self.model, self.serial, self.dev_file, self.host, self.port = \
                parseDeviceURI( self.device_uri )
        except Error:
            log.warn( "Malformed/non-HP URI: %s" % self.device_uri )
            self.io_state = IO_STATE_NON_HP
            raise Error( ERROR_INVALID_DEVICE_URI )

        self.io_state = IO_STATE_HP_READY
        self.device_state = DEVICE_STATE_FOUND

        log.debug( "URI: backend=%s, is_hp=%s, bus=%s, model=%s, serial=%s, dev=%s, host=%s, port=%d" % \
            ( self.back_end, self.is_hp, self.bus, self.model, self.serial, self.dev_file, self.host, self.port ) )

        self.is_local = isLocal( self.bus )


        if self.io_state == IO_STATE_HP_READY:
            if hpiod_sock is None and xmit_callback is None:
                self.hpiod_sock = OpenConnection()
                self.close_hpiod_socket = True
            else:
                self.hpiod_sock = hpiod_sock

        for p in printers:
            if self.device_uri == p.device_uri:
                self.cups_printers.append( p.name ) 
                self.state = p.state
                if self.io_state == IO_STATE_NON_HP:
                    self.model = p.makemodel.split(',')[0]


        self.model, self.model_ui = normalizeModelName( self.model )



    def __xmitMessage( self, msg_type, payload=None, other_fields={}, timeout=DEFAULT_READ_TIMEOUT ):
        return msg.xmitMessage( self.hpiod_sock, msg_type, payload, other_fields, timeout )

    def deviceQuery( self, prev_device_state, prev_status_code, 
                     string_query, model_query, r_values=None, 
                    panel_check=True ):
        dq = {}
        d = None

        device_state = self.determineIOState( force=False, leave_open=True, 
                                              do_ping=True, prev_device_state=prev_device_state )

        dq[ 'device-state' ] = device_state

        if not self.mq:
            try:
                self.mq = model_query( self.model )
            except Error:
                self.mq = {}

        if panel_check:
            panel_check = int( self.mq.get( 'panel-check-type', 0 ) )
        
        status_type = int( self.mq.get( 'status-type', 0 ) )
        r_type = int( self.mq.get( 'r-type', 0 ) )

        log.debug( "status-type=%d" % status_type )
        log.debug( "io-state=%d" % self.io_state )

        dq[ 'panel-line1' ] = ''
        dq[ 'panel-line2' ] = ''
        dq[ 'panel' ] = 0

        if self.io_state == IO_STATE_HP_OPEN:
            io_control = self.mq.get('io-control', 'gusher')
            dq[ 'status-code' ] = STATUS_PRINTER_IDLE

            parsed, dq[ 'deviceid' ] = self.ID()
            dq[ 'serial-number' ] = self.serialNumber() 
            dq[ 'dev-file' ] = self.devFile()

            agents = []

            dq[ '3bit-status-code' ], dq[ '3bit-status-name' ] = self.threeBitStatus()

            status_block = {}
            
            if status_type == STATUS_TYPE_NONE:
                log.warn( "No status available for device." )

            elif status_type in ( STATUS_TYPE_VSTATUS, STATUS_TYPE_S ):
                log.debug( "Type 1/2 (S: or VSTATUS:) status" )
                status_block = status.parseStatus( parsed )

            elif status_type == STATUS_TYPE_LJ: 
                log.debug( "Type 3 LaserJet status" )
                status_block = status.StatusType3( self, parsed )

            elif status_type == STATUS_TYPE_S_W_BATTERY: 
                log.debug( "Type 4 S: status with battery check" )
                status_block = status.parseStatus( parsed )
                status.BatteryCheck( self, status_block, io_control )

            else:
                log.error( "Unimplemented status type: %d" % status_type )
                
            if status_block:
                dq.update( status_block )
                try:
                    status_block[ 'agents' ]
                except KeyError:
                    pass
                else:
                    agents = status_block[ 'agents' ]
                    del dq[ 'agents' ]

            status_code = dq.get( 'status-code', STATUS_PRINTER_IDLE )
            dq['error-state'] = STATUS_TO_ERROR_STATE_MAP.get( status_code, ERROR_STATE_CLEAR )

            # panel check is called here because it potentially is
            # usable across multiple status_types
            if status_type != STATUS_TYPE_NONE and panel_check:
                panel_check, line1, line2 = status.PanelCheck( self, io_control )
                
                dq[ 'panel' ] = int(panel_check)
                dq[ 'panel-line1' ] = line1
                dq[ 'panel-line2' ] = line2
                
            r_value, rg, rr, r_value_str = 0, '000', '000000', '000000000'

            if r_type > 0:
                if r_values is None:
                    try:
                        r_value = self.getDynamicCounter( 140 )
                        self.closeChannel( 'PRINT' )
                        r_value_str = str( r_value )
                        r_value_str = ''.join( [ '0'*(9 - len(r_value_str)), r_value_str ] )
                        rg, rr, r_value = r_value_str[:3], r_value_str[3:], int( rr )
                    except:
                        pass
                    else:
                        r_values =  ( r_value, r_value_str, rg, rr )

                else:
                    r_value, r_value_str, rg, rr = r_values 

            dq[ 'r' ], dq[ 'rs' ], dq[ 'rg' ], dq[ 'rr' ] = r_value, r_value_str, rg, rr

            a = 1
            while True:
                mq_agent_kind = int( self.mq.get( 'r%d-agent%d-kind' % ( r_value, a ), '0' ) )

                if mq_agent_kind == 0:
                    break

                mq_agent_type = int( self.mq.get( 'r%d-agent%d-type' % ( r_value, a ), '0' ) )
                mq_agent_sku = self.mq.get( 'r%d-agent%d-sku' % ( r_value, a ), '' )

                found = False
                for agent in agents:
                    agent_kind = agent['kind']
                    agent_type = agent['type']

                    if agent_kind == mq_agent_kind and \
                       agent_type == mq_agent_type:
                       found = True
                       break

                if found:
                    agent_health = agent.get( 'health', AGENT_HEALTH_OK )
                    agent_level_trigger = agent.get( 'level-trigger', AGENT_LEVEL_TRIGGER_SUFFICIENT_0 )

                    try:
                        agent_desc = string_query( 'agent_%s_%s' % ( AGENT_types.get( agent_type, 'unknown' ), 
                                                                     AGENT_kinds.get( agent_kind, 'unknown' ) ) )
                    except Error:
                        agent_desc = ''

                    dq.update( 
                    { 
                        'agent%d-kind' % a :          agent_kind,
                        'agent%d-type' % a :          agent_type,
                        'agent%d-known' % a :         agent.get( 'known', False ),
                        'agent%d-sku' % a :           mq_agent_sku,
                        'agent%d-level' % a :         agent.get( 'level', 0 ),
                        'agent%d-level-trigger' % a : agent_level_trigger,
                        'agent%d-ack' % a :           agent.get( 'ack', False ),
                        'agent%d-hp-ink' % a :        agent.get('hp-ink', False ),
                        'agent%d-health' % a :        agent_health,
                        'agent%d-dvc' % a :           agent.get( 'dvc', 0 ),
                        'agent%d-virgin' % a :        agent.get( 'virgin', False ),
                        'agent%d-desc' % a :          agent_desc,
                    } )

                else:
                    agent_health = AGENT_HEALTH_MISINSTALLED
                    agent_level_trigger = AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT

                    try:
                        agent_desc = string_query( 'agent_%s_%s' % ( AGENT_types.get( mq_agent_type, 'unknown' ), 
                                                                     AGENT_kinds.get( mq_agent_kind, 'unknown' ) ) )
                    except Error:
                        agent_desc = ''

                    dq.update( 
                    { 
                        'agent%d-kind' % a :          mq_agent_kind,
                        'agent%d-type' % a :          mq_agent_type,
                        'agent%d-known' % a :         False,
                        'agent%d-sku' % a :           mq_agent_sku,
                        'agent%d-level' % a :         0,
                        'agent%d-level-trigger' % a : agent_level_trigger,
                        'agent%d-ack' % a :           False,
                        'agent%d-hp-ink' % a :        False,
                        'agent%d-health' % a :        agent_health,
                        'agent%d-dvc' % a :           0,
                        'agent%d-virgin' % a :        False,
                        'agent%d-desc' % a :          agent_desc,
                    } )

                query = 'agent_%s_%s' % ( AGENT_types.get( mq_agent_type, 'unknown' ), 
                                          AGENT_kinds.get( mq_agent_kind, 'unknown' ) )

                try:
                    dq[ 'agent%d-desc' % a ] = string_query( query )
                except Error:
                    dq[ 'agent%d-desc' % a ] = ''

                # If agent health is OK, check for low supplies. If low, use
                # the agent level trigger description for the agent description.
                # Otherwise, report the agent health.
                if agent_health == AGENT_HEALTH_OK and \
                  agent_level_trigger >= AGENT_LEVEL_TRIGGER_MAY_BE_LOW:

                    query = 'agent_level_%s' % AGENT_levels.get( agent_level_trigger, 'unknown' )
                else:
                    query = 'agent_health_%s' % AGENT_healths.get( agent_health, 'unknown' )

                try:
                    dq[ 'agent%d-health-desc' % a ] = string_query( query )
                except Error:
                    dq[ 'agent%d-health-desc' % a ] = ''

                a += 1

        else: # Create agent keys for not-found devices
            dq[ 'status-code' ] = EVENT_ERROR_DEVICE_NOT_FOUND
            dq[ 'error-state' ] = ERROR_STATE_ERROR

            r_value = 0
            if r_type > 0 and r_values is not None:    
                    r_value = r_values[0]

            a = 1
            while True:
                mq_agent_kind = int( self.mq.get( 'r%d-agent%d-kind' % ( r_value, a ), '0' ) )

                if mq_agent_kind == 0:
                    break

                mq_agent_type = int( self.mq.get( 'r%d-agent%d-type' % ( r_value, a ), '0' ) )
                mq_agent_sku = self.mq.get( 'r%d-agent%d-sku' % ( r_value, a ), '' )

                try:
                    agent_desc = string_query( 'agent_%s_%s' % ( AGENT_types.get( mq_agent_type, 'unknown' ), 
                                                                 AGENT_kinds.get( mq_agent_kind, 'unknown' ) ) )
                except Error:
                    agent_desc = ''


                dq.update( 
                { 
                    'agent%d-kind' % a :          mq_agent_kind,
                    'agent%d-type' % a :          mq_agent_type,
                    'agent%d-known' % a :         False,
                    'agent%d-sku' % a :           mq_agent_sku,
                    'agent%d-level' % a :         0,
                    'agent%d-level-trigger' % a : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                    'agent%d-ack' % a :           False,
                    'agent%d-hp-ink' % a :        False,
                    'agent%d-health' % a :        AGENT_HEALTH_MISINSTALLED,
                    'agent%d-dvc' % a :           0,
                    'agent%d-virgin' % a :        False,
                    'agent%d-health-desc' % a :   string_query( 'agent_health_unknown' ),
                    'agent%d-desc' % a :          agent_desc,
                } )

                a += 1


        return dq, r_values, panel_check


    def determineIOState( self, force=True, leave_open=False, do_ping=False, 
                          delay=-1.0, timeout=1, prev_device_state=DEVICE_STATE_FOUND ):

        ret = DEVICE_STATE_FOUND 

        if self.is_local: # USB
            try:
                self.open( force )
            except Error:
                ret = DEVICE_STATE_NOT_FOUND
            else:
                if prev_device_state == DEVICE_STATE_NOT_FOUND:
                    ret = DEVICE_STATE_JUST_FOUND

                if not leave_open:
                    self.close()

        else: # Network
            if do_ping:
                try:
                    delay = utils.ping( self.host, timeout )
                except socket.error:
                    self.io_state = IO_STATE_HP_NOT_AVAIL
                    ret = DEVICE_STATE_NOT_FOUND
                else:    
                    if delay < 0.0:
                        self.io_state = IO_STATE_HP_NOT_AVAIL
                        ret = DEVICE_STATE_NOT_FOUND
                    else:
                        if prev_device_state == DEVICE_STATE_NOT_FOUND:
                            ret = DEVICE_STATE_JUST_FOUND
                        try:
                            self.open( force )
                        except Error:
                            ret = DEVICE_STATE_NOT_FOUND
                        else:
                            if not leave_open:
                                self.close()

        self.device_state = ret
        return ret 


    def open( self, force=True ):
        #print "open()"
        if force or self.io_state == IO_STATE_HP_READY:
        #if 1:
            log.debug( "Opening device: %s" % self.device_uri )
            try:
                fields, data = self.xmitMessage( "DeviceOpen", 
                                                None, { 'device-uri':  self.device_uri, } )
            except Error, e:
                self.io_state = IO_STATE_HP_NOT_AVAIL
                log.error( "Unable to communicate with device: %s" % self.device_uri )
                raise Error( e.opt )
            else:
                #print fields, data
                self.device_id = fields[ 'device-id' ]
                log.debug( "device-id=%d" % self.device_id )
                self.io_state = IO_STATE_HP_OPEN
                log.debug( "Opened device: %s\n\t(hp=%s,bus=%s,model=%s,dev=%s,serial=%s)" % 
                          (self.device_uri, self.is_hp, self.bus, self.model, self.dev_file, self.serial ) )

                return self.device_id

        return -1

    def checkOpenChannel( self, service_name ):
        if self.io_state == IO_STATE_HP_OPEN:
            service_name = service_name.lower()

            if service_name not in self.channels:
                return self.openChannel( service_name )
            else:
                return self.channels[ service_name ]
        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )

    def openChannel( self, service_name, flow_control='gusher' ):
        log.debug( "Opening %s channel..." % service_name )

        if self.io_state == IO_STATE_HP_OPEN:
            service_name = service_name.lower()
            io_mode = 'raw'
            
            if service_name == 'print':
                try:
                    io_mode = self.mq.get( 'io-mode', 'raw' )
                except:
                    pass
                    
            if service_name not in self.channels:
                try:
                    fields, data = self.xmitMessage( "ChannelOpen", 
                                                    None, 
                                                    { 'device-id':  self.device_id,
                                                      'service-name' : service_name, 
                                                      'io-control' : flow_control,
                                                      'io-mode' : io_mode,
                                                    } 
                                                  )
                except Error:
                    raise Error( ERROR_INTERNAL )

                try:
                    channel_id = fields[ 'channel-id' ]
                except KeyError:
                    raise Error( ERROR_INTERNAL )

                self.channels[ service_name ] = channel_id
                log.debug( "channel-id=%d" % channel_id )
                return channel_id
            else:
                return self.channels[ service_name ]
        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )


    def removeChannel( self, service_name ):
        try:
            del self.channels[ service_name.lower() ]
        except KeyError:
            pass


    def ID( self ):
        if self.io_state == IO_STATE_HP_OPEN:
            fields, data = self.xmitMessage( 'DeviceID', 
                                            None, { 'device-id' : self.device_id, } )

            self.deviceID = parseDeviceID( data )

            return self.deviceID, data # (parsed, raw)

        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )


    def getDynamicCounter( self, counter, callback=None, convert_to_int=True ):
        if self.io_state == IO_STATE_HP_OPEN:
            self.ID()

            if 'DYN' in self.deviceID.get( 'CMD', '' ).split(','):

                self.writeChannel( self.checkOpenChannel( 'PRINT' ), 
                                   pcl.buildDynamicCounter( counter ), 
                                   callback )

                value, tries, times_seen, sleepy_time, max_tries = 0, 0, 0, 0.1, 20
                time.sleep( 0.1 )

                while True:

                    if callback:
                        callback()

                    sleepy_time += 0.1
                    tries += 1

                    time.sleep( sleepy_time )

                    parsed, raw = self.ID()

                    if 'CTR' in self.deviceID and \
                        pat_dynamic_ctr.search( raw ) is not None:
                        dev_counter, value = parseDynamicCounter( self.deviceID['CTR'], convert_to_int )
                        if counter == dev_counter:
                            self.writeChannel( self.checkOpenChannel( 'PRINT' ), 
                                               pcl.buildDynamicCounter( 0 ), callback ) 
                            return value

                    if tries > max_tries:
                        self.writeChannel( self.checkOpenChannel( 'PRINT' ), 
                                           pcl.buildDynamicCounter( 0 ), callback ) 
                        return 0

            else:
                raise Error( ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION )
        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )


    def deviceIDStatus( self ):
        return status.parseStatus( self.ID()[0] )


    def threeBitStatus( self ):
        if self.io_state == IO_STATE_HP_OPEN:
            fields, data = self.xmitMessage( 'DeviceStatus', 
                                            None, { 'device-id' : self.device_id, } )

            return fields[ 'status-code' ], fields[ 'status-name' ]

        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )

    def devFile( self ):
        if self.io_state == IO_STATE_HP_OPEN:

            fields, data = self.xmitMessage( "DeviceFile",
                                             None, 
                                             { 
                                               'device-uri' : self.device_uri, 
                                             } 
                                            )

            self.dev_file = fields[ 'device-file' ]
            return self.dev_file

        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )

    def serialNumber( self ):
        if not self.deviceID:
            self.ID()

        try:
            self.serial = self.deviceID[ 'SN' ]
        except KeyError:
            pass
        else:
            if len( self.serial ):
                return self.serial
        try:
            channel_id = self.openChannel( 'HP-MESSAGE' )
            error_code, self.serial = self.getPML( channel_id, pml.OID_SERIAL_NUMBER )
            self.closeChannel( 'HP-MESSAGE' )
        except Error:
            self.serial = ''

        if self.serial is None:
            self.serial = ''

        return self.serial


    def setPML( self, channel_id, oid, value ): #, value_type ):
        if self.io_state == IO_STATE_HP_OPEN:
            typ = oid[1]

            value = pml.ConvertToPMLDataFormat( value, typ )

            fields, data = self.xmitMessage( "SetPML", 
                                             value,
                                             { 
                                                'device-id' : self.device_id,
                                                'channel-id' : channel_id,
                                                'oid' : pml.PMLToSNMP( oid[0] ),
                                                'type' : typ,
                                              }
                                            )

            return fields.get( 'pml-result-code', pml.ERROR_OK )

        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )


    def getPML( self, channel_id, oid, desired_int_size=pml.INT_SIZE_INT ): 
        if self.io_state == IO_STATE_HP_OPEN:
            typ = oid[1]
            fields, data = self.xmitMessage( "GetPML", 
                                             None,
                                             { 
                                                'device-id' : self.device_id,
                                                'channel-id' : channel_id,
                                                'oid' : pml.PMLToSNMP( oid[0] ),
                                                'type' : typ,
                                              }
                                            )

            pml_result_code = fields.get( 'pml-result-code', pml.ERROR_OK )

            if pml_result_code >= pml.ERROR_UNKNOWN_REQUEST:
                return pml_result_code, None

            return pml_result_code, pml.ConvertFromPMLDataFormat( data, typ, desired_int_size )

        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )

    def sendSCLCmd( self, punc, letter1, letter2, value='', data=None ):
        p = scl.buildSCLCmd( punc, letter1, letter2, value, data )
        log.debug( "Sending SCL command: %s" % repr(p) )
        self.writeChannel( self.checkOpenChannel( 'hp-scan' ), p )

    def inquireSCLMinimum( self, *cmd ):
        return self._inquireSCL( *scl.buildSCLInquireMinimum( *cmd ) )

    def inquireSCLMaximum( self, *cmd ):
        return self._inquireSCL( *scl.buildSCLInquireMaximum( *cmd ) )

    def inquireSCLPresent( self, *cmd ):
        return self._inquireSCL( *scl.buildSCLInquirePresent( *cmd ) )

    def inquireSCLDeviceParam( self, id ):
        return self._inquireSCL( *scl.buildSCLInquireDeviceParam( id ) )

    def inquireSCLPseudoMaximum( self, id ):
        return self._inquireSCL( scl.buildSCLCmd( '*', 's', 'H', value=id ), id )

    def _inquireSCL( self, packet, send_id ):
        channel_id = self.checkOpenChannel( 'HP-SCAN' )
        log.debug( "Writing SCL inquire packet: %s" % repr(packet) )
        self.writeChannel( channel_id, packet )
        fields, data = self.readChannel( channel_id ) # TODO: Handle partial INQ result
        log.debug( "Reading SCL inquire response packet: %s" % repr(data) )
        value, recv_id, typ, data = scl.parseSCLInquire( data )
        #if value is not None:
        #    return int(value)  #, data
        return int(value)

    def buildEmbeddedPML( self, oid, value, data_type ):
        return pcl.buildEmbeddedPML( pcl.buildPCLCmd( '&', 'b', 'W', 
                                     pml.buildEmbeddedPMLSetPacket( oid, 
                                                                    value, 
                                                                    data_type ) ) )

    ##def sendEmbeddedPML( self, oid, value, data_type ): # OID dotted string
    ##    pcl_data = self.buildEmbeddedPML( oid, value, data_type )
    ##    log.debug( "Sending embedded PML:\n%s" % repr(pcl_data) )
    ##    channel_id = self.checkOpenChannel( 'PRINT' )
    ##    self.writeChannel( channel_id, pcl_data )

    def sendEmbeddedPMLEx( self, oid, value ): # OID tuple 
        pcl_data = self.buildEmbeddedPML( oid[0], value, oid[1] )
        log.debug( "Sending embedded PML:\n%s" % repr(pcl_data) )
        channel_id = self.checkOpenChannel( 'PRINT' )
        self.writeChannel( channel_id, pcl_data )

    ##def printData( self, data ):
    ##    self.writeChannel( self.checkOpenChannel( 'PRINT' ), data )

    def printFile( self, file_name, callback=None, direct=True, raw=True ):
        log.debug( "Printing file '%s'" % file_name )
        if direct: # implies raw==True
            self.writeChannel( self.checkOpenChannel( 'PRINT' ), 
                file( file_name, 'r' ).read(), callback )
            self.closeChannel( 'PRINT' )
        else:
            raw_str = ''
            if raw:
                raw_str = ' -oraw'

            c = 'lp -d%s -s%s %s' % ( self.cups_printers[0], raw_str, file_name )
            os.system( c )

    def printGzipFile( self, file_name, callback=None , direct=True, raw=True ):
        log.debug( "Printing gzip file '%s'" % file_name )
        if direct: # implies raw==True
            self.writeChannel( self.checkOpenChannel( 'PRINT' ), 
                gzip.open( file_name, 'r' ).read(), callback )
            self.closeChannel( 'PRINT' )
        else:
            c = 'gunzip -c %s | lp -d%s -s' % ( file_name, self.cups_printers[0] )

            if raw:
                c += ' -oraw'

            os.system( c )


    def printData( self, data, callback=None, direct=True, raw=True ):
        if direct:
            self.writeChannel( self.checkOpenChannel( 'PRINT' ), data, callback )
            self.closeChannel( 'PRINT' )
        else:
            temp_file_fd, temp_file_name = utils.make_temp_file()
            os.write( temp_file_fd, data )
            os.close( temp_file_fd )

            self.printFile( temp_file_name, callback, direct, raw )
            os.remove( temp_file_name )



    def printParsedGzipPostscript( self, print_file ):
        try:
            os.stat( print_file )
        except OSError:
            log.error( "File not found." )
            return

        temp_file_fd, temp_file_name = utils.make_temp_file()
        f = gzip.open( print_file, 'r' )

        x = f.readline()
        while not x.startswith( '%PY_BEGIN' ):
            os.write( temp_file_fd, x )
            x = f.readline()

        sub_lines = []
        x = f.readline()
        while not x.startswith( '%PY_END' ):
            sub_lines.append( x )
            x = f.readline()

        if self.dev_file == '':
            self.devFile()

        SUBS = { 'VERSION' : prop.version,
                 'MODEL'   : self.model_ui,
                 'URI'     : self.device_uri,
                 'BUS'     : self.bus,
                 'SERIAL'  : self.serialNumber(),
                 'IP'      : self.host,
                 'PORT'    : self.port,
                 'DEVNODE' : self.dev_file,
                 }

        if self.bus == 'net':
            SUBS[ 'DEVNODE' ] = 'n/a'
        else:
            SUBS[ 'IP' ] = 'n/a'
            SUBS[ 'PORT' ] = 'n/a'

        for s in sub_lines:
            os.write( temp_file_fd, s % SUBS )

        os.write( temp_file_fd, f.read() )
        f.close()
        os.close( temp_file_fd )
        os.system( 'lp -d%s -s %s' % ( self.cups_printers[0], temp_file_name ) )
        os.remove( temp_file_name )



    def readChannel( self, channel_id, timeout=DEFAULT_READ_TIMEOUT, bytes_to_read=prop.max_message_len ):
        if self.io_state == IO_STATE_HP_OPEN:
            log.debug( "Reading channel %d..." % channel_id )

            return self.xmitMessage( 'ChannelDataIn', 
                                     None,
                                     { 'device-id': self.device_id, 
                                       'channel-id' : channel_id, 
                                       'bytes-to-read' : bytes_to_read,
                                       'timeout' : timeout,
                                      } 
                                   )
        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )


    def readChannelToStream( self, channel_id, stream ):
        if self.io_state == IO_STATE_HP_OPEN:
            try:
                num_bytes = 0
                while True:
                    fields, data = self.readChannel( channel_id )
                    if len( data ) == 0: 
                        log.debug( "End of data" )
                        break
                    stream.write( data )
                    num_bytes += len(data)
                    log.debug( "Wrote %d bytes to stream..." % len(data) )

                log.debug( "Wrote %d total bytes to stream." % num_bytes )
            finally:
                return num_bytes
        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )


    def writeChannel( self, channel_id, data, callback=None ):
        if self.io_state == IO_STATE_HP_OPEN:
            if channel_id in self.channels.values():
                log.debug( "Writing channel %d..." % channel_id ) 
                buffer, bytes_out, total_bytes_to_write = data, 0, len(data)

                while len( buffer ) > 0:
                    fields, data = self.xmitMessage( 'ChannelDataOut', 
                                                    buffer[ :prop.max_message_len ], 
                                                    { 
                                                     'device-id': self.device_id, 
                                                     'channel-id' : channel_id,
                                                    } 
                                                  )

                    buffer = buffer[ prop.max_message_len: ]
                    bytes_out += fields[ 'bytes-written' ]

                    if callback is not None:
                        callback()

                if total_bytes_to_write != bytes_out:
                    raise Error( ERROR_DEVICE_IO_ERROR )

                return bytes_out

            else:
                raise Error( ERROR_ERROR_INVALID_CHANNEL_ID )

        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )


    def closeChannel( self, service_name ):
        if self.io_state == IO_STATE_HP_OPEN:
            service_name = service_name.lower()
            if service_name in self.channels:
                log.debug( "Closing %s channel..." % service_name )
                try:
                    fields, data = self.xmitMessage( 'ChannelClose', 
                                                    None, 
                                                    { 
                                                      'device-id': self.device_id, 
                                                      'channel-id' : self.channels[ service_name ],
                                                    }  
                                                  )    
                except Error:
                    pass # best effort

                del self.channels[ service_name ]


    def close( self, new_io_state=IO_STATE_HP_READY ):
        if self.io_state == IO_STATE_HP_OPEN:
            log.debug( "Closing device..." )

            if len( self.channels ) > 0:
                channels = self.channels.keys()

                for c in channels:
                    self.closeChannel( c )

            try:
                fields, data = self.xmitMessage( "DeviceClose", 
                                                None, 
                                                { 
                                                  'device-id': self.device_id,
                                                } 
                                              )

            except Error:
                pass # best effort

            self.is_open = False
            self.channels.clear()

            if self.close_hpiod_socket:
                self.hpiod_sock.close()

            self.io_state = new_io_state






