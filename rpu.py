#!/usr/bin/env python
#
# $Revision: 1.11 $ 
# $Date: 2005/03/21 17:38:49 $
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


_VERSION = '1.1'

# Std Lib
import sys
import re
import getopt

# Local
from base.g import *
from base.codes import *
from base import device, service, status, utils
from prnt import cups, pcl

def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( """\nUsage: hp-rpu [PRINTER|DEVICE-URI] [OPTIONS]\n\n""" )
    
    log.info( formatter.compose( ( "[PRINTER|DEVICE-URI] (**See NOTES)", "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ) ) )
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
        
        if len(str(x)) != 4:
            log.error( "You must enter a four digit number" )
            continue
        
        break
        
    
    return True, str(x)

utils.log_title( 'RPU Utility', _VERSION )    

try:
    opts, args = getopt.getopt( sys.argv[1:], 
                                'p:d:hl:b:c:', 
                                [ 'printer=', 
                                  'device=', 
                                  'help', 
                                  'logging=',
                                  'bus=',
                                ] 
                              ) 
except getopt.GetoptError:
    usage()
    sys.exit(1)
    
printer_name = None
device_uri = None    
bus = 'cups,usb'
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
        
        

for x in bus.split(','):
    bb = x.lower().strip()
    #if not bb in ( 'usb', 'net', 'bt', 'fw' ):
    if bb not in ( 'usb', 'cups', 'net' ):
        log.error( "Invalid bus name: %s" % bb )
        usage()
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
    
log.info( "" )
log.info( utils.bold( "Please wait..." ) )
    
try:
    try:
        try:
            device_id = d.open()
        except Error:
            log.error( "Unable to open device. Exiting. " )
            raise Error(0)
            
        try:
            value_12 = d.getDynamicCounter( 12, update_spinner )
        except Error, e:
            log.error( e[0] )
    
        try:
            value_28 = d.getDynamicCounter( 28, update_spinner )
        except Error, e:
            log.error( e[0] )
            
        try:
            value_29 = d.getDynamicCounter( 29, update_spinner )
        except Error, e:
            log.error( e[0] )
            
        try:
            value_301 = d.getDynamicCounter( 301, update_spinner )
        except Error, e:
            log.error( e[0] )
    
        try:
            value_302 = d.getDynamicCounter( 302, update_spinner )
        except Error, e:
            log.error( e[0] )
    
        log.info("")
        parsed, raw = d.ID()
        log.debug( "S/N=%s" % parsed['SN'] )
        sn = "%12s" % parsed['SN']
        len_sn = len(sn)
            
        if len_sn <= 12:
            box_11 = sn[:4]
            box_12 = sn[4:8]
            box_13 = sn[8:]
        elif len_sn == 13:
            box_11 = sn[:5]
            box_12 = sn[5:9]
            box_13 = sn[9:]
        else:
            box_11 = sn[:5]
            box_12 = sn[5:10]
            box_13 = sn[10:]
        
        log.info( utils.brown( "Box 11: %s" % box_11 ) )
        log.info( utils.brown( "Box 12: %s" % box_12 ) ) 
        log.info( utils.brown( "Box 13: %s" % box_13 ) )
        
        boxes_14_15 = "%08d" % value_12
        log.debug( "Counter 12=%d (0x%x)" % (value_12, value_12) )
        box_14 = boxes_14_15[:4]
        box_15 = boxes_14_15[4:]
            
        log.info( utils.darkblue( "Box 14: %s" % box_14 ) )
        log.info( utils.darkblue( "Box 15: %s" % box_15 ) )
    
        boxes_16_17_21_22 = "%08X%08X" % (value_301>>3, value_28)
        log.debug( "Counter 28=%d (0x%x)" % (value_28, value_28) )
        log.debug( "Counter 301=%d (0x%x)" % (value_301, value_301) )
        log.debug( "Counter 301>>3=%d (0x%x)" % (value_301>>3, value_301>>3) )
        log.debug( "Left Pen ID=%x" % value_28 )
        box_16 = boxes_16_17_21_22[:4]
        box_17 = boxes_16_17_21_22[4:8]
        box_21 = boxes_16_17_21_22[8:12]
        box_22 = boxes_16_17_21_22[12:]
            
        log.info( utils.darkred( "Box 16: %s" % box_16 ) )
        log.info( utils.darkred( "Box 17: %s" % box_17 ) )
        log.info( utils.darkred( "Box 21: %s" % box_21 ) )
        log.info( utils.darkred( "Box 22: %s" % box_22 ) )
        
        boxes_23_24_25_26 = "%08X%08X" % (value_302>>3, value_29 )
        log.debug( "Counter 29=%d (0x%x)" % (value_29,value_29) )
        log.debug( "Counter 302=%d (0x%x)" % (value_302, value_302) )
        log.debug( "Counter 302>>3=%d (0x%x)" % (value_302>>3, value_302>>3) )
        log.debug( "Left Pen ID=%x" % value_29 )
        box_23 = boxes_23_24_25_26[:4]
        box_24 = boxes_23_24_25_26[4:8]
        box_25 = boxes_23_24_25_26[8:12]
        box_26 = boxes_23_24_25_26[12:]
            
        log.info( utils.darkgreen( "Box 23: %s" % box_23 ) )
        log.info( utils.darkgreen( "Box 24: %s" % box_24 ) )
        log.info( utils.darkgreen( "Box 25: %s" % box_25 ) )
        log.info( utils.darkgreen( "Box 26: %s" % box_26 ) )
    
        log.info( utils.brown( "Box 27: 0000" ) )
        
        temp = sn + boxes_14_15 + boxes_16_17_21_22 + boxes_23_24_25_26 + '0000'
        log.info( "" )
        log.info( utils.darkred( "Box 31: %d" % utils.calcCRC(temp) ) )
        log.info( "" )
        
        cont, box_41 = enterNumber( "Enter Box 41 (or enter 'q' to quit): ", 0, sys.maxint )
        if not cont:
            raise Error(0)
        
        cont, box_42 = enterNumber( "Enter Box 42 (or enter 'q' to quit): ", 0, sys.maxint )
        if not cont:
            raise Error(0)
        
        cont, box_43 = enterNumber( "Enter Box 43 (or enter 'q' to quit): ", 0, sys.maxint )
        if not cont:
            raise Error(0)
        
        cont, box_44 = enterNumber( "Enter Box 44 (or enter 'q' to quit): ", 0, sys.maxint )
        if not cont:
            raise Error(0)
    
        cont, box_45 = enterNumber( "Enter Box 45 (or enter 'q' to quit): ", 0, sys.maxint )
        if not cont:
            raise Error(0)
            
        temp = box_41 + box_42 + box_43 + box_44 + box_45
        log.info( "" )
        log.info( utils.darkred( "Box 51: %d" % utils.calcCRC(temp) ) )
        log.info( "" )
        
        while True:
            x = raw_input( utils.bold( "If Box 51, is correct, enter 'c' or continue. Otherwise, enter 'q' to quit: " ) )
            x = str(x).lower()
    
            if x == 'c':
                break
                
            elif x == 'q':
                raise Error(0)
                
            else:
                log.error( "Please enter 'c' or 'q'" )
        
        p = pcl.buildRP( box_41, box_42, box_43, box_44, box_45 )
        
        c = d.checkOpenChannel( 'PRINT' )
        d.writeChannel( c, p, update_spinner )
        d.closeChannel( 'PRINT' )
    except:
        pass
finally:    
    log.info( "" )
    if d is not None:
        d.close()
        
    log.info( 'Done.' )
