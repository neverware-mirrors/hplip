#!/usr/bin/env python
#
# $Revision: 1.3 $ 
# $Date: 2005/01/07 23:28:37 $
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

# string_table := { 'string_id' : ( 'short', 'long' ), ... }

# string_id's for error codes are the string form of the error code
# Strings that need localization use lambda : _( 'string' ) form.
# Strings that refer to other strings, use '%reference%' form.
# Blank strings use '' form.

string_table = {

'try_again' :       ( '', 
                      lambda : _( 'Please correct the problem and try again.') ),

'press_continue' :  ( '',
                      lambda : _( 'Please correct the problem and press continue on the printer.' ) ),

'500' :             ( lambda : _( 'The printer has started a print job.' ),
                     '' ),
          
'501' :             ( lambda : _( 'Print job has completed.' ),
                     '' ),

'1000' :            ( lambda : _( 'The printer is idle.' ),
                      '' ),

'1001' :            ( lambda : _( 'The printer is busy.' ),
                     '' ),

'1002' :            ( lambda : _( 'The print job is continuing.' ),
                      '' ),

'1003' :            ( lambda : _( 'Turning off.' ),
                      '' ),

'1004' :            ( lambda : _( 'Report printing.' ),
                      '' ),

'1005' :            ( lambda : _( 'Canceling.' ),
                      '' ),

'1006' :            ( '%5002',
                      '%try_again%' ),

'1007' :            ( lambda : _( 'Waiting for ink to dry.' ),
                      '' ),

'1008' :            ( lambda : _( 'Pen change.' ),
                     '' ),

'1009' :            ( lambda : _( 'The printer is out of paper.' ),
                      lambda : _( 'Please load more paper and follow the instructions on the front panel (if any) to continue printing.' ) ),

'1010' :            ( lambda : _( 'Banner eject needed.' ),
                      '' ),
                      
'1011' :            ( lambda : _( 'Banner mismatch.' ),
                      '%try_again%' ),
                      
'1012' :            ( lambda : _( 'Photo mismatch.' ),
                      '%try_again%' ),
                      
'1013' :            ( lambda : _( 'Duplex mismatch.' ),
                      '%try_again' ),
                      
'1014' :            ( lambda : _( 'Paper or cartridge carriage jammed.' ),
                      lambda : _( 'Please clear the jam and press continue on the printer.' ) ),
                      
'1015' :            ( '%1014%',
                      '%1014%' ),
                      
'1016' :            ( '%1014%',
                      '%1014%' ),

'1017' :            ( lambda : _( 'There is a problem with a cartridge.' ),
                      '%press_continue%' ),
                      
'1018' :            ( '%unknown_error%',
                      '%try_again%' ),
                      
'1019' :            ( lambda : _( 'Powering down.' ),
                      '' ),
                      
'1020' :            ( lambda : _( 'Front panel test.' ),
                      '' ),
                      
'1021' :            ( lambda : _( 'Clean out tray missing.' ),
                      '%try_again%' ),
                      
'2000' :            ( lambda : _( 'Scan job started.' ),
                      '' ),
                      
'2001' :            ( lambda : _( 'Scan job completed.' ),
                      '' ),
                      
'2002' :            ( lambda : _( 'Scanner error.' ),
                      '%try_again%' ),
                      
'5002' :            ( lambda : _( 'Device is offline or unplugged.' ),
                      '%5012%' ),
                      
'5012' :            ( lambda : _( 'Device communication error.' ),
                      '%try_again%' ),
                      
'5021' :            ( lambda : _( 'Device is busy.' ),
                      '%try_again%' ),
                      
'5030' :            ( '%unknown_error%',
                      '%try_again%' ),
                      
'5031' :            ( '%5021%',
                      '%try_again%' ),

'5033' :            ( lambda : _( 'Unsupported I/O bus.'),
                      '%try_again%' ),
                      
'5034' :            ( lambda : _( 'Device does not support requested operation.' ),
                      '%try_again%' ),
                      
'unknown_error' :   ( lambda : _( 'Unknown error.' ),
                      '' ),
                      
'print' :           ( lambda : _( 'Print' ),
                      '' ),
                      
'scan' :            ( lambda : _( 'Scan' ),
                      '' ),
                      
'send_fax' :        ( lambda : _( 'Send fax' ),
                      '' ),
                      
'make_copies' :     ( lambda : _( 'Make copies' ),
                      '' ),
                      
'access_photo_cards' :    ( lambda : _( 'Access photo cards' ),
                           '' ),
                      
'agent_invalid_invalid' : ( lambda : _( 'Invalid/missing' ),
                            '' ),
                            
'agent_invalid_supply' :  ( lambda : _( 'Invalid/missing ink cartridge' ),
                            '' ),
                      
'agent_invalid_cartridge':( lambda : _( 'Invalid/missing cartridge' ),
                            '' ),
                            
'agent_invalid_head' :    ( lambda : _( 'Invalid/missing print head' ),
                            '' ),
                            
'agent_unknown_unknown' : ( lambda : _( 'Unknown' ),
                            '' ),
                            

'agent_black_head' :      ( lambda : _( 'Black print head' ),
                            '' ),
                            
'agent_black_supply' :    ( lambda : _( 'Black ink cartridge' ),
                            '' ),
                            
'agent_black_cartridge' : ( lambda : _( 'Black cartridge' ),
                            '' ),
                            

'agent_cmy_head' :        ( lambda : _( 'Tri-color print head' ),
                            '' ),
                            
'agent_cmy_supply' :      ( lambda : _( 'Tri-color ink cartridge' ),
                            '' ),
                            
'agent_cmy_cartridge' :   ( lambda : _( 'Tri-color cartridge' ),
                            '' ),
                            
                            
'agent_kcm_head' :        ( lambda : _( 'Photo print head' ),
                            '' ),
                            
'agent_kcm_supply' :      ( lambda : _( 'Photo ink cartridge' ),
                            '' ),
                            
'agent_kcm_cartridge' :   ( lambda : _( 'Photo cartridge' ),
                            '' ),
                            
                            
'agent_cyan_head' :       ( lambda : _( 'Cyan print head' ),
                            '' ),
                            
'agent_cyan_supply' :     ( lambda : _( 'Cyan ink cartridge' ),
                            '' ),
                            
'agent_cyan_cartridge' :  ( lambda : _( 'Cyan cartridge' ),
                            '' ),
                            
                            
'agent_magenta_head' :    ( lambda : _( 'Magenta print head' ),
                            '' ),
                            
'agent_magenta_supply' :  ( lambda : _( 'Magenta ink cartridge' ),
                            '' ),
                            
'agent_magenta_cartridge':( lambda : _( 'Magenta cartridge' ),
                            '' ),
                            
                            
'agent_yellow_head' :     ( lambda : _( 'Yellow print head' ),
                            '' ),
                            
'agent_yellow_supply' :   ( lambda : _( 'Yellow ink cartridge' ),
                            '' ),
                            
'agent_yellow_cartridge': ( lambda : _( 'Yellow cartridge' ),
                            '' ),


'agent_photo_cyan_head' :       ( lambda : _( 'Photo cyan print head' ),
                                   '' ),
                            
'agent_photo_cyan_supply' :     ( lambda : _( 'Photo cyan ink cartridge' ),
                                  '' ),
                            
'agent_photo_cyan_cartridge' :  ( lambda : _( 'Photo cyan cartridge' ),
                                  '' ),
                            
                            
'agent_photo_magenta_head' :    ( lambda : _( 'Photo magenta print head' ),
                                  '' ),
                            
'agent_photo_magenta_supply' :  ( lambda : _( 'Photo magenta ink cartridge' ),
                                  '' ),
                            
'agent_photo_magenta_cartridge':( lambda : _( 'Photo magenta cartridge' ),
                                  '' ),
                            
                            
'agent_photo_yellow_head' :     ( lambda : _( 'Photo yellow print head' ),
                                  '' ),
                            
'agent_photo_yellow_supply' :   ( lambda : _( 'Photo yellow ink cartridge' ),
                                  '' ),
                            
'agent_photo_yellow_cartridge': ( lambda : _( 'Photo yellow cartridge' ),
                                  '' ),
                            

'agent_photo_gray_head' :       ( lambda : _( 'Photo gray print head' ),
                                   '' ),
                            
'agent_photo_gray_supply' :     ( lambda : _( 'Photo gray ink cartridge' ),
                                  '' ),
                            
'agent_photo_gray_cartridge' :  ( lambda : _( 'Photo gray cartridge' ),
                                  '' ),


'agent_photo_blue_head' :       ( lambda : _( 'Photo blue print head' ),
                                   '' ),
                            
'agent_photo_blue_supply' :     ( lambda : _( 'Photo blue ink cartridge' ),
                                  '' ),
                            
'agent_photo_blue_cartridge' :  ( lambda : _( 'Photo blue cartridge' ),
                                  '' ),


'agent_health_unknown'     : ( lambda : _( 'Unknown' ),
                               '' ),
                           
'agent_health_ok'          : ( lambda : _( 'OK' ),
                               '' ),
                           
'agent_health_misinstalled': ( lambda : _( 'Not installed or mis-installed' ),
                               '' ),
                           
'agent_health_incorrect'   : ( lambda : _( 'Incorrect' ),
                               '' ),
                               
'agent_health_failed'      : ( lambda : _( 'Failed' ),
                               '' ),


}

