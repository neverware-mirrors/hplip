#!/usr/bin/env python
#
# $Revision: 1.19 $ 
# $Date: 2004/12/21 19:19:24 $
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
log = logger.Logger( '', logger.Logger.LOG_LEVEL_INFO, logger.Logger.LOG_TO_CONSOLE )
log.set_level( 'info' )

MINIMUM_PYQT_MAJOR_VER = 3
MINIMUM_PYQT_MINOR_VER = 8
MINIMUM_QT_MAJOR_VER = 3
MINIMUM_QT_MINOR_VER = 0

# System wide properties
class Properties(dict):

    def __getattr__( self, attr ):
        if attr in self.keys():
            return self.__getitem__( attr )
        else:
            return ""
        
    def __setattr__( self, attr, val ):
        self.__setitem__( attr, val )
        
prop = Properties()

# Language settings
locale.setlocale( locale.LC_ALL, '' )

try:
    t, prop.encoding = locale.getdefaultlocale()
except ValueError:
    t = 'en_US'
    prop.encoding = 'ISO8859-1'
    
try:
    prop.lang_code = t[ :2 ].lower()
except TypeError:
    prop.lang_code = 'en'

# Config file: directories and ports
prop.config_file = '/etc/hp/hplip.conf'

if os.path.exists( prop.config_file ):
    config = ConfigParser.ConfigParser()
    config.read( prop.config_file )

    try:
        prop.hpssd_cfg_port = config.getint( "hpssd", "port" )
    except:
        prop.hpssd_cfg_port = 0

    try:
        prop.version = config.get( 'hplip', 'version' )
    except:
        prop.version = ''

    try:
        prop.home_dir = config.get( 'dirs', 'home' )
    except:
        prop.home_dir = os.path.realpath( os.path.normpath( os.getcwd() ) )

try:
    prop.hpiod_port = int( file( '/var/run/hpiod.port', 'r' ).read() )
except:
    prop.hpiod_port = 0
    
try:
    prop.hpssd_port = int( file( '/var/run/hpssd.port', 'r' ).read() )
except:
    prop.hpssd_port = 0
    
        
prop.hpiod_host = 'localhost'
prop.hpssd_host = 'localhost'
prop.hpguid_host = 'localhost'

prop.username = pwd.getpwuid(os.getuid())[0]

prop.data_dir = os.path.join( prop.home_dir, 'data' )
prop.i18n_dir = os.path.join( prop.home_dir, 'data', 'qm' )
prop.image_dir = os.path.join( prop.home_dir, 'data', 'images' )
prop.html_dir = os.path.join( prop.home_dir, 'data', 'html', prop.lang_code )

prop.max_message_len = 8192
prop.ppd_search_path = '/usr/share;/usr/local/share;/usr/lib;/usr/local/lib;/usr/libexec;/opt'
prop.ppd_search_pattern = 'HP-*.ppd.*'
prop.ppd_download_url = 'http://www.linuxprinting.org/ppd-o-matic.cgi'
prop.ppd_file_suffix = '-hpijs.ppd'

prop.errors_file = os.path.join( prop.home_dir, 'data', 'xml', 'errors.xml' )
prop.strings_file = os.path.join( prop.home_dir, 'data', 'xml', 'strings.xml' )
prop.models_file = os.path.join( prop.home_dir, 'data', 'xml', 'models.xml' )

# Spinner, ala Gentoo Portage
spinner = "\|/-\|/-"
#spinner = "oOo.oOo."
spinpos = 0

def update_spinner():
    global spinner, spinpos
    if sys.stdout.isatty():
        sys.stdout.write( "\b" + spinner[ spinpos ] )
        spinpos=( spinpos + 1 ) % 8
        sys.stdout.flush()


# Internal/messaging errors

class Error( Exception ):
    def __init__( self, opt=ERROR_INTERNAL ):
        self.opt = opt
        self.msg = ERROR_STRINGS.get( opt, ERROR_STRINGS[ ERROR_INTERNAL ] )
        log.debug( "Exception: %d (%s)" % ( opt, self.msg ) )
        Exception.__init__( self, self.msg, opt  )
        
        
# Make sure True and False are avail. in pre-2.2 versions
try:
    True
except:
    True = (1==1)
    False = not True



