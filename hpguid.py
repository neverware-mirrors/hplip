#!/usr/bin/env python
#
# $Revision: 1.22 $ 
# $Date: 2004/12/21 19:21:04 $
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


_VERSION = '3.0'

##from __future__ import generators

# Std Lib
import sys
import socket
import os, pwd, os.path
import getopt
import signal
import atexit
import ConfigParser

# Local
from base.g import *
import base.async_qt as async
import base.utils as utils
from base.msg import *
import base.service as service

app = None
services = None
server = None    
main_widget = None
toolbox  = None


# PyQt
try:
    from qt import *
except ImportError:
    log.error( "PyQt not installed. GUI not available. Exiting." )
    sys.exit(0)

# check version of Qt
qtMajor = int( qVersion().split('.')[0] )

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
        
    


# UI Forms        
from ui.form1 import Form1
#from ui.devmgr3 import devmgr3
#from ui.devmgr2 import DevMgr2
from ui.devmgr4 import devmgr4

def _showToolbox( show=True, raiseup=True, initial_device_uri=None ):
    global toolbox
    
    if show:
        if not prop.toolbox_ui_active:
            log.debug( "Creating toolbox UI" )
            toolbox = devmgr4( initial_device_uri )
            prop.toolbox_ui_active = True
        
        if raiseup:
            log.debug( "Showing toolbox" )
            toolbox.show()
            toolbox.setActiveWindow()
            toolbox.raiseW()
    else:
        if prop.toolbox_ui_active:
            log.debug( "Hiding toolbox" )
            toolbox.hide()

