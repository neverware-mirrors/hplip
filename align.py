#!/usr/bin/env python
#
# $Revision: 1.18 $ 
# $Date: 2005/01/07 21:39:51 $
# $Author: pparks $
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

_VERSION = '2.1'

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

    log.info( """\nUsage: align.py [PRINTER|DEVICE-URI] [OPTIONS]\n\n""" )
    
    log.info( formatter.compose( ( "[PRINTER|DEVICE-URI] (**See NOTES)", "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ) ) )
    log.info( formatter.compose( ( "[OPTIONS]",                            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "Bus to probe (interactive mode only):","-b<bus> or --bus=<bus>" ) ) )
    log.info( formatter.compose( ( "",                                     "<bus>: cups*, usb, net, bt, fw, par (*default) (Note: net, bt, fw, and par not supported)" ) ) )
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ) ) )

    log.info(  """Examples:\n\nAlign CUPS printer named "hp5550":\n   align.py -php5550\n\n""" \
               """Align printer with URI of "hp:/usb/DESKJET_990C?serial=12345":\n   align.py -dhp:/usb/DESKJET_990C?serial=12345\n\n""" \
               """**NOTES: 1. If device or printer is not specified, the local device bus\n""" \
               """            is probed and the program enters interactive mode.\n""" \
               """         2. If -p* is specified, the default CUPS printer will be used.\n""" )
        

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

def enterAlignmentNumber( letter, hortvert, colors, line_count, maximum ):
    return enterNumber( "Enter the best aligned value for line %s (1-%d): " % ( letter, maximum ),
                        1, 
                        maximum )
                        
def enterPaperEdge( maximum ):
    return enterNumber( "Enter numbered arrow that is best aligned with the paper edge (1-%d): " % maximum,
                        1, 
                        maximum )

def colorAdj( line, maximum ):
    return enterNumber( "Enter the numbered box on line %s that is best color matched to the background color (1-%d): " % ( line, maximum ),
                        1, 
                        maximum )
                        

def loadPlainPaper():
    x = raw_input( utils.bold( "An alignment page will be printed.\nPlease load plain paper into the printer. Press <Enter> to contine or 'q' to quit." ) )
    if len(x) > 0 and x[0].lower() == 'q':
        return False
    return True 
    
def bothPensRequired():
    log.error( "Cannot perform alignment with 0 or 1 cartridges installed.\nPlease install both cartridges and try again." )
    
def invalidPen():
    log.error( "Invalid cartridge(s) installed.\nPlease install valid cartridges and try again." )

def aioUI1():
    log.info( "To perform alignment, you will need the alignment page that is automatically\nprinted after you install a print cartridge." )
    log.info( "If you would like to cancel, enter 'C' or 'c'" )
    log.info( "If you do not have this page, enter 'N' or 'n'" )
    log.info( "If you already have this page, enter 'Y' or 'y'" )
    
    while 1:
        x = raw_input( utils.bold( "Enter 'C', 'c','Y', 'y', 'N', or 'n': " ) )
        if len(x) > 0:
            x = x.lower()
            if x[0] in ['c', 'y', 'n']:
                break
            
        info.warning( "Please enter 'C', 'c', 'Y', 'y', 'N' or 'n'." )
    
    if x[0] == 'n':
        return True, True
        
    elif x[0] == 'c':
        return False, False
        
    elif x[0] == 'y':
        return True, False
        
    
def aioUI2():    
    log.info( utils.bold( "Follow these steps to complete the alignment:" ) )
    log.info( "1. Place the alignment page, with the printed side facing down, "  )
    log.info( "   in the scanner." )
    log.info( "2. Press the Enter or Scan button on the printer." )
    log.info( '3. "Alignment Complete" will be displayed when the process is finished (on some models).' )

utils.log_title( 'Printer Cartridge Alignment Utility', _VERSION )
    
try:
    opts, args = getopt.getopt( sys.argv[1:], 
                                'p:d:hl:b:a', 
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
align_debug = False

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
        
    elif o == '-a':
        align_debug = True
        

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
    
#log.info( "Aligning device..." )
try:
    s = None
    try:
        device_id = d.open()
    except Error:
        log.error( "Unable to open device. Exiting. " )
        #sys.exit(0)
        raise Error(0)
    
    try:
        s = service.Service()
    except Error:
        log.error( "Unable to contact services daemon. Exiting." )
        #sys.exit(0)
        raise Error(0)
        
    try:
        fields = s.queryModel( d.model )
        align_type = fields.get( 'align-type', 0 )
    except Error:
        log.error( "Query for model failed. Exiting." )
        #sys.exit(0)
        raise Error(0)
    
    log.debug( "Alignment type=%d" % align_type )
    
    if align_type == 0: 
        log.error( "Alignment not supported or required by device." )
        raise Error(0)
        
    if align_type == 1: # auto PCL 
        maint.AlignType1( d, loadPlainPaper )

    elif align_type == 2: # 8xx (Phobos)
        maint.AlignType2( d, loadPlainPaper, enterAlignmentNumber, bothPensRequired, update_spinner )
        
    elif align_type == 3: # 9xx (Thriftway/Subway)
        maint.AlignType3( d, loadPlainPaper, enterAlignmentNumber, enterPaperEdge, update_spinner )
        
    elif align_type == 6: # LIDIL Auto (Homer)
       maint.AlignType6( d, aioUI1, aioUI2, loadPlainPaper )
        
    elif align_type == 8: # 450
        maint.AlignType8( d, loadPlainPaper, enterAlignmentNumber, update_spinner )    
        
    elif align_type in [ 4, 5, 7 ]: # LIDIL xBow (Dart/Arrow), LIDIL xBow+ (Spear/Stelleto/Dagger), xBow VIP (Crayola)
        maint.AlignxBow( d, align_type, loadPlainPaper, enterAlignmentNumber, enterPaperEdge, invalidPen, colorAdj, update_spinner )
    
    else:
        log.error( "Invalid alignmen type." )
        
finally:    
    log.info( "" )
    if d is not None:
        d.close()
    if s is not None:
        s.close()
        
    log.info( 'Done.' )
