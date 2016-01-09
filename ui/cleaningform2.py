# -*- coding: utf-8 -*-

import sys
from base.g import *
from qt import *
import os.path
from cleaningform2_base import CleaningForm2_base

class CleaningForm2(CleaningForm2_base):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        CleaningForm2_base.__init__(self,parent,name,modal,fl)

        self.Icon.setPixmap( QPixmap( os.path.join( prop.image_dir, 'clean.png' ) ) )
