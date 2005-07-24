#!/usr/bin/env python
#
# $Revision: 1.10 $ 
# $Date: 2005/07/11 21:19:10 $
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



_VERSION = '2.2'


# Std Lib
import sys
import os
import getopt
import re
#import gzip

# Local
from base.g import *
from base import device, utils
from prnt import cups


def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( utils.TextFormatter.bold( """\nUsage: hp-testpage [PRINTER|DEVICE-URI] [OPTIONS]\n\n""") )

    log.info( formatter.compose( ( utils.TextFormatter.bold("[PRINTER|DEVICE-URI]"), "" ) ) )
    log.info( formatter.compose( ( "(**See NOTES 1&2)",                     "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ), True ) )
    log.info( formatter.compose( ( utils.TextFormatter.bold("[OPTIONS]"),            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    #log.info( formatter.compose( ( "Bus to probe (interactive mode only):","-b<bus> or --bus=<bus>" ) ) )
    #log.info( formatter.compose( ( "",                                     "<bus>: cups*, usb, net, bt, fw, par (*default) (Note: net, bt, fw, and par not supported)" ) ) )
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ), True ) )

    log.info(  """Examples:\n\nPrint a testpage to a CUPS printer named "hp5550":\n   hp-testpage -php5550 FILENAME\n\n""" \
               """Print a testpage to a printer with a URI of "hp:/usb/DESKJET_990C?serial=12345":\n   hp-testpage -dhp:/usb/DESKJET_990C?serial=12345 FILENAME\n\n"""\
               """**NOTES: 1. If device or printer is not specified, the local device bus\n""" \
               """            is probed and the program enters interactive mode.\n""" \
               """         2. If -p* is specified, the default CUPS printer will be used.\n""" )    


utils.log_title( 'Testpage Print Utility', _VERSION )

try:
    opts, args = getopt.getopt( sys.argv[1:], 'p:d:hl:', 
                               [ 'printer=', 'device=', 'help', 'logging=' ] ) 
except getopt.GetoptError:
    usage()
    sys.exit(0)

printer_name = None
device_uri = None    
bus = 'cups'
log_level = 'info'

for o, a in opts:
    if o in ( '-h', '--help' ):
        usage()
        sys.exit(0)

    elif o in ( '-p', '--printer' ):
        printer_name = a

    elif o in ( '-d', '--device' ):
        device_uri = a

    #elif o in ( '-b', '--bus' ):
    #    bus = a.lower().strip()

    elif o in ( '-l', '--logging' ):
        log_level = a.lower().strip()


if not log_level in ( 'info', 'warn', 'error', 'debug' ):
    log.error( "Invalid logging level." )
    sys.exit(0)

log.set_level( log_level )   

if device_uri and printer_name:
    log.error( "You may not specify both a printer (-p) and a device (-d)." )
    sys.exit(0)

if printer_name:
    printer_list = cups.getPrinters()
    found = False
    for p in printer_list:
        if p.name == printer_name:
            found = True

    if not found:
        log.error( "Unknown printer name: %s" % printer_name )
        sys.exit(0)

if not device_uri and not printer_name:
    try:
        device_uri = device.getInteractiveDeviceURI( bus )
        if device_uri is None:
            sys.exit(0)
    except:
        log.error( "Error occured during interative mode. Exiting." )
        sys.exit(0)

d = device.Device( device_uri, printer_name )

if d.device_uri is None and printer_name:
    log.error( "Printer '%s' not found." % printer_name )
    sys.exit(0)

if d.device_uri is None and device_uri:
    log.error( "Malformed/invalid device-uri: %s" % device_uri )
    sys.exit(0)
    
d.queryDevice()

if d.error_state ==  ERROR_STATE_CLEAR:
    print_file = os.path.join( prop.home_dir, 'data', 'ps', 'testpage.ps.gz' )
    
    try:
        device_id = d.open()
    except Error:
        log.error( "Unable to print to printer. Please check device and try again." )
        sys.exit(0)
    
    log.info( "Printing test page..." )
    d.printParsedGzipPostscript( print_file )
    d.close()
    
    log.info( "Page has been sent to spooler..." )
    sys.exit(0)
    
else:
    log.error( "Printer is in an error state (%s). Please check printer and try again." % d.status_desc )
    sys.exit(-1)
    





