# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
import sys
import traceback
import webbrowser

from collections import OrderedDict

from PyQt5.QtCore import Qt, QSettings, QFile, QIODevice, QSizeF, QRectF
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QPainter, QPageSize
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QMainWindow, QAction, QStatusBar, QMessageBox, QDialog, QStyle
from PyQt5.QtWidgets import QMenu, QToolButton, QUndoGroup
from PyQt5.QtXml import QDomDocument

from eddy import __version__ as version, __appname__ as appname, __organization__ as organization
from eddy.commands import CommandComposeAxiom, CommandDecomposeAxiom, CommandItemsMultiRemove
from eddy.commands import CommandNodeLabelMove, CommandNodeLabelEdit, CommandEdgeBreakpointDel, CommandRefactor
from eddy.commands import CommandNodeSetZValue, CommandNodeHexagonSwitchTo, CommandNodeValueDomainSelectDatatype
from eddy.commands import CommandNodeSquareChangeRestriction, CommandNodeSetSpecial, CommandNodeChangeBrush
from eddy.commands import CommandEdgeInclusionToggleComplete, CommandEdgeInputToggleFunctional, CommandEdgeSwap
from eddy.datatypes import Color, File, DiagramMode, FileType, Restriction, Special, XsdDatatype
from eddy.dialogs import AboutDialog, CardinalityRestrictionForm, RenameForm
from eddy.dialogs import OpenFileDialog, PreferencesDialog, SaveFileDialog, ScenePropertiesDialog
from eddy.exceptions import ParseError
from eddy.functions import connect, disconnect, getPath, make_colored_icon, make_shaded_icon
from eddy.items import Item, __mapping__ as mapping
from eddy.items import UnionNode, EnumerationNode, ComplementNode, RoleChainNode, IntersectionNode
from eddy.items import RoleInverseNode, DisjointUnionNode, DatatypeRestrictionNode
from eddy.utils import Clipboard
from eddy.widgets import DockWidget, Navigator, Overview, Palette
from eddy.widgets import MdiArea, MdiSubWindow
from eddy.widgets import DiagramScene
from eddy.widgets import MainView
from eddy.widgets import ZoomControl


