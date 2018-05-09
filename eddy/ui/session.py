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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import os
import sys
import textwrap
from collections import OrderedDict

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy import APPNAME, DIAG_HOME, GRAPHOL_HOME
from eddy import ORGANIZATION, VERSION, WORKSPACE
from eddy.core.clipboard import Clipboard
from eddy.core.commands.common import CommandComposeAxiom
from eddy.core.commands.common import CommandItemsRemove
from eddy.core.commands.common import CommandItemsTranslate
from eddy.core.commands.common import CommandSnapItemsToGrid
from eddy.core.commands.diagram import CommandDiagramAdd
from eddy.core.commands.diagram import CommandDiagramRemove
from eddy.core.commands.diagram import CommandDiagramRename
from eddy.core.commands.edges import CommandEdgeBreakpointRemove
from eddy.core.commands.edges import CommandEdgeSwap
from eddy.core.commands.edges import CommandSwitchSameDifferentEdge
from eddy.core.commands.labels import CommandLabelMove
from eddy.core.commands.labels import CommandLabelChange
from eddy.core.commands.labels import CommandLabelMove
from eddy.core.commands.nodes import CommandNodeSetBrush
from eddy.core.commands.nodes import CommandNodeSetDepth
from eddy.core.commands.nodes import CommandNodeSwitchTo
from eddy.core.commands.nodes_2 import CommandNodeSetRemainingCharacters
from eddy.core.commands.nodes_2 import CommandProjetSetIRIPrefixesNodesDict, CommandProjetSetIRIofCutNodes
from eddy.core.commands.project import CommandProjectSetProfile, CommandProjectDisconnectSpecificSignals, CommandProjectConnectSpecificSignals
from eddy.core.common import HasActionSystem
from eddy.core.common import HasDiagramExportSystem
from eddy.core.common import HasDiagramLoadSystem
from eddy.core.common import HasMenuSystem
from eddy.core.common import HasNotificationSystem
from eddy.core.common import HasOntologyExportSystem
from eddy.core.common import HasOntologyLoadSystem
from eddy.core.common import HasPluginSystem
from eddy.core.common import HasProfileSystem
from eddy.core.common import HasProjectExportSystem
from eddy.core.common import HasProjectLoadSystem
from eddy.core.common import HasReasoningSystem
from eddy.core.common import HasThreadingSystem
from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.graphol import Identity, Item
from eddy.core.datatypes.graphol import Restriction, Special
from eddy.core.datatypes.misc import Color, DiagramMode
from eddy.core.datatypes.owl import Datatype, Facet, OWLProfile
from eddy.core.datatypes.qt import BrushIcon, Font
from eddy.core.datatypes.system import Channel, File
from eddy.core.diagram import Diagram
from eddy.core.exporters.graphml import GraphMLDiagramExporter
from eddy.core.exporters.graphol import GrapholProjectExporter
from eddy.core.exporters.graphreferences import GraphReferences
from eddy.core.exporters.image import ImageExporter
from eddy.core.exporters.owl2 import OWLOntologyExporter
from eddy.core.exporters.pdf import PdfDiagramExporter
from eddy.core.exporters.printer import PrinterDiagramExporter
from eddy.core.factory import MenuFactory, PropertyFactory, DescriptionFactory
from eddy.core.functions.fsystem import fexists
from eddy.core.functions.misc import first, format_exception
from eddy.core.functions.misc import snap, snapF
from eddy.core.functions.path import expandPath
from eddy.core.functions.path import shortPath
from eddy.core.functions.signals import connect
from eddy.core.items.common import AbstractItem
from eddy.core.loaders.graphml import GraphMLOntologyLoader
from eddy.core.loaders.graphol import GrapholOntologyLoader_v2
from eddy.core.loaders.graphol import GrapholProjectLoader_v2
from eddy.core.output import getLogger
from eddy.core.plugin import PluginManager
from eddy.core.profiles.owl2 import OWL2Profile
from eddy.core.profiles.owl2ql import OWL2QLProfile
from eddy.core.profiles.owl2rl import OWL2RLProfile
from eddy.core.reasoner import ReasonerManager
from eddy.core.update import UpdateCheckWorker
from eddy.ui.DiagramsSelectionDialog import DiagramsSelectionDialog
from eddy.ui.about import AboutDialog
from eddy.ui.fields import ComboBox
from eddy.ui.forms import CardinalityRestrictionForm
from eddy.ui.forms import NewDiagramForm
from eddy.ui.forms import RefactorNameForm
from eddy.ui.forms import RenameDiagramForm
from eddy.ui.forms import ValueForm
from eddy.ui.log import LogDialog
from eddy.ui.mdi import MdiArea
from eddy.ui.mdi import MdiSubWindow
from eddy.ui.ontology_consistency_check import OntologyConsistencyCheckDialog
from eddy.ui.plugin import PluginInstallDialog
from eddy.ui.preferences import PreferencesDialog
from eddy.ui.prefix_explorer import OntologyExplorerDialog
from eddy.ui.progress import BusyProgressDialog
from eddy.ui.syntax import SyntaxValidationDialog
from eddy.ui.view import DiagramView

_LINUX = sys.platform.startswith('linux')
_MACOS = sys.platform.startswith('darwin')
_WIN32 = sys.platform.startswith('win32')

LOGGER = getLogger()

