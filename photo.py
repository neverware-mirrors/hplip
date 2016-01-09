#!/usr/bin/env python
#
# $Revision: 1.17 $
# $Date: 2005/07/21 17:31:38 $
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


_VERSION = '3.1'


# Std Lib
import sys
import os, os.path
import getopt
import re
import cmd
import readline
import time
import fnmatch
import string

# Local
from base.g import *
from base import device, service, utils #, exif
from prnt import cups
from pcard import photocard

def usage():
    formatter = utils.usage_formatter()
    log.info(utils.bold("""\nUsage: hp-photo [PRINTER|DEVICE-URI] [OPTIONS]\n\n""" ))
    log.info(utils.bold( "[PRINTER|DEVICE-URI] (**See NOTES)" ) )
    utils.usage_device(formatter)
    utils.usage_printer(formatter, True)
    utils.usage_options()
    utils.usage_bus(formatter)
    utils.usage_logging(formatter)
    utils.usage_help(formatter, True)
    utils.usage_notes()
    log.info("\n\tUse 'help' command at the pcard:> prompt for command help.")
    sys.exit(0)


## Console class (from ASPN Python Cookbook)
## Author:   James Thiele
## Date:     27 April 2004
## Version:  1.0
## Location: http://www.eskimo.com/~jet/python/examples/cmd/
## Copyright (c) 2004, James Thiele

