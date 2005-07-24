#!/usr/bin/env python
#
# $Revision: 1.21 $ 
# $Date: 2005/07/19 23:21:55 $
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
# Thanks to Henrique M. Holschuh <hmh@debian.org> for various security patches
#

_VERSION = '5.0'

# Std Lib
import sys
import socket
import os, os.path
import getopt
import signal
import atexit
import ConfigParser

# Local
from base.g import *
import base.async_qt as async
import base.utils as utils
from base.msg import *
from base import service

app = None
server = None    
toolbox  = None

# PyQt
if not utils.checkPyQtImport():
    sys.exit(0)

from qt import *

# UI Forms
from ui.devmgr4 import devmgr4


def usage():
    formatter = utils.TextFormatter(
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info(utils.TextFormatter.bold("""\nUsage: hp-toolbox [OPTIONS]\n\n"""))

    log.info(formatter.compose((utils.TextFormatter.bold("[OPTIONS]"), "")))

    log.info(formatter.compose(("Set the logging level:", "-l<level> or --logging=<level>")))
    log.info(formatter.compose(("",                       "<level>: none, info*, error, warn, debug (*default)")))
    log.info(formatter.compose(("This help information:", "-h or --help"), True))


class hpguid_server(async.dispatcher):

    def __init__(self, ip):
        self.ip = ip
        self.port = socket.htons(0)
        async.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        try:
            self.bind((ip, self.port))
        except socket.error,e:
            log.fatal("Unable to address to socket: %s" % e[1])
            raise Error
        self.port = self.socket.getsockname()[1]
        prop.hpguid_port = self.port
        self.listen(5)


    def writable(self):
        return False

    def readable(self):
        return self.accepting

    def handle_accept(self):
        try:
            conn, addr = self.accept()
        except socket.error:
            log.error("Socket error on accept()")
            return
        except TypeError:
            log.error("EWOULDBLOCK exception on accept()")
            return
        handler = hpguid_handler(conn, addr, self)

    def __str__(self):
        return "<hpssd_server listening on %s:%d (fd=%d)>" % \
                (self.ip, self.port, self._fileno)

    def handle_close(self):
        async.dispatcher.handle_close(self)




# This handler takes care of all conversations with
# clients when hpguid is acting as a server.
# This dispatcher receives requests messages and
# and replies with result messages. It does not 
# initiate sending requests.
class hpguid_handler(async.dispatcher):

    def __init__(self, conn, addr, the_server): 
        async.dispatcher.__init__(self, sock=conn)
        self.addr = addr
        self.in_buffer = ""
        self.out_buffer = ""
        self.server = the_server
        self.fields = {}
        self.data = ''
        self.error_dialog = None
        self.toolbox_active = False
        self.signal_exit = False

        # handlers for all the messages we expect to receive
        self.handlers = {
                        'eventgui' : self.handle_eventgui,
                        'unknown' : self.handle_unknown,
                        'exitguievent' : self.handle_exitguievent,  
                        }

    def __str__(self):
        return "<hpssd_handler connected to %s (fd=%d)>" % \
                (self.addr, self._fileno)

    def handle_read(self):
        log.debug("Reading data on channel (%d)" % self._fileno)
        self.in_buffer = self.recv(prop.max_message_len)

        if self.in_buffer == '':
            return False
        
        remaining_msg = self.in_buffer
        
        while True:
        
            try:
                self.fields, self.data, remaining_msg = parseMessage(remaining_msg)
            except Error, e:
                log.debug(repr(self.in_buffer))
                log.warn("Message parsing error: %s (%d)" % (e.opt, e.msg))
                self.out_buffer = self.handle_unknown()
                log.debug(self.out_buffer)
                return True
    
            msg_type = self.fields.get('msg', 'unknown')
            log.debug("%s %s %s" % ("*"*40, msg_type, "*"*40)) 
            log.debug(repr(self.in_buffer)) 
    
            try:
                self.out_buffer = self.handlers.get(msg_type, self.handle_unknown)()
            except Error:
                log.error("Unhandled exception during processing")    
    
            if len(self.out_buffer): # data is ready for send
                self.sock_write_notifier.setEnabled(True)
                
            if not remaining_msg:
                break

        return True

    def handle_write(self):
        if not len(self.out_buffer):
            return

        log.debug("Sending data on channel (%d)" % self._fileno)
        log.debug(repr(self.out_buffer))
        try:
            sent = self.send(self.out_buffer)
        except:
            log.error("send() failed.")

        self.out_buffer = self.out_buffer[sent:]


    def writable(self):
        return not ((len(self.out_buffer) == 0) 
                     and self.connected)


    def handle_exitguievent(self):
        self.signal_exit = True
        if self.signal_exit:
            if toolbox is not None:
                toolbox.close()
            qApp.quit()

        return '' 

    # EVENT
    def handle_eventgui(self):
        global toolbox
        try:
            job_id = self.fields['job-id']
            event_code = self.fields['event-code']
            event_type = self.fields['event-type']
            retry_timeout = self.fields['retry-timeout']
            lines = self.data.splitlines()
            error_string_short, error_string_long = lines[0], lines[1]
            device_uri = self.fields['device-uri']

            log.debug("Event: %d '%s'" % (event_code, event_type))

            toolbox.EventUI(event_code, event_type, error_string_short, 
                             error_string_long, retry_timeout, job_id, 
                             device_uri)


        except:
            log.exception()

        return ''

    def handle_unknown(self):
        return buildResultMessage('MessageError', None, ERROR_INVALID_MSG_TYPE)

    def handle_messageerror(self):
        return ''

    def handle_close(self):
        log.debug("closing channel (%d)" % self._fileno)
        self.connected = False
        async.dispatcher.close(self)


def registerGUI():
    try:
        service.registerGUI(prop.username, prop.hpguid_host, 
                             prop.hpguid_port, os.getpid(), 'tbx')
    except Error, e:
        log.error("Unable to connect to HPLIP I/O. Please restart HPLIP and try again.")
        sys.exit(0)

def unregisterGUI():
    try:
        service.unregisterGUI(prop.username, os.getpid(), 'tbx')
    except Error, e:
        log.error("UnRegister GUI failed (code=%d). " % e.opt)


def toolboxCleanup():
    unregisterGUI()

def handleEXIT():
    if server is not None:
        try:
            server.close()
        except:
            pass

    try: 
        app.quit()
    except: 
        pass


def main(args):
    prop.prog = sys.argv[0]

    log.set_module('toolbox')

    utils.log_title('HP Device Manager', _VERSION)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'l:h', ['level=', 'help']) 

    except getopt.GetoptError:
        usage()
        sys.exit(1)

    for o, a in opts:

        if o in ('-l', '--logging'):
            log_level = a.lower().strip()
            log.set_level(log_level)

        elif o in ('-h', '--help'):
            usage()
            sys.exit(1)


    # Security: Do *not* create files that other users can muck around with
    os.umask (0077)

    # hpguid server dispatcher object
    global server
    try:
        server = hpguid_server(prop.hpguid_host) 
    except Error:
        log.error("Unable to create server object.")
        sys.exit(0)

    log.info("Listening on %s port %d" % (prop.hpguid_host, prop.hpguid_port))

    # create the main application object
    global app
    app = QApplication(sys.argv)

    global toolbox
    toolbox = devmgr4(toolboxCleanup)
    app.setMainWidget(toolbox)

    registerGUI()
    
    pid = os.getpid()
    log.debug('pid=%d' % pid)

    toolbox.show()

    atexit.register(handleEXIT)   
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    user_config = os.path.expanduser('~/.hplip.conf')
    loc = utils.loadTranslators(app, user_config)
    
    try:
        log.debug("Starting GUI loop...")
        app.exec_loop()
    except KeyboardInterrupt:
        pass
    except:
        log.exception()

    handleEXIT()
    
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
