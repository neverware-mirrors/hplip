#!/usr/bin/env python
#
# $Revision: 1.21 $ 
# $Date: 2004/11/17 21:34:41 $
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


_VERSION = '2.7'

# Std Lib
import sys
import os
import getopt
import re

# Local
from base.g import *
from base import device, service, status, utils
from prnt import cups
    
    
def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( utils.TextFormatter.bold( """\nUsage: info.py [PRINTER|DEVICE-URI] [OPTIONS]\n\n""") )
    
    log.info( formatter.compose( ( utils.TextFormatter.bold("[PRINTER|DEVICE-URI]"), "" ) ) )
    log.info( formatter.compose( ( "(**See NOTES 1&2)",                     "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ), True ) )
    log.info( formatter.compose( ( utils.TextFormatter.bold("[OPTIONS]"),            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "Bus to probe (interactive mode only):","-b<bus> or --bus=<bus>" ) ) )
    log.info( formatter.compose( ( "",                                     "<bus>: cups*, usb, net, bt, fw, par (*default) (Note: net, bt, fw, and par not supported)" ) ) )
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ), True ) )

    log.info(  """Examples:\n\nInfo on a CUPS printer named "hp5550":\n   info.py -php5550\n\n""" \
               """Info on printer with a URI of "hp:/usb/DESKJET_990C?serial=12345":\n   info.py -dhp:/usb/DESKJET_990C?serial=12345\n\n"""\
               """**NOTES: 1. If device or printer is not specified, the local device bus\n""" \
               """            is probed and the program enters interactive mode.\n""" \
               """         2. If -p* is specified, the default CUPS printer will be used.\n""" )
        
utils.log_title( 'Device Information Utility', _VERSION )

try:
    opts, args = getopt.getopt( sys.argv[1:], 'p:d:hl:b:', [ 'printer=', 'device=', 'help', 'logging=' ] ) 
except getopt.GetoptError:
    usage()
    sys.exit(1)
    
printer_name = None
device_uri = None    
log_level = None
bus = 'cups'
log_level = 'info'

for o, a in opts:
    if o in ( '-h', '--help' ):
        usage()
        sys.exit(0)
    
    elif o in ( '-p', '--printer' ):
        if a.startswith('*'):
            printer_name = cups.getDefault() 
            log.debug( printer_name )
        else:
            printer_name = a
    
    elif o in ( '-d', '--device' ):
        device_uri = a
        
    elif o in ( '-b', '--bus' ):
        bus = a.lower().strip()
        
    elif o in ( '-l', '--logging' ):
        log_level = a.lower().strip()
        
        
if not bus in ( 'cups', 'usb', 'net', 'bt', 'fw' ):
    log.error( "Invalid bus name." )
    sys.exit(0)
        
if not log_level in ( 'info', 'warn', 'error', 'debug' ):
    log.error( "Invalid logging level." )
    sys.exit(0)

log.set_level( log_level )                
        
if device_uri and printer_name:
    log.error( "You may not specify both a printer (-p) and a device (-d)." )
    sys.exit(0)
    
if not device_uri and not printer_name:
    try:
        device_uri = utils.getInteractiveDeviceURI( bus )
        if device_uri is None:
            sys.exit(0)
    except Error:
        log.error( "Error occured during interactive mode. Exiting." )
        sys.exit(0)

try:
    d = device.Device( None, device_uri, printer_name )
except Error:
    log.error( "Error opening device. Exiting." )
    sys.exit(0)

if d.device_uri is None and printer_name:
    log.error( "Printer '%s' not found." % printer_name )
    sys.exit(0)
    
if d.device_uri is None and device_uri:
    log.error( "Malformed/invalid device-uri: %s" % device_uri )
    sys.exit(0)
    

