#!/usr/bin/env python
#
# $Revision: 1.9 $ 
# $Date: 2004/11/17 21:39:58 $
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


# Std Lib
import os
import os.path
import gzip
import re
import time
import urllib#2
import tempfile

# Local
from base.g import *
import cupsext

# PPD parsing patterns
mfg_pat = re.compile( r'\*\s*Manufacturer:\s*\".*?(.*?)\"', re.IGNORECASE )
model_pat = re.compile( r'\*\s*Product:\s*\"\(.*?(.*?)\)\"', re.IGNORECASE )

def restartCUPS(): # must be root. How do you check for this?
    os.system( 'killall -HUP cupsd' )
    
def getPPDPath( addtional_paths=[] ):
    search_paths = [ prop.ppd_search_path.split(';') ] + addtional_paths
    for path in search_paths:
        ppd_path = os.path.join( path, 'cups/model' )
        if os.path.exists( ppd_path ):
            return ppd_path
            
    
def collectPPDs( ppd_path ):
    from base import utils
    ppds = {} # { <model> : <PPD file> , ... }
    
    for f in utils.walkFiles( ppd_path, recurse=True, abs_paths=True, 
                              return_folders=False , pattern=prop.ppd_search_pattern ):

        if f.endswith( '.gz' ):
            g = gzip.open( f, 'r' )
        else:
            g = open( f, 'r' )
        
        try:
            d = g.read( 4096 )
        except IOError:
            g.close()
            continue
        try:
            mfg = mfg_pat.search( d ).group( 1 ).lower()
        except ValueError:
            g.close()
            continue
        
        if mfg != 'hp':
            continue
        
        try:
            model = model_pat.search( d ).group( 1 ).replace( ' ', '_' )
        except ValueError:
            g.close()
            continue
        
        ppds[ model ] = f
            
        g.close()
        
    return ppds    
        

def downloadPPD( model_name, url=prop.ppd_download_url ):
    model_name = 'HP-' + model_name.replace( ' ', '_' )
    u = urllib.urlopen( url, urllib.urlencode( { 'driver' : 'hpijs', 
                                                 'printer' : urllib.quote( model_name ), 
                                                 'show' : '0' } ) )
    
    ppd_file = os.path.join( tempfile.gettempdir(), model_name + prop.ppd_file_suffix )
    f = file( ppd_file, 'w' )
    f.write( u.read() )
    f.close()
    
    return ppd_file
    

def CUPSWebInterface():
    import webbrowser
    webbrowser.open_new( 'http://localhost:631/' )

    
# cupsext wrapper    

def getDefault():
    return cupsext.getDefault()
    
def getPrinters():
    return cupsext.getPrinters()
    
def getJobs( my_job=0, completed=0 ):
    return cupsext.getJobs( my_job, completed )
    
def getAllJobs( my_job=0 ):
    return cupsext.getJobs( my_job, 0 ) + cupsext.getJobs( my_job, 1 )
    
def getVersion():
    return cupsext.getVersion()

def getServer():
    return cupsext.getServer()
    
def cancelJob( jobid, dest=None ):
    if dest is not None:
        return cupsext.cancelJob( dest, jobid )
    else:
        jobs = cupsext.getJobs( 0, 0 )
        for j in jobs:
            if j.id == jobid:
                return cupsext.cancelJob( j.dest, jobid )
                
    return False
            
    
if __name__ == '__main__':
    #ppd_path = getPPDPath()
    #print ppd_path
    #t1 = time.time()
    #ppds = collectPPDs( ppd_path )
    #t2 = time.time()
    #print t2-t1
    #print ppds
    #print len( ppds )
    #print ppds[ 'PSC 2100 Series' ]
    
    #models = ppds.keys()
    #models.sort()
    #for m in models:
    #    print m, ppds[m]
        
    #print downloadPPD( "Business Inkjet 3000" )
    print getJobs()
