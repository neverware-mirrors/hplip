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

from base.g import *
from base import utils
from qt import *
from settingsdialog_base import SettingsDialog_base

class SettingsDialog(SettingsDialog_base):
    def __init__(self, cleaning_level, parent = None,name = None,modal = 0,fl = 0):
        SettingsDialog_base.__init__(self,parent,name,modal,fl)
        self.cleaning_level = cleaning_level
        self.CleaningLevel.setButton( self.cleaning_level )
        self.DefaultsButton.setEnabled( False )
        
    def PrintCmdChangeButton_clicked(self):
        #self.PrintCommand
        pass
        
    def ScanCmdChangeButton_clicked(self):
        #self.ScanCommand
        pass
        
    def AccessPCardCmdChangeButton_clicked(self):
        #self.AccessPCardCommand
        pass
        
    def SendFaxCmdChangeButton_clicked(self):
        #self.SendFaxCommand
        pass
        
    def MakeCopiesCmdChangeButton_clicked(self):
        #self.MakeCopiesCommand
        pass
        
    def CleaningLevel_clicked(self,a0):
        self.cleaning_level = a0
        
    def DefaultsButton_clicked(self):
        cmd_print, cmd_scan, cmd_pcard, cmd_copy, cmd_fax = utils.deviceDefaultFunctions()
        self.PrintCommand.setText( cmd_print )
        self.ScanCommand.setText( cmd_scan )
        self.AccessPCardCommand.setText( cmd_pcard )
        self.SendFaxCommand.setText( cmd_fax )
        self.MakeCopiesCommand.setText( cmd_copy )

    def TabWidget_currentChanged(self,a0):
        name = str( a0.name() )
        
        if name == 'FunctionCommands':
            self.DefaultsButton.setEnabled( True )
        else:
            self.DefaultsButton.setEnabled( False )
      
    
    def EmailTestButton_clicked(self):
        print "SettingsDialog_base.EmailTestButton_clicked(): Not implemented yet"  
        
        