log.info( utils.TextFormatter.bold( "\nInfo for: %s\n" % d.device_uri ) )
try:
    s = None
    try:
        device_id = d.open()
    except Error:
        log.error( "Error opening device. Exiting." )
        #d.close()
        sys.exit(0)
    
    
    formatter = utils.TextFormatter( 
                    (
                        {'width': 18, 'margin' : 2},
                        {'width': 58, 'margin' : 2},
                    )
                )
    
    log.info( utils.TextFormatter.bold( formatter.compose( ( "Info", "Value" ) ) ) )
    log.info( formatter.compose( ( '-'*18, '-'*58 ) ) )
    log.info( formatter.compose( ( "device URI:", d.device_uri ) ) )
    log.info( formatter.compose( ( "Model name:", d.model.replace( '_', ' ' ) ) ) )
    log.info( formatter.compose( ( "Serial no.:", d.serialNumber() ) ) )
    log.info( formatter.compose( ( "CUPS back end:", d.back_end ) ) )
    log.info( formatter.compose( ( "Device file:", d.devFile() ) ) )
    log.info( formatter.compose( ( "I/O bus:", d.bus ) ) )
    
    try:
        s = service.Service()
    except Error:
        log.error( "Unable to contact services daemon. Exiting." )
        sys.exit(0)
    
    
    try:
        data = s.queryDevice( d.device_uri, 0, False )
        #log.info( formatter.compose( ( "Model Query:",  repr(data) ) ) )
    except Error:
        log.error( "Query for model failed." )
    else:
        ds_keys = data.keys()
        ds_keys.sort()
        for key,i in zip( ds_keys, range(len(ds_keys))):
            if i == 0:
                log.info( formatter.compose( ( "Device Query:",  "%s: %s" % ( key, data[key] ) ) ) )
            else:
                log.info( formatter.compose( ( "",              "%s: %s" % ( key, data[key] ) ), ( i == len(ds_keys)-1 ) ) )
    
    
    
    
    if 0:
        
        tb_i, tb_s = d.threeBitStatus()
        log.info( formatter.compose( ( "Status (3bit):", "%d (%s)" % (tb_i, tb_s ) ), True ) )
        parsed_DeviceID, raw_DeviceID = d.ID()
        log.info( formatter.compose( ( "Device ID (raw):", repr(raw_DeviceID) ), True ) )
        di_keys = parsed_DeviceID.keys()
        di_keys.sort()
        for key,i in zip( di_keys, range(len(di_keys))):
            if i == 0:
                log.info( formatter.compose( ( "Device ID:", "%s: %s" % ( key, parsed_DeviceID[key] ) ) ) )
            else:
                log.info( formatter.compose( ( "", "%s: %s" % ( key, parsed_DeviceID[key] ) ), (i==len(di_keys)-1) ) )
        
        stat = status.parseStatus( parsed_DeviceID )
        st_keys = stat.keys()
        st_keys.sort()
        for key,i in zip( st_keys, range(len(st_keys))):
            #print key
            if i == 0:
                log.info( formatter.compose( ( "Status:", "" ) ) ) #, "%s: %s" % ( key, stat[key] ) ) ) )
            
            if key == 'agents':
                pens = stat['agents']
                for p,k in zip(pens,range(len(pens))):
                    kth_pen = pens[k]
                    pks = kth_pen.keys()
                    pks.sort()
                    for pk, j in zip( pks, range(len(pks))):
                        log.info( formatter.compose( ( "", "pen %d: %s: %s" % ( k+1, pk, kth_pen[pk] ) ) ) )
            else:
                log.info( formatter.compose( ( "", "%s: %s" % ( key, stat[key] ) ), (i==len(st_keys)-1) ) )
        
        
        try:
            s = service.Service()
        except Error:
            log.error( "Unable to contact services daemon. Exiting." )
            sys.exit(0)
            
        try:
            data = s.queryModel( d.model )
            #log.info( formatter.compose( ( "Model Query:",  repr(data) ) ) )
        except Error:
            log.error( "Query for model failed." )
        else:
            mq_keys = data.keys()
            mq_keys.sort()
            for key,i in zip( mq_keys, range(len(mq_keys))):
                if i == 0:
                    log.info( formatter.compose( ( "Model Query:",  "%s: %s" % ( key, data[key] ) ) ) )
                else:
                    log.info( formatter.compose( ( "",              "%s: %s" % ( key, data[key] ) ), ( i == len(mq_keys)-1 ) ) )
            
        cups_printers = cups.getPrinters()
        printers = []
        for p in cups_printers:
            if p.device_uri == d.device_uri:
                printers.append( p.name )
        
        if len( printers ) > 0:
            log.info( formatter.compose( ( "CUPS printers:",  ', '.join( printers ) ) ) )
        else:    
            log.info( formatter.compose( ( "CUPS printers:",  '' ) ) )
        
    print

finally:
    log.debug( "Closing services..." )
    if s is not None: 
        s.close()
    if d is not None:
        d.close()

