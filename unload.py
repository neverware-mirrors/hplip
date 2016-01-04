#!/usr/bin/env python
#
# $Revision: 1.15 $
# $Date: 2005/07/21 23:54:55 $
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


_VERSION = '1.8'

# Std Lib
import sys
import getopt

# Local
from base.g import *
from base import utils, device
from prnt import cups

use_qt_splashscreen = False

def usage():
    formatter = utils.usage_formatter()
    log.info( utils.TextFormatter.bold( """\nUsage: hp-unload [PRINTER|DEVICE-URI] [OPTIONS]\n\n""") )
    log.info( utils.bold("[PRINTER|DEVICE-URI]"))
    utils.usage_device(formatter)
    utils.usage_printer(formatter, True)
    utils.usage_options()
    utils.usage_logging(formatter)
    utils.usage_help(formatter, True)

    sys.exit(0)


# PyQt
if not utils.checkPyQtImport():
    sys.exit(0)

from qt import *
from ui import unloadform

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

utils.log_title( 'Photo Card Access GUI', _VERSION )

for o, a in opts:

    if o in ( '-h', '--help' ):
        usage()

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

def __tr( s,c = None):
    return qApp.translate( "Unload",s,c)

try:
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))

    if use_qt_splashscreen:
        pixmap = QPixmap( os.path.join( prop.image_dir, "hp-tux-printer.png" ) )
        splash = QSplashScreen( pixmap )
        splash.message( __tr( "Loading..." ), Qt.AlignBottom )
        splash.show()

    w = unloadform.UnloadForm( bus, device_uri, printer_name )
    a.setMainWidget(w)
    w.show()

    if use_qt_splashscreen:
        splash.finish( w )

    a.exec_loop()
except Exception, e:
    log.exception()







