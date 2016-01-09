#!/usr/bin/env python
#

# $Revision: 1.32 $
# $Date: 2005/08/10 16:39:39 $
# $Author: dwelch $

#
# (c) Copyright 2003-2005 Hewlett-Packard Development Company, L.P.
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

# Local
from g import *
from codes import *
import msg

sock = None

def __openServices():
    global sock
    sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    try:
        sock.connect( ( prop.hpssd_host, prop.hpssd_port ) )
    except socket.error:
        raise Error(ERROR_UNABLE_TO_CONTACT_SERVICE)


def __closeServices():
    global sock
    sock.close()


def registerGUI( username, host, port, pid, typ ):
    __openServices()
    msg.sendEvent( sock,
                    "RegisterGUIEvent",
                    None,
                    { 'username' : username,
                      'hostname' : host,
                      'port' : port,
                      'pid' : pid,
                      'type' : typ }
                  )

    __closeServices()

def unregisterGUI( username, pid, typ ):
    __openServices()
    msg.sendEvent( sock,
                    "UnRegisterGUIEvent",
                    None,
                    {
                        'username' : username,
                        'pid' : pid,
                        'type' : typ,
                    }
                  )

    __closeServices()


def showToolbox( username ):
    __openServices()
    msg.sendEvent( sock,
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

    __closeServices()

def testEmail( email_address, smtp_server, username, password ):
    __openServices()
    fields = {}
    result_code = ERROR_SUCCESS
    try:
        fields, data, result_code = \
            msg.xmitMessage( sock,
                            "TestEmail",
                            None,
                            {
                                'email-address' : email_address,
                                'smtp-server' : smtp_server,
                                'username'      : username,
                                'server-pass'   : password,
                            }
                            )
    except Error, e:
        result_code = e.opt
        utils.log_exception()

    __closeServices()


    return result_code

def getGUI( username ):
    __openServices()
    fields = {}
    try:
        fields, data, result_code = \
            msg.xmitMessage( sock,
                            "GetGUI",
                            None,
                            {
                                'username' : username,
                            }
                            )
    except Error:
        pass

    __closeServices()

    return ( fields.get( 'port', 0 ),  fields.get( 'hostname', '' ) )

def sendEvent(event, typ, jobid, username, device_uri, other_fields={}):
    __openServices()
    fields = {'job-id'        : jobid,
              'event-type'    : typ,
              'event-code'    : event,
              'username'      : username,
              'device-uri'    : device_uri,
              'retry-timeout' : 0,}

    if other_fields:
        fields.update(other_fields)
    #print fields

    #def sendEvent(sock, msg_type, payload=None, other_fields={}):
    msg.sendEvent(sock, 'Event', None, fields)

    __closeServices()


def setAlerts( email_alerts, email_address, smtp_server ):
    __openServices()
    fields, data, result_code = \
        msg.xmitMessage( sock,
                        "SetAlerts",
                        None,
                        {
                            'username'      : prop.username,
                            'email-alerts'  : email_alerts,
                            'email-address' : email_address,
                            'smtp-server'   : smtp_server,
                        }
                        )


    __closeServices()
