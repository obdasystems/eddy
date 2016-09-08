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


from jnius import autoclass, cast, detach

from PyQt5.QtCore import Qt, QObject, QThread
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QMessageBox
from PyQt5.QtWidgets import QFrame, QProgressBar, QVBoxLayout, QWidget

from eddy import BUG_TRACKER
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.graphol import Item, Identity, Special, Restriction
from eddy.core.datatypes.owl import OWLSyntax, Datatype, Facet
from eddy.core.datatypes.system import File
from eddy.core.exceptions import MalformedDiagramError
from eddy.core.exporters.common import AbstractProjectExporter
from eddy.core.functions.fsystem import fwrite
from eddy.core.functions.misc import first, clamp, isEmpty, postfix, format_exception
from eddy.core.functions.owl import OWLShortIRI, OWLAnnotationText
from eddy.core.functions.owl import OWLFunctionalDocumentFilter
from eddy.core.functions.path import expandPath, openPath
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger

from eddy.ui.fields import ComboBox


LOGGER = getLogger(__name__)


class OWLProjectExporter(AbstractProjectExporter):
    """
    Extends AbstractProjectExporter with facilities to export a Graphol project into an OWL ontology.
    """
    def __init__(self, project, session=None):
        """
        Initialize the OWL Project exporter
        :type project: Project
        :type session: Session
        """
        super(OWLProjectExporter, self).__init__(project, session)

    #############################################
    #   INTERFACE
    #################################

    def export(self, path):
        """
        Perform OWL ontology generation.
        :type path: str
        """
        if not self.project.isEmpty():
            dialog = OWLProjectExporterDialog(self.project, path, self.session)
            dialog.exec_()

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Owl


