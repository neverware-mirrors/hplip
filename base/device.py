#!/usr/bin/env python
#
# $Revision: 1.105 $
# $Date: 2005/11/22 00:53:34 $
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

# Std Lib
import socket
import re
import gzip
import os.path
import time
import struct

#from pprint import pprint

# Local
from g import *
from codes import *
import msg, utils, status, pml, slp
from prnt import pcl, ldl, cups

DEFAULT_PROBE_BUS = 'usb,par,cups'
VALID_BUSES = ('par', 'net', 'cups', 'usb', 'bt', 'fw')
DEFAULT_FILTER = 'none'
VALID_FILTERS = ('none', 'print', 'scan', 'fax', 'pcard', 'copy')

pat_deviceuri = re.compile(r"""(.*?):/(.*?)/(\S*?)\?(?:serial=(\S*)|device=(\S*)|ip=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[^&]*))(?:&port=(\d))?""", re.IGNORECASE)

# Pattern to check for ; at end of CTR fields
# Note: If ; not present, CTR value is invalid
pat_dynamic_ctr = re.compile(r"""CTR:\d*\s.*;""", re.IGNORECASE)


def getInteractiveDeviceURI(bus='cups,usb,par', filter='none'):
    bus = bus.lower()
    probed_devices = probeDevices(bus=bus, filter=filter)
    cups_printers = cups.getPrinters()
    log.debug(probed_devices)
    log.debug(cups_printers)
    max_deviceid_size, x, devices = 0, 0, {}

    for d in probed_devices:
        printers = []

        for p in cups_printers:
            if p.device_uri == d:
                printers.append(p.name)

        devices[x] = (d, printers)
        x += 1
        max_deviceid_size = max(len(d), max_deviceid_size)

    if x == 0:
        log.error("No devices found.")
        raise Error(ERROR_NO_PROBED_DEVICES_FOUND)

    elif x == 1:
        log.info(utils.bold("Using device: %s" % devices[0][0]))
        return devices[0][0]

    else:
        log.info(utils.bold("\nChoose device from probed devices connected on bus(es): %s:\n" % bus))
        formatter = utils.TextFormatter(
                (
                    {'width': 4},
                    {'width': max_deviceid_size, 'margin': 2},
                    {'width': 80-max_deviceid_size-8, 'margin': 2},
                )
            )
        log.info(formatter.compose(("Num.", "Device-URI", "CUPS printer(s)")))
        log.info(formatter.compose(('-'*4, '-'*(max_deviceid_size), '-'*(80-max_deviceid_size-10))))

        for y in range(x):
            log.info(formatter.compose((str(y), devices[y][0], ', '.join(devices[y][1]))))

        while 1:
            user_input = raw_input(utils.bold("\nEnter number 0...%d for device (q=quit) ?" % (x-1)))

            if user_input == '':
                log.warn("Invalid input - enter a numeric value or 'q' to quit.")
                continue

            if user_input.strip()[0] in ('q', 'Q'):
                return

            try:
                i = int(user_input)
            except ValueError:
                log.warn("Invalid input - enter a numeric value or 'q' to quit.")
                continue

            if i < 0 or i > (x-1):
                log.warn("Invalid input - enter a value between 0 and %d or 'q' to quit." % (x-1))
                continue

            break

        return devices[i][0]




def probeDevices(sock=None, bus='cups,usb,par', timeout=5,
                  ttl=4, filter='', format='default'):
    close_sock = False

    if sock is None:
        close_sock = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((prop.hpssd_host, prop.hpssd_port))
        except socket.error:
            log.error("Unable to connect to HPLIP I/O. Please restart HPLIP and try again.")
            raise Error(ERROR_UNABLE_TO_CONTACT_SERVICE)

    fields, data, result_code = \
        msg.xmitMessage(sock,
                         "ProbeDevicesFiltered",
                         None,
                         {
                           'bus' : bus,
                           'timeout' : timeout,
                           'ttl' : ttl,
                           'format' : format,
                           'filter' : filter,
                          }
                       )

    if result_code > ERROR_SUCCESS:
        return ''

    if close_sock:
        sock.close()

    temp = data.splitlines()
    probed_devices = []
    for t in temp:
        probed_devices.append(t.split(',')[0])

    return probed_devices


def getSupportedCUPSDevices():
    devices = {}
    printers = cups.getPrinters()

    for p in printers:
        try:
            back_end, is_hp, bus, model, serial, dev_file, host, port = \
                parseDeviceURI(p.device_uri)

        except Error:
            continue

        if is_hp:
            try:
                devices[p.device_uri]
            except KeyError:
                devices[p.device_uri] = [p.name]
            else:
                devices[p.device_uri].append(p.name)

    return devices # { 'device_uri' : [ CUPS printer list ], ... }


def parseDeviceID(device_id):
    d= {}
    x = [y.strip() for y in device_id.strip().split(';') if y]

    for z in x:
        y = z.split(':')
        try:
            d.setdefault(y[0].strip(), y[1])
        except IndexError:
            d.setdefault(y[0].strip(), None)

    d.setdefault('MDL', '')
    d.setdefault('SN',  '')

    if 'MODEL' in d:
        d['MDL'] = d['MODEL']
        del d['MODEL']

    if 'SERIAL' in d:
        d['SN'] = d['SERIAL']
        del d['SERIAL']

    elif 'SERN' in d:
        d['SN'] = d['SERN']
        del d['SERN']

    if d['SN'].startswith('X'):
        d['SN'] = ''

    return d


def parseDynamicCounter(ctr_field, convert_to_int=True):
    counter, value = ctr_field.split(' ')
    try:
        counter = int(counter.lstrip('0') or '0')
        if convert_to_int:
            value = int(value.lstrip('0') or '0')
    except ValueError:
        if convert_to_int:
            counter, value = 0, 0
        else:
            counter, value = 0, ''

    return counter, value


def parseDeviceURI(device_uri):
    m = pat_deviceuri.match(device_uri)

    if m is None:
        raise Error(ERROR_INVALID_DEVICE_URI)

    back_end = m.group(1).lower() or ''
    #is_hp = (back_end in ('hp', 'hpfax'))
    is_hp = (back_end == 'hp')
    bus = m.group(2).lower() or ''

    if bus not in ('usb', 'net', 'bt', 'fw', 'par'):
        raise Error(ERROR_INVALID_DEVICE_URI)

    model = m.group(3).replace(' ', '_')  or ''
    serial = m.group(4) or ''
    dev_file = m.group(5) or ''
    host = m.group(6) or ''
    port = m.group(7) or 1

    if bus == 'net':
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 1

        if port == 0:
            port = 1

    return back_end, is_hp, bus, model, serial, dev_file, host, port


def validateBusList(bus):
    for x in bus.split(','):
        bb = x.lower().strip()
        if bb not in VALID_BUSES:
            log.error( "Invalid bus name: %s" % bb )
            return False

    return True

