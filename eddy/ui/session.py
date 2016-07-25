# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import os
import webbrowser

from collections import OrderedDict
from textwrap import dedent

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtCore import Qt, QSettings, QByteArray, QEvent, QSize
from PyQt5.QtGui import QBrush, QColor, QCursor
from PyQt5.QtGui import QIcon, QKeySequence, QPainterPath
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QStatusBar, QToolButton
from PyQt5.QtWidgets import QStyle, QMenu, QAction, QActionGroup, QFileDialog

from eddy import APPNAME, DIAG_HOME, GRAPHOL_HOME, ORGANIZATION
from eddy.core.commands.common import CommandComposeAxiom
from eddy.core.commands.common import CommandItemsRemove
from eddy.core.commands.common import CommandItemsTranslate
from eddy.core.commands.common import CommandSnapItemsToGrid
from eddy.core.commands.edges import CommandEdgeBreakpointRemove
from eddy.core.commands.edges import CommandEdgeSwap
from eddy.core.commands.edges import CommandEdgeToggleEquivalence
from eddy.core.commands.labels import CommandLabelMove
from eddy.core.commands.labels import CommandLabelChange
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
from eddy.core.factory import MenuFactory, PropertyFactory
from eddy.core.functions.fsystem import fexists, fcopy, fremove
from eddy.core.functions.misc import first, format_exception
from eddy.core.functions.misc import snap, snapF, cutR, uncapitalize
from eddy.core.functions.path import expandPath, isSubPath, uniquePath, shortPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.common import AbstractItem
from eddy.core.loaders.graphml import GraphmlLoader
from eddy.core.loaders.graphol import GrapholLoader
from eddy.core.loaders.project import ProjectLoader
from eddy.core.misc import HasActionSystem, HasMenuSystem
from eddy.core.output import getLogger
from eddy.core.qt import BrushIcon
from eddy.core.utils.clipboard import Clipboard

from eddy.ui.about import AboutDialog
from eddy.ui.diagram import NewDiagramDialog
from eddy.ui.diagram import RenameDiagramDialog
from eddy.ui.dock import DockWidget
from eddy.ui.explorer import OntologyExplorer
from eddy.ui.explorer import ProjectExplorer
from eddy.ui.forms import CardinalityRestrictionForm
from eddy.ui.forms import RefactorNameForm
from eddy.ui.forms import ValueForm
from eddy.ui.info import Info
from eddy.ui.mdi import MdiArea
from eddy.ui.mdi import MdiSubWindow
from eddy.ui.overview import Overview
from eddy.ui.palette import Palette
from eddy.ui.preferences import PreferencesDialog
from eddy.ui.progress import BusyProgressDialog
from eddy.ui.view import DiagramView
from eddy.ui.zoom import Zoom


LOGGER = getLogger(__name__)


