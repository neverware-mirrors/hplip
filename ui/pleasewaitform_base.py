# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/homes/dwelch/lnx/Projects/hplups/pleasewaitform_base.ui'
#
# Created: Wed Sep 10 14:22:48 2003
#      by: The PyQt User Interface Compiler (pyuic) 3.6
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class PleaseWaitForm_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("PleaseWaitForm_base")

        self.setSizePolicy(QSizePolicy(1,1,0,0,self.sizePolicy().hasHeightForWidth()))
        f = QFont(self.font())
        f.setPointSize(12)
        self.setFont(f)

        PleaseWaitForm_baseLayout = QGridLayout(self,1,1,11,6,"PleaseWaitForm_baseLayout")

        self.textLabel1 = QLabel(self,"textLabel1")

        PleaseWaitForm_baseLayout.addWidget(self.textLabel1,0,0)

        self.languageChange()

        self.resize(QSize(134,41).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)


    def languageChange(self):
        self.setCaption(self.tr("Please Wait"))
        self.textLabel1.setText(self.tr("Please wait..."))


if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = PleaseWaitForm_base()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
