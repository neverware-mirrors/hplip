#!/usr/bin/env python
#
# $Revision: 1.8 $ 
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
from base import device, service, status, utils, maint
from prnt import cups   
    
def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( """\nUsage: colorcal.py [PRINTER|DEVICE-URI] [OPTIONS]\n\n""" )
    
    log.info( formatter.compose( ( "[PRINTER|DEVICE-URI] (**See NOTES)", "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ) ) )
    log.info( formatter.compose( ( "[OPTIONS]",                            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "Bus to probe (interactive mode only):","-b<bus> or --bus=<bus>" ) ) )
    log.info( formatter.compose( ( "",                                     "<bus>: cups*, usb, net, bt, fw, par (*default) (Note: net, bt, fw, and par not supported)" ) ) )
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ) ) )

    log.info(  """Examples:\n\Calibrate color on CUPS printer named "hp5550":\n   colorcal.py -php5550\n\n""" \
               """Color calibrate on printer with URI of "hp:/usb/DESKJET_990C?serial=12345":\n   colorcal.py -dhp:/usb/DESKJET_990C?serial=12345\n\n""" \
               """**NOTES: 1. If device or printer is not specified, the local device bus\n""" \
               """            is probed and the program enters interactive mode.\n""" \
               """         2. If -p* is specified, the default CUPS printer will be used.\n""" )
        

def enterNumber( letter, text, minimum, maximum ):
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
        
    return x

def enterAlignmentNumber( letter, hortvert, colors, minimum, maximum ):
    return enterNumber( "Enter the best aligned value for line %s (%d-%d): " % ( letter, minimum, maximum ),
                        minimum, 
                        maximum )
                        
def enterPaperEdge( maximum ):
    return enterNumber( "Enter numbered arrow that is best aligned with the paper edge (1-%d): " % maximum,
                        1, 
                        maximum )

def colorAdj( line, maximum ):
    return enterNumber( "Enter the numbered box o line %s that is best color matched to the background color (1-%d): " % ( line, maximum ),
                        1, 
                        maximum )

def loadPlainPaper():
    x = raw_input( utils.bold( "An alignment page will be printed.\nPlease load plain paper into the printer. Press <Enter> to contine or 'q' to quit." ) )
    if len(x) > 0 and x[0].lower() == 'q':
        return False
    return True 
    
def invalidPen():
    log.error( "Invalid cartridge(s) installed.\nPlease install valid cartridges and try again." )
  
def photoPenRequired():
    log.error( "Photo cartridge not installed.\nPlease install the photo cartridge and try again." )

    
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
    sys.exit(1)
    
printer_name = None
device_uri = None    
bus = 'cups'
log_level = 'info'

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
  
d = device.Device( None, device_uri, printer_name )

if d.device_uri is None and printer_name:
    log.error( "Printer '%s' not found." % printer_name )
    sys.exit(0)
    
if d.device_uri is None and device_uri:
    log.error( "Malformed/invalid device-uri: %s" % device_uri )
    sys.exit(0)
    

try:
    s = None
    try:
        device_id = d.open()
    except Error:
        log.error( "Unable to open device. Exiting. " )
        raise Error(0)
    
    try:
        s = service.Service()
    except Error:
        log.error( "Unable to contact services daemon. Exiting." )
        raise Error(0)
        
    try:
        fields = s.queryModel( d.model )
        color_cal_type = fields.get( 'color-cal-type', 0 )
    except Error:
        log.error( "Query for model failed. Exiting." )
        raise Error(0)
    
    log.debug( "Color calibration type=%d" % color_cal_type )
    
    if color_cal_type == 0: 
        log.error( "Color calibration not supported or required by device." )
        raise Error(0)
        
    elif color_cal_type == 1:
        maint.colorCalType1( cur_device, loadPlainPaper, colorCal, photoPenRequired, update_spinner )    

    else:
        log.error( "Invalid color calibration type.")
        
finally:    
    if d is not None:
        d.close()
    if s is not None:
        s.close()
        
    log.info( 'Done' )
    