class Session(HasActionSystem, HasMenuSystem, QMainWindow):
    """
    This class implements Eddy's main working session.
    """
    sgnClosed = pyqtSignal()
    sgnQuit = pyqtSignal()

    def __init__(self, path, **kwargs):
        """
        Initialize the application main working session.
        :type path: str
        :type kwargs: dict
        """
        super().__init__(**kwargs)

        #############################################
        # LOAD THE GIVEN PROJECT
        #################################

        self.project = ProjectLoader(path, self).run()

        #############################################
        # CREATE UTILITIES
        #################################

        self.clipboard = Clipboard(self)
        self.mf = MenuFactory(self)
        self.pf = PropertyFactory(self)

        #############################################
        # CREATE TOOLBARS
        #################################

        self.toolbarDocument = self.addToolBar('Document')
        self.toolbarDocument.setObjectName('toolbarDocument')
        self.toolbarEditor = self.addToolBar('Editor')
        self.toolbarEditor.setObjectName('toolbarEditor')
        self.toolbarView = self.addToolBar('View')
        self.toolbarView.setObjectName('toolbarView')
        self.toolbarGraphol = self.addToolBar('Graphol')
        self.toolbarGraphol.setObjectName('toolbarGraphol')

        #############################################
        # CREATE WIDGETS
        #################################

        self.info = Info(self)
        self.mdi = MdiArea(self)
        self.ontologyExplorer = OntologyExplorer(self)
        self.overview = Overview(self)
        self.palette_ = Palette(self)
        self.projectExplorer = ProjectExplorer(self)
        self.zoom = Zoom(self.toolbarView)

        self.dockInfo = DockWidget('Info', 'ic_info_outline_black', self)
        self.dockOntologyExplorer = DockWidget('Ontology Explorer', 'ic_explore_black', self)
        self.dockOverview = DockWidget('Overview', 'ic_zoom_black', self)
        self.dockPalette = DockWidget('Palette', 'ic_palette_black', self)
        self.dockProjectExplorer = DockWidget('Project Explorer', 'ic_storage_black', self)

        self.buttonSetBrush = QToolButton()

        #############################################
        # CONFIGURE SESSION
        #################################

        self.configureActions()
        self.configureWidgets()
        self.configureMenus()
        self.configureStatusBar()
        self.configureToolbars()
        self.configureState()

        self.setAcceptDrops(True)
        self.setCentralWidget(self.mdi)
        self.setDockOptions(QMainWindow.AnimatedDocks|QMainWindow.AllowTabbedDocks)
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle(self.project)

    #############################################
    #   SESSION CONFIGURATION
    #################################

    def configureActions(self):
        """
        Configure application built-in actions.
        """
        #############################################
        # APPLICATION GENERIC
        #################################

        action = QAction(
            QIcon(':/icons/24/ic_settings_black'), 'Preferences', self,
            objectName='open_preferences', shortcut=QKeySequence.Preferences,
            statusTip='Open application preferences', triggered=self.doOpenDialog)
        action.setData(PreferencesDialog)
        self.addAction(action)

        self.addAction(QAction(
            QIcon(':/icons/24/ic_power_settings_new_black'), 'Quit', self,
            objectName='quit', shortcut=QKeySequence.Quit,
            statusTip='Quit {0}'.format(APPNAME), triggered=self.doQuit))

        action = QAction(
            QIcon(':/icons/24/ic_help_outline_black'), 'About {0}'.format(APPNAME),
            self, objectName='about', shortcut=QKeySequence.HelpContents,
            statusTip='About {0}'.format(APPNAME), triggered=self.doOpenDialog)
        action.setData(AboutDialog)
        self.addAction(action)

        action = QAction(
            QIcon(':/icons/24/ic_link_black'), 'Visit DIAG website', self,
            objectName='diag_web', statusTip='Visit DIAG website',
            triggered=self.doOpenURL)
        action.setData(DIAG_HOME)
        self.addAction(action)

        action = QAction(
            QIcon(':/icons/24/ic_link_black'), 'Visit Graphol website', self,
            objectName='graphol_web', statusTip='Visit Graphol website',
            triggered=self.doOpenURL)
        action.setData(GRAPHOL_HOME)
        self.addAction(action)

        if Platform.identify() is Platform.Darwin:
            self.action('about').setIcon(QIcon())
            self.action('open_preferences').setIcon(QIcon())
            self.action('quit').setIcon(QIcon())

        #############################################
        # PROJECT / DIAGRAM MANAGEMENT
        #################################

        self.addAction(QAction(
            QIcon(':/icons/24/ic_add_document_black'), 'New diagram...',
            self, objectName='new_diagram', shortcut=QKeySequence.New,
            statusTip='Create a new diagram', triggered=self.doNewDiagram))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_folder_open_black'), 'Open...',
            self, objectName='open', shortcut=QKeySequence.Open,
            statusTip='Open a diagram and add it to the current project',
            triggered=self.doOpen))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_close_black'), 'Close', self,
            objectName='close_project', shortcut=QKeySequence.Close,
            statusTip='Close the current project', triggered=self.doClose))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_save_black'), 'Save', self,
            objectName='save', shortcut=QKeySequence.Save,
            statusTip='Save the current project', enabled=False,
            triggered=self.doSave))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_save_black'), 'Save As...', self,
            objectName='save_as', shortcut=QKeySequence.SaveAs,
            statusTip='Create a copy of the active diagram',
            enabled=False, triggered=self.doSaveAs))

        self.addAction(QAction(
            'Import...', self, objectName='import',
            statusTip='Import a document in the current project',
            triggered=self.doImport))

        self.addAction(QAction(
            'Export...', self, objectName='export',
            statusTip='Export the current project in a different format',
            enabled=not self.project.isEmpty(), triggered=self.doExport))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_print_black'), 'Print...', self,
            objectName='print', shortcut=QKeySequence.Print,
            statusTip='Print the current project', enabled=False,
            triggered=self.doPrint))

        #############################################
        # PROJECT SPECIFIC
        #################################

        action = self.project.undoStack.createUndoAction(self)
        action.setIcon(QIcon(':/icons/24/ic_undo_black'))
        action.setObjectName('undo')
        action.setShortcut(QKeySequence.Undo)
        self.addAction(action)

        action = self.project.undoStack.createRedoAction(self)
        action.setIcon(QIcon(':/icons/24/ic_redo_black'))
        action.setObjectName('redo')
        action.setShortcut(QKeySequence.Redo)
        self.addAction(action)

        self.addAction(QAction(
            QIcon(':/icons/24/ic_spellcheck_black'), 'Run syntax check',
            self, objectName='syntax_check', triggered=self.doSyntaxCheck,
            statusTip = 'Run syntax validation on the current project'))

        #############################################
        # DIAGRAM SPECIFIC
        #################################

        self.addAction(QAction(
            QIcon(':/icons/24/ic_center_focus_strong_black'), 'Center diagram', self,
            objectName='center_diagram', statusTip='Center the active diagram',
            enabled=False, triggered=self.doCenterDiagram))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_settings_black'), 'Properties...',
            self, objectName='diagram_properties',
            statusTip='Open current diagram properties',
            triggered=self.doOpenDiagramProperties))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_healing_black'), 'Snap to grid',
            self, objectName='snap_to_grid', enabled=False,
            statusTip='Align the elements in the active diagram to the grid',
            triggered=self.doSnapTopGrid))

        icon = QIcon()
        icon.addFile(':/icons/24/ic_grid_on_black', QSize(), QIcon.Normal, QIcon.On)
        icon.addFile(':/icons/24/ic_grid_off_black', QSize(), QIcon.Normal, QIcon.Off)
        self.addAction(QAction(
            icon, 'Toggle the grid', self, objectName='toggle_grid', enabled=False,
            checkable=True, statusTip='Activate or deactivate the diagram grid',
            triggered=self.doToggleGrid))

        #############################################
        # ITEM GENERICS
        #################################

        self.addAction(QAction(
            QIcon(':/icons/24/ic_content_cut_black'), 'Cut', self,
            objectName='cut', enabled=False, shortcut=QKeySequence.Cut,
            statusTip='Cut selected items', triggered=self.doCut))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_content_copy_black'), 'Copy', self,
            objectName='copy', enabled=False, shortcut=QKeySequence.Copy,
            statusTip='Copy selected items', triggered=self.doCopy))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_content_paste_black'), 'Paste', self,
            objectName='paste', enabled=False, shortcut=QKeySequence.Paste,
            statusTip='Paste previously copied items', triggered=self.doPaste))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_delete_black'), 'Delete', self,
            objectName='delete', enabled=False, shortcut=QKeySequence.Delete,
            statusTip='Delete selected items', triggered=self.doDelete))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_flip_to_front_black'), 'Bring to front',
            self, objectName='bring_to_front', enabled=False,
            statusTip='Bring selected items to front',
            triggered=self.doBringToFront))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_flip_to_back_black'), 'Send to back',
            self, objectName='send_to_back', enabled=False,
            statusTip='Send selected items to back',
            triggered=self.doSendToBack))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_select_all_black'), 'Select all',
            self, objectName='select_all', enabled=False,
            statusTip='Select all items in the active diagram',
            triggered=self.doSelectAll))

        #############################################
        # EDGE RELATED
        #################################

        self.addAction(QAction(
            QIcon(':/icons/24/ic_delete_black'), 'Remove breakpoint', self,
            objectName='remove_breakpoint', statusTip='Remove the selected edge breakpoint',
            triggered=self.doRemoveBreakpoint))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_equivalence_black'), 'Toggle edge equivalence', self,
            objectName='toggle_edge_equivalence', shortcut='ALT+C', enabled=False,
            statusTip='Toggle the equivalence for all the selected inclusion edges',
            triggered=self.doToggleEdgeEquivalence))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_swap_horiz_black'), 'Swap edge', self,
            objectName='swap_edge', shortcut='ALT+S', enabled=False,
            statusTip='Swap the direction of all the selected edges',
            triggered=self.doSwapEdge))

        #############################################
        # NODE RELATED
        #################################

        self.addAction(QAction(
            QIcon(':/icons/24/ic_settings_black'), 'Properties...',
            self, objectName='node_properties',
            triggered=self.doOpenNodeProperties))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_label_outline_black'), 'Rename...',
            self, objectName='refactor_name',
            triggered=self.doRefactorName))

        self.addAction(QAction(
            QIcon(':/icons/24/ic_refresh_black'), 'Relocate label',
            self, objectName='relocate_label',
            triggered=self.doRelocateLabel))

        action = QAction(
            QIcon(':/icons/24/ic_top_black'), Special.Top.value,
            self, objectName='special_top',
            triggered=self.doSetNodeSpecial)
        action.setData(Special.Top)
        self.addAction(action)

        action = QAction(
            QIcon(':/icons/24/ic_bottom_black'), Special.Bottom.value,
            self, objectName='special_bottom',
            triggered=self.doSetNodeSpecial)
        action.setData(Special.Bottom)
        self.addAction(action)

        style = self.style()
        isize = style.pixelMetric(QStyle.PM_ToolBarIconSize)
        for name, trigger in (('brush', self.doSetNodeBrush), ('refactor_brush', self.doRefactorBrush)):
            group = QActionGroup(self, objectName=name)
            for color in Color:
                action = QAction(
                    BrushIcon(isize, isize, color.value), color.name, self,
                    checkable=False, triggered=trigger)
                action.setData(color)
                group.addAction(action)
            self.addAction(group)

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        action = QAction(
            QIcon(':/icons/24/ic_square_outline_black'), 'Domain',
            self, objectName='property_domain',
            triggered=self.doComposePropertyExpression)
        action.setData(Item.DomainRestrictionNode)
        self.addAction(action)

        action = QAction(
            QIcon(':/icons/24/ic_square_black'), 'Range',
            self, objectName='property_range',
            triggered=self.doComposePropertyExpression)
        action.setData(Item.RangeRestrictionNode)
        self.addAction(action)

        #############################################
        # PROPERTY DOMAIN / RANGE SPECIFIC
        #################################

        group = QActionGroup(self, objectName='restriction')
        for restriction in Restriction:
            action = QAction(restriction.value, group,
                objectName=restriction.name, checkable=True,
                triggered=self.doSetPropertyRestriction)
            action.setData(restriction)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # VALUE-DOMAIN SPECIFIC
        #################################

        group = QActionGroup(self, objectName='datatype')
        for datatype in Datatype:
            action = QAction(datatype.value, group,
                objectName=datatype.name, checkable=True,
                triggered=self.doSetDatatype)
            action.setData(datatype)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # INDIVIDUAL SPECIFIC
        #################################

        group = QActionGroup(self, objectName='switch_individual')
        for identity in (Identity.Instance, Identity.Value):
            action = QAction(identity.value, group,
                objectName=identity.name,
                triggered=self.doSetIndividualAs)
            action.setData(identity)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # FACET SPECIFIC
        #################################

        group = QActionGroup(self, objectName='facet')
        for facet in Facet:
            action = QAction(facet.value, group,
                objectName=facet.name, checkable=True,
                triggered=self.doSetFacet)
            action.setData(facet)
            group.addAction(action)
        self.addAction(group)

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

        group = QActionGroup(self, objectName='switch_operator')
        for k, v in data.items():
            action = QAction(v, group,
                objectName=k.name, checkable=True,
                triggered=self.doSwitchOperatorNode)
            action.setData(k)
            group.addAction(action)
        self.addAction(group)

    def configureWidgets(self):
        """
        Configure previously initialized widgets.
        """
        #############################################
        # CONFIGURE TOOLBAR WIDGETS
        #################################

        self.buttonSetBrush.setIcon(QIcon(':/icons/24/ic_format_color_fill_black'))
        self.buttonSetBrush.setMenu(self.menu('brush'))
        self.buttonSetBrush.setPopupMode(QToolButton.InstantPopup)
        self.buttonSetBrush.setStatusTip('Change the background color of the selected predicate nodes')
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
        Configure application built-in menus.
        """
        #############################################
        # MENU BAR RELATED
        #################################

        menu = QMenu('File', objectName='file')
        menu.addAction(self.action('new_diagram'))
        menu.addAction(self.action('open'))
        menu.addSeparator()
        menu.addAction(self.action('save'))
        menu.addAction(self.action('save_as'))
        menu.addAction(self.action('close_project'))
        menu.addSeparator()
        menu.addAction(self.action('import'))
        menu.addAction(self.action('export'))
        menu.addSeparator()
        menu.addAction(self.action('print'))
        menu.addSeparator()
        menu.addAction(self.action('quit'))
        self.addMenu(menu)

        menu = QMenu('\u200CEdit', objectName='edit')
        menu.addAction(self.action('undo'))
        menu.addAction(self.action('redo'))
        menu.addSeparator()
        menu.addAction(self.action('cut'))
        menu.addAction(self.action('copy'))
        menu.addAction(self.action('paste'))
        menu.addAction(self.action('delete'))
        menu.addSeparator()
        menu.addAction(self.action('bring_to_front'))
        menu.addAction(self.action('send_to_back'))
        menu.addSeparator()
        menu.addAction(self.action('swap_edge'))
        menu.addAction(self.action('toggle_edge_equivalence'))
        menu.addSeparator()
        menu.addAction(self.action('select_all'))
        menu.addAction(self.action('snap_to_grid'))
        menu.addAction(self.action('center_diagram'))
        menu.addSeparator()
        menu.addAction(self.action('open_preferences'))
        self.addMenu(menu)

        menu = QMenu('Toolbars', objectName='toolbars')
        menu.addAction(self.toolbarDocument.toggleViewAction())
        menu.addAction(self.toolbarEditor.toggleViewAction())
        menu.addAction(self.toolbarGraphol.toggleViewAction())
        menu.addAction(self.toolbarView.toggleViewAction())
        self.addMenu(menu)

        menu = QMenu('\u200CView', objectName='view')
        menu.addAction(self.action('toggle_grid'))
        menu.addSeparator()
        menu.addMenu(self.menu('toolbars'))
        menu.addSeparator()
        menu.addAction(self.dockInfo.toggleViewAction())
        menu.addAction(self.dockOntologyExplorer.toggleViewAction())
        menu.addAction(self.dockOverview.toggleViewAction())
        menu.addAction(self.dockPalette.toggleViewAction())
        menu.addAction(self.dockProjectExplorer.toggleViewAction())
        self.addMenu(menu)

        menu = QMenu('Tools', objectName='tools')
        menu.addAction(self.action('syntax_check'))
        self.addMenu(menu)

        menu = QMenu('Help', objectName='help')
        menu.addAction(self.action('about'))
        menu.addSeparator()
        menu.addAction(self.action('diag_web'))
        menu.addAction(self.action('graphol_web'))
        self.addMenu(menu)

        #############################################
        # NODE GENERIC
        #################################

        menu = QMenu('Select color', objectName='brush')
        menu.setIcon(QIcon(':/icons/24/ic_format_color_fill_black'))
        menu.addActions(self.action('brush').actions())
        self.addMenu(menu)

        menu = QMenu('Special type', objectName='special')
        menu.setIcon(QIcon(':/icons/24/ic_star_black'))
        menu.addAction(self.action('special_top'))
        menu.addAction(self.action('special_bottom'))
        self.addMenu(menu)

        menu = QMenu('Select color', objectName='refactor_brush')
        menu.setIcon(QIcon(':/icons/24/ic_format_color_fill_black'))
        menu.addActions(self.action('refactor_brush').actions())
        self.addMenu(menu)

        menu = QMenu('Refactor', objectName='refactor')
        menu.setIcon(QIcon(':/icons/24/ic_format_shapes_black'))
        menu.addAction(self.action('refactor_name'))
        menu.addMenu(self.menu('refactor_brush'))
        self.addMenu(menu)

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        menu = QMenu('Compose', objectName='compose')
        menu.setIcon(QIcon(':/icons/24/ic_create_black'))
        menu.addAction(self.action('property_domain'))
        menu.addAction(self.action('property_range'))
        self.addMenu(menu)

        #############################################
        # VALUE-DOMAIN SPECIFIC
        #################################

        menu = QMenu('Select type', objectName='datatype')
        menu.setIcon(QIcon(':/icons/24/ic_refresh_black'))
        menu.addActions(self.action('datatype').actions())
        self.addMenu(menu)

        #############################################
        # FACET SPECIFIC
        #################################

        menu = QMenu('Select facet', objectName='facet')
        menu.setIcon(QIcon(':/icons/24/ic_refresh_black'))
        menu.addActions(self.action('facet').actions())
        self.addMenu(menu)

        #############################################
        # PROPERTY DOMAIN / RANGE SPECIFIC
        #################################

        menu = QMenu('Select restriction', objectName='property_restriction')
        menu.setIcon(QIcon(':/icons/24/ic_refresh_black'))
        menu.addActions(self.action('restriction').actions())
        self.addMenu(menu)

        #############################################
        # INDIVIDUAL SPECIFIC
        #################################

        menu = QMenu('Switch to', objectName='switch_individual')
        menu.setIcon(QIcon(':/icons/24/ic_refresh_black'))
        menu.addActions(self.action('switch_individual').actions())
        self.addMenu(menu)

        #############################################
        # OPERATORS SPECIFIC
        #################################

        menu = QMenu('Switch to', objectName='switch_operator')
        menu.setIcon(QIcon(':/icons/24/ic_refresh_black'))
        menu.addActions(self.action('switch_operator').actions())
        self.addMenu(menu)

        #############################################
        # CONFIGURE MENUBAR
        #################################

        menuBar = self.menuBar()
        menuBar.addMenu(self.menu('file'))
        menuBar.addMenu(self.menu('edit'))
        menuBar.addMenu(self.menu('view'))
        menuBar.addMenu(self.menu('tools'))
        menuBar.addMenu(self.menu('help'))
    
    def configureStatusBar(self):
        """
        Configure the status bar.
        """
        statusbar = QStatusBar(self)
        statusbar.setSizeGripEnabled(False)
        self.setStatusBar(statusbar)
    
    def configureToolbars(self):
        """
        Configure previously initialized toolbars.
        """
        self.toolbarDocument.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbarEditor.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbarView.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbarGraphol.setContextMenuPolicy(Qt.PreventContextMenu)

        self.toolbarDocument.addAction(self.action('new_diagram'))
        self.toolbarDocument.addAction(self.action('open'))
        self.toolbarDocument.addAction(self.action('save'))
        self.toolbarDocument.addAction(self.action('print'))

        self.toolbarEditor.addAction(self.action('undo'))
        self.toolbarEditor.addAction(self.action('redo'))
        self.toolbarEditor.addSeparator()
        self.toolbarEditor.addAction(self.action('cut'))
        self.toolbarEditor.addAction(self.action('copy'))
        self.toolbarEditor.addAction(self.action('paste'))
        self.toolbarEditor.addAction(self.action('delete'))
        self.toolbarEditor.addSeparator()
        self.toolbarEditor.addAction(self.action('bring_to_front'))
        self.toolbarEditor.addAction(self.action('send_to_back'))
        self.toolbarEditor.addSeparator()
        self.toolbarEditor.addAction(self.action('swap_edge'))
        self.toolbarEditor.addAction(self.action('toggle_edge_equivalence'))
        self.toolbarEditor.addSeparator()
        self.toolbarEditor.addWidget(self.buttonSetBrush)

        self.toolbarView.addAction(self.action('toggle_grid'))
        self.toolbarView.addAction(self.action('snap_to_grid'))
        self.toolbarView.addAction(self.action('center_diagram'))
        self.toolbarView.addSeparator()
        self.toolbarView.addWidget(self.zoom.buttonZoomOut)
        self.toolbarView.addWidget(self.zoom.buttonZoomIn)
        self.toolbarView.addWidget(self.zoom.buttonZoomReset)

        self.toolbarGraphol.addAction(self.action('syntax_check'))

    def configureState(self):
        """
        Configure application state by reading the preferences file.
        """
        settings = QSettings(ORGANIZATION, APPNAME)
        self.restoreGeometry(settings.value('session/geometry', QByteArray(), QByteArray))
        self.restoreState(settings.value('session/state', QByteArray(), QByteArray))
        self.action('toggle_grid').setChecked(settings.value('diagram/grid', False, bool))

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
                    command = CommandItemsTranslate(diagram, items, moveX, moveY, 'center diagram')
                    self.project.undoStack.push(command)
                    self.mdi.activeView.centerOn(0, 0)

    @pyqtSlot()
    def doClose(self):
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
                name = 'compose {0} {1}'.format(node.shortname, item.shortname)
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
            dialog.setFileMode(QFileDialog.AnyFile)
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
                    msgbox.setDetailedText(format_exception(e))
                    msgbox.setIconPixmap(QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                    msgbox.setStandardButtons(QMessageBox.Close)
                    msgbox.setText('Eddy could not load the specified diagram: {0}!'.format(path))
                    msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
                    msgbox.setWindowTitle('Diagram load failed!')
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
            properties = self.pf.create(diagram)
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
                properties = self.pf.create(diagram, node)
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
                self.project.undoStack.push(CommandLabelMove(diagram, node, undo, redo))

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
            msgbox.setIconPixmap(QIcon(':/icons/48/ic_question_outline_black').pixmap(48))
            msgbox.setInformativeText('<b>NOTE: This action is not reversible!</b>')
            msgbox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msgbox.setTextFormat(Qt.RichText)
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Remove diagram: {0}?'.format(diagram.name))
            msgbox.setText(dedent("""Are you sure you want to remove diagram <b>{0}</b>?
            If you continue, all the predicates that have been defined only in this
            diagram will be lost!""".format(diagram.name)))
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
            msgbox.setDetailedText(format_exception(e))
            msgbox.setIconPixmap(QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText('Eddy could not save the current project!')
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Save failed!')
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
            dialog.setFileMode(QFileDialog.AnyFile)
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
                    data = restriction.toString()
                else:
                    form = CardinalityRestrictionForm(self)
                    if form.exec_() == CardinalityRestrictionForm.Accepted:
                        data = restriction.toString(form.min() or '-', form.max() or '-')
                if data and node.text() != data:
                    name = 'change {0} to {1}'.format(node.shortname, data)
                    self.project.undoStack.push(CommandLabelChange(diagram, node, node.text(), data, name))

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
                        self.project.undoStack.push(CommandLabelChange(diagram, node, node.text(), data, name))
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
                    name = 'change {0} to {1}'.format(node.shortname, data)
                    self.project.undoStack.push(CommandLabelChange(diagram, node, node.text(), data, name))

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
                    self.project.undoStack.push(CommandLabelChange(diagram, node, node.text(), data, name))

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
                    name = 'change {0} to {1}'.format(node.facet.value, facet.value)
                    self.project.undoStack.push(CommandLabelChange(diagram, node, node.text(), data, name))

    @pyqtSlot()
    def doSnapTopGrid(self):
        """
        Snap all the element sin the active diagram to the grid.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            data = {'redo': {'nodes': {}, 'edges': {}}, 'undo': {'nodes': {}, 'edges': {}}}
            for item in diagram.items():
                if item.isNode():
                    undoPos = item.pos()
                    redoPos = snap(undoPos, Diagram.GridSize)
                    if undoPos != redoPos:
                        data['undo']['nodes'][item] = {
                            'pos': undoPos,
                            'anchors': {k: v for k, v in item.anchors.items()}
                        }
                        data['redo']['nodes'][item] = {
                            'pos': redoPos,
                            'anchors': {k: v + redoPos - undoPos for k, v in item.anchors.items()}
                        }
                elif item.isEdge():
                    undoPts = item.breakpoints
                    redoPts = [snap(x, Diagram.GridSize) for x in undoPts]
                    if undoPts != redoPts:
                        data['undo']['edges'][item] = {'breakpoints': undoPts}
                        data['redo']['edges'][item] = {'breakpoints': redoPts}

            if data['undo']['nodes'] or data['undo']['edges']:
                self.project.undoStack.push(CommandSnapItemsToGrid(diagram, data))

    @pyqtSlot()
    def doSwapEdge(self):
        """
        Swap the selected edges by inverting source/target points.
        """
        diagram = self.mdi.activeDiagram
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = [e for e in diagram.selectedEdges() if e.isSwapAllowed()]
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
        icon = QIcon(':/icons/48/ic_done_black')
        message = 'No syntax error found!'
        with BusyProgressDialog('Running syntax validation...', 1, self):
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
                    message = 'Syntax error detected on {0} from {1} to {2}: <i>{3}</i>.' \
                    .format(edge.name, nameA, nameB, uncapitalize(result.message))
                    icon = QIcon(':/icons/48/ic_warning_black')
                    item = edge
                    break
            else:
                for node in self.project.nodes():
                    if node.identity is Identity.Unknown:
                        name = '{0} "{1}"'.format(node.name, node.id)
                        if node.isPredicate():
                            name = '{0} "{1}:{2}"'.format(node.name, node.text(), node.id)
                        message = 'Unkown node identity detected on {0}.'.format(name)
                        icon = QIcon(':/icons/48/ic_warning_black')
                        item = node
                        break

        msgbox = QMessageBox(self)
        msgbox.setIconPixmap(icon.pixmap(48))
        msgbox.setStandardButtons(QMessageBox.Close)
        msgbox.setText(message)
        msgbox.setTextFormat(Qt.RichText)
        msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Syntax validation completed!')
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
    def doToggleGrid(self):
        """
        Toggle snap to grid setting.
        """
        settings = QSettings(ORGANIZATION, APPNAME)
        settings.setValue('diagram/grid', self.action('toggle_grid').isChecked())
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

        self.action('bring_to_front').setEnabled(isNodeSelected)
        self.action('center_diagram').setEnabled(isDiagramActive)
        self.action('cut').setEnabled(isNodeSelected)
        self.action('copy').setEnabled(isNodeSelected)
        self.action('delete').setEnabled(isNodeSelected or isEdgeSelected)
        self.action('export').setEnabled(not isProjectEmpty)
        self.action('paste').setEnabled(not isClipboardEmpty)
        self.action('save').setEnabled(not isUndoStackClean)
        self.action('save_as').setEnabled(isDiagramActive)
        self.action('select_all').setEnabled(isDiagramActive)
        self.action('send_to_back').setEnabled(isNodeSelected)
        self.action('snap_to_grid').setEnabled(isDiagramActive)
        self.action('swap_edge').setEnabled(isEdgeSelected and isEdgeSwapEnabled)
        self.action('toggle_edge_equivalence').setEnabled(isEdgeSelected and isEdgeToggleEnabled)
        self.action('toggle_grid').setEnabled(isDiagramActive)
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
                button = self.palette_.button(item.type())
                button.setChecked(False)
                diagram.setMode(DiagramMode.Idle)

    @pyqtSlot(DiagramMode)
    def onDiagramModeChanged(self, mode):
        """
        Executed when the scene operation mode changes.
        :type mode: DiagramMode
        """
        if mode not in (DiagramMode.NodeAdd, DiagramMode.EdgeAdd):
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
                    diagram.setMode(DiagramMode.NodeAdd, button.item)
                elif Item.InclusionEdge <= button.item <= Item.MembershipEdge:
                    diagram.setMode(DiagramMode.EdgeAdd, button.item)

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
            msgbox.setIconPixmap(QIcon(':/icons/48/ic_question_outline_black').pixmap(48))
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Save changes?')
            msgbox.setStandardButtons(QMessageBox.Cancel|QMessageBox.No|QMessageBox.Yes)
            msgbox.setText('Your project contains unsaved changes. Do you want to save?')
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
        # noinspection PyUnresolvedReferences
        return super().eventFilter(source, event)

    def keyReleaseEvent(self, keyEvent):
        """
        Executed when a keyboard button is released from the scene.
        :type keyEvent: QKeyEvent
        """
        if keyEvent.key() == Qt.Key_Control:
            diagram = self.mdi.activeDiagram
            if diagram and not diagram.isEdgeAddInProgress():
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
        Create a subwindow in the MDI area that displays the given widget.
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
        with BusyProgressDialog('Importing {0}...'.format(name), 2, self):

            try:
                worker = GraphmlLoader(self.project, path, self)
                diagram = worker.run()
            except Exception as e:
                msgbox = QMessageBox(self)
                msgbox.setDetailedText(format_exception(e))
                msgbox.setIconPixmap(QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                msgbox.setStandardButtons(QMessageBox.Close)
                msgbox.setText('Eddy could not import the specified file: {0}!'.format(path))
                msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('Diagram import failed!')
                msgbox.exec_()
            else:
                self.project.addDiagram(diagram)
                self.doFocusDiagram(diagram)
                self.doSave()

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