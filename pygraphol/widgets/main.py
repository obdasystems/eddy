# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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

import sys
import traceback
import webbrowser

from PyQt5.QtCore import Qt, QSize, QRectF, pyqtSlot, QSettings, QFile, QIODevice, QPointF
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget, QAction, QStatusBar, QButtonGroup, QHBoxLayout
from PyQt5.QtWidgets import QToolButton, QWidget, QUndoGroup, QMessageBox
from PyQt5.QtXml import QDomDocument

from pygraphol import __version__ as version, __appname__ as appname
from pygraphol import __organization__ as organization
from pygraphol.datatypes import FileType
from pygraphol.dialogs import OpenFileDialog
from pygraphol.dialogs import PreferencesDialog
from pygraphol.exceptions import ParseError
from pygraphol.functions import getPath, shaded
from pygraphol.items.nodes import Node
from pygraphol.items.edges import Edge
from pygraphol.items import __mapping__
from pygraphol.items import *
from pygraphol.widgets import MdiArea, MdiSubWindow
from pygraphol.widgets import GraphicsScene
from pygraphol.widgets import Palette, Pane
from pygraphol.widgets import MainView, Navigator
from pygraphol.widgets import ZoomControl


class MainWindow(QMainWindow):
    """
    This class implements the pyGraphol Main Window.
    """
    MinWidth = 1024
    MinHeight = 600

    def __init__(self):
        """
        Initialize the application Main Window.
        """
        super().__init__()
        self.settings = QSettings(organization, appname)
        self.undoGroup = QUndoGroup()
        self.undoGroup.cleanChanged.connect(self.handleUndoGroupChanged)

        ############################################ EXTRA WIDGETS #####################################################

        self.nav = Navigator()
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
        self.iconPreferences = getIcon(':/icons/preferences')
        self.iconPrint = getIcon(':/icons/print')
        self.iconQuit = getIcon(':/icons/quit')
        self.iconRedo = getIcon(':/icons/redo')
        self.iconSave = getIcon(':/icons/save')
        self.iconSaveAs = getIcon(':/icons/save')
        self.iconSelectAll = getIcon(':/icons/select-all')
        self.iconSendToBack = getIcon(':/icons/send-to-back')
        self.iconUndo = getIcon(':/icons/undo')

        ################################################ ACTIONS #######################################################

        self.actionNewDocument = QAction('New', self)
        self.actionNewDocument.setIcon(self.iconNew)
        self.actionNewDocument.setShortcut(QKeySequence.New)
        self.actionNewDocument.setStatusTip('Create a new document')
        self.actionNewDocument.triggered.connect(self.handleNewDocument)

        self.actionOpenDocument = QAction('Open...', self)
        self.actionOpenDocument.setIcon(self.iconOpen)
        self.actionOpenDocument.setShortcut(QKeySequence.Open)
        self.actionOpenDocument.setStatusTip('Open a document')
        self.actionOpenDocument.triggered.connect(self.handleOpenDocument)

        self.actionSaveDocument = QAction('Save', self)
        self.actionSaveDocument.setIcon(self.iconSave)
        self.actionSaveDocument.setShortcut(QKeySequence.Save)
        self.actionSaveDocument.setStatusTip('Save the current document')
        self.actionSaveDocument.triggered.connect(self.handleSaveDocument)
        self.actionSaveDocument.setEnabled(False)

        self.actionSaveDocumentAs = QAction('Save As...', self)
        self.actionSaveDocumentAs.setIcon(self.iconSaveAs)
        self.actionSaveDocumentAs.setShortcut(QKeySequence.SaveAs)
        self.actionSaveDocumentAs.setStatusTip('Save the active document')
        self.actionSaveDocumentAs.triggered.connect(self.handleSaveDocumentAs)
        self.actionSaveDocumentAs.setEnabled(False)

        self.actionImportDocument = QAction('Import...', self)
        self.actionImportDocument.setStatusTip('Import a document')
        self.actionImportDocument.triggered.connect(self.handleImportDocument)

        self.actionExportDocument = QAction('Export...', self)
        self.actionExportDocument.setStatusTip('Export the active document')
        self.actionExportDocument.triggered.connect(self.handleExportDocument)
        self.actionExportDocument.setEnabled(False)

        self.actionPrintDocument = QAction('Print...', self)
        self.actionPrintDocument.setIcon(self.iconPrint)
        self.actionPrintDocument.setStatusTip('Print the active document')
        self.actionPrintDocument.triggered.connect(self.handlePrintDocument)
        self.actionPrintDocument.setEnabled(False)

        self.actionCloseActiveSubWindow = QAction('Close', self)
        self.actionCloseActiveSubWindow.setIcon(self.iconClose)
        self.actionCloseActiveSubWindow.setShortcut(QKeySequence.Close)
        self.actionCloseActiveSubWindow.setStatusTip('Close the active document')
        self.actionCloseActiveSubWindow.triggered.connect(lambda: self.mdiArea.activeSubWindow().close())
        self.actionCloseActiveSubWindow.setEnabled(False)

        self.actionOpenPreferences = QAction('Preferences', self)
        self.actionOpenPreferences.setIcon(self.iconPreferences)
        self.actionOpenPreferences.setShortcut(QKeySequence.Preferences)
        self.actionOpenPreferences.setStatusTip('Open application preferences dialog')
        self.actionOpenPreferences.triggered.connect(self.handleOpenPreferences)

        self.actionQuit = QAction('Quit', self)
        self.actionQuit.setIcon(self.iconQuit)
        self.actionQuit.setStatusTip('Quit pyGraphol')
        self.actionQuit.setShortcut(QKeySequence.Quit)
        self.actionQuit.triggered.connect(self.close)

        self.actionSnapToGrid = QAction('Snap to grid', self)
        self.actionSnapToGrid.setIcon(self.iconGrid)
        self.actionSnapToGrid.setStatusTip('Snap scene elements to the grid')
        self.actionSnapToGrid.setCheckable(True)
        self.actionSnapToGrid.setChecked(self.settings.value('scene/snap_to_grid', False, bool))
        self.actionSnapToGrid.triggered.connect(self.handleSnapToGrid)

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
        self.actionSelectAll.setStatusTip('Send all items in the active scene')
        self.actionSelectAll.setEnabled(False)

        self.actionUndo = self.undoGroup.createUndoAction(self)
        self.actionUndo.setIcon(self.iconUndo)
        self.actionUndo.setShortcut(QKeySequence.Undo)

        self.actionRedo = self.undoGroup.createRedoAction(self)
        self.actionRedo.setIcon(self.iconRedo)
        self.actionRedo.setShortcut(QKeySequence.Redo)

        self.actionSapienzaWebOpen = QAction('DIAG - Sapienza university', self)
        self.actionSapienzaWebOpen.setIcon(self.iconLink)
        self.actionSapienzaWebOpen.triggered.connect(lambda: webbrowser.open('http://www.dis.uniroma1.it/en'))

        self.actionGrapholWebOpen = QAction('Graphol homepage', self)
        self.actionGrapholWebOpen.setIcon(self.iconLink)
        self.actionGrapholWebOpen.triggered.connect(lambda: webbrowser.open('http://www.dis.uniroma1.it/~graphol/'))

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

        self.menuHelp = self.menuBar().addMenu("&Help")
        self.menuHelp.addAction(self.actionSapienzaWebOpen)
        self.menuHelp.addAction(self.actionGrapholWebOpen)

        ############################################### STATUS BAR #####################################################

        statusbar = QStatusBar(self)
        statusbar.setSizeGripEnabled(False)
        self.setStatusBar(statusbar)

        ################################################ TOOLBAR #######################################################

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

        ################################################ PALETTE #######################################################

        self.paletteItems = dict()
        self.paletteNodes = dict()
        self.paletteEdges = dict()

        self.pGroup = QButtonGroup()
        self.pGroup.setExclusive(False)
        self.pGroup.buttonClicked[int].connect(self.handleToolBoxButtonClicked)

        self.cGroup = QButtonGroup()
        self.cGroup.setExclusive(False)
        self.cGroup.buttonClicked[int].connect(self.handleToolBoxButtonClicked)

        self.eGroup = QButtonGroup()
        self.eGroup.setExclusive(False)
        self.eGroup.buttonClicked[int].connect(self.handleToolBoxButtonClicked)

        nodes = [self.paletteItems, self.paletteNodes]
        edges = [self.paletteItems, self.paletteEdges]

        def _w(item, bgroup, groups):
            """
            Create a cell widget with the item shape rendered inside.
            :type item: class
            :type bgroup: QButtonGroup
            :type groups: list
            :param item: the class implementing the item.
            :param bgroup: the button group this widget is associated.
            :param groups: an iterable of dictionaries where to map the generated QToolButton using the item class type.
            :rtype: QToolButton
            """
            button = QToolButton()
            if not isinstance(item.image, str):
                icon = item.image(w=60, h=44)
            else:
                icon = item.image

            button.setIcon(QIcon(icon))
            button.setIconSize(QSize(60, 44))
            button.setCheckable(True)
            button.setContentsMargins(0, 0, 0, 0)
            button.setProperty('item', item)
            bgroup.addButton(button, item.type)
            for collection in groups:
                collection[item.type] = button
            return button

        pItem = Palette.Item('Predicate nodes', collapsed=False)
        pItem.addWidget(_w(ConceptNode, self.pGroup, nodes))
        pItem.addWidget(_w(RoleNode, self.pGroup, nodes))
        pItem.addWidget(_w(ValueDomainNode, self.pGroup, nodes))
        pItem.addWidget(_w(IndividualNode, self.pGroup, nodes))
        pItem.addWidget(_w(ValueRestrictionNode, self.pGroup, nodes))
        pItem.addWidget(_w(AttributeNode, self.pGroup, nodes))

        cItem = Palette.Item('Constructor nodes', collapsed=False)
        cItem.addWidget(_w(DomainRestrictionNode, self.cGroup, nodes))
        cItem.addWidget(_w(RangeRestrictionNode, self.cGroup, nodes))
        cItem.addWidget(_w(UnionNode, self.cGroup, nodes))
        cItem.addWidget(_w(EnumerationNode, self.cGroup, nodes))
        cItem.addWidget(_w(ComplementNode, self.cGroup, nodes))
        cItem.addWidget(_w(RoleChainNode, self.cGroup, nodes))
        cItem.addWidget(_w(IntersectionNode, self.cGroup, nodes))
        cItem.addWidget(_w(RoleInverseNode, self.cGroup, nodes))
        cItem.addWidget(_w(DatatypeRestrictionNode, self.cGroup, nodes))
        cItem.addWidget(_w(DisjointUnionNode, self.cGroup, nodes))
        cItem.addWidget(_w(PropertyAssertionNode, self.cGroup, nodes))

        eItem = Palette.Item('Edges', collapsed=False)
        eItem.addWidget(_w(InclusionEdge, self.eGroup, edges))
        eItem.addWidget(_w(InputEdge, self.eGroup, edges))
        eItem.addWidget(_w(InstanceOfEdge, self.eGroup, edges))

        self.palette = Palette()
        self.palette.addItem(pItem)
        self.palette.addItem(cItem)
        self.palette.addItem(eItem)

        ############################################### MDI AREA #######################################################

        self.mdiArea = MdiArea(self.nav)
        self.mdiArea.subWindowActivated.connect(self.handleSubWindowActivated)

        ############################################## LEFT PANE #######################################################

        self.leftPane = Pane(alignment=Qt.AlignLeft|Qt.AlignTop)
        self.leftPane.addWidget(self.palette)

        ############################################## RIGHT PANE ######################################################

        self.rightPane = Pane(alignment=Qt.AlignRight|Qt.AlignTop)
        self.rightPane.addWidget(self.nav)

        ############################################ CENTRAL WIDGET ####################################################

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(self.leftPane)
        layout.addWidget(self.mdiArea)
        layout.addWidget(self.rightPane)
        self.setCentralWidget(widget)
        self.setWindowTitle()

        ############################################### GEOMETRY #######################################################

        screen = QDesktopWidget().screenGeometry()
        posX = (screen.width() - MainWindow.MinWidth) / 2
        posY = (screen.height() - MainWindow.MinHeight) / 2
        self.setGeometry(posX, posY, MainWindow.MinWidth, MainWindow.MinHeight)
        self.setMinimumSize(MainWindow.MinWidth, MainWindow.MinHeight)

    ####################################################################################################################
    #                                                                                                                  #
    #   ACTION HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def handleNewDocument(self):
        """
        Create a new empty document and add it to the MDI Area.
        """
        scene = self.getScene()
        mainview = self.getMainView(scene)
        subwindow = self.getMDISubWindow(mainview)
        subwindow.showMaximized()
        self.mdiArea.setActiveSubWindow(subwindow)
        self.mdiArea.update()

    def handleOpenDocument(self):
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

    def handleSaveDocument(self):
        """
        Save the currently open graphol document.
        """
        subwindow = self.mdiArea.currentSubWindow()
        if subwindow:
            subwindow.saveScene()

    def handleSaveDocumentAs(self):
        """
        Save the currently open graphol document (enforcing a new name).
        """
        subwindow = self.mdiArea.currentSubWindow()
        if subwindow:
            subwindow.saveSceneAs()

    def handleImportDocument(self):
        """
        Import a document from a different file format.
        """
        pass

    def handleExportDocument(self):
        """
        Export the currently open graphol document.
        """
        subwindow = self.mdiArea.currentSubWindow()
        if subwindow:
            subwindow.exportScene()

    def handlePrintDocument(self):
        """
        Print the currently open graphol document.
        """
        subwindow = self.mdiArea.currentSubWindow()
        if subwindow:
            subwindow.printScene()

    def handleOpenPreferences(self):
        """
        Open the preferences dialog.
        """
        preferences = PreferencesDialog(self.centralWidget())
        preferences.exec_()

    def handleSnapToGrid(self):
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
    def handleDocumentSaved(self, subwindow):
        """
        Executed when the document in a subwindow is saved.
        :param subwindow: the subwindow containing the saved document.
        """
        mainview = subwindow.widget()
        scene = mainview.scene()
        self.setWindowTitle(scene.document.name)

    @pyqtSlot(Edge)
    def handleEdgeInsertEnd(self, edge):
        """
        Triggered after a edge insertion process ends.
        :param edge: the inserted edge.
        """
        self.paletteItems[edge.type].setChecked(False)

    @pyqtSlot(Node)
    def handleNodeInsertEnd(self, node):
        """
        Triggered after a node insertion process ends.
        :param node:the inserted node.
        """
        self.paletteItems[node.type].setChecked(False)

    @pyqtSlot(int)
    def handleSceneModeChanged(self, mode):
        """
        Triggered when the scene operation mode changes.
        :param mode: the scene operation mode.
        """
        if mode == GraphicsScene.MoveItem:
            # if we are moving items clear the palette selection
            for btn in self.paletteItems.values():
                btn.setChecked(False)

    @pyqtSlot(int)
    def handleToolBoxButtonClicked(self, button_id):
        """
        Executed whenever a node QToolButton in a QButtonGroup is clicked.
        :param button_id: the button id.
        """
        mainview = self.mdiArea.activeView
        if not mainview:
            for btn in self.paletteItems.values():
                btn.setChecked(False)
        else:
            currentscene = mainview.scene()
            currentscene.clearSelection()
            button = self.paletteItems[button_id]

            for btn in self.paletteItems.values():
                if btn != button:
                    btn.setChecked(False)

            if not button.isChecked():
                currentscene.setMode(GraphicsScene.MoveItem)
            else:
                if button_id in self.paletteNodes:
                    currentscene.setMode(GraphicsScene.InsertNode, button.property('item'))
                elif button_id in self.paletteEdges:
                    currentscene.setMode(GraphicsScene.InsertEdge, button.property('item'))

    @pyqtSlot('QMdiSubWindow')
    def handleSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :param subwindow: the subwindow which got the focus (0 if there is no subwindow).
        """
        if subwindow:

            self.actionSaveDocumentAs.setEnabled(True)
            self.actionExportDocument.setEnabled(True)
            self.actionPrintDocument.setEnabled(True)
            self.actionSelectAll.setEnabled(True)
            self.actionCloseActiveSubWindow.setEnabled(True)

            mainview = subwindow.widget()
            scene = mainview.scene()

            try:

                # detach signals from the old view/scene: will raise an exception if the scene got closed
                # since the action reference has been destroyed and we don't need to detach anything
                self.actionItemCut.disconnect()
                self.actionItemCopy.disconnect()
                self.actionItemPaste.disconnect()
                self.actionItemDelete.triggered.disconnect()
                self.actionBringToFront.triggered.disconnect()
                self.actionSendToBack.triggered.disconnect()
                self.actionSelectAll.triggered.disconnect()

                self.zoomctl.signalScaleChanged.disconnect()

                mainview.zoomChanged.disconnect()

            except (RuntimeError, TypeError):

                # just do nothing since we do not have the reference to the subwindow anymore so
                # we can't detach signals (in case the scene has already a reference somewhere else the
                # signal won't be detached, but it won't cause any trouble since the scene can't be focused)
                pass

            finally:

                # attach signals to the new active view/scene
                self.actionItemCut.triggered.connect(scene.handleItemCut)
                self.actionItemCopy.triggered.connect(scene.handleItemCopy)
                self.actionItemPaste.triggered.connect(scene.handleItemPaste)
                self.actionItemDelete.triggered.connect(scene.handleItemDelete)
                self.actionBringToFront.triggered.connect(scene.handleBringToFront)
                self.actionSendToBack.triggered.connect(scene.handleSendToBack)
                self.actionSelectAll.triggered.connect(scene.handleSelectAll)

                self.zoomctl.setEnabled(False)
                self.zoomctl.setZoomLevel(self.zoomctl.index(mainview.zoom))
                self.zoomctl.signalScaleChanged.connect(mainview.handleScaleChanged)
                self.zoomctl.setEnabled(True)

                mainview.zoomChanged.connect(self.zoomctl.handleMainViewZoomChanged)

                # update scene specific actions
                scene.updateActions()

            self.setWindowTitle(scene.document.name)

        else:

            # disable the stuff below only if all the subwindows have been closed: this if clause
            # make sure to keep those things activated in case the MainWindow lost just the focus
            if not len(self.mdiArea.subWindowList()):
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
                self.setWindowTitle()

    @pyqtSlot(bool)
    def handleUndoGroupChanged(self, clean):
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
        view.centerOn(scene.sceneRect().width() / 2, scene.sceneRect().height() / 2)
        view.setDragMode(MainView.RubberBandDrag)
        return view

    def getMDISubWindow(self, mainview):
        """
        Create a MdiSubWindow rendering the given main view to be added with the MDI area.
        :param mainview: the mainview to be rendered in the subwindow.
        :rtype: MdiSubWindow
        """
        subwindow = self.mdiArea.addSubWindow(MdiSubWindow(mainview))
        subwindow.widget().scene().undoStack.cleanChanged.connect(subwindow.handleUndoStackCleanChanged)
        subwindow.signalDocumentSaved.connect(self.handleDocumentSaved)
        if subwindow.widget().scene().document.filepath:
            # set the title in case the scene we are rendering is saved already somewhere (used when opening documents)
            subwindow.setWindowTitle(subwindow.widget().scene().document.name)
        return subwindow

    def getScene(self):
        """
        Create and return an empty scene.
        :return: the initialized GraphicScene.
        :rtype: GraphicsScene
        """
        # get the size of the document from the preferences
        size = self.settings.value('scene/size', 5000, int)

        # create the new scene
        scene = GraphicsScene(self)
        scene.setSceneRect(QRectF(0, 0, size, size))
        scene.nodeInsertEnd.connect(self.handleNodeInsertEnd)
        scene.edgeInsertEnd.connect(self.handleEdgeInsertEnd)
        scene.modeChanged.connect(self.handleSceneModeChanged)

        # connect the undostack to the undogroup
        self.undoGroup.addStack(scene.undoStack)

        return scene

    def getSceneFromGrapholFile(self, filepath):
        """
        Create a new scene by loading the given graphol file.
        :param filepath: the path of the file to be loaded.
        :return: the initialized GraphicScene, or None if the load fails.
        :rtype: GraphicsScene
        """
        file = QFile(filepath)
        if not file.open(QIODevice.ReadOnly):
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowTitle('WARNING')
            box.setText('Unable to open Graphol document %s!' % filepath)
            box.setDetailedText(file.errorString())
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return None

        try:

            document = QDomDocument()
            if not document.setContent(file):
                raise ParseError('could not initialized DOM document')

            root = document.documentElement()

            graph = root.firstChildElement('graph')
            w = int(graph.attribute('width', '5000'))
            h = int(graph.attribute('height', '5000'))

            # create the scene
            scene = GraphicsScene(self)
            scene.document.filepath = filepath
            scene.setSceneRect(QRectF(0, 0, w, h))
            scene.nodeInsertEnd.connect(self.handleNodeInsertEnd)
            scene.edgeInsertEnd.connect(self.handleEdgeInsertEnd)
            scene.modeChanged.connect(self.handleSceneModeChanged)

            # add the nodes
            xmlnodes = graph.elementsByTagName('node')
            for i in range(0, xmlnodes.count()):

                E = xmlnodes.at(i).toElement()
                U = E.elementsByTagName('data:url').at(0).toElement()
                D = E.elementsByTagName('data:description').at(0).toElement()
                G = E.elementsByTagName('shape:geometry').at(0).toElement()
                L = E.elementsByTagName('shape:label').at(0).toElement()

                nid = E.attribute('id')
                ntype = E.attribute('type')

                shapeX = int(G.attribute('x'))
                shapeY = int(G.attribute('y'))
                shapeW = int(G.attribute('width'))
                shapeH = int(G.attribute('height'))

                labelV = L.text()
                labelX = int(L.attribute('x'))
                labelY = int(L.attribute('y'))
                labelW = int(L.attribute('width'))
                labelH = int(L.attribute('height'))

                # create the node: this will set the position of the node matching the center of the shape.
                # the might have been not true when the scene has been exported but we don't record such info
                # in the graphol XML document in order to make the document format indipendent from the tool.
                node = __mapping__[ntype](scene=scene, id=nid, url=U.text(), description=D.text(), width=shapeW, height=shapeH)
                node.shape.setPos(QPointF(shapeX, shapeY))

                # add the node label: the node label position stored in the graphol document is in scene coordinates,
                # and the position matches the center of the bounding rect of the text item: we need to adapt this data
                # to fix our needs (QT uses top left corner as (0,0) position instead of the bounding rect center).
                labelPos = node.shape.mapFromScene(QPointF(labelX, labelY))
                labelPos = QPointF(labelPos.x() - labelW / 2, labelPos.y() - labelH / 2)
                node.shape.setLabelPos(labelPos)
                node.shape.setLabelText(labelV)

                # append the element to the scene
                scene.itemList.append(node)
                scene.addItem(node.shape)

                # adjust the scene node id
                scene.uniqueID.update(nid)

            # add the edges
            xmledges = graph.elementsByTagName('edge')
            for i in range(0, xmledges.count()):

                E = xmledges.at(i).toElement()

                eid = E.attribute('id')
                etype = E.attribute('type')

                # get source an target node of this edge
                source = scene.node(E.attribute('source'))
                target = scene.node(E.attribute('target'))

                points = []

                # extract all the breakpoints from the edge children
                xmlchildren = E.elementsByTagName('line:point')
                for j in range(0, xmlchildren.count()):
                    P = xmlchildren.at(j).toElement()
                    points.append(QPointF(int(P.attribute('x')), int(P.attribute('y'))))

                # remove the first and last breakpoints since we handle the anchors differently
                sourceP = points[0]
                targetP = points[-1]
                breakpoints = points[1:-1]

                # create the edge
                edge = __mapping__[etype](scene=scene, source=source, target=target, breakpoints=breakpoints, id=eid)
                edge.source.shape.setAnchor(edge.shape, sourceP)
                edge.target.shape.setAnchor(edge.shape, targetP)
                edge.shape.updateEdge()

                # map the edge over the source and target nodes
                edge.source.edges.append(edge)
                edge.target.edges.append(edge)

                # append the element to the scene
                scene.itemList.append(edge)
                scene.addItem(edge.shape)

                # adjust the scene edge id
                scene.uniqueID.update(eid)

            # connect the undostack to the undogroup
            self.undoGroup.addStack(scene.undoStack)

        except Exception as e:
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowTitle('WARNING')
            box.setText('Unable to parse Graphol document from %s!' % filepath)
            # format the traceback so it prints nice
            most_recent_calls = traceback.format_tb(sys.exc_info()[2])
            most_recent_calls = [x.strip().replace('\n', '') for x in most_recent_calls]
            # set the traceback as detailed text so it won't occupy too much space in the dialog box
            box.setDetailedText('%s: %s\n\n%s' % (e.__class__.__name__, str(e), '\n'.join(most_recent_calls)))
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
        super().setWindowTitle('%s %s' % (appname, version) if not p_str else '%s - %s %s' % (p_str, appname, version))
