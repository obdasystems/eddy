# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
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

from PyQt5.QtCore import Qt, QSettings, QByteArray, QEvent, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPixmap, QCursor
from PyQt5.QtGui import QIcon, QKeySequence, QPainterPath
from PyQt5.QtWidgets import QMainWindow, QAction, QStatusBar, QToolButton
from PyQt5.QtWidgets import QMenu, QApplication, QMessageBox
from PyQt5.QtWidgets import QStyle, QFileDialog

from eddy import APPNAME, DIAG_HOME, GRAPHOL_HOME, ORGANIZATION, BUG_TRACKER
from eddy.core.commands.common import CommandComposeAxiom
from eddy.core.commands.common import CommandItemsRemove
from eddy.core.commands.common import CommandItemsTranslate
from eddy.core.commands.edges import CommandEdgeBreakpointRemove
from eddy.core.commands.edges import CommandEdgeSwap
from eddy.core.commands.edges import CommandEdgeToggleEquivalence
from eddy.core.commands.nodes import CommandNodeLabelChange
from eddy.core.commands.nodes import CommandNodeLabelMove
from eddy.core.commands.nodes import CommandNodeOperatorSwitchTo
from eddy.core.commands.nodes import CommandNodeSetBrush
from eddy.core.commands.nodes import CommandNodeSetDepth
from eddy.core.datatypes.graphol import Identity
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.graphol import Restriction
from eddy.core.datatypes.graphol import Special
from eddy.core.datatypes.misc import Color, DiagramMode
from eddy.core.datatypes.owl import Datatype, Facet
from eddy.core.datatypes.system import Platform, File
from eddy.core.diagram import Diagram
from eddy.core.exporters.graphml import GraphmlExporter
from eddy.core.exporters.graphol import GrapholExporter
from eddy.core.exporters.project import ProjectExporter
from eddy.core.functions.fsystem import fexists, fcopy, fremove
from eddy.core.functions.misc import snapF, first, format_exception, cutR, uncapitalize
from eddy.core.functions.path import expandPath, isSubPath, uniquePath, shortPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.common import AbstractItem
from eddy.core.loaders.graphml import GraphmlLoader
from eddy.core.loaders.graphol import GrapholLoader
from eddy.core.loaders.project import ProjectLoader
from eddy.core.qt import Icon, ColoredIcon
from eddy.core.utils.clipboard import Clipboard

from eddy.lang import gettext as _

from eddy.ui.dialogs.about import About
from eddy.ui.dialogs.diagram import NewDiagramDialog
from eddy.ui.dialogs.diagram import RenameDiagramDialog
from eddy.ui.dialogs.forms import CardinalityRestrictionForm
from eddy.ui.dialogs.forms import RefactorNameForm
from eddy.ui.dialogs.forms import ValueForm
from eddy.ui.dialogs.preferences import PreferencesDialog
from eddy.ui.dialogs.progress import BusyProgressDialog
from eddy.ui.dialogs.properties import PropertyFactory
from eddy.ui.menus import MenuFactory
from eddy.ui.widgets.dock import DockWidget
from eddy.ui.widgets.explorer import OntologyExplorer
from eddy.ui.widgets.explorer import ProjectExplorer
from eddy.ui.widgets.info import Info
from eddy.ui.widgets.mdi import MdiArea
from eddy.ui.widgets.mdi import MdiSubWindow
from eddy.ui.widgets.overview import Overview
from eddy.ui.widgets.palette import Palette
from eddy.ui.widgets.view import DiagramView
from eddy.ui.widgets.zoom import Zoom


