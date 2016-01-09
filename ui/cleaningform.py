# -*- coding: utf-8 -*-


#import sys
from qt import *
from cleaningform_base import CleaningForm_base
from base.g import *
import os.path

class CleaningForm(CleaningForm_base):
    def __init__(self, parent, cleaning_level, name = None, modal = 0, fl = 0):
        CleaningForm_base.__init__(self,parent,name,modal,fl)

        text = str( self.CleaningText.text() )
        self.CleaningText.setText( text % str( cleaning_level + 1 ) )
        
        text = str( self.Continue.text() )
        self.Continue.setText( text % str( cleaning_level + 1 ) )
        
        text = str( self.CleaningTitle.text() )
        self.CleaningTitle.setText( text % str( cleaning_level ) )

        self.Icon.setPixmap( QPixmap( os.path.join( prop.image_dir, 'clean.png' ) ) )
    
