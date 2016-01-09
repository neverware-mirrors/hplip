#!/usr/bin/env python
#
# $Revision: 1.19 $
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

_VERSION = '1.4'

# Std Lib
import sys
import re
import getopt


# Local
from base.g import *
from base import device, status, utils, maint
from prnt import cups

def usage():
    formatter = utils.usage_formatter()
    log.info( utils.bold("""\nUsage: hp-colorcal [PRINTER|DEVICE-URI] [OPTIONS]\n\n""" ))
    log.info( utils.bold( "[PRINTER|DEVICE-URI] (**See NOTES)" ) )
    utils.usage_device(formatter)
    utils.usage_printer(formatter, True)
    utils.usage_options()
    utils.usage_bus(formatter)
    utils.usage_logging(formatter)
    utils.usage_help(formatter, True)
    utils.usage_notes()
    utils.usage_examples()
    log.info(  """\nColor calibrate CUPS printer named "hp5550":\n\thp-colorcal -php5550\n\n""" \
               """Color calibrate printer with URI of "hp:/usb/DESKJET_990C?serial=12345":\n\t"""\
               """hp-colorcal -dhp:/usb/DESKJET_990C?serial=12345\n\n""" )
    sys.exit(0)

def enterNumber( text, minimum, maximum ):
    while True:
        x = raw_input( utils.bold( text ) )
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

def enterAlignmentNumber( letter, hortvert, colors, minimum, maximum ):
    return enterNumber( "Enter the best aligned value for line %s (%d-%d): " % ( letter, minimum, maximum ),
                        minimum,
                        maximum )

def enterPaperEdge( maximum ):
    return enterNumber( "Enter numbered arrow that is best aligned with the paper edge (1-%d): " % maximum,
                        1,
                        maximum )

def colorAdj( line, maximum ):
    return enterNumber( "Enter the numbered box on line %s that is best color matched to the background color (1-%d): " % ( line, maximum ),
                        1,
                        maximum )

def colorCal():
    return enterNumber( """Enter the numbered image labeled "1" thru "7" that is best color matched to the image labeled "X""", 1, 7 )

def colorCal2():
    return enterNumber( """Select the number between 1 and 81 of the numbered patch that best matches the background.""", 1, 81 )

def loadPlainPaper():
    x = raw_input( utils.bold( "An alignment page will be printed.\nPlease load plain paper into the printer. Press <Enter> to contine or 'q' to quit." ) )
    if len(x) > 0 and x[0].lower() == 'q':
        return False
    return True

def invalidPen():
    log.error( "Invalid cartridge(s) installed.\nPlease install valid cartridges and try again." )

def photoPenRequired():
    log.error( "Photo cartridge not installed.\nPlease install the photo cartridge and try again." )

def photoPenRequired2():
    log.error( "Photo cartridge or photo blue cartridge not installed.\nPlease install the photo (or photo blue) cartridge and try again." )



utils.log_title( 'Printer Cartridge Color Calibration Utility', _VERSION )

try:
    opts, args = getopt.getopt( sys.argv[1:],
                                'p:d:hl:b:',
                                [ 'printer=',
                                  'device=',
                                  'help',
                                  'logging=',
                                  'bus='
                                ]
                              )
except getopt.GetoptError:
    usage()

printer_name = None
device_uri = None
bus = device.DEFAULT_PROBE_BUS
log_level = logger.DEFAULT_LOG_LEVEL

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
except Error, e:
    log.error("Unable to open device: %s" % e.msg)
    sys.exit(0)

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

color_cal_type = d.mq.get( 'color-cal-type', 0 )
log.debug( "Color calibration type=%d" % color_cal_type )

if color_cal_type == 0:
    log.error( "Color calibration not supported or required by device." )
    sys.exit(0)

elif color_cal_type == COLOR_CAL_TYPE_DESKJET_450:
    maint.colorCalType1( d, loadPlainPaper, colorCal, photoPenRequired )

elif color_cal_type == COLOR_CAL_TYPE_MALIBU_CRICK:
    ok = maint.colorCalType2( d, loadPlainPaper, colorCal2, invalidPen )

elif color_cal_type == COLOR_CAL_TYPE_STRINGRAY_LONGBOW_TORNADO:
    ok = maint.colorCalType3( d, loadPlainPaper, colorAdj, photoPenRequired2 )

elif color_cal_type == COLOR_CAL_TYPE_CONNERY:
    #ok = maint.colorCalType4(d, loadPlainPaper, ???, update_spinner)
    log.error("Not implemented yet. Please use the HP Device Manager.")

else:
    log.error( "Invalid color calibration type.")

log.info("")
d.close()
log.info( 'Done' )

