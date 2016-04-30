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
from traceback import format_exception

from PyQt5.QtCore import Qt, QSettings, QByteArray, QEvent, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QPixmap
from PyQt5.QtGui import QIcon, QKeySequence, QPainterPath
from PyQt5.QtWidgets import QMainWindow, QAction, QStatusBar, QMessageBox
from PyQt5.QtWidgets import QMenu, QToolButton, QDockWidget, QApplication
from PyQt5.QtWidgets import QUndoGroup, QStyle, QFileDialog

from eddy import APPNAME, DIAG_HOME, GRAPHOL_HOME, ORGANIZATION, VERSION
from eddy.core.commands.common import CommandComposeAxiom
from eddy.core.commands.common import CommandItemsRemove
from eddy.core.commands.common import CommandItemsTranslate
from eddy.core.commands.edges import CommandEdgeBreakpointRemove
from eddy.core.commands.edges import CommandEdgeSwap
from eddy.core.commands.edges import CommandEdgeToggleComplete
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
from eddy.core.datatypes.owl import XsdDatatype
from eddy.core.datatypes.system import Platform, File
from eddy.core.diagram import Diagram
from eddy.core.exporters.graphol import GrapholExporter
from eddy.core.exporters.project import ProjectExporter
from eddy.core.functions.fsystem import fexists, fcopy
from eddy.core.functions.misc import snapF, first, cutR
from eddy.core.functions.path import expandPath, isSubPath, uniquePath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.loaders.graphol import GrapholLoader
from eddy.core.loaders.project import ProjectLoader
from eddy.core.qt import Icon, ColoredIcon
from eddy.core.utils.clipboard import Clipboard

from eddy.lang import gettext as _

from eddy.ui.dialogs.about import About
from eddy.ui.dialogs.diagram import NewDiagramDialog
from eddy.ui.dialogs.nodes import CardinalityRestrictionForm
from eddy.ui.dialogs.nodes import RefactorNameDialog
from eddy.ui.dialogs.nodes import ValueForm
from eddy.ui.dialogs.nodes import ValueRestrictionForm
from eddy.ui.dialogs.preferences import PreferencesDialog
from eddy.ui.menus import MenuFactory
from eddy.ui.properties.factory import PropertyFactory
from eddy.ui.toolbar import Zoom
from eddy.ui.widgets.explorer import OntologyExplorer
from eddy.ui.widgets.explorer import ProjectExplorer
from eddy.ui.widgets.info import Info
from eddy.ui.widgets.mdi import MdiArea
from eddy.ui.widgets.mdi import MdiSubWindow
from eddy.ui.widgets.overview import Overview
from eddy.ui.widgets.palette import Palette
from eddy.ui.widgets.view import DiagramView


