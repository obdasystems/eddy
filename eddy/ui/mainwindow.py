# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import os
import webbrowser

from collections import OrderedDict
from traceback import format_exception

from PyQt5.QtCore import Qt, QSettings, QSizeF, QRectF
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QPainter
from PyQt5.QtGui import QPageSize, QCursor, QBrush, QColor
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QMainWindow, QAction, QStatusBar, QMessageBox
from PyQt5.QtWidgets import QDialog, QMenu, QToolButton, QDockWidget
from PyQt5.QtWidgets import QUndoGroup, QStyle, QGraphicsItem

from eddy import APPNAME, VERSION, BUG_TRACKER, GRAPHOL_HOME, DIAG_HOME

from eddy.core.commands import CommandComposeAxiom, CommandItemsMultiRemove
from eddy.core.commands import CommandEdgeInclusionToggleComplete, CommandRefactor
from eddy.core.commands import CommandItemsTranslate, CommandEdgeSwap
from eddy.core.commands import CommandNodeLabelMove, CommandNodeLabelChange
from eddy.core.commands import CommandNodeOperatorSwitchTo, CommandNodeSetZValue
from eddy.core.commands import CommandNodeSetBrush, CommandEdgeBreakpointRemove
from eddy.core.datatypes import Color, File, DiagramMode, Filetype, Platform
from eddy.core.datatypes import Restriction, Special, XsdDatatype, Identity
from eddy.core.exporters import GrapholExporter
from eddy.core.functions import connect, disconnect, uncapitalize
from eddy.core.functions import expandPath, rCut, snapF
from eddy.core.items import Item, DatatypeRestrictionNode
from eddy.core.items import RoleInverseNode, DisjointUnionNode
from eddy.core.items import UnionNode, EnumerationNode, ComplementNode
from eddy.core.items import RoleChainNode, IntersectionNode
from eddy.core.loaders import GraphmlLoader, GrapholLoader
from eddy.core.utils import Clipboard
from eddy.core.qt import ColoredIcon, Icon

from eddy.ui.dialogs import About, OpenFile, SaveFile
from eddy.ui.dialogs import BusyProgressDialog, PreferencesDialog
from eddy.ui.docks import Overview, Palette, Explorer, Info
from eddy.ui.forms import CardinalityRestrictionForm, ValueRestrictionForm
from eddy.ui.forms import OWLTranslationForm, ValueForm, RenameForm
from eddy.ui.mdi import MdiArea, MdiSubWindow
from eddy.ui.menus import MenuFactory
from eddy.ui.properties import PropertyFactory
from eddy.ui.scene import DiagramScene
from eddy.ui.toolbar import ZoomControl
from eddy.ui.view import MainView


