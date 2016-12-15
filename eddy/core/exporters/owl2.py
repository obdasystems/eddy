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

from jnius import autoclass, cast, detach

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy import APPNAME, BUG_TRACKER, ORGANIZATION
from eddy.core.common import HasThreadingSystem, HasWidgetSystem
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.graphol import Item, Identity, Special, Restriction
from eddy.core.datatypes.owl import Datatype, Facet, OWLAxiom, OWLSyntax
from eddy.core.datatypes.system import File
from eddy.core.diagram import DiagramMalformedError
from eddy.core.exporters.common import AbstractOntologyExporter
from eddy.core.functions.fsystem import fwrite, fremove
from eddy.core.functions.misc import first, clamp, isEmpty
from eddy.core.functions.misc import rstrip, postfix, format_exception
from eddy.core.functions.owl import OWLShortIRI, OWLAnnotationText
from eddy.core.functions.owl import OWLFunctionalDocumentFilter
from eddy.core.functions.path import expandPath, openPath
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger
from eddy.core.worker import AbstractWorker

from eddy.ui.fields import ComboBox, CheckBox
from eddy.ui.progress import BusyProgressDialog
from eddy.ui.syntax import SyntaxValidationWorker


LOGGER = getLogger()

        
class OWLOntologyExporter(AbstractOntologyExporter, HasThreadingSystem):
    """
    Extends AbstractProjectExporter with facilities to export a Graphol project into a valid OWL 2 ontology.
    """
    def __init__(self, project, session=None):
        """
        Initialize the OWL Project exporter
        :type project: Project
        :type session: Session
        """
        super().__init__(project, session)
        self.items = list(project.edges()) + list(filter(lambda n: not n.adjacentNodes(), project.nodes()))
        self.path = None
        self.progress = None

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
        dialog = OWLOntologyExporterDialog(self.project, self.path, self.session)
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
        if not self.project.isEmpty():
            self.path = path
            self.progress = BusyProgressDialog('Performing syntax check...')
            self.progress.show()
            worker = SyntaxValidationWorker(0, self.items, self.project)
            connect(worker.sgnCompleted, self.onSyntaxCheckCompleted)
            connect(worker.sgnSyntaxError, self.onSyntaxCheckErrored)
            self.startThread('syntaxCheck', worker)


