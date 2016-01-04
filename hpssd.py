#!/usr/bin/env python
#

# $Revision: 1.75 $ 
# $Date: 2005/03/29 21:06:48 $
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
# Authors: Don Welch, Pete Parks
#
# Thanks to Henrique M. Holschuh <hmh@debian.org> for various security patches
#

# Remove in 2.3
from __future__ import generators

_VERSION = '4.1'

# Std Lib
import sys
import socket
import os, os.path
import signal
import getopt
import smtplib
import threading
import atexit
import gettext

# Local
from base.g import *
from base.codes import *
from base.msg import *
from base import async, utils, database, status, pml, slp

# Printing support
from prnt import cups

# Device support
from base import device

device_r_cache = {} # { 'uri' : ( r_value, r_value_str, rg, rr ), ... }
device_panel_cache = {} # { 'uri' : ( load_panel_strings ), ... }

class hpssd_server( async.dispatcher ):

    def __init__( self, ip, port ):
        self.ip = ip

        if port != 0:
            self.port = port
        else:
            self.port = socket.htons(0)

        async.dispatcher.__init__( self )
        self.create_socket( socket.AF_INET, socket.SOCK_STREAM )
        self.set_reuse_addr()

        try:
            self.bind( ( ip, port ) )
        except socket.error:
            raise Error( ERROR_UNABLE_TO_BIND_SOCKET )

        prop.hpssd_port = self.port = self.socket.getsockname()[1]

        self.listen( 5 )


    def writable( self ):
        return False

    def readable( self ):
        return self.accepting

    def handle_accept( self ):
        try:
            conn, addr = self.accept()
        except socket.error:
            log.error( "Socket error on accept()" )
            return
        except TypeError:
            log.error( "EWOULDBLOCK exception on accept()" )
            return
        handler = hpssd_handler( conn, addr, self )
        log.debug( str(handler) )


    def __str__( self ):
        return "<hpssd_server listening on %s:%d (fd=%d)>" % \
                ( self.ip, self.port, self._fileno )

    def handle_close( self ):
        async.dispatcher.handle_close( self )


