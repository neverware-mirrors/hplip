#!/usr/bin/env python
#
# $Revision: 1.16.2.3 $ 
# $Date: 2005/01/18 22:35:35 $
# $Author: dsuffield $
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


# Local
from g import *
from codes import *
import msg, utils, status, pml
from prnt import pcl, ldl

def AlignType1( dev, loadpaper_ui ): # Auto VIP
    dialogState = False
    dialogState = loadpaper_ui()
    if dialogState == True:
        dev.sendEmbeddedPMLEx( pml.OID_AUTO_ALIGNMENT, 1100 )

    return dialogState

def AlignType2( dev, loadpaper_ui, align_ui, bothpens_ui, busy_callback ): # 8xx
    state, a, b, c, d = 0, 6, 6, 3, 3
    dialogState = False
    while state != -1:
        if state == 0:
            state = 1
            pens = dev.deviceIDStatus()['agents']
            if pens[0]['type'] == status.AGENT_TYPE_NONE or \
               pens[1]['type'] == status.AGENT_TYPE_NONE:
                log.error( "Cannot perform alignment with 0 or 1 pen installed." )
                state = 100

        elif state == 1:
            state = -1
            dialogState = loadpaper_ui()
            if dialogState:
                state = 2

        elif state == 2:
            state = -1
            alignType2Phase1( dev, busy_callback )
            ok, a = align_ui( 'A', 'h', 'kc', 2, 11 )
            if ok:
                state = 3

        elif state == 3:
            state = -1
            ok, b = align_ui( 'B', 'v', 'kc', 2, 11 )
            if ok:
                state = 4

        elif state == 4:
            state = -1
            ok, c = align_ui( 'C', 'v', 'kc', 2, 5 )
            if ok:
                state = 5

        elif state == 5:
            state = -1
            ok, d = align_ui( 'D', 'v', 'c', 2, 5 )
            if ok:
                state = 6

        elif state == 6:
            dialogState = loadpaper_ui()
            if dialogState:
                alignType2Phase2( dev, a, b, c, d, busy_callback )
            state = -1

        elif state == 100:
            bothpens_ui()
            state = -1

    return dialogState



def AlignType3( dev, loadpaper_ui, align_ui, paperedge_ui, busy_callback, align_type ): # 9xx
    state, a, b, c, d, zca = 0, 6, 6, 3, 3, 6
    dialogState = False
    while state != -1:
        if state == 0:
            state = -1
            dialogState = loadpaper_ui()
            if dialogState:
                alignType3Phase1( dev, busy_callback )
                state = 1

        elif state == 1:
            state = -1
            ok, a = align_ui( 'A', 'h', 'kc', 2, 11 )
            if ok:
                state = 2

        elif state == 2:
            state = -1
            ok, b = align_ui( 'B', 'v', 'kc', 2, 11 )
            if ok:
                state = 3

        elif state == 3:
            state = -1
            ok, c = align_ui( 'C', 'v', 'k', 2, 11 )
            if ok:
                state = 4
        
        elif state == 4:
            state = -1
            ok, d = align_ui( 'D', 'v', 'kc', 2, 11 )
            if ok:
                state = 5

        elif state == 5:
            state = -1
            alignType3Phase2( dev, a, b, c, d )
            if align_type == 9:
                state = 7
            else: 
                dialogState = loadpaper_ui()
                if dialogState:
                    state = 6

        elif state == 6:
            state = -1
            alignType3Phase3( dev )
            ok, zca = paperedge_ui( 13 )
            if ok:
                state = 7

        elif state == 7:
            dialogState = loadpaper_ui()
            if dialogState:
                alignType3Phase4( dev, zca, busy_callback )
            state = -1

    return dialogState


