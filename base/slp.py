#!/usr/bin/env python
#
# $Revision: 1.15 $ 
# $Date: 2005/03/22 22:21:37 $
# $Author: pparks $
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


# Std Lib
import sys
import time
import socket
import select
import struct
import random
#import threading
import re

# Local
from g import *


prod_pat = re.compile( r"""\(\s*x-hp-prod_id\s*=\s*(.*?)\s*\)""", re.IGNORECASE )
mac_pat  = re.compile( r"""\(\s*x-hp-mac\s*=\s*(.*?)\s*\)""", re.IGNORECASE )
num_port_pat = re.compile( r"""\(\s*x-hp-num_port\s*=\s*(.*?)\s*\)""", re.IGNORECASE )
ip_pat =   re.compile( r"""\(\s*x-hp-ip\s*=\s*(.*?)\s*\)""", re.IGNORECASE )
p1_pat =   re.compile( r"""\(\s*x-hp-p1\s*=(?:\d\)|\s*(.*?)\s*;\))""", re.IGNORECASE )
p2_pat =   re.compile( r"""\(\s*x-hp-p2\s*=(?:\d\)|\s*(.*?)\s*;\))""", re.IGNORECASE )
p3_pat =   re.compile( r"""\(\s*x-hp-p3\s*=(?:\d\)|\s*(.*?)\s*;\))""", re.IGNORECASE )
hn_pat =   re.compile( r"""\(\s*x-hp-hn\s*=\s*(.*?)\s*\)""", re.IGNORECASE )
        
        

def detectNetworkDevices( mcast_addr='224.0.1.60', mcast_port=427, ttl=4, timeout=5, xid=None, qappobj = None ):
    found_devices = {}

    s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    
    try:
        addr = socket.gethostname()
        intf = socket.gethostbyname( addr )
##        log.debug("address1: %s" % intf)
    except socket.error:
##        log.warning( "GetHostByName() failed. Trying UDP socket." )
##        import fcntl
##        SIOCGIFADDR = 0x8915
##        ifname = 'eth0'
##        s1=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
##        ifr = ifname+'\0'*(16-len(ifname))+chr(socket.AF_INET)+15*'\0'
##        r= fcntl.ioctl(s1.fileno(),SIOCGIFADDR,ifr)
##        intf = '.'.join(map(str,map(ord,r[20:24])))
##        log.debug("address2: %s" % intf)
            x=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            x.connect( ('1.2.3.4',56 ) )
            intf = x.getsockname()[0]
            x.close()

    s.setblocking(0)
    ttl = struct.pack( 'b', ttl ) 
    s.setsockopt( socket.SOL_IP, socket.IP_MULTICAST_TTL, ttl )
    s.setsockopt( socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton( intf ) + socket.inet_aton( '0.0.0.0' ) )
    
    packet = ''.join( [ '\x01\x06\x00,\x00\x00en\x00\x03', 
                        struct.pack( '!H', xid or random.randint( 1, 65535 ) ),
                        '\x00\x00\x00\x18service:x-hpnp-discover:\x00\x00\x00\x00'  ] )
    
    try:
        s.sendto( packet, ( mcast_addr, mcast_port ) )
    except socket.error:
        log.error( "Unable to send broadcast SLP packet: %s" % e )
       
    time_left = timeout
    

    while time_left > 0:
        
        if qappobj is not None:
            qappobj.processEvents(0)
        
        start_time = time.time()
        r, w, e = select.select( [s], [], [], time_left )
        time_left -= ( time.time() - start_time )
        
        if qappobj is not None:
            qappobj.processEvents(0)
        
        if r == []: continue
        
        data, addr = s.recvfrom( 1024 ) 
        ver, func, length, flags, dialect, lang_code, char_encode, recv_xid, status_code, attr_length = \
            struct.unpack( "!BBHBBHHHHH", data[:16] )
            
        x = struct.unpack( "!%ds" % attr_length, data[16:] )[0].strip()
        y = {} 
        
        try:
            num_ports = int( num_port_pat.search( x ).group( 1 ) )
        except ( AttributeError, ValueError ):
            num_ports = 1
            
        if num_ports == 0: # Embedded devices
            num_ports = 1
         
        y['num_ports'] = num_ports
        y['num_devices'] = 0
        y['device1'] = '0'
        y['device2'] = '0'
        y['device3'] = '0'
        
        # Check port 1
        try:
            y[ 'device1' ] = p1_pat.search( x ).group( 1 )
        except AttributeError:
            y['device1'] = '0'
        else:
            y['num_devices'] += 1
        
        
        if num_ports > 1: # Check port 2
            try:
                y[ 'device2' ] = p2_pat.search( x ).group( 1 )
            except AttributeError:
                y[ 'device2' ] = '0'
            else:
                y[ 'num_devices' ] += 1
            
            
            if num_ports > 2: # Check port 3
                try:
                    y[ 'device3' ] = p3_pat.search( x ).group( 1 )
                except AttributeError:
                    y[ 'device3' ] = '0'
                else:
                    y['num_devices'] += 1
        
        if y['device1'] is None:
            y['device1'] = '0'
        
        if y['device2'] is None:
            y['device2'] = '0'
        
        if y['device3'] is None:
            y['device3'] = '0'
        
        try:
            y[ 'product_id' ] = prod_pat.search( x ).group( 1 )
        except AttributeError:
            y[ 'product_id' ] = ''
        try:
            y[ 'mac' ] = mac_pat.search( x ).group( 1 )
        except AttributeError:
            y[ 'mac' ] = ''
        try:
            y[ 'ip' ] = ip_pat.search( x ).group( 1 )
        except AttributeError:
            y[ 'ip' ] = ''
        try:
            y[ 'hn' ] = hn_pat.search( x ).group( 1 )
        except AttributeError:
            y[ 'hn' ] = ''

        y[ 'status_code' ] = status_code
        found_devices[ addr[0] ] = y

        
    return found_devices
    