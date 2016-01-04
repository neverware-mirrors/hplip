#!/usr/bin/env python
#

# $Revision: 1.101 $
# $Date: 2005/07/21 01:48:39 $
# $Author: dsuffield $

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
# Authors: Don Welch, Pete Parks
#
# Thanks to Henrique M. Holschuh <hmh@debian.org> for various security patches
#

# Remove in 2.3?
from __future__ import generators

_VERSION = '5.1'

# Std Lib
import sys, socket, os, os.path, signal, getopt, time
import smtplib, threading, atexit, gettext, re, xml.parsers.expat

# Local
from base.g import *
from base.codes import *
from base.msg import *
from base import async, utils, status, pml, slp, device
from base.strings import string_table

# Printing support
from prnt import cups

# Device support
from base import device

# Per user alert settings
alerts = {}

# Available guis
guis = {} # { 'username' { 'tbx' : (host, port, pid),
          #                'fax' : (host, port, pid), }, ...
          # }

# All active devices
devices = {} # { 'device_uri' : ServerDevice, ... }

inter_pat = re.compile(r"""%(.*)%""", re.IGNORECASE)

def QueryString(id, typ=0):
    id = str(id)
    #log.debug( "String query: %s" % id )

    try:
        s = string_table[id][typ]
    except KeyError:
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
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.startElement
        parser.EndElementHandler = self.endElement
        parser.CharacterDataHandler = self.charData
        parser.Parse(open(prop.models_file).read(), True)

        if not self.model_found:
            # read the untested models.xml.untested XML file if it exists
            untested_models_file = prop.models_file + '.untested'

            if os.path.exists(untested_models_file):
                parser = xml.parsers.expat.ParserCreate()
                parser.StartElementHandler = self.startElement
                parser.EndElementHandler = self.endElement
                parser.CharacterDataHandler = self.charData
                parser.Parse(open(untested_models_file).read(), True)

        if self.model_found:
            return self.model
        else:
            raise Error(ERROR_UNSUPPORTED_MODEL)


def QueryModel(model_name):
    p = ModelParser()
    model_name = model_name.replace(' ', '_').strip('_').replace('__', '_').lower()
    log.debug("Query model: %s" % model_name)
    return p.parseModels(model_name)



class hpssd_server(async.dispatcher):

    def __init__(self, ip, port):
        self.ip = ip

        if port != 0:
            self.port = port
        else:
            self.port = socket.htons(0)

        async.dispatcher.__init__(self)
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
        log.debug(str(handler))


    def __str__(self):
        return "<hpssd_server listening on %s:%d (fd=%d)>" % \
                (self.ip, self.port, self._fileno)

    def handle_close(self):
        async.dispatcher.handle_close(self)


