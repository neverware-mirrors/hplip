#!/usr/bin/env python
#
# $Revision: 1.3 $ 
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



_VERSION = '2.0'


# Std Lib
import sys
import os
import getopt
import re
#import gzip

# Local
from base.g import *
from base import device, service, utils
from prnt import cups

   
def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( utils.TextFormatter.bold( """\nUsage: print.py [PRINTER|DEVICE-URI] [OPTIONS]\n\n""") )
    
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

    log.info(  """Examples:\n\nPrint to a CUPS printer named "hp5550":\n   print.py -php5550 FILENAME\n\n""" \
               """Print to a printer with a URI of "hp:/usb/DESKJET_990C?serial=12345":\n   print.py -dhp:/usb/DESKJET_990C?serial=12345 FILENAME\n\n"""\
               """**NOTES: 1. If device or printer is not specified, the local device bus\n""" \
               """            is probed and the program enters interactive mode.\n""" \
               """         2. If -p* is specified, the default CUPS printer will be used.\n""" )    
    

utils.log_title( 'Testpage Print Utility', _VERSION )

try:
    opts, args = getopt.getopt( sys.argv[1:], 'p:d:hb:l:', 
                               [ 'printer=', 'device=', 'help', 'bus=', 'logging=' ] ) 
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
        
    elif o in ( '-b', '--bus' ):
        bus = a.lower().strip()
        
    elif o in ( '-l', '--logging' ):
        log_level = a.lower().strip()

    
if not log_level in ( 'info', 'warn', 'error', 'debug' ):
    log.error( "Invalid logging level." )
    sys.exit(0)
    
log.set_level( log_level )   
   
if not bus in ( 'cups', 'usb', 'net', 'bt', 'fw' ):
    log.error( "Invalid bus name." )
    sys.exit(0)

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
        device_uri = utils.getInteractiveDeviceURI( bus )
        if device_uri is None:
            sys.exit(0)
    except Error:
        log.error( "Error occured during interative mode. Exiting." )
        sys.exit(0)

d = device.Device( None, device_uri, printer_name )

if d.device_uri is None and printer_name:
    log.error( "Printer '%s' not found." % printer_name )
    sys.exit(0)
    
if d.device_uri is None and device_uri:
    log.error( "Malformed/invalid device-uri: %s" % device_uri )
    sys.exit(0)

print_file = os.path.join( prop.home_dir, 'data', 'ps', 'testpage.ps.gz' )

device_id = d.open()    
log.info( "Printing test page..." )
d.printParsedGzipPostscript( print_file )
d.close()

log.info( "Done." )

sys.exit(0)



device_id = d.open()
channel_id = d.openChannel( 'PRINT' )
if channel_id == -1:
    log.error( "Could not open print channel" )
    sys.exit(0)

log.info( "Printing test page..." )

f = gzip.open( print_file, 'r' )

x = f.readline()
while not x.startswith( '%PY_BEGIN' ):
    os.write( temp_file_fd, x )
    x = f.readline()
    
sub_lines = []
x = f.readline()
while not x.startswith( '%PY_END' ):
    sub_lines.append( x )
    x = f.readline()
    

SUBS = { 'VERSION' : prop.version,
         'MODEL'   : d.model_ui,
         'URI'     : d.device_uri,
         'BUS'     : d.bus,
         'SERIAL'  : d.serialNumber(),
         'IP'      : d.host,
         'PORT'    : d.port,
         'DEVNODE' : d.dev_file,
         }
if d.bus == 'net':
    SUBS[ 'DEVNODE' ] = 'n/a'
else:
    SUBS[ 'IP' ] = 'n/a'
    SUBS[ 'PORT' ] = 'n/a'
    
         

for s in sub_lines:
    #print s
    os.write( temp_file_fd, s % SUBS )
    
os.write( temp_file_fd, f.read() )



f.close()
os.close( temp_file_fd )

os.system( 'lp -d%s -s %s' % ( d.cups_printers[0], temp_file_name ) )

os.remove( temp_file_name )
d.close()

log.info( "Done." )


    