def validateFilterList(filter):
    for f in filter.split(','):
        if f not in VALID_FILTERS:
            log.error( "Invalid term '%s' in filter list" % f )
            return False

    return True


AGENT_types = {AGENT_TYPE_NONE        : 'invalid',
                AGENT_TYPE_BLACK       : 'black',
                AGENT_TYPE_CMY         : 'cmy',
                AGENT_TYPE_KCM         : 'kcm',
                AGENT_TYPE_CYAN        : 'cyan',
                AGENT_TYPE_MAGENTA     : 'magenta',
                AGENT_TYPE_YELLOW      : 'yellow',
                AGENT_TYPE_CYAN_LOW    : 'photo_cyan',
                AGENT_TYPE_MAGENTA_LOW : 'photo_magenta',
                AGENT_TYPE_YELLOW_LOW  : 'photo_yellow',
                AGENT_TYPE_GGK         : 'photo_gray',
                AGENT_TYPE_BLUE        : 'photo_blue',
                AGENT_TYPE_UNSPECIFIED : 'unspecified', # Kind=5,6
            }

AGENT_kinds = {AGENT_KIND_NONE            : 'invalid',
                AGENT_KIND_HEAD            : 'head',
                AGENT_KIND_SUPPLY          : 'supply',
                AGENT_KIND_HEAD_AND_SUPPLY : 'cartridge',
                AGENT_KIND_TONER_CARTRIDGE : 'toner',
                AGENT_KIND_MAINT_KIT       : 'maint_kit', # fuser
                AGENT_KIND_ADF_KIT         : 'adf_kit',
                AGENT_KIND_DRUM_KIT        : 'drum_kit',
                AGENT_KIND_TRANSFER_KIT    : 'transfer_kit',
                AGENT_KIND_INT_BATTERY     : 'battery',
                AGENT_KIND_UNKNOWN         : 'unknown',
              }

AGENT_healths = {AGENT_HEALTH_OK           : 'ok',
                  AGENT_HEALTH_MISINSTALLED : 'misinstalled',
                  AGENT_HEALTH_INCORRECT    : 'incorrect',
                  AGENT_HEALTH_FAILED       : 'failed',
                  AGENT_HEALTH_OVERTEMP     : 'overtemp', # battery
                  AGENT_HEALTH_CHARGING     : 'charging', # battery
                  AGENT_HEALTH_DISCHARGING  : 'discharging', # battery
                }


AGENT_levels = {AGENT_LEVEL_TRIGGER_MAY_BE_LOW : 'low',
                 AGENT_LEVEL_TRIGGER_PROBABLY_OUT : 'low',
                 AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT : 'out',
               }


MODEL_UI_REPLACEMENTS = {'laserjet'   : 'LaserJet',
                          'psc'        : 'PSC',
                          'officejet'  : 'Officejet',
                          'deskjet'    : 'Deskjet',
                          'hp'         : 'HP',
                          'business'   : 'Business',
                          'inkjet'     : 'Inkjet',
                          'photosmart' : 'Photosmart',
                          'color'      : 'Color',
                          'series'     : 'series',
                          'printer'    : 'Printer',
                          'mfp'        : 'MFP',
                          'mopier'     : 'Mopier',
                        }


def normalizeModelName(model):
    if not model.lower().startswith('hp'):
        z = 'HP ' + model.replace('_', ' ')
    else:
        z = model.replace('_', ' ')

    y = []
    for x in z.split():
        xx = x.lower()
        y.append(MODEL_UI_REPLACEMENTS.get(xx, xx))

    model_ui = ' '.join(y)

    return model, model_ui

def isLocal(bus):
    return bus in ('par', 'usb', 'fw', 'bt')


# **************************************************************************** #


class BaseDevice(object):

    def __init__(self, device_uri, sock=None, host=None, port=None, callback=None):
        self.device_uri = device_uri
        self.callback = callback
        self.close_socket = False

        self.sock_host = host
        self.sock_port = port

        try:
            self.back_end, self.is_hp, self.bus, self.model, \
                self.serial, self.dev_file, self.host, self.port = \
                parseDeviceURI(self.device_uri)
        except Error:
            self.io_state = IO_STATE_NON_HP
            raise Error(ERROR_INVALID_DEVICE_URI)

        log.debug("URI: backend=%s, is_hp=%s, bus=%s, model=%s, serial=%s, dev=%s, host=%s, port=%d" % \
            (self.back_end, self.is_hp, self.bus, self.model, self.serial, self.dev_file, self.host, self.port))

        self.model, self.model_ui = normalizeModelName(self.model)
        log.debug("Model/UI model: %s/%s" % (self.model, self.model_ui))

        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.sock.connect((self.sock_host, self.sock_port))
                self.close_socket = True
            except socket.error:
                raise Error(ERROR_UNABLE_TO_CONTACT_SERVICE)
        else:
            self.sock = sock


        # Items cached in both client and server
        self.mq = {} # Model query
        self.dq = {} # Device query
        self.cups_printers = []
        self.supported = False


    def xmitMessage(self, msg_type, other_fields={},
                      payload=None, timeout=prop.read_timeout):

        return msg.xmitMessage(self.sock, msg_type,
                                payload, other_fields, timeout)


    def quit(self):
        if self.close_socket:
            self.sock.close()

# **************************************************************************** #