class MainWindow(QMainWindow):
    """
    This class implements Eddy's main window.
    """
    MaxRecentDocuments = 5
    MinHeight = 600
    MinWidth = 1024

    documentLoaded = pyqtSignal('QGraphicsScene')
    documentSaved = pyqtSignal('QGraphicsScene')

    def __init__(self, parent=None):
        """
        Initialize the application main window.
        :param parent: the parent widget.
        """
        super().__init__(parent)

        self.abortQuit = False
        self.clipboard = Clipboard()
        self.undogroup = QUndoGroup()
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, organization, appname)

        ################################################################################################################
        #                                                                                                              #
        #   CREATE MENUS                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        self.menuFile = self.menuBar().addMenu("&File")
        self.menuEdit = self.menuBar().addMenu("&Edit")
        self.menuView = self.menuBar().addMenu("&View")
        self.menuHelp = self.menuBar().addMenu("&Help")

        ################################################################################################################
        #                                                                                                              #
        #   CREATE TOOLBARS                                                                                            #
        #                                                                                                              #
        ################################################################################################################

        self.toolbar = self.addToolBar('Toolbar')

        ################################################################################################################
        #                                                                                                              #
        #   CREATE WIDGETS                                                                                             #
        #                                                                                                              #
        ################################################################################################################

        self.mdi = MdiArea()
        self.navigator = Navigator()
        self.overview = Overview()
        self.palette_ = Palette()
        self.zoomctrl = ZoomControl()

        ################################################################################################################
        #                                                                                                              #
        #   CREATE DOCK WIDGETS                                                                                        #
        #                                                                                                              #
        ################################################################################################################

        self.dockNavigator = DockWidget('Navigator', self.navigator, self)
        self.dockOverview = DockWidget('Overview', self.overview, self)
        self.dockPalette = DockWidget('Palette', self.palette_, self)

        ################################################################################################################
        #                                                                                                              #
        #   CREATE ICONS                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        self.iconBringToFront = make_shaded_icon(':/icons/bring-to-front')
        self.iconClose = make_shaded_icon(':/icons/close')
        self.iconColorFill = make_shaded_icon(':/icons/color-fill')
        self.iconCopy = make_shaded_icon(':/icons/copy')
        self.iconCreate = make_shaded_icon(':/icons/create')
        self.iconCut = make_shaded_icon(':/icons/cut')
        self.iconDelete = make_shaded_icon(':/icons/delete')
        self.iconGrid = make_shaded_icon(':/icons/grid')
        self.iconLabel = make_shaded_icon(':/icons/label')
        self.iconLink = make_shaded_icon(':/icons/link')
        self.iconNew = make_shaded_icon(':/icons/new')
        self.iconOpen = make_shaded_icon(':/icons/open')
        self.iconPaste = make_shaded_icon(':/icons/paste')
        self.iconPalette = make_shaded_icon(':/icons/appearance')
        self.iconPreferences = make_shaded_icon(':/icons/preferences')
        self.iconPrint = make_shaded_icon(':/icons/print')
        self.iconQuit = make_shaded_icon(':/icons/quit')
        self.iconRedo = make_shaded_icon(':/icons/redo')
        self.iconRefactor = make_shaded_icon(':/icons/refactor')
        self.iconRefresh = make_shaded_icon(':/icons/refresh')
        self.iconSave = make_shaded_icon(':/icons/save')
        self.iconSaveAs = make_shaded_icon(':/icons/save')
        self.iconSelectAll = make_shaded_icon(':/icons/select-all')
        self.iconSendToBack = make_shaded_icon(':/icons/send-to-back')
        self.iconStarFilled = make_shaded_icon(':/icons/star-filled')
        self.iconSwapHorizontal = make_shaded_icon(':/icons/swap-horizontal')
        self.iconSwapVertical = make_shaded_icon(':/icons/swap-vertical')
        self.iconUndo = make_shaded_icon(':/icons/undo')
        self.iconZoom = make_shaded_icon(':/icons/zoom')
        self.iconZoomIn = make_shaded_icon(':/icons/zoom-in')
        self.iconZoomOut = make_shaded_icon(':/icons/zoom-out')

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
        for i in range(MainWindow.MaxRecentDocuments):
            action = QAction(self)
            action.setVisible(False)
            connect(action.triggered, self.openRecentDocument)
            self.actionsOpenRecentDocument.append(action)

        self.actionSaveDocument = QAction('Save', self)
        self.actionSaveDocument.setIcon(self.iconSave)
        self.actionSaveDocument.setShortcut(QKeySequence.Save)
        self.actionSaveDocument.setStatusTip('Save the current diagram')
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
        self.actionOpenPreferences.setStatusTip('Open {} preferences'.format(appname))
        connect(self.actionOpenPreferences.triggered, self.openPreferences)

        if not sys.platform.startswith('darwin'):
            self.actionOpenPreferences.setIcon(self.iconPreferences)

        self.actionQuit = QAction('Quit', self)
        self.actionQuit.setStatusTip('Quit {}'.format(appname))
        self.actionQuit.setShortcut(QKeySequence.Quit)
        connect(self.actionQuit.triggered, self.close)

        if not sys.platform.startswith('darwin'):
            self.actionQuit.setIcon(self.iconQuit)

        self.actionAbout = QAction('About {}'.format(appname), self)
        self.actionAbout.setShortcut(QKeySequence.HelpContents)
        connect(self.actionAbout.triggered, self.about)

        self.actionSapienzaWeb = QAction('DIAG - Sapienza university', self)
        self.actionSapienzaWeb.setIcon(self.iconLink)
        connect(self.actionSapienzaWeb.triggered, lambda: webbrowser.open('http://www.diag.uniroma1.it/en'))

        self.actionGrapholWeb = QAction('Graphol homepage', self)
        self.actionGrapholWeb.setIcon(self.iconLink)
        connect(self.actionGrapholWeb.triggered, lambda: webbrowser.open('http://www.diag.uniroma1.it/~graphol/'))

        ## DIAGRAM SCENE
        self.actionOpenSceneProperties = QAction('Properties...', self)
        self.actionOpenSceneProperties.setIcon(self.iconPreferences)
        connect(self.actionOpenSceneProperties.triggered, self.openSceneProperties)

        self.actionSnapToGrid = QAction('Snap to grid', self)
        self.actionSnapToGrid.setIcon(self.iconGrid)
        self.actionSnapToGrid.setStatusTip('Snap diagram elements to the grid')
        self.actionSnapToGrid.setCheckable(True)
        self.actionSnapToGrid.setChecked(self.settings.value('scene/snap_to_grid', False, bool))
        self.actionSnapToGrid.setEnabled(False)
        connect(self.actionSnapToGrid.triggered, self.toggleSnapToGrid)

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
            action.setIcon(make_colored_icon(size, size, color.value))
            action.setCheckable(False)
            action.setData(color)
            connect(action.triggered, self.changeNodeBrush)
            self.actionsChangeNodeBrush.append(action)

        self.actionResetLabelPosition = QAction('Reset label position', self)
        self.actionResetLabelPosition.setIcon(self.iconRefresh)
        connect(self.actionResetLabelPosition.triggered, self.resetLabelPosition)

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
            action.setIcon(make_colored_icon(size, size, color.value))
            action.setCheckable(False)
            action.setData(color)
            connect(action.triggered, self.refactorBrush)
            self.actionsRefactorBrush.append(action)

        ## ROLE NODE
        self.actionComposeAsymmetricRole = QAction('Asymmetric Role', self)
        self.actionComposeAsymmetricRole.setCheckable(True)
        connect(self.actionComposeAsymmetricRole.triggered, self.composeAsymmetricRole)

        self.actionComposeIrreflexiveRole = QAction('Irreflexive Role', self)
        self.actionComposeIrreflexiveRole.setCheckable(True)
        connect(self.actionComposeIrreflexiveRole.triggered, self.composeIrreflexiveRole)

        self.actionComposeReflexiveRole = QAction('Reflexive Role', self)
        self.actionComposeReflexiveRole.setCheckable(True)
        connect(self.actionComposeReflexiveRole.triggered, self.composeReflexiveRole)

        self.actionComposeSymmetricRole = QAction('Symmetric Role', self)
        self.actionComposeSymmetricRole.setCheckable(True)
        connect(self.actionComposeSymmetricRole.triggered, self.composeSymmetricRole)

        self.actionComposeTransitiveRole = QAction('Transitive Role', self)
        self.actionComposeTransitiveRole.setCheckable(True)
        connect(self.actionComposeTransitiveRole.triggered, self.composeTransitiveRole)

        ## ROLE / ATTRIBUTE NODES
        self.actionComposeFunctional = QAction('Functional', self)
        self.actionComposeInverseFunctional = QAction('Inverse Functional', self)
        self.actionComposePropertyDomain = QAction('Property Domain', self)
        self.actionComposePropertyRange = QAction('Property Range', self)

        connect(self.actionComposeFunctional.triggered, self.composeFunctional)
        connect(self.actionComposeInverseFunctional.triggered, self.composeInverseFunctional)
        connect(self.actionComposePropertyDomain.triggered, self.composePropertyDomain)
        connect(self.actionComposePropertyRange.triggered, self.composePropertyRange)

        ## DOMAIN / RANGE RESTRICTION
        self.actionsRestrictionChange = []
        for restriction in Restriction:
            action = QAction(restriction.value, self)
            action.setCheckable(True)
            action.setData(restriction)
            connect(action.triggered, self.changeDomainRangeRestriction)
            self.actionsRestrictionChange.append(action)

        ## VALUE DOMAIN NODE
        self.actionsChangeValueDomainDatatype = []
        for datatype in XsdDatatype:
            action = QAction(datatype.value, self)
            action.setCheckable(True)
            action.setData(datatype)
            connect(action.triggered, self.changeValueDomainDatatype)
            self.actionsChangeValueDomainDatatype.append(action)

        ## HEXAGON BASED CONSTRUCTOR NODES
        data = OrderedDict()
        data[ComplementNode] = 'Complement'
        data[DisjointUnionNode] = 'Disjoint union'
        data[DatatypeRestrictionNode] = 'Datatype restriction'
        data[EnumerationNode] = 'Enumeration'
        data[IntersectionNode] = 'Intersection'
        data[RoleChainNode] = 'Role chain'
        data[RoleInverseNode] = 'Role inverse'
        data[UnionNode] = 'Union'

        self.actionsSwitchHexagonNode = []
        for k, v in data.items():
            action = QAction(v, self)
            action.setCheckable(True)
            action.setData(k)
            connect(action.triggered, self.switchHexagonNode)
            self.actionsSwitchHexagonNode.append(action)

        ## EDGES
        self.actionRemoveEdgeBreakpoint = QAction('Remove breakpoint', self)
        self.actionRemoveEdgeBreakpoint.setIcon(self.iconDelete)
        connect(self.actionRemoveEdgeBreakpoint.triggered, self.removeBreakpoint)

        self.actionSwapEdge = QAction('Swap', self)
        self.actionSwapEdge.setIcon(self.iconSwapHorizontal)
        self.actionSwapEdge.setShortcut('CTRL+ALT+S' if sys.platform.startswith('win32') else 'ALT+S')
        connect(self.actionSwapEdge.triggered, self.swapEdge)

        self.actionToggleEdgeComplete = QAction('Complete', self)
        self.actionToggleEdgeComplete.setShortcut('CTRL+ALT+C' if sys.platform.startswith('win32') else 'ALT+C')
        self.actionToggleEdgeComplete.setCheckable(True)
        connect(self.actionToggleEdgeComplete.triggered, self.toggleEdgeComplete)

        self.actionToggleEdgeFunctional = QAction('Functional', self)
        self.actionToggleEdgeFunctional.setShortcut('CTRL+ALT+F' if sys.platform.startswith('win32') else 'ALT+F')
        self.actionToggleEdgeFunctional.setCheckable(True)
        connect(self.actionToggleEdgeFunctional.triggered, self.toggleEdgeFunctional)

        self.addAction(self.actionSwapEdge)
        self.addAction(self.actionToggleEdgeComplete)
        self.addAction(self.actionToggleEdgeFunctional)
        
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
        for i in range(MainWindow.MaxRecentDocuments):
            self.menuFile.addAction(self.actionsOpenRecentDocument[i])
        self.updateRecentDocuments()

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
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionOpenPreferences)

        self.menuView.addAction(self.actionSnapToGrid)
        self.menuView.addSeparator()
        self.menuView.addAction(self.toolbar.toggleViewAction())
        self.menuView.addSeparator()
        self.menuView.addAction(self.dockNavigator.toggleViewAction())
        self.menuView.addAction(self.dockOverview.toggleViewAction())
        self.menuView.addAction(self.dockPalette.toggleViewAction())

        self.menuHelp.addAction(self.actionAbout)

        if not sys.platform.startswith('darwin'):
            self.menuHelp.addSeparator()

        self.menuHelp.addAction(self.actionSapienzaWeb)
        self.menuHelp.addAction(self.actionGrapholWeb)

        ## NODE GENERIC MENU
        self.menuChangeNodeBrush = QMenu('Select color')
        self.menuChangeNodeBrush.setIcon(self.iconColorFill)
        for action in self.actionsChangeNodeBrush:
            self.menuChangeNodeBrush.addAction(action)

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

        ## ROLE NODE
        self.menuRoleNodeCompose = QMenu('Compose')
        self.menuRoleNodeCompose.setIcon(self.iconCreate)
        self.menuRoleNodeCompose.addAction(self.actionComposeAsymmetricRole)
        self.menuRoleNodeCompose.addAction(self.actionComposeIrreflexiveRole)
        self.menuRoleNodeCompose.addAction(self.actionComposeReflexiveRole)
        self.menuRoleNodeCompose.addAction(self.actionComposeSymmetricRole)
        self.menuRoleNodeCompose.addAction(self.actionComposeTransitiveRole)
        self.menuRoleNodeCompose.addSeparator()
        self.menuRoleNodeCompose.addAction(self.actionComposeFunctional)
        self.menuRoleNodeCompose.addAction(self.actionComposeInverseFunctional)
        self.menuRoleNodeCompose.addSeparator()
        self.menuRoleNodeCompose.addAction(self.actionComposePropertyDomain)
        self.menuRoleNodeCompose.addAction(self.actionComposePropertyRange)

        ## ATTRIBUTE NODE
        self.menuAttributeNodeCompose = QMenu('Compose')
        self.menuAttributeNodeCompose.setIcon(self.iconCreate)
        self.menuAttributeNodeCompose.addAction(self.actionComposeFunctional)
        self.menuAttributeNodeCompose.addSeparator()
        self.menuAttributeNodeCompose.addAction(self.actionComposePropertyDomain)
        self.menuAttributeNodeCompose.addSeparator()
        self.menuAttributeNodeCompose.addAction(self.actionComposePropertyDomain)
        self.menuAttributeNodeCompose.addAction(self.actionComposePropertyRange)

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

        ## HEXAGON BASED NODES
        self.menuHexagonNodeSwitch = QMenu('Switch to')
        self.menuHexagonNodeSwitch.setIcon(self.iconRefresh)
        for action in self.actionsSwitchHexagonNode:
            self.menuHexagonNodeSwitch.addAction(action)

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

        self.changeNodeBrushButton = QToolButton()
        self.changeNodeBrushButton.setIcon(self.iconColorFill)
        self.changeNodeBrushButton.setMenu(self.menuChangeNodeBrush)
        self.changeNodeBrushButton.setPopupMode(QToolButton.InstantPopup)
        self.changeNodeBrushButton.setEnabled(False)

        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.changeNodeBrushButton)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionSnapToGrid)

        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.zoomctrl.buttonZoomOut)
        self.toolbar.addWidget(self.zoomctrl.buttonZoomIn)
        self.toolbar.addWidget(self.zoomctrl.buttonZoomLevelChange)

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

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE MAIN WINDOW                                                                                      #
        #                                                                                                              #
        ################################################################################################################

        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockPalette)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockNavigator)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockOverview)
        self.setCentralWidget(self.mdi)
        self.setMinimumSize(MainWindow.MinWidth, MainWindow.MinHeight)
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setWindowTitle()

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
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
                    scene.undostack.push(CommandNodeSetZValue(scene=scene, node=selected, zValue=zValue))

    @pyqtSlot()
    def changeDomainRangeRestriction(self):
        """
        Change domain/range restriction types.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            node = next(filter(lambda x: x.isItem(Item.DomainRestrictionNode,
                                                  Item.RangeRestrictionNode), scene.selectedNodes()), None)
            if node:
                restriction = action.data()
                if restriction == Restriction.cardinality:
                    form = CardinalityRestrictionForm()
                    if form.exec_() == CardinalityRestrictionForm.Accepted:
                        cardinality = dict(min=form.minCardinalityValue, max=form.maxCardinalityValue)
                        scene.undostack.push(CommandNodeSquareChangeRestriction(scene, node, restriction, cardinality))
                else:
                    scene.undostack.push(CommandNodeSquareChangeRestriction(scene, node, action.data()))

    @pyqtSlot()
    def changeNodeBrush(self):
        """
        Change the brush of selected nodes.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            selected = scene.selectedNodes()
            selected = [x for x in selected if x.isItem(Item.AttributeNode, Item.ConceptNode,
                                                        Item.IndividualNode, Item.RoleNode,
                                                        Item.ValueDomainNode, Item.ValueRestrictionNode)]
            if selected:
                scene.undostack.push(CommandNodeChangeBrush(scene, selected, action.data()))

    @pyqtSlot()
    def changeValueDomainDatatype(self):
        """
        Change the datatype of the selected value-domain node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            node = next(filter(lambda x: x.isItem(Item.ValueDomainNode), scene.selectedNodes()), None)
            if node:
                scene.undostack.push(CommandNodeValueDomainSelectDatatype(scene, node, action.data()))

    @pyqtSlot()
    def closeActiveSubWindow(self):
        """
        Close the currently active subwindow.
        """
        subwindow = self.mdi.activeSubWindow()
        if subwindow:
            subwindow.close()

    @pyqtSlot()
    def composeAsymmetricRole(self):
        """
        Compose an asymmetric role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isItem(Item.RoleNode), scene.selectedNodes()), None)
            if node:
                action = self.sender()
                if action:
                    if action.isChecked():
                        if not node.asymmetric:
                            items = scene.asymmetricRoleAxiomComposition(node)
                            nodes = {x for x in items if x.node}
                            edges = {x for x in items if x.edge}
                            kwargs = {
                                'name': 'compose asymmetric role',
                                'scene': scene,
                                'source': node,
                                'nodes': nodes,
                                'edges': edges,
                            }
                            scene.undostack.push(CommandComposeAxiom(**kwargs))
                    else:
                        if node.asymmetric:
                            kwargs = {
                                'name': 'decompose asymmetric role',
                                'scene': scene,
                                'source': node,
                                'items': node.asymmetryPath,
                            }
                            scene.undostack.push(CommandDecomposeAxiom(**kwargs))

    @pyqtSlot()
    def composeFunctional(self):
        """
        Makes the selected role/attribute node functional.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            args = Item.RoleNode, Item.AttributeNode
            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:
                items = scene.functionalAxiomComposition(node)
                nodes = {x for x in items if x.node}
                edges = {x for x in items if x.edge}
                kwargs = {
                    'name': 'compose functional {}'.format(node.name),
                    'scene': scene,
                    'source': node,
                    'nodes': nodes,
                    'edges': edges,
                }
                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composeInverseFunctional(self):
        """
        Makes the selected role node inverse functional.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            args = Item.RoleNode, Item.AttributeNode
            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:
                items = scene.inverseFunctionalAxiomComposition(node)
                nodes = {x for x in items if x.node}
                edges = {x for x in items if x.edge}
                kwargs = {
                    'name': 'compose inverse functional {}'.format(node.name),
                    'scene': scene,
                    'source': node,
                    'nodes': nodes,
                    'edges': edges,
                }
                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composeIrreflexiveRole(self):
        """
        Compose an irreflexive role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isItem(Item.RoleNode), scene.selectedNodes()), None)
            if node:
                action = self.sender()
                if action:
                    if action.isChecked():
                        if not node.irreflexive:
                            items = scene.irreflexiveRoleAxiomComposition(node)
                            nodes = {x for x in items if x.node}
                            edges = {x for x in items if x.edge}
                            kwargs = {
                                'name': 'compose irreflexive role',
                                'scene': scene,
                                'source': node,
                                'nodes': nodes,
                                'edges': edges,
                            }
                            scene.undostack.push(CommandComposeAxiom(**kwargs))
                    else:
                        if node.irreflexive:
                            kwargs = {
                                'name': 'decompose irreflexive role',
                                'scene': scene,
                                'source': node,
                                'items': node.irreflexivityPath,
                            }
                            scene.undostack.push(CommandDecomposeAxiom(**kwargs))

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
                items = scene.propertyDomainAxiomComposition(node)
                nodes = {x for x in items if x.node}
                edges = {x for x in items if x.edge}
                kwargs = {
                    'name': 'compose {} property domain'.format(node.name),
                    'scene': scene,
                    'source': node,
                    'nodes': nodes,
                    'edges': edges,
                }
                scene.undostack.push(CommandComposeAxiom(**kwargs))

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
                items = scene.propertyRangeAxiomComposition(node)
                nodes = {x for x in items if x.node}
                edges = {x for x in items if x.edge}
                kwargs = {
                    'name': 'compose {} property range'.format(node.name),
                    'scene': scene,
                    'source': node,
                    'nodes': nodes,
                    'edges': edges,
                }
                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composeReflexiveRole(self):
        """
        Compose a reflexive role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isItem(Item.RoleNode), scene.selectedNodes()), None)
            if node:
                action = self.sender()
                if action:
                    if action.isChecked():
                        if not node.reflexive:
                            items = scene.reflexiveRoleAxiomComposition(node)
                            nodes = {x for x in items if x.node}
                            edges = {x for x in items if x.edge}
                            kwargs = {
                                'name': 'compose reflexive role',
                                'scene': scene,
                                'source': node,
                                'nodes': nodes,
                                'edges': edges,
                            }
                            scene.undostack.push(CommandComposeAxiom(**kwargs))
                    else:
                        if node.reflexive:
                            kwargs = {
                                'name': 'decompose reflexive role',
                                'scene': scene,
                                'source': node,
                                'items': node.reflexivityPath,
                            }
                            scene.undostack.push(CommandDecomposeAxiom(**kwargs))

    @pyqtSlot()
    def composeSymmetricRole(self):
        """
        Compose a symmetric role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isItem(Item.RoleNode), scene.selectedNodes()), None)
            if node:
                action = self.sender()
                if action:
                    if action.isChecked():
                        if not node.symmetric:
                            items = scene.symmetricRoleAxiomComposition(node)
                            nodes = {x for x in items if x.node}
                            edges = {x for x in items if x.edge}
                            kwargs = {
                                'name': 'compose symmetric role',
                                'scene': scene,
                                'source': node,
                                'nodes': nodes,
                                'edges': edges,
                            }
                            scene.undostack.push(CommandComposeAxiom(**kwargs))
                    else:
                        if node.symmetric:
                            kwargs = {
                                'name': 'decompose symmetric role',
                                'scene': scene,
                                'source': node,
                                'items': node.symmetryPath,
                            }
                            scene.undostack.push(CommandDecomposeAxiom(**kwargs))

    @pyqtSlot()
    def composeTransitiveRole(self):
        """
        Compose a transitive role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isItem(Item.RoleNode), scene.selectedNodes()), None)
            if node:
                action = self.sender()
                if action:
                    if action.isChecked():
                        if not node.transitive:
                            items = scene.transitiveRoleAxiomComposition(node)
                            nodes = {x for x in items if x.node}
                            edges = {x for x in items if x.edge}
                            kwargs = {
                                'name': 'compose transitive role',
                                'scene': scene,
                                'source': node,
                                'nodes': nodes,
                                'edges': edges,
                            }
                            scene.undostack.push(CommandComposeAxiom(**kwargs))
                    else:
                        if node.transitive:
                            kwargs = {
                                'name': 'decompose transitive role',
                                'scene': scene,
                                'source': node,
                                'items': node.transitivityPath,
                            }
                            scene.undostack.push(CommandDecomposeAxiom(**kwargs))

    @pyqtSlot('QGraphicsScene')
    def documentLoadedOrSaved(self, scene):
        """
        Executed when a document is loaded or saved from/to a Graphol file.
        :param scene: the diagram scene instance containing the document.
        """
        self.addRecentDocument(scene.document.path)
        self.setWindowTitle(scene.document.name)

    @pyqtSlot()
    def exportDocument(self):
        """
        Export the currently open graphol document.
        """
        scene = self.mdi.activeScene
        if scene:
            res = self.exportFilePath(name=scene.document.name)
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
    def itemCut(self):
        """
        Cut selected items from the active scene.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            scene.clipboardPasteOffsetX = 0
            scene.clipboardPasteOffsetY = 0

            self.clipboard.update(scene)
            self.refreshActionsState()

            selection = scene.selectedItems()
            if selection:
                selection.extend([x for item in selection if item.node for x in item.edges if x not in selection])
                scene.undostack.push(CommandItemsMultiRemove(scene=scene, collection=selection))

    @pyqtSlot()
    def itemCopy(self):
        """
        Make a copy of selected items.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            scene.clipboardPasteOffsetX = Clipboard.PasteOffsetX
            scene.clipboardPasteOffsetY = Clipboard.PasteOffsetY
            self.clipboard.update(scene)
            self.refreshActionsState()

    @pyqtSlot()
    def itemPaste(self):
        """
        Paste previously copied items.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            if not self.clipboard.empty():
                # TODO: figure out how to send context menu position to the clipboard
                self.clipboard.paste(scene)

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
                scene.undostack.push(CommandItemsMultiRemove(scene=scene, collection=selection))

    @pyqtSlot('QGraphicsItem', int)
    def itemInserted(self, item, modifiers):
        """
        Executed after an item insertion process ends.
        :param item: the inserted item.
        :param modifiers: keyboard modifiers held during item insertion.
        """
        if not modifiers & Qt.ControlModifier:
            self.palette_.button(item.item).setChecked(False)
            scene = self.mdi.activeScene
            if scene:
                scene.setMode(DiagramMode.Idle)
                scene.command = None

    @pyqtSlot()
    def newDocument(self):
        """
        Create a new empty document and add it to the MDI Area.
        """
        size = self.settings.value('diagram/size', 5000, int)
        scene = self.createScene(size, size)
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
        dialog = OpenFileDialog(getPath('~'))
        dialog.setNameFilters([FileType.graphol.value])
        if dialog.exec_():
            filepath = dialog.selectedFiles()[0]
            if not self.focusDocument(filepath):
                scene = self.createSceneFromGrapholFile(filepath)
                if scene:
                    mainview = self.createView(scene)
                    subwindow = self.createSubWindow(mainview)
                    subwindow.showMaximized()
                    self.mdi.setActiveSubWindow(subwindow)
                    self.mdi.update()

    @pyqtSlot()
    def openNodeProperties(self):
        """
        Executed when node properties needs to be displayed.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            collection = scene.selectedNodes()
            if collection:
                node = collection[0]
                prop = node.propertiesDialog()
                prop.exec_()

    @pyqtSlot()
    def openPreferences(self):
        """
        Open the preferences dialog.
        """
        preferences = PreferencesDialog(self.centralWidget())
        preferences.exec_()
        
    @pyqtSlot()
    def openRecentDocument(self):
        """
        Open the clicked recent document.
        """
        action = self.sender()
        if action:
            if not self.focusDocument(action.data()):
                scene = self.createSceneFromGrapholFile(action.data())
                if scene:
                    mainview = self.createView(scene)
                    subwindow = self.createSubWindow(mainview)
                    subwindow.showMaximized()
                    self.mdi.setActiveSubWindow(subwindow)
                    self.mdi.update()

    @pyqtSlot()
    def openSceneProperties(self):
        """
        Executed when scene properties needs to be displayed.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            prop = ScenePropertiesDialog(scene=scene)
            prop.exec_()

    @pyqtSlot(int)
    def paletteButtonClicked(self, button_id):
        """
        Executed whenever a Palette button is clicked.
        :param button_id: the button id.
        """
        scene = self.mdi.activeScene
        if not scene:
            self.palette_.clear()
        else:
            scene.clearSelection()
            button = self.palette_.button(button_id)
            self.palette_.clear(button)
            if not button.isChecked():
                scene.setMode(DiagramMode.Idle)
            else:
                if Item.ConceptNode <= button_id < Item.InclusionEdge:
                    scene.setMode(DiagramMode.NodeInsert, button.property('item'))
                elif Item.InclusionEdge <= button_id <= Item.InstanceOfEdge:
                    scene.setMode(DiagramMode.EdgeInsert, button.property('item'))

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
            args = Item.ConceptNode, Item.RoleNode, \
                   Item.AttributeNode, Item.IndividualNode, \
                   Item.ValueRestrictionNode

            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:
                action = self.sender()
                scene.undostack.push(CommandNodeChangeBrush(scene, scene.nodesByLabel[node.labelText()], action.data()))

    @pyqtSlot()
    def refactorName(self):
        """
        Rename the label of the currently selected node and all the occurrences sharing the same label text.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            args = Item.ConceptNode, Item.RoleNode, \
                   Item.AttributeNode, Item.IndividualNode, \
                   Item.ValueRestrictionNode

            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:

                form = RenameForm(node, self)
                if form.exec_() == RenameForm.Accepted:

                    if node.labelText() != form.renameField.value():

                        commands = []
                        for n in scene.nodesByLabel[node.labelText()]:
                            command = CommandNodeLabelEdit(scene=scene, node=n)
                            command.end(form.renameField.value())
                            commands.append(command)

                        kwargs = {
                            'name': 'rename {} node{}'.format(len(commands), 's' if len(commands) > 1 else ''),
                            'scene': scene,
                            'commands': commands,
                        }

                        scene.undostack.push(CommandRefactor(**kwargs))

    @pyqtSlot()
    def refreshActionsState(self):
        """
        Update actions enabling/disabling them when needed.
        """
        wind = undo = clip = edge = node = pred = False

        # we need to check if we have at least one subwindow because if the program
        # simply lose the focus, self.mdi.activeScene will return None even though we
        # do not need to disable actions because we will have scene in the background
        if self.mdi.subWindowList():

            scene = self.mdi.activeScene
            if scene:

                nodes = scene.selectedNodes()
                edges = scene.selectedEdges()

                wind = True
                undo = not self.undogroup.isClean()
                clip = not self.clipboard.empty()
                edge = len(edges) != 0
                node = len(nodes) != 0
                pred = next(filter(lambda x: x.isItem(Item.AttributeNode,
                                                      Item.ConceptNode,
                                                      Item.IndividualNode,
                                                      Item.RoleNode,
                                                      Item.ValueDomainNode,
                                                      Item.ValueRestrictionNode), nodes), None) is not None

        self.actionBringToFront.setEnabled(node)
        self.actionCloseActiveSubWindow.setEnabled(wind)
        self.actionCut.setEnabled(node)
        self.actionCopy.setEnabled(node)
        self.actionDelete.setEnabled(node or edge)
        self.actionExportDocument.setEnabled(wind)
        self.actionPaste.setEnabled(clip)
        self.actionPrintDocument.setEnabled(wind)
        self.actionSaveDocument.setEnabled(undo)
        self.actionSaveDocumentAs.setEnabled(wind)
        self.actionSelectAll.setEnabled(wind)
        self.actionSendToBack.setEnabled(node)
        self.actionSnapToGrid.setEnabled(wind)
        self.changeNodeBrushButton.setEnabled(pred)
        self.zoomctrl.setEnabled(wind)

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
                scene.undostack.push(CommandEdgeBreakpointDel(scene=scene, edge=edge, index=breakpoint))

    @pyqtSlot()
    def resetLabelPosition(self):
        """
        Reset selected node label to default position.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: hasattr(x, 'label'), scene.selectedNodes()), None)
            if node and node.label.movable:
                command = CommandNodeLabelMove(scene=scene, node=node, label=node.label)
                command.end(pos=node.label.defaultPos())
                scene.undostack.push(command)
                node.label.updatePos()

    @pyqtSlot()
    def saveDocument(self):
        """
        Save the currently open graphol document.
        """
        scene = self.mdi.activeScene
        if scene:
            filepath = scene.document.path or self.saveFilePath(name=scene.document.name)
            if filepath:
                saved = self.saveSceneToGrapholFile(scene, filepath)
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
            filepath = self.saveFilePath(name=scene.document.name)
            if filepath:
                saved = self.saveSceneToGrapholFile(scene, filepath)
                if saved:
                    scene.undostack.setClean()
                    self.documentSaved.emit(scene)

    @pyqtSlot(DiagramMode)
    def sceneModeChanged(self, mode):
        """
        Executed when the scene operation mode changes.
        :param mode: the scene operation mode.
        """
        if mode not in (DiagramMode.NodeInsert, DiagramMode.EdgeInsert):
            self.palette_.clear()

    @pyqtSlot()
    def selectAll(self):
        """
        Select all the items in the scene.
        """
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
                    scene.undostack.push(CommandNodeSetZValue(scene=scene, node=selected, zValue=zValue))

    @pyqtSlot()
    def setSpecialNode(self):
        """
        Set the special type of the selected concept node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            args = Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.ValueDomainNode
            node = next(filter(lambda x: x.isItem(*args), scene.selectedNodes()), None)
            if node:
                special = action.data() if node.special is not action.data() else None
                scene.undostack.push(CommandNodeSetSpecial(scene, node, special))

    @pyqtSlot('QMdiSubWindow')
    def subWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :param subwindow: the subwindow which got the focus (0 if there is no subwindow).
        """
        if subwindow:

            mainview = subwindow.widget()
            scene = mainview.scene()
            scene.undostack.setActive()

            self.navigator.setView(mainview)
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
                self.navigator.clearView()
                self.overview.clearView()
                self.setWindowTitle()

        self.refreshActionsState()

    @pyqtSlot('QMdiSubWindow')
    def subWindowCloseEventIgnored(self, subwindow):
        """
        Executed when the close event of an MDI subwindow is aborted.
        :param subwindow: the subwindow whose closeEvent has been interrupted.
        """
        self.abortQuit = True
        self.mdi.setActiveSubWindow(subwindow)

    @pyqtSlot()
    def swapEdge(self):
        """
        Swap the selected edges by inverting source/target points.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = [edge for edge in scene.selectedEdges() if edge.isValid(edge.target, edge.source)]
            if selected:
                scene.undostack.push(CommandEdgeSwap(scene=scene, edges=selected))

    @pyqtSlot()
    def switchHexagonNode(self):
        """
        Switch the selected hexagon based constructor node to a different type.
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
                    scene.undostack.push(CommandNodeHexagonSwitchTo(scene=scene, node1=node, node2=xnode))

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
                func = sum(edge.complete for edge in selected) <= len(selected) / 2
                data = {edge: {'from': edge.complete, 'to': func} for edge in selected}
                scene.undostack.push(CommandEdgeInclusionToggleComplete(scene=scene, data=data))

    @pyqtSlot()
    def toggleEdgeFunctional(self):
        """
        Toggle the 'functional' attribute for all the selected Input edges.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = [item for item in scene.selectedEdges() if item.isItem(Item.InputEdge)]
            if selected:
                func = sum(edge.functional for edge in selected) <= len(selected) / 2
                data = {edge: {'from': edge.functional, 'to': func} for edge in selected}
                scene.undostack.push(CommandEdgeInputToggleFunctional(scene=scene, data=data))

    @pyqtSlot()
    def toggleSnapToGrid(self):
        """
        Toggle snap to grid setting.
        """
        self.settings.setValue('scene/snap_to_grid', self.actionSnapToGrid.isChecked())
        scene = self.mdi.activeScene
        if scene:
            scene.update()

    @pyqtSlot(bool)
    def undoGroupCleanChanged(self, clean):
        """
        Executed when the clean state of the active undostack changes.
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

    def keyReleaseEvent(self, keyEvent):
        """
        Executed when a keyboard button is released from the scene.
        :param keyEvent: the keyboard event instance.
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
        documents = self.settings.value('document/recent_documents', None, str)

        try:
            documents.remove(path)
        except ValueError:
            pass
        finally:
            documents.insert(0, path) # insert on top of the list
            documents = documents[:MainWindow.MaxRecentDocuments]

        self.settings.setValue('document/recent_documents', documents)
        self.updateRecentDocuments()

    def createScene(self, width, height):
        """
        Create and return an empty scene.
        :param width: the width of the scene rect.
        :param height: the height of the scene rect
        :return: the initialized diagram scene.
        :rtype: DiagramScene
        """
        scene = DiagramScene(self)
        scene.setSceneRect(QRectF(-width / 2, -height / 2, width, height))
        scene.setItemIndexMethod(DiagramScene.NoIndex)
        connect(scene.nodeInserted, self.itemInserted)
        connect(scene.edgeInserted, self.itemInserted)
        connect(scene.modeChanged, self.sceneModeChanged)
        connect(scene.selectionChanged, self.refreshActionsState)
        self.undogroup.addStack(scene.undostack)
        return scene

    def createSceneFromGrapholFile(self, filepath):
        """
        Create a new scene by loading the given Graphol file.
        :param filepath: the path of the file to be loaded.
        :rtype: DiagramScene
        """
        file = QFile(filepath)

        try:

            if not file.open(QIODevice.ReadOnly):
                raise IOError('file not found: {}'.format(filepath))

            document = QDomDocument()
            if not document.setContent(file):
                raise ParseError('could not initialized DOM document')

            root = document.documentElement()

            # read graph initialization data
            graph = root.firstChildElement('graph')
            w = int(graph.attribute('width', self.settings.value('diagram/size', '5000', str)))
            h = int(graph.attribute('height', self.settings.value('diagram/size', '5000', str)))

            # create the scene
            scene = self.createScene(width=w, height=h)
            scene.document.path = filepath
            scene.document.edited = os.path.getmtime(filepath)

            # add the nodes
            nodes_from_graphol = graph.elementsByTagName('node')
            for i in range(nodes_from_graphol.count()):
                E = nodes_from_graphol.at(i).toElement()
                C = mapping[E.attribute('type')]
                node = C.fromGraphol(scene=scene, E=E)
                scene.addItem(node)
                scene.uniqueID.update(node.id)

            # add the edges
            edges_from_graphol = graph.elementsByTagName('edge')
            for i in range(edges_from_graphol.count()):
                E = edges_from_graphol.at(i).toElement()
                C = mapping[E.attribute('type')]
                edge = C.fromGraphol(scene=scene, E=E)
                scene.addItem(edge)
                scene.uniqueID.update(edge.id)

        except Exception as e:
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowIcon(QIcon(':/images/eddy'))
            box.setWindowTitle('Load FAILED')
            box.setText('Could not open Graphol document: {}!'.format(filepath))
            # format the traceback so it prints nice
            most_recent_calls = traceback.format_tb(sys.exc_info()[2])
            most_recent_calls = [x.strip().replace('\n', '') for x in most_recent_calls]
            # set the traceback as detailed text so it won't occupy too much space in the dialog box
            box.setDetailedText('{}: {}\n\n{}'.format(e.__class__.__name__, str(e), '\n'.join(most_recent_calls)))
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return None
        else:
            self.documentLoaded.emit(scene)
            return scene
        finally:
            file.close()

    def createSubWindow(self, mainview):
        """
        Create a MdiSubWindow displaying the given main view.
        :param mainview: the mainview to be rendered in the subwindow.
        :rtype: MdiSubWindow
        """
        subwindow = self.mdi.addSubWindow(MdiSubWindow(mainview))
        subwindow.updateTitle()
        scene = mainview.scene()
        connect(self.documentSaved, subwindow.documentSaved)
        connect(scene.undostack.cleanChanged, subwindow.undoStackCleanChanged)
        connect(subwindow.closeEventIgnored, self.subWindowCloseEventIgnored)
        return subwindow

    @staticmethod
    def createView(scene):
        """
        Create a new main view displaying the given scene.
        :param scene: the scene to be added in the view.
        :rtype: MainView
        """
        view = MainView(scene)
        view.setViewportUpdateMode(MainView.FullViewportUpdate)
        view.centerOn(0, 0)
        view.setDragMode(MainView.NoDrag)
        return view

    @staticmethod
    def exportFilePath(path=None, name=None):
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

    @staticmethod
    def saveFilePath(path=None, name=None):
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

    @staticmethod
    def saveSceneToGrapholFile(scene, filepath):
        """
        Save the given scene to the corresponding given filepath.
        Will return True if the save has been performed, False otherwise.
        :param scene: the scene to be saved.
        :param filepath: the path where to save the scene.
        :rtype: bool
        """
        try:
            document = scene.toGraphol()
            scene.document.write(document.toString(4), filepath)
        except Exception:
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowIcon(QIcon(':/images/eddy'))
            box.setWindowTitle('Save FAILED')
            box.setText('Could not export diagram!')
            box.setDetailedText(traceback.format_exc())
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return False
        else:
            return True

    def setWindowTitle(self, p_str=None):
        """
        Set the main window title.
        :param p_str: the prefix for the window title
        """
        T = '{} - {} {}'.format(p_str, appname, version) if p_str else '{} {}'.format(appname, version)
        super().setWindowTitle(T)

    def updateRecentDocuments(self):
        """
        Update the recent document action list.
        """
        documents = self.settings.value('document/recent_documents', None, str)
        numRecentDocuments = min(len(documents), MainWindow.MaxRecentDocuments)

        for i in range(numRecentDocuments):
            filename = '&{} {}'.format(i + 1, os.path.basename(os.path.normpath(documents[i])))
            self.actionsOpenRecentDocument[i].setText(filename)
            self.actionsOpenRecentDocument[i].setData(documents[i])
            self.actionsOpenRecentDocument[i].setVisible(True)

        # turn off actions that we don't need
        for i in range(numRecentDocuments, MainWindow.MaxRecentDocuments):
            self.actionsOpenRecentDocument[i].setVisible(False)

        # show the separator only if we got at least one recent document
        self.recentDocumentSeparator.setVisible(numRecentDocuments > 0)