class MainWindow(QMainWindow):
    """
    This class implements Eddy's main window.
    """
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
        self.menuSetIndividualAs = QMenu(_('MENU_SET_INDIVIDUAL_AS'))
        self.menuSetPropertyRestriction = QMenu(_('MENU_SET_PROPERTY_RESTRICTION'))
        self.menuSetSpecial = QMenu(_('MENU_SET_SPECIAL'))
        self.menuSwitchOperator = QMenu(_('MENU_SWITCH_OPERATOR'))

        #############################################
        # CREATE TOOLBARS
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        # TODO: TRANSLATE
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.setObjectName('toolbar')

        #############################################
        # CREATE WIDGETS
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        self.clipboard = Clipboard(self)
        self.menuFactory = MenuFactory(self)
        self.propertyFactory = PropertyFactory(self)
        self.undoGroup = QUndoGroup(self)

        self.info = Info(self)
        self.mdi = MdiArea(self)
        self.ontologyExplorer = OntologyExplorer(self)
        self.overview = Overview(self)
        self.palette_ = Palette(self)
        self.projectExplorer = ProjectExplorer(self)
        self.zoom = Zoom(self.toolbar)

        self.dockInfo = QDockWidget(_('DOCK_INFO'), self, Qt.Widget)
        self.dockOntologyExplorer = QDockWidget(_('DOCK_ONTOLOGY_EXPLORER'), self, Qt.Widget)
        self.dockOverview = QDockWidget(_('DOCK_OVERVIEW'), self, Qt.Widget)
        self.dockPalette = QDockWidget(_('DOCK_PALETTE'), self, Qt.Widget)
        self.dockProjectExplorer = QDockWidget(_('DOCK_PROJECT_EXPLORER'), self, Qt.Widget)

        self.buttonSetBrush = QToolButton()

        #############################################
        # CREATE ICONS
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        self.iconBottom = Icon(':/icons/bottom')
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
        self.iconPropertyDomain = Icon(':/icons/property-domain')
        self.iconPropertyRange = Icon(':/icons/property-range')
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
        self.iconTop = Icon(':/icons/top')

        #############################################
        # CREATE ACTIONS
        #################################

        # noinspection PyArgumentList
        QApplication.processEvents()

        self.actionUndo = self.undoGroup.createUndoAction(self)
        self.actionRedo = self.undoGroup.createRedoAction(self)
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
        self.actionOpenDiagramProperties = QAction(_('ACTION_OPEN_DIAGRAM_PROPERTIES_N'), self)
        self.actionSnapToGrid = QAction(_('ACTION_SNAP_TO_GRID_N'), self)
        self.actionCut = QAction(_('ACTION_CUT_N'), self)
        self.actionCopy = QAction(_('ACTION_COPY_N'), self)
        self.actionPaste = QAction(_('ACTION_PASTE_N'), self)
        self.actionDelete = QAction(_('ACTION_DELETE_N'), self)
        self.actionBringToFront = QAction(_('ACTION_BRING_TO_FRONT_N'), self)
        self.actionSendToBack = QAction(_('ACTION_SEND_TO_BACK_N'), self)
        self.actionSelectAll = QAction(_('ACTION_SELECT_ALL_N'), self)
        self.actionOpenNodeProperties = QAction(_('ACTION_OPEN_NODE_PROPERTIES_N'), self)
        self.actionRelocateLabel = QAction(_('ACTION_RELOCATE_LABEL_N'), self)
        self.actionRefactorName = QAction(_('ACTION_REFACTOR_NAME_N'), self)
        self.actionComposePropertyDomain = QAction(_('ACTION_COMPOSE_PROPERTY_DOMAIN_N'), self)
        self.actionComposePropertyRange = QAction(_('ACTION_COMPOSE_PROPERTY_RANGE_N'), self)
        self.actionSetValueRestriction = QAction(_('ACTION_SET_VALUE_RESTRICTION_N'), self)
        self.actionRemoveEdgeBreakpoint = QAction(_('ACTION_REMOVE_EDGE_BREAKPOINT_N'), self)
        self.actionSwapEdge = QAction(_('ACTION_EDGE_SWAP_N'), self)
        self.actionToggleEdgeComplete = QAction(_('ACTION_TOGGLE_EDGE_COMPLETE_N'), self)

        self.actionsRefactorBrush = []
        self.actionsSetBrush = []
        self.actionsSetSpecial = []
        self.actionsSetPropertyRestriction = []
        self.actionsSetDatatype = []
        self.actionsSetIndividualAs = []
        self.actionsSwitchOperator = []

        #############################################
        # LOAD THE GIVEN PROJECT
        #################################

        worker = ProjectLoader(path, self)
        self.project = worker.run()

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
        self.setWindowTitle(None)

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
        connect(self.actionSave.triggered, self.doSave)

        self.actionSaveAs.setIcon(self.iconSaveAs)
        self.actionSaveAs.setShortcut(QKeySequence.SaveAs)
        self.actionSaveAs.setStatusTip(_('ACTION_SAVE_AS'))
        self.actionSaveAs.setEnabled(False)
        connect(self.actionSaveAs.triggered, self.doSaveAs)

        self.actionImport.setStatusTip(_('ACTION_IMPORT_S'))
        connect(self.actionImport.triggered, self.doImport)

        self.actionExport.setStatusTip(_('ACTION_EXPORT_S'))
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

        self.actionOpenDiagramProperties.setIcon(self.iconPreferences)
        connect(self.actionOpenDiagramProperties.triggered, self.doOpenDiagramProperties)

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
        
        self.actionOpenNodeProperties.setIcon(self.iconPreferences)
        connect(self.actionOpenNodeProperties.triggered, self.doOpenNodeProperties)
        
        self.actionRefactorName.setIcon(self.iconLabel)
        connect(self.actionRefactorName.triggered, self.doRefactorName)

        self.actionRelocateLabel.setIcon(self.iconRefresh)
        connect(self.actionRelocateLabel.triggered, self.doRelocateLabel)

        for color in Color:
            size = self.style().pixelMetric(QStyle.PM_ToolBarIconSize)
            action = QAction(color.name, self)
            action.setIcon(ColoredIcon(size, size, color.value))
            action.setCheckable(False)
            action.setData(color)
            connect(action.triggered, self.doSetNodeBrush)
            self.actionsSetBrush.append(action)

        for special in Special:
            action = QAction(special.value, self)
            action.setCheckable(True)
            action.setData(special)
            connect(action.triggered, self.doSetNodeSpecial)
            self.actionsSetSpecial.append(action)

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

        for datatype in XsdDatatype:
            action = QAction(datatype.value, self)
            action.setCheckable(True)
            action.setData(datatype)
            connect(action.triggered, self.doSetDatatype)
            self.actionsSetDatatype.append(action)

        #############################################
        # VALUE-RESTRICTION SPECIFIC
        #################################

        self.actionSetValueRestriction.setIcon(self.iconRefresh)
        connect(self.actionSetValueRestriction.triggered, self.doSetValueRestriction)

        #############################################
        # INDIVIDUAL SPECIFIC
        #################################

        for identity in (Identity.Instance, Identity.Value):
            action = QAction(identity.value, self)
            action.setData(identity)
            connect(action.triggered, self.doSetIndividualAs)
            self.actionsSetIndividualAs.append(action)

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

        self.actionSwapEdge.setIcon(self.iconSwapHorizontal)
        self.actionSwapEdge.setShortcut('ALT+S')
        connect(self.actionSwapEdge.triggered, self.doSwapEdge)

        self.actionToggleEdgeComplete.setShortcut('ALT+C')
        self.actionToggleEdgeComplete.setCheckable(True)
        connect(self.actionToggleEdgeComplete.triggered, self.doToggleEdgeComplete)

        self.addAction(self.actionSwapEdge)
        self.addAction(self.actionToggleEdgeComplete)

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

        self.dockOntologyExplorer.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockOntologyExplorer.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable)
        self.dockOntologyExplorer.installEventFilter(self)
        self.dockOntologyExplorer.setObjectName('ontologyExplorer')
        self.dockOntologyExplorer.setWidget(self.ontologyExplorer)

        self.dockInfo.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockInfo.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable)
        self.dockInfo.installEventFilter(self)
        self.dockInfo.setObjectName('info')
        self.dockInfo.setWidget(self.info)

        self.dockOverview.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockOverview.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable)
        self.dockOverview.installEventFilter(self)
        self.dockOverview.setObjectName('overview')
        self.dockOverview.setWidget(self.overview)

        self.dockPalette.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockPalette.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable)
        self.dockPalette.installEventFilter(self)
        self.dockPalette.setObjectName('palette')
        self.dockPalette.setWidget(self.palette_)

        self.dockProjectExplorer.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.dockProjectExplorer.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable)
        self.dockProjectExplorer.installEventFilter(self)
        self.dockProjectExplorer.setObjectName('projectExplorer')
        self.dockProjectExplorer.setWidget(self.projectExplorer)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockPalette)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockProjectExplorer)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockOverview)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockInfo)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockOntologyExplorer)

        self.ontologyExplorer.browse(self.project)
        self.projectExplorer.browse(self.project)

        connect(self.mdi.subWindowActivated, self.onSubWindowActivated)
        connect(self.palette_.buttonClicked[int], self.onPaletteButtonClicked)
        connect(self.ontologyExplorer.sgnItemDoubleClicked['QGraphicsItem'], self.doFocusItem)
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
        self.menuEdit.addAction(self.actionSelectAll)
        self.menuEdit.addAction(self.actionCenterDiagram)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionOpenPreferences)

        self.menuView.addAction(self.actionSnapToGrid)
        self.menuView.addSeparator()
        self.menuView.addAction(self.toolbar.toggleViewAction())
        self.menuView.addSeparator()
        self.menuView.addAction(self.dockInfo.toggleViewAction())
        self.menuView.addAction(self.dockOntologyExplorer.toggleViewAction())
        self.menuView.addAction(self.dockOverview.toggleViewAction())
        self.menuView.addAction(self.dockPalette.toggleViewAction())
        self.menuView.addAction(self.dockProjectExplorer.toggleViewAction())

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

        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)

        self.toolbar.addAction(self.actionNewDiagram)
        self.toolbar.addAction(self.actionOpen)
        self.toolbar.addAction(self.actionSave)
        self.toolbar.addAction(self.actionPrint)
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

        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.buttonSetBrush)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionSnapToGrid)
        self.toolbar.addAction(self.actionCenterDiagram)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionSyntaxCheck)

        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.zoom.buttonZoomOut)
        self.toolbar.addWidget(self.zoom.buttonZoomIn)
        self.toolbar.addWidget(self.zoom.buttonZoomReset)
    
    def configureState(self):
        """
        Configure application state by reading the preferences file.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        settings = QSettings(ORGANIZATION, APPNAME)

        #############################################
        # RESTORE MAINWINDOW APPEARANCE
        #################################

        self.restoreGeometry(settings.value('mainwindow/geometry', QByteArray(), QByteArray))
        self.restoreState(settings.value('mainwindow/state', QByteArray(), QByteArray))

        #############################################
        # TOGGLE ACTIONS STATE
        #################################

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
                    diagram.undoStack.push(CommandNodeSetDepth(diagram, node, zValue))

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
                r1 = diagram.sceneRect()
                r2 = diagram.visibleRect(margin=0)
                mX = snapF(((r1.right() - r2.right()) - (r2.left() - r1.left())) / 2, Diagram.GridSize)
                mY = snapF(((r1.bottom() - r2.bottom()) - (r2.top() - r1.top())) / 2, Diagram.GridSize)
                if mX or mY:
                    items = [x for x in items if x.isNode() or x.isEdge()]
                    command = CommandItemsTranslate(diagram, items, mX, mY, _('COMMAND_DIAGRAM_CENTER'))
                    diagram.undoStack.push(command)
                    self.mdi.activeView.centerOn(0, 0)

    @pyqtSlot()
    def doCloseProject(self):
        """
        Close the currently active subwindow.
        """
        # TODO: IMPLEMENT
        pass

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
                diagram.undoStack.push(CommandComposeAxiom(name, diagram, node, nodes, edges))

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
                diagram.undoStack.push(CommandItemsRemove(diagram, items))

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
                diagram.undoStack.push(CommandItemsRemove(diagram, items))

    @pyqtSlot()
    def doExport(self):
        """
        Export the currently open graphol document.
        """
        # TODO: IMPLEMENT
        # scene = self.mdi.activeScene
        # if scene:
        #     result = self.exportPath(name=cutR(scene.document.name, File.Graphol.extension))
        #     if result:
        #         filepath = result[0]
        #         filetype = File.forValue(result[1])
        #         if filetype is File.Pdf:
        #             self.exportToPdf(scene, filepath)
        #         elif filetype is File.Owl:
        #             self.exportToOwl(scene, filepath)

    @pyqtSlot('QGraphicsScene')
    def doFocusDiagram(self, diagram):
        """
        Focus the given diagram in the MDI area.
        :type diagram: Diagram
        """
        for subwindow in self.mdi.subWindowList():
            if subwindow.diagram is diagram:
                break
        else:
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
        # TODO: IMPLEMENT
        # dialog = OpenFile(expandPath('~'))
        # dialog.setNameFilters([File.Graphml.value])
        #
        # if dialog.exec_():
        #
        #     filepath = dialog.selectedFiles()[0]
        #     worker = GraphmlLoader(self, filepath)
        #
        #     with BusyProgressDialog('Importing {}'.format(os.path.basename(filepath)), self):
        #
        #         try:
        #             worker.run()
        #         except Exception as e:
        #             msgbox = QMessageBox(self)
        #             msgbox.setIconPixmap(QPixmap(':/icons/error'))
        #             msgbox.setWindowIcon(QIcon(':/images/eddy'))
        #             msgbox.setWindowTitle('Import failed!')
        #             msgbox.setStandardButtons(QMessageBox.Close)
        #             msgbox.setText('Failed to import {}!'.format(os.path.basename(filepath)))
        #             msgbox.setDetailedText(''.join(format_exception(type(e), e, e.__traceback__)))
        #             msgbox.exec_()
        #         else:
        #             scene = worker.scene
        #             scene.setMode(DiagramMode.Idle)
        #             mainview = self.createDiagramView(scene)
        #             subwindow = self.createMdiSubWindow(mainview)
        #             subwindow.showMaximized()
        #             self.mdi.setActiveSubWindow(subwindow)
        #             self.mdi.update()
        #
        #     if worker.errors:
        #
        #         # If some errors have been generated during the import process, display
        #         # them into a popup so the user can check whether the problem is in the
        #         # .graphml document or Eddy is not handling the import properly.
        #         m1 = 'Document {} has been imported! However some errors ({}) have been generated ' \
        #              'during the import process. You can inspect detailed information by expanding the ' \
        #              'box below.'.format(os.path.basename(filepath), len(worker.errors))
        #
        #         m2 = 'If needed, <a href="{}">submit a bug report</a> with detailed information.'.format(BUG_TRACKER)
        #
        #         parts = []
        #         for k, v in enumerate(worker.errors, start=1):
        #             parts.append('{}) {}'.format(k, ''.join(format_exception(type(v), v, v.__traceback__))))
        #
        #         m3 = '\n'.join(parts)
        #
        #         msgbox = QMessageBox(self)
        #         msgbox.setIconPixmap(QPixmap(':/icons/warning'))
        #         msgbox.setWindowIcon(QIcon(':/images/eddy'))
        #         msgbox.setWindowTitle('Partial document import!')
        #         msgbox.setStandardButtons(QMessageBox.Close)
        #         msgbox.setText(m1)
        #         msgbox.setInformativeText(m2)
        #         msgbox.setDetailedText(m3)
        #         msgbox.exec_()

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
                    msgbox.setIconPixmap(QPixmap(':/icons/error'))
                    msgbox.setWindowIcon(QIcon(':/images/eddy'))
                    msgbox.setWindowTitle(_('DIAGRAM_LOAD_FAILED_WINDOW_TITLE'))
                    msgbox.setStandardButtons(QMessageBox.Close)
                    msgbox.setText(_('DIAGRAM_LOAD_FAILED_MESSAGE', path))
                    msgbox.setDetailedText(''.join(format_exception(type(e), e, e.__traceback__)))
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
    def doOpenNodeProperties(self):
        """
        Executed when node properties needs to be displayed.
        """
        # TODO: review
        # scene = self.mdi.activeScene
        # if scene:
        #     scene.setMode(DiagramMode.Idle)
        #     node = first(scene.selectedNodes())
        #     if node:
        #         prop = self.propertyFactory.create(scene=scene, node=node)
        #         prop.exec_()

    @pyqtSlot()
    def doOpenDiagramProperties(self):
        """
        Executed when scene properties needs to be displayed.
        """
        # TODO: IMPLEMENT
        # scene = self.mdi.activeScene
        # if scene:
        #     scene.setMode(DiagramMode.Idle)
        #     prop = self.propertyFactory.create(scene=scene)
        #     prop.exec_()

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
        Print the currently open graphol document.
        """
        # TODO: implement
        # scene = self.mdi.activeScene
        # if scene:
        #     shape = scene.visibleRect(margin=20)
        #     if shape:
        #         printer = QPrinter(QPrinter.HighResolution)
        #         printer.setOutputFormat(QPrinter.NativeFormat)
        #         dialog = QPrintDialog(printer)
        #         if dialog.exec_() == QDialog.Accepted:
        #             painter = QPainter()
        #             if painter.begin(printer):
        #                 scene.render(painter, source=shape)

    @pyqtSlot()
    def doQuit(self):
        """
        Quit Eddy.
        """

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
                diagram.undoStack.push(CommandNodeSetBrush(diagram, nodes, QBrush(QColor(color.value))))

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
                 dialog = RefactorNameDialog(node, self)
                 dialog.exec_()

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
                diagram.undoStack.push(CommandEdgeBreakpointRemove(diagram, edge, breakpoint))

    @pyqtSlot()
    def doRelocateLabel(self):
        """
        Reset the selected node label to its default position.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first([x for x in diagram.selectedNodes() if hasattr(x, 'label')])
            if node and node.label.movable:
                undo = node.label.pos()
                redo = node.label.defaultPos()
                diagram.undoStack.push(CommandNodeLabelMove(diagram, node, undo, redo))

    @pyqtSlot()
    def doSave(self):
        """
        Save the current project.
        """
        worker = ProjectExporter(self.project, self)
        worker.run()

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
            dialog.setNameFilters([File.Graphol.value])
            dialog.setOption(QFileDialog.DontConfirmOverwrite, True)
            dialog.setViewMode(QFileDialog.Detail)
            dialog.selectFile(diagram.name)
            if dialog.exec_():
                self.saveFile(diagram, first(dialog.selectedFiles()))

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
                    diagram.undoStack.push(CommandNodeSetDepth(diagram, node, zValue))

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
                diagram.undoStack.push(CommandNodeSetBrush(diagram, selected, brush))

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
                    name = 'change {0} to {1}'.format(node.shortname, data)
                    diagram.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))

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
                        name = 'change {0} to {1}'.format(node.text(), data)
                        diagram.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))
                elif action.data() is Identity.Value:
                    form = ValueForm(node, self)
                    if form.exec_() == ValueForm.Accepted:
                        datatype = form.datatypeField.currentData()
                        value = form.valueField.value()
                        data = node.composeValue(value, datatype)
                        if node.text() != data:
                            name = 'change {0} to {1}'.format(node.text(), data)
                            diagram.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))

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
                special = action.data() if node.special is not action.data() else None
                data = special.value if special else node.label.template
                if node.text() != data:
                    name = 'change {0} to {1}'.format(node.shortname, data)
                    diagram.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))

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
                    name = 'change {0} to {1}'.format(node.shortname, data)
                    diagram.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))

    @pyqtSlot()
    def doSetValueRestriction(self):
        """
        Set the restriction of a Value-Restriction node.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first([x for x in diagram.selectedNodes() if x.type() is Item.ValueRestrictionNode])
            if node:
                form = ValueRestrictionForm(node, self)
                form.datatypeField.setEnabled(not node.constrained)
                if form.exec() == ValueRestrictionForm.Accepted:
                    datatype = form.datatypeField.currentData()
                    facet = form.facetField.currentData()
                    value = form.valueField.value()
                    data = node.compose(facet, value, datatype)
                    if node.text() != data:
                        name = 'change {0} to {1}'.format(node.shortname, data)
                        diagram.undoStack.push(CommandNodeLabelChange(diagram, node, node.text(), data, name))

    @pyqtSlot()
    def doSwapEdge(self):
        """
        Swap the selected edges by inverting source/target points.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = [e for e in diagram.selectedEdges() if self.project.validator.valid(e.target, e, e.source)]
            if selected:
                diagram.undoStack.push(CommandEdgeSwap(diagram, selected))

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
                    diagram.undoStack.push(CommandNodeOperatorSwitchTo(diagram, node, xnode))

    @pyqtSlot()
    def doSyntaxCheck(self):
        """
        Perform syntax checking on the active diagram.
        """
        # TODO: IMPLEMENT
        # scene = self.mdi.activeScene
        # if scene:
        # 
        #     placeholder = None
        #     pixmap = QPixmap(':/icons/done')
        #     message = 'No syntax error found!'
        # 
        #     with BusyProgressDialog('Syntax check...', self):
        # 
        #         for edge in scene.edges():
        #             res = scene.validator.result(edge.source, edge, edge.target)
        #             if not res.valid:
        #                 e = res.edge
        #                 s = res.source
        #                 t = res.target
        #                 m = uncapitalize(res.message)
        #                 placeholder = res.edge
        #                 sname = '{} "{}"'.format(s.name, s.id if not s.predicate else '{}:{}'.format(s.text(), s.id))
        #                 tname = '{} "{}"'.format(t.name, t.id if not t.predicate else '{}:{}'.format(t.text(), t.id))
        #                 message = 'Syntax error detected on {} from {} to {}: <i>{}</i>.'.format(e.name, sname, tname, m)
        #                 pixmap = QPixmap(':/icons/warning')
        #                 break
        #         else:
        #             for n in scene.nodes():
        #                 if n.identity is Identity.Unknown:
        #                     placeholder = n
        #                     name = '{} "{}"'.format(n.name, n.id if not n.predicate else '{}:{}'.format(n.text(), n.id))
        #                     message = 'Unkown node identity detected on {}.'.format(name)
        #                     pixmap = QPixmap(':/icons/warning')
        #                     break
        # 
        #     msgbox = QMessageBox(self)
        #     msgbox.setIconPixmap(pixmap)
        #     msgbox.setWindowIcon(QIcon(':/images/eddy'))
        #     msgbox.setWindowTitle('Syntax check completed!')
        #     msgbox.setStandardButtons(QMessageBox.Close)
        #     msgbox.setText(message)
        #     msgbox.setTextFormat(Qt.RichText)
        #     msgbox.exec_()
        # 
        #     if placeholder:
        #         focus = placeholder
        #         if placeholder.edge:
        #             if placeholder.breakpoints:
        #                 focus = placeholder.breakpoints[int(len(placeholder.breakpoints)/2)]
        # 
        #         scene.clearSelection()
        #         placeholder.setSelected(True)
        #         mainview = self.mdi.activeView
        #         mainview.centerOn(focus)

    @pyqtSlot()
    def doToggleEdgeComplete(self):
        """
        Toggle the 'complete' attribute for all the selected inclusion edges.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = [x for x in diagram.selectedEdges() if x.type() is Item.InclusionEdge]
            if selected:
                comp = sum(edge.complete for edge in selected) <= len(selected) / 2
                data = {edge: {'from': edge.complete, 'to': comp} for edge in selected}
                diagram.undoStack.push(CommandEdgeToggleComplete(diagram, data))

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
    def doUpdateState(self):
        """
        Update actions enabling/disabling them when needed.
        """
        isDiagramActive = False
        isClipboardEmpty = True
        isEdgeSelected = False
        isNodeSelected = False
        isPredicateSelected = False

        if self.mdi.subWindowList():
            diagram = self.mdi.activeDiagram
            if diagram:
                nodes = diagram.selectedNodes()
                edges = diagram.selectedEdges()
                isDiagramActive = True
                isClipboardEmpty = self.clipboard.empty()
                isEdgeSelected = first(edges) is not None
                isNodeSelected = first(nodes) is not None
                isPredicateSelected = any([i.isPredicate() for i in nodes])

        self.actionBringToFront.setEnabled(isNodeSelected)
        self.actionCenterDiagram.setEnabled(isDiagramActive)
        self.actionCut.setEnabled(isNodeSelected)
        self.actionCopy.setEnabled(isNodeSelected)
        self.actionDelete.setEnabled(isNodeSelected or isEdgeSelected)
        self.actionPaste.setEnabled(not isClipboardEmpty)
        self.actionSaveAs.setEnabled(isDiagramActive)
        self.actionSelectAll.setEnabled(isDiagramActive)
        self.actionSendToBack.setEnabled(isNodeSelected)
        self.actionSnapToGrid.setEnabled(isDiagramActive)
        self.buttonSetBrush.setEnabled(isPredicateSelected)
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
                self.palette_.button(item.type()).setChecked(False)
                diagram.setMode(DiagramMode.Idle)

    @pyqtSlot(DiagramMode)
    def onDiagramModeChanged(self, mode):
        """
        Executed when the scene operation mode changes.
        :type mode: DiagramMode
        """
        if mode not in (DiagramMode.InsertNode, DiagramMode.InsertEdge):
            self.palette_.clear()

    @pyqtSlot(int)
    def onPaletteButtonClicked(self, item):
        """
        Executed whenever a palette button is clicked.
        :type item: Item
        """
        # TODO: disable palette when there is no diagram
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.clearSelection()
            button = self.palette_.button(item)
            self.palette_.clear(button)
            if not button.isChecked():
                diagram.setMode(DiagramMode.Idle)
            else:
                if Item.ConceptNode <= item < Item.InclusionEdge:
                    diagram.setMode(DiagramMode.InsertNode, item)
                elif Item.InclusionEdge <= item <= Item.MembershipEdge:
                    diagram.setMode(DiagramMode.InsertEdge, item)

    @pyqtSlot('QMdiSubWindow')
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        if subwindow:
            view = subwindow.view
            diagram = subwindow.diagram
            diagram.undoStack.setActive()
            self.info.browse(diagram)
            self.overview.browse(view)
            disconnect(self.zoom.sgnChanged)
            disconnect(view.sgnScaled)
            self.zoom.adjust(view.zoom)
            connect(self.zoom.sgnChanged, view.onZoomChanged)
            connect(view.sgnScaled, self.zoom.scaleChanged)
            self.setWindowTitle(diagram.name)
        else:
            if not self.mdi.subWindowList():
                self.info.reset()
                self.overview.reset()
                self.zoom.zoomReset()
                self.setWindowTitle(None)

        self.doUpdateState()

    #############################################
    #   EVENTS
    #################################

    def closeEvent(self, closeEvent):
        """
        Executed when the main window is closed.
        :type closeEvent: QCloseEvent
        """
        # self.abortQuit = False
        # for subwindow in self.mdi.subWindowList():
        #     mainview = subwindow.widget()
        #     scene = mainview.scene()
        #     if (scene.items() and not scene.document.path) or (not scene.undoStack.isClean()):
        #         self.mdi.setActiveSubWindow(subwindow)
        #         subwindow.showMaximized()
        #     subwindow.close()
        #     if self.abortQuit:
        #         closeEvent.ignore()
        #         break

        #############################################
        # EXPORT CURRENT STATE
        #################################
        #
        # settings = QSettings(expandPath('@home/{}.ini'.format(APPNAME)), QSettings.IniFormat)
        # settings.beginGroup('diagram')
        # settings.setValue('grid', self.snapToGrid)
        # settings.setValue('size', self.diagramSize)
        # settings.endGroup()
        # settings.beginGroup('mainwindow')
        # settings.setValue('geometry', self.saveGeometry())
        # settings.setValue('state', self.saveState())
        # settings.endGroup()
        # settings.sync()

    # def dragEnterEvent(self, dragEvent):
    #     """
    #     Executed when a drag is in progress and the mouse enter this widget.
    #     :type dragEvent: QDragEnterEvent
    #     """
    #     if dragEvent.mimeData().hasUrls():
    #         self.setCursor(QCursor(Qt.DragCopyCursor))
    #         dragEvent.setDropAction(Qt.CopyAction)
    #         dragEvent.accept()
    #     else:
    #         dragEvent.ignore()
    #
    # def dragMoveEvent(self, dragEvent):
    #     """
    #     Executed when a drag is in progress and the mouse moves onto this widget.
    #     :type dragEvent: QDragMoveEvent
    #     """
    #     dragEvent.accept()
    #
    # def dragLeaveEvent(self, dragEvent):
    #     """
    #     Executed when a drag is in progress and the mouse leave this widget.
    #     :type dragEvent: QDragEnterEvent
    #     """
    #     self.unsetCursor()
    #
    # def dropEvent(self, dropEvent):
    #     """
    #     Executed when the drag is dropped on this widget.
    #     :type dropEvent: QDropEvent
    #     """
    #     if dropEvent.mimeData().hasUrls():
    #
    #         self.unsetCursor()
    #         dropEvent.setDropAction(Qt.CopyAction)
    #         platform = Platform.identify()
    #         for url in dropEvent.mimeData().urls():
    #
    #             path = url.path()
    #             if platform is Platform.Windows:
    #                 # On Windows the absolute path returned for each URL has a
    #                 # leading slash: this obviously is not correct on windows
    #                 # platform when absolute url have the form C:\\Programs\\... (Qt bug?)
    #                 path = path.lstrip('/').lstrip('\\')
    #
    #             if os.path.isfile(path) and path.endswith(File.Graphol.extension):
    #                 # If the file exists and is a Graphol file then open it!
    #                 if not self.focusDocument(path):
    #                     scene = self.createSceneFromGrapholFile(path)
    #                     if scene:
    #                         mainview = self.createDiagramView(scene)
    #                         subwindow = self.createMdiSubWindow(mainview)
    #                         subwindow.showMaximized()
    #                         self.mdi.setActiveSubWindow(subwindow)
    #                         self.mdi.update()
    #
    #         dropEvent.accept()
    #     else:
    #         dropEvent.ignore()

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
            if diagram:
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

    def createScene(self, width, height):
        """
        Create and return an empty scene.
        :type width: int
        :type height: int
        :rtype: Diagram
        """
        # TODO: MOVE IN PROJECT
        # scene = Diagram(self)
        # scene.setSceneRect(QRectF(-width / 2, -height / 2, width, height))
        # scene.setItemIndexMethod(Diagram.NoIndex)
        # connect(scene.sgnActionCompleted, self.onDiagramActionCompleted)
        # connect(scene.sgnModeChanged, self.onDiagramModeChanged)
        # connect(scene.selectionChanged, self.doUpdateState)
        # self.undoGroup.addStack(scene.undoStack)
        # return scene
    
    # TODO: REMOVE
    # def createSceneFromGrapholFile(self, filepath):
    #     """
    #     Create a new scene by loading the given Graphol file.
    #     :type filepath: str
    #     :rtype: Diagram
    #     """
    #     worker = GrapholLoader(self, filepath)
    # 
    #     try:
    #         worker.run()
    #     except Exception as e:
    #         msgbox = QMessageBox(self)
    #         msgbox.setIconPixmap(QPixmap(':/icons/error'))
    #         msgbox.setWindowIcon(QIcon(':/images/eddy'))
    #         msgbox.setWindowTitle('Load failed!')
    #         msgbox.setStandardButtons(QMessageBox.Close)
    #         msgbox.setText('Failed to load {}!'.format(os.path.basename(filepath)))
    #         msgbox.setDetailedText(''.join(format_exception(type(e), e, e.__traceback__)))
    #         msgbox.exec_()
    #         return None
    #     else:
    #         return worker.scene

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

    def exportPath(self, path=None, name=None):
        """
        Bring up the 'Export' file dialog and returns the selected filepath.
        Will return None in case the user hit the 'Cancel' button to abort the operation.
        :type path: str
        :type name: str
        :rtype: tuple
        """
        # TODO: ADAPT
        # dialog = SaveFile(path=path, parent=self)
        # dialog.setWindowTitle('Export')
        # dialog.setNameFilters([File.Owl.value, File.Pdf.value])
        # dialog.selectFile(name or 'Untitled')
        # if dialog.exec_():
        #     return dialog.selectedFiles()[0], dialog.selectedNameFilter()
        # return None

    def exportToOwl(self, scene, filepath):
        """
        Export the given scene in OWL syntax saving it in the given filepath.
        :type scene: Diagram
        :type filepath: str
        :rtype: bool
        """
        # TODO: ADAPT
        # exportForm = OWLTranslationForm(scene, filepath, self)
        # if exportForm.exec_() == OWLTranslationForm.Accepted:
        #     return True
        # return False

    @staticmethod
    def exportToPdf(scene, filepath):
        """
        Export the given scene as PDF saving it in the given filepath.
        :type scene: Diagram
        :type filepath: str
        :rtype: bool
        """
        # TODO: ADAPT
        # shape = scene.visibleRect(margin=20)
        # if shape:
        #
        #     printer = QPrinter(QPrinter.HighResolution)
        #     printer.setOutputFormat(QPrinter.PdfFormat)
        #     printer.setOutputFileName(filepath)
        #     printer.setPaperSize(QPrinter.Custom)
        #     printer.setPageSize(QPageSize(QSizeF(shape.width(), shape.height()), QPageSize.Point))
        #
        #     painter = QPainter()
        #     if painter.begin(printer):
        #
        #         # TURN CACHING OFF!
        #         for item in scene.items():
        #             if item.node or item.edge:
        #                 item.setCacheMode(QGraphicsItem.NoCache)
        #
        #         # RENDER THE SCENE
        #         scene.render(painter, source=shape)
        #
        #         # TURN CACHING ON!
        #         for item in scene.items():
        #             if item.node or item.edge:
        #                 item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        #
        #         painter.end()
        #         return True
        #
        # return False

    # TODO: IMPLEMENT
    # def insertRecentDocument(self, path):
    #     """
    #     Add the given document to the recent document list.
    #     :type path: str
    #     """
    #     try:
    #         self.recentDocument.remove(path)
    #     except ValueError:
    #         pass
    #     finally:
    #         self.recentDocument.insert(0, path)
    #         self.recentDocument = self.recentDocument[:Diagram.RecentNum]
    #         self.refreshRecentDocument()

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

    def saveFile(self, diagram, path):
        """
        Save the given diagram in a file identified by the given path.
        :type diagram: Diagram
        :type path: str
        """
        base = os.path.dirname(path)
        name = cutR(os.path.basename(path), File.Graphol.extension)
        path = uniquePath(base, name, File.Graphol.extension)
        worker = GrapholExporter(diagram, self)
        worker.run(path)

    def setWindowTitle(self, s=None):
        """
        Set the main window title.
        :type s: T <= str | None
        """
        super().setWindowTitle('{} - {} {}'.format(s, APPNAME, VERSION) if s else '{} {}'.format(APPNAME, VERSION))