#!/usr/bin/env python
#
# $Revision: 1.20 $
# $Date: 2005/07/21 23:50:32 $
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


_VERSION = '1.3'

# Std Lib
import sys, getopt, re, socket

# Local
from base.g import *
from base import device, utils, slp, msg

def usage():
    formatter = utils.usage_formatter()
    log.info( utils.bold( """\nUsage: hp-probe [OPTIONS]\n\n""" ) )
    utils.usage_options()
    utils.usage_logging(formatter)
    utils.usage_bus(formatter)
    log.info( formatter.compose( ( "TTL:", "-t<ttl> or --ttl=<ttl>" ) ) )
    log.info( formatter.compose( ( "", "(Network only)" ) ) )
    log.info( formatter.compose( ( "Timeout:", "-o<timeout in secs> or --timeout=<timeout in secs>" ) ) )
    log.info( formatter.compose( ( "", "(Network only)" ) ) )
    log.info( formatter.compose( ( "Filter:", "-e<filter list> or --filter=<filter list>" ) ) )
    log.info( formatter.compose( ( "", "<filter list>: comma separated list of one or more of: scan, pcard, fax, copy, or none*. (*none is the default)" ) ) )
    log.info( formatter.compose( ( "Search:", "-s<search re> or --search=<search re>" ) ) )
    log.info( formatter.compose( ( "", "<search re> must be a valid regular expression (not case sensitive)" ) ) )
    utils.usage_help(formatter, True)
    utils.usage_examples()
    log.info(  """\nFind all devices on the network:\n\thp-probe -bnet\n\n""" \
               """Find all devices on USB that support scanning:\n\thp-probe -busb -escan\n\n""" \
               """Find all networked devices that contain the name 'lnx' and that support photo cards or scanning:\n\thp-probe -bnet -slnx -escan,pcard\n\n"""
               """Find all devices that are on the USB or parallel buses or that are installed in CUPS:\n\thp-probe\n\n"""
            )


    sys.exit(0)

utils.log_title( 'Device Detection (Probe) Utility', _VERSION )

try:
    opts, args = getopt.getopt( sys.argv[1:],
                                'hl:b:t:o:e:s:',
                                [ 'help',
                                  'logging=',
                                  'bus=',
                                  'event=',
                                  'ttl=',
                                  'timeout=',
                                  'filter=',
                                  'search='
                                ]
                              )
except getopt.GetoptError:
    usage()

log_level = logger.DEFAULT_LOG_LEVEL
bus = device.DEFAULT_PROBE_BUS
align_debug = False
format='cups'
timeout=5
ttl=4
filter = 'none'
search = None

for o, a in opts:

    if o in ( '-h', '--help' ):
        usage()

    elif o in ( '-b', '--bus' ):
        bus = a.lower().strip()

    elif o in ( '-l', '--logging' ):
        log_level = a.lower().strip()

    elif o in ( '-t', '--ttl' ):
        try:
            ttl = int( a )
        except ValueError:
            ttl = 4

    elif o in ( '-o', '--timeout' ):
        try:
            timeout = int( a )
            if timeout > 44:
                timeout = 44
        except ValueError:
            timeout = 5

    elif o in ( '-f', '--format' ):
        format = a.lower().strip()

    elif o in ( '-e', '--filter' ):
        filter = a.lower().strip()

    elif o in ( '-s', '--search' ):
        search = a.lower().strip()


if not device.validateBusList(bus):
    usage()

if not log.set_level( log_level ):
    usage()

if timeout < 0:
    log.error( "You must specify a positive timeout in seconds." )
    usage()

if not device.validateFilterList(filter):
    usage()

hpssd_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
hpssd_sock.connect( ( prop.hpssd_host, prop.hpssd_port ) )

fields, data, result_code = \
    msg.xmitMessage( hpssd_sock,
                     "ProbeDevicesFiltered",
                      None,
                      {
                            'bus' : bus,
                            'timeout' : timeout,
                            'ttl' : ttl,
                            'format' : 'cups',
                            'filter' : filter,

                      }
                    )

hpssd_sock.close()

pat = re.compile( r'(.*?)\s(.*?)\s"(.*?)"\s"(.*?)"', re.IGNORECASE )

max_c1 = 0
max_c2 = 0
max_c3 = 0
dd = data.splitlines()

if len(dd) > 0:

    if search is not None:
        try:
            search_pat = re.compile( search, re.IGNORECASE )
        except:
            log.error( "Invalid search pattern. Search uses standard regular expressions. For more info, see: http://www.amk.ca/python/howto/regex/" )
            sys.exit(0)

        ee = []
        for d in dd:
            match_obj = search_pat.search( d )
            if match_obj is not None:
                ee.append(d)

        if len(ee) == 0:
            log.warn( "No devices found that match search criteria." )
            sys.exit(0)
    else:
        ee = dd

    for d in ee:
        x = pat.search( d )
        c1 = x.group(2)
        max_c1 = max( len(c1), max_c1 )
        c2 = x.group(3)
        max_c2 = max( len(c2), max_c2 )
        c3 = x.group(4)
        max_c3 = max( len(c3), max_c3 )

    formatter = utils.TextFormatter(
                (
                    {'width': max_c1, 'margin' : 2},
                    {'width': max_c2, 'margin' : 2},
                    {'width': max_c3, 'margin' : 2},
                )
            )

    if bus == 'net':
        log.info( formatter.compose( ( "Device URI", "Model", "Name" ) ) )
        log.info( formatter.compose( ( '-'*max_c1, '-'*max_c2, '-'*max_c3 ) ) )
        for d in ee:
            x = pat.search( d )
            uri = x.group(2)
            name = x.group(3)
            model = x.group(4)
            log.info( formatter.compose( ( uri, name, model ) ) )
    else:
        log.info( formatter.compose( ( "Device URI", "Model", "" ) ) )
        log.info( formatter.compose( ( '-'*max_c1, '-'*max_c2, "" ) ) )
        for d in ee:
            x = pat.search( d )
            uri = x.group(2)
            model = x.group(3)
            log.info( formatter.compose( ( uri, model, "" ) ) )
else:
    log.warn( "No devices found. If this isn't the result you are expecting," )

    if bus == 'net':
        log.warn( "check your network connections and make sure your internet" )
        log.warn( "firewall software is disabled." )
    else:
        log.warn( "check to make sure your devices are properly connected." )



