#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2006 Hewlett-Packard Development Company, L.P.
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

__version__ = '1.1'
__title__ = 'CUPS Fax Backend (hpfax:)'
__doc__ = "CUPS backend for PC send fax. Generally this backend is run by CUPS, not directly by a user. To send a fax as a user, run hp-sendfax"

import sys
import getopt
import ConfigParser
import os.path, os
import socket
import syslog

config_file = '/etc/hp/hplip.conf'
home_dir = ''

if os.path.exists(config_file):
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    try:
        home_dir = config.get('dirs', 'home')
    except:
        syslog.syslog(syslog.LOG_CRIT, "hpfax: Error setting home directory: home= under [dirs] not found.")
        sys.exit(1)
else:
    syslog.syslog(syslog.LOG_CRIT, "hpfax: Error setting home directory: /etc/hp/hplip.conf not found.")
    sys.exit(1)

if not home_dir or not os.path.exists(home_dir):
    syslog.syslog(syslog.LOG_CRIT, "hpfax: Error setting home directory: home directory %s not found." % home_dir)
    sys.exit(1)

sys.path.insert( 0, home_dir )

try:
    from base.g import *
    from base.codes import *
    from base import device, utils, msg
    from base.service import sendEvent
except ImportError:
    syslog.syslog(syslog.LOG_CRIT, "Error importing HPLIP modules.")
    sys.exit(1)


USAGE = [(__doc__, "", "para", True),
         ("Usage: hpfax [OPTIONS] [job_id] [username] [title] [copies] [options]", "", "summary", True),
         utils.USAGE_OPTIONS,
         utils.USAGE_LOGGING1, utils.USAGE_LOGGING2,
         utils.USAGE_HELP,
        ]

def usage(typ='text'):
    if typ == 'text':
        utils.log_title(__title__, __version__)
        
    utils.format_text(USAGE, typ, title=__title__, crumb='hpfax:')
    sys.exit(0)        
    

try:
    opts, args = getopt.getopt(sys.argv[1:], 'l:h', ['level=', 'help', 'help-rest', 'help-man'])

except getopt.GetoptError:
    usage()

for o, a in opts:

    if o in ('-l', '--logging'):
        log_level = a.lower().strip()
        log.set_level(log_level)

    elif o in ('-h', '--help'):
        usage()
        
    elif o == '--help-rest':
        usage('rest')
    
    elif o == '--help-man':
        usage('man')
        

log.set_module("hpfax")

if len( args ) == 0:
    try:
        devices = device.probeDevices(sock=None, bus='usb,par', timeout=5,
                                      ttl=4, filter='fax', format='cups')
    except Error:
        log.stderr("ERROR: Unable to contact HPLIP I/O (hpssd).")
        sys.exit(1)

    if len(devices):
        for d in devices:
            print d.replace('hp:/', 'hpfax:/')
    else:
        print 'direct hpfax:/no_device_found "Unknown" "hpfax no_device_found"'
        
    sys.exit(0)

else:
    # CUPS provided environment
    try:
        device_uri = os.environ['DEVICE_URI']
        printer_name = os.environ['PRINTER']
    except KeyError:
        log.stderr("ERROR: Improper environment: Must be run by CUPS.")
        sys.exit(1)
        
    log.debug(args)
    
    try:
        job_id, username, title, copies, options = args[0:5]
    except IndexError:
        log.stderr("ERROR: Invalid command line: Invalid arguments.")
        sys.exit(1)
        
    try:
        input_fd = file(args[5], 'r')
    except IndexError:
        input_fd = 0
        
    #log.error("INFO: URI=%s, Printer=%s, Job ID=%s, User=%s, Title=%s, Copies=%s, Options=%s" % \
    #    (device_uri, printer_name, job_id, username, title, copies, options))

    pdb = pwd.getpwnam(username)
    home_folder, uid, gid = pdb[5], pdb[2], pdb[3]
    
    #log.error("INFO: User home=%s, Uid=%d, Gid=%d" % (home_folder, uid, gid))
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((prop.hpssd_host, prop.hpssd_port))
    except socket.error:
        log.error("ERROR: Unable to contact HPLIP I/O (hpssd).")
        sys.exit(1)

    try:
        fields, data, result_code = \
            msg.xmitMessage(sock, "HPFaxBegin", 
                                 None,
                                 {"username": username,
                                  "job-id": job_id,
                                  "device-uri": device_uri,
                                  "printer": printer_name,
                                  "title": title,
                                 })
                           
    except Error:
        log.stderr("ERROR: Unable to send event to HPLIP I/O (hpssd).")
        sys.exit(1) 
   
    if result_code == ERROR_GUI_NOT_AVAILABLE:
        # New behavior in 0.9.11
        log.stderr("ERROR: You must run hp-sendfax first. Run hp-sendfax now and then restart this queue to continue.")
        
        sendEvent(sock, EVENT_ERROR_FAX_MUST_RUN_SENDFAX_FIRST, 'event',
                  job_id, username, device_uri)
        
        sys.exit(1)

    bytes_read = 0
    while True:
        data = os.read(input_fd, prop.max_message_len)
        
        if not data:
            fields, data, result_code = \
                msg.xmitMessage(sock, "HPFaxEnd", 
                                     None,
                                     {"username": username,
                                      "job-id": job_id,
                                      "printer": printer_name,
                                      "title": title,
                                      "options": options,
                                      "device-uri": device_uri,
                                      "job-size": bytes_read,
                                     })
            
            break
                                   
            
        bytes_read += len(data) 
        
        fields, data, result_code = \
            msg.xmitMessage(sock, "HPFaxData", 
                                 data,
                                 {"username": username,
                                  "job-id": job_id,
                                 })

    os.close(input_fd)
    
    if not bytes_read:
        log.error("No data!")
        sys.exit(1)
    
    sock.close()
    sys.exit(0)
    
    