class Console(cmd.Cmd):

    def __init__(self, pc ):
        cmd.Cmd.__init__(self)
        self.intro  = "Type 'help' for a list of commands. Type 'exit' to quit."
        self.pc = pc
        disk_info = self.pc.info()
        pc.write_protect = disk_info[8]
        if pc.write_protect:
            log.warning( "Photo card is write protected." )
        self.prompt = utils.bold( "pcard: %s > " % self.pc.pwd() )

    ## Command definitions ##
    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print self._hist

    def do_exit(self, args):
        """Exits from the console"""
        return -1

    def do_quit( self, args ):
        """Exits from the console"""
        return -1

    ## Command definitions to support Cmd object functionality ##
    def do_EOF(self, args):
        """Exit on system end of file character"""
        return self.do_exit(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):
        """Do nothing on empty input line"""
        pass

    def default(self, line):
        print utils.bold( "ERROR: Unrecognized command. Use 'help' to list commands." )

    def do_ldir( self, args ):
        """ List local directory contents."""
        os.system( 'ls -l' )

    def do_lls( self, args ):
        """ List local directory contents."""
        os.system( 'ls -l' )

    def do_dir( self, args ):
        """Synonym for the ls command."""
        return self.do_ls( args )

    def do_ls( self, args ):
        """List photo card directory contents."""
        args = args.strip().lower()
        files = self.pc.ls( True, args )

        if 1:

            total_size = 0
            formatter = utils.TextFormatter(
                    (
                        {'width': 14, 'margin' : 2},
                        {'width': 12, 'margin' : 2, 'alignment' : utils.TextFormatter.RIGHT },
                        {'width': 30, 'margin' : 2},
                    )
                )

            print
            print utils.bold( formatter.compose( ("Name", "Size", "Type" ) ) )

            num_files = 0
            for d in self.pc.current_directories():
                if d[0] in ('.', '..'):
                    print formatter.compose( ( d[0], "", "directory" ) )
                else:
                    print formatter.compose( ( d[0] + "/", "", "directory" ) )

            for f in self.pc.current_files():
                print formatter.compose( ( f[0], utils.format_bytes(f[2]), self.pc.classify_file( f[0] ) ) )
                num_files += 1
                total_size += f[2]

            print utils.bold( "% d files, %s" % ( num_files, utils.format_bytes( total_size, True ) ) )


    def do_df( self, args ):
        """Display free space on photo card.
        Options:
        -h\tDisplay in human readable format
        """
        freespace = self.pc.df()

        if args.strip().lower() == '-h':
            fs = utils.format_bytes( freespace )
        else:
            fs = utils.commafy(freespace)

        print "Freespace = %s Bytes" % fs


    def do_cp( self, args, remove_after_copy=False ):
        """Copy files from photo card to current local directory.
        Usage:
        \tcp FILENAME(S)|GLOB PATTERN(S)
        Example:
        \tCopy all JPEG and GIF files and a file named thumbs.db from photo card to local directory:
        \tcp *.jpg *.gif thumbs.db
        """
        args = args.strip().lower()

        matched_files = self.pc.match_files( args )

        if len( matched_files ) == 0:
            print "ERROR: File(s) not found."
        else:
            total, delta = self.pc.cp_multiple( matched_files, remove_after_copy, self.cp_status_callback, self.rm_status_callback )

            print utils.bold( "\n%s transfered in %d sec (%d KB/sec)" % ( utils.format_bytes( total ), delta, (total/1024)/(delta) ) )

    def do_unload( self, args ):
        """Unload all image files from photocard to current local directory.
        Note:
        \tSubdirectories on photo card are not preserved
        Options:
        -x\tDon't remove files after copy
        -p\tPrint unload list but do not copy or remove files"""
        args = args.lower().strip().split()
        dont_remove = False
        if '-x' in args:
            if self.pc.write_protect:
                log.error( "Photo card is write protected. -x not allowed." )
                return
            else:
                dont_remove = True


        unload_list = self.pc.get_unload_list()
        print

        if len( unload_list ) > 0:
            if '-p' in args:

                max_len = 0
                for u in unload_list:
                    max_len = max( max_len, len(u[0]) )

                formatter = utils.TextFormatter(
                        (
                            {'width': max_len+2, 'margin' : 2},
                            {'width': 12, 'margin' : 2, 'alignment' : utils.TextFormatter.RIGHT },
                            {'width': 12, 'margin' : 2},
                        )
                    )

                print
                print utils.bold( formatter.compose( ("Name", "Size", "Type" ) ) )

                total = 0
                for u in unload_list:
                     print formatter.compose( ( '%s' % u[0], utils.format_bytes(u[1]), '%s/%s' % ( u[2], u[3] ) ))
                     total += u[1]


                print utils.bold( "Found %d files to unload, %s" % ( len(unload_list), utils.format_bytes( total, True ) ) )
            else:
                print utils.bold( "Unloading %d files..." % len(unload_list) )
                total, delta, was_cancelled = self.pc.unload( unload_list, self.cp_status_callback, self.rm_status_callback, dont_remove )
                print utils.bold( "\n%s unloaded in %d sec (%d KB/sec)" % ( utils.format_bytes( total ), delta, (total/1024)/delta ) )

        else:
            print "No image, audio, or video files found."


    def cp_status_callback( self, src, trg, size ):
        print "Copying %s to %s (%s)..." % ( src, trg, utils.format_bytes(size) )

    def rm_status_callback( self, src ):
        print "Removing %s..." % src



    def do_rm( self, args ):
        """Remove files from photo card."""
        if self.pc.write_protect:
            log.error( "Photo card is write protected. rm not allowed." )
            return

        args = args.strip().lower()

        matched_files = self.pc.match_files( args )

        if len( matched_files ) == 0:
            print "ERROR: File(s) not found."
        else:
            for f in matched_files:
                self.pc.rm( f, False )

        self.pc.ls()

    def do_mv( self, args ):
        """Move files off photocard"""
        if self.pc.write_protect:
            log.error( "Photo card is write protected. mv not allowed." )
            return
        self.do_cp( args, True )

    def do_lpwd( self, args ):
        """Print name of local current/working directory."""
        print os.getcwd()

    def do_lcd( self, args ):
        """Change current local working directory."""
        try:
            os.chdir( args.strip() )
        except OSError:
            print utils.bold( "ERROR: Directory not found." )
        print os.getcwd()

    def do_pwd( self, args ):
        """Print name of photo card current/working directory
        Usage:
        \t>pwd"""
        print self.pc.pwd()

    def do_cd( self, args ):
        """Change current working directory on photo card.
        Note:
        \tYou may only specify one directory level at a time.
        Usage:
        \tcd <directory>
        """
        args = args.lower().strip()

        if args == '..':
            if self.pc.pwd() != '/':
                self.pc.cdup()

        elif args == '.':
            pass

        elif args == '/':
            self.pc.cd('/')

        else:
            matched_dirs = self.pc.match_dirs( args )

            if len( matched_dirs ) == 0:
                print "Directory not found"

            elif len( matched_dirs ) > 1:
                print "Pattern matches more than one directory"

            else:
                self.pc.cd( matched_dirs[0] )

        self.prompt = utils.bold( "pcard: %s > " % self.pc.pwd() )

    def do_cdup( self, args ):
        """Change to parent directory."""
        self.do_cd( '..' )

    #def complete_cd( self, text, line, begidx, endidx ):
    #    print text, line, begidx, endidx
    #    #return "XXX"

    def do_cache( self, args ):
        """Display current cache entries, or turn cache on/off.
        Usage:
        \tDisplay: cache
        \tTurn on: cache on
        \tTurn off: cache off
        """
        args = args.strip().lower()

        if args == 'on':
            self.pc.cache_control(True)

        elif args == 'off':
            self.pc.cache_control(False)

        else:
            if self.pc.cache_state():
                cache_info = self.pc.cache_info()

                t = cache_info.keys()
                t.sort()
                print
                for s in t:
                    print "sector %d (%d hits)" % ( s, cache_info[s] )

                print utils.bold( "Total cache usage: %s (%s maximum)" % (utils.format_bytes(len(t)*512), utils.format_bytes(photocard.MAX_CACHE * 512)))
                print utils.bold( "Total cache sectors: %s of %s" % (utils.commafy(len(t)), utils.commafy(photocard.MAX_CACHE)))
            else:
                print "Cache is off."

    def do_sector( self, args ):
        """Display sector data.
        Usage:
        \tsector <sector num>
        """
        args = args.strip().lower()
        cached = False
        try:
            sector = int(args)
        except ValueError:
            print "Sector must be specified as a number"
            return

        if self.pc.cache_check( sector ) > 0:
            print "Cached sector"

        print repr( self.pc.sector( sector ) )


    def do_tree( self, args ):
        """Display photo card directory tree."""
        tree = self.pc.tree( )
        print
        self.print_tree( tree )

    def print_tree( self, tree, level=0 ):
        for d in tree:
            if type(tree[d]) == type({}):
                print ''.join( [ ' '*level*4, d, '/' ] )
                self.print_tree( tree[d], level+1 )


    def do_reset( self, args ):
        """Reset the cache."""
        self.pc.cache_reset()


    def do_card( self, args ):
        """Print info about photocard."""
        print
        print "Device URI = %s" % self.pc.device.device_uri
        print "Model = %s" % self.pc.device.model_ui
        print "Working dir = %s" % self.pc.pwd()
        disk_info = self.pc.info()
        print "OEM ID = %s" % disk_info[0]
        print "Bytes/sector = %d" % disk_info[1]
        print "Sectors/cluster = %d" % disk_info[2]
        print "Reserved sectors = %d" % disk_info[3]
        print "Root entries = %d" % disk_info[4]
        print "Sectors/FAT = %d" % disk_info[5]
        print "Volume label = %s" % disk_info[6]
        print "System ID = %s" % disk_info[7]
        print "Write protected = %d" % disk_info[8]
        print "Cached sectors = %s" % utils.commafy( len( self.pc.cache_info() ) )


    def do_display( self, args ):
        """Display an image with ImageMagick.
        Usage:
        \tdisplay <filename>"""
        args = args.strip().lower()
        matched_files = self.pc.match_files( args )

        if len( matched_files ) == 1:

            typ = self.pc.classify_file( args ).split('/')[0]

            if typ == 'image':
                fd, temp_name = utils.make_temp_file()
                self.pc.cp( args, temp_name )
                os.system( 'display %s' % temp_name )
                os.remove( temp_name )

            else:
                print "File is not an image."

        elif len( matched_files ) == 0:
            print "File not found."

        else:
            print "Only one file at a time may be specified for display."

    def do_show( self, args ):
        """Synonym for the display command."""
        self.do_display( args )

    def do_thumbnail( self, args ):
        """Display an embedded thumbnail image with ImageMagick.
        Note:
        \tOnly works with JPEG/JFIF images with embedded JPEG/TIFF thumbnails
        Usage:
        \tthumbnail <filename>"""
        args = args.strip().lower()
        matched_files = self.pc.match_files( args )

        if len( matched_files ) == 1:
            typ, subtyp = self.pc.classify_file( args ).split('/')
            #print "'%s' '%s'" % (typ, subtyp)

            if typ == 'image' and subtyp in ( 'jpeg', 'tiff' ):
                exif_info = self.pc.get_exif( args )

                dir_name, file_name=os.path.split(args)
                photo_name, photo_ext=os.path.splitext(args)

                if 'JPEGThumbnail' in exif_info:
                    #print "JPEG thumbnail found."
                    temp_file_fd, temp_file_name = utils.make_temp_file()
                    #thumb_name = os.path.join( os.getcwd(), photo_name ) + '_thumb.jpg'
                    open(temp_file_name, 'wb').write(exif_info['JPEGThumbnail'])
                    os.system( 'display %s' % temp_file_name )
                    os.remove( temp_file_name )

                elif 'TIFFThumbnail' in exif_info:
                    #print "TIFF thumbnail found."
                    #thumb_name = os.path.join( os.getcwd(), photo_name ) + '_thumb.tif'
                    temp_file_fd, temp_file_name = utils.make_temp_file()
                    open(temp_file_name, 'wb').write(exif_info['TIFFThumbnail'])
                    os.system( 'display %s' % temp_file_name )
                    os.remove( temp_file_name )

                else:
                    print "No thumbnail found."

            else:
                print "Incorrect file type for thumbnail."

        elif len( matched_files ) == 0:
            print "File not found."
        else:
            print "Only one file at a time may be specified for thumbnail display."

    def do_thumb( self, args):
        """Synonym for the thumbnail command."""
        self.do_thumbnail( args )

    def do_exif( self, args ):
        """Display EXIF info for file.
        Usage:
        \texif <filename>"""
        args = args.strip().lower()
        matched_files = self.pc.match_files( args )

        if len( matched_files ) == 1:
            typ, subtyp = self.pc.classify_file( args ).split('/')
            #print "'%s' '%s'" % (typ, subtyp)

            if typ == 'image' and subtyp in ( 'jpeg', 'tiff' ):
                exif_info = self.pc.get_exif( args )

                formatter = utils.TextFormatter(
                        (
                            {'width': 40, 'margin' : 2},
                            {'width': 40, 'margin' : 2},
                        )
                    )

                print
                print utils.bold( formatter.compose( ("Tag", "Value" ) ) )

                ee = exif_info.keys()
                ee.sort()
                for e in ee:
                    if e not in ( 'JPEGThumbnail', 'TIFFThumbnail', 'Filename' ):
                        #if e != 'EXIF MakerNote':
                        print formatter.compose( ( e, '%s' % exif_info[e] ) )
                        #else:
                        #    print formatter.compose( ( e, ''.join( [ chr(x) for x in exif_info[e].values if chr(x) in string.printable ] ) ) )
            else:
                print "Incorrect file type for thumbnail."

        elif len( matched_files ) == 0:
            print "File not found."
        else:
            print "Only one file at a time may be specified for thumbnail display."

    def do_info( self, args ):
        """Synonym for the exif command."""
        self.do_exif( args )




