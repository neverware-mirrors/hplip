# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/dwelch/linux-imaging-and-printing/src/ui/successform_base.ui'
#
# Created: Mon Oct 4 09:29:25 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.11
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class SuccessForm_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("SuccessForm_base")


        SuccessForm_baseLayout = QGridLayout(self,1,1,11,6,"SuccessForm_baseLayout")

        self.Icon = QLabel(self,"Icon")
        self.Icon.setSizePolicy(QSizePolicy(0,0,0,0,self.Icon.sizePolicy().hasHeightForWidth()))
        self.Icon.setScaledContents(1)

        SuccessForm_baseLayout.addWidget(self.Icon,0,0)

        self.textLabel1 = QLabel(self,"textLabel1")

        SuccessForm_baseLayout.addWidget(self.textLabel1,0,1)

        self.pushButton23 = QPushButton(self,"pushButton23")

        SuccessForm_baseLayout.addWidget(self.pushButton23,1,2)
        spacer22 = QSpacerItem(501,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        SuccessForm_baseLayout.addMultiCell(spacer22,1,1,0,1)

        self.languageChange()

        self.resize(QSize(544,108).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton23,SIGNAL("clicked()"),self,SLOT("close()"))


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager"))
        self.textLabel1.setText(self.__tr("Operation completed successfully."))
        self.pushButton23.setText(self.__tr("OK"))


    def __tr(self,s,c = None):
        return qApp.translate("SuccessForm_base",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = SuccessForm_base()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