# This handler takes care of all conversations with
# clients when hpssd is acting as a server.
# This dispatcher receives requests messages and
# and replies with result messages. It does not
# initiate sending requests.
class hpssd_handler(async.dispatcher):
    def __init__(self, conn, addr, server):
        async.dispatcher.__init__(self, sock=conn)
        self.addr = addr
        self.in_buffer = ""
        self.out_buffer = ""
        self.server = server
        self.fields = {}
        self.payload = ""
        self.signal_exit = False

        # handlers for all the messages we expect to receive
        self.handlers = {
            # Request/Reply Messages
            'probedevicesfiltered' : self.handle_probedevicesfiltered,
            'setalerts'            : self.handle_setalerts,
            'testemail'            : self.handle_test_email,
            'getgui'               : self.handle_getgui,
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
            #'printparsedgzipps'    : self.handle_printparsedgzippostscript,
            'reservechannel'       : self.handle_reserve_channel,
            'unreservechannel'     : self.handle_unreserve_channel,

            # Event Messages (no reply message)
            'event'                : self.handle_event,
            'registerguievent'     : self.handle_registerguievent,
            'unregisterguievent'   : self.handle_unregisterguievent,
            'exitevent'            : self.handle_exit,

            # Misc
            'unknown'              : self.handle_unknown,
        }

    def __str__(self):
        return "<hpssd_handler connected to %s (fd=%d)>" % \
                (self.addr, self._fileno)

    def handle_read(self):
        log.debug("Reading data on channel (%d)" % self._fileno)
        self.in_buffer = self.recv(prop.max_message_read)

        if self.in_buffer == '':
            return False

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
            log.debug(mq)
        except Error, e:
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
            typ  = self.field.get('type', pml.TYPE_UNKNOWN)
            try:
                result_code = \
                    devices[device_uri].setPML((oid, typ), self.payload)
            except Error, e:
                result_code = e.opt

        return buildResultMessage('SetPMLResult', None, result_code)


    def handle_getdynamiccounter(self):
        device_uri = self.fields.get('device-uri', '')
        result_code = self.__opendevice(device_uri)

        if result_code == ERROR_SUCCESS:
            counter = self.fields.get('counter', 0)
            try:
                data = devices[device_uri].getDynamicCounter(counter)
            except Error, e:
                result_code = e.opt
        else:
            data = 0

        return buildResultMessage('GetDynamicCounterResult', None, result_code, data)


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

        return buildResultMessage('ReadPrintChannel', None, result_code, data)


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


    #def handle_printparsedgzippostscript(self):
    #    device_uri = self.fields.get('device-uri', '')
    #    result_code = self.__opendevice(device_uri)

    #    if result_code == ERROR_SUCCESS:
    #        print_file = self.fields.get('file', '')

    #        try:
    #            devices[device_uri].printParsedGzipPostscript(print_file)
    #        except Error, e:
    #            result_code = e.opt

    #    return buildResultMessage('PrintParsedGzipPSResult', None, result_code)


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
        host = self.fields.get('hostname', 'localhost')
        port = self.fields.get('port', 0)
        pid = self.fields.get('pid', 0)
        typ = self.fields.get('type', '')

        log.debug("Registering GUI: %s %s:%d %d %s" % (username, host, port, pid, typ))

        try:
            guis[username]
        except KeyError:
            guis[username] = {}

        guis[username][typ] = (host, port, pid)

        pid_file = '/var/run/hp%s-%s.pid' % (typ, username)

        if pid != 0:
            os.umask(0133)
            file(pid_file, 'w').write('%d\n' % pid)
            os.umask(0077)
            log.debug('Wrote PID %d to %s' % (pid, pid_file))


        return ''


    # EVENT
    def handle_unregisterguievent(self):
        username = self.fields.get('username', '')
        typ = self.fields.get('type', '')

        try:
            del guis[username][typ]
        except KeyError:
            pass

        pid_file = '/var/run/hp%s-%s.pid' % (typ, username)
        log.debug("Removing file %s" % pid_file)

        try:
            os.remove(pid_file)
        except:
            pass

        return ''


    def handle_getgui(self):
        result_code, port, host = ERROR_SUCCESS, 0, ''
        username = self.fields.get('username', '')
        typ = self.fields.get('type', '')

        try:
            host, port, pid = self.get_gui(username, typ)
        except Error, e:
            result_code = ERROR_GUI_NOT_AVAILABLE
            host, port, pid = '', 0, 0
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
            except socket.error:
                result_code = ERROR_GUI_NOT_AVAILABLE
                host, port = '', 0
                self.handle_unregisterguievent()
            else:
                s.close()

        return buildResultMessage('GetGUIResult', None,
                                   result_code, {'port' : port,
                                                  'hostname' : host,
                                                  'pid' : pid,
                                                }
                                 )


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
        if EVENT_UI_FAX_MIN <= event_code <= EVENT_UI_FAX_MAX:
            typ = 'fax'