class Device(BaseDevice):
    def __init__(self, device_uri=None, printer_name=None,
                  hpssd_sock=None, callback=None,
                  cups_printers=[]):

        if device_uri is None:
            printers = cups.getPrinters()
            for p in printers:
                if p.name.lower() == printer_name.lower():
                    device_uri = p.device_uri
                    break
            else:
                raise Error(ERROR_DEVICE_NOT_FOUND)

        BaseDevice.__init__(self, device_uri, hpssd_sock,
                             prop.hpssd_host, prop.hpssd_port,
                             callback)

        self.cups_printers = cups_printers
            
        if not self.cups_printers:
            printers = cups.getPrinters()
            for p in printers:
                if self.device_uri == p.device_uri:
                    self.cups_printers.append(p.name)
        
        try:
            self.first_cups_printer = self.cups_printers[0]
        except IndexError:
            self.first_cups_printer = ''

        self.device_vars = {
            'URI'        : self.device_uri,
            'DEVICE_URI' : self.device_uri,
            'SANE_URI'   : self.device_uri.replace('hp:', 'hpaio:'),
            'PRINTER'    : self.first_cups_printer,
            'HOME'       : prop.home_dir,
                           }

        self.device_id = -1

        self.error_state = ERROR_STATE_ERROR
        self.device_state = DEVICE_STATE_NOT_FOUND
        self.status_code = EVENT_ERROR_DEVICE_NOT_FOUND

        # PCard support, for direct HPIOD communication
        # BaseDevice connects to hpssd for services and I/O (print, pml, etc)
        self.hpiod_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hpiod_sock_connected = False
        self.pcard_channel_id = -1
        self.pcard = False


    def open(self, pcard=False):
        self.pcard = pcard

        if pcard:
            if not self.hpiod_sock_connected:
                log.debug("Connecting to hpiod at %s:%d..." % (prop.hpiod_host, prop.hpiod_port))
                try:
                    self.hpiod_sock.connect((prop.hpiod_host, prop.hpiod_port))
                except socket.error:
                    raise Error(ERROR_UNABLE_TO_CONTACT_SERVICE)

            self.queryModel()

            fields, data, result_code = \
                self.xmitHpiodMessage("DeviceOpen",
                                        {'device-uri':   self.device_uri,
                                          'io-mode' :     self.mq.get('io-mode', '0'),
                                          'io-mfp-mode' : self.mq.get('io-mfp-mode', '2'),
                                          'io-control' :  self.mq.get('io-control', '0'),
                                          'io-scan-port': self.mq.get('io-scan-port', '0'),
                                        }
                                      )

            if result_code == ERROR_SUCCESS:
                self.device_id = fields['device-id']
            else:
                raise Error(result_code)

        else:

            fields, data, result_code = \
                self.xmitMessage("OpenDevice",
                                  {'device-uri' : self.device_uri,})

            self.queryModel()
            
            return result_code


    def close(self):
        if self.pcard:

            fields, data, result_code = \
                self.xmitHpiodMessage("DeviceClose",
                                        {
                                           'device-id': self.device_id,
                                        }
                                      )

            if self.hpiod_sock_connected:
                self.hpiod_sock_connected.close()
        else:
            fields, data, result_code = \
                self.xmitMessage("CloseDevice",
                                  {'device-uri' : self.device_uri,})


        return result_code


    def __openChannel(self, service_name):
        fields, data, result_code = \
            self.xmitMessage("OpenChannel",
                              {
                                'device-uri' : self.device_uri,
                                'service-name' : service_name,
                              }
                            )
        return result_code


    def __closeChannel(self, service_name):
        fields, data, result_code = \
            self.xmitMessage("CloseChannel",
                               {
                                    'device-uri' : self.device_uri,
                                    'service-name' : service_name,
                                }
                              )
        return result_code

    
    def queryDevice(self):
        self.dq, data, result_code = \
            self.xmitMessage("QueryDevice",
                              {
                                'device-uri' : self.device_uri,
                              }
                            )

        for d in self.dq:
            self.__dict__[d.replace('-','_')] = self.dq[d]

        try:
            self.cups_printers = self.cups_printers.split(',')
        except:
            self.cups_printers = []



    def getStatusFromDeviceID(self):
        fields, data, result_code = \
            self.xmitMessage("DeviceId",
                              {
                                'device-uri' : self.device_uri,
                              }
                            )

        return status.parseStatus(parseDeviceID(data))

    def getDeviceID(self):
        fields, data, result_code = \
            self.xmitMessage("DeviceId",
                              {
                                'device-uri' : self.device_uri,
                              }
                            )

        return parseDeviceID(data)

    
    
    def queryModel(self):
        result_code = ERROR_SUCCESS

        if not self.mq:
            self.mq, data, result_code = \
                self.xmitMessage("QueryModel",
                                  {
                                    'device-uri' : self.device_uri,
                                  }
                                )

        self.supported = bool(self.mq)
        if self.supported:
            for m in self.mq:
                self.__dict__[m.replace('-','_')] = self.mq[m]


    def queryHistory(self):
        fields, data, result_code = \
            self.xmitMessage("QueryHistory",
                               {
                                    'device-uri' : self.device_uri,
                                }
                             )

        result = []
        lines = data.strip().splitlines()
        lines.reverse()

        for x in lines:
            yr, mt, dy, hr, mi, sec, wd, yd, dst, job, user, ec, ess, esl = x.strip().split(',', 13)
            result.append((int(yr), int(mt), int(dy), int(hr), int(mi), int(sec), int(wd),
                             int(yd), int(dst), int(job), user, int(ec), ess, esl))

        return result


    def openPML(self):
        if not self.mq['io-mode'] == IO_MODE_UNI:
            return self.__openChannel('HP-MESSAGE')
        else:
            return -1


    def getPML(self, oid):
        if not self.mq['io-mode'] == IO_MODE_UNI:
            fields, data, result_code = \
                self.xmitMessage("GetPML",
                                  {
                                    'device-uri' : self.device_uri,
                                    'oid' : oid[0],
                                    'type' : oid[1],
                                  }
                                )
        else:
            data, result_code = '', ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION

        return data, result_code


    def setPML(self, oid, value):
        if not self.mq['io-mode'] == IO_MODE_UNI:
            fields, data, result_code = \
                self.xmitMessage("SetPML",
                                  {
                                    'device-uri' : self.device_uri,
                                    'oid' : oid[0],
                                    'type' : oid[1],
                                  },
                                  value
                                )
        else:
            result_code = ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION

        return result_code


    def closePML(self):
        if not self.mq['io-mode'] == IO_MODE_UNI:
            return self.__closeChannel('HP-MESSAGE')


    def getDynamicCounter(self, counter, convert_to_int=True):
        fields, value, result_code = \
            self.xmitMessage("GetDynamicCounter",
                              {
                                'device-uri' : self.device_uri,
                                'counter' : counter,
                                #'convert-int' : convert_int,
                              }
                            )

        if value.startswith('#'):
            value = value[1:]

        if convert_to_int:
            try:
                value = int(value)
            except ValueError:
                pass

        return value


    def openPrint(self):
        return self.__openChannel('PRINT')


    def readPrint(self, bytes_to_read=prop.max_message_len):
        fields, data, result_code = \
            self.xmitMessage("ReadPrintChannel",
                              {
                                'device-uri' : self.device_uri,
                                'bytes-to-read' : bytes_to_read,
                              }
                            )

        return data, result_code


    def writePrint(self, data):
        buffer, bytes_out, total_bytes_to_write = data, 0, len(data)

        while len(buffer) > 0:
            fields, data, result_code = \
                self.xmitMessage('WritePrintChannel',
                                    {
                                        'device-uri': self.device_uri,
                                    },
                                    buffer[:prop.max_message_len],
                                  )

            if result_code != ERROR_SUCCESS:
                log.error("WritePrintChannel error")
                raise Error(ERROR_INTERNAL)

            buffer = buffer[prop.max_message_len:]

            if self.callback is not None:
                self.callback()



    def printData(self, data, direct=False, raw=True):
        if direct:
            return self.writePrint(data)
        else:
            temp_file_fd, temp_file_name = utils.make_temp_file()
            os.write(temp_file_fd, data)
            os.close(temp_file_fd)

            if len(data) < 1024 and \
                log.get_level() == log.LOG_LEVEL_DEBUG:

                log.debug("Printing data: %s" % repr(data))

            self.printFile(temp_file_name, direct, raw, remove=True)
            #os.remove(temp_file_name)



    def printFile(self, filename, direct=False, raw=True, remove=False):
        if os.path.exists(filename):
            is_gzip = os.path.splitext(filename)[-1].lower() == '.gz'

            if direct:
                if is_gzip:
                    f = gzip.open(filename, 'r')
                else:
                    f = file(filename, 'r')

                self.writePrint(f.read())

                f.close()

                if remove:
                    os.remove(filename)

            else:
                raw_str = ('', '-l')[raw]
                rem_str = ('', '-r')[remove]

                if is_gzip:
                    c = ' '.join(['gunzip -c', filename, '| lpr -P', self.first_cups_printer, raw_str, rem_str])
                else:
                    c = ' '.join(['lpr -P', self.first_cups_printer, raw_str, rem_str, filename])

                log.debug(c)
                os.system(c)


    def printGzipFile(self, filename, direct=False, raw=True, remove=False):
        return self.printFile(filename, direct, raw, remove)


    def printTestPage(self):
        return self.printParsedGzipPostscript(os.path.join( prop.home_dir, 'data',
                                              'ps', 'testpage.ps.gz' ))


    def writeEmbeddedPML(self, oid, value, direct=False):
        fields, data, result_code = \
            self.xmitMessage("WriteEmbeddedPML",
                              {
                                'device-uri' : self.device_uri,
                                'oid' : oid[0],
                                'type' : oid[1],
                                'direct' : direct,
                              },
                              value,
                            )


    def closePrint(self):
        return self.__closeChannel('PRINT')

    def cancelJob(self, jobid):
        cups.cancelJob(jobid)
        self.sendEvent(STATUS_PRINTER_CANCELING, 'event', jobid,
            prop.username, self.device_uri)


    def printParsedGzipPostscript(self, print_file):
        # direct=False, raw=False
        try:
            os.stat(print_file)
        except OSError:
            log.error("File not found: %s" % print_file)
            return

        temp_file_fd, temp_file_name = utils.make_temp_file()
        f = gzip.open(print_file, 'r')

        x = f.readline()
        while not x.startswith('%PY_BEGIN'):
            os.write(temp_file_fd, x)
            x = f.readline()

        sub_lines = []
        x = f.readline()
        while not x.startswith('%PY_END'):
            sub_lines.append(x)
            x = f.readline()
            
        SUBS = {'VERSION' : prop.version,
                 'MODEL'   : self.model_ui,
                 'URI'     : self.device_uri,
                 'BUS'     : self.bus,
                 'SERIAL'  : self.serial,
                 'IP'      : self.host,
                 'PORT'    : self.port,
                 'DEVNODE' : self.dev_file,
                 }

        if self.bus == 'net':
            SUBS['DEVNODE'] = 'n/a'
        else:
            SUBS['IP'] = 'n/a'
            SUBS['PORT'] = 'n/a'

        for s in sub_lines:
            os.write(temp_file_fd, s % SUBS)

        os.write(temp_file_fd, f.read())
        f.close()
        os.close(temp_file_fd)

        self.printFile(temp_file_name, direct=False, raw=False, remove=True)


    def setAlerts(self, email_alerts, email_address, smtp_server):

        fields, data, result_code = \
            self.xmitMessage("SetAlerts",
                              {
                                'username'      : prop.username,
                                'email-alerts'  : email_alerts,
                                'email-address' : email_address,
                                'smtp-server'   : smtp_server,
                               }
                            )


    def sendEvent(self, event, typ, jobid, username, device_uri):
        msg.sendEvent(self.sock, 'Event', None,
                      {
                          'job-id'        : jobid,
                          'event-type'    : typ,
                          'event-code'    : event,
                          'username'      : username,
                          'device-uri'    : device_uri,
                          'retry-timeout' : 0,
                      }
                     )


    def reserveChannel(self, service_name):
        fields, data, result_code = \
            self.xmitMessage("ReserveChannel",
                              {
                                'device-uri' : self.device_uri,
                                'service-name' : service_name,
                              }
                            )
        return result_code

    def unreserveChannel(self, service_name):
        fields, data, result_code = \
            self.xmitMessage("UnReserveChannel",
                              {
                                'device-uri' : self.device_uri,
                                'service-name' : service_name,
                              }
                            )
        return result_code



    def xmitHpiodMessage(self, msg_type, other_fields={},
                          payload=None, timeout=prop.read_timeout):

        return msg.xmitMessage(self.hpiod_sock, msg_type,
                                payload, other_fields, timeout)


    def openPCard(self):
        fields, data, result_code = \
            self.xmitHpiodMessage("ChannelOpen",
                                   {'device-id':  self.device_id,
                                     'service-name' : 'HP-CARD-ACCESS',
                                   }
                                 )

        self.pcard_channel_id = fields['channel-id']
        self.reserveChannel('HP-CARD-ACCESS')


    def closePCard(self):
        self.unreserveChannel('HP-CARD-ACCESS')

        fields, data, result_code = \
            self.xmitHpiodMessage('ChannelClose',
                                   {
                                    'device-id': self.device_id,
                                    'channel-id' : self.pcard_channel_id,
                                   }
                                 )


    def readPCard(self, bytes_to_read=prop.max_message_len, timeout=prop.read_timeout):
        num_bytes = 0
        buffer = ''

        while True:
            fields, data, result_code = \
                self.xmitHpiodMessage('ChannelDataIn',

                                        {'device-id': self.device_id,
                                          'channel-id' : self.pcard_channel_id,
                                          'bytes-to-read' : bytes_to_read,
                                          'timeout' : timeout,
                                        }
                                      )

            l = len(data)

            if result_code != ERROR_SUCCESS:
                log.error("Print channel read error")
                raise Error(ERROR_DEVICE_IO_ERROR)

            if l == 0:
                log.debug("End of data")
                break

            buffer = ''.join([buffer, data])

            num_bytes += l

            if num_bytes >= bytes_to_read:
                break

            if self.callback is not None:
                self.callback()

        log.debug("Returned %d total bytes in buffer." % num_bytes)
        return buffer


    def writePCard(self, data):
        buffer, bytes_out, total_bytes_to_write = data, 0, len(data)

        while len(buffer) > 0:
            fields, data, result_code =                self.xmitHpiodMessage('ChannelDataOut',
                                        {
                                            'device-id': self.device_id,
                                            'channel-id' : self.pcard_channel_id,
                                        },
                                        buffer[:prop.max_message_len],
                                      )

            if result_code != ERROR_SUCCESS:
                log.error("Print channel write error")
                raise Error(ERROR_DEVICE_IO_ERROR)

            buffer = buffer[prop.max_message_len:]
            bytes_out += fields['bytes-written']

            if self.callback is not None:
                self.callback()

        if total_bytes_to_write != bytes_out:
            raise Error(ERROR_DEVICE_IO_ERROR)

        return bytes_out


