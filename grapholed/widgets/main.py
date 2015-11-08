# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  GrapholEd: an editor for the Graphol ontology language.               #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


import os
import sys
import traceback
import webbrowser

from PyQt5.QtCore import Qt, QRectF, pyqtSlot, QSettings, QFile, QIODevice, pyqtSignal, QTextStream, QSizeF
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap, QPainter, QPageSize
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget, QAction, QStatusBar, QMessageBox, QDialog
from PyQt5.QtWidgets import QUndoGroup
from PyQt5.QtXml import QDomDocument

from grapholed import __version__, __appname__, __organization__
from grapholed.datatypes import FileType, DiagramMode, DistinctList
from grapholed.dialogs import AboutDialog, OpenFileDialog, PreferencesDialog, SaveFileDialog
from grapholed.exceptions import ParseError
from grapholed.functions import getPath, shaded, connect, disconnect
from grapholed.items import __mapping__, ItemType
from grapholed.widgets.dock import DockWidget, Navigator, Overview, Palette
from grapholed.widgets.mdi import MdiArea, MdiSubWindow
from grapholed.widgets.scene import DiagramScene, DiagramDocument
from grapholed.widgets.view import MainView
from grapholed.widgets.toolbar import ZoomControl


class MainWindow(QMainWindow):
    """
    This class implements the Grapholed Main Window.
    """
    MaxRecentDocuments = 5
    MinWidth = 1024
    MinHeight = 600

    documentLoaded = pyqtSignal('QGraphicsScene')
    documentSaved = pyqtSignal('QGraphicsScene')

    def __init__(self):
        """
        Initialize the application Main Window.
        """
        super().__init__()
        self.abortQuit = False  ## will be set to true whenever we need to about a Quit action
        self.settings = QSettings(__organization__, __appname__)  ## application settings
        self.undoGroup = QUndoGroup()  ## undo group for DiagramScene undo stacks

        ################################################# ICONS ########################################################

        def getIcon(path):
            """
            Load the given icon.
            :param path: the icon path.
            :rtype: QIcon
            """
            icon = QIcon()
            icon.addPixmap(QPixmap(path), QIcon.Normal)
            icon.addPixmap(shaded(QPixmap(path), 0.25), QIcon.Disabled)
            return icon

        self.iconBringToFront = getIcon(':/icons/bring-to-front')
        self.iconClose = getIcon(':/icons/close')
        self.iconCopy = getIcon(':/icons/copy')
        self.iconCut = getIcon(':/icons/cut')
        self.iconDelete = getIcon(':/icons/delete')
        self.iconGrid = getIcon(':/icons/grid')
        self.iconLink = getIcon(':/icons/link')
        self.iconNew = getIcon(':/icons/new')
        self.iconOpen = getIcon(':/icons/open')
        self.iconPaste = getIcon(':/icons/paste')
        self.iconPalette = getIcon(':/icons/appearance')
        self.iconPreferences = getIcon(':/icons/preferences')
        self.iconPrint = getIcon(':/icons/print')
        self.iconQuit = getIcon(':/icons/quit')
        self.iconRedo = getIcon(':/icons/redo')
        self.iconSave = getIcon(':/icons/save')
        self.iconSaveAs = getIcon(':/icons/save')
        self.iconSelectAll = getIcon(':/icons/select-all')
        self.iconSendToBack = getIcon(':/icons/send-to-back')
        self.iconUndo = getIcon(':/icons/undo')
        self.iconZoom = getIcon(':/icons/zoom')

        ############################################# DOCK WIDGETS #####################################################

        self.palette_ = Palette()
        self.paletteDock = DockWidget('Palette', self)
        self.paletteDock.setWidget(self.palette_)

        self.navigator = Navigator()
        self.navigatorDock = DockWidget('Navigator', self)
        self.navigatorDock.setWidget(self.navigator)

        self.overview = Overview()
        self.overviewDock = DockWidget('Overview', self)
        self.overviewDock.setWidget(self.overview)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.paletteDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.navigatorDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.overviewDock)

        ########################################### MAIN AREA WIDGET ###################################################

        self.mdiArea = MdiArea()
        self.setCentralWidget(self.mdiArea)
        self.setWindowIcon(QIcon(':/images/grapholed'))
        self.setWindowTitle()

        ################################################ ACTIONS #######################################################

        self.actionNewDocument = QAction('New', self)
        self.actionNewDocument.setIcon(self.iconNew)
        self.actionNewDocument.setShortcut(QKeySequence.New)
        self.actionNewDocument.setStatusTip('Create a new diagram')
        connect(self.actionNewDocument.triggered, self.newDocument)

        self.actionOpenDocument = QAction('Open...', self)
        self.actionOpenDocument.setIcon(self.iconOpen)
        self.actionOpenDocument.setShortcut(QKeySequence.Open)
        self.actionOpenDocument.setStatusTip('Open a diagram')
        connect(self.actionOpenDocument.triggered, self.openDocument)

        self.actionsOpenRecentDocument = []
        for i in range(MainWindow.MaxRecentDocuments):
            action = QAction(self)
            action.setVisible(False)
            self.actionsOpenRecentDocument.append(action)

        self.actionSaveDocument = QAction('Save', self)
        self.actionSaveDocument.setIcon(self.iconSave)
        self.actionSaveDocument.setShortcut(QKeySequence.Save)
        self.actionSaveDocument.setStatusTip('Save the current document')
        self.actionSaveDocument.setEnabled(False)
        connect(self.actionSaveDocument.triggered, self.saveDocument)

        self.actionSaveDocumentAs = QAction('Save As...', self)
        self.actionSaveDocumentAs.setIcon(self.iconSaveAs)
        self.actionSaveDocumentAs.setShortcut(QKeySequence.SaveAs)
        self.actionSaveDocumentAs.setStatusTip('Save the active diagram')
        self.actionSaveDocumentAs.setEnabled(False)
        connect(self.actionSaveDocumentAs.triggered, self.saveDocumentAs)

        self.actionImportDocument = QAction('Import...', self)
        self.actionImportDocument.setStatusTip('Import a document')
        connect(self.actionImportDocument.triggered, self.importDocument)

        self.actionExportDocument = QAction('Export...', self)
        self.actionExportDocument.setStatusTip('Export the active diagram')
        self.actionExportDocument.setEnabled(False)
        connect(self.actionExportDocument.triggered, self.exportDocument)

        self.actionPrintDocument = QAction('Print...', self)
        self.actionPrintDocument.setIcon(self.iconPrint)
        self.actionPrintDocument.setStatusTip('Print the active diagram')
        self.actionPrintDocument.setEnabled(False)
        connect(self.actionPrintDocument.triggered, self.printDocument)

        self.actionCloseActiveSubWindow = QAction('Close', self)
        self.actionCloseActiveSubWindow.setIcon(self.iconClose)
        self.actionCloseActiveSubWindow.setShortcut(QKeySequence.Close)
        self.actionCloseActiveSubWindow.setStatusTip('Close the active diagram')
        self.actionCloseActiveSubWindow.setEnabled(False)
        connect(self.actionCloseActiveSubWindow.triggered, lambda: self.mdiArea.activeSubWindow().close())

        self.actionOpenPreferences = QAction('Preferences', self)
        self.actionOpenPreferences.setShortcut(QKeySequence.Preferences)
        self.actionOpenPreferences.setStatusTip('Open {0} preferences'.format(__appname__))
        connect(self.actionOpenPreferences.triggered, self.openPreferences)

        if not sys.platform.startswith('darwin'):
            self.actionOpenPreferences.setIcon(self.iconPreferences)

        self.actionQuit = QAction('Quit', self)
        self.actionQuit.setStatusTip('Quit {0}'.format(__appname__))
        self.actionQuit.setShortcut(QKeySequence.Quit)
        connect(self.actionQuit.triggered, self.close)

        if not sys.platform.startswith('darwin'):
            self.actionQuit.setIcon(self.iconQuit)

        self.actionSnapToGrid = QAction('Snap to grid', self)
        self.actionSnapToGrid.setIcon(self.iconGrid)
        self.actionSnapToGrid.setStatusTip('Snap diagram elements to the grid')
        self.actionSnapToGrid.setCheckable(True)
        self.actionSnapToGrid.setChecked(self.settings.value('scene/snap_to_grid', False, bool))
        connect(self.actionSnapToGrid.triggered, self.toggleSnapToGrid)

        self.actionAbout = QAction('About {0}'.format(__appname__), self)
        self.actionAbout.setShortcut(QKeySequence.HelpContents)
        connect(self.actionAbout.triggered, self.about)

        self.actionSapienzaWebOpen = QAction('DIAG - Sapienza university', self)
        self.actionSapienzaWebOpen.setIcon(self.iconLink)
        connect(self.actionSapienzaWebOpen.triggered, lambda: webbrowser.open('http://www.dis.uniroma1.it/en'))

        self.actionGrapholWebOpen = QAction('Graphol homepage', self)
        self.actionGrapholWebOpen.setIcon(self.iconLink)
        connect(self.actionGrapholWebOpen.triggered, lambda: webbrowser.open('http://www.dis.uniroma1.it/~graphol/'))

        ## SET THE ICON ON DOCK WIDGETS ACTIONS
        self.navigatorDock.toggleViewAction().setIcon(self.iconZoom)
        self.overviewDock.toggleViewAction().setIcon(self.iconZoom)
        self.paletteDock.toggleViewAction().setIcon(self.iconPalette)

        # --------------------------------------- SCENE SPECIFIC ACTIONS --------------------------------------------- #
        # actions below are being used from within the DiagramScene (context menu): they need to be declared here      #
        # in the Main Window so we can add them to the toolbar (so they are both bisivle there and they can also be    #
        # triggered by means of shortcuts (see description below for actions with shortcuts only)                      #
        # ------------------------------------------------------------------------------------------------------------ #

        self.actionItemCut = QAction('Cut', self)
        self.actionItemCut.setIcon(self.iconCut)
        self.actionItemCut.setShortcut(QKeySequence.Cut)
        self.actionItemCut.setStatusTip('Cut selected items')
        self.actionItemCut.setEnabled(False)

        self.actionItemCopy = QAction('Copy', self)
        self.actionItemCopy.setIcon(self.iconCopy)
        self.actionItemCopy.setShortcut(QKeySequence.Copy)
        self.actionItemCopy.setStatusTip('Copy selected items')
        self.actionItemCopy.setEnabled(False)

        self.actionItemPaste = QAction('Paste', self)
        self.actionItemPaste.setIcon(self.iconPaste)
        self.actionItemPaste.setShortcut(QKeySequence.Paste)
        self.actionItemPaste.setStatusTip('Paste items')
        self.actionItemPaste.setEnabled(False)

        self.actionItemDelete = QAction('Delete', self)
        self.actionItemDelete.setIcon(self.iconDelete)
        self.actionItemDelete.setShortcut(QKeySequence.Delete)
        self.actionItemDelete.setStatusTip('Delete selected items')
        self.actionItemDelete.setEnabled(False)

        self.actionBringToFront = QAction('Bring to Front', self)
        self.actionBringToFront.setIcon(self.iconBringToFront)
        self.actionBringToFront.setStatusTip('Bring selected items to front')
        self.actionBringToFront.setEnabled(False)

        self.actionSendToBack = QAction('Send to Back', self)
        self.actionSendToBack.setIcon(self.iconSendToBack)
        self.actionSendToBack.setStatusTip('Send selected items to back')
        self.actionSendToBack.setEnabled(False)

        self.actionSelectAll = QAction('Select All', self)
        self.actionSelectAll.setIcon(self.iconSelectAll)
        self.actionSelectAll.setShortcut(QKeySequence.SelectAll)
        self.actionSelectAll.setStatusTip('Select all items in the active diagram')
        self.actionSelectAll.setEnabled(False)

        self.actionUndo = self.undoGroup.createUndoAction(self)
        self.actionUndo.setIcon(self.iconUndo)
        self.actionUndo.setShortcut(QKeySequence.Undo)

        self.actionRedo = self.undoGroup.createRedoAction(self)
        self.actionRedo.setIcon(self.iconRedo)
        self.actionRedo.setShortcut(QKeySequence.Redo)

        # ---------------------------------------- SHORTCUT ONLY ACTIONS --------------------------------------------- #
        # actions below are not available in the application Main Menu, nor in the Toolbar (entries can be found in    #
        # context menus): since we need shortcuts to work, we would need to add such actions to a visible widget that  #
        # receive events, otherwise we won't be able to use shortcuts. More on this can be found in the lik below:     #
        # https://forum.qt.io/topic/15107/solved-action-shortcut-not-triggering-unless-action-is-placed-in-a-toolbar)  #
        # ------------------------------------------------------------------------------------------------------------ #
        self.actionToggleEdgeComplete = QAction('Complete', self)
        self.actionToggleEdgeComplete.setShortcut('ALT+C')
        self.actionToggleEdgeComplete.setCheckable(True)

        self.actionToggleEdgeFunctional = QAction('Functional', self)
        self.actionToggleEdgeFunctional.setShortcut('ALT+F')
        self.actionToggleEdgeFunctional.setCheckable(True)

        self.addAction(self.actionToggleEdgeComplete)
        self.addAction(self.actionToggleEdgeFunctional)
        
        ################################################# MENUS ########################################################

        self.menuFile = self.menuBar().addMenu("&File")
        self.menuFile.addAction(self.actionNewDocument)
        self.menuFile.addAction(self.actionOpenDocument)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSaveDocument)
        self.menuFile.addAction(self.actionSaveDocumentAs)
        self.menuFile.addAction(self.actionCloseActiveSubWindow)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionImportDocument)
        self.menuFile.addAction(self.actionExportDocument)

        self.recentDocumentSeparator = self.menuFile.addSeparator()
        for i in range(MainWindow.MaxRecentDocuments):
            self.menuFile.addAction(self.actionsOpenRecentDocument[i])
        self.updateRecentDocumentActions()

        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionPrintDocument)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)

        self.menuEdit = self.menuBar().addMenu("&Edit")
        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionItemCut)
        self.menuEdit.addAction(self.actionItemCopy)
        self.menuEdit.addAction(self.actionItemPaste)
        self.menuEdit.addAction(self.actionItemDelete)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionBringToFront)
        self.menuEdit.addAction(self.actionSendToBack)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionSelectAll)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionOpenPreferences)

        self.menuView = self.menuBar().addMenu("&View")
        self.menuView.addAction(self.actionSnapToGrid)
        self.menuView.addSeparator()
        self.menuView.addAction(self.navigatorDock.toggleViewAction())
        self.menuView.addAction(self.overviewDock.toggleViewAction())
        self.menuView.addAction(self.paletteDock.toggleViewAction())

        self.menuHelp = self.menuBar().addMenu("&Help")
        self.menuHelp.addAction(self.actionAbout)

        if not sys.platform.startswith('darwin'):
            self.menuHelp.addSeparator()

        self.menuHelp.addAction(self.actionSapienzaWebOpen)
        self.menuHelp.addAction(self.actionGrapholWebOpen)

        ############################################### STATUS BAR #####################################################

        statusbar = QStatusBar(self)
        statusbar.setSizeGripEnabled(False)
        self.setStatusBar(statusbar)

        ################################################# TOOLBAR ######################################################

        self.zoomctl = ZoomControl()

        self.documentToolBar = self.addToolBar("Document")
        self.documentToolBar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.documentToolBar.setFloatable(False)
        self.documentToolBar.setMovable(False)

        self.documentToolBar.addAction(self.actionNewDocument)
        self.documentToolBar.addAction(self.actionOpenDocument)
        self.documentToolBar.addAction(self.actionSaveDocument)
        self.documentToolBar.addAction(self.actionPrintDocument)
        self.documentToolBar.addSeparator()
        self.documentToolBar.addAction(self.actionUndo)
        self.documentToolBar.addAction(self.actionRedo)
        self.documentToolBar.addSeparator()
        self.documentToolBar.addAction(self.actionItemCut)
        self.documentToolBar.addAction(self.actionItemCopy)
        self.documentToolBar.addAction(self.actionItemPaste)
        self.documentToolBar.addAction(self.actionItemDelete)
        self.documentToolBar.addSeparator()
        self.documentToolBar.addAction(self.actionBringToFront)
        self.documentToolBar.addAction(self.actionSendToBack)
        self.documentToolBar.addSeparator()
        self.documentToolBar.addAction(self.actionSnapToGrid)
        self.documentToolBar.addSeparator()
        self.documentToolBar.addWidget(self.zoomctl)

        ############################################### GEOMETRY #######################################################

        screen = QDesktopWidget().screenGeometry()
        posX = (screen.width() - MainWindow.MinWidth) / 2
        posY = (screen.height() - MainWindow.MinHeight) / 2
        self.setGeometry(posX, posY, MainWindow.MinWidth, MainWindow.MinHeight)
        self.setMinimumSize(MainWindow.MinWidth, MainWindow.MinHeight)

        ############################################### SIGNALS ########################################################

        connect(self.documentLoaded, self.onDocumentLoaded)
        connect(self.documentSaved, self.onDocumentSaved)
        connect(self.mdiArea.subWindowActivated, self.onSubWindowActivated)
        connect(self.palette_.buttonClicked[int], self.onPaletteButtonClicked)
        connect(self.undoGroup.cleanChanged, self.onUndoGroupCleanChanged)

        for i in range(MainWindow.MaxRecentDocuments):
            connect(self.actionsOpenRecentDocument[i].triggered, self.openRecentDocument)

    ####################################################################################################################
    #                                                                                                                  #
    #   ACTION HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def about(self):
        """
        Display the about dialog.
        """
        about = AboutDialog()
        about.exec_()

    @pyqtSlot()
    def exportDocument(self):
        """
        Export the currently open graphol document.
        """
        mainview = self.mdiArea.activeView
        if mainview:
            scene = mainview.scene()
            res = self.getExportFilePath(name=scene.document.name)
            if res:
                filepath = res[0]
                filetype = FileType.forValue(res[1])
                if filetype is FileType.pdf:
                    self.exportSceneToPdfFile(scene, filepath)

    @pyqtSlot()
    def importDocument(self):
        """
        Import a document from a different file format.
        """
        pass

    @pyqtSlot()
    def newDocument(self):
        """
        Create a new empty document and add it to the MDI Area.
        """
        size = self.settings.value('scene/size', 5000, int)
        scene = self.getScene(size, size)
        mainview = self.getMainView(scene)
        subwindow = self.getMDISubWindow(mainview)
        subwindow.showMaximized()
        self.mdiArea.setActiveSubWindow(subwindow)
        self.mdiArea.update()

    @pyqtSlot()
    def openDocument(self):
        """
        Open a document.
        """
        dialog = OpenFileDialog(getPath('~'))
        dialog.setNameFilters([FileType.graphol.value])
        if dialog.exec_():
            filepath = dialog.selectedFiles()[0]
            if not self.focusDocument(filepath):
                scene = self.getSceneFromGrapholFile(filepath)
                if scene:
                    mainview = self.getMainView(scene)
                    subwindow = self.getMDISubWindow(mainview)
                    subwindow.showMaximized()
                    self.mdiArea.setActiveSubWindow(subwindow)
                    self.mdiArea.update()

    @pyqtSlot()
    def openRecentDocument(self):
        """
        Open the clicked recent document.
        """
        action = self.sender()
        if action:
            if not self.focusDocument(action.data()):
                scene = self.getSceneFromGrapholFile(action.data())
                if scene:
                    mainview = self.getMainView(scene)
                    subwindow = self.getMDISubWindow(mainview)
                    subwindow.showMaximized()
                    self.mdiArea.setActiveSubWindow(subwindow)
                    self.mdiArea.update()

    @pyqtSlot()
    def saveDocument(self):
        """
        Save the currently open graphol document.
        """
        mainview = self.mdiArea.activeView
        if mainview:
            scene = mainview.scene()
            filepath = scene.document.filepath or self.getSaveFilePath(name=scene.document.name)
            if filepath:
                saved = self.saveSceneToGrapholFile(scene, filepath)
                if saved:
                    scene.document.filepath = filepath
                    scene.document.edited = os.path.getmtime(filepath)
                    scene.undoStack.setClean()
                    self.documentSaved.emit(scene)

    @pyqtSlot()
    def saveDocumentAs(self):
        """
        Save the currently open graphol document (enforcing a new name).
        """
        mainview = self.mdiArea.activeView
        if mainview:
            scene = mainview.scene()
            filepath = self.getSaveFilePath(name=scene.document.name)
            if filepath:
                saved = self.saveSceneToGrapholFile(scene, filepath)
                if saved:
                    scene.document.filepath = filepath
                    scene.document.edited = os.path.getmtime(filepath)
                    scene.undoStack.setClean()
                    self.documentSaved.emit(scene)

    @pyqtSlot()
    def printDocument(self):
        """
        Print the currently open graphol document.
        """
        mainview = self.mdiArea.activeView
        if mainview:
            scene = mainview.scene()
            shape = scene.visibleRect(margin=20)
            if shape:
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.NativeFormat)
                dialog = QPrintDialog(printer)
                if dialog.exec_() == QDialog.Accepted:
                    painter = QPainter()
                    if painter.begin(printer):
                        scene.render(painter, source=shape)

    @pyqtSlot()
    def openPreferences(self):
        """
        Open the preferences dialog.
        """
        preferences = PreferencesDialog(self.centralWidget())
        preferences.exec_()

    @pyqtSlot()
    def toggleSnapToGrid(self):
        """
        Toggle snap to grid setting.
        """
        self.settings.setValue('scene/snap_to_grid', self.actionSnapToGrid.isChecked())
        mainview = self.mdiArea.activeView
        if mainview:
            mainview.scene().update()

    ####################################################################################################################
    #                                                                                                                  #
    #   SIGNAL HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot('QGraphicsScene')
    def onDocumentLoaded(self, scene):
        """
        Executed when a document is loaded from Graphol file.
        :param scene: the DiagramScene instance containing the document.
        """
        self.addRecentDocument(scene.document.filepath)
        self.setWindowTitle(scene.document.name)

    @pyqtSlot('QGraphicsScene')
    def onDocumentSaved(self, scene):
        """
        Executed when a document is saved to a Graphol file
        :param scene: the DiagramScene instance containing the document.
        """
        self.addRecentDocument(scene.document.filepath)
        self.setWindowTitle(scene.document.name)

    @pyqtSlot('QGraphicsItem', int)
    def onEdgeInserted(self, edge, modifiers):
        """
        Triggered after a edge insertion process ends.
        :param edge: the inserted edge.
        :param modifiers: keyboard modifiers held during edge insertion.
        """
        if not modifiers & Qt.ControlModifier:
            self.palette_.button(edge.itemtype).setChecked(False)

    @pyqtSlot('QGraphicsItem', int)
    def onNodeInserted(self, node, modifiers):
        """
        Triggered after a node insertion process ends.
        :param node: the inserted node.
        :param modifiers: keyboard modifiers held during node insertion.
        """
        if not modifiers & Qt.ControlModifier:
            self.palette_.button(node.itemtype).setChecked(False)

    @pyqtSlot(DiagramMode)
    def onModeChanged(self, mode):
        """
        Triggered when the scene operation mode changes.
        :param mode: the scene operation mode.
        """
        if mode not in (DiagramMode.NodeInsert, DiagramMode.EdgeInsert):
            self.palette_.clear()

    @pyqtSlot(int)
    def onPaletteButtonClicked(self, button_id):
        """
        Executed whenever a Palette button is clicked.
        :param button_id: the button id.
        """
        mainview = self.mdiArea.activeView
        if not mainview:
            self.palette_.clear()
        else:
            scene = mainview.scene()
            scene.clearSelection()
            button = self.palette_.button(button_id)
            self.palette_.clear(button)
            if not button.isChecked():
                scene.setMode(DiagramMode.Idle)
            else:
                if ItemType.ConceptNode <= button_id < ItemType.InclusionEdge:
                    scene.setMode(DiagramMode.NodeInsert, button.property('item'))
                elif ItemType.InclusionEdge <= button_id <= ItemType.InstanceOfEdge:
                    scene.setMode(DiagramMode.EdgeInsert, button.property('item'))

    @pyqtSlot('QMdiSubWindow')
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :param subwindow: the subwindow which got the focus (0 if there is no subwindow).
        """
        if subwindow:

            mainview = subwindow.widget()
            scene = mainview.scene()
            scene.undoStack.setActive()
            scene.updateActions()

            self.navigator.setView(mainview)
            self.overview.setView(mainview)

            self.actionCloseActiveSubWindow.setEnabled(True)
            self.actionExportDocument.setEnabled(True)
            self.actionPrintDocument.setEnabled(True)
            self.actionSaveDocumentAs.setEnabled(True)
            self.actionSelectAll.setEnabled(True)

            disconnect(self.actionToggleEdgeComplete.triggered)
            disconnect(self.actionToggleEdgeFunctional.triggered)
            disconnect(self.actionItemCut.triggered)
            disconnect(self.actionItemCopy.triggered)
            disconnect(self.actionItemPaste.triggered)
            disconnect(self.actionItemDelete.triggered)
            disconnect(self.actionBringToFront.triggered)
            disconnect(self.actionSendToBack.triggered)
            disconnect(self.actionSelectAll.triggered)
            disconnect(self.zoomctl.scaleChanged)
            disconnect(mainview.zoomChanged)

            self.zoomctl.setEnabled(False)
            self.zoomctl.setZoomLevel(self.zoomctl.index(mainview.zoom))
            self.zoomctl.setEnabled(True)

            connect(self.actionToggleEdgeComplete.triggered, scene.toggleEdgeComplete)
            connect(self.actionToggleEdgeFunctional.triggered, scene.toggleEdgeFunctional)
            connect(self.actionItemCut.triggered, scene.itemCut)
            connect(self.actionItemCopy.triggered, scene.itemCopy)
            connect(self.actionItemPaste.triggered, scene.itemPaste)
            connect(self.actionItemDelete.triggered, scene.itemDelete)
            connect(self.actionBringToFront.triggered, scene.bringToFront)
            connect(self.actionSendToBack.triggered, scene.sendToBack)
            connect(self.actionSelectAll.triggered, scene.selectAll)
            connect(self.zoomctl.scaleChanged, mainview.onScaleChanged)
            connect(mainview.zoomChanged, self.zoomctl.onMainViewZoomChanged)

            self.setWindowTitle(scene.document.name)

        else:

            # disable the stuff below only if all the subwindows have been closed: this if clause
            # make sure to keep those things activated in case the MainWindow lost just the focus
            if not self.mdiArea.subWindowList():

                self.actionSaveDocumentAs.setEnabled(False)
                self.actionExportDocument.setEnabled(False)
                self.actionPrintDocument.setEnabled(False)
                self.actionItemCut.setEnabled(False)
                self.actionItemCopy.setEnabled(False)
                self.actionItemPaste.setEnabled(False)
                self.actionItemDelete.setEnabled(False)
                self.actionBringToFront.setEnabled(False)
                self.actionSendToBack.setEnabled(False)
                self.actionSelectAll.setEnabled(False)
                self.actionCloseActiveSubWindow.setEnabled(False)
                self.zoomctl.reset()
                self.zoomctl.setEnabled(False)
                self.navigator.clearView()
                self.overview.clearView()
                self.setWindowTitle()

    @pyqtSlot('QMdiSubWindow')
    def onSubwindowCloseEventIgnored(self, subwindow):
        """
        Executed when the close event of an MDI subwindow is aborted.
        :param subwindow: the subwindow whose closeEvent has been interrupted.
        """
        self.abortQuit = True
        self.mdiArea.setActiveSubWindow(subwindow)

    @pyqtSlot(bool)
    def onUndoGroupCleanChanged(self, clean):
        """
        Executed when the clean state of the active undoStack changes.
        :param clean: the clean state.
        """
        self.actionSaveDocument.setEnabled(not clean)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def closeEvent(self, closeEvent):
        """
        Executed when the main window is closed.
        :param closeEvent: the close event instance.
        """
        self.abortQuit = False
        for subwindow in self.mdiArea.subWindowList():
            mainview = subwindow.widget()
            scene = mainview.scene()
            if (scene.items() and not scene.document.filepath) or (not scene.undoStack.isClean()):
                self.mdiArea.setActiveSubWindow(subwindow)
                subwindow.showMaximized()
            subwindow.close()
            if self.abortQuit:
                closeEvent.ignore()
                break

    def keyReleaseEvent(self, keyEvent):
        """
        Executed when a keyboard button is released from the scene.
        :param keyEvent: the keyboard event instance.
        """
        if keyEvent.key() == Qt.Key_Control:
            mainview = self.mdiArea.activeView
            if mainview:
                scene = mainview.scene()
                scene.setMode(DiagramMode.Idle)
        super().keyReleaseEvent(keyEvent)

    def showEvent(self, showEvent):
        """
        Executed when the window is shown.
        :param showEvent: the show event instance.
        """
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.activateWindow()
        self.raise_()

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def addRecentDocument(self, path):
        """
        Add the given document to the recent document list
        :param path: the path of the recent document.
        :return:
        """
        documents = self.settings.value('recentDocumentList', DistinctList())
        documents.remove(path)
        documents.insert(0, path) # insert on top of the list
        documents = documents[:MainWindow.MaxRecentDocuments]
        self.settings.setValue('recentDocumentList', documents)
        self.updateRecentDocumentActions()

    @staticmethod
    def exportSceneToPdfFile(scene, filepath):
        """
        Export the given scene as PDF saving it in the given filepath.
        :param scene: the scene to be exported.
        :param filepath: the filepath where to export the scene.
        :return: True if the export has been performed, False otherwise.
        """
        shape = scene.visibleRect(margin=20)
        if shape:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filepath)
            printer.setPaperSize(QPrinter.Custom)
            printer.setPageSize(QPageSize(QSizeF(shape.width(), shape.height()), QPageSize.Point))

            painter = QPainter()
            if painter.begin(printer):
                scene.render(painter, source=shape)
                painter.end()
                return True

        return False

    def focusDocument(self, document):
        """
        Move the focus on the subwindow containing the given document.
        :param document: the document filepath.
        :return: True if the subwindow has been focused, False otherwise.
        :rtype: bool
        """
        if isinstance(document, DiagramScene):
            document = document.document.filepath
        elif isinstance(document, DiagramDocument):
            document = document.filepath

        for subwindow in self.mdiArea.subWindowList():
            scene = subwindow.widget().scene()
            if scene.document.filepath and scene.document.filepath == document:
                self.mdiArea.setActiveSubWindow(subwindow)
                self.mdiArea.update()
                return True

        return False

    @staticmethod
    def getExportFilePath(path=None, name=None):
        """
        Bring up the 'Export' file dialog and returns the selected filepath.
        Will return None in case the user hit the 'Cancel' button to abort the operation.
        :param path: the start path of the file dialog.
        :param name: the default name of the file.
        :return: a tuple with the filepath and the selected file filter.
        :rtype: tuple
        """
        dialog = SaveFileDialog(path)
        dialog.setWindowTitle('Export')
        dialog.setNameFilters([x.value for x in FileType if x is not FileType.graphol])
        dialog.selectFile(name or 'Untitled')
        if dialog.exec_():
            return dialog.selectedFiles()[0], dialog.selectedNameFilter()
        return None

    @staticmethod
    def getMainView(scene):
        """
        Create a new Main View for the given scene.
        :param scene: the scene to be added in the view.
        :rtype: MainView
        """
        view = MainView(scene)
        view.setViewportUpdateMode(MainView.FullViewportUpdate)
        view.centerOn(0, 0)
        view.setDragMode(MainView.RubberBandDrag)
        return view

    def getMDISubWindow(self, mainview):
        """
        Create a MdiSubWindow rendering the given main view to be added with the MDI area.
        :param mainview: the mainview to be rendered in the subwindow.
        :rtype: MdiSubWindow
        """
        subwindow = self.mdiArea.addSubWindow(MdiSubWindow(mainview))
        subwindow.updateSubwindowTitle()
        scene = mainview.scene()
        connect(self.documentSaved, subwindow.onDocumentSaved)
        connect(scene.undoStack.cleanChanged, subwindow.onUndoStackCleanChanged)
        connect(subwindow.closeEventIgnored, self.onSubwindowCloseEventIgnored)
        return subwindow

    @staticmethod
    def getSaveFilePath(path=None, name=None):
        """
        Bring up the 'Save' file dialog and returns the selected filepath.
        Will return None in case the user hit the 'Cancel' button to abort the operation.
        :param path: the start path of the file dialog.
        :param name: the default name of the file.
        :rtype: str
        """
        dialog = SaveFileDialog(path)
        dialog.setNameFilters([FileType.graphol.value])
        dialog.selectFile(name or 'Untitled')
        if dialog.exec_():
            return dialog.selectedFiles()[0]
        return None

    def getScene(self, width, height):
        """
        Create and return an empty scene.
        :param width: the width of the scene rect.
        :param height: the height of the scene rect
        :return: the initialized GraphicScene.
        :rtype: DiagramScene
        """
        scene = DiagramScene(self)
        scene.setSceneRect(QRectF(-width / 2, -height / 2, width, height))
        scene.setItemIndexMethod(DiagramScene.NoIndex)
        connect(scene.nodeInserted, self.onNodeInserted)
        connect(scene.edgeInserted, self.onEdgeInserted)
        connect(scene.modeChanged, self.onModeChanged)
        self.undoGroup.addStack(scene.undoStack)
        return scene

    def getSceneFromGrapholFile(self, filepath):
        """
        Create a new scene by loading the given graphol file.
        :param filepath: the path of the file to be loaded.
        :return: the initialized GraphicScene, or None if the load fails.
        :rtype: DiagramScene
        """
        file = QFile(filepath)

        try:

            if not file.open(QIODevice.ReadOnly):
                raise IOError('file not found: {0}'.format(filepath))

            document = QDomDocument()
            if not document.setContent(file):
                raise ParseError('could not initialized DOM document')

            root = document.documentElement()

            # read graph initialization data
            graph = root.firstChildElement('graph')
            w = int(graph.attribute('width', self.settings.value('scene/size', '5000', str)))
            h = int(graph.attribute('height', self.settings.value('scene/size', '5000', str)))

            # create the scene
            scene = self.getScene(width=w, height=h)
            scene.document.filepath = filepath
            scene.document.edited = os.path.getmtime(filepath)

            # add the nodes
            nodes_from_graphol = graph.elementsByTagName('node')
            for i in range(nodes_from_graphol.count()):
                E = nodes_from_graphol.at(i).toElement()
                C = __mapping__[E.attribute('type')]
                node = C.fromGraphol(scene=scene, E=E)
                scene.addItem(node)
                scene.uniqueID.update(node.id)

            # add the edges
            edges_from_graphol = graph.elementsByTagName('edge')
            for i in range(edges_from_graphol.count()):
                E = edges_from_graphol.at(i).toElement()
                C = __mapping__[E.attribute('type')]
                edge = C.fromGraphol(scene=scene, E=E)
                scene.addItem(edge)
                scene.uniqueID.update(edge.id)

        except Exception as e:
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowIcon(QIcon(':/images/grapholed'))
            box.setWindowTitle('Load FAILED')
            box.setText('Could not open Graphol document: {0}!'.format(filepath))
            # format the traceback so it prints nice
            most_recent_calls = traceback.format_tb(sys.exc_info()[2])
            most_recent_calls = [x.strip().replace('\n', '') for x in most_recent_calls]
            # set the traceback as detailed text so it won't occupy too much space in the dialog box
            box.setDetailedText('{0}: {1}\n\n{2}'.format(e.__class__.__name__, str(e), '\n'.join(most_recent_calls)))
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return None
        else:
            self.documentLoaded.emit(scene)
            return scene
        finally:
            file.close()

    @staticmethod
    def saveSceneToGrapholFile(scene, filepath):
        """
        Save the given scene to the corresponding given filepath.
        :param scene: the scene to be saved.
        :param filepath: the filepath where to save the scene.
        :return: True if the save has been performed, False otherwise.
        """
        # save the file in a hidden file inside the grapholed home: if the save successfully
        # complete, move the file on the given filepath (in this way if an exception is raised
        # while exporting the scene, we won't lose previously saved data)
        tmpPath = getPath('@home/.{0}'.format(os.path.basename(os.path.normpath(filepath))))
        tmpFile = QFile(tmpPath)

        try:
            if not tmpFile.open(QIODevice.WriteOnly|QIODevice.Truncate|QIODevice.Text):
                raise IOError('could not create temporary file {0}'.format(tmpPath))
            stream = QTextStream(tmpFile)
            document = scene.toGraphol()
            document.save(stream, 2)
            tmpFile.close()
            if os.path.isfile(filepath):
                os.remove(filepath)
            os.rename(tmpPath, filepath)
        except Exception:
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowIcon(QIcon(':/images/grapholed'))
            box.setWindowTitle('Save FAILED')
            box.setText('Could not export diagram!')
            box.setDetailedText(traceback.format_exc())
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return False
        else:
            return True
        finally:
            if tmpFile.isOpen():
                tmpFile.close()

    def setWindowTitle(self, p_str=None):
        """
        Set the main window title.
        :param p_str: the prefix for the window title
        """
        T = '{0} - {1} {2}'.format(p_str, __appname__, __version__) if p_str else '{0} {1}'.format(__appname__, __version__)
        super().setWindowTitle(T)

    def updateRecentDocumentActions(self):
        """
        Update the recent document action list.
        """
        documents = self.settings.value('recentDocumentList', DistinctList())
        numRecentDocuments = min(len(documents), MainWindow.MaxRecentDocuments)

        for i in range(numRecentDocuments):
            filename = '&{0} {1}'.format(i + 1, os.path.basename(os.path.normpath(documents[i])))
            self.actionsOpenRecentDocument[i].setText(filename)
            self.actionsOpenRecentDocument[i].setData(documents[i])
            self.actionsOpenRecentDocument[i].setVisible(True)

        # turn off actions that we don't need
        for i in range(numRecentDocuments, MainWindow.MaxRecentDocuments):
            self.actionsOpenRecentDocument[i].setVisible(False)

        # show the separator only if we got at least one recent document
        self.recentDocumentSeparator.setVisible(numRecentDocuments > 0)