def usage():
    formatter = utils.TextFormatter( 
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info( utils.TextFormatter.bold( """\nUsage: hpguid.py [OPTIONS]\n\n""" ) )
    
    log.info( formatter.compose( ( utils.TextFormatter.bold("[OPTIONS]"), "" ) ) )
    
    log.info( formatter.compose( ( "Set the logging level:", "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "",                       "<level>: none, info*, error, warn, debug (*default)" ) ) )
    #log.info( formatter.compose( ( "Start with UI:",         "-u<ui> or --ui=<ui>" ) ) )
    log.info( formatter.compose( ( "Do not daemonize:",      "-x" ) ) )
    log.info( formatter.compose( ( "This help information:", "-h or --help" ), True ) )

            


class hpguid_server( async.dispatcher ):

    def __init__( self, ip ):
        self.ip = ip
        self.port = socket.htons(0)
        async.dispatcher.__init__( self )
        self.create_socket( socket.AF_INET, socket.SOCK_STREAM )
        self.set_reuse_addr()
        try:
            self.bind( ( ip, self.port ) )
        except socket.error,e:
            log.fatal( "Unable to address to socket: %s" % e[1] )
            raise Error
        self.port = self.socket.getsockname()[1]
        prop.hpguid_port = self.port
        self.listen( 5 )
       
        
    def writable( self ):
        return False
        
    def readable( self ):
        return self.accepting
        
    def handle_accept( self ):
        try:
            conn, addr = self.accept()
        except socket.error:
            log.error( "Socket error on accept()" )
            return
        except TypeError:
            log.error( "EWOULDBLOCK exception on accept()" )
            return
        handler = hpguid_handler( conn, addr, self )
        
    def __str__( self ):
        return "<hpssd_server listening on %s:%d (fd=%d)>" % \
                ( self.ip, self.port, self._fileno )
        
    def handle_close( self ):
        async.dispatcher.handle_close( self )

 


# This handler takes care of all conversations with
# clients when hpguid is acting as a server.
# This dispatcher receives requests messages and
# and replies with result messages. It does not 
# initiate sending requests.
class hpguid_handler( async.dispatcher ):
    
    def __init__( self, conn, addr, server ): 
        async.dispatcher.__init__( self, sock=conn )
        self.addr = addr
        self.in_buffer = ""
        self.out_buffer = ""
        self.server = server
        self.fields = {}
        self.data = ''
        self.error_dialog = None
        self.toolbox_active = False
        self.signal_exit = False

        # handlers for all the messages we expect to receive
        self.handlers = { 
                        'eventgui' : self.handle_eventgui,
                        ##'showguievent' : self.handleguievent,
                        'unknown' : self.handle_unknown,
                        'exitguievent' : self.handle_exitguievent,  
                        }
                         
    def __str__( self ):
        return "<hpssd_handler connected to %s (fd=%d)>" % \
                ( self.addr, self._fileno )

    def handle_read( self ):
        log.debug( "Reading data on channel (%d)" % self._fileno )
        self.in_buffer = self.recv( prop.max_message_len )
        
        if self.in_buffer == '':
            return False
        
        try:
            self.fields, self.data = parseMessage( self.in_buffer )
        except Error, e:
            log.debug( repr(self.in_buffer) )
            log.warn( "Message parsing error: %s (%d)" % (e.msg, err) )
            self.out_buffer = self.handle_unknown( err )
            log.debug( self.out_buffer )
            return True
            
        msg_type = self.fields.get( 'msg', 'unknown' )
        #self.sock_write_notifier.setEnabled( False )
        log.debug( "%s %s %s" % ("*"*40, msg_type, "*"*40 ) ) 
        log.debug( repr( self.in_buffer ) ) 
        
        try:
            self.out_buffer = self.handlers.get( msg_type, self.handle_unknown )()
        except Error:
            log.error( "Unhandled exception during processing" )    
            
        if len( self.out_buffer ): # data is ready for send
            self.sock_write_notifier.setEnabled( True )
        
        #self.sock_write_notifier.setEnabled( True )
        return True
        
    def handle_write( self ):
        if not len(self.out_buffer):
            return
            
        log.debug( "Sending data on channel (%d)" % self._fileno )
        log.debug( repr( self.out_buffer ) )
        try:
            sent = self.send( self.out_buffer )
        except:
            log.error( "send() failed." )
            
        self.out_buffer = self.out_buffer[ sent: ]
        
        #if self.signal_exit:
        #    if toolbox is not None:
        #        toolbox.close()
        #    main_widget.close()
        #    qApp.quit()


    def writable( self ):
        return not ( ( len( self.out_buffer ) == 0 ) 
                     and self.connected )


    def handle_exitguievent( self ):
        self.signal_exit = True
        if self.signal_exit:
            if toolbox is not None:
                toolbox.close()
            main_widget.close()
            qApp.quit()
        
        
        return '' #buildResultMessage( 'ExitUIGUIResult' )

    
    # EVENT
    def handle_eventgui( self ):
        global toolbox
        #try:
        if 1:
            job_id = self.fields[ 'job-id' ]
            event_code = self.fields[ 'event-code' ]
            event_type = self.fields[ 'event-type' ]
            retry_timeout = self.fields[ 'retry-timeout' ]
            popup = self.fields[ 'popup' ]
            lines = self.data.splitlines()
            error_string_short, error_string_long = lines[0], lines[1]
            device_uri = self.fields[ 'device-uri' ]
            
            log.debug( "Event: %d '%s'" % ( event_code, event_type ) )
            toolbox_was_active = prop.toolbox_ui_active
            
            if event_type == 'event':
                if event_code == EVENT_UI_SHOW_TOOLBOX:
                    _showToolbox( True, True )
                    toolbox.eventUI( EVENT_UI_SHOW_TOOLBOX, 'event', '', '', 0, 0, '' )
                
                elif event_code == EVENT_UI_HIDE_TOOLBOX:
                    _showToolbox( False, False )
                
                else:
                    _showToolbox( True, popup, device_uri )
                    if toolbox_was_active:
                        toolbox.eventUI( event_code, event_type, error_string_short, error_string_long, 
                                         retry_timeout, job_id, device_uri )
                    
            else: 
                _showToolbox( True, popup, device_uri ) # error, warning, fatal
                if toolbox_was_active:
                    toolbox.eventUI( event_code, event_type, error_string_short, error_string_long, 
                                     retry_timeout, job_id, device_uri )
                
        if 1:
            return ''
                                   
    def handle_unknown( self ):
        return buildResultMessage( 'MessageError', None, ERROR_INVALID_MSG_TYPE )
        
    def handle_messageerror( self ):
        return ''
        
    def handle_close( self ):
        log.debug( "closing channel (%d)" % self._fileno )
        self.connected = False
        async.dispatcher.close( self )
    
    
def registerGUI():
    try:
        services.registerGUI( prop.username, prop.hpguid_host, prop.hpguid_port, os.getpid() )
    except Error, e:
        log.error( "Register GUI failed (code=%d). Exiting. " % e.opt )
        sys.exit(0)
    
def unregisterGUI():
    try:
        services.unregisterGUI( prop.username, os.getpid() )
    except Error, e:
        log.error( "UnRegister GUI failed (code=%d). " % e.opt )


    

#def handleSIGHUP( signo, frame ):
#    log.info( "SIGHUP" )
#    if services is not None:
#        registerGUI()
    
#def handleSIGTERM( signo, frame ):
#    log.info( "SIGTERM" )
#    raise SystemError( signo )
    
def handleEXIT():
    try:
        toolbox.cleanup()
    except:
        pass
    
    if services is not None:
        try:
            unregisterGUI()
            services.close()
        except:
            pass
        
    
    if server is not None:
        try:
            server.close()
        except:
            pass
    
    try: 
        app.quit()
    except: 
        pass
    
    sys.exit(0)
    
    
    
def main( args ):
    prop.prog = sys.argv[0]        
    prop.daemonize = True
    log.set_module( 'hpguid' )

    utils.log_title( 'GUI Daemon', _VERSION )

    try:
        opts, args = getopt.getopt( sys.argv[1:], 'l:hx', [ 'level=', 'help' ] ) 
              
    except getopt.GetoptError:
        usage()
        sys.exit(1)
        
    ui = None
    
    for o, a in opts:
        
        if o in ( '-l', '--logging' ):
            log_level = a.lower().strip()
            log.set_level( log_level )
            
        elif o in ( '-h', '--help' ):
            usage()
            sys.exit(1)
            
        #elif o in ( '-u', '--ui' ):
        #    ui = a.lower().strip()
            
        elif o in ( '-x', ):
            prop.daemonize = False
            
            
    if prop.daemonize:
        utils.daemonize()
    
    # hpguid server dispatcher object
    global server
    try:
        server = hpguid_server( prop.hpguid_host ) 
        ##log.debug( str( server ) )
    except Error:
        log.error( "Unable to create server object." )
        sys.exit( 0 )
    
    log.info( "Listening on %s port %d" % ( prop.hpguid_host, prop.hpguid_port ) )
    
    # create the main application object
    global app
    app = QApplication( sys.argv )

    global main_widget
    main_widget = Form1()
    app.setMainWidget( main_widget )
    
    prop.toolbox_ui_active = False

    global services
    try:
        services = service.Service()
    except Error:
        log.error( "Unable to contact services daemon. Exiting." )
        sys.exit(0)
    
    registerGUI()
    
    pid = os.getpid()
    log.debug( 'pid=%d' % pid )

    if log.get_level() == log.LOG_LEVEL_DEBUG:
        main_widget.show()
        QObject.connect( app, SIGNAL( "lastWindowClosed()" ), app, SLOT( "quit()" ) )

    atexit.register( handleEXIT )   
    #signal.signal( signal.SIGHUP, handleSIGHUP )
    signal.signal( signal.SIGPIPE, signal.SIG_IGN )
    
    user_config = os.path.expanduser( '~/.hplip.conf' )
    loc = None
    
    if os.path.exists( user_config ):
        config = ConfigParser.ConfigParser()
        config.read( user_config )
    
        if config.has_section( "ui" ):
            loc = config.get( "ui", "loc" )
        
            if not loc:
                loc = None
    
    if loc is not None:
    
        if loc.lower() == 'system':
            loc = str(QTextCodec.locale())
            
        if loc.lower() != 'c':
            
            log.debug( "Trying to load .qm file for %s locale." % loc )
            
            dirs = [ prop.home_dir, prop.data_dir, prop.i18n_dir ]
    
            trans = QTranslator(None)
            
            for dir in dirs:
                qm_file = 'hplip_%s' % loc
                loaded = trans.load( qm_file, dir)
                
                if loaded:
                    app.installTranslator( trans )
                    break
        else:
            loc = None
            
    if loc is None:
        log.debug( "Using default 'C' locale" )
    else:
        log.debug( "Using locale: %s" % loc )
    
    try:
        try:
            log.debug( "Starting GUI loop..." )
            app.exec_loop()
        #except KeyboardInterrupt:
        #    handleEXIT()
        except:
            utils.log_exception()
    finally:
        handleEXIT()
        
if __name__ == "__main__":
    sys.exit( main( sys.argv[1:] ) )
    