class MainWindow(QMainWindow):
    """
    This class implements Eddy's main window.
    """
    MinHeight = 600
    MinWidth = 1024

    documentLoaded = pyqtSignal('QGraphicsScene')
    documentSaved = pyqtSignal('QGraphicsScene')

    def __init__(self, parent=None):
        """
        Initialize the application main window.
        :type parent: QWidget
        """
        super().__init__(parent)

        platform = Platform.identify()

        self.clipboard = Clipboard(self)
        self.menuFactory = MenuFactory(self)
        self.propertyFactory = PropertyFactory(self)
        self.undogroup = QUndoGroup(self)

        self.abortQuit = False
        self.diagramSize = 5000
        self.recentDocument = []
        self.snapToGrid = False

        ################################################################################################################
        #                                                                                                              #
        #   CREATE MENUS                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        self.menuFile = self.menuBar().addMenu("&File")
        self.menuEdit = self.menuBar().addMenu("&Edit")
        self.menuView = self.menuBar().addMenu("&View")
        self.menuTools = self.menuBar().addMenu("&Tools")
        self.menuHelp = self.menuBar().addMenu("&Help")

        ################################################################################################################
        #                                                                                                              #
        #   CREATE TOOLBARS                                                                                            #
        #                                                                                                              #
        ################################################################################################################

        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.setObjectName('toolbar')

        ################################################################################################################
        #                                                                                                              #
        #   CREATE ICONS                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        self.iconBringToFront = Icon(':/icons/bring-to-front')
        self.iconCenterFocus = Icon(':/icons/center-focus')
        self.iconClose = Icon(':/icons/close')
        self.iconColorFill = Icon(':/icons/color-fill')
        self.iconCopy = Icon(':/icons/copy')
        self.iconCreate = Icon(':/icons/create')
        self.iconCut = Icon(':/icons/cut')
        self.iconDelete = Icon(':/icons/delete')
        self.iconGrid = Icon(':/icons/grid')
        self.iconHelp = Icon(':/icons/help')
        self.iconLabel = Icon(':/icons/label')
        self.iconLicense = Icon(':/icons/license')
        self.iconLink = Icon(':/icons/link')
        self.iconNew = Icon(':/icons/new')
        self.iconOpen = Icon(':/icons/open')
        self.iconPaste = Icon(':/icons/paste')
        self.iconPalette = Icon(':/icons/appearance')
        self.iconPreferences = Icon(':/icons/preferences')
        self.iconPrint = Icon(':/icons/print')
        self.iconQuit = Icon(':/icons/quit')
        self.iconRedo = Icon(':/icons/redo')
        self.iconRefactor = Icon(':/icons/refactor')
        self.iconRefresh = Icon(':/icons/refresh')
        self.iconSave = Icon(':/icons/save')
        self.iconSaveAs = Icon(':/icons/save')
        self.iconSelectAll = Icon(':/icons/select-all')
        self.iconSendToBack = Icon(':/icons/send-to-back')
        self.iconSpellCheck = Icon(':/icons/spell-check')
        self.iconStarFilled = Icon(':/icons/star-filled')
        self.iconSwapHorizontal = Icon(':/icons/swap-horizontal')
        self.iconSwapVertical = Icon(':/icons/swap-vertical')
        self.iconUndo = Icon(':/icons/undo')
        self.iconZoom = Icon(':/icons/zoom')
        self.iconZoomIn = Icon(':/icons/zoom-in')
        self.iconZoomOut = Icon(':/icons/zoom-out')

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE ACTIONS                                                                                          #
        #                                                                                                              #
        ################################################################################################################

        self.actionUndo = self.undogroup.createUndoAction(self)
        self.actionUndo.setIcon(self.iconUndo)
        self.actionUndo.setShortcut(QKeySequence.Undo)

        self.actionRedo = self.undogroup.createRedoAction(self)
        self.actionRedo.setIcon(self.iconRedo)
        self.actionRedo.setShortcut(QKeySequence.Redo)

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
        for i in range(DiagramScene.RecentNum):
            action = QAction(self)
            action.setVisible(False)
            connect(action.triggered, self.openRecentDocument)
            self.actionsOpenRecentDocument.append(action)

        self.actionSaveDocument = QAction('Save', self)
        self.actionSaveDocument.setIcon(self.iconSave)
        self.actionSaveDocument.setShortcut(QKeySequence.Save)
        self.actionSaveDocument.setStatusTip('Save the active diagram')
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
        connect(self.actionCloseActiveSubWindow.triggered, self.closeActiveSubWindow)

        self.actionOpenPreferences = QAction('Preferences', self)
        self.actionOpenPreferences.setShortcut(QKeySequence.Preferences)
        self.actionOpenPreferences.setStatusTip('Open {} preferences'.format(APPNAME))
        self.actionOpenPreferences.setData(PreferencesDialog)
        connect(self.actionOpenPreferences.triggered, self.openDialog)

        if platform is not Platform.Darwin:
            self.actionOpenPreferences.setIcon(self.iconPreferences)

        self.actionQuit = QAction('Quit', self)
        self.actionQuit.setStatusTip('Quit {}'.format(APPNAME))
        self.actionQuit.setShortcut(QKeySequence.Quit)
        connect(self.actionQuit.triggered, self.close)

        if platform is not Platform.Darwin:
            self.actionQuit.setIcon(self.iconQuit)

        self.actionAbout = QAction('About {}'.format(APPNAME), self)
        self.actionAbout.setShortcut(QKeySequence.HelpContents)
        self.actionAbout.setData(About)
        connect(self.actionAbout.triggered, self.openDialog)

        if platform is not Platform.Darwin:
            self.actionAbout.setIcon(self.iconHelp)

        self.actionSapienzaWeb = QAction('DIAG - Sapienza university', self)
        self.actionSapienzaWeb.setIcon(self.iconLink)
        connect(self.actionSapienzaWeb.triggered, lambda: webbrowser.open(DIAG_HOME))

        self.actionGrapholWeb = QAction('Graphol homepage', self)
        self.actionGrapholWeb.setIcon(self.iconLink)
        connect(self.actionGrapholWeb.triggered, lambda: webbrowser.open(GRAPHOL_HOME))

        ## DIAGRAM SCENE
        self.actionOpenSceneProperties = QAction('Properties...', self)
        self.actionOpenSceneProperties.setIcon(self.iconPreferences)
        connect(self.actionOpenSceneProperties.triggered, self.openSceneProperties)

        self.actionSnapToGrid = QAction('Snap to grid', self)
        self.actionSnapToGrid.setIcon(self.iconGrid)
        self.actionSnapToGrid.setStatusTip('Snap diagram elements to the grid')
        self.actionSnapToGrid.setCheckable(True)
        self.actionSnapToGrid.setChecked(self.snapToGrid)
        self.actionSnapToGrid.setEnabled(False)
        connect(self.actionSnapToGrid.triggered, self.toggleSnapToGrid)

        self.actionCenterDiagram = QAction('Center diagram', self)
        self.actionCenterDiagram.setIcon(self.iconCenterFocus)
        self.actionCenterDiagram.setStatusTip('Center the diagram in the scene')
        self.actionCenterDiagram.setEnabled(False)
        connect(self.actionCenterDiagram.triggered, self.centerDiagram)

        self.actionSyntaxCheck = QAction('Run syntax check', self)
        self.actionSyntaxCheck.setIcon(self.iconSpellCheck)
        self.actionSyntaxCheck.setStatusTip('Run syntax check on the active diagram')
        self.actionSyntaxCheck.setEnabled(False)
        connect(self.actionSyntaxCheck.triggered, self.syntaxCheck)

        ## ITEM GENERIC ACTIONS
        self.actionCut = QAction('Cut', self)
        self.actionCut.setIcon(self.iconCut)
        self.actionCut.setShortcut(QKeySequence.Cut)
        self.actionCut.setStatusTip('Cut selected items')
        self.actionCut.setEnabled(False)
        connect(self.actionCut.triggered, self.itemCut)

        self.actionCopy = QAction('Copy', self)
        self.actionCopy.setIcon(self.iconCopy)
        self.actionCopy.setShortcut(QKeySequence.Copy)
        self.actionCopy.setStatusTip('Copy selected items')
        self.actionCopy.setEnabled(False)
        connect(self.actionCopy.triggered, self.itemCopy)

        self.actionPaste = QAction('Paste', self)
        self.actionPaste.setIcon(self.iconPaste)
        self.actionPaste.setShortcut(QKeySequence.Paste)
        self.actionPaste.setStatusTip('Paste items')
        self.actionPaste.setEnabled(False)
        connect(self.actionPaste.triggered, self.itemPaste)

        self.actionDelete = QAction('Delete', self)
        self.actionDelete.setIcon(self.iconDelete)
        self.actionDelete.setShortcut(QKeySequence.Delete)
        self.actionDelete.setStatusTip('Delete selected items')
        self.actionDelete.setEnabled(False)
        connect(self.actionDelete.triggered, self.itemDelete)

        self.actionBringToFront = QAction('Bring to Front', self)
        self.actionBringToFront.setIcon(self.iconBringToFront)
        self.actionBringToFront.setStatusTip('Bring selected items to front')
        self.actionBringToFront.setEnabled(False)
        connect(self.actionBringToFront.triggered, self.bringToFront)

        self.actionSendToBack = QAction('Send to Back', self)
        self.actionSendToBack.setIcon(self.iconSendToBack)
        self.actionSendToBack.setStatusTip('Send selected items to back')
        self.actionSendToBack.setEnabled(False)
        connect(self.actionSendToBack.triggered, self.sendToBack)

        self.actionSelectAll = QAction('Select All', self)
        self.actionSelectAll.setIcon(self.iconSelectAll)
        self.actionSelectAll.setShortcut(QKeySequence.SelectAll)
        self.actionSelectAll.setStatusTip('Select all items in the active diagram')
        self.actionSelectAll.setEnabled(False)
        connect(self.actionSelectAll.triggered, self.selectAll)

        ## NODE GENERIC ACTIONS
        self.actionOpenNodeProperties = QAction('Properties...', self)
        self.actionOpenNodeProperties.setIcon(self.iconPreferences)
        connect(self.actionOpenNodeProperties.triggered, self.openNodeProperties)

        style = self.style()
        size = style.pixelMetric(QStyle.PM_ToolBarIconSize)

        self.actionsChangeNodeBrush = []
        for color in Color:
            action = QAction(color.name, self)
            action.setIcon(ColoredIcon(size, size, color.value))
            action.setCheckable(False)
            action.setData(color)
            connect(action.triggered, self.setNodeBrush)
            self.actionsChangeNodeBrush.append(action)

        self.actionResetTextPosition = QAction('Reset label position', self)
        self.actionResetTextPosition.setIcon(self.iconRefresh)
        connect(self.actionResetTextPosition.triggered, self.resetTextPosition)

        self.actionsNodeSetSpecial = []
        for special in Special:
            action = QAction(special.value, self)
            action.setCheckable(True)
            action.setData(special)
            connect(action.triggered, self.setSpecialNode)
            self.actionsNodeSetSpecial.append(action)

        self.actionRefactorName = QAction('Rename...', self)
        self.actionRefactorName.setIcon(self.iconLabel)
        connect(self.actionRefactorName.triggered, self.refactorName)

        self.actionsRefactorBrush = []
        for color in Color:
            action = QAction(color.name, self)
            action.setIcon(ColoredIcon(size, size, color.value))
            action.setCheckable(False)
            action.setData(color)
            connect(action.triggered, self.refactorBrush)
            self.actionsRefactorBrush.append(action)

        ## ROLE / ATTRIBUTE NODES
        self.actionComposePropertyDomain = QAction('Property Domain', self)
        self.actionComposePropertyRange = QAction('Property Range', self)

        connect(self.actionComposePropertyDomain.triggered, self.composePropertyDomain)
        connect(self.actionComposePropertyRange.triggered, self.composePropertyRange)

        ## DOMAIN / RANGE RESTRICTION
        self.actionsRestrictionChange = []
        for restriction in Restriction:
            action = QAction(restriction.value, self)
            action.setCheckable(True)
            action.setData(restriction)
            connect(action.triggered, self.setDomainRangeRestriction)
            self.actionsRestrictionChange.append(action)

        ## VALUE DOMAIN NODE
        self.actionsChangeValueDomainDatatype = []
        for datatype in XsdDatatype:
            action = QAction(datatype.value, self)
            action.setCheckable(True)
            action.setData(datatype)
            connect(action.triggered, self.setValueDomainDatatype)
            self.actionsChangeValueDomainDatatype.append(action)

        ## VALUE RESTRICTION
        self.actionChangeValueRestriction = QAction('Select restriction...', self)
        self.actionChangeValueRestriction.setIcon(self.iconRefresh)
        connect(self.actionChangeValueRestriction.triggered, self.setValueRestriction)

        ## OPERATOR NODES
        data = OrderedDict()
        data[ComplementNode] = 'Complement'
        data[DisjointUnionNode] = 'Disjoint union'
        data[DatatypeRestrictionNode] = 'Datatype restriction'
        data[EnumerationNode] = 'Enumeration'
        data[IntersectionNode] = 'Intersection'
        data[RoleChainNode] = 'Role chain'
        data[RoleInverseNode] = 'Role inverse'
        data[UnionNode] = 'Union'

        self.actionsSwitchOperatorNode = []
        for k, v in data.items():
            action = QAction(v, self)
            action.setCheckable(True)
            action.setData(k)
            connect(action.triggered, self.switchOperatorNode)
            self.actionsSwitchOperatorNode.append(action)

        ## INDIVIDUAL NODE
        self.actionsSetIndividualNodeAs = []
        for identity in (Identity.Instance, Identity.Value):
            action = QAction(identity.label, self)
            action.setData(identity)
            connect(action.triggered, self.setIndividualNodeAs)
            self.actionsSetIndividualNodeAs.append(action)

        ## EDGES
        self.actionRemoveEdgeBreakpoint = QAction('Remove breakpoint', self)
        self.actionRemoveEdgeBreakpoint.setIcon(self.iconDelete)
        connect(self.actionRemoveEdgeBreakpoint.triggered, self.removeBreakpoint)

        self.actionSwapEdge = QAction('Swap', self)
        self.actionSwapEdge.setIcon(self.iconSwapHorizontal)
        self.actionSwapEdge.setShortcut('ALT+S')
        connect(self.actionSwapEdge.triggered, self.swapEdge)

        self.actionToggleEdgeComplete = QAction('Complete', self)
        self.actionToggleEdgeComplete.setShortcut('ALT+C')
        self.actionToggleEdgeComplete.setCheckable(True)
        connect(self.actionToggleEdgeComplete.triggered, self.toggleEdgeComplete)

        self.addAction(self.actionSwapEdge)
        self.addAction(self.actionToggleEdgeComplete)

        ################################################################################################################
        #                                                                                                              #
        #   CREATE WIDGETS                                                                                             #
        #                                                                                                              #
        ################################################################################################################

        self.explorer = Explorer(self)
        self.info = Info(self)
        self.mdi = MdiArea(self)
        self.overview = Overview(self)
        self.palette_ = Palette(self)
        self.zoomctrl = ZoomControl(self.toolbar)

        self.dockExplorer = QDockWidget('Explorer', self, Qt.Widget)
        self.dockExplorer.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockExplorer.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable)
        self.dockExplorer.setFixedWidth(self.explorer.width())
        self.dockExplorer.setObjectName('explorer')
        self.dockExplorer.setWidget(self.explorer)

        self.dockInfo = QDockWidget('Info', self, Qt.Widget)
        self.dockInfo.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockInfo.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable)
        self.dockInfo.setFixedWidth(self.info.width())
        self.dockInfo.setObjectName('info')
        self.dockInfo.setWidget(self.info)

        self.dockOverview = QDockWidget('Overview', self, Qt.Widget)
        self.dockOverview.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockOverview.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable)
        self.dockOverview.setFixedWidth(self.overview.width())
        self.dockOverview.setObjectName('overview')
        self.dockOverview.setWidget(self.overview)

        self.dockPalette = QDockWidget('Palette', self, Qt.Widget)
        self.dockPalette.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockPalette.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable)
        self.dockPalette.setFixedSize(self.palette_.size())
        self.dockPalette.setObjectName('palette')
        self.dockPalette.setWidget(self.palette_)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockPalette)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockInfo)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockOverview)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockExplorer)

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE MAIN WINDOW UI                                                                                   #
        #                                                                                                              #
        ################################################################################################################

        self.setAcceptDrops(True)
        self.setCentralWidget(self.mdi)
        self.setDockOptions(MainWindow.AnimatedDocks|MainWindow.AllowTabbedDocks)
        self.setMinimumSize(MainWindow.MinWidth, MainWindow.MinHeight)
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setWindowTitle(None)

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE MENUS                                                                                            #
        #                                                                                                              #
        ################################################################################################################

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
        for i in range(DiagramScene.RecentNum):
            self.menuFile.addAction(self.actionsOpenRecentDocument[i])

        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionPrintDocument)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)

        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionCut)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addAction(self.actionPaste)
        self.menuEdit.addAction(self.actionDelete)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionBringToFront)
        self.menuEdit.addAction(self.actionSendToBack)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionSelectAll)
        self.menuEdit.addAction(self.actionCenterDiagram)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionOpenPreferences)

        self.menuView.addAction(self.actionSnapToGrid)
        self.menuView.addSeparator()
        self.menuView.addAction(self.toolbar.toggleViewAction())
        self.menuView.addSeparator()
        self.menuView.addAction(self.dockExplorer.toggleViewAction())
        self.menuView.addAction(self.dockInfo.toggleViewAction())
        self.menuView.addAction(self.dockOverview.toggleViewAction())
        self.menuView.addAction(self.dockPalette.toggleViewAction())

        self.menuTools.addAction(self.actionSyntaxCheck)

        self.menuHelp.addAction(self.actionAbout)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionSapienzaWeb)
        self.menuHelp.addAction(self.actionGrapholWeb)

        ## NODE GENERIC MENU
        self.menuNodeChangeBrush = QMenu('Select color')
        self.menuNodeChangeBrush.setIcon(self.iconColorFill)
        for action in self.actionsChangeNodeBrush:
            self.menuNodeChangeBrush.addAction(action)

        self.menuNodeSpecial = QMenu('Special type')
        self.menuNodeSpecial.setIcon(self.iconStarFilled)
        for action in self.actionsNodeSetSpecial:
            self.menuNodeSpecial.addAction(action)

        self.menuRefactorBrush = QMenu('Select color')
        self.menuRefactorBrush.setIcon(self.iconColorFill)
        for action in self.actionsRefactorBrush:
            self.menuRefactorBrush.addAction(action)

        self.menuNodeRefactor = QMenu('Refactor')
        self.menuNodeRefactor.setIcon(self.iconRefactor)
        self.menuNodeRefactor.addAction(self.actionRefactorName)
        self.menuNodeRefactor.addMenu(self.menuRefactorBrush)

        ## ROLE / ATTRIBUTE NODE
        self.menuNodeCompose = QMenu('Compose')
        self.menuNodeCompose.setIcon(self.iconCreate)
        self.menuNodeCompose.addAction(self.actionComposePropertyDomain)
        self.menuNodeCompose.addAction(self.actionComposePropertyRange)

        ## VALUE DOMAIN NODE
        self.menuChangeValueDomainDatatype = QMenu('Select type')
        self.menuChangeValueDomainDatatype.setIcon(self.iconRefresh)
        for action in self.actionsChangeValueDomainDatatype:
            self.menuChangeValueDomainDatatype.addAction(action)

        ## DOMAIN / RANGE RESTRICTION NODES
        self.menuRestrictionChange = QMenu('Select restriction')
        self.menuRestrictionChange.setIcon(self.iconRefresh)
        for action in self.actionsRestrictionChange:
            self.menuRestrictionChange.addAction(action)

        ## OPERATOR NODES
        self.menuOperatorNodeSwitch = QMenu('Switch to')
        self.menuOperatorNodeSwitch.setIcon(self.iconRefresh)
        for action in self.actionsSwitchOperatorNode:
            self.menuOperatorNodeSwitch.addAction(action)

        ## INDIVIDUAL NODE
        self.menuSetIndividualNodeAs = QMenu('Set as')
        self.menuSetIndividualNodeAs.setIcon(self.iconRefresh)
        for action in self.actionsSetIndividualNodeAs:
            self.menuSetIndividualNodeAs.addAction(action)

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE STATUS BAR                                                                                       #
        #                                                                                                              #
        ################################################################################################################

        statusbar = QStatusBar(self)
        statusbar.setSizeGripEnabled(False)
        self.setStatusBar(statusbar)

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE TOOLBAR                                                                                          #
        #                                                                                                              #
        ################################################################################################################

        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)

        self.toolbar.addAction(self.actionNewDocument)
        self.toolbar.addAction(self.actionOpenDocument)
        self.toolbar.addAction(self.actionSaveDocument)
        self.toolbar.addAction(self.actionPrintDocument)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionUndo)
        self.toolbar.addAction(self.actionRedo)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionCut)
        self.toolbar.addAction(self.actionCopy)
        self.toolbar.addAction(self.actionPaste)
        self.toolbar.addAction(self.actionDelete)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionBringToFront)
        self.toolbar.addAction(self.actionSendToBack)

        self.buttonChangeNodeBrush = QToolButton()
        self.buttonChangeNodeBrush.setIcon(self.iconColorFill)
        self.buttonChangeNodeBrush.setMenu(self.menuNodeChangeBrush)
        self.buttonChangeNodeBrush.setPopupMode(QToolButton.InstantPopup)
        self.buttonChangeNodeBrush.setEnabled(False)

        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.buttonChangeNodeBrush)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionSnapToGrid)
        self.toolbar.addAction(self.actionCenterDiagram)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionSyntaxCheck)

        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.zoomctrl.buttonZoomOut)
        self.toolbar.addWidget(self.zoomctrl.buttonZoomIn)
        self.toolbar.addWidget(self.zoomctrl.buttonZoomLevelChange)

        ################################################################################################################
        #                                                                                                              #
        #   LOAD SETTINGS [RESTORE STATE]                                                                              #
        #                                                                                                              #
        ################################################################################################################

        settings = QSettings(expandPath('@home/{}.ini'.format(APPNAME)), QSettings.IniFormat)

        settings.beginGroup('diagram')
        self.diagramSize = settings.value('size', self.diagramSize, int)
        self.snapToGrid = settings.value('grid', self.snapToGrid, bool)

        if not settings.contains('recent'):
            # From PyQt5 documentation: if the value of the setting is a container (corresponding to either
            # QVariantList, QVariantMap or QVariantHash) then the type is applied to the contents of the
            # container. So according to this we can't use an empty list as default value because PyQt5 needs
            # to know the type of the contents added to the collection: we avoid this problem by placing
            # the list of examples file in the recentDocumentList (only if there is no list defined already).
            settings.setValue('recent', [
                expandPath('@examples/Animals.graphol'),
                expandPath('@examples/Diet.graphol'),
                expandPath('@examples/Family.graphol'),
                expandPath('@examples/LUBM.graphol'),
                expandPath('@examples/Pizza.graphol'),
            ])

        self.recentDocument = settings.value('recent', None, str)
        self.refreshRecentDocument()
        settings.endGroup()

        settings.beginGroup('mainwindow')
        geometry = settings.value('geometry')
        state = settings.value('state')
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        settings.endGroup()

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE SIGNALS                                                                                          #
        #                                                                                                              #
        ################################################################################################################

        connect(self.documentLoaded, self.documentLoadedOrSaved)
        connect(self.documentSaved, self.documentLoadedOrSaved)
        connect(self.mdi.subWindowActivated, self.subWindowActivated)
        connect(self.palette_.buttonClicked[int], self.paletteButtonClicked)
        connect(self.undogroup.cleanChanged, self.undoGroupCleanChanged)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def bringToFront(self):
        """
        Bring the selected item to the top of the scene.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            for selected in scene.selectedNodes():
                zValue = 0
                colliding = selected.collidingItems()
                for item in filter(lambda x: not x.isItem(Item.LabelNode, Item.LabelEdge), colliding):
                    if item.zValue() >= zValue:
                        zValue = item.zValue() + 0.2
                if zValue != selected.zValue():
                    scene.undostack.push(CommandNodeSetZValue(scene, selected, zValue))

    @pyqtSlot()
    def centerDiagram(self):
        """
        Center the diagram in the scene.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            items = scene.items()
            if items:
                R1 = scene.sceneRect()
                R2 = scene.visibleRect(margin=0)
                moveX = snapF(((R1.right() - R2.right()) - (R2.left() - R1.left())) / 2, DiagramScene.GridSize)
                moveY = snapF(((R1.bottom() - R2.bottom()) - (R2.top() - R1.top())) / 2, DiagramScene.GridSize)
                if moveX or moveY:
                    collection = [x for x in items if x.node or x.edge]
                    scene.undostack.push(CommandItemsTranslate(scene, collection, moveX, moveY, 'center diagram'))
                    mainview = self.mdi.activeView
                    mainview.centerOn(0, 0)

    @pyqtSlot()
    def closeActiveSubWindow(self):
        """
        Close the currently active subwindow.
        """
        subwindow = self.mdi.activeSubWindow()
        if subwindow:
            subwindow.close()

    @pyqtSlot()
    def composePropertyDomain(self):
        """
        Compose a property domain using the selected role/attribute node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            args = Item.RoleNode, Item.AttributeNode
            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:
                name = 'compose {} property domain'.format(node.item.label)
                items = scene.propertyDomainAxiomComposition(node)
                nodes = {x for x in items if x.node}
                edges = {x for x in items if x.edge}
                scene.undostack.push(CommandComposeAxiom(name, scene, node, nodes, edges))

    @pyqtSlot()
    def composePropertyRange(self):
        """
        Compose a property range using the selected role/attribute node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            args = Item.RoleNode, Item.AttributeNode
            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:
                name = 'compose {} property range'.format(node.item.label)
                items = scene.propertyRangeAxiomComposition(node)
                nodes = {x for x in items if x.node}
                edges = {x for x in items if x.edge}
                scene.undostack.push(CommandComposeAxiom(name, scene, node, nodes, edges))

    @pyqtSlot('QGraphicsScene')
    def documentLoadedOrSaved(self, scene):
        """
        Executed when a document is loaded or saved from/to a Graphol file.
        :type scene: DiagramScene
        """
        self.insertRecentDocument(scene.document.path)
        self.setWindowTitle(scene.document.name)

    @pyqtSlot()
    def exportDocument(self):
        """
        Export the currently open graphol document.
        """
        scene = self.mdi.activeScene
        if scene:
            result = self.exportPath(name=rCut(scene.document.name, Filetype.Graphol.extension))
            if result:
                filepath = result[0]
                filetype = Filetype.forValue(result[1])
                if filetype is Filetype.Pdf:
                    self.exportToPdf(scene, filepath)
                elif filetype is Filetype.Owl:
                    self.exportToOwl(scene, filepath)

    @pyqtSlot()
    def importDocument(self):
        """
        Import a document from a different file format.
        """
        dialog = OpenFile(expandPath('~'))
        dialog.setNameFilters([Filetype.Graphml.value])

        if dialog.exec_():

            filepath = dialog.selectedFiles()[0]
            worker = GraphmlLoader(self, filepath)

            with BusyProgressDialog('Importing {}'.format(os.path.basename(filepath)), self):

                try:
                    worker.run()
                except Exception as e:
                    msgbox = QMessageBox(self)
                    msgbox.setIconPixmap(QPixmap(':/icons/error'))
                    msgbox.setWindowIcon(QIcon(':/images/eddy'))
                    msgbox.setWindowTitle('Import failed!')
                    msgbox.setStandardButtons(QMessageBox.Close)
                    msgbox.setText('Failed to import {}!'.format(os.path.basename(filepath)))
                    msgbox.setDetailedText(''.join(format_exception(type(e), e, e.__traceback__)))
                    msgbox.exec_()
                else:
                    scene = worker.scene
                    scene.setMode(DiagramMode.Idle)
                    mainview = self.createView(scene)
                    subwindow = self.createSubWindow(mainview)
                    subwindow.showMaximized()
                    self.mdi.setActiveSubWindow(subwindow)
                    self.mdi.update()

            if worker.errors:

                # If some errors have been generated during the import process, display
                # them into a popup so the user can check whether the problem is in the
                # .graphml document or Eddy is not handling the import properly.
                m1 = 'Document {} has been imported! However some errors ({}) have been generated ' \
                     'during the import process. You can inspect detailed information by expanding the ' \
                     'box below.'.format(os.path.basename(filepath), len(worker.errors))

                m2 = 'If needed, <a href="{}">submit a bug report</a> with detailed information.'.format(BUG_TRACKER)

                parts = []
                for k, v in enumerate(worker.errors, start=1):
                    parts.append('{}) {}'.format(k, ''.join(format_exception(type(v), v, v.__traceback__))))

                m3 = '\n'.join(parts)

                msgbox = QMessageBox(self)
                msgbox.setIconPixmap(QPixmap(':/icons/warning'))
                msgbox.setWindowIcon(QIcon(':/images/eddy'))
                msgbox.setWindowTitle('Partial document import!')
                msgbox.setStandardButtons(QMessageBox.Close)
                msgbox.setText(m1)
                msgbox.setInformativeText(m2)
                msgbox.setDetailedText(m3)
                msgbox.exec_()

    @pyqtSlot('QGraphicsItem', int)
    def itemAdded(self, item, modifiers):
        """
        Executed after an item insertion process ends (even if the item has not been truly inserted).
        :type item: AbstractItem
        :type modifiers: int
        """
        scene = self.mdi.activeScene
        if not modifiers & Qt.ControlModifier:
            self.palette_.button(item.item).setChecked(False)
            scene.setMode(DiagramMode.Idle)

    @pyqtSlot()
    def itemCut(self):
        """
        Cut selected items from the active scene.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            scene.pasteOffsetX = 0
            scene.pasteOffsetY = 0
            self.clipboard.update(scene)
            self.sceneSelectionChanged()
            selection = scene.selectedItems()
            if selection:
                selection.extend([x for item in selection if item.node for x in item.edges if x not in selection])
                scene.undostack.push(CommandItemsMultiRemove(scene, selection))

    @pyqtSlot()
    def itemCopy(self):
        """
        Make a copy of selected items.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            scene.pasteOffsetX = Clipboard.PasteOffsetX
            scene.pasteOffsetY = Clipboard.PasteOffsetY
            self.clipboard.update(scene)
            self.sceneSelectionChanged()

    @pyqtSlot()
    def itemPaste(self):
        """
        Paste previously copied items.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            if not self.clipboard.empty():
                self.clipboard.paste(scene, scene.mousePressPos)

    @pyqtSlot()
    def itemDelete(self):
        """
        Delete the currently selected items from the diagram scene.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selection = scene.selectedItems()
            if selection:
                selection.extend([x for item in selection if item.node for x in item.edges if x not in selection])
                scene.undostack.push(CommandItemsMultiRemove(scene, selection))

    @pyqtSlot()
    def newDocument(self):
        """
        Create a new empty document and add it to the MDI Area.
        """
        scene = self.createScene(self.diagramSize, self.diagramSize)
        mainview = self.createView(scene)
        subwindow = self.createSubWindow(mainview)
        subwindow.showMaximized()
        self.mdi.setActiveSubWindow(subwindow)
        self.mdi.update()

    @pyqtSlot()
    def openDocument(self):
        """
        Open a document.
        """
        dialog = OpenFile(expandPath('~'))
        dialog.setNameFilters([Filetype.Graphol.value])
        if dialog.exec_():
            self.openFile(dialog.selectedFiles()[0])

    @pyqtSlot()
    def openDialog(self):
        """
        Open a dialog window by initializing it using the class stored in action data.
        """
        action = self.sender()
        dialog = action.data()
        window = dialog(self)
        window.exec_()

    @pyqtSlot()
    def openNodeProperties(self):
        """
        Executed when node properties needs to be displayed.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            node = next(iter(scene.selectedNodes()), None)
            if node:
                prop = self.propertyFactory.create(scene=scene, node=node)
                prop.exec_()
        
    @pyqtSlot()
    def openRecentDocument(self):
        """
        Open the clicked recent document.
        """
        action = self.sender()
        if action:
            self.openFile(action.data())

    @pyqtSlot()
    def openSceneProperties(self):
        """
        Executed when scene properties needs to be displayed.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            prop = self.propertyFactory.create(scene=scene)
            prop.exec_()

    @pyqtSlot(int)
    def paletteButtonClicked(self, item):
        """
        Executed whenever a Palette button is clicked.
        :type item: Item
        """
        scene = self.mdi.activeScene
        if not scene:
            self.palette_.clear()
        else:
            scene.clearSelection()
            button = self.palette_.button(item)
            self.palette_.clear(button)
            if not button.isChecked():
                scene.setMode(DiagramMode.Idle)
            else:
                if Item.ConceptNode <= item < Item.InclusionEdge:
                    scene.setMode(DiagramMode.NodeInsert, item)
                elif Item.InclusionEdge <= item <= Item.InstanceOfEdge:
                    scene.setMode(DiagramMode.EdgeInsert, item)

    @pyqtSlot()
    def printDocument(self):
        """
        Print the currently open graphol document.
        """
        scene = self.mdi.activeScene
        if scene:
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
    def refactorBrush(self):
        """
        Change the node brush for all the nodes whose label is equal to the label of the currently selected node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            args = Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode
            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:
                action = self.sender()
                color = action.data()
                nodes = scene.index.nodesForLabel(node.item, node.text())
                scene.undostack.push(CommandNodeSetBrush(scene, nodes, QBrush(QColor(color.value))))

    @pyqtSlot()
    def refactorName(self):
        """
        Rename the label of the currently selected node and all the occurrences sharing the same label text.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            args = Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode
            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:
                form = RenameForm(node, self)
                if form.exec_() == RenameForm.Accepted:
                    if node.text() != form.renameField.value():
                        commands = []
                        undo = node.text()
                        redo = form.renameField.value()
                        for n in scene.index.nodesForLabel(node.item, node.text()):
                            commands.append(CommandNodeLabelChange(scene, n, n.text(), redo))
                        name = 'change predicate "{}" name to "{}"'.format(undo, redo)
                        scene.undostack.push(CommandRefactor(name, scene, commands))

    @pyqtSlot()
    def removeBreakpoint(self):
        """
        Remove the edge breakpoint specified in the action triggering this slot.
        """
        scene = self.mdi.activeScene
        if scene:
            action = self.sender()
            edge, breakpoint = action.data()
            if 0 <= breakpoint < len(edge.breakpoints):
                scene.undostack.push(CommandEdgeBreakpointRemove(scene, edge, breakpoint))

    @pyqtSlot()
    def resetTextPosition(self):
        """
        Reset selected node label to default position.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: hasattr(x, 'label'), scene.selectedNodes()), None)
            if node and node.label.movable:
                undo = node.label.pos()
                redo = node.label.defaultPos()
                scene.undostack.push(CommandNodeLabelMove(scene, node, undo, redo))
                node.updateTextPos()

    @pyqtSlot()
    def saveDocument(self):
        """
        Save the currently open graphol document.
        """
        scene = self.mdi.activeScene
        if scene:
            filepath = scene.document.path or self.savePath(name=scene.document.name)
            if filepath:
                saved = self.saveFile(scene, filepath)
                if saved:
                    scene.undostack.setClean()
                    self.documentSaved.emit(scene)

    @pyqtSlot()
    def saveDocumentAs(self):
        """
        Save the currently open graphol document (enforcing a new name).
        """
        scene = self.mdi.activeScene
        if scene:
            filepath = self.savePath(name=scene.document.name)
            if filepath:
                saved = self.saveFile(scene, filepath)
                if saved:
                    scene.undostack.setClean()
                    self.documentSaved.emit(scene)

    @pyqtSlot(DiagramMode)
    def sceneModeChanged(self, mode):
        """
        Executed when the scene operation mode changes.
        :type mode: DiagramMode
        """
        if mode not in (DiagramMode.NodeInsert, DiagramMode.EdgeInsert):
            self.palette_.clear()

    @pyqtSlot()
    def sceneSelectionChanged(self):
        """
        Update actions enabling/disabling them when needed.
        """
        window = False
        undo = False
        clipboard = False
        edge = False
        node = False
        predicate = False

        # we need to check if we have at least one subwindow because if Eddy simply
        # lose the focus, self.mdi.activeScene will return None even though we do
        # not need to disable actions because we will have scene in the background.
        if self.mdi.subWindowList():

            scene = self.mdi.activeScene
            if scene:

                nodes = scene.selectedNodes()
                edges = scene.selectedEdges()

                window = True
                undo = not self.undogroup.isClean()
                clipboard = not self.clipboard.empty()
                edge = len(edges) != 0
                node = len(nodes) != 0
                predicate = next(filter(lambda x: x.predicate, nodes), None) is not None

        self.actionBringToFront.setEnabled(node)
        self.actionCenterDiagram.setEnabled(window)
        self.actionCloseActiveSubWindow.setEnabled(window)
        self.actionCut.setEnabled(node)
        self.actionCopy.setEnabled(node)
        self.actionDelete.setEnabled(node or edge)
        self.actionExportDocument.setEnabled(window)
        self.actionPaste.setEnabled(clipboard)
        self.actionPrintDocument.setEnabled(window)
        self.actionSaveDocument.setEnabled(undo)
        self.actionSaveDocumentAs.setEnabled(window)
        self.actionSelectAll.setEnabled(window)
        self.actionSendToBack.setEnabled(node)
        self.actionSnapToGrid.setEnabled(window)
        self.actionSyntaxCheck.setEnabled(window)
        self.buttonChangeNodeBrush.setEnabled(predicate)
        self.zoomctrl.setEnabled(window)

    @pyqtSlot()
    def selectAll(self):
        """
        Select all the items in the scene.
        """
        # TODO SPEED UP
        scene = self.mdi.activeScene
        if scene:
            scene.clearSelection()
            scene.setMode(DiagramMode.Idle)
            for collection in (scene.nodes(), scene.edges()):
                for item in collection:
                    item.setSelected(True)

    @pyqtSlot()
    def sendToBack(self):
        """
        Send the selected item to the back of the scene.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            for selected in scene.selectedNodes():
                zValue = 0
                colliding = selected.collidingItems()
                for item in filter(lambda x: not x.isItem(Item.LabelNode, Item.LabelEdge), colliding):
                    if item.zValue() <= zValue:
                        zValue = item.zValue() - 0.2
                if zValue != selected.zValue():
                    scene.undostack.push(CommandNodeSetZValue(scene, selected, zValue))

    @pyqtSlot()
    def setNodeBrush(self):
        """
        Set the brush of selected nodes.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            color = action.data()
            brush = QBrush(QColor(color.value))
            selected = [x for x in scene.selectedNodes() if x.predicate and x.brush != brush]
            if selected:
                scene.undostack.push(CommandNodeSetBrush(scene, selected, brush))

    @pyqtSlot()
    def setDomainRangeRestriction(self):
        """
        Set a domain/range restriction.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            nodes = scene.selectedNodes()
            node = next(filter(lambda x: x.isItem(Item.DomainRestrictionNode, Item.RangeRestrictionNode), nodes), None)
            if node:
                data = None
                action = self.sender()
                restriction = action.data()
                if restriction is not Restriction.Cardinality:
                    data = restriction.label
                else:
                    form = CardinalityRestrictionForm()
                    if form.exec_() == CardinalityRestrictionForm.Accepted:
                        data = '({},{})'.format(form.minCardinalityValue or '-', form.maxCardinalityValue or '-')
                if data:
                    if node.text() != data:
                        item = 'range' if node.isItem(Item.RangeRestrictionNode) else 'domain'
                        name = 'change {} restriction to {}'.format(item, data)
                        scene.undostack.push(CommandNodeLabelChange(scene, node, node.text(), data, name))

    @pyqtSlot()
    def setIndividualNodeAs(self):
        """
        Set an invididual node either to Instance or Value.
        Will bring up the Literal Form if needed.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = scene.selectedNodes()
            node = next(filter(lambda x: x.isItem(Item.IndividualNode), selected), None)
            if node:
                action = self.sender()
                if action.data() is Identity.Instance:
                    if node.identity is Identity.Value:
                        name = 'change value to instance'
                        data = node.label.template
                        scene.undostack.push(CommandNodeLabelChange(scene, node, node.text(), data, name))
                elif action.data() is Identity.Value:
                    form = ValueForm(node, self)
                    if form.exec_() == ValueForm.Accepted:
                        datatype = form.datatypeField.currentData()
                        value = form.valueField.value()
                        data = node.composeValue(value, datatype)
                        if node.text() != data:
                            name = 'change {} to {}'.format(node.identity.label.lower(), data)
                            scene.undostack.push(CommandNodeLabelChange(scene, node, node.text(), data, name))

    @pyqtSlot()
    def setSpecialNode(self):
        """
        Set the special type of the selected node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            args = Item.ConceptNode, Item.RoleNode, Item.AttributeNode
            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:
                special = action.data() if node.special is not action.data() else None
                data = special.value if special else node.label.template
                if node.text() != data:
                    name = 'change {} label to "{}"'.format(node.name, data)
                    scene.undostack.push(CommandNodeLabelChange(scene, node, node.text(), data, name))

    @pyqtSlot()
    def setValueDomainDatatype(self):
        """
        Set the datatype of the selected value-domain node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = scene.selectedNodes()
            node = next(filter(lambda x: x.isItem(Item.ValueDomainNode), selected), None)
            if node:
                action = self.sender()
                datatype = action.data()
                data = datatype.value
                if node.text() != data:
                    name = 'change {} datatype to {}'.format(node.name, data)
                    scene.undostack.push(CommandNodeLabelChange(scene, node, node.text(), data, name))

    @pyqtSlot()
    def setValueRestriction(self):
        """
        Set an invididual node either to Individual or Literal.
        Will bring up the Literal Form if needed.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = scene.selectedNodes()
            node = next(filter(lambda x: x.isItem(Item.ValueRestrictionNode), selected), None)
            if node:
                form = ValueRestrictionForm(node, self)
                form.datatypeField.setEnabled(not node.constrained)
                if form.exec() == ValueRestrictionForm.Accepted:
                    datatype = form.datatypeField.currentData()
                    facet = form.facetField.currentData()
                    value = form.valueField.value()
                    data = node.compose(facet, value, datatype)
                    if node.text() != data:
                        name = 'change value restriction to {}'.format(data)
                        scene.undostack.push(CommandNodeLabelChange(scene, node, node.text(), data, name))

    @pyqtSlot('QMdiSubWindow')
    def subWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        if subwindow:
            mainview = subwindow.widget()
            scene = mainview.scene()
            scene.undostack.setActive()
            self.info.setScene(scene)
            self.explorer.setView(mainview)
            self.overview.setView(mainview)
            disconnect(self.zoomctrl.zoomChanged)
            disconnect(mainview.zoomChanged)
            self.zoomctrl.adjustZoomLevel(mainview.zoom)
            connect(self.zoomctrl.zoomChanged, mainview.scaleChanged)
            connect(mainview.zoomChanged, self.zoomctrl.scaleChanged)
            self.setWindowTitle(scene.document.name)
        else:

            if not self.mdi.subWindowList():
                self.zoomctrl.resetZoomLevel()
                self.info.clear()
                self.explorer.clear()
                self.overview.clear()
                self.setWindowTitle(None)

        self.sceneSelectionChanged()

    @pyqtSlot('QMdiSubWindow')
    def subWindowCloseAborted(self, subwindow):
        """
        Executed when the close event of an MDI subwindow is aborted.
        :type subwindow: MdiSubWindow
        """
        self.abortQuit = True
        self.mdi.setActiveSubWindow(subwindow)

    @pyqtSlot('QMdiSubWindow')
    def subWindowClosed(self, subwindow):
        """
        Executed when an MDI subwindow is closed.
        :type subwindow: MdiSubWindow
        """
        mainview = subwindow.widget()
        if mainview:
            self.explorer.flush(mainview)

    @pyqtSlot()
    def swapEdge(self):
        """
        Swap the selected edges by inverting source/target points.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = [edge for edge in scene.selectedEdges() if scene.validator.valid(edge.target, edge, edge.source)]
            if selected:
                scene.undostack.push(CommandEdgeSwap(scene, selected))

    @pyqtSlot()
    def switchOperatorNode(self):
        """
        Switch the selected operator node to a different type.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            selected = scene.selectedNodes()
            node = next(filter(lambda x: Item.UnionNode <= x.item <= Item.DisjointUnionNode, selected), None)
            if node:
                clazz = action.data()
                if not isinstance(node, clazz):
                    xnode = clazz(scene=scene)
                    xnode.setPos(node.pos())
                    scene.undostack.push(CommandNodeOperatorSwitchTo(scene, node, xnode))

    @pyqtSlot()
    def syntaxCheck(self):
        """
        Perform syntax checking on the active diagram.
        """
        scene = self.mdi.activeScene
        if scene:

            placeholder = None
            message = 'No syntax error found!'
            pixmap = QPixmap(':/icons/info')

            with BusyProgressDialog('Syntax check...', self):

                for edge in scene.edges():
                    res = scene.validator.result(edge.source, edge, edge.target)
                    if not res.valid:
                        e = res.edge
                        s = res.source
                        t = res.target
                        m = uncapitalize(res.message)
                        placeholder = res.edge
                        sname = '{} "{}"'.format(s.name, s.id if not s.predicate else '{}:{}'.format(s.text(), s.id))
                        tname = '{} "{}"'.format(t.name, t.id if not t.predicate else '{}:{}'.format(t.text(), t.id))
                        message = 'Syntax error detected on {} from {} to {}: <i>{}</i>.'.format(e.name, sname, tname, m)
                        pixmap = QPixmap(':/icons/warning')
                        break
                else:
                    for n in scene.nodes():
                        if n.identity is Identity.Unknown:
                            placeholder = n
                            name = '{} "{}"'.format(n.name, n.id if not n.predicate else '{}:{}'.format(n.text(), n.id))
                            message = 'Unkown node identity detected on {}.'.format(name)
                            pixmap = QPixmap(':/icons/warning')
                            break

            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(pixmap)
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle('Syntax check completed!')
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText(message)
            msgbox.setTextFormat(Qt.RichText)
            msgbox.exec_()

            if placeholder:
                mainview = self.mdi.activeView
                mainview.centerOn(placeholder)

    @pyqtSlot()
    def toggleEdgeComplete(self):
        """
        Toggle the 'complete' attribute for all the selected Inclusion edges.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = [item for item in scene.selectedEdges() if item.isItem(Item.InclusionEdge)]
            if selected:
                comp = sum(edge.complete for edge in selected) <= len(selected) / 2
                data = {edge: {'from': edge.complete, 'to': comp} for edge in selected}
                scene.undostack.push(CommandEdgeInclusionToggleComplete(scene, data))

    @pyqtSlot()
    def toggleSnapToGrid(self):
        """
        Toggle snap to grid setting.
        """
        self.snapToGrid = self.actionSnapToGrid.isChecked()
        for subwindow in self.mdi.subWindowList():
            mainview = subwindow.widget()
            mainview.snapToGrid = self.snapToGrid
            viewport = mainview.viewport()
            if viewport:
                viewport.update()

    @pyqtSlot(bool)
    def undoGroupCleanChanged(self, clean):
        """
        Executed when the clean state of the active undostack changes.
        :type clean: bool
        """
        self.actionSaveDocument.setEnabled(not clean)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def closeEvent(self, closeEvent):
        """
        Executed when the main window is closed.
        :type closeEvent: QCloseEvent
        """
        self.abortQuit = False
        for subwindow in self.mdi.subWindowList():
            mainview = subwindow.widget()
            scene = mainview.scene()
            if (scene.items() and not scene.document.path) or (not scene.undostack.isClean()):
                self.mdi.setActiveSubWindow(subwindow)
                subwindow.showMaximized()
            subwindow.close()
            if self.abortQuit:
                closeEvent.ignore()
                break

        ################################################################################################################
        #                                                                                                              #
        #   EXPORT CURRENT SETTINGS                                                                                    #
        #                                                                                                              #
        ################################################################################################################

        settings = QSettings(expandPath('@home/{}.ini'.format(APPNAME)), QSettings.IniFormat)

        # DIAGRAM
        settings.beginGroup('diagram')
        settings.setValue('grid', self.snapToGrid)
        settings.setValue('recent', self.recentDocument)
        settings.setValue('size', self.diagramSize)
        settings.endGroup()

        # MAIN WINDOW
        settings.beginGroup('mainwindow')
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('state', self.saveState())
        settings.endGroup()

        # SAVE TO DISK
        settings.sync()

    def dragEnterEvent(self, dragEvent):
        """
        Executed when a drag is in progress and the mouse enter this widget.
        :type dragEvent: QDragEnterEvent
        """
        if dragEvent.mimeData().hasUrls():
            self.setCursor(QCursor(Qt.DragCopyCursor))
            dragEvent.setDropAction(Qt.CopyAction)
            dragEvent.accept()
        else:
            dragEvent.ignore()

    def dragMoveEvent(self, dragEvent):
        """
        Executed when a drag is in progress and the mouse moves onto this widget.
        :type dragEvent: QDragMoveEvent
        """
        dragEvent.accept()

    def dragLeaveEvent(self, dragEvent):
        """
        Executed when a drag is in progress and the mouse leave this widget.
        :type dragEvent: QDragEnterEvent
        """
        self.unsetCursor()

    def dropEvent(self, dropEvent):
        """
        Executed when the drag is dropped on this widget.
        :type dropEvent: QDropEvent
        """
        if dropEvent.mimeData().hasUrls():

            self.unsetCursor()
            dropEvent.setDropAction(Qt.CopyAction)
            platform = Platform.identify()
            for url in dropEvent.mimeData().urls():

                path = url.path()
                if platform is Platform.Windows:
                    # On Windows the absolute path returned for each URL has a
                    # leading slash: this obviously is not correct on windows
                    # platform when absolute url have the form C:\\Programs\\... (Qt bug?)
                    path = path.lstrip('/').lstrip('\\')

                if os.path.isfile(path) and path.endswith(Filetype.Graphol.extension):
                    # If the file exists and is a Graphol file then open it!
                    if not self.focusDocument(path):
                        scene = self.createSceneFromGrapholFile(path)
                        if scene:
                            mainview = self.createView(scene)
                            subwindow = self.createSubWindow(mainview)
                            subwindow.showMaximized()
                            self.mdi.setActiveSubWindow(subwindow)
                            self.mdi.update()

            dropEvent.accept()
        else:
            dropEvent.ignore()

    def keyReleaseEvent(self, keyEvent):
        """
        Executed when a keyboard button is released from the scene.
        :type keyEvent: QKeyEvent
        """
        if keyEvent.key() == Qt.Key_Control:
            mainview = self.mdi.activeView
            if mainview:
                scene = mainview.scene()
                scene.setMode(DiagramMode.Idle)
        super().keyReleaseEvent(keyEvent)

    def showEvent(self, showEvent):
        """
        Executed when the window is shown.
        :type showEvent: QShowEvent
        """
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.activateWindow()
        self.raise_()

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def createScene(self, width, height):
        """
        Create and return an empty scene.
        :type width: int
        :type height: int
        :rtype: DiagramScene
        """
        scene = DiagramScene(self)
        scene.setSceneRect(QRectF(-width / 2, -height / 2, width, height))
        scene.setItemIndexMethod(DiagramScene.NoIndex)
        connect(scene.itemAdded, self.itemAdded)
        connect(scene.modeChanged, self.sceneModeChanged)
        connect(scene.selectionChanged, self.sceneSelectionChanged)
        self.undogroup.addStack(scene.undostack)
        return scene

    def createSceneFromGrapholFile(self, filepath):
        """
        Create a new scene by loading the given Graphol file.
        :type filepath: str
        :rtype: DiagramScene
        """
        worker = GrapholLoader(self, filepath)

        try:
            worker.run()
        except Exception as e:
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/error'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle('Load failed!')
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText('Failed to load {}!'.format(os.path.basename(filepath)))
            msgbox.setDetailedText(''.join(format_exception(type(e), e, e.__traceback__)))
            msgbox.exec_()
            return None
        else:
            return worker.scene

    def createSubWindow(self, mainview):
        """
        Create a MdiSubWindow displaying the given main view.
        :type mainview: MainView
        :rtype: MdiSubWindow
        """
        subwindow = self.mdi.addSubWindow(MdiSubWindow(mainview))
        subwindow.updateWindowTitle()
        scene = mainview.scene()
        connect(self.documentSaved, subwindow.documentSaved)
        connect(scene.undostack.cleanChanged, subwindow.undoStackCleanChanged)
        connect(subwindow.closeAborted, self.subWindowCloseAborted)
        connect(subwindow.closed, self.subWindowClosed)
        return subwindow

    def createView(self, scene):
        """
        Create a new main view displaying the given scene.
        :type scene: DiagramScene
        :rtype: MainView
        """
        view = MainView(self, scene)
        view.centerOn(0, 0)
        connect(scene.updated, view.updateView)
        return view

    def exportPath(self, path=None, name=None):
        """
        Bring up the 'Export' file dialog and returns the selected filepath.
        Will return None in case the user hit the 'Cancel' button to abort the operation.
        :type path: str
        :type name: str
        :rtype: tuple
        """
        dialog = SaveFile(path=path, parent=self)
        dialog.setWindowTitle('Export')
        dialog.setNameFilters([Filetype.Owl.value, Filetype.Pdf.value])
        dialog.selectFile(name or 'Untitled')
        if dialog.exec_():
            return dialog.selectedFiles()[0], dialog.selectedNameFilter()
        return None

    def exportToOwl(self, scene, filepath):
        """
        Export the given scene in OWL syntax saving it in the given filepath.
        :type scene: DiagramScene
        :type filepath: str
        :rtype: bool
        """
        exportForm = OWLTranslationForm(scene, filepath, self)
        if exportForm.exec_() == OWLTranslationForm.Accepted:
            return True
        return False

    @staticmethod
    def exportToPdf(scene, filepath):
        """
        Export the given scene as PDF saving it in the given filepath.
        :type scene: DiagramScene
        :type filepath: str
        :rtype: bool
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

                # TURN CACHING OFF!
                for item in scene.items():
                    if item.node or item.edge:
                        item.setCacheMode(QGraphicsItem.NoCache)

                # RENDER THE SCENE
                scene.render(painter, source=shape)

                # TURN CACHING ON!
                for item in scene.items():
                    if item.node or item.edge:
                        item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

                painter.end()
                return True

        return False

    def focusDocument(self, document):
        """
        Move the focus on the subwindow containing the given document.
        Will return True if the subwindow has been focused, False otherwise.
        :type document: T <= DiagramScene | File | str
        :rtype: bool
        """
        if isinstance(document, DiagramScene):
            document = document.document.path
        elif isinstance(document, File):
            document = document.path
        for subwindow in self.mdi.subWindowList():
            scene = subwindow.widget().scene()
            if scene.document.path and scene.document.path == document:
                self.mdi.setActiveSubWindow(subwindow)
                self.mdi.update()
                return True
        return False

    def insertRecentDocument(self, path):
        """
        Add the given document to the recent document list.
        :type path: str
        """
        try:
            self.recentDocument.remove(path)
        except ValueError:
            pass
        finally:
            self.recentDocument.insert(0, path)
            self.recentDocument = self.recentDocument[:DiagramScene.RecentNum]
            self.refreshRecentDocument()

    def openFile(self, filepath):
        """
        Open a Graphol document creating the scene and attaching it to the MDI area.
        :type filepath: str
        """
        if not self.focusDocument(filepath):
            scene = self.createSceneFromGrapholFile(filepath)
            if scene:
                mainview = self.createView(scene)
                subwindow = self.createSubWindow(mainview)
                subwindow.showMaximized()
                self.mdi.setActiveSubWindow(subwindow)
                self.mdi.update()

    def refreshRecentDocument(self):
        """
        Update the recent document action list.
        """
        num = min(len(self.recentDocument), DiagramScene.RecentNum)
        for i in range(num):
            name = '&{} {}'.format(i + 1, os.path.basename(os.path.normpath(self.recentDocument[i])))
            self.actionsOpenRecentDocument[i].setText(name)
            self.actionsOpenRecentDocument[i].setData(self.recentDocument[i])
            self.actionsOpenRecentDocument[i].setVisible(True)
        for i in range(num, DiagramScene.RecentNum):
            self.actionsOpenRecentDocument[i].setVisible(False)
        self.recentDocumentSeparator.setVisible(num > 0)

    def saveFile(self, scene, filepath):
        """
        Save the given scene to the corresponding given filepath.
        Will return True if the save has been performed, False otherwise.
        :type scene: DiagramScene
        :type filepath: str
        :rtype: bool
        """
        worker = GrapholExporter(scene)

        try:
            worker.run()
            scene.document.write(worker.export(indent=2), filepath)
        except Exception as e:
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/error'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle('Save failed!')
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText('Failed to save document to {}!'.format(os.path.basename(filepath)))
            msgbox.setDetailedText(''.join(format_exception(type(e), e, e.__traceback__)))
            msgbox.exec_()
            return False
        else:
            return True

    def savePath(self, path=None, name=None):
        """
        Bring up the 'Save' file dialog and returns the selected filepath.
        Will return None in case the user hit the 'Cancel' button to abort the operation.
        :type path: str
        :type name: str
        :rtype: str
        """
        dialog = SaveFile(path=path, parent=self)
        dialog.setNameFilters([Filetype.Graphol.value])
        dialog.selectFile(name or 'Untitled')
        if dialog.exec_():
            return dialog.selectedFiles()[0]
        return None

    def setWindowTitle(self, s=None):
        """
        Set the main window title.
        :type s: T <= str | None
        """
        super().setWindowTitle('{} - {} {}'.format(s, APPNAME, VERSION) if s else '{} {}'.format(APPNAME, VERSION))