#!/usr/bin/env python
#
# $Revision: 1.16 $
# $Date: 2005/07/21 17:31:38 $
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
    formatter = utils.usage_formatter()
    log.info( utils.TextFormatter.bold( """\nUsage: hp-print [PRINTER|DEVICE-URI] [OPTIONS] [FILE LIST]\n\n""") )
    log.info( utils.bold("[PRINTER|DEVICE-URI]"))
    utils.usage_device(formatter)
    utils.usage_printer(formatter, True)
    utils.usage_options()
    utils.usage_logging(formatter)
    utils.usage_help(formatter, True)
    log.info(utils.bold("[FILELIST]"))
    log.info( formatter.compose( ( "Optional list of files:", """Space delimited list of files to print. """ \
                                   """Files can also be selected for print by adding them to the file list """ \
                                   """in the UI.""" ), True ) )

    sys.exit(0)

def main( args ):

    utils.log_title( 'File Print Utility', _VERSION )

    try:
        opts, args = getopt.getopt( sys.argv[1:], 'P:p:d:hb:l:',
                                   [ 'printer=', 'device=', 'help', 'logging=' ] )
    except getopt.GetoptError:
        usage()

    printer_name = None
    device_uri = None
    log_level = logger.DEFAULT_LOG_LEVEL

    for o, a in opts:
        if o in ( '-h', '--help' ):
            usage()

        elif o in ( '-p', '-P', '--printer' ):
            printer_name = a

        elif o in ( '-d', '--device' ):
            device_uri = a

        elif o in ( '-l', '--logging' ):
            log_level = a.lower().strip()


    if not log.set_level( log_level ):
        usage()

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

