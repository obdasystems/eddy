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


import json
import os
import textwrap

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from rdflib import (
    DCAT,
    DCTERMS,
    Literal,
    RDF,
    URIRef,
)

from eddy import BUG_TRACKER
from eddy.core.common import (
    HasThreadingSystem,
    HasWidgetSystem,
)
from eddy.core.datatypes.graphol import (
    Identity,
    Item,
    Restriction,
)
from eddy.core.datatypes.owl import (
    Datatype,
    OWLAxiom,
    OWLSyntax,
)
from eddy.core.datatypes.system import File
from eddy.core.diagram import DiagramMalformedError
from eddy.core.exporters.common import AbstractOntologyExporter
from eddy.core.functions.fsystem import (
    fwrite,
    fremove,
)
from eddy.core.functions.misc import (
    clamp,
    first,
)
from eddy.core.functions.misc import format_exception
from eddy.core.functions.owl import (
    OWLFunctionalSyntaxDocumentFilter,
    OWLManchesterSyntaxDocumentFilter,
    RDFXMLDocumentFilter,
    TurtleDocumentFilter,
)
from eddy.core.functions.path import (
    expandPath,
    openPath,
)
from eddy.core.functions.signals import connect
from eddy.core.jvm import getJavaVM
from eddy.core.metadata import (
    LiteralValue,
    NamedEntity,
)
from eddy.core.ndc import (
    ADMS,
    NDCDataset,
)
from eddy.core.network import NetworkManager
from eddy.core.output import getLogger
from eddy.core.owl import (
    OWL2Datatype,
    OWL2Facet,
)
from eddy.core.worker import AbstractWorker
from eddy.ui.dialogs import DiagramSelectionDialog
from eddy.ui.fields import (
    ComboBox,
    CheckBox,
)

# from eddy.ui.progress import BusyProgressDialog
# from eddy.ui.syntax import SyntaxValidationWorker

LOGGER = getLogger()


class OWLOntologyExporter(AbstractOntologyExporter, HasThreadingSystem):
    """
    Extends AbstractProjectExporter with facilities to export a Graphol project into a valid OWL 2 ontology.
    """
    def __init__(self, project, session=None, **kwargs):
        """
        Initialize the OWL Project exporter
        :type project: Project
        :type session: Session
        """
        super().__init__(project, session)
        self.items = list(project.edges()) + list(filter(lambda n: not n.adjacentNodes(), project.nodes()))
        self.path = None
        self.progress = None
        self.diagrams = kwargs.get('diagrams', None)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onSyntaxCheckCompleted(self):
        """
        Executed when the syntax validation procedure is completed.
        """
        self.progress.sleep()
        self.progress.close()
        dialog = OWLOntologyExporterDialog(self.project, self.path, self.session, self.diagrams)
        dialog.exec_()

    @QtCore.pyqtSlot(str)
    def onSyntaxCheckErrored(self, _):
        """
        Executed when a syntax error is detected.
        :type _: str
        """
        self.progress.sleep()
        self.progress.close()
        msgbox = QtWidgets.QMessageBox(self.session)
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
        msgbox.setText('One or more syntax errors have been detected. '
                       'Please run the syntax validation utility before exporting the OWL 2 ontology.')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Syntax error detected!')
        msgbox.exec_()

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Owl

    def run(self, path):
        """
        Perform OWL ontology generation.
        :type path: str
        """
        # DIAGRAM SELECTION
        if self.diagrams is None:
            if not self.project.isEmpty():
                dialog = DiagramSelectionDialog(self.session)
                if not dialog.exec_():
                    return
                self.diagrams = dialog.selectedDiagrams()
            else:
                self.diagrams = self.project.diagrams()
        self.path = path
        # DISABLE SYNTAX CHECK
        # self.progress = BusyProgressDialog('Performing syntax check...')
        # self.progress.show()
        # worker = SyntaxValidationWorker(0, self.items, self.project)
        # connect(worker.sgnCompleted, self.onSyntaxCheckCompleted)
        # connect(worker.sgnSyntaxError, self.onSyntaxCheckErrored)
        # self.startThread('syntaxCheck', worker)
        dialog = OWLOntologyExporterDialog(self.project, self.path, self.session, self.diagrams)
        dialog.exec_()


