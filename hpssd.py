#!/usr/bin/env python
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
# Authors: Don Welch, Pete Parks
#
# Thanks to Henrique M. Holschuh <hmh@debian.org> for various security patches
#
# ======================================================================
# Async code is Copyright 1996 by Sam Rushing
#
#                         All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software and
# its documentation for any purpose and without fee is hereby
# granted, provided that the above copyright notice appear in all
# copies and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of Sam
# Rushing not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission.
#
# SAM RUSHING DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN
# NO EVENT SHALL SAM RUSHING BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# ======================================================================
#

# Remove in 2.3?
from __future__ import generators

_VERSION = '6.0'

# Std Lib
import sys, socket, os, os.path, signal, getopt, glob, time, select
import smtplib, threading, gettext, re, xml.parsers.expat #, atexit
from errno import EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, \
     ENOTCONN, ESHUTDOWN, EINTR, EISCONN
import fcntl     

# Local
from base.g import *
from base.codes import *
from base.msg import *
from base import utils, status, pml, slp, device
from base.strings import string_table

# Printing support
from prnt import cups

# Per user alert settings
alerts = {}

# All active devices
devices = {} # { 'device_uri' : ServerDevice, ... }

inter_pat = re.compile(r"""%(.*)%""", re.IGNORECASE)

def QueryString(id, typ=0):
    id = str(id)
    #log.debug( "String query: %s" % id )

    try:
        s = string_table[id][typ]
    except KeyError:
        log.debug("String %s not found" % id)
        raise Error(ERROR_STRING_QUERY_FAILED)

    if type(s) == type(''):
        return s

    try:
        return s()
    except:
        raise Error(ERROR_STRING_QUERY_FAILED)


def initStrings():
    cycles = 0

    while True:

        found = False

        for s in string_table:
            short_string, long_string = string_table[s]
            short_replace, long_replace = short_string, long_string

            try:
                short_match = inter_pat.match(short_string).group(1)
            except (AttributeError, TypeError):
                short_match = None

            if short_match is not None:
                found = True

                try:
                    short_replace, dummy = string_table[short_match]
                except KeyError:
                    log.error("String interpolation error: %s" % short_match)

            try:
                long_match = inter_pat.match(long_string).group(1)
            except (AttributeError, TypeError):
                long_match = None

            if long_match is not None:
                found = True

                try:
                    dummy, long_replace = string_table[long_match]
                except KeyError:
                    log.error("String interpolation error: %s" % long_match)


            if found:
                string_table[s] = (short_replace, long_replace)

        if not found:
            break
        else:
            cycles +=1
            if cycles > 1000:
                break
                

class ModelParser:

    def __init__(self):
        self.model = {}
        self.cur_model = None
        self.stack = []
        self.model_found = False

    def startElement(self, name, attrs):
        global models

        if name in ('id', 'models'):
            return

        elif name == 'model':
            #self.model = {}
            self.cur_model = str(attrs['name']).lower()
            if self.cur_model == self.model_name:
                #log.debug( "Model found." )
                self.model_found = True
                self.stack = []
            else:
                self.cur_model = None

        elif self.cur_model is not None:
            self.stack.append(str(name).lower())

            if len(attrs):
                for a in attrs:
                    self.stack.append(str(a).lower())

                    try:
                        i = int(attrs[a])
                    except ValueError:
                        i = str(attrs[a])

                    self.model[str('-'.join(self.stack))] = i
                    self.stack.pop()

    def endElement(self, name):
        global models
        if name == 'model':
            pass
        elif name in ('id', 'models'):
            return
        else:
            if self.cur_model is not None:
                self.stack.pop()


    def charData(self, data):
        data = str(data).strip()

        if data and self.model is not None and \
            self.cur_model is not None and \
            self.stack:

            try:
                i = int(data)
            except ValueError:
                i = str(data)

            self.model[str('-'.join(self.stack))] = i

    def parseModels(self, model_name):
        self.model_name = model_name

        for g in [prop.xml_dir, os.path.join(prop.xml_dir, 'unreleased')]:

            if os.path.exists(g):
                log.debug("Searching directory: %s" % g)

                for f in glob.glob(g + "/*.xml"):
                    log.debug("Searching file: %s" % f)
                    parser = xml.parsers.expat.ParserCreate()
                    parser.StartElementHandler = self.startElement
                    parser.EndElementHandler = self.endElement
                    parser.CharacterDataHandler = self.charData
                    parser.Parse(open(f).read(), True)

                    if self.model_found:
                        log.debug("Found")
                        return self.model

        log.error("Not found")
        raise Error(ERROR_UNSUPPORTED_MODEL)



def QueryModel(model_name):
    p = ModelParser()
    model_name = model_name.replace(' ', '_').strip('_').replace('__', '_').replace('~','').lower()
    log.debug("Query model: %s" % model_name)
    return p.parseModels(model_name)

