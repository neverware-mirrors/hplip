#!/usr/bin/env python
#
# $Revision: 1.9 $ 
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

#Std Lib
import sys
import re
import getopt

# Local
from base.g import *
from base import device, service, utils, maint
from prnt import cups
   
def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( """\nUsage: clean.py [PRINTER|DEVICE-URI] [OPTIONS]\n\n""" )
    
    log.info( formatter.compose( ( "[PRINTER|DEVICE-URI] (**See NOTES)", "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ) ) )
    log.info( formatter.compose( ( "[OPTIONS]",                            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "Bus to probe (interactive mode only):","-b<bus> or --bus=<bus>" ) ) )
    log.info( formatter.compose( ( "",                                     "<bus>: cups*, usb, net, bt, fw, par (*default) (Note: net, bt, fw, and par not supported)" ) ) )
    log.info( formatter.compose( ( "Cleaning level:",                      "-v<level> or --level=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: 1*, 2, or 3 (*default)" ) ) )
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ) ) )

    log.info(  """Examples:\n\Clean CUPS printer named "hp5550":\n   clean.py -php5550\n\n""" \
               """Clean printer with URI of "hp:/usb/DESKJET_990C?serial=12345":\n   clean.py -dhp:/usb/DESKJET_990C?serial=12345\n\n""" \
               """**NOTES: 1. If device or printer is not specified, the local device bus\n""" \
               """            is probed and the program enters interactive mode.\n""" \
               """         2. If -p* is specified, the default CUPS printer will be used.\n""" )
        
        
utils.log_title( 'Printer Cartridge Cleaning Utility', _VERSION )

try:
    opts, args = getopt.getopt( sys.argv[1:], 'p:d:hl:b:v:', 
                                [ 'printer=', 'device=', 'help', 'logging=', 'bus=', 'level=' ] ) 
except getopt.GetoptError:
    usage()
    sys.exit(1)
    
bus = 'cups'
printer_name = None
device_uri = None    
log_level = 'info'
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
    
#log.info( "Cleaning device..." )

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
        clean_type = int( fields.get( 'clean-type', 0 ) )
    except Error:
        log.error( "Query for model failed. Exiting." )
        raise Error(0)
        
    log.info( "Performing type %d, level %d cleaning..." % ( clean_type, level ) )

    if clean_type == 1:
        if level == 3:
            maint.wipeAndSpitType1()
        elif level == 2:
            maint.primeType1( d )
        else:
            maint.cleanType1( d )
    
    elif clean_type == 2:
        if level == 3:
            maint.wipeAndSpitType2( d )
        elif level == 2:
            maint.primeType2( d )
        else:
            maint.cleanType2( d )
    
    else:
        log.error( "Cleaning not needed or supported on this device." )
        
        
finally:    
    log.info( "" )
    if d is not None:
        d.close()
    if s is not None:
        s.close()

    log.info( "Done." )
    
