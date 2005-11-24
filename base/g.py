#!/usr/bin/env python
#
# $Revision: 1.32 $
# $Date: 2005/11/10 17:22:08 $
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


#
# NOTE: This module is safe for 'from g import *'
#


# Std Lib
import sys
import os, os.path
import ConfigParser
import locale
import pwd

# Local
from codes import *

import logger

# System wide logger
log = logger.Logger('', logger.Logger.LOG_LEVEL_INFO, logger.Logger.LOG_TO_CONSOLE)
log.set_level('info')

MINIMUM_PYQT_MAJOR_VER = 3
MINIMUM_PYQT_MINOR_VER = 8
MINIMUM_QT_MAJOR_VER = 3
MINIMUM_QT_MINOR_VER = 0

# System wide properties
class Properties(dict):

    def __getattr__(self, attr):
        if attr in self.keys():
            return self.__getitem__(attr)
        else:
            return ""

    def __setattr__(self, attr, val):
        self.__setitem__(attr, val)

prop = Properties()

# Language settings
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    log.error("Unable to set locale.")

try:
    t, prop.encoding = locale.getdefaultlocale()
except ValueError:
    t = 'en_US'
    prop.encoding = 'ISO8859-1'

try:
    prop.lang_code = t[:2].lower()
except TypeError:
    prop.lang_code = 'en'

# Config file: directories and ports
prop.config_file = '/etc/hp/hplip.conf'

if os.path.exists(prop.config_file):
    config = ConfigParser.ConfigParser()
    config.read(prop.config_file)

    try:
        prop.hpssd_cfg_port = config.getint("hpssd", "port")
    except:
        prop.hpssd_cfg_port = 0

    try:
        prop.version = config.get('hplip', 'version')
    except:
        prop.version = ''

    try:
        prop.home_dir = config.get('dirs', 'home')
    except:
        prop.home_dir = os.path.realpath(os.path.normpath(os.getcwd()))

    try:
        prop.run_dir = config.get('dirs', 'run')
    except:
        prop.run_dir = '/var/run'

try:
    prop.hpiod_port = int(file(os.path.join(prop.run_dir, 'hpiod.port'), 'r').read())
except:
    prop.hpiod_port = 0

try:
    prop.hpssd_port = int(file(os.path.join(prop.run_dir, 'hpssd.port'), 'r').read())
except:
    prop.hpssd_port = 0


prop.hpiod_host = 'localhost'
prop.hpssd_host = 'localhost'
prop.hpfaxd_host = 'localhost'
prop.hpguid_host = 'localhost'

prop.username = pwd.getpwuid(os.getuid())[0]

prop.data_dir = os.path.join(prop.home_dir, 'data')
prop.i18n_dir = os.path.join(prop.home_dir, 'data', 'qm')
prop.image_dir = os.path.join(prop.home_dir, 'data', 'images')
prop.xml_dir = os.path.join(prop.home_dir, 'data', 'xml')
#prop.html_dir = os.path.join(prop.home_dir, 'data', 'html', prop.lang_code)

prop.max_message_len = 8192
prop.max_message_read = 65536
prop.read_timeout = 90

prop.ppd_search_path = '/usr/share;/usr/local/share;/usr/lib;/usr/local/lib;/usr/libexec;/opt'
prop.ppd_search_pattern = 'HP-*.ppd.*'
prop.ppd_download_url = 'http://www.linuxprinting.org/ppd-o-matic.cgi'
prop.ppd_file_suffix = '-hpijs.ppd'

prop.errors_file = os.path.join(prop.home_dir, 'data', 'xml', 'errors.xml')
prop.strings_file = os.path.join(prop.home_dir, 'data', 'xml', 'strings.xml')
prop.models_file = os.path.join(prop.home_dir, 'data', 'xml', 'models.xml')

# Spinner, ala Gentoo Portage
spinner = "\|/-\|/-"
#spinner = "oOo.oOo."
spinpos = 0

def update_spinner():
    global spinner, spinpos
    if sys.stdout.isatty():
        sys.stdout.write("\b" + spinner[spinpos])
        spinpos=(spinpos + 1) % 8
        sys.stdout.flush()


# Internal/messaging errors

