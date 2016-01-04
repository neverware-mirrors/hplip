# -*- coding: utf-8 -*-
#
# (c) Copyright 2001-2004 Hewlett-Packard Development Company, L.P.
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

import cStringIO

from qt import *
from advancedinfoform_base import AdvancedInfoForm_base

import base.utils as utils
import base.status as status
import prnt.cups as cups

class AdvancedInfoForm( AdvancedInfoForm_base ):
    def __init__(self, device, parent = None, name = None, modal = 0, fl = 0 ):
        AdvancedInfoForm_base.__init__( self, parent, name, modal, fl )
        
        t = cStringIO.StringIO()
        
        #t.write( file( '/home/dwelch/test.html', 'r').read() )
        
        t.write( '<table width="100%">' )
        
        t.write( '<tr><td><b>Item</b></td><td><b>Value</b></td>' )
        #t.write( '<hr>' )
        t.write( '<tr><td>Device URI</td>' )
        t.write( '<td>%s</td></tr>' % device.device_uri )
        
        t.write( '<tr><td>Model name</td>' )
        t.write( '<td>%s</td></tr>' % device.model )
        
        #t.write( '<tr><td>Serial No.</td>' )
        #t.write( '<td>%s</td></tr>' % device.ds.get( 'serial-number', '' ) )

        t.write( '<tr><td>CUPS back end</td>' )
        t.write( '<td>%s</td></tr>' % device.back_end )

        #t.write( '<tr><td>Device file</td>' )
        #t.write( '<td>%s</td></tr>' % device.ds.get( 'dev-file', '' ) )
        
        t.write( '<tr><td>I/O bus</td>' )
        t.write( '<td>%s</td></tr>' % device.bus )
        
        #t.write( '<tr><td>3bit status</td>' )
        #tb_i, tb_s = device.threeBitStatus()
        #t.write( '<td>%d (%s)</td></tr>' % (tb_i, tb_s ) )
        
        #t.write( '<tr><td>Device ID (raw)</td>' )
        #parsed_DeviceID, raw_DeviceID = device.ID()
        #t.write( '<td>%s</td></tr>' % raw_DeviceID )

        #t.write( '<tr><td>Device ID (parsed)</td>' )
        #t.write( '<td>%s</td></tr>' % parsed_DeviceID )
        
        #stat = status.parseStatus( parsed_DeviceID )
        #t.write( '<tr><td>Status/Agents</td></tr>' )
        #st_keys = stat.keys()
        #st_keys.sort()
        
        #for key,i in zip( st_keys, range(len(st_keys))):
        #    if key == 'agents':
        #        pens = stat['agents']
        #        print pens
        #        for p,k in zip(pens,range(len(pens))):
        #            kth_pen = pens[k]
        #            pks = kth_pen.keys()
        #            pks.sort()
        #            for pk, j in zip( pks, range(len(pks))):
        #                t.write( '<tr><td>pen %d</td><td>%s:%s</td></tr>' % ( k+1, pk, kth_pen[pk] ) )
        #    else:
        #        t.write( '<tr><td></td><td>%s:%s</td></tr>' % ( key, stat[key] ) )
    
        #t.write( '<tr><td>Model Info</td></tr>' )
    
        ds_keys = device.ds.keys()
        ds_keys.sort()
        for key,i in zip( ds_keys, range(len(ds_keys))):
            t.write( '<tr><td>%s</td><td>%s</td></tr>' % ( key, device.ds[key] ) )
                
        #cups_printers = cups.getPrinters()
        #printers = []
        #for p in cups_printers:
        #    if p.device_uri == device.device_uri:
        #        printers.append( p.name )
        
        if len( device.cups_printers ) > 0:
            t.write( '<tr><td>CUPS printers</td> <td>%s</td></tr>' %  ', '.join( device.cups_printers ) )
        else:    
            t.write( '<tr><td>CUPS printers</td> <td></td></tr>' )
                
                

        t.write( '</table>' )
        
        self.AdvInfoText.setText( t.getvalue() )
