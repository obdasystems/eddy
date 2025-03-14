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
from typing import Optional

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy import (
    APPNAME,
    APP_HOME,
    BUG_TRACKER,
    GRAPHOL_HOME,
    ORGANIZATION_NAME,
    ORGANIZATION_URL,
    PROJECT_HOME,
    VERSION,
    MANUAL_URL
)
from eddy.core.clipboard import Clipboard
from eddy.core.commands.common import (
    CommandComposeAxiom,
    CommandItemsRemove,
    CommandItemsTranslate,
    CommandSnapItemsToGrid,
)
from eddy.core.commands.diagram import (
    CommandDiagramAdd,
    CommandDiagramRemove,
    CommandDiagramRename,
)
from eddy.core.commands.edges import (
    CommandEdgeBreakpointRemove,
    CommandEdgeSwap,
    CommandSwitchSameDifferentEdge,
)
from eddy.core.commands.iri import CommandIRISetMeta
from eddy.core.commands.labels import (
    CommandLabelChange,
    CommandLabelMove,
)
from eddy.core.commands.nodes import (
    CommandNodeSetBrush,
    CommandNodeSetDepth,
    CommandNodeSwitchTo,
)
from eddy.core.commands.project import (
    CommandProjectRename,
    CommandProjectSetProfile,
)
from eddy.core.common import (
    HasActionSystem,
    HasDiagramExportSystem,
    HasDiagramLoadSystem,
    HasMenuSystem,
    HasNotificationSystem,
    HasOntologyExportSystem,
    HasOntologyLoadSystem,
    HasPluginSystem,
    HasProfileSystem,
    HasProjectExportSystem,
    HasProjectLoadSystem,
    HasThreadingSystem,
    HasWidgetSystem,
)
from eddy.core.datatypes.graphol import (
    Item,
    Restriction,
)
from eddy.core.datatypes.misc import (
    Color,
    DiagramMode,
)
from eddy.core.datatypes.owl import (
    Datatype,
    Facet,
    Namespace,
)
from eddy.core.datatypes.qt import BrushIcon
from eddy.core.datatypes.system import (
    Channel,
    File,
    IS_MACOS,
)
from eddy.core.diagram import Diagram
from eddy.core.exporters.graphml import GraphMLDiagramExporter
from eddy.core.exporters.graphol_iri import GrapholIRIProjectExporter
from eddy.core.exporters.graphreferences import GraphReferencesProjectExporter
from eddy.core.exporters.image import (
    BmpDiagramExporter,
    JpegDiagramExporter,
    PngDiagramExporter,
)
from eddy.core.exporters.metadata import (
    AnnotationsOverridingDialog,
    CsvProjectExporter,
    XlsxProjectExporter,
)
from eddy.core.exporters.owl2 import OWLOntologyExporter
from eddy.core.exporters.pdf import PdfProjectExporter
from eddy.core.exporters.printer import PrinterDiagramExporter
from eddy.core.factory import (
    MenuFactory,
    PropertyFactory,
)
from eddy.core.functions.fsystem import fexists
from eddy.core.functions.misc import (
    first,
    format_exception,
    snap,
    snapF,
)
from eddy.core.functions.path import (
    expandPath,
    shortPath,
)
from eddy.core.functions.signals import connect
from eddy.core.items.common import AbstractItem
from eddy.core.items.edges.common.base import AxiomEdge
from eddy.core.items.nodes.common.base import (
    AbstractNode,
    PredicateNodeMixin,
)
from eddy.core.items.nodes.facet import FacetNode
from eddy.core.items.nodes.literal import LiteralNode
from eddy.core.loaders.annotations import CsvLoader, XlsxLoader
from eddy.core.loaders.graphml import GraphMLOntologyLoader
from eddy.core.loaders.graphol_iri import (
    GrapholIRIProjectLoader_v3,
    GrapholOntologyIRILoader_v3,
)
from eddy.core.loaders.owl2 import (
    OwlOntologyImportSetWorker,
    OwlProjectLoader,
)
from eddy.core.network import NetworkManager
from eddy.core.output import getLogger
from eddy.core.owl import (
    IRIRender,
    IRI,
    OWL2Profiles,
    ImportedOntology,
    AnnotationAssertion,
)
from eddy.core.plugin import PluginManager
from eddy.core.profiles.owl2 import OWL2Profile
from eddy.core.profiles.owl2ql import OWL2QLProfile
from eddy.core.profiles.owl2rl import OWL2RLProfile
from eddy.core.project import (
    K_ASYMMETRIC,
    K_FUNCTIONAL,
    K_INVERSE_FUNCTIONAL,
    K_IRREFLEXIVE,
    K_REFLEXIVE,
    K_SYMMETRIC,
    K_TRANSITIVE,
    Project,
)
from eddy.core.regex import RE_CAMEL_SPACE
from eddy.ui.about import AboutDialog
from eddy.ui.annotation import (
    AnnotationAssertionBuilderDialog,
    AnnotationBuilderDialog,
)
from eddy.ui.axioms_by_iri import AxiomsByEntityDialog
from eddy.ui.consistency_check import OntologyConsistencyCheckDialog
from eddy.ui.dialogs import DiagramSelectionDialog
from eddy.ui.dl import OWL2DLProfileValidationDialog
from eddy.ui.explanation import (
    ExplanationDialog,
    EmptyEntityDialog,
)
from eddy.ui.fields import ComboBox
from eddy.ui.file import FileDialog
from eddy.ui.forms import (
    CardinalityRestrictionForm,
    NewDiagramForm,
    RefactorNameForm,
    RenameDiagramForm,
    RenameProjectForm,
)
from eddy.ui.import_ontology import ImportOntologyDialog
from eddy.ui.iri import (
    ConstrainingFacetDialog,
    EdgeAxiomDialog,
    FontDialog,
    IriBuilderDialog,
    IriPropsDialog,
    LiteralDialog,
)
from eddy.ui.label import LabelDialog
from eddy.ui.log import LogDialog
from eddy.ui.mdi import (
    MdiArea,
    MdiSubWindow,
)
from eddy.ui.plugin import PluginInstallDialog
from eddy.ui.preferences import PreferencesDialog
from eddy.ui.progress import BusyProgressDialog
from eddy.ui.syntax import SyntaxValidationDialog
from eddy.ui.view import DiagramView

#############################################
#   GLOBALS
#################################

LOGGER = getLogger()


