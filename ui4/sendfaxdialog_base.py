# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui4/sendfaxdialog_base.ui'
#
# Created: Thu Apr  9 13:51:55 2009
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,600,500).size()).expandedTo(Dialog.minimumSizeHint()))

        self.gridlayout = QtGui.QGridLayout(Dialog)
        self.gridlayout.setObjectName("gridlayout")

        self.StackedWidget = QtGui.QStackedWidget(Dialog)
        self.StackedWidget.setFrameShape(QtGui.QFrame.NoFrame)
        self.StackedWidget.setObjectName("StackedWidget")

        self.SelectFax = QtGui.QWidget()
        self.SelectFax.setObjectName("SelectFax")

        self.gridlayout1 = QtGui.QGridLayout(self.SelectFax)
        self.gridlayout1.setObjectName("gridlayout1")

        self.label_8 = QtGui.QLabel(self.SelectFax)

        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.gridlayout1.addWidget(self.label_8,0,0,1,1)

        self.line_4 = QtGui.QFrame(self.SelectFax)
        self.line_4.setFrameShape(QtGui.QFrame.HLine)
        self.line_4.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_4.setObjectName("line_4")
        self.gridlayout1.addWidget(self.line_4,1,0,1,1)

        self.gridlayout2 = QtGui.QGridLayout()
        self.gridlayout2.setObjectName("gridlayout2")

        self.FaxComboBox = PrinterNameComboBox(self.SelectFax)
        self.FaxComboBox.setObjectName("FaxComboBox")
        self.gridlayout2.addWidget(self.FaxComboBox,0,0,1,3)

        spacerItem = QtGui.QSpacerItem(20,20,QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Minimum)
        self.gridlayout2.addItem(spacerItem,1,0,1,1)

        self.FaxOptionsButton = QtGui.QPushButton(self.SelectFax)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.FaxOptionsButton.sizePolicy().hasHeightForWidth())
        self.FaxOptionsButton.setSizePolicy(sizePolicy)
        self.FaxOptionsButton.setObjectName("FaxOptionsButton")
        self.gridlayout2.addWidget(self.FaxOptionsButton,1,1,1,1)

        self.FaxSetupButton = QtGui.QPushButton(self.SelectFax)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.FaxSetupButton.sizePolicy().hasHeightForWidth())
        self.FaxSetupButton.setSizePolicy(sizePolicy)
        self.FaxSetupButton.setObjectName("FaxSetupButton")
        self.gridlayout2.addWidget(self.FaxSetupButton,1,2,1,1)
        self.gridlayout1.addLayout(self.gridlayout2,2,0,1,1)

        spacerItem1 = QtGui.QSpacerItem(564,221,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout1.addItem(spacerItem1,3,0,1,1)

        self.label_12 = QtGui.QLabel(self.SelectFax)
        self.label_12.setWordWrap(True)
        self.label_12.setObjectName("label_12")
        self.gridlayout1.addWidget(self.label_12,4,0,1,1)
        self.StackedWidget.addWidget(self.SelectFax)

        self.CoverPage = QtGui.QWidget()
        self.CoverPage.setObjectName("CoverPage")

        self.gridlayout3 = QtGui.QGridLayout(self.CoverPage)
        self.gridlayout3.setObjectName("gridlayout3")

        self.label_3 = QtGui.QLabel(self.CoverPage)

        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.gridlayout3.addWidget(self.label_3,0,0,1,1)

        self.line_2 = QtGui.QFrame(self.CoverPage)
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridlayout3.addWidget(self.line_2,1,0,1,1)

        self.CoverPageGroupBox = QtGui.QGroupBox(self.CoverPage)
        self.CoverPageGroupBox.setEnabled(True)
        self.CoverPageGroupBox.setCheckable(True)
        self.CoverPageGroupBox.setChecked(False)
        self.CoverPageGroupBox.setObjectName("CoverPageGroupBox")

        self.gridlayout4 = QtGui.QGridLayout(self.CoverPageGroupBox)
        self.gridlayout4.setObjectName("gridlayout4")

        self.gridlayout5 = QtGui.QGridLayout()
        self.gridlayout5.setObjectName("gridlayout5")

        self.CoverPageName = QtGui.QLabel(self.CoverPageGroupBox)
        self.CoverPageName.setFrameShape(QtGui.QFrame.NoFrame)
        self.CoverPageName.setAlignment(QtCore.Qt.AlignCenter)
        self.CoverPageName.setObjectName("CoverPageName")
        self.gridlayout5.addWidget(self.CoverPageName,0,0,1,4)

        self.CoverPagePreview = QtGui.QLabel(self.CoverPageGroupBox)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.CoverPagePreview.sizePolicy().hasHeightForWidth())
        self.CoverPagePreview.setSizePolicy(sizePolicy)
        self.CoverPagePreview.setMinimumSize(QtCore.QSize(134,192))
        self.CoverPagePreview.setMaximumSize(QtCore.QSize(134,192))
        self.CoverPagePreview.setFrameShape(QtGui.QFrame.NoFrame)
        self.CoverPagePreview.setScaledContents(True)
        self.CoverPagePreview.setAlignment(QtCore.Qt.AlignCenter)
        self.CoverPagePreview.setObjectName("CoverPagePreview")
        self.gridlayout5.addWidget(self.CoverPagePreview,1,0,1,4)

        spacerItem2 = QtGui.QSpacerItem(16,20,QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Minimum)
        self.gridlayout5.addItem(spacerItem2,2,0,1,1)

        self.PrevCoverPageButton = QtGui.QPushButton(self.CoverPageGroupBox)
        self.PrevCoverPageButton.setObjectName("PrevCoverPageButton")
        self.gridlayout5.addWidget(self.PrevCoverPageButton,2,1,1,1)

        self.NextCoverPageButton = QtGui.QPushButton(self.CoverPageGroupBox)
        self.NextCoverPageButton.setObjectName("NextCoverPageButton")
        self.gridlayout5.addWidget(self.NextCoverPageButton,2,2,1,1)

        spacerItem3 = QtGui.QSpacerItem(31,20,QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Minimum)
        self.gridlayout5.addItem(spacerItem3,2,3,1,1)

        spacerItem4 = QtGui.QSpacerItem(20,21,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout5.addItem(spacerItem4,3,1,1,1)
        self.gridlayout4.addLayout(self.gridlayout5,0,0,2,1)

        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setObjectName("vboxlayout")

        self.label_16 = QtGui.QLabel(self.CoverPageGroupBox)
        self.label_16.setObjectName("label_16")
        self.vboxlayout.addWidget(self.label_16)

        self.RegardingEdit = QtGui.QLineEdit(self.CoverPageGroupBox)
        self.RegardingEdit.setObjectName("RegardingEdit")
        self.vboxlayout.addWidget(self.RegardingEdit)
        self.gridlayout4.addLayout(self.vboxlayout,0,1,1,1)

        self.gridlayout6 = QtGui.QGridLayout()
        self.gridlayout6.setObjectName("gridlayout6")

        self.label_17 = QtGui.QLabel(self.CoverPageGroupBox)
        self.label_17.setObjectName("label_17")
        self.gridlayout6.addWidget(self.label_17,0,0,1,1)

        self.MessageEdit = QtGui.QTextEdit(self.CoverPageGroupBox)
        self.MessageEdit.setObjectName("MessageEdit")
        self.gridlayout6.addWidget(self.MessageEdit,1,0,1,1)

        self.PreserveFormattingCheckBox = QtGui.QCheckBox(self.CoverPageGroupBox)
        self.PreserveFormattingCheckBox.setObjectName("PreserveFormattingCheckBox")
        self.gridlayout6.addWidget(self.PreserveFormattingCheckBox,2,0,1,1)
        self.gridlayout4.addLayout(self.gridlayout6,1,1,1,1)
        self.gridlayout3.addWidget(self.CoverPageGroupBox,2,0,1,1)

        self.label_13 = QtGui.QLabel(self.CoverPage)
        self.label_13.setWordWrap(True)
        self.label_13.setObjectName("label_13")
        self.gridlayout3.addWidget(self.label_13,3,0,1,1)
        self.StackedWidget.addWidget(self.CoverPage)

        self.SelectFiles = QtGui.QWidget()
        self.SelectFiles.setObjectName("SelectFiles")

        self.gridlayout7 = QtGui.QGridLayout(self.SelectFiles)
        self.gridlayout7.setObjectName("gridlayout7")

        self.label_2 = QtGui.QLabel(self.SelectFiles)

        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_2.setFont(font)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        self.gridlayout7.addWidget(self.label_2,0,0,1,1)

        self.line = QtGui.QFrame(self.SelectFiles)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridlayout7.addWidget(self.line,1,0,1,1)

        self.FilesTable = FileTable(self.SelectFiles)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.FilesTable.sizePolicy().hasHeightForWidth())
        self.FilesTable.setSizePolicy(sizePolicy)
        self.FilesTable.setObjectName("FilesTable")
        self.gridlayout7.addWidget(self.FilesTable,2,0,1,1)

        self.FilesPageNote = QtGui.QLabel(self.SelectFiles)
        self.FilesPageNote.setWordWrap(True)
        self.FilesPageNote.setObjectName("FilesPageNote")
        self.gridlayout7.addWidget(self.FilesPageNote,3,0,1,1)
        self.StackedWidget.addWidget(self.SelectFiles)

        self.SelectRecipients = QtGui.QWidget()
        self.SelectRecipients.setObjectName("SelectRecipients")

        self.gridlayout8 = QtGui.QGridLayout(self.SelectRecipients)
        self.gridlayout8.setObjectName("gridlayout8")

        self.label_4 = QtGui.QLabel(self.SelectRecipients)

        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.gridlayout8.addWidget(self.label_4,0,0,1,1)

        self.line_3 = QtGui.QFrame(self.SelectRecipients)
        self.line_3.setFrameShape(QtGui.QFrame.HLine)
        self.line_3.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.gridlayout8.addWidget(self.line_3,1,0,1,1)

        self.groupBox_4 = QtGui.QGroupBox(self.SelectRecipients)
        self.groupBox_4.setObjectName("groupBox_4")

        self.gridlayout9 = QtGui.QGridLayout(self.groupBox_4)
        self.gridlayout9.setObjectName("gridlayout9")

        self.RecipientsTable = QtGui.QTableWidget(self.groupBox_4)
        self.RecipientsTable.setObjectName("RecipientsTable")
        self.gridlayout9.addWidget(self.RecipientsTable,0,0,1,5)

        self.RemoveRecipientButton = QtGui.QPushButton(self.groupBox_4)
        self.RemoveRecipientButton.setEnabled(False)
        self.RemoveRecipientButton.setObjectName("RemoveRecipientButton")
        self.gridlayout9.addWidget(self.RemoveRecipientButton,1,0,1,1)

        self.MoveRecipientUpButton = QtGui.QPushButton(self.groupBox_4)
        self.MoveRecipientUpButton.setEnabled(False)
        self.MoveRecipientUpButton.setObjectName("MoveRecipientUpButton")
        self.gridlayout9.addWidget(self.MoveRecipientUpButton,1,1,1,1)

        self.MoveRecipientDownButton = QtGui.QPushButton(self.groupBox_4)
        self.MoveRecipientDownButton.setEnabled(False)
        self.MoveRecipientDownButton.setObjectName("MoveRecipientDownButton")
        self.gridlayout9.addWidget(self.MoveRecipientDownButton,1,2,1,1)

        spacerItem5 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.gridlayout9.addItem(spacerItem5,1,3,1,1)

        self.FABButton = QtGui.QPushButton(self.groupBox_4)
        self.FABButton.setObjectName("FABButton")
        self.gridlayout9.addWidget(self.FABButton,1,4,1,1)
        self.gridlayout8.addWidget(self.groupBox_4,2,0,1,1)

        self.groupBox = QtGui.QGroupBox(self.SelectRecipients)
        self.groupBox.setObjectName("groupBox")

        self.gridlayout10 = QtGui.QGridLayout(self.groupBox)
        self.gridlayout10.setObjectName("gridlayout10")

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")

        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.hboxlayout.addWidget(self.label)

        spacerItem6 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem6)

        self.AddIndividualComboBox = QtGui.QComboBox(self.groupBox)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.AddIndividualComboBox.sizePolicy().hasHeightForWidth())
        self.AddIndividualComboBox.setSizePolicy(sizePolicy)
        self.AddIndividualComboBox.setObjectName("AddIndividualComboBox")
        self.hboxlayout.addWidget(self.AddIndividualComboBox)

        self.AddIndividualButton = QtGui.QPushButton(self.groupBox)
        self.AddIndividualButton.setEnabled(False)
        self.AddIndividualButton.setObjectName("AddIndividualButton")
        self.hboxlayout.addWidget(self.AddIndividualButton)
        self.gridlayout10.addLayout(self.hboxlayout,0,0,1,1)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.label_5 = QtGui.QLabel(self.groupBox)
        self.label_5.setObjectName("label_5")
        self.hboxlayout1.addWidget(self.label_5)

        spacerItem7 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem7)

        self.AddGroupComboBox = QtGui.QComboBox(self.groupBox)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.AddGroupComboBox.sizePolicy().hasHeightForWidth())
        self.AddGroupComboBox.setSizePolicy(sizePolicy)
        self.AddGroupComboBox.setObjectName("AddGroupComboBox")
        self.hboxlayout1.addWidget(self.AddGroupComboBox)

        self.AddGroupButton = QtGui.QPushButton(self.groupBox)
        self.AddGroupButton.setEnabled(False)
        self.AddGroupButton.setObjectName("AddGroupButton")
        self.hboxlayout1.addWidget(self.AddGroupButton)
        self.gridlayout10.addLayout(self.hboxlayout1,1,0,1,1)
        self.gridlayout8.addWidget(self.groupBox,3,0,1,1)

        self.groupBox_3 = QtGui.QGroupBox(self.SelectRecipients)
        self.groupBox_3.setObjectName("groupBox_3")

        self.gridlayout11 = QtGui.QGridLayout(self.groupBox_3)
        self.gridlayout11.setObjectName("gridlayout11")

        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setObjectName("hboxlayout2")

        self.label_6 = QtGui.QLabel(self.groupBox_3)
        self.label_6.setObjectName("label_6")
        self.hboxlayout2.addWidget(self.label_6)

        self.QuickAddNameEdit = QtGui.QLineEdit(self.groupBox_3)
        self.QuickAddNameEdit.setObjectName("QuickAddNameEdit")
        self.hboxlayout2.addWidget(self.QuickAddNameEdit)

        self.label_7 = QtGui.QLabel(self.groupBox_3)
        self.label_7.setObjectName("label_7")
        self.hboxlayout2.addWidget(self.label_7)

        self.QuickAddFaxEdit = QtGui.QLineEdit(self.groupBox_3)
        self.QuickAddFaxEdit.setObjectName("QuickAddFaxEdit")
        self.hboxlayout2.addWidget(self.QuickAddFaxEdit)

        self.QuickAddButton = QtGui.QPushButton(self.groupBox_3)
        self.QuickAddButton.setEnabled(False)
        self.QuickAddButton.setObjectName("QuickAddButton")
        self.hboxlayout2.addWidget(self.QuickAddButton)
        self.gridlayout11.addLayout(self.hboxlayout2,0,0,1,1)
        self.gridlayout8.addWidget(self.groupBox_3,4,0,1,1)
        self.StackedWidget.addWidget(self.SelectRecipients)

        self.SendFax = QtGui.QWidget()
        self.SendFax.setObjectName("SendFax")

        self.gridlayout12 = QtGui.QGridLayout(self.SendFax)
        self.gridlayout12.setObjectName("gridlayout12")

        self.label_9 = QtGui.QLabel(self.SendFax)

        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.gridlayout12.addWidget(self.label_9,0,0,1,1)

        self.line_5 = QtGui.QFrame(self.SendFax)
        self.line_5.setFrameShape(QtGui.QFrame.HLine)
        self.line_5.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_5.setObjectName("line_5")
        self.gridlayout12.addWidget(self.line_5,1,0,1,1)

        self.label_10 = QtGui.QLabel(self.SendFax)
        self.label_10.setObjectName("label_10")
        self.gridlayout12.addWidget(self.label_10,2,0,1,1)

        self.StatusList = QtGui.QListWidget(self.SendFax)
        self.StatusList.setObjectName("StatusList")
        self.gridlayout12.addWidget(self.StatusList,3,0,1,1)

        self.label_15 = QtGui.QLabel(self.SendFax)
        self.label_15.setObjectName("label_15")
        self.gridlayout12.addWidget(self.label_15,4,0,1,1)
        self.StackedWidget.addWidget(self.SendFax)
        self.gridlayout.addWidget(self.StackedWidget,0,0,1,5)

        self.line_6 = QtGui.QFrame(Dialog)
        self.line_6.setFrameShape(QtGui.QFrame.HLine)
        self.line_6.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_6.setObjectName("line_6")
        self.gridlayout.addWidget(self.line_6,1,0,1,5)

        self.StepText = QtGui.QLabel(Dialog)
        self.StepText.setObjectName("StepText")
        self.gridlayout.addWidget(self.StepText,2,0,1,1)

        spacerItem8 = QtGui.QSpacerItem(231,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem8,2,1,1,1)

        self.BackButton = QtGui.QPushButton(Dialog)
        self.BackButton.setObjectName("BackButton")
        self.gridlayout.addWidget(self.BackButton,2,2,1,1)

        self.NextButton = QtGui.QPushButton(Dialog)
        self.NextButton.setObjectName("NextButton")
        self.gridlayout.addWidget(self.NextButton,2,3,1,1)

        self.CancelButton = QtGui.QPushButton(Dialog)
        self.CancelButton.setObjectName("CancelButton")
        self.gridlayout.addWidget(self.CancelButton,2,4,1,1)

        self.retranslateUi(Dialog)
        self.StackedWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "HP Device Manager - Send Fax", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("Dialog", "Select Fax", None, QtGui.QApplication.UnicodeUTF8))
        self.FaxOptionsButton.setText(QtGui.QApplication.translate("Dialog", "Fax Settings...", None, QtGui.QApplication.UnicodeUTF8))
        self.FaxSetupButton.setText(QtGui.QApplication.translate("Dialog", "Fax Device Setup...", None, QtGui.QApplication.UnicodeUTF8))
        self.label_12.setText(QtGui.QApplication.translate("Dialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Select the desired fax printer queue and click <span style=\" font-style:italic;\">Next</span> to continue. Note: Once you continue to the next step, you will not be able to change to a different fax queue.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Select and Edit Fax Coverpage (Optional)", None, QtGui.QApplication.UnicodeUTF8))
        self.CoverPageGroupBox.setTitle(QtGui.QApplication.translate("Dialog", "Include Coverpage", None, QtGui.QApplication.UnicodeUTF8))
        self.label_16.setText(QtGui.QApplication.translate("Dialog", "Regarding:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_17.setText(QtGui.QApplication.translate("Dialog", "Optional Message: (max. 2000 characters or 32 preformatted lines)", None, QtGui.QApplication.UnicodeUTF8))
        self.PreserveFormattingCheckBox.setText(QtGui.QApplication.translate("Dialog", "Preformatted (preserve formatting)", None, QtGui.QApplication.UnicodeUTF8))
        self.label_13.setText(QtGui.QApplication.translate("Dialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'DejaVu Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\'; font-size:9pt;\">Check<span style=\" font-style:italic;\"> Include Coverpage </span>to add a coverpage to this fax. To continue without a coverpage, click <span style=\" font-style:italic;\">Next &gt;</span>.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "Select Files to Send", None, QtGui.QApplication.UnicodeUTF8))
        self.FilesPageNote.setText(QtGui.QApplication.translate("Dialog", "Note: You may also add files to the fax by printing from any application to the \'%1\' fax printer.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Dialog", "Select Fax Recipients", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_4.setTitle(QtGui.QApplication.translate("Dialog", "Recipients", None, QtGui.QApplication.UnicodeUTF8))
        self.RecipientsTable.clear()
        self.RecipientsTable.setColumnCount(0)
        self.RecipientsTable.setRowCount(0)
        self.RemoveRecipientButton.setText(QtGui.QApplication.translate("Dialog", "Remove", None, QtGui.QApplication.UnicodeUTF8))
        self.MoveRecipientUpButton.setText(QtGui.QApplication.translate("Dialog", "Move Up", None, QtGui.QApplication.UnicodeUTF8))
        self.MoveRecipientDownButton.setText(QtGui.QApplication.translate("Dialog", "Move Down", None, QtGui.QApplication.UnicodeUTF8))
        self.FABButton.setText(QtGui.QApplication.translate("Dialog", "Fax Address Book...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Add Recipients or Groups from the Fax Address Book", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Add an individual:", None, QtGui.QApplication.UnicodeUTF8))
        self.AddIndividualButton.setText(QtGui.QApplication.translate("Dialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Dialog", "Add a group:", None, QtGui.QApplication.UnicodeUTF8))
        self.AddGroupButton.setText(QtGui.QApplication.translate("Dialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_3.setTitle(QtGui.QApplication.translate("Dialog", "Quick Add an Individual Recipient (recipient will automatically be added to fax address book)", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("Dialog", "Name:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("Dialog", "Fax Number:", None, QtGui.QApplication.UnicodeUTF8))
        self.QuickAddButton.setText(QtGui.QApplication.translate("Dialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("Dialog", "Send Fax", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("Dialog", "Status:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_15.setText(QtGui.QApplication.translate("Dialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Click <span style=\" font-style:italic;\">Send Fax</span> to start the fax transmission.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.StepText.setText(QtGui.QApplication.translate("Dialog", "Step %1 of %2", None, QtGui.QApplication.UnicodeUTF8))
        self.BackButton.setText(QtGui.QApplication.translate("Dialog", "< Back", None, QtGui.QApplication.UnicodeUTF8))
        self.NextButton.setText(QtGui.QApplication.translate("Dialog", "Next >", None, QtGui.QApplication.UnicodeUTF8))
        self.CancelButton.setText(QtGui.QApplication.translate("Dialog", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

from printernamecombobox import PrinterNameComboBox
from filetable import FileTable
