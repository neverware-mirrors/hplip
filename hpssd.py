#!/usr/bin/env python
#
# $Revision: 1.49 $ 
# $Date: 2005/01/07 23:19:57 $
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


# Remove in 2.3
from __future__ import generators

_VERSION = '3.0'


# Std Lib
import sys
import socket
import os, os.path
import signal
import getopt
import time
import pwd
import ConfigParser
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



AGENT_types = { status.AGENT_TYPE_NONE        : 'invalid',
                status.AGENT_TYPE_BLACK       : 'black',
                status.AGENT_TYPE_CMY         : 'cmy',
                status.AGENT_TYPE_KCM         : 'kcm',
                status.AGENT_TYPE_CYAN        : 'cyan',
                status.AGENT_TYPE_MAGENTA     : 'magenta',
                status.AGENT_TYPE_YELLOW      : 'yellow',
                status.AGENT_TYPE_CYAN_LOW    : 'photo_cyan',
                status.AGENT_TYPE_MAGENTA_LOW : 'photo_magenta',
                status.AGENT_TYPE_YELLOW_LOW  : 'photo_yellow',
                status.AGENT_TYPE_GGK         : 'photo_gray',
                status.AGENT_TYPE_BLUE        : 'photo_blue',
            }

AGENT_kinds = { status.AGENT_KIND_NONE            : 'invalid',
                status.AGENT_KIND_HEAD            : 'head',
                status.AGENT_KIND_SUPPLY          : 'supply',
                status.AGENT_KIND_HEAD_AND_SUPPLY : 'cartridge',
            }
            
AGENT_healths = { status.AGENT_HEALTH_OK           : 'ok',
                  status.AGENT_HEALTH_MISINSTALLED : 'misinstalled',
                  status.AGENT_HEALTH_INCORRECT    : 'incorrect',
                  status.AGENT_HEALTH_FAILED       : 'failed',
                }


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
        except socket.error, e:
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


        
def _getHpguid( username ):
    try:
        gui = database.guis[ username ]
        gui_host = gui[ 'host' ]
        gui_port = int( gui[ 'port' ] )
    except:
        log.warning( "Unable to find GUI for username %s." % username )
        raise Error( ERROR_GUI_NOT_AVAILABLE )
    
    return gui_host, gui_port

