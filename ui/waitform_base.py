# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/dwelch/linux-imaging-and-printing/src/ui/waitform_base.ui'
#
# Created: Tue Jan 25 11:22:49 2005
#      by: The PyQt User Interface Compiler (pyuic) 3.13
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class WaitForm_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("WaitForm_base")


        WaitForm_baseLayout = QGridLayout(self,1,1,11,6,"WaitForm_baseLayout")

        layout2 = QVBoxLayout(None,0,6,"layout2")

        self.textLabel3 = QLabel(self,"textLabel3")
        layout2.addWidget(self.textLabel3)

        self.ProgressBar = QProgressBar(self,"ProgressBar")
        layout2.addWidget(self.ProgressBar)

        WaitForm_baseLayout.addLayout(layout2,0,0)
        spacer10 = QSpacerItem(20,31,QSizePolicy.Minimum,QSizePolicy.Expanding)
        WaitForm_baseLayout.addItem(spacer10,1,0)

        self.languageChange()

        self.resize(QSize(424,87).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager - Waiting"))
        self.textLabel3.setText(self.__tr("<b>Waiting for procedure to finish...</b>"))


    def __tr(self,s,c = None):
        return qApp.translate("WaitForm_base",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = WaitForm_base()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