def AlignxBow( dev, align_type, loadpaper_ui, align_ui, paperedge_ui,
               invalidpen_ui, coloradj_ui, busy_callback ): # Types 4, 5, and 7
               
    state, statepos = 0, 0
    user_cancel_states = [1000, -1]
    a, b, c, d, e, f, g = 0, 0, 0, 0, 0, 0, 0
    error_states = [-1]
    dialogState = False
    
    dev.pen_config = status.getPenConfiguration( dev.deviceIDStatus() )
    
    if dev.pen_config in ( status.AGENT_CONFIG_NONE, status.AGENT_CONFIG_INVALID ):
        state, states = 100, [-1]
    
    elif dev.pen_config == status.AGENT_CONFIG_BLACK_ONLY:
        state, states = 0, [2, 200, 3, -1]
    
    elif dev.pen_config == status.AGENT_CONFIG_PHOTO_ONLY:
        state, states = 0, [2, 200, 3, -1]
    
    elif dev.pen_config == status.AGENT_CONFIG_COLOR_ONLY:
        state, states = 0, [2, 300, 3, -1]
    
    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_BLACK:
        state, states = 0, [2, 400, 500, 600, 700, 3, 4, -1]
    
    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_PHOTO:
        state, states = 0, [2, 400, 500, 600, 700, 800, 900, 3, 4, -1]
    
    while state != -1:
        
        if state == 0:
            dialogState = loadpaper_ui()
            if dialogState:
                if align_type == 4:
                    alignType4Phase1( dev, busy_callback )
                elif align_type == 5:
                    alignType5Phase1( dev, busy_callback )
                elif align_type == 7: 
                    alignType7Phase1( dev, busy_callback )
                else:
                    statepos, states = 0, error_states
            else:
                statepos, states = 0, user_cancel_states
                
                
        elif state == 2:
            ok, a = paperedge_ui( 13 )
            if not ok:
                statepos, states = 0, user_cancel_states
                
        elif state == 3:
            if align_type == 4:
                alignType4Phase2( dev, a, b, c, d, e )
            elif align_type == 5:
                alignType5Phase2( dev, a, b, c, d, e, f, g )
            else:
                alignType7Phase2( dev, a, b, c, d, e, f, g )
                
        elif state == 4:
            dialogState = loadpaper_ui()
            if dialogState:
                if align_type == 4:
                    alignType4Phase3( dev, busy_callback )
                elif align_type == 5:
                    alignType5Phase3( dev, busy_callback )
                else:
                    alignType7Phase3( dev, busy_callback )
            else:
                statepos, states = 0, user_cancel_states
            
        elif state == 100: 
            invalidpen_ui()
            state = -1
        
        elif state == 200: # B Line - Black only or photo only
            ok, b = align_ui(  'B', 'v', 'k', 2, 11 )
            if not ok:
                statepos, states = 0, user_cancel_states
            
        elif state == 300: # B Line - Color only
            ok, b = align_ui( 'B', 'v', 'kc', 2, 11 )
            if not ok:
                statepos, states = 0, user_cancel_states
            
        elif state == 400: # B Line - 2 pen 
            ok, b = align_ui( 'B', 'h', 'kc', 2, 17 )
            if not ok:
                statepos, states = 0, user_cancel_states
            
        elif state == 500: # C Line
            ok, c = align_ui( 'C', 'v', 'kc', 2, 17 )
            if not ok:
                statepos, states = 0, user_cancel_states
            
        elif state == 600 : # D Line
            ok, d = align_ui( 'D', 'v', 'k', 2, 11 )
            if not ok:
                statepos, states = 0, user_cancel_states
            
        elif state == 700: # E Line
            ok, e = align_ui( 'E', 'v', 'kc', 2, 11 )
            if not ok:
                statepos, states = 0, user_cancel_states
            
        elif state == 800: # F Line
            ok, f = coloradj_ui( 'F', 21 )
            if not ok:
                statepos, states = 0, user_cancel_states
            
        elif state == 900: # G Line
            ok, f = coloradj_ui( 'G', 21 )
            if not ok:
                statepos, states = 0, user_cancel_states
        
        elif state == 1000: # User cancel
            log.warning( "Alignment canceled at user request." )
        
        state = states[ statepos ]
        statepos += 1
    
    return dialogState

def AlignType6( dev, ui1, ui2, loadpaper_ui  ):
    state = 0
    dialogState = False
    
    while state != -1:
        if state == 0:
            state = -1
            okay, print_page = ui1()
            if print_page:
                # Need to printout alignment page
                state = 1
            elif okay: 
                # Next >
                state = 2
            
        elif state == 1: # Load and print
            state = -1
            dialogState = loadpaper_ui()
            if dialogState:
                alignType6Phase1( dev )
                state = 2
                
        elif state == 2: # Finish
            ui2()
            state = -1
            
            
    return dialogState
    