def _getUsername( job_id ):
    if job_id is None or job_id == 0:
        prop.username
    
    elif job_id is not None:
        jobs = cups.getAllJobs() 
        
        for j in jobs:
            if j.id == job_id:
                return j.user
        
    return prop.username



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
        
        self.device_r_cache = {} # { 'model' : ( r_value, r_value_str, rg, rr ), ... }
        
        # handlers for all the messages we expect to receive
        self.handlers = { 
                            # Primary Request/Reply Messages
                            'stringquery'          : self.handle_stringquery,
                            'errorstringquery'     : self.handle_errorstringquery,
                            'modelquery'           : self.handle_modelquery,
                            'historyquery'         : self.handle_historyquery,
                            'probedevicesfiltered' : self.handle_probedevicesfiltered,
                            'setalerts'            : self.handle_setalerts,
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
        log.debug( "%s %s %s" % ("*"*40, msg_type, "*"*40 ) ) 
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
        fields, result_code, = {}, ERROR_SUCCESS
        device_state = 'unknown'
        d = None
        #try:
        if 1:
            device_uri = self.fields[ 'device-uri' ]
            prev_device_state = self.fields[ 'device-state-previous' ]
            make_history = self.fields[ 'make-history' ]
            
            d = device.Device( hpiod_sock, device_uri )
            
            device_state = d.determineIOState( force=False, leave_open=True, 
                                               do_ping=True, prev_device_state=prev_device_state )
            
            fields[ 'device-state' ] = device_state
            
            if not database.checkHistory( device_uri ) or make_history:
                
                if device_state == device.DEVICE_STATE_NOT_FOUND and \
                    prev_device_state in ( device.DEVICE_STATE_FOUND, device.DEVICE_STATE_JUST_FOUND ): 
                    
                    database.createNotFoundHistory( device_uri )
            
                elif device_state == device.DEVICE_STATE_JUST_FOUND: 
                    database.createIdleHistory( device_uri )
                
            
            try:
                mq = database.queryModels( d.model )
                fields.update( mq )
            except Error, e:
                log.warn( "ModelQuery failed: %s (%d)" % ( e.msg, e.opt ) )
                mq = {}

            status_type = int( mq.get( 'status-type', 0 ) )
            
            log.debug( "status-type=%d" % status_type )
            log.debug( "io-state=%d" % d.io_state )
            
            if d.io_state == device.IO_STATE_HP_OPEN:
               
                fields[ 'serial-number' ] = d.serialNumber() 
                fields[ 'dev-file' ] = d.devFile()
                code, name = d.threeBitStatus()
                fields[ 'status-code' ] = code
                fields[ 'status-name' ] = name
                parsed, raw = d.ID()
                fields[ 'deviceid' ] = raw
                agents = []
                
                status_code, status_name = d.threeBitStatus()
                fields[ 'status-code' ] = status_code 
                fields[ 'status-name' ] = status_name 

                if status_type == 0:
                    log.warn( "No status available for device." )
                    
                elif status_type in [1,2]:
                    log.debug( "Using S: or VSTATUS:" )
                    if 'S' in parsed or 'VSTATUS' in parsed:
                        status_block = status.parseStatus( parsed )
                        fields.update( status_block )
                        if 'agents' in fields:
                            del fields[ 'agents' ]
                        agents = status_block[ 'agents' ]
                        
                        
                elif status_type == 3:
                    log.warn( "Unimpletemented status type." )
                
                elif status_type == 4:
                    log.warn( "Unimpletemented status type." )

                elif status_type == 5:
                    log.warn( "Unimpletemented status type." )

                elif status_type == 6:
                    log.warn( "Unimpletemented status type." )
                
                r_value, rg, rr, r_value_str = 0, '000', '000000', '000000000'
                r_type = int( mq.get( 'r-type', '0' ) )
                
                if r_type > 0:
                    if d.model not in self.device_r_cache:
                        try:
                            r_value = d.getDynamicCounter( 140 )
                            r_value_str = str( r_value )
                            r_value_str = ''.join( [ '0'*(9 - len(r_value_str)), r_value_str ] )
                            rg = r_value_str[:3]
                            rr = r_value_str[3:]
                            r_value = int( rr )
                        except:
                            pass
                        else:
                            self.device_r_cache[ d.model ] =  ( r_value, r_value_str, rg, rr )
                        
                    else:
                        r_value, r_value_str, rg, rr = self.device_r_cache[ d.model ]
                
                fields[ 'r' ] = r_value
                fields[ 'rs' ] = r_value_str
                fields[ 'rg' ] = rg
                fields[ 'rr' ] = rr
                
                a = 1
                while True:
                    mq_agent_kind = int( mq.get( 'r%d-agent%d-kind' % ( r_value, a ), '0' ) )
                    
                    if mq_agent_kind == 0:
                        break
                    
                    mq_agent_type = int( mq.get( 'r%d-agent%d-type' % ( r_value, a ), '0' ) )
                    mq_agent_sku =       mq.get( 'r%d-agent%d-sku' % ( r_value, a ), '???' )

                    found = False
                    for agent in agents:
                        agent_kind = agent['kind']
                        agent_type = agent['type']
                        
                        if agent_kind == mq_agent_kind and \
                           agent_type == mq_agent_type:
                           found = True
                           break
                    
                    if found:
                        fields[ 'agent%d-kind' % a ] = agent_kind
                        fields[ 'agent%d-type' % a ] = agent_type
                        fields[ 'agent%d-level' % a ] = agent.get('level', 0 )
                        fields[ 'agent%d-ack' % a ] = agent.get( 'ack', False )
                        fields[ 'agent%d-hp-ink' % a ] = agent.get('hp-ink', True )
                        fields[ 'agent%d-dvc' % a ] = agent.get( 'dvc', 0 )
                        fields[ 'agent%d-level-trigger' % a ] = agent.get( 'level-trigger', 0 )
                        fields[ 'agent%d-virgin' % a ] = agent.get( 'virgin', True )
                        agent_health = agent.get( 'health', 0 )
                        fields[ 'agent%d-health' % a ] = agent_health
                        fields[ 'agent%d-known' % a ] = agent.get( 'known', True )
                        fields[ 'agent%d-sku' % a ] = mq_agent_sku
                        
                    else:
                        fields[ 'agent%d-kind' % a ] = mq_agent_kind
                        agent_kind = mq_agent_kind
                        fields[ 'agent%d-type' % a ] = mq_agent_type
                        agent_type = mq_agent_type
                        fields[ 'agent%d-sku' % a ]  = mq_agent_sku
                        fields[ 'agent%d-level' % a ] = 0
                        agent_health = status.AGENT_HEALTH_MISINSTALLED
                        fields[ 'agent%d-health' % a ] = agent_health
                        fields[ 'agent%d-ack' % a ] = False
                        fields[ 'agent%d-hp-ink' % a ] = False
                        fields[ 'agent%d-dvc' % a ] = 0
                        fields[ 'agent%d-level-trigger' % a ] = 0
                        fields[ 'agent%d-virgin' % a ] = False
                        fields[ 'agent%d-known' % a ] = False
                        
                    string_query = 'agent_%s_%s' % ( AGENT_types.get( agent_type, 'unknown' ), 
                                                     AGENT_kinds.get( agent_kind, 'unknown' ) )
                    
                    fields[ 'agent%d-desc' % a ] = database.queryStrings( string_query )
                    
                    string_query = 'agent_health_%s' % AGENT_healths.get( agent_health, 'unknown' )
                    fields[ 'agent%d-health-desc' % a ] = database.queryStrings( string_query )
                    

                    a += 1
                
   
                            
        #finally:
        if 1:
            if d is not None:
                d.close()
            return buildResultMessage( 'DeviceQueryResult', None, result_code, fields )
            
            
    def handle_ping( self ):
        delay, fields, result_code, = -1.0, {}, ERROR_SUCCESS
        if 1:
            host = self.fields[ 'host' ]
            timeout = self.fields.get( 'timeout', 1 )
            delay = utils.ping( host, timeout )
        if 1:
            return buildResultMessage( 'PingResult', '%f\n' % delay, result_code, fields )
            
    
    def handle_modelquery( self ):
        fields, result_code, = {}, ERROR_SUCCESS
        #try:
        if 1:
            model = self.fields[ 'model' ]
            log.debug( "ModelQuery: %s" % model )
            
            try:
                fields = database.queryModels( model )
                log.debug( "MQ result:\n%s" % fields )
            except Error, e:
                log.warn( "ModelQuery failed: %s (%d)" % ( e.msg, e.opt ) )
                result_code = ERROR_QUERY_FAILED
        #finally:
        if 1:
            return buildResultMessage( 'ModelQueryResult', None, result_code, fields )
    

    def handle_historyquery( self ):
        result_code, payload = ERROR_SUCCESS, ''
        ##try:
        if 1:
            device_uri = self.fields[ 'device-uri' ]
            log.debug( "HistoryQuery: %s" % device_uri )
            
            try:
                hist = database.devices_hist[ device_uri ].get()
            
            except KeyError:
                log.warn( "HistoryQuery failed: Initializing..." ) 
                hist = database.initHistory( device_uri, hpiod_sock )

            for h in hist:
                payload = '\n'.join( [ payload, ','.join( [ str(x) for x in h ] ) ] ) 
        ##finally:
        if 1:
            return buildResultMessage( 'HistoryQueryResult', payload, result_code )


    
    
    def handle_setalerts( self ):
        result_code = ERROR_SUCCESS
        try:
            username = self.fields.get( 'username', '' )
            email_alerts = self.fields.get( 'email-alerts', False )
            email_address = self.fields.get( 'email-address', '' )
            smtp_server = self.fields.get( 'smtp-server', '' )
            popup_alerts = self.fields.get( 'popup-alerts', True )
            
            database.alerts[ username ] = { 'email-alerts'  : email_alerts,
                                            'email-address' : email_address,
                                            'smtp-server'   : smtp_server,
                                            'popup-alerts'  : popup_alerts }

        finally:
            return buildResultMessage( 'SetAlertsResult', None, result_code )
    
    # EVENT
    def handle_registerguievent( self ):
        try:
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
                log.debug( 'Wrote PID %d to %s' % ( pid, pid_file ) )

            
        finally:
            return ''
    
    # EVENT
    def handle_unregisterguievent( self ):
        try:
            username = self.fields.get( 'username', '' )
            pid = self.fields.get( 'pid', 0 )
            
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
            
        finally:
            return ''
    
    
    def handle_getgui( self ):
        result_code, port, host = ERROR_SUCCESS, 0, ''
        try:
            username = self.fields[ 'username' ]
            try:
                port = database.guis[ username ][ 'port' ]
                host = database.guis[ username ][ 'host' ]
            except KeyError:
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

        finally:        
            return buildResultMessage( 'GetGUIResult', None, 
                           result_code, { 'port' : port,
                                          'hostname' : host 
                                        } )
    
    
    def handle_stringquery( self ): 
        payload, result_code = '', ERROR_SUCCESS
        try:
            string_id = self.fields[ 'string-id' ]
            try:
                payload = database.queryStrings( string_id )
            except Error: 
                payload = None
                result_code = ERROR_STRING_QUERY_FAILED
        finally:
            return buildResultMessage( 'StringQueryResult', payload, result_code )
            
    def handle_errorstringquery( self ):
        payload, result_code = '', ERROR_STRING_QUERY_FAILED
        try:
            error_code = self.fields[ 'error-code' ]
            payload = database.queryStrings( str( error_code ) )
            result_code = ERROR_SUCCESS
        finally:
            return buildResultMessage( 'ErrorStringQueryResult', payload, result_code )
  
    
    # EVENT
    def handle_event( self ):
        if 1:
        #try:
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
                username = _getUsername( job_id )
            
            no_fwd = self.fields.get( 'no-fwd', False )
            
            log.debug( "username (jobid): %s (%d)" % ( username, job_id ) )
            
            retry_timeout = self.fields.get( 'retry-timeout', 0 )
            device_uri = self.fields.get( 'device-uri', '' )
            
            try:
                database.devices_hist[ device_uri ]
            except KeyError:
                database.devices_hist[ device_uri ] = utils.RingBuffer( prop.history_size )

            database.devices_hist[ device_uri ].append( tuple( time.localtime() ) + 
                                                        ( job_id, username, event_code, 
                                                          error_string_short, 
                                                          error_string_long ) )
                                                          
            try:
                gui_host, gui_port = _getHpguid( username )
            except Error, e:
                log.error( "No GUI available. (%d)" % e.opt )
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
                    log.error( "Unable to find GUI to display error" )
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
        if 1:
            return ''
   
    # EVENT
    def handle_exituievent( self ):
        try:
            username = self.fields[ 'username' ]
            try:
                gui_host, gui_port = _getHpguid( username )
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
            return ''
    
    # EVENT    
    def handle_showuievent( self ):
        try:
            ui_id = self.fields[ 'ui-id' ]
            username = self.fields[ 'username' ]
            
            log.debug( "ShowUI: %s %s" % ( ui_id, username ) )
            try:
                gui_host, gui_port = _getHpguid( username )
            except Error, e:
                log.error( "No GUI available. (%d)" % e.opt )
                raise Error( e.opt )
    
            log.debug( "Sending to GUI..." )
            s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            s.connect( ( gui_host, gui_port ) )
            
            try:
                sendEvent( s, 'ShowGUIEvent', None, 
                           { 'ui-id' : ui_id, 
                            'username' : username } )
            except Error, e:
                log.error( "Error sending event to GUI. (%d)" % e.opt )
            
            s.close()
            
        finally:
            return ''
 
       
    def handle_probedevicesfiltered( self ):
        payload, result_code = '', ERROR_SUCCESS
        num_devices = 0
        #try:
        if 1:
            bus = self.fields.get( 'bus', 'usb' )
            format = self.fields.get( 'format', 'default' )
            
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
                                    product_id = devices[ip].get( 'product_id', '?UNKNOWN?' )
                                    device_id = device.parseDeviceID( dev )
                                    model = device_id.get( 'MDL', '?UNKNOWN?' ).replace( ' ', '_' ).replace( '/', '_' )
                                    
                                    if num_ports_on_jd == 1:
                                        device_uri = 'hp:/net/%s?ip=%s' % ( model, ip )
                                    else:  
                                        device_uri = 'hp:/net/%s?ip=%s&port=%d' % ( model, ip, (port+1) )
                                
                                    filter = self.fields.get( 'filter', 'none' )
                
                                    if filter in ( 'none', 'print' ):
                                        include = True
                                    else:
                                        include = True
                
                                        try:
                                            fields = database.queryModels( model )
                                        except Error:
                                            continue
                
                                        for f in filter.split(','):
                                            filter_type = int( fields.get( '%s-type' % f.lower().strip(), 0 ) )
                                            if filter_type == 0:
                                                include = False
                                                break
                
                                    if include:
                                        num_devices += 1
                                        if format == 'default':
                                            payload = ''.join( [ payload, device_uri, ',', model, '\n' ] )
                                        else:
                                            payload = ''.join( [ payload, 'direct ', device_uri, ' "', hn, '" ', '"HP ', model, '"\n' ] )
                
                    
            else:
                devices = device.probeDevices( bus, hpiod_sock )

                for d in devices:
                    back_end, is_hp, bus, model, serial, dev_file, host, port = device.parseDeviceURI( d )
    
                    if is_hp:
    
                        filter = self.fields.get( 'filter', 'none' )
    
                        if filter in ( 'none', 'print' ):
                            include = True
                        else:
                            include = True

                            try:
                                fields = database.queryModels( model )
                            except Error:
                                continue

                            for f in filter.split(','):
                                filter_type = int( fields.get( '%s-type' % f.lower().strip(), 0 ) )
                                if filter_type == 0:
                                    include = False
                                    break
    
                        if include:
                            num_devices += 1
                            if format == 'default':
                                payload = ''.join( [ payload, d, ',', model, '\n' ] )
                            else:
                                payload = ''.join( [ payload, 'direct ', d, ' "HP ', model, '" "', d, '"\n' ] )
        #finally:
        if 1:
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
    
 

class MailThread( threading.Thread ):
    def __init__( self, message, smtp_server, from_addr, to_addr_list ):
        threading.Thread.__init__( self )
        self.message = message
        self.smtp_server = smtp_server
        self.to_addr_list = to_addr_list
        self.from_addr = from_addr
    
    def run( self ):
        log.debug( "Starting Mail Thread" )
        try:
            server = smtplib.SMTP( self.smtp_server ) 
        except smtplib.SMTPConnectError, e:
            log.error( "SMTP Error: Unable to connect to server: %s" % e )

        else:
            try:
                server.sendmail( self.from_addr, self.to_addr_list, self.message )
            except smtplib.SMTPRecipientsRefused, e:
                log.error( "SMTP Errror: All recepients refused: %s" % e )
            except smtplib.SMTPHeloError, e:
                log.error( "SMTP Errror: Invalid server response to HELO command: %s" % e )
            except smtplib.SMTPSenderRefused, e:
                log.error( "SMTP Errror: Recepient refused: %s" % e )
            except smtplib.SMTPDataError, e:
                log.error( "SMTP Errror: Unknown error: %s" % e )
            
            server.quit()
        
        log.debug( "Exiting mail thread" )




def reInit():    
    database.initDatabases( hpiod_sock )
    #TODO: Reset connections, devices, etc.
    
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


    prop.history_size = 20

    # Lock pidfile before we muck around with system state
    # Patch by Henrique M. Holschuh <hmh@debian.org>
    utils.get_pidfile_lock('/var/run/hpssd.pid')

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
    log.debug( 'port=%d' % prop.hpssd_port )
    log.info( "Listening on %s port %d" % ( prop.hpssd_host, prop.hpssd_port ) )
    
    global hpiod_sock
    try:
        hpiod_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        hpiod_sock.connect( ( prop.hpiod_host, prop.hpiod_port ) )
    except socket.error:
        log.error( "Unable to connect to hpiod." )
        sys.exit(-1)
    
        
    if prop.daemonize:
        utils.daemonize()
        
    atexit.register( exitAllGUIs )        
    signal.signal( signal.SIGHUP, handleSIGHUP )
    #signal.signal( signal.SIGPIPE, signal.SIG_IGN )
        
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
    
    