utils.log_title( 'Photo Card Access Utility', _VERSION )

try:
    opts, args = getopt.getopt( sys.argv[1:], 'p:d:hb:l:',
                               [ 'printer=', 'device=', 'help', 'bus=', 'logging=' ] )
except getopt.GetoptError:
    usage()

printer_name = None
device_uri = None
bus = device.DEFAULT_PROBE_BUS
log_level = logger.DEFAULT_LOG_LEVEL

for o, a in opts:
    if o in ( '-h', '--help' ):
        usage()

    elif o in ( '-p', '--printer' ):
        printer_name = a

    elif o in ( '-d', '--device' ):
        device_uri = a

    elif o in ( '-b', '--bus' ):
        bus = a.lower().strip()

    elif o in ( '-l', '--logging' ):
        log_level = a.lower().strip()


if not device.validateBusList(bus):
    usage()

if not log.set_level( log_level ):
    usage()

if device_uri and printer_name:
    log.error( "You may not specify both a printer (-p) and a device (-d)." )
    usage()

if printer_name:
    printer_list = cups.getPrinters()
    found = False
    for p in printer_list:
        if p.name == printer_name:
            found = True

    if not found:
        log.error( "Unknown printer name: %s" % printer_name )
        sys.exit(0)


if not device_uri and not printer_name:
    try:
        device_uri = device.getInteractiveDeviceURI( bus, 'pcard' )
        if device_uri is None:
            sys.exit(0)
    except Error:
        log.error( "Error occured during interative mode. Exiting." )
        sys.exit(0)