def AlignType8( dev, loadpaper_ui, align_ui, busy_callback ): # 450
    state, a, b, c, d = 0, 5, 5, 5, 5
    dialogState = False

    while state != -1:

        if state == 0:
            state = -1
            dialogState = loadpaper_ui()
            if dialogState:
                num_inks = alignType8Phase1( dev )
                state = 1

        elif state == 1:
            state = -1
            ok, a = align_ui( 'A', 'v', 'k', 3, 9 )
            if ok:
                state = 2

        elif state == 2:
            state = -1
            ok, b = align_ui( 'B', 'v', 'c', 3, 9 )
            if ok:
                state = 3

        elif state == 3:
            state = -1
            ok, c = align_ui( 'C', 'v', 'kc', 3, 9 )
            if ok:
                state = 4

        elif state == 4:
            state = -1
            ok, d = align_ui( 'D', 'h', 'kc', 3, 9 )
            if ok:
                state = 5

        elif state == 5:
            alignType8Phase2( dev, num_inks, a, b, c, d )
            state = -1  

    return dialogState


def alignType2Phase1( dev, callback=None ): # Type 2 (8xx)
    channel_id = dev.checkOpenChannel( 'PRINT' )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_VERTICAL_ALIGNMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT1_BIDIR_ADJUSTMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_BIDIR_ADJUSTMENT, 0 )
    dev.closeChannel( 'PRINT' )
    
    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'pcl', 'align1_8xx.pcl.gz' ), callback, False )

def alignType2Phase2(  dev, a, b, c, d, callback=None ): # (8xx)
    channel_id = dev.checkOpenChannel( 'PRINT' )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_VERTICAL_ALIGNMENT, (a - 6) * 12 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, (b - 6) * 12 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT1_BIDIR_ADJUSTMENT, (c - 3) * 12 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_BIDIR_ADJUSTMENT, (d - 3) * 12 )
    dev.sendEmbeddedPMLEx( pml.OID_MARKING_AGENTS_INITIALIZED, 3 )
    dev.closeChannel( 'PRINT' )
    
    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'pcl', 'align2_8xx.pcl.gz' ), callback, False )
    

def alignType3Phase1( dev, callback=None ): # Type 3 (9xx)
    channel_id = dev.checkOpenChannel( 'PRINT' )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_VERTICAL_ALIGNMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT1_BIDIR_ADJUSTMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_BIDIR_ADJUSTMENT, 0 )
    dev.closeChannel( 'PRINT' )
    
    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'pcl', 'align1_9xx.pcl.gz' ), callback, False )

def alignType3Phase2( dev, a, b, c, d ): # Type 3 (9xx)
    channel_id = dev.checkOpenChannel( 'PRINT' )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_VERTICAL_ALIGNMENT, (a - 6) * 12 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, (6 - b) * 12 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT1_BIDIR_ADJUSTMENT, (6 - c) * 12 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_BIDIR_ADJUSTMENT, (6 - d) * 6 )
    dev.closeChannel( 'PRINT' )

def alignType3Phase3( dev, callback=None ): # Type 3 (9xx)
    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'pcl', 'align3_9xx.pcl.gz' ), callback, False )

def alignType3Phase4( dev, zca, callback=None ): # Type 3 (9xx)
    channel_id = dev.checkOpenChannel( 'PRINT' )
    dev.sendEmbeddedPMLEx( pml.OID_MARKING_AGENTS_INITIALIZED, 3 )
    dev.closeChannel( 'PRINT' )
    
    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'pcl', 'align2_9xx.pcl.gz' ), callback, False )
    
    
def alignType4Phase1( dev, callback=None ): # Type 4 (xBow/LIDIL 0.3.8)
    channel_id = dev.checkOpenChannel( 'PRINT' )
    dev.writeChannel( channel_id, ldl.buildLIDILPacket( ldl.PACKET_TYPE_RESUME_NORMAL_OPERATION ) )

    if dev.pen_config in ( status.AGENT_CONFIG_NONE, status.AGENT_CONFIG_INVALID ):
        return

    elif dev.pen_config == status.AGENT_CONFIG_BLACK_ONLY:
        ldl_file = 'cbbcal.ldl.gz'
    
    elif dev.pen_config == status.AGENT_CONFIG_COLOR_ONLY:
        ldl_file = 'cbccal.ldl.gz'
    
    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_BLACK:
        ldl_file = 'cb2pcal.ldl.gz'
        
    dev.writeChannel( channel_id, ldl.buildSetPrinterAlignmentPacket( 0, 0, 0, 0 ) )
    dev.closeChannel( 'PRINT' )
    
    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'ldl', ldl_file ), callback, False )
    