class MainWindow(QMainWindow):
    """
    This class implements Eddy's main window.
    """
    sgnClosed = pyqtSignal()
    sgnQuit = pyqtSignal()

    def __init__(self, path, parent=None):
        """
        Initialize the application main window.
        :type path: str
        :type parent: QWidget
        """
        super().__init__(parent)

        #############################################
        # CREATE MENUS
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        self.menuFile = self.menuBar().addMenu(_('MENU_FILE'))
        self.menuEdit = self.menuBar().addMenu(_('MENU_EDIT'))
        self.menuView = self.menuBar().addMenu(_('MENU_VIEW'))
        self.menuTools = self.menuBar().addMenu(_('MENU_TOOLS'))
        self.menuHelp = self.menuBar().addMenu(_('MENU_HELP'))

        self.menuCompose = QMenu(_('MENU_COMPOSE'))
        self.menuRefactorBrush = QMenu(_('MENU_REFACTOR_BRUSH'))
        self.menuRefactor = QMenu(_('MENU_REFACTOR'))
        self.menuSetBrush = QMenu(_('MENU_SET_BRUSH'))
        self.menuSetDatatype = QMenu(_('MENU_SET_DATATYPE'))
        self.menuSetFacet = QMenu(_('MENU_SET_FACET'))
        self.menuSetIndividualAs = QMenu(_('MENU_SET_INDIVIDUAL_AS'))
        self.menuSetPropertyRestriction = QMenu(_('MENU_SET_PROPERTY_RESTRICTION'))
        self.menuSetSpecial = QMenu(_('MENU_SET_SPECIAL'))
        self.menuSwitchOperator = QMenu(_('MENU_SWITCH_OPERATOR'))
        self.menuToolbars = QMenu(_('MENU_TOOLBARS'))

        #############################################
        # CREATE TOOLBARS
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        self.toolbarDocument = self.addToolBar(_('TOOLBAR_DOCUMENT'))
        self.toolbarDocument.setObjectName('toolbarDocument')
        self.toolbarEditor = self.addToolBar(_('TOOLBAR_EDITOR'))
        self.toolbarEditor.setObjectName('toolbarEditor')
        self.toolbarView = self.addToolBar(_('TOOLBAR_VIEW'))
        self.toolbarView.setObjectName('toolbarView')
        self.toolbarGraphol = self.addToolBar(_('TOOLBAR_GRAPHOL'))
        self.toolbarGraphol.setObjectName('toolbarGraphol')

        #############################################
        # CREATE WIDGETS
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        self.info = Info(self)
        self.mdi = MdiArea(self)
        self.ontologyExplorer = OntologyExplorer(self)
        self.overview = Overview(self)
        self.palette_ = Palette(self)
        self.projectExplorer = ProjectExplorer(self)
        self.zoom = Zoom(self.toolbarView)

        self.dockInfo = DockWidget(_('DOCK_INFO'), ':/icons/18/info', self)
        self.dockOntologyExplorer = DockWidget(_('DOCK_ONTOLOGY_EXPLORER'), ':/icons/18/explore', self)
        self.dockOverview = DockWidget(_('DOCK_OVERVIEW'), ':/icons/18/zoom', self)
        self.dockPalette = DockWidget(_('DOCK_PALETTE'), ':/icons/18/palette', self)
        self.dockProjectExplorer = DockWidget(_('DOCK_PROJECT_EXPLORER'), ':/icons/18/storage', self)

        self.buttonSetBrush = QToolButton()

        #############################################
        # LOAD THE GIVEN PROJECT
        #################################

        self.project = ProjectLoader(path, self).run()
        connect(self.project.undoStack.cleanChanged, self.doUpdateState)

        #############################################
        # CREATE UTILITIES
        #################################

        self.clipboard = Clipboard(self)
        self.menuFactory = MenuFactory(self)
        self.propertyFactory = PropertyFactory(self)

        #############################################
        # CREATE ICONS
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        self.iconBottom = Icon(':/icons/24/bottom')
        self.iconBringToFront = Icon(':/icons/24/bring-to-front')
        self.iconCenterFocus = Icon(':/icons/24/center-focus')
        self.iconClose = Icon(':/icons/24/close')
        self.iconColorFill = Icon(':/icons/24/color-fill')
        self.iconCopy = Icon(':/icons/24/copy')
        self.iconCreate = Icon(':/icons/24/create')
        self.iconCut = Icon(':/icons/24/cut')
        self.iconDelete = Icon(':/icons/24/delete')
        self.iconGrid = Icon(':/icons/24/grid')
        self.iconHelp = Icon(':/icons/24/help')
        self.iconLabel = Icon(':/icons/24/label')
        self.iconLicense = Icon(':/icons/24/license')
        self.iconLink = Icon(':/icons/24/link')
        self.iconNew = Icon(':/icons/24/new')
        self.iconOpen = Icon(':/icons/24/open')
        self.iconPaste = Icon(':/icons/24/paste')
        self.iconPalette = Icon(':/icons/24/palette')
        self.iconPreferences = Icon(':/icons/24/preferences')
        self.iconPrint = Icon(':/icons/24/print')
        self.iconPropertyDomain = Icon(':/icons/24/property-domain')
        self.iconPropertyRange = Icon(':/icons/24/property-range')
        self.iconQuit = Icon(':/icons/24/quit')
        self.iconRedo = Icon(':/icons/24/redo')
        self.iconRefactor = Icon(':/icons/24/refactor')
        self.iconRefresh = Icon(':/icons/24/refresh')
        self.iconSave = Icon(':/icons/24/save')
        self.iconSaveAs = Icon(':/icons/24/save')
        self.iconSelectAll = Icon(':/icons/24/select-all')
        self.iconSendToBack = Icon(':/icons/24/send-to-back')
        self.iconSpellCheck = Icon(':/icons/24/spell-check')
        self.iconStarFilled = Icon(':/icons/24/star-filled')
        self.iconSwapHorizontal = Icon(':/icons/24/swap-horizontal')
        self.iconSwapVertical = Icon(':/icons/24/swap-vertical')
        self.iconUndo = Icon(':/icons/24/undo')
        self.iconTop = Icon(':/icons/24/top')

        #############################################
        # CREATE ACTIONS
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        self.actionUndo = self.project.undoStack.createUndoAction(self)
        self.actionRedo = self.project.undoStack.createRedoAction(self)
        self.actionNewDiagram = QAction(_('ACTION_NEW_DIAGRAM_N'), self)
        self.actionOpen = QAction(_('ACTION_OPEN_N'), self)
        self.actionSave = QAction(_('ACTION_SAVE_N'), self)
        self.actionSaveAs = QAction(_('ACTION_SAVE_AS_N'), self)
        self.actionImport = QAction(_('ACTION_IMPORT_N'), self)
        self.actionExport = QAction(_('ACTION_EXPORT_N'), self)
        self.actionPrint = QAction(_('ACTION_PRINT_N'), self)
        self.actionOpenPreferences = QAction(_('ACTION_OPEN_PREFERENCES_N'), self)
        self.actionQuit = QAction(_('ACTION_QUIT_N'), self)
        self.actionCloseProject = QAction(_('ACTION_CLOSE_PROJECT_N'), self)
        self.actionAbout = QAction(_('ACTION_ABOUT', APPNAME), self)
        self.actionDiagWeb = QAction(_('ACTION_DIAG_WEBSITE_N'), self)
        self.actionGrapholWeb = QAction(_('ACTION_GRAPHOL_WEBSITE_N'), self)
        self.actionSyntaxCheck = QAction(_('ACTION_SYNTAX_CHECK_N'), self)
        self.actionCenterDiagram = QAction(_('ACTION_CENTER_DIAGRAM_N'), self)
        self.actionDiagramProperties = QAction(_('ACTION_DIAGRAM_PROPERTIES_N'), self)
        self.actionSnapToGrid = QAction(_('ACTION_SNAP_TO_GRID_N'), self)
        self.actionCut = QAction(_('ACTION_CUT_N'), self)
        self.actionCopy = QAction(_('ACTION_COPY_N'), self)
        self.actionPaste = QAction(_('ACTION_PASTE_N'), self)
        self.actionDelete = QAction(_('ACTION_DELETE_N'), self)
        self.actionBringToFront = QAction(_('ACTION_BRING_TO_FRONT_N'), self)
        self.actionSendToBack = QAction(_('ACTION_SEND_TO_BACK_N'), self)
        self.actionSelectAll = QAction(_('ACTION_SELECT_ALL_N'), self)
        self.actionNodeProperties = QAction(_('ACTION_NODE_PROPERTIES_N'), self)
        self.actionRelocateLabel = QAction(_('ACTION_RELOCATE_LABEL_N'), self)
        self.actionRefactorName = QAction(_('ACTION_REFACTOR_NAME_N'), self)
        self.actionComposePropertyDomain = QAction(_('ACTION_COMPOSE_PROPERTY_DOMAIN_N'), self)
        self.actionComposePropertyRange = QAction(_('ACTION_COMPOSE_PROPERTY_RANGE_N'), self)
        self.actionRemoveEdgeBreakpoint = QAction(_('ACTION_REMOVE_EDGE_BREAKPOINT_N'), self)
        self.actionSwapEdge = QAction(_('ACTION_EDGE_SWAP_N'), self)
        self.actionToggleEdgeEquivalence = QAction(_('ACTION_EDGE_TOGGLE_EQUIVALENCE_N'), self)

        self.actionsRefactorBrush = []
        self.actionsSetBrush = []
        self.actionsSetSpecial = []
        self.actionsSetPropertyRestriction = []
        self.actionsSetDatatype = []
        self.actionsSetFacet = []
        self.actionsSetIndividualAs = []
        self.actionsSwitchOperator = []

        #############################################
        # CONFIGURE MAIN WINDOW
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        self.setAcceptDrops(True)
        self.setCentralWidget(self.mdi)
        self.setDockOptions(MainWindow.AnimatedDocks|MainWindow.AllowTabbedDocks)
        self.setMinimumSize(1140, 720)
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setWindowTitle(self.project)

        self.configureActions()
        self.configureWidgets()
        self.configureMenus()
        self.configureStatusBar()
        self.configureToolbars()
        self.configureState()

    #############################################
    #   MAIN WINDOW CONFIGURATION
    #################################

    def configureActions(self):
        """
        Configure previously initialized actions.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        #############################################
        # APPLICATION GENERIC
        #################################

        self.actionOpenPreferences.setShortcut(QKeySequence.Preferences)
        self.actionOpenPreferences.setData(PreferencesDialog)
        connect(self.actionOpenPreferences.triggered, self.doOpenDialog)

        if Platform.identify() is not Platform.Darwin:
            self.actionOpenPreferences.setIcon(self.iconPreferences)

        self.actionQuit.setStatusTip(_('ACTION_QUIT_S', APPNAME))
        self.actionQuit.setShortcut(QKeySequence.Quit)
        connect(self.actionQuit.triggered, self.doQuit)

        if Platform.identify() is not Platform.Darwin:
            self.actionQuit.setIcon(self.iconQuit)

        self.actionAbout.setShortcut(QKeySequence.HelpContents)
        self.actionAbout.setStatusTip(_('ACTION_ABOUT_S', APPNAME))
        self.actionAbout.setData(About)
        connect(self.actionAbout.triggered, self.doOpenDialog)

        if Platform.identify() is not Platform.Darwin:
            self.actionAbout.setIcon(self.iconHelp)

        self.actionDiagWeb.setIcon(self.iconLink)
        self.actionDiagWeb.setData(DIAG_HOME)
        connect(self.actionDiagWeb.triggered, self.doOpenURL)

        self.actionGrapholWeb.setIcon(self.iconLink)
        self.actionGrapholWeb.setData(GRAPHOL_HOME)
        connect(self.actionGrapholWeb.triggered, self.doOpenURL)

        #############################################
        # PROJECT / DIAGRAM MANAGEMENT
        #################################

        self.actionNewDiagram.setIcon(self.iconNew)
        self.actionNewDiagram.setShortcut(QKeySequence.New)
        self.actionNewDiagram.setStatusTip(_('ACTION_NEW_DIAGRAM_S'))
        connect(self.actionNewDiagram.triggered, self.doNewDiagram)

        self.actionOpen.setIcon(self.iconOpen)
        self.actionOpen.setShortcut(QKeySequence.Open)
        self.actionOpen.setStatusTip(_('ACTION_OPEN_S'))
        connect(self.actionOpen.triggered, self.doOpen)

        self.actionCloseProject.setIcon(self.iconClose)
        self.actionCloseProject.setShortcut(QKeySequence.Close)
        self.actionCloseProject.setStatusTip(_('ACTION_CLOSE_PROJECT_S'))
        connect(self.actionCloseProject.triggered, self.doCloseProject)

        self.actionSave.setIcon(self.iconSave)
        self.actionSave.setShortcut(QKeySequence.Save)
        self.actionSave.setStatusTip(_('ACTION_SAVE_S'))
        self.actionSave.setEnabled(False)
        connect(self.actionSave.triggered, self.doSave)

        self.actionSaveAs.setIcon(self.iconSaveAs)
        self.actionSaveAs.setShortcut(QKeySequence.SaveAs)
        self.actionSaveAs.setStatusTip(_('ACTION_SAVE_AS'))
        self.actionSaveAs.setEnabled(False)
        connect(self.actionSaveAs.triggered, self.doSaveAs)

        self.actionImport.setStatusTip(_('ACTION_IMPORT_S'))
        connect(self.actionImport.triggered, self.doImport)

        self.actionExport.setStatusTip(_('ACTION_EXPORT_S'))
        self.actionExport.setEnabled(not self.project.isEmpty())
        connect(self.actionExport.triggered, self.doExport)

        self.actionPrint.setIcon(self.iconPrint)
        self.actionPrint.setStatusTip(_('ACTION_PRINT_S'))
        connect(self.actionPrint.triggered, self.doPrint)

        #############################################
        # PROJECT SPECIFIC
        #################################

        self.actionSyntaxCheck.setIcon(self.iconSpellCheck)
        self.actionSyntaxCheck.setStatusTip(_('ACTION_SYNTAX_CHECK_S'))
        connect(self.actionSyntaxCheck.triggered, self.doSyntaxCheck)

        #############################################
        # DIAGRAM SPECIFIC
        #################################

        self.actionUndo.setIcon(self.iconUndo)
        self.actionUndo.setShortcut(QKeySequence.Undo)
        self.actionRedo.setIcon(self.iconRedo)
        self.actionRedo.setShortcut(QKeySequence.Redo)

        self.actionCenterDiagram.setIcon(self.iconCenterFocus)
        self.actionCenterDiagram.setStatusTip(_('ACTION_CENTER_DIAGRAM_S'))
        self.actionCenterDiagram.setEnabled(False)
        connect(self.actionCenterDiagram.triggered, self.doCenterDiagram)

        self.actionDiagramProperties.setIcon(self.iconPreferences)
        connect(self.actionDiagramProperties.triggered, self.doOpenDiagramProperties)

        self.actionSnapToGrid.setIcon(self.iconGrid)
        self.actionSnapToGrid.setStatusTip(_('ACTION_SNAP_TO_GRID_S'))
        self.actionSnapToGrid.setCheckable(True)
        self.actionSnapToGrid.setEnabled(False)
        connect(self.actionSnapToGrid.triggered, self.doSnapToGrid)

        #############################################
        # ITEM GENERICS
        #################################

        self.actionCut.setIcon(self.iconCut)
        self.actionCut.setShortcut(QKeySequence.Cut)
        self.actionCut.setStatusTip(_('ACTION_CUT_S'))
        self.actionCut.setEnabled(False)
        connect(self.actionCut.triggered, self.doCut)

        self.actionCopy.setIcon(self.iconCopy)
        self.actionCopy.setShortcut(QKeySequence.Copy)
        self.actionCopy.setStatusTip(_('ACTION_COPY_S'))
        self.actionCopy.setEnabled(False)
        connect(self.actionCopy.triggered, self.doCopy)

        self.actionPaste.setIcon(self.iconPaste)
        self.actionPaste.setShortcut(QKeySequence.Paste)
        self.actionPaste.setStatusTip(_('ACTION_PASTE_S'))
        self.actionPaste.setEnabled(False)
        connect(self.actionPaste.triggered, self.doPaste)

        self.actionDelete.setIcon(self.iconDelete)
        self.actionDelete.setShortcut(QKeySequence.Delete)
        self.actionDelete.setStatusTip(_('ACTION_DELETE_S'))
        self.actionDelete.setEnabled(False)
        connect(self.actionDelete.triggered, self.doDelete)

        self.actionBringToFront.setIcon(self.iconBringToFront)
        self.actionBringToFront.setStatusTip(_('ACTION_BRING_TO_FRONT_S'))
        self.actionBringToFront.setEnabled(False)
        connect(self.actionBringToFront.triggered, self.doBringToFront)

        self.actionSendToBack.setIcon(self.iconSendToBack)
        self.actionSendToBack.setStatusTip(_('ACTION_SEND_TO_BACK_S'))
        self.actionSendToBack.setEnabled(False)
        connect(self.actionSendToBack.triggered, self.doSendToBack)

        self.actionSelectAll.setIcon(self.iconSelectAll)
        self.actionSelectAll.setShortcut(QKeySequence.SelectAll)
        self.actionSelectAll.setStatusTip(_('ACTION_SELECT_ALL_S'))
        self.actionSelectAll.setEnabled(False)
        connect(self.actionSelectAll.triggered, self.doSelectAll)

        #############################################
        # NODE GENERICS
        #################################
        
        self.actionNodeProperties.setIcon(self.iconPreferences)
        connect(self.actionNodeProperties.triggered, self.doOpenNodeProperties)
        
        self.actionRefactorName.setIcon(self.iconLabel)
        connect(self.actionRefactorName.triggered, self.doRefactorName)

        self.actionRelocateLabel.setIcon(self.iconRefresh)
        connect(self.actionRelocateLabel.triggered, self.doRelocateLabel)

        action = QAction(Special.Top.value, self)
        action.setData(Special.Top)
        action.setIcon(self.iconTop)
        connect(action.triggered, self.doSetNodeSpecial)
        self.actionsSetSpecial.append(action)
        action = QAction(Special.Bottom.value, self)
        action.setData(Special.Bottom)
        action.setIcon(self.iconBottom)
        connect(action.triggered, self.doSetNodeSpecial)
        self.actionsSetSpecial.append(action)

        for color in Color:
            size = self.style().pixelMetric(QStyle.PM_ToolBarIconSize)
            action = QAction(color.name, self)
            action.setIcon(ColoredIcon(size, size, color.value))
            action.setCheckable(False)
            action.setData(color)
            connect(action.triggered, self.doSetNodeBrush)
            self.actionsSetBrush.append(action)

        for color in Color:
            size = self.style().pixelMetric(QStyle.PM_ToolBarIconSize)
            action = QAction(color.name, self)
            action.setIcon(ColoredIcon(size, size, color.value))
            action.setCheckable(False)
            action.setData(color)
            connect(action.triggered, self.doRefactorBrush)
            self.actionsRefactorBrush.append(action)

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        self.actionComposePropertyDomain.setIcon(self.iconPropertyDomain)
        self.actionComposePropertyDomain.setData(Item.DomainRestrictionNode)
        connect(self.actionComposePropertyDomain.triggered, self.doComposePropertyExpression)

        self.actionComposePropertyRange.setIcon(self.iconPropertyRange)
        self.actionComposePropertyRange.setData(Item.RangeRestrictionNode)
        connect(self.actionComposePropertyRange.triggered, self.doComposePropertyExpression)

        #############################################
        # PROPERTY DOMAIN / RANGE SPECIFIC
        #################################

        for restriction in Restriction:
            action = QAction(restriction.value, self)
            action.setCheckable(True)
            action.setData(restriction)
            connect(action.triggered, self.doSetPropertyRestriction)
            self.actionsSetPropertyRestriction.append(action)

        #############################################
        # VALUE-DOMAIN SPECIFIC
        #################################

        for datatype in Datatype:
            action = QAction(datatype.value, self)
            action.setCheckable(True)
            action.setData(datatype)
            connect(action.triggered, self.doSetDatatype)
            self.actionsSetDatatype.append(action)

        #############################################
        # INDIVIDUAL SPECIFIC
        #################################

        for identity in (Identity.Instance, Identity.Value):
            action = QAction(identity.value, self)
            action.setData(identity)
            connect(action.triggered, self.doSetIndividualAs)
            self.actionsSetIndividualAs.append(action)

        #############################################
        # FACET SPECIFIC
        #################################

        for facet in Facet:
            action = QAction(facet.value, self)
            action.setCheckable(True)
            action.setData(facet)
            connect(action.triggered, self.doSetFacet)
            self.actionsSetFacet.append(action)

        #############################################
        # OPERATORS SPECIFIC
        #################################

        data = OrderedDict()
        data[Item.ComplementNode] = 'Complement'
        data[Item.DisjointUnionNode] = 'Disjoint union'
        data[Item.DatatypeRestrictionNode] = 'Datatype restriction'
        data[Item.EnumerationNode] = 'Enumeration'
        data[Item.IntersectionNode] = 'Intersection'
        data[Item.RoleChainNode] = 'Role chain'
        data[Item.RoleInverseNode] = 'Role inverse'
        data[Item.UnionNode] = 'Union'

        for k, v in data.items():
            action = QAction(v, self)
            action.setCheckable(True)
            action.setData(k)
            connect(action.triggered, self.doSwitchOperatorNode)
            self.actionsSwitchOperator.append(action)

        #############################################
        # EDGE SPECIFIC
        #################################

        self.actionRemoveEdgeBreakpoint.setIcon(self.iconDelete)
        connect(self.actionRemoveEdgeBreakpoint.triggered, self.doRemoveBreakpoint)

        self.actionToggleEdgeEquivalence.setShortcut('ALT+C')
        self.actionToggleEdgeEquivalence.setCheckable(True)
        connect(self.actionToggleEdgeEquivalence.triggered, self.doToggleEdgeEquivalence)

        self.actionSwapEdge.setIcon(self.iconSwapHorizontal)
        self.actionSwapEdge.setShortcut('ALT+S')
        connect(self.actionSwapEdge.triggered, self.doSwapEdge)

        self.addAction(self.actionSwapEdge)
        self.addAction(self.actionToggleEdgeEquivalence)

    def configureWidgets(self):
        """
        Configure previously initialized widgets.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        #############################################
        # CONFIGURE TOOLBAR WIDGETS
        #################################

        self.buttonSetBrush.setIcon(self.iconColorFill)
        self.buttonSetBrush.setMenu(self.menuSetBrush)
        self.buttonSetBrush.setPopupMode(QToolButton.InstantPopup)
        self.buttonSetBrush.setEnabled(False)

        #############################################
        # CONFIGURE DOCK WIDGETS
        #################################

        self.dockOntologyExplorer.installEventFilter(self)
        self.dockOntologyExplorer.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockOntologyExplorer.setObjectName('ontologyExplorer')
        self.dockOntologyExplorer.setWidget(self.ontologyExplorer)

        self.dockInfo.installEventFilter(self)
        self.dockInfo.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockInfo.setObjectName('info')
        self.dockInfo.setWidget(self.info)

        self.dockOverview.installEventFilter(self)
        self.dockOverview.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockOverview.setObjectName('overview')
        self.dockOverview.setWidget(self.overview)

        self.dockPalette.installEventFilter(self)
        self.dockPalette.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockPalette.setObjectName('palette')
        self.dockPalette.setWidget(self.palette_)

        self.dockProjectExplorer.installEventFilter(self)
        self.dockProjectExplorer.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockProjectExplorer.setObjectName('projectExplorer')
        self.dockProjectExplorer.setWidget(self.projectExplorer)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockPalette)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockProjectExplorer)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockOverview)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockInfo)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockOntologyExplorer)

        #############################################
        # CONFIGURE DOCK WIDGETS CONTROLS
        #################################

        for button in self.palette_.controls():
            self.dockPalette.addTitleBarButton(button)

        #############################################
        # CONFIGURE WIDGETS INSPECTIONS
        #################################

        self.info.browse(self.project)
        self.ontologyExplorer.browse(self.project)
        self.projectExplorer.browse(self.project)

        #############################################
        # CONFIGURE SIGNALS
        #################################

        connect(self.mdi.subWindowActivated, self.onSubWindowActivated)
        connect(self.palette_.sgnButtonClicked['QToolButton'], self.onPaletteClicked)
        connect(self.ontologyExplorer.sgnItemDoubleClicked['QGraphicsItem'], self.doFocusItem)
        connect(self.ontologyExplorer.sgnItemRightClicked['QGraphicsItem'], self.doFocusItem)
        connect(self.projectExplorer.sgnItemDoubleClicked['QGraphicsScene'], self.doFocusDiagram)

    def configureMenus(self):
        """
        Configure previously initialized menus.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        #############################################
        # MENU BAR RELATED
        #################################

        self.menuFile.addAction(self.actionNewDiagram)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionCloseProject)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionImport)
        self.menuFile.addAction(self.actionExport)

        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionPrint)
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
        self.menuEdit.addAction(self.actionSwapEdge)
        self.menuEdit.addAction(self.actionToggleEdgeEquivalence)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionSelectAll)
        self.menuEdit.addAction(self.actionCenterDiagram)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionOpenPreferences)

        self.menuView.addAction(self.actionSnapToGrid)
        self.menuView.addSeparator()
        self.menuView.addMenu(self.menuToolbars)
        self.menuView.addSeparator()
        self.menuView.addAction(self.dockInfo.toggleViewAction())
        self.menuView.addAction(self.dockOntologyExplorer.toggleViewAction())
        self.menuView.addAction(self.dockOverview.toggleViewAction())
        self.menuView.addAction(self.dockPalette.toggleViewAction())
        self.menuView.addAction(self.dockProjectExplorer.toggleViewAction())

        self.menuToolbars.addAction(self.toolbarDocument.toggleViewAction())
        self.menuToolbars.addAction(self.toolbarEditor.toggleViewAction())
        self.menuToolbars.addAction(self.toolbarGraphol.toggleViewAction())
        self.menuToolbars.addAction(self.toolbarView.toggleViewAction())

        self.menuTools.addAction(self.actionSyntaxCheck)

        self.menuHelp.addAction(self.actionAbout)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionDiagWeb)
        self.menuHelp.addAction(self.actionGrapholWeb)

        #############################################
        # NODE GENERIC
        #################################

        self.menuSetBrush.setIcon(self.iconColorFill)
        for action in self.actionsSetBrush:
            self.menuSetBrush.addAction(action)

        self.menuSetSpecial.setIcon(self.iconStarFilled)
        for action in self.actionsSetSpecial:
            self.menuSetSpecial.addAction(action)

        self.menuRefactorBrush.setIcon(self.iconColorFill)
        for action in self.actionsRefactorBrush:
            self.menuRefactorBrush.addAction(action)

        self.menuRefactor.setIcon(self.iconRefactor)
        self.menuRefactor.addAction(self.actionRefactorName)
        self.menuRefactor.addMenu(self.menuRefactorBrush)

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        self.menuCompose.setIcon(self.iconCreate)
        self.menuCompose.addAction(self.actionComposePropertyDomain)
        self.menuCompose.addAction(self.actionComposePropertyRange)

        #############################################
        # VALUE-DOMAIN SPECIFIC
        #################################

        self.menuSetDatatype.setIcon(self.iconRefresh)
        for action in self.actionsSetDatatype:
            self.menuSetDatatype.addAction(action)

        #############################################
        # FACET SPECIFIC
        #################################

        self.menuSetFacet.setIcon(self.iconRefresh)
        for action in self.actionsSetFacet:
            self.menuSetFacet.addAction(action)

        #############################################
        # PROPERTY DOMAIN / RANGE SPECIFIC
        #################################

        self.menuSetPropertyRestriction.setIcon(self.iconRefresh)
        for action in self.actionsSetPropertyRestriction:
            self.menuSetPropertyRestriction.addAction(action)

        #############################################
        # INDIVIDUAL SPECIFIC
        #################################

        self.menuSetIndividualAs.setIcon(self.iconRefresh)
        for action in self.actionsSetIndividualAs:
            self.menuSetIndividualAs.addAction(action)

        #############################################
        # OPERATORS SPECIFIC
        #################################

        self.menuSwitchOperator.setIcon(self.iconRefresh)
        for action in self.actionsSwitchOperator:
            self.menuSwitchOperator.addAction(action)
    
    def configureStatusBar(self):
        """
        Configure the status bar.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        statusbar = QStatusBar(self)
        statusbar.setSizeGripEnabled(False)
        self.setStatusBar(statusbar)
    
    def configureToolbars(self):
        """
        Configure previously initialized toolbars.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        self.toolbarDocument.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbarEditor.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbarView.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbarGraphol.setContextMenuPolicy(Qt.PreventContextMenu)

        self.toolbarDocument.addAction(self.actionNewDiagram)
        self.toolbarDocument.addAction(self.actionOpen)
        self.toolbarDocument.addAction(self.actionSave)
        self.toolbarDocument.addAction(self.actionPrint)

        self.toolbarEditor.addAction(self.actionUndo)
        self.toolbarEditor.addAction(self.actionRedo)
        self.toolbarEditor.addSeparator()
        self.toolbarEditor.addAction(self.actionCut)
        self.toolbarEditor.addAction(self.actionCopy)
        self.toolbarEditor.addAction(self.actionPaste)
        self.toolbarEditor.addAction(self.actionDelete)
        self.toolbarEditor.addSeparator()
        self.toolbarEditor.addAction(self.actionBringToFront)
        self.toolbarEditor.addAction(self.actionSendToBack)
        self.toolbarEditor.addWidget(self.buttonSetBrush)

        self.toolbarView.addAction(self.actionSnapToGrid)
        self.toolbarView.addAction(self.actionCenterDiagram)
        self.toolbarView.addSeparator()
        self.toolbarView.addWidget(self.zoom.buttonZoomOut)
        self.toolbarView.addWidget(self.zoom.buttonZoomIn)
        self.toolbarView.addWidget(self.zoom.buttonZoomReset)

        self.toolbarGraphol.addAction(self.actionSyntaxCheck)

    def configureState(self):
        """
        Configure application state by reading the preferences file.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        settings = QSettings(ORGANIZATION, APPNAME)
        self.restoreGeometry(settings.value('mainwindow/geometry', QByteArray(), QByteArray))
        self.restoreState(settings.value('mainwindow/state', QByteArray(), QByteArray))
        self.actionSnapToGrid.setChecked(settings.value('diagram/grid', False, bool))

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def doBringToFront(self):
        """
        Bring the selected item to the top of the diagram.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            for node in diagram.selectedNodes():
                zValue = 0
                for item in [x for x in node.collidingItems() if x.type() is not Item.Label]:
                    if item.zValue() >= zValue:
                        zValue = item.zValue() + 0.2
                if zValue != node.zValue():
                    self.project.undoStack.push(CommandNodeSetDepth(diagram, node, zValue))

    @pyqtSlot()
    def doCenterDiagram(self):
        """
        Center the active diagram.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            items = diagram.items()
            if items:
                R1 = diagram.sceneRect()
                R2 = diagram.visibleRect(margin=0)
                moveX = snapF(((R1.right() - R2.right()) - (R2.left() - R1.left())) / 2, Diagram.GridSize)
                moveY = snapF(((R1.bottom() - R2.bottom()) - (R2.top() - R1.top())) / 2, Diagram.GridSize)
                if moveX or moveY:
                    items = [x for x in items if x.isNode() or x.isEdge()]
                    command = CommandItemsTranslate(diagram, items, moveX, moveY, _('COMMAND_DIAGRAM_CENTER'))
                    self.project.undoStack.push(command)
                    self.mdi.activeView.centerOn(0, 0)

    @pyqtSlot()
    def doCloseProject(self):
        """
        Close the currently active subwindow.
        """
        self.doSave()
        self.close()
        self.sgnClosed.emit()

    @pyqtSlot()
    def doComposePropertyExpression(self):
        """
        Compose a property domain using the selected role/attribute node.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            supported = {Item.RoleNode, Item.AttributeNode}
            node = first([x for x in diagram.selectedNodes() if x.type() in supported])
            if node:
                action = self.sender()
                item = action.data()
                name = _('COMMAND_COMPOSE_DOMAIN_RANGE_RESTRICTION', node.shortname, item.shortname)
                items = diagram.propertyComposition(node, item)
                nodes = {x for x in items if x.isNode()}
                edges = {x for x in items if x.isEdge()}
                self.project.undoStack.push(CommandComposeAxiom(name, diagram, node, nodes, edges))

    @pyqtSlot()
    def doCopy(self):
        """
        Make a copy of selected items.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            diagram.pasteX = Clipboard.PasteOffsetX
            diagram.pasteY = Clipboard.PasteOffsetY
            self.clipboard.update(diagram)
            self.doUpdateState()

    @pyqtSlot()
    def doCut(self):
        """
        Cut selected items from the active diagram.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            diagram.pasteX = 0
            diagram.pasteY = 0
            self.clipboard.update(diagram)
            self.doUpdateState()
            items = diagram.selectedItems()
            if items:
                items.extend([x for item in items if item.isNode() for x in item.edges if x not in items])
                self.project.undoStack.push(CommandItemsRemove(diagram, items))

    @pyqtSlot()
    def doDelete(self):
        """
        Delete the currently selected items from the active diagram.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            items = diagram.selectedItems()
            if items:
                items.extend([x for item in items if item.isNode() for x in item.edges if x not in items])
                self.project.undoStack.push(CommandItemsRemove(diagram, items))

    @pyqtSlot()
    def doExport(self):
        """
        Export the current project.
        """
        if not self.project.isEmpty():
            dialog = QFileDialog(self)
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setDirectory(expandPath('~/'))
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.setNameFilters([File.Owl.value, File.Pdf.value])
            dialog.setViewMode(QFileDialog.Detail)
            dialog.selectFile(self.project.name)
            if dialog.exec_():
                file = File.forValue(dialog.selectedNameFilter())
                path = first(dialog.selectedFiles())
                self.project.export(path, file)

    @pyqtSlot('QGraphicsScene')
    def doFocusDiagram(self, diagram):
        """
        Focus the given diagram in the MDI area.
        :type diagram: Diagram
        """
        subwindow = self.mdi.subWindowForDiagram(diagram)
        if not subwindow:
            view = self.createDiagramView(diagram)
            subwindow = self.createMdiSubWindow(view)
            subwindow.showMaximized()

        self.mdi.setActiveSubWindow(subwindow)
        self.mdi.update()

    @pyqtSlot('QGraphicsItem')
    def doFocusItem(self, item):
        """
        Focus an item in its diagram.
        :type item: AbstractItem
        """
        self.doFocusDiagram(item.diagram)
        self.mdi.activeDiagram.clearSelection()
        self.mdi.activeView.centerOn(item)
        item.setSelected(True)

    @pyqtSlot()
    def doImport(self):
        """
        Import a document from a different file format.
        """
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath('~'))
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setNameFilters([File.Graphml.value])
        if dialog.exec_():
            path = first(dialog.selectedFiles())
            if File.forPath(path) is File.Graphml:
                self.importFromGraphml(path)

    @pyqtSlot(str)
    def doLoadDiagram(self, path):
        """
        Load the given diagram and add it to the project.
        :type path: str
        """
        if fexists(path):

            if File.forPath(path) is File.Graphol:

                worker = GrapholLoader(self.project, path, self)

                try:
                    diagram = worker.run()
                except Exception as e:
                    msgbox = QMessageBox(self)
                    msgbox.setIconPixmap(QPixmap(':/icons/48/error'))
                    msgbox.setWindowIcon(QIcon(':/images/eddy'))
                    msgbox.setWindowTitle(_('DIAGRAM_LOAD_FAILED_WINDOW_TITLE'))
                    msgbox.setStandardButtons(QMessageBox.Close)
                    msgbox.setText(_('DIAGRAM_LOAD_FAILED_MESSAGE', path))
                    msgbox.setDetailedText(format_exception(e))
                    msgbox.exec_()
                else:
                    self.project.addDiagram(diagram)

    @pyqtSlot()
    def doNewDiagram(self):
        """
        Create a new diagram.
        """
        form = NewDiagramDialog(self.project, self)
        if form.exec_() == NewDiagramDialog.Accepted:
            path = expandPath(form.pathField.value())
            self.doLoadDiagram(path)
            self.doFocusDiagram(self.project.diagram(path))
            self.doSave()

    @pyqtSlot()
    def doOpen(self):
        """
        Open a document.
        """
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath('~'))
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setNameFilters([File.Graphol.value])
        if dialog.exec_():
            self.openFile(first(dialog.selectedFiles()))

    @pyqtSlot()
    def doOpenDialog(self):
        """
        Open a dialog window by initializing it using the class stored in action data.
        """
        action = self.sender()
        dialog = action.data()
        window = dialog(self)
        window.exec_()

    @pyqtSlot()
    def doOpenURL(self):
        """
        Open a URL using the operating system default browser.
        """
        action = self.sender()
        weburl = action.data()
        if weburl:
            webbrowser.open(weburl)

    @pyqtSlot()
    def doOpenDiagramProperties(self):
        """
        Executed when scene properties needs to be displayed.
        """
        diagram = self.sender().data() or self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            properties = self.propertyFactory.create(diagram)
            properties.exec_()

    @pyqtSlot()
    def doOpenNodeProperties(self):
        """
        Executed when node properties needs to be displayed.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(diagram.selectedNodes())
            if node:
                properties = self.propertyFactory.create(diagram, node)
                properties.exec_()

    @pyqtSlot()
    def doPaste(self):
        """
        Paste previously copied items.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            if not self.clipboard.empty():
                self.clipboard.paste(diagram, diagram.mousePressPos)

    @pyqtSlot()
    def doPrint(self):
        """
        Print the current project.
        """
        if not self.project.isEmpty():
            self.project.print()

    @pyqtSlot()
    def doQuit(self):
        """
        Quit Eddy.
        """
        self.doSave()
        self.sgnQuit.emit()

    @pyqtSlot()
    def doRefactorBrush(self):
        """
        Change the node brush for all the predicate nodes matching the selected predicate.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            supported = {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}
            node = first([x for x in diagram.selectedNodes() if x.type() in supported])
            if node:
                action = self.sender()
                color = action.data()
                nodes = self.project.predicates(node.type(), node.text())
                self.project.undoStack.push(CommandNodeSetBrush(diagram, nodes, QBrush(QColor(color.value))))

    @pyqtSlot()
    def doRefactorName(self):
        """
        Rename all the instance of the selected predicate node.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            supported = {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}
            node = first([x for x in diagram.selectedNodes() if x.type() in supported])
            if node:
                 dialog = RefactorNameForm(node, self)
                 dialog.exec_()

    @pyqtSlot()
    def doRelocateLabel(self):
        """
        Reset the selected node label to its default position.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first([x for x in diagram.selectedNodes() if x.label is not None])
            if node and node.label.isMovable():
                undo = node.label.pos()
                redo = node.label.defaultPos()
                self.project.undoStack.push(CommandNodeLabelMove(diagram, node, undo, redo))

    @pyqtSlot()
    def doRemoveBreakpoint(self):
        """
        Remove the edge breakpoint specified in the action triggering this slot.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            edge, breakpoint = action.data()
            if 0 <= breakpoint < len(edge.breakpoints):
                self.project.undoStack.push(CommandEdgeBreakpointRemove(diagram, edge, breakpoint))

    @pyqtSlot()
    def doRemoveDiagram(self):
        """
        Removes a diagram from the current project.
        """
        action = self.sender()
        diagram = action.data()
        if diagram:
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/48/question'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle(_('DIAGRAM_REMOVE_POPUP_TITLE', diagram.name))
            msgbox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msgbox.setTextFormat(Qt.RichText)
            msgbox.setText(_('DIAGRAM_REMOVE_POPUP_QUESTION', diagram.name))
            msgbox.setInformativeText(_('DIAGRAM_REMOVE_POPUP_INFORMATIVE_TEXT'))
            msgbox.exec_()
            if msgbox.result() == QMessageBox.Yes:
                subwindow = self.mdi.subWindowForDiagram(diagram)
                if subwindow:
                    subwindow.close()
                self.project.removeDiagram(diagram)
                fremove(diagram.path)
                self.doSave()

    @pyqtSlot()
    def doRenameDiagram(self):
        """
        Renames a diagram.
        """
        action = self.sender()
        diagram = action.data()
        if diagram:
            form = RenameDiagramDialog(self.project, diagram, self)
            if form.exec_() == RenameDiagramDialog.Accepted:
                self.doSave()

    @pyqtSlot()
    def doSave(self):
        """
        Save the current project.
        """
        try:
            worker = ProjectExporter(self.project, self)
            worker.run()
        except Exception as e:
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/48/error'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle(_('PROJECT_SAVE_FAILED_WINDOW_TITLE'))
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText(_('PROJECT_SAVE_FAILED_MESSAGE'))
            msgbox.setDetailedText(format_exception(e))
            msgbox.exec_()
        else:
            self.project.undoStack.setClean()

    @pyqtSlot()
    def doSaveAs(self):
        """
        Creates a copy of the currently open diagram.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            dialog = QFileDialog(self)
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setDirectory(self.project.path)
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.setNameFilters([File.Graphol.value, File.Graphml.value])
            dialog.setOption(QFileDialog.DontConfirmOverwrite, True)
            dialog.setViewMode(QFileDialog.Detail)
            dialog.selectFile(diagram.name)
            if dialog.exec_():
                file = File.forValue(dialog.selectedNameFilter())
                path = first(dialog.selectedFiles())
                self.saveFile(diagram, path, file)

    @pyqtSlot()
    def doSelectAll(self):
        """
        Select all the items in the active diagrsm.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            path = QPainterPath()
            path.addRect(diagram.sceneRect())
            diagram.setSelectionArea(path)
            diagram.setMode(DiagramMode.Idle)

    @pyqtSlot()
    def doSendToBack(self):
        """
        Send the selected item to the back of the diagram.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            for node in diagram.selectedNodes():
                zValue = 0
                for item in [x for x in node.collidingItems() if x.type() is not Item.Label]:
                    if item.zValue() <= zValue:
                        zValue = item.zValue() - 0.2
                if zValue != node.zValue():
                    self.project.undoStack.push(CommandNodeSetDepth(diagram, node, zValue))

    @pyqtSlot()
    def doSetNodeBrush(self):
        """
        Set the brush of selected nodes.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            color = action.data()
            brush = QBrush(QColor(color.value))
            supported = {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}
            selected = {x for x in diagram.selectedNodes() if x.type() in supported and x.brush != brush}
            if selected:
                self.project.undoStack.push(CommandNodeSetBrush(diagram, selected, brush))

    @pyqtSlot()
    def doSetPropertyRestriction(self):
        """
        Set a property domain / range restriction.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            supported = {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
            node = first([x for x in diagram.selectedNodes() if x.type() in supported])
            if node:
                data = None
                action = self.sender()
                restriction = action.data()
                if restriction is not Restriction.Cardinality:
                    data = restriction.format()
                else:
                    form = CardinalityRestrictionForm(self)
                    if form.exec_() == CardinalityRestrictionForm.Accepted:
                        data = restriction.format(form.minValue or '-', form.maxValue or '-')
                if data and node.text() != data:
                    name = _('COMMAND_NODE_SET_PROPERTY_RESTRICTION', node.shortname, data)
                    self.project.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))

    @pyqtSlot()
    def doSetIndividualAs(self):
        """
        Set an invididual node either to Instance or Value.
        Will bring up the Value Form if needed.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first([x for x in diagram.selectedNodes() if x.type() is Item.IndividualNode])
            if node:
                action = self.sender()
                if action.data() is Identity.Instance:
                    if node.identity is Identity.Value:
                        data = node.label.template
                        name = _('COMMAND_NODE_SET_INDIVIDUAL_AS', node.text(), data)
                        self.project.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))
                elif action.data() is Identity.Value:
                    form = ValueForm(node, self)
                    form.exec_()

    @pyqtSlot()
    def doSetNodeSpecial(self):
        """
        Set the special type of the selected node.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            supported = {Item.ConceptNode, Item.RoleNode, Item.AttributeNode}
            node = first([x for x in diagram.selectedNodes() if x.type() in supported])
            if node:
                special = action.data()
                data = special.value
                if node.text() != data:
                    name = _('COMMAND_NODE_SET_SPECIAL', node.shortname, data)
                    self.project.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))

    @pyqtSlot()
    def doSetDatatype(self):
        """
        Set the datatype of the selected value-domain node.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first([x for x in diagram.selectedNodes() if x.type() is Item.ValueDomainNode])
            if node:
                action = self.sender()
                datatype = action.data()
                data = datatype.value
                if node.text() != data:
                    name = _('COMMAND_NODE_SET_DATATYPE', node.shortname, data)
                    self.project.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))

    @pyqtSlot()
    def doSetFacet(self):
        """
        Set the facet of a Facet node.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first([x for x in diagram.selectedNodes() if x.type() is Item.FacetNode])
            if node:
                action = self.sender()
                facet = action.data()
                if facet != node.facet:
                    data = node.compose(facet, node.value)
                    name = _('COMMAND_NODE_SET_FACET', node.facet.value, facet.value)
                    self.project.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))

    @pyqtSlot()
    def doSwapEdge(self):
        """
        Swap the selected edges by inverting source/target points.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            validate = self.project.validator.validate
            selected = [e for e in diagram.selectedEdges() if validate(e.target, e, e.source).valid]
            if selected:
                self.project.undoStack.push(CommandEdgeSwap(diagram, selected))

    @pyqtSlot()
    def doSwitchOperatorNode(self):
        """
        Switch the selected operator node to a different type.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first([x for x in diagram.selectedNodes() if Item.UnionNode <= x.type() <= Item.DisjointUnionNode])
            if node:
                action = self.sender()
                if node.type() is not action.data():
                    xnode = diagram.factory.create(action.data())
                    xnode.setPos(node.pos())
                    self.project.undoStack.push(CommandNodeOperatorSwitchTo(diagram, node, xnode))

    @pyqtSlot()
    def doSyntaxCheck(self):
        """
        Perform syntax checking on the active diagram.
        """
        item = None
        pixmap = QPixmap(':/icons/48/done')
        message = _('SYNTAX_MANUAL_NO_ERROR_FOUND')
        with BusyProgressDialog(_('SYNTAX_MANUAL_PROGRESS_TITLE'), 2, self):
            for edge in self.project.edges():
                source = edge.source
                target = edge.target
                result = self.project.validator.validate(source, edge, target)
                if not result.valid:
                    nameA = '{0} "{1}"'.format(source.name, source.id)
                    nameB = '{0} "{1}"'.format(target.name, target.id)
                    if source.isPredicate():
                        nameA = '{0} "{1}:{2}"'.format(source.name, source.text(), source.id)
                    if target.isPredicate():
                        nameB = '{0} "{1}:{2}"'.format(target.name, target.text(), target.id)
                    message = _('SYNTAX_MANUAL_EDGE_ERROR', edge.name, nameA, nameB, uncapitalize(result.message))
                    pixmap = QPixmap(':/icons/48/warning')
                    item = edge
                    break
            else:
                for node in self.project.nodes():
                    if node.identity is Identity.Unknown:
                        name = '{0} "{1}"'.format(node.name, node.id)
                        if node.isPredicate():
                            name = '{0} "{1}:{2}"'.format(node.name, node.text(), node.id)
                        message = _('SYNTAX_MANUAL_NODE_IDENTITY_UNKNOWN', name)
                        pixmap = QPixmap(':/icons/48/warning')
                        item = node
                        break

        msgbox = QMessageBox(self)
        msgbox.setIconPixmap(pixmap)
        msgbox.setWindowIcon(QIcon(':/images/eddy'))
        msgbox.setWindowTitle(_('SYNTAX_MANUAL_WINDOW_TITLE'))
        msgbox.setStandardButtons(QMessageBox.Close)
        msgbox.setText(message)
        msgbox.setTextFormat(Qt.RichText)
        msgbox.exec_()

        if item:
            focus = item
            if item.isEdge():
                if item.breakpoints:
                    focus = item.breakpoints[int(len(item.breakpoints)/2)]
            self.doFocusDiagram(item.diagram)
            self.mdi.activeView.centerOn(focus)
            self.mdi.activeDiagram.clearSelection()
            item.setSelected(True)

    @pyqtSlot()
    def doSnapToGrid(self):
        """
        Toggle snap to grid setting.
        """
        settings = QSettings(ORGANIZATION, APPNAME)
        settings.setValue('diagram/grid', self.actionSnapToGrid.isChecked())
        settings.sync()
        for subwindow in self.mdi.subWindowList():
            viewport = subwindow.view.viewport()
            viewport.update()

    @pyqtSlot()
    def doToggleEdgeEquivalence(self):
        """
        Set/unset the 'equivalence' attribute for all the selected Inclusion edges.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = diagram.selectedEdges()
            selected = [e for e in selected if e.type() is Item.InclusionEdge and e.isEquivalenceAllowed()]
            if selected:
                comp = sum(edge.equivalence for edge in selected) <= len(selected) / 2
                data = {edge: {'from': edge.equivalence, 'to': comp} for edge in selected}
                self.project.undoStack.push(CommandEdgeToggleEquivalence(diagram, data))

    @pyqtSlot()
    def doUpdateState(self):
        """
        Update actions enabling/disabling them when needed.
        """
        isDiagramActive = False
        isClipboardEmpty = True
        isEdgeSelected = False
        isNodeSelected = False
        isPredicateSelected = False
        isProjectEmpty = self.project.isEmpty()
        isUndoStackClean = self.project.undoStack.isClean()
        isEdgeSwapEnabled = False
        isEdgeToggleEnabled = False

        if self.mdi.subWindowList():

            diagram = self.mdi.activeDiagram
            predicates = {Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.IndividualNode}
            if diagram:

                nodes = diagram.selectedNodes()
                edges = diagram.selectedEdges()
                isDiagramActive = True
                isClipboardEmpty = self.clipboard.empty()
                isEdgeSelected = first(edges) is not None
                isNodeSelected = first(nodes) is not None
                isPredicateSelected = any([i.type() in predicates for i in nodes])

                if isEdgeSelected:
                    for edge in edges:
                        if not isEdgeSwapEnabled:
                            isEdgeSwapEnabled = edge.isSwapAllowed()
                        if not isEdgeToggleEnabled:
                            if edge.type() is Item.InclusionEdge:
                                isEdgeToggleEnabled = edge.isEquivalenceAllowed()
                        if isEdgeSwapEnabled and isEdgeToggleEnabled:
                            break

        self.actionBringToFront.setEnabled(isNodeSelected)
        self.actionCenterDiagram.setEnabled(isDiagramActive)
        self.actionCut.setEnabled(isNodeSelected)
        self.actionCopy.setEnabled(isNodeSelected)
        self.actionDelete.setEnabled(isNodeSelected or isEdgeSelected)
        self.actionExport.setEnabled(not isProjectEmpty)
        self.actionPaste.setEnabled(not isClipboardEmpty)
        self.actionSave.setEnabled(not isUndoStackClean)
        self.actionSaveAs.setEnabled(isDiagramActive)
        self.actionSelectAll.setEnabled(isDiagramActive)
        self.actionSendToBack.setEnabled(isNodeSelected)
        self.buttonSetBrush.setEnabled(isPredicateSelected)
        self.actionSnapToGrid.setEnabled(isDiagramActive)
        self.actionSwapEdge.setEnabled(isEdgeSelected and isEdgeSwapEnabled)
        self.actionToggleEdgeEquivalence.setEnabled(isEdgeSelected and isEdgeToggleEnabled)
        self.zoom.setEnabled(isDiagramActive)

    @pyqtSlot('QGraphicsItem', int)
    def onDiagramActionCompleted(self, item, modifiers):
        """
        Executed after an item insertion process ends.
        :type item: AbstractItem
        :type modifiers: int
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            if not modifiers & Qt.ControlModifier:
                button = self.palette_.button(item.type())
                button.setChecked(False)
                diagram.setMode(DiagramMode.Idle)

    @pyqtSlot(DiagramMode)
    def onDiagramModeChanged(self, mode):
        """
        Executed when the scene operation mode changes.
        :type mode: DiagramMode
        """
        if mode not in (DiagramMode.InsertNode, DiagramMode.InsertEdge):
            self.palette_.reset()

    @pyqtSlot('QToolButton')
    def onPaletteClicked(self, button):
        """
        Executed whenever a palette button is clicked.
        :type button: Button
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.clearSelection()
            if not button.isChecked():
                diagram.setMode(DiagramMode.Idle)
            else:
                if Item.ConceptNode <= button.item < Item.InclusionEdge:
                    diagram.setMode(DiagramMode.InsertNode, button.item)
                elif Item.InclusionEdge <= button.item <= Item.MembershipEdge:
                    diagram.setMode(DiagramMode.InsertEdge, button.item)

    @pyqtSlot('QMdiSubWindow')
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        if subwindow:

            view = subwindow.view
            diagram = subwindow.diagram
            diagram.setMode(DiagramMode.Idle)
            self.info.browse(diagram)
            self.overview.browse(view)
            disconnect(self.zoom.sgnChanged)
            disconnect(view.sgnScaled)
            self.zoom.adjust(view.zoom)
            connect(self.zoom.sgnChanged, view.onZoomChanged)
            connect(view.sgnScaled, self.zoom.scaleChanged)
            self.setWindowTitle(self.project, diagram)

        else:

            if not self.mdi.subWindowList():
                self.info.reset()
                self.overview.reset()
                self.zoom.zoomReset()
                self.setWindowTitle(self.project)

        self.doUpdateState()

    #############################################
    #   EVENTS
    #################################

    def closeEvent(self, closeEvent):
        """
        Executed when the main window is closed.
        :type closeEvent: QCloseEvent
        """
        close = True
        save = False
        if not self.project.undoStack.isClean():
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/48/question'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle(_('PROJECT_CLOSING_SAVE_CHANGES_WINDOW_TITLE'))
            msgbox.setStandardButtons(QMessageBox.Cancel|QMessageBox.No|QMessageBox.Yes)
            msgbox.setText(_('PROJECT_CLOSING_SAVE_CHANGES_MESSAGE'))
            msgbox.exec_()
            if msgbox.result() == QMessageBox.Cancel:
                close = False
            elif msgbox.result() == QMessageBox.No:
                save = False
            elif msgbox.result() == QMessageBox.Yes:
                save = True

        if not close:
            closeEvent.ignore()
        else:
            if save:
                self.doSave()
            self.sgnClosed.emit()
            closeEvent.accept()

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
                if fexists(path) and File.forPath(path) is File.Graphol:
                    self.openFile(path)
            dropEvent.accept()
        else:
            dropEvent.ignore()

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :type source: QObject
        :type event: QEvent
        :rtype: bool
        """
        if event.type() == QEvent.Resize:

            try:
                widget = source.widget()
                widget.redraw()
            except AttributeError:
                pass

        return super().eventFilter(source, event)

    def keyReleaseEvent(self, keyEvent):
        """
        Executed when a keyboard button is released from the scene.
        :type keyEvent: QKeyEvent
        """
        if keyEvent.key() == Qt.Key_Control:
            diagram = self.mdi.activeDiagram
            if diagram and not diagram.isEdgeInsertionInProgress():
                diagram.setMode(DiagramMode.Idle)
        super().keyReleaseEvent(keyEvent)

    def showEvent(self, showEvent):
        """
        Executed when the window is shown.
        :type showEvent: QShowEvent
        """
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.activateWindow()
        self.raise_()

    #############################################
    #   INTERFACE
    #################################

    def createDiagramView(self, diagram):
        """
        Create a new diagram view displaying the given diagram.
        :type diagram: Diagram
        :rtype: DigramView
        """
        view = DiagramView(diagram, self)
        view.centerOn(0, 0)
        return view

    def createMdiSubWindow(self, widget):
        """
        Create a subwindow in the MDI area that displays the given widget
        :type widget: QWidget
        :rtype: MdiSubWindow
        """
        subwindow = MdiSubWindow(widget)
        subwindow = self.mdi.addSubWindow(subwindow)
        subwindow.showMaximized()
        return subwindow

    def importFromGraphml(self, path):
        """
        Import from .graphml file format, adding the new diagram to the project and MDI area.
        :type path: str
        """
        if not fexists(path):
            raise IOError('file not found: {0}'.format(path))

        name = os.path.basename(path)
        with BusyProgressDialog(_('DIAGRAM_IMPORT_PROGRESS_TITLE', name, 2, self)):

            worker = GraphmlLoader(self.project, path, self)

            try:
                diagram = worker.run()
            except Exception as e:
                msgbox = QMessageBox(self)
                msgbox.setIconPixmap(QPixmap(':/icons/48/error'))
                msgbox.setWindowIcon(QIcon(':/images/eddy'))
                msgbox.setWindowTitle(_('DIAGRAM_IMPORT_FAILED_WINDOW_TITLE'))
                msgbox.setStandardButtons(QMessageBox.Close)
                msgbox.setText(_('DIAGRAM_IMPORT_FAILED_MESSAGE', path))
                msgbox.setDetailedText(format_exception(e))
                msgbox.exec_()
            else:
                self.project.addDiagram(diagram)
                self.doFocusDiagram(diagram)
                self.doSave()

        if worker.errors:
            # If some errors have been generated during the import process, display
            # them into a popup so the user can check whether the problem is in the
            # .graphml document or Eddy is not handling the import properly.
            enums = enumerate(worker.errors, start=1)
            parts = ['{0}) {1}'.format(k, format_exception(v)) for k, v in enums]
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/48/warning'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle(_('DIAGRAM_IMPORT_PARTIAL_WINDOW_TITLE'))
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setTextFormat(Qt.RichText)
            msgbox.setText(_('DIAGRAM_IMPORT_PARTIAL_MESSAGE', name, len(worker.errors)))
            msgbox.setInformativeText(_('DIAGRAM_IMPORT_PARTIAL_INFORMATIVE_MESSAGE', BUG_TRACKER))
            msgbox.setDetailedText('\n'.join(parts))
            msgbox.exec_()

    def openFile(self, path):
        """
        Open a graphol document adding it to the project and to the MDI area.
        :type path: str
        """
        if not self.project.diagram(expandPath(path)):

            if not fexists(path):
                raise IOError('file not found: {0}'.format(path))

            if not isSubPath(self.project.path, path):
                name = cutR(os.path.basename(path), File.Graphol.extension)
                dest = uniquePath(self.project.path, name, File.Graphol.extension)
                path = fcopy(path, dest)

            self.doLoadDiagram(path)
            self.doFocusDiagram(self.project.diagram(path))
            self.doSave()

    def saveFile(self, diagram, path, file):
        """
        Save the given diagram in a file identified by the given path.
        :type diagram: Diagram
        :type path: str
        :type file: File
        """
        base = os.path.dirname(path)
        name = cutR(os.path.basename(path), file.extension)
        path = uniquePath(base, name, file.extension)
        if file is File.Graphol:
            worker = GrapholExporter(diagram, path, self)
            worker.run()
        elif file is File.Graphml:
            worker = GraphmlExporter(diagram, path, self)
            worker.run()

    def setWindowTitle(self, project, diagram=None):
        """
        Set the main window title.
        :type project: Project
        :type diagram: Diagram
        """
        title = '{0} - [{1}]'.format(project.name, shortPath(project.path))
        if diagram:
            title = '{0} - {1}'.format(diagram.name, title)
        super().setWindowTitle(title)