socket_map = {}
loopback_trigger = None

def loop( timeout=1.0, sleep_time=0.1 ):
    while socket_map:
        r = []; w = []; e = []
        for fd, obj in socket_map.items():
            if obj.readable():
                r.append( fd )
            if obj.writable():
                w.append( fd )
        if [] == r == w == e:
            time.sleep( timeout )
        else:
            try:
                r,w,e = select.select( r, w, e, timeout )
            except select.error, err:
                if err[0] != EINTR:
                    raise Error( ERROR_INTERNAL )
                r = []; w = []; e = []

        for fd in r:
            try:
                obj = socket_map[ fd ]
            except KeyError:
                continue

            try:
                obj.handle_read_event()
            except Error, e:
                obj.handle_error( e )

        for fd in w:
            try:
                obj = socket_map[ fd ]
            except KeyError:
                continue

            try:
                obj.handle_write_event()
            except Error, e:
                obj.handle_error( e )

            time.sleep( sleep_time )


class dispatcher:
    connected = False
    accepting = False
    closing = False
    addr = None

    def __init__ (self, sock=None ):
        if sock:
            self.set_socket( sock ) 
            self.socket.setblocking( 0 )
            self.connected = True
            try:
                self.addr = sock.getpeername()
            except socket.error:
                # The addr isn't crucial
                pass
        else:
            self.socket = None

    def add_channel ( self ): 
        global socket_map
        socket_map[ self._fileno ] = self

    def del_channel( self ): 
        global socket_map
        fd = self._fileno
        if socket_map.has_key( fd ):
            del socket_map[ fd ]

    def create_socket( self, family, type ):
        self.family_and_type = family, type
        self.socket = socket.socket (family, type)
        self.socket.setblocking( 0 )
        self._fileno = self.socket.fileno()
        self.add_channel()

    def set_socket( self, sock ): 
        self.socket = sock
        self._fileno = sock.fileno()
        self.add_channel()

    def set_reuse_addr( self ):
        try:
            self.socket.setsockopt (
                socket.SOL_SOCKET, socket.SO_REUSEADDR,
                self.socket.getsockopt (socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR) | 1
                )
        except socket.error:
            pass

    def readable (self):
        return True

    def writable (self):
        return True

    def listen (self, num):
        self.accepting = True
        return self.socket.listen( num )

    def bind( self, addr ):
        self.addr = addr
        return self.socket.bind( addr )

    def connect( self, address ):
        self.connected = False
        err = self.socket.connect_ex( address )
        if err in ( EINPROGRESS, EALREADY, EWOULDBLOCK ):
            return
        if err in (0, EISCONN):
            self.addr = address
            self.connected = True
            self.handle_connect()
        else:
            raise socket.error, err

    def accept (self):
        try:
            conn, addr = self.socket.accept()
            return conn, addr
        except socket.error, why:
            if why[0] == EWOULDBLOCK:
                pass
            else:
                raise socket.error, why

    def send (self, data):
        try:
            result = self.socket.send( data )
            return result
        except socket.error, why:
            if why[0] == EWOULDBLOCK:
                return 0
            else:
                raise socket.error, why
            return 0

    def recv( self, buffer_size ):
        try:
            data = self.socket.recv (buffer_size)
            if not data:
                self.handle_close()
                return ''
            else:
                return data
        except socket.error, why:
            if why[0] in [ECONNRESET, ENOTCONN, ESHUTDOWN]:
                self.handle_close()
                return ''
            else:
                raise socket.error, why

    def close (self):
        self.del_channel()
        self.socket.close()

    # cheap inheritance, used to pass all other attribute
    # references to the underlying socket object.
    #def __getattr__ (self, attr):
    #    return getattr (self.socket, attr)

    def handle_read_event( self ):
        if self.accepting:
            if not self.connected:
                self.connected = True
            self.handle_accept()
        elif not self.connected:
            self.handle_connect()
            self.connected = True
            self.handle_read()
        else:
            self.handle_read()

    def handle_write_event( self ):
        if not self.connected:
            self.handle_connect()
            self.connected = True
        self.handle_write()

    def handle_expt_event( self ):
        self.handle_expt()

    def handle_error( self, e ):
        log.error( "Error processing request." )
        raise Error(ERROR_INTERNAL)

    def handle_expt( self ):
        raise Error

    def handle_read( self ):
        raise Error

    def handle_write( self ):
        raise Error

    def handle_connect( self ):
        raise Error

    def handle_accept( self ):
        raise Error

    def handle_close( self ):
        self.close()


class file_wrapper:
    def __init__(self, fd):
        self.fd = fd

    def recv(self, *args):
        return os.read(self.fd, *args)

    def send(self, *args):
        return os.write(self.fd, *args)

    read = recv
    write = send

    def close(self):
        os.close(self.fd)

    def fileno(self):
        return self.fd