def alignType4Phase2( dev, a, b, c, d, e ): # Type 4 (LIDIL 0.3.8)
    log.debug( "A=%d, B=%d, C=%d, D=%d, E=%d" % ( a, b, c, d, e ) )
    
    if dev.pen_config in ( status.AGENT_CONFIG_NONE, status.AGENT_CONFIG_INVALID ):
        return

    channel_id = dev.checkOpenChannel( 'PRINT' )
    
    # ZCA
    zca = ( 7 - a ) * -48
    dev.writeChannel( channel_id, ldl.buildZCAPacket( zca ) )
    
    if dev.pen_config == status.AGENT_CONFIG_BLACK_ONLY:
        k_bidi = ( 6 - b ) * 2
        dev.writeChannel( channel_id, ldl.buildSetPrinterAlignmentPacket( k_bidi, 0, 0, 0 ) )

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_ONLY:
        cmy_bidi = ( 6 - b ) * 2
        dev.writeChannel( channel_id, ldl.buildSetPrinterAlignmentPacket( 0, 0, 0, cmy_bidi ) )

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_BLACK:
        vert = ( 9 - b ) * 2 
        hort = ( 9 - c ) * -2 
        k_bidi = ( 6 - d ) * 2 
        cmy_bidi = ( 6 - e ) * 2 
        dev.writeChannel( channel_id, ldl.buildSetPrinterAlignmentPacket( k_bidi, hort, vert, cmy_bidi ) )
        
    # Set alignment
    dev.writeChannel( channel_id, ldl.buildSetPensAlignedPacket() )
    dev.closeChannel( 'PRINT' )
    
def alignType4Phase3( dev, callback=None ): # Type 4 (LIDIL 0.3.8)
    if dev.pen_config == status.AGENT_CONFIG_COLOR_AND_BLACK:
        dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'ldl', 'cb2pcal_done.ldl.gz' ), callback, False )
    

def alignType5Phase1( dev, callback=None ): # Type 5 (xBow+/LIDIL 0.4.3)
    channel_id = dev.checkOpenChannel( 'PRINT' )
    dev.writeChannel( channel_id, ldl.buildLIDILPacket( ldl.PACKET_TYPE_RESUME_NORMAL_OPERATION ) )

    if dev.pen_config in ( status.AGENT_CONFIG_NONE, status.AGENT_CONFIG_INVALID ):
        return

    elif dev.pen_config == status.AGENT_CONFIG_BLACK_ONLY:
        ldl_file = 'cbbcal.ldl.gz'

    elif dev.pen_config == status.AGENT_CONFIG_PHOTO_ONLY:
        ldl_file = 'cbpcal.ldl.gz'

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_ONLY:
        ldl_file = 'cbccal.ldl.gz'

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_BLACK:
        ldl_file = 'cb2pcal.ldl.gz'

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_PHOTO:
        ldl_file = 'cbcpcal.ldl.gz'

    dev.writeChannel( channel_id, ldl.buildZCAPacket( 0 ) )
    dev.writeChannel( channel_id, ldl.buildColorHortPacket( 0 ) )
    dev.writeChannel( channel_id, ldl.buildColorVertPacket( 0 ) )
    dev.writeChannel( channel_id, ldl.buildBlackVertPacket( 0 ) )
    dev.writeChannel( channel_id, ldl.buildBlackHortPacket( 0 ) )
    dev.writeChannel( channel_id, ldl.buildBlackBidiPacket( 0 ) )
    dev.writeChannel( channel_id, ldl.buildColorBidiPacket( 0 ) )
    dev.writeChannel( channel_id, ldl.buildPhotoHuePacket( 0 ) )
    dev.writeChannel( channel_id, ldl.buildColorHuePacket( 0 ) )
    dev.closeChannel( 'PRINT' )

    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'ldl', ldl_file ), callback, False )
    
    