pc = photocard.PhotoCard( None, device_uri, printer_name )
pc.set_callback( update_spinner )

if pc.device.device_uri is None and printer_name:
    log.error( "Printer '%s' not found." % printer_name )
    sys.exit(0)

if pc.device.device_uri is None and device_uri:
    log.error( "Malformed/invalid device-uri: %s" % device_uri )
    sys.exit(0)

pc.device.sendEvent( EVENT_START_PCARD_JOB, 'event', 0,
    prop.username, pc.device.device_uri )

try:
    pc.mount()
except Error:
    log.error( "Unable to mount photo card on device. Check that device is powered on and photo card is correctly inserted." )
    pc.umount()
    pc.device.sendEvent( EVENT_PCARD_UNABLE_TO_MOUNT, 'error', 0, prop.username,
        pc.device.device_uri )
    sys.exit(0)

log.info( utils.bold("\nPhotocard on device %s mounted" % pc.device.device_uri ) )
log.info( utils.bold("DO NOT REMOVE PHOTO CARD UNTIL YOU EXIT THIS PROGRAM") )

console = Console( pc )
try:
    try:
        console . cmdloop()
    except Exception, e:
        log.error( "An error occured: %s" % e )
finally:
    pc.umount()

pc.device.sendEvent( EVENT_END_PCARD_JOB, 'event', 0, prop.username,
    pc.device.device_uri )

log.info( "Done." )





