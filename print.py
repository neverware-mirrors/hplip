#!/usr/bin/env python
#
# $Revision: 1.15 $ 
# $Date: 2005/06/28 23:13:41 $
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
import os
import getopt
import re

# Local
from base.g import *
from base import utils, device
from prnt import cups

# PyQt
if not utils.checkPyQtImport():
    sys.exit(0)

from qt import *
from ui.printerform import PrinterForm

app = None   
printdlg = None

def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( utils.TextFormatter.bold( """\nUsage: hp-print [PRINTER|DEVICE-URI] [OPTIONS] [FILE LIST]\n\n""") )

    log.info( formatter.compose( ( utils.TextFormatter.bold("[PRINTER|DEVICE-URI]"), "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ), True ) )
    log.info( formatter.compose( ( utils.TextFormatter.bold("[OPTIONS]"),            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ), True ) )

def main( args ):

    utils.log_title( 'Print Utility', _VERSION )

    try:
        opts, args = getopt.getopt( sys.argv[1:], 'P:p:d:hb:l:', 
                                   [ 'printer=', 'device=', 'help', 'logging=' ] ) 
    except getopt.GetoptError:
        usage()
        sys.exit(0)

    printer_name = None
    device_uri = None    
    log_level = 'info'

    for o, a in opts:
        if o in ( '-h', '--help' ):
            usage()
            sys.exit(0)

        elif o in ( '-p', '-P', '--printer' ): 
            printer_name = a

        elif o in ( '-d', '--device' ):
            device_uri = a

        elif o in ( '-l', '--logging' ):
            log_level = a.lower().strip()


    if not log_level in ( 'info', 'warn', 'error', 'debug' ):
        log.error( "Invalid logging level." )
        sys.exit(0)

    log.set_level( log_level )   
    log.set_module( 'hp-print' )

    # Security: Do *not* create files that other users can muck around with
    os.umask ( 0077 )

    # create the main application object
    global app
    app = QApplication( sys.argv )

    global printdlg
    printdlg = PrinterForm( device_uri, printer_name, args )
    printdlg.show()
    app.setMainWidget( printdlg )

    user_config = os.path.expanduser( '~/.hplip.conf' )
    loc = utils.loadTranslators( app, user_config )

    try:
        log.debug( "Starting GUI loop..." )
        app.exec_loop()
    except KeyboardInterrupt:
        pass
    except:
        log.exception()

if __name__ == "__main__":
    sys.exit( main( sys.argv[1:] ) )

