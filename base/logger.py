#!/usr/bin/env python
#
# $Revision: 1.9 $ 
# $Date: 2005/06/28 23:13:58 $
# $Author: dwelch $
#
# (c) Copyright 2002-2004 Hewlett-Packard Development Company, L.P.
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
# Authors: Doug Deprenger, Don Welch
#



# Std Lib
import os
import sys
import thread
import syslog
import traceback

# 3rd Party

# Local



class Logger( object ):

    LOG_LEVEL_NONE = 99
    LOG_LEVEL_FATAL = 6
    LOG_LEVEL_ERROR = 5
    LOG_LEVEL_WARN = 4
    LOG_LEVEL_INFO = 3
    LOG_LEVEL_DEBUG = 2
    LOG_LEVEL_DBG = 2

    logging_levels = { 'none' : LOG_LEVEL_NONE,
                       'fata' : LOG_LEVEL_FATAL,
                       'fatal' : LOG_LEVEL_FATAL,
                       'erro' : LOG_LEVEL_ERROR,
                       'error' : LOG_LEVEL_ERROR,
                       'warn' : LOG_LEVEL_WARN,
                       'info' : LOG_LEVEL_INFO,
                       'debu' : LOG_LEVEL_DEBUG,
                       'debug' : LOG_LEVEL_DEBUG }
                  
    
    LOG_TO_DEV_NULL = 0
    LOG_TO_CONSOLE = 1
    LOG_TO_SCREEN = 1
    LOG_TO_FILE = 2
    LOG_TO_CONSOLE_AND_FILE = 3
    LOG_TO_BOTH = 3
    
    
    def __init__( self, module='', level=LOG_LEVEL_INFO, where=LOG_TO_CONSOLE_AND_FILE, log_datetime=False, log_file=None ):
        self.set_level( level )
        self._where = where
        self._log_file = log_file
        self._log_datetime = log_datetime
        self._lock = thread.allocate_lock()
        self.module = module

    def set_level( self, level ):
        if type( level ) is str:
            self._level = Logger.logging_levels.get( level[:4].lower(), Logger.LOG_LEVEL_INFO )
        else:
            self._level = level
                               
    def set_module( self, module ):
        self.module = module
    
    def get_level( self ):
        return self._level

    level = property( get_level, set_level )

    def log( self, message, level ):
        try:
            self._lock.acquire()
            if level >= Logger.LOG_LEVEL_WARN:
                out = sys.stderr
            else:
                out = sys.stdout
            out.write( message )
            out.write( '\n' )
        finally:
            self._lock.release()

    def debug( self, message ):
        if self._level <= Logger.LOG_LEVEL_DEBUG:
            self.log( "%s%s [DEBUG]: %s%s" % ( '\x1b[34;01m', self.module, message, '\x1b[0m' ), Logger.LOG_LEVEL_DEBUG )
            syslog.syslog( syslog.LOG_DEBUG, "%s [DEBUG] %s" % (self.module, message ) )

    dbg = debug

    def info( self, message ):
        if self._level <= Logger.LOG_LEVEL_INFO:
            self.log( "%s %s" % (self.module, message ), Logger.LOG_LEVEL_INFO )

    information = info
   
    def warn( self, message ):
        if self._level <= Logger.LOG_LEVEL_WARN:
            self.log( "%s%s [WARNING]: %s%s" % ( '\x1b[31;01m', self.module, message, '\x1b[0m' ), Logger.LOG_LEVEL_WARN )
            syslog.syslog( syslog.LOG_WARNING, "%s [WARN] %s" % (self.module, message ) )

    warning = warn

    def error( self, message ):
        if self._level <= Logger.LOG_LEVEL_ERROR:
            self.log( "%s%s [ERROR]: %s%s" % ( '\x1b[31;01m', self.module, message, '\x1b[0m' ), Logger.LOG_LEVEL_ERROR )
            syslog.syslog( syslog.LOG_ALERT, "%s [ERROR] %s" % (self.module, message ) )

    def fatal( self, message ):
        if self._level <= Logger.LOG_LEVEL_FATAL:
            self.log( "%s%s [FATAL]: %s%s" % ( '\x1b[31;01m', self.module, message, '\x1b[0m' ), Logger.LOG_LEVEL_DEBUG )
            syslog.syslog( syslog.LOG_CRIT, "%s [FATAL] %s" % (self.module, message ) )

    def exception( self ):
        typ, value, tb = sys.exc_info()
        body = "Traceback (innermost last):\n"
        lst = traceback.format_tb(tb) + traceback.format_exception_only(typ, value)
        body = body + "%-20s %s" % (''.join( lst[:-1] ), lst[-1], )
        self.fatal( body )
