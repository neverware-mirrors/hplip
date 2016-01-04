# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/dwelch/linux-imaging-and-printing/src/ui/unloadprogressdlg.ui'
#
# Created: Wed Aug 25 10:55:59 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.11
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class UnloadProgressDlg(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("UnloadProgressDlg")


        UnloadProgressDlgLayout = QGridLayout(self,1,1,11,6,"UnloadProgressDlgLayout")

        self.line2 = QFrame(self,"line2")
        self.line2.setFrameShape(QFrame.HLine)
        self.line2.setFrameShadow(QFrame.Sunken)
        self.line2.setFrameShape(QFrame.HLine)

        UnloadProgressDlgLayout.addWidget(self.line2,1,0)

        self.ProgressBar = QProgressBar(self,"ProgressBar")

        UnloadProgressDlgLayout.addWidget(self.ProgressBar,2,0)
        spacer6 = QSpacerItem(20,16,QSizePolicy.Minimum,QSizePolicy.Expanding)
        UnloadProgressDlgLayout.addItem(spacer6,3,0)

        self.FilenameText = QLabel(self,"FilenameText")

        UnloadProgressDlgLayout.addWidget(self.FilenameText,0,0)

        self.languageChange()

        self.resize(QSize(425,98).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)


    def languageChange(self):
        self.setCaption(self.__tr("Unloading Files"))
        self.FilenameText.setText(self.__tr("<b>FILENAME</b>"))


    def __tr(self,s,c = None):
        return qApp.translate("UnloadProgressDlg",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = UnloadProgressDlg()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
