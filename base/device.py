#!/usr/bin/env python
#
# $Revision: 1.33 $ 
# $Date: 2004/12/16 00:00:44 $
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

DEFAULT_READ_TIMEOUT = 30
    
pat_deviceuri = re.compile( r"""(.*?):/(.*?)/(\S*?)\?(?:serial=(\S*)|device=(\S*)|ip=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[^&]*))(?:&port=(\d))?""", re.IGNORECASE )

# Pattern to check for ; at end of CTR fields
# If ; not present, CTR value is invalid
pat_dynamic_ctr = re.compile( r"""CTR:\d*\s\d*;""", re.IGNORECASE )


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
    
def parseDynamicCounter( ctr_field ):
    counter, value = ctr_field.split(' ')
    try:
        counter = int( counter.lstrip('0') )
        value = int( value.lstrip('0') )
    except ValueError:
        counter,value=0,0
    
    return counter, value
    
    
def probeDevices( bus='usb', hpiod_sock=None ):
    bus=bus.lower()
    close_hpiod_socket = False
    devices = []
    
    if bus == "cups":
        cups_devices = {}
        cups_printers = cups.getPrinters()
        x = len( cups_printers )
        
        for p in cups_printers:
            device_uri = p.device_uri
            if p.device_uri != '':
                try:
                    cups_devices[ device_uri ]
                except KeyError: 
                    cups_devices[ device_uri ] = 1
                
        devices = cups_devices.keys()
            
    elif bus == "usb":
        try:
            if hpiod_sock is None:
                hpiod_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                hpiod_sock.connect( ( prop.hpiod_host, prop.hpiod_port ) )
                close_hpiod_socket = True
            
            fields, data = msg.xmitMessage( hpiod_sock, "ProbeDevices", None, 
                                            { 'bus' : bus } )
            
        finally:
            if close_hpiod_socket:
                hpiod_sock.close()
    
        devices = [ x.split(' ')[1] for x in data.splitlines() ]
    
    elif bus in ( "net", "network", "jetdirect", "jd" ):
        return slp.detectNetworkDevices()
    
    elif bus in ( "bluetooth", "bt" ):
        raise Error( ERROR_UNSUPPORTED_BUS_TYPE )
    
    elif bus in ( "firewire", "fw" ):
        raise Error( ERROR_UNSUPPORTED_BUS_TYPE )
        
    elif bus in ( "parallel", "par" ):
        raise Error( ERROR_UNSUPPORTED_BUS_TYPE )
    
    else:
        raise Error( ERROR_UNSUPPORTED_BUS_TYPE )
    
    return devices


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

    
IO_STATE_HP_OPEN = 0
IO_STATE_HP_READY = 1
IO_STATE_HP_NOT_AVAIL = 2
IO_STATE_NON_HP = 3   