# This handler takes care of all conversations with
# clients when hpssd is acting as a server.
# This dispatcher receives requests messages and
# and replies with result messages. It does not 
# initiate sending requests.
class hpssd_handler( async.dispatcher ):
    def __init__( self, conn, addr, server ): 
        async.dispatcher.__init__( self, sock=conn )
        self.addr = addr
        self.in_buffer = ""
        self.out_buffer = ""
        self.server = server
        self.fields = {}
        self.payload = ""
        self.signal_exit = False

        # handlers for all the messages we expect to receive
        self.handlers = { 
            # Primary Request/Reply Messages
            'stringquery'          : self.handle_stringquery,
            'errorstringquery'     : self.handle_errorstringquery,
            'modelquery'           : self.handle_modelquery,
            'historyquery'         : self.handle_historyquery,
            'probedevicesfiltered' : self.handle_probedevicesfiltered,
            'setalerts'            : self.handle_setalerts,
            'testemail'            : self.handle_test_email,

            #'getalerts'            : self.handle_getalerts,
            'getgui'               : self.handle_getgui,
            'devicequery'          : self.handle_device_query,

            # Primary Event Messages
            'event'                : self.handle_event,
            'registerguievent'     : self.handle_registerguievent,
            'unregisterguievent'   : self.handle_unregisterguievent,

            # Misc
            'unknown'              : self.handle_unknown,
            'ping'                  : self.handle_ping,

            # undocumented Events
            'exitevent'            : self.handle_exit,
                        }        

    def __str__( self ):
        return "<hpssd_handler connected to %s (fd=%d)>" % \
                ( self.addr, self._fileno )

    def handle_read( self ):
        log.debug( "Reading data on channel (%d)" % self._fileno )
        self.in_buffer = self.recv( prop.max_message_len << 2 )

        if self.in_buffer == '':
            return False

        try:
            self.fields, self.payload = parseMessage( self.in_buffer )
        except Error, e:
            err = e.opt
            log.debug( repr(self.in_buffer) )
            log.warn( "Message parsing error: %s (%d)" % (e.msg, err) )
            self.out_buffer = self.handle_unknown( err )
            log.debug( self.out_buffer )
            return True

        msg_type = self.fields.get( 'msg', 'unknown' )
        log.debug( "%s %s %s" % ("*"*60, msg_type, "*"*60 ) )
        log.debug( repr(self.in_buffer) )

        try:
            self.out_buffer = self.handlers.get( msg_type, self.handle_unknown )()
        except Error:
            log.error( "Unhandled exception during processing" )

        return True

    def handle_unknown( self, err=ERROR_INVALID_MSG_TYPE ):
        return buildResultMessage( 'MessageError', None, err )


    def handle_write( self ):
        log.debug( "Sending data on channel (%d)" % self._fileno )
        log.debug( repr(self.out_buffer) )
        sent = self.send( self.out_buffer )
        self.out_buffer = self.out_buffer[ sent: ]

        if self.signal_exit:
            self.handle_close()


    def handle_device_query( self ):
        dq, result_code, = {}, ERROR_SUCCESS
        device_uri = self.fields[ 'device-uri' ]
        prev_device_state = self.fields[ 'device-state-previous' ]
        make_history = self.fields[ 'make-history' ]
        prev_status_code = self.fields[ 'status-code-previous' ]

        r_values = device_r_cache.get( device_uri, None )
        panel_check = device_panel_cache.get( device_uri, True )
        
        d = device.Device( hpiod_sock, device_uri )

        dq, r_values, panel_check = \
              d.deviceQuery( prev_device_state, 
              prev_status_code, database.queryStrings,
              database.queryModels, r_values, 
              panel_check )

        d.close()
        
        device_panel_cache[ device_uri ] = panel_check
        device_r_cache[ device_uri ] = r_values

        device_state = dq[ 'device-state' ]
        status_code = dq[ 'status-code' ]

        log.debug( "Device state = %d (was %d)" % ( device_state, prev_device_state ) )
        log.debug( "Status code = %d (was %d)" % ( status_code, prev_status_code ) )

        if make_history:

            non_idle_status = False

            #if device_state == DEVICE_STATE_NOT_FOUND and \
            #  prev_device_state in ( DEVICE_STATE_FOUND, DEVICE_STATE_JUST_FOUND ): 
            if device_state == DEVICE_STATE_NOT_FOUND:
                database.createNotFoundHistory( device_uri )
                non_idle_status = True

            elif device_state == DEVICE_STATE_JUST_FOUND:
                database.createHistory( device_uri, status_code )

            if device_state == DEVICE_STATE_FOUND and status_code != STATUS_PRINTER_IDLE:
                #if status_code != prev_status_code:
                if 1:
                    database.createHistory( device_uri, status_code )
                    non_idle_status = True

            if non_idle_status:
                # check for low supplies        
                if device_state in ( DEVICE_STATE_FOUND, DEVICE_STATE_JUST_FOUND ):
                    tech_type = dq.get( 'tech-type' , TECH_TYPE_NONE )
                    tech_type = 2
                    if tech_type != TECH_TYPE_NONE:

                        if tech_type in ( TECH_TYPE_MONO_INK, TECH_TYPE_COLOR_INK ):
                            base = STATUS_PRINTER_LOW_INK_BASE

                        elif tech_type in ( TECH_TYPE_MONO_LASER, TECH_TYPE_COLOR_LASER ):
                            base = STATUS_PRINTER_LOW_TONER_BASE

                        a = 1
                        while True:
                            try:
                                agent_type = int( dq[ 'agent%d-type' % a ] )
                            except KeyError:
                                break
                            else:
                                agent_level_trigger = int( dq[ 'agent%d-level-trigger' % a ] )
                                agent_health = int( dq[ 'agent%d-health' % a ] )

                                if agent_health == AGENT_HEALTH_OK:

                                    if agent_level_trigger in ( AGENT_LEVEL_TRIGGER_MAY_BE_LOW,
                                                                AGENT_LEVEL_TRIGGER_PROBABLY_OUT,
                                                                AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT ):

                                        code = agent_type+base 
                                        database.createHistory( device_uri, code  )
                                        non_idle_status = True


                            a += 1

            if not non_idle_status: # and status_code != prev_status_code:
                error_state = STATUS_TO_ERROR_STATE_MAP.get( prev_status_code, ERROR_STATE_CLEAR )
                if error_state != ERROR_STATE_BUSY:
                    database.createHistory( device_uri, STATUS_PRINTER_IDLE )



        return buildResultMessage( 'DeviceQueryResult', None, result_code, dq )


    def handle_ping( self ):
        delay, fields, result_code, = -1.0, {}, ERROR_SUCCESS
        host = self.fields.get( 'host', '' )
        timeout = self.fields.get( 'timeout', 1 )
        try:
            delay = utils.ping( host, timeout )
        except Error:
            utils.log_exception()
            result_code = ERROR_INTERNAL

        return buildResultMessage( 'PingResult', '%f\n' % delay, result_code, fields )


    def handle_modelquery( self ):
        fields, result_code, = {}, ERROR_SUCCESS
        model = self.fields[ 'model' ]
        log.debug( "ModelQuery: %s" % model )

        try:
            fields = database.queryModels( model )
            #log.debug( "MQ result:\n%s" % fields )
        except Error, e:
            log.warn( "ModelQuery failed: %s (%d)" % ( e.msg, e.opt ) )
            result_code = ERROR_QUERY_FAILED

        return buildResultMessage( 'ModelQueryResult', None, result_code, fields )


    def handle_historyquery( self ):
        result_code, payload = ERROR_SUCCESS, ''
        device_uri = self.fields.get( 'device-uri', '' )
        log.debug( "HistoryQuery: %s" % device_uri )

        try:
            hist = database.devices_hist[ device_uri ].get()

        except KeyError:
            log.warn( "HistoryQuery failed: Initializing..." ) 
            database.initHistory( device_uri, hpiod_sock )
            hist = database.devices_hist[ device_uri ].get()

        for h in hist:
            payload = '\n'.join( [ payload, ','.join( [ str(x) for x in h ] ) ] ) 

        return buildResultMessage( 'HistoryQueryResult', payload, result_code )


    def handle_setalerts( self ):
        result_code = ERROR_SUCCESS
        username = self.fields.get( 'username', '' )
        email_alerts = self.fields.get( 'email-alerts', False )
        email_address = self.fields.get( 'email-address', '' )
        smtp_server = self.fields.get( 'smtp-server', '' )
        popup_alerts = self.fields.get( 'popup-alerts', True )

        database.alerts[ username ] = { 'email-alerts'  : email_alerts,
                                        'email-address' : email_address,
                                        'smtp-server'   : smtp_server,
                                        'popup-alerts'  : popup_alerts }

        return buildResultMessage( 'SetAlertsResult', None, result_code )

    # EVENT
    def handle_registerguievent( self ):
        username = self.fields.get( 'username', '' )
        admin_flag = self.fields.get( 'admin-flag', 0 )
        host = self.fields.get( 'hostname', 'localhost' )
        port = self.fields.get( 'port', 0 )
        pid = self.fields.get( 'pid', 0 )

        log.debug( "Registering GUI: %s %d %s:%d %d" % ( username, admin_flag, host, port, pid ) )

        database.guis[ username ] = { 'admin_flag'    : admin_flag, 
                                      'host'          : host, 
                                      'port'          : port,
                                    }

        if pid != 0:
            os.umask( 0133 )
            pid_file = '/var/run/hpguid-%s.pid' % username
            file( pid_file, 'w').write( '%d\n' % pid )
            os.umask( 0077 )
            log.debug( 'Wrote PID %d to %s' % ( pid, pid_file ) )


        return ''

    # EVENT
    def handle_unregisterguievent( self ):
        username = self.fields.get( 'username', '' )
        try:
            del database.guis[ username ]
        except KeyError:
            log.error( "UnRegister GUI error. Invalid username %s." % username )

        pid_file = '/var/run/hpguid-%s.pid' % username                
        log.debug( "Removing file %s" % pid_file )

        try:
            os.remove( pid_file )
        except:
            pass

        return ''


    def handle_getgui( self ):
        result_code, port, host = ERROR_SUCCESS, 0, ''
        username = self.fields.get( 'username', '' )

        try:
            host, port = self.get_guid( username )
        except Error, e:
            result_code = ERROR_GUI_NOT_AVAILABLE
            host, port = '', 0
        else:   
            try:
                s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                s.connect( ( host, port ) )
            except socket.error:
                result_code = ERROR_GUI_NOT_AVAILABLE
                host, port = '', 0
                try:
                    del database.guis[ username ]
                except KeyError:
                    pass
            else:
                s.close()

        return buildResultMessage( 'GetGUIResult', None, 
                                   result_code, { 'port' : port,
                                                  'hostname' : host 
                                                } )


    def handle_test_email( self ): 
        result_code = ERROR_SUCCESS
        try:
            to_address = self.fields[ 'email-address' ]
            smtp_server = self.fields[ 'smtp-server' ] 
            username = self.fields[ 'username' ]
            server_pass = self.fields[ 'server-pass' ] 
            from_address = '@localhost.com'
            #log.debug( "########  HOST: %s" % from_address )

            try:
                if username and server_pass:
                    from_address = username + "@" + smtp_server
                else:
                    stringName = socket.gethostname()
                    from_address = stringName + from_address
                log.debug( "Return address: %s" % from_address )
            except Error:
                log.debug( "Can't open socket" )
                result_code = ERROR_TEST_EMAIL_FAILED
                raise Error( ERROR_TEST_EMAIL_FAILED )

            msg = "From: %s\r\nTo: %s\r\n" % ( from_address, to_address )
            try:
                subject_string = database.queryStrings(  'email_test_subject' )
                log.debug( "Subject (%s)" % subject_string )
            except Error: 
                subject_string = None
                result_code = ERROR_TEST_EMAIL_FAILED
                raise Error( ERROR_TEST_EMAIL_FAILED )

            try:
                message_string = database.queryStrings( 'email_test_message' )
                log.debug( "Message (%s)" % message_string )
            except Error: 
                message_string = None
                result_code = ERROR_TEST_EMAIL_FAILED
                raise Error( ERROR_TEST_EMAIL_FAILED )

            msg = ''.join( [ msg, subject_string, '\r\n\r\n', message_string ] )

            try:
                mt = MailThread( msg, smtp_server, from_address, to_address, username, server_pass )
                mt.start() 
                mt.join() # wait for thread to finish
                result_code = mt.result # get the result
                log.debug( "MailThread had an exception (%s)" %  str(result_code) )
            except Error: 
                log.debug( "MailThread TRY: had an exception (%s)" %  str(result_code) )
                result_code = ERROR_TEST_EMAIL_FAILED
                raise Error( ERROR_TEST_EMAIL_FAILED )

        except Error, e:
            log.error( "Error: %d", e.opt )

        log.debug("hpssd.py::handle_email_test::Current error code: %s" % str(result_code))
        return buildResultMessage( 'TestEmailResult', None, result_code )    


    def handle_stringquery( self ): 
        payload, result_code = '', ERROR_SUCCESS
        string_id = self.fields[ 'string-id' ]

        try:
            payload = database.queryStrings( string_id )
        except Error: 
            #utils.log_exception()
            log.error( "String query failed for id %s" % string_id )
            payload = None
            result_code = ERROR_STRING_QUERY_FAILED

        return buildResultMessage( 'StringQueryResult', payload, result_code )

    def handle_errorstringquery( self ):
        payload, result_code = '', ERROR_STRING_QUERY_FAILED
        try:
            error_code = self.fields[ 'error-code' ]
            payload = database.queryStrings( str( error_code ) )
            result_code = ERROR_SUCCESS
        except Error:
            utils.log_exception()
            result_code = ERROR_STRING_QUERY_FAILED

        return buildResultMessage( 'ErrorStringQueryResult', payload, result_code )


    # EVENT
    def handle_event( self ):
        #try:
        if 1:
            gui_port, gui_host = None, None

            event_code = self.fields[ 'event-code' ]
            event_type = self.fields[ 'event-type' ]

            log.debug( "code (type): %d (%s)" % ( event_code, event_type ) )

            try:
                error_string_short = database.queryStrings( str( event_code ), 0 )
            except Error:
                error_string_short = ''

            try:
                error_string_long = database.queryStrings( str( event_code ), 1 )
            except Error:
                error_string_long = ''

            log.debug( "short: %s" % error_string_short )
            log.debug( "long: %s" % error_string_long )

            job_id = self.fields.get( 'job-id', 0 )

            try:
                username = self.fields[ 'username' ]
            except KeyError:
                if job_id == 0:
                    username = prop.username
                else:
                    jobs = cups.getAllJobs() 

                    for j in jobs:
                        if j.id == job_id:
                            username = j.user
                            break
                    else:
                        username = prop.username


            no_fwd = self.fields.get( 'no-fwd', False )

            log.debug( "username (jobid): %s (%d)" % ( username, job_id ) )

            retry_timeout = self.fields.get( 'retry-timeout', 0 )
            device_uri = self.fields.get( 'device-uri', '' )

            database.createHistory( device_uri, event_code, job_id, username )

            try:
                gui_host, gui_port = self.get_guid( username )
            except Error, e:
                log.warn( "No GUI available. (%d)" % e.opt )
                raise Error( e.opt )

            log.debug( "%s:%d" % ( gui_host, gui_port ) )

            user_alerts = database.alerts.get( username, {} )

            if not no_fwd:
                if gui_host is not None and gui_port is not None:

                    log.debug( "Sending to GUI..." )
                    try:
                        s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                        s.connect( ( gui_host, gui_port) )
                    except socket.error:
                        log.error( "Unable to communicate with GUI on port %d" % gui_port )
                    else:
                        try:
                            sendEvent( s, 'EventGUI', 
                                          '%s\n%s\n' % ( error_string_short, error_string_long ),
                                         { 'job-id' : job_id,
                                           'event-code' : event_code,
                                           'event-type' : event_type,
                                           'retry-timeout' : retry_timeout,
                                           'device-uri' : device_uri,
                                           'popup' : user_alerts.get( 'popup-alerts', False ),
                                         }
                                        )
                        except Error,e:
                            log.error( "Error sending event to GUI. (%d)" % e.opt )

                        s.close()

                    # TODO: also send msg to all admin guid's???

                else: # gui not registered or user no longer logged on
                    log.warn( "Unable to find GUI to display error" )
            else:
                log.debug( "Not sending to GUI, no_fwd=True" )


            if user_alerts.get( 'email-alerts', False ) and event_type == 'error':

                fromaddr = prop.username + '@localhost'
                toaddrs = user_alerts.get( 'email-address', 'root@localhost' ).split()
                smtp_server = user_alerts.get( 'smtp-server', 'localhost' )
                msg = "From: %s\r\nTo: %s\r\n\r\n" % ( fromaddr, ', '.join(toaddrs) )
                msg = msg + 'Printer: %s\r\nCode: %d\r\nError: %s\r\n' % ( device_uri, event_code, error_string_short )

                mt = MailThread( msg, 
                                 smtp_server, 
                                 fromaddr, 
                                 toaddrs )
                mt.start()

        #finally:
        #    utils.log_exception()

        return ''

    # EVENT
    def handle_exituievent( self ):
        try:
            username = self.fields[ 'username' ]
            try:
                gui_host, gui_port = self.get_guid( username )
            except Error, e:
                log.error( "No GUI available. (%d)" % e.opt )
                raise Error( e.opt )

            log.debug( "Sending to GUI..." )
            s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            s.connect( ( gui_host, gui_port ) )

            try:
                sendEvent( s, 'ExitGUIEvent' )
            except Error, e:
                log.error( "Error sending event to GUI. (%d)" % e.opt )
            s.close()

        finally:
            utils.log_exception()

        return ''

    # EVENT    
    def handle_showuievent( self ):
        try:
            ui_id = self.fields[ 'ui-id' ]
            username = self.fields[ 'username' ]

            log.debug( "ShowUI: %s %s" % ( ui_id, username ) )
            try:
                gui_host, gui_port = self.get_guid( username )
            except Error, e:
                log.warning( "No GUI available. (%d)" % e.opt )
                raise Error( e.opt )

            log.debug( "Sending to GUI..." )
            s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            s.connect( ( gui_host, gui_port ) )

            try:
                sendEvent( s, 'ShowGUIEvent', None, 
                           { 'ui-id' : ui_id, 
                            'username' : username } )
            except Error, e:
                log.warning( "Error sending event to GUI. (%d)" % e.opt )
                raise Error( e.opt )

            s.close()

        finally:
            utils.log_exception()

        return ''


    def handle_probedevicesfiltered( self ):
        payload, result_code = '', ERROR_SUCCESS
        num_devices, ret_devices = 0, {}

        buses = self.fields.get( 'bus', 'cups,usb' )
        buses = buses.split(',')
        format = self.fields.get( 'format', 'default' )

        for b in buses:
            bus = b.lower().strip()
            if bus == 'net':
                ttl = int( self.fields.get( 'ttl', 4 ) )
                timeout = int( self.fields.get( 'timeout', 5 ) )

                try:
                    devices = slp.detectNetworkDevices( '224.0.1.60', 427, ttl, timeout )  
                except Error:
                    log.error( "An error occured during network probe." )
                else:
                    for ip in devices:
                        hn = devices[ip].get( 'hn', '?UNKNOWN?' )
                        num_devices_on_jd = devices[ip].get( 'num_devices', 0 )
                        num_ports_on_jd = devices[ip].get( 'num_ports', 1 )

                        if num_devices_on_jd > 0:
                            for port in range( num_ports_on_jd ):
                                dev = devices[ip].get( 'device%d' % (port+1), '0' )

                                if dev is not None and dev != '0':
                                    device_id = device.parseDeviceID( dev )
                                    model = device_id.get( 'MDL', '?UNKNOWN?' ).replace( ' ', '_' ).replace( '/', '_' )

                                    if num_ports_on_jd == 1:
                                        device_uri = 'hp:/net/%s?ip=%s' % ( model, ip )
                                    else:  
                                        device_uri = 'hp:/net/%s?ip=%s&port=%d' % ( model, ip, (port+1) )

                                    device_filter = self.fields.get( 'filter', 'none' )

                                    if device_filter in ( 'none', 'print' ):
                                        include = True
                                    else:
                                        include = True

                                        try:
                                            fields = database.queryModels( model )
                                        except Error:
                                            continue

                                        for f in device_filter.split(','):
                                            filter_type = int( fields.get( '%s-type' % f.lower().strip(), 0 ) )
                                            if filter_type == 0:
                                                include = False
                                                break

                                    if include:
                                        ret_devices[ device_uri ] = ( model, hn )


            elif bus == 'usb': 
                try:
                    fields, data = xmitMessage( hpiod_sock, 
                                                "ProbeDevices", 
                                                 None, 
                                                 { 
                                                    'bus' : 'usb' 
                                                 } 
                                              )                
                except Error:
                    devices = []
                else:
                    devices = [ x.split(' ')[1] for x in data.splitlines() ]

                for d in devices:
                    try:
                        back_end, is_hp, bus, model, serial, dev_file, host, port = \
                            device.parseDeviceURI( d )
                    except Error:
                        log.warning( "Inrecognized URI: %s" % d )
                        continue

                    if is_hp:

                        device_filter = self.fields.get( 'filter', 'none' )

                        if device_filter in ( 'none', 'print' ):
                            include = True
                        else:
                            include = True

                            try:
                                fields = database.queryModels( model )
                            except Error:
                                continue

                            for f in device_filter.split(','):
                                filter_type = int( fields.get( '%s-type' % f.lower().strip(), 0 ) )
                                if filter_type == 0:
                                    include = False
                                    break

                        if include:
                            ret_devices[ d ] = ( model, '' )

            elif bus == 'cups':

                cups_devices = {}
                cups_printers = cups.getPrinters()
                x = len( cups_printers )

                for p in cups_printers:
                    device_uri = p.device_uri

                    if p.device_uri != '':

                        device_filter = self.fields.get( 'filter', 'none' )

                        try:
                            back_end, is_hp, bs, model, serial, dev_file, host, port = \
                                device.parseDeviceURI( device_uri )
                        except Error:
                            log.warning( "Inrecognized URI: %s" % device_uri )
                            continue


                        if device_filter in ( 'none', 'print' ):
                            include = True
                        else:
                            include = True

                            try:
                                fields = database.queryModels( model )
                            except Error:
                                continue

                            for f in device_filter.split(','):
                                filter_type = int( fields.get( '%s-type' % f.lower().strip(), 0 ) )
                                if filter_type == 0:
                                    include = False
                                    break

                        if include:
                            ret_devices[ device_uri ] = ( model, '' )


        for d in ret_devices:
            num_devices += 1

            if format == 'default':
                payload = ''.join( [ payload, d, ',', ret_devices[d][0], '\n' ] )
            else:
                if ret_devices[d][1] != '':
                    payload = ''.join( [ payload, 'direct ', d, ' "HP ', ret_devices[d][0], '" "', ret_devices[d][1], '"\n' ] )
                else:
                    payload = ''.join( [ payload, 'direct ', d, ' "HP ', ret_devices[d][0], '" "', d, '"\n' ] )


        return buildResultMessage( 'ProbeDevicesFilteredResult', payload, 
                                   result_code, { 'num-devices' : num_devices } )


    # EVENT
    def handle_exit( self ):
        self.signal_exit = True
        return ''

    def handle_messageerror( self ):
        return ''

    def writable( self ):
        return not ( ( len( self.out_buffer ) == 0 ) 
                     and self.connected )


    def handle_close( self ):
        log.debug( "closing channel (%d)" % self._fileno )
        self.connected = False
        self.close()

    def get_guid( self, username ):
        try:
            gui = database.guis[ username ]
            gui_host = gui[ 'host' ]
            gui_port = int( gui[ 'port' ] )
        except:
            raise Error( ERROR_GUI_NOT_AVAILABLE )

        return gui_host, gui_port

