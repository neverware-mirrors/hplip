# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/pparks/linux-imaging-and-printing/src/ui/aligntype6form1_base.ui'
#
# Created: Thu Jan 6 14:14:11 2005
#      by: The PyQt User Interface Compiler (pyuic) 3.13
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class AlignType6Form1_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("AlignType6Form1_base")


        AlignType6Form1_baseLayout = QGridLayout(self,1,1,11,6,"AlignType6Form1_baseLayout")
        spacer2 = QSpacerItem(313,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        AlignType6Form1_baseLayout.addItem(spacer2,1,0)

        self.printPageButton = QPushButton(self,"printPageButton")

        AlignType6Form1_baseLayout.addWidget(self.printPageButton,1,2)

        self.pushButton2 = QPushButton(self,"pushButton2")

        AlignType6Form1_baseLayout.addWidget(self.pushButton2,1,3)

        self.textLabel1 = QLabel(self,"textLabel1")
        self.textLabel1.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)

        AlignType6Form1_baseLayout.addMultiCellWidget(self.textLabel1,0,0,0,3)

        self.cancelButton = QPushButton(self,"cancelButton")

        AlignType6Form1_baseLayout.addWidget(self.cancelButton,1,1)

        self.languageChange()

        self.resize(QSize(627,188).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton2,SIGNAL("clicked()"),self.accept)
        self.connect(self.cancelButton,SIGNAL("clicked()"),self.reject)
        self.connect(self.printPageButton,SIGNAL("clicked()"),self.printPageButton_clicked)


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager - Alignment"))
        self.printPageButton.setText(self.__tr("Print Page"))
        self.pushButton2.setText(self.__tr("Next >"))
        self.textLabel1.setText(self.__tr("To perform alignment, you will need the <b>alignment page</b> that is automatically printed after you install a print cartridge.\n"
"<p> If you do <b>not</b> have this page, click <i>Print Page</i>.\n"
"<p>If you already have this page, click <i>Next ></i>."))
        self.cancelButton.setText(self.__tr("Cancel"))




    def printPageButton_clicked(self):
        print "AlignType6Form1_base.printPageButton_clicked(): Not implemented yet"

    def __tr(self,s,c = None):
        return qApp.translate("AlignType6Form1_base",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = AlignType6Form1_base()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