def alignType5Phase2( dev, a, b, c, d, e, f, g ): # Type 5 (xBow+/LIDIL 0.4.3)
    log.debug( "A=%d, B=%d, C=%d, D=%d, E=%d, F=%d, G=%d" % ( a, b, c, d, e, f, g ) )
    
    if dev.pen_config in ( status.AGENT_CONFIG_NONE, status.AGENT_CONFIG_INVALID ):
        return

    channel_id = dev.checkOpenChannel( 'PRINT' )
    
    # ZCA
    zca = ( 7 - a ) * -48
    dev.writeChannel( channel_id, ldl.buildZCAPacket( zca ) )
    
    if dev.pen_config == status.AGENT_CONFIG_BLACK_ONLY:
        k_bidi = ( 6 - b ) * 2
        dev.writeChannel( channel_id, ldl.buildBlackBidiPacket( k_bidi ) )

    elif dev.pen_config == status.AGENT_CONFIG_PHOTO_ONLY:
        kcm_bidi = ( 6 - b ) * 2
        dev.writeChannel( channel_id, ldl.buildPhotoBidiPacket( kcm_bidi ) )

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_ONLY:
        cmy_bidi = ( 6 - b ) * 2
        dev.writeChannel( channel_id, ldl.buildColorBidiPacket( cmy_bidi ) )

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_BLACK:
        vert = ( 9 - b ) * 2 
        hort = ( 9 - c ) * -2 
        k_bidi = ( 6 - d ) * 2 
        cmy_bidi = ( 6 - e ) * 2 

        dev.writeChannel( channel_id, ldl.buildColorHortPacket( 0 ) )
        dev.writeChannel( channel_id, ldl.buildColorVertPacket( 0 ) )
        dev.writeChannel( channel_id, ldl.buildBlackVertPacket( vert ) )
        dev.writeChannel( channel_id, ldl.buildBlackHortPacket( hort ) )
        dev.writeChannel( channel_id, ldl.buildBlackBidiPacket( k_bidi ) )
        dev.writeChannel( channel_id, ldl.buildColorBidiPacket( cmy_bidi ) )

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_PHOTO:
        vert = ( 9 - b ) * 2
        hort = ( 9 - c ) * -2
        cmy_bidi = ( 6 - d ) * 2
        kcm_bidi = ( 6 - e ) * 2

        photo_adj = ldl.PHOTO_ALIGN_TABLE[f][g]
        color_adj = ldl.COLOR_ALIGN_TABLE[f][g]

        dev.writeChannel( channel_id, ldl.buildPhotoHortPacket( hort ) )
        dev.writeChannel( channel_id, ldl.buildPhotoVertPacket( vert ) )
        dev.writeChannel( channel_id, ldl.buildColorHortPacket( 0 ) )
        dev.writeChannel( channel_id, ldl.buildColorVertPacket( 0 ) )
        dev.writeChannel( channel_id, ldl.buildPhotoBidiPacket( kcm_bidi ) )
        dev.writeChannel( channel_id, ldl.buildColorBidiPacket( cmy_bidi ) )
        dev.writeChannel( channel_id, ldl.buildPhotoHuePacket( photo_adj ) )
        dev.writeChannel( channel_id, ldl.buildColorHuePacket( color_adj ) )

    # Set alignment
    dev.writeChannel( channel_id, ldl.buildSetPensAlignedPacket() )
    dev.closeChannel( 'PRINT' )

def alignType5Phase3( dev, callback=None ): # Type 5 (xBow+/LIDIL 0.4.3)

    if dev.pen_config == status.AGENT_CONFIG_COLOR_AND_BLACK:
        dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'ldl', "cb2pcal_done.ldl.gz" ), callback, False )
    
    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_PHOTO:
        dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'ldl', "cbccal_done.ldl.gz" ), callback, False ) 

    dev.closeChannel( 'PRINT' )
    
def alignType6Phase1( dev ): # Type 6 (xBow AiO)
    channel_id = dev.checkOpenChannel( 'PRINT' )
    dev.writeChannel( channel_id, ldl.buildPrintInternalPagePacket() )
    dev.closeChannel( 'PRINT' )
    
