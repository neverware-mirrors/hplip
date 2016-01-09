#!/usr/bin/env python
#
# $Revision: 1.8 $ 
# $Date: 2005/07/12 16:43:09 $
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


_VERSION = '2.3'

# Std Lib
import sys
import re
import getopt
import socket


# Local
from base.g import *
from base import device, utils, msg

def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 48, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( utils.bold( """\nUsage: hp-makeuri [OPTIONS] IPs|DEVNODEs\n\n""" ) )

    log.info( formatter.compose( ( "[OPTIONS]",                            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "Show the CUPS URI only (quiet mode)(See note):","-c or --cups" ) ) )
    log.info( formatter.compose( ( "Show the SANE URI only (quiet mode)(See note):","-s or --sane" ) ) )
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ) ) )
    log.info("")
    log.info( "Note: Sets logging level to 'none'" )





try:
    opts, args = getopt.getopt( sys.argv[1:], 
                                'hl:cs', 
                                [ 'help', 
                                  'logging=',
                                  'cups',
                                  'sane'
                                ] 
                              ) 
except getopt.GetoptError:
    usage()
    sys.exit(1)


log_level = 'info'
cups_quiet_mode = False
sane_quiet_mode = False

for o, a in opts:

    if o in ( '-h', '--help' ):
        usage()
        sys.exit(0)

    elif o in ( '-l', '--logging' ):
        log_level = a.lower().strip()
        
    elif o in ( '-c', '--cups' ):
        cups_quiet_mode = True
        
    elif o in ( '-s', '--sane' ):
        sane_quiet_mode = True


if not log_level in ( 'none', 'info', 'warn', 'error', 'debug' ):
    log.error( "Invalid logging level." )
    usage()
    sys.exit(0)
    
if cups_quiet_mode or sane_quiet_mode:
    log_level = 'none'

log.set_level( log_level )

utils.log_title( 'Device URI Creation Utility', _VERSION )

hpiod_sock = None
try:
    hpiod_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    hpiod_sock.connect( ( prop.hpiod_host, prop.hpiod_port ) )
except socket.error:
    log.error( "Unable to connect to hpiod." )
    sys.exit(-1)


ip_pat = re.compile( r"""\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b""", re.IGNORECASE )
dev_pat = re.compile( r"""/dev/.+""", re.IGNORECASE )

if len(args) == 0:
    log.error( "You must specify IPs and/or DEVNODEs on the command line." )
    sys.exit(0)

for a in args:
    log.info( utils.bold( "Creating URIs for '%s':" % a ) )

    if ip_pat.search(a) is not None:
        try:
            fields, data, result_code = \
                msg.xmitMessage( hpiod_sock, 
                                 "MakeURI", 
                                 None, 
                                 { 
                                    'hostname' : a,
                                    'port' : 1,
                                 } 
                                )
        except Error:
            result_code = ERROR_INTERNAL
        
        if result_code == ERROR_SUCCESS:
            cups_uri = fields.get( 'device-uri', '' )
            sane_uri = cups_uri.replace("hp:","hpaio:")
            
            if cups_quiet_mode or (not cups_quiet_mode and not sane_quiet_mode):
                print "CUPS URI:", cups_uri
            
            if sane_quiet_mode or (not cups_quiet_mode and not sane_quiet_mode):
                print "SANE URI:", sane_uri
        
        elif result_code == ERROR_INVALID_HOSTNAME:
            log.error( "Invalid hostname IP address. Please check the address and try again." )
        
        else:
            log.error( "Failed (error code=%d). Please check address of device and try again." % result_code )
        
    elif dev_pat.search(a) is not None:
        try:
            fields, data, result_code = \
                msg.xmitMessage( hpiod_sock, 
                                "MakeURI", 
                                None, 
                                { 
                                    'device-file' : a,
                                } 
                               )
        except Error:
            result_code = ERROR_INTERNAL

        if result_code == ERROR_SUCCESS:
            cups_uri = fields.get( 'device-uri', '' )
            sane_uri = cups_uri.replace("hp:","hpaio:")
            
            if cups_quiet_mode or (not cups_quiet_mode and not sane_quiet_mode):
                print "CUPS URI:", cups_uri
            
            if sane_quiet_mode or (not cups_quiet_mode and not sane_quiet_mode):
                print "SANE URI:", sane_uri
            
        else:
            log.error( "Failed. Please check device node of device and try again." )
            
    else:
        log.error( "Invalid IP or device node." )
        log.error( "IP addresses must be in the form 'a.b.c.d', where a, b, c, and d are between 0 and 255." )
        log.error( "Device nodes must be in the form '/dev/*' (e.g., /dev/usb/lp0 or /dev/hp6800)" )
    
    log.info( "" )

hpiod_sock.close()