class OWLOntologyExporterDialog(QtWidgets.QDialog, HasThreadingSystem, HasWidgetSystem):
    """
    Extends QtWidgets.QDialog providing the form used to perform Graphol -> OWL ontology translation.
    """
    def __init__(self, project, path, session):
        """
        Initialize the form dialog.
        :type project: Project
        :type path: str
        :type session: Session
        """
        super().__init__(session)

        self.path = expandPath(path)
        self.project = project

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        #############################################
        # MAIN FORM AREA
        #################################

        ## SYNTAX
        field = ComboBox(self)
        for syntax in OWLSyntax:
            field.addItem(syntax.value, syntax)
        field.setCurrentIndex(0)
        field.setFont(Font('Roboto', 12))
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
        intensionalLayout.addWidget(self.widget(OWLAxiom.InverseFunctionalObjectProperty.value), 3, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.InverseObjectProperties.value), 4, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.IrreflexiveObjectProperty.value), 5, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.ObjectPropertyDomain.value), 6, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.ObjectPropertyRange.value), 7, 1)
        intensionalLayout.addWidget(self.widget(OWLAxiom.ReflexiveObjectProperty.value), 0, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.SubClassOf.value), 1, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.SubDataPropertyOf.value), 2, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.SubObjectPropertyOf.value), 3, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.SymmetricObjectProperty.value), 4, 2)
        intensionalLayout.addWidget(self.widget(OWLAxiom.TransitiveObjectProperty.value), 5, 2)
        intensionalGroup = QtWidgets.QGroupBox('Intensional', self)
        intensionalGroup.setLayout(intensionalLayout)
        extensionalLayout = QtWidgets.QGridLayout()
        extensionalLayout.setColumnMinimumWidth(0, 230)
        extensionalLayout.setColumnMinimumWidth(1, 230)
        extensionalLayout.setColumnMinimumWidth(2, 230)
        extensionalLayout.addWidget(self.widget(OWLAxiom.ClassAssertion.value), 0, 0)
        extensionalLayout.addWidget(self.widget(OWLAxiom.DataPropertyAssertion.value), 1, 0)
        extensionalLayout.addWidget(self.widget(OWLAxiom.NegativeDataPropertyAssertion.value), 0, 1)
        extensionalLayout.addWidget(self.widget(OWLAxiom.NegativeObjectPropertyAssertion.value), 1, 1)
        extensionalLayout.addWidget(self.widget(OWLAxiom.ObjectPropertyAssertion.value), 0, 2)
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
        normalization.setFont(Font('Roboto', 12))
        normalization.setObjectName('normalization')
        self.addWidget(normalization)

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Ok)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setFont(Font('Roboto', 12))
        confirmation.setObjectName('confirmation')
        connect(confirmation.accepted, self.run)
        connect(confirmation.rejected, self.reject)
        self.addWidget(confirmation)

        confirmationLayout = QtWidgets.QHBoxLayout()
        confirmationLayout.setContentsMargins(0, 0, 0, 0)
        confirmationLayout.addWidget(self.widget('normalization'), 0 , QtCore.Qt.AlignLeft)
        confirmationLayout.addWidget(self.widget('confirmation'), 0, QtCore.Qt.AlignRight)
        confirmationArea = QtWidgets.QWidget()
        confirmationArea.setLayout(confirmationLayout)

        #############################################
        # CONFIGURE LAYOUT
        #################################

        for axiom in OWLAxiom.forProfile(self.project.profile.type()):
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

        self.setFixedSize(self.sizeHint())
        self.setFont(Font('Roboto', 12))
        self.setLayout(mainLayout)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('{} Export'.format(self.project.profile.name()))

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
        Returns whether the current ontolofy needs to be normalized, or not.
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
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No)
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

    @QtCore.pyqtSlot()
    def onCompleted(self):
        """
        Executed whenever the translation completes.
        """
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No)
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
            checkbox = self.widget(axiom.value)
            checkbox.setEnabled(False)

    @QtCore.pyqtSlot()
    def run(self):
        """
        Perform the Graphol -> OWL translation in a separate thread.
        """
        LOGGER.info('Exporting project %s in OWL 2 format: %s', self.project.name, self.path)
        worker = OWLOntologyExporterWorker(self.project, self.path,
           axioms=self.axioms(), normalize=self.normalize(),
           syntax=self.syntax())
        connect(worker.sgnStarted, self.onStarted)
        connect(worker.sgnCompleted, self.onCompleted)
        connect(worker.sgnErrored, self.onErrored)
        connect(worker.sgnProgress, self.onProgress)
        self.startThread('OWL2Export', worker)


