# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/invalidpenconfigform_base.ui'
#
# Created: Thu Sep 2 11:14:58 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.11
#
# WARNING! All changes made in this file will be lost!


from qt import *


class InvalidPenConfigForm_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("InvalidPenConfigForm_base")


        InvalidPenConfigForm_baseLayout = QGridLayout(self,1,1,11,6,"InvalidPenConfigForm_baseLayout")

        self.pushButton49 = QPushButton(self,"pushButton49")

        InvalidPenConfigForm_baseLayout.addWidget(self.pushButton49,2,2)
        spacer43 = QSpacerItem(540,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        InvalidPenConfigForm_baseLayout.addMultiCell(spacer43,2,2,0,1)

        self.Icon = QLabel(self,"Icon")
        self.Icon.setSizePolicy(QSizePolicy(0,0,0,0,self.Icon.sizePolicy().hasHeightForWidth()))
        self.Icon.setFrameShape(QLabel.NoFrame)
        self.Icon.setScaledContents(1)

        InvalidPenConfigForm_baseLayout.addWidget(self.Icon,0,0)

        self.textLabel7 = QLabel(self,"textLabel7")
        self.textLabel7.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)

        InvalidPenConfigForm_baseLayout.addMultiCellWidget(self.textLabel7,0,0,1,2)

        self.languageChange()

        self.resize(QSize(610,161).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton49,SIGNAL("clicked()"),self,SLOT("accept()"))


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager - Cartridges Missing"))
        self.pushButton49.setText(self.__tr("OK"))
        self.textLabel7.setText(self.__tr("One or more cartiridges are missing from the printer. Please install cartridge(s) and try again.."))


    def __tr(self,s,c = None):
        return qApp.translate("InvalidPenConfigForm_base",s,c)
