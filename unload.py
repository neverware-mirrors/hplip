#!/usr/bin/env python
#
# $Revision: 1.13 $ 
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


_VERSION = '1.6'

# Std Lib
import sys
import getopt

# Local
from base.g import *
from base import utils


def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( utils.TextFormatter.bold( """\nUsage: hp-unload [PRINTER|DEVICE-URI] [OPTIONS]\n\n""") )
    log.info( formatter.compose( ( utils.TextFormatter.bold("[PRINTER|DEVICE-URI]"), "" ) ) )
    #log.info( formatter.compose( ( "(**See NOTES 1&2)",                     "" ) ) )
    log.info( formatter.compose( ( "To specify a CUPS printer:",           "-p<printer> or --printer=<printer>" ) ) )
    log.info( formatter.compose( ( "To specify a device-URI:",             "-d<device-uri> or --device=<device-uri>" ), True ) )
    log.info( formatter.compose( ( utils.TextFormatter.bold("[OPTIONS]"),            "" ) ) )
    log.info( formatter.compose( ( "Set the logging level:",               "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                                     "<level>: none, info*, error, warn, debug (*default)" ) ) )
    log.info( formatter.compose( ( "Bus to probe (interactive mode only):","-b<bus> or --bus=<bus>" ) ) )
    log.info( formatter.compose( ( "",                                     "<bus>: cups*, usb, net, bt, fw, par (*default) (Note: net, bt, fw, and par not supported)" ) ) )
    log.info( formatter.compose( ( "This help information:",               "-h or --help" ), True ) )



# PyQt
try:
    from qt import *
except ImportError:
    log.error( "PyQt not installed. GUI not available. Exiting." )
    sys.exit(0)

# check version of Qt
qt_split_version = qVersion().split('.')
qtMajor = int( qt_split_version[0] )
qtMinor = int( qt_split_version[1] )

if qtMajor < MINIMUM_QT_MAJOR_VER: 
    
    log.error( "Incorrect version of Qt installed. Ver. 3.0.0 or greater required.")
    sys.exit(0)

#check version of PyQt
try:
    pyqtVersion = PYQT_VERSION_STR
except:
    pyqtVersion = PYQT_VERSION

while pyqtVersion.count('.') < 2:
    pyqtVersion += '.0'

(maj, min, pat) = pyqtVersion.split('.')

if pyqtVersion.find( 'snapshot' ) >= 0:
    log.warning( "A non-stable snapshot version of PyQt is installed.")
else:    
    try:
        maj = int(maj)
        min = int(min)
        pat = int(pat)
    except ValueError:
        maj, min, pat = 0, 0, 0
        
    if maj < MINIMUM_PYQT_MAJOR_VER or \
        (maj == MINIMUM_PYQT_MAJOR_VER and min < MINIMUM_PYQT_MINOR_VER):
        log.error( "This program may not function properly with the version of PyQt that is installed (%d.%d.%d)." % (maj, min, pat) )
        log.error( "Incorrect version of pyQt installed. Ver. %d.%d or greater required." % ( MINIMUM_PYQT_MAJOR_VER, MINIMUM_PYQT_MINOR_VER ) )
        
    
use_qt_splashscreen = False
#if qtMajor >= 3 and qtMinor >= 2:
#    use_qt_splashscreen = True

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
    sys.exit(1)
    
printer_name = None
device_uri = None    
bus = 'usb,cups'
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
    usage()
    sys.exit(0)

log.set_level( log_level )         
        

def __tr( s,c = None):
    return qApp.translate( "Unload",s,c)
    
utils.log_title( 'Photo Card Access GUI', _VERSION )

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



        
    
    

