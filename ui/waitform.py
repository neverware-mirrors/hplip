# -*- coding: utf-8 -*-

import sys
from qt import *
from waitform_base import WaitForm_base

class WaitForm(WaitForm_base):
    def __init__(self, seconds, parent = None, name = None, modal = 0, fl = 0):
        WaitForm_base.__init__(self,parent,name,modal,fl)
        
        self.wait_timer = QTimer(self, "WaitTimer")
        self.connect( self.wait_timer, SIGNAL('timeout()'), self.wait_timer_timeout )
        self.seconds = seconds
        self.wait_timer.start( 1000 )
        self.progress = 0
        self.ProgressBar.setTotalSteps( self.seconds )

    def wait_timer_timeout( self ):
        self.progress += 1
        self.ProgressBar.setProgress( self.progress )

        if self.progress == self.seconds:
            self.wait_timer.stop()
            self.close()
 
