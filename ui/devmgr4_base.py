# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/dwelch/linux-imaging-and-printing/src/ui/devmgr4_base.ui'
#
# Created: Wed Dec 8 08:55:05 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.12
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class DevMgr4_base(QMainWindow):
    def __init__(self,parent = None,name = None,fl = 0):
        QMainWindow.__init__(self,parent,name,fl)
        self.statusBar()

        if not name:
            self.setName("DevMgr4_base")


        self.setCentralWidget(QWidget(self,"qt_central_widget"))
        DevMgr4_baseLayout = QGridLayout(self.centralWidget(),1,1,11,6,"DevMgr4_baseLayout")

        layout29 = QGridLayout(None,1,1,0,6,"layout29")

        self.DeviceList = QIconView(self.centralWidget(),"DeviceList")
        self.DeviceList.setSizePolicy(QSizePolicy(5,5,0,0,self.DeviceList.sizePolicy().hasHeightForWidth()))
        self.DeviceList.setMaximumSize(QSize(32767,32767))
        self.DeviceList.setResizePolicy(QIconView.Manual)
        self.DeviceList.setArrangement(QIconView.TopToBottom)
        self.DeviceList.setResizeMode(QIconView.Adjust)

        layout29.addMultiCellWidget(self.DeviceList,0,0,0,3)

        DevMgr4_baseLayout.addLayout(layout29,0,0)

        self.Tabs = QTabWidget(self.centralWidget(),"Tabs")

        self.TabPage = QWidget(self.Tabs,"TabPage")
        TabPageLayout = QGridLayout(self.TabPage,1,1,11,6,"TabPageLayout")

        self.ConfigureFeaturesButton = QPushButton(self.TabPage,"ConfigureFeaturesButton")

        TabPageLayout.addWidget(self.ConfigureFeaturesButton,3,1)
        spacer11_2 = QSpacerItem(321,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        TabPageLayout.addItem(spacer11_2,3,0)
        spacer10 = QSpacerItem(20,80,QSizePolicy.Minimum,QSizePolicy.Expanding)
        TabPageLayout.addItem(spacer10,2,1)

        layout2 = QVBoxLayout(None,0,6,"layout2")

        self.PrintButton = QPushButton(self.TabPage,"PrintButton")
        self.PrintButton.setEnabled(0)
        layout2.addWidget(self.PrintButton)

        self.ScanButton = QPushButton(self.TabPage,"ScanButton")
        self.ScanButton.setEnabled(0)
        layout2.addWidget(self.ScanButton)

        self.PCardButton = QPushButton(self.TabPage,"PCardButton")
        self.PCardButton.setEnabled(0)
        layout2.addWidget(self.PCardButton)

        self.SendFaxButton = QPushButton(self.TabPage,"SendFaxButton")
        self.SendFaxButton.setEnabled(0)
        layout2.addWidget(self.SendFaxButton)

        self.MakeCopiesButton = QPushButton(self.TabPage,"MakeCopiesButton")
        self.MakeCopiesButton.setEnabled(0)
        layout2.addWidget(self.MakeCopiesButton)

        TabPageLayout.addMultiCellLayout(layout2,1,1,0,1)
        spacer12_2 = QSpacerItem(20,111,QSizePolicy.Minimum,QSizePolicy.Expanding)
        TabPageLayout.addItem(spacer12_2,0,0)
        self.Tabs.insertTab(self.TabPage,QString(""))

        self.StatusTab = QWidget(self.Tabs,"StatusTab")
        StatusTabLayout = QGridLayout(self.StatusTab,1,1,11,6,"StatusTabLayout")

        self.groupBox3 = QGroupBox(self.StatusTab,"groupBox3")
        self.groupBox3.setColumnLayout(0,Qt.Vertical)
        self.groupBox3.layout().setSpacing(6)
        self.groupBox3.layout().setMargin(11)
        groupBox3Layout = QGridLayout(self.groupBox3.layout())
        groupBox3Layout.setAlignment(Qt.AlignTop)

        self.StatusHistoryList = QListView(self.groupBox3,"StatusHistoryList")
        self.StatusHistoryList.addColumn(self.__tr("Date"))
        self.StatusHistoryList.addColumn(self.__tr("Time"))
        self.StatusHistoryList.addColumn(self.__tr("User"))
        self.StatusHistoryList.addColumn(self.__tr("Job ID"))
        self.StatusHistoryList.addColumn(self.__tr("Code"))
        self.StatusHistoryList.addColumn(self.__tr("Description"))
        self.StatusHistoryList.setEnabled(1)
        self.StatusHistoryList.setSelectionMode(QListView.Single)
        self.StatusHistoryList.setAllColumnsShowFocus(1)

        groupBox3Layout.addWidget(self.StatusHistoryList,0,0)

        StatusTabLayout.addWidget(self.groupBox3,1,0)

        self.StatusGroupBox = QGroupBox(self.StatusTab,"StatusGroupBox")
        self.StatusGroupBox.setColumnLayout(0,Qt.Vertical)
        self.StatusGroupBox.layout().setSpacing(6)
        self.StatusGroupBox.layout().setMargin(11)
        StatusGroupBoxLayout = QGridLayout(self.StatusGroupBox.layout())
        StatusGroupBoxLayout.setAlignment(Qt.AlignTop)

        self.StatusIcon = QLabel(self.StatusGroupBox,"StatusIcon")
        self.StatusIcon.setSizePolicy(QSizePolicy(0,0,0,0,self.StatusIcon.sizePolicy().hasHeightForWidth()))
        self.StatusIcon.setMinimumSize(QSize(32,32))
        self.StatusIcon.setMaximumSize(QSize(32,32))
        self.StatusIcon.setFrameShape(QLabel.NoFrame)
        self.StatusIcon.setScaledContents(1)

        StatusGroupBoxLayout.addMultiCellWidget(self.StatusIcon,0,1,4,4)

        self.textLabel7 = QLabel(self.StatusGroupBox,"textLabel7")

        StatusGroupBoxLayout.addWidget(self.textLabel7,4,0)

        self.textLabel5 = QLabel(self.StatusGroupBox,"textLabel5")

        StatusGroupBoxLayout.addWidget(self.textLabel5,3,0)

        self.textLabel1 = QLabel(self.StatusGroupBox,"textLabel1")

        StatusGroupBoxLayout.addWidget(self.textLabel1,1,0)

        self.StatusDate = QLabel(self.StatusGroupBox,"StatusDate")

        StatusGroupBoxLayout.addMultiCellWidget(self.StatusDate,1,1,1,2)

        self.StatusTime = QLabel(self.StatusGroupBox,"StatusTime")

        StatusGroupBoxLayout.addMultiCellWidget(self.StatusTime,2,2,1,2)

        self.textLabel18 = QLabel(self.StatusGroupBox,"textLabel18")

        StatusGroupBoxLayout.addWidget(self.textLabel18,2,0)

        self.CancelJobButton = QPushButton(self.StatusGroupBox,"CancelJobButton")
        self.CancelJobButton.setEnabled(0)

        StatusGroupBoxLayout.addMultiCellWidget(self.CancelJobButton,4,4,3,4)
        spacer37 = QSpacerItem(81,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        StatusGroupBoxLayout.addItem(spacer37,4,2)

        self.StatusJobID = QLabel(self.StatusGroupBox,"StatusJobID")
        self.StatusJobID.setAlignment(QLabel.AlignVCenter | QLabel.AlignLeft)

        StatusGroupBoxLayout.addWidget(self.StatusJobID,4,1)

        self.StatusCode = QLabel(self.StatusGroupBox,"StatusCode")
        self.StatusCode.setTextFormat(QLabel.AutoText)
        self.StatusCode.setAlignment(QLabel.AlignVCenter | QLabel.AlignLeft)

        StatusGroupBoxLayout.addMultiCellWidget(self.StatusCode,3,3,1,2)
        spacer35 = QSpacerItem(240,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        StatusGroupBoxLayout.addMultiCell(spacer35,0,0,1,3)

        self.StatusText = QLabel(self.StatusGroupBox,"StatusText")
        StatusText_font = QFont(self.StatusText.font())
        StatusText_font.setBold(1)
        self.StatusText.setFont(StatusText_font)

        StatusGroupBoxLayout.addWidget(self.StatusText,0,0)

        StatusTabLayout.addWidget(self.StatusGroupBox,0,0)
        self.Tabs.insertTab(self.StatusTab,QString(""))

        self.SuppliesTab = QWidget(self.Tabs,"SuppliesTab")
        SuppliesTabLayout = QGridLayout(self.SuppliesTab,1,1,11,6,"SuppliesTabLayout")

        self.SuppliesList = QListView(self.SuppliesTab,"SuppliesList")
        self.SuppliesList.addColumn(self.__tr("Type"))
        self.SuppliesList.addColumn(self.__tr("Part Number"))
        self.SuppliesList.addColumn(self.__tr("Approx. Level"))
        self.SuppliesList.setEnabled(1)

        SuppliesTabLayout.addWidget(self.SuppliesList,1,0)

        self.textLabel1_2 = QLabel(self.SuppliesTab,"textLabel1_2")

        SuppliesTabLayout.addWidget(self.textLabel1_2,0,0)
        self.Tabs.insertTab(self.SuppliesTab,QString(""))

        self.MaintTab = QWidget(self.Tabs,"MaintTab")
        MaintTabLayout = QGridLayout(self.MaintTab,1,1,11,6,"MaintTabLayout")

        self.groupBox6 = QGroupBox(self.MaintTab,"groupBox6")
        self.groupBox6.setColumnLayout(0,Qt.Vertical)
        self.groupBox6.layout().setSpacing(6)
        self.groupBox6.layout().setMargin(11)
        groupBox6Layout = QGridLayout(self.groupBox6.layout())
        groupBox6Layout.setAlignment(Qt.AlignTop)

        self.textLabel11 = QLabel(self.groupBox6,"textLabel11")

        groupBox6Layout.addMultiCellWidget(self.textLabel11,0,0,0,1)

        self.PrintTestPageButton = QPushButton(self.groupBox6,"PrintTestPageButton")
        self.PrintTestPageButton.setEnabled(0)

        groupBox6Layout.addWidget(self.PrintTestPageButton,2,1)
        spacer14 = QSpacerItem(391,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        groupBox6Layout.addItem(spacer14,2,0)

        MaintTabLayout.addWidget(self.groupBox6,3,0)

        self.groupBox4 = QGroupBox(self.MaintTab,"groupBox4")
        self.groupBox4.setColumnLayout(0,Qt.Vertical)
        self.groupBox4.layout().setSpacing(6)
        self.groupBox4.layout().setMargin(11)
        groupBox4Layout = QGridLayout(self.groupBox4.layout())
        groupBox4Layout.setAlignment(Qt.AlignTop)

        self.CleanPensButton = QPushButton(self.groupBox4,"CleanPensButton")
        self.CleanPensButton.setEnabled(0)

        groupBox4Layout.addWidget(self.CleanPensButton,2,1)

        self.textLabel9 = QLabel(self.groupBox4,"textLabel9")
        self.textLabel9.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)

        groupBox4Layout.addMultiCellWidget(self.textLabel9,0,0,0,1)
        spacer12 = QSpacerItem(391,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        groupBox4Layout.addItem(spacer12,2,0)

        MaintTabLayout.addWidget(self.groupBox4,0,0)

        self.groupBox5 = QGroupBox(self.MaintTab,"groupBox5")
        self.groupBox5.setColumnLayout(0,Qt.Vertical)
        self.groupBox5.layout().setSpacing(6)
        self.groupBox5.layout().setMargin(11)
        groupBox5Layout = QGridLayout(self.groupBox5.layout())
        groupBox5Layout.setAlignment(Qt.AlignTop)

        self.AlignPensButton = QPushButton(self.groupBox5,"AlignPensButton")
        self.AlignPensButton.setEnabled(0)

        groupBox5Layout.addWidget(self.AlignPensButton,2,1)

        self.textLabel10 = QLabel(self.groupBox5,"textLabel10")
        self.textLabel10.setTextFormat(QLabel.AutoText)
        self.textLabel10.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)

        groupBox5Layout.addMultiCellWidget(self.textLabel10,0,0,0,1)
        spacer13 = QSpacerItem(401,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        groupBox5Layout.addItem(spacer13,2,0)

        MaintTabLayout.addWidget(self.groupBox5,1,0)

        self.groupBox7 = QGroupBox(self.MaintTab,"groupBox7")
        self.groupBox7.setColumnLayout(0,Qt.Vertical)
        self.groupBox7.layout().setSpacing(6)
        self.groupBox7.layout().setMargin(11)
        groupBox7Layout = QGridLayout(self.groupBox7.layout())
        groupBox7Layout.setAlignment(Qt.AlignTop)

        self.ColorCalibrationButton = QPushButton(self.groupBox7,"ColorCalibrationButton")
        self.ColorCalibrationButton.setEnabled(0)

        groupBox7Layout.addMultiCellWidget(self.ColorCalibrationButton,1,2,1,1)

        self.textLabel1_3 = QLabel(self.groupBox7,"textLabel1_3")
        self.textLabel1_3.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)

        groupBox7Layout.addMultiCellWidget(self.textLabel1_3,0,0,0,1)
        spacer11 = QSpacerItem(361,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        groupBox7Layout.addItem(spacer11,2,0)

        MaintTabLayout.addWidget(self.groupBox7,2,0)
        spacer13_2 = QSpacerItem(20,31,QSizePolicy.Minimum,QSizePolicy.Expanding)
        MaintTabLayout.addItem(spacer13_2,4,0)
        self.Tabs.insertTab(self.MaintTab,QString(""))

        self.InfoTab = QWidget(self.Tabs,"InfoTab")
        InfoTabLayout = QGridLayout(self.InfoTab,1,1,11,6,"InfoTabLayout")

        self.groupBox12 = QGroupBox(self.InfoTab,"groupBox12")
        self.groupBox12.setColumnLayout(0,Qt.Vertical)
        self.groupBox12.layout().setSpacing(6)
        self.groupBox12.layout().setMargin(11)
        groupBox12Layout = QGridLayout(self.groupBox12.layout())
        groupBox12Layout.setAlignment(Qt.AlignTop)

        self.DeviceURI = QLabel(self.groupBox12,"DeviceURI")

        groupBox12Layout.addMultiCellWidget(self.DeviceURI,0,0,1,3)

        self.Model = QLabel(self.groupBox12,"Model")

        groupBox12Layout.addMultiCellWidget(self.Model,1,1,1,3)

        self.SerialNo = QLabel(self.groupBox12,"SerialNo")

        groupBox12Layout.addMultiCellWidget(self.SerialNo,2,2,1,3)

        self.CUPSPrinters = QLabel(self.groupBox12,"CUPSPrinters")

        groupBox12Layout.addMultiCellWidget(self.CUPSPrinters,3,3,1,3)
        spacer39 = QSpacerItem(20,230,QSizePolicy.Minimum,QSizePolicy.Expanding)
        groupBox12Layout.addItem(spacer39,4,2)

        self.textLabel12 = QLabel(self.groupBox12,"textLabel12")

        groupBox12Layout.addWidget(self.textLabel12,0,0)

        self.textLabel14 = QLabel(self.groupBox12,"textLabel14")

        groupBox12Layout.addWidget(self.textLabel14,1,0)

        self.textLabel16 = QLabel(self.groupBox12,"textLabel16")

        groupBox12Layout.addWidget(self.textLabel16,2,0)

        self.textLabel16_2 = QLabel(self.groupBox12,"textLabel16_2")

        groupBox12Layout.addWidget(self.textLabel16_2,3,0)

        self.AdvancedInfoButton = QPushButton(self.groupBox12,"AdvancedInfoButton")
        self.AdvancedInfoButton.setEnabled(0)

        groupBox12Layout.addWidget(self.AdvancedInfoButton,5,3)
        spacer38 = QSpacerItem(420,21,QSizePolicy.Expanding,QSizePolicy.Minimum)
        groupBox12Layout.addMultiCell(spacer38,5,5,0,1)

        InfoTabLayout.addWidget(self.groupBox12,0,0)
        self.Tabs.insertTab(self.InfoTab,QString(""))

        DevMgr4_baseLayout.addWidget(self.Tabs,0,1)

        self.helpContentsAction = QAction(self,"helpContentsAction")
        self.helpContentsAction.setEnabled(0)
        self.helpIndexAction = QAction(self,"helpIndexAction")
        self.helpIndexAction.setEnabled(0)
        self.helpAboutAction = QAction(self,"helpAboutAction")
        self.deviceRescanAction = QAction(self,"deviceRescanAction")
        self.deviceExitAction = QAction(self,"deviceExitAction")
        self.settingsPopupAlertsAction = QAction(self,"settingsPopupAlertsAction")
        self.settingsEmailAlertsAction = QAction(self,"settingsEmailAlertsAction")
        self.settingsConfigure = QAction(self,"settingsConfigure")
        self.deviceRefreshAll = QAction(self,"deviceRefreshAll")




        self.MenuBar = QMenuBar(self,"MenuBar")


        self.Device = QPopupMenu(self)
        self.deviceRescanAction.addTo(self.Device)
        self.deviceRefreshAll.addTo(self.Device)
        self.Device.insertSeparator()
        self.deviceExitAction.addTo(self.Device)
        self.MenuBar.insertItem(QString(""),self.Device,1)

        self.Settings = QPopupMenu(self)
        self.settingsConfigure.addTo(self.Settings)
        self.MenuBar.insertItem(QString(""),self.Settings,2)

        self.helpMenu = QPopupMenu(self)
        self.helpContentsAction.addTo(self.helpMenu)
        self.helpIndexAction.addTo(self.helpMenu)
        self.helpMenu.insertSeparator()
        self.helpAboutAction.addTo(self.helpMenu)
        self.MenuBar.insertItem(QString(""),self.helpMenu,3)


        self.languageChange()

        self.resize(QSize(770,588).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.helpIndexAction,SIGNAL("activated()"),self.helpIndex)
        self.connect(self.helpContentsAction,SIGNAL("activated()"),self.helpContents)
        self.connect(self.helpAboutAction,SIGNAL("activated()"),self.helpAbout)
        self.connect(self.deviceExitAction,SIGNAL("activated()"),self,SLOT("close()"))
        self.connect(self.deviceRescanAction,SIGNAL("activated()"),self.deviceRescanAction_activated)
        self.connect(self.settingsEmailAlertsAction,SIGNAL("activated()"),self.settingsEmailAlertsAction_activated)
        self.connect(self.settingsConfigure,SIGNAL("activated()"),self.settingsConfigure_activated)
        self.connect(self.AdvancedInfoButton,SIGNAL("clicked()"),self.AdvancedInfoButton_clicked)
        self.connect(self.ColorCalibrationButton,SIGNAL("clicked()"),self.ColorCalibrationButton_clicked)
        self.connect(self.AlignPensButton,SIGNAL("clicked()"),self.AlignPensButton_clicked)
        self.connect(self.CleanPensButton,SIGNAL("clicked()"),self.CleanPensButton_clicked)
        self.connect(self.PrintTestPageButton,SIGNAL("clicked()"),self.PrintTestPageButton_clicked)
        self.connect(self.DeviceList,SIGNAL("currentChanged(QIconViewItem*)"),self.DeviceList_currentChanged)
        self.connect(self.PrintButton,SIGNAL("clicked()"),self.PrintButton_clicked)
        self.connect(self.ScanButton,SIGNAL("clicked()"),self.ScanButton_clicked)
        self.connect(self.PCardButton,SIGNAL("clicked()"),self.PCardButton_clicked)
        self.connect(self.SendFaxButton,SIGNAL("clicked()"),self.SendFaxButton_clicked)
        self.connect(self.MakeCopiesButton,SIGNAL("clicked()"),self.MakeCopiesButton_clicked)
        self.connect(self.ConfigureFeaturesButton,SIGNAL("clicked()"),self.ConfigureFeaturesButton_clicked)
        self.connect(self.CancelJobButton,SIGNAL("clicked()"),self.CancelJobButton_clicked)
        self.connect(self.deviceRefreshAll,SIGNAL("activated()"),self.deviceRefreshAll_activated)
        self.connect(self.DeviceList,SIGNAL("clicked(QIconViewItem*)"),self.DeviceList_clicked)


    def languageChange(self):
        self.setCaption(self.__tr("HP Device Manager"))
        self.ConfigureFeaturesButton.setText(self.__tr("Configure..."))
        self.PrintButton.setText(self.__tr("Print..."))
        self.ScanButton.setText(self.__tr("Scan..."))
        self.PCardButton.setText(self.__tr("Access Photo Cards..."))
        self.SendFaxButton.setText(self.__tr("Send Fax..."))
        self.MakeCopiesButton.setText(self.__tr("Make Copies..."))
        self.Tabs.changeTab(self.TabPage,self.__tr("Functions"))
        self.groupBox3.setTitle(self.__tr("History"))
        self.StatusHistoryList.header().setLabel(0,self.__tr("Date"))
        self.StatusHistoryList.header().setLabel(1,self.__tr("Time"))
        self.StatusHistoryList.header().setLabel(2,self.__tr("User"))
        self.StatusHistoryList.header().setLabel(3,self.__tr("Job ID"))
        self.StatusHistoryList.header().setLabel(4,self.__tr("Code"))
        self.StatusHistoryList.header().setLabel(5,self.__tr("Description"))
        self.StatusGroupBox.setTitle(self.__tr("Last"))
        self.textLabel7.setText(self.__tr("Job ID:"))
        self.textLabel5.setText(self.__tr("Code:"))
        self.textLabel1.setText(self.__tr("Date:"))
        self.StatusDate.setText(QString.null)
        self.StatusTime.setText(QString.null)
        self.textLabel18.setText(self.__tr("Time:"))
        self.CancelJobButton.setText(self.__tr("Cancel Print Job"))
        self.StatusJobID.setText(QString.null)
        self.StatusCode.setText(QString.null)
        self.StatusText.setText(QString.null)
        self.Tabs.changeTab(self.StatusTab,self.__tr("Status"))
        self.SuppliesList.header().setLabel(0,self.__tr("Type"))
        self.SuppliesList.header().setLabel(1,self.__tr("Part Number"))
        self.SuppliesList.header().setLabel(2,self.__tr("Approx. Level"))
        self.textLabel1_2.setText(self.__tr("Ink Cartridges and Toner Cartridges Supply Levels"))
        self.Tabs.changeTab(self.SuppliesTab,self.__tr("Supplies"))
        self.groupBox6.setTitle(self.__tr("Test Page"))
        self.textLabel11.setText(self.__tr("Print a test page to test the setup of your printer."))
        self.PrintTestPageButton.setText(self.__tr("Print Test Page"))
        self.groupBox4.setTitle(self.__tr("Cartridge Cleaning"))
        self.CleanPensButton.setText(self.__tr("Clean Cartridges..."))
        self.textLabel9.setText(self.__tr("You only need to perform this action if you are having problems with poor printout quality due to clogged ink nozzles."))
        self.groupBox5.setTitle(self.__tr("Cartridge Alignment"))
        self.AlignPensButton.setText(self.__tr("Align Cartridges..."))
        self.textLabel10.setText(self.__tr("This will improve the quality of output when a new cartridge is installed. Some printers will automatically align cartridges when new cartridges are installed, so you may not need to perform this action."))
        self.groupBox7.setTitle(self.__tr("Color Calibration"))
        self.ColorCalibrationButton.setText(self.__tr("Color Calibration..."))
        self.textLabel1_3.setText(self.__tr("Some printers require this procedure to optimimize the color output when both a three color and photo cartridge are inserted."))
        self.Tabs.changeTab(self.MaintTab,self.__tr("Maintenance"))
        self.groupBox12.setTitle(self.__tr("Device Information"))
        self.DeviceURI.setText(QString.null)
        self.Model.setText(QString.null)
        self.SerialNo.setText(QString.null)
        self.CUPSPrinters.setText(QString.null)
        self.textLabel12.setText(self.__tr("<b>Device URI:</b>"))
        self.textLabel14.setText(self.__tr("<b>Model:</b>"))
        self.textLabel16.setText(self.__tr("<b>Serial No.:</b>"))
        self.textLabel16_2.setText(self.__tr("<b>CUPS Printer(s):</b>"))
        self.AdvancedInfoButton.setText(self.__tr("Advanced..."))
        self.Tabs.changeTab(self.InfoTab,self.__tr("Information"))
        self.helpContentsAction.setText(self.__tr("Contents"))
        self.helpContentsAction.setMenuText(self.__tr("&Contents..."))
        self.helpContentsAction.setAccel(QString.null)
        self.helpIndexAction.setText(self.__tr("Index"))
        self.helpIndexAction.setMenuText(self.__tr("&Index..."))
        self.helpIndexAction.setAccel(QString.null)
        self.helpAboutAction.setText(self.__tr("About"))
        self.helpAboutAction.setMenuText(self.__tr("&About"))
        self.helpAboutAction.setAccel(QString.null)
        self.deviceRescanAction.setText(self.__tr("Refresh Device"))
        self.deviceRescanAction.setMenuText(self.__tr("Refresh Device"))
        self.deviceRescanAction.setToolTip(self.__tr("Refresh Device (F5)"))
        self.deviceRescanAction.setAccel(self.__tr("F5"))
        self.deviceExitAction.setText(self.__tr("Exit"))
        self.deviceExitAction.setMenuText(self.__tr("Exit"))
        self.deviceExitAction.setToolTip(self.__tr("Exit HP Device Manager"))
        self.deviceExitAction.setAccel(self.__tr("Ctrl+Q"))
        self.settingsPopupAlertsAction.setText(self.__tr("Popup Alerts..."))
        self.settingsPopupAlertsAction.setMenuText(self.__tr("Popup alerts..."))
        self.settingsPopupAlertsAction.setToolTip(self.__tr("Configure popup alerts"))
        self.settingsEmailAlertsAction.setText(self.__tr("Email alerts..."))
        self.settingsEmailAlertsAction.setMenuText(self.__tr("Email alerts..."))
        self.settingsEmailAlertsAction.setToolTip(self.__tr("Configure email alerts"))
        self.settingsConfigure.setText(self.__tr("Configure HP Device Manager..."))
        self.deviceRefreshAll.setText(self.__tr("Refresh All"))
        self.deviceRefreshAll.setAccel(self.__tr("F6"))
        if self.MenuBar.findItem(1):
            self.MenuBar.findItem(1).setText(self.__tr("Device"))
        if self.MenuBar.findItem(2):
            self.MenuBar.findItem(2).setText(self.__tr("Settings"))
        if self.MenuBar.findItem(3):
            self.MenuBar.findItem(3).setText(self.__tr("&Help"))


    def fileNew(self):
        print "DevMgr4_base.fileNew(): Not implemented yet"

    def fileOpen(self):
        print "DevMgr4_base.fileOpen(): Not implemented yet"

    def fileSave(self):
        print "DevMgr4_base.fileSave(): Not implemented yet"

    def fileSaveAs(self):
        print "DevMgr4_base.fileSaveAs(): Not implemented yet"

    def filePrint(self):
        print "DevMgr4_base.filePrint(): Not implemented yet"

    def fileExit(self):
        print "DevMgr4_base.fileExit(): Not implemented yet"

    def editUndo(self):
        print "DevMgr4_base.editUndo(): Not implemented yet"

    def editRedo(self):
        print "DevMgr4_base.editRedo(): Not implemented yet"

    def editCut(self):
        print "DevMgr4_base.editCut(): Not implemented yet"

    def editCopy(self):
        print "DevMgr4_base.editCopy(): Not implemented yet"

    def editPaste(self):
        print "DevMgr4_base.editPaste(): Not implemented yet"

    def editFind(self):
        print "DevMgr4_base.editFind(): Not implemented yet"

    def helpIndex(self):
        print "DevMgr4_base.helpIndex(): Not implemented yet"

    def helpContents(self):
        print "DevMgr4_base.helpContents(): Not implemented yet"

    def helpAbout(self):
        print "DevMgr4_base.helpAbout(): Not implemented yet"

    def deviceRescanAction_activated(self):
        print "DevMgr4_base.deviceRescanAction_activated(): Not implemented yet"

    def settingsEmailAlertsAction_activated(self):
        print "DevMgr4_base.settingsEmailAlertsAction_activated(): Not implemented yet"

    def DeviceList_currentChanged(self,a0):
        print "DevMgr4_base.DeviceList_currentChanged(QIconViewItem*): Not implemented yet"

    def CleanPensButton_clicked(self):
        print "DevMgr4_base.CleanPensButton_clicked(): Not implemented yet"

    def AlignPensButton_clicked(self):
        print "DevMgr4_base.AlignPensButton_clicked(): Not implemented yet"

    def PrintTestPageButton_clicked(self):
        print "DevMgr4_base.PrintTestPageButton_clicked(): Not implemented yet"

    def AdvancedInfoButton_clicked(self):
        print "DevMgr4_base.AdvancedInfoButton_clicked(): Not implemented yet"

    def ColorCalibrationButton_clicked(self):
        print "DevMgr4_base.ColorCalibrationButton_clicked(): Not implemented yet"

    def settingsConfigure_activated(self):
        print "DevMgr4_base.settingsConfigure_activated(): Not implemented yet"

    def PrintButton_clicked(self):
        print "DevMgr4_base.PrintButton_clicked(): Not implemented yet"

    def ScanButton_clicked(self):
        print "DevMgr4_base.ScanButton_clicked(): Not implemented yet"

    def PCardButton_clicked(self):
        print "DevMgr4_base.PCardButton_clicked(): Not implemented yet"

    def SendFaxButton_clicked(self):
        print "DevMgr4_base.SendFaxButton_clicked(): Not implemented yet"

    def MakeCopiesButton_clicked(self):
        print "DevMgr4_base.MakeCopiesButton_clicked(): Not implemented yet"

    def ConfigureFeaturesButton_clicked(self):
        print "DevMgr4_base.ConfigureFeaturesButton_clicked(): Not implemented yet"

    def CancelJobButton_clicked(self):
        print "DevMgr4_base.CancelJobButton_clicked(): Not implemented yet"

    def deviceRefreshAll_activated(self):
        print "DevMgr4_base.deviceRefreshAll_activated(): Not implemented yet"

    def DeviceList_clicked(self,a0):
        print "DevMgr4_base.DeviceList_clicked(QIconViewItem*): Not implemented yet"

    def __tr(self,s,c = None):
        return qApp.translate("DevMgr4_base",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = DevMgr4_base()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