class MailThread( threading.Thread ):
    def __init__( self, message, smtp_server, from_addr, to_addr_list, username, server_pass ):
        threading.Thread.__init__( self )
        self.message = message
        self.smtp_server = smtp_server
        self.to_addr_list = to_addr_list
        self.from_addr = from_addr
        self.result = ERROR_SUCCESS
        self.username = username
        self.server_pass = server_pass

    def run( self ):
        log.debug( "Starting Mail Thread" )
        try:
            server = smtplib.SMTP( self.smtp_server, smtplib.SMTP_PORT, 'localhost' ) 
            server.set_debuglevel(True)
            if self.username and self.server_pass:
                try:
                    server.starttls();
                    server.login(self.username, self.server_pass)
                except (smtplib.SMTPHeloError, smtplib.SMTPException), e:
                    log.error( "SMTP Server Login Error: Unable to connect to server: %s" % e )
                    self.result = ERROR_SMTP_LOGIN_HELO_ERROR

                except (smtplib.SMTPAuthenticationError), e:
                    log.error( "SMTP Server Login Error: Unable to authenicate with server: %s" % e )
                    self.result = ERROR_SMTP_AUTHENTICATION_ERROR
        except smtplib.SMTPConnectError, e:
            log.error( "SMTP Error: Unable to connect to server: %s" % e )
            self.result = ERROR_SMTP_CONNECT_ERROR

        try:
            server.sendmail( self.from_addr, self.to_addr_list, self.message )
            log.debug("hpssd.py::MailThread::Current error code: %s" % str(self.result))
        except smtplib.SMTPRecipientsRefused, e:
            log.error( "SMTP Errror: All recepients refused: %s" % e )
            self.result = ERROR_SMTP_RECIPIENTS_REFUSED
        except smtplib.SMTPHeloError, e:
            log.error( "SMTP Errror: Invalid server response to HELO command: %s" % e )
            self.result = ERROR_SMTP_HELO_ERROR
        except smtplib.SMTPSenderRefused, e:
            log.error( "SMTP Errror: Recepient refused: %s" % e )
            self.result = ERROR_SMTP_SENDER_REFUSED
        except smtplib.SMTPDataError, e:
            log.error( "SMTP Errror: Unknown error: %s" % e )
            self.result = ERROR_SMTP_DATA_ERROR

        server.quit()
        log.debug( "Exiting mail thread" )