class Session(HasReasoningSystem, HasActionSystem, HasMenuSystem, HasPluginSystem, HasWidgetSystem,
              HasDiagramExportSystem, HasOntologyExportSystem, HasProjectExportSystem,
              HasDiagramLoadSystem, HasOntologyLoadSystem, HasProjectLoadSystem,
              HasProfileSystem, HasThreadingSystem, HasNotificationSystem, QtWidgets.QMainWindow):
    """
    Extends QtWidgets.QMainWindow and implements Eddy main working session.
    Additionally to built-in signals, this class emits:
    * sgnClosed: whenever the current session is closed.
    * sgnFocusDiagram: whenever a diagram is to be focused.
    * sgnFocusItem: whenever an item is to be focused.
    * sgnPluginDisposed: to notify that a plugin has been destroyed.
    * sgnPluginStarted: to notify that a plugin startup sequence has been completed.
    * sgnProjectSaved: to notify that the current project has been saved.
    * sgnQuit: whenever the application is to be terminated.
    * sgnReady: after the session startup sequence completes.
    * sgnSaveProject: whenever the current project is to be saved.
    * sgnUpdateState: to notify that something in the session state changed.
    """
    sgnClosed = QtCore.pyqtSignal()
    sgnCheckForUpdate = QtCore.pyqtSignal()
    sgnDiagramFocused = QtCore.pyqtSignal('QGraphicsScene')
    sgnFocusDiagram = QtCore.pyqtSignal('QGraphicsScene')
    sgnFocusItem = QtCore.pyqtSignal('QGraphicsItem')
    sgnPluginDisposed = QtCore.pyqtSignal(str)
    sgnPluginStarted = QtCore.pyqtSignal(str)
    sgnProjectSaved = QtCore.pyqtSignal()
    sgnQuit = QtCore.pyqtSignal()
    sgnReady = QtCore.pyqtSignal()
    sgnSaveProject = QtCore.pyqtSignal()
    sgnUpdateState = QtCore.pyqtSignal()

    sgnReasonerDisposed = QtCore.pyqtSignal(str)
    sgnReasonerStarted = QtCore.pyqtSignal(str)

    def __init__(self, application, path, **kwargs):
        """
        Initialize the application main working session.
        :type application: QApplication
        :type path: str
        :type kwargs: dict
        """
        super().__init__(**kwargs)

        #############################################
        # INITIALIZE MAIN STUFF
        #################################

        self.app = application
        self.clipboard = Clipboard(self)
        self.undostack = QtWidgets.QUndoStack(self)
        self.mdi = MdiArea(self)
        self.mf = MenuFactory(self)
        self.pf = PropertyFactory(self)
        self.df = DescriptionFactory(self)
        self.pmanager = PluginManager(self)

        self.rmanager = ReasonerManager(self)  # written by ASHWIN RAVISHANKAR

        self.project = None

        #############################################
        # CONFIGURE SESSION
        #################################

        self.initReasoners()  # written by ASHWIN RAVISHANKAR

        self.initPre()
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

        worker = self.createProjectLoader(File.Graphol, path, self)
        worker.run()

        #############################################
        # COMPLETE SESSION SETUP
        #################################

        self.setAcceptDrops(False)
        self.setCentralWidget(self.mdi)
        self.setDockOptions(Session.AnimatedDocks | Session.AllowTabbedDocks)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle(self.project)

        self.sgnReady.emit()

        LOGGER.info('Session startup completed: %s v%s [%s]', APPNAME, VERSION, self.project.name)

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
            QtGui.QIcon(':/icons/24/ic_message_black'), 'System log...',
            self, objectName='system_log', statusTip='Show application system log',
            triggered=self.doOpenDialog)
        action.setData(LogDialog)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_extension_black'), 'Install Plugin...',
            self, objectName='install_plugin', statusTip='Install a plugin',
            triggered=self.doOpenDialog)
        action.setData(PluginInstallDialog)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_system_update'), 'Check for Updates...',
            self, objectName='check_for_updates', statusTip='Checks for available updates.',
            triggered=self.doCheckForUpdate)
        self.addAction(action)

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        collection = settings.value('project/recent', None, str) or []
        collection = collection[:5]
        group = QtWidgets.QActionGroup(self, objectName='recent_projects')
        for i, path in enumerate(collection, start=1):
            action = QtWidgets.QAction('{0}. {1}'.format(i, os.path.basename(path)), group, triggered=self.doOpenRecent)
            action.setData(path)
            group.addAction(action)
        self.addAction(group)

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

        #self.addAction(QtWidgets.QAction(
        #    'Import...', self, objectName='import', triggered=self.doImport,
        #    statusTip='Import a document in the current project'))

        self.addAction(QtWidgets.QAction(
            'Export...', self, objectName='export', triggered=self.doExport,
            statusTip='Export the current project in a different format',
            enabled=False))

        self.addAction(QtWidgets.QAction(
            'Import Ontology', self, objectName='import_ontology', triggered=self.doImport,
            statusTip='Import a document in the current project'))

        self.addAction(QtWidgets.QAction(
            'Export Ontology', self, objectName='export_ontology', triggered=self.doExportOntology,
            statusTip='Export the current project in a different format'))

        self.addAction(QtWidgets.QAction(
            'Export Diagrams', self, objectName='export_diagrams', triggered=self.doExportDiagram,
            statusTip='Export a in a different format'))

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
            statusTip='Run syntax validation according to the selected profile', enabled=False))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/18/ic_treeview_branch_closed'), 'Run consistency check on active ontology',
            self, objectName='ontology_consistency_check', triggered=self.doOntologyConsistencyCheck,
            statusTip='Run Reasoner', enabled=False))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_refresh_black'), 'Reset consistency check',
            self, objectName='decolour_nodes', triggered=self.BackgrounddeColourNodesAndEdges,
            statusTip='(decolour the nodes)', enabled=False))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_settings_ethernet_black'),
            'Open Ontology Manager',
            self, objectName='open_prefix_manager', enabled=True,
            statusTip='Open Ontology Manager', triggered=self.doOpenOntologyExplorer))
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
        # SAME/DIFFERENT SPECIFIC
        #################################

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_transform_black'), 'Switch to different', self,
            objectName='switch_same_to_different', statusTip='Switch same edge to different edge',
            triggered=self.doSwitchSameDifferentEdge))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_transform_black'), 'Switch to same', self,
            objectName='switch_different_to_same', statusTip='Switch different edge to same edge',
            triggered=self.doSwitchSameDifferentEdge))

        #############################################
        # NODE RELATED
        #################################

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_settings_black'), 'Properties...',
            self, objectName='node_properties',
            triggered=self.doOpenNodeProperties))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_node_description'), 'Description',
            self, objectName='node_description',
            triggered=self.doOpenNodeDescription))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'), 'Rename...',
            self, objectName='refactor_name',
            triggered=self.doRefactorName))

        """
        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'), 'Change prefix...',
            self, objectName='refactor_change_prefix',
            triggered=self.doRefactorChangeprefix))
        """

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
            QtGui.QIcon(':/icons/24/ic_square_pair_black'), 'Invert Role', self,
            objectName='invert_role', triggered=self.doInvertRole,
            statusTip='Invert the selected role in all its occurrences'))

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_square_outline_black'), 'Domain',
            self, objectName='property_domain', shortcut='CTRL+D',
            triggered=self.doComposePropertyExpression)
        action.setData((Item.DomainRestrictionNode,))
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_square_black'), 'Range',
            self, objectName='property_range', shortcut='CTRL+R',
            triggered=self.doComposePropertyExpression)
        action.setData((Item.RangeRestrictionNode,))
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_square_half_black'), 'Domain/Range',
            self, objectName='property_domain_range',
            triggered=self.doComposePropertyExpression)
        action.setData((Item.DomainRestrictionNode, Item.RangeRestrictionNode))
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
        self.addDiagramExporter(PdfDiagramExporter)
        self.addDiagramExporter(ImageExporter)
        self.addDiagramExporter(GraphReferences)
        self.addOntologyExporter(OWLOntologyExporter)
        self.addProjectExporter(GrapholProjectExporter)


    def initLoaders(self):
        """
        Initialize diagram and project loaders.
        """
        self.addOntologyLoader(GraphMLOntologyLoader)
        self.addOntologyLoader(GrapholOntologyLoader_v2)
        self.addProjectLoader(GrapholProjectLoader_v2)

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
        #menu.addAction(self.action('import'))
        menu.addAction(self.action('import_ontology'))
        menu.addAction(self.action('export_ontology'))
        #menu.addSeparator()
        #menu.addAction(self.action('export'))
        menu.addSeparator()
        menu.addAction(self.action('export_diagrams'))
        menu.addSeparator()
        for action in self.action('recent_projects').actions():
            menu.addAction(action)
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

        menu = QtWidgets.QMenu('Compose', objectName='compose')
        menu.addAction(self.action('property_domain'))
        menu.addAction(self.action('property_range'))
        menu.addAction(self.action('property_domain_range'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Toolbars', objectName='toolbars')
        menu.addAction(self.widget('document_toolbar').toggleViewAction())
        menu.addAction(self.widget('editor_toolbar').toggleViewAction())
        menu.addAction(self.widget('graphol_toolbar').toggleViewAction())
        menu.addAction(self.widget('view_toolbar').toggleViewAction())

        menu.addAction(self.widget('reasoner_toolbar').toggleViewAction()) # ASHWIN RAVISHANKAR

        self.addMenu(menu)

        menu = QtWidgets.QMenu('\u200CView', objectName='view')
        menu.addAction(self.action('toggle_grid'))
        menu.addSeparator()
        menu.addMenu(self.menu('toolbars'))
        menu.addSeparator()
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Ontology', objectName='ontology')
        menu.addAction(self.action('syntax_check'))
        menu.addAction(self.action('ontology_consistency_check'))
        menu.addSeparator()
        menu.addAction(self.action('open_prefix_manager'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Tools', objectName='tools')
        menu.addAction(self.action('install_plugin'))
        menu.addSeparator()
        menu.addAction(self.action('system_log'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Help', objectName='help')
        menu.addAction(self.action('about'))
        if not _MACOS:
            menu.addSeparator()
        menu.addAction(self.action('check_for_updates'))
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

        #menu = QtWidgets.QMenu('Change Prefix', objectName='Change Prefix')
        #menu.setIcon(QtGui.QIcon(':/icons/24/ic_star_black'))
        #menu.addAction(self.action('special_top'))
        #menu.addAction(self.action('special_bottom'))
        #self.addMenu(menu)

        menu = QtWidgets.QMenu('Select color', objectName='refactor_brush')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        menu.addActions(self.action('refactor_brush').actions())
        self.addMenu(menu)

        #menu = QtWidgets.QMenu('Change prefix', objectName='refactor_change_prefix')
        #menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        #menu.addActions(self.action('refactor_change_prefix').actions())
        #self.addMenu(menu)

        menu = QtWidgets.QMenu('Refactor', objectName='refactor')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_shapes_black'))
        menu.addAction(self.action('refactor_name'))
        #menu.addMenu(self.menu('refactor_change_prefix'))
        menu.addMenu(self.menu('refactor_brush'))
        self.addMenu(menu)

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Compose', objectName='compose_domain_range')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        menu.addAction(self.action('property_domain'))
        menu.addAction(self.action('property_range'))
        menu.addSeparator()
        menu.addAction(self.action('property_domain_range'))
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
        menuBar.addMenu(self.menu('compose'))
        menuBar.addMenu(self.menu('view'))
        menuBar.addMenu(self.menu('ontology'))
        menuBar.addMenu(self.menu('tools'))
        menuBar.addMenu(self.menu('help'))

    def initPre(self):
        """
        Initialize stuff that are shared by actions, menus, widgets etc.
        """
        self.addWidget(QtWidgets.QToolBar('Document', objectName='document_toolbar'))
        self.addWidget(QtWidgets.QToolBar('Editor', objectName='editor_toolbar'))
        self.addWidget(QtWidgets.QToolBar('View', objectName='view_toolbar'))
        self.addWidget(QtWidgets.QToolBar('Graphol', objectName='graphol_toolbar'))
        self.addWidget(QtWidgets.QToolBar('Reasoner', objectName='reasoner_toolbar'))

    def initPlugins(self):
        """
        Load and initialize application plugins.
        """
        skip_list = ['Explanation_explorer','Unsatisfiable_Entity_Explorer','developers_iri','prefix_explorer']
        #skip_list = ['Explanation_explorer', 'Unsatisfiable_Entity_Explorer', 'prefix_explorer']
        self.addPlugins(self.pmanager.init(skip_list=skip_list))

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
        connect(self.sgnCheckForUpdate, self.doCheckForUpdate)
        connect(self.sgnFocusDiagram, self.doFocusDiagram)
        connect(self.sgnFocusItem, self.doFocusItem)
        connect(self.sgnReady, self.doUpdateState)
        connect(self.sgnReady, self.onSessionReady)
        connect(self.sgnSaveProject, self.doSave)
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
        statusbar.addPermanentWidget(self.widget('progress_bar'))
        statusbar.addPermanentWidget(QtWidgets.QWidget())
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

        toolbar = self.widget('reasoner_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addWidget(self.widget('select_reasoner'))
        toolbar.addAction(self.action('ontology_consistency_check'))
        toolbar.addAction(self.action('decolour_nodes'))

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('document_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('editor_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('view_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('graphol_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('reasoner_toolbar'))

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

        reasoner_names = []

        for entry in ReasonerManager.info:

            reasoner_name = entry[0].get('reasoner', 'name')
            reasoner_names.append(reasoner_name)

        combobox_2 = ComboBox(objectName='select_reasoner')
        combobox_2.setEditable(False)
        combobox_2.setFont(Font('Roboto', 12))
        combobox_2.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox_2.setScrollEnabled(False)
        combobox_2.setStatusTip('Select one of any available reasoners')
        combobox_2.addItems(reasoner_names)
        combobox_2.setEnabled(False)
        connect(combobox_2.activated, self.doSelectReasoner)
        self.addWidget(combobox_2)

        progressBar = QtWidgets.QProgressBar(objectName='progress_bar')
        progressBar.setContentsMargins(0, 0, 0, 0)
        progressBar.setFixedSize(222, 14)
        progressBar.setRange(0, 0)
        progressBar.setVisible(False)
        self.addWidget(progressBar)

    def initReasoners(self):

        self.addReasoners(self.rmanager.init())

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
    def doCheckForUpdate(self):
        """
        Execute the update check routine.
        """
        channel = Channel.Beta
        # SHOW PROGRESS BAR
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('Checking for updates...')
        progressBar.setVisible(True)
        # RUN THE UPDATE CHECK WORKER IN A THREAD
        try:
            settings = QtCore.QSettings(ORGANIZATION, APPNAME)
            channel = Channel.valueOf(settings.value('update/channel', channel, str))
        except TypeError:
            pass
        finally:
            worker = UpdateCheckWorker(channel, VERSION)
            connect(worker.sgnNoUpdateAvailable, self.onNoUpdateAvailable)
            connect(worker.sgnNoUpdateDataAvailable, self.onNoUpdateDataAvailable)
            connect(worker.sgnUpdateAvailable, self.onUpdateAvailable)
            self.startThread('updateCheck', worker)

    @QtCore.pyqtSlot()
    def doClose(self):
        """
        Close the currently active subwindow.
        """
        self.close()
        self.sgnClosed.emit()

    @QtCore.pyqtSlot()
    def doComposePropertyExpression(self):
        """
        Compose a property domain using the selected role/attribute node.
        """
        positions = []

        def compose(scene, source, items):
            """
            Returns a collection of items to be added to the given source node to compose a property expression.
            :type scene: Diagram
            :type source: AbstractNode
            :type items: tuple
            :rtype: set
            """
            collection = set()
            for item in items:
                restriction = scene.factory.create(item)
                edge = scene.factory.create(Item.InputEdge, source=source, target=restriction)
                size = Diagram.GridSize
                offsets = (
                    QtCore.QPointF(snapF(+source.width() / 2 + 70, size), 0),
                    QtCore.QPointF(snapF(-source.width() / 2 - 70, size), 0),
                    QtCore.QPointF(0, snapF(-source.height() / 2 - 70, size)),
                    QtCore.QPointF(0, snapF(+source.height() / 2 + 70, size)),
                    QtCore.QPointF(snapF(+source.width() / 2 + 70, size), snapF(-source.height() / 2 - 70, size)),
                    QtCore.QPointF(snapF(-source.width() / 2 - 70, size), snapF(-source.height() / 2 - 70, size)),
                    QtCore.QPointF(snapF(+source.width() / 2 + 70, size), snapF(+source.height() / 2 + 70, size)),
                    QtCore.QPointF(snapF(-source.width() / 2 - 70, size), snapF(+source.height() / 2 + 70, size)),
                )
                pos = source.pos() + offsets[0]
                num = sys.maxsize
                rad = QtCore.QPointF(restriction.width() / 2, restriction.height() / 2)
                for o in offsets:
                    if source.pos() + o not in positions:
                        count = len(scene.items(QtCore.QRectF(source.pos() + o - rad, source.pos() + o + rad)))
                        if count < num:
                            num = count
                            pos = source.pos() + o
                restriction.setPos(pos)
                collection.update({restriction, edge})
                positions.append(pos)
            return collection

        diagram = self.mdi.activeDiagram()
        if diagram:
            commands = []
            action = self.sender()
            elements = action.data()
            diagram.setMode(DiagramMode.Idle)
            supported = {Item.RoleNode, Item.AttributeNode}
            for node in diagram.selectedNodes(lambda x: x.type() in supported):
                name = 'compose {0} restriction(s)'.format(node.shortName)
                addons = compose(diagram, node, elements)
                nodes = {x for x in addons if x.isNode()}
                edges = {x for x in addons if x.isEdge()}
                commands.append(CommandComposeAxiom(name, diagram, node, nodes, edges))
            if commands:
                if len(commands) > 1:
                    self.undostack.beginMacro('compose attribute/role restriction(s)')
                    for command in commands:
                        self.undostack.push(command)
                    self.undostack.endMacro()
                else:
                    self.undostack.push(first(commands))

    def common_commands_for_cut_delete_purge(self,diagram,items):

        Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict,
                                                                             dict())
        Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict,
                                                                             dict())

        Dup_1B = self.project.copy_list(self.project.iri_of_cut_nodes, [])
        Dup_2B = self.project.copy_list(self.project.iri_of_cut_nodes, [])

        iris_to_update = []
        nodes_to_update = []

        for item in items:
            if (('AttributeNode' in str(type(item))) or ('ConceptNode' in str(type(item))) or (
                        'IndividualNode' in str(type(item))) or ('RoleNode' in str(type(item)))):
                iri_of_node = self.project.get_iri_of_node(item)

                iris_to_update.append(iri_of_node)
                nodes_to_update.append(item)

                Dup_1B.append(item)
                Dup_1B.append(iri_of_node)

                Duplicate_dict_1[iri_of_node][1].remove(item)

        commands = []

        commands.append(CommandItemsRemove(diagram, items))
        commands.append(
            CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1, iris_to_update,
                                                 nodes_to_update))
        commands.append(CommandProjetSetIRIofCutNodes(Dup_2B, Dup_1B, self.project))

        self.undostack.beginMacro('>>')
        for command in commands:
            if command:
                self.undostack.push(command)
        self.undostack.endMacro()

    @QtCore.pyqtSlot()
    def doCopy(self):
        """
        Make a copy of selected items.
        """
        self.project.iri_of_cut_nodes[:] = []

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
        self.project.iri_of_cut_nodes[:] = []

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

                self.common_commands_for_cut_delete_purge(diagram, items)


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

                self.common_commands_for_cut_delete_purge(diagram, items)


    #not used
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
            dialog.setNameFilters(
                # self.ontologyExporterNameFilters()                -> .owl
                # self.projectExporterNameFilters(except{File.Graphol})   -> .csv
                sorted(self.ontologyExporterNameFilters() + self.projectExporterNameFilters({File.Graphol})\
                + self.diagramExporterNameFilters({File.Pdf, File.GraphML})
                       ))

            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.selectFile(self.project.name)
            dialog.selectNameFilter(File.Owl.value)
            if dialog.exec_():
                filetype = File.valueOf(dialog.selectedNameFilter())
                try:
                    worker = self.createOntologyExporter(filetype, self.project, self)
                except ValueError:
                    try:
                        worker = self.createProjectExporter(filetype, self.project, self)
                    except ValueError:
                        arbitrary_diagram = list(self.project.diagrams())[0]
                        if arbitrary_diagram:
                            worker = self.createDiagramExporter(filetype, arbitrary_diagram, self)
                        else:
                            LOGGER.critical('no diagram present in the project')
                worker.run(expandPath(first(dialog.selectedFiles())))

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
        self.sgnFocusDiagram.emit(item.diagram)
        self.mdi.activeDiagram().clearSelection()
        self.mdi.activeView().centerOn(item)
        item.setSelected(True)

    @QtCore.pyqtSlot()
    def doImport(self):
        """
        Import an ontology into the currently active Project.
        """
        dialog = QtWidgets.QFileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath('~'))
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        dialog.setNameFilters(self.ontologyLoaderNameFilters())
        if dialog.exec_():
            filetype = File.valueOf(dialog.selectedNameFilter())
            selected = [x for x in dialog.selectedFiles() if File.forPath(x) is filetype and fexists(x)]
            if selected:
                try:
                    with BusyProgressDialog(parent=self) as progress:
                        for path in selected:
                            progress.setWindowTitle('Importing {0}...'.format(os.path.basename(path)))
                            worker = self.createOntologyLoader(filetype, path, self.project, self)
                            worker.run()
                except Exception as e:
                    msgbox = QtWidgets.QMessageBox(self)
                    msgbox.setDetailedText(format_exception(e))
                    msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
                    msgbox.setText('Eddy could not import all the selected files!')
                    msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                    msgbox.setWindowTitle('Import failed!')
                    msgbox.exec_()

    @QtCore.pyqtSlot()
    def doExportDiagram(self):

        #diagram = self.mdi.activeDiagram()
        #if diagram:
        if len(self.project.diagrams()) > 0:

            dialog = QtWidgets.QFileDialog(self)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setDirectory(expandPath('~/'))
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            #dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)

            #dialog.setNameFilters(self.diagramExporterNameFilters({File.Xml}))
            dialog.setNameFilters(self.diagramExporterNameFilters())
            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.selectNameFilter(File.Pdf.value)
            dialog.selectFile(self.project.name)

            if dialog.exec_():
                filetype = File.valueOf(dialog.selectedNameFilter())

                flag = False

                if filetype in {File.Pdf, File.Xml}:
                    selected_diagrams = [list(self.project.diagrams())[0]]
                else:
                    diagrams_selection_dialog = DiagramsSelectionDialog(self.project, self)
                    diagrams_selection_dialog.exec_()
                    selected_diagrams = diagrams_selection_dialog.diagrams_selected

                    flag = True

                file_names = []

                for diag in selected_diagrams:

                    if flag is False:
                        path = expandPath(first(dialog.selectedFiles()))
                    else:
                        short_path = first(dialog.selectedFiles())
                        last_dot_index = short_path.rindex('.')
                        new_path = short_path[0:last_dot_index]+'_'+diag.name+short_path[last_dot_index:len(short_path)]

                        path = expandPath(new_path)

                    worker = self.createDiagramExporter(filetype, diag, self)
                    worker.run(path)

                    file_names.append(path)

                if flag:

                    text_to_display = str(len(file_names))+' files were created with filenames having the following pattern - [diagram_name]_[filename given in the file dialog].\n\n The files are \n'

                    for f in file_names:
                        text_to_display = text_to_display+'     '+f+'\n'

                    dialog_filename_changed = QtWidgets.QMessageBox()
                    dialog_filename_changed.setText(text_to_display)
                    dialog_filename_changed.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    dialog_filename_changed.exec_()

    @QtCore.pyqtSlot()
    def doExportOntology(self):
        """
        Export the current project.
        """
        if not self.project.isEmpty():
            dialog = QtWidgets.QFileDialog(self)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setDirectory(expandPath('~/'))
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setNameFilters(
                # self.ontologyExporterNameFilters()                -> .owl
                # self.projectExporterNameFilters(except{File.Graphol})   -> .csv
                sorted(self.ontologyExporterNameFilters() + self.projectExporterNameFilters({File.Graphol}) \
                       #+ self.diagramExporterNameFilters({File.Pdf, File.GraphML})
                       ))

            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.selectFile(self.project.name)
            dialog.selectNameFilter(File.Owl.value)
            if dialog.exec_():
                filetype = File.valueOf(dialog.selectedNameFilter())
                try:
                    worker = self.createOntologyExporter(filetype, self.project, self)
                except ValueError:
                    try:
                        worker = self.createProjectExporter(filetype, self.project, self)
                    except ValueError:
                        arbitrary_diagram = list(self.project.diagrams())[0]
                        if arbitrary_diagram:
                            worker = self.createDiagramExporter(filetype, arbitrary_diagram, self)
                        else:
                            LOGGER.critical('no diagram present in the project')
                worker.run(expandPath(first(dialog.selectedFiles())))

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
                    self.undostack.beginMacro("swap '{0}' domain and range".format(node.text()))
                    for xnode, ynode in collection.items():
                        self.undostack.push(CommandNodeSwitchTo(xnode.diagram, xnode, ynode))
                    self.undostack.endMacro()

    @QtCore.pyqtSlot()
    def doLookupOccurrence(self):
        """
        Focus the item which is being held by the supplying QAction.
        """
        self.sgnFocusItem.emit(self.sender().data())

    @QtCore.pyqtSlot()
    def refactorsetprefix(self):

        node = self.sender().data()
        to_prefix = self.sender().text()
        if to_prefix == ':':
            to_iri = None
            for iri_itr in self.project.IRI_prefixes_nodes_dict.keys():
                if 'display_in_widget' in self.project.IRI_prefixes_nodes_dict[iri_itr][2]:
                    to_iri = iri_itr
                    break
            if to_iri is None:
                self.statusBar().showMessage(
                    ': prefix does not correspond to any IRI in the widget. please contact developer.')
        else:
            to_iri = self.project.get_iri_for_prefix(to_prefix)
        from_prefix = self.project.get_prefix_of_node(node)
        from_iri = self.project.get_iri_of_node(node)

        #print('from_prefix', from_prefix)
        #print('to_prefix',to_prefix)
        #print('from_iri', from_iri)
        #print('to_iri',to_iri)
        #print('node',node)

        # case 1
        if from_prefix == to_prefix:
            # print('from_prefix == to_prefix')
            return

        Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())
        Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())

        commands = []

        # case 2
        if from_iri == to_iri:

            if to_prefix != ':':

                Duplicate_dict_1[from_iri][0].remove(to_prefix)
                Duplicate_dict_1[from_iri][0].append(to_prefix)

                commands.append(CommandProjectDisconnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))
                commands.append(CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1, [from_iri], None))
                commands.append(CommandProjectConnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))

        # case 3
        else:

            metaDataChanged_ADD_OK_var = set()
            metaDataChanged_REMOVE_OK_var = set()
            metaDataChanged_IGNORE_var = set()

            @QtCore.pyqtSlot(str, str, str)
            def metaDataChanged_REMOVE_OK(iri, node, message):
                # print('metaDataChanged_REMOVE_OK -', iri, ',', node, ',', message)
                metaDataChanged_REMOVE_OK_var.add(True)

            @QtCore.pyqtSlot(str, str, str)
            def metaDataChanged_ADD_OK(iri, node, message):
                # print('metaDataChanged_ADD_OK -', iri, ',', node, ',', message)
                metaDataChanged_ADD_OK_var.add(True)

            @QtCore.pyqtSlot(str, str, str)
            def metaDataChanged_IGNORE(iri, node, message):
                # if node.id is None:
                # print('metaDataChanged_IGNORE >', iri, '-', 'None', '-', message)
                # else:
                # print('metaDataChanged_IGNORE >', iri, '-', node, '-', message)
                metaDataChanged_IGNORE_var.add(True)

            connect(self.project.sgnIRINodeEntryAdded, metaDataChanged_ADD_OK)
            connect(self.project.sgnIRINodeEntryRemoved, metaDataChanged_REMOVE_OK)
            connect(self.project.sgnIRINodeEntryIgnored, metaDataChanged_IGNORE)

            list_of_nodes_to_process = []

            for n in self.project.nodes():
                if (('AttributeNode' in str(type(n))) or ('ConceptNode' in str(type(n))) or (
                            'IndividualNode' in str(type(n))) or ('RoleNode' in str(type(n)))):

                    if (self.project.get_iri_of_node(n) == from_iri) and (n.remaining_characters == node.remaining_characters):
                        list_of_nodes_to_process.append(n)

            for n in list_of_nodes_to_process:

                self.project.removeIRINodeEntry(Duplicate_dict_1, from_iri, n)
                self.project.addIRINodeEntry(Duplicate_dict_1, to_iri, n)

                if ((False not in metaDataChanged_REMOVE_OK_var) and (False not in metaDataChanged_ADD_OK_var)) \
                        and (True not in metaDataChanged_IGNORE_var):
                    pass
                else:
                    LOGGER.warning('redo != undo but transaction was not executed correctly')
                    self.statusBar().showMessage('transaction was not executed correctly for node' + str(n), 15000)
                    return

            # part 2
            if to_prefix != ':':
                Duplicate_dict_1[to_iri][0].remove(to_prefix)
                Duplicate_dict_1[to_iri][0].append(to_prefix)

            commands.append(CommandProjectDisconnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))
            commands.append(CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1,
                                                           [from_iri, to_iri], list_of_nodes_to_process))
            commands.append(CommandProjectConnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))

        if any(commands):
            self.undostack.beginMacro('edit {0} refactorsetprefix'.format(node.name))
            for command in commands:
                if command:
                    self.undostack.push(command)
            self.undostack.endMacro()

    @QtCore.pyqtSlot()
    def setprefix(self):

        node = self.sender().data()
        to_prefix = self.sender().text()
        if to_prefix == ':':
            to_iri = None
            for iri_itr in self.project.IRI_prefixes_nodes_dict.keys():
                if 'display_in_widget' in self.project.IRI_prefixes_nodes_dict[iri_itr][2]:
                    to_iri = iri_itr
                    break
            if to_iri is None:
                self.statusBar().showMessage(': prefix does not correspond to any IRI in the widget. please contact developer.')
        else:
            to_iri = self.project.get_iri_for_prefix(to_prefix)
        from_prefix = self.project.get_prefix_of_node(node)
        from_iri = self.project.get_iri_of_node(node)

        #print('from_prefix', from_prefix)
        #print('to_prefix',to_prefix)
        #print('from_iri', from_iri)
        #print('to_iri',to_iri)
        #print('node',node)

        #case 1
        if from_prefix == to_prefix:
            #print('from_prefix == to_prefix')
            return

        Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())
        Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())

        commands = []

        #case 2
        if from_iri == to_iri:

            if to_prefix != ':':

                Duplicate_dict_1[from_iri][0].remove(to_prefix)
                Duplicate_dict_1[from_iri][0].append(to_prefix)

                commands.append(
                    CommandProjectDisconnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))
                commands.append(CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1,
                                                               [from_iri], None))
                commands.append(CommandProjectConnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))

        #case 3
        else:

            metaDataChanged_ADD_OK_var = set()
            metaDataChanged_REMOVE_OK_var = set()
            metaDataChanged_IGNORE_var = set()

            @QtCore.pyqtSlot(str, str, str)
            def metaDataChanged_REMOVE_OK(iri, node, message):
                #print('metaDataChanged_REMOVE_OK -', iri, ',', node, ',', message)
                metaDataChanged_REMOVE_OK_var.add(True)

            @QtCore.pyqtSlot(str, str, str)
            def metaDataChanged_ADD_OK(iri, node, message):
                #print('metaDataChanged_ADD_OK -', iri, ',', node, ',', message)
                metaDataChanged_ADD_OK_var.add(True)

            @QtCore.pyqtSlot(str, str, str)
            def metaDataChanged_IGNORE(iri, node, message):
                # if node.id is None:
                # print('metaDataChanged_IGNORE >', iri, '-', 'None', '-', message)
                # else:
                #print('metaDataChanged_IGNORE >', iri, '-', node, '-', message)
                metaDataChanged_IGNORE_var.add(True)

            connect(self.project.sgnIRINodeEntryAdded, metaDataChanged_ADD_OK)
            connect(self.project.sgnIRINodeEntryRemoved, metaDataChanged_REMOVE_OK)
            connect(self.project.sgnIRINodeEntryIgnored, metaDataChanged_IGNORE)

            self.project.removeIRINodeEntry(Duplicate_dict_1, from_iri, node)
            self.project.addIRINodeEntry(Duplicate_dict_1, to_iri, node)

            if ((False not in metaDataChanged_REMOVE_OK_var) and (False not in metaDataChanged_ADD_OK_var)) \
                    and(True not in metaDataChanged_IGNORE_var):
                pass
            else:
                LOGGER.warning('redo != undo but transaction was not executed correctly')
                self.statusBar().showMessage('transaction was not executed correctly for node' + str(node),15000)
                return

            #part 2
            if to_prefix != ':':
                Duplicate_dict_1[to_iri][0].remove(to_prefix)
                Duplicate_dict_1[to_iri][0].append(to_prefix)

            commands.append(
                CommandProjectDisconnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))
            commands.append(CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1,
                                                               [from_iri, to_iri], [node]))
            commands.append(CommandProjectConnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))

        if any(commands):
            self.undostack.beginMacro('edit {0} setprefix'.format(node.name))
            for command in commands:
                if command:
                    self.undostack.push(command)
            self.undostack.endMacro()

    @QtCore.pyqtSlot()
    def doNewDiagram(self):
        """
        Create a new diagram.
        """
        form = NewDiagramForm(self.project, self)
        if form.exec_() == NewDiagramForm.Accepted:
            settings = QtCore.QSettings(ORGANIZATION, APPNAME)
            size = settings.value('diagram/size', 5000, int)
            name = form.nameField.value()
            diagram = Diagram.create(name, size, self.project)
            connect(diagram.sgnItemAdded, self.project.doAddItem)
            connect(diagram.sgnItemRemoved, self.project.doRemoveItem)
            connect(diagram.selectionChanged, self.doUpdateState)
            self.undostack.push(CommandDiagramAdd(diagram, self.project))
            self.sgnFocusDiagram.emit(diagram)

    @QtCore.pyqtSlot()
    def doOpen(self):
        """
        Open a project in a new session.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        workspace = settings.value('workspace/home', WORKSPACE, str)
        dialog = QtWidgets.QFileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath(workspace))
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            self.app.sgnCreateSession.emit(expandPath(first(dialog.selectedFiles())))

    @QtCore.pyqtSlot()
    def doOpenRecent(self):
        """
        Open a recent project in a new session.
        """
        action = self.sender()
        path = expandPath(action.data())
        if path != expandPath(self.project.path):
            self.app.sgnCreateSession.emit(expandPath(action.data()))

    @QtCore.pyqtSlot()
    def doOpenDialog(self):
        """
        Open a dialog window by initializing it using the class stored in action data.
        """

        action = self.sender()
        dialog = action.data()
        window = dialog(self)

        window.hide()
        window.setWindowModality(QtCore.Qt.NonModal)
        window.show()
        window.exec_()

    @QtCore.pyqtSlot()
    def doOpenURL(self):
        """
        Open a URL using the operating system default browser.
        """
        action = self.sender()
        weburl = action.data()
        if weburl:
            # noinspection PyTypeChecker,PyCallByClass,PyCallByClass
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(weburl))

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
    def doOpenNodeDescription(self):
        """
        Executed when node description needs to be displayed.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(diagram.selectedNodes())
            if node:
                description = self.df.create(diagram, node)
                description.exec()

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
            worker = PrinterDiagramExporter(diagram, self)
            worker.run()

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
            collection = list(items | purge)
            if collection:
                collection.extend(
                    [x for item in collection if item.isNode() for x in item.edges if x not in collection])

                self.common_commands_for_cut_delete_purge(diagram, collection)

                #self.undostack.push(CommandItemsRemove(diagram, collection))

    @QtCore.pyqtSlot()
    def doQuit(self):
        """
        Quit Eddy.
        """
        self.close()
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
            self.undostack.push(CommandDiagramRemove(diagram, self.project))

    @QtCore.pyqtSlot()
    def doRenameDiagram(self):
        """
        Renames a diagram.
        """
        action = self.sender()
        diagram = action.data()
        if diagram:
            form = RenameDiagramForm(self.project, diagram, self)
            if form.exec_() == RenameDiagramForm.Accepted:
                name = form.nameField.value()
                self.undostack.push(CommandDiagramRename(diagram.name, name, diagram, self.project))

    @QtCore.pyqtSlot()
    def doSave(self):
        """
        Save the current project.
        """
        try:
            worker = self.createProjectExporter(File.Graphol, self.project, self)
            worker.run()
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
            dialog.setNameFilters(self.diagramExporterNameFilters({File.Xml}))
            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.selectFile(diagram.name)
            dialog.selectNameFilter(File.Pdf.value)
            if dialog.exec_():
                filetype = File.valueOf(dialog.selectedNameFilter())
                worker = self.createDiagramExporter(filetype, diagram, self)
                worker.run(expandPath(first(dialog.selectedFiles())))

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
        #print('>>>      Session (doSetIndividualAs)')

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

                        Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries\
                            (self.project.IRI_prefixes_nodes_dict,dict())
                        Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries\
                            (self.project.IRI_prefixes_nodes_dict,dict())

                        old_iri = self.project.get_iri_of_node(node)
                        new_iri = self.project.iri

                        if self.project.prefix is None:
                            new_label = self.project.get_full_IRI(new_iri,None,data)
                            #new_label = str(new_iri+'#'+data)
                        else:
                            new_label = str(self.project.prefix+':'+data)

                        #data = data.replace('\n','')

                        Duplicate_dict_1[old_iri][1].remove(node)
                        Duplicate_dict_1[new_iri][1].add(node)

                        commands = []

                        commands.append(CommandProjectDisconnectSpecificSignals(self.project))
                        commands.append(CommandLabelChange(diagram, node, node.text(), new_label))
                        commands.append(CommandProjetSetIRIPrefixesNodesDict(self.project,Duplicate_dict_2,Duplicate_dict_1, [old_iri, new_iri], [node]))
                        commands.append(CommandNodeSetRemainingCharacters(node.remaining_characters, data, node, self.project))
                        commands.append(CommandLabelChange(diagram, node, node.text(), new_label))
                        commands.append(CommandProjectConnectSpecificSignals(self.project))

                        if any(commands):
                            self.undostack.beginMacro('edit Forms >> accept() {0}'.format(node))
                            for command in commands:
                                if command:
                                    self.undostack.push(command)
                            self.undostack.endMacro()

                elif action.data() is Identity.Value:
                    form = ValueForm(node, self)
                    form.exec_()

        #print('>>>      Session (doSetIndividualAs) END')

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

                    old_iri = self.project.get_iri_of_node(node)
                    new_iri = 'http://www.w3.org/2002/07/owl'

                    if node.type() is Item.ConceptNode:
                        new_rc_lst = ['Nothing','Thing']
                    if node.type() is Item.RoleNode:
                        new_rc_lst = ['BottomObjectProperty','TopObjectProperty']
                    if node.type() is Item.AttributeNode:
                        new_rc_lst = ['BottomDataProperty','TopDataProperty']

                    if data == 'TOP':
                        new_rc = new_rc_lst[1]
                    elif data == 'BOTTOM':
                        new_rc = new_rc_lst[0]

                    #new_rc = new_rc.replace('\n','')

                    Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries \
                        (self.project.IRI_prefixes_nodes_dict, dict())
                    Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries \
                        (self.project.IRI_prefixes_nodes_dict, dict())

                    Duplicate_dict_1[old_iri][1].remove(node)
                    Duplicate_dict_1[new_iri][1].add(node)

                    commands = []

                    commands.append(CommandProjectDisconnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))
                    commands.append(CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1, [old_iri, new_iri], [node]))
                    commands.append(CommandNodeSetRemainingCharacters(node.remaining_characters, new_rc, node, diagram.project))
                    commands.append(CommandProjectConnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False))

                    if any(commands):
                        self.undostack.beginMacro('edit {0} doSetNodeSpecial'.format(node))
                        for command in commands:
                            if command:
                                self.undostack.push(command)
                        self.undostack.endMacro()

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
    def doSwitchSameDifferentEdge(self):
        """
        Switch selected same/different edges to different/same respectively.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fe = lambda e: e.type() in {Item.SameEdge, Item.DifferentEdge}
            selected = diagram.selectedEdges(filter_on_edges=fe)
            if selected:
                self.undostack.push(CommandSwitchSameDifferentEdge(diagram, selected))

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
    def doSelectReasoner(self):
        """
        Set the currently used project profile.
        """
        widget = self.widget('select_reasoner')
        reasoner = widget.currentText()
        widget.clearFocus()

    @QtCore.pyqtSlot()
    def doOntologyConsistencyCheck(self):
        """
        Perform Ontology Consistency checking on the active ontology/diagram.
        """
        dialog = OntologyConsistencyCheckDialog(self.project, self)
        dialog.exec_()

    @QtCore.pyqtSlot()
    def doOpenOntologyExplorer(self):
        """
        Perform Ontology Consistency checking on the active ontology/diagram.
        """
        dialog = OntologyExplorerDialog(self.project, self)
        dialog.exec_()

    @QtCore.pyqtSlot()
    def BackgrounddeColourNodesAndEdges(self,**kwargs):

        call_update_node = kwargs.get('call_updateNode',True)
        call_ClearInconsistentEntitiesAndDiagItemsData = kwargs.get('call_ClearInconsistentEntitiesAndDiagItemsData',True)

        brush = QtGui.QBrush(QtCore.Qt.NoBrush)

        all_nodes = list(self.project.nodes())
        all_edges = list(self.project.edges())

        for node in all_nodes:

            node.selection.setBrush(brush)
            node.setCacheMode(AbstractItem.NoCache)
            node.setCacheMode(AbstractItem.DeviceCoordinateCache)
            node.update(node.boundingRect())

            if call_update_node is True:
                node.updateNode()

        for edge in all_edges:

            edge.selection.setBrush(brush)
            edge.setCacheMode(AbstractItem.NoCache)
            edge.setCacheMode(AbstractItem.DeviceCoordinateCache)
            edge.update(edge.boundingRect())

        if call_ClearInconsistentEntitiesAndDiagItemsData:
            self.ClearInconsistentEntitiesAndDiagItemsData()

        diags = self.project.diagrams()

        for d in diags:
            d.sgnUpdated.emit()

    @QtCore.pyqtSlot()
    def ClearInconsistentEntitiesAndDiagItemsData(self):

        self.project.ontology_OWL = None
        self.project.axioms_to_nodes_edges_mapping = None

        self.project.unsatisfiable_classes = []
        self.project.explanations_for_unsatisfiable_classes = []
        self.project.unsatisfiable_attributes = []
        self.project.explanations_for_unsatisfiable_attributes = []
        self.project.unsatisfiable_roles = []
        self.project.explanations_for_unsatisfiable_roles = []

        self.project.inconsistent_ontology = None
        self.project.explanations_for_inconsistent_ontology = []

        self.project.uc_as_input_for_explanation_explorer = None
        self.project.nodes_of_unsatisfiable_entities = []
        self.project.nodes_or_edges_of_axioms_to_display_in_widget = []
        self.project.nodes_or_edges_of_explanations_to_display_in_widget = []

        self.project.converted_nodes = dict()

    @QtCore.pyqtSlot()
    def doToggleGrid(self):
        """
        Toggle snap to grid setting and viewport display.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue('diagram/grid', self.action('toggle_grid').isChecked())
        settings.sync()
        for subwindow in self.mdi.subWindowList():
            subwindow.view.setGridSize(Diagram.GridSize)
            viewport = subwindow.view.viewport()
            viewport.update()

    @QtCore.pyqtSlot()
    def doUpdateState(self):
        """
        Update built-in actions according to the application state.
        """
        isDomainRangeUsable = False
        isDiagramActive = False
        isClipboardEmpty = True
        isEdgeSelected = False
        isEdgeSwapEnabled = False
        isNodeSelected = False
        isPredicateSelected = False
        isSwitchToSameEnabled = self.project.profile.type() is not OWLProfile.OWL2QL
        isSwitchToDifferentEnabled = True
        isProjectEmpty = self.project.isEmpty()
        isUndoStackClean = self.undostack.isClean()

        if self.mdi.subWindowList():
            diagram = self.mdi.activeDiagram()
            restrictables = {Item.AttributeNode, Item.RoleNode}
            predicates = {Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.IndividualNode}
            if diagram:
                nodes = diagram.selectedNodes()
                edges = diagram.selectedEdges()
                isDiagramActive = True
                isClipboardEmpty = self.clipboard.empty()
                isEdgeSelected = first(edges) is not None
                isNodeSelected = first(nodes) is not None
                isDomainRangeUsable = any([x.type() in restrictables for x in nodes])
                isPredicateSelected = any([x.type() in predicates for x in nodes])
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
        self.action('property_domain').setEnabled(isDomainRangeUsable)
        self.action('property_domain_range').setEnabled(isDomainRangeUsable)
        self.action('property_range').setEnabled(isDomainRangeUsable)
        self.action('save').setEnabled(not isUndoStackClean)
        self.action('save_as').setEnabled(isDiagramActive)
        self.action('select_all').setEnabled(isDiagramActive)
        self.action('send_to_back').setEnabled(isNodeSelected)
        self.action('snap_to_grid').setEnabled(isDiagramActive)
        self.action('syntax_check').setEnabled(not isProjectEmpty)
        self.action('swap_edge').setEnabled(isEdgeSelected and isEdgeSwapEnabled)
        self.action('switch_same_to_different').setEnabled(isSwitchToDifferentEnabled)
        self.action('switch_different_to_same').setEnabled(isSwitchToSameEnabled)
        self.action('toggle_grid').setEnabled(isDiagramActive)
        self.widget('button_set_brush').setEnabled(isPredicateSelected)
        self.widget('profile_switch').setCurrentText(self.project.profile.name())

        if self.mdi.activeDiagram():

            self.widget('select_reasoner').setEnabled(not isProjectEmpty)
            self.action('decolour_nodes').setEnabled(not isProjectEmpty)
            self.action('ontology_consistency_check').setEnabled(not isProjectEmpty)

    @QtCore.pyqtSlot()
    def onNoUpdateAvailable(self):
        """
        Executed when the update worker thread terminates and no software update is available.
        """
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('')
        progressBar.setVisible(False)
        self.addNotification('No update available.')

    @QtCore.pyqtSlot()
    def onNoUpdateDataAvailable(self):
        """
        Executed when the update worker thread terminates abnormally.
        """
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('')
        progressBar.setVisible(False)
        self.addNotification(textwrap.dedent("""
            <b><font color="#7E0B17">ERROR</font></b>: Could not connect to update site:
            unable to get update information.
            """))

    @QtCore.pyqtSlot()
    def onSessionReady(self):
        """
        Executed when the session is initialized.
        """
        ## CONNECT PROJECT SPECIFIC SIGNALS
        connect(self.project.sgnDiagramRemoved, self.mdi.onDiagramRemoved)
        ## CHECK FOR UPDATES ON STARTUP
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        if settings.value('update/check_on_startup', True, bool):
            action = self.action('check_for_updates')
            action.trigger()

    @QtCore.pyqtSlot(str, str)
    def onUpdateAvailable(self, name, url):
        """
        Executed when the update worker thread terminates and a new software update is available.
        :type name: str
        :type url: str
        """
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('')
        progressBar.setVisible(False)
        self.addNotification(textwrap.dedent("""
            A new version of {} is available for download: <a href="{}"><b>{}</b></a>""".format(APPNAME, url, name)))

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
            msgbox.setStandardButtons(
                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
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
            ## SAVE THE CURRENT PROJECT IF NEEDED
            if save:
                self.sgnSaveProject.emit()
            ## DISPOSE ALL THE PLUGINS
            for plugin in self.plugins():
                self.pmanager.dispose(plugin)
            self.pmanager.clear()
            ## DISPOSE ALL THE RUNNING THREADS
            self.stopRunningThreads()
            ## HIDE ALL THE NOTIFICATION POPUPS
            self.hideNotifications()
            ## SHUTDOWN THE ACTIVE SESSION
            self.sgnClosed.emit()
            closeEvent.accept()

            LOGGER.info('Session shutdown completed: %s v%s [%s]', APPNAME, VERSION, self.project.name)

    def keyPressEvent(self, keyEvent):
        """
        Executed when a keyboard button is pressed
        :type keyEvent: QKeyEvent
        """
        if _MACOS:
            if keyEvent.key() == QtCore.Qt.Key_Backspace:
                action = self.action('delete')
                action.trigger()
        super().keyPressEvent(keyEvent)

    def keyReleaseEvent(self, keyEvent):
        """
        Executed when a keyboard button is released.
        :type keyEvent: QKeyEvent
        """
        if keyEvent.key() == QtCore.Qt.Key_Control:
            diagram = self.mdi.activeDiagram()
            if diagram and not diagram.isEdgeAdd():
                diagram.setMode(DiagramMode.Idle)
        super().keyReleaseEvent(keyEvent)

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

    def save(self):
        """
        Save the current session state.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue('session/geometry', self.saveGeometry())
        settings.setValue('session/state', self.saveState())
        settings.sync()

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
