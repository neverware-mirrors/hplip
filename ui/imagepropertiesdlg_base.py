# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/dwelch/linux-imaging-and-printing/src/ui/imagepropertiesdlg_base.ui'
#
# Created: Tue Aug 24 15:14:17 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.11
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class ImagePropertiesDlg_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("ImagePropertiesDlg_base")


        ImagePropertiesDlg_baseLayout = QGridLayout(self,1,1,11,6,"ImagePropertiesDlg_baseLayout")

        self.line1 = QFrame(self,"line1")
        self.line1.setFrameShape(QFrame.HLine)
        self.line1.setFrameShadow(QFrame.Sunken)
        self.line1.setFrameShape(QFrame.HLine)

        ImagePropertiesDlg_baseLayout.addMultiCellWidget(self.line1,1,1,0,3)

        self.FilenameText = QLabel(self,"FilenameText")

        ImagePropertiesDlg_baseLayout.addMultiCellWidget(self.FilenameText,0,0,0,2)

        self.textLabel6 = QLabel(self,"textLabel6")

        ImagePropertiesDlg_baseLayout.addWidget(self.textLabel6,3,0)

        self.textLabel8 = QLabel(self,"textLabel8")

        ImagePropertiesDlg_baseLayout.addWidget(self.textLabel8,4,0)

        self.textLabel10 = QLabel(self,"textLabel10")

        ImagePropertiesDlg_baseLayout.addWidget(self.textLabel10,2,0)

        self.pushButton6 = QPushButton(self,"pushButton6")

        ImagePropertiesDlg_baseLayout.addWidget(self.pushButton6,6,3)
        spacer5 = QSpacerItem(31,130,QSizePolicy.Minimum,QSizePolicy.Expanding)
        ImagePropertiesDlg_baseLayout.addItem(spacer5,5,2)
        spacer3 = QSpacerItem(160,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        ImagePropertiesDlg_baseLayout.addItem(spacer3,6,2)

        self.ViewEXIFButton = QPushButton(self,"ViewEXIFButton")
        self.ViewEXIFButton.setEnabled(0)

        ImagePropertiesDlg_baseLayout.addMultiCellWidget(self.ViewEXIFButton,6,6,0,1)
        spacer4 = QSpacerItem(20,120,QSizePolicy.Minimum,QSizePolicy.Expanding)
        ImagePropertiesDlg_baseLayout.addItem(spacer4,5,0)

        self.LocationText = QLabel(self,"LocationText")

        ImagePropertiesDlg_baseLayout.addMultiCellWidget(self.LocationText,2,2,1,3)

        self.MimeTypeText = QLabel(self,"MimeTypeText")

        ImagePropertiesDlg_baseLayout.addMultiCellWidget(self.MimeTypeText,3,3,1,3)

        self.SizeText = QLabel(self,"SizeText")

        ImagePropertiesDlg_baseLayout.addMultiCellWidget(self.SizeText,4,4,1,3)

        self.languageChange()

        self.resize(QSize(375,312).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton6,SIGNAL("clicked()"),self,SLOT("close()"))
        self.connect(self.ViewEXIFButton,SIGNAL("clicked()"),self.ViewEXIFButton_clicked)


    def languageChange(self):
        self.setCaption(self.__tr("Properties for"))
        self.FilenameText.setText(self.__tr("FILENAME"))
        self.textLabel6.setText(self.__tr("MIME Type:"))
        self.textLabel8.setText(self.__tr("Size:"))
        self.textLabel10.setText(self.__tr("Location:"))
        self.pushButton6.setText(self.__tr("OK"))
        self.ViewEXIFButton.setText(self.__tr("View EXIF information..."))
        self.LocationText.setText(self.__tr("LOCATION"))
        self.MimeTypeText.setText(self.__tr("MIME TYPE"))
        self.SizeText.setText(self.__tr("SIZE"))


    def ViewEXIFButton_clicked(self):
        print "ImagePropertiesDlg_base.ViewEXIFButton_clicked(): Not implemented yet"

    def __tr(self,s,c = None):
        return qApp.translate("ImagePropertiesDlg_base",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = ImagePropertiesDlg_base()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
