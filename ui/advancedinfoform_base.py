# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/advancedinfoform_base.ui'
#
# Created: Thu Sep 2 11:14:58 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.11
#
# WARNING! All changes made in this file will be lost!


from qt import *


class AdvancedInfoForm_base(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("AdvancedInfoForm_base")


        AdvancedInfoForm_baseLayout = QGridLayout(self,1,1,11,6,"AdvancedInfoForm_baseLayout")

        self.pushButton7 = QPushButton(self,"pushButton7")

        AdvancedInfoForm_baseLayout.addWidget(self.pushButton7,1,1)
        spacer14 = QSpacerItem(411,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        AdvancedInfoForm_baseLayout.addItem(spacer14,1,0)

        self.AdvInfoText = QTextEdit(self,"AdvInfoText")
        self.AdvInfoText.setWordWrap(QTextEdit.WidgetWidth)
        self.AdvInfoText.setReadOnly(1)

        AdvancedInfoForm_baseLayout.addMultiCellWidget(self.AdvInfoText,0,0,0,1)

        self.languageChange()

        self.resize(QSize(600,480).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton7,SIGNAL("clicked()"),self,SLOT("close()"))


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager - Advanced Information"))
        self.pushButton7.setText(self.__tr("OK"))


    def __tr(self,s,c = None):
        return qApp.translate("AdvancedInfoForm_base",s,c)
