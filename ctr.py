#!/usr/bin/env python
#
# $Revision: 1.7 $ 
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

_VERSION = '1.2'

# Std Lib
import sys
import re
import getopt

# Local
from base.g import *
from base.codes import *
from base import device, service, status, utils
from prnt import cups   

def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( """\nUsage: ctr.py [PRINTER|DEVICE-URI] COUNTER [OPTIONS]\n\n""" )
    
    log.info( formatter.compose( ( "[PRINTER|DEVICE-URI] (**See NOTES)",   "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ) ) )
    log.info( formatter.compose( ( "COUNTER",                              "" ) ) )
    log.info( formatter.compose( ( "Counter:",                             "-c<counter> or --counter=<counter>" ) ) )
    
    log.info( formatter.compose( ( "[OPTIONS]",                            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "Bus to probe (interactive mode only):","-b<bus> or --bus=<bus>" ) ) )
    log.info( formatter.compose( ( "",                                     "<bus>: cups*, usb, net, bt, fw, par (*default) (Note: net, bt, fw, and par not supported)" ) ) )
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ) ) )

        

def enterNumber( text, minimum, maximum ):
    while True:
        x = raw_input( utils.bold( text ) )
        
        if len(x) > 0 and x[0] in [ 'q', 'Q' ]:
            return False, 0
        
        try:
            x = int(x)
        except ValueError:
            log.error( "You must enter a numeric value.")
            continue
        if x < minimum or x > maximum:
            log.error( "You must enter a number between %d and %d." % ( minimum, maximum ) )
            continue
        break
        
    return True, x

utils.log_title( 'Dynamic Counter Utility', _VERSION )
    
try:
    opts, args = getopt.getopt( sys.argv[1:], 
                                'p:d:hl:b:c:', 
                                [ 'printer=', 
                                  'device=', 
                                  'help', 
                                  'logging=',
                                  'bus=',
                                  'counter='
                                ] 
                              ) 
except getopt.GetoptError:
    usage()
    sys.exit(1)
    
printer_name = None
device_uri = None    
bus = 'cups'
log_level = 'info'
counter = -1

for o, a in opts:
    
    if o in ( '-h', '--help' ):
        usage()
        sys.exit(0)
    
    elif o in ( '-p', '--printer' ):
        if a.startswith('*'):
            printer_name = cups.getDefault()    
        else:
            printer_name = a
    
    elif o in ( '-d', '--device' ):
        device_uri = a

    elif o in ( '-b', '--bus' ):
        bus = a.lower().strip()
        
    elif o in ( '-l', '--logging' ):
        log_level = a.lower().strip()
        
    elif o in ( '-c', '--counter' ):
        counter = int( a )
        
        

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
  
if counter < 0 or counter > 999:
    log.warning( "You must enter a valid counter number." )
    ok, counter = enterNumber( "Enter the counter number (or 'q' to exit):", 0, 999 )

    if not ok:
        sys.exit(0)

d = device.Device( None, device_uri, printer_name )

if d.device_uri is None and printer_name:
    log.error( "Printer '%s' not found." % printer_name )
    sys.exit(0)
    
if d.device_uri is None and device_uri:
    log.error( "Malformed/invalid device-uri: %s" % device_uri )
    sys.exit(0)
    
try:
    try:
        device_id = d.open()
    except Error:
        log.error( "Unable to open device. Exiting. " )
        raise Error(0)
        
    value = 0
    try:
        value = d.getDynamicCounter( counter )
    except Error, e:
        log.error( e[0] )

    if type(value) == type(1):
        log.info( utils.bold( "\nValue of counter %d is %d (0x%x)." % ( counter, value, value ) ) )
        if value == 0:
            log.warning( "A value of 0 (zero) may indicate that the counter is not implemented.")
    else:
        log.info( utils.bold( "\nValue of counter %d is '%s'." % ( counter, value ) ) )
        
finally:    
    log.info( "" )
    if d is not None:
        d.close()
        
    log.info( 'Done.' )
