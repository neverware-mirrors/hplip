# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/dwelch/linux-imaging-and-printing/src/ui/bothpensrequiredform_base.ui'
#
# Created: Thu Nov 18 13:56:06 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.12
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class BothPensRequiredForm_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("BothPensRequiredForm_base")


        BothPensRequiredForm_baseLayout = QGridLayout(self,1,1,11,6,"BothPensRequiredForm_baseLayout")

        self.Icon = QLabel(self,"Icon")
        self.Icon.setSizePolicy(QSizePolicy(0,0,0,0,self.Icon.sizePolicy().hasHeightForWidth()))
        self.Icon.setFrameShape(QLabel.NoFrame)
        self.Icon.setScaledContents(1)

        BothPensRequiredForm_baseLayout.addWidget(self.Icon,0,0)

        self.textLabel7 = QLabel(self,"textLabel7")
        self.textLabel7.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)

        BothPensRequiredForm_baseLayout.addMultiCellWidget(self.textLabel7,0,0,1,2)

        self.pushButton49 = QPushButton(self,"pushButton49")

        BothPensRequiredForm_baseLayout.addWidget(self.pushButton49,1,2)
        spacer43 = QSpacerItem(570,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        BothPensRequiredForm_baseLayout.addMultiCell(spacer43,1,1,0,1)

        self.languageChange()

        self.resize(QSize(652,216).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton49,SIGNAL("clicked()"),self,SLOT("accept()"))


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager - Both Cartridges Required"))
        self.textLabel7.setText(self.__tr("<b>Both cartridges are required for alignment.</b> Please install both cartridges and try again."))
        self.pushButton49.setText(self.__tr("OK"))


    def __tr(self,s,c = None):
        return qApp.translate("BothPensRequiredForm_base",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = BothPensRequiredForm_base()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
