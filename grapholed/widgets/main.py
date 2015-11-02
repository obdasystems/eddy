# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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

from PyQt5.QtCore import Qt, QRectF, pyqtSlot, QSettings, QFile, QIODevice
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget, QAction, QStatusBar, QMessageBox
from PyQt5.QtWidgets import QUndoGroup
from PyQt5.QtXml import QDomDocument

from grapholed import __version__, __appname__, __organization__
from grapholed.datatypes import FileType, DiagramMode
from grapholed.dialogs import AboutDialog, OpenFileDialog, PreferencesDialog
from grapholed.exceptions import ParseError
from grapholed.functions import getPath, shaded, connect, disconnect
from grapholed.items import __mapping__, ItemType
from grapholed.widgets.dock import DockWidget, Navigator, Overview, Palette
from grapholed.widgets.mdi import MdiArea, MdiSubWindow
from grapholed.widgets.scene import DiagramScene
from grapholed.widgets.view import MainView
from grapholed.widgets.toolbar import ZoomControl


class MainWindow(QMainWindow):
    """
    This class implements the Grapholed Main Window.
    """
    MinWidth = 1024
    MinHeight = 600

    def __init__(self):
        """
        Initialize the application Main Window.
        """
        super().__init__()
        self.settings = QSettings(__organization__, __appname__)
        self.undoGroup = QUndoGroup()

        ########################################### AUXILIARY WIDGETS ##################################################

        self.zoomctl = ZoomControl()

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

        self.actionOpenDocument = QAction('Open...', self)
        self.actionOpenDocument.setIcon(self.iconOpen)
        self.actionOpenDocument.setShortcut(QKeySequence.Open)
        self.actionOpenDocument.setStatusTip('Open a diagram')

        self.actionSaveDocument = QAction('Save', self)
        self.actionSaveDocument.setIcon(self.iconSave)
        self.actionSaveDocument.setShortcut(QKeySequence.Save)
        self.actionSaveDocument.setStatusTip('Save the current document')
        self.actionSaveDocument.setEnabled(False)

        self.actionSaveDocumentAs = QAction('Save As...', self)
        self.actionSaveDocumentAs.setIcon(self.iconSaveAs)
        self.actionSaveDocumentAs.setShortcut(QKeySequence.SaveAs)
        self.actionSaveDocumentAs.setStatusTip('Save the active diagram')
        self.actionSaveDocumentAs.setEnabled(False)

        self.actionImportDocument = QAction('Import...', self)
        self.actionImportDocument.setStatusTip('Import a document')

        self.actionExportDocument = QAction('Export...', self)
        self.actionExportDocument.setStatusTip('Export the active diagram')
        self.actionExportDocument.setEnabled(False)

        self.actionPrintDocument = QAction('Print...', self)
        self.actionPrintDocument.setIcon(self.iconPrint)
        self.actionPrintDocument.setStatusTip('Print the active diagram')
        self.actionPrintDocument.setEnabled(False)

        self.actionCloseActiveSubWindow = QAction('Close', self)
        self.actionCloseActiveSubWindow.setIcon(self.iconClose)
        self.actionCloseActiveSubWindow.setShortcut(QKeySequence.Close)
        self.actionCloseActiveSubWindow.setStatusTip('Close the active diagram')
        self.actionCloseActiveSubWindow.setEnabled(False)

        self.actionOpenPreferences = QAction('Preferences', self)
        self.actionOpenPreferences.setShortcut(QKeySequence.Preferences)
        self.actionOpenPreferences.setStatusTip('Open {0} preferences'.format(__appname__))

        if not sys.platform.startswith('darwin'):
            self.actionOpenPreferences.setIcon(self.iconPreferences)

        self.actionQuit = QAction('Quit', self)
        self.actionQuit.setStatusTip('Quit {0}'.format(__appname__))
        self.actionQuit.setShortcut(QKeySequence.Quit)

        if not sys.platform.startswith('darwin'):
            self.actionQuit.setIcon(self.iconQuit)

        self.actionSnapToGrid = QAction('Snap to grid', self)
        self.actionSnapToGrid.setIcon(self.iconGrid)
        self.actionSnapToGrid.setStatusTip('Snap diagram elements to the grid')
        self.actionSnapToGrid.setCheckable(True)
        self.actionSnapToGrid.setChecked(self.settings.value('scene/snap_to_grid', False, bool))
        
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

        self.actionAbout = QAction('About {0}'.format(__appname__), self)
        self.actionAbout.setShortcut(QKeySequence.HelpContents)

        self.actionSapienzaWebOpen = QAction('DIAG - Sapienza university', self)
        self.actionSapienzaWebOpen.setIcon(self.iconLink)
        
        self.actionGrapholWebOpen = QAction('Graphol homepage', self)
        self.actionGrapholWebOpen.setIcon(self.iconLink)

        self.navigatorDock.toggleViewAction().setIcon(self.iconZoom)
        self.overviewDock.toggleViewAction().setIcon(self.iconZoom)
        self.paletteDock.toggleViewAction().setIcon(self.iconPalette)
        
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

        self.documentToolBar = self.addToolBar("Document")
        self.documentToolBar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.documentToolBar.setFloatable(False)

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

        connect(self.actionNewDocument.triggered, self.doNewDocument)
        connect(self.actionOpenDocument.triggered, self.doOpenDocument)
        connect(self.actionSaveDocument.triggered, self.doSaveDocument)
        connect(self.actionSaveDocumentAs.triggered, self.doSaveDocumentAs)
        connect(self.actionImportDocument.triggered, self.doImportDocument)
        connect(self.actionExportDocument.triggered, self.doExportDocument)
        connect(self.actionPrintDocument.triggered, self.doPrintDocument)
        connect(self.actionCloseActiveSubWindow.triggered, lambda: self.mdiArea.activeSubWindow().close())
        connect(self.actionOpenPreferences.triggered, self.doOpenPreferences)
        connect(self.actionQuit.triggered, self.close)
        connect(self.actionSnapToGrid.triggered, self.doSnapToGrid)
        connect(self.actionAbout.triggered, self.doAbout)
        connect(self.actionSapienzaWebOpen.triggered, lambda: webbrowser.open('http://www.dis.uniroma1.it/en'))
        connect(self.actionGrapholWebOpen.triggered, lambda: webbrowser.open('http://www.dis.uniroma1.it/~graphol/'))
        connect(self.mdiArea.subWindowActivated, self.onSubWindowActivated)
        connect(self.palette_.buttonClicked[int], self.onPaletteButtonClicked)
        connect(self.undoGroup.cleanChanged, self.onUndoGroupCleanChanged)

    ####################################################################################################################
    #                                                                                                                  #
    #   ACTION HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def doAbout(self):
        """
        Display the about dialog.
        """
        about = AboutDialog()
        about.exec_()

    @pyqtSlot()
    def doNewDocument(self):
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
    def doOpenDocument(self):
        """
        Open a document.
        """
        opendialog = OpenFileDialog(getPath('~'))
        opendialog.setNameFilters([FileType.graphol.value])
        if opendialog.exec_():

            filepath = opendialog.selectedFiles()[0]
            # if the file is already opened just focus the subwindow
            for subwindow in self.mdiArea.subWindowList():
                scene = subwindow.widget().scene()
                if scene.document.filepath and scene.document.filepath == filepath:
                    self.mdiArea.setActiveSubWindow(subwindow)
                    self.mdiArea.update()
                    return

            scene = self.getSceneFromGrapholFile(filepath)

            if scene:
                mainview = self.getMainView(scene)
                subwindow = self.getMDISubWindow(mainview)
                subwindow.showMaximized()
                self.mdiArea.setActiveSubWindow(subwindow)
                self.mdiArea.update()

    @pyqtSlot()
    def doSaveDocument(self):
        """
        Save the currently open graphol document.
        """
        subwindow = self.mdiArea.currentSubWindow()
        if subwindow:
            subwindow.saveScene()

    @pyqtSlot()
    def doSaveDocumentAs(self):
        """
        Save the currently open graphol document (enforcing a new name).
        """
        subwindow = self.mdiArea.currentSubWindow()
        if subwindow:
            subwindow.saveSceneAs()

    @pyqtSlot()
    def doImportDocument(self):
        """
        Import a document from a different file format.
        """
        pass

    @pyqtSlot()
    def doExportDocument(self):
        """
        Export the currently open graphol document.
        """
        subwindow = self.mdiArea.currentSubWindow()
        if subwindow:
            subwindow.exportScene()

    @pyqtSlot()
    def doPrintDocument(self):
        """
        Print the currently open graphol document.
        """
        subwindow = self.mdiArea.currentSubWindow()
        if subwindow:
            subwindow.printScene()

    @pyqtSlot()
    def doOpenPreferences(self):
        """
        Open the preferences dialog.
        """
        preferences = PreferencesDialog(self.centralWidget())
        preferences.exec_()

    @pyqtSlot()
    def doSnapToGrid(self):
        """
        Toggle snap to grid setting.
        """
        self.settings.setValue('scene/snap_to_grid', self.actionSnapToGrid.isChecked())
        subwindow = self.mdiArea.currentSubWindow()
        if subwindow:
            subwindow.widget().scene().update()

    ####################################################################################################################
    #                                                                                                                  #
    #   SIGNAL HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot('QMdiSubWindow')
    def onDocumentSaved(self, subwindow):
        """
        Executed when the document in a subwindow is saved.
        :param subwindow: the subwindow containing the saved document.
        """
        mainview = subwindow.widget()
        scene = mainview.scene()
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

            connect(self.actionItemCut.triggered, scene.doItemCut)
            connect(self.actionItemCopy.triggered, scene.doItemCopy)
            connect(self.actionItemPaste.triggered, scene.doItemPaste)
            connect(self.actionItemDelete.triggered, scene.doItemDelete)
            connect(self.actionBringToFront.triggered, scene.doBringToFront)
            connect(self.actionSendToBack.triggered, scene.doSendToBack)
            connect(self.actionSelectAll.triggered, scene.doSelectAll)
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
        for subwindow in self.mdiArea.subWindowList():
            subwindow.close()

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
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def getMainView(self, scene):
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
        scene = mainview.scene()
        connect(scene.undoStack.cleanChanged, subwindow.onUndoStackCleanChanged)
        connect(subwindow.documentSaved, self.onDocumentSaved)

        if scene.document.filepath:
            # set the title in case the scene we are rendering
            # is saved already somewhere (used when opening documents)
            subwindow.setWindowTitle(scene.document.name)

        return subwindow

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
        if not file.open(QIODevice.ReadOnly):
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowIcon(QIcon(':/images/grapholed'))
            box.setWindowTitle('WARNING')
            box.setText('Unable to open Graphol document {0}!'.format(filepath))
            box.setDetailedText(file.errorString())
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return None

        try:

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
            box.setWindowTitle('WARNING')
            box.setText('Unable to parse Graphol document from {0}!'.format(filepath))
            # format the traceback so it prints nice
            most_recent_calls = traceback.format_tb(sys.exc_info()[2])
            most_recent_calls = [x.strip().replace('\n', '') for x in most_recent_calls]
            # set the traceback as detailed text so it won't occupy too much space in the dialog box
            box.setDetailedText('{0}: {1}\n\n{2}'.format(e.__class__.__name__, str(e), '\n'.join(most_recent_calls)))
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return None
        else:
            return scene
        finally:
            file.close()

    def setWindowTitle(self, p_str=None):
        """
        Set the main window title.
        :param p_str: the prefix for the window title
        """
        T = '{0} {1}'.format(__appname__, __version__) if not p_str else '{0} - {1} {2}'.format(p_str, __appname__, __version__)
        super().setWindowTitle(T)