ERROR_STRINGS = {
                ERROR_SUCCESS : 'No error',
                ERROR_UNKNOWN_ERROR : 'Unknown error',
                ERROR_DEVICE_NOT_FOUND : 'Device not found',
                ERROR_INVALID_DEVICE_ID : 'Unknown/invalid device-id field',
                ERROR_INVALID_DEVICE_URI : 'Unknown/invalid device-uri field',
                ERROR_INVALID_MSG_TYPE : 'Unknown message type',
                ERROR_INVALID_DATA_ENCODING : 'Unknown data encoding',
                ERROR_INVALID_CHAR_ENCODING : 'Unknown character encoding',
                ERROR_DATA_LENGTH_EXCEEDS_MAX : 'Data length exceeds maximum',
                ERROR_DATA_LENGTH_MISMATCH : "Data length doesn't match length field",
                ERROR_DATA_DIGEST_MISMATCH : "Digest of data doesn't match digest field",
                ERROR_INVALID_JOB_ID : 'Invalid job-id',
                ERROR_DEVICE_IO_ERROR : 'Device I/O error',
                ERROR_STRING_QUERY_FAILED : 'String/error query failed',
                ERROR_QUERY_FAILED : 'Query failed',
                ERROR_GUI_NOT_AVAILABLE : 'hpguid not running',
                ERROR_NO_CUPS_DEVICES_FOUND : 'No CUPS devices found (deprecated)',
                ERROR_NO_PROBED_DEVICES_FOUND : 'No probed devices found',
                ERROR_INVALID_BUS_TYPE : 'Invalid bus type',
                ERROR_BUS_TYPE_CANNOT_BE_PROBED : 'Bus cannot be probed',
                ERROR_DEVICE_BUSY : 'Device busy',
                ERROR_NO_DATA_AVAILABLE : 'No data avaiable',
                ERROR_INVALID_DEVICEID : 'Invalid/missing DeviceID',
                ERROR_INVALID_CUPS_VERSION : 'Invlaid CUPS version',
                ERROR_CUPS_NOT_RUNNING : 'CUPS not running',
                ERROR_DEVICE_STATUS_NOT_AVAILABLE : 'DeviceStatus not available',
                ERROR_DATA_IN_SHORT_READ: 'ChannelDataIn short read',
                ERROR_INVALID_SERVICE_NAME : 'Invalid service name',
                ERROR_INVALID_USER_ERROR_CODE : 'Invalid user level error code',
                ERROR_ERROR_INVALID_CHANNEL_ID : 'Invalid channel-id',
                ERROR_CHANNEL_BUSY : 'Channel busy/in-use',
                ERROR_CHANNEL_CLOSE_FAILED : 'ChannelClose failed. Channel not open',
                ERROR_UNSUPPORTED_BUS_TYPE : 'Unsupported bus type',
                ERROR_DEVICE_DOES_NOT_SUPPORT_OPERATION : 'Device does not support operation',
                ERROR_INTERNAL : 'Unknown internal error',
                ERROR_DEVICE_NOT_OPEN : 'Device not open',
                ERROR_UNABLE_TO_CONTACT_SERVICE : 'Unable to contact service',
                ERROR_UNABLE_TO_BIND_SOCKET : 'Unable to bind to socket',
                ERROR_DEVICEOPEN_FAILED_ONE_DEVICE_ONLY : 'Device open failed - 1 open per session allowed',
                ERROR_DEVICEOPEN_FAILED_DEV_NODE_MOVED : 'Device open failed - device node moved',
                ERROR_TEST_EMAIL_FAILED : "Email test failed",
                ERROR_SMTP_CONNECT_ERROR : "SMTP server connect error",
                ERROR_SMTP_RECIPIENTS_REFUSED : "SMTP recipients refused",
                ERROR_SMTP_HELO_ERROR : "SMTP HELO error",
                ERROR_SMTP_SENDER_REFUSED : "STMP sender refused",
                ERROR_SMTP_DATA_ERROR : "SMTP data error",
                ERROR_INVALID_HOSTNAME : "Invalid hostname ip address",
                ERROR_INVALID_PORT_NUMBER : "Invalid JetDirect port number",
                ERROR_INTERFACE_BUSY : "Interface busy",
                ERROR_NO_CUPS_QUEUE_FOUND_FOR_DEVICE : "No CUPS queue found for device.",
                ERROR_UNSUPPORTED_MODEL : "Unsupported printer model.",
               }

class Error(Exception):
    def __init__(self, opt=ERROR_INTERNAL):
        self.opt = opt
        self.msg = ERROR_STRINGS.get(opt, ERROR_STRINGS[ERROR_INTERNAL])
        log.debug("Exception: %d (%s)" % (opt, self.msg))
        Exception.__init__(self, self.msg, opt)


# Make sure True and False are avail. in pre-2.2 versions
try:
    True
except NameError:
    True = (1==1)
    False = not True



