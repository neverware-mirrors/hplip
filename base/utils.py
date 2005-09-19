#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Revision: 1.62 $
# $Date: 2005/09/08 18:23:07 $
# $Author: dwelch $
#
# (c) Copyright 2001-2005 Hewlett-Packard Development Company, L.P.
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
# Thanks to Henrique M. Holschuh <hmh@debian.org> for various security patches
#

from __future__ import generators

# Std Lib
import sys, os, fnmatch, tempfile, socket, struct, select, time
import fcntl, errno, stat, string, xml.parsers.expat, commands

# Local
from g import *
from codes import *


def Translator(frm='', to='', delete='', keep=None):
    allchars = string.maketrans('','')

    if len(to) == 1:
        to = to * len(frm)
    trans = string.maketrans(frm, to)

    if keep is not None:
        delete = allchars.translate(allchars, keep.translate(allchars, delete))

    def callable(s):
        return s.translate(trans, delete)

    return callable

# For pidfile locking (must be "static" and global to the whole app)
prv_pidfile = None
prv_pidfile_name = ""


def get_pidfile_lock ( a_pidfile_name="" ):
    """ Call this to either lock the pidfile, or to update it after a fork()
        Credit: Henrique M. Holschuh <hmh@debian.org>
    """
    global prv_pidfile
    global prv_pidfile_name
    if prv_pidfile_name == "":
        try:
            prv_pidfile_name = a_pidfile_name
            prv_pidfile = os.fdopen(os.open(prv_pidfile_name, os.O_RDWR | os.O_CREAT, 0644), 'r+')
            fcntl.fcntl(prv_pidfile.fileno(), fcntl.F_SETFD, fcntl.FD_CLOEXEC)
            while 1:
                try:
                    fcntl.flock(prv_pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (OSError, IOError), e:
                    if e.errno == errno.EINTR:
                        continue
                    elif e.errno == errno.EWOULDBLOCK:
                        try:
                            prv_pidfile.seek(0)
                            otherpid = int(prv_pidfile.readline(), 10)
                            sys.stderr.write ("can't lock %s, running daemon's pid may be %d\n" % (prv_pidfile_name, otherpid))
                        except (OSError, IOError), e:
                            sys.stderr.write ("error reading pidfile %s: (%d) %s\n" % (prv_pidfile_name, e.errno, e.strerror))

                        sys.exit(1)
                    sys.stderr.write ("can't lock %s: (%d) %s\n" % (prv_pidfile_name, e.errno, e.strerror))
                    sys.exit(1)
                break
        except (OSError, IOError), e:
            sys.stderr.write ("can't open pidfile %s: (%d) %s\n" % (prv_pidfile_name, e.errno, e.strerror))
            sys.exit(1)
    try:
        prv_pidfile.seek(0)
        prv_pidfile.write("%d\n" % (os.getpid()))
        prv_pidfile.flush()
        prv_pidfile.truncate()
    except (OSError, IOError), e:
        log.error("can't update pidfile %s: (%d) %s\n" % (prv_pidfile_name, e.errno, e.strerror))



def daemonize ( stdin='/dev/null', stdout='/dev/null', stderr='/dev/null' ):
    """
    Credit: Jürgen Hermann, Andy Gimblett, and Noah Spurrier
            http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012

    Proper pidfile support: Henrique M. Holschuh <hmh@debian.org>
    """
    # Try to lock pidfile if not locked already
    if prv_pidfile_name != '' or prv_pidfile_name != "":
        get_pidfile_lock( prv_pidfile_name )

    # Do first fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0) # Exit first parent.
    except OSError, e:
        sys.stderr.write ("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror)    )
        sys.exit(1)

    # Decouple from parent environment.
    os.chdir("/")
    os.umask(0)
    os.setsid()

    # Do second fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0) # Exit second parent.
    except OSError, e:
        sys.stderr.write ("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror)    )
        sys.exit(1)

    if prv_pidfile_name != "":
        get_pidfile_lock()

    # Now I am a daemon!

    # Redirect standard file descriptors.
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())



def ifelse( cond, t, f ):
    if cond: return t
    else: return f

def to_bool_str( s, default='0' ):
    """ Convert an arbitrary 0/1/T/F/Y/N string to a normalized string 0/1."""
    if len( s ):
        if s[0].lower() in [ '1', 't', 'y' ]:
            return '1'
        elif s[0].lower() in [ '0', 'f', 'n' ]:
            return '0'

    return default

def to_bool( s, default=False ):
    """ Convert an arbitrary 0/1/T/F/Y/N string to a boolean True/False value."""
    if len( s ):
        if s[0].lower() in [ '1', 't', 'y' ]:
            return True
        elif s[0].lower() in [ '0', 'f', 'n' ]:
            return False

    return default

def path_exists_safely( path ):
    """ Returns True if path exists, and points to a file with permissions at least as strict as 0755.
        Credit: Contributed by Henrique M. Holschuh <hmh@debian.org>"""
    try:
        pathmode = os.stat( path )[stat.ST_MODE]
        if pathmode & 0022 != 0:
            return False
    except (IOError,OSError):
        return False
    return True


def walkFiles( root, recurse=True, abs_paths=False, return_folders=False, pattern='*', path=None ):
    if path is None:
        path = root

    try:
        names = os.listdir( root )
    except os.error:
        raise StopIteration

    pattern = pattern or '*'
    pat_list = pattern.split( ';' )

    for name in names:
        fullname = os.path.normpath( os.path.join( root, name ) )

        for pat in pat_list:
            if fnmatch.fnmatch( name, pat ):
                if return_folders or not os.path.isdir( fullname ):
                    if abs_paths:
                        yield fullname
                    else:
                        try:
                            yield fullname[ fullname.find( path ) + len( path ) : ]
                        except ValueError:
                            yield fullname

        if os.path.islink( fullname ):
            fullname = os.path.realpath( os.readlink( fullname ) )

        if recurse and os.path.isdir( fullname ) or os.path.islink( fullname ):
            for f in walkFiles( fullname, recurse, abs_paths, return_folders, pattern, path ):
                yield f


def is_path_writable( path ):

    if os.path.exists( path ):
        s = os.stat( path )
        mode = s[ stat.ST_MODE ] & 0777

        if mode & 02:
            return True
        elif s[ stat.ST_GID ] == os.getgid() and mode & 020:
            return True
        elif s[ stat.ST_UID ] == os.getuid() and mode & 0200:
            return True

    return False


# Provides the TextFormatter class for formatting text into columns.
# Original Author: Hamish B Lawson, 1999
# Modified by: Don Welch, 2003
class TextFormatter:

    LEFT  = 0
    CENTER = 1
    RIGHT  = 2

    def __init__( self, colspeclist ):
        self.columns = []
        for colspec in colspeclist:
            self.columns.append( Column( **colspec ) )

    def compose(self, textlist, add_newline=False):
        numlines = 0
        textlist = list(textlist)
        if len(textlist) != len(self.columns):
            log.error( "Formatter: Number of text items does not match columns" )
            return
        for text, column in map(None, textlist, self.columns):
            column.wrap(text)
            numlines = max(numlines, len(column.lines))
        complines = [''] * numlines
        for ln in range(numlines):
            for column in self.columns:
                complines[ln] = complines[ln] + column.getline(ln)
        if add_newline:
            return '\n'.join(complines) + '\n'
        else:
            return '\n'.join(complines)

    def bold( text ):
        return ''.join( [ "\033[1m", text, "\033[0m" ] )

    bold = staticmethod( bold )


class Column:

    def __init__(self, width=78, alignment=TextFormatter.LEFT, margin=0):
        self.width = width
        self.alignment = alignment
        self.margin = margin
        self.lines = []

    def align(self, line):
        if self.alignment == TextFormatter.CENTER:
            return line.center(self.width)
        elif self.alignment == TextFormatter.RIGHT:
            return line.rjust(self.width)
        else:
            return line.ljust(self.width)

    def wrap(self, text):
        self.lines = []
        words = []
        for word in text.split():
            if word <= self.width:
                words.append(word)
            else:
                for i in range(0, len(word), self.width):
                    words.append(word[i:i+self.width])
        if not len(words): return
        current = words.pop(0)
        for word in words:
            increment = 1 + len(word)
            if len(current) + increment > self.width:
                self.lines.append(self.align(current))
                current = word
            else:
                current = current + ' ' + word
        self.lines.append(self.align(current))

    def getline(self, index):
        if index < len(self.lines):
            return ' '*self.margin + self.lines[index]
        else:
            return ' ' * (self.margin + self.width)





class Stack:
    def __init__( self ):
        self.stack = []

    def pop( self ):
        return self.stack.pop()

    def push( self, value ):
        self.stack.append( value )

    def as_list( self ):
        return self.stack

    def clear( self ):
        self.stack = []


# RingBuffer class
# Source: Python Cookbook 1st Ed., sec. 5.18, pg. 201
# Credit: Sebastien Keim
# License: Modified BSD
class RingBuffer:
    def __init__(self,size_max=50):
        self.max = size_max
        self.data = []
    def append(self,x):
        """append an element at the end of the buffer"""
        self.data.append(x)
        if len(self.data) == self.max:
            self.cur=0
            self.__class__ = RingBufferFull
    def get(self):
        """ return a list of elements from the oldest to the newest"""
        return self.data


class RingBufferFull:
    def __init__(self,n):
        #raise "you should use RingBuffer"
        pass
    def append(self,x):
        self.data[self.cur]=x
        self.cur=(self.cur+1) % self.max
    def get(self):
        return self.data[self.cur:]+self.data[:self.cur]


# CRC routines for RP
if 0:
    def updateCRC( crc, ch ):
        ch = ord(ch)
        for i in range( 8 ):
            if ( (crc ^ ch ) & 1 ):
                crc = ( crc >> 1 ) ^ 0xa001
            else:
                crc = crc >> 1
            ch = ch >> 1

        return crc



# 16-bit CRCs should detect 65535/65536 or 99.998% of all errors in
# data blocks up to 4096 bytes
MASK_CCITT  = 0x1021     # CRC-CCITT mask (ISO 3309, used in X25, HDLC)
MASK_CRC16  = 0xA001     # CRC16 mask (used in ARC files)

#----------------------------------------------------------------------------
# Calculate and return an incremental CRC value based on the current value
# and the data bytes passed in as a string.
#
def updateCRC(crc, data, mask=MASK_CRC16):

    for char in data:
        c = ord(char)
        c = c << 8L

        for j in xrange(8):
            if (crc ^ c) & 0x8000L:
                crc = (crc << 1L) ^ mask
            else:
                crc = crc << 1L
            c = c << 1L

    return crc & 0xffffL

def calcCRC( data ):
    crc = 0
    #for c in data:
    #    crc = updateCRC( crc, c )

    crc = updateCRC( crc, data )

    if crc == 0:
        crc = len( data )

    return crc




def sort_dict_by_value(d):
    """ Returns the keys of dictionary d sorted by their values """
    items=d.items()
    backitems=[ [v[1],v[0]] for v in items]
    backitems.sort()
    return [ backitems[i][1] for i in range(0,len(backitems))]


# Copied from Gentoo Portage output.py
# Copyright 1998-2003 Daniel Robbins, Gentoo Technologies, Inc.
# Distributed under the GNU Public License v2

codes={}
codes["reset"]="\x1b[0m"
codes["bold"]="\x1b[01m"

codes["teal"]="\x1b[36;06m"
codes["turquoise"]="\x1b[36;01m"

codes["fuscia"]="\x1b[35;01m"
codes["purple"]="\x1b[35;06m"

codes["blue"]="\x1b[34;01m"
codes["darkblue"]="\x1b[34;06m"

codes["green"]="\x1b[32;01m"
codes["darkgreen"]="\x1b[32;06m"

codes["yellow"]="\x1b[33;01m"
codes["brown"]="\x1b[33;06m"

codes["red"]="\x1b[31;01m"
codes["darkred"]="\x1b[31;06m"


def bold(text):
    return codes["bold"]+text+codes["reset"]

def white(text):
    return bold(text)

def teal(text):
    return codes["teal"]+text+codes["reset"]

def turquoise(text):
    return codes["turquoise"]+text+codes["reset"]

def darkteal(text):
    return turquoise(text)

def fuscia(text):
    return codes["fuscia"]+text+codes["reset"]

def purple(text):
    return codes["purple"]+text+codes["reset"]

def blue(text):
    return codes["blue"]+text+codes["reset"]

def darkblue(text):
    return codes["darkblue"]+text+codes["reset"]

def green(text):
    return codes["green"]+text+codes["reset"]

def darkgreen(text):
    return codes["darkgreen"]+text+codes["reset"]

def yellow(text):
    return codes["yellow"]+text+codes["reset"]

def brown(text):
    return codes["brown"]+text+codes["reset"]

def darkyellow(text):
    return brown(text)

def red(text):
    return codes["red"]+text+codes["reset"]

def darkred(text):
    return codes["darkred"]+text+codes["reset"]


def commafy(val):
    return val < 0 and '-' + commafy( abs( val ) ) \
        or val < 1000 and str( val ) \
        or '%s,%03d' % ( commafy( val / 1000 ), (val % 1000) )


def format_bytes( s, show_bytes=False ):
    if s < 1024:
        return ''.join( [ commafy( s ), ' B' ] )
    elif 1024 < s < 1048576:
        if show_bytes:
            return ''.join( [ str( round( s/1024.0, 1 ) ) , ' KB (',  commafy(s), ')' ] )
        else:
            return ''.join( [ str( round( s/1024.0, 1 ) ) , ' KB' ] )
    else:
        if show_bytes:
            return ''.join( [ str( round( s/1048576.0, 1 ) ), ' MB (',  commafy(s), ')' ] )
        else:
            return ''.join( [ str( round( s/1048576.0, 1 ) ), ' MB' ] )



try:
    make_temp_file = tempfile.mkstemp # 2.3+
except AttributeError:
    def make_temp_file( suffix='', prefix='', dir='', text=False ): # pre-2.3
        path = tempfile.mktemp( suffix )
        fd = os.open( path, os.O_RDWR|os.O_CREAT|os.O_EXCL, 0700 )
        #os.unlink( path ) # TODO... make this secure
        #return ( os.fdopen( fd, 'w+b' ), path )
        return ( fd, path )

def log_title( program_name, version ):
    log.info( "" )
    log.info( bold( "HP Linux Imaging and Printing System (ver. %s)" % prop.version ) )
    log.info( bold( "%s ver. %s" % ( program_name,version) ) )
    log.info( "" )
    log.info( "Copyright (c) 2003-5 Hewlett-Packard Development Company, LP" )
    log.info( "This software comes with ABSOLUTELY NO WARRANTY." )
    log.info( "This is free software, and you are welcome to distribute it" )
    log.info( "under certain conditions. See COPYING file for more details." )
    log.info( "" )


def which( command ):
    path = os.getenv( 'PATH' ).split( ':' )
    found_path = ''
    for p in path:
        try:
            files = os.listdir( p )
        except:
            continue
        else:
            if command in files:
                found_path = p
                break

    return found_path


def deviceDefaultFunctions():
    cmd_print, cmd_copy, cmd_fax, cmd_pcard, cmd_scan = \
        '', '', '', '', ''

    # Print
    path = which( 'hp-print' )

    if len( path ) > 0:
        cmd_print = 'hp-print -p%PRINTER%'
    else:
        path = which( 'kprinter' )

        if len(path) > 0:
            cmd_print = 'kprinter -P%PRINTER% --system cups'
        else:
            path = which( 'gtklp' )

            if len(path) > 0:
                cmd_print = 'gtklp -P%PRINTER%'

            else:
                path = which( 'xpp' )

                if len( path ) > 0:
                    cmd_print = 'xpp -P%PRINTER%'


    # Scan
    path = which( 'xsane' )

    if len(path) > 0:
        cmd_scan = 'xsane -V %SANE_URI%'
    else:
        path = which( 'kooka' )

        if len(path)>0:
            #cmd_scan = 'kooka -d "%SANE_URI%"'
            cmd_scan = 'kooka'

        else:
            path = which( 'xscanimage' )

            if len(path)>0:
                cmd_scan = 'xscanimage'

    # Photo Card
    path = which( 'hp-unload' )

    if len( path ) > 0:
        cmd_pcard = 'hp-unload -d %DEVICE_URI%'

    else:
        cmd_pcard = 'python %HOME%/unload.py -d %DEVICE_URI%'

    # Copy
    #

    # Fax
    #

    return cmd_print, cmd_scan, cmd_pcard, cmd_copy, cmd_fax




# Derived from ping.c distributed in Linux's netkit. That code is
# copyright (c) 1989 by The Regents of the University of California.
# That code is in turn derived from code written by Mike Muuss of the
# US Army Ballistic Research Laboratory in December, 1983 and
# placed in the public domain. They have my thanks.

# Bugs are naturally mine. I'd be glad to hear about them. There are
# certainly word-size dependenceies here.

# Copyright (c) Matthew Dixon Cowles, <http://www.visi.com/~mdc/>.
# Distributable under the terms of the GNU General Public License
# version 2. Provided with no warranties of any sort.

# Note that ICMP messages can only be sent from processes running
# as root.

# Revision history:
#
# November 22, 1997
# Initial hack. Doesn't do much, but rather than try to guess
# what features I (or others) will want in the future, I've only
# put in what I need now.
#
# December 16, 1997
# For some reason, the checksum bytes are in the wrong order when
# this is run under Solaris 2.X for SPARC but it works right under
# Linux x86. Since I don't know just what's wrong, I'll swap the
# bytes always and then do an htons().
#
# December 4, 2000
# Changed the struct.pack() calls to pack the checksum and ID as
# unsigned. My thanks to Jerome Poincheval for the fix.
#

# From /usr/include/linux/icmp.h; your milage may vary.
ICMP_ECHO_REQUEST = 8 # Seems to be the same on Solaris.

# I'm not too confident that this is right but testing seems
# to suggest that it gives the same answers as in_cksum in ping.c
def checksum( str ):
    csum = 0
    countTo = ( len(str) / 2 ) * 2
    count = 0
    while count < countTo:
        thisVal = ord( str[count+1] ) * 256 + ord( str[count] )
        csum = csum + thisVal
        csum = csum & 0xffffffffL # Necessary?
        count = count + 2

    if countTo < len(str):
        csum = csum + ord( str[ len(str) - 1 ] )
        csum = csum & 0xffffffffL # Necessary?

    csum = ( csum >> 16 ) + ( csum & 0xffff )
    csum = csum + ( csum >> 16 )
    answer = ~csum
    answer = answer & 0xffff

    # Swap bytes. Bugger me if I know why.
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer

def receiveOnePing(mySocket, ID, timeout ):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select( [mySocket], [], [], timeLeft )
        howLongInSelect = ( time.time() - startedSelect )

        if whatReady[0] == []: # Timeout
            return -1

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)
        icmpHeader = recPacket[20:28]
        typ, code, checksum, packetID, sequence = struct.unpack( "bbHHh", icmpHeader )

        if packetID == ID:
            bytesInDouble = struct.calcsize( "d" )
            timeSent = struct.unpack( "d", recPacket[ 28:28 + bytesInDouble ] )[0]
            return timeReceived - timeSent

        timeLeft = timeLeft - howLongInSelect

        if timeLeft <= 0:
            return -1

def sendOnePing( mySocket, destAddr, ID ):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0

    # Make a dummy heder with a 0 checksum.
    header = struct.pack( "bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1 )
    bytesInDouble = struct.calcsize( "d" )
    data = ( 192 - bytesInDouble ) * "Q"
    data = struct.pack( "d", time.time() ) + data

    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum( header + data )

    # Now that we have the right checksum, we put that in. It's just easier
    # to make up a new header than to stuff it into the dummy.
    if prop.platform == 'darwin':
        myChecksum = socket.htons( myChecksum ) & 0xffff
    else:
        myChecksum = socket.htons( myChecksum )

    header = struct.pack( "bbHHh", ICMP_ECHO_REQUEST, 0,
                        myChecksum, ID, 1 )

    packet = header + data
    mySocket.sendto( packet, ( destAddr, 1 ) ) # Don't know about the 1

def doOne( destAddr, timeout=10 ):
    # Returns either the delay (in seconds) or none on timeout.
    icmp = socket.getprotobyname( "icmp" )
    mySocket = socket.socket( socket.AF_INET,socket.SOCK_RAW,icmp )
    myID = os.getpid() & 0xFFFF
    sendOnePing( mySocket, destAddr, myID )
    delay = receiveOnePing( mySocket, myID, timeout )
    mySocket.close()

    return delay


def ping( host, timeout=1 ):
    dest = socket.gethostbyname( host )
    delay = doOne( dest, timeout )
    return delay


def checkPyQtImport():
    # PyQt
    try:
        import qt
    except ImportError:
        log.error( "PyQt not installed. GUI not available. Exiting." )
        return False

    # check version of Qt
    qtMajor = int( qt.qVersion().split('.')[0] )

    if qtMajor < MINIMUM_QT_MAJOR_VER:

        log.error( "Incorrect version of Qt installed. Ver. 3.0.0 or greater required.")
        return False

    #check version of PyQt
    try:
        pyqtVersion = qt.PYQT_VERSION_STR
    except:
        pyqtVersion = qt.PYQT_VERSION

    while pyqtVersion.count('.') < 2:
        pyqtVersion += '.0'

    (maj_ver, min_ver, pat_ver) = pyqtVersion.split('.')

    if pyqtVersion.find( 'snapshot' ) >= 0:
        log.warning( "A non-stable snapshot version of PyQt is installed.")
    else:
        try:
            maj_ver = int(maj_ver)
            min_ver = int(min_ver)
            pat_ver = int(pat_ver)
        except ValueError:
            maj_ver, min_ver, pat_ver = 0, 0, 0

        if maj_ver < MINIMUM_PYQT_MAJOR_VER or \
            (maj_ver == MINIMUM_PYQT_MAJOR_VER and min_ver < MINIMUM_PYQT_MINOR_VER):
            log.error( "This program may not function properly with the version of PyQt that is installed (%d.%d.%d)." % (maj_ver, min_ver, pat_ver) )
            log.error( "Incorrect version of pyQt installed. Ver. %d.%d or greater required." % ( MINIMUM_PYQT_MAJOR_VER, MINIMUM_PYQT_MINOR_VER ) )
            return False

    return True


def loadTranslators( app, user_config ):
    #from qt import *
    import qt
    loc = None

    if os.path.exists( user_config ):
        # user_config contains executables we will run, so we
        # must make sure it is a safe file, and refuse to run
        # otherwise.
        if not path_exists_safely( user_config ):
            log.warning( "File %s has insecure permissions! File ignored." % user_config )
        else:
            config = ConfigParser.ConfigParser()
            config.read( user_config )

            if config.has_section( "ui" ):
                loc = config.get( "ui", "loc" )

                if not loc:
                    loc = None

    if loc is not None:

        if loc.lower() == 'system':
            loc = str(qt.QTextCodec.locale())

        if loc.lower() != 'c':

            log.debug( "Trying to load .qm file for %s locale." % loc )

            dirs = [ prop.home_dir, prop.data_dir, prop.i18n_dir ]

            trans = qt.QTranslator(None)

            for dir in dirs:
                qm_file = 'hplip_%s' % loc
                loaded = trans.load( qm_file, dir)

                if loaded:
                    app.installTranslator( trans )
                    break
        else:
            loc = None

    if loc is None:
        log.debug( "Using default 'C' locale" )
    else:
        log.debug( "Using locale: %s" % loc )

    return loc

try:
    from string import Template # will fail in Python <= 2.3
except ImportError:
    # Code from Python 2.4 string.py
    import re as _re

    class _multimap:
        """Helper class for combining multiple mappings.

        Used by .{safe_,}substitute() to combine the mapping and keyword
        arguments.
        """
        def __init__(self, primary, secondary):
            self._primary = primary
            self._secondary = secondary

        def __getitem__(self, key):
            try:
                return self._primary[key]
            except KeyError:
                return self._secondary[key]


    class _TemplateMetaclass(type):
        pattern = r"""
        %(delim)s(?:
          (?P<escaped>%(delim)s) |   # Escape sequence of two delimiters
          (?P<named>%(id)s)      |   # delimiter and a Python identifier
          {(?P<braced>%(id)s)}   |   # delimiter and a braced identifier
          (?P<invalid>)              # Other ill-formed delimiter exprs
        )
        """

        def __init__(cls, name, bases, dct):
            super(_TemplateMetaclass, cls).__init__(name, bases, dct)
            if 'pattern' in dct:
                pattern = cls.pattern
            else:
                pattern = _TemplateMetaclass.pattern % {
                    'delim' : _re.escape(cls.delimiter),
                    'id'    : cls.idpattern,
                    }
            cls.pattern = _re.compile(pattern, _re.IGNORECASE | _re.VERBOSE)


    class Template:
        """A string class for supporting $-substitutions."""
        __metaclass__ = _TemplateMetaclass

        delimiter = '$'
        idpattern = r'[_a-z][_a-z0-9]*'

        def __init__(self, template):
            self.template = template

        # Search for $$, $identifier, ${identifier}, and any bare $'s

        def _invalid(self, mo):
            i = mo.start('invalid')
            lines = self.template[:i].splitlines(True)
            if not lines:
                colno = 1
                lineno = 1
            else:
                colno = i - len(''.join(lines[:-1]))
                lineno = len(lines)
            raise ValueError('Invalid placeholder in string: line %d, col %d' %
                             (lineno, colno))

        def substitute(self, *args, **kws):
            if len(args) > 1:
                raise TypeError('Too many positional arguments')
            if not args:
                mapping = kws
            elif kws:
                mapping = _multimap(kws, args[0])
            else:
                mapping = args[0]
            # Helper function for .sub()
            def convert(mo):
                # Check the most common path first.
                named = mo.group('named') or mo.group('braced')
                if named is not None:
                    val = mapping[named]
                    # We use this idiom instead of str() because the latter will
                    # fail if val is a Unicode containing non-ASCII characters.
                    return '%s' % val
                if mo.group('escaped') is not None:
                    return self.delimiter
                if mo.group('invalid') is not None:
                    self._invalid(mo)
                raise ValueError('Unrecognized named group in pattern',
                                 self.pattern)
            return self.pattern.sub(convert, self.template)

        def safe_substitute(self, *args, **kws):
            if len(args) > 1:
                raise TypeError('Too many positional arguments')
            if not args:
                mapping = kws
            elif kws:
                mapping = _multimap(kws, args[0])
            else:
                mapping = args[0]
            # Helper function for .sub()
            def convert(mo):
                named = mo.group('named')
                if named is not None:
                    try:
                        # We use this idiom instead of str() because the latter
                        # will fail if val is a Unicode containing non-ASCII
                        return '%s' % mapping[named]
                    except KeyError:
                        return self.delimiter + named
                braced = mo.group('braced')
                if braced is not None:
                    try:
                        return '%s' % mapping[braced]
                    except KeyError:
                        return self.delimiter + '{' + braced + '}'
                if mo.group('escaped') is not None:
                    return self.delimiter
                if mo.group('invalid') is not None:
                    return self.delimiter
                raise ValueError('Unrecognized named group in pattern',
                                 self.pattern)
            return self.pattern.sub(convert, self.template)



cat = lambda _ : Template(_).substitute(sys._getframe(1).f_globals, **sys._getframe(1).f_locals)


class ModelParser:

    def __init__( self ):
        self.model = None
        self.cur_model = None
        self.stack = []
        self.in_model = False
        self.models = {}

    def startElement( self, name, attrs ):
        if name == 'models':
            return

        elif name == 'model':
            self.model = {}
            self.cur_model = str( attrs[ 'name' ] ).replace('_', ' ').\
                replace( 'HP', '' ).replace( 'hp', '' ).strip()
            self.in_model = True
            self.stack = []

        else:
            self.stack.append( str(name).lower() )
            if len(attrs):
                for a in attrs:
                    self.stack.append( str(a).lower() )
                    try:
                        i = int( attrs[a] )
                    except ValueError:
                        i = str( attrs[a] )

                    self.model[ str( '-'.join( self.stack ) ) ] = i
                    self.stack.pop()


    def endElement( self, name ):
        if name == 'model':
            self.in_model = False

            if self.cur_model in self.models:
                log.error( "Duplicate model in XML: %s" % self.cur_model )
                raise Error( ERROR_INTERNAL )

            self.models[ self.cur_model ] = self.model

            self.model = None
        elif name == 'models':
            return
        else:
            self.stack.pop()


    def charData( self, data ):
        data = str(data).strip()
        if data and self.model is not None and self.stack:
            self.model[ str( '-'.join( self.stack ) ) ] = str( data )

    def loadModels( self, filename, untested=False ):
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.startElement
        parser.EndElementHandler = self.endElement
        parser.CharacterDataHandler = self.charData
        try:
            parser.Parse( open( filename ).read(), True )
        except xml.parsers.expat.ExpatError, e:
            log.error( "XML file parse error: %s" % e )
            raise Error( ERROR_INTERNAL )

        return self.models


identity = string.maketrans('','')
unprintable = identity.translate(identity, string.printable)

def printable(s):
    return s.translate(identity, unprintable)


def usage_logging(formatter, space_after=False):
    log.info( formatter.compose( ( "Set the logging level:", "-l<level> or --logging=<level>" ) ) )
    log.info( formatter.compose( ( "", "<level>: none, info*, error, warn, debug (*default)" ), space_after ) )

def usage_help(formatter, space_after=False):
    log.info( formatter.compose( ( "This help information:", "-h or --help" ), space_after ) )

def usage_device(formatter, space_after=False):
    log.info( formatter.compose( ( "To specify a device-URI:", "-d<device-uri> or --device=<device-uri>" ) ) )

def usage_printer(formatter, space_after=False):
    log.info( formatter.compose( ( "To specify a CUPS printer:", "-p<printer> or --printer=<printer>" ), space_after ) )

def usage_options():
    log.info(bold("[OPTIONS]"))

def usage_bus(formatter, space_after=False):
    log.info( formatter.compose( ( "Bus to probe (if device not specified):", "-b<bus> or --bus=<bus>" ) ) )
    log.info( formatter.compose( ( "",
        "<bus>: cups*, usb*, net, bt, fw, par* (*default) (Note: bw and bt not supported)" ), space_after ) )

def usage_examples():
    log.info(bold("Examples:"))

def usage_notes():
    log.info(bold("**NOTES"))
    log.info( """\t1. If device or printer is not specified, the local device bus\n""" \
              """ \t   is probed and the program enters interactive mode.\n""" \
              """\t2. If -p* is specified, the default CUPS printer will be used.\n""" )

def ttysize():
    ln1 = commands.getoutput( 'stty -a' ).splitlines()[0]
    vals = {'rows':None, 'columns':None}
    for ph in ln1.split(';'):
        x = ph.split()
        if len(x) == 2:
            vals[x[0]] = x[1]
            vals[x[1]] = x[0]
    return int( vals['rows'] ), int( vals['columns'] )


def usage_formatter(override=0):
    rows, cols = ttysize()
    
    if override:
        col1 = override
        col2 = cols - col1 - 8
    else:
        col1 = int(cols / 3) - 8
        col2 = cols - col1 - 8
    
    return TextFormatter( ( {'width': col1, 'margin' : 2},
                            {'width': col2, 'margin' : 2}, ))


def any(S,f=lambda x:x):
    for x in S:
        if f(x): return True
    return False

def all(S,f=lambda x:x):
    for x in S:
        if not f(x): return False
    return True