def alignType7Phase1( dev, callback=None ): # Type 7 (xBow VIP)
    channel_id = dev.checkOpenChannel( 'PRINT' )
    # Zero out all alignment values
    dev.sendEmbeddedPMLEx( pml.OID_AGENT1_BIDIR_ADJUSTMENT, 0 )

    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_VERTICAL_ALIGNMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT2_BIDIR_ADJUSTMENT, 0 )

    dev.sendEmbeddedPMLEx( pml.OID_AGENT3_VERTICAL_ALIGNMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT3_HORIZONTAL_ALIGNMENT, 0 )
    dev.sendEmbeddedPMLEx( pml.OID_AGENT3_BIDIR_ADJUSTMENT, 0 )
    
    dev.sendEmbeddedPMLEx( pml.OID_ZCA, 0 )

    if dev.pen_config in ( status.AGENT_CONFIG_NONE, status.AGENT_CONFIG_INVALID ):
        return

    elif dev.pen_config == status.AGENT_CONFIG_BLACK_ONLY:
        pcl_file = 'crbcal.pcl.gz'

    elif dev.pen_config == status.AGENT_CONFIG_PHOTO_ONLY:
        pcl_file = 'crpcal.pcl.gz'

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_ONLY:
        pcl_file = 'crccal.pcl.gz'

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_BLACK:
        pcl_file = 'crcbcal.pcl.gz'

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_PHOTO:
        pcl_file = 'crcpcal.pcl.gz'
        
    dev.closeChannel( 'PRINT' )

    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'pcl', pcl_file ), callback, False )


def alignType7Phase2( dev, a, b, c, d, e, f, g ): # Type 7 (xBow VIP)
    log.debug( "A=%d, B=%d, C=%d, D=%d, E=%d, F=%d, G=%d" % ( a, b, c, d, e, f, g ) )

    channel_id = dev.checkOpenChannel( 'PRINT' )
    # ZCA
    zca = ( 7 - a ) * -12
    dev.sendEmbeddedPMLEx( pml.OID_ZCA, zca )

    if dev.pen_config == status.AGENT_CONFIG_BLACK_ONLY:
        k_bidi = ( 6 - b ) * 6
        dev.sendEmbeddedPMLEx( pml.OID_AGENT1_BIDIR_ADJUSTMENT, k_bidi )

    elif dev.pen_config == status.AGENT_CONFIG_PHOTO_ONLY:
        kcm_bidi = ( 6 - b ) * 6
        dev.sendEmbeddedPMLEx( pml.OID_AGENT3_BIDIR_ADJUSTMENT, kcm_bidi )

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_ONLY:
        cmy_bidi = ( 6 - b ) * 6
        dev.sendEmbeddedPMLEx( pml.OID_AGENT2_BIDIR_ADJUSTMENT, cmy_bidi )

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_BLACK:
        vert = ( 9 - b ) * 6
        hort = ( 9 - c ) * -6 
        k_bidi = ( 6 - d ) * 6 
        cmy_bidi = ( 6 - e ) * 6 

        dev.sendEmbeddedPMLEx( pml.OID_AGENT1_BIDIR_ADJUSTMENT, k_bidi )
        dev.sendEmbeddedPMLEx( pml.OID_AGENT2_BIDIR_ADJUSTMENT, cmy_bidi )
        dev.sendEmbeddedPMLEx( pml.OID_AGENT2_HORIZONTAL_ALIGNMENT, hort )
        dev.sendEmbeddedPMLEx( pml.OID_AGENT2_VERTICAL_ALIGNMENT, vert )

    elif dev.pen_config == status.AGENT_CONFIG_COLOR_AND_PHOTO:
        vert = ( 9 - b ) * 6
        hort = ( 9 - c ) * -6
        cmy_bidi = ( 6 - d ) * 6
        kcm_bidi = ( 6 - e ) * 6

        photo_adj = ldl.PHOTO_ALIGN_TABLE[f][g]
        color_adj = ldl.COLOR_ALIGN_TABLE[f][g]
        
        x = ( color_adj << 8 ) + photo_adj
        
        dev.sendEmbeddedPMLEx( pml.OID_COLOR_CALIBRATION_SELECTION, x )

        dev.sendEmbeddedPMLEx( pml.OID_AGENT2_BIDIR_ADJUSTMENT, cmy_bidi )
        dev.sendEmbeddedPMLEx( pml.OID_AGENT3_BIDIR_ADJUSTMENT, kcm_bidi )
        dev.sendEmbeddedPMLEx( pml.OID_AGENT3_HORIZONTAL_ALIGNMENT, hort )
        dev.sendEmbeddedPMLEx( pml.OID_AGENT3_VERTICAL_ALIGNMENT, vert )
        
        dev.closeChannel( 'PRINT' )
        
def alignType7Phase3( dev, callback=None ): # Type 7 (xBow VIP)
    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'pcl', "crcaldone.pcl.gz" ), callback, False ) 
    
