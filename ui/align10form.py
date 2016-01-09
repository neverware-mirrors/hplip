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
import os.path
from qt import *
from align10form_base import Align10Form_Base

class Align10Form(Align10Form_Base):
    def __init__(self, pattern, parent = None, name = None, modal = 0, fl = 0):
        Align10Form_Base.__init__(self,parent,name,modal,fl)
        self.Icon.setPixmap( QPixmap( os.path.join( prop.image_dir, 'align10.png' ) ) )
        if pattern == 1:
            self.controls = { 'A' : (True, 23),
                             'B' : (True, 9),
                             'C' : (True, 9),
                             'D' : (False, 0),
                             'E' : (False, 0),
                             'F' : (False, 0),
                             'G' : (False, 0),
                             'H' : (False, 0),}
        elif pattern == 2:
            self.controls = { 'A' : (True, 23),
                             'B' : (True, 17),
                             'C' : (True, 23),
                             'D' : (True, 23),
                             'E' : (True, 9),
                             'F' : (True, 9),
                             'G' : (True, 9),
                             'H' : (True, 9),}
        
        elif pattern == 3:
            self.controls = { 'A' : (True, 23),
                             'B' : (True, 9),
                             'C' : (True, 23),
                             'D' : (True, 23),
                             'E' : (True, 9),
                             'F' : (True, 9),
                             'G' : (True, 9),
                             'H' : (True, 9),}

        for line in self.controls:
            if not self.controls[line][0]:
                eval('self.comboBox%s.setEnabled(False)' % line )
            else:
                for x in range(self.controls[line][1]):
                    eval('self.comboBox%s.insertItem("%s%d")' % (line, line, x+1))
    
    def getValues(self):
        ret = []
        for line in self.controls:
            if not self.controls[line][0]:
                ret.append(0)
            else:
                exec('selected = str(self.comboBox%s.currentText())' % line)
                try:
                    selected = int(selected[1:])
                except ValueError:
                    selected = 0
                ret.append(selected)
        
        return ret
        