class OWLOntologyExporterWorker(AbstractWorker):
    """
    Extends AbstractWorker providing a worker thread that will perform the OWL 2 ontology generation.
    """
    sgnCompleted = QtCore.pyqtSignal()
    sgnErrored = QtCore.pyqtSignal(Exception)
    sgnProgress = QtCore.pyqtSignal(int, int)
    sgnStarted = QtCore.pyqtSignal()

    def __init__(self, project, path, **kwargs):
        """
        Initialize the OWL 2 Exporter worker.
        :type project: Project
        :type path: str
        """
        super().__init__()

        self.DefaultPrefixManager = autoclass('org.semanticweb.owlapi.util.DefaultPrefixManager')
        self.FunctionalSyntaxDocumentFormat = autoclass('org.semanticweb.owlapi.formats.FunctionalSyntaxDocumentFormat')
        self.HashSet = autoclass('java.util.HashSet')
        self.IRI = autoclass('org.semanticweb.owlapi.model.IRI')
        self.LinkedList = autoclass('java.util.LinkedList')
        self.List = autoclass('java.util.List')
        self.ManchesterSyntaxDocumentFormat = autoclass('org.semanticweb.owlapi.formats.ManchesterSyntaxDocumentFormat')
        self.OWLAnnotationValue = autoclass('org.semanticweb.owlapi.model.OWLAnnotationValue')
        self.OWLFacet = autoclass('org.semanticweb.owlapi.vocab.OWLFacet')
        self.OWL2Datatype = autoclass('org.semanticweb.owlapi.vocab.OWL2Datatype')
        self.OWLManager = autoclass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.OWLOntologyDocumentTarget = autoclass('org.semanticweb.owlapi.io.OWLOntologyDocumentTarget')
        self.RDFXMLDocumentFormat = autoclass('org.semanticweb.owlapi.formats.RDFXMLDocumentFormat')
        self.PrefixManager = autoclass('org.semanticweb.owlapi.model.PrefixManager')
        self.Set = autoclass('java.util.Set')
        self.StringDocumentTarget = autoclass('org.semanticweb.owlapi.io.StringDocumentTarget')
        self.TurtleDocumentFormat = autoclass('org.semanticweb.owlapi.formats.TurtleDocumentFormat')

        self.path = path
        self.project = project
        self.axiomsList = kwargs.get('axioms', set())
        self.normalize = kwargs.get('normalize', False)
        self.syntax = kwargs.get('syntax', OWLSyntax.Functional)

        self._axioms = set()
        self._converted = dict()

        self.df = None
        self.man = None
        self.num = 0
        self.max = len(self.project.nodes()) * 2 + len(self.project.edges())
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
        if node not in self._converted[node.diagram.name]:
            if node.type() is Item.ConceptNode:
                self._converted[node.diagram.name][node.id] = self.getConcept(node)
            elif node.type() is Item.AttributeNode:
                self._converted[node.diagram.name][node.id] = self.getAttribute(node)
            elif node.type() is Item.RoleNode:
                self._converted[node.diagram.name][node.id] = self.getRole(node)
            elif node.type() is Item.ValueDomainNode:
                self._converted[node.diagram.name][node.id] = self.getValueDomain(node)
            elif node.type() is Item.IndividualNode:
                self._converted[node.diagram.name][node.id] = self.getIndividual(node)
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
            else:
                raise ValueError('no conversion available for node %s' % node)
        return self._converted[node.diagram.name][node.id]

    def converted(self):
        """
        Returns the dictionary of converted nodes.
        :rtype: dict
        """
        return self._converted

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
        if facet is Facet.maxExclusive:
            return self.OWLFacet.valueOf('MAX_EXCLUSIVE')
        if facet is Facet.maxInclusive:
            return self.OWLFacet.valueOf('MAX_INCLUSIVE')
        if facet is Facet.minExclusive:
            return self.OWLFacet.valueOf('MIN_EXCLUSIVE')
        if facet is Facet.minInclusive:
            return self.OWLFacet.valueOf('MIN_INCLUSIVE')
        if facet is Facet.langRange:
            return self.OWLFacet.valueOf('LANG_RANGE')
        if facet is Facet.length:
            return self.OWLFacet.valueOf('LENGTH')
        if facet is Facet.maxLength:
            return self.OWLFacet.valueOf('MIN_LENGTH')
        if facet is Facet.minLength:
            return self.OWLFacet.valueOf('MIN_LENGTH')
        if facet is Facet.pattern:
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
        if node.special() is Special.Top:
            return self.df.getOWLTopDataProperty()
        if node.special() is Special.Bottom:
            return self.df.getOWLBottomDataProperty()
        return self.df.getOWLDataProperty(OWLShortIRI(self.project.prefix, node.text()), self.pm)

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
        if node.special() is Special.Top:
            return self.df.getOWLThing()
        if node.special() is Special.Bottom:
            return self.df.getOWLNothing()
        return self.df.getOWLClass(OWLShortIRI(self.project.prefix, node.text()), self.pm)

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

        return self.df.getOWLDatatypeRestriction(de, cast(self.Set, collection))

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
                    cardinalities.add(self.df.getOWLDataMinCardinality(max_cardinality, dpe, dre))
                if cardinalities.isEmpty():
                    raise DiagramMalformedError(node, 'missing cardinality')
                if cardinalities.size() > 1:
                    return self.df.getOWLDataIntersectionOf(cast(self.Set, cardinalities))
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
                    return self.df.getOWLObjectIntersectionOf(cast(self.Set, cardinalities))
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
        return self.df.getOWLObjectOneOf(cast(self.Set, individuals))

    def getFacet(self, node):
        """
        Build and returns a OWL 2 facet restriction using the given graphol node.
        :type node: FacetNode
        :rtype: OWLFacetRestriction
        """
        datatype = node.datatype
        if not datatype:
            raise DiagramMalformedError(node, 'disconnected facet node')
        literal = self.df.getOWLLiteral(node.value, self.getOWLApiDatatype(datatype))
        facet = self.getOWLApiFacet(node.facet)
        return self.df.getOWLFacetRestriction(facet, literal)

    def getIndividual(self, node):
        """
        Build and returns a OWL 2 individual using the given graphol node.
        :type node: IndividualNode
        :rtype: OWLNamedIndividual
        """
        if node.identity() is Identity.Individual:
            return self.df.getOWLNamedIndividual(OWLShortIRI(self.project.prefix, node.text()), self.pm)
        elif node.identity() is Identity.Value:
            return self.df.getOWLLiteral(node.value, self.getOWLApiDatatype(node.datatype))
        raise DiagramMalformedError(node, 'unsupported identity (%s)' % node.identity())

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
            return self.df.getOWLObjectIntersectionOf(cast(self.Set, collection))
        return self.df.getOWLDataIntersectionOf(cast(self.Set, collection))

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
            if operand.type() is not Item.IndividualNode:
                raise DiagramMalformedError(node, 'unsupported operand (%s)' % operand)
            conversion = self.convert(operand)
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
                    return self.df.getOWLObjectIntersectionOf(cast(self.Set, cardinalities))
                return cardinalities.iterator().next()
            raise DiagramMalformedError(node, 'unsupported restriction (%s)' % node.restriction())

    def getRole(self, node):
        """
        Build and returns a OWL 2 role using the given graphol node.
        :type node: RoleNode
        :rtype: OWLObjectProperty
        """
        if node.special() is Special.Top:
            return self.df.getOWLTopObjectProperty()
        elif node.special() is Special.Bottom:
            return self.df.getOWLBottomObjectProperty()
        return self.df.getOWLObjectProperty(OWLShortIRI(self.project.prefix, node.text()), self.pm)

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
        return cast(self.List, collection)

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
            return self.df.getOWLObjectUnionOf(cast(self.Set, collection))
        return self.df.getOWLDataUnionOf(cast(self.Set, collection))

    def getValueDomain(self, node):
        """
        Build and returns a OWL 2 datatype using the given graphol node.
        :type node: ValueDomainNode
        :rtype: OWLDatatype
        """
        return self.getOWLApiDatatype(node.datatype)

    #############################################
    #   AXIOMS GENERATION
    #################################

    def createAnnotationAssertionAxiom(self, node):
        """
        Generate a OWL 2 annotation axiom.
        :type node: AbstractNode
        """
        if OWLAxiom.Annotation in self.axiomsList:
            meta = self.project.meta(node.type(), node.text())
            if meta and not isEmpty(meta.get('description', '')):
                aproperty = self.df.getOWLAnnotationProperty(self.IRI.create("rdfs:comment"))
                value = self.df.getOWLLiteral(OWLAnnotationText(meta.get('description', '')))
                value = cast(self.OWLAnnotationValue, value)
                annotation = self.df.getOWLAnnotation(aproperty, value)
                conversion = self.convert(node)
                self.addAxiom(self.df.getOWLAnnotationAssertionAxiom(conversion.getIRI(), annotation))

    def createClassAssertionAxiom(self, edge):
        """
        Generate a OWL 2 ClassAssertion axiom.
        :type edge: MembershipEdge
        """
        if OWLAxiom.ClassAssertion in self.axiomsList:
            conversionA = self.convert(edge.target)
            conversionB = self.convert(edge.source)
            self.addAxiom(self.df.getOWLClassAssertionAxiom(conversionA, conversionB))

    def createDataPropertyAssertionAxiom(self, edge):
        """
        Generate a OWL 2 DataPropertyAssertion axiom.
        :type edge: MembershipEdge
        """
        if OWLAxiom.DataPropertyAssertion in self.axiomsList:
            conversionA = self.convert(edge.target)
            conversionB = self.convert(edge.source)[0]
            conversionC = self.convert(edge.source)[1]
            self.addAxiom(self.df.getOWLDataPropertyAssertionAxiom(conversionA, conversionB, conversionC))

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
                self.addAxiom(self.df.getOWLDisjointClassesAxiom(cast(self.Set, collection)))
            elif node.type() is Item.ComplementNode:
                operand = first(node.incomingNodes(lambda x: x.type() is Item.InputEdge))
                conversionA = self.convert(operand)
                for included in node.adjacentNodes(lambda x: x.type() in {Item.InclusionEdge, Item.EquivalenceEdge}):
                    conversionB = self.convert(included)
                    collection = self.HashSet()
                    collection.add(conversionA)
                    collection.add(conversionB)
                    self.addAxiom(self.df.getOWLDisjointClassesAxiom(cast(self.Set, collection)))

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
            self.addAxiom(self.df.getOWLDisjointDataPropertiesAxiom(cast(self.Set, collection)))

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
            self.addAxiom(self.df.getOWLDisjointObjectPropertiesAxiom(cast(self.Set, collection)))

    def createEquivalentClassesAxiom(self, edge):
        """
        Generate a OWL 2 EquivalentClasses axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.EquivalentClasses in self.axiomsList:
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
                            self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB))
                    elif edge.target.type() is Item.IntersectionNode:
                        # A ISA (B AND C) needs to be normalized to A ISA B && A ISA C
                        f1 = lambda x: x.type() is Item.InputEdge
                        f2 = lambda x: x.identity() is Identity.Concept
                        for operand in target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                            conversionA = self.convert(source)
                            conversionB = self.convert(operand)
                            self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB))
                    else:
                        conversionA = self.convert(source)
                        conversionB = self.convert(target)
                        self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB))
            else:
                conversionA = self.convert(edge.source)
                conversionB = self.convert(edge.target)
                collection = self.HashSet()
                collection.add(conversionA)
                collection.add(conversionB)
                self.addAxiom(self.df.getOWLEquivalentClassesAxiom(cast(self.Set, collection)))

    def createEquivalentDataPropertiesAxiom(self, edge):
        """
        Generate a OWL 2 EquivalentDataProperties axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.EquivalentDataProperties in self.axiomsList:
            if self.normalize:
                for source, target in ((edge.source, edge.target), (edge.target, edge.source)):
                    conversionA = self.convert(source)
                    conversionB = self.convert(target)
                    self.addAxiom(self.df.getOWLSubDataPropertyOfAxiom(conversionA, conversionB))
            else:
                conversionA = self.convert(edge.source)
                conversionB = self.convert(edge.target)
                collection = self.HashSet()
                collection.add(conversionA)
                collection.add(conversionB)
                self.addAxiom(self.df.getOWLEquivalentDataPropertiesAxiom(cast(self.Set, collection)))

    def createEquivalentObjectPropertiesAxiom(self, edge):
        """
        Generate a OWL 2 EquivalentObjectProperties axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.EquivalentObjectProperties in self.axiomsList:
            if self.normalize:
                for source, target in ((edge.source, edge.target), (edge.target, edge.source)):
                    conversionA = self.convert(source)
                    conversionB = self.convert(target)
                    self.addAxiom(self.df.getOWLSubObjectPropertyOfAxiom(conversionA, conversionB))
            else:
                conversionA = self.convert(edge.source)
                conversionB = self.convert(edge.target)
                collection = self.HashSet()
                collection.add(conversionA)
                collection.add(conversionB)
                self.addAxiom(self.df.getOWLEquivalentObjectPropertiesAxiom(cast(self.Set, collection)))

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
            self.addAxiom(self.df.getOWLNegativeDataPropertyAssertionAxiom(conversionA, conversionB, conversionC))

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
            self.addAxiom(self.df.getOWLNegativeObjectPropertyAssertionAxiom(conversionA, conversionB, conversionC))

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

            if edge.source.type() in {Item.DisjointUnionNode, Item.UnionNode} and self.normalize:
                # (A OR B) ISA C needs to be normalized to (A ISA C) && (B ISA C)
                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.identity() is Identity.Concept
                for operand in edge.source.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                    conversionA = self.convert(operand)
                    conversionB = self.convert(edge.target)
                    self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB))
            elif edge.target.type() is Item.IntersectionNode and self.normalize:
                # A ISA (B AND C) needs to be normalized to A ISA B && A ISA C
                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.identity() is Identity.Concept
                for operand in edge.target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                    conversionA = self.convert(edge.source)
                    conversionB = self.convert(operand)
                    self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB))
            else:
                conversionA = self.convert(edge.source)
                conversionB = self.convert(edge.target)
                self.addAxiom(self.df.getOWLSubClassOfAxiom(conversionA, conversionB))

    def createSubDataPropertyOfAxiom(self, edge):
        """
        Generate a OWL 2 SubDataPropertyOf axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.SubDataPropertyOf in self.axiomsList:
            conversionA = self.convert(edge.source)
            conversionB = self.convert(edge.target)
            self.addAxiom(self.df.getOWLSubDataPropertyOfAxiom(conversionA, conversionB))

    def createSubObjectPropertyOfAxiom(self, edge):
        """
        Generate a OWL 2 SubObjectPropertyOf axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.SubObjectPropertyOf in self.axiomsList:
            conversionA = self.convert(edge.source)
            conversionB = self.convert(edge.target)
            self.addAxiom(self.df.getOWLSubObjectPropertyOfAxiom(conversionA, conversionB))

    def createSubPropertyChainOfAxiom(self, edge):
        """
        Generate a OWL 2 SubPropertyChainOf axiom.
        :type edge: InclusionEdge
        """
        if OWLAxiom.SubObjectPropertyOf in self.axiomsList:
            conversionA = self.convert(edge.source)
            conversionB = self.convert(edge.target)
            self.addAxiom(self.df.getOWLSubPropertyChainOfAxiom(conversionA, conversionB))

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

            #############################################
            # INITIALIZE ONTOLOGY
            #################################

            self.man = self.OWLManager.createOWLOntologyManager()
            self.df = self.man.getOWLDataFactory()
            self.ontology = self.man.createOntology(self.IRI.create(rstrip(self.project.iri, '#')))
            self.pm = self.DefaultPrefixManager()
            self.pm.setPrefix(self.project.prefix, postfix(self.project.iri, '#'))

            cast(self.PrefixManager, self.pm)

            LOGGER.debug('Initialized OWL 2 Ontology: %s', rstrip(self.project.iri, '#'))

            #############################################
            # NODES PRE-PROCESSING
            #################################

            for node in self.project.nodes():
                self.convert(node)
                self.step(+1)

            LOGGER.debug('Pre-processed %s nodes into OWL 2 expressions', len(self.converted()))

            #############################################
            # AXIOMS FROM NODES
            #################################

            for node in self.project.nodes():

                if node.type() in {Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.ValueDomainNode}:
                    self.createDeclarationAxiom(node)
                    if node.type() is Item.AttributeNode:
                        self.createDataPropertyAxiom(node)
                    elif node.type() is Item.RoleNode:
                        self.createObjectPropertyAxiom(node)
                elif node.type() is Item.DisjointUnionNode:
                    self.createDisjointClassesAxiom(node)
                elif node.type() is Item.ComplementNode:
                    if node.identity() is Identity.Concept:
                        self.createDisjointClassesAxiom(node)
                elif node.type() is Item.DomainRestrictionNode:
                    self.createPropertyDomainAxiom(node)
                elif node.type() is Item.RangeRestrictionNode:
                    self.createPropertyRangeAxiom(node)

                if node.isMeta():
                    self.createAnnotationAssertionAxiom(node)

                self.step(+1)

            LOGGER.debug('Generated OWL 2 axioms from nodes (axioms = %s)', len(self.axioms()))

            #############################################
            # AXIOMS FROM EDGES
            #################################

            for edge in self.project.edges():

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
                    if edge.source.identity() is Identity.Individual and edge.target.identity() is Identity.Concept:
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

                self.step(+1)

            LOGGER.debug('Generated OWL 2 axioms from edges (axioms = %s)', len(self.axioms()))

            #############################################
            # APPLY GENERATED AXIOMS
            #################################

            LOGGER.debug('Applying OWL 2 axioms on the OWL 2 Ontology')

            for axiom in self.axioms():
                self.man.addAxiom(self.ontology, axiom)

            #############################################
            # SERIALIZE THE ONTOLOGY
            #################################

            if self.syntax is OWLSyntax.Functional:
                DocumentFormat = self.FunctionalSyntaxDocumentFormat
                DocumentFilter = OWLFunctionalDocumentFilter
            elif self.syntax is OWLSyntax.Manchester:
                DocumentFormat = self.ManchesterSyntaxDocumentFormat
                DocumentFilter = lambda x: x
            elif self.syntax is OWLSyntax.RDF:
                DocumentFormat = self.RDFXMLDocumentFormat
                DocumentFilter = lambda x: x
            elif self.syntax is OWLSyntax.Turtle:
                DocumentFormat = self.TurtleDocumentFormat
                DocumentFilter = lambda x: x
            else:
                raise TypeError('unsupported syntax (%s)' % self.syntax)

            LOGGER.debug('Serializing the OWL 2 Ontology in %s', self.syntax.value)

            # COPY PREFIXES
            ontoFormat = DocumentFormat()
            ontoFormat.copyPrefixesFrom(self.pm)
            # CREARE TARGET STREAM
            stream = self.StringDocumentTarget()
            stream = cast(self.OWLOntologyDocumentTarget, stream)
            # SAVE THE ONTOLOGY TO DISK
            self.man.setOntologyFormat(self.ontology, ontoFormat)
            self.man.saveOntology(self.ontology, stream)
            stream = cast(self.StringDocumentTarget, stream)
            string = DocumentFilter(stream.toString())
            fwrite(string, self.path)
            # REMOVE RANDOM FILES GENERATED BY OWL API
            fremove(os.path.join(os.path.dirname(self.path), 'catalog-v001.xml'))

        except DiagramMalformedError as e:
            LOGGER.warning('Malformed expression detected on {0}: {1} ... aborting!'.format(e.item, e))
            self.sgnErrored.emit(e)
        except Exception as e:
            LOGGER.exception('OWL 2 export could not be completed')
            self.sgnErrored.emit(e)
        else:
            self.sgnCompleted.emit()
        finally:
            detach()
            self.finished.emit()