def reInit():    
    database.initModels()
    database.initStrings()
    #device_r_cache.update( database.initHistories( hpiod_sock ) )

def handleSIGHUP( signo, frame ):
    log.info( "SIGHUP" )
    reInit()

def exitAllGUIs():
    log.debug( "Sending EXIT to all registered GUIs" )
    for gui in database.guis:
        g = database.guis[ gui ]
        try:
            gui_host = g[ 'host' ]
            gui_port = int( g[ 'port' ] )
        except:
            pass
        else:
            log.debug( "Closing GUI %s:%d" % ( gui_host, gui_port ) )
            try:
                s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                s.connect( ( gui_host, gui_port) )
            except socket.error:
                log.error( "Unable to communicate with GUI on port %d" % gui_port )
            else:
                try:
                    sendEvent( s, 'ExitGUIEvent', None, {} )
                except Error,e:
                    log.warning( "Unable to send event to GUI (%s:%s). (%d)" % ( gui_host, gui_port, e.opt ) )

                s.close()





def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( utils.TextFormatter.bold( """\nUsage: hpssd.py [OPTIONS]\n\n""" ) )

    log.info( formatter.compose( ( utils.TextFormatter.bold("[OPTIONS]"), "" ) ) )

    log.info( formatter.compose( ( "Set the logging level:",   "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                         "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "Disable daemonize:",       "-x" ) ) )
    log.info( formatter.compose( ( "This help information:",   "-h or --help" ), True ) )