# **************************************************************************** #

class ServerDevice(BaseDevice):
    def __init__(self, device_uri, hpiod_sock=None,
                  model_query_func=None, string_query_func=None,
                  callback=None):

        self.model_query_func = model_query_func
        self.string_query_func = string_query_func

        BaseDevice.__init__(self, device_uri, hpiod_sock,
                             prop.hpiod_host, prop.hpiod_port,
                             callback)

        self.channels = {} # { 'SERVICENAME' : channel_id, ... }
        self.device_id = -1
        self.r_values = None # ( r_value, r_value_str, rg, rr )
        self.deviceID = ''
        self.panel_check = True
        self.history = utils.RingBuffer(prop.history_size)
        self.io_state = IO_STATE_HP_READY
        self.is_local = isLocal(self.bus)
        self.dev_file = ''
        self.serial = ''
        
        printers = cups.getPrinters()
        for p in printers:
            if self.device_uri == p.device_uri:
                self.cups_printers.append(p.name)
                self.state = p.state # ?

                if self.io_state == IO_STATE_NON_HP:
                    self.model = p.makemodel.split(',')[0]

        try:
            self.mq = self.model_query_func(self.model)
        except Error:
            log.error("Unsupported model: %s" % self.model)
            self.createHistory(STATUS_DEVICE_UNSUPPORTED)
        else:
            self.supported = True

        self.mq.update({'model'    : self.model,
                        'model-ui' : self.model_ui})

        self.error_state = ERROR_STATE_ERROR
        self.device_state = DEVICE_STATE_NOT_FOUND
        self.status_code = EVENT_ERROR_DEVICE_NOT_FOUND

        self.dq.update({
            'back-end'         : self.back_end,
            'is-hp'            : self.is_hp,
            'serial'           : self.serial,
            'dev-file'         : self.dev_file,
            'host'             : self.host,
            'port'             : self.port,
            'cups-printers'    : ','.join(self.cups_printers),
            'status-code'      : self.status_code,
            'status-desc'      : '',
            'deviceid'         : '',
            'panel'            : 0,
            'panel-line1'      : '',
            'panel-line2'      : '',
            '3bit-status-code' : 0,
            '3bit-status-name' : 'IOTrap',
            'device-state'     : self.device_state,
            'error-state'      : self.error_state,
            'device-uri'       : self.device_uri,
            'cups-uri'         : self.device_uri,
            })

        if self.mq.get('fax-type', FAX_TYPE_NONE) != FAX_TYPE_NONE:
            self.dq.update({ 'fax-uri' : self.device_uri.replace('hp:/', 'hpfax:/')})

        if self.mq.get('scan-type', SCAN_TYPE_NONE) != SCAN_TYPE_NONE:
            self.dq.update({ 'scan-uri' : self.device_uri.replace('hp:/', 'hpaio:/')})


    def createHistory(self, code, jobid=0, username=prop.username):
        try:
            short_string = self.string_query_func(code, 0)
        except Error:
            short_string = ''

        try:
            long_string = self.string_query_func(code, 1)
        except Error:
            long_string = ''

        self.history.append(tuple(time.localtime()) +
                            (jobid, username, code,
                             short_string, long_string))


    def open(self, network_timeout=3):
        if self.supported and self.io_state in (IO_STATE_HP_READY, IO_STATE_HP_NOT_AVAIL):
            log.debug("Opening device: %s" % self.device_uri)
            prev_device_state = self.device_state
            self.io_state = IO_STATE_HP_NOT_AVAIL
            self.device_state = DEVICE_STATE_NOT_FOUND
            self.error_state = ERROR_STATE_ERROR
            self.status_code = EVENT_ERROR_DEVICE_NOT_FOUND
            self.device_id = -1

            if not self.is_local:
                log.debug("Pinging %s..." % self.host)
                try:
                    delay = utils.ping(self.host, network_timeout)
                except socket.error:
                    self.createHistory(self.status_code)
                    raise Error(ERROR_DEVICE_NOT_FOUND)
                    #return
                else:
                    if delay < 0.0:
                        self.createHistory(self.status_code)
                        raise Error(ERROR_DEVICE_NOT_FOUND)

            fields, data, result_code = \
                self.xmitMessage("DeviceOpen",
                                    {'device-uri':   self.device_uri,
                                      'io-mode' :     self.mq.get('io-mode', '0'),
                                      'io-mfp-mode' : self.mq.get('io-mfp-mode', '2'),
                                      'io-control' :  self.mq.get('io-control', '0'),
                                      'io-scan-port': self.mq.get('io-scan-port', '0'),
                                    }
                                  )

            if result_code != ERROR_SUCCESS:
                self.createHistory(self.status_code)
                log.error("Unable to communicate with device: %s" % self.device_uri)
                raise Error(ERROR_DEVICE_NOT_FOUND)
            else:
                self.device_id = fields['device-id']
                log.debug("device-id=%d" % self.device_id)
                self.io_state = IO_STATE_HP_OPEN
                self.error_state = ERROR_STATE_CLEAR
                log.debug("Opened device: %s (hp=%s,bus=%s,model=%s,dev=%s,serial=%s)" %
                          (self.device_uri, self.is_hp, self.bus, self.model, self.dev_file, self.serial))

                if prev_device_state == DEVICE_STATE_NOT_FOUND:
                    self.device_state = DEVICE_STATE_JUST_FOUND
                else:
                    self.device_state = DEVICE_STATE_FOUND

                self.getDeviceID()
                self.getSerialNumber()



    def close(self):
        if self.io_state == IO_STATE_HP_OPEN:
            log.debug("Closing device...")

            if len(self.channels) > 0:

                for c in self.channels.keys():
                    self.__closeChannel(c)

            fields, data, result_code = \
                self.xmitMessage("DeviceClose",
                                    {
                                       'device-id': self.device_id,
                                    }
                                  )

            self.channels.clear()
            self.io_state = IO_STATE_HP_READY


    def reserveChannel(self, service_name, channel_id=-1):
        service_name = service_name.upper()
        try:
            self.channels[service_name]
        except KeyError:
            self.channels[service_name] = channel_id
        else:
            pass # TODO: Handle multiple access to single (non PML) channel

    def unreserveChannel(self, service_name):
        service_name = service_name.upper()
        try:
            self.channels[service_name]
        except KeyError:
            pass
        else:
            del self.channels[service_name]

    def __openChannel(self, service_name):
        self.open()

        service_name = service_name.upper()

        if service_name not in self.channels:
            log.debug("Opening %s channel..." % service_name)

            fields, data, result_code = \
                self.xmitMessage("ChannelOpen",
                                  {'device-id':  self.device_id,
                                    'service-name' : service_name,
                                  }
                                )
            try:
                channel_id = fields['channel-id']
            except KeyError:
                raise Error(ERROR_INTERNAL)

            self.reserveChannel(service_name, channel_id)
            log.debug("channel-id=%d" % channel_id)
            return channel_id
        else:
            return self.channels[service_name]


    def openChannel(self, service_name):
        return self.__openChannel(service_name)


    def openPrint(self):
        return self.__openChannel('PRINT')


    def openPCard(self):
        return self.__openChannel('HP-CARD-ACCESS')


    def closePrint(self):
        return self.__closeChannel('PRINT')


    def closePCard(self):
        return self.__closeChannel('HP-CARD-ACCESS')


    def openPML(self):
        return self.__openChannel('HP-MESSAGE')


    def closePML(self):
        return self.__closeChannel('HP-MESSAGE')


    def __closeChannel(self, service_name):

        if self.io_state == IO_STATE_HP_OPEN:
            service_name = service_name.upper()

            if service_name in self.channels:
                log.debug("Closing %s channel..." % service_name)

                fields, data, result_code = \
                    self.xmitMessage('ChannelClose',
                                      {
                                        'device-id': self.device_id,
                                        'channel-id' : self.channels[service_name],
                                      }
                                    )

                self.unreserveChannel(service_name)


    def closeChannel(self, service_name):
        return self.__closeChannel(service_name)


    def getDeviceID(self):
        fields, data, result_code = \
            self.xmitMessage('DeviceID',
                              {'device-id' : self.device_id,})

        if result_code != ERROR_SUCCESS:
            self.raw_deviceID = ''
            self.deviceID = {}
        else:
            self.raw_deviceID = data
            self.deviceID = parseDeviceID(data)


    def getSerialNumber(self):
        if len(self.serial):
            return

        try:
            self.serial = self.deviceID['SN']
        except KeyError:
            pass
        else:
            if len(self.serial):
                return

        if self.mq.get('status-type', STATUS_TYPE_NONE) != STATUS_TYPE_NONE and \
            not self.mq.get('io-mode', IO_MODE_UNI) == IO_MODE_UNI:

            try:
                try:
                    error_code, self.serial = self.getPML(pml.OID_SERIAL_NUMBER)
                except Error:
                    self.serial = ''
            finally:
                self.closePML()
            
        if self.serial is None:
            self.serial = ''


    def getThreeBitStatus(self):
        fields, data, result_code = \
            self.xmitMessage('DeviceStatus',
                              {'device-id' : self.device_id,})

        if result_code != ERROR_SUCCESS:
            self.three_bit_status_code = 0
            self.three_bit_status_name = 'IOTrap'
        else:
            self.three_bit_status_code = fields['status-code']
            self.three_bit_status_name = fields['status-name']


    def getDevFile(self):
        fields, data, result_code = \
            self.xmitMessage('DeviceFile',
                              {'device-id' : self.device_id,})

        if result_code == ERROR_SUCCESS:
            self.dev_file = fields['device-file']


    def queryDevice(self):
        if not self.supported:
            self.dq = {}
            return

        r_type = self.mq.get('r-type', 0)
        tech_type = self.mq.get('tech-type', TECH_TYPE_NONE)
        status_type = self.mq.get('status-type', STATUS_TYPE_NONE)
        io_mode = self.mq.get('io-mode', IO_MODE_UNI)

        # Turn off status if local connection and bi-di not avail.
        if io_mode  == IO_MODE_UNI and self.back_end != 'net':
            status_type = STATUS_TYPE_NONE
        
        agents = []
            
        if self.device_state != DEVICE_STATE_NOT_FOUND:
            try:
                self.getThreeBitStatus()
            except Error, e:
                pass
    
            try:
                self.getDeviceID()
            except Error, e:
                pass
    
            try:
                self.getDevFile()
            except Error, e:
                pass
    
            try:
                status_desc = self.string_query_func(self.status_code)
            except Error:
                status_desc = ''
        
            self.dq.update({
                'back-end'         : self.back_end,
                'is-hp'            : self.is_hp,
                'serial'           : self.serial,
                'host'             : self.host,
                'port'             : self.port,
                'cups-printers'    : ','.join(self.cups_printers),
                'status-code'      : self.status_code,
                'status-desc'      : status_desc,
                'deviceid'         : self.raw_deviceID,
                'panel'            : 0,
                'panel-line1'      : '',
                'panel-line2'      : '',
                '3bit-status-code' : self.three_bit_status_code,
                '3bit-status-name' : self.three_bit_status_name,
                'device-state'     : self.device_state,
                'error-state'      : self.error_state,
                'dev-file'         : self.dev_file,
                })

            status_block = {}

            if status_type == STATUS_TYPE_NONE:
                log.warn("No status available for device.")
                status_block = {'status-code' : STATUS_PRINTER_IDLE}

            elif status_type in (STATUS_TYPE_VSTATUS, STATUS_TYPE_S):
                log.debug("Type 1/2 (S: or VSTATUS:) status")
                status_block = status.parseStatus(self.deviceID)

            elif status_type == STATUS_TYPE_LJ:
                log.debug("Type 3 LaserJet status")
                status_block = status.StatusType3(self, self.deviceID)

            elif status_type == STATUS_TYPE_S_W_BATTERY:
                log.debug("Type 4 S: status with battery check")
                status_block = status.parseStatus(self.deviceID)
                status.BatteryCheck(self, status_block)

            else:
                log.error("Unimplemented status type: %d" % status_type)

            if status_block:
                log.debug(status_block)
                self.dq.update(status_block)
                try:
                    status_block['agents']
                except KeyError:
                    pass
                else:
                    agents = status_block['agents']
                    del self.dq['agents']

            status_code = self.dq.get('status-code', STATUS_UNKNOWN)
            self.createHistory(status_code)

            try:
                self.dq.update({'status-desc' : self.string_query_func(status_code),
                                'error-state' : STATUS_TO_ERROR_STATE_MAP.get(status_code, ERROR_STATE_CLEAR),
                                })
            except (KeyError, Error):
                self.dq.update({'status-desc' : '',
                                'error-state' : ERROR_STATE_CLEAR,
                                })

            r_value, rg, rr, r_value_str = 0, '000', '000000', '000000000'

            if status_type != STATUS_TYPE_NONE:

                if self.panel_check:
                    self.panel_check = bool(self.mq.get('panel-check-type', 0))

                if self.panel_check and status_type != STATUS_TYPE_NONE:
                    try:
                        self.panel_check, line1, line2 = status.PanelCheck(self)
                    finally:
                        self.closePML()

                    self.dq.update({'panel'       : int(self.panel_check),
                                      'panel-line1' : line1,
                                      'panel-line2' : line2,})

                if r_type > 0:

                    if self.r_values is None:
                        try:
                            try:
                                r_value = self.getDynamicCounter(140)
    
                                if r_value is not None:
                                    r_value_str = str(r_value)
                                    r_value_str = ''.join(['0'*(9 - len(r_value_str)), r_value_str])
                                    rg, rr, r_value = r_value_str[:3], r_value_str[3:], int(rr)
                                    self.r_values = r_value, r_value_str, rg, rr
                                else:
                                    log.error("Error attempting to read r-value (2).")
                                    r_value = 0
                            except Error:
                                log.error("Error attempting to read r-value (1).")
                                r_value = 0
                        
                        finally:
                            self.closePrint()
                        
                    else:
                        r_value, r_value_str, rg, rr = self.r_values

            self.dq.update({'r'  : r_value,
                            'rs' : r_value_str,
                            'rg' : rg,
                            'rr' : rr,
                          })

            a = 1
            while True:
                mq_agent_kind = self.mq.get('r%d-agent%d-kind' % (r_value, a), 0)

                if mq_agent_kind == 0:
                    break

                mq_agent_type = self.mq.get('r%d-agent%d-type' % (r_value, a), 0)
                mq_agent_sku = self.mq.get('r%d-agent%d-sku' % (r_value, a), '')

                found = False
                for agent in agents:
                    agent_kind = agent['kind']
                    agent_type = agent['type']

                    if agent_kind == mq_agent_kind and \
                       agent_type == mq_agent_type:
                       found = True
                       break

                if found:
                    agent_health = agent.get('health', AGENT_HEALTH_OK)
                    agent_level_trigger = agent.get('level-trigger',
                        AGENT_LEVEL_TRIGGER_SUFFICIENT_0)

                    query = 'agent_%s_%s' % (AGENT_types.get(agent_type, 'unknown'), 
                                             AGENT_kinds.get(agent_kind, 'unknown'))
                    log.debug(query)
                    try:
                        agent_desc = self.string_query_func(query)
                    except Error:
                        agent_desc = ''

                    self.dq.update(
                    {
                        'agent%d-kind' % a :          agent_kind,
                        'agent%d-type' % a :          agent_type,
                        'agent%d-known' % a :         agent.get('known', False),
                        'agent%d-sku' % a :           mq_agent_sku,
                        'agent%d-level' % a :         agent.get('level', 0),
                        'agent%d-level-trigger' % a : agent_level_trigger,
                        'agent%d-ack' % a :           agent.get('ack', False),
                        'agent%d-hp-ink' % a :        agent.get('hp-ink', False),
                        'agent%d-health' % a :        agent_health,
                        'agent%d-dvc' % a :           agent.get('dvc', 0),
                        'agent%d-virgin' % a :        agent.get('virgin', False),
                        'agent%d-desc' % a :          agent_desc,
                        'agent%d-id' % a :            agent.get('id', 0 )
                    })

                else:
                    agent_health = AGENT_HEALTH_MISINSTALLED
                    agent_level_trigger = AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT

                    query = 'agent_%s_%s' % (AGENT_types.get(mq_agent_type, 'unknown'),
                                             AGENT_kinds.get(mq_agent_kind, 'unknown'))
                    log.debug(query)
                    try:
                        agent_desc = self.string_query_func(query)
                    except Error:
                        agent_desc = ''

                    self.dq.update(
                    {
                        'agent%d-kind' % a :          mq_agent_kind,
                        'agent%d-type' % a :          mq_agent_type,
                        'agent%d-known' % a :         False,
                        'agent%d-sku' % a :           mq_agent_sku,
                        'agent%d-level' % a :         0,
                        'agent%d-level-trigger' % a : agent_level_trigger,
                        'agent%d-ack' % a :           False,
                        'agent%d-hp-ink' % a :        False,
                        'agent%d-health' % a :        agent_health,
                        'agent%d-dvc' % a :           0,
                        'agent%d-virgin' % a :        False,
                        'agent%d-desc' % a :          agent_desc,
                        'agent%d-id' % a :            0,
                    })

                query = 'agent_%s_%s' % (AGENT_types.get(mq_agent_type, 'unknown'),
                                         AGENT_kinds.get(mq_agent_kind, 'unknown'))

                log.debug(query)
                try:
                    self.dq['agent%d-desc' % a] = self.string_query_func(query)
                except Error:
                    self.dq['agent%d-desc' % a] = ''

                # If printer is not in an error state, and
                # if agent health is OK, check for low supplies. If low, use
                # the agent level trigger description for the agent description.
                # Otherwise, report the agent health.
                if status_code == STATUS_PRINTER_IDLE and \
                    agent_health == AGENT_HEALTH_OK and \
                    agent_level_trigger >= AGENT_LEVEL_TRIGGER_MAY_BE_LOW:

                    # Low
                    query = 'agent_level_%s' % AGENT_levels.get(agent_level_trigger, 'unknown')

                    if tech_type in (TECH_TYPE_MONO_INK, TECH_TYPE_COLOR_INK):
                        code = agent_type + STATUS_PRINTER_LOW_INK_BASE
                    else:
                        code = agent_type + STATUS_PRINTER_LOW_TONER_BASE

                    self.dq['status-code'] = code
                    try:
                        self.dq['status-desc'] = self.string_query_func(code)
                    except Error:
                        self.dq['status-desc'] = ''
                        
                    self.dq['error-state'] = STATUS_TO_ERROR_STATE_MAP.get(code, ERROR_STATE_LOW_SUPPLIES)
                    self.createHistory(code)

                else:
                    # OK
                    query = 'agent_health_%s' % AGENT_healths.get(agent_health, 'unknown')

                log.debug(query)
                
                try:
                    self.dq['agent%d-health-desc' % a] = self.string_query_func(query)
                except Error:
                    self.dq['agent%d-health-desc' % a] = ''

                a += 1

        else: # Create agent keys for not-found devices

            r_value = 0
            if r_type > 0 and self.r_values is not None:
                r_value = self.r_values[0]

            a = 1
            while True:
                mq_agent_kind = self.mq.get('r%d-agent%d-kind' % (r_value, a), 0)

                if mq_agent_kind == 0:
                    break

                mq_agent_type = self.mq.get('r%d-agent%d-type' % (r_value, a), 0)
                mq_agent_sku = self.mq.get('r%d-agent%d-sku' % (r_value, a), '')
                query = 'agent_%s_%s' % (AGENT_types.get(mq_agent_type, 'unknown'),
                                         AGENT_kinds.get(mq_agent_kind, 'unknown'))
                log.debug(query)
                try:
                    agent_desc = self.string_query_func(query)
                except Error:
                    agent_desc = ''


                self.dq.update(
                {
                    'agent%d-kind' % a :          mq_agent_kind,
                    'agent%d-type' % a :          mq_agent_type,
                    'agent%d-known' % a :         False,
                    'agent%d-sku' % a :           mq_agent_sku,
                    'agent%d-level' % a :         0,
                    'agent%d-level-trigger' % a : AGENT_LEVEL_TRIGGER_ALMOST_DEFINITELY_OUT,
                    'agent%d-ack' % a :           False,
                    'agent%d-hp-ink' % a :        False,
                    'agent%d-health' % a :        AGENT_HEALTH_MISINSTALLED,
                    'agent%d-dvc' % a :           0,
                    'agent%d-virgin' % a :        False,
                    'agent%d-health-desc' % a :   self.string_query_func('agent_health_unknown'),
                    'agent%d-desc' % a :          agent_desc,
                    'agent%d-id' % a :            0,
                })

                a += 1


    def getPML(self, oid, desired_int_size=pml.INT_SIZE_INT): # oid => ( 'dotted oid value', pml type )
        channel_id = self.openPML()

        fields, data, result_code = \
            self.xmitMessage("GetPML",
                              {
                                'device-id' :  self.device_id,
                                'channel-id' : channel_id,
                                'oid' :        pml.PMLToSNMP(oid[0]),
                                'type' :       oid[1],
                               }
                            )

        pml_result_code = fields.get('pml-result-code', pml.ERROR_OK)

        if pml_result_code >= pml.ERROR_UNKNOWN_REQUEST:
            return pml_result_code, None

        return pml_result_code, pml.ConvertFromPMLDataFormat(data, oid[1], desired_int_size)


    def setPML(self, oid, value): # oid => ( 'dotted oid value', pml type )
        channel_id = self.openPML()

        value = pml.ConvertToPMLDataFormat(value, oid[1])

        fields, data, result_code = \
            self.xmitMessage("SetPML",
                              {
                                'device-id' :  self.device_id,
                                'channel-id' : channel_id,
                                'oid' :        pml.PMLToSNMP(oid[0]),
                                'type' :      oid[1],
                              },
                             value,
                            )

        return fields.get('pml-result-code', pml.ERROR_OK)


    def getDynamicCounter(self, counter, convert_to_int=True):
        self.getDeviceID()

        if 'DYN' in self.deviceID.get('CMD', '').split(','):

            self.printData(pcl.buildDynamicCounter(counter), direct=True)

            value, tries, times_seen, sleepy_time, max_tries = 0, 0, 0, 0.1, 10
            time.sleep(0.1)

            while True:

                if self.callback:
                    self.callback()

                sleepy_time += 0.1
                tries += 1

                time.sleep(sleepy_time)

                self.getDeviceID()

                if 'CTR' in self.deviceID and \
                    pat_dynamic_ctr.search(self.raw_deviceID) is not None:
                    dev_counter, value = parseDynamicCounter(self.deviceID['CTR'], convert_to_int)

                    if counter == dev_counter:
                        self.printData(pcl.buildDynamicCounter(0), direct=True)
                        # protect the value as a string during msg handling
                        if not convert_to_int:
                            value = '#' + value
                        return value

                if tries > max_tries:
                    self.printData(pcl.buildDynamicCounter(0), direct=True)
                    return None

        else:
            raise Error(ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION)



    def readPrint(self, stream=None, timeout=prop.read_timeout):
        channel_id = self.openPrint()

        log.debug("Reading channel %d..." % channel_id)

        num_bytes = 0

        if stream is None:
            buffer = ''

        while True:
            fields, data, result_code = \
                self.xmitMessage('ChannelDataIn',
                                    None,
                                    {'device-id': self.device_id,
                                      'channel-id' : channel_id,
                                      'bytes-to-read' : bytes_to_read,
                                      'timeout' : timeout,
                                    }
                                  )

            l = len(data)

            if result_code != ERROR_SUCCESS:
                log.error("Print channel read error")
                raise Error(ERROR_DEVICE_IO_ERROR)

            if l == 0:
                log.debug("End of data")
                break

            if stream is None:
                buffer = ''.join([buffer, data])
            else:
                stream.write(data)
                log.debug("Wrote %d bytes to stream." % l)

            num_bytes += l

            if self.callback is not None:
                self.callback()

        if stream is None:
            log.debug("Returned %d total bytes in buffer." % num_bytes)
            return buffer
        else:
            log.debug("Wrote %d total bytes to stream." % num_bytes)
            return num_bytes


    def writePrint(self, data):
        channel_id = self.openPrint()

        log.debug("Writing channel %d..." % channel_id)
        buffer, bytes_out, total_bytes_to_write = data, 0, len(data)

        while len(buffer) > 0:
            fields, data, result_code =                self.xmitMessage('ChannelDataOut',
                                    {
                                        'device-id': self.device_id,
                                        'channel-id' : channel_id,
                                    },
                                    buffer[:prop.max_message_len],
                                  )

            if result_code != ERROR_SUCCESS:
                log.error("Print channel write error")
                raise Error(ERROR_DEVICE_IO_ERROR)

            buffer = buffer[prop.max_message_len:]
            bytes_out += fields['bytes-written']

            if self.callback is not None:
                self.callback()

        if total_bytes_to_write != bytes_out:
            raise Error(ERROR_DEVICE_IO_ERROR)

        return bytes_out


    def writeEmbeddedPML(self, oid, value, style=1, direct=True):
        if style == 1:
            func = pcl.buildEmbeddedPML2
        else:
            func = pcl.buildEmbeddedPML

        data = func(pcl.buildPCLCmd('&', 'b', 'W',
                     pml.buildEmbeddedPMLSetPacket(oid[0],
                                                    value,
                                                    oid[1])))

        self.printData(data, direct=True)


    def printFile(self, file_name, direct=True, raw=True, remove=False):
        is_gzip = os.path.splitext(file_name)[-1].lower() == '.gz'
        log.debug("Printing file '%s' (gzip=%s, direct=%s, raw=%s, remove=%s)" %
                   (file_name, is_gzip, direct, raw, remove))

        if direct: # implies raw==True
            if is_gzip:
                self.writePrint(gzip.open(file_name, 'r').read())
            else:
                self.writePrint(file(file_name, 'r').read())

        elif len(self.cups_printers) > 0:
            if is_gzip:
                c = 'gunzip -c %s | lpr -P%s' % (file_name, cups_printers[0])
            else:
                c = 'lpr -P%s %s' % (self.cups_printers[0], file_name)

            if raw:
                c = ''.join([c, ' -l'])

            if remove:
                c = ''.join([c, ' -r'])

            log.debug(c)
            os.system(c)

        else:
            raise Error(ERROR_NO_CUPS_QUEUE_FOUND_FOR_DEVICE)


    def printData(self, data, direct=True, raw=True):
        if direct:
            self.writePrint(data)
        else:
            temp_file_fd, temp_file_name = utils.make_temp_file()
            os.write(temp_file_fd, data)
            os.close(temp_file_fd)

            self.printFile(temp_file_name, direct, raw, remove=True)

