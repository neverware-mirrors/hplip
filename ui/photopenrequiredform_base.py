# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/photopenrequiredform_base.ui'
#
# Created: Thu Sep 2 11:14:58 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.11
#
# WARNING! All changes made in this file will be lost!


from qt import *


class PhotoPenRequiredForm_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("PhotoPenRequiredForm_base")


        PhotoPenRequiredForm_baseLayout = QGridLayout(self,1,1,11,6,"PhotoPenRequiredForm_baseLayout")

        self.pushButton8 = QPushButton(self,"pushButton8")

        PhotoPenRequiredForm_baseLayout.addWidget(self.pushButton8,2,2)
        spacer5 = QSpacerItem(431,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        PhotoPenRequiredForm_baseLayout.addMultiCell(spacer5,2,2,0,1)
        spacer6 = QSpacerItem(20,16,QSizePolicy.Minimum,QSizePolicy.Expanding)
        PhotoPenRequiredForm_baseLayout.addItem(spacer6,1,1)

        self.Icon = QLabel(self,"Icon")
        self.Icon.setSizePolicy(QSizePolicy(0,0,0,0,self.Icon.sizePolicy().hasHeightForWidth()))
        self.Icon.setFrameShape(QLabel.NoFrame)
        self.Icon.setScaledContents(1)

        PhotoPenRequiredForm_baseLayout.addWidget(self.Icon,0,0)

        self.textLabel7 = QLabel(self,"textLabel7")
        self.textLabel7.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)

        PhotoPenRequiredForm_baseLayout.addMultiCellWidget(self.textLabel7,0,0,1,2)

        self.languageChange()

        self.resize(QSize(607,131).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton8,SIGNAL("clicked()"),self,SLOT("accept()"))


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager - Photo and Color Pen Required for Color Calibration"))
        self.pushButton8.setText(self.__tr("OK"))
        self.textLabel7.setText(self.__tr("Both the photo and color cartridges must be inserted into the printer to perform color calibration. If you are planning on printing with the photo cartridge, please insert it and try again.."))


    def __tr(self,s,c = None):
        return qApp.translate("PhotoPenRequiredForm_base",s,c)
