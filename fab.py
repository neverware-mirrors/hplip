#!/usr/bin/env python
#

# $Revision: 1.3 $ 
# $Date: 2005/06/28 23:13:40 $
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

_VERSION = '0.1'

from base.g import *
from base import utils

import getopt

# PyQt
if not utils.checkPyQtImport():
    sys.exit(0)

from qt import *

from ui.faxaddrbookform import FaxAddrBookForm

app = None
addrbook = None

def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 28, 'margin' : 2},
                    {'width': 58, 'margin' : 2},
                )
            )

    log.info( utils.TextFormatter.bold( """\nUsage: hp-fab [OPTIONS]\n\n""" ) )

    log.info( formatter.compose( ( utils.TextFormatter.bold("[OPTIONS]"), "" ) ) )

    log.info( formatter.compose( ( "Set the logging level:", "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                       "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "This help information:", "-h or --help" ), True ) )

def main( args ):

    

    utils.log_title( 'HP Device Manager - Fax Address Book', _VERSION )
    log.info( "Includes code from KirbyBase 1.8.1" )
    log.info( "Copyright (c) Jamey Cribbs (jcribbs@twmi.rr.com)" )
    log.info( "Licensed under the Python Software Foundation License." )

    try:
        opts, args = getopt.getopt( sys.argv[1:], 'l:h', [ 'level=', 'help' ] ) 

    except getopt.GetoptError:
        usage()
        sys.exit(1)

    for o, a in opts:

        if o in ( '-l', '--logging' ):
            log_level = a.lower().strip()
            log.set_level( log_level )

        elif o in ( '-h', '--help' ):
            usage()
            sys.exit(1)
    
    log.set_module( 'fab' )

    # Security: Do *not* create files that other users can muck around with
    os.umask ( 0077 )
    
    # create the main application object
    global app
    app = QApplication( sys.argv )
    
    global addrbook
    addrbook = FaxAddrBookForm( )
    addrbook.show()
    app.setMainWidget( addrbook )

    user_config = os.path.expanduser( '~/.hplip.conf' )
    loc = utils.loadTranslators( app, user_config )

    try:
        log.debug( "Starting GUI loop..." )
        app.exec_loop()
    except KeyboardInterrupt:
        pass
    except:
        log.exception()

    #handleEXIT()

if __name__ == "__main__":
    sys.exit( main( sys.argv[1:] ) )
