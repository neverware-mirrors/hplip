# -*- coding: utf-8 -*-

from qt import *
from printerform_base import PrinterForm_base
from base.g import *
from base.codes import *
from base import utils, device, magic
from prnt import cups
import glob


class RangeValidator( QValidator ):
    def __init__( self, parent=None, name=None):
        QValidator.__init__( self, parent, name )

    def validate( self, input, pos ):
        for x in str(input)[pos-1:]:
            if x not in '0123456789,-':
                return QValidator.Invalid, pos

        return QValidator.Acceptable, pos


class PrinterForm(PrinterForm_base):

    def __init__(self, device_uri, printer_name, args, parent = None,name = None,modal = 0,fl = 0):
        PrinterForm_base.__init__(self,parent,name,modal,fl)
        self.device_uri = device_uri
        self.printer_name = printer_name
        self.file_list = []
        self.auto_duplex_button_group = 0
        self.orientation_button_group = 0
        self.pages_button_group = 0

        self.pageRangeEdit.setValidator( RangeValidator( self.pageRangeEdit ) )

        self.MIME_TYPES_DESC = \
        {   
            "application/pdf" : self.__tr( "PDF Document" ),
            "application/postscript" : self.__tr( "Postscript Document" ),
            "application/vnd.hp-HPGL" : self.__tr( "HP Graphics Language File" ), 
            "application/x-cshell" : self.__tr( "C Shell Script" ),
            "application/x-perl" : self.__tr( "Perl Script" ),
            "application/x-python" : self.__tr( "Python Program" ),
            "application/x-shell" : self.__tr( "Shell Script" ),
            "text/plain" : self.__tr( "Plain Text" ),
            "text/html" : self.__tr( "HTML Dcoument" ),
            "image/gif" : self.__tr( "GIF Image" ),
            "image/png" : self.__tr(  "PNG Image" ),
            "image/jpeg" : self.__tr( "JPEG Image" ),
            "image/tiff" : self.__tr( "TIFF Image" ),
            "image/x-bitmap" : self.__tr( "Bitmap (BMP) Image" ),
            "image/x-photocd" : self.__tr( "Photo CD Image" ),
            "image/x-portable-anymap" : self.__tr( "Portable Image (PNM)" ),
            "image/x-portable-bitmap" : self.__tr( "Portable B&W Image (PBM)" ),
            "image/x-portable-graymap" : self.__tr( "Portable Grayscale Image (PGM)" ),
            "image/x-portable-pixmap" : self.__tr( "Portable Color Image (PPM)" ),
            "image/x-sgi-rgb" : self.__tr( "SGI RGB" ),
            "image/x-xbitmap" : self.__tr( "X11 Bitmap (XBM)" ),
            "image/x-xpixmap" : self.__tr( "X11 Pixmap (XPM)" ),
            "image/x-sun-raster" : self.__tr( "Sun Raster Format" ),
        }

        icon = QPixmap( os.path.join( prop.image_dir, 'HPmenu.png' ) )
        self.setIcon( icon )

        pix = QPixmap( os.path.join( prop.image_dir, 'folder_open.png' ) )
        self.addFileButton.setPixmap( pix )

        pix = QPixmap( os.path.join( prop.image_dir, 'folder_remove.png' ) )
        self.delFileButton.setPixmap( pix )
        
        pix = QPixmap( os.path.join( prop.image_dir, 'status_refresh.png' ))
        self.refreshToolButton.setPixmap( pix )

        self.fileListView.setSorting(-1)

        for f in args:
            self.addFile( f )

        # Scan all /etc/cups/*.convs files for allowable file formats
        files = glob.glob( "/etc/cups/*.convs" )

        self.allowable_mime_types = []

        for f in files:
            log.debug( "Capturing allowable MIME types from: %s" % f )
            conv_file = file( f, 'r' )

            for line in conv_file:
                if not line.startswith("#") and len(line) > 1:
                    try:
                        source, dest, cost, prog =  line.split()
                    except ValueError:
                        continue

                    self.allowable_mime_types.append( source )

        QTimer.singleShot( 0, self.InitialUpdate )

    def InitialUpdate( self ):
        self.cups_printers = []
        self.printer_list = cups.getPrinters()

        if self.device_uri is None:

            if self.printer_name is None:
                self.FailureUI( self.__tr( "<b>You must provide a device URI or printer name.</b><p>Run 'hp-print --help' for a list of options." ) )
                self.close()
                return

            else:
                found = False
                for p in self.printer_list:
                    if p.name == self.printer_name:
                        found = True
                        self.device_uri = p.device_uri
                        break
                else:
                    self.FailureUI( self.__tr( "<b>Unknown printer name.</b><p>Run 'lpstat -a' or 'hp-probe' for a list of printers." ) )                    
                    self.close()
                    return


        log.debug( self.device_uri )
        self.DeviceURIText.setText( self.device_uri )

        for p in self.printer_list:
            if p.device_uri == self.device_uri:
                self.cups_printers.append( p.name )

        for p in self.cups_printers:
            self.printerNameComboBox.insertItem( p )

        self.dev = device.Device( self.device_uri )
        
        self.UpdatePrinterStatus()
        
        if self.printer_name is None:
            self.printerNameComboBox.setCurrentItem(0)
        elif self.printer_name in self.cups_printers:
            self.printerNameComboBox.setCurrentText( self.printer_name )

        self.current_printer = str( self.printerNameComboBox.currentText() )

        self.UpdatePrinterInfo()

    def UpdatePrinterStatus( self ):
        self.dev.queryDevice()

        if self.dev.device_state == DEVICE_STATE_NOT_FOUND:
            self.FailureUI( self.__tr( "<b>Unable to communicate with device:</b><p>%s" % self.device_uri ) )
            self.close()
            return

        self.StateText.setText( self.dev.status_desc )
        self.dev.close()

    def addFile( self, path ):
        path = os.path.realpath( path )
        if os.path.exists( path ):
            mime_type = magic.mime_type( path )
            mime_type_desc = mime_type

            try:
                mime_type_desc = self.MIME_TYPES_DESC[ mime_type ]
            except:
                self.WarningUI( self.__tr( "<b>You are trying to add a file that cannot be directly printed with this utility.</b><p>To print this file, use the print command in the application that created it." ) )
            else:
                log.debug( "Adding file %s (%s,%s)" % ( path, mime_type, mime_type_desc ) )
                self.file_list.append( ( path, mime_type, mime_type_desc ) )
        else:
            self.FailureUI( self.__tr( "<b>Unable to add file '%s' to file list.</b><p>Check the file name and try again." % path ) )

        self.UpdateFileList()

    def UpdateFileList( self ):
        self.fileListView.clear()
        temp = self.file_list[:]
        temp.reverse()

        for p, t, d in temp:
            i = QListViewItem( self.fileListView, os.path.basename( p ), d, p )
            #self.fileListView.setSelected( i, True )

        non_empty_file_list = self.fileListView.childCount() > 0
        ##self.delFileButton.setEnabled( non_empty_file_list )
        self.printPushButton.setEnabled( non_empty_file_list )

    def addFileButton_clicked(self):
        ##s = str( QFileDialog.getOpenFileName( os.path.expanduser("~"), "All files (*.*)", self, 
        ##                                      "openfile", self.caption() ) )
        ##if s: 
        ##    self.addFile( s )
        self.setFocus()
        
        log.debug("isTopLevel %d" % self.isTopLevel())
        log.debug("hasFocus %d" % self.hasFocus())
        log.debug("isEnabled %d" % self.isEnabled())
        
        workingDirectory = os.path.expanduser("~")
        
        log.debug("workingDirectory: %s" % workingDirectory)
        
        dlg = QFileDialog(workingDirectory, QString.null, None, None, True )
        
        dlg.setCaption( "openfile" )
        dlg.setMode( QFileDialog.ExistingFile )
        dlg.show() 
        
        if dlg.exec_loop() == QDialog.Accepted:
                results = dlg.selectedFile()
                workingDirectory = dlg.url()
                log.debug("results: %s" % results)
                log.debug("workingDirectory: %s" % workingDirectory)
                
                if results:
                    self.addFile(str(results))
            
            

    def delFileButton_clicked(self):
        try:
            path = self.fileListView.currentItem().text(2)
        except AttributeError:
            return
        else:
            index = 0
            for p, t, d in self.file_list:
                if p == path:
                    del self.file_list[index]
                    break
                index += 1
    
            self.UpdateFileList()


    def fileListView_currentChanged(self,item):
        #print item
        pass

    def printerNameComboBox_highlighted(self,a0):
        self.current_printer = str(a0)
        self.UpdatePrinterInfo()

    def UpdatePrinterInfo( self ):
        for p in self.printer_list:
            if p.name == self.current_printer:
                
                try:
                    self.LocationText.setText( p.location )
                except AttributeError:
                    self.LocationText.setText( '' )
                
                try:
                    self.CommentText.setText( p.info )
                except AttributeError:
                    self.CommentText.setText( '' )
                    
                cups.openPPD( p.name )
                self.UpdateDuplex()
                cups.closePPD()
                break

    def UpdateDuplex( self ):
        duplex = cups.getPPDOption( "Duplex" )
        if duplex is not None:
            if duplex.startswith( "long" ):
                self.duplexButtonGroup.setButton( 1 )
                self.auto_duplex_button_group = 1
            elif duplex.startswith( "short" ):
                self.duplexButtonGroup.setButton( 2 )
                self.auto_duplex_button_group = 2
            else:
                self.duplexButtonGroup.setButton( 0 )
                self.auto_duplex_button_group = 0
        else:
            self.duplexButtonGroup.setEnabled( False )


    def pagesButtonGroup_clicked(self,item):
        self.pageRangeEdit.setEnabled( item == 1 )

    def printPushButton_clicked(self):
        copies = int( self.copiesSpinBox.value() )
        rev = bool( self.reverseCheckBox.isChecked() )
        collate = bool( self.collateCheckBox.isChecked() )
        all_pages = self.pages_button_group == 0
        page_range = str( self.pageRangeEdit.text() )
        page_set = int( self.pageSetComboBox.currentItem() )
        nup = int( str( self.nUpComboBox.currentText() ) )

        for p, t, d in self.file_list:

            cmd = ' '.join( [ 'lpr -P', self.current_printer ] )

            if copies > 1:
                cmd = ' '.join( [ cmd, '-#%d' % copies ] )

            if not all_pages and len( page_range ) > 0:
                cmd = ' '.join( [ cmd, '-o page-ranges=%s' % page_range ] )

            if page_set > 0:
                if page_set == 1:
                    cmd = ' '.join( [ cmd, '-o page-set=even' ] )
                else:
                    cmd = ' '.join( [ cmd, '-o page-set=odd' ] )

            if rev:
                cmd = ' '.join( [ cmd, '-o outputorder=reverse' ] )

            if collate and copies > 1:
                cmd = ' '.join( [ cmd, '-o Collate=True' ] )

            if t in [   "application/x-cshell", 
                        "application/x-perl",
                        "application/x-python",
                        "application/x-shell",
                        "text/plain",
                    ]:
                cmd = ' '.join( [ cmd, '-o prettyprint' ] )

            if nup > 1:
                cmd = ' '.join( [ cmd, '-o number-up=%d' % nup ] )

            if self.auto_duplex_button_group == 1: # long
                cmd = ' '.join( [ cmd, '-o sides=two-sided-long-edge' ] )
            elif self.auto_duplex_button_group == 2: # short
                cmd = ' '.join( [ cmd, '-o sides=two-sided-short-edge' ] )
            else:
                cmd = ' '.join( [ cmd, '-o sides=one-sided' ] )

            if self.orientation_button_group == 1:
                cmd = ' '.join( [ cmd, '-o landscape' ] )

            cmd = ''.join( [ cmd, ' "', p, '"' ] )

            log.debug( "Printing: %s" % cmd )

            os.system( cmd )

        del self.file_list[:]
        self.UpdateFileList()

    def pagesButtonGroup_clicked(self,a0):
        self.pages_button_group = a0
        self.pageRangeEdit.setEnabled( a0 == 1 )
            

    def duplexButtonGroup_clicked(self,a0):
        self.auto_duplex_button_group = a0

    def orientationButtonGroup_clicked(self,a0):
        self.orientation_button_group = a0

    def refreshToolButton_clicked(self):
        self.UpdatePrinterStatus()


    def SuccessUI( self ):
        QMessageBox.information( self, 
                             self.caption(),
                             self.__tr( "<p><b>The operation completed successfully.</b>" ),
                              QMessageBox.Ok, 
                              QMessageBox.NoButton, 
                              QMessageBox.NoButton )

    def FailureUI( self, error_text ):
        QMessageBox.critical( self, 
                             self.caption(),
                             error_text,
                              QMessageBox.Ok, 
                              QMessageBox.NoButton, 
                              QMessageBox.NoButton )

    def WarningUI( self, msg ):
        QMessageBox.warning( self, 
                             self.caption(),
                             msg,
                              QMessageBox.Ok, 
                              QMessageBox.NoButton, 
                              QMessageBox.NoButton )        


    def __tr(self,s,c = None):
        return qApp.translate("PrinterForm",s,c)