def alignType8Phase1( dev, callback=None ): # 450
    pens = dev.deviceIDStatus()['agents']
    
    if pens[0]['type'] == status.AGENT_TYPE_KCM or \
       pens[1]['type'] == status.AGENT_TYPE_KCM :
        f, num_inks = 'align6_450.pcl.gz', 6
    else:
        f, num_inks = 'align4_450.pcl.gz', 4
    
    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'pcl', f ), callback )
    
    return num_inks
    
def alignType8Phase2( dev, num_inks, a, b, c, d ): # 450
    align_values1 = { 1 : '\x00\x00\x18',
                      2 : '\x00\x00\x12',
                      3 : '\x00\x00\x0c',
                      4 : '\x00\x00\x06',    
                      5 : '\x00\x00\x00',    
                      6 : '\x01\x00\x06',    
                      7 : '\x01\x00\x0c',    
                      8 : '\x01\x00\x12',    
                      9 : '\x01\x00\x18',    
                    }
                    
    align_values2 = { 1 : '\x00\x00\x12',
                      2 : '\x00\x00\x0c',
                      3 : '\x00\x00\x06',
                      4 : '\x00\x00\x00',    
                      5 : '\x01\x00\x06',    
                      6 : '\x01\x00\x0c',    
                      7 : '\x01\x00\x12',    
                      8 : '\x01\x00\x18',    
                      9 : '\x01\x00\x1e',    
                    }

    align_values3 = { 1 : '\x00\x00\x24',
                      2 : '\x00\x00\x18',
                      3 : '\x00\x00\x12',
                      4 : '\x00\x00\x06',    
                      5 : '\x00\x00\x00',    
                      6 : '\x01\x00\x06',    
                      7 : '\x01\x00\x12',    
                      8 : '\x01\x00\x18',    
                      9 : '\x01\x00\x24',    
                    }
    
    if num_inks == 4:
        s = ''.join( [ pcl.UEL, 
              '@PJL ENTER LANGUAGE=PCL3GUI\n', 
              pcl.RESET, 
              pcl.ESC, '*o5W\x1a\x01', align_values1[a], 
              pcl.ESC, '*o5W\x1a\x02', align_values2[a], 
              pcl.ESC, '*o5W\x1a\x03', align_values1[b], 
              pcl.ESC, '*o5W\x1a\x04', align_values1[b], 
              pcl.ESC, '*o5W\x1a\x08', align_values1[c], 
              pcl.ESC, '*o5W\x1a\x07', align_values1[d], 
              pcl.RESET,
              pcl.UEL ] )

    else: # 6
        s = ''.join( [ pcl.UEL, 
              '@PJL ENTER LANGUAGE=PCL3GUI\n', 
              pcl.RESET, 
              pcl.ESC, '*o5W\x1a\x05', align_values1[a], 
              pcl.ESC, '*o5W\x1a\x06', align_values3[a], 
              pcl.ESC, '*o5W\x1a\x03', align_values1[b], 
              pcl.ESC, '*o5W\x1a\x04', align_values1[b], 
              pcl.ESC, '*o5W\x1a\x0a', align_values1[c], 
              pcl.ESC, '*o5W\x1a\x09', align_values1[d], 
              pcl.RESET,
              pcl.UEL ] )
                  
    channel_id = dev.checkOpenChannel( 'PRINT' )
    dev.writeChannel( channel_id, s )
    dev.closeChannel( 'PRINT' )


def cleanType1( dev ): # PCL, Level 1
    #dev.writeChannel( dev.checkOpenChannel( 'PRINT' ),
    #                  '\x1bE\x1b&b16WPML \x04\x00\x06\x01\x04\x01\x05 \x01\x01\x04\x01d\x1b%-12345X' )
    dev.sendEmbeddedPML( '1.4.1.5.1.1', 100, pml.TYPE_ENUMERATION )
    dev.closeChannel( 'PRINT' )
    

def primeType1( dev ): # PCL, Level 2
    #dev.writeChannel( dev.checkOpenChannel( 'PRINT' ),
    #                  '\x1bE\x1b&b16WPML \x04\x00\x06\x01\x04\x01\x05 \x01\x01\x04\x01\xc8\x1b%-12345X' )
    dev.sendEmbeddedPML( '1.4.1.5.1.1', 200, pml.TYPE_ENUMERATION )
    dev.closeChannel( 'PRINT' )

