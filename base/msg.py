#!/usr/bin/env python
#
# $Revision: 1.14 $ 
# $Date: 2004/12/02 19:46:03 $
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
import sys
import cStringIO
import select
import time

# Local
from g import *
import utils
from codes import *


##ErrorReturn = ( {}, '', -1 )
valid_encodings = ( '', 'none', 'base64' )
valid_char_encodings = ( '', 'utf-8', 'latin-1' )


def buildResultMessage( msg_type, payload=None, result_code=ERROR_SUCCESS, other_fields={} ):
    #if not other_fields:
    #    other_fields = {}
    other_fields.update( { 'result-code' : result_code } )
    return buildMessage( msg_type, payload, other_fields )

def buildMessage( msg_type, payload=None, other_fields={} ): 

    if msg_type is None or not msg_type:
        raise Error( ERROR_INVALID_MSG_TYPE )

    msg = cStringIO.StringIO()
    msg.write( "msg=%s\n" % msg_type.lower() )
    
    if other_fields:
        for k in other_fields:
            msg.write( '%s=%s\n' % ( k, str( other_fields[k] ) ) )

    if payload is not None:
        msg.write( "encoding=none\n" ) 
        msg.write( "length=%d\n" % len( payload ) )
        msg.write( "data:\n%s" % payload )
                
    return msg.getvalue()

    
conv_funcs = { 
               # GMP v1.0
               'default'         : lambda x : str(x),
               'msg'             : lambda x : str(x).lower(),
               'length'          : lambda x : int(x),
               'result-code'     : lambda x : int(x),
               'device-uri'      : lambda x : str(x),
               'device-id'       : lambda x : int(x),
               'job-id'          : lambda x : int(x),
               'channel-id'      : lambda x : int(x),
               'char-encoding'   : lambda x : str(x).lower(),
               'encoding'        : lambda x : str(x).lower(),
               'digest'          : lambda x : int(x),
               # GMP v2.0
               'bytes-written'   : lambda x : int(x),
               'device-file'     : lambda x : str(x),
               'status-code'     : lambda x : int(x),
               'status-name'     : lambda x : str(x).lower(),
               'retry-timeout'   : lambda x : int(x),
               'recovery-result' : lambda x : str(x),
               'ui-id'           : lambda x : str(x).lower(),
               'error-code'      : lambda x : int(x),
               'service-name'    : lambda x : str(x).upper(),
               'username'        : lambda x : str(x),
               'model'           : lambda x : str(x),
               'port'            : lambda x : int(x),
               'admin-flag'      : lambda x : utils.to_bool(x),
               # Model Query v2.0
               'align-type'      : lambda x : int(x),
               'scan-adf'        : lambda x : utils.to_bool(x),
               'scan-mfpdtf'     : lambda x : utils.to_bool(x),
               # GMP v3.0
               'event-code'      : lambda x : int(x),
               'hostname'        : lambda x : str(x),
               'event-type'      : lambda x : str(x).lower(),
               # Alerts GMP v3.7
               'email-alerts'    : lambda x : utils.to_bool(x),
               'email-address'   : lambda x : str(x),
               'smtp-server'     : lambda x : str(x),
               'popup-alerts'    : lambda x : utils.to_bool(x),
               #
               'color-cal-type'  : lambda x : int(x),
               # ProbeDevicesFiltered v4.1
               'ttl'             : lambda x : int(x),
               'timeout'         : lambda x : int(x),
               'bus'             : lambda x : str(x).lower(),
               'filter'          : lambda x : str(x).lower(),
               'num-devices'     : lambda x : int(x),
               'format'          : lambda x : str(x).lower(),
               'no-fwd'          : lambda x : utils.to_bool(x),
                # Toolbox improvements
               'device-state'    : lambda x : int(x),
               'device-state-previous' : lambda x : int(x),
               'make-history'    : lambda x : utils.to_bool(x),
               'pid'             : lambda x : int(x),
              }
             
               
def parseMessage( message ):
    fields, data_found, data = {}, False, ''
    
    try:
        msg = cStringIO.StringIO( message )
    except TypeError:
        raise Error( ERROR_INVALID_MSG_TYPE )
    
    while True:
        line = msg.readline().strip()
        
        if line == "": 
            break
        
        if line.startswith( 'data:' ): 
            data_found = True
            break
        
        if line.startswith( '#' ): 
            continue
            
        try:
            key, value = line.split( '=', 1 )
            key = key.strip().lower()
        except ValueError:
            raise Error( ERROR_INVALID_MSG_TYPE )
        
        try:
            fields[ key ] = conv_funcs.get( key, conv_funcs[ 'default' ] )( value )
        
        except ValueError:

            if key == 'device-id': 
                raise Error( ERROR_INVALID_DEVICE_ID )
            
            elif key == 'length':
                raise Error( ERROR_DATA_LENGTH_MISMATCH )
            
            elif key == 'job-id':
                raise Error( ERROR_INVALID_JOB_ID )
            
            elif key == 'digest':
                raise Error( ERROR_DATA_DIGEST_MISMATCH )
                
            else:
                raise Error( ERROR_INVALID_MSG_TYPE )
                
        
    if 'msg' not in fields:
        raise Error( ERROR_INVALID_MSG_TYPE )

    if data_found:
        
        data = msg.read() or ''
  
        length_field = fields[ 'length' ]
        data_len = len( data )
        
        if data_len != length_field:
            log.error( "Data len=%d" % data_len )
            log.error( "length=%d" % length_field )
            log.error( repr(message) )
            raise Error( ERROR_DATA_LENGTH_MISMATCH )
            
        if data_len > prop.max_message_len:
            #raise Error( ERROR_DATA_LENGTH_EXCEEDS_MAX )
            log.warn( "Data length exceeds maximum of %d" % prop.max_message_len ) 
    
    return fields, data


def sendEvent( sock, msg_type, payload=None, other_fields={} ):
    m = buildMessage( msg_type, payload, other_fields )
    log.debug( repr(m) )
    sock.send( m )

    
def xmitMessage( sock, msg_type, payload=None, other_fields={}, timeout=30 ): 
    
    m = buildMessage( msg_type, payload, other_fields )
    log.debug( repr(m) )
    sock.send( m )
    
    r, w, e = select.select( [sock], [], [], timeout )

    if r == []: 
        raise Error( ERROR_INTERNAL )

    m = sock.recv( prop.max_message_len<<2 )
    #m = sock.recv()
    log.debug( repr(m) )
    fields, data = parseMessage( m )
    result_code = fields[ 'result-code' ]
    
    if result_code > ERROR_SUCCESS:
        raise Error( result_code )
        
    del fields['msg']
        
    return fields, data
    
