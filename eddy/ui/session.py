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
import sys
import textwrap
import webbrowser

from collections import OrderedDict

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy import APPNAME, DIAG_HOME, GRAPHOL_HOME, ORGANIZATION, VERSION
from eddy.core.clipboard import Clipboard
from eddy.core.commands.common import CommandComposeAxiom
from eddy.core.commands.common import CommandItemsRemove
from eddy.core.commands.common import CommandItemsTranslate
from eddy.core.commands.common import CommandSnapItemsToGrid
from eddy.core.commands.edges import CommandEdgeBreakpointRemove
from eddy.core.commands.edges import CommandEdgeSwap
from eddy.core.commands.labels import CommandLabelMove
from eddy.core.commands.labels import CommandLabelChange
from eddy.core.commands.nodes import CommandNodeSwitchTo
from eddy.core.commands.nodes import CommandNodeSetBrush
from eddy.core.commands.nodes import CommandNodeSetDepth
from eddy.core.commands.project import CommandProjectSetProfile
from eddy.core.common import HasActionSystem
from eddy.core.common import HasMenuSystem
from eddy.core.common import HasPluginSystem
from eddy.core.common import HasWidgetSystem
from eddy.core.common import HasDiagramExportSystem
from eddy.core.common import HasProjectExportSystem
from eddy.core.common import HasDiagramLoadSystem
from eddy.core.common import HasProjectLoadSystem
from eddy.core.common import HasProfileSystem
from eddy.core.datatypes.graphol import Identity, Item
from eddy.core.datatypes.graphol import Restriction, Special
from eddy.core.datatypes.misc import Color, DiagramMode
from eddy.core.datatypes.owl import Datatype, Facet
from eddy.core.datatypes.qt import BrushIcon, Font
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.exporters.graphml import GraphMLDiagramExporter
from eddy.core.exporters.graphol import GrapholDiagramExporter
from eddy.core.exporters.graphol import GrapholProjectExporter
from eddy.core.exporters.owl2 import OWLProjectExporter
from eddy.core.exporters.pdf import PdfDiagramExporter
from eddy.core.exporters.printer import PrinterDiagramExporter
from eddy.core.factory import MenuFactory, PropertyFactory
from eddy.core.functions.fsystem import fcopy, fremove, fexists
from eddy.core.functions.misc import first, format_exception, rstrip
from eddy.core.functions.misc import snap, snapF
from eddy.core.functions.path import expandPath, isSubPath
from eddy.core.functions.path import uniquePath, shortPath
from eddy.core.functions.signals import connect
from eddy.core.loaders.graphml import GraphMLDiagramLoader
from eddy.core.loaders.graphol import GrapholDiagramLoader
from eddy.core.loaders.graphol import GrapholProjectLoader
from eddy.core.output import getLogger
from eddy.core.plugin import PluginManager
from eddy.core.profiles.owl2 import OWL2Profile
from eddy.core.profiles.owl2ql import OWL2QLProfile
from eddy.core.profiles.owl2rl import OWL2RLProfile

from eddy.ui.about import AboutDialog
from eddy.ui.diagram import NewDiagramDialog
from eddy.ui.diagram import RenameDiagramDialog
from eddy.ui.fields import ComboBox
from eddy.ui.forms import CardinalityRestrictionForm
from eddy.ui.forms import RefactorNameForm
from eddy.ui.forms import ValueForm
from eddy.ui.log import LogDialog
from eddy.ui.mdi import MdiArea
from eddy.ui.mdi import MdiSubWindow
from eddy.ui.plugin import PluginInstallDialog
from eddy.ui.preferences import PreferencesDialog
from eddy.ui.progress import BusyProgressDialog
from eddy.ui.syntax import SyntaxValidationDialog
from eddy.ui.view import DiagramView


_LINUX = sys.platform.startswith('linux')
_MACOS = sys.platform.startswith('darwin')
_WIN32 = sys.platform.startswith('win32')


LOGGER = getLogger(__name__)


