#!/usr/bin/env python
#
# $Revision: 1.12 $
# $Date: 2005/10/13 18:08:12 $
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

_VERSION = '3.0'

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
    formatter = utils.usage_formatter()
    log.info( utils.bold("""\nUsage: hp-testpage [PRINTER|DEVICE-URI] [OPTIONS]\n\n""" ))
    log.info( utils.bold( "[PRINTER|DEVICE-URI] (**See NOTES)" ) )
    utils.usage_device(formatter)
    utils.usage_printer(formatter, True)
    utils.usage_options()
    utils.usage_bus(formatter)
    utils.usage_logging(formatter)
    utils.usage_help(formatter, True)
    utils.usage_notes()
    utils.usage_examples()
    log.info(  """\nPrint a testpage to a CUPS printer named "hp5550":\n\thp-testpage -php5550 FILENAME\n\n""" \
               """Print a testpage to a printer with a URI of "hp:/usb/DESKJET_990C?serial=12345":\n\t""" \
               """hp-testpage -dhp:/usb/DESKJET_990C?serial=12345 FILENAME\n\n""" )

    sys.exit(0)


utils.log_title( 'Testpage Print Utility', _VERSION )

try:
    opts, args = getopt.getopt( sys.argv[1:], 'p:d:hl:',
                               [ 'printer=', 'device=', 'help', 'logging=' ] )
except getopt.GetoptError:
    usage()

printer_name = None
device_uri = None
bus = device.DEFAULT_PROBE_BUS
log_level = logger.DEFAULT_LOG_LEVEL

for o, a in opts:
    if o in ( '-h', '--help' ):
        usage()

    elif o in ( '-p', '--printer' ):
        printer_name = a

    elif o in ( '-d', '--device' ):
        device_uri = a

    elif o in ( '-b', '--bus' ):
        bus = a.lower().strip()

    elif o in ( '-l', '--logging' ):
        log_level = a.lower().strip()


if not device.validateBusList(bus):
    usage()

if not log.set_level( log_level ):
    usage()

if device_uri and printer_name:
    log.error( "You may not specify both a printer (-p) and a device (-d)." )
    usage()

if device_uri and printer_name:
    log.error( "You may not specify both a printer (-p) and a device (-d)." )
    usage()

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
except Error, e:
    log.error("Unable to open device: %s" % e.msg)
    sys.exit(0)

if d.device_uri is None and printer_name:
    log.error( "Printer '%s' not found." % printer_name )
    sys.exit(0)

if d.device_uri is None and device_uri:
    log.error( "Malformed/invalid device-uri: %s" % device_uri )
    sys.exit(0)

d.queryDevice()

if d.error_state ==  ERROR_STATE_CLEAR:
    try:
        device_id = d.open()
    except Error:
        log.error( "Unable to print to printer. Please check device and try again." )
        sys.exit(0)

    log.info( "Printing test page..." )
    d.printTestPage()
    d.close()

    log.info( "Page has been sent to printer..." )
    sys.exit(0)

else:
    log.error( "Printer is in an error state (%s). Please check printer and try again." % d.status_desc )
    sys.exit(0)