class OWLProjectExporterDialog(QDialog):
    """
    Extends QDialog providing
    This class implements the form used to perform Graphol -> OWL ontology translation.
    """
    def __init__(self, project, path, session):
        """
        Initialize the form dialog.
        :type project: Project
        :type path: str
        :type session: Session
        """
        super(OWLProjectExporterDialog, self).__init__(session)

        arial12r = Font('Arial', 12)

        self.path = expandPath(path)
        self.project = project
        self.worker = None
        self.workerThread = None

        #############################################
        # FORM AREA
        #################################

        self.syntaxField = ComboBox(self)
        for syntax in OWLSyntax:
            self.syntaxField.addItem(syntax.value, syntax)
        self.syntaxField.setCurrentIndex(0)
        self.syntaxField.setFixedWidth(300)
        self.syntaxField.setFont(arial12r)

        spacer = QFrame()
        spacer.setFrameShape(QFrame.HLine)
        spacer.setFrameShadow(QFrame.Sunken)

        self.progressBar = QProgressBar(self)
        self.progressBar.setAlignment(Qt.AlignHCenter)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        self.formWidget = QWidget(self)
        self.formLayout = QFormLayout(self.formWidget)
        self.formLayout.addRow('Syntax', self.syntaxField)
        self.formLayout.addRow(spacer)
        self.formLayout.addRow(self.progressBar)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)

        #############################################
        # CONFIGURE LAYOUT
        #################################

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.formWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, Qt.AlignRight)

        self.setWindowTitle('OWL Export')
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        self.setFixedSize(self.sizeHint())

        connect(self.confirmationBox.accepted, self.run)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   INTERFACE
    #################################

    def syntax(self):
        """
        Returns the value of the OWL syntax field.
        :rtype: OWLSyntax
        """
        return self.syntaxField.currentData()


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

    @pyqtSlot(Exception)
    def onErrored(self, exception):
        """
        Executed whenever the translation errors.
        :type exception: Exception
        """
        self.workerThread.quit()

        if isinstance(exception, MalformedDiagramError):
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setInformativeText('Do you want to see the error in the diagram?')
            msgbox.setText('Malformed expression detected on {0}: {1}'.format(exception.item, exception))
            msgbox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Malformed expression')
            msgbox.exec_()
            if msgbox.result() == QMessageBox.Yes:
                self.session.doFocusItem(exception.item)
        else:
            # LOG INTO CONSOLE
            LOGGER.error('OWL2 translation could not be completed', exc_info=1)
            # SHOW A POPUP WITH THE ERROR MESSAGE
            msgbox = QMessageBox(self)
            msgbox.setDetailedText(format_exception(exception))
            msgbox.setIconPixmap(QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
            msgbox.setInformativeText('Please <a href="{0}">submit a bug report</a>.'.format(BUG_TRACKER))
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText('Diagram translation could not be completed!')
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Unhandled exception!')
            msgbox.exec_()

        self.reject()

    @pyqtSlot()
    def onCompleted(self):
        """
        Executed whenever the translation completes.
        """
        self.workerThread.quit()

        msgbox = QMessageBox(self)
        msgbox.setIconPixmap(QIcon(':/icons/24/ic_info_outline_black').pixmap(48))
        msgbox.setInformativeText('Do you want to open the OWL ontology?')
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setText('Translation completed!')
        msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        msgbox.exec_()
        if msgbox.result() == QMessageBox.Yes:
            openPath(self.path)

        self.accept()

    @pyqtSlot(int, int)
    def onProgress(self, current, total):
        """
        Update the progress bar showing the translation advancement.
        :type current: int
        :type total: int
        """
        self.progressBar.setRange(0, total)
        self.progressBar.setValue(current)

    @pyqtSlot()
    def onStarted(self):
        """
        Executed whenever the translation starts.
        """
        self.confirmationBox.setEnabled(False)

    @pyqtSlot()
    def run(self):
        """
        Perform the Graphol -> OWL translation in a separate thread.
        """
        self.workerThread = QThread()
        self.worker = OWLProjectExporterWorker(self.project, self.path, self.syntax())
        self.worker.moveToThread(self.workerThread)
        connect(self.worker.sgnStarted, self.onStarted)
        connect(self.worker.sgnCompleted, self.onCompleted)
        connect(self.worker.sgnErrored, self.onErrored)
        connect(self.worker.sgnProgress, self.onProgress)
        connect(self.workerThread.started, self.worker.run)
        self.workerThread.start()


class OWLProjectExporterWorker(QObject):
    """
    Extends QObject providing a worker thread that will perform the OWL ontology generation.
    """
    sgnCompleted = pyqtSignal()
    sgnErrored = pyqtSignal(Exception)
    sgnFinished = pyqtSignal()
    sgnProgress = pyqtSignal(int, int)
    sgnStarted = pyqtSignal()

    def __init__(self, project, path, syntax):
        """
        Initialize the OWL Exporter worker.
        :type project: Project
        :type path: str
        :type syntax: OWLSyntax
        """
        super(OWLProjectExporterWorker, self).__init__()

        self.path = path
        self.project = project
        self.ontoIRI = self.project.iri
        self.ontoPrefix = self.project.prefix
        self.syntax = syntax

        self.axioms = set()
        self.conv = dict()
        self.df = None
        self.num = 0
        self.man = None
        self.max = len(self.project.nodes()) + len(self.project.edges())
        self.ontology = None
        self.pm = None

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
        elif datatype is Datatype.base64Binary:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_BASE_64_BINARY').getIRI())
        elif datatype is Datatype.boolean:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_BOOLEAN').getIRI())
        elif datatype is Datatype.byte:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_BYTE').getIRI())
        elif datatype is Datatype.dateTime:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_DATE_TIME').getIRI())
        elif datatype is Datatype.dateTimeStamp:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_DATE_TIME_STAMP').getIRI())
        elif datatype is Datatype.decimal:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_DECIMAL').getIRI())
        elif datatype is Datatype.double:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_DOUBLE').getIRI())
        elif datatype is Datatype.float:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_FLOAT').getIRI())
        elif datatype is Datatype.hexBinary:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_HEX_BINARY').getIRI())
        elif datatype is Datatype.int:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_INT').getIRI())
        elif datatype is Datatype.integer:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_INTEGER').getIRI())
        elif datatype is Datatype.language:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_LANGUAGE').getIRI())
        elif datatype is Datatype.literal:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('RDFS_LITERAL').getIRI())
        elif datatype is Datatype.long:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_LONG').getIRI())
        elif datatype is Datatype.Name:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NAME').getIRI())
        elif datatype is Datatype.NCName:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NCNAME').getIRI())
        elif datatype is Datatype.negativeInteger:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NEGATIVE_INTEGER').getIRI())
        elif datatype is Datatype.NMTOKEN:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NMTOKEN').getIRI())
        elif datatype is Datatype.nonNegativeInteger:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NON_NEGATIVE_INTEGER').getIRI())
        elif datatype is Datatype.nonPositiveInteger:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NON_POSITIVE_INTEGER').getIRI())
        elif datatype is Datatype.normalizedString:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_NORMALIZED_STRING').getIRI())
        elif datatype is Datatype.plainLiteral:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('RDF_PLAIN_LITERAL').getIRI())
        elif datatype is Datatype.positiveInteger:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_POSITIVE_INTEGER').getIRI())
        elif datatype is Datatype.rational:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('OWL_RATIONAL').getIRI())
        elif datatype is Datatype.real:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('OWL_REAL').getIRI())
        elif datatype is Datatype.short:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_SHORT').getIRI())
        elif datatype is Datatype.string:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_STRING').getIRI())
        elif datatype is Datatype.token:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_TOKEN').getIRI())
        elif datatype is Datatype.unsignedByte:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_UNSIGNED_BYTE').getIRI())
        elif datatype is Datatype.unsignedInt:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_UNSIGNED_INT').getIRI())
        elif datatype is Datatype.unsignedLong:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_UNSIGNED_LONG').getIRI())
        elif datatype is Datatype.unsignedShort:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('XSD_UNSIGNED_SHORT').getIRI())
        elif datatype is Datatype.xmlLiteral:
            return self.df.getOWLDatatype(self.OWL2Datatype.valueOf('RDF_XML_LITERAL').getIRI())
        raise ValueError('invalid datatype supplied: {0}'.format(datatype))

    def getOWLApiFacet(self, facet):
        """
        Returns the OWLFacet matching the given Facet.
        :type facet: Facet
        :rtype: OWLFacet 
        """
        if facet is Facet.maxExclusive:
            return self.OWLFacet.valueOf('MAX_EXCLUSIVE')
        elif facet is Facet.maxInclusive:
            return self.OWLFacet.valueOf('MAX_INCLUSIVE')
        elif facet is Facet.minExclusive:
            return self.OWLFacet.valueOf('MIN_EXCLUSIVE')
        elif facet is Facet.minInclusive:
            return self.OWLFacet.valueOf('MIN_INCLUSIVE')
        elif facet is Facet.langRange:
            return self.OWLFacet.valueOf('LANG_RANGE')
        elif facet is Facet.length:
            return self.OWLFacet.valueOf('LENGTH')
        elif facet is Facet.maxLength:
            return self.OWLFacet.valueOf('MIN_LENGTH')
        elif facet is Facet.minLength:
            return self.OWLFacet.valueOf('MIN_LENGTH')
        elif facet is Facet.pattern:
            return self.OWLFacet.valueOf('PATTERN')
        raise ValueError('invalid facet supplied: {0}'.format(facet))
    
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
    #   NODES PRE-PROCESSING
    #################################

    def buildAttribute(self, node):
        """
        Build and returns a OWL attribute using the given graphol node.
        :type node: AttributeNode
        :rtype: OWLDataProperty
        """
        if node not in self.conv:
            if node.special() is Special.Top:
                self.conv[node] = self.df.getOWLTopDataProperty()
            elif node.special() is Special.Bottom:
                self.conv[node] = self.df.getOWLBottomDataProperty()
            else:
                self.conv[node] = self.df.getOWLDataProperty(OWLShortIRI(self.ontoPrefix, node.text()), self.pm)
        return self.conv[node]

    def buildComplement(self, node):
        """
        Build and returns a OWL complement using the given graphol node.
        :type node: ComplementNode
        :rtype: OWLClassExpression
        """
        if node not in self.conv:

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity() in {Identity.Attribute, Identity.Concept, Identity.ValueDomain, Identity.Role}

            incoming = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
            if not incoming:
                raise MalformedDiagramError(node, 'missing operand(s)')
            if len(incoming) > 1:
                raise MalformedDiagramError(node, 'too many operands')

            operand = first(incoming)

            if operand.identity() is Identity.Concept:

                if operand.type() is Item.ConceptNode:
                    self.conv[node] = self.df.getOWLObjectComplementOf(self.buildConcept(operand))
                elif operand.type() is Item.ComplementNode:
                    self.conv[node] = self.df.getOWLObjectComplementOf(self.buildComplement(operand))
                elif operand.type() is Item.EnumerationNode:
                    self.conv[node] = self.df.getOWLObjectComplementOf(self.buildEnumeration(operand))
                elif operand.type() is Item.IntersectionNode:
                    self.conv[node] = self.df.getOWLObjectComplementOf(self.buildIntersection(operand))
                elif operand.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    self.conv[node] = self.df.getOWLObjectComplementOf(self.buildUnion(operand))
                elif operand.type() is Item.DomainRestrictionNode:
                    self.conv[node] = self.df.getOWLObjectComplementOf(self.buildDomainRestriction(operand))
                elif operand.type() is Item.RangeRestrictionNode:
                    self.conv[node] = self.df.getOWLObjectComplementOf(self.buildRangeRestriction(operand))
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(operand))

            elif operand.identity() is Identity.ValueDomain:

                if operand.type() is Item.ValueDomainNode:
                    self.conv[node] = self.df.getOWLDataComplementOf(self.buildValueDomain(operand))
                elif operand.type() is Item.ComplementNode:
                    self.conv[node] = self.df.getOWLDataComplementOf(self.buildComplement(operand))
                elif operand.type() is Item.EnumerationNode:
                    self.conv[node] = self.df.getOWLDataComplementOf(self.buildEnumeration(operand))
                elif operand.type() is Item.IntersectionNode:
                    self.conv[node] = self.df.getOWLDataComplementOf(self.buildIntersection(operand))
                elif operand.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    self.conv[node] = self.df.getOWLDataComplementOf(self.buildUnion(operand))
                elif operand.type() is Item.DatatypeRestrictionNode:
                    self.conv[node] = self.df.getOWLDataComplementOf(self.buildDatatypeRestriction(operand))
                elif operand.type() is Item.RangeRestrictionNode:
                    self.conv[node] = self.df.getOWLObjectComplementOf(self.buildRangeRestriction(operand))
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(operand))

            elif operand.identity() is Identity.Role:

                # OWLDisjointObjectPropertiesAxiom
                if operand.type() is Item.RoleNode:
                    self.conv[node] = self.buildRole(operand)
                elif operand.type() is Item.RoleInverseNode:
                    self.conv[node] = self.buildRoleInverse(operand)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(operand))

            elif operand.identity() is Identity.Attribute:

                # OWLDisjointDataPropertiesAxiom
                if operand.type() is Item.AttributeNode:
                    self.conv[node] = self.buildAttribute(operand)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(operand))

        return self.conv[node]

    def buildConcept(self, node):
        """
        Build and returns a OWL concept using the given graphol node.
        :type node: ConceptNode
        :rtype: OWLClass
        """
        if node not in self.conv:
            if node.special() is Special.Top:
                self.conv[node] = self.df.getOWLThing()
            elif node.special() is Special.Bottom:
                self.conv[node] = self.df.getOWLNothing()
            else:
                self.conv[node] = self.df.getOWLClass(OWLShortIRI(self.ontoPrefix, node.text()), self.pm)
        return self.conv[node]

    def buildDatatypeRestriction(self, node):
        """
        Build and returns a OWL datatype restriction using the given graphol node.
        :type node: DatatypeRestrictionNode
        :rtype: OWLDatatypeRestriction
        """
        if node not in self.conv:

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.ValueDomainNode
            f3 = lambda x: x.type() is Item.FacetNode

            #############################################
            # BUILD DATATYPE
            #################################

            operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not operand:
                raise MalformedDiagramError(node, 'missing value domain node')

            datatypeEx = self.buildValueDomain(operand)

            #############################################
            # BUILD FACETS
            #################################

            incoming = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)
            if not incoming:
                raise MalformedDiagramError(node, 'missing facet node(s)')

            collection = self.HashSet()
            for i in incoming:
                collection.add(self.buildFacet(i))

            #############################################
            # BUILD DATATYPE RESTRICTION
            #################################

            collection = cast(self.Set, collection)
            self.conv[node] = self.df.getOWLDatatypeRestriction(datatypeEx, collection)

        return self.conv[node]

    def buildDomainRestriction(self, node):
        """
        Build and returns a OWL domain restriction using the given graphol node.
        :type node: DomainRestrictionNode
        :rtype: OWLClassExpression
        """
        if node not in self.conv:

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity() in {Identity.Role, Identity.Attribute}
            f3 = lambda x: x.identity() is Identity.ValueDomain
            f4 = lambda x: x.identity() is Identity.Concept

            operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not operand:
                raise MalformedDiagramError(node, 'missing operand(s)')

            if operand.identity() is Identity.Attribute:

                #############################################
                # BUILD OPERAND
                #################################

                dataPropEx = self.buildAttribute(operand)

                #############################################
                # BUILD FILLER
                #################################

                filler = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
                if not filler:
                    dataRangeEx = self.df.getTopDatatype()
                elif filler.type() is Item.ValueDomainNode:
                    dataRangeEx = self.buildValueDomain(filler)
                elif filler.type() is Item.ComplementNode:
                    dataRangeEx = self.buildComplement(filler)
                elif filler.type() is Item.EnumerationNode:
                    dataRangeEx = self.buildEnumeration(filler)
                elif filler.type() is Item.IntersectionNode:
                    dataRangeEx = self.buildIntersection(filler)
                elif filler.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    dataRangeEx = self.buildUnion(filler)
                elif filler.type() is Item.DatatypeRestrictionNode:
                    dataRangeEx = self.buildDatatypeRestriction(filler)
                elif filler.type() is Item.RangeRestrictionNode:
                    dataRangeEx = self.buildRangeRestriction(filler)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(filler))

                if node.restriction is Restriction.Exists:
                    self.conv[node] = self.df.getOWLDataSomeValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.Forall:
                    self.conv[node] = self.df.getOWLDataAllValuesFrom(dataPropEx, dataRangeEx)
                elif node.restriction is Restriction.Cardinality:
                    cardinalities = self.HashSet()
                    min_c = node.cardinality['min']
                    max_c = node.cardinality['max']
                    if min_c is not None:
                        cardinalities.add(self.df.getOWLDataMinCardinality(min_c, dataPropEx, dataRangeEx))
                    if max_c is not None:
                        cardinalities.add(self.df.getOWLDataMinCardinality(max_c, dataPropEx, dataRangeEx))
                    if cardinalities.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    elif cardinalities.size() >= 1:
                        cardinalities = cast(self.Set, cardinalities)
                        self.conv[node] = self.df.getOWLDataIntersectionOf(cardinalities)
                    else:
                        self.conv[node] = cardinalities.iterator().next()
                else:
                    raise MalformedDiagramError(node, 'unsupported restriction')

            elif operand.identity() is Identity.Role:

                #############################################
                # BUILD OPERAND
                #################################

                if operand.type() is Item.RoleNode:
                    objectPropertyEx = self.buildRole(operand)
                elif operand.type() is Item.RoleInverseNode:
                    objectPropertyEx = self.buildRoleInverse(operand)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(operand))

                #############################################
                # BUILD FILLER
                #################################

                filler = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f4))
                if not filler:
                    classEx = self.df.getOWLThing()
                elif filler.type() is Item.ConceptNode:
                    classEx = self.buildConcept(filler)
                elif filler.type() is Item.ComplementNode:
                    classEx = self.buildComplement(filler)
                elif filler.type() is Item.EnumerationNode:
                    classEx = self.buildEnumeration(filler)
                elif filler.type() is Item.IntersectionNode:
                    classEx = self.buildIntersection(filler)
                elif filler.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    classEx = self.buildUnion(filler)
                elif filler.type() is Item.DomainRestrictionNode:
                    classEx = self.buildDomainRestriction(filler)
                elif filler.type() is Item.RangeRestrictionNode:
                    classEx = self.buildRangeRestriction(filler)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(filler))

                if node.restriction is Restriction.Self:
                    self.conv[node] = self.df.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.Exists:
                    self.conv[node] = self.df.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Forall:
                    self.conv[node] = self.df.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Cardinality:
                    cardinalities = self.HashSet()
                    min_c = node.cardinality['min']
                    max_c = node.cardinality['max']
                    if min_c is not None:
                        cardinalities.add(self.df.getOWLObjectMinCardinality(min_c, objectPropertyEx, classEx))
                    if max_c is not None:
                        cardinalities.add(self.df.getOWLObjectMaxCardinality(max_c, objectPropertyEx, classEx))
                    if cardinalities.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    elif cardinalities.size() >= 1:
                        cardinalities = cast(self.Set, cardinalities)
                        self.conv[node] = self.df.getOWLObjectIntersectionOf(cardinalities)
                    else:
                        self.conv[node] = cardinalities.iterator().next()

        return self.conv[node]

    def buildEnumeration(self, node):
        """
        Build and returns a OWL enumeration using the given graphol node.
        :type node: EnumerationNode
        :rtype: OWLObjectOneOf
        """
        if node not in self.conv:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.IndividualNode
            individuals = self.HashSet()
            for i in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                individuals.add(self.buildIndividual(i))
            if individuals.isEmpty():
                raise MalformedDiagramError(node, 'missing operand(s)')
            individuals = cast(self.Set, individuals)
            self.conv[node] = self.df.getOWLObjectOneOf(individuals)
        return self.conv[node]

    def buildFacet(self, node):
        """
        Build and returns a OWL facet restriction using the given graphol node.
        :type node: FacetNode
        :rtype: OWLFacetRestriction
        """
        if node not in self.conv:
            datatype = node.datatype
            if not datatype:
                raise MalformedDiagramError(node, 'disconnected facet node')
            literal = self.df.getOWLLiteral(node.value, self.getOWLApiDatatype(datatype))
            facet = self.getOWLApiFacet(node.facet)
            self.conv[node] = self.df.getOWLFacetRestriction(facet, literal)
        return self.conv[node]

    def buildIndividual(self, node):
        """
        Build and returns a OWL individual using the given graphol node.
        :type node: IndividualNode
        :rtype: OWLNamedIndividual
        """
        if node not in self.conv:
            if node.identity() is Identity.Individual:
                self.conv[node] = self.df.getOWLNamedIndividual(OWLShortIRI(self.ontoPrefix, node.text()), self.pm)
            elif node.identity() is Identity.Value:
                self.conv[node] = self.df.getOWLLiteral(node.value, self.getOWLApiDatatype(node.datatype))
        return self.conv[node]

    def buildIntersection(self, node):
        """
        Build and returns a OWL intersection using the given graphol node.
        :type node: IntersectionNode
        :rtype: T <= OWLObjectIntersectionOf|OWLDataIntersectionOf
        """
        if node not in self.conv:

            collection = self.HashSet()

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity() in {Identity.Concept, Identity.ValueDomain}

            for operand in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                if operand.type() is Item.ConceptNode:
                    collection.add(self.buildConcept(operand))
                elif operand.type() is Item.ValueDomainNode:
                    collection.add(self.buildValueDomain(operand))
                elif operand.type() is Item.ComplementNode:
                    collection.add(self.buildComplement(operand))
                elif operand.type() is Item.EnumerationNode:
                    collection.add(self.buildEnumeration(operand))
                elif operand.type() is Item.IntersectionNode:
                    collection.add(self.buildIntersection(operand))
                elif operand.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    collection.add(self.buildUnion(operand))
                elif operand.type() is Item.DomainRestrictionNode:
                    collection.add(self.buildDomainRestriction(operand))
                elif operand.type() is Item.RangeRestrictionNode:
                    collection.add(self.buildRangeRestriction(operand))
                elif operand.type() is Item.DatatypeRestrictionNode:
                    collection.add(self.buildDatatypeRestriction(operand))
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(operand))

            if collection.isEmpty():
                raise MalformedDiagramError(node, 'missing operand(s)')

            collection = cast(self.Set, collection)

            if node.identity() is Identity.Concept:
                self.conv[node] = self.df.getOWLObjectIntersectionOf(collection)
            elif node.identity() is Identity.ValueDomain:
                self.conv[node] = self.df.getOWLDataIntersectionOf(collection)

        return self.conv[node]

    def buildPropertyAssertion(self, node):
        """
        Build and returns a collection of individuals that can be used to build property assertions.
        :type node: PropertyAssertionNode
        :rtype: tuple
        """
        if node not in self.conv:

            if len(node.inputs) < 2:
                raise MalformedDiagramError(node, 'missing operand(s)')
            elif len(node.inputs) > 2:
                raise MalformedDiagramError(node, 'too many operands')

            collection = []
            for n in [node.diagram.edge(i).other(node) for i in node.inputs]:
                if n.type() is not Item.IndividualNode:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(n))
                collection.append(self.buildIndividual(n))

            self.conv[node] = collection

        return self.conv[node]

    def buildRangeRestriction(self, node):
        """
        Build and returns a OWL range restriction using the given graphol node.
        :type node: DomainRestrictionNode
        :rtype: T <= OWLClassExpression|OWLDataProperty
        """
        if node not in self.conv:

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity() in {Identity.Role, Identity.Attribute}
            f3 = lambda x: x.identity() is Identity.Concept

            operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not operand:
                raise MalformedDiagramError(node, 'missing operand(s)')

            if operand.identity() is Identity.Attribute:

                #############################################
                # BUILD OPERAND
                #################################

                # In this case we just create a mapping using
                # OWLDataPropertyExpression which is needed later
                # when we create the DataPropertyRange using this
                # very node and a Value-Domain expression.
                self.conv[node] = self.buildAttribute(operand)

            elif operand.identity() is Identity.Role:

                #############################################
                # BUILD OPERAND
                #################################

                if operand.type() is Item.RoleNode:
                    objectPropertyEx = self.buildRole(operand).getInverseProperty()
                elif operand.type() is Item.RoleInverseNode:
                    objectPropertyEx = self.buildRoleInverse(operand).getInverseProperty()
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(operand))

                #############################################
                # BUILD FILLER
                #################################

                filler = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
                if not filler:
                    classEx = self.df.getOWLThing()
                elif filler.type() is Item.ConceptNode:
                    classEx = self.buildConcept(filler)
                elif filler.type() is Item.ComplementNode:
                    classEx = self.buildComplement(filler)
                elif filler.type() is Item.EnumerationNode:
                    classEx = self.buildEnumeration(filler)
                elif filler.type() is Item.IntersectionNode:
                    classEx = self.buildIntersection(filler)
                elif filler.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    classEx = self.buildUnion(filler)
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(filler))

                if node.restriction is Restriction.Self:
                    self.conv[node] = self.df.getOWLObjectHasSelf(objectPropertyEx)
                elif node.restriction is Restriction.Exists:
                    self.conv[node] = self.df.getOWLObjectSomeValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Forall:
                    self.conv[node] = self.df.getOWLObjectAllValuesFrom(objectPropertyEx, classEx)
                elif node.restriction is Restriction.Cardinality:
                    cardinalities = self.HashSet()
                    min_c = node.cardinality['min']
                    max_c = node.cardinality['max']
                    if min_c is not None:
                        cardinalities.add(self.df.getOWLObjectMinCardinality(min_c, objectPropertyEx, classEx))
                    if max_c is not None:
                        cardinalities.add(self.df.getOWLObjectMaxCardinality(max_c, objectPropertyEx, classEx))
                    if cardinalities.isEmpty():
                        raise MalformedDiagramError(node, 'missing cardinality')
                    if cardinalities.size() >= 1:
                        cardinalities = cast(self.Set, cardinalities)
                        self.conv[node] = self.df.getOWLObjectIntersectionOf(cardinalities)
                    else:
                        self.conv[node] = cardinalities.iterator().next()

        return self.conv[node]

    def buildRole(self, node):
        """
        Build and returns a OWL role using the given graphol node.
        :type node: RoleNode
        :rtype: OWLObjectProperty
        """
        if node not in self.conv:
            if node.special() is Special.Top:
                self.conv[node] = self.df.getOWLTopObjectProperty()
            elif node.special() is Special.Bottom:
                self.conv[node] = self.df.getOWLBottomObjectProperty()
            else:
                self.conv[node] = self.df.getOWLObjectProperty(OWLShortIRI(self.ontoPrefix, node.text()), self.pm)
        return self.conv[node]

    def buildRoleChain(self, node):
        """
        Constructs and returns a chain of OWLObjectExpression (OPE => Role & RoleInverse).
        :type node: RoleChainNode
        :rtype: list
        """
        if node not in self.conv:
            if not node.inputs:
                raise MalformedDiagramError(node, 'missing operand(s)')
            collection = self.LinkedList()
            for n in [node.diagram.edge(i).other(node) for i in node.inputs]:
                if n.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(n))
                elif n.type() is Item.RoleNode:
                    collection.add(self.buildRole(n))
                elif n.type() is Item.RoleInverseNode:
                    collection.add(self.buildRoleInverse(n))
            collection = cast(self.List, collection)
            self.conv[node] = collection
        return self.conv[node]

    def buildRoleInverse(self, node):
        """
        Build and returns a OWL role inverse using the given graphol node.
        :type node: RoleInverseNode
        :rtype: OWLObjectPropertyExpression
        """
        if node not in self.conv:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.RoleNode
            operand = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
            if not operand:
                raise MalformedDiagramError(node, 'missing operand(s)')
            self.conv[node] = self.buildRole(operand).getInverseProperty()
        return self.conv[node]

    def buildUnion(self, node):
        """
        Build and returns a OWL union using the given graphol node.
        :type node: UnionNode
        :rtype: T <= OWLObjectUnionOf|OWLDataUnionOf
        """
        if node not in self.conv:

            collection = self.HashSet()

            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity() in {Identity.Concept, Identity.ValueDomain}

            for item in node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):

                if item.type() is Item.ConceptNode:
                    collection.add(self.buildConcept(item))
                elif item.type() is Item.ValueDomainNode:
                    collection.add(self.buildValueDomain(item))
                elif item.type() is Item.ComplementNode:
                    collection.add(self.buildComplement(item))
                elif item.type() is Item.EnumerationNode:
                    collection.add(self.buildEnumeration(item))
                elif item.type() is Item.IntersectionNode:
                    collection.add(self.buildIntersection(item))
                elif item.type() in {Item.UnionNode, Item.DisjointUnionNode}:
                    collection.add(self.buildUnion(item))
                elif item.type() is Item.DomainRestrictionNode:
                    collection.add(self.buildDomainRestriction(item))
                elif item.type() is Item.RangeRestrictionNode:
                    collection.add(self.buildRangeRestriction(item))
                elif item.type() is Item.DatatypeRestrictionNode:
                    collection.add(self.buildDatatypeRestriction(item))
                else:
                    raise MalformedDiagramError(node, 'unsupported operand ({0})'.format(item))

            if not collection.size():
                raise MalformedDiagramError(node, 'missing operand(s)')

            collection = cast(self.Set, collection)

            if node.identity() is Identity.Concept:
                self.conv[node] = self.df.getOWLObjectUnionOf(collection)
            elif node.identity() is Identity.ValueDomain:
                self.conv[node] = self.df.getOWLDataUnionOf(collection)

        return self.conv[node]

    def buildValueDomain(self, node):
        """
        Build and returns a OWL datatype using the given graphol node.
        :type node: ValueDomainNode
        :rtype: OWLDatatype
        """
        if node not in self.conv:
            self.conv[node] = self.getOWLApiDatatype(node.datatype)
        return self.conv[node]

    #############################################
    #   AXIOMS GENERATION
    #################################

    def axiomAnnotation(self, node):
        """
        Generate a OWL annotation axiom.
        :type node: AbstractNode
        """
        meta = self.project.meta(node.type(), node.text())
        if meta and not isEmpty(meta['description']):
            prop = self.df.getOWLAnnotationProperty(self.IRI.create("Description"))
            value = self.df.getOWLLiteral(OWLAnnotationText(meta['description']))
            value = cast(self.OWLAnnotationValue, value)
            annotation = self.df.getOWLAnnotation(prop, value)
            self.axioms.add(self.df.getOWLAnnotationAssertionAxiom(self.conv[node].getIRI(), annotation))

    def axiomDataProperty(self, node):
        """
        Generate OWL Data Property specific axioms.
        :type node: AttributeNode
        """
        if node.isFunctional():
            self.axioms.add(self.df.getOWLFunctionalDataPropertyAxiom(self.conv[node]))

    def axiomClassAssertion(self, edge):
        """
        Generate a OWL ClassAssertion axiom.
        :type edge: InstanceOf
        """
        self.axioms.add(self.df.getOWLClassAssertionAxiom(self.conv[edge.target], self.conv[edge.source]))

    def axiomDataPropertyAssertion(self, edge):
        """
        Generate a OWL DataPropertyAssertion axiom.
        :type edge: InstanceOf
        """
        operand1 = self.conv[edge.source][0]
        operand2 = self.conv[edge.source][1]
        self.axioms.add(self.df.getOWLDataPropertyAssertionAxiom(self.conv[edge.target], operand1, operand2))

    def axiomDataPropertyRange(self, edge):
        """
        Generate a OWL DataPropertyRange axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.df.getOWLDataPropertyRangeAxiom(self.conv[edge.source], self.conv[edge.target]))

    def axiomDeclaration(self, node):
        """
        Generate a OWL Declaration axiom.
        :type node: AbstractNode
        """
        self.axioms.add(self.df.getOWLDeclarationAxiom(self.conv[node]))

    def axiomDisjointClasses(self, node):
        """
        Generate a OWL DisjointClasses axiom.
        :type node: DisjointUnionNode
        """
        collection = self.HashSet()
        for j in node.incomingNodes(lambda x: x.type() is Item.InputEdge):
            collection.add(self.conv[j])
        collection = cast(self.Set, collection)
        self.axioms.add(self.df.getOWLDisjointClassesAxiom(collection))

    def axiomDisjointDataProperties(self, edge):
        """
        Generate a OWL DisjointDataProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = cast(self.Set, collection)
        self.axioms.add(self.df.getOWLDisjointDataPropertiesAxiom(collection))

    def axiomDisjointObjectProperties(self, edge):
        """
        Generate a OWL DisjointObjectProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = cast(self.Set, collection)
        self.axioms.add(self.df.getOWLDisjointObjectPropertiesAxiom(collection))

    def axiomEquivalentClasses(self, edge):
        """
        Generate a OWL EquivalentClasses axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = cast(self.Set, collection)
        self.axioms.add(self.df.getOWLEquivalentClassesAxiom(collection))

    def axiomEquivalentDataProperties(self, edge):
        """
        Generate a OWL EquivalentDataProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = cast(self.Set, collection)
        self.axioms.add(self.df.getOWLEquivalentDataPropertiesAxiom(collection))

    def axiomEquivalentObjectProperties(self, edge):
        """
        Generate a OWL EquivalentObjectProperties axiom.
        :type edge: InclusionEdge
        """
        collection = self.HashSet()
        collection.add(self.conv[edge.source])
        collection.add(self.conv[edge.target])
        collection = cast(self.Set, collection)
        self.axioms.add(self.df.getOWLEquivalentObjectPropertiesAxiom(collection))

    def axiomObjectProperty(self, node):
        """
        Generate OWL ObjectProperty specific axioms.
        :type node: RoleNode
        """
        if node.isFunctional():
            self.axioms.add(self.df.getOWLFunctionalObjectPropertyAxiom(self.conv[node]))
        if node.isInverseFunctional():
            self.axioms.add(self.df.getOWLInverseFunctionalObjectPropertyAxiom(self.conv[node]))
        if node.isAsymmetric():
            self.axioms.add(self.df.getOWLAsymmetricObjectPropertyAxiom(self.conv[node]))
        if node.isIrreflexive():
            self.axioms.add(self.df.getOWLIrreflexiveObjectPropertyAxiom(self.conv[node]))
        if node.isReflexive():
            self.axioms.add(self.df.getOWLReflexiveObjectPropertyAxiom(self.conv[node]))
        if node.isSymmetric():
            self.axioms.add(self.df.getOWLSymmetricObjectPropertyAxiom(self.conv[node]))
        if node.isTransitive():
            self.axioms.add(self.df.getOWLTransitiveObjectPropertyAxiom(self.conv[node]))

    def axiomObjectPropertyAssertion(self, edge):
        """
        Generate a OWL ObjectPropertyAssertion axiom.
        :type edge: InstanceOf
        """
        operand1 = self.conv[edge.source][0]
        operand2 = self.conv[edge.source][1]
        self.axioms.add(self.df.getOWLObjectPropertyAssertionAxiom(self.conv[edge.target], operand1, operand2))

    def axiomSubclassOf(self, edge):
        """
        Generate a OWL SubclassOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.df.getOWLSubClassOfAxiom(self.conv[edge.source], self.conv[edge.target]))

    def axiomSubDataPropertyOfAxiom(self, edge):
        """
        Generate a OWL SubDataPropertyOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.df.getOWLSubDataPropertyOfAxiom(self.conv[edge.source], self.conv[edge.target]))

    def axiomSubObjectPropertyOf(self, edge):
        """
        Generate a OWL SubObjectPropertyOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.df.getOWLSubObjectPropertyOfAxiom(self.conv[edge.source], self.conv[edge.target]))

    def axiomSubPropertyChainOf(self, edge):
        """
        Generate a OWL SubPropertyChainOf axiom.
        :type edge: InclusionEdge
        """
        self.axioms.add(self.df.getOWLSubPropertyChainOfAxiom(self.conv[edge.source], self.conv[edge.target]))
        
    #############################################
    #   MAIN WORKER
    #################################

    @pyqtSlot()
    def run(self):
        """
        Main worker.
        """
        try:
            
            self.sgnStarted.emit()

            #############################################
            # INITIALIZE ONTOLOGY
            #################################

            # FIXME: https://github.com/owlcs/owlapi/issues/529
            self.man = self.OWLManager.createOWLOntologyManager()
            self.df = self.man.getOWLDataFactory()
            self.ontology = self.man.createOntology(self.IRI.create(self.ontoIRI.rstrip('#')))
            self.pm = self.DefaultPrefixManager()
            self.pm.setPrefix(self.project.prefix, postfix(self.ontoIRI, '#'))

            cast(self.PrefixManager, self.pm)

            #############################################
            # NODES CONVERSION
            #################################

            for n in self.project.nodes():

                if n.type() is Item.ConceptNode:  # CONCEPT
                    self.buildConcept(n)
                elif n.type() is Item.AttributeNode:  # ATTRIBUTE
                    self.buildAttribute(n)
                elif n.type() is Item.RoleNode:  # ROLE
                    self.buildRole(n)
                elif n.type() is Item.ValueDomainNode:  # VALUE-DOMAIN
                    self.buildValueDomain(n)
                elif n.type() is Item.IndividualNode:  # INDIVIDUAL
                    self.buildIndividual(n)
                elif n.type() is Item.FacetNode:  # FACET
                    self.buildFacet(n)
                elif n.type() is Item.RoleInverseNode:  # ROLE INVERSE
                    self.buildRoleInverse(n)
                elif n.type() is Item.RoleChainNode:  # ROLE CHAIN
                    self.buildRoleChain(n)
                elif n.type() is Item.ComplementNode:  # COMPLEMENT
                    self.buildComplement(n)
                elif n.type() is Item.EnumerationNode:  # ENUMERATION
                    self.buildEnumeration(n)
                elif n.type() is Item.IntersectionNode:  # INTERSECTION
                    self.buildIntersection(n)
                elif n.type() in {Item.UnionNode, Item.DisjointUnionNode}:  # UNION / DISJOINT UNION
                    self.buildUnion(n)
                elif n.type() is Item.DatatypeRestrictionNode:  # DATATYPE RESTRICTION
                    self.buildDatatypeRestriction(n)
                elif n.type() is Item.PropertyAssertionNode:  # PROPERTY ASSERTION
                    self.buildPropertyAssertion(n)
                elif n.type() is Item.DomainRestrictionNode:  # DOMAIN RESTRICTION
                    self.buildDomainRestriction(n)
                elif n.type() is Item.RangeRestrictionNode:  # RANGE RESTRICTION
                    self.buildRangeRestriction(n)

                self.step(+1)

            #############################################
            # AXIOMS FROM NODES
            #################################

            for n in self.project.nodes():

                if n.type() in {Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.ValueDomainNode}:
                    self.axiomDeclaration(n)
                    if n.type() is Item.AttributeNode:
                        self.axiomDataProperty(n)
                    elif n.type() is Item.RoleNode:
                        self.axiomObjectProperty(n)
                elif n.type() is Item.DisjointUnionNode:
                    self.axiomDisjointClasses(n)

                if n.isPredicate():
                    self.axiomAnnotation(n)

            #############################################
            # AXIOMS FROM EDGES
            #################################

            for e in self.project.edges():

                if e.type() is Item.InclusionEdge:

                    if not e.equivalence:

                        if e.source.identity() is Identity.Concept and e.target.identity() is Identity.Concept:
                            self.axiomSubclassOf(e)
                        elif e.source.identity() is Identity.Role and e.target.identity() is Identity.Role:
                            if e.source.type() is Item.RoleChainNode:
                                self.axiomSubPropertyChainOf(e)
                            elif e.source.type() in {Item.RoleNode, Item.RoleInverseNode}:
                                if e.target.type() is Item.ComplementNode:
                                    self.axiomDisjointObjectProperties(e)
                                elif e.target.type() in {Item.RoleNode, Item.RoleInverseNode}:
                                    self.axiomSubObjectPropertyOf(e)
                        elif e.source.identity() is Identity.Attribute and e.target.identity() is Identity.Attribute:
                            if e.source.type() is Item.AttributeNode:
                                if e.target.type() is Item.ComplementNode:
                                    self.axiomDisjointDataProperties(e)
                                elif e.target.type() is Item.AttributeNode:
                                    self.axiomSubDataPropertyOfAxiom(e)
                        elif e.source.type() is Item.RangeRestrictionNode and e.target.identity() is Identity.ValueDomain:
                            self.axiomDataPropertyRange(e)
                        else:
                            raise MalformedDiagramError(e, 'type mismatch in inclusion assertion')

                    else:

                        if e.source.identity() is Identity.Concept and e.target.identity() is Identity.Concept:
                            self.axiomEquivalentClasses(e)
                        elif e.source.identity() is Identity.Role and e.target.identity() is Identity.Role:
                            self.axiomEquivalentObjectProperties(e)
                        elif e.source.identity() is Identity.Attribute and e.target.identity() is Identity.Attribute:
                            self.axiomEquivalentDataProperties(e)
                        else:
                            raise MalformedDiagramError(e, 'type mismatch in equivalence assertion')

                elif e.type() is Item.MembershipEdge:

                    if e.source.identity() is Identity.Individual and e.target.identity() is Identity.Concept:
                        self.axiomClassAssertion(e)
                    elif e.source.identity() is Identity.RoleInstance:
                        self.axiomObjectPropertyAssertion(e)
                    elif e.source.identity() is Identity.AttributeInstance:
                        self.axiomDataPropertyAssertion(e)
                    else:
                        raise MalformedDiagramError(e, 'type mismatch in membership assertion')

                self.step(+1)

            #############################################
            # APPLY GENERATED AXIOMS
            #################################

            for axiom in self.axioms:
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
                raise TypeError('unsupported syntax ({0})'.format(self.syntax))

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
            
        except Exception as e:
            self.sgnErrored.emit(e)
        else:
            self.sgnCompleted.emit()
        finally:
            detach()
            self.sgnFinished.emit()