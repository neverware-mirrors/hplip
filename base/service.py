#!/usr/bin/env python
#

# $Revision: 1.25 $ 
# $Date: 2005/03/18 22:44:31 $
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


#Std Lib
import socket
import cStringIO

# Local
from g import *
from codes import *
import msg
import utils
from prnt import cups
import status


class Service:

    def __init__( self, hpssd_sock=None ):
        
        if hpssd_sock is None:
            self.hpssd_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            try:
                self.hpssd_sock.connect( ( prop.hpssd_host, prop.hpssd_port ) )
            except socket.error:
                raise Error( ERROR_UNABLE_TO_CONTACT_SERVICE )
            self.close_hpssd_sock = True
        else:
            self.hpssd_sock = hpssd_sock
            self.close_hpssd_sock = False
            
    
    def probeDevices( self, bus='usb', timeout=5, ttl=4, fltr='' ):
        fields, data = msg.xmitMessage( self.hpssd_sock, 
                                        "ProbeDevicesFiltered",
                                        None, 
                                        { 
                                            'bus' : bus,
                                            'timeout' : timeout,
                                            'ttl' : ttl,
                                            'format' : 'default',
                                            'filter' : fltr,
                                                
                                        } 
                                      )
    
        temp = data.splitlines()            
        probed_devices = []
        for t in temp:
            probed_devices.append( t.split(',')[0] )
            
        return probed_devices

    
    def queryDevice( self, device_uri, prev_device_state, prev_status_code, make_history=True ):
    
        fields, data = msg.xmitMessage( self.hpssd_sock, 
                                        "DeviceQuery",
                                        None, 
                                        { 
                                            'device-uri' : device_uri, 
                                            'device-state-previous' : prev_device_state,
                                            'make-history' : make_history,
                                            'status-code-previous' : prev_status_code,
                                        } 
                                      )
                                      
        del fields[ 'result-code' ]
        
        return fields
        
    
    
    def queryModel( self, model_name ):
        model_name = model_name.replace( ' ', '_' )
        fields, data = msg.xmitMessage( self.hpssd_sock, 
                                        "ModelQuery",
                                        None, 
                                        { 
                                            'model' : model_name 
                                        } 
                                      )
            
        #del fields[ 'msg' ]
        del fields[ 'result-code' ]
        
        agents = []
        i = 1
        while True:
            try:
                fields[ 'agent%d-kind' % i ]
            except KeyError:
                break
            else:
                agents.append( { 'kind' : int(fields[ 'agent%d-kind' % i ]), 
                                 'type' : int(fields[ 'agent%d-type' % i ]),
                                 'sku'  : fields[ 'agent%d-sku' % i ], 
                                } )
                                 
                del fields[ 'agent%d-kind' % i ]
                del fields[ 'agent%d-type' % i ]
                del fields[ 'agent%d-sku' % i ]
            
            i += 1
            
            fields[ 'agents' ] = agents
    
        return fields
        
    def queryString( self, string_id ):
        fields, data = msg.xmitMessage( self.hpssd_sock, 
                                        "StringQuery",
                                        None, 
                                        { 
                                            'string-id' : string_id
                                        } 
                                      )
        return data.strip('\n')
                                    
        
        
    def registerGUI( self, username, host, port, pid, admin_flag=False ):
        msg.sendEvent( self.hpssd_sock, 
                        "RegisterGUIEvent", 
                        None, 
                        { 'username' : username,
                          'admin-flag' : admin_flag,
                          'hostname' : host,
                          'port' : port,
                          'pid' : pid }
                      )
                                          
    def unregisterGUI( self, username, pid ):
        msg.sendEvent( self.hpssd_sock, 
                        "UnRegisterGUIEvent", 
                        None, 
                        { 
                            'username' : username,
                            'pid' : pid,
                        } 
                      )
    
    def showToolbox( self, username ):
        msg.sendEvent( self.hpssd_sock, 
                        'Event', 
                        None, 
                        { 
                            'event-code' : EVENT_UI_SHOW_TOOLBOX,
                            'event-type' : 'event',
                            'username' : username,
                            'job-id' : 0,
                            'retry-timeout' : 0,
                        } 
                      )
                      
    def sendEvent( self, event_code, event_type, job_id, username, device_uri, no_fwd=False ):
        #print "SENDING EVENT %d" % event_code
        msg.sendEvent( self.hpssd_sock, 
                        'Event', 
                        None, 
                        { 
                            'device-uri' : device_uri,
                            'event-code' : event_code,
                            'event-type' : event_type,
                            'username' : username,
                            'job-id' : job_id,
                            'retry-timeout' : 0,
                            'no-fwd' : no_fwd,
                        } 
                      )

    def testEmail( self, email_address, smtp_server, username, password ):
        fields = {}
        result_code = ERROR_SUCCESS
        try:
            fields, data = msg.xmitMessage( self.hpssd_sock, 
                                            "TestEmail",
                                            None, 
                                            { 
                                                'email-address' : email_address,
                                                'smtp-server' : smtp_server,
                                                'username'      : username,
                                                'server-pass'   : password,
                                            } 
                                          )
        except Error:
            result_code = e.opt
            utils.log_exception()
                
        return result_code
        
    def getGUI( self, username ):
        fields = {}
        try:
            fields, data = msg.xmitMessage( self.hpssd_sock, 
                                            "GetGUI",
                                            None, 
                                            { 
                                                'username' : username,
                                            } 
                                          )
        except Error:
            #utils.log_exception()
            pass
        
        return ( fields.get( 'port', 0 ),  fields.get( 'hostname', '' ) )
        
                      
    def getHistory( self, device_uri ):
        fields, data = msg.xmitMessage( self.hpssd_sock, 
                                        "HistoryQuery",
                                        None, 
                                        { 
                                            'device-uri' : device_uri,
                                        } 
                                      )
                                      
        result = []
        lines = data.strip().splitlines()
        lines.reverse()
        for x in lines:
            yr, mt, dy, hr, mi, sec, wd, yd, dst, job, user, ec, ess, esl = x.strip().split(',', 13)
            result.append( ( int(yr), int(mt), int(dy), int(hr), int(mi), int(sec), int(wd), 
                             int(yd), int(dst), int(job), user, int(ec), ess, esl ) )
        
        return result
        
    def setAlerts( self, popup_alerts, email_alerts, email_address, smtp_server ):
        
        fields, data = msg.xmitMessage( self.hpssd_sock, 
                                        "SetAlerts",
                                        None, 
                                        { 
                                            'username'      : prop.username,
                                            'popup-alerts'  : popup_alerts,
                                            'email-alerts'  : email_alerts,
                                            'email-address' : email_address,
                                            'smtp-server'   : smtp_server,
                                        }
                                      )
                                      
    def cancelJob( self, jobid, uri ):
        cups.cancelJob( jobid )
        msg.sendEvent( self.hpssd_sock, 'Event', None, 
                  { 
                      'job-id' : jobid,
                      'event-type' : 'event',
                      'event-code' : STATUS_PRINTER_CANCELING,
                      'username' : prop.username,
                      'device-uri' : uri,
                      'retry-timeout' : 0,
                  } 
                 )
                 
    def doPing( self, host, timeout=1 ):
        fields, data = msg.xmitMessage( self.hpssd_sock, 
                                        "Ping",
                                        None, 
                                        { 
                                            'host' : host,
                                            'timeout' : timeout,
                                        } 
                                      )
        
        return float( data.strip().splitlines()[0] )
        


    
    
    def close( self ):
        if self.close_hpssd_sock:
            self.hpssd_sock.close()