DEVICE_STATE_NOT_FOUND = -1
DEVICE_STATE_FOUND = 0
DEVICE_STATE_JUST_FOUND = 1
    
    
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
        self.event_code = EVENT_PRINTER_UNKNOWN
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
        #else:
        self.io_state = IO_STATE_HP_READY
        self.device_state = DEVICE_STATE_FOUND
        
        log.debug( "URI: backend=%s, is_hp=%s, bus=%s, model=%s, serial=%s, dev=%s, host=%s, port=%d" % \
            ( self.back_end, self.is_hp, self.bus, self.model, self.serial, self.dev_file, self.host, self.port ) )
        
        #if self.bus in [ 'par', 'usb', 'bt', 'fw' ]:
        #    self.is_local = True
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
        #if not self.model.lower().startswith( 'hp' ):
        #    z = 'HP ' + self.model.replace( '_', ' ')
        #else:
        #    z = self.model.replace( '_', ' ')
            
        #MODEL_UI_REPLACEMENTS = { 'laserjet'   : 'LaserJet',
        #                          'psc'        : 'PSC',
        #                          'officejet'  : 'Officejet',
        #                          'deskjet'    : 'Deskjet',
        #                          'hp'         : 'HP',
        #                          'business'   : 'Business',
        #                          'inkjet'     : 'Inkjet',
        #                          'photosmart' : 'Photosmart',
        #                          'color'      : 'Color',
        #                          'series'     : 'series',
        #                          'printer'    : 'Printer',
        #                          'mfp'        : 'MFP',
        #                        }
        
        
        #y = []
        #for x in z.split():
        #    xx = x.lower()
        #    y.append( MODEL_UI_REPLACEMENTS.get( xx, xx ) )
        
        #self.model_ui = ' '.join( y )
                    
    def __xmitMessage( self, msg_type, payload=None, other_fields={}, timeout=DEFAULT_READ_TIMEOUT ):
        return msg.xmitMessage( self.hpiod_sock, msg_type, payload, other_fields, timeout )


    
    def determineIOState( self, force=True, leave_open=False, do_ping=False, delay=-1.0, timeout=1, prev_device_state=DEVICE_STATE_FOUND ):
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
        
                        self.open( force )
                        
                        if not leave_open:
                            self.close()
                    
        log.debug( "Device state: %d -> %d" % ( prev_device_state, ret ) )
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
            
            if service_name not in self.channels:
                fields, data = self.xmitMessage( "ChannelOpen", 
                                                None, 
                                                { 'device-id':  self.device_id,
                                                  'service-name' : service_name, 
                                                  'io-control' : flow_control,
                                                } 
                                              )

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
            

    def getDynamicCounter( self, counter, callback=None ):
        if self.io_state == IO_STATE_HP_OPEN:
            self.ID()
            
            #print raw
            
            if 'DYN' in self.deviceID.get( 'CMD', '' ).split(','):
                
                
                #if 'CTR' in self.deviceID and pat_dynamic_ctr.search( raw ) is not None:
                #    dev_counter, value = parseDynamicCounter( self.deviceID['CTR'] )
                    
                #    self.writeChannel( self.checkOpenChannel( 'PRINT' ), pcl.buildDynamicCounter( 0 ) )
                    
                #    if counter == dev_counter:
                #        return value

                #time.sleep( 0.5 )
                
                self.writeChannel( self.checkOpenChannel( 'PRINT' ), pcl.buildDynamicCounter( counter ), callback )
                
                value, tries, times_seen, sleepy_time, max_tries = 0, 0, 0, 0.1, 20
                time.sleep( 0.1 )
                
                while True:
                    
                    if callback:
                        callback()
                    
                    sleepy_time += 0.1
                    tries += 1
                    
                    #if tries % 3 == 0:
                    #   self.writeChannel( self.checkOpenChannel( 'PRINT' ), pcl.buildDynamicCounter( counter ), callback ) 
                    
                    time.sleep( sleepy_time )

                    parsed, raw = self.ID()
                    
                    #print raw
                    
                    if 'CTR' in self.deviceID and \
                        pat_dynamic_ctr.search( raw ) is not None:
                        
                        dev_counter, value = parseDynamicCounter( self.deviceID['CTR'] )
                        
                        #if value != 0:
                        #    times_seen += 1
                        
                        if counter == dev_counter: # and value != 0 and times_seen > 1:
                            self.writeChannel( self.checkOpenChannel( 'PRINT' ), pcl.buildDynamicCounter( 0 ), callback ) 
                            #print self.deviceID
                            return value
                            
                    if tries > max_tries:
                        self.writeChannel( self.checkOpenChannel( 'PRINT' ), pcl.buildDynamicCounter( 0 ), callback ) 
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
                                            None, { 'device-uri' : self.device_uri, } )
                                                
            self.dev_file = fields[ 'device-file' ]
            return self.dev_file

        else:
            raise Error( ERROR_DEVICE_NOT_OPEN )
            
    def serialNumber( self ):
        self.serial = ''    
        
        if not self.deviceID:
            self.ID()
        
        try:
            self.serial = self.deviceID[ 'SN' ]
        except:
            pass
            
        #if self.serial:
        #    return self.serial
        
        #try:
        #    self.serial, data_type, error_code = self.getPML( pml.OID_SERIAL_NUMBER )
        #except Error:
        #    pass
        
        return self.serial
            
    
    def setPML( self, oid, value ): #, value_type ):
        channel_id = self.checkOpenChannel( 'HP-MESSAGE' )
        p = pml.buildPMLSetPacketEx( oid, value ) #, value_type )
        log.debug( "setPML (write): %s" % repr(p) )
        self.writeChannel( channel_id, p )
        fields, data = self.readChannel( channel_id )
        log.debug( "setPML (read): %s" % repr(data) )
        return pml.parsePMLPacket( data, oid['type'] )
        
    def getPML( self, oid ): 
        channel_id = self.checkOpenChannel( 'HP-MESSAGE' )
        p = pml.buildPMLGetPacketEx( oid )
        log.debug( "getPML (write): %s" % repr(p) )
        self.writeChannel( channel_id, p )
        fields, data = self.readChannel( channel_id )
        log.debug( "getPML (read): %s" % repr(data) )
        return pml.parsePMLPacket( data, oid['type'] )
        
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
        
    def sendEmbeddedPML( self, oid, value, data_type ): # OID dotted string
        pcl_data = pcl.buildEmbeddedPML( pcl.buildPCLCmd( '&', 'b', 'W', 
                                         pml.buildEmbeddedPMLSetPacket( oid, value, data_type ) ) )
        log.debug( "Sending embedded PML:\n%s" % repr(pcl_data) )
        channel_id = self.checkOpenChannel( 'PRINT' )
        self.writeChannel( channel_id, pcl_data )
        
    def sendEmbeddedPMLEx( self, oid, value ): # OID dictionary 
        pcl_data = pcl.buildEmbeddedPML( pcl.buildPCLCmd( '&', 'b', 'W', 
                                         pml.buildEmbeddedPMLSetPacket( oid['oid'], value, oid['type'] ) ) )
        log.debug( "Sending embedded PML:\n%s" % repr(pcl_data) )
        channel_id = self.checkOpenChannel( 'PRINT' )
        self.writeChannel( channel_id, pcl_data )
    
    
    def printData( self, data ):
        self.writeChannel( self.checkOpenChannel( 'PRINT' ), data )
    
    def printFile( self, file_name, callback=None, direct=True ):
        log.debug( "Printing file '%s'" % file_name )
        if direct:
            self.writeChannel( self.checkOpenChannel( 'PRINT' ), file( file_name, 'r' ).read(), callback )
        else:
            os.system( 'lp -d%s -s -oraw %s' % ( self.cups_printers[0], file_name ) )
        
    def printGzipFile( self, file_name, callback=None , direct=True ):
        log.debug( "Printing gzip file '%s'" % file_name )
        if direct:
            self.writeChannel( self.checkOpenChannel( 'PRINT' ), gzip.open( file_name, 'r' ).read(), callback )
        else:
            os.system( 'gunzip -c %s | lp -d%s -s -oraw' % ( file_name, self.cups_printers[0] ) )
            
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
                    fields, data = self.readChannel( self.channel_id )
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
                

    
    
        
        