class file_dispatcher(dispatcher):

    def __init__(self, fd):
        dispatcher.__init__(self, None)
        self.connected = True
        self.set_file(fd)
        flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, flags)

    def set_file(self, fd):
        self._fileno = fd
        self.socket = file_wrapper(fd)
        self.add_channel()    


class trigger(file_dispatcher):
        def __init__(self):
            r, w = os.pipe()
            self.trigger = w
            file_dispatcher.__init__(self, r)
            self.send_events = False

        def readable(self):
            return 1

        def writable(self):
            return 0

        def handle_connect(self):
            pass

        def pull_trigger(self):
            os.write(self.trigger, '.')

        def handle_read (self):
            self.recv(8192)


class hpssd_server(dispatcher):

    def __init__(self, ip, port):
        self.ip = ip
        self.send_events = False

        if port != 0:
            self.port = port
        else:
            self.port = socket.htons(0)

        dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()

        try:
            self.bind((ip, port))
        except socket.error:
            raise Error(ERROR_UNABLE_TO_BIND_SOCKET)

        prop.hpssd_port = self.port = self.socket.getsockname()[1]
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
        handler = hpssd_handler(conn, addr, self)

    def handle_close(self):
        dispatcher.handle_close(self)


class hpssd_handler(dispatcher):
    def __init__(self, conn, addr, server):
        dispatcher.__init__(self, sock=conn)
        self.addr = addr
        self.in_buffer = ""
        self.out_buffer = ""
        self.server = server
        self.fields = {}
        self.payload = ""
        self.signal_exit = False

        self.send_events = False 
        self.username = ''

        # handlers for all the messages we expect to receive
        self.handlers = {
            # Request/Reply Messages
            'probedevicesfiltered' : self.handle_probedevicesfiltered,
            'setalerts'            : self.handle_setalerts,
            'testemail'            : self.handle_test_email,
            'opendevice'           : self.handle_opendevice,
            'closedevice'          : self.handle_closedevice,
            'openchannel'          : self.handle_openchannel,
            'closechannel'         : self.handle_closechannel,
            'querydevice'          : self.handle_querydevice,
            'deviceid'             : self.handle_deviceid,
            'querymodel'           : self.handle_querymodel, # By device URI
            'modelquery'           : self.handle_modelquery, # By model (backwards compatibility)
            'getpml'               : self.handle_getpml,
            'setpml'               : self.handle_setpml,
            'getdynamiccounter'    : self.handle_getdynamiccounter,
            'readprintchannel'     : self.handle_readprintchannel,
            'writeprintchannel'    : self.handle_writeprintchannel,
            'writeembeddedpml'     : self.handle_writeembeddedpml,
            'queryhistory'         : self.handle_queryhistory,
            'querystring'          : self.handle_querystring,
            'reservechannel'       : self.handle_reserve_channel,
            'unreservechannel'     : self.handle_unreserve_channel,

            # Event Messages (no reply message)
            'event'                : self.handle_event,
            'registerguievent'     : self.handle_registerguievent, # register for events
            'unregisterguievent'   : self.handle_unregisterguievent,
            'exitevent'            : self.handle_exit,

            # Misc
            'unknown'              : self.handle_unknown,
        }


    def handle_read(self):
        log.debug("Reading data on channel (%d)" % self._fileno)
        self.in_buffer = self.recv(prop.max_message_read)

        if self.in_buffer == '':
            return False

        log.debug(repr(self.in_buffer))

        remaining_msg = self.in_buffer

        while True:
            try:
                self.fields, self.payload, remaining_msg = parseMessage(remaining_msg)
            except Error, e:
                err = e.opt
                log.debug(repr(self.in_buffer))
                log.warn("Message parsing error: %s (%d)" % (e.msg, err))
                self.out_buffer = self.handle_unknown(err)
                log.debug(self.out_buffer)
                return True

            msg_type = self.fields.get('msg', 'unknown').lower()
            log.debug("Handling: %s %s %s" % ("*"*60, msg_type, "*"*60))
            log.debug(repr(self.in_buffer))

            try:
                self.out_buffer = self.handlers.get(msg_type, self.handle_unknown)()
            except Error:
                log.error("Unhandled exception during processing:")
                log.exception()

            if not remaining_msg:
                break

        return True

    def handle_unknown(self, err=ERROR_INVALID_MSG_TYPE):
        return buildResultMessage('MessageError', None, err)


    def handle_write(self):
        log.debug("Sending data on channel (%d)" % self._fileno)
        log.debug(repr(self.out_buffer))
        sent = self.send(self.out_buffer)
        self.out_buffer = self.out_buffer[sent:]

        if self.signal_exit:
            self.handle_close()


    def __checkdevice(self, device_uri):
        try:
            devices[device_uri]
        except KeyError:
            log.debug("New device: %s" % device_uri)

            try:
                devices[device_uri] = device.ServerDevice(device_uri, hpiod_sock,
                                                           QueryModel, QueryString)
            except Error, e:
                log.debug("New device init failed.")
                return e.opt

        return ERROR_SUCCESS


    def __opendevice(self, device_uri):
        log.debug("Open: %s" % device_uri)
        result_code = self.__checkdevice(device_uri)

        if result_code == ERROR_SUCCESS:
            try:
                devices[device_uri].open()
            except Error, e:
                log.error("Open failed for device: %s" % device_uri)
                result_code = e.opt

        return result_code


    def __closedevice(self, device_uri):
        log.debug("Close: %s" % device_uri)
        try:
            devices[device_uri]
        except:
            pass
        else:
            devices[device_uri].close()


    def handle_queryhistory(self):
        device_uri = self.fields.get('device-uri', '')
        payload = ''
        result_code = self.__checkdevice(device_uri)

        if result_code == ERROR_SUCCESS:
            for h in devices[device_uri].history.get():
                payload = '\n'.join([payload, ','.join([str(x) for x in h])])

        return buildResultMessage('QueryHistoryResult', payload, result_code)


    def handle_opendevice(self):
        device_uri = self.fields.get('device-uri', '')
        return buildResultMessage('OpenDeviceResult', None,
            self.__opendevice(device_uri))


    def handle_closedevice(self):
        device_uri = self.fields.get('device-uri', '')
        self.__closedevice(device_uri)
        return buildResultMessage('CloseDeviceResult', None, ERROR_SUCCESS)


    def handle_openchannel(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)

        if result_code == ERROR_SUCCESS:
            service_name = self.fields.get('service-name', '')
            try:
                devices[device_uri].openChannel(service_name)
            except Error, e:
                result_code = e.opt

        return buildResultMessage('OpenChannelResult', None, result_code)


    def handle_reserve_channel(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__checkdevice(device_uri)

        if result_code == ERROR_SUCCESS:
            service_name = self.fields.get('service-name', '')
            try:
                devices[device_uri].reserveChannel(service_name)
            except Error, e:
                result_code = e.opt

        return buildResultMessage('ReserveChannelResult', None, result_code)


    def handle_unreserve_channel(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__checkdevice(device_uri)

        if result_code == ERROR_SUCCESS:
            service_name = self.fields.get('service-name', '')
            try:
                devices[device_uri].unreserveChannel(service_name)
            except Error, e:
                result_code = e.opt

        return buildResultMessage('UnReserveChannelResult', None, result_code)


    def handle_closechannel(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)

        if result_code == ERROR_SUCCESS:
            service_name = self.fields.get('service-name', '')
            try:
                devices[device_uri].closeChannel(service_name)
            except Error, e:
                result_code = e.opt

        return buildResultMessage('CloseChannelResult', None, result_code)


    def handle_deviceid(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)
        if result_code == ERROR_SUCCESS:
            try:
                devices[device_uri].getDeviceID()
            except Error, e:
                result_code = e.opt

        return buildResultMessage('CloseChannelResult', \
            devices[device_uri].raw_deviceID, result_code)


    def handle_querydevice(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)

        try:
            devices[device_uri].queryDevice()
        except Error, e:
            result_code = e.opt

        return buildResultMessage('QueryDeviceResult', None, result_code, \
            devices[device_uri].dq)


    def handle_querymodel(self): # By device URI
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__checkdevice(device_uri) # Don't open

        if result_code == ERROR_SUCCESS:
            mq = devices[device_uri].mq
        else:
            mq = {}

        log.debug(mq)

        return buildResultMessage('QueryModelResult', None, result_code, mq)


    def handle_modelquery(self): # By model
        model = self.fields.get('model', '')

        result_code = ERROR_SUCCESS
        try:
            mq = QueryModel(model)
        except Error, e:
            mq = {}
            result_code = e.opt
            mq = {}

        log.debug(mq)

        return buildResultMessage('ModelQueryResult', None, result_code, mq)

    def handle_getpml(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)

        if result_code == ERROR_SUCCESS:
            oid = self.fields.get('oid', '')
            typ  = self.fields.get('type', pml.TYPE_UNKNOWN)
            int_size = self.fields.get('int-size', pml.INT_SIZE_INT)
            try:
                result_code, data = \
                    devices[device_uri].getPML((oid, typ), int_size)
            except Error, e:
                result_code = e.opt
        else:
            data = None

        return buildResultMessage('GetPMLResult', data, result_code)


    def handle_setpml(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)

        if result_code == ERROR_SUCCESS:
            oid = self.fields.get('oid', '')
            typ  = self.fields.get('type', pml.TYPE_UNKNOWN)
            try:
                result_code = \
                    devices[device_uri].setPML((oid, typ), self.payload)
            except Error, e:
                result_code = e.opt

        return buildResultMessage('SetPMLResult', None, result_code)


    def handle_getdynamiccounter(self):
        device_uri = self.fields.get('device-uri', '')
        #convert_to_int = self.fields.get('convert-int', True)
        result_code = self.__opendevice(device_uri)

        if result_code == ERROR_SUCCESS:
            counter = self.fields.get('counter', 0)
            try:
                data = devices[device_uri].getDynamicCounter(counter, False)
            except Error, e:
                result_code = e.opt
        else:
            data = 0

        return buildResultMessage('GetDynamicCounterResult', data, result_code)


    def handle_readprintchannel(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)

        if result_code == ERROR_SUCCESS:
            try:
                data = devices[device_uri].readPrint()
            except Error, e:
                result_code = e.opt
        else:
            data = ''

        return buildResultMessage('ReadPrintChannel', data, result_code)


    def handle_writeprintchannel(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)

        if result_code == ERROR_SUCCESS:
            try:
                devices[device_uri].writePrint(self.payload)
            except Error, e:
                result_code = e.opt

        return buildResultMessage('WritePrintChannelResult', None, result_code)


    def handle_writeembeddedpml(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)

        if result_code == ERROR_SUCCESS:
            oid = self.fields.get('oid', '')
            typ  = self.fields.get('type', pml.TYPE_UNKNOWN)
            direct = bool(self.fields.get('direct', 1))

            try:
                devices[device_uri].writeEmbeddedPML((oid, typ), self.payload, direct)
            except Error, e:
                result_code = e.opt

        return buildResultMessage('WriteEmbeddedPMLResult', None, result_code)


    def handle_setalerts(self):
        result_code = ERROR_SUCCESS
        username = self.fields.get('username', '')
        email_alerts = self.fields.get('email-alerts', False)
        email_address = self.fields.get('email-address', '')
        smtp_server = self.fields.get('smtp-server', '')

        alerts[username] = {'email-alerts'  : email_alerts,
                               'email-address' : email_address,
                               'smtp-server'   : smtp_server,
                              }

        return buildResultMessage('SetAlertsResult', None, result_code)


    # EVENT
    def handle_registerguievent(self):
        username = self.fields.get('username', '')
        self.username = username
        typ = 'tbx'

        log.debug("Registering GUI for events: %s" % username)
        self.send_events = True
        return ''

    # EVENT
    def handle_unregisterguievent(self):
        username = self.fields.get('username', '')
        self.send_events = False
        return ''


    def handle_test_email(self):
        result_code = ERROR_SUCCESS
        try:
            to_address = self.fields['email-address']
            smtp_server = self.fields['smtp-server']
            username = self.fields['username']
            server_pass = self.fields['server-pass']
            from_address = '@localhost'

            try:
                if username and server_pass:
                    from_address = username + "@" + smtp_server
                else:
                    stringName = socket.gethostname()
                    from_address = stringName + from_address
                log.debug("Return address: %s" % from_address)
            except Error:
                log.debug("Can't open socket")
                result_code = ERROR_TEST_EMAIL_FAILED
                raise Error(ERROR_TEST_EMAIL_FAILED)

            msg = "From: %s\r\nTo: %s\r\n" % (from_address, to_address)
            try:


                subject_string = QueryString('email_test_subject')
                log.debug("Subject (%s)" % subject_string)
            except Error:
                subject_string = None
                result_code = ERROR_TEST_EMAIL_FAILED
                raise Error(ERROR_TEST_EMAIL_FAILED)


            try:
                message_string = QueryString('email_test_message')
                log.debug("Message (%s)" % message_string)
            except Error:
                message_string = None
                result_code = ERROR_TEST_EMAIL_FAILED
                raise Error(ERROR_TEST_EMAIL_FAILED)

            # Use NULL address for envelope sender
            from_address = '<>'

            msg = ''.join([msg, subject_string, '\r\n\r\n', message_string])

            try:
                mt = MailThread(msg, smtp_server, from_address, to_address, username, server_pass)
                mt.start()
                mt.join() # wait for thread to finish
                result_code = mt.result # get the result
                log.debug("MailThread had an exception (%s)" %  str(result_code))
            except Error:
                log.debug("MailThread TRY: had an exception (%s)" %  str(result_code))
                result_code = ERROR_TEST_EMAIL_FAILED
                raise Error(ERROR_TEST_EMAIL_FAILED)

        except Error, e:
            log.error("Error: %d", e.opt)

        log.debug("hpssd.py::handle_email_test::Current error code: %s" % str(result_code))
        return buildResultMessage('TestEmailResult', None, result_code)


    def handle_querystring(self):
        payload, result_code = '', ERROR_SUCCESS
        string_id = self.fields['string-id']
        try:
            payload = QueryString(string_id)
        except Error:
            log.error("String query failed for id %s" % string_id)
            payload = None
            result_code = ERROR_STRING_QUERY_FAILED

        return buildResultMessage('QueryStringResult', payload, result_code)

    def handle_errorstringquery(self):
        payload, result_code = '', ERROR_STRING_QUERY_FAILED
        try:
            error_code = self.fields['error-code']

            payload = QueryString(str(error_code))
            result_code = ERROR_SUCCESS
        except Error:
            result_code = ERROR_STRING_QUERY_FAILED

        return buildResultMessage('ErrorStringQueryResult', payload, result_code)


    # EVENT
    def handle_event(self):
        gui_port, gui_host = None, None
        f = self.fields
        event_code, event_type = f['event-code'], f['event-type']
        log.debug("code (type): %d (%s)" % (event_code, event_type))

        try:
            error_string_short = QueryString(str(event_code), 0)
        except Error:
            error_string_short = ''

        try:
            error_string_long = QueryString(str(event_code), 1)
        except Error:
            error_string_long = ''

        log.debug("short: %s" % error_string_short)
        log.debug("long: %s" % error_string_long)
        job_id = f.get('job-id', 0)

        try:
            username = f['username']
        except KeyError:
            if job_id == 0:
                username = prop.username
            else:
                jobs = cups.getAllJobs()
                for j in jobs:
                    if j.id == job_id:
                        username = j.user
                        break
                else:
                    username = prop.username


        no_fwd = f.get('no-fwd', False)
        log.debug("username (jobid): %s (%d)" % (username, job_id))
        retry_timeout = f.get('retry-timeout', 0)
        device_uri = f.get('device-uri', '')
        self.__checkdevice(device_uri)
        devices[device_uri].createHistory(event_code, job_id, username)

        typ = 'tbx'
        if EVENT_FAX_MIN <= event_code <= EVENT_FAX_MAX:
            typ = 'fax'

        if typ == 'fax':
            user_alerts = {'email-alerts' : False}
        else:
            user_alerts = alerts.get(username, {})        

        pull = False
        if not no_fwd:
            for handler in socket_map:
                handler_obj = socket_map[handler]

                if handler_obj.send_events:
                    print self, self.username
                    log.debug("Sending event to client for user %s" % self.username)
                    pull = True

                    handler_obj.out_buffer = \
                        buildMessage('EventGUI', 
                            '%s\n%s\n' % (error_string_short, error_string_long),
                            {'job-id' : job_id,
                             'event-code' : event_code,
                             'event-type' : event_type,
                             'retry-timeout' : retry_timeout,
                             'device-uri' : device_uri,
                            })

            if pull:
                loopback_trigger.pull_trigger()

            if user_alerts.get('email-alerts', False) and event_type == 'error':

                fromaddr = prop.username + '@localhost'
                toaddrs = user_alerts.get('email-address', 'root@localhost').split()
                smtp_server = user_alerts.get('smtp-server', 'localhost')
                msg = "From: %s\r\nTo: %s\r\n\r\n" % (fromaddr, ', '.join(toaddrs))
                msg = msg + 'Printer: %s\r\nCode: %d\r\nError: %s\r\n' % (device_uri, event_code, error_string_short)

                mt = MailThread(msg,
                                smtp_server,
                                fromaddr,
                                toaddrs,
                                prop.username,
                                '')
                mt.start()

        return ''


    def handle_probedevicesfiltered(self):
        payload, result_code = '', ERROR_SUCCESS
        num_devices, ret_devices = 0, {}

        buses = self.fields.get('bus', 'cups,usb,par')
        buses = buses.split(',')
        format = self.fields.get('format', 'default')

        for b in buses:
            bus = b.lower().strip()
            if bus == 'net':
                ttl = int(self.fields.get('ttl', 4))
                timeout = int(self.fields.get('timeout', 5))

                try:
                    detected_devices = slp.detectNetworkDevices('224.0.1.60', 427, ttl, timeout)
                except Error:
                    log.error("An error occured during network probe.")
                else:
                    for ip in detected_devices:
                        hn = detected_devices[ip].get('hn', '?UNKNOWN?')
                        num_devices_on_jd = detected_devices[ip].get('num_devices', 0)
                        num_ports_on_jd = detected_devices[ip].get('num_ports', 1)

                        if num_devices_on_jd > 0:
                            for port in range(num_ports_on_jd):
                                dev = detected_devices[ip].get('device%d' % (port+1), '0')

                                if dev is not None and dev != '0':
                                    device_id = device.parseDeviceID(dev)
                                    model = device_id.get('MDL', '?UNKNOWN?'). \
                                        strip().replace('  ', '_').replace(' ', '_'). \
                                        replace('/', '_')

                                    if num_ports_on_jd == 1:
                                        device_uri = 'hp:/net/%s?ip=%s' % (model, ip)
                                    else:
                                        device_uri = 'hp:/net/%s?ip=%s&port=%d' % (model, ip, (port+1))

                                    device_filter = self.fields.get('filter', 'none')

                                    if device_filter in ('none', 'print'):
                                        include = True
                                    else:
                                        include = True

                                        try:

                                            fields = QueryModel(model)
                                        except Error:
                                            continue

                                        for f in device_filter.split(','):
                                            filter_type = int(fields.get('%s-type' % f.lower().strip(), 0))
                                            if filter_type == 0:
                                                include = False
                                                break

                                    if include:
                                        ret_devices[device_uri] = (model, hn)


            elif bus in ('usb', 'par'):
                fields, data, result_code = \
                    xmitMessage(hpiod_sock,
                                 "ProbeDevices",
                                 None,
                                 {
                                   'bus' : bus,
                                 }
                               )
                if result_code != ERROR_SUCCESS:
                    detected_devices = []
                else:
                    detected_devices = [x.split(' ')[1] for x in data.splitlines()]

                for d in detected_devices:
                    try:
                        back_end, is_hp, bus, model, serial, dev_file, host, port = \
                            device.parseDeviceURI(d)
                    except Error:
                        continue

                    if is_hp:

                        device_filter = self.fields.get('filter', 'none')

                        if device_filter in ('none', 'print'):
                            include = True
                        else:
                            include = True

                            try:

                                fields = QueryModel(model)
                            except Error:
                                continue

                            for f in device_filter.split(','):
                                filter_type = int(fields.get('%s-type' % f.lower().strip(), 0))
                                if filter_type == 0:
                                    include = False
                                    break

                        if include:
                            ret_devices[d] = (model, '')

            elif bus == 'cups':

                #cups_devices = {}
                cups_printers = cups.getPrinters()
                x = len(cups_printers)

                for p in cups_printers:
                    device_uri = p.device_uri

                    if p.device_uri != '':

                        device_filter = self.fields.get('filter', 'none')

                        try:
                            back_end, is_hp, bs, model, serial, dev_file, host, port = \
                                device.parseDeviceURI(device_uri)
                        except Error:
                            log.warning("Inrecognized URI: %s" % device_uri)
                            continue

                        if not is_hp:
                            continue

                        if device_filter in ('none', 'print'):
                            include = True
                        else:
                            include = True

                            try:

                                fields = QueryModel(model)
                            except Error:
                                continue

                            for f in device_filter.split(','):
                                filter_type = int(fields.get('%s-type' % f.lower().strip(), 0))
                                if filter_type == 0:
                                    include = False
                                    break

                        if include:
                            ret_devices[device_uri] = (model, '')


        for d in ret_devices:
            num_devices += 1

            if format == 'default':
                payload = ''.join([payload, d, ',', ret_devices[d][0], '\n'])
            else:
                if ret_devices[d][1] != '':
                    payload = ''.join([payload, 'direct ', d, ' "HP ', ret_devices[d][0], '" "', ret_devices[d][1], '"\n'])
                else:
                    payload = ''.join([payload, 'direct ', d, ' "HP ', ret_devices[d][0], '" "', d, '"\n'])


        return buildResultMessage('ProbeDevicesFilteredResult', payload,
                                   result_code, {'num-devices' : num_devices})

    # EVENT
    def handle_exit(self):
        self.signal_exit = True
        return ''

    def handle_messageerror(self):
        return ''

    def writable(self):
        return not ((len(self.out_buffer) == 0)
                     and self.connected)


    def handle_close(self):
        log.debug("closing channel (%d)" % self._fileno)
        self.connected = False
        self.close()


class MailThread(threading.Thread):
    def __init__(self, message, smtp_server, from_addr, to_addr_list, username, server_pass):
        threading.Thread.__init__(self)
        self.message = message
        self.smtp_server = smtp_server
        self.to_addr_list = to_addr_list
        self.from_addr = from_addr
        self.result = ERROR_SUCCESS
        self.username = username
        self.server_pass = server_pass

    def run(self):
        log.debug("Starting Mail Thread...")
        try:
            try:
                log.debug("Attempting to connect to SMTP server: %s:%d" % (self.smtp_server, smtplib.SMTP_PORT))
                server = smtplib.SMTP(self.smtp_server, smtplib.SMTP_PORT, 'localhost')
            except:
                self.result = ERROR_SMTP_CONNECT_ERROR
                return
            server.set_debuglevel(True)
            if self.username and self.server_pass:
                try:
                    server.starttls();
                    server.login(self.username, self.server_pass)
                except (smtplib.SMTPHeloError, smtplib.SMTPException), e:
                    log.error("SMTP Server Login Error: Unable to connect to server: %s" % e)
                    self.result = ERROR_SMTP_HELO_ERROR

                except (smtplib.SMTPAuthenticationError), e:
                    log.error("SMTP Server Login Error: Unable to authenicate with server: %s" % e)
                    self.result = ERROR_SMTP_CONNECT_ERROR
        except smtplib.SMTPConnectError, e:
            log.error("SMTP Error: Unable to connect to server: %s" % e)
            self.result = ERROR_SMTP_CONNECT_ERROR

        try:
            server.sendmail(self.from_addr, self.to_addr_list, self.message)
            log.debug("hpssd.py::MailThread::Current error code: %s" % str(self.result))
        except smtplib.SMTPRecipientsRefused, e:
            log.error("SMTP Errror: All recepients refused: %s" % e)
            self.result = ERROR_SMTP_RECIPIENTS_REFUSED
        except smtplib.SMTPHeloError, e:
            log.error("SMTP Errror: Invalid server response to HELO command: %s" % e)
            self.result = ERROR_SMTP_HELO_ERROR
        except smtplib.SMTPSenderRefused, e:
            log.error("SMTP Errror: Recepient refused: %s" % e)
            self.result = ERROR_SMTP_SENDER_REFUSED
        except smtplib.SMTPDataError, e:
            log.error("SMTP Errror: Unknown error: %s" % e)
            self.result = ERROR_SMTP_DATA_ERROR

        server.quit()
        log.debug("Exiting mail thread")


def reInit():
    initStrings()


def handleSIGHUP(signo, frame):
    log.info("SIGHUP")
    reInit()


def exitAllGUIs():
    pass

def usage():
    formatter = utils.usage_formatter()
    log.info(utils.bold("""\nUsage: hpssd.py [OPTIONS]\n\n""" ))
    utils.usage_options()
    utils.usage_logging(formatter)
    log.info(formatter.compose(("Disable daemonize:", "-x")))
    log.info(formatter.compose(("Port to listen on:", "-p<port> or --port=<port> (overrides value in /etc/hp/hplip.conf)")))
    utils.usage_help(formatter, True)
    sys.exit(0)


hpiod_sock = None

def main(args):
    prop.prog = sys.argv[0]
    prop.daemonize = True
    utils.log_title('Services and Status Daemon', _VERSION)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'l:xhp:', ['level=', 'help', 'port='])

    except getopt.GetoptError:
        usage()

    for o, a in opts:
        if o in ('-l', '--logging'):
            log_level = a.lower().strip()
            log.set_level(log_level)

        elif o in ('-x',):
            prop.daemonize = False

        elif o in ('-h', '--help'):
            usage()

        elif o in ('-p', '--port'):
            try:
                prop.hpssd_cfg_port = int(a)
            except ValueError:
                log.error('Port must be a numeric value')
                usage()


    prop.history_size = 32

    # Lock pidfile before we muck around with system state
    # Patch by Henrique M. Holschuh <hmh@debian.org>
    utils.get_pidfile_lock(os.path.join(prop.run_dir, 'hpssd.pid'))

    # Spawn child right away so that boot up sequence
    # is as fast as possible
    if prop.daemonize:
        utils.daemonize()

    log.set_module('hpssd')

    # configure the various data stores
    gettext.install('hplip')
    reInit()

    # hpssd server dispatcher object
    try:
        server = hpssd_server(prop.hpssd_host, prop.hpssd_cfg_port)
        #log.debug(str(server))
    except Error, e:
        log.error("Server exited with error: %s" % e.msg)
        sys.exit(-1)

    global loopback_trigger
    try:
        loopback_trigger = trigger()
    except Error, e:
        log.error("Server exited with error: %s" % e.msg)
        sys.exit(-1)


    #device.ServerDevice.setQueryFuncs( QueryModel, QueryString )
    device.ServerDevice.model_query_func = QueryModel
    device.ServerDevice.string_query_func = QueryString

    os.umask(0133)
    file(os.path.join(prop.run_dir, 'hpssd.port'), 'w').write('%d\n' % prop.hpssd_port)
    os.umask (0077)
    log.debug('port=%d' % prop.hpssd_port)
    log.info("Listening on %s:%d" % (prop.hpssd_host, prop.hpssd_port))


    global hpiod_sock
    try:
        hpiod_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hpiod_sock.connect((prop.hpiod_host, prop.hpiod_port))
    except socket.error:
        log.error("Unable to connect to hpiod.")
        sys.exit(-1)

    ##atexit.register(exitAllGUIs)
    signal.signal(signal.SIGHUP, handleSIGHUP)

    try:
        log.debug("Starting async loop...")
        try:
            loop(timeout=0.5)
        except KeyboardInterrupt:
            log.warn("Ctrl-C hit, exiting...")
        except Exception:
            log.exception()

        log.debug("Cleaning up...")
    finally:
        os.remove(os.path.join(prop.run_dir, 'hpssd.pid'))
        os.remove(os.path.join(prop.run_dir, 'hpssd.port'))
        server.close()
        hpiod_sock.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


