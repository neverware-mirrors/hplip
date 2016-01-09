#!/usr/bin/env python
#
# $Revision: 1.13 $ 
# $Date: 2005/03/08 18:59:55 $
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




_VERSION = '2.1'

import sys, os, pwd, os.path, time
from base.g import *
from base.codes import *
from base import service, utils

utils.log_title( 'Toolbox/Device Manager', _VERSION )

s = None



try:
    s = service.Service()
except Error, e:
    log.error( "hpssd is not running. Unable to start toolbox. Use the startup script to start the HPLIP daemons." )
    sys.exit(1)

port, host = s.getGUI( prop.username )

if port == 0:
    log.debug( "Running new hpguid instance..." )
    hpguid_path = os.path.join( prop.home_dir, 'hpguid.py' )
    
    if os.path.exists( hpguid_path ):
        
        os.system( 'python %s' % hpguid_path ) 
        
        tries = 0
        
        while 1:
            time.sleep(0.5)
            port, host = s.getGUI( prop.username )
            tries += 1
            
            if port > 0: break
            
            if tries > 10:
                log.error( "Unable to start hpguid. Use the startup script to restart the HPLIP daemons." )
                sys.exit(1)
    else:
        log.error( "Unable to locate hpguid.py. Please check HPLIP installation for problems." )
        s.close()
        sys.exit(1)

log.info( "Launching toolbox (%s:%d)..." % (host, port ) )
s.showToolbox( prop.username )

s.close()
sys.exit(0)