class Session(
    HasActionSystem,
    HasMenuSystem,
    HasPluginSystem,
    HasWidgetSystem,
    HasDiagramExportSystem,
    HasOntologyExportSystem,
    HasProjectExportSystem,
    HasDiagramLoadSystem,
    HasOntologyLoadSystem,
    HasProjectLoadSystem,
    HasProfileSystem,
    HasThreadingSystem,
    HasNotificationSystem,
    QtWidgets.QMainWindow,
):
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
    * sgnPrefixAdded: when a prefix entry is added to the IRIManager of the session.
    * sgnPrefixRemoved: when a prefix entry is adremoved from the IRIManager of the session.
    * sgnPrefixModified: when a prefix entry managed by the IRIManager of the session is modified.
    """
    sgnClosed = QtCore.pyqtSignal()
    sgnCheckForUpdate = QtCore.pyqtSignal()
    sgnDiagramFocused = QtCore.pyqtSignal(QtWidgets.QGraphicsScene)
    sgnFocusDiagram = QtCore.pyqtSignal(QtWidgets.QGraphicsScene)
    sgnFocusItem = QtCore.pyqtSignal(QtWidgets.QGraphicsItem)
    sgnPluginDisposed = QtCore.pyqtSignal(str)
    sgnPluginStarted = QtCore.pyqtSignal(str)
    sgnProjectSaved = QtCore.pyqtSignal()
    sgnQuit = QtCore.pyqtSignal()
    sgnReady = QtCore.pyqtSignal()
    sgnSaveProject = QtCore.pyqtSignal()
    sgnNoSaveProject = QtCore.pyqtSignal()
    sgnUpdateState = QtCore.pyqtSignal()

    sgnPrefixAdded = QtCore.pyqtSignal(str, str)
    sgnPrefixRemoved = QtCore.pyqtSignal(str)
    sgnPrefixModified = QtCore.pyqtSignal(str, str)
    sgnIRIRemovedFromAllDiagrams = QtCore.pyqtSignal(IRI)
    sgnSingleNodeSwitchIRI = QtCore.pyqtSignal(AbstractNode, IRI)

    sgnStartOwlImport = QtCore.pyqtSignal(str)

    # Signals related to rendering options
    sgnRenderingModified = QtCore.pyqtSignal(str)

    # Signals related to consistency check.
    # May be removed when a new reasoner API is implemented
    sgnConsistencyCheckStarted = QtCore.pyqtSignal()
    sgnPerfectOntology = QtCore.pyqtSignal()
    sgnInconsistentOntology = QtCore.pyqtSignal()
    sgnUnsatisfiableEntities = QtCore.pyqtSignal(int)
    sgnConsistencyCheckReset = QtCore.pyqtSignal()
    sgnUnsatisfiableClass = QtCore.pyqtSignal(IRI)
    sgnUnsatisfiableObjectProperty = QtCore.pyqtSignal(IRI)
    sgnUnsatisfiableDataProperty = QtCore.pyqtSignal(IRI)

    def __init__(
        self,
        application: QtWidgets.QApplication,
        path: Optional[str] = None,
        name: Optional[str] = None,
        iri: Optional[str] = None,
        prefix: Optional[str] = None,
        owl_path: Optional[str] = None,
        **kwargs: str,
    ) -> None:
        """
        Initialize the application main working session.

        :param application: Application instance
        :param path: The project file path
        :param name: The project name, for new projects
        :param iri: The ontology IRI, for new projects
        :param prefix: The IRI prefix, for new projects
        :param kwargs: Keyword arguments
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
        self.pmanager = PluginManager(self)
        self.nmanager = NetworkManager(self)
        self.project = None

        #############################################
        # INITIALIZE REASONER STATE VARIABLES
        #################################

        self.currentEmptyEntityIRI = None
        self.currentEmptyEntityType = None
        self.currentEmptyEntityExplanations = list()
        self.emptyEntityExplanations = {}
        self.inconsistentOntologyExplanations = list()

        #############################################
        # CONFIGURE SESSION
        #################################

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
        # LOAD THE PROJECT IF ONE GIVEN, OTHERWISE CREATE NEW PROJECT FROM SCRATCH
        #################################

        self.projectFromFile = False
        self.owlOntologyImportSize = None
        self.owlOntologyImportLoadedCount = None
        self.owlOntologyImportErrors = None
        if path:
            self.projectFromFile = True
            worker = self.createProjectLoader(File.Graphol, path, self)
            worker.run()
        elif owl_path:
            self.projectFromFile = True
            worker = self.createProjectLoader(File.Owl, owl_path, self)
            worker.run()
            self.project.name = name
        else:
            self.project = Project(
                parent=self,
                name=name,
                ontologyIRI=iri,
                ontologyPrefix=prefix,
                profile=OWL2Profile(),
            )

        if self.projectFromFile:
            worker = OwlOntologyImportSetWorker(self.project)
            worker.run()
            self.owlOntologyImportSize = worker.importSize
            self.owlOntologyImportLoadedCount = worker.loadCount
            if self.owlOntologyImportSize > self.owlOntologyImportLoadedCount:
                self.owlOntologyImportErrors = worker.owlOntologyImportErrors

        #############################################
        # CONNECT PROJECT SIGNALS
        #################################

        connect(self.project.sgnPrefixAdded, self.onPrefixAddedToProject)
        connect(self.project.sgnPrefixRemoved, self.onPrefixRemovedFromProject)
        connect(self.project.sgnPrefixModified, self.onPrefixModifiedInProject)
        connect(self.project.sgnIRIRemovedFromAllDiagrams, self.onIRIRemovedFromAllDiagrams)
        connect(self.project.sgnSingleNodeSwitchIRI, self.onSingleNodeSwitchIRI)
        connect(self.project.sgnUpdated, self.doResetConsistencyCheck)
        connect(self.project.sgnLanguageTagAdded, self.doAddLanguageTagToMenu)

        #############################################
        # COMPLETE SESSION SETUP
        #################################

        self.loadLanguageTagActions()
        self.setAcceptDrops(False)
        self.setCentralWidget(self.mdi)
        self.setDockOptions(Session.AnimatedDocks | Session.AllowTabbedDocks)
        self.setCorner(QtCore.Qt.TopLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.TopRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle(self.project)

        self.sgnReady.emit()

        LOGGER.info('Session startup completed: %s v%s [%s]', APPNAME, VERSION, self.project.name)

    #############################################
    #   SESSION CONFIGURATION
    #################################

    # noinspection PyArgumentList
    def loadLanguageTagActions(self) -> None:
        for langTag in self.project.getLanguages():
            settings = QtCore.QSettings()
            rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value)

            actionObjName = 'render_label_{}'.format(langTag)
            if not self.action(objectName=actionObjName):
                labelMenu = self.menu('render_label')
                action = QtWidgets.QAction(langTag, self, objectName=actionObjName,
                                           triggered=self.doRenderByLabel)
                action.setData(langTag)
                action.setCheckable(True)
                labelMenu.addAction(action)
                self.addAction(action)
                if rendering == IRIRender.LABEL.value or rendering == IRIRender.LABEL:
                    lang = settings.value('ontology/iri/render/language', 'it')
                    action.setChecked(lang == langTag)

    # noinspection PyArgumentList
    def initActions(self) -> None:
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
            QtGui.QIcon.fromTheme('system-reboot'), 'Restart', self,
            objectName='restart', statusTip='Restart {0}'.format(APPNAME),
            triggered=self.app.doRestart)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_help_outline_black'), 'About Qt',
            self, objectName='about_qt', statusTip='About Qt',
            triggered=QtWidgets.QApplication.aboutQt)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_help_outline_black'), 'About {0}'.format(APPNAME),
            self, objectName='about', shortcut=QtGui.QKeySequence.HelpContents,
            statusTip='About {0}'.format(APPNAME), triggered=self.doOpenDialog)
        action.setData(AboutDialog)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_link_black'), 'Go to the Eddy wiki',
            self, objectName='manual_web', statusTip='Go to the Eddy wiki',
            triggered=self.doOpenURL)
        action.setData(MANUAL_URL)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_link_black'), 'Report a bug',
            self, objectName='report_bug_web', statusTip='Report a bug',
            triggered=self.doOpenURL)
        action.setData(BUG_TRACKER)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_link_black'),
            'Visit {0} repository on GitHub'.format(APPNAME),
            self, objectName='github_web',
            statusTip='Visit {0} repository on GitHub'.format(APPNAME),
            triggered=self.doOpenURL)
        action.setData(PROJECT_HOME)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_link_black'), 'Visit {0} website'.format(ORGANIZATION_NAME),
            self, objectName='organization_web',
            statusTip='Visit {0} website'.format(ORGANIZATION_NAME),
            triggered=self.doOpenURL)
        action.setData(ORGANIZATION_URL)
        self.addAction(action)

        action = QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_link_black'), 'Visit {0} website'.format(APPNAME),
            self, objectName='app_web', statusTip='Visit {0} website'.format(APPNAME),
            triggered=self.doOpenURL)
        action.setData(APP_HOME)
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
            shortcut='SHIFT+F12', triggered=self.doOpenDialog)
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

        settings = QtCore.QSettings()
        collection = settings.value('project/recent', None, str) or []
        collection = collection[:5]
        group = QtWidgets.QActionGroup(self, objectName='recent_projects')
        for i, path in enumerate(collection, start=1):
            action = QtWidgets.QAction('{0}. {1}'.format(i, os.path.basename(path)), group,
                                       triggered=self.doOpenRecent)
            action.setData(path)
            group.addAction(action)
        self.addAction(group)

        if IS_MACOS:
            self.action('about').setIcon(QtGui.QIcon())
            self.action('open_preferences').setIcon(QtGui.QIcon())
            self.action('quit').setIcon(QtGui.QIcon())

        #############################################
        # APPLICATION NAVIGATION
        #################################

        action = QtWidgets.QAction(
            'Next Project Window', self, objectName='next_project_window',
            statusTip='Switch to the next open project', triggered=self.app.doFocusNextSession)
        action.setData(self)
        self.addAction(action)

        action = QtWidgets.QAction(
            'Previous Project Window', self, objectName='previous_project_window',
            statusTip='Switch to the previous open project',
            triggered=self.app.doFocusPreviousSession)
        action.setData(self)
        self.addAction(action)

        self.addAction(QtWidgets.QAction(
            'Focus Active Tab', self, objectName='focus_active_tab', shortcut='ALT+0',
            statusTip='Focus active tab', triggered=self.doFocusMdiArea))

        self.addAction(QtWidgets.QAction(
            'Next Tab', self, objectName='next_tab', shortcut='ALT+RIGHT',
            statusTip='Switch to next tab', triggered=self.mdi.activateNextSubWindow))

        self.addAction(QtWidgets.QAction(
            'Previous Tab', self, objectName='previous_tab', shortcut='ALT+LEFT',
            statusTip='Switch to previous tab', triggered=self.mdi.activatePreviousSubWindow))

        self.addAction(QtWidgets.QAction(
            'Close Tab', self, objectName='close_tab',
            statusTip='Close active tab', triggered=self.mdi.closeActiveSubWindow))

        self.addAction(QtWidgets.QAction(
            'Close Other Tabs', self, objectName='close_other_tabs',
            statusTip='Close other tabs', triggered=self.mdi.doCloseOtherSubWindows))

        self.addAction(QtWidgets.QAction(
            'Close All Tabs', self, objectName='close_all_tabs',
            statusTip='Close all tabs', triggered=self.mdi.closeAllSubWindows))

        self.addAction(QtWidgets.QActionGroup(self, objectName='sessions'))

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
            QtGui.QIcon(':/icons/24/ic_label_outline_black'), 'Rename...',
            self, objectName='rename_project', statusTip='Rename project',
            triggered=self.doRenameProject))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_close_black'), 'Close Project', self,
            objectName='close_project', shortcut='CTRL+SHIFT+W',
            statusTip='Close the current project', triggered=self.doClose))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_save_black'), 'Save', self,
            objectName='save', shortcut=QtGui.QKeySequence.Save,
            statusTip='Save the current project', enabled=False,
            triggered=self.doSave))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_save_black'), 'Save As...', self,
            objectName='save_as', shortcut=QtGui.QKeySequence.SaveAs,
            statusTip='Save the current project', triggered=self.doSaveAs))

        # self.addAction(QtWidgets.QAction(
        #    'Import...', self, objectName='import', triggered=self.doImport,
        #    statusTip='Import a document in the current project'))

        self.addAction(QtWidgets.QAction(
            'Export...', self, objectName='export', triggered=self.doExport,
            statusTip='Export the current project in a different format',
            enabled=False))

        self.addAction(QtWidgets.QAction(
            'Import Ontology', self, objectName='import_ontology', triggered=self.doImport,
            shortcut='CTRL+I', statusTip='Import a document in the current project'))

        self.addAction(QtWidgets.QAction(
            'Export Ontology', self, objectName='export_ontology', triggered=self.doExportOntology,
            shortcut='CTRL+E', statusTip='Export the current project in a different format'))

        self.addAction(QtWidgets.QAction(
            'Export Diagrams', self, objectName='export_diagrams', triggered=self.doExportDiagram,
            shortcut='CTRL+SHIFT+E', statusTip='Export a in a different format'))

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
            QtGui.QIcon(':/icons/24/ic_spellcheck_black'), 'Check compliance to profile',
            self, objectName='syntax_check', triggered=self.doProfileSyntaxCheck,
            statusTip='Run syntax validation according to the selected profile', enabled=False))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_owl'), 'Check OWL 2 DL compliance',
            self, objectName='dl_check', triggered=self.doDLCheck,
            statusTip='Check if the ontology can be interpreted by the Direct Semantics',
            enabled=False))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_help_outline_black'), 'Show explanation(s)',
            self, objectName='inconsistency_explanations',
            triggered=self.doShowInconsistentOntologyExplanations,
            statusTip='Show explanation(s) for inconsistent ontology', enabled=False))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_close_black'), 'Check labels',
            self, objectName='label_check',
            triggered=self.doShowNoMatchingLabelIRIs,
            statusTip='Show IRIs with no matching labels', enabled=True))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/18/ic_treeview_branch_closed'),
            'Run consistency check on active ontology',
            self, objectName='ontology_consistency_check',
            triggered=self.doOntologyConsistencyCheck,
            statusTip='Run Reasoner', enabled=False))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_refresh_black'), 'Reset consistency check',
            self, objectName='reset_reasoner', triggered=self.doResetConsistencyCheck,
            statusTip='Reset Reasoner', enabled=False))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_settings_ethernet_black'),
            'Open Ontology Manager',
            self, objectName='open_prefix_manager', enabled=True, shortcut='CTRL+M',
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
        icon.addFile(':/icons/24/ic_grid_on_black', QtCore.QSize(), QtGui.QIcon.Normal,
                     QtGui.QIcon.On)
        icon.addFile(':/icons/24/ic_grid_off_black', QtCore.QSize(), QtGui.QIcon.Normal,
                     QtGui.QIcon.Off)
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

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/18/ic_zoom_black'), 'Focus on source', self,
            objectName='focus_on_source', statusTip='Focus on the source node',
            triggered=self.doFocusOnSource))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/18/ic_zoom_black'), 'Focus on target', self,
            objectName='focus_on_target', statusTip='Focus on the target node',
            triggered=self.doFocusOnTarget))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_delete_black'), 'Remove all breakpoints', self,
            objectName='remove_all_breakpoints', statusTip='Remove all the breakpoints',
            triggered=self.doRemoveAllBreakpoints))

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
            QtGui.QIcon(':/icons/24/ic_label_outline_black'), 'Rename...',
            self, objectName='refactor_name',
            triggered=self.doRefactorName))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_refresh_black'), 'Relocate label',
            self, objectName='relocate_label',
            triggered=self.doRelocateLabel))

        style = self.style()
        isize = style.pixelMetric(QtWidgets.QStyle.PM_ToolBarIconSize)
        for name, trigger in (
        ('brush', self.doSetNodeBrush), ('refactor_brush', self.doRefactorBrush)):
            group = QtWidgets.QActionGroup(self, objectName=name)
            for color in Color:
                action = QtWidgets.QAction(
                    BrushIcon(isize, isize, color.value), color.name,
                    self, checkable=False, iconVisibleInMenu=True, triggered=trigger)
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

        action = QtWidgets.QAction(
            'Functional', self, objectName='property_functional',
            checkable=True, checked=False, triggered=self.doSetNodeMeta)
        action.setData(K_FUNCTIONAL)
        self.addAction(action)

        action = QtWidgets.QAction(
            'Inverse Functional', self, objectName='property_inverse_functional',
            checkable=True, checked=False, triggered=self.doSetNodeMeta)
        action.setData(K_INVERSE_FUNCTIONAL)
        self.addAction(action)

        action = QtWidgets.QAction(
            'Asymmetric', self, objectName='property_asymmetric',
            checkable=True, checked=False, triggered=self.doSetNodeMeta)
        action.setData(K_ASYMMETRIC)
        self.addAction(action)

        action = QtWidgets.QAction(
            'Irreflexive', self, objectName='property_irreflexive',
            checkable=True, checked=False, triggered=self.doSetNodeMeta)
        action.setData(K_IRREFLEXIVE)
        self.addAction(action)

        action = QtWidgets.QAction(
            'Reflexive', self, objectName='property_reflexive',
            checkable=True, checked=False, triggered=self.doSetNodeMeta)
        action.setData(K_REFLEXIVE)
        self.addAction(action)

        action = QtWidgets.QAction(
            'Symmetric', self, objectName='property_symmetric',
            checkable=True, checked=False, triggered=self.doSetNodeMeta)
        action.setData(K_SYMMETRIC)
        self.addAction(action)

        action = QtWidgets.QAction(
            'Transitive', self, objectName='property_transitive',
            checkable=True, checked=False, triggered=self.doSetNodeMeta)
        action.setData(K_TRANSITIVE)
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

        #############################################
        # IRI SPECIFIC
        #################################

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'),
            'IRI refactor',
            self, objectName='iri_refactor',
            triggered=self.doOpenIRIPropsBuilder))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_format_size_black'),
            'Set font',
            self, objectName='iri_set_font',
            triggered=self.doOpenIRIFontDialog))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_create_black'),
            'Annotations',
            self, objectName='iri_annotations_refactor',
            triggered=self.doOpenIRIPropsAnnotationBuilder))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_create_black'),
            'Annotations',
            self, objectName='edge_annotations_refactor',
            triggered=self.doOpenEdgePropsAnnotationBuilder))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_owl'),
            'OWL Axioms',
            self, objectName='iri_involving_axioms',
            triggered=self.doShowInvolvingAxioms))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'),
            'Node IRI',
            self, objectName='node_iri_refactor',
            triggered=self.doOpenIRIDialog))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_format_size_black'),
            'Set font',
            self, objectName='node_set_font',
            triggered=self.doOpenNodeFontDialog))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'),
            'Facet refactor',
            self, objectName='node_facet_refactor',
            triggered=self.doOpenFacetDialog))

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'),
            'Literal refactor',
            self, objectName='node_literal_refactor',
            triggered=self.doOpenLiteralDialog))

        action = QtWidgets.QAction('Render by full IRI', self, objectName='render_full_iri',
                                   triggered=self.doRenderByFullIRI)
        action.setCheckable(True)
        self.addAction(action)
        action = QtWidgets.QAction('Render by prefixed IRI', self, objectName='render_prefixed_iri',
                                   triggered=self.doRenderByPrefixedIRI)
        action.setCheckable(True)
        self.addAction(action)
        action = QtWidgets.QAction('Render by simple name', self, objectName='render_simple_name',
                                   triggered=self.doRenderBySimpleName)
        action.setCheckable(True)
        self.addAction(action)

        '''action = QtWidgets.QAction('Render by label', self, objectName='render_label', triggered=self.doRenderByLabel)
        self.addAction(action)
        action.setCheckable(True)'''

        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value)
        if rendering == IRIRender.FULL.value or rendering == IRIRender.FULL:
            self.action(objectName='render_full_iri').setChecked(True)
        elif rendering == IRIRender.PREFIX.value or rendering == IRIRender.PREFIX:
            self.action(objectName='render_prefixed_iri').setChecked(True)
        elif rendering == IRIRender.SIMPLE_NAME.value or rendering == IRIRender.SIMPLE_NAME:
            self.action(objectName='render_simple_name').setChecked(True)
        '''elif rendering == IRIRender.LABEL.value or rendering == IRIRender.LABEL:
            self.action(objectName='render_label').setChecked(True)'''

        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/icons/24/ic_help_outline_black'),
            'Show explanation(s)',
            self, objectName='emptiness_explanation',
            triggered=self.doEmptyEntityExplanation))

    def initExporters(self) -> None:
        """
        Initialize diagram and project exporters.
        """
        self.addOntologyExporter(OWLOntologyExporter)
        self.addProjectExporter(GrapholIRIProjectExporter)
        self.addProjectExporter(PdfProjectExporter)
        self.addProjectExporter(CsvProjectExporter)
        self.addProjectExporter(XlsxProjectExporter)
        # FIXME: CURRENTLY UNSUPPORTED
        # self.addProjectExporter(GraphReferencesProjectExporter)
        # self.addDiagramExporter(GraphMLDiagramExporter)
        self.addDiagramExporter(BmpDiagramExporter)
        self.addDiagramExporter(JpegDiagramExporter)
        self.addDiagramExporter(PngDiagramExporter)

    def initLoaders(self) -> None:
        """
        Initialize diagram and project loaders.
        """
        self.addOntologyLoader(GraphMLOntologyLoader)
        self.addOntologyLoader(GrapholOntologyIRILoader_v3)
        self.addOntologyLoader(CsvLoader)
        self.addOntologyLoader(XlsxLoader)
        self.addProjectLoader(GrapholIRIProjectLoader_v3)
        self.addProjectLoader(OwlProjectLoader)

    # noinspection PyArgumentList
    def initMenus(self) -> None:
        """
        Configure application built-in menus.
        """
        #############################################
        # MENU BAR RELATED
        #################################

        menu = QtWidgets.QMenu('&File', objectName='file')
        menu.addAction(self.action('new_diagram'))
        menu.addAction(self.action('open'))
        menu.addSeparator()
        menu.addAction(self.action('save'))
        # DISABLE SAVE AS ACTION
        # See: https://github.com/obdasystems/eddy/issues/9
        menu.addAction(self.action('save_as'))
        menu.addAction(self.action('close_project'))
        menu.addSeparator()
        # menu.addAction(self.action('import'))
        menu.addAction(self.action('import_ontology'))
        menu.addAction(self.action('export_ontology'))
        # menu.addSeparator()
        # menu.addAction(self.action('export'))
        menu.addSeparator()
        menu.addAction(self.action('export_diagrams'))
        menu.addSeparator()
        for action in self.action('recent_projects').actions():
            menu.addAction(action)
        menu.addSeparator()
        menu.addAction(self.action('print'))
        menu.addSeparator()
        menu.addAction(self.action('restart'))
        menu.addSeparator()
        menu.addAction(self.action('quit'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Compose', objectName='compose')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        menu.addAction(self.action('property_domain'))
        menu.addAction(self.action('property_range'))
        menu.addAction(self.action('property_domain_range'))
        menu.addSeparator()
        menu.addAction(self.action('property_functional'))
        menu.addAction(self.action('property_inverse_functional'))
        menu.addAction(self.action('property_symmetric'))
        menu.addAction(self.action('property_asymmetric'))
        menu.addAction(self.action('property_reflexive'))
        menu.addAction(self.action('property_irreflexive'))
        menu.addAction(self.action('property_transitive'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('\u200C&Edit', objectName='edit')
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
        menu.addMenu(self.menu('compose'))
        menu.addSeparator()
        menu.addAction(self.action('open_preferences'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Toolbars', objectName='toolbars')
        menu.addAction(self.widget('document_toolbar').toggleViewAction())
        menu.addAction(self.widget('editor_toolbar').toggleViewAction())
        menu.addAction(self.widget('graphol_toolbar').toggleViewAction())
        menu.addAction(self.widget('view_toolbar').toggleViewAction())
        menu.addAction(self.widget('reasoner_toolbar').toggleViewAction())

        self.addMenu(menu)

        menu = QtWidgets.QMenu('\u200C&View', objectName='view')
        # RENDER BY IRI,PREFIX,LABEL .... Menu
        renderInnerMenu = menu.addMenu('Render by...')
        renderInnerMenu.addAction(self.action('render_full_iri'))
        renderInnerMenu.addAction(self.action('render_prefixed_iri'))
        renderInnerMenu.addAction(self.action('render_simple_name'))
        # renderInnerMenu.addAction(self.action('render_label'))

        labelMenu = QtWidgets.QMenu('Render by label', objectName='render_label')
        self.addMenu(labelMenu)
        action = QtWidgets.QAction('it', self, objectName='render_label_it',
                                   triggered=self.doRenderByLabel)
        action.setData('it')
        action.setCheckable(True)
        self.addAction(action)
        labelMenu.addAction(action)
        action = QtWidgets.QAction('en', self, objectName='render_label_en',
                                   triggered=self.doRenderByLabel)
        action.setData('en')
        self.addAction(action)
        action.setCheckable(True)
        labelMenu.addAction(action)
        action = QtWidgets.QAction('es', self, objectName='render_label_es',
                                   triggered=self.doRenderByLabel)
        action.setData('es')
        self.addAction(action)
        action.setCheckable(True)
        labelMenu.addAction(action)
        action = QtWidgets.QAction('fr', self, objectName='render_label_fr',
                                   triggered=self.doRenderByLabel)
        action.setData('fr')
        self.addAction(action)
        action.setCheckable(True)
        labelMenu.addAction(action)
        action = QtWidgets.QAction('de', self, objectName='render_label_de',
                                   triggered=self.doRenderByLabel)
        action.setData('de')
        self.addAction(action)
        action.setCheckable(True)
        labelMenu.addAction(action)

        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value)
        if rendering == IRIRender.LABEL.value or rendering == IRIRender.LABEL:
            lang = settings.value('ontology/iri/render/language', 'it')
            if lang == 'it':
                self.action(objectName='render_label_it').setChecked(True)
                self.action(objectName='render_label_en').setChecked(False)
                self.action(objectName='render_label_es').setChecked(False)
                self.action(objectName='render_label_fr').setChecked(False)
                self.action(objectName='render_label_de').setChecked(False)
            elif lang == 'en':
                self.action(objectName='render_label_it').setChecked(False)
                self.action(objectName='render_label_en').setChecked(True)
                self.action(objectName='render_label_es').setChecked(False)
                self.action(objectName='render_label_fr').setChecked(False)
                self.action(objectName='render_label_de').setChecked(False)
            elif lang == 'es':
                self.action(objectName='render_label_it').setChecked(False)
                self.action(objectName='render_label_en').setChecked(False)
                self.action(objectName='render_label_es').setChecked(True)
                self.action(objectName='render_label_fr').setChecked(False)
                self.action(objectName='render_label_de').setChecked(False)
            elif lang == 'fr':
                self.action(objectName='render_label_it').setChecked(False)
                self.action(objectName='render_label_en').setChecked(False)
                self.action(objectName='render_label_es').setChecked(False)
                self.action(objectName='render_label_fr').setChecked(True)
                self.action(objectName='render_label_de').setChecked(False)
            elif lang == 'de':
                self.action(objectName='render_label_it').setChecked(False)
                self.action(objectName='render_label_en').setChecked(False)
                self.action(objectName='render_label_es').setChecked(False)
                self.action(objectName='render_label_fr').setChecked(False)
                self.action(objectName='render_label_de').setChecked(True)

        renderInnerMenu.addMenu(labelMenu)

        menu.addSeparator()
        menu.addAction(self.action('toggle_grid'))
        menu.addSeparator()
        menu.addMenu(self.menu('toolbars'))
        menu.addSeparator()
        self.addMenu(menu)

        menu = QtWidgets.QMenu('&Ontology', objectName='ontology')
        menu.addAction(self.action('syntax_check'))
        menu.addAction(self.action('label_check'))
        menu.addAction(self.action('dl_check'))
        menu.addAction(self.action('inconsistency_explanations'))

        # TODO scommenta dopo corretta implementazione reasoner per consistency check
        menu.addAction(self.action('ontology_consistency_check'))
        menu.addSeparator()
        menu.addAction(self.action('open_prefix_manager'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('&Tools', objectName='tools')
        menu.addAction(self.action('install_plugin'))
        menu.addSeparator()
        menu.addAction(self.action('system_log'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Diagram Tabs', objectName='diagrams')
        menu.addAction(self.action('focus_active_tab'))
        menu.addAction(self.action('next_tab'))
        menu.addAction(self.action('previous_tab'))
        menu.addSeparator()
        menu.addAction(self.action('close_tab'))
        menu.addAction(self.action('close_other_tabs'))
        menu.addAction(self.action('close_all_tabs'))
        menu.addSeparator()
        self.addMenu(menu)

        menu = QtWidgets.QMenu('&Window', objectName='window')
        menu.addAction(self.action('next_project_window'))
        menu.addAction(self.action('previous_project_window'))
        menu.addSeparator()
        menu.addMenu(self.menu('diagrams'))
        menu.addSeparator()
        self.addMenu(menu)

        menu = QtWidgets.QMenu('&Help', objectName='help')
        menu.addAction(self.action('about'))
        if not IS_MACOS:
            menu.addSeparator()
        menu.addAction(self.action('check_for_updates'))
        menu.addSeparator()
        menu.addAction(self.action('manual_web'))
        menu.addAction(self.action('report_bug_web'))
        menu.addAction(self.action('github_web'))
        menu.addAction(self.action('organization_web'))
        menu.addAction(self.action('app_web'))
        menu.addAction(self.action('graphol_web'))
        self.addMenu(menu)

        #############################################
        # NODE GENERIC
        #################################

        menu = QtWidgets.QMenu('Select color', objectName='brush')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        menu.addActions(self.action('brush').actions())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Select color', objectName='refactor_brush')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        menu.addActions(self.action('refactor_brush').actions())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Refactor', objectName='refactor')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_shapes_black'))
        menu.addAction(self.action('iri_refactor'))
        menu.addMenu(self.menu('refactor_brush'))
        menu.addAction(self.action('iri_set_font'))
        self.addMenu(menu)

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Compose', objectName='compose_attribute')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        menu.addSection('Domain / Range')
        menu.addAction(self.action('property_domain'))
        menu.addAction(self.action('property_range'))
        menu.addAction(self.action('property_domain_range'))
        menu.addSection('Axioms')
        menu.addAction(self.action('property_functional'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Compose', objectName='compose_role')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        menu.addSection('Domain / Range')
        menu.addAction(self.action('property_domain'))
        menu.addAction(self.action('property_range'))
        menu.addAction(self.action('property_domain_range'))
        menu.addSection('Axioms')
        menu.addAction(self.action('property_functional'))
        menu.addAction(self.action('property_inverse_functional'))
        menu.addAction(self.action('property_symmetric'))
        menu.addAction(self.action('property_asymmetric'))
        menu.addAction(self.action('property_reflexive'))
        menu.addAction(self.action('property_irreflexive'))
        menu.addAction(self.action('property_transitive'))
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
        menuBar.addMenu(self.menu('ontology'))
        menuBar.addMenu(self.menu('tools'))
        menuBar.addMenu(self.menu('window'))
        menuBar.addMenu(self.menu('help'))

    # noinspection PyArgumentList,PyTypeChecker
    def initPre(self) -> None:
        """
        Initialize stuff that are shared by actions, menus, widgets etc.
        """
        self.addWidget(QtWidgets.QToolBar('Document', objectName='document_toolbar'))
        self.addWidget(QtWidgets.QToolBar('Editor', objectName='editor_toolbar'))
        self.addWidget(QtWidgets.QToolBar('View', objectName='view_toolbar'))
        self.addWidget(QtWidgets.QToolBar('Graphol', objectName='graphol_toolbar'))
        self.addWidget(QtWidgets.QToolBar('Reasoner', objectName='reasoner_toolbar'))

    def initPlugins(self) -> None:
        """
        Load and initialize application plugins.
        """
        self.addPlugins(self.pmanager.init())

    def initProfiles(self) -> None:
        """
        Initialize the ontology profiles.
        """
        self.addProfile(OWL2Profile)
        self.addProfile(OWL2QLProfile)
        self.addProfile(OWL2RLProfile)

    def initSignals(self) -> None:
        """
        Connect session specific signals to their slots.
        """
        connect(self.app.sgnSessionCreated, self.onSessionCreated)
        connect(self.app.sgnSessionClosed, self.onSessionClosed)
        connect(self.undostack.cleanChanged, self.doUpdateState)
        connect(self.nmanager.sgnNoUpdateAvailable, self.onNoUpdateAvailable)
        connect(self.nmanager.sgnNoUpdateDataAvailable, self.onNoUpdateDataAvailable)
        connect(self.nmanager.sgnUpdateAvailable, self.onUpdateAvailable)
        connect(self.sgnCheckForUpdate, self.doCheckForUpdate)
        connect(self.sgnFocusDiagram, self.doFocusDiagram)
        connect(self.sgnFocusItem, self.doFocusItem)
        connect(self.sgnProjectSaved, self.onProjectSaved)
        connect(self.sgnReady, self.doUpdateState)
        connect(self.sgnReady, self.onSessionReady)
        connect(self.sgnSaveProject, self.doSave)
        connect(self.sgnUpdateState, self.doUpdateState)

    def initState(self) -> None:
        """
        Configure application state by reading the preferences file.
        """
        settings = QtCore.QSettings()
        self.restoreGeometry(
            settings.value('session/geometry', QtCore.QByteArray(), QtCore.QByteArray))
        self.restoreState(settings.value('session/state', QtCore.QByteArray(), QtCore.QByteArray))
        self.action('toggle_grid').setChecked(settings.value('diagram/grid', False, bool))

    def initStatusBar(self) -> None:
        """
        Configure the status bar.
        """
        statusbar = QtWidgets.QStatusBar(self)
        statusbar.addPermanentWidget(self.widget('progress_bar'))
        statusbar.addPermanentWidget(QtWidgets.QWidget())
        statusbar.setSizeGripEnabled(False)
        self.setStatusBar(statusbar)

    def initToolBars(self) -> None:
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
        toolbar.addAction(self.action('dl_check'))

        toolbar = self.widget('reasoner_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        # TODO scommenta dopo corretta implementazione reasoner per consistency check
        # toolbar.addWidget(self.widget('select_reasoner'))
        toolbar.addAction(self.action('ontology_consistency_check'))
        toolbar.addAction(self.action('reset_reasoner'))
        toolbar.addAction(self.action('inconsistency_explanations'))

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('document_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('editor_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('view_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('graphol_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('reasoner_toolbar'))

    # noinspection PyArgumentList
    def initWidgets(self) -> None:
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
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.setStatusTip('Change the profile of the active project')
        combobox.addItems(self.profileNames())
        connect(combobox.activated, self.doSetProfile)
        self.addWidget(combobox)

        # TODO: fix reasoner setup when a decent reasoner support is implemented
        combobox = ComboBox(objectName='select_reasoner')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.setStatusTip('Select one of any available reasoners')
        combobox.addItems(['HermiT'])
        combobox.setEnabled(False)
        connect(combobox.activated, self.doSelectReasoner)
        self.addWidget(combobox)

        progressBar = QtWidgets.QProgressBar(objectName='progress_bar')
        progressBar.setContentsMargins(0, 0, 0, 0)
        progressBar.setFixedSize(222, 14)
        progressBar.setRange(0, 0)
        progressBar.setVisible(False)
        self.addWidget(progressBar)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str, str)
    def onPrefixAddedToProject(self, pref: str, ns: str) -> None:
        self.sgnPrefixAdded.emit(pref, ns)

    @QtCore.pyqtSlot(str)
    def onPrefixRemovedFromProject(self, pref: str) -> None:
        self.sgnPrefixRemoved.emit(pref)

    @QtCore.pyqtSlot(str, str)
    def onPrefixModifiedInProject(self, pref: str, ns: str) -> None:
        self.sgnPrefixModified.emit(pref, ns)

    @QtCore.pyqtSlot(IRI)
    def onIRIRemovedFromAllDiagrams(self, iri: IRI) -> None:
        self.sgnIRIRemovedFromAllDiagrams.emit(iri)

    @QtCore.pyqtSlot(QtWidgets.QGraphicsItem, IRI)
    def onSingleNodeSwitchIRI(self, node: QtWidgets.QGraphicsItem, iri: IRI) -> None:
        self.sgnSingleNodeSwitchIRI.emit(node, iri)

    @QtCore.pyqtSlot()
    def doBringToFront(self) -> None:
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
    def doCenterDiagram(self) -> None:
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
                moveX = snapF(((R1.right() - R2.right()) - (R2.left() - R1.left())) / 2,
                              Diagram.GridSize)
                moveY = snapF(((R1.bottom() - R2.bottom()) - (R2.top() - R1.top())) / 2,
                              Diagram.GridSize)
                if moveX or moveY:
                    items = [x for x in items if x.isNode() or x.isEdge()]
                    command = CommandItemsTranslate(diagram, items, moveX, moveY, 'center diagram')
                    self.undostack.push(command)
                    self.mdi.activeView().centerOn(0, 0)

    @QtCore.pyqtSlot()
    def doCheckForUpdate(self) -> None:
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
            settings = QtCore.QSettings()
            channel = Channel.valueOf(settings.value('update/channel', channel, str))
        except TypeError:
            pass
        finally:
            self.nmanager.checkForUpdate(channel)

    @QtCore.pyqtSlot()
    def doClose(self) -> None:
        """
        Close the currently active subwindow.
        """
        self.close()
        self.sgnClosed.emit()

    @QtCore.pyqtSlot()
    def doComposePropertyExpression(self) -> None:
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
                    QtCore.QPointF(snapF(-source.width() / 2 - 70, size), 0),
                    QtCore.QPointF(snapF(+source.width() / 2 + 70, size), 0),
                    QtCore.QPointF(0, snapF(-source.height() / 2 - 70, size)),
                    QtCore.QPointF(0, snapF(+source.height() / 2 + 70, size)),
                    QtCore.QPointF(snapF(-source.width() / 2 - 70, size),
                                   snapF(-source.height() / 2 - 70, size)),
                    QtCore.QPointF(snapF(+source.width() / 2 + 70, size),
                                   snapF(-source.height() / 2 - 70, size)),
                    QtCore.QPointF(snapF(-source.width() / 2 - 70, size),
                                   snapF(+source.height() / 2 + 70, size)),
                    QtCore.QPointF(snapF(+source.width() / 2 + 70, size),
                                   snapF(+source.height() / 2 + 70, size)),
                )
                pos = source.pos() + offsets[0]
                num = sys.maxsize
                rad = QtCore.QPointF(restriction.width() / 2, restriction.height() / 2)
                for o in offsets:
                    if source.pos() + o not in positions:
                        count = len(scene.items(
                            QtCore.QRectF(source.pos() + o - rad, source.pos() + o + rad)))
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

    # noinspection PyArgumentList
    @QtCore.pyqtSlot(str)
    def doAddLanguageTagToMenu(self, lang: str) -> None:
        """
        Add an action to RenderByLabel menu to allow selecting 'lang'
        """
        labelMenu = self.menu('render_label')
        action = QtWidgets.QAction(lang, self, objectName='render_label_{}'.format(lang),
                                   triggered=self.doRenderByLabel)
        action.setData(lang)
        action.setCheckable(True)
        labelMenu.addAction(action)
        self.addAction(action)

    @QtCore.pyqtSlot()
    def doCopy(self) -> None:
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
    def doCut(self) -> None:
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
                items.extend([x for item in items if item.isNode()
                              for x in item.edges if x not in items])
                self.undostack.push(CommandItemsRemove(diagram, items))

    @QtCore.pyqtSlot()
    def doDelete(self) -> None:
        """
        Delete the currently selected items from the active diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            items = diagram.selectedItems()
            if items:
                items.extend([x for item in items if item.isNode()
                              for x in item.edges if x not in items])
                self.undostack.push(CommandItemsRemove(diagram, items))

    @QtCore.pyqtSlot()
    def doExport(self) -> None:
        """
        Export the current project.
        """
        if self.project.isEmpty():
            return
        dialog = FileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setNameFilters(sorted(
            self.ontologyExporterNameFilters() +
            self.projectExporterNameFilters({File.Graphol}) +
            self.diagramExporterNameFilters({File.Pdf, File.GraphML})
        ))
        dialog.selectFile(self.project.name)
        dialog.selectNameFilter(File.Owl.value)
        if dialog.exec_():
            filetype = File.valueOf(dialog.selectedNameFilter())
            try:
                try:
                    worker = self.createOntologyExporter(filetype, self.project, self)
                except ValueError:
                    try:
                        worker = self.createProjectExporter(filetype, self.project, self)
                    except ValueError:
                        diagram = first(self.project.diagrams())
                        if not diagram:
                            LOGGER.info('no diagram present in the project')
                            return
                        worker = self.createDiagramExporter(filetype, diagram, self)
                worker.run(expandPath(first(dialog.selectedFiles())))
            except Exception as e:
                LOGGER.error('error during export: {}', e)
                self.addNotification("""
                <b><font color="#7E0B17">ERROR</font></b>:
                Could not complete the export, see the System Log for details.
                """)

    @QtCore.pyqtSlot()
    def doExportDiagram(self) -> None:
        """
        Export the current project diagrams.
        """
        if self.project.isEmpty():
            return
        dialog = FileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setNameFilters(sorted(
            self.projectExporterNameFilters({File.Graphol}) +
            self.diagramExporterNameFilters()
        ))
        dialog.selectFile(self.project.name)
        dialog.selectNameFilter(File.Pdf.value)
        if dialog.exec_():
            filetype = File.valueOf(dialog.selectedNameFilter())
            try:
                # EXPORT PROJECT
                with BusyProgressDialog('Exporting {0}...'.format(self.project.name), parent=self):
                    worker = self.createProjectExporter(filetype, self.project, self)
                    worker.run(expandPath(first(dialog.selectedFiles())))
                    if fexists(expandPath(first(dialog.selectedFiles()))):
                        self.addNotification("""
                        Project export completed: <br><br>
                        <b><a href=file:{0}>{1}</a></b>
                        """.format(expandPath(first(dialog.selectedFiles())), 'Open File'))
            except ValueError:
                # DIAGRAM SELECTION
                filterDialog = DiagramSelectionDialog(self)
                if not filterDialog.exec_():
                    return
                # EXPORT DIAGRAMS
                with BusyProgressDialog(parent=self) as progress:
                    for diagram in filterDialog.selectedDiagrams():
                        progress.setWindowTitle('Exporting {0}...'.format(diagram.name))
                        path = first(dialog.selectedFiles())
                        name, ext = os.path.splitext(path)
                        outputPath = expandPath('{}_{}{}'.format(name, diagram.name, ext))
                        worker = self.createDiagramExporter(filetype, diagram, self)
                        worker.run(outputPath)
                self.addNotification("""
                Project export completed: <br><br>
                <b><a href={0}>{1}</a></b>
                """.format(os.path.dirname(first(dialog.selectedFiles())), 'Open Folder'))
            except Exception as e:
                LOGGER.error('error during export: {}', e)
                self.addNotification("""
                <b><font color="#7E0B17">ERROR</font></b>:
                Could not complete the export, see the System Log for details.
                """)

    @QtCore.pyqtSlot()
    def doExportOntology(self) -> None:
        """
        Export the current project.
        """
        dialog = FileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setNameFilters(sorted(
            self.ontologyExporterNameFilters() +
            self.projectExporterNameFilters({File.Graphol})
        ))
        dialog.selectFile(self.project.name)
        dialog.selectNameFilter(File.Owl.value)
        if dialog.exec_():
            filetype = File.valueOf(dialog.selectedNameFilter())
            try:
                try:
                    worker = self.createOntologyExporter(filetype, self.project, self)
                except ValueError:
                    worker = self.createProjectExporter(filetype, self.project, self)
                worker.run(expandPath(first(dialog.selectedFiles())))
                if (fexists(expandPath(first(dialog.selectedFiles())))):
                    self.addNotification("""
                    Ontology export completed: <br><br>
                    <b><a href=file:{0}>{1}</a></b>
                    """.format(expandPath(first(dialog.selectedFiles())), 'Open File'))
            except Exception as e:
                LOGGER.error('error during export: {}', e)
                self.addNotification("""
                <b><font color="#7E0B17">ERROR</font></b>:
                Could not complete the export, see the System Log for details.
                """)

    @QtCore.pyqtSlot()
    def doFocusMdiArea(self) -> None:
        """
        Focus the active MDI area subwindow, if any.
        """
        subwindow = self.mdi.currentSubWindow()
        if subwindow:
            subwindow.setFocus()

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene)
    def doFocusDiagram(self, diagram: Diagram) -> None:
        """
        Focus the given diagram in the MDI area.

        :param diagram: The diagram to focus
        """
        subwindow = self.mdi.subWindowForDiagram(diagram)
        if not subwindow:
            view = self.createDiagramView(diagram)
            subwindow = self.createMdiSubWindow(view)
            subwindow.showMaximized()
        self.mdi.setActiveSubWindow(subwindow)
        self.mdi.update()
        self.sgnDiagramFocused.emit(diagram)

    @QtCore.pyqtSlot(QtWidgets.QGraphicsItem)
    def doFocusItem(self, item: AbstractItem) -> None:
        """
        Focus an item in its diagram.

        :param item: The item to focus
        """
        self.sgnFocusDiagram.emit(item.diagram)
        self.mdi.activeDiagram().clearSelection()
        self.mdi.activeView().centerOn(item)
        item.setSelected(True)

    @QtCore.pyqtSlot()
    def doFocusOnSource(self) -> None:
        """
        Focus on the source node of the selected edge.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = diagram.selectedEdges()
            if len(selected) == 1:
                edge = selected[0]
                sourceNode = edge.source
                self.doFocusItem(sourceNode)

    @QtCore.pyqtSlot()
    def doFocusOnTarget(self) -> None:
        """
        Focus on the target node of the selected edge.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = diagram.selectedEdges()
            if len(selected) == 1:
                edge = selected[0]
                targetNode = edge.target
                self.doFocusItem(targetNode)

    @QtCore.pyqtSlot()
    def doImport(self) -> None:
        """
        Import an ontology into the currently active Project.
        """
        dialog = FileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setNameFilters(self.ontologyLoaderNameFilters({File.GraphML}))
        if dialog.exec_():
            filetype = File.valueOf(dialog.selectedNameFilter())
            selected = [x for x in dialog.selectedFiles() if
                        File.forPath(x) is filetype and fexists(x)]
            if selected:
                try:
                    with BusyProgressDialog(parent=self) as progress:
                        for path in selected:
                            progress.setWindowTitle(
                                'Importing {0}...'.format(os.path.basename(path)))
                            worker = self.createOntologyLoader(filetype, path, self.project, self)
                            if filetype == File.Csv or filetype == File.Xlsx:
                                progress.close()
                                dialog = AnnotationsOverridingDialog(self)
                                if not dialog.exec_():
                                    return
                                override = dialog.checkedOption()
                            if filetype == File.Csv:
                                worker.run(path, override)
                            elif filetype == File.Xlsx:
                                worker.run(expandPath(path), override)
                            else:
                                worker.run()
                                if worker.owlOntologyImportErrors:
                                    msgbox = QtWidgets.QMessageBox(self)
                                    msgbox.setDetailedText(
                                        '{} OWL 2 ontologies declared as imports '
                                        'have not been loaded. Please open the ontology manager '
                                        'for more details and to retry loading'
                                        .format(len(worker.owlOntologyImportErrors)))
                                    msgbox.setIconPixmap(
                                        QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
                                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
                                    msgbox.setText('Eddy could not correctly load some of '
                                                   'the declared OWL ontology imports')
                                    msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                                    msgbox.setWindowTitle('Problem managing OWL ontology '
                                                          'import declaration(s)')
                                    msgbox.exec_()
                except Exception as e:
                    msgbox = QtWidgets.QMessageBox(self)
                    msgbox.setDetailedText(format_exception(e))
                    msgbox.setIconPixmap(
                        QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
                    msgbox.setText('Eddy could not import all the selected files!')
                    msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                    msgbox.setWindowTitle('Import failed!')
                    msgbox.exec_()

    @QtCore.pyqtSlot()
    def doInvertRole(self) -> None:
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
                '''
                predicates = self.project.predicates(node.type(), node.text())
                for predicate in predicates:
                    swappable = set.union(swappable, predicate.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                    for inv in predicate.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f3):
                        swappable = set.union(swappable, inv.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                '''
                occurrences = self.project.iriOccurrences(node.type(), node.iri)
                for occ in occurrences:
                    swappable = set.union(swappable,
                                          occ.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                    for inv in occ.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f3):
                        swappable = set.union(swappable, inv.outgoingNodes(filter_on_edges=f1,
                                                                           filter_on_nodes=f2))

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
    def doLookupOccurrence(self) -> None:
        """
        Focus the item which is being held by the supplying QAction.
        """
        self.sgnFocusItem.emit(self.sender().data())

    @QtCore.pyqtSlot()
    def doNewDiagram(self) -> None:
        """
        Create a new diagram.
        """
        form = NewDiagramForm(self.project, self)
        if form.exec_() == NewDiagramForm.Accepted:
            settings = QtCore.QSettings()
            size = settings.value('diagram/size', 5000, int)
            name = form.nameField.value()
            diagram = Diagram.create(name, size, self.project)
            connect(diagram.sgnItemAdded, self.project.doAddItem)
            connect(diagram.sgnItemRemoved, self.project.doRemoveItem)
            connect(diagram.selectionChanged, self.doUpdateState)
            self.undostack.push(CommandDiagramAdd(diagram, self.project))
            self.sgnFocusDiagram.emit(diagram)

    @QtCore.pyqtSlot()
    def doOpen(self) -> None:
        """
        Open a project in a new session.
        """
        dialog = FileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setNameFilters([File.Graphol.value])
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            self.app.sgnCreateSession.emit(expandPath(first(dialog.selectedFiles())))

    @QtCore.pyqtSlot()
    def doOpenRecent(self) -> None:
        """
        Open a recent project in a new session.
        """
        action = self.sender()
        path = expandPath(action.data())
        if path != expandPath(self.project.path):
            self.app.sgnCreateSession.emit(expandPath(action.data()))

    @QtCore.pyqtSlot()
    def doOpenDialog(self) -> None:
        """
        Open a dialog window by initializing it using the class stored in action data.
        """
        action = self.sender()
        dialog = action.data()
        window = dialog(self)
        window.open()

    @QtCore.pyqtSlot()
    def doOpenURL(self) -> None:
        """
        Open a URL using the operating system default browser.
        """
        action = self.sender()
        weburl = action.data()
        if weburl:
            # noinspection PyTypeChecker,PyCallByClass,PyCallByClass
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(weburl))

    @QtCore.pyqtSlot()
    def doOpenDiagramProperties(self) -> None:
        """
        Executed when scene properties needs to be displayed.
        """
        diagram = self.sender().data() or self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            properties = self.pf.create(diagram)
            properties.open()

    @QtCore.pyqtSlot()
    def doOpenNodeProperties(self) -> None:
        """
        Executed when node properties needs to be displayed.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(diagram.selectedNodes())
            if node:
                properties = self.pf.create(diagram, node)
                properties.open()

    @QtCore.pyqtSlot(AbstractNode)
    def doOpenIRIBuilder(self, node: AbstractNode) -> None:
        """
        Executed when an IRI must be associated to an empty node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            if not node:
                node = first(diagram.selectedNodes())
            if node:
                builder = IriBuilderDialog(node, diagram, self)
                builder.open()

    @QtCore.pyqtSlot(FacetNode)
    def doOpenConstrainingFacetBuilder(self, node: FacetNode) -> None:
        """
        Executed when a facet must be associated to a node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            if not node:
                node = first(diagram.selectedNodes())
            if node:
                builder = ConstrainingFacetDialog(node, diagram, self)
                builder.open()

    @QtCore.pyqtSlot(LiteralNode)
    def doOpenLiteralBuilder(self, node: LiteralNode) -> None:
        """
        Executed when a literal must be associated to a node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            if not node:
                node = first(diagram.selectedNodes())
            if node:
                builder = LiteralDialog(node, diagram, self)
                builder.open()

    @QtCore.pyqtSlot()
    def doOpenIRIDialog(self, node=None):
        """
        Executed when the IRI associated to a node might be modified by the user.
        """
        # TODO: Merge with doOpenIRIBuilder
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = diagram.selectedNodes()
            # node = None
            if not node:
                if len(selected) == 1:
                    node = first(selected)
            if node:
                builder = IriBuilderDialog(node, diagram, self)
                # connect(builder.sgnIRIChanged, self.project.doSingleSwitchIRI)
                builder.open()

    @QtCore.pyqtSlot()
    def doOpenIRIFontDialog(self) -> None:
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(diagram.selectedNodes())
            if node:
                dialog = FontDialog(self, node, refactor=True)
                dialog.open()

    @QtCore.pyqtSlot()
    def doOpenNodeFontDialog(self) -> None:
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(diagram.selectedNodes())
            if node:
                dialog = FontDialog(self, node)
                dialog.open()

    @QtCore.pyqtSlot()
    def doOpenFacetDialog(self) -> None:
        """
        Executed when the Facet associated to a node might be modified by the user.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(diagram.selectedNodes())
            if node:
                builder = ConstrainingFacetDialog(node, diagram, self)
                builder.open()

    @QtCore.pyqtSlot()
    def doOpenLiteralDialog(self) -> None:
        """
        Executed when the Literal associated to a node might be modified by the user.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(diagram.selectedNodes())
            if node:
                builder = LiteralDialog(node, diagram, self)
                builder.open()

    @QtCore.pyqtSlot()
    def doOpenIRIPropsBuilder(self) -> None:
        """
        Executed when IRI props builder needs to be displayed.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = diagram.selectedNodes()
            node = None
            iri = None
            if len(selected) == 1:
                node = first(selected)
            if isinstance(node, PredicateNodeMixin):
                iri = node.iri
            if iri:
                builder = IriPropsDialog(iri, self)
                connect(builder.sgnIRISwitch, self.project.doSwitchIRI)
                # connect(builder.sgnReHashIRI, self.project.doReHashIRI)
                builder.open()

    @QtCore.pyqtSlot()
    def doOpenIRIPropsAnnotationBuilder(self) -> None:
        """
        Executed when IRI props builder needs to be displayed with focus on annotation assertions.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = diagram.selectedNodes()
            node = None
            iri = None
            if len(selected) == 1:
                node = first(selected)
            if isinstance(node, PredicateNodeMixin):
                iri = node.iri
            if iri:
                builder = IriPropsDialog(iri, self, True)
                connect(builder.sgnIRISwitch, self.project.doSwitchIRI)
                # connect(builder.sgnReHashIRI, self.project.doReHashIRI)
                builder.open()

    @QtCore.pyqtSlot(IRI)
    def doOpenAnnotationAssertionBuilder(self, iri: IRI = None, assertion: AnnotationAssertion = None,):
        """
        Executed when annotation assertion builder needs to be displayed.
        """
        builder = AnnotationAssertionBuilderDialog(self, iri, assertion)
        builder.open()
        return builder

    @QtCore.pyqtSlot()
    def doOpenEdgePropsAnnotationBuilder(self) -> None:
        """
        Executed when annotation builder needs to be displayed.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            edge = first(diagram.selectedEdges(lambda x: isinstance(x, AxiomEdge)))
            if edge:
                builder = EdgeAxiomDialog(edge, self)
                builder.open()

    @QtCore.pyqtSlot(AxiomEdge)
    def doOpenAnnotationBuilder(self, edge: AxiomEdge, annotation: AnnotationAssertion = None):
        """
        Executed when annotation builder needs to be displayed.
        """
        if edge:
            builder = AnnotationBuilderDialog(edge, self, annotation)
            builder.open()
            return builder
        else:
            diagram = self.mdi.activeDiagram()
            if diagram:
                diagram.setMode(DiagramMode.Idle)
                edge = first(diagram.selectedEdges(lambda x: isinstance(x, AxiomEdge)))
                if edge:
                    builder = AnnotationBuilderDialog(edge, self, annotation)
                    builder.open()

    @QtCore.pyqtSlot(ImportedOntology)
    def doOpenImportOntologyWizard(self, importedOntology: ImportedOntology = None):
        """
        Executed when annotation assertion builder needs to be displayed.
        :type node: IRI
        """
        builder = ImportOntologyDialog(self, importedOntology)
        builder.open()
        return builder

    @QtCore.pyqtSlot()
    def doPaste(self) -> None:
        """
        Paste previously copied items.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            if not self.clipboard.empty():
                self.clipboard.paste(diagram, diagram.mp_Pos)

    @QtCore.pyqtSlot()
    def doPrint(self) -> None:
        """
        Print the active diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            worker = PrinterDiagramExporter(diagram, self)
            worker.run()

    @QtCore.pyqtSlot()
    def doPurge(self) -> None:
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
                collection.extend([x for item in collection if item.isNode()
                                   for x in item.edges if x not in collection])
                self.undostack.push(CommandItemsRemove(diagram, collection))

    @QtCore.pyqtSlot()
    def doQuit(self) -> None:
        """
        Quit Eddy.
        """
        self.close()
        self.sgnQuit.emit()

    @QtCore.pyqtSlot()
    def doRefactorBrush(self) -> None:
        """
        Change the node brush for all the predicate nodes matching the selected predicate.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode,
                                        Item.IndividualNode,
                                        Item.ConceptNode, Item.IndividualNode,
                                        Item.RoleNode, Item.AttributeNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                action = self.sender()
                color = action.data()
                if isinstance(node, PredicateNodeMixin):
                    nodes = self.project.iriOccurrences(node.type(), node.iri)
                else:
                    nodes = self.project.predicates(node.type(), node.text())
                self.undostack.push(
                    CommandNodeSetBrush(diagram, nodes, QtGui.QBrush(QtGui.QColor(color.value)))
                )

    # TODO TO BE REMOVED
    @QtCore.pyqtSlot()
    def doRefactorName(self):
        """
        Rename all the instance of the selected predicate node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode,
                                        Item.IndividualNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                dialog = RefactorNameForm(node, self)
                dialog.exec_()

    @QtCore.pyqtSlot()
    def doRelocateLabel(self) -> None:
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
    def doRemoveBreakpoint(self) -> None:
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
    def doRemoveAllBreakpoints(self) -> None:
        """
        Focus on the source node of the selected edge.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = diagram.selectedEdges()
            if len(selected) == 1:
                edge = selected[0]
                breakpoints = edge.breakpoints
                while breakpoints:
                    remove = CommandEdgeBreakpointRemove(diagram, edge, 0)
                    self.undostack.push(remove)


    @QtCore.pyqtSlot()
    def doRemoveDiagram(self) -> None:
        """
        Removes a diagram from the current project.
        """
        action = self.sender()
        diagram = action.data()
        if diagram:
            self.undostack.push(CommandDiagramRemove(diagram, self.project))

    @QtCore.pyqtSlot()
    def doRenameDiagram(self) -> None:
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
    def doRenameProject(self) -> None:
        """
        Renames a project.
        """
        action = self.sender()
        project = action.data()
        if project:
            form = RenameProjectForm(project, self)
            if form.exec_() == RenameProjectForm.Accepted:
                name = form.nameField.value()
                self.undostack.push(CommandProjectRename(project.name, name, project))

    @QtCore.pyqtSlot()
    def doSave(self) -> None:
        """
        Save the current project.
        """
        currentPath = self.project.path
        try:
            if not self.project.path:
                dialog = FileDialog(self)
                dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
                dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
                dialog.setNameFilter(File.Graphol.value)
                dialog.selectFile(self.project.name)
                dialog.selectNameFilter(File.Graphol.value)
                dialog.setDefaultSuffix(File.Graphol.extension)
                if not dialog.exec_():
                    return
                self.project.path = expandPath(first(dialog.selectedFiles()))
            worker = self.createProjectExporter(File.Graphol, self.project, self)
            worker.run()
        except Exception as e:
            self.project.path = currentPath
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
    def doSaveAs(self) -> None:
        """
        Save the current project as...
        """
        currentPath = self.project.path
        try:
            dialog = FileDialog(self)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setNameFilter(File.Graphol.value)
            dialog.selectNameFilter(File.Graphol.value)
            dialog.setDefaultSuffix(File.Graphol.extension)
            if dialog.exec_():
                self.project.path = expandPath(first(dialog.selectedFiles()))
                worker = self.createProjectExporter(File.Graphol, self.project, self)
                worker.run()
        except Exception as e:
            self.project.path = currentPath
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
    def doSelectAll(self) -> None:
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
    def doSendToBack(self) -> None:
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
    def doSetNodeBrush(self) -> None:
        """
        Set the brush of selected nodes.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            color = action.data()
            brush = QtGui.QBrush(QtGui.QColor(color.value))
            supported = {Item.ConceptNode, Item.RoleNode, Item.AttributeNode,
                         Item.IndividualNode, Item.LiteralNode}
            fn = lambda x: x.type() in supported and x.brush() != brush
            selected = diagram.selectedNodes(filter_on_nodes=fn)
            if selected:
                self.undostack.push(CommandNodeSetBrush(diagram, selected, brush))

    @QtCore.pyqtSlot()
    def doSetNodeMeta(self) -> None:
        """
        Set meta values of selected nodes
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            key = action.data()
            checked = action.isChecked()
            supported = {Item.RoleNode, Item.AttributeNode}
            fn = lambda x: x.type() in supported
            selected = diagram.selectedNodes(filter_on_nodes=fn)
            if selected and len(selected) == 1:
                node = first(selected)
                undo = node.iri.getMetaProperties()
                # undo = self.project.meta(node.type(), node.text())
                redo = undo.copy()
                redo[key] = checked
                if redo != undo:
                    prop = RE_CAMEL_SPACE.sub(r'\g<1> \g<2>', key).lower()
                    name = "{0}set '{1}' {2} property".format('' if checked else 'un', node.iri,
                                                              prop)
                    self.undostack.push(
                        CommandIRISetMeta(self.project, node.type(), node.iri, undo, redo, name))
                    # self.undostack.push(CommandNodeSetMeta(self.project, node.type(), node.text(), undo, redo, name))

    @QtCore.pyqtSlot()
    def doSetPropertyRestriction(self) -> None:
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
                    self.undostack.push(
                        CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.pyqtSlot()
    def doSetDatatype(self) -> None:
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
                    self.undostack.push(
                        CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.pyqtSlot()
    def doSetFacet(self) -> None:
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
                    self.undostack.push(
                        CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.pyqtSlot()
    def doSetProfile(self) -> None:
        """
        Set the currently used project profile.
        """
        widget = self.widget('profile_switch')
        profile = widget.currentText()
        if self.project.profile.name() != profile:
            self.undostack.push(
                CommandProjectSetProfile(self.project, self.project.profile.name(), profile))
        widget.clearFocus()

    @QtCore.pyqtSlot()
    def doSnapTopGrid(self) -> None:
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
    def doSwapEdge(self) -> None:
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
    def doSwitchSameDifferentEdge(self) -> None:
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
    def doSwitchOperatorNode(self) -> None:
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
    def doSwitchRestrictionNode(self) -> None:
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
    def doProfileSyntaxCheck(self) -> None:
        """
        Perform syntax checking on the active diagram.
        """
        dialog = SyntaxValidationDialog(self.project, self)
        dialog.exec_()

    @QtCore.pyqtSlot()
    def doDLCheck(self) -> None:
        """
        Perform OWL DL check on the ontology.
        """
        dialog = OWL2DLProfileValidationDialog(self.project, self)
        dialog.exec_()

    @QtCore.pyqtSlot()
    def doShowInconsistentOntologyExplanations(self) -> None:
        """
        Show explanations for inconsistent ontology
        """
        dialog = ExplanationDialog(self, self.inconsistentOntologyExplanations)
        dialog.open()

    @QtCore.pyqtSlot()
    def doShowEmptyEntityExplanations(self) -> None:
        """
        Show explanations for empty entity
        """
        dialog = ExplanationDialog(self, self.currentEmptyEntityExplanations,
                                   entityIRI=self.currentEmptyEntityIRI,
                                   entityType=self.currentEmptyEntityType)
        dialog.open()

    @QtCore.pyqtSlot()
    def doShowInvolvingAxioms(self) -> None:
        """
        Executed when user need to visualize the OWL Axioms involving a given IRI
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            selected = diagram.selectedNodes()
            node = None
            iri = None
            if len(selected) == 1:
                node = first(selected)
            if isinstance(node, PredicateNodeMixin):
                iri = node.iri
            if iri:
                dialog = AxiomsByEntityDialog(self.project, self, iri)
                dialog.open()

    @QtCore.pyqtSlot()
    def doShowNoMatchingLabelIRIs(self) -> None:
        iris = self.project.getAllIRIsWithNoMatchingLabel()
        dialog = LabelDialog(self, iris)
        dialog.open()

    @QtCore.pyqtSlot()
    def doSelectReasoner(self) -> None:
        """
        Set the currently used project profile.
        """
        widget = self.widget('select_reasoner')
        reasoner = widget.currentText()
        widget.clearFocus()

    @QtCore.pyqtSlot()
    def doOntologyConsistencyCheck(self) -> None:
        """
        Perform Ontology Consistency checking on the active ontology/diagram.
        """
        dialog = OntologyConsistencyCheckDialog(self.project, self)
        connect(dialog.sgnUnsatisfiableEntities, self.onUnsatisfiableEntities)
        connect(dialog.sgnOntologyInconsistent, self.onInconsistentOntology)
        connect(dialog.sgnUnsatisfiableClass, self.onUnsatisfiableClass)
        connect(dialog.sgnUnsatisfiableObjectProperty, self.onUnsatisfiableObjectProperty)
        connect(dialog.sgnUnsatisfiableDataProperty, self.onUnsatisfiableDataProperty)
        self.sgnConsistencyCheckStarted.emit()
        dialog.exec_()

    @QtCore.pyqtSlot()
    def doEmptyEntityExplanation(self) -> None:
        """
        Compute explanation for entity emptiness
        """
        if self.currentEmptyEntityIRI and self.currentEmptyEntityType:
            key = '{}-{}'.format(str(self.currentEmptyEntityIRI), self.currentEmptyEntityType)
            if key in self.emptyEntityExplanations:
                self.currentEmptyEntityExplanations = self.emptyEntityExplanations[key]
                self.doShowEmptyEntityExplanations()
            else:
                dialog = EmptyEntityDialog(self.project, self, self.currentEmptyEntityIRI,
                                           self.currentEmptyEntityType)
                connect(dialog.sgnExplanationComputed, self.onNewEmptyEntityExplanation)
                dialog.exec_()

    @QtCore.pyqtSlot()
    def onNewEmptyEntityExplanation(self) -> None:
        """
        Executed when new explanations for empty entities are computed
        """
        self.doShowEmptyEntityExplanations()

    @QtCore.pyqtSlot(IRI)
    def onUnsatisfiableClass(self, iri: IRI) -> None:
        self.sgnUnsatisfiableClass.emit(iri)

    @QtCore.pyqtSlot(IRI)
    def onUnsatisfiableObjectProperty(self, iri: IRI) -> None:
        self.sgnUnsatisfiableObjectProperty.emit(iri)

    @QtCore.pyqtSlot(IRI)
    def onUnsatisfiableDataProperty(self, iri: IRI) -> None:
        self.sgnUnsatisfiableDataProperty.emit(iri)

    @QtCore.pyqtSlot()
    def onInconsistentOntology(self) -> None:
        """
        Executed when the consistency check reports that the ontology is inconsistent.
        """
        self.action('reset_reasoner').setEnabled(True)
        self.action('inconsistency_explanations').setEnabled(True)
        self.sgnInconsistentOntology.emit()

    @QtCore.pyqtSlot(int)
    def onUnsatisfiableEntities(self, unsatCount: int) -> None:
        """
        Executed when the consistency check reports that the ontology is consistent.
        """
        self.action('reset_reasoner').setEnabled(True)
        self.sgnUnsatisfiableEntities.emit(unsatCount)

    @QtCore.pyqtSlot()
    def doOpenOntologyExplorer(self) -> None:
        """
        Perform Ontology Consistency checking on the active ontology/diagram.
        """
        # dialog = OntologyExplorerDialog(self.project, self)
        from eddy.ui.ontology import OntologyManagerDialog
        dialog = OntologyManagerDialog(self)
        dialog.exec_()

    @QtCore.pyqtSlot()
    def doResetConsistencyCheck(self) -> None:
        """
        Signals to reset the status of the project after the consistency check.
        """
        self.action('reset_reasoner').setEnabled(False)
        self.action('inconsistency_explanations').setEnabled(False)
        self.inconsistentOntologyExplanations = list()
        self.currentEmptyEntityType = None
        self.currentEmptyEntityIRI = None
        self.currentEmptyEntityExplanations = list()
        self.emptyEntityExplanations = {}
        self.sgnConsistencyCheckReset.emit()

    @QtCore.pyqtSlot()
    def doToggleGrid(self) -> None:
        """
        Toggle snap to grid setting and viewport display.
        """
        settings = QtCore.QSettings()
        settings.setValue('diagram/grid', self.action('toggle_grid').isChecked())
        settings.sync()
        for subwindow in self.mdi.subWindowList():
            subwindow.view.setGridSize(Diagram.GridSize)
            viewport = subwindow.view.viewport()
            viewport.update()

    @QtCore.pyqtSlot()
    def doUpdateState(self) -> None:
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
        isProfileOWL2QL = self.project.profile.type() is OWL2Profiles.OWL2QL
        isProfileOWL2RL = self.project.profile.type() is OWL2Profiles.OWL2RL
        isPropertyFunctionalEnabled = False
        isPropertyInvFunctionalEnabled = False
        isPropertySymmetricEnabled = False
        isPropertyAsymmetricEnabled = False
        isPropertyReflexiveEnabled = False
        isPropertyIrreflexiveEnabled = False
        isPropertyTransitiveEnabled = False
        isPropertyFunctionalChecked = False
        isPropertyInvFunctionalChecked = False
        isPropertySymmetricChecked = False
        isPropertyAsymmetricChecked = False
        isPropertyReflexiveChecked = False
        isPropertyIrreflexiveChecked = False
        isPropertyTransitiveChecked = False
        isSwitchToSameEnabled = not isProfileOWL2QL
        isSwitchToDifferentEnabled = True
        isProjectEmpty = self.project.isEmpty()
        isUndoStackClean = self.undostack.isClean()
        isDiagramSwitchEnabled = False
        isSessionSwitchEnabled = len(self.app.sessions) > 1

        if self.mdi.subWindowList():
            diagram = self.mdi.activeDiagram()
            restrictables = {Item.AttributeNode, Item.RoleNode}
            predicates = {Item.ConceptNode, Item.AttributeNode, Item.RoleNode,
                          Item.IndividualNode}
            if diagram:
                nodes = diagram.selectedNodes()
                edges = diagram.selectedEdges()
                isDiagramActive = True
                isDiagramSwitchEnabled = len(self.mdi.subWindowList()) > 1
                isClipboardEmpty = self.clipboard.empty()
                isEdgeSelected = first(edges) is not None
                isNodeSelected = first(nodes) is not None
                isDomainRangeUsable = any([x.type() in restrictables for x in nodes])
                isPredicateSelected = any([x.type() in predicates for x in nodes])
                isRestrictable = len(nodes) == 1 and first(nodes).type() in restrictables
                isRoleSelected = isRestrictable and first(nodes).type() is Item.RoleNode
                if isRestrictable:
                    # meta = self.project.meta(first(nodes).type(), first(nodes).text())
                    firstNode = first(nodes)
                    meta = firstNode.iri.getMetaProperties()
                    isPropertyFunctionalChecked = meta.get(K_FUNCTIONAL, False)
                    isPropertyInvFunctionalChecked = meta.get(K_INVERSE_FUNCTIONAL, False)
                    isPropertySymmetricChecked = meta.get(K_SYMMETRIC, False)
                    isPropertyAsymmetricChecked = meta.get(K_ASYMMETRIC, False)
                    isPropertyReflexiveChecked = meta.get(K_REFLEXIVE, False)
                    isPropertyIrreflexiveChecked = meta.get(K_IRREFLEXIVE, False)
                    isPropertyTransitiveChecked = meta.get(K_TRANSITIVE, False)
                    isPropertyFunctionalEnabled = isPropertyFunctionalChecked or not isProfileOWL2QL
                    if isRoleSelected:
                        isPropertyInvFunctionalEnabled = isPropertyInvFunctionalChecked or not isProfileOWL2QL
                        isPropertySymmetricEnabled = True
                        isPropertyAsymmetricEnabled = True
                        isPropertyReflexiveEnabled = isPropertyReflexiveChecked or not isProfileOWL2RL
                        isPropertyIrreflexiveEnabled = True
                        isPropertyTransitiveEnabled = isPropertyTransitiveChecked or not isProfileOWL2QL
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
        self.action('export_diagrams').setEnabled(not isProjectEmpty)
        self.action('paste').setEnabled(not isClipboardEmpty)
        self.action('print').setEnabled(isDiagramActive)
        self.action('property_domain').setEnabled(isDomainRangeUsable)
        self.action('property_domain_range').setEnabled(isDomainRangeUsable)
        self.action('property_range').setEnabled(isDomainRangeUsable)
        self.action('property_functional').setChecked(isPropertyFunctionalChecked)
        self.action('property_functional').setEnabled(isPropertyFunctionalEnabled)
        self.action('property_inverse_functional').setChecked(isPropertyInvFunctionalChecked)
        self.action('property_inverse_functional').setEnabled(isPropertyInvFunctionalEnabled)
        self.action('property_symmetric').setChecked(isPropertySymmetricChecked)
        self.action('property_symmetric').setEnabled(isPropertySymmetricEnabled)
        self.action('property_asymmetric').setChecked(isPropertyAsymmetricChecked)
        self.action('property_asymmetric').setEnabled(isPropertyAsymmetricEnabled)
        self.action('property_reflexive').setChecked(isPropertyReflexiveChecked)
        self.action('property_reflexive').setEnabled(isPropertyReflexiveEnabled)
        self.action('property_irreflexive').setChecked(isPropertyIrreflexiveChecked)
        self.action('property_irreflexive').setEnabled(isPropertyIrreflexiveEnabled)
        self.action('property_transitive').setChecked(isPropertyTransitiveChecked)
        self.action('property_transitive').setEnabled(isPropertyTransitiveEnabled)
        self.action('save').setEnabled(not isUndoStackClean)
        self.action('select_all').setEnabled(isDiagramActive)
        self.action('send_to_back').setEnabled(isNodeSelected)
        self.action('snap_to_grid').setEnabled(isDiagramActive)
        self.action('syntax_check').setEnabled(not isProjectEmpty)
        self.action('dl_check').setEnabled(not isProjectEmpty)
        self.action('swap_edge').setEnabled(isEdgeSelected and isEdgeSwapEnabled)
        self.action('focus_on_source').setEnabled(isEdgeSelected)
        self.action('focus_on_target').setEnabled(isEdgeSelected)
        self.action('remove_all_breakpoints').setEnabled(isEdgeSelected)
        self.action('switch_same_to_different').setEnabled(isSwitchToDifferentEnabled)
        self.action('switch_different_to_same').setEnabled(isSwitchToSameEnabled)
        self.action('toggle_grid').setEnabled(isDiagramActive)
        self.action('next_project_window').setEnabled(isSessionSwitchEnabled)
        self.action('previous_project_window').setEnabled(isSessionSwitchEnabled)
        self.action('focus_active_tab').setEnabled(isDiagramActive)
        self.action('next_tab').setEnabled(isDiagramSwitchEnabled)
        self.action('previous_tab').setEnabled(isDiagramSwitchEnabled)
        self.action('close_tab').setEnabled(isDiagramActive)
        self.action('close_other_tabs').setEnabled(isDiagramSwitchEnabled)
        self.action('close_all_tabs').setEnabled(isDiagramSwitchEnabled)
        self.widget('button_set_brush').setEnabled(isPredicateSelected)
        self.widget('profile_switch').setCurrentText(self.project.profile.name())
        self.widget('select_reasoner').setEnabled(not isProjectEmpty)
        # self.action('reset_reasoner').setEnabled(not isProjectEmpty)
        self.action('ontology_consistency_check').setEnabled(not isProjectEmpty)
        self.setWindowTitle(self.project)

    @QtCore.pyqtSlot()
    def doRenderByFullIRI(self) -> None:
        """
        Render ontology elements by full IRIs
        """
        with BusyProgressDialog('Switching label rendering', parent=self):
            settings = QtCore.QSettings()
            settings.setValue('ontology/iri/render', IRIRender.FULL.value)
            self.action(objectName='render_full_iri').setChecked(True)
            self.action(objectName='render_prefixed_iri').setChecked(False)
            self.action(objectName='render_simple_name').setChecked(False)
            for langTag in self.project.getLanguages():
                actionObjName = 'render_label_{}'.format(langTag)
                self.action(objectName=actionObjName).setChecked(False)
            for node in self.project.nodes():
                if isinstance(node, PredicateNodeMixin):
                    node.doUpdateNodeLabel()
            self.sgnRenderingModified.emit(IRIRender.FULL.value)

    @QtCore.pyqtSlot()
    def doRenderByPrefixedIRI(self) -> None:
        """
        Render ontology elements by prefixed IRIs
        """
        with BusyProgressDialog('Switching label rendering', parent=self):
            settings = QtCore.QSettings()
            settings.setValue('ontology/iri/render', IRIRender.PREFIX.value)
            self.action(objectName='render_full_iri').setChecked(False)
            self.action(objectName='render_prefixed_iri').setChecked(True)
            self.action(objectName='render_simple_name').setChecked(False)
            for langTag in self.project.getLanguages():
                actionObjName = 'render_label_{}'.format(langTag)
                self.action(objectName=actionObjName).setChecked(False)
            for node in self.project.nodes():
                if isinstance(node, PredicateNodeMixin):
                    node.doUpdateNodeLabel()
            self.sgnRenderingModified.emit(IRIRender.PREFIX.value)

    @QtCore.pyqtSlot()
    def doRenderBySimpleName(self) -> None:
        """
        Render ontology elements by prefixed IRIs
        """
        with BusyProgressDialog('Switching label rendering', parent=self):
            settings = QtCore.QSettings()
            settings.setValue('ontology/iri/render', IRIRender.SIMPLE_NAME.value)
            self.action(objectName='render_full_iri').setChecked(False)
            self.action(objectName='render_prefixed_iri').setChecked(False)
            self.action(objectName='render_simple_name').setChecked(True)
            # self.action(objectName='render_label').setChecked(False)
            for langTag in self.project.getLanguages():
                actionObjName = 'render_label_{}'.format(langTag)
                self.action(objectName=actionObjName).setChecked(False)
            for node in self.project.nodes():
                if isinstance(node, PredicateNodeMixin):
                    node.doUpdateNodeLabel()
        self.sgnRenderingModified.emit(IRIRender.SIMPLE_NAME.value)

    @QtCore.pyqtSlot()
    def doRenderByLabel(self) -> None:
        """
        Render ontology elements by prefixed IRIs
        """
        with BusyProgressDialog('Switching label rendering', parent=self):
            action = self.sender()
            lang = action.data()
            settings = QtCore.QSettings()
            settings.setValue('ontology/iri/render', IRIRender.LABEL.value)
            settings.setValue('ontology/iri/render/language', lang)
            self.action(objectName='render_full_iri').setChecked(False)
            self.action(objectName='render_prefixed_iri').setChecked(False)
            self.action(objectName='render_simple_name').setChecked(False)
            # self.action(objectName='render_label').setChecked(True)
            for langTag in self.project.getLanguages():
                actionObjName = 'render_label_{}'.format(langTag)
                self.action(objectName=actionObjName).setChecked(langTag == lang)
            for node in self.project.nodes():
                if isinstance(node, (PredicateNodeMixin, FacetNode)):
                    node.doUpdateNodeLabel()
            self.sgnRenderingModified.emit(IRIRender.LABEL.value)

    @QtCore.pyqtSlot()
    def onNoUpdateAvailable(self) -> None:
        """
        Executed when the update worker thread terminates and no software update is available.
        """
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('')
        progressBar.setVisible(False)
        self.addNotification('No update available.')

    @QtCore.pyqtSlot()
    def onNoUpdateDataAvailable(self) -> None:
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
    def onProjectSaved(self) -> None:
        """
        Executed when the current project is saved.
        """
        # UPDATE WINDOW TITLE
        self.setWindowTitle(self.project)
        # UPDATE RECENT PROJECTS
        settings = QtCore.QSettings()
        projects = [self.project.path]
        for path in map(expandPath, settings.value('project/recent', None, str) or []):
            if fexists(path) and path not in projects:
                projects.append(path)
        settings.setValue('project/recent', projects)
        settings.sync()

    @QtCore.pyqtSlot()
    def onSessionReady(self) -> None:
        """
        Executed when the session is initialized.
        """
        # CREATE SESSION SWITCH ACTIONS
        for session in self.app.sessions:
            self.onSessionCreated(session)
        # CONNECT PROJECT SPECIFIC SIGNALS
        connect(self.project.sgnDiagramRemoved, self.mdi.onDiagramRemoved)
        connect(self.project.sgnUpdated, self.doUpdateState)
        # CHECK FOR UPDATES ON STARTUP
        settings = QtCore.QSettings()
        if settings.value('update/check_on_startup', True, bool):
            action = self.action('check_for_updates')
            action.trigger()
        if (
            self.projectFromFile
            and self.owlOntologyImportSize > 0
            and self.owlOntologyImportSize != self.owlOntologyImportLoadedCount
        ):
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setDetailedText(
                '{} OWL 2 ontologies declared as imports have not been loaded. '
                'Please open the ontology manager for more details and to retry loading'
                .format(self.owlOntologyImportSize - self.owlOntologyImportLoadedCount))
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
            msgbox.setText('Eddy could not correctly load some of '
                           'the declared OWL ontology imports')
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Problem managing OWL ontology import declaration(s)')
            msgbox.exec_()

    @QtCore.pyqtSlot(QtWidgets.QMainWindow)
    def onSessionCreated(self, session: QtWidgets.QMainWindow) -> None:
        """
        Executed when a new session is created.
        """
        if session:
            # noinspection PyArgumentList
            action = QtWidgets.QAction(session.project.name, self,
                                       triggered=self.app.doFocusSession)
            action.setIconVisibleInMenu(True)
            action.setData(session)
            self.action('sessions').addAction(action)
            if session == self:
                # DRAW A CHECK MARK NEAR THE CURRENT SESSION
                pixmap = QtGui.QPixmap(18, 18)
                pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(pixmap)
                painter.setPen(QtCore.Qt.black)
                painter.drawText(QtCore.QRectF(pixmap.rect()), QtCore.Qt.AlignCenter, '\u2713')
                painter.end()
                action.setIcon(QtGui.QIcon(pixmap))
            self.menu('window').addAction(action)
            self.sgnUpdateState.emit()

    @QtCore.pyqtSlot(QtWidgets.QMainWindow)
    def onSessionClosed(self, session: QtWidgets.QMainWindow) -> None:
        """
        Executed when a session is closed.
        """
        if session:
            # REMOVE THE CORRESPONDING ACTION FROM THE MENU BAR
            action = first(self.action('sessions').actions(),
                           filter_on_item=lambda i: i.data() == session)
            if action:
                self.action('sessions').removeAction(action)
            self.sgnUpdateState.emit()

    @QtCore.pyqtSlot(str, str)
    def onUpdateAvailable(self, name: str, url: str):
        """
        Executed when the update worker thread terminates and a new software update is available.

        :param name: Name of the update version
        :param url: URL of the update download
        """
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('')
        progressBar.setVisible(False)
        self.addNotification(textwrap.dedent("""
            A new version of {} is available for download: <a href="{}"><b>{}</b></a>""".format(
            APPNAME, url, name)))

    #############################################
    #   EVENTS
    #################################

    def closeEvent(self, closeEvent: QtGui.QCloseEvent) -> None:
        """
        Executed when the main window is closed.
        """
        close = True
        save = False
        if not self.undostack.isClean():
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_help_outline_black').pixmap(48))
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
                self.sgnNoSaveProject.emit()
            elif msgbox.result() == QtWidgets.QMessageBox.Yes:
                save = True

        if not close:
            closeEvent.ignore()
        else:
            # SAVE THE CURRENT PROJECT IF NEEDED
            if save:
                self.sgnSaveProject.emit()
            # DISPOSE ALL THE PLUGINS
            for plugin in self.plugins():
                self.pmanager.dispose(plugin)
            self.pmanager.clear()
            # DISPOSE ALL THE RUNNING THREADS
            self.stopRunningThreads()
            # HIDE ALL THE NOTIFICATION POPUPS
            self.hideNotifications()
            # SHUTDOWN THE ACTIVE SESSION
            self.sgnClosed.emit()
            closeEvent.accept()

            LOGGER.info('Session shutdown completed: %s v%s [%s]', APPNAME, VERSION,
                        self.project.name)

    def keyPressEvent(self, keyEvent: QtGui.QKeyEvent) -> None:
        """
        Executed when a keyboard button is pressed
        """
        if IS_MACOS:
            if keyEvent.key() == QtCore.Qt.Key_Backspace:
                action = self.action('delete')
                action.trigger()
        super().keyPressEvent(keyEvent)

    def keyReleaseEvent(self, keyEvent: QtGui.QKeyEvent) -> None:
        """
        Executed when a keyboard button is released.
        """
        if keyEvent.key() == QtCore.Qt.Key_Control:
            diagram = self.mdi.activeDiagram()
            if diagram and not diagram.isEdgeAdd():
                diagram.setMode(DiagramMode.Idle)
        super().keyReleaseEvent(keyEvent)

    def showEvent(self, showEvent: QtGui.QShowEvent) -> None:
        """
        Executed when the window is shown.
        """
        self.setWindowState(
            (self.windowState() & ~QtCore.Qt.WindowMinimized) | QtCore.Qt.WindowActive)
        self.activateWindow()
        self.raise_()

    #############################################
    #   INTERFACE
    #################################

    def createDiagramView(self, diagram: Diagram) -> DiagramView:
        """
        Create a new diagram view displaying the given diagram.
        """
        view = DiagramView(diagram, self)
        view.centerOn(0, 0)
        return view

    def createMdiSubWindow(self, widget: QtWidgets.QWidget) -> MdiSubWindow:
        """
        Create a subwindow in the MDI area that displays the given widget.
        """
        subwindow = MdiSubWindow(widget)
        subwindow = self.mdi.addSubWindow(subwindow)
        subwindow.showMaximized()
        return subwindow

    def save(self) -> None:
        """
        Save the current session state.
        """
        settings = QtCore.QSettings()
        settings.setValue('session/geometry', self.saveGeometry())
        settings.setValue('session/state', self.saveState())
        settings.sync()

    def setWindowTitle(self, project: Project, diagram: Diagram = None) -> None:
        """
        Set the main window title.
        """
        title = project.name if not project.path else '{0} - [{1}]'.format(project.name,
                                                                           shortPath(project.path))
        if diagram:
            title = '{0} - {1}'.format(diagram.name, title)
        super().setWindowTitle(title)
