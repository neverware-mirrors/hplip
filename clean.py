#!/usr/bin/env python
#
# $Revision: 1.15 $
# $Date: 2005/07/21 17:31:38 $
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


_VERSION = '1.5'

#Std Lib
import sys
import re
import getopt

# Local
from base.g import *
from base import device, utils, maint
from prnt import cups


def usage():
    formatter = utils.usage_formatter()
    log.info( utils.bold("""\nUsage: hp-clean [PRINTER|DEVICE-URI] [OPTIONS]\n\n""" ))
    log.info( utils.bold( "[PRINTER|DEVICE-URI] (**See NOTES)" ) )
    utils.usage_device(formatter)
    utils.usage_printer(formatter, True)
    utils.usage_options()
    utils.usage_bus(formatter)
    utils.usage_logging(formatter)
    log.info( formatter.compose( ( "Cleaning level:", "-v<level> or --level=<level>" ) ) )
    log.info( formatter.compose( ( "", "<level>: 1*, 2, or 3 (*default)" ) ) )
    utils.usage_help(formatter, True)
    utils.usage_notes()
    utils.usage_examples()
    log.info(  """\nClean CUPS printer named "hp5550":\n\thp-clean -php5550\n\n""" \
               """Clean printer with URI of "hp:/usb/DESKJET_990C?serial=12345":\n\t"""\
               """hp-clean -dhp:/usb/DESKJET_990C?serial=12345\n\n""" )

    sys.exit(0)


utils.log_title( 'Printer Cartridge Cleaning Utility', _VERSION )

try:
    opts, args = getopt.getopt( sys.argv[1:], 'p:d:hl:b:v:',
                                [ 'printer=', 'device=', 'help', 'logging=', 'bus=', 'level=' ] )
except getopt.GetoptError:
    usage()

bus = device.DEFAULT_PROBE_BUS
log_level = logger.DEFAULT_LOG_LEVEL
printer_name = None
device_uri = None
level = 1

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

    elif o in ( '-v', '--level' ):
        try:
            level = int(a)
        except ValueError:
            log.error( "Invalid cleaning level, setting level to 1." )
            level = 1

if level < 1 or level > 3:
    log.error( "Invalid cleaning level, setting level to 1." )
    level = 1

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

d = device.Device( device_uri, printer_name )

if d.device_uri is None and printer_name:
    log.error( "Printer '%s' not found." % printer_name )
    sys.exit(0)

if d.device_uri is None and device_uri:
    log.error( "Malformed/invalid device-uri: %s" % device_uri )
    sys.exit(0)

try:
    device_id = d.open()
except Error:
    log.error( "Unable to open device. Exiting. " )
    sys.exit(0)

clean_type = d.mq.get( 'clean-type', 0 )
log.info( "Performing type %d, level %d cleaning..." % ( clean_type, level ) )

if clean_type in (CLEAN_TYPE_PCL,CLEAN_TYPE_PCL_WITH_PRINTOUT):
    if level == 3:
        maint.wipeAndSpitType1()
    elif level == 2:
        maint.primeType1( d )
    else:
        maint.cleanType1( d )

elif clean_type == CLEAN_TYPE_LIDIL:
    if level == 3:
        maint.wipeAndSpitType2( d )
    elif level == 2:
        maint.primeType2( d )
    else:
        maint.cleanType2( d )

else:
    log.error( "Cleaning not needed or supported on this device." )

log.info( "" )
d.close()
log.info( "Done." )

