# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/dwelch/linux-imaging-and-printing/src/ui/aboutdlg_base.ui'
#
# Created: Wed Nov 17 11:17:37 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.12
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class AboutDlg_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("AboutDlg_base")


        AboutDlg_baseLayout = QGridLayout(self,1,1,11,6,"AboutDlg_baseLayout")

        self.pushButton15 = QPushButton(self,"pushButton15")

        AboutDlg_baseLayout.addWidget(self.pushButton15,6,2)
        spacer15 = QSpacerItem(481,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        AboutDlg_baseLayout.addMultiCell(spacer15,6,6,0,1)
        spacer14 = QSpacerItem(20,21,QSizePolicy.Minimum,QSizePolicy.Expanding)
        AboutDlg_baseLayout.addItem(spacer14,5,1)

        self.textLabel3 = QLabel(self,"textLabel3")

        AboutDlg_baseLayout.addMultiCellWidget(self.textLabel3,3,3,0,2)

        self.textLabel4 = QLabel(self,"textLabel4")

        AboutDlg_baseLayout.addWidget(self.textLabel4,2,0)

        self.textLabel2 = QLabel(self,"textLabel2")

        AboutDlg_baseLayout.addMultiCellWidget(self.textLabel2,4,4,0,2)

        self.VersionText = QLabel(self,"VersionText")

        AboutDlg_baseLayout.addWidget(self.VersionText,2,1)
        spacer16 = QSpacerItem(20,21,QSizePolicy.Minimum,QSizePolicy.Expanding)
        AboutDlg_baseLayout.addItem(spacer16,1,0)

        self.textLabel1 = QLabel(self,"textLabel1")

        AboutDlg_baseLayout.addMultiCellWidget(self.textLabel1,0,0,0,2)

        self.languageChange()

        self.resize(QSize(465,487).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton15,SIGNAL("clicked()"),self,SLOT("close()"))


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager - About"))
        self.pushButton15.setText(self.__tr("OK"))
        self.textLabel3.setText(self.__tr("<b>License and Copyright:</b>\n"
"(c) Copyright 2004 Hewlett-Packard Development Company, L.P. This software is licensed under the GNU General Public License (GPL) and the MIT License. See the software sources for details."))
        self.textLabel4.setText(self.__tr("<b>Software Version:</b>"))
        self.textLabel2.setText(self.__tr("<b>Authors and Contributors:</b>\n"
"David Suffield, Don Welch, Shiyun Yie, \n"
"John Oleinik, Cory Meisch, Foster Nuffer,\n"
"Pete Parks, Jacqueline Pitter, Raghothama Cauligi,\n"
"David Paschal,\n"
"Steve DeRoos, Kathy Hartshorn, Sharon Asker, \n"
"Bill Powell, Elizabeth Atwater, Mark Overton"))
        self.VersionText.setText(self.__tr("0.0.0"))
        self.textLabel1.setText(self.__tr("<font size=\"+3\"><p align=\"center\">HP Linux Imaging and Printing System</p></font>"))


    def __tr(self,s,c = None):
        return qApp.translate("AboutDlg_base",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = AboutDlg_base()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
