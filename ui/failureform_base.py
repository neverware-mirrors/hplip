# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/dwelch/linux-imaging-and-printing/src/ui/failureform_base.ui'
#
# Created: Mon Oct 4 11:37:48 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.11
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class FailureForm_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("FailureForm_base")


        FailureForm_baseLayout = QGridLayout(self,1,1,11,6,"FailureForm_baseLayout")

        self.Icon = QLabel(self,"Icon")
        self.Icon.setSizePolicy(QSizePolicy(0,0,0,0,self.Icon.sizePolicy().hasHeightForWidth()))
        self.Icon.setScaledContents(1)

        FailureForm_baseLayout.addWidget(self.Icon,0,0)

        self.pushButton23 = QPushButton(self,"pushButton23")

        FailureForm_baseLayout.addWidget(self.pushButton23,1,2)
        spacer22 = QSpacerItem(501,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        FailureForm_baseLayout.addMultiCell(spacer22,1,1,0,1)

        layout10 = QVBoxLayout(None,0,6,"layout10")

        self.textLabel1 = QLabel(self,"textLabel1")
        layout10.addWidget(self.textLabel1)

        self.ErrorText = QLabel(self,"ErrorText")
        self.ErrorText.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)
        layout10.addWidget(self.ErrorText)

        FailureForm_baseLayout.addMultiCellLayout(layout10,0,0,1,2)

        self.languageChange()

        self.resize(QSize(544,147).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton23,SIGNAL("clicked()"),self,SLOT("close()"))


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager"))
        self.pushButton23.setText(self.__tr("OK"))
        self.textLabel1.setText(self.__tr("Operation <b>failed.</b>"))
        self.ErrorText.setText(self.__tr("ERROR TEXT"))


    def __tr(self,s,c = None):
        return qApp.translate("FailureForm_base",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = FailureForm_base()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
