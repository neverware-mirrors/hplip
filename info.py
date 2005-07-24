#!/usr/bin/env python
#
# $Revision: 1.30 $ 
# $Date: 2005/06/28 23:13:41 $
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


_VERSION = '3.0'

# Std Lib
import sys
import os
import getopt
import re
import time

# Local
from base.g import *
from base import device, status, utils
from prnt import cups


def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( utils.TextFormatter.bold( """\nUsage: hp-info [PRINTER|DEVICE-URI] [OPTIONS]\n\n""") )

    log.info( formatter.compose( ( utils.TextFormatter.bold("[PRINTER|DEVICE-URI]"), "" ) ) )
    log.info( formatter.compose( ( "(**See NOTES 1&2)",                     "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ), True ) )
    log.info( formatter.compose( ( utils.TextFormatter.bold("[OPTIONS]"),            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "Bus to probe (interactive mode only):","-b<bus> or --bus=<bus>" ) ) )
    log.info( formatter.compose( ( "",                                     "<bus>: cups*, usb, net, bt, fw, par (*default) (Note: net, bt, fw, and par not supported)" ) ) )
    log.info( formatter.compose( ( "Device ID mode:",                      "-i or --id" ) ) )
    
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ), True ) )

    log.info(  """Examples:\n\nInfo on a CUPS printer named "hp5550":\n   hp-info -php5550\n\n""" \
               """Info on printer with a URI of "hp:/usb/DESKJET_990C?serial=12345":\n   hp-info -dhp:/usb/DESKJET_990C?serial=12345\n\n"""\
               """**NOTES: 1. If device or printer is not specified, the local device bus\n""" \
               """            is probed and the program enters interactive mode.\n""" \
               """         2. If -p* is specified, the default CUPS printer will be used.\n""" )



try:
    opts, args = getopt.getopt( sys.argv[1:], 'p:d:hl:b:i', 
        [ 'printer=', 'device=', 'help', 'logging=', 'id' ] ) 
except getopt.GetoptError:
    usage()
    sys.exit(1)

printer_name = None
device_uri = None    
log_level = None
bus = 'usb,cups'
log_level = 'info'
devid_mode = False

for o, a in opts:
    if o in ( '-h', '--help' ):
        usage()
        sys.exit(0)

    elif o in ( '-p', '--printer' ):
        if a.startswith('*'):
            printer_name = cups.getDefault() 
            log.info( "Using CUPS default printer: %s" % printer_name )
            log.debug( printer_name )
        else:
            printer_name = a

    elif o in ( '-d', '--device' ):
        device_uri = a

    elif o in ( '-b', '--bus' ):
        bus = a.lower().strip()

    elif o in ( '-l', '--logging' ):
        log_level = a.lower().strip()

    elif o in ( '-i', '--id' ):
        devid_mode = True


if not devid_mode:
    utils.log_title( 'Device Information Utility', _VERSION )

for x in bus.split(','):
    bb = x.lower().strip()
    #if not bb in ( 'usb', 'net', 'bt', 'fw' ):
    if bb not in ( 'usb', 'cups', 'net' ):
        log.error( "Invalid bus name: %s" % bb )
        usage()
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
        device_uri = device.getInteractiveDeviceURI( bus )
        if device_uri is None:
            sys.exit(0)
    except Error:
        log.error( "Error occured during interactive mode. Exiting." )
        sys.exit(0)

try:
    d = device.Device( device_uri, printer_name )
except Error:
    log.error( "Error opening device. Exiting." )
    sys.exit(0)

if d.device_uri is None and printer_name:
    log.error( "Printer '%s' not found." % printer_name )
    sys.exit(0)

if d.device_uri is None and device_uri:
    log.error( "Malformed/invalid device-uri: %s" % device_uri )
    sys.exit(0)


if not devid_mode:
    log.info( utils.TextFormatter.bold( "\nInfo for: %s\n" % d.device_uri ) )



try:
    d.open()
    d.queryDevice()
except Error:
    log.error( "Error opening device. Exiting." )
    sys.exit(0)

if not devid_mode:
    formatter = utils.TextFormatter( 
                    (
                        {'width': 28, 'margin' : 2},
                        {'width': 58, 'margin' : 2},
                    )
                )



if devid_mode:
    try:
        print d.dq['deviceid']
    except KeyError:
        log.error( "Device ID not available." )
else:
    dq_keys = d.dq.keys()
    dq_keys.sort()
    
    log.info( utils.bold( "Device Parameters:") )
    log.info( utils.TextFormatter.bold( formatter.compose( ( "Parameter", "Value(s)" ) ) ) )
    log.info( formatter.compose( ( '-'*28, '-'*58 ) ) )

    for key in dq_keys:
        log.info( formatter.compose( ( key, str(d.dq[key]) ) ) )
    
    log.info( utils.bold("\nModel Parameters:") )
    log.info( utils.TextFormatter.bold( formatter.compose( ( "Parameter", "Value(s)" ) ) ) )
    log.info( formatter.compose( ( '-'*28, '-'*58 ) ) )
    
    mq_keys = d.mq.keys()
    mq_keys.sort()

    for key in mq_keys:
        log.info( formatter.compose( ( key, str(d.mq[key]) ) ) )
        
    log.info( utils.bold("\nStatus History:" ) )
    log.info( utils.TextFormatter.bold( formatter.compose( ( "Date/Time", "Status Description (code)" ) ) ) )
    log.info( formatter.compose( ( '-'*28, '-'*58 ) ) )
    
    hq = d.queryHistory()
    for h in hq:
        log.info( formatter.compose( ( time.strftime( "%x %H:%M:%S", h[:9] ),  "%s (%d)" % (h[12], h[11]) ) ) )
    
    log.info("")
        
d.close()