def wipeAndSpitType1( dev ): # PCL, Level 3
    #dev.writeChannel( dev.checkOpenChannel( 'PRINT' ),
    #                  '\x1bE\x1b&b16WPML \x04\x00\x06\x01\x04\x01\x05 \x01\x01\x04\x02\x01\x1b%-12345X' )
    dev.sendEmbeddedPML( '1.4.1.5.1.1', 300, pml.TYPE_ENUMERATION )
    dev.closeChannel( 'PRINT' )
        
def cleanType2( dev ): # LIDIL, Level 1
    p = ldl.buildLIDILPacket( ldl.PACKET_TYPE_COMMAND, ldl.COMMAND_HANDLE_PEN, 
                              ldl.COMMAND_HANDLE_PEN_CLEAN_LEVEL1 )
                              
    dev.writeChannel( dev.checkOpenChannel( 'PRINT' ), p )
    dev.closeChannel( 'PRINT' )
    
def primeType2( dev ): # LIDIL, Level 2
    p = ldl.buildLIDILPacket( ldl.PACKET_TYPE_COMMAND, ldl.COMMAND_HANDLE_PEN, 
                              ldl.COMMAND_HANDLE_PEN_CLEAN_LEVEL2 )

    dev.writeChannel( dev.checkOpenChannel( 'PRINT' ), p )
    dev.closeChannel( 'PRINT' )
    
def wipeAndSpitType2( dev ): # LIDIL, Level 3
    p = ldl.buildLIDILPacket( ldl.PACKET_TYPE_COMMAND, ldl.COMMAND_HANDLE_PEN, 
                              ldl.COMMAND_HANDLE_PEN_CLEAN_LEVEL3 )
                              
    dev.writeChannel( dev.checkOpenChannel( 'PRINT' ), p )
    dev.closeChannel( 'PRINT' )

def colorCalType1( dev, loadpaper_ui, colorcal_ui, photopenreq_ui, busy_callback ): # 450
    value, state = 4, 0
    dialogState = False
    while state != -1:
        
        if state == 0:
            if colorCalType1PenCheck( dev ):
                state = 1
            else:
                state = 100
        
        elif state == 1:
            state = -1
            dialogState = loadpaper_ui()
            if dialogState:
                colorCalType1Phase1( dev, busy_callback )
                state = 2
                
        elif state == 2:
            state = -1
            ok, value = colorcal_ui()
            if ok:
                state = 3
                
        elif state == 3:
            colorCalType1Phase2( dev, value )
            state = -1
            
        elif state == 100:
            photopenreq_ui()
            state = -1

    return dialogState

def colorCalType1PenCheck( dev ): # 450
    pens = dev.deviceIDStatus()['agents']
    
    if ( pens[0]['type'] == status.AGENT_TYPE_CMY and 
         pens[1]['type'] == status.AGENT_TYPE_KCM ) or \
        ( pens[0]['type'] == status.AGENT_TYPE_KCM and 
          pens[1]['type'] == status.AGENT_TYPE_CMY ) :
        
        return True

    else:
        log.error( "Cannot perform color calibration with no photo pen installed." )
        return False


def colorCalType1Phase1( dev, callback=None ): # 450
    dev.printGzipFile( os.path.join( prop.home_dir, 'data', 'pcl', 'colorcal1_450.pcl.gz' ), callback, False )
    
def colorCalType1Phase2( dev, value ): # 450

    color_cal = { 1 : ( '\x0f\x3c', '\x17\x0c' ),
                  2 : ( '\x10\xcc', '\x15\x7c' ),
                  3 : ( '\x12\x5c', '\x13\xec' ),
                  4 : ( '\x13\xec', '\x12\x5c' ),
                  5 : ( '\x15\x7c', '\x10\xcc' ),
                  6 : ( '\x17\x0c', '\x0f\x3c' ),
                  7 : ( '\x18\x9c', '\x0d\xac' ),
                }
    
    s = ''.join( [ pcl.UEL, 
                  '@PJL ENTER LANGUAGE=PCL3GUI\n', 
                  pcl.RESET, 
                  pcl.ESC, '*o5W\x1a\x0c\x00', color_cal[value][0], 
                  pcl.ESC, '*o5W\x1a\x0b\x00', color_cal[value][1], 
                  pcl.RESET,
                  pcl.UEL ] )
                  
    dev.writeChannel( dev.checkOpenChannel( 'PRINT' ), s )
    dev.closeChannel( 'PRINT' )