class OWLOntologyExporterDialog(QtWidgets.QDialog, HasThreadingSystem, HasWidgetSystem):
    """
    Extends QtWidgets.QDialog providing the form used to perform Graphol -> OWL ontology translation.
    """
    def __init__(self, project, path, session, diagrams):
        """
        Initialize the form dialog.
        :type project: Project
        :type path: str
        :type session: Session
        """
        super().__init__(session)

        self.path = expandPath(path)
        self.project = project

        settings = QtCore.QSettings()

        self.diagrams = diagrams

        #############################################
        # MAIN FORM AREA
        #################################

        ## SYNTAX
        field = ComboBox(self)
        for syntax in OWLSyntax:
            field.addItem(syntax.value, syntax)
        field.setCurrentIndex(0)
        # TRY PRESET SYNTAX FIELD BASED ON FILE EXTENSION
        if self.path:
            if self.path.endswith('.ttl'):
                field.setCurrentIndex(field.findData(OWLSyntax.Turtle))
            elif self.path.endswith('.omn'):
                field.setCurrentIndex(field.findData(OWLSyntax.Manchester))
            elif self.path.endswith('.owx'):
                field.setCurrentIndex(field.findData(OWLSyntax.RDF))
            elif self.path.endswith('.ofn'):
                field.setCurrentIndex(field.findData(OWLSyntax.Functional))
        field.setObjectName('syntax_field')
        field.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.addWidget(field)

        syntaxLayout = QtWidgets.QVBoxLayout()
        syntaxLayout.addWidget(field)
        syntaxGroup = QtWidgets.QGroupBox('Syntax', self)
        syntaxGroup.setLayout(syntaxLayout)

        ## AXIOMS
        self.addWidget(QtWidgets.QPushButton('All', self,
                                             clicked=self.doCheckAxiomMarks,
                                             objectName='btn_check_all'))
        self.addWidget(QtWidgets.QPushButton('Clear', self,
                                             clicked=self.doCheckAxiomMarks,
                                             objectName='btn_clear_all'))
        for axiom in OWLAxiom:
            self.addWidget(CheckBox(axiom.value, self,
                                    enabled=False, objectName=axiom.value,
                                    checked=False, clicked=self.onAxiomCheckClicked))

        nonLogicalLayout = QtWidgets.QGridLayout()
        nonLogicalLayout.setColumnMinimumWidth(0, 230)
        nonLogicalLayout.setColumnMinimumWidth(1, 230)
        nonLogicalLayout.setColumnMinimumWidth(2, 230)
        nonLogicalLayout.addWidget(self.widget(OWLAxiom.Annotation.value), 0, 0)
        nonLogicalLayout.addWidget(self.widget(OWLAxiom.Declaration.value), 0, 1)
        nonLogicalLayout.addWidget(QtWidgets.QWidget(self), 0, 2)
        nonLogicalGroup = QtWidgets.QGroupBox('Non-Logical', self)
        nonLogicalGroup.setLayout(nonLogicalLayout)
        intensionalLayout = QtWidgets.QGridLayout()
        intensionalLayout.setColumnMinimumWidth(0, 230)
        intensionalLayout.setColumnMinimumWidth(1, 230)
        intensionalLayout.setColumnMinimumWidth(2, 230)
        intensionalLayout.addWidget(self.widget(OWLAxiom.AsymmetricObjectProperty.value), 0, 0)
        intensionalLayout.addWidget(self.widget(OWLAxiom.DataPropertyDomain.value), 1, 0)
        intensionalLayout.addWidget(self.widget(OWLAxiom.DataPropertyRange.value), 2, 0)
        intensionalLayout.addWidget(self.widget(OWLAxiom.DisjointClasses.value), 3, 0)
        intensionalLayout.addWidget(self.widget(OWLAxiom.DisjointDataProperties.value), 4, 0)
        intensionalLayout.addWidget(self.widget(OWLAxiom.DisjointObjectProperties.value), 5, 0)
        intensionalLayout.addWidget(self.widget(OWLAxiom.EquivalentClasses.value), 6, 0)
        intensionalLayout.addWidget(self.widget(OWLAxiom.EquivalentDataProperties.value), 7, 0)
        intensionalLayout.addWidget(self.widget(OWLAxiom.EquivalentObjectProperties.value), 0, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.FunctionalDataProperty.value), 1, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.FunctionalObjectProperty.value), 2, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.HasKey.value), 3, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.InverseFunctionalObjectProperty.value), 4, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.InverseObjectProperties.value), 5, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.IrreflexiveObjectProperty.value), 6, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.ObjectPropertyDomain.value), 7, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.ObjectPropertyRange.value), 0, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.ReflexiveObjectProperty.value), 1, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.SubClassOf.value), 2, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.SubDataPropertyOf.value), 3, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.SubObjectPropertyOf.value), 4, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.SymmetricObjectProperty.value), 5, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.TransitiveObjectProperty.value), 6, 2)
        intensionalGroup = QtWidgets.QGroupBox('Intensional', self)
        intensionalGroup.setLayout(intensionalLayout)
        extensionalLayout = QtWidgets.QGridLayout()
        extensionalLayout.setColumnMinimumWidth(0, 230)
        extensionalLayout.setColumnMinimumWidth(1, 230)
        extensionalLayout.setColumnMinimumWidth(2, 230)
        extensionalLayout.addWidget(self.widget(OWLAxiom.ClassAssertion.value), 0, 0)
        extensionalLayout.addWidget(self.widget(OWLAxiom.DataPropertyAssertion.value), 1, 0)
        extensionalLayout.addWidget(self.widget(OWLAxiom.DifferentIndividuals.value), 2, 0)
        extensionalLayout.addWidget(self.widget(OWLAxiom.NegativeDataPropertyAssertion.value), 0, 1)
        extensionalLayout.addWidget(self.widget(OWLAxiom.NegativeObjectPropertyAssertion.value), 1, 1)
        extensionalLayout.addWidget(self.widget(OWLAxiom.ObjectPropertyAssertion.value), 2, 1)
        extensionalLayout.addWidget(self.widget(OWLAxiom.SameIndividual.value), 0, 2)
        extensionalGroup = QtWidgets.QGroupBox('Extensional', self)
        extensionalGroup.setLayout(extensionalLayout)
        logicalLayout = QtWidgets.QVBoxLayout()
        logicalLayout.addWidget(intensionalGroup)
        logicalLayout.addWidget(extensionalGroup)
        logicalGroup = QtWidgets.QGroupBox('Logical', self)
        logicalGroup.setLayout(logicalLayout)
        axiomsTopLayout = QtWidgets.QVBoxLayout()
        axiomsTopLayout.addWidget(nonLogicalGroup)
        axiomsTopLayout.addWidget(logicalGroup)
        axiomsBottomLayout = QtWidgets.QHBoxLayout()
        axiomsBottomLayout.setContentsMargins(0, 6, 0, 0)
        axiomsBottomLayout.setAlignment(QtCore.Qt.AlignRight)
        axiomsBottomLayout.addWidget(self.widget('btn_clear_all'), 0, QtCore.Qt.AlignRight)
        axiomsBottomLayout.addWidget(self.widget('btn_check_all'), 0, QtCore.Qt.AlignRight)
        axiomsLayout = QtWidgets.QVBoxLayout()
        axiomsLayout.addLayout(axiomsTopLayout)
        axiomsLayout.addLayout(axiomsBottomLayout)
        axiomsGroup = QtWidgets.QGroupBox('OWL 2 Axioms To Export', self)
        axiomsGroup.setLayout(axiomsLayout)

        # SPACER
        spacer = QtWidgets.QFrame()
        spacer.setFrameShape(QtWidgets.QFrame.HLine)
        spacer.setFrameShadow(QtWidgets.QFrame.Sunken)

        # PROGRESS BAR
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        #############################################
        # BOTTOM AREA
        #################################

        normalization = CheckBox('Normalize', self)
        normalization.setChecked(False)
        normalization.setObjectName('normalization')
        self.addWidget(normalization)

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Ok)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setObjectName('confirmation')
        connect(confirmation.accepted, self.run)
        connect(confirmation.rejected, self.reject)
        self.addWidget(confirmation)

        confirmationLayout = QtWidgets.QHBoxLayout()
        confirmationLayout.setContentsMargins(0, 0, 0, 0)
        confirmationLayout.addWidget(self.widget('normalization'), 0, QtCore.Qt.AlignLeft)
        confirmationLayout.addWidget(self.widget('confirmation'), 0, QtCore.Qt.AlignRight)
        confirmationArea = QtWidgets.QWidget()
        confirmationArea.setLayout(confirmationLayout)

        #############################################
        # CONFIGURE LAYOUT
        #################################

        # for axiom in OWLAxiom.forProfile(self.project.profile.type()):
        for axiom in OWLAxiom:
            checkbox = self.widget(axiom.value)
            checkbox.setChecked(settings.value('export/axiom/{0}'.format(axiom.value), True, bool))
            checkbox.setEnabled(True)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.addWidget(syntaxGroup)
        mainLayout.addWidget(axiomsGroup)
        mainLayout.addWidget(spacer)
        mainLayout.addWidget(self.progressBar)
        mainLayout.addWidget(confirmationArea)

        self.setLayout(mainLayout)
        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('{0} Export'.format(self.project.profile.name()))

    #############################################
    #   INTERFACE
    #################################

    def axioms(self):
        """
        Returns the set of axioms that needs to be exported.
        :rtype: set
        """
        return {axiom for axiom in OWLAxiom if self.widget(axiom.value).isChecked()}

    def normalize(self):
        """
        Returns whether the current ontology needs to be normalized, or not.
        :rtype: bool
        """
        return self.widget('normalization').isChecked()

    def syntax(self):
        """
        Returns the value of the OWL syntax field.
        :rtype: OWLSyntax
        """
        return self.widget('syntax_field').currentData()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (alias for OWLProjectExporterDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onAxiomCheckClicked(self):
        """
        Executed when an axiom checkbox is clicked.
        """
        self.widget('confirmation').setEnabled(any(x.isChecked() for x in (self.widget(k.value) for k in OWLAxiom)))

    @QtCore.pyqtSlot()
    def doCheckAxiomMarks(self):
        """
        Check axioms marks according to the action that triggered the slot.
        """
        checked = self.sender() is self.widget('btn_check_all')
        for axiom in OWLAxiom.forProfile(self.project.profile.type()):
            checkbox = self.widget(axiom.value)
            checkbox.setChecked(checked)
        self.widget('confirmation').setEnabled(checked)

    @QtCore.pyqtSlot(Exception)
    def onErrored(self, exception):
        """
        Executed whenever the translation errors.
        :type exception: Exception
        """
        if isinstance(exception, DiagramMalformedError):
            # SHOW A POPUP WITH THE WARNING MESSAGE
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setInformativeText('Do you want to see the error in the diagram?')
            msgbox.setText('Malformed expression detected on {0}: {1}'.format(exception.item, exception))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Malformed expression')
            msgbox.exec_()
            if msgbox.result() == QtWidgets.QMessageBox.Yes:
                self.session.doFocusItem(exception.item)
        else:
            # SHOW A POPUP WITH THE ERROR MESSAGE
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setDetailedText(format_exception(exception))
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
            msgbox.setInformativeText('Please <a href="{0}">submit a bug report</a>.'.format(BUG_TRACKER))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
            msgbox.setText('Diagram translation could not be completed!')
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Unhandled exception!')
            msgbox.exec_()

        self.reject()

    @QtCore.pyqtSlot(str)
    def onMetadataFetchErrored(self, message):
        """
        Executed when a metadata fetch request fails.
        :type message: str
        """
        self.session.addNotification(textwrap.dedent(f"""
        <b><font color="#7E0B17">ERROR</font></b>:\n
        {message}
        """))

    @QtCore.pyqtSlot()
    def onCompleted(self):
        """
        Executed whenever the translation completes.
        """
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setText('Translation completed! Do you want to open the OWL ontology?')
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.exec_()
        if msgbox.result() == QtWidgets.QMessageBox.Yes:
            openPath(self.path)
        self.accept()

    @QtCore.pyqtSlot(int, int)
    def onProgress(self, current, total):
        """
        Update the progress bar showing the translation advancement.
        :type current: int
        :type total: int
        """
        self.progressBar.setRange(0, total)
        self.progressBar.setValue(current)

    @QtCore.pyqtSlot()
    def onStarted(self):
        """
        Executed whenever the translation starts.
        """
        self.widget('confirmation').setEnabled(False)
        self.widget('btn_clear_all').setEnabled(False)
        self.widget('btn_check_all').setEnabled(False)
        for axiom in OWLAxiom:
            if axiom is not OWLAxiom.Declaration:
                checkbox = self.widget(axiom.value)
                checkbox.setEnabled(False)
        self.widget('normalization').setEnabled(False)

    @QtCore.pyqtSlot()
    def run(self):
        """
        Perform the Graphol -> OWL translation in a separate thread.
        """
        LOGGER.info('Exporting project %s in OWL 2 format: %s', self.project.name, self.path)
        worker = OWLOntologyExporterWorker(self.project, self.path,
                                           axioms=self.axioms(), normalize=self.normalize(),
                                           syntax=self.syntax(), diagrams=self.diagrams)

        connect(worker.sgnStarted, self.onStarted)
        connect(worker.sgnCompleted, self.onCompleted)
        connect(worker.sgnErrored, self.onErrored)
        connect(worker.sgnMetadataFetchErrored, self.onMetadataFetchErrored)
        connect(worker.sgnProgress, self.onProgress)
        self.startThread('OWL2Export', worker)


class OWLOntologyExporterWorker(AbstractWorker):
    """
    Extends AbstractWorker providing a worker thread that will perform the OWL 2 ontology generation.
    """
    sgnCompleted = QtCore.pyqtSignal()
    sgnErrored = QtCore.pyqtSignal(Exception)
    sgnMetadataFetchErrored = QtCore.pyqtSignal(str)
    sgnProgress = QtCore.pyqtSignal(int, int)
    sgnStarted = QtCore.pyqtSignal()

    def __init__(self, project, path=None, **kwargs):
        """
        Initialize the OWL 2 Exporter worker.
        :type project: Project
        :type path: str
        """
        super().__init__()

        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()
        self.AddOntologyAnnotation = self.vm.getJavaClass('org.semanticweb.owlapi.model.AddOntologyAnnotation')
        self.DefaultPrefixManager = self.vm.getJavaClass('org.semanticweb.owlapi.util.DefaultPrefixManager')
        self.FunctionalSyntaxDocumentFormat = self.vm.getJavaClass('org.semanticweb.owlapi.formats.FunctionalSyntaxDocumentFormat')
        self.HashSet = self.vm.getJavaClass('java.util.HashSet')
        self.IRI = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.LinkedList = self.vm.getJavaClass('java.util.LinkedList')
        self.List = self.vm.getJavaClass('java.util.List')
        self.ManchesterSyntaxDocumentFormat = self.vm.getJavaClass('org.semanticweb.owlapi.formats.ManchesterSyntaxDocumentFormat')
        self.OWLAnnotationValue = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLAnnotationValue')
        self.OWLFacet = self.vm.getJavaClass('org.semanticweb.owlapi.vocab.OWLFacet')
        self.OWL2Datatype = self.vm.getJavaClass('org.semanticweb.owlapi.vocab.OWL2Datatype')
        self.OWLManager = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.OWLOntologyID = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLOntologyID')
        self.OWLOntologyDocumentTarget = self.vm.getJavaClass('org.semanticweb.owlapi.io.OWLOntologyDocumentTarget')
        self.RDFXMLDocumentFormat = self.vm.getJavaClass('org.semanticweb.owlapi.formats.RDFXMLDocumentFormat')
        self.PrefixManager = self.vm.getJavaClass('org.semanticweb.owlapi.model.PrefixManager')
        self.Set = self.vm.getJavaClass('java.util.Set')
        self.StringDocumentTarget = self.vm.getJavaClass('org.semanticweb.owlapi.io.StringDocumentTarget')
        self.TurtleDocumentFormat = self.vm.getJavaClass('org.semanticweb.owlapi.formats.TurtleDocumentFormat')

        self.JavaFileClass = self.vm.getJavaClass('java.io.File')
        self.URIClass = self.vm.getJavaClass('java.net.URI')
        self.IRIMapperClass = self.vm.getJavaClass('org.semanticweb.owlapi.util.SimpleIRIMapper')
        self.ImportsDeclarationClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLImportsDeclaration')
        self.ImportsEnum = self.vm.getJavaClass('org.semanticweb.owlapi.model.parameters.Imports')
        self.AddImportClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.AddImport')

        self.path = path
        self.project = project
        self.nmanager = NetworkManager(self)
        self.axiomsList = kwargs.get('axioms', set())
        self.normalize = kwargs.get('normalize', False)
        self.syntax = kwargs.get('syntax', OWLSyntax.Functional)

        self.selected_diagrams = kwargs.get('diagrams', self.project.diagrams())

        self._axioms = set()
        self._converted = dict()
        self._converted_meta_individuals = dict()
        self.metadataProperty = self.project.getIRI('urn:x-graphol:origin')

        self.df = None
        self.man = None
        self.num = 0
        self.max = sum([len(diagram.nodes()) * 2 + len(diagram.edges()) for diagram in self.selected_diagrams])
        self.ontology = None
        self.pm = None

    #############################################
    #   INTERFACE
    #################################

    def addAxiom(self, axiom):
        """
        Add an axiom to the axiom set.
        :type axiom: OWLAxiom
        """
        self._axioms.add(axiom)

    def axioms(self):
        """
        Returns the set of axioms.
        :rtype: set
        """
        return self._axioms

    def convert(self, node):
        """
        Build and returns the OWL 2 conversion of the given node.
        :type node: AbstractNode
        :rtype: OWLObject
        """
        if node.diagram.name not in self._converted:
            self._converted[node.diagram.name] = dict()
            self._converted_meta_individuals[node.diagram.name] = dict()
        if node not in self._converted[node.diagram.name]:
            if node.type() is Item.ConceptNode:
                self._converted[node.diagram.name][node.id] = self.getConcept(node)
                if node.occursAsIndividual():
                    self._converted_meta_individuals[node.diagram.name][node.id] = self.getIndividual(node)
            elif node.type() is Item.AttributeNode:
                self._converted[node.diagram.name][node.id] = self.getAttribute(node)
                if node.occursAsIndividual():
                    self._converted_meta_individuals[node.diagram.name][node.id] = self.getIndividual(node)
            elif node.type() is Item.RoleNode:
                self._converted[node.diagram.name][node.id] = self.getRole(node)
                if node.occursAsIndividual():
                    self._converted_meta_individuals[node.diagram.name][node.id] = self.getIndividual(node)
            elif node.type() is Item.ValueDomainNode:
                self._converted[node.diagram.name][node.id] = self.getValueDomain(node)
            elif node.type() is Item.IndividualNode:
                self._converted[node.diagram.name][node.id] = self.getIndividual(node)
            elif node.type() is Item.LiteralNode:
                self._converted[node.diagram.name][node.id] = self.getLiteral(node)
            elif node.type() is Item.FacetNode:
                self._converted[node.diagram.name][node.id] = self.getFacet(node)
            elif node.type() is Item.RoleInverseNode:
                self._converted[node.diagram.name][node.id] = self.getRoleInverse(node)
            elif node.type() is Item.RoleChainNode:
                self._converted[node.diagram.name][node.id] = self.getRoleChain(node)
            elif node.type() is Item.ComplementNode:
                self._converted[node.diagram.name][node.id] = self.getComplement(node)
            elif node.type() is Item.EnumerationNode:
                self._converted[node.diagram.name][node.id] = self.getEnumeration(node)
            elif node.type() is Item.IntersectionNode:
                self._converted[node.diagram.name][node.id] = self.getIntersection(node)
            elif node.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                self._converted[node.diagram.name][node.id] = self.getUnion(node)
            elif node.type() is Item.DatatypeRestrictionNode:
                self._converted[node.diagram.name][node.id] = self.getDatatypeRestriction(node)
            elif node.type() is Item.PropertyAssertionNode:
                self._converted[node.diagram.name][node.id] = self.getPropertyAssertion(node)
            elif node.type() is Item.DomainRestrictionNode:
                self._converted[node.diagram.name][node.id] = self.getDomainRestriction(node)
            elif node.type() is Item.RangeRestrictionNode:
                self._converted[node.diagram.name][node.id] = self.getRangeRestriction(node)
            elif node.type() is Item.HasKeyNode:
                self._converted[node.diagram.name][node.id] = self.getHasKey(node)
            else:
                raise ValueError('no conversion available for node %s' % node)
        return self._converted[node.diagram.name][node.id]

    def converted(self):
        """
        Returns the dictionary of converted nodes.
        :rtype: dict
        """
        return self._converted

    def convertPredicateNodeOccurringAsIndividual(self, node):
        """
        Needed for translation of PropertyAssertion nodes (i.e., getPropertyAssertion).
        """
        owlInd = self.getIndividual(node)
        self._converted_meta_individuals[node.diagram.name][node.id] = owlInd
        return owlInd

    def step(self, num, increase=0):
        """
        Increments the progress by the given step and emits the progress signal.
        :type num: int
        :type increase: int
        """
        self.max += increase
        self.num += num
        self.num = clamp(self.num, minval=0, maxval=self.max)
        self.sgnProgress.emit(self.num, self.max)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def getOWLApiAnnotation(self, annotation):
        """
        Returns an OWLAnnotation corresponding to the given annotation object.
        :type annotation: Annotation
        :rtype: OWLAnnotation
        """
        prop = self.df.getOWLAnnotationProperty(self.IRI.create(str(annotation.assertionProperty)))
        if annotation.isIRIValued():
            value = self.IRI.create(str(annotation.value))
        else:
            lexicalForm = annotation.value
            if annotation.language:
                value = self.df.getOWLLiteral(lexicalForm, annotation.language)
            else:
                if annotation.datatype:
                    datatype = self.df.getOWLDatatype(self.IRI.create(str(annotation.datatype)))
                else:
                    datatype = self.OWL2Datatype.RDF_PLAIN_LITERAL
                value = self.df.getOWLLiteral(lexicalForm, datatype)
        return self.df.getOWLAnnotation(prop, value)

    def getOWLApiDatatype(self, datatype):
        """
        Returns the OWLDatatype matching the given Datatype.
        :type datatype: Datatype
        :rtype: OWLDatatype
        """
        if datatype is Datatype.anyURI:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_ANY_URI').getIRI())
        if datatype is Datatype.base64Binary:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_BASE_64_BINARY').getIRI())
        if datatype is Datatype.boolean:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_BOOLEAN').getIRI())
        if datatype is Datatype.byte:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_BYTE').getIRI())
        if datatype is Datatype.dateTime:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_DATE_TIME').getIRI())
        if datatype is Datatype.dateTimeStamp:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_DATE_TIME_STAMP').getIRI())
        if datatype is Datatype.decimal:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_DECIMAL').getIRI())
        if datatype is Datatype.double:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_DOUBLE').getIRI())
        if datatype is Datatype.float:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_FLOAT').getIRI())
        if datatype is Datatype.hexBinary:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_HEX_BINARY').getIRI())
        if datatype is Datatype.int:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_INT').getIRI())
        if datatype is Datatype.integer:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_INTEGER').getIRI())
        if datatype is Datatype.language:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_LANGUAGE').getIRI())
        if datatype is Datatype.Literal:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('RDFS_LITERAL').getIRI())
        if datatype is Datatype.long:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_LONG').getIRI())
        if datatype is Datatype.Name:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NAME').getIRI())
        if datatype is Datatype.NCName:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NCNAME').getIRI())
        if datatype is Datatype.negativeInteger:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NEGATIVE_INTEGER').getIRI())
        if datatype is Datatype.NMTOKEN:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NMTOKEN').getIRI())
        if datatype is Datatype.nonNegativeInteger:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NON_NEGATIVE_INTEGER').getIRI())
        if datatype is Datatype.nonPositiveInteger:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NON_POSITIVE_INTEGER').getIRI())
        if datatype is Datatype.normalizedString:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NORMALIZED_STRING').getIRI())
        if datatype is Datatype.PlainLiteral:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('RDF_PLAIN_LITERAL').getIRI())
        if datatype is Datatype.positiveInteger:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_POSITIVE_INTEGER').getIRI())
        if datatype is Datatype.rational:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('OWL_RATIONAL').getIRI())
        if datatype is Datatype.real:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('OWL_REAL').getIRI())
        if datatype is Datatype.short:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_SHORT').getIRI())
        if datatype is Datatype.string:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_STRING').getIRI())
        if datatype is Datatype.token:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_TOKEN').getIRI())
        if datatype is Datatype.unsignedByte:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_UNSIGNED_BYTE').getIRI())
        if datatype is Datatype.unsignedInt:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_UNSIGNED_INT').getIRI())
        if datatype is Datatype.unsignedLong:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_UNSIGNED_LONG').getIRI())
        if datatype is Datatype.unsignedShort:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_UNSIGNED_SHORT').getIRI())
        if datatype is Datatype.XMLLiteral:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('RDF_XML_LITERAL').getIRI())
        raise ValueError('invalid datatype supplied: %s' % datatype)

    def getOWLApiFacet(self, facet):
        """
        Returns the OWLFacet matching the given Facet.
        :type facet: Facet
        :rtype: OWLFacet
        """
        if facet is OWL2Facet.maxExclusive.value:
            return self.OWLFacet.valueOf('MAX_EXCLUSIVE')
        if facet is OWL2Facet.maxInclusive.value:
            return self.OWLFacet.valueOf('MAX_INCLUSIVE')
        if facet is OWL2Facet.minExclusive.value:
            return self.OWLFacet.valueOf('MIN_EXCLUSIVE')
        if facet is OWL2Facet.minInclusive.value:
            return self.OWLFacet.valueOf('MIN_INCLUSIVE')
        if facet is OWL2Facet.langRange.value:
            return self.OWLFacet.valueOf('LANG_RANGE')
        if facet is OWL2Facet.length.value:
            return self.OWLFacet.valueOf('LENGTH')
        if facet is OWL2Facet.maxLength.value:
            return self.OWLFacet.valueOf('MIN_LENGTH')
        if facet is OWL2Facet.minLength.value:
            return self.OWLFacet.valueOf('MIN_LENGTH')
        if facet is OWL2Facet.pattern.value:
            return self.OWLFacet.valueOf('PATTERN')
        raise ValueError('invalid facet supplied: %s' % facet)

    #############################################
    #   NODES PROCESSING
    #################################

    def getAttribute(self, node):
        """
        Build and returns a OWL 2 attribute using the given graphol node.
        :type node: AttributeNode
        :rtype: OWLDataProperty
        """
        iri = node.iri
        if iri.isTopDataProperty():
            return self.df.getOWLTopDataProperty()
        if iri.isBottomDataProperty():
            return self.df.getOWLBottomDataProperty()
        owlProp = self.df.getOWLDataProperty(self.IRI.create(str(iri)))
        if OWLAxiom.Declaration in self.axiomsList:
            self.addAxiom(self.df.getOWLDeclarationAxiom(owlProp))
        if OWLAxiom.FunctionalDataProperty in self.axiomsList:
            if iri.functional:
                self.addAxiom(self.df.getOWLFunctionalDataPropertyAxiom(owlProp))
        return owlProp

    def getAxiomAnnotationSet(self, edge):
        """
        Returns the set of annotations for the given axiom edge.
        :type edge: AxiomEdge
        :rtype: Set
        """
        collection = self.HashSet()
        if OWLAxiom.Annotation in self.axiomsList:
            for annotation in edge.annotations:
                collection.add(self.getOWLApiAnnotation(annotation))
        return collection

    def getComplement(self, node):
        """
        Build and returns a OWL 2 complement using the given graphol node.
        :type node: ComplementNode
        :rtype: OWLClassExpression
        """
        if node.identity() is Identity.Unknown:
            raise DiagramMalformedError(node, 'unsupported operand(s)')
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() in {Identity.Attribute, Identity.Concept, Identity.ValueDomain, Identity.Role}
        incoming = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
        if not incoming:
            raise DiagramMalformedError(node, 'missing operand(s)')
        if len(incoming) > 1:
            raise DiagramMalformedError(node, 'too many operands')
        operand = first(incoming)
        if operand.identity() is Identity.Concept:
            conversion = self.convert(operand)
            return self.df.getOWLObjectComplementOf(conversion)
        if operand.identity() is Identity.ValueDomain:
            conversion = self.convert(operand)
            return self.df.getOWLDataComplementOf(conversion)
        if operand.identity() is Identity.Role:
            return self.convert(operand)
        if operand.identity() is Identity.Attribute:
            return self.convert(operand)
        raise DiagramMalformedError(node, 'unsupported operand (%s)' % operand)

    def getConcept(self, node):
        """
        Build and returns a OWL 2 concept using the given graphol node.
        :type node: ConceptNode
        :rtype: OWLClass
        """
        iri = node.iri
        if iri.isOwlThing():
            return self.df.getOWLThing()
        if iri.isOwlNothing():
            return self.df.getOWLNothing()
        owlCl = self.df.getOWLClass(self.IRI.create(str(iri)))
        if OWLAxiom.Declaration in self.axiomsList:
            self.addAxiom(self.df.getOWLDeclarationAxiom(owlCl))
        return owlCl

    def getDatatypeRestriction(self, node):
        """
        Build and returns a OWL 2 datatype restriction using the given graphol node.
        :type node: DatatypeRestrictionNode
        :rtype: OWLDatatypeRestriction
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.ValueDomainNode
        f3 = lambda x: x.type() is Item.FacetNode

        #############################################
        # BUILD DATATYPE
        #################################

        operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if not operand:
            raise DiagramMalformedError(node, 'missing value domain node')

        de = self.convert(operand)

        #############################################
        # BUILD FACETS
        #################################

        incoming = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)
        if not incoming:
            raise DiagramMalformedError(node, 'missing facet node(s)')

        collection = self.HashSet()
        for facet in incoming:
            conversion = self.convert(facet)
            collection.add(conversion)

        #############################################
        # BUILD DATATYPE RESTRICTION
        #################################

        return self.df.getOWLDatatypeRestriction(de, self.vm.cast(self.Set, collection))

    def getDomainRestriction(self, node):
        """
        Build and returns a OWL 2 domain restriction using the given graphol node.
        :type node: DomainRestrictionNode
        :rtype: OWLClassExpression
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() in {Identity.Role, Identity.Attribute}
        f3 = lambda x: x.identity() is Identity.ValueDomain
        f4 = lambda x: x.identity() is Identity.Concept

        operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if not operand:
            raise DiagramMalformedError(node, 'missing operand(s)')

        if operand.identity() is Identity.Attribute:

            #############################################
            # BUILD OPERAND
            #################################

            dpe = self.convert(operand)

            #############################################
            # BUILD FILLER
            #################################

            filler = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            if not filler:
                dre = self.df.getTopDatatype()
            else:
                dre = self.convert(filler)

            if OWLAxiom.DataPropertyDomain in self.axiomsList:
                if not node.isRestrictionQualified() and node.restriction() is Restriction.Exists:
                    if dpe:
                        f5 = lambda x: x.type() is Item.InclusionEdge
                        f6 = lambda x: x.type() is Item.EquivalenceEdge
                        f7 = lambda x: x.identity() is Identity.Concept
                        for concept in node.outgoingNodes(f5, f7) | node.adjacentNodes(f6, f7):
                            conversionB = self.convert(concept)
                            self.addAxiom(self.df.getOWLDataPropertyDomainAxiom(dpe, conversionB))
            if node.restriction() is Restriction.Exists:
                return self.df.getOWLDataSomeValuesFrom(dpe, dre)
            if node.restriction() is Restriction.Forall:
                return self.df.getOWLDataAllValuesFrom(dpe, dre)
            if node.restriction() is Restriction.Cardinality:
                cardinalities = self.HashSet()
                min_cardinality = node.cardinality('min')
                max_cardinality = node.cardinality('max')
                if min_cardinality:
                    cardinalities.add(self.df.getOWLDataMinCardinality(min_cardinality, dpe, dre))
                if max_cardinality is not None:
                    cardinalities.add(self.df.getOWLDataMaxCardinality(max_cardinality, dpe, dre))
                if cardinalities.isEmpty():
                    raise DiagramMalformedError(node, 'missing cardinality')
                if cardinalities.size() > 1:
                    return self.df.getOWLObjectIntersectionOf(self.vm.cast(self.Set, cardinalities))
                return cardinalities.iterator().next()
            raise DiagramMalformedError(node, 'unsupported restriction (%s)' % node.restriction())

        elif operand.identity() is Identity.Role:

            #############################################
            # BUILD OPERAND
            #################################

            ope = self.convert(operand)

            #############################################
            # BUILD FILLER
            #################################

            filler = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f4))
            if not filler:
                ce = self.df.getOWLThing()
            else:
                ce = self.convert(filler)

            if node.restriction() is Restriction.Self:
                return self.df.getOWLObjectHasSelf(ope)
            if node.restriction() is Restriction.Exists:
                return self.df.getOWLObjectSomeValuesFrom(ope, ce)
            if node.restriction() is Restriction.Forall:
                return self.df.getOWLObjectAllValuesFrom(ope, ce)
            if node.restriction() is Restriction.Cardinality:
                cardinalities = self.HashSet()
                min_cardinality = node.cardinality('min')
                max_cardinality = node.cardinality('max')
                if min_cardinality:
                    cardinalities.add(self.df.getOWLObjectMinCardinality(min_cardinality, ope, ce))
                if max_cardinality is not None:
                    cardinalities.add(self.df.getOWLObjectMaxCardinality(max_cardinality, ope, ce))
                if cardinalities.isEmpty():
                    raise DiagramMalformedError(node, 'missing cardinality')
                if cardinalities.size() > 1:
                    return self.df.getOWLObjectIntersectionOf(self.vm.cast(self.Set, cardinalities))
                return cardinalities.iterator().next()
            raise DiagramMalformedError(node, 'unsupported restriction (%s)' % node.restriction())

    def getEnumeration(self, node):
        """
        Build and returns a OWL 2 enumeration using the given graphol node.
        :type node: EnumerationNode
        :rtype: OWLObjectOneOf
        """
        if node.identity() is Identity.Unknown:
            raise DiagramMalformedError(node, 'unsupported operand(s)')
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.IndividualNode
        individuals = self.HashSet()
        for individual in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
            conversion = self.convert(individual)
            individuals.add(conversion)
        if individuals.isEmpty():
            raise DiagramMalformedError(node, 'missing operand(s)')
        return self.df.getOWLObjectOneOf(self.vm.cast(self.Set, individuals))

    def getFacet(self, node):
        """
        Build and returns a OWL 2 facet restriction using the given graphol node.
        :type node: FacetNode
        :rtype: OWLFacetRestriction
        """
        nodeFacet = node.facet
        literal = self.df.getOWLLiteral(
            nodeFacet.literal.lexicalForm,
            self.df.getOWLDatatype(self.IRI.create(str(nodeFacet.literal.datatype))),
        )
        facet = self.getOWLApiFacet(nodeFacet.constrainingFacet)
        return self.df.getOWLFacetRestriction(facet, literal)

    def getHasKey(self, node):
        """
        Build and returns a collection of expressions that can be used to build
        a OWL 2 HasKey axiom. The first item of the collection is a the class expression,
        and the remaining items are object and data property expressions that uniquely
        identify named instances of the class expression.
        :type node: HasKeyNode
        :rtype: list
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() is Identity.Concept
        f3 = lambda x: x.identity() is Identity.Role
        f4 = lambda x: x.identity() is Identity.Attribute
        classes = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
        objProps = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)
        dtProps = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f4)

        if not classes:
            raise DiagramMalformedError(node, 'missing class expression operand')
        if len(classes) > 1:
            raise DiagramMalformedError(node, 'too many class expression operands')
        if not (objProps or dtProps):
            raise DiagramMalformedError(node, 'HasKey nodes must be connected to at least '
                                              'an (object or data) property expression')

        collection = [self.convert(first(classes))]
        for prop in objProps:
            collection.append(self.convert(prop))
        for prop in dtProps:
            collection.append(self.convert(prop))
        return collection

    def getIndividual(self, node):
        """
        Build and returns a OWL 2 individual using the given graphol node.
        Also perform punning if the node is not an IndividualNode
        :type node: IndividualNode|ConceptNode|RoleNode|AttributeNode
        :rtype: OWLNamedIndividual
        """
        iri = node.iri
        owlInd = self.df.getOWLNamedIndividual(self.IRI.create(str(iri)))
        if OWLAxiom.Declaration in self.axiomsList:
            self.addAxiom(self.df.getOWLDeclarationAxiom(owlInd))
        return owlInd

    def getIntersection(self, node):
        """
        Build and returns a OWL 2 intersection using the given graphol node.
        :type node: IntersectionNode
        :rtype: T <= OWLObjectIntersectionOf|OWLDataIntersectionOf
        """
        if node.identity() is Identity.Unknown:
            raise DiagramMalformedError(node, 'unsupported operand(s)')
        collection = self.HashSet()
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() is node.identity()
        for operand in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
            conversion = self.convert(operand)
            collection.add(conversion)
        if collection.isEmpty():
            raise DiagramMalformedError(node, 'missing operand(s)')
        if node.identity() is Identity.Concept:
            return self.df.getOWLObjectIntersectionOf(self.vm.cast(self.Set, collection))
        return self.df.getOWLDataIntersectionOf(self.vm.cast(self.Set, collection))

    def getLiteral(self, node):
        """
        Build and returns a OWL 2 literal using the given graphol node.
        :type node: LiteralNode
        :rtype: OWLLiteral
        """
        literal = node.literal
        lexForm = literal.lexicalForm
        lang = literal.language
        datatype = literal.datatype
        if lang:
            return self.df.getOWLLiteral(lexForm, str(lang))
        else:
            if datatype:
                owlApiDatatype = self.df.getOWLDatatype(self.IRI.create(str(datatype)))
            else:
                owlApiDatatype = self.df.getOWLDatatype(self.IRI.create(str(OWL2Datatype.PlainLiteral.value)))
            return self.df.getOWLLiteral(lexForm, owlApiDatatype)

    def getPropertyAssertion(self, node):
        """
        Build and returns a collection of individuals that can be used to build property assertions.
        :type node: PropertyAssertionNode
        :rtype: list
        """
        if node.identity() is Identity.Unknown:
            raise DiagramMalformedError(node, 'unsupported operand(s)')
        collection = list()
        for operand in [node.diagram.edge(i).other(node) for i in node.inputs]:
            if operand.type() not in {Item.IndividualNode, Item.ConceptNode, Item.RoleNode,
                                      Item.AttributeNode, Item.LiteralNode}:
                raise DiagramMalformedError(node, 'unsupported operand (%s)' % operand)
            if operand.type() in {Item.IndividualNode, Item.LiteralNode}:
                conversion = self.convert(operand)
            else:
                conversion = self.convertPredicateNodeOccurringAsIndividual(operand)
            collection.append(conversion)
        if len(collection) < 2:
            raise DiagramMalformedError(node, 'missing operand(s)')
        if len(collection) > 2:
            raise DiagramMalformedError(node, 'too many operands')
        return collection

    def getRangeRestriction(self, node):
        """
        Build and returns a OWL 2 range restriction using the given graphol node.
        :type node: DomainRestrictionNode
        :rtype: T <= OWLClassExpression|OWLDataProperty
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() in {Identity.Role, Identity.Attribute}
        f3 = lambda x: x.identity() is Identity.Concept

        # We discard Attribute's range restriction. The idea is that the
        # range restriction node whose input is an Attribute, can only serve
        # to compose the DataPropertyRange axiom and thus should never be
        # given in input to any other type of node, nor it should have
        # another input itself. If one of the above mentioned things happens
        # we'll see an AttributeError added in the application log which will
        # highlight an expression composition problem.

        operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if not operand:
            raise DiagramMalformedError(node, 'missing operand(s)')

        if operand.identity() is Identity.Role:

            #############################################
            # BUILD OPERAND
            #################################

            ope = self.convert(operand).getInverseProperty()

            #############################################
            # BUILD FILLER
            #################################

            filler = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            if not filler:
                ce = self.df.getOWLThing()
            else:
                ce = self.convert(filler)

            if node.restriction() is Restriction.Self:
                return self.df.getOWLObjectHasSelf(ope)
            if node.restriction() is Restriction.Exists:
                return self.df.getOWLObjectSomeValuesFrom(ope, ce)
            if node.restriction() is Restriction.Forall:
                return self.df.getOWLObjectAllValuesFrom(ope, ce)
            if node.restriction() is Restriction.Cardinality:
                cardinalities = self.HashSet()
                min_cardinality = node.cardinality('min')
                max_cardinality = node.cardinality('max')
                if min_cardinality:
                    cardinalities.add(self.df.getOWLObjectMinCardinality(min_cardinality, ope, ce))
                if max_cardinality is not None:
                    cardinalities.add(self.df.getOWLObjectMaxCardinality(max_cardinality, ope, ce))
                if cardinalities.isEmpty():
                    raise DiagramMalformedError(node, 'missing cardinality')
                if cardinalities.size() > 1:
                    return self.df.getOWLObjectIntersectionOf(self.vm.cast(self.Set, cardinalities))
                return cardinalities.iterator().next()
            raise DiagramMalformedError(node, 'unsupported restriction (%s)' % node.restriction())

    def getRole(self, node):
        """
        Build and returns a OWL 2 role using the given graphol node.
        :type node: RoleNode
        :rtype: OWLObjectProperty
        """
        iri = node.iri
        if iri.isTopObjectProperty():
            return self.df.getOWLTopObjectProperty()
        if iri.isBottomObjectProperty():
            return self.df.getOWLBottomObjectProperty()
        owlProp = self.df.getOWLObjectProperty(self.IRI.create(str(iri)))
        if OWLAxiom.Declaration in self.axiomsList:
            self.addAxiom(self.df.getOWLDeclarationAxiom(owlProp))
        if OWLAxiom.FunctionalObjectProperty in self.axiomsList:
            if iri.functional:
                self.addAxiom(self.df.getOWLFunctionalObjectPropertyAxiom(owlProp))
        if OWLAxiom.InverseFunctionalObjectProperty in self.axiomsList:
            if iri.inverseFunctional:
                self.addAxiom(self.df.getOWLInverseFunctionalObjectPropertyAxiom(owlProp))
        if OWLAxiom.AsymmetricObjectProperty in self.axiomsList:
            if iri.asymmetric:
                self.addAxiom(self.df.getOWLAsymmetricObjectPropertyAxiom(owlProp))
        if OWLAxiom.IrreflexiveObjectProperty in self.axiomsList:
            if iri.irreflexive:
                self.addAxiom(self.df.getOWLIrreflexiveObjectPropertyAxiom(owlProp))
        if OWLAxiom.ReflexiveObjectProperty in self.axiomsList:
            if iri.reflexive:
                self.addAxiom(self.df.getOWLReflexiveObjectPropertyAxiom(owlProp))
        if OWLAxiom.SymmetricObjectProperty in self.axiomsList:
            if iri.symmetric:
                self.addAxiom(self.df.getOWLSymmetricObjectPropertyAxiom(owlProp))
        if OWLAxiom.TransitiveObjectProperty in self.axiomsList:
            if iri.transitive:
                self.addAxiom(self.df.getOWLTransitiveObjectPropertyAxiom(owlProp))
        return owlProp

    def getRoleChain(self, node):
        """
        Constructs and returns LinkedList of chained OWLObjectExpression (OPE => Role & RoleInverse).
        :type node: RoleChainNode
        :rtype: List
        """
        if not node.inputs:
            raise DiagramMalformedError(node, 'missing operand(s)')
        collection = self.LinkedList()
        for operand in [node.diagram.edge(i).other(node) for i in node.inputs]:
            if operand.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                raise DiagramMalformedError(node, 'unsupported operand (%s)' % operand)
            conversion = self.convert(operand)
            collection.add(conversion)
        if collection.isEmpty():
            raise DiagramMalformedError(node, 'missing operand(s)')
        return self.vm.cast(self.List, collection)

    def getRoleInverse(self, node):
        """
        Build and returns a OWL 2 role inverse using the given graphol node.
        :type node: RoleInverseNode
        :rtype: OWLObjectPropertyExpression
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.RoleNode
        operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if not operand:
            raise DiagramMalformedError(node, 'missing operand')
        return self.convert(operand).getInverseProperty()

    def getUnion(self, node):
        """
        Build and returns a OWL 2 union using the given graphol node.
        :type node: UnionNode
        :rtype: T <= OWLObjectUnionOf|OWLDataUnionOf
        """
        if node.identity() is Identity.Unknown:
            raise DiagramMalformedError(node, 'unsupported operand(s)')
        collection = self.HashSet()
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() is node.identity()
        for operand in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
            conversion = self.convert(operand)
            collection.add(conversion)
        if collection.isEmpty():
            raise DiagramMalformedError(node, 'missing operand(s)')
        if node.identity() is Identity.Concept:
            return self.df.getOWLObjectUnionOf(self.vm.cast(self.Set, collection))
        return self.df.getOWLDataUnionOf(self.vm.cast(self.Set, collection))

    def getValueDomain(self, node):
        """
        Build and returns a OWL 2 datatype using the given graphol node.
        :type node: ValueDomainNode
        :rtype: OWLDatatype
        """
        # return self.getOWLApiDatatype(node.datatype)
        owlDt = self.df.getOWLDatatype(self.IRI.create(str(node.iri)))
        if OWLAxiom.Declaration in self.axiomsList:
            self.addAxiom(self.df.getOWLDeclarationAxiom(owlDt))
        return owlDt

    #############################################
    #   AXIOMS GENERATION
    #################################

    def createAnnotationAssertionAxioms(self, node):
        """
        Generate a set of OWL 2 annotation assertion axioms for the given node annotations.
        :type node: AbstractNode
        """
        if OWLAxiom.Annotation in self.axiomsList:
            for annotation in node.iri.annotationAssertions:
                subject = self.IRI.create(str(annotation.subject))
                if annotation.assertionProperty == self.metadataProperty:
                    uri = annotation.value
                    # FIXME: this is a sync request!!!
                    result, response = self.nmanager.getSync(str(uri))
                    if not result:
                        msg = f'Retrieval of {uri} failed: {response}'
                        LOGGER.warning(msg)
                        self.sgnMetadataFetchErrored.emit(msg)
                        continue
                    try:
                        for assertion in NamedEntity.from_dict(json.loads(response)).annotations:
                            if isinstance(assertion.object, LiteralValue):
                                from eddy.core.owl import Annotation
                                value = Annotation(
                                    self.project.getIRI(str(assertion.predicate.iri)),
                                    assertion.object.value,
                                    type=assertion.object.datatype,
                                    language=assertion.object.language,
                                    parent=self.project,
                                )
                            elif isinstance(assertion.object, NamedEntity):
                                value = Annotation(
                                    self.project.getIRI(str(assertion.predicate.iri)),
                                    self.project.getIRI(str(assertion.object.iri)),
                                    parent=self.project,
                                )
                            else:
                                LOGGER.warning(f'Skipping annotation with bnode object {assertion}')
                            value = self.getOWLApiAnnotation(value)
                            self.addAxiom(self.df.getOWLAnnotationAssertionAxiom(subject, value))
                    except Exception as e:
                        msg = f'Failed to parse metadata for {uri}'
                        LOGGER.warning(f'{msg}: {response}')
                        self.sgnMetadataFetchErrored.emit(f'{msg}: See log for details.')
                else:
                    value = self.getOWLApiAnnotation(annotation)
                    self.addAxiom(self.df.getOWLAnnotationAssertionAxiom(subject, value))

    def createClassAssertionAxiom(self, edge):
        """
        Generate a OWL 2 ClassAssertion axiom.
        :type edge: MembershipEdge
        """
        if OWLAxiom.ClassAssertion in self.axiomsList:
            conversionA = self.convert(edge.target)
            if edge.source.type() is Item.IndividualNode:
                conversionB = self.convert(edge.source)
            else:
                conversionB = self._converted_meta_individuals[edge.source.diagram.name][edge.source.id]
            anns = self.getAxiomAnnotationSet(edge)
            self.addAxiom(self.df.getOWLClassAssertionAxiom(conversionA, conversionB, anns))

    def createDataPropertyAssertionAxiom(self, edge):
        """
        Generate a OWL 2 DataPropertyAssertion axiom.
        :type edge: MembershipEdge
        """
        if OWLAxiom.DataPropertyAssertion in self.axiomsList:
            conversionA = self.convert(edge.target)
            conversionB = self.convert(edge.source)[0]
            conversionC = self.convert(edge.source)[1]
            anns = self.getAxiomAnnotationSet(edge)
            self.addAxiom(self.df.getOWLDataPropertyAssertionAxiom(conversionA, conversionB, conversionC, anns))

    def createDataPropertyAxiom(self, node):
        """
        Generate OWL 2 Data Property specific axioms.
        :type node: AttributeNode
        """
        if OWLAxiom.FunctionalDataProperty in self.axiomsList:
            if node.isFunctional():
                conversion = self.convert(node)
                self.addAxiom(self.df.getOWLFunctionalDataPropertyAxiom(conversion))

    def createDeclarationAxiom(self, node):
        """
        Generate a OWL 2 Declaration axiom.
        :type node: AbstractNode
        """
        if OWLAxiom.Declaration in self.axiomsList:
            conversion = self.convert(node)
            self.addAxiom(self.df.getOWLDeclarationAxiom(conversion))

    def createDifferentIndividualsAxiom(self, edge):
        """
        Generate a OWL 2 DifferentIndividuals axiom.
        :type edge: DifferentEdge
        """
        if OWLAxiom.DifferentIndividuals in self.axiomsList:
            collection = self.HashSet()
            anns = self.getAxiomAnnotationSet(edge)
            for node in [edge.source, edge.target]:
                if node.identity() in {Identity.Concept, Identity.Role, Identity.Attribute}:
                    # Perform punning of node
                    collection.add(self._converted_meta_individuals[node.diagram.name][node.id])
                else:
                    collection.add(self.convert(node))
            self.addAxiom(self.df.getOWLDifferentIndividualsAxiom(collection, anns))

    def createDisjointClassesAxiom(self, node):
        """
        Generate a OWL 2 DisjointClasses axiom.
        :type node: T <= ComplementNode|DisjointUnionNode
        """
        if OWLAxiom.DisjointClasses in self.axiomsList:
            if node.type() is Item.DisjointUnionNode:
                collection = self.HashSet()
                for operand in node.incomingNodes(lambda x: x.type() is Item.InputEdge):
                    conversion = self.convert(operand)
                    collection.add(conversion)
                self.addAxiom(self.df.getOWLDisjointClassesAxiom(self.vm.cast(self.Set, collection)))
            elif node.type() is Item.ComplementNode:
                operand = first(node.incomingNodes(lambda x: x.type() is Item.InputEdge))
                conversionA = self.convert(operand)
                for included in node.adjacentNodes(lambda x: x.type() in {Item.InclusionEdge, Item.EquivalenceEdge}):
                    conversionB = self.convert(included)
                    collection = self.HashSet()
                    collection.add(conversionA)
                    collection.add(conversionB)
                    self.addAxiom(self.df.getOWLDisjointClassesAxiom(self.vm.cast(self.Set, collection)))

    def createDisjointDataPropertiesAxiom(self, edge):
        """
        Generate a OWL 2 DisjointDataProperties axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.DisjointDataProperties in self.axiomsList:
            conversionA = self.convert(edge.source)
            conversionB = self.convert(edge.target)
            collection = self.HashSet()
            collection.add(conversionA)
            collection.add(conversionB)
            anns = self.getAxiomAnnotationSet(edge)
            self.addAxiom(self.df.getOWLDisjointDataPropertiesAxiom(collection, anns))

    def createDisjointObjectPropertiesAxiom(self, edge):
        """
        Generate a OWL 2 DisjointObjectProperties axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.DisjointObjectProperties in self.axiomsList:
            conversionA = self.convert(edge.source)
            conversionB = self.convert(edge.target)
            collection = self.HashSet()
            collection.add(conversionA)
            collection.add(conversionB)
            anns = self.getAxiomAnnotationSet(edge)
            self.addAxiom(self.df.getOWLDisjointObjectPropertiesAxiom(collection, anns))

    def createEquivalentClassesAxiom(self, edge):
        """
        Generate a OWL 2 EquivalentClasses axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.EquivalentClasses in self.axiomsList:
            anns = self.getAxiomAnnotationSet(edge)
            if self.normalize:
                for source, target in ((edge.source, edge.target), (edge.target, edge.source)):
                    if source.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                        # If we have a domain/range restriction node as source for the inclusion
                        # we need to check whether the inclusion edge is just expressing an axiom
                        # among ObjectPropertyDomain, ObjectPropertyRange, DataPropertyDomain,
                        # DataPropertyRange, in which case we do not generate also the SubClassOf
                        # axiom because it would be redundant.
                        if not source.isRestrictionQualified() and source.restriction() is Restriction.Exists:
                            continue
                    if source.type() in {Item.DisjointUnionNode, Item.UnionNode}:
                        # (A OR B) ISA C needs to be normalized to (A ISA C) && (B ISA C)
                        f1 = lambda x: x.type() is Item.InputEdge
                        f2 = lambda x: x.identity() is Identity.Concept
                        for operand in source.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                            conversionA = self.convert(operand)
                            conversionB = self.convert(target)
                            self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB, anns))
                    elif edge.target.type() is Item.IntersectionNode:
                        # A ISA (B AND C) needs to be normalized to A ISA B && A ISA C
                        f1 = lambda x: x.type() is Item.InputEdge
                        f2 = lambda x: x.identity() is Identity.Concept
                        for operand in target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                            conversionA = self.convert(source)
                            conversionB = self.convert(operand)
                            self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB, anns))
                    else:
                        conversionA = self.convert(source)
                        conversionB = self.convert(target)
                        self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB, anns))
            else:
                conversionA = self.convert(edge.source)
                conversionB = self.convert(edge.target)
                collection = self.HashSet()
                collection.add(conversionA)
                collection.add(conversionB)
                self.addAxiom(self.df.getOWLEquivalentClassesAxiom(collection, anns))

    def createEquivalentDataPropertiesAxiom(self, edge):
        """
        Generate a OWL 2 EquivalentDataProperties axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.EquivalentDataProperties in self.axiomsList:
            anns = self.getAxiomAnnotationSet(edge)
            if self.normalize:
                for source, target in ((edge.source, edge.target), (edge.target, edge.source)):
                    conversionA = self.convert(source)
                    conversionB = self.convert(target)
                    self.addAxiom(self.df.getOWLSubDataPropertyOfAxiom(conversionA, conversionB, anns))
            else:
                conversionA = self.convert(edge.source)
                conversionB = self.convert(edge.target)
                collection = self.HashSet()
                collection.add(conversionA)
                collection.add(conversionB)
                self.addAxiom(self.df.getOWLEquivalentDataPropertiesAxiom(collection, anns))

    def createEquivalentObjectPropertiesAxiom(self, edge):
        """
        Generate a OWL 2 EquivalentObjectProperties axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.EquivalentObjectProperties in self.axiomsList:
            anns = self.getAxiomAnnotationSet(edge)
            if self.normalize:
                for source, target in ((edge.source, edge.target), (edge.target, edge.source)):
                    conversionA = self.convert(source)
                    conversionB = self.convert(target)
                    self.addAxiom(self.df.getOWLSubObjectPropertyOfAxiom(conversionA, conversionB, anns))
            else:
                conversionA = self.convert(edge.source)
                conversionB = self.convert(edge.target)
                collection = self.HashSet()
                collection.add(conversionA)
                collection.add(conversionB)
                self.addAxiom(self.df.getOWLEquivalentObjectPropertiesAxiom(collection, anns))

    def createHasKeyAxiom(self, node):
        """
        Generate a OWL 2 HasKeyAxiom starting from node.
        :type node: HasKeyNode
        """
        if OWLAxiom.HasKey in self.axiomsList:
            properties = self.HashSet()
            expression = self.convert(node)[0]
            for prop in self.convert(node)[1:]:
                properties.add(prop)
            self.addAxiom(self.df.getOWLHasKeyAxiom(expression, properties))

    def createInverseObjectPropertiesAxiom(self, edge):
        """
        Generate a OWL 2 InverseObjectProperties axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.InverseObjectProperties in self.axiomsList:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.RoleNode
            if edge.source.type() is Item.RoleInverseNode:
                forward = edge.target
                inverse = first(edge.source.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            else:
                forward = edge.source
                inverse = first(edge.target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            conversionA = self.convert(forward)
            conversionB = self.convert(inverse)
            self.addAxiom(self.df.getOWLInverseObjectPropertiesAxiom(conversionA, conversionB))

    def createNegativeDataPropertyAssertionAxiom(self, edge):
        """
        Generate a OWL 2 NegativeObjectPropertyAssertion axiom.
        :type edge: MembershipEdge
        """
        if OWLAxiom.NegativeDataPropertyAssertion in self.axiomsList:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity() is Identity.Attribute
            conversionA = self.convert(first(edge.target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)))
            conversionB = self.convert(edge.source)[0]
            conversionC = self.convert(edge.source)[1]
            anns = self.getAxiomAnnotationSet(edge)
            self.addAxiom(self.df.getOWLNegativeDataPropertyAssertionAxiom(conversionA, conversionB, conversionC, anns))

    def createNegativeObjectPropertyAssertionAxiom(self, edge):
        """
        Generate a OWL 2 NegativeObjectPropertyAssertion axiom.
        :type edge: MembershipEdge
        """
        if OWLAxiom.NegativeObjectPropertyAssertion in self.axiomsList:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity() is Identity.Role
            conversionA = self.convert(first(edge.target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)))
            conversionB = self.convert(edge.source)[0]
            conversionC = self.convert(edge.source)[1]
            anns = self.getAxiomAnnotationSet(edge)
            self.addAxiom(self.df.getOWLNegativeObjectPropertyAssertionAxiom(conversionA, conversionB, conversionC, anns))

    def createObjectPropertyAxiom(self, node):
        """
        Generate OWL 2 ObjectProperty specific axioms.
        :type node: RoleNode
        """
        if OWLAxiom.FunctionalObjectProperty in self.axiomsList:
            if node.isFunctional():
                conversion = self.convert(node)
                self.addAxiom(self.df.getOWLFunctionalObjectPropertyAxiom(conversion))
        if OWLAxiom.InverseFunctionalObjectProperty in self.axiomsList:
            if node.isInverseFunctional():
                conversion = self.convert(node)
                self.addAxiom(self.df.getOWLInverseFunctionalObjectPropertyAxiom(conversion))
        if OWLAxiom.AsymmetricObjectProperty in self.axiomsList:
            if node.isAsymmetric():
                conversion = self.convert(node)
                self.addAxiom(self.df.getOWLAsymmetricObjectPropertyAxiom(conversion))
        if OWLAxiom.IrreflexiveObjectProperty in self.axiomsList:
            if node.isIrreflexive():
                conversion = self.convert(node)
                self.addAxiom(self.df.getOWLIrreflexiveObjectPropertyAxiom(conversion))
        if OWLAxiom.ReflexiveObjectProperty in self.axiomsList:
            if node.isReflexive():
                conversion = self.convert(node)
                self.addAxiom(self.df.getOWLReflexiveObjectPropertyAxiom(conversion))
        if OWLAxiom.SymmetricObjectProperty in self.axiomsList:
            if node.isSymmetric():
                conversion = self.convert(node)
                self.addAxiom(self.df.getOWLSymmetricObjectPropertyAxiom(conversion))
        if OWLAxiom.TransitiveObjectProperty in self.axiomsList:
            if node.isTransitive():
                conversion = self.convert(node)
                self.addAxiom(self.df.getOWLTransitiveObjectPropertyAxiom(conversion))

    def createObjectPropertyAssertionAxiom(self, edge):
        """
        Generate a OWL 2 ObjectPropertyAssertion axiom.
        :type edge: MembershipEdge
        """
        if OWLAxiom.ObjectPropertyAssertion in self.axiomsList:
            conversionA = self.convert(edge.target)
            conversionB = self.convert(edge.source)[0]
            conversionC = self.convert(edge.source)[1]
            self.addAxiom(self.df.getOWLObjectPropertyAssertionAxiom(conversionA, conversionB, conversionC))

    def createPropertyDomainAxiom(self, node):
        """
        Generate OWL 2 ObjectPropertyDomain and DataPropertyDomain axioms.
        :type node: DomainRestrictionNode
        """
        if OWLAxiom.ObjectPropertyDomain in self.axiomsList:
            if not node.isRestrictionQualified() and node.restriction() is Restriction.Exists:
                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.identity() is Identity.Role
                role = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                if role:
                    f3 = lambda x: x.type() is Item.InclusionEdge
                    f4 = lambda x: x.type() is Item.EquivalenceEdge
                    f5 = lambda x: x.identity() is Identity.Concept
                    for concept in node.outgoingNodes(f3, f5) | node.adjacentNodes(f4, f5):
                        conversionA = self.convert(role)
                        conversionB = self.convert(concept)
                        self.addAxiom(self.df.getOWLObjectPropertyDomainAxiom(conversionA, conversionB))
        if OWLAxiom.DataPropertyDomain in self.axiomsList:
            if not node.isRestrictionQualified() and node.restriction() is Restriction.Exists:
                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.identity() is Identity.Attribute
                attribute = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                if attribute:
                    f3 = lambda x: x.type() is Item.InclusionEdge
                    f4 = lambda x: x.type() is Item.EquivalenceEdge
                    f5 = lambda x: x.identity() is Identity.Concept
                    for concept in node.outgoingNodes(f3, f5) | node.adjacentNodes(f4, f5):
                        conversionA = self.convert(attribute)
                        conversionB = self.convert(concept)
                        self.addAxiom(self.df.getOWLDataPropertyDomainAxiom(conversionA, conversionB))

    def createPropertyRangeAxiom(self, node):
        """
        Generate OWL 2 ObjectPropertyRange and DataPropertyRange axioms.
        :type node: RangeRestrictionNode
        """
        if OWLAxiom.ObjectPropertyRange in self.axiomsList:
            if not node.isRestrictionQualified() and node.restriction() is Restriction.Exists:
                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.identity() is Identity.Role
                role = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                if role:
                    f3 = lambda x: x.type() is Item.InclusionEdge
                    f4 = lambda x: x.type() is Item.EquivalenceEdge
                    f5 = lambda x: x.identity() is Identity.Concept
                    for concept in node.outgoingNodes(f3, f5) | node.adjacentNodes(f4, f5):
                        conversionA = self.convert(role)
                        conversionB = self.convert(concept)
                        self.addAxiom(self.df.getOWLObjectPropertyRangeAxiom(conversionA, conversionB))
        if OWLAxiom.DataPropertyRange in self.axiomsList:
            if not node.isRestrictionQualified() and node.restriction() is Restriction.Exists:
                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.identity() is Identity.Attribute
                attribute = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                if attribute:
                    f3 = lambda x: x.type() is Item.InclusionEdge
                    f4 = lambda x: x.type() is Item.EquivalenceEdge
                    f5 = lambda x: x.identity() is Identity.ValueDomain
                    for datatype in node.outgoingNodes(f3, f5) | node.adjacentNodes(f4, f5):
                        conversionA = self.convert(attribute)
                        conversionB = self.convert(datatype)
                        self.addAxiom(self.df.getOWLDataPropertyRangeAxiom(conversionA, conversionB))

    def createSameIndividualAxiom(self, edge):
        """
        Generate a OWL2 SameIndividual axiom.
        :type edge: SameEdge
        """
        if OWLAxiom.SameIndividual in self.axiomsList:
            collection = self.HashSet()
            anns = self.getAxiomAnnotationSet(edge)
            for node in [edge.source, edge.target]:
                if node.identity() in {Identity.Concept, Identity.Role, Identity.Attribute}:
                    # Perform punning of node
                    collection.add(self._converted_meta_individuals[node.diagram.name][node.id])
                else: # Node is already an IndividualNode
                    collection.add(self.convert(node))
            self.addAxiom(self.df.getOWLSameIndividualAxiom(collection, anns))

    def createSubclassOfAxiom(self, edge):
        """
        Generate a OWL 2 SubclassOf axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.SubClassOf in self.axiomsList:

            if Item.ComplementNode in {edge.source.type(), edge.target.type()}:
                # We need to discard the case where a complement node is involved in the inclusion, since
                # we changed the axiom SubClassOf(ClassExpression ObjectComplementOf(ClassExpression)) to
                # be DisjointClasses(ClassExpression ...) so that it will be serialized in the same way
                # as for the Disjoint Union node.
                return

            if edge.source.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                # If we have a domain/range restriction node as source for the inclusion
                # we need to check whether the inclusion edge is just expressing an axiom
                # among ObjectPropertyDomain, ObjectPropertyRange, DataPropertyDomain,
                # DataPropertyRange, in which case we do not generate also the SubClassOf
                # axiom because it would be redundant.
                if not edge.source.isRestrictionQualified() and edge.source.restriction() is Restriction.Exists:
                    return

            anns = self.getAxiomAnnotationSet(edge)
            if edge.source.type() in {Item.DisjointUnionNode, Item.UnionNode} and self.normalize:
                # (A OR B) ISA C needs to be normalized to (A ISA C) && (B ISA C)
                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.identity() is Identity.Concept
                for operand in edge.source.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                    conversionA = self.convert(operand)
                    conversionB = self.convert(edge.target)
                    self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB, anns))
            elif edge.target.type() is Item.IntersectionNode and self.normalize:
                # A ISA (B AND C) needs to be normalized to A ISA B && A ISA C
                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.identity() is Identity.Concept
                for operand in edge.target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                    conversionA = self.convert(edge.source)
                    conversionB = self.convert(operand)
                    self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB, anns))
            else:
                conversionA = self.convert(edge.source)
                conversionB = self.convert(edge.target)
                self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB, anns))

    def createSubDataPropertyOfAxiom(self, edge):
        """
        Generate a OWL 2 SubDataPropertyOf axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.SubDataPropertyOf in self.axiomsList:
            conversionA = self.convert(edge.source)
            conversionB = self.convert(edge.target)
            anns = self.getAxiomAnnotationSet(edge)
            self.addAxiom(self.df.getOWLSubDataPropertyOfAxiom(conversionA, conversionB, anns))

    def createSubObjectPropertyOfAxiom(self, edge):
        """
        Generate a OWL 2 SubObjectPropertyOf axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.SubObjectPropertyOf in self.axiomsList:
            conversionA = self.convert(edge.source)
            conversionB = self.convert(edge.target)
            anns = self.getAxiomAnnotationSet(edge)
            self.addAxiom(self.df.getOWLSubObjectPropertyOfAxiom(conversionA, conversionB, anns))

    def createSubPropertyChainOfAxiom(self, edge):
        """
        Generate a OWL 2 SubPropertyChainOf axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.SubObjectPropertyOf in self.axiomsList:
            conversionA = self.convert(edge.source)
            conversionB = self.convert(edge.target)
            anns = self.getAxiomAnnotationSet(edge)
            self.addAxiom(self.df.getOWLSubPropertyChainOfAxiom(conversionA, conversionB, anns))

    def createNDCNamedIndividual(self, entity):
        """
        Generate an OWL 2 NamedIndividual for NDC entities.
        """
        ind = self.df.getOWLNamedIndividual(self.IRI.create(entity.uri.toPython()))
        if OWLAxiom.Declaration in self.axiomsList:
            self.addAxiom(self.df.getOWLDeclarationAxiom(ind))
        for s, p, o in entity.triples():
            if p == RDF.type and OWLAxiom.ClassAssertion in self.axiomsList:
                inst = self.df.getOWLClassAssertionAxiom(
                    self.df.getOWLClass(self.IRI.create(o.toPython())),
                    ind,
                )
                self.addAxiom(inst)
            elif OWLAxiom.Annotation in self.axiomsList:
                prop = self.df.getOWLAnnotationProperty(self.IRI.create(p.toPython()))
                if isinstance(o, URIRef):
                    value = self.IRI.create(o.toPython())
                elif isinstance(o, Literal) and o.datatype:
                    dtype = self.df.getOWLDatatype(o.datatype.toPython())
                    value = self.df.getOWLLiteral(o.toPython(), dtype)
                elif isinstance(o, Literal) and o.language:
                    value = self.df.getOWLLiteral(o.toPython(), o.language)
                else:
                    value = self.df.getOWLLiteral(o.toPython())
                assertion = self.df.getOWLAnnotationAssertionAxiom(prop, ind.getIRI(), value)
                self.addAxiom(assertion)

    def createNDCNamedIndividuals(self):
        """
        Generate OWL 2 NamedIndividuals for NDC entities.
        """
        if OWLAxiom.Annotation in self.axiomsList:
            dataset = NDCDataset()
            dataset.load()
            for annotation in self.project.ontologyIRI.annotationAssertions:
                if str(annotation.assertionProperty) in [
                    DCTERMS.rightsHolder.toPython(),
                    DCTERMS.publisher.toPython(),
                    DCTERMS.creator.toPython(),
                ]:
                    agent = first(dataset.agents(URIRef(str(annotation.value))))
                    self.createNDCNamedIndividual(agent)
                elif str(annotation.assertionProperty) == DCAT.contactPoint.toPython():
                    contact = first(dataset.contactPoints(URIRef(str(annotation.value))))
                    self.createNDCNamedIndividual(contact)
                elif str(annotation.assertionProperty) == ADMS.hasSemanticAssetDistribution.toPython():
                    distrib = first(dataset.distributions(URIRef(str(annotation.value))))
                    self.createNDCNamedIndividual(distrib)
                elif str(annotation.assertionProperty) == ADMS.semanticAssetInUse.toPython():
                    proj = first(dataset.projects(URIRef(str(annotation.value))))
                    self.createNDCNamedIndividual(proj)

    #############################################
    #   MAIN WORKER
    #################################

    @QtCore.pyqtSlot()
    def run(self):
        """
        Main worker.
        """
        try:
            self.sgnStarted.emit()
            self.vm.attachThreadToJVM()

            #############################################
            # INITIALIZE ONTOLOGY
            #################################

            ontologyIRI = str(self.project.ontologyIRI)
            versionIRI = self.project.version
            if versionIRI:
                ontologyID = self.OWLOntologyID(self.IRI.create(ontologyIRI),
                                                self.IRI.create(versionIRI))
            else:
                ontologyID = self.OWLOntologyID(self.IRI.create(ontologyIRI))
            self.man = self.OWLManager.createOWLOntologyManager()
            self.df = self.OWLManager.getOWLDataFactory()
            self.ontology = self.man.createOntology(ontologyID)
            self.pm = self.DefaultPrefixManager()

            for prefix, ns in self.project.prefixDictItems():
                self.pm.setPrefix(prefix, ns)

            #############################################
            # ONTOLOGY ANNOTATIONS
            #################################

            if OWLAxiom.Annotation in self.axiomsList:
                for annotation in self.project.ontologyIRI.annotationAssertions:
                    value = self.getOWLApiAnnotation(annotation)
                    self.ontology.applyChange(self.AddOntologyAnnotation(self.ontology, value))

            self.createNDCNamedIndividuals()
            LOGGER.debug('Initialized OWL 2 Ontology: %s', ontologyIRI)

            #############################################
            # NODES PRE-PROCESSING
            #################################

            # for node in self.project.nodes():
            for diagram in self.selected_diagrams:
                for node in diagram.nodes():
                    self.convert(node)
                    self.step(+1)

            LOGGER.debug('Pre-processed %s nodes into OWL 2 expressions', len(self.converted()))

            #############################################
            # AXIOMS FROM NODES
            #################################

            # for node in self.project.nodes():
            for diagram in self.selected_diagrams:
                for node in diagram.nodes():
                    if node.type() is Item.DisjointUnionNode:
                        self.createDisjointClassesAxiom(node)
                    elif node.type() is Item.ComplementNode:
                        if node.identity() is Identity.Concept:
                            self.createDisjointClassesAxiom(node)
                    elif node.type() is Item.DomainRestrictionNode:
                        self.createPropertyDomainAxiom(node)
                    elif node.type() is Item.RangeRestrictionNode:
                        self.createPropertyRangeAxiom(node)
                    elif node.type() is Item.HasKeyNode:
                        self.createHasKeyAxiom(node)

                    if node.isPredicate():
                        self.createAnnotationAssertionAxioms(node)

                    self.step(+1)

            LOGGER.debug('Generated OWL 2 axioms from nodes (axioms = %s)', len(self.axioms()))

            #############################################
            # AXIOMS FROM EDGES
            #################################

            # for edge in self.project.edges():
            for diagram in self.selected_diagrams:
                for edge in diagram.edges():

                    #############################################
                    # INCLUSION
                    #################################

                    if edge.type() is Item.InclusionEdge:
                        # CONCEPTS
                        if edge.source.identity() is Identity.Concept and edge.target.identity() is Identity.Concept:
                            self.createSubclassOfAxiom(edge)
                        # ROLES
                        elif edge.source.identity() is Identity.Role and edge.target.identity() is Identity.Role:
                            if edge.source.type() is Item.RoleChainNode:
                                self.createSubPropertyChainOfAxiom(edge)
                            elif edge.source.type() in {Item.RoleNode, Item.RoleInverseNode}:
                                if edge.target.type() is Item.ComplementNode:
                                    self.createDisjointObjectPropertiesAxiom(edge)
                                elif edge.target.type() in {Item.RoleNode, Item.RoleInverseNode}:
                                    self.createSubObjectPropertyOfAxiom(edge)
                        # ATTRIBUTES
                        elif edge.source.identity() is Identity.Attribute and edge.target.identity() is Identity.Attribute:
                            if edge.source.type() is Item.AttributeNode:
                                if edge.target.type() is Item.ComplementNode:
                                    self.createDisjointDataPropertiesAxiom(edge)
                                elif edge.target.type() is Item.AttributeNode:
                                    self.createSubDataPropertyOfAxiom(edge)
                        # VALUE DOMAIN (ONLY DATA PROPERTY RANGE)
                        elif edge.source.type() is Item.RangeRestrictionNode and edge.target.identity() is Identity.ValueDomain:
                            # This is being handled already in createPropertyRangeAxiom.
                            pass
                        else:
                            raise DiagramMalformedError(edge, 'invalid inclusion assertion')

                    #############################################
                    # EQUIVALENCE
                    #################################

                    elif edge.type() is Item.EquivalenceEdge:

                        # CONCEPTS
                        if edge.source.identity() is Identity.Concept and edge.target.identity() is Identity.Concept:
                            self.createEquivalentClassesAxiom(edge)
                        # ROLES
                        elif edge.source.identity() is Identity.Role and edge.target.identity() is Identity.Role:
                            if Item.RoleInverseNode in {edge.source.type(), edge.target.type()}:
                                self.createInverseObjectPropertiesAxiom(edge)
                            else:
                                self.createEquivalentObjectPropertiesAxiom(edge)
                        # ATTRIBUTES
                        elif edge.source.identity() is Identity.Attribute and edge.target.identity() is Identity.Attribute:
                            self.createEquivalentDataPropertiesAxiom(edge)
                        else:
                            raise DiagramMalformedError(edge, 'invalid equivalence assertion')

                    #############################################
                    # MEMBERSHIP
                    #################################

                    elif edge.type() is Item.MembershipEdge:

                        # CONCEPTS
                        if Identity.Individual in edge.source.identities() and edge.target.identity() is Identity.Concept:
                            self.createClassAssertionAxiom(edge)
                        # ROLES
                        elif edge.source.identity() is Identity.RoleInstance:
                            if edge.target.type() is Item.ComplementNode:
                                self.createNegativeObjectPropertyAssertionAxiom(edge)
                            else:
                                self.createObjectPropertyAssertionAxiom(edge)
                        # ATTRIBUTES
                        elif edge.source.identity() is Identity.AttributeInstance:
                            if edge.target.type() is Item.ComplementNode:
                                self.createNegativeDataPropertyAssertionAxiom(edge)
                            else:
                                self.createDataPropertyAssertionAxiom(edge)
                        else:
                            raise DiagramMalformedError(edge, 'invalid membership assertion')

                    #############################################
                    # SAME
                    #################################

                    elif edge.type() is Item.SameEdge:
                        if edge.source.identity() in {Identity.Individual, Identity.Concept, Identity.Role, Identity.Attribute} and \
                           edge.target.identity() in {Identity.Individual, Identity.Concept, Identity.Role, Identity.Attribute} and \
                           edge.source.identities().intersection(edge.target.identities()):
                            self.createSameIndividualAxiom(edge)
                        else:
                            raise DiagramMalformedError(edge, 'invalid sameIndividual assertion')

                    #############################################
                    # DIFFERENT
                    #################################

                    elif edge.type() is Item.DifferentEdge:
                        if edge.source.identity() in {Identity.Individual, Identity.Concept, Identity.Role, Identity.Attribute} and \
                           edge.target.identity() in {Identity.Individual, Identity.Concept, Identity.Role, Identity.Attribute} and \
                           edge.source.identities().intersection(edge.target.identities()):
                            self.createDifferentIndividualsAxiom(edge)
                        else:
                            raise DiagramMalformedError(edge, 'invalid differentIndividuals assertion')

                    self.step(+1)

            LOGGER.debug('Generated OWL 2 axioms from edges (axioms = %s)', len(self.axioms()))

            #############################################
            # APPLY GENERATED AXIOMS
            #################################

            LOGGER.debug('Applying OWL 2 axioms on the OWL 2 Ontology')

            for axiom in self.axioms():
                self.man.addAxiom(self.ontology, axiom)

            #############################################
            # IMPORT DECLARATIONS
            #################################

            LOGGER.debug('Adding import declarations to the OWL 2 Ontology')

            for impOnt in self.project.importedOntologies:
                try:
                    docObj = None
                    if impOnt.isLocalDocument:
                        docObj = self.JavaFileClass(impOnt.docLocation)
                    else:
                        docObj = self.URIClass(impOnt.docLocation)
                    docLocationIRI = self.IRI.create(docObj)
                    impOntIRI = self.IRI.create(impOnt.ontologyIRI)
                    # iriMapper = self.IRIMapperClass(impOntIRI, docLocationIRI)
                    # self.man.getIRIMappers().add(iriMapper)
                    impDecl = self.df.getOWLImportsDeclaration(impOntIRI)
                    addImp = self.AddImportClass(self.ontology, impDecl)
                    self.man.applyChange(addImp)
                except Exception as e:
                    LOGGER.exception('The import declaration <{}> cannot be added.\nError:{}'.format(impOnt, str(e)))
                else:
                    LOGGER.debug('Ontology declaration ({}) correctly added.'.format(impOnt))

            #############################################
            # SERIALIZE THE ONTOLOGY
            #################################

            if self.path:
                if self.syntax is OWLSyntax.Functional:
                    DocumentFormat = self.FunctionalSyntaxDocumentFormat
                    DocumentFilter = OWLFunctionalSyntaxDocumentFilter
                elif self.syntax is OWLSyntax.Manchester:
                    DocumentFormat = self.ManchesterSyntaxDocumentFormat
                    DocumentFilter = OWLManchesterSyntaxDocumentFilter
                elif self.syntax is OWLSyntax.RDF:
                    DocumentFormat = self.RDFXMLDocumentFormat
                    DocumentFilter = RDFXMLDocumentFilter
                elif self.syntax is OWLSyntax.Turtle:
                    DocumentFormat = self.TurtleDocumentFormat
                    DocumentFilter = TurtleDocumentFilter
                else:
                    raise TypeError('unsupported syntax (%s)' % self.syntax)

                LOGGER.debug('Serializing the OWL 2 Ontology in %s', self.syntax.value)

                # COPY PREFIXES
                ontoFormat = DocumentFormat()
                ontoFormat.copyPrefixesFrom(self.pm)

                # CREARE TARGET STREAM
                stream = self.StringDocumentTarget()
                stream = self.vm.cast(self.OWLOntologyDocumentTarget, stream)
                # SAVE THE ONTOLOGY TO DISK
                self.man.setOntologyFormat(self.ontology, ontoFormat)
                self.man.saveOntology(self.ontology, stream)
                stream = self.vm.cast(self.StringDocumentTarget, stream)
                string = DocumentFilter(stream.toString())
                fwrite(string, self.path)
                # REMOVE RANDOM FILES GENERATED BY OWL API
                fremove(os.path.join(os.path.dirname(self.path), 'catalog-v001.xml'))
        except DiagramMalformedError as e:
            LOGGER.warning('Malformed expression detected on {0}: {1} ... aborting!'.format(e.item, e))
            self.sgnErrored.emit(e)
            if not self.path:
                raise e
        except Exception as e:
            LOGGER.exception('OWL 2 export could not be completed')
            self.sgnErrored.emit(e)
            if not self.path:
                raise e
        else:
            self.sgnCompleted.emit()
        finally:
            self.vm.detachThreadFromJVM()
            self.finished.emit()
