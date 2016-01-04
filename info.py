#!/usr/bin/env python
#
# $Revision: 1.32 $
# $Date: 2005/07/21 23:53:01 $
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


_VERSION = '3.2'

# Std Lib
import sys, getopt, time

# Local
from base.g import *
from base import device, status, utils
from prnt import cups


def usage():
    formatter = utils.usage_formatter()
    log.info(utils.bold("""\nUsage: hp-info [PRINTER|DEVICE-URI] [OPTIONS]\n\n""" ))
    log.info(utils.bold( "[PRINTER|DEVICE-URI] (**See NOTES)" ) )
    utils.usage_device(formatter)
    utils.usage_printer(formatter, True)
    utils.usage_options()
    log.info( formatter.compose( ( "Device ID mode:", "-i or --id (prints device ID only and exits)" ) ) )
    utils.usage_bus(formatter)
    utils.usage_logging(formatter)
    utils.usage_help(formatter, True)
    utils.usage_notes()
    utils.usage_examples()
    log.info(  """\n\nInfo on a CUPS printer named "hp5550":\n\thp-info -php5550\n\n""" \
               """Info on printer with a URI of "hp:/usb/DESKJET_990C?serial=12345":\n\t""" \
               """hp-info -dhp:/usb/DESKJET_990C?serial=12345\n\n""" )
    sys.exit(0)

try:
    opts, args = getopt.getopt( sys.argv[1:], 'p:d:hl:b:i',
        [ 'printer=', 'device=', 'help', 'logging=', 'id' ] )
except getopt.GetoptError:
    usage()

printer_name = None
device_uri = None
log_level = logger.DEFAULT_LOG_LEVEL
bus = device.DEFAULT_PROBE_BUS
devid_mode = False

for o, a in opts:
    if o in ( '-h', '--help' ):
        usage()

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

if not device.validateBusList(bus):
    usage()

if not log.set_level( log_level ):
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
    log.info("")

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