class Session(HasActionSystem, HasMenuSystem, HasPluginSystem, HasWidgetSystem,
              HasDiagramExportSystem, HasProjectExportSystem, HasDiagramLoadSystem,
              HasProjectLoadSystem, HasProfileSystem, QtWidgets.QMainWindow):
    """
    Extends QtWidgets.QMainWindow and implements Eddy main working session.
    Additionally to built-in signals, this class emits:

    * sgnClosed: whenever the current session is closed.
    * sgnDiagramFocus: whenever a diagram is to be focused.
    * sgnDiagramLoad: whenever a diagram is to be loaded.
    * sgnDiagramLoaded: to notify that a diagram has been loaded.
    * sgnDiagramRenamed: to notify that a diagram has been renamed.
    * sgnPluginDisposed: to notify that a plugin has been destroyed.
    * sgnPluginStarted: to notify that a plugin startup sequence has been completed.
    * sgnProjectSave: whenever the current project is to be saved.
    * sgnProjectSaved: to notify that the current project has been saved.
    * sgnQuit: whenever the application is to be terminated.
    * sgnReady: after the session startup sequence completes.
    * sgnUpdateState: to notify that something in the session state changed.
    """
    sgnClosed = QtCore.pyqtSignal()
    sgnDiagramFocus = QtCore.pyqtSignal('QGraphicsScene')
    sgnDiagramFocused = QtCore.pyqtSignal('QGraphicsScene')
    sgnDiagramLoad = QtCore.pyqtSignal(str)
    sgnDiagramLoaded = QtCore.pyqtSignal('QGraphicsScene')
    sgnDiagramRenamed = QtCore.pyqtSignal('QGraphicsScene')
    sgnPluginDisposed = QtCore.pyqtSignal(str)
    sgnPluginStarted = QtCore.pyqtSignal(str)
    sgnProjectSave = QtCore.pyqtSignal()
    sgnProjectSaved = QtCore.pyqtSignal()
    sgnQuit = QtCore.pyqtSignal()
    sgnReady = QtCore.pyqtSignal()
    sgnUpdateState = QtCore.pyqtSignal()

    def __init__(self, path, **kwargs):
        """
        Initialize the application main working session.
        :type path: str
        :type kwargs: dict
        """
        super(Session, self).__init__(**kwargs)

        #############################################
        # INITIALIZE MAIN STUFF
        #################################

        self.clipboard = Clipboard(self)
        self.undostack = QtWidgets.QUndoStack(self)
        self.mdi = MdiArea(self)
        self.mf = MenuFactory(self)
        self.pf = PropertyFactory(self)
        self.pmanager = PluginManager(self)

        # ------------------------------------------------------- #
        # Because toolbars are needed both by built-in widgets    #
        # and built-in actions, they need to be initialized       #
        # outside 'init' methods not to generate cycles:          #
        # ------------------------------------------------------- #
        # * TOOLBARS  -> WIDGETS && ACTIONS                       #
        # * WIDGETS   -> MENUS                                    #
        # * MENUS     -> ACTIONS && TOOLBARS                      #
        # ------------------------------------------------------- #

        self.addWidget(QtWidgets.QToolBar('Document', objectName='document_toolbar'))
        self.addWidget(QtWidgets.QToolBar('Editor', objectName='editor_toolbar'))
        self.addWidget(QtWidgets.QToolBar('View', objectName='view_toolbar'))
        self.addWidget(QtWidgets.QToolBar('Graphol', objectName='graphol_toolbar'))

        #############################################
        # CONFIGURE SESSION
        #################################

        self.initActions()
        self.initMenus()
        self.initProfiles()
        self.initWidgets()
        self.initExporters()
        self.initLoaders()
        self.initSignals()
        self.initStatusBar()
        self.initToolBars()
        self.initPlugins()
        self.initState()

        #############################################
        # LOAD THE GIVEN PROJECT
        #################################

        self.project = self.createProjectLoader(File.Graphol, path, self).load()

        #############################################
        # COMPLETE SESSION SETUP
        #################################

        self.setAcceptDrops(True)
        self.setCentralWidget(self.mdi)
        self.setDockOptions(Session.AnimatedDocks | Session.AllowTabbedDocks)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle(self.project)

        self.sgnReady.emit()

        LOGGER.header('Session startup completed: %s v%s', APPNAME, VERSION)

    #############################################
    #   SESSION CONFIGURATION
    #################################

    def initActions(self):
        """
        Configure application built-in actions.
        """
        #############################################
        # APPLICATION GENERIC
        #################################

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_settings_black'), 'Preferences', self,
            objectName='open_preferences', shortcut=QtGui.QKeySequence.Preferences,
            statusTip='Open application preferences', triggered=self.doOpenDialog)
        action.setData(PreferencesDialog)
        self.addAction(action)

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_power_settings_new_black'), 'Quit', self,
            objectName='quit', shortcut=QtGui.QKeySequence.Quit,
            statusTip='Quit {0}'.format(APPNAME), triggered=self.doQuit))

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_help_outline_black'), 'About {0}'.format(APPNAME),
            self, objectName='about', shortcut=QtGui.QKeySequence.HelpContents,
            statusTip='About {0}'.format(APPNAME), triggered=self.doOpenDialog)
        action.setData(AboutDialog)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_link_black'), 'Visit DIAG website', self,
            objectName='diag_web', statusTip='Visit DIAG website',
            triggered=self.doOpenURL)
        action.setData(DIAG_HOME)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_link_black'), 'Visit Graphol website', self,
            objectName='graphol_web', statusTip='Visit Graphol website',
            triggered=self.doOpenURL)
        action.setData(GRAPHOL_HOME)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_message_black'), 'Show log...',
            self, objectName='show_log', statusTip='Show application log',
            triggered=self.doOpenDialog)
        action.setData(LogDialog)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_extension_black'), 'Install plugin...',
            self, objectName='install_plugin', statusTip='Install a plugin',
            triggered=self.doOpenDialog)
        action.setData(PluginInstallDialog)
        self.addAction(action)

        if _MACOS:
            self.action('about').setIcon(QtGui.QIcon())
            self.action('open_preferences').setIcon(QtGui.QIcon())
            self.action('quit').setIcon(QtGui.QIcon())

        #############################################
        # PROJECT / DIAGRAM MANAGEMENT
        #################################

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_add_document_black'), 'New diagram...',
            self, objectName='new_diagram', shortcut=QtGui.QKeySequence.New,
            statusTip='Create a new diagram', triggered=self.doNewDiagram))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'), 'Rename...',
            self, objectName='rename_diagram', statusTip='Rename a diagram',
            triggered=self.doRenameDiagram))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_delete_black'), 'Delete...',
            self, objectName='remove_diagram', statusTip='Delete a diagram',
            triggered=self.doRemoveDiagram))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_folder_open_black'), 'Open...',
            self, objectName='open', shortcut=QtGui.QKeySequence.Open,
            statusTip='Open a diagram and add it to the current project',
            triggered=self.doOpen))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_close_black'), 'Close', self,
            objectName='close_project', shortcut=QtGui.QKeySequence.Close,
            statusTip='Close the current project', triggered=self.doClose))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_save_black'), 'Save', self,
            objectName='save', shortcut=QtGui.QKeySequence.Save,
            statusTip='Save the current project', enabled=False,
            triggered=self.doSave))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_save_black'), 'Save As...', self,
            objectName='save_as', shortcut=QtGui.QKeySequence.SaveAs,
            statusTip='Create a copy of the active diagram',
            enabled=False, triggered=self.doSaveAs))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_import_black'), 'Import...', self,
            statusTip='Import a document in the current project',
            objectName='import', triggered=self.doImport))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_export_black'), 'Export...', self,
            statusTip='Export the current project in a different format',
            objectName='export', enabled=False, triggered=self.doExport))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_print_black'), 'Print...', self,
            objectName='print', shortcut=QtGui.QKeySequence.Print,
            statusTip='Print the active diagram', enabled=False,
            triggered=self.doPrint))

        #############################################
        # PROJECT SPECIFIC
        #################################

        action = self.undostack.createUndoAction(self)
        action.setIcon(QtGui.QIcon(':/icons/24/ic_undo_black'))
        action.setObjectName('undo')
        action.setShortcut(QtGui.QKeySequence.Undo)
        self.addAction(action)

        action = self.undostack.createRedoAction(self)
        action.setIcon(QtGui.QIcon(':/icons/24/ic_redo_black'))
        action.setObjectName('redo')
        action.setShortcut(QtGui.QKeySequence.Redo)
        self.addAction(action)

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_spellcheck_black'), 'Run syntax check',
            self, objectName='syntax_check', triggered=self.doSyntaxCheck,
            statusTip='Run syntax validation according to the selected profile'))

        #############################################
        # DIAGRAM SPECIFIC
        #################################

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_center_focus_strong_black'), 'Center diagram', self,
            objectName='center_diagram', statusTip='Center the active diagram',
            enabled=False, triggered=self.doCenterDiagram))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_settings_black'), 'Properties...',
            self, objectName='diagram_properties',
            statusTip='Open current diagram properties',
            triggered=self.doOpenDiagramProperties))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_healing_black'), 'Snap to grid',
            self, objectName='snap_to_grid', enabled=False,
            statusTip='Align the elements in the active diagram to the grid',
            triggered=self.doSnapTopGrid))

        icon = QtGui.QIcon()
        icon.addFile(':/icons/24/ic_grid_on_black', QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.On)
        icon.addFile(':/icons/24/ic_grid_off_black', QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.addAction(QtWidgets.QAction(
            icon, 'Toggle the grid', self, objectName='toggle_grid', enabled=False,
            checkable=True, statusTip='Activate or deactivate the diagram grid',
            triggered=self.doToggleGrid))

        #############################################
        # ITEM GENERICS
        #################################

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_content_cut_black'), 'Cut', self,
            objectName='cut', enabled=False, shortcut=QtGui.QKeySequence.Cut,
            statusTip='Cut selected items', triggered=self.doCut))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_content_copy_black'), 'Copy', self,
            objectName='copy', enabled=False, shortcut=QtGui.QKeySequence.Copy,
            statusTip='Copy selected items', triggered=self.doCopy))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_content_paste_black'), 'Paste', self,
            objectName='paste', enabled=False, shortcut=QtGui.QKeySequence.Paste,
            statusTip='Paste previously copied items', triggered=self.doPaste))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_delete_black'), 'Delete', self,
            objectName='delete', enabled=False, shortcut=QtGui.QKeySequence.Delete,
            statusTip='Delete selected items', triggered=self.doDelete))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_delete_forever_black'), 'Purge', self,
            objectName='purge', enabled=False, triggered=self.doPurge,
            statusTip='Delete selected items by also removing no more necessary elements'))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_flip_to_front_black'), 'Bring to front',
            self, objectName='bring_to_front', enabled=False,
            statusTip='Bring selected items to front',
            triggered=self.doBringToFront))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_flip_to_back_black'), 'Send to back',
            self, objectName='send_to_back', enabled=False,
            statusTip='Send selected items to back',
            triggered=self.doSendToBack))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_select_all_black'), 'Select all',
            self, objectName='select_all', enabled=False,
            statusTip='Select all items in the active diagram',
            shortcut=QtGui.QKeySequence.SelectAll, triggered=self.doSelectAll))

        #############################################
        # EDGE RELATED
        #################################

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_delete_black'), 'Remove breakpoint', self,
            objectName='remove_breakpoint', statusTip='Remove the selected edge breakpoint',
            triggered=self.doRemoveBreakpoint))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_swap_horiz_black'), 'Swap edge', self,
            objectName='swap_edge', shortcut='ALT+S', enabled=False,
            statusTip='Swap the direction of all the selected edges',
            triggered=self.doSwapEdge))

        #############################################
        # NODE RELATED
        #################################

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_settings_black'), 'Properties...',
            self, objectName='node_properties',
            triggered=self.doOpenNodeProperties))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'), 'Rename...',
            self, objectName='refactor_name',
            triggered=self.doRefactorName))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_refresh_black'), 'Relocate label',
            self, objectName='relocate_label',
            triggered=self.doRelocateLabel))

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_top_black'), Special.Top.value,
            self, objectName='special_top',
            triggered=self.doSetNodeSpecial)
        action.setData(Special.Top)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_bottom_black'), Special.Bottom.value,
            self, objectName='special_bottom',
            triggered=self.doSetNodeSpecial)
        action.setData(Special.Bottom)
        self.addAction(action)

        style = self.style()
        isize = style.pixelMetric(QtWidgets.QStyle.PM_ToolBarIconSize)
        for name, trigger in (('brush', self.doSetNodeBrush), ('refactor_brush', self.doRefactorBrush)):
            group = QtWidgets.QActionGroup(self, objectName=name)
            for color in Color:
                action = QtWidgets.QAction(
                    BrushIcon(isize, isize, color.value), color.name,
                    self, checkable=False, triggered=trigger)
                action.setData(color)
                group.addAction(action)
            self.addAction(group)

        #############################################
        # ROLE SPECIFIC
        #################################

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_square_half_black'), 'Invert Role', self,
            objectName='invert_role', triggered=self.doInvertRole,
            statusTip='Invert the selected role in all its occurrences'))

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_square_outline_black'), 'Domain',
            self, objectName='property_domain',
            triggered=self.doComposePropertyExpression)
        action.setData(Item.DomainRestrictionNode)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_square_black'), 'Range',
            self, objectName='property_range',
            triggered=self.doComposePropertyExpression)
        action.setData(Item.RangeRestrictionNode)
        self.addAction(action)

        #############################################
        # PROPERTY DOMAIN / RANGE SPECIFIC
        #################################

        group = QtWidgets.QActionGroup(self, objectName='restriction')
        for restriction in Restriction:
            action = QtWidgets.QAction(restriction.value, group,
                objectName=restriction.name, checkable=True,
                triggered=self.doSetPropertyRestriction)
            action.setData(restriction)
            group.addAction(action)
        self.addAction(group)

        data = OrderedDict()
        data[Item.DomainRestrictionNode] = 'Domain'
        data[Item.RangeRestrictionNode] = 'Range'

        group = QtWidgets.QActionGroup(self, objectName='switch_restriction')
        for k, v in data.items():
            action = QtWidgets.QAction(v, group,
                objectName=k.name, checkable=True,
                triggered=self.doSwitchRestrictionNode)
            action.setData(k)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # VALUE-DOMAIN SPECIFIC
        #################################

        group = QtWidgets.QActionGroup(self, objectName='datatype')
        for datatype in Datatype:
            action = QtWidgets.QAction(datatype.value, group,
                objectName=datatype.name, checkable=True,
                triggered=self.doSetDatatype)
            action.setData(datatype)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # INDIVIDUAL SPECIFIC
        #################################

        group = QtWidgets.QActionGroup(self, objectName='switch_individual')
        for identity in (Identity.Individual, Identity.Value):
            action = QtWidgets.QAction(identity.value, group,
                objectName=identity.name, checkable=True,
                triggered=self.doSetIndividualAs)
            action.setData(identity)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # FACET SPECIFIC
        #################################

        group = QtWidgets.QActionGroup(self, objectName='facet')
        for facet in Facet:
            action = QtWidgets.QAction(facet.value, group,
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

        group = QtWidgets.QActionGroup(self, objectName='switch_operator')
        for k, v in data.items():
            action = QtWidgets.QAction(v, group,
                objectName=k.name, checkable=True,
                triggered=self.doSwitchOperatorNode)
            action.setData(k)
            group.addAction(action)
        self.addAction(group)

    def initExporters(self):
        """
        Initialize diagram and project exporters.
        """
        self.addDiagramExporter(GraphMLDiagramExporter)
        self.addDiagramExporter(GrapholDiagramExporter)
        self.addDiagramExporter(PdfDiagramExporter)
        self.addProjectExporter(GrapholProjectExporter)
        self.addProjectExporter(OWLProjectExporter)

    def initLoaders(self):
        """
        Initialize diagram and project loaders.
        """
        self.addDiagramLoader(GraphMLDiagramLoader)
        self.addDiagramLoader(GrapholDiagramLoader)
        self.addProjectLoader(GrapholProjectLoader)

    def initMenus(self):
        """
        Configure application built-in menus.
        """
        #############################################
        # MENU BAR RELATED
        #################################

        menu = QtWidgets.QMenu('File', objectName='file')
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

        menu = QtWidgets.QMenu('\u200CEdit', objectName='edit')
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
        menu.addSeparator()
        menu.addAction(self.action('select_all'))
        menu.addAction(self.action('snap_to_grid'))
        menu.addAction(self.action('center_diagram'))
        menu.addSeparator()
        menu.addAction(self.action('open_preferences'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Toolbars', objectName='toolbars')
        menu.addAction(self.widget('document_toolbar').toggleViewAction())
        menu.addAction(self.widget('editor_toolbar').toggleViewAction())
        menu.addAction(self.widget('graphol_toolbar').toggleViewAction())
        menu.addAction(self.widget('view_toolbar').toggleViewAction())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('\u200CView', objectName='view')
        menu.addAction(self.action('toggle_grid'))
        menu.addSeparator()
        menu.addAction(self.action('show_log'))
        menu.addSeparator()
        menu.addMenu(self.menu('toolbars'))
        menu.addSeparator()
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Tools', objectName='tools')
        menu.addAction(self.action('install_plugin'))
        menu.addSeparator()
        menu.addAction(self.action('syntax_check'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Help', objectName='help')
        menu.addAction(self.action('about'))
        menu.addSeparator()
        menu.addAction(self.action('diag_web'))
        menu.addAction(self.action('graphol_web'))
        self.addMenu(menu)

        #############################################
        # NODE GENERIC
        #################################

        menu = QtWidgets.QMenu('Select color', objectName='brush')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        menu.addActions(self.action('brush').actions())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Special type', objectName='special')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_star_black'))
        menu.addAction(self.action('special_top'))
        menu.addAction(self.action('special_bottom'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Select color', objectName='refactor_brush')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        menu.addActions(self.action('refactor_brush').actions())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Refactor', objectName='refactor')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_shapes_black'))
        menu.addAction(self.action('refactor_name'))
        menu.addMenu(self.menu('refactor_brush'))
        self.addMenu(menu)

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Compose', objectName='compose')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        menu.addAction(self.action('property_domain'))
        menu.addAction(self.action('property_range'))
        self.addMenu(menu)

        #############################################
        # VALUE-DOMAIN SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Select type', objectName='datatype')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
        menu.addActions(self.action('datatype').actions())
        self.addMenu(menu)

        #############################################
        # FACET SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Select facet', objectName='facet')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
        menu.addActions(self.action('facet').actions())
        self.addMenu(menu)

        #############################################
        # PROPERTY DOMAIN / RANGE SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Select restriction', objectName='property_restriction')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_settings_ethernet'))
        menu.addActions(self.action('restriction').actions())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Switch to', objectName='switch_restriction')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
        menu.addActions(self.action('switch_restriction').actions())
        self.addMenu(menu)

        #############################################
        # INDIVIDUAL SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Switch to', objectName='switch_individual')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
        menu.addActions(self.action('switch_individual').actions())
        self.addMenu(menu)

        #############################################
        # OPERATORS SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Switch to', objectName='switch_operator')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
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

    def initPlugins(self):
        """
        Load and initialize application plugins.
        """
        LOGGER.header('Loading plugins')

        #############################################
        # SEARCH PLUGINS
        #################################

        info = []
        for path in ('@plugins/', '@home/plugins/'):
            info.extend(self.pmanager.lookup(expandPath(path)))

        #############################################
        # INITIALIZE PLUGINS
        #################################

        self.addPlugins(self.pmanager.init(info))

    def initProfiles(self):
        """
        Initialize the ontology profiles.
        """
        self.addProfile(OWL2Profile)
        self.addProfile(OWL2QLProfile)
        self.addProfile(OWL2RLProfile)

    def initSignals(self):
        """
        Connect session specific signals to their slots.
        """
        connect(self.undostack.cleanChanged, self.doUpdateState)
        connect(self.sgnDiagramFocus, self.doFocusDiagram)
        connect(self.sgnDiagramLoad, self.doLoadDiagram)
        connect(self.sgnReady, self.doUpdateState)
        connect(self.sgnProjectSave, self.doSave)
        connect(self.sgnUpdateState, self.doUpdateState)

    def initState(self):
        """
        Configure application state by reading the preferences file.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        self.restoreGeometry(settings.value('session/geometry', QtCore.QByteArray(), QtCore.QByteArray))
        self.restoreState(settings.value('session/state', QtCore.QByteArray(), QtCore.QByteArray))
        self.action('toggle_grid').setChecked(settings.value('diagram/grid', False, bool))

    def initStatusBar(self):
        """
        Configure the status bar.
        """
        statusbar = QtWidgets.QStatusBar(self)
        statusbar.setSizeGripEnabled(False)
        self.setStatusBar(statusbar)

    def initToolBars(self):
        """
        Configure application built-in toolbars.
        """
        toolbar = self.widget('document_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addAction(self.action('new_diagram'))
        toolbar.addAction(self.action('open'))
        toolbar.addAction(self.action('save'))
        toolbar.addAction(self.action('print'))

        toolbar = self.widget('editor_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addAction(self.action('undo'))
        toolbar.addAction(self.action('redo'))
        toolbar.addSeparator()
        toolbar.addAction(self.action('cut'))
        toolbar.addAction(self.action('copy'))
        toolbar.addAction(self.action('paste'))
        toolbar.addAction(self.action('delete'))
        toolbar.addAction(self.action('purge'))
        toolbar.addSeparator()
        toolbar.addAction(self.action('bring_to_front'))
        toolbar.addAction(self.action('send_to_back'))
        toolbar.addSeparator()
        toolbar.addAction(self.action('swap_edge'))
        toolbar.addWidget(self.widget('button_set_brush'))

        toolbar = self.widget('view_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addAction(self.action('toggle_grid'))
        toolbar.addAction(self.action('snap_to_grid'))
        toolbar.addAction(self.action('center_diagram'))

        toolbar = self.widget('graphol_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addWidget(self.widget('profile_switch'))
        toolbar.addAction(self.action('syntax_check'))

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('document_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('editor_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('view_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('graphol_toolbar'))

    def initWidgets(self):
        """
        Configure application built-in widgets.
        """
        button = QtWidgets.QToolButton(objectName='button_set_brush')
        button.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        button.setMenu(self.menu('brush'))
        button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        button.setStatusTip('Change the background color of the selected predicate nodes')
        button.setEnabled(False)
        self.addWidget(button)

        combobox = ComboBox(objectName='profile_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.setStatusTip('Change the profile of the active project')
        combobox.addItems(self.profileNames())
        connect(combobox.activated, self.doSetProfile)
        self.addWidget(combobox)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doBringToFront(self):
        """
        Bring the selected item to the top of the diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            commands = []
            diagram.setMode(DiagramMode.Idle)
            for node in diagram.selectedNodes():
                zValue = 0
                for item in [x for x in node.collidingItems() if x.type() is not Item.Label]:
                    if item.zValue() >= zValue:
                        zValue = item.zValue() + 0.2
                if zValue != node.zValue():
                    commands.append(CommandNodeSetDepth(diagram, node, zValue))
            if commands:
                if len(commands) > 1:
                    self.undostack.beginMacro('change the depth of {0} nodes'.format(len(commands)))
                    for command in commands:
                        self.undostack.push(command)
                    self.undostack.endMacro()
                else:
                    self.undostack.push(first(commands))

    @QtCore.pyqtSlot()
    def doCenterDiagram(self):
        """
        Center the active diagram.
        """
        diagram = self.mdi.activeDiagram()
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
                    self.undostack.push(command)
                    self.mdi.activeView().centerOn(0, 0)

    @QtCore.pyqtSlot()
    def doClose(self):
        """
        Close the currently active subwindow.
        """
        self.sgnProjectSave.emit()
        self.close()
        self.sgnClosed.emit()

    @QtCore.pyqtSlot()
    def doComposePropertyExpression(self):
        """
        Compose a property domain using the selected role/attribute node.
        """
        def compose(_diagram, _source, _item):
            """
            Returns a collection of items to be added to the given source node to compose a property expression.
            :type _diagram: Diagram
            :type _source: AbstractNode
            :type _item: Item
            :rtype: set
            """
            restriction = _diagram.factory.create(_item)
            edge = _diagram.factory.create(Item.InputEdge, source=_source, target=restriction)
            size = Diagram.GridSize
            offsets = (
                QtCore.QPointF(snapF(+_source.width() / 2 + 70, size), 0),
                QtCore.QPointF(snapF(-_source.width() / 2 - 70, size), 0),
                QtCore.QPointF(0, snapF(-_source.height() / 2 - 70, size)),
                QtCore.QPointF(0, snapF(+_source.height() / 2 + 70, size)),
                QtCore.QPointF(snapF(+_source.width() / 2 + 70, size), snapF(-_source.height() / 2 - 70, size)),
                QtCore.QPointF(snapF(-_source.width() / 2 - 70, size), snapF(-_source.height() / 2 - 70, size)),
                QtCore.QPointF(snapF(+_source.width() / 2 + 70, size), snapF(+_source.height() / 2 + 70, size)),
                QtCore.QPointF(snapF(-_source.width() / 2 - 70, size), snapF(+_source.height() / 2 + 70, size)),
            )
            pos = None
            num = sys.maxsize
            rad = QtCore.QPointF(restriction.width() / 2, restriction.height() / 2)
            for o in offsets:
                count = len(_diagram.items(QtCore.QRectF(_source.pos() + o - rad, _source.pos() + o + rad)))
                if count < num:
                    num = count
                    pos = _source.pos() + o
            restriction.setPos(pos)
            return {restriction, edge}

        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            supported = {Item.RoleNode, Item.AttributeNode}
            node = first(diagram.selectedNodes(lambda x: x.type() in supported))
            if node:
                action = self.sender()
                item = action.data()
                name = 'compose {0} {1}'.format(node.shortName, item.shortName)
                items = compose(diagram, node, item)
                nodes = {x for x in items if x.isNode()}
                edges = {x for x in items if x.isEdge()}
                self.undostack.push(CommandComposeAxiom(name, diagram, node, nodes, edges))

    @QtCore.pyqtSlot()
    def doCopy(self):
        """
        Make a copy of selected items.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            diagram.pasteX = Clipboard.PasteOffsetX
            diagram.pasteY = Clipboard.PasteOffsetY
            self.clipboard.update(diagram)
            self.sgnUpdateState.emit()

    @QtCore.pyqtSlot()
    def doCut(self):
        """
        Cut selected items from the active diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            diagram.pasteX = 0
            diagram.pasteY = 0
            self.clipboard.update(diagram)
            self.sgnUpdateState.emit()
            items = diagram.selectedItems()
            if items:
                items.extend([x for item in items if item.isNode() for x in item.edges if x not in items])
                self.undostack.push(CommandItemsRemove(diagram, items))

    @QtCore.pyqtSlot()
    def doDelete(self):
        """
        Delete the currently selected items from the active diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            items = diagram.selectedItems()
            if items:
                items.extend([x for item in items if item.isNode() for x in item.edges if x not in items])
                self.undostack.push(CommandItemsRemove(diagram, items))

    @QtCore.pyqtSlot()
    def doExport(self):
        """
        Export the current project.
        """
        if not self.project.isEmpty():
            dialog = QtWidgets.QFileDialog(self)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setDirectory(expandPath('~/'))
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setNameFilters(self.projectExporterNameFilters(exclude={File.Graphol}))
            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.selectFile(self.project.name)
            if dialog.exec_():
                filetype = File.forValue(dialog.selectedNameFilter())
                exporter = self.createProjectExporter(filetype, self.project, self)
                exporter.export(expandPath(first(dialog.selectedFiles())))

    @QtCore.pyqtSlot('QGraphicsScene')
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
        self.sgnDiagramFocused.emit(diagram)

    @QtCore.pyqtSlot('QGraphicsItem')
    def doFocusItem(self, item):
        """
        Focus an item in its diagram.
        :type item: AbstractItem
        """
        self.sgnDiagramFocus.emit(item.diagram)
        self.mdi.activeDiagram().clearSelection()
        self.mdi.activeView().centerOn(item)
        item.setSelected(True)

    @QtCore.pyqtSlot()
    def doImport(self):
        """
        Import a document from a different file format.
        """
        dialog = QtWidgets.QFileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath('~'))
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        dialog.setNameFilters(self.diagramLoaderNameFilters(exclude={File.Graphol}))
        if dialog.exec_():
            filetype = File.forValue(dialog.selectedNameFilter())
            selected = [x for x in dialog.selectedFiles() if File.forPath(x) is filetype and fexists(x)]
            if selected:
                try:
                    with BusyProgressDialog(parent=self) as progress:
                        for path in selected:
                            progress.setWindowTitle('Importing {0}...'.format(os.path.basename(path)))
                            loader = self.createDiagramLoader(filetype, path, self.project, self)
                            loader.load()
                            self.sgnDiagramFocus.emit(loader.diagram)
                except Exception as e:
                    msgbox = QtWidgets.QMessageBox(self)
                    msgbox.setDetailedText(format_exception(e))
                    msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
                    msgbox.setText('Eddy could not import all the selected files!')
                    msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                    msgbox.setWindowTitle('Import failed!')
                    msgbox.exec_()
                finally:
                    self.sgnProjectSave.emit()

    @QtCore.pyqtSlot()
    def doInvertRole(self):
        """
        Swap the direction of all the occurrences of the selected role.
        """

        def invert(item):
            """
            Invert the type of a node.
            :type item: Item
            :rtype: Item
            """
            if item is Item.DomainRestrictionNode:
                return Item.RangeRestrictionNode
            return Item.DomainRestrictionNode

        f0 = lambda x: x.type() is Item.RoleNode
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
        f3 = lambda x: x.type() is Item.RoleInverseNode

        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(x for x in diagram.selectedNodes(filter_on_nodes=f0))
            if node:
                swappable = set()
                collection = dict()
                predicates = self.project.predicates(node.type(), node.text())
                for predicate in predicates:
                    swappable = set.union(swappable, predicate.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                    for inv in predicate.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f3):
                        swappable = set.union(swappable, inv.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                for xnode in swappable:
                    ynode = xnode.diagram.factory.create(invert(xnode.type()))
                    ynode.setPos(xnode.pos())
                    ynode.setText(xnode.text())
                    ynode.setTextPos(xnode.textPos())
                    collection[xnode] = ynode
                if collection:
                    self.undostack.beginMacro("swap '{0}' domain & range".format(node.text()))
                    for xnode, ynode in collection.items():
                        self.undostack.push(CommandNodeSwitchTo(xnode.diagram, xnode, ynode))
                    self.undostack.endMacro()

    @QtCore.pyqtSlot(str)
    def doLoadDiagram(self, path):
        """
        Load the given diagram and add it to the project.
        :type path: str
        """
        if fexists(path):

            if File.forPath(path) is File.Graphol:

                try:
                    loader = self.createDiagramLoader(File.Graphol, path, self.project, self)
                    loader.load()
                except Exception as e:
                    msgbox = QtWidgets.QMessageBox(self)
                    msgbox.setDetailedText(format_exception(e))
                    msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
                    msgbox.setText('Eddy could not load the specified diagram: {0}!'.format(path))
                    msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                    msgbox.setWindowTitle('Diagram load failed!')
                    msgbox.exec_()

    @QtCore.pyqtSlot()
    def doNewDiagram(self):
        """
        Create a new diagram.
        """
        form = NewDiagramDialog(self.project, self)
        if form.exec_() == NewDiagramDialog.Accepted:
            path = expandPath(form.pathField.value())
            self.sgnDiagramLoad.emit(path)
            self.sgnDiagramFocus.emit(self.project.diagram(path))
            self.sgnProjectSave.emit()

    @QtCore.pyqtSlot()
    def doOpen(self):
        """
        Open a document.
        """
        dialog = QtWidgets.QFileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath('~'))
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        dialog.setNameFilters([File.Graphol.value])
        if dialog.exec_():
            self.openFile(first(dialog.selectedFiles()))

    @QtCore.pyqtSlot()
    def doOpenDialog(self):
        """
        Open a dialog window by initializing it using the class stored in action data.
        """
        action = self.sender()
        dialog = action.data()
        window = dialog(self)
        window.exec_()

    @QtCore.pyqtSlot()
    def doOpenURL(self):
        """
        Open a URL using the operating system default browser.
        """
        action = self.sender()
        weburl = action.data()
        if weburl:
            webbrowser.open(weburl)

    @QtCore.pyqtSlot()
    def doOpenDiagramProperties(self):
        """
        Executed when scene properties needs to be displayed.
        """
        diagram = self.sender().data() or self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            properties = self.pf.create(diagram)
            properties.exec_()

    @QtCore.pyqtSlot()
    def doOpenNodeProperties(self):
        """
        Executed when node properties needs to be displayed.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(diagram.selectedNodes())
            if node:
                properties = self.pf.create(diagram, node)
                properties.exec_()

    @QtCore.pyqtSlot()
    def doPaste(self):
        """
        Paste previously copied items.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            if not self.clipboard.empty():
                self.clipboard.paste(diagram, diagram.mp_Pos)

    @QtCore.pyqtSlot()
    def doPrint(self):
        """
        Print the active diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            exporter = PrinterDiagramExporter(diagram, self)
            exporter.export()

    @QtCore.pyqtSlot()
    def doPurge(self):
        """
        Delete the currently selected items by also removing no more necessary elements.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            items = set(diagram.selectedItems())
            purge = set()
            for item in items:
                if item.isNode():
                    for node in item.definition():
                        if item.isConstructor():
                            if node not in items:
                                # Here we examine a node which is included in the definition of a node
                                # in the original selection, but it's not included in the selection itself.
                                # If the node contribute only to the definition on this node and has no
                                # relation with any other node in the diagram, which is not in the original
                                # item selection, we will remove it.
                                if node.adjacentNodes(filter_on_nodes=lambda x: x not in items):
                                    continue
                        purge.add(node)
            collection = list(items|purge)
            if collection:
                collection.extend([x for item in collection if item.isNode() for x in item.edges if x not in collection])
                self.undostack.push(CommandItemsRemove(diagram, collection))

    @QtCore.pyqtSlot()
    def doQuit(self):
        """
        Quit Eddy.
        """
        self.sgnProjectSave.emit()
        self.sgnQuit.emit()

    @QtCore.pyqtSlot()
    def doRefactorBrush(self):
        """
        Change the node brush for all the predicate nodes matching the selected predicate.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                action = self.sender()
                color = action.data()
                nodes = self.project.predicates(node.type(), node.text())
                self.undostack.push(CommandNodeSetBrush(diagram, nodes, QtGui.QBrush(QtGui.QColor(color.value))))

    @QtCore.pyqtSlot()
    def doRefactorName(self):
        """
        Rename all the instance of the selected predicate node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                 dialog = RefactorNameForm(node, self)
                 dialog.exec_()

    @QtCore.pyqtSlot()
    def doRelocateLabel(self):
        """
        Reset the selected node label to its default position.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.label is not None
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node and node.label.isMovable():
                undo = node.label.pos()
                redo = node.label.defaultPos()
                self.undostack.push(CommandLabelMove(diagram, node, undo, redo))

    @QtCore.pyqtSlot()
    def doRemoveBreakpoint(self):
        """
        Remove the edge breakpoint specified in the action triggering this slot.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            edge, breakpoint = action.data()
            if 0 <= breakpoint < len(edge.breakpoints):
                self.undostack.push(CommandEdgeBreakpointRemove(diagram, edge, breakpoint))

    @QtCore.pyqtSlot()
    def doRemoveDiagram(self):
        """
        Removes a diagram from the current project.
        """
        action = self.sender()
        diagram = action.data()
        if diagram:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_question_outline_black').pixmap(48))
            msgbox.setInformativeText('<b>NOTE: This action is not reversible!</b>')
            msgbox.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Remove diagram: {0}?'.format(diagram.name))
            msgbox.setText(textwrap.dedent("""Are you sure you want to remove diagram <b>{0}</b>?
            If you continue, all the predicates that have been defined only in this
            diagram will be lost!""".format(diagram.name)))
            msgbox.exec_()
            if msgbox.result() == QtWidgets.QMessageBox.Yes:
                subwindow = self.mdi.subWindowForDiagram(diagram)
                if subwindow:
                    subwindow.close()
                self.project.removeDiagram(diagram)
                fremove(diagram.path)
                self.sgnProjectSave.emit()

    @QtCore.pyqtSlot()
    def doRenameDiagram(self):
        """
        Renames a diagram.
        """
        action = self.sender()
        diagram = action.data()
        if diagram:
            form = RenameDiagramDialog(self.project, diagram, self)
            if form.exec_() == RenameDiagramDialog.Accepted:
                self.sgnProjectSave.emit()
                self.sgnDiagramRenamed.emit(diagram)

    @QtCore.pyqtSlot()
    def doSave(self):
        """
        Save the current project.
        """
        try:
            exporter = self.createProjectExporter(File.Graphol, self.project, self)
            exporter.export()
        except Exception as e:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setDetailedText(format_exception(e))
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
            msgbox.setText('Eddy could not save the current project!')
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Save failed!')
            msgbox.exec_()
        else:
            self.undostack.setClean()
            self.sgnProjectSaved.emit()

    @QtCore.pyqtSlot()
    def doSaveAs(self):
        """
        Creates a copy of the currently open diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            dialog = QtWidgets.QFileDialog(self)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setDirectory(expandPath('~/'))
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setNameFilters(self.diagramExporterNameFilters())
            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.selectFile(rstrip(diagram.name, File.Graphol.extension))
            if dialog.exec_():
                filetype = File.forValue(dialog.selectedNameFilter())
                exporter = self.createDiagramExporter(filetype, diagram, self)
                exporter.export(expandPath(first(dialog.selectedFiles())))

    @QtCore.pyqtSlot()
    def doSelectAll(self):
        """
        Select all the items in the active diagrsm.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            path = QtGui.QPainterPath()
            path.addRect(diagram.sceneRect())
            diagram.setSelectionArea(path)
            diagram.setMode(DiagramMode.Idle)

    @QtCore.pyqtSlot()
    def doSendToBack(self):
        """
        Send the selected item to the back of the diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            commands = []
            diagram.setMode(DiagramMode.Idle)
            for node in diagram.selectedNodes():
                zValue = 0
                for item in [x for x in node.collidingItems() if x.type() is not Item.Label]:
                    if item.zValue() <= zValue:
                        zValue = item.zValue() - 0.2
                if zValue != node.zValue():
                    commands.append(CommandNodeSetDepth(diagram, node, zValue))
            if commands:
                if len(commands) > 1:
                    self.undostack.beginMacro('change the depth of {0} nodes'.format(len(commands)))
                    for command in commands:
                        self.undostack.push(command)
                    self.undostack.endMacro()
                else:
                    self.undostack.push(first(commands))
            
    @QtCore.pyqtSlot()
    def doSetNodeBrush(self):
        """
        Set the brush of selected nodes.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            color = action.data()
            brush = QtGui.QBrush(QtGui.QColor(color.value))
            supported = {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}
            fn = lambda x: x.type() in supported and x.brush() != brush
            selected = diagram.selectedNodes(filter_on_nodes=fn)
            if selected:
                self.undostack.push(CommandNodeSetBrush(diagram, selected, brush))

    @QtCore.pyqtSlot()
    def doSetPropertyRestriction(self):
        """
        Set a property domain / range restriction.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                data = None
                action = self.sender()
                restriction = action.data()
                if restriction is not Restriction.Cardinality:
                    data = restriction.toString()
                else:
                    form = CardinalityRestrictionForm(self)
                    if form.exec_() == CardinalityRestrictionForm.Accepted:
                        data = restriction.toString(form.min(), form.max())
                if data and node.text() != data:
                    name = 'change {0} to {1}'.format(node.shortName, data)
                    self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.pyqtSlot()
    def doSetIndividualAs(self):
        """
        Set an invididual node either to Individual or Value.
        Will bring up the Value Form if needed.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() is Item.IndividualNode
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                action = self.sender()
                if action.data() is Identity.Individual:
                    if node.identity() is Identity.Value:
                        data = node.label.template
                        name = 'change {0} to {1}'.format(node.text(), data)
                        self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))
                elif action.data() is Identity.Value:
                    form = ValueForm(node, self)
                    form.exec_()

    @QtCore.pyqtSlot()
    def doSetNodeSpecial(self):
        """
        Set the special type of the selected node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            fn = lambda x: x.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                special = action.data()
                data = special.value
                if node.text() != data:
                    name = 'change {0} to {1}'.format(node.shortName, data)
                    self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.pyqtSlot()
    def doSetDatatype(self):
        """
        Set the datatype of the selected value-domain node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() is Item.ValueDomainNode
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                action = self.sender()
                datatype = action.data()
                data = datatype.value
                if node.text() != data:
                    name = 'change {0} to {1}'.format(node.shortName, data)
                    self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.pyqtSlot()
    def doSetFacet(self):
        """
        Set the facet of a Facet node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() is Item.FacetNode
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                action = self.sender()
                facet = action.data()
                if facet != node.facet:
                    data = node.compose(facet, node.value)
                    name = 'change {0} to {1}'.format(node.facet.value, facet.value)
                    self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.pyqtSlot()
    def doSetProfile(self):
        """
        Set the currently used project profile.
        """
        widget = self.widget('profile_switch')
        profile = widget.currentText()
        if self.project.profile.name() != profile:
            self.undostack.push(CommandProjectSetProfile(self.project, self.project.profile.name(), profile))
        widget.clearFocus()

    @QtCore.pyqtSlot()
    def doSnapTopGrid(self):
        """
        Snap all the element in the active diagram to the grid.
        """
        diagram = self.mdi.activeDiagram()
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
                self.undostack.push(CommandSnapItemsToGrid(diagram, data))

    @QtCore.pyqtSlot()
    def doSwapEdge(self):
        """
        Swap the selected edges by inverting source/target points.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fe = lambda x: x.isSwapAllowed()
            selected = diagram.selectedEdges(filter_on_edges=fe)
            if selected:
                self.undostack.push(CommandEdgeSwap(diagram, selected))

    @QtCore.pyqtSlot()
    def doSwitchOperatorNode(self):
        """
        Switch the selected operator node to a different type.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: Item.UnionNode <= x.type() <= Item.DisjointUnionNode
            node = first([x for x in diagram.selectedNodes(filter_on_nodes=fn)])
            if node:
                action = self.sender()
                if node.type() is not action.data():
                    xnode = diagram.factory.create(action.data())
                    xnode.setPos(node.pos())
                    self.undostack.push(CommandNodeSwitchTo(diagram, node, xnode))

    @QtCore.pyqtSlot()
    def doSwitchRestrictionNode(self):
        """
        Switch the selected restriction node to a different type.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
            node = first([x for x in diagram.selectedNodes(filter_on_nodes=fn)])
            if node:
                action = self.sender()
                if node.type() is not action.data():
                    xnode = diagram.factory.create(action.data())
                    xnode.setPos(node.pos())
                    xnode.setText(node.text())
                    xnode.setTextPos(node.textPos())
                    self.undostack.push(CommandNodeSwitchTo(diagram, node, xnode))

    @QtCore.pyqtSlot()
    def doSyntaxCheck(self):
        """
        Perform syntax checking on the active diagram.
        """
        dialog = SyntaxValidationDialog(self.project, self)
        dialog.exec_()

    @QtCore.pyqtSlot()
    def doToggleGrid(self):
        """
        Toggle snap to grid setting.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue('diagram/grid', self.action('toggle_grid').isChecked())
        settings.sync()
        for subwindow in self.mdi.subWindowList():
            viewport = subwindow.view.viewport()
            viewport.update()

    @QtCore.pyqtSlot()
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
        isUndoStackClean = self.undostack.isClean()
        isEdgeSwapEnabled = False

        if self.mdi.subWindowList():
            diagram = self.mdi.activeDiagram()
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
                        isEdgeSwapEnabled = edge.isSwapAllowed()
                        if isEdgeSwapEnabled:
                            break

        self.action('bring_to_front').setEnabled(isNodeSelected)
        self.action('center_diagram').setEnabled(isDiagramActive)
        self.action('cut').setEnabled(isNodeSelected)
        self.action('copy').setEnabled(isNodeSelected)
        self.action('delete').setEnabled(isNodeSelected or isEdgeSelected)
        self.action('purge').setEnabled(isNodeSelected)
        self.action('export').setEnabled(not isProjectEmpty)
        self.action('paste').setEnabled(not isClipboardEmpty)
        self.action('save').setEnabled(not isUndoStackClean)
        self.action('save_as').setEnabled(isDiagramActive)
        self.action('select_all').setEnabled(isDiagramActive)
        self.action('send_to_back').setEnabled(isNodeSelected)
        self.action('snap_to_grid').setEnabled(isDiagramActive)
        self.action('syntax_check').setEnabled(not isProjectEmpty)
        self.action('swap_edge').setEnabled(isEdgeSelected and isEdgeSwapEnabled)
        self.action('toggle_grid').setEnabled(isDiagramActive)
        self.widget('button_set_brush').setEnabled(isPredicateSelected)
        self.widget('profile_switch').setCurrentText(self.project.profile.name())

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
        if not self.undostack.isClean():
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_question_outline_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Save changes?')
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Cancel|QtWidgets.QMessageBox.No|QtWidgets.QMessageBox.Yes)
            msgbox.setText('Your project contains unsaved changes. Do you want to save?')
            msgbox.exec_()
            if msgbox.result() == QtWidgets.QMessageBox.Cancel:
                close = False
            elif msgbox.result() == QtWidgets.QMessageBox.No:
                save = False
            elif msgbox.result() == QtWidgets.QMessageBox.Yes:
                save = True

        if not close:
            closeEvent.ignore()
        else:
            if save:
                # SAVE THE CURRENT PROJECT IF NEEDED
                self.sgnProjectSave.emit()
            # DISPOSE ALL THE PLUGINS
            for plugin in self.plugins():
                self.pmanager.dispose(plugin)
            self.pmanager.clear()
            # SHUTDOWN THE ACTIVE SESSION
            self.sgnClosed.emit()
            closeEvent.accept()

            LOGGER.header('Session shutdown completed: %s v%s', APPNAME, VERSION)

    def dragEnterEvent(self, dragEvent):
        """
        Executed when a drag is in progress and the mouse enter this widget.
        :type dragEvent: QDragEnterEvent
        """
        if dragEvent.mimeData().hasUrls():
            self.setCursor(QtGui.QCursor(QtCore.Qt.DragCopyCursor))
            dragEvent.setDropAction(QtCore.Qt.CopyAction)
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
            dropEvent.setDropAction(QtCore.Qt.CopyAction)
            for url in dropEvent.mimeData().urls():
                path = url.path()
                if _WIN32:
                    # On Windows the absolute path returned for each URL has a
                    # leading slash: this obviously is not correct on windows
                    # platform when absolute url have the form C:\\Programs\\... (QtCore.Qt bug?)
                    path = path.lstrip('/').lstrip('\\')
                if fexists(path) and File.forPath(path) is File.Graphol:
                    self.openFile(path)
            dropEvent.accept()
        else:
            dropEvent.ignore()

    def keyPressEvent(self, keyEvent):
        """
        Executed when a keyboard button is pressed
        :type keyEvent: QKeyEvent
        """
        if _MACOS:
            if keyEvent.key() == QtCore.Qt.Key_Backspace:
                action = self.action('delete')
                action.trigger()
        super(Session, self).keyPressEvent(keyEvent)

    def keyReleaseEvent(self, keyEvent):
        """
        Executed when a keyboard button is released.
        :type keyEvent: QKeyEvent
        """
        if keyEvent.key() == QtCore.Qt.Key_Control:
            diagram = self.mdi.activeDiagram()
            if diagram and not diagram.isEdgeAddInProgress():
                diagram.setMode(DiagramMode.Idle)
        super(Session, self).keyReleaseEvent(keyEvent)

    def showEvent(self, showEvent):
        """
        Executed when the window is shown.
        :type showEvent: QShowEvent
        """
        self.setWindowState((self.windowState() & ~QtCore.Qt.WindowMinimized) | QtCore.Qt.WindowActive)
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

    def openFile(self, path):
        """
        Open a graphol document adding it to the project and to the MDI area.
        :type path: str
        """
        if not self.project.diagram(expandPath(path)):

            if not fexists(path):
                raise IOError('file not found: {0}'.format(path))

            if not isSubPath(self.project.path, path):
                name = rstrip(os.path.basename(path), File.Graphol.extension)
                dest = uniquePath(self.project.path, name, File.Graphol.extension)
                path = fcopy(path, dest)

            self.sgnDiagramLoad.emit(path)
            self.sgnDiagramFocus.emit(self.project.diagram(path))
            self.sgnProjectSave.emit()

    def setWindowTitle(self, project, diagram=None):
        """
        Set the main window title.
        :type project: Project
        :type diagram: Diagram
        """
        title = '{0} - [{1}]'.format(project.name, shortPath(project.path))
        if diagram:
            title = '{0} - {1}'.format(diagram.name, title)
        super(Session, self).setWindowTitle(title)