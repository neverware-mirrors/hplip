#!/usr/bin/env python
#
# $Revision: 1.30 $ 
# $Date: 2005/03/28 22:48:12 $
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
import sys
import xml.parsers.expat
import time
import re

# Local
from g import *
from codes import *
import utils
import device
from prnt import cups
from strings import string_table

inter_pat = re.compile( r"""%(.*)%""", re.IGNORECASE )

# Available guis
guis = {}

# Per user alert settings
alerts = {}

# Device status buffers
devices_hist = {} # { "<device_uri>" : RingBuffer(), ... }


# cached model objects
models = {} # { "<model_name>" : { "<model_field>" : <data>, 
              #                    ... }, 
              # ... }


class ModelParser:

    def __init__( self ):
        self.model = None
        self.cur_model = None
        self.stack = []

    def startElement( self, name, attrs ):
        global models

        if name in ( 'id', 'models' ):
            return

        elif name == 'model':
            self.model = {} 
            self.cur_model = str( attrs[ 'name' ] ).lower()
            if self.cur_model == self.model_name:
                self.stack = []
            else:
                self.cur_model = None

        elif self.cur_model is not None:
            self.stack.append( str(name).lower() )
            if len(attrs):
                for a in attrs:
                    self.stack.append( str(a).lower() )
                    self.model[ str( '-'.join( self.stack ) ) ] = str( attrs[a] )
                    self.stack.pop()

    def endElement( self, name ):
        global models
        if name == 'model':
            if self.cur_model is not None:
                models[ self.cur_model ] = self.model 
            self.model = None
        elif name in ( 'id', 'models' ):
            return
        else:
            if self.cur_model is not None:
                self.stack.pop()


    def charData( self, data ):
        data = str(data).strip()
        if data and self.model is not None and self.cur_model is not None and self.stack:
            self.model[ str( '-'.join( self.stack ) ) ] = str( data )

    def parseModels( self, model_name ):
        self.model_name = model_name
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.startElement
        parser.EndElementHandler = self.endElement
        parser.CharacterDataHandler = self.charData
        parser.Parse( open( prop.models_file ).read(), True )
        
        # read the secondary models.xml.untested XML file if it exists
        # but only in debug mode
        if log.get_level() == log.LOG_LEVEL_DEBUG:
            untested_models_file = prop.models_file + '.untested'
            
            if utils.path_exists_safely( untested_models_file ):
                parser = xml.parsers.expat.ParserCreate()
                parser.StartElementHandler = self.startElement
                parser.EndElementHandler = self.endElement
                parser.CharacterDataHandler = self.charData
                parser.Parse( open( untested_models_file ).read(), True )


def queryModels( model_name ): 
    model_name = model_name.replace( ' ', '_' ).lower()
    if model_name not in models:
        p = ModelParser()
        p.parseModels( model_name )

    if model_name not in models:
        raise Error( ERROR_QUERY_FAILED )

    return models[ model_name ]

def initModels():
    global models
    models.clear()


def queryStrings( id, typ=0 ):
    id = str( id )
    log.debug( "String query: %s" % id )

    try:
        s = string_table[ id ][ typ ]
    except KeyError:
        raise Error( ERROR_STRING_QUERY_FAILED )

    if type( s ) == type( '' ):
        return s

    try:
        return s()
    except:
        raise Error( ERROR_STRING_QUERY_FAILED )


def initStrings():
    cycles = 0

    while True:

        found = False

        for s in string_table:
            short_string, long_string = string_table[ s ]
            short_replace, long_replace = short_string, long_string

            try:
                short_match = inter_pat.match( short_string ).group( 1 )
            except (AttributeError, TypeError):
                short_match = None

            if short_match is not None:
                found = True

                try:
                    short_replace, dummy = string_table[ short_match ] 
                except KeyError:
                    log.error( "String interpolation error: %s" % short_match )

            try:
                long_match = inter_pat.match( long_string ).group( 1 )
            except (AttributeError, TypeError):
                long_match = None

            if long_match is not None:
                found = True

                try:
                    dummy, long_replace = string_table[ long_match ] 
                except KeyError:
                    log.error( "String interpolation error: %s" % long_match )


            if found:
                string_table[ s ] = ( short_replace, long_replace )

        if not found:
            break
        else:
            cycles +=1
            if cycles > 1000:
                break




##def initHistories( hpiod_sock ):
##    global devices_hist
##    devices_hist.clear()
##    printer_list = cups.getPrinters()
##    r_values_cache = {}
##
##    for p in printer_list:
##        device_uri = p.device_uri
##
##        if not device_uri.startswith( 'hp' ):
##            continue
##
##        try:
##            devices_hist[ device_uri ]
##
##        except KeyError:
##            try:
##                back_end, is_hp, bus, model, serial, dev_file, host, port = \
##                    device.parseDeviceURI( device_uri )
##            except Error:
##                pass
##            else:
##                #if is_hp:
##                r_values = initHistory( device_uri, hpiod_sock )
##                r_values_cache[ device_uri ] = r_values
##
##    return r_values_cache

def createHistory( device_uri, code, jobid=0, username=prop.username ):
    global devices_hist
    checkHistory( device_uri )

    try:
        short_string = queryStrings( code, 0 )
    except Error:
        short_string = ''

    try:
        long_string = queryStrings( code, 1 )
    except Error:
        long_string = ''

    devices_hist[ device_uri ].append( tuple( time.localtime() ) + 
                                       ( jobid, username, code, 
                                         short_string, long_string ) )

def createIdleHistory( device_uri ):
    createHistory( device_uri, STATUS_PRINTER_IDLE )

def createNotFoundHistory( device_uri ):
    createHistory( device_uri, EVENT_ERROR_DEVICE_NOT_FOUND )

def checkHistory( device_uri ):
    """Returns True if device already has history buffer, False otherwise."""
    global devices_hist
    try:
        devices_hist[ device_uri ]
    except KeyError:
        devices_hist[ device_uri ] = utils.RingBuffer( prop.history_size )
        return False

    return True

def initHistory( device_uri, hpiod_sock ):
    log.debug( "Initializing history for %s" % device_uri )
    checkHistory( device_uri )

    d = device.Device( hpiod_sock, device_uri )

    dq, r_values, panel_check = d.deviceQuery( DEVICE_STATE_NOT_FOUND, 
                                               0, queryStrings, queryModels, None )

    d.close()

    device_state = dq[ 'device-state' ]
    status_code = dq[ 'status-code' ]

    if device_state == DEVICE_STATE_NOT_FOUND: 
        createNotFoundHistory( device_uri )

    else:
        createHistory( device_uri, status_code )


    return r_values, panel_check


#def initDatabases( hpiod_sock ):
#    initModels()
#    initStrings()
#    return initHistories( hpiod_sock )