##        try:
##            gui_host, gui_port, gui_pid = self.get_gui( username, typ )
##        except Error, e:
##            pass
##        else:
        # send to all GUIs
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log.debug("Sending to all GUIs...")

        for gui in guis:
            try:
                gui_host, gui_port, gui_pid = guis[gui][typ]
            except KeyError:
                continue
            #print gui_host, gui_port, gui_pid

            log.debug("%s:%d (%d)" % (gui_host, gui_port, gui_pid))

            if typ == 'fax':
                user_alerts = {'email-alerts' : False}
            else:
                user_alerts = alerts.get(username, {})

            if not no_fwd:
                if gui_host is not None and gui_port is not None:

                    log.debug("Sending to %s GUI..." % typ)
                    try:

                        s.connect((gui_host, gui_port))
                    except socket.error:
                        log.debug("Unable to communicate with %s GUI on port %d" % (typ, gui_port))
                    else:
                        try:
                            sendEvent(s, 'EventGUI',
                                          '%s\n%s\n' % (error_string_short, error_string_long),
                                         {'job-id' : job_id,
                                           'event-code' : event_code,
                                           'event-type' : event_type,
                                           'retry-timeout' : retry_timeout,
                                           'device-uri' : device_uri,
                                         }
                                        )
                        except Error,e:
                            log.debug("Error sending event to %s GUI. (%d)" % (typ, e.opt))

                        s.close()

                else: # gui not registered or user no longer logged on
                    log.debug("Unable to find %s GUI to display error" % typ)
                    pass
            else:
                log.debug("Not sending to %s GUI, no_fwd=True" % typ)


            if user_alerts.get('email-alerts', False) and event_type == 'error':

                fromaddr = prop.username + '@localhost'
                toaddrs = user_alerts.get('email-address', 'root@localhost').split()
                smtp_server = user_alerts.get('smtp-server', 'localhost')
                msg = "From: %s\r\nTo: %s\r\n\r\n" % (fromaddr, ', '.join(toaddrs))
                msg = msg + 'Printer: %s\r\nCode: %d\r\nError: %s\r\n' % (device_uri, event_code, error_string_short)

                mt = MailThread(msg,
                                 smtp_server,
                                 fromaddr,
                                 toaddrs)
                mt.start()

        return ''


    # EVENT
    def handle_exituievent(self):
        try:
            username = self.fields['username']
            try:
                gui_host, gui_port, gui_pid = self.get_gui(username)
            except Error, e:
                raise Error(e.opt)

            log.debug("Sending to GUI...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((gui_host, gui_port))

            try:
                sendEvent(s, 'ExitGUIEvent')
            except Error, e:
                pass
            s.close()

        finally:
            pass

        return ''


    def handle_probedevicesfiltered(self):
        payload, result_code = '', ERROR_SUCCESS
        num_devices, ret_devices = 0, {}

        buses = self.fields.get('bus', 'cups,usb')
        buses = buses.split(',')
        format = self.fields.get('format', 'default')

        for b in buses:
            bus = b.lower().strip()
            if bus == 'net':
                ttl = int(self.fields.get('ttl', 4))
                timeout = int(self.fields.get('timeout', 5))

                try:
                    devices = slp.detectNetworkDevices('224.0.1.60', 427, ttl, timeout)
                except Error:
                    log.error("An error occured during network probe.")
                else:
                    for ip in devices:
                        hn = devices[ip].get('hn', '?UNKNOWN?')
                        num_devices_on_jd = devices[ip].get('num_devices', 0)
                        num_ports_on_jd = devices[ip].get('num_ports', 1)

                        if num_devices_on_jd > 0:
                            for port in range(num_ports_on_jd):
                                dev = devices[ip].get('device%d' % (port+1), '0')

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


            elif bus == 'usb':
                #try:
                fields, data, result_code =                    xmitMessage(hpiod_sock,
                                 "ProbeDevices",
                                 None,
                                 {
                                   'bus' : 'usb'
                                 }
                               )
                #except Error:
                if result_code != ERROR_SUCCESS:
                    devices = []
                else:
                    devices = [x.split(' ')[1] for x in data.splitlines()]

                for d in devices:
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

                cups_devices = {}
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

    def get_gui(self, username, typ):
        try:
            return guis[username][typ]
        except KeyError:
            raise Error(ERROR_GUI_NOT_AVAILABLE)


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
                    self.result = ERROR_SMTP_LOGIN_HELO_ERROR

                except (smtplib.SMTPAuthenticationError), e:
                    log.error("SMTP Server Login Error: Unable to authenicate with server: %s" % e)
                    self.result = ERROR_SMTP_AUTHENTICATION_ERROR
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
    log.debug("Sending EXIT to all registered GUIs")
    for username in guis:
        for typ in guis[username]:
            host, port, pid = guis[username][typ]
            log.debug("Closing %s GUI %s:%d (%d)" % (typ, host, port, pid))
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
            except socket.error:
                log.error("Unable to communicate with %s GUI on port %d" % (typ, port))
                continue
            else:
                try:
                    sendEvent(s, 'ExitGUIEvent', None, {})
                except Error,e:
                    log.warning("Unable to send event to %s GUI (%s:%s). (%d)" % (typ, host, port, e.opt))
                    continue

                pid_file = '/var/run/hp%s-%s.pid' % (typ, username)
                log.debug("Removing file %s" % pid_file)

                try:
                    os.remove(pid_file)
                except:
                    pass

                s.close()


def usage():
    formatter = utils.TextFormatter(
                (
                    {'width': 38, 'margin' : 2},
                    {'width': 38, 'margin' : 2},
                )
            )

    log.info(utils.TextFormatter.bold("""\nUsage: hpssd.py [OPTIONS]\n\n"""))

    log.info(formatter.compose((utils.TextFormatter.bold("[OPTIONS]"), "")))

    log.info(formatter.compose(("Set the logging level:",   "-l<level> or --logging=<level>")))
    log.info(formatter.compose(("",                         "<level>: none, info*, error, warn, debug (*default)")))
    log.info(formatter.compose(("Disable daemonize:",       "-x")))
    log.info(formatter.compose(("This help information:",   "-h or --help"), True))

hpiod_sock = None

def main(args):

    prop.prog = sys.argv[0]
    prop.daemonize = True
    log.set_module('hpssd')

    utils.log_title('Services and Status Daemon', _VERSION)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'l:xhp:', ['level=', 'help', 'port='])

    except getopt.GetoptError:
        usage()
        sys.exit(1)

    for o, a in opts:
        if o in ('-l', '--logging'):
            log_level = a.lower().strip()
            log.set_level(log_level)

        elif o in ('-x',):
            prop.daemonize = False

        elif o in ('-h', '--help'):
            usage()
            sys.exit(1)

        elif o in ('-p', '--port'):
            try:
                prop.hpssd_cfg_port = int(a)
            except ValueError:
                log.error('Port must be a numeric value')
                sys.exit(1)


    prop.history_size = 32

    # Lock pidfile before we muck around with system state
    # Patch by Henrique M. Holschuh <hmh@debian.org>
    utils.get_pidfile_lock('/var/run/hpssd.pid')

    # Spawn child right away so that boot up sequence
    # is as fast as possible
    if prop.daemonize:
        utils.daemonize()

    # Give hpiod enough time to startup
    # This fixes a race condition that was occuring on fast PCs
    #time.sleep(1)

    # configure the various data stores
    gettext.install('hplip')
    reInit()

    # hpssd server dispatcher object
    try:
        server = hpssd_server(prop.hpssd_host, prop.hpssd_cfg_port)
        log.debug(str(server))
    except Error, e:
        log.error("Server exited with error: %s" % e.msg)
        sys.exit(-1)

    #device.ServerDevice.setQueryFuncs( QueryModel, QueryString )
    device.ServerDevice.model_query_func = QueryModel
    device.ServerDevice.string_query_func = QueryString

    os.umask(0133)
    file('/var/run/hpssd.port', 'w').write('%d\n' % prop.hpssd_port)
    os.umask (0077)
    log.debug('port=%d' % prop.hpssd_port)
    log.info("Listening on %s port %d" % (prop.hpssd_host, prop.hpssd_port))

    global hpiod_sock
    try:
        hpiod_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hpiod_sock.connect((prop.hpiod_host, prop.hpiod_port))
    except socket.error:
        log.error("Unable to connect to hpiod.")
        sys.exit(-1)

    atexit.register(exitAllGUIs)
    signal.signal(signal.SIGHUP, handleSIGHUP)

    try:
        log.debug("Starting async loop...")
        try:
            async.loop(timeout=1.0)
        except KeyboardInterrupt:
            log.warn("Ctrl-C hit, exiting...")
        except async.ExitNow:
            log.warn("Exit message received, exiting...")
        except Exception:
            log.exception()

        log.debug("Cleaning up...")
    finally:
        os.remove('/var/run/hpssd.pid')
        os.remove('/var/run/hpssd.port')
        server.close()
        hpiod_sock.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