hpiod_sock = None

def main( args ):

    prop.prog = sys.argv[0]        
    prop.daemonize = True
    log.set_module( 'hpssd' )

    utils.log_title( 'Services and Status Daemon', _VERSION )

    try:
        opts, args = getopt.getopt( sys.argv[1:], 'l:xhp:', [ 'level=', 'help', 'port=' ] ) 

    except getopt.GetoptError:
        usage()
        sys.exit(1)

    for o, a in opts:
        if o in ( '-l', '--logging' ):
            log_level = a.lower().strip()
            log.set_level( log_level )

        elif o in ( '-x', ):
            prop.daemonize = False

        elif o in ( '-h', '--help' ):
            usage()
            sys.exit(1)

        elif o in ( '-p', '--port' ):
            try:
                prop.hpssd_cfg_port = int( a )
            except ValueError:
                log.error( 'Port must be a numeric value' )
                sys.exit(1)


    prop.history_size = 32

    # Lock pidfile before we muck around with system state
    # Patch by Henrique M. Holschuh <hmh@debian.org>
    utils.get_pidfile_lock('/var/run/hpssd.pid')

    # Spawn child right away so that boot up sequence
    # is as fast as possible
    if prop.daemonize:
        utils.daemonize()

    # configure the various data stores
    gettext.install( 'hplip' )
    reInit()

    # hpssd server dispatcher object
    try:
        server = hpssd_server( prop.hpssd_host, prop.hpssd_cfg_port )
        log.debug( str( server ) )
    except Error, e:
        log.error( "Server exited with error: %s" % e.msg ) 
        sys.exit( -1 )

    os.umask( 0133 )
    file( '/var/run/hpssd.port', 'w' ).write( '%d\n' % prop.hpssd_port )
    os.umask (0077 )
    log.debug( 'port=%d' % prop.hpssd_port )
    log.info( "Listening on %s port %d" % ( prop.hpssd_host, prop.hpssd_port ) )

    global hpiod_sock
    try:
        hpiod_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        hpiod_sock.connect( ( prop.hpiod_host, prop.hpiod_port ) )
    except socket.error:
        log.error( "Unable to connect to hpiod." )
        sys.exit(-1)

    atexit.register( exitAllGUIs )        
    signal.signal( signal.SIGHUP, handleSIGHUP )

    try:
        log.debug( "Starting async loop..." )
        try:
            async.loop( timeout=1.0 )
        except KeyboardInterrupt:
            log.warn( "Ctrl-C hit, exiting..." )
        except async.ExitNow:
            log.warn( "Exit message received, exiting..." )
        except Exception:
            utils.log_exception()

        log.debug( "Cleaning up..." )
    finally:
        os.remove( '/var/run/hpssd.pid' )
        os.remove( '/var/run/hpssd.port' )
        server.close()
        hpiod_sock.close()

if __name__ == "__main__":
    sys.exit( main( sys.argv[1:] ) )


