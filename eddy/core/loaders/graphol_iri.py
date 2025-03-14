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
import textwrap
from time import time

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
    QtXml,
)

from eddy import APPNAME
from eddy.core.commands.diagram import CommandDiagramAdd
from eddy.core.commands.project import (
    CommandProjectAddAnnotationProperty,
    CommandProjectAddOntologyImport,
    CommandProjectAddPrefix,
)
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.owl import Namespace
from eddy.core.datatypes.system import File
from eddy.core.diagram import (
    Diagram,
    DiagramNotFoundError,
    DiagramNotValidError,
)
from eddy.core.exporters.graphol_iri import GrapholIRIProjectExporter
from eddy.core.functions.fsystem import fread, fexists, isdir, rmdir, make_archive
from eddy.core.functions.misc import rstrip, rtfStripFontAttributes
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.nodes.common.base import PredicateNodeMixin
from eddy.core.loaders.common import (
    AbstractDiagramLoader,
    AbstractOntologyLoader,
    AbstractProjectLoader,
)
from eddy.core.loaders.owl2 import OwlOntologyImportWorker
from eddy.core.output import getLogger
from eddy.core.owl import (
    Annotation,
    AnnotationAssertion,
    AnnotationAssertionProperty,
    Facet,
    ImportedOntology,
    Literal,
    OWL2Datatype,
)
from eddy.core.project import (
    K_ASYMMETRIC,
    K_DESCRIPTION,
    K_FUNCTIONAL,
    K_INVERSE_FUNCTIONAL,
    K_IRREFLEXIVE,
    K_REFLEXIVE,
    K_SYMMETRIC,
    K_TRANSITIVE,
    Project,
    ProjectNotFoundError,
    ProjectNotValidError,
    ProjectStopImportingError,
    ProjectStopLoadingError,
    ProjectVersionError,
)
from eddy.core.regex import RE_FACET
from eddy.ui.dialogs import DiagramSelectionDialog

LOGGER = getLogger()


class GrapholDiagramLoader_v1(AbstractDiagramLoader):
    """
    Extends AbstractDiagramLoader with facilities to load diagrams from Graphol file format.
    """

    def __init__(self, path, project, session):
        """
        Initialize the Graphol diagram loader.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(path, project, session)

        self.diagram = None
        self.edges = dict()
        self.nodes = dict()

        self.importFuncForItem = {
            Item.AttributeNode: self.importAttributeNode,
            Item.ComplementNode: self.importComplementNode,
            Item.ConceptNode: self.importConceptNode,
            Item.DatatypeRestrictionNode: self.importDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.importDisjointUnionNode,
            Item.DomainRestrictionNode: self.importDomainRestrictionNode,
            Item.EnumerationNode: self.importEnumerationNode,
            Item.FacetNode: self.importFacetNode,
            Item.IndividualNode: self.importIndividualNode,
            Item.IntersectionNode: self.importIntersectionNode,
            Item.PropertyAssertionNode: self.importPropertyAssertionNode,
            Item.RangeRestrictionNode: self.importRangeRestrictionNode,
            Item.RoleNode: self.importRoleNode,
            Item.RoleChainNode: self.importRoleChainNode,
            Item.RoleInverseNode: self.importRoleInverseNode,
            Item.UnionNode: self.importUnionNode,
            Item.ValueDomainNode: self.importValueDomainNode,
            Item.InclusionEdge: self.importInclusionEdge,
            Item.EquivalenceEdge: self.importEquivalenceEdge,
            Item.InputEdge: self.importInputEdge,
            Item.MembershipEdge: self.importMembershipEdge,
        }

        self.itemFromXml = {
            'attribute': Item.AttributeNode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptNode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
            'facet': Item.FacetNode,
            'individual': Item.IndividualNode,
            'intersection': Item.IntersectionNode,
            'property-assertion': Item.PropertyAssertionNode,
            'range-restriction': Item.RangeRestrictionNode,
            'role': Item.RoleNode,
            'role-chain': Item.RoleChainNode,
            'role-inverse': Item.RoleInverseNode,
            'union': Item.UnionNode,
            'value-domain': Item.ValueDomainNode,
            'value-restriction': Item.FacetNode,
            'inclusion': Item.InclusionEdge,
            'equivalence': Item.EquivalenceEdge,
            'input': Item.InputEdge,
            'instance-of': Item.MembershipEdge,
            'membership': Item.MembershipEdge,
        }

    #############################################
    #   NODES
    #################################

    def importAttributeNode(self, e):
        """
        Build an Attribute node using the given QDomElement.
        :type e: QDomElement
        :rtype: AttributeNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.AttributeNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.iri = self.getIRIFromLabel(label.text(), node.type())
        node.doUpdateNodeLabel()
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importComplementNode(self, e):
        """
        Build a Complement node using the given QDomElement.
        :type e: QDomElement
        :rtype: ComplementNode
        """
        return self.importGenericNode(Item.ComplementNode, e)

    def importConceptNode(self, e):
        """
        Build a Concept node using the given QDomElement.
        :type e: QDomElement
        :rtype: ConceptNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.ConceptNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.iri = self.getIRIFromLabel(label.text(), node.type())
        node.doUpdateNodeLabel()
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importDatatypeRestrictionNode(self, e):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.importGenericNode(Item.DatatypeRestrictionNode, e)

    def importDisjointUnionNode(self, e):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type e: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.importGenericNode(Item.DisjointUnionNode, e)

    def importDomainRestrictionNode(self, e):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DomainRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.DomainRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importEnumerationNode(self, e):
        """
        Build an Enumeration node using the given QDomElement.
        :type e: QDomElement
        :rtype: EnumerationNode
        """
        return self.importGenericNode(Item.EnumerationNode, e)

    def importFacetNode(self, e):
        """
        Build a FacetNode node using the given QDomElement.
        :type e: QDomElement
        :rtype: FacetNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.FacetNode, e)
        match = RE_FACET.match(label.text())
        if match:
            facet = Facet(
                self.nproject.getIRI(match.group('facet')),
                Literal(match.group('value')),
            )
            node.facet = facet
            node.doUpdateNodeLabel()
        return node

    def importIndividualNode(self, e):
        """
        Build an Individual node using the given QDomElement.
        :type e: QDomElement
        :rtype: IndividualNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.IndividualNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.iri = self.getIRIFromLabel(label.text(), node.type())
        node.doUpdateNodeLabel()
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importIntersectionNode(self, e):
        """
        Build an Intersection node using the given QDomElement.
        :type e: QDomElement
        :rtype: IntersectionNode
        """
        return self.importGenericNode(Item.IntersectionNode, e)

    def importPropertyAssertionNode(self, e):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type e: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(Item.PropertyAssertionNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRangeRestrictionNode(self, e):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: RangeRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.RangeRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importRoleNode(self, e):
        """
        Build a Role node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.RoleNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.iri = self.getIRIFromLabel(label.text(), node.type())
        node.doUpdateNodeLabel()
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importRoleChainNode(self, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleChainNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(Item.RoleChainNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRoleInverseNode(self, e):
        """
        Build a RoleInverse node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleInverseNode
        """
        return self.importGenericNode(Item.RoleInverseNode, e)

    def importValueDomainNode(self, e):
        """
        Build a Value-Domain node using the given QDomElement.
        :type e: QDomElement
        :rtype: ValueDomainNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.ValueDomainNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.iri = self.project.getExpandedIRI(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importUnionNode(self, e):
        """
        Build a Union node using the given QDomElement.
        :type e: QDomElement
        :rtype: UnionNode
        """
        return self.importGenericNode(Item.UnionNode, e)

    #############################################
    #   EDGES
    #################################

    def importEquivalenceEdge(self, e):
        """
        Build an Equivalence edge using the given QDomElement.
        :type e: QDomElement
        :rtype: EquivalenceEdge
        """
        return self.importGenericEdge(Item.EquivalenceEdge, e)

    def importInclusionEdge(self, e):
        """
        Build an Inclusion edge using the given QDomElement.
        :type e: QDomElement
        :rtype: InclusionEdge
        """
        if self.getEdgeEquivalenceFromElement(e):
            return self.importEquivalenceEdge(e)
        return self.importGenericEdge(Item.InclusionEdge, e)

    def importInputEdge(self, e):
        """
        Build an Input edge using the given QDomElement.
        :type e: QDomElement
        :rtype: InputEdge
        """
        return self.importGenericEdge(Item.InputEdge, e)

    def importMembershipEdge(self, e):
        """
        Build a Membership edge using the given QDomElement.
        :type e: QDomElement
        :rtype: MembershipEdge
        """
        return self.importGenericEdge(Item.MembershipEdge, e)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def importGenericEdge(self, item, e):
        """
        Build an edge using the given item type and QDomElement.
        :type item: Item
        :type e: QDomElement
        :rtype: AbstractEdge
        """
        points = []
        point = self.getPointInsideElement(e)
        while not point.isNull():
            points.append(QtCore.QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = self.getPointBesideElement(point)

        source = self.nodes[e.attribute('source')]
        target = self.nodes[e.attribute('target')]
        edge = self.diagram.factory.create(item, **{
            'id': e.attribute('id'),
            'source': source,
            'target': target,
            'breakpoints': [
                p for p in points[1:-1]
                if not (source.painterPath().contains(p) or target.painterPath().contains(p))
            ]
        })

        path = edge.source.painterPath()
        if path.contains(edge.source.mapFromScene(points[0])):
            edge.source.setAnchor(edge, points[0])

        path = edge.target.painterPath()
        if path.contains(edge.target.mapFromScene(points[-1])):
            edge.target.setAnchor(edge, points[-1])

        edge.source.addEdge(edge)
        edge.target.addEdge(edge)
        return edge

    def importGenericNode(self, item, e):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type e: QDomElement
        :rtype: AbstractNode
        """
        geometry = self.getGeometryFromElement(e)
        node = self.diagram.factory.create(item, **{
            'id': e.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width'))
        })
        node.setPos(QtCore.QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        return node

    @staticmethod
    def getEdgeEquivalenceFromElement(e):
        """
        Returns the value of the 'equivalence' attribute from the given element.
        :type e: QDomElement
        :rtype: bool
        """
        if e.hasAttribute('equivalence'):
            return bool(int(e.attribute('equivalence', '0')))
        return bool(int(e.attribute('complete', '0')))

    def getIRIFromLabel(self, label, item, addRdfsLabel=False, lang=None):
        """
        Returns an IRI object from a plain text label.
        :type label: str
        :type item: Item
        :type addRdfsLabel: bool
        :type lang: str
        :rtype: IRI
        """
        label = label.replace('\n', '')
        if label == 'TOP':
            if item is Item.ConceptNode:
                ns = 'http://www.w3.org/2002/07/owl#Thing'
            elif item is Item.AttributeNode:
                ns = 'http://www.w3.org/2002/07/owl#topDataProperty'
            elif item is Item.RoleNode:
                ns = 'http://www.w3.org/2002/07/owl#topObjectProperty'
            else:
                ns = label
            iri = self.project.getIRI(ns)
        elif label == 'BOTTOM':
            if item is Item.ConceptNode:
                ns = 'http://www.w3.org/2002/07/owl#Nothing'
            elif item is Item.AttributeNode:
                ns = 'http://www.w3.org/2002/07/owl#bottomDataProperty'
            elif item is Item.RoleNode:
                ns = 'http://www.w3.org/2002/07/owl#bottomObjectProperty'
            else:
                ns = label
            iri = self.project.getIRI(ns)
        else:
            iri = self.project.getIRI(label)
            if addRdfsLabel:
                annotation = AnnotationAssertion(
                    iri, AnnotationAssertionProperty.Label.value,
                    label, OWL2Datatype.PlainLiteral.value, lang)
                iri.addAnnotationAssertion(annotation)
        return iri

    @staticmethod
    def getGeometryFromElement(e):
        """
        Returns the geometry element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('geometry')
        if search.isNull():
            search = e.firstChildElement('shape:geometry')
        return search

    @staticmethod
    def getLabelFromElement(e):
        """
        Returns the label element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('label')
        if search.isNull():
            search = e.firstChildElement('shape:label')
        return search

    @staticmethod
    def getPointBesideElement(e):
        """
        Returns the point element beside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.nextSiblingElement('point')
        if search.isNull():
            search = e.nextSiblingElement('line:point')
        return search

    @staticmethod
    def getPointInsideElement(e):
        """
        Returns the point element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('point')
        if search.isNull():
            search = e.firstChildElement('line:point')
        return search

    def itemFromGrapholNode(self, e):
        """
        Returns the item matching the given graphol node.
        :type e: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[e.attribute('type').lower().strip()]
        except KeyError:
            return None

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform diagram import from Graphol file format and add it to the project.
        """
        LOGGER.info('Loading diagram: %s', self.path)

        if not fexists(self.path):
            raise DiagramNotFoundError('diagram not found: {0}'.format(self.path))

        document = QtXml.QDomDocument()
        if not document.setContent(fread(self.path)):
            raise DiagramNotValidError('could not parse diagram from {0}'.format(self.path))

        root = document.documentElement()
        graph = root.firstChildElement('graph')
        size = max(int(graph.attribute('width', '10000')), int(graph.attribute('height', '10000')))

        #############################################
        # CREATE AN EMPTY DIAGRAM
        #################################

        LOGGER.debug('Initialzing empty diagram with size: %s', size)

        name = os.path.basename(self.path)
        name = rstrip(name, File.Graphol.extension)
        self.diagram = Diagram.create(name, size, self.project)

        #############################################
        # LOAD NODES
        #################################

        element = graph.firstChildElement('node')
        while not element.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromGrapholNode(element)
                func = self.importFuncForItem[item]
                node = func(element)
            except Exception:
                LOGGER.exception('Failed to create node %s', element.attribute('id'))
            else:
                self.diagram.addItem(node)
                self.diagram.guid.update(node.id)
                self.nodes[node.id] = node
            finally:
                element = element.nextSiblingElement('node')

        LOGGER.debug('Loaded nodes: %s', len(self.nodes))

        #############################################
        # LOAD EDGES
        #################################

        element = graph.firstChildElement('edge')
        while not element.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromGrapholNode(element)
                func = self.importFuncForItem[item]
                edge = func(element)
            except Exception:
                LOGGER.exception('Failed to create edge %s', element.attribute('id'))
            else:
                self.diagram.addItem(edge)
                self.diagram.guid.update(edge.id)
                self.edges[edge.id] = edge
                edge.updateEdge()
            finally:
                element = element.nextSiblingElement('edge')

        LOGGER.debug('Loaded edges: %s', len(self.edges))

        #############################################
        # IDENTIFY NODES
        #################################

        nodes = [n for n in self.nodes.values() if Identity.Neutral in n.identities()]
        if nodes:
            LOGGER.debug('Running identification algorithm for %s nodes', len(nodes))
            for node in nodes:
                self.diagram.sgnNodeIdentification.emit(node)

        #############################################
        # CONFIGURE DIAGRAM SIGNALS
        #################################

        connect(self.diagram.sgnItemAdded, self.project.doAddItem)
        connect(self.diagram.sgnItemRemoved, self.project.doRemoveItem)
        connect(self.diagram.selectionChanged, self.session.doUpdateState)

        LOGGER.debug('Diagram created: %s', self.diagram.name)

        #############################################
        # ADD THE DIAGRAM TO THE PROJECT
        #################################

        self.project.addDiagram(self.diagram)

        LOGGER.debug('Diagram "%s" added to project "%s"', self.diagram.name, self.project.name)


class GrapholProjectLoader_v1(AbstractProjectLoader):
    """
    Extends AbstractProjectLoader with facilities to load Graphol projects.
    This class can be used to load projects.

    A Graphol project is stored within a directory whose structure is the following:

    - projectname/
    -   .eddy/              # subdirectory which contains project specific information
    -       meta.xml        # contains ontology and predicates meta information
    -       modules.xml     # contains the paths of all the modules of the ontology

    -   module1.graphol
    -   module2.graphol
    -   ...
    -   moduleN.graphol
    """

    def __init__(self, path, session):
        """
        Initialize the project loader.
        :type path: str
        :type session: Session
        """
        super().__init__(path, session)

        self.project = None
        self.metaDocument = None
        self.modulesDocument = None

        self.projectMainPath = expandPath(self.path)
        self.projectHomePath = os.path.join(self.projectMainPath, '.eddy')
        self.projectMetaDataPath = os.path.join(self.projectHomePath, 'meta.xml')
        self.projectModulesDataPath = os.path.join(self.projectHomePath, 'modules.xml')

        self.metaFuncForItem = {
            Item.AttributeNode: self.importAttributeMetadata,
            Item.ConceptNode: self.importPredicateMetadata,
            Item.IndividualNode: self.importPredicateMetadata,
            Item.RoleNode: self.importRoleMetadata,
        }

        self.itemFromXml = {
            'attribute': Item.AttributeNode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptNode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
            'facet': Item.FacetNode,
            'individual': Item.IndividualNode,
            'intersection': Item.IntersectionNode,
            'property-assertion': Item.PropertyAssertionNode,
            'range-restriction': Item.RangeRestrictionNode,
            'role': Item.RoleNode,
            'role-chain': Item.RoleChainNode,
            'role-inverse': Item.RoleInverseNode,
            'union': Item.UnionNode,
            'value-domain': Item.ValueDomainNode,
            'inclusion': Item.InclusionEdge,
            'input': Item.InputEdge,
            'instance-of': Item.MembershipEdge,
            'membership': Item.MembershipEdge,
        }

    #############################################
    #   AUXILIARY METHODS
    #################################

    def importAttributeMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        """
        self.importPredicateMetadata(element)
        iri = self.project.getIRI(element.attribute('name'))
        iri.functional = bool(int(element.firstChildElement(K_FUNCTIONAL).text()))

    def importPredicateMetadata(self, element):
        """
        Build predicate metadata using the given QDomElement.
        :type element: QDomElement
        """
        iri = self.project.getIRI(element.attribute('name'))
        description = AnnotationAssertion(
            iri,
            self.project.getIRI('http://www.w3.org/2000/01/rdf-schema#comment'),
            element.firstChildElement(K_DESCRIPTION).text(),
        )
        # We currently don't import K_URL as we derive the predicate IRI from its label.
        # url = element.firstChildElement(K_URL).text()
        iri.addAnnotationAssertion(description)

    def importRoleMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: dict
        """
        self.importPredicateMetadata(element)
        iri = self.project.getIRI(element.attribute('name'))
        iri.functional = bool(int(element.firstChildElement(K_FUNCTIONAL).text()))
        iri.inverseFunctional = bool(int(element.firstChildElement(K_INVERSE_FUNCTIONAL).text()))
        iri.asymmetric = bool(int(element.firstChildElement(K_ASYMMETRIC).text()))
        iri.irreflexive = bool(int(element.firstChildElement(K_IRREFLEXIVE).text()))
        iri.reflexive = bool(int(element.firstChildElement(K_REFLEXIVE).text()))
        iri.symmetric = bool(int(element.firstChildElement(K_SYMMETRIC).text()))
        iri.transitive = bool(int(element.firstChildElement(K_TRANSITIVE).text()))

    #############################################
    #   IMPORT PROJECT FROM XML
    #################################

    def importProjectFromXML(self):
        """
        Initialize the project instance by reading project metadata from XML file.
        :raise ProjectNotValidError: If the project metadata file is missing or not readable.
        """
        QtWidgets.QApplication.processEvents()

        LOGGER.info('Loading ontology metadata from %s', self.projectMetaDataPath)

        if not fexists(self.projectMetaDataPath):
            raise ProjectNotValidError('missing project metadata: {0}'.format(self.projectMetaDataPath))

        self.metaDocument = QtXml.QDomDocument()
        if not self.metaDocument.setContent(fread(self.projectMetaDataPath)):
            raise ProjectNotValidError('could read project metadata from {0}'.format(self.projectMetaDataPath))

        path = self.projectMainPath
        root = self.metaDocument.documentElement()
        ontology = root.firstChildElement('ontology')
        prefix = ontology.firstChildElement('prefix').text()
        LOGGER.debug('Loaded ontology prefix: %s', prefix)
        iri = ontology.firstChildElement('iri').text()
        LOGGER.debug('Loaded ontology IRI: %s', iri)
        profileName = ontology.firstChildElement('profile').text()
        if not profileName:
            profileName = 'OWL 2'
            LOGGER.warning('Missing ontology profile, using default: %s', profileName)
        profile = self.session.createProfile(profileName)
        LOGGER.debug('Loaded ontology profile: %s', profile.name())
        self.project = Project(
            name=os.path.basename(path),
            ontologyIRI=iri,
            path='{}{}'.format(path, File.Graphol.extension),
            profile=profile,
            parent=self.session,
        )

    def importMetaFromXML(self):
        """
        Import predicate metadata from XML file.
        """
        QtWidgets.QApplication.processEvents()

        #############################################
        # LOAD PREDICATE METADATA
        #################################

        LOGGER.info('Loading ontology predicate metadata from %s', self.projectMetaDataPath)

        root = self.metaDocument.documentElement()
        predicates = root.firstChildElement('predicates')
        predicate = predicates.firstChildElement('predicate')
        while not predicate.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXml[predicate.attribute('type')]
                func = self.metaFuncForItem[item]
                func(predicate)
            except Exception:
                LOGGER.exception('Failed to create metadata for predicate %s', predicate.attribute('name'))
            finally:
                predicate = predicate.nextSiblingElement('predicate')

        #############################################
        # UPDATE LAYOUT ACCORDING TO METADATA
        #################################

        predicates = self.project.iriOccurrences()
        LOGGER.info('Refreshing state for %s predicate nodes', len(predicates))
        for node in predicates:
            node.updateNode()

    def importModulesFromXML(self):
        """
        Import project modules from XML file.
        :raise ProjectNotValidError: If the project structure file is missing or not readable.
        """
        QtWidgets.QApplication.processEvents()

        LOGGER.info('Loading ontology structure from %s', self.projectModulesDataPath)

        if not fexists(self.projectModulesDataPath):
            raise ProjectNotValidError('missing project structure: {0}'.format(self.projectModulesDataPath))

        self.modulesDocument = QtXml.QDomDocument()
        if not self.modulesDocument.setContent(fread(self.projectModulesDataPath)):
            raise ProjectNotValidError('could read project structure from {0}'.format(self.projectModulesDataPath))

        root = self.modulesDocument.documentElement()
        modules = root.firstChildElement('modules')
        mod = modules.firstChildElement('module')
        while not mod.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                name = mod.text()
                path = os.path.join(self.projectMainPath, name)
                worker = GrapholDiagramLoader_v1(path, self.project, self.session)
                worker.run()
            except (DiagramNotFoundError, DiagramNotValidError) as e:
                LOGGER.warning('Failed to load project diagram %s: %s', name, e)
            except Exception:
                LOGGER.exception('Failed to load diagram module %s', name)
            finally:
                mod = mod.nextSiblingElement('module')

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform project import (LEGACY MODE).
        """
        #############################################
        # VALIDATE PROJECT
        #################################

        if not isdir(self.projectMainPath):
            raise ProjectNotFoundError('project not found: {0}'.format(self.projectMainPath))

        if not isdir(self.projectHomePath):
            raise ProjectNotValidError('missing project home: {0}'.format(self.projectHomePath))

        #############################################
        # LEGACY LOADING CHECK
        #################################

        msgbox = QtWidgets.QMessageBox()
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Legacy mode')
        msgbox.setText(textwrap.dedent("""
        You have selected an {EDDY} version <b>1</b> project.<br/>
        If you continue with the loading procedure the project will be automatically
        converted to the most recent project version.<br/><br/>
        Do you want to continue?
        """.format(EDDY=APPNAME)))
        msgbox.exec_()

        if msgbox.result() == QtWidgets.QMessageBox.No:
            raise ProjectStopLoadingError

        #############################################
        # IMPORT PROJECT
        #################################

        LOGGER.info('Loading ontology: %s (LEGACY MODE)...', os.path.basename(self.projectMainPath))

        self.importProjectFromXML()
        self.importModulesFromXML()
        self.importMetaFromXML()

        #############################################
        # BACKUP PROJECT DIRECTORY
        #################################

        projectName = os.path.basename(self.projectMainPath)
        archivePath = os.path.join(self.projectMainPath, os.path.pardir)
        archiveName = '{}-{}'.format(projectName, int(round(time() * 1000)))
        archiveFullName = os.path.join(archivePath, archiveName)
        LOGGER.info('Archiving legacy project to: {}'.format(archiveFullName))
        make_archive(archivePath, expandPath(archiveFullName), projectName)

        #############################################
        # CLEANUP PROJECT DIRECTORY
        #################################

        rmdir(self.projectMainPath)

        #############################################
        # SET THE LOADED PROJECT IN THE CURRENT SESSION
        #################################

        self.session.project = self.project


class GrapholProjectIRILoaderMixin_2(object):
    """
    Mixin which adds the ability to create a project out of a Graphol file.
    """

    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)

        self.buffer = dict()
        self.document = None
        self.nproject = None

        self.itemFromXml = {
            'attribute': Item.AttributeNode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptNode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
            'facet': Item.FacetNode,
            'individual': Item.IndividualNode,
            'intersection': Item.IntersectionNode,
            'property-assertion': Item.PropertyAssertionNode,
            'range-restriction': Item.RangeRestrictionNode,
            'role': Item.RoleNode,
            'role-chain': Item.RoleChainNode,
            'role-inverse': Item.RoleInverseNode,
            'union': Item.UnionNode,
            'value-domain': Item.ValueDomainNode,
            'inclusion': Item.InclusionEdge,
            'equivalence': Item.EquivalenceEdge,
            'input': Item.InputEdge,
            'membership': Item.MembershipEdge,
            'same': Item.SameEdge,
            'different': Item.DifferentEdge,
        }

        self.importFuncForItem = {
            Item.AttributeNode: self.importAttributeNode,
            Item.ComplementNode: self.importComplementNode,
            Item.ConceptNode: self.importConceptNode,
            Item.DatatypeRestrictionNode: self.importDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.importDisjointUnionNode,
            Item.DomainRestrictionNode: self.importDomainRestrictionNode,
            Item.EnumerationNode: self.importEnumerationNode,
            Item.FacetNode: self.importFacetNode,
            Item.IndividualNode: self.importIndividualNode,
            Item.IntersectionNode: self.importIntersectionNode,
            Item.PropertyAssertionNode: self.importPropertyAssertionNode,
            Item.RangeRestrictionNode: self.importRangeRestrictionNode,
            Item.RoleNode: self.importRoleNode,
            Item.RoleChainNode: self.importRoleChainNode,
            Item.RoleInverseNode: self.importRoleInverseNode,
            Item.UnionNode: self.importUnionNode,
            Item.ValueDomainNode: self.importValueDomainNode,
            Item.InclusionEdge: self.importInclusionEdge,
            Item.EquivalenceEdge: self.importEquivalenceEdge,
            Item.InputEdge: self.importInputEdge,
            Item.MembershipEdge: self.importMembershipEdge,
            Item.SameEdge: self.importSameEdge,
            Item.DifferentEdge: self.importDifferentEdge,
        }

        self.importMetaFuncForItem = {
            Item.AttributeNode: self.importAttributeMeta,
            Item.ConceptNode: self.importConceptMeta,
            Item.IndividualNode: self.importIndividualMeta,
            Item.RoleNode: self.importRoleMeta,
        }

    #############################################
    #   DOCUMENT (Prefixes,OntologyIRI)
    #################################

    def createDomDocument(self):
        """
        Create the QDomDocument from where to parse Project information.
        """
        if not fexists(self.path):
            raise ProjectNotFoundError('missing project ontology: %s' % self.path)
        self.document = QtXml.QDomDocument()
        if File.forPath(self.path) is not File.Graphol or not self.document.setContent(fread(self.path)):
            raise ProjectNotValidError('invalid project ontology supplied: %s' % self.path)
        e = self.document.documentElement()
        version = int(e.attribute('version', '2'))
        if version != 2:
            raise ProjectVersionError('project version mismatch: %s != 2' % version)

    #############################################
    #   PROJECT (Prefixes,OntologyIRI)
    #################################

    def createProject(self):
        """
        Create the Project by reading data from the parsed QDomDocument.
        """
        section = self.document.documentElement().firstChildElement('ontology')

        def parse(tag, default='NULL'):
            """
            Read an element from the given tag.
            :type tag: str
            :type default: str
            :rtype: str
            """
            QtWidgets.QApplication.processEvents()
            subelement = section.firstChildElement(tag)
            if subelement.isNull():
                LOGGER.warning('Missing tag <%s> in ontology section, using default: %s', tag, default)
                return default
            content = subelement.text()
            if (not content):
                LOGGER.warning('Empty tag <%s> in ontology section, using default: %s', tag, default)
                return default
            LOGGER.debug('Loaded ontology %s: %s', tag, content)
            return content

        self.nproject = Project(
            parent=self.session,
            path=self.path,
            name=parse(tag='name', default=os.path.splitext(self.path)[0]),
            version=parse(tag='version', default='1.0'),
            profile=self.session.createProfile('OWL 2'),
            prefixMap=self.getPrefixesDict(section),
            ontologyIRI=self.getOntologyIRI(section),
            ontologyPrefix=self.getOntologyPrefix(section),
        )
        LOGGER.info('Loaded ontology: %s...', self.nproject.name)

    def getOntologyIRI(self, ontologySection):
        result = ''
        e = ontologySection.firstChildElement('IRI_prefixes_nodes_dict')
        if not e.isNull():
            sube = e.firstChildElement('iri')
            while not sube.isNull():
                try:
                    QtWidgets.QApplication.processEvents()
                    namespace = sube.attribute('iri_value')
                    sube_properties = sube.firstChildElement('properties')
                    sube_property = sube_properties.firstChildElement('property')
                    while not sube_property.isNull():
                        try:
                            QtWidgets.QApplication.processEvents()
                            property_value = sube_property.attribute('property_value')
                        except Exception:
                            LOGGER.exception('Failed to fetch property %s', property_value)
                        else:
                            if property_value == 'Project_IRI':
                                return namespace
                        finally:
                            sube_property = sube_property.nextSiblingElement('property')
                except Exception:
                    LOGGER.exception('Failed to fetch namespace  %s', namespace)
                finally:
                    sube = sube.nextSiblingElement('iri')
        else:
            ontIriEl = ontologySection.firstChildElement('iri')
            if not ontIriEl.isNull():
                if ontIriEl.text():
                    return ontIriEl.text()
        return result

    def getOntologyPrefix(self, ontologySection):
        result = ''
        e = ontologySection.firstChildElement('IRI_prefixes_nodes_dict')
        sube = e.firstChildElement('iri')
        while not sube.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                sube_properties = sube.firstChildElement('properties')
                sube_property = sube_properties.firstChildElement('property')
                while not sube_property.isNull():
                    try:
                        QtWidgets.QApplication.processEvents()
                        property_value = sube_property.attribute('property_value')
                    except Exception:
                        LOGGER.exception('Failed to fetch property %s', property_value)
                    else:
                        if property_value == 'Project_IRI':
                            prefix_value = None
                            sube_prefixes = sube.firstChildElement('prefixes')
                            sube_prefix = sube_prefixes.firstChildElement('prefix')
                            if not sube_prefix.isNull():
                                prefix_value = sube_prefix.attribute('prefix_value')
                            else:
                                prefix_value =''
                            return prefix_value
                    finally:
                        sube_property = sube_property.nextSiblingElement('property')
            except Exception:
                iriValue = sube.attribute('iri_value')
                LOGGER.exception('Failed to fetch namespace  %s', iriValue if iriValue else '"unknown"')
            finally:
                sube = sube.nextSiblingElement('iri')
        return result

    def getPrefixesDict(self, ontologySection):
        dictionary_to_return = dict()
        e = ontologySection.firstChildElement('IRI_prefixes_nodes_dict')
        if not e.isNull():
            sube = e.firstChildElement('iri')
            while not sube.isNull():
                try:
                    QtWidgets.QApplication.processEvents()
                    namespace = sube.attribute('iri_value')

                    ### Needed to fix the namespace of standard vocabularies which up to
                    ### version 1.1.2 where stored without the fragment separator (#).
                    ### See: https://github.com/obdasystems/eddy/issues/20
                    for ns in Namespace:
                        if namespace+'#' == ns.value:
                            # Append the missing fragment separator
                            namespace += '#'
                            break

                    sube_prefixes = sube.firstChildElement('prefixes')

                    #PREFIX MAP
                    sube_prefix = sube_prefixes.firstChildElement('prefix')
                    while not sube_prefix.isNull():
                        try:
                            QtWidgets.QApplication.processEvents()
                            prefix_value = sube_prefix.attribute('prefix_value')
                        except Exception:
                            LOGGER.exception('Failed to fetch prefixes %s', prefix_value)
                        else:
                            dictionary_to_return[prefix_value]=namespace
                        finally:
                            sube_prefix = sube_prefix.nextSiblingElement('prefix')
                except Exception:
                    LOGGER.exception('Failed to fetch namespace  %s', namespace)
                finally:
                    sube = sube.nextSiblingElement('iri')
        else:
            prefixEl = ontologySection.firstChildElement('prefix')
            ontIriEl = ontologySection.firstChildElement('iri')
            if not (prefixEl.isNull() or ontIriEl.isNull()):
                if ontIriEl.text():
                    dictionary_to_return[prefixEl.text()] = ontIriEl.text()

        return dictionary_to_return

    def projectRender(self):
        """
        Render all the elements in the Project ontology.
        """
        for item in self.nproject.items():
            QtWidgets.QApplication.processEvents()
            item.updateEdgeOrNode()

    #############################################
    #   DIAGRAM
    #################################
    def createDiagrams(self):
        """
        Create ontology diagrams by parsing the 'diagrams' section of the QDomDocument.
        """
        counter = 1
        section = self.document.documentElement().firstChildElement('diagrams')
        element = section.firstChildElement('diagram')
        while not element.isNull():
            self.nproject.addDiagram(self.importDiagram(element, counter))
            element = element.nextSiblingElement('diagram')
            counter += 1

    def importDiagram(self, diagramElement, i):
        """
        Create a diagram from the given QDomElement.
        :type e: QDomElement
        :type i: int
        :rtype: Diagram
        """
        QtWidgets.QApplication.processEvents()
        ## PARSE DIAGRAM INFORMATION
        name = diagramElement.attribute('name', 'diagram_{0}'.format(i))
        size = max(int(diagramElement.attribute('width', '10000')), int(diagramElement.attribute('height', '10000')))
        ## CREATE NEW DIAGRAM
        LOGGER.info('Loading diagram: %s', name)
        diagram = Diagram.create(name, size, self.nproject)
        self.buffer[diagram.name] = dict()
        ## LOAD DIAGRAM NODES
        nodeElement = diagramElement.firstChildElement('node')
        while not nodeElement.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(nodeElement)
                func = self.importFuncForItem[item]
                node = func(diagram,nodeElement)
            except Exception as e:
                LOGGER.exception('Failed to create node {}. [{}]'.format(nodeElement.attribute('id'),e))
            else:
                diagram.addItem(node)
                diagram.guid.update(node.id)
                self.buffer[diagram.name][node.id] = node
            finally:
                nodeElement = nodeElement.nextSiblingElement('node')

        ## LOAD DIAGRAM EDGES
        edgeElement = diagramElement.firstChildElement('edge')
        while not edgeElement.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(edgeElement)
                func = self.importFuncForItem[item]
                edge = func(diagram, edgeElement)
            except Exception as e:
                LOGGER.exception('Failed to create edge {}. [{}]'.format(edgeElement.attribute('id'),e))
            else:
                diagram.addItem(edge)
                diagram.guid.update(edge.id)
                self.buffer[diagram.name][edge.id] = edge
            finally:
                edgeElement = edgeElement.nextSiblingElement('edge')
        ## IDENTIFY NEUTRAL NODES
        nodes = [x for x in diagram.items(edges=False) if Identity.Neutral in x.identities()]
        if nodes:
            LOGGER.debug('Running identification algorithm for %s nodes', len(nodes))
            for node in nodes:
                diagram.sgnNodeIdentification.emit(node)
        ## CONFIGURE DIAGRAM SIGNALS
        connect(diagram.sgnItemAdded, self.nproject.doAddItem)
        connect(diagram.sgnItemRemoved, self.nproject.doRemoveItem)
        connect(diagram.selectionChanged, self.session.doUpdateState)
        ## RETURN GENERATED DIAGRAM
        return diagram

    #############################################
    #   IRI META
    #################################
    def createPredicatesMeta(self):
        """
        Create ontology predicate metadata by parsing the 'predicates' section of the QDomDocument.
        """
        section = self.document.documentElement().firstChildElement('predicates')
        predicateElement = section.firstChildElement('predicate')
        while not predicateElement.isNull():
            try:
                QtWidgets.QApplication.processEvents()

                prefixedIriString = predicateElement.attribute('name')
                iriElList = prefixedIriString.split(':')
                if len(iriElList) > 1:
                    prefix = iriElList[0]
                    resolvedPrefix = self.nproject.getPrefixResolution(prefix)
                    if not resolvedPrefix:
                        resolvedPrefix = ''
                    namespace = iriElList[1]
                    iriString = '{}{}'.format(resolvedPrefix, namespace)
                elif len(iriElList) == 1:
                    iriString = iriElList[0]
                else:
                    iriString = prefixedIriString
                predicateIRI = self.nproject.getIRI(iriString)

                value = rtfStripFontAttributes(predicateElement.firstChildElement(K_DESCRIPTION).text())
                if value:
                    commentIRI = self.nproject.getIRI('http://www.w3.org/2000/01/rdf-schema#comment')
                    annAss = AnnotationAssertion(predicateIRI,commentIRI,value,OWL2Datatype.PlainLiteral.value, 'it')
                    predicateIRI.addAnnotationAssertion(annAss)

                item = self.itemFromXml[predicateElement.attribute('type')]
                func = self.importMetaFuncForItem[item]
                func(predicateElement,predicateIRI)
            except Exception as e:
                LOGGER.exception('Failed to import meta for predicate {}. [{}]'.format(predicateElement.attribute('name'),e))
            finally:
                predicateElement = predicateElement.nextSiblingElement('predicate')

    def importAttributeMeta(self, predicateElement, iri):
        boolValue = bool(int(predicateElement.firstChildElement(K_FUNCTIONAL).text()))
        iri.functional = boolValue

    def importConceptMeta(self, predicateElement, iri):
        pass

    def importIndividualMeta(self, predicateElement, iri):
        pass

    def importRoleMeta(self, predicateElement, iri):
        boolValue = bool(int(predicateElement.firstChildElement(K_FUNCTIONAL).text()))
        iri.functional = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_INVERSE_FUNCTIONAL).text()))
        iri.inverseFunctional = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_ASYMMETRIC).text()))
        iri.asymmetric = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_IRREFLEXIVE).text()))
        iri.irreflexive = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_REFLEXIVE).text()))
        iri.reflexive = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_SYMMETRIC).text()))
        iri.symmetric = boolValue
        boolValue = bool(int(predicateElement.firstChildElement(K_TRANSITIVE).text()))
        iri.transitive = boolValue

    #############################################
    #   NODES
    #################################

    def getIriFromLabelText(self, labelText, itemType, addRdfsLabel=False, lang=None):
        iriString = ''
        if labelText == 'TOP':
            addRdfsLabel = False
            if itemType is Item.AttributeNode:
                iriString = 'http://www.w3.org/2002/07/owl#topDataProperty'
            if itemType is Item.RoleNode:
                iriString = 'http://www.w3.org/2002/07/owl#topObjectProperty'
            if itemType is Item.ConceptNode:
                iriString = 'http://www.w3.org/2002/07/owl#Thing'
        elif labelText == 'BOTTOM':
            addRdfsLabel = False
            if itemType is Item.AttributeNode:
                iriString = 'http://www.w3.org/2002/07/owl#bottomDataProperty'
            if itemType is Item.RoleNode:
                iriString = 'http://www.w3.org/2002/07/owl#bottomObjectProperty'
            if itemType is Item.ConceptNode:
                iriString = 'http://www.w3.org/2002/07/owl#Nothing'
        labelTextForIRI = labelText.replace('\n','')
        iriElList = labelTextForIRI.split(':')
        if len(iriElList) > 1:
            prefix = iriElList[0]
            resolvedPrefix = self.nproject.getPrefixResolution(prefix)
            if not resolvedPrefix:
                resolvedPrefix = ''
            simpleName = iriElList[1]
            iriString = '{}{}'.format(resolvedPrefix, simpleName)
        elif len(iriElList) == 1:
            iriString = iriElList[0]
        else:
            iriString = labelTextForIRI
        iri = self.nproject.getIRI(iriString)
        if addRdfsLabel:
            annAss = iri.getAnnotationAssertion(AnnotationAssertionProperty.Label.value, lang=lang)
            if not annAss:
                rdfsLabelValue = labelText
                labelElList = labelText.split(':')
                if len(labelElList)>1:
                    rdfsLabelValue = labelElList[1]
                annAss = AnnotationAssertion(iri, AnnotationAssertionProperty.Label.value, rdfsLabelValue,OWL2Datatype.PlainLiteral.value, lang)
                iri.addAnnotationAssertion(annAss)
        return iri

    def getIriPredicateNode(self, diagram, nodeElement, itemType):
        addRdfsLabel = False if itemType is Item.ValueDomainNode else True
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        iri = self.getIriFromLabelText(labelText,itemType,addRdfsLabel=addRdfsLabel, lang='it')
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(itemType, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'iri': iri
        })
        node.setBrush(QtGui.QBrush(QtGui.QColor(nodeElement.attribute('color', '#fcfcfc'))))
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.doUpdateNodeLabel()
        node.setTextPos(
            node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))
        return node

    def importAttributeNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.AttributeNode)

    def importRoleNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.RoleNode)

    def importConceptNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.ConceptNode)

    def importIndividualNode(self, diagram, nodeElement):
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        doubleQuote = '"'
        if doubleQuote in labelText:
            return self.importLiteralNode(diagram, nodeElement)
        return self.getIriPredicateNode(diagram, nodeElement, Item.IndividualNode)

    def importValueDomainNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.ValueDomainNode)

    def importLiteralNode(self, diagram, nodeElement):
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        firstQuote = labelText.find('"')
        secondQuote = labelText.rfind('"')
        lexForm = labelText[firstQuote+1:secondQuote]
        typeIndex = labelText.rfind('^')
        prefixedType = labelText[typeIndex+1:]
        colonIndex = prefixedType.find(':')
        prefix = prefixedType[:colonIndex]
        ns = prefixedType[colonIndex+1:]
        iriString = '{}{}'.format(self.nproject.getPrefixResolution(prefix), ns)
        dtIRI = self.nproject.getIRI(iriString)
        literal = Literal(lexForm,dtIRI)
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(Item.LiteralNode, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'literal': literal
        })
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.doUpdateNodeLabel()
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))
        return node

    def importFacetNode(self, diagram, nodeElement):
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        firstQuote = labelText.find('"')
        secondQuote = labelText.rfind('"')
        lexForm = labelText[firstQuote + 1:secondQuote]
        literal = Literal(lexForm)
        typeIndex = labelText.find('^')
        prefixedType = labelText[:typeIndex]
        colonIndex = prefixedType.find(':')
        prefix = prefixedType[:colonIndex]
        ns = prefixedType[colonIndex + 1:]
        iriString = '{}{}'.format(self.nproject.getPrefixResolution(prefix), ns)
        conFacetIRI = self.nproject.getIRI(iriString)
        facet = Facet(conFacetIRI,literal)
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(Item.FacetNode, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'facet': facet
        })
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.doUpdateNodeLabel()
        node.setTextPos(
            node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))
        return node

    def importComplementNode(self, diagram, e):
        """
        Build a Complement node using the given QDomElement.
        :type e: QDomElement
        :rtype: ComplementNode
        """
        return self.importGenericNode(diagram, Item.ComplementNode, e)

    def importDatatypeRestrictionNode(self, diagram, e):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.importGenericNode(diagram, Item.DatatypeRestrictionNode, e)

    def importDisjointUnionNode(self, diagram, e):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type e: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.importGenericNode(diagram, Item.DisjointUnionNode, e)

    def importDomainRestrictionNode(self, diagram, e):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DomainRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(diagram, Item.DomainRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importEnumerationNode(self, diagram, e):
        """
        Build an Enumeration node using the given QDomElement.
        :type e: QDomElement
        :rtype: EnumerationNode
        """
        return self.importGenericNode(diagram, Item.EnumerationNode, e)

    def importIntersectionNode(self, diagram, e):
        """
        Build an Intersection node using the given QDomElement.
        :type e: QDomElement
        :rtype: IntersectionNode
        """
        return self.importGenericNode(diagram, Item.IntersectionNode, e)

    def importPropertyAssertionNode(self, diagram, e):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type e: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(diagram, Item.PropertyAssertionNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRangeRestrictionNode(self, diagram, e):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: RangeRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(diagram, Item.RangeRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importRoleChainNode(self, diagram, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleChainNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(diagram, Item.RoleChainNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRoleInverseNode(self, diagram, e):
        """
        Build a RoleInverse node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleInverseNode
        """
        return self.importGenericNode(diagram, Item.RoleInverseNode, e)

    def importUnionNode(self, diagram, e):
        """
        Build a Union node using the given QDomElement.
        :type e: QDomElement
        :rtype: UnionNode
        """
        return self.importGenericNode(diagram, Item.UnionNode, e)

    #############################################
    #   EDGES
    #################################

    def importEquivalenceEdge(self, d, e):
        """
        Build an Equivalence edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: EquivalenceEdge
        """
        return self.importGenericEdge(d, Item.EquivalenceEdge, e)

    def importInclusionEdge(self, d, e):
        """
        Build an Inclusion edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: InclusionEdge
        """
        return self.importGenericEdge(d, Item.InclusionEdge, e)

    def importInputEdge(self, d, e):
        """
        Build an Input edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: InputEdge
        """
        return self.importGenericEdge(d, Item.InputEdge, e)

    def importMembershipEdge(self, d, e):
        """
        Build a Membership edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: MembershipEdge
        """
        return self.importGenericEdge(d, Item.MembershipEdge, e)

    def importSameEdge(self, d, e):
        """
        Build a Same edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: SameEdge
        """
        return self.importGenericEdge(d, Item.SameEdge, e)

    def importDifferentEdge(self, d, e):
        """
        Build a Different edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DifferentEdge
        """
        return self.importGenericEdge(d, Item.DifferentEdge, e)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def itemFromXmlNode(self, e):
        """
        Returns the item matching the given Graphol XML node.
        :type e: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[e.attribute('type').lower().strip()]
        except KeyError:
            return None

    def importGenericEdge(self, d, i, e):
        """
        Build an edge using the given item type and QDomElement.
        :type d: Diagram
        :type i: Item
        :type e: QDomElement
        :rtype: AbstractEdge
        """
        points = []
        point = e.firstChildElement('point')
        while not point.isNull():
            points.append(QtCore.QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = point.nextSiblingElement('point')

        source = self.buffer[d.name][e.attribute('source')]
        target = self.buffer[d.name][e.attribute('target')]
        edge = d.factory.create(i, **{
            'id': e.attribute('id'),
            'source': source,
            'target': target,
            'breakpoints': [p for p in points[1:-1]
                            if not (source.painterPath().contains(source.mapFromScene(p)) or
                                    target.painterPath().contains(target.mapFromScene(p)))]
        })

        path = edge.source.painterPath()
        if path.contains(edge.source.mapFromScene(points[0])):
            edge.source.setAnchor(edge, points[0])

        path = edge.target.painterPath()
        if path.contains(edge.target.mapFromScene(points[-1])):
            edge.target.setAnchor(edge, points[-1])

        edge.source.addEdge(edge)
        edge.target.addEdge(edge)
        return edge

    def importGenericNode(self, diagram, item, e):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type e: QDomElement
        :rtype: AbstractNode
        """
        geometry = self.getGeometryFromElement(e)
        node = diagram.factory.create(item, **{
            'id': e.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width'))
        })
        node.setPos(QtCore.QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        return node

    @staticmethod
    def getEdgeEquivalenceFromElement(e):
        """
        Returns the value of the 'equivalence' attribute from the given element.
        :type e: QDomElement
        :rtype: bool
        """
        if e.hasAttribute('equivalence'):
            return bool(int(e.attribute('equivalence', '0')))
        return bool(int(e.attribute('complete', '0')))

    @staticmethod
    def getGeometryFromElement(e):
        """
        Returns the geometry element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('geometry')
        if search.isNull():
            search = e.firstChildElement('shape:geometry')
        return search

    @staticmethod
    def getLabelFromElement(e):
        """
        Returns the label element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('label')
        if search.isNull():
            search = e.firstChildElement('shape:label')
        return search

    @staticmethod
    def getPointBesideElement(e):
        """
        Returns the point element beside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.nextSiblingElement('point')
        if search.isNull():
            search = e.nextSiblingElement('line:point')
        return search

    @staticmethod
    def getPointInsideElement(e):
        """
        Returns the point element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('point')
        if search.isNull():
            search = e.firstChildElement('line:point')
        return search

    def itemFromGrapholNode(self, e):
        """
        Returns the item matching the given graphol node.
        :type e: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[e.attribute('type').lower().strip()]
        except KeyError:
            return None

class GrapholOntologyIRILoader_v2(AbstractOntologyLoader, GrapholProjectIRILoaderMixin_2):
    """
    Extends AbstractOntologyLoader with facilities to load ontologies from Graphol file format.
    """

    def __init__(self, path, project, session):
        """
        Initialize the Graphol importer.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(expandPath(path), project, session)

    def projectMerge(self):
        """
        Merge the loaded project with the one currently loaded in Eddy session.
        """
        pass

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform ontology import from Graphol file format and merge the loaded ontology with the current project.
        """
        self.createDomDocument()
        self.createProject()
        self.createDiagrams()

        self.createPredicatesMeta()

        self.projectRender()
        self.projectMerge()


class GrapholIRIProjectLoader_v2(AbstractProjectLoader, GrapholProjectIRILoaderMixin_2):
    """
    Extends AbstractProjectLoader with facilities to load Graphol projects.
    """

    def __init__(self, path, session):
        """
        Initialize the Project loader.
        :type path: str
        :type session: Session
        """
        path = expandPath(path)
        #path = os.path.join(path, os.path.basename(path))
        #path = postfix(path, File.Graphol.extension)
        super().__init__(path, session)

    def createLegacyProject(self):
        """
        Create a Project using the @deprecated Graphol project loader (v1).
        """
        worker = GrapholProjectLoader_v1(os.path.dirname(self.path), self.session)
        worker.run()
        worker = GrapholIRIProjectExporter(self.session.project)
        worker.run()

    def projectLoaded(self):
        """
        Initialize the Session Project to be the loaded one.
        """
        self.session.project = self.nproject

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform project import.
        """
        try:
            self.createDomDocument()

            #############################################
            # LEGACY LOADING CHECK
            #################################

            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Legacy mode')
            msgbox.setText(textwrap.dedent("""
                                You have selected an {EDDY} version <b>2</b> project.<br/>
                                If you continue with the loading procedure the project will be automatically
                                converted to the most recent project version.<br/><br/>
                                Do you want to continue?
                                """.format(EDDY=APPNAME)))
            msgbox.exec_()

            if msgbox.result() == QtWidgets.QMessageBox.No:
                raise ProjectStopLoadingError
        except (ProjectNotFoundError, ProjectVersionError):
            self.createLegacyProject()
        else:
            self.createProject()
            self.createDiagrams()
            self.createPredicatesMeta()
            self.projectRender()
            self.projectLoaded()


class GrapholProjectIRILoaderMixin_3(object):
    """
    Mixin which adds the ability to create a project out of a Graphol file.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)

        self.buffer = dict()
        self.document = None
        self.nproject = None

        self.itemFromXml = {
            'attribute': Item.AttributeNode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptNode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
            'facet': Item.FacetNode,
            'individual': Item.IndividualNode,
            'literal': Item.LiteralNode,
            'intersection': Item.IntersectionNode,
            'property-assertion': Item.PropertyAssertionNode,
            'range-restriction': Item.RangeRestrictionNode,
            'role': Item.RoleNode,
            'role-chain': Item.RoleChainNode,
            'role-inverse': Item.RoleInverseNode,
            'union': Item.UnionNode,
            'value-domain': Item.ValueDomainNode,
            'inclusion': Item.InclusionEdge,
            'equivalence': Item.EquivalenceEdge,
            'input': Item.InputEdge,
            'membership': Item.MembershipEdge,
            'same': Item.SameEdge,
            'different': Item.DifferentEdge,
            'has-key': Item.HasKeyNode
        }

        self.importFuncForItem = {
            Item.AttributeNode: self.importAttributeNode,
            Item.ComplementNode: self.importComplementNode,
            Item.ConceptNode: self.importConceptNode,
            Item.DatatypeRestrictionNode: self.importDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.importDisjointUnionNode,
            Item.DomainRestrictionNode: self.importDomainRestrictionNode,
            Item.EnumerationNode: self.importEnumerationNode,
            Item.FacetNode: self.importFacetNode,
            Item.IndividualNode: self.importIndividualNode,
            Item.LiteralNode: self.importLiteralNode,
            Item.IntersectionNode: self.importIntersectionNode,
            Item.PropertyAssertionNode: self.importPropertyAssertionNode,
            Item.RangeRestrictionNode: self.importRangeRestrictionNode,
            Item.RoleNode: self.importRoleNode,
            Item.RoleChainNode: self.importRoleChainNode,
            Item.RoleInverseNode: self.importRoleInverseNode,
            Item.UnionNode: self.importUnionNode,
            Item.ValueDomainNode: self.importValueDomainNode,
            Item.InclusionEdge: self.importInclusionEdge,
            Item.EquivalenceEdge: self.importEquivalenceEdge,
            Item.InputEdge: self.importInputEdge,
            Item.MembershipEdge: self.importMembershipEdge,
            Item.SameEdge: self.importSameEdge,
            Item.DifferentEdge: self.importDifferentEdge,
            Item.HasKeyNode:self.importHasKeyNode
        }

    #############################################
    #   DOCUMENT (Prefixes,OntologyIRI)
    #################################
    def createDomDocument(self):
        """
        Create the QDomDocument from where to parse Project information.
        """
        if not fexists(self.path):
            raise ProjectNotFoundError('missing project ontology: %s' % self.path)
        self.document = QtXml.QDomDocument()
        if not self.document.setContent(fread(self.path)):
            raise ProjectNotValidError('invalid project ontology supplied: %s' % self.path)
        e = self.document.documentElement()
        version = int(e.attribute('version', '3'))
        if version != 3:
            raise ProjectVersionError('project version mismatch: %s != 3' % version)

    #############################################
    #   PROJECT (Prefixes,OntologyIRI)
    #################################
    def createProject(self):
        """
        Create the Project by reading data from the parsed QDomDocument.
        """
        projectEl = self.document.documentElement().firstChildElement('project')
        projectVersion = projectEl.attribute('version')
        projectName = projectEl.attribute('name')
        ontologyEl = projectEl.firstChildElement('ontology')
        ontologyIri = ontologyEl.attribute('iri')
        ontologyPrefix =  ontologyEl.attribute('prefix',None) if ontologyEl.hasAttribute('prefix') else None
        labelBoolean = False
        if ontologyEl.attribute('addLabelFromSimpleName'):
            labelBoolean = bool(int(ontologyEl.attribute('addLabelFromSimpleName')))
        labelUserInputBoolean = False
        if ontologyEl.attribute('addLabelFromUserInput'):
            labelUserInputBoolean = bool(int(ontologyEl.attribute('addLabelFromUserInput')))

        ontologyLang = ontologyEl.attribute('lang')
        prefixMap = self.getPrefixMap(ontologyEl)
        datatypes = self.getDatatypes(ontologyEl)
        facets = self.getFacets(ontologyEl)
        annotationProperties = self.getAnnotationproperties(ontologyEl)
        languages = self.getLanguages(ontologyEl)
        imports = self.getImports(ontologyEl)
        self.nproject = Project(
            parent=self.session,
            name=projectName,
            path=self.path,
            version=projectVersion,
            profile=self.session.createProfile('OWL 2'),
            prefixMap=prefixMap,
            ontologyIRI=ontologyIri,
            ontologyPrefix=ontologyPrefix,
            annotationProperties=annotationProperties,
            datatypes=datatypes,
            facets=facets,
            imports=imports,
            languages=languages,
            defaultLanguage=ontologyLang,
            addLabelFromSimpleName=labelBoolean,
            addLabelFromUserInput=labelUserInputBoolean,
        )
        LOGGER.info('Loaded ontology: %s...', self.nproject.name)

        irisEl = ontologyEl.firstChildElement('iris')
        iriEl = irisEl.firstChildElement('iri')
        while not iriEl.isNull():
            try:
                self.getIri(iriEl, datatypes,facets,annotationProperties)
            except Exception as e:
                LOGGER.exception('Failed to import iri element [{}]'.format(e))
            finally:
                iriEl = iriEl.nextSiblingElement('iri')



    def getIri(self,iriEl,datatypes,facets,annotationProperties):
        iriString = iriEl.firstChildElement('value').text()
        if not (iriString in datatypes or iriString in facets or iriString in annotationProperties):
            result = self.nproject.getIRI(iriString)
            if not iriEl.firstChildElement('functional').isNull():
                result.functional = True
            if not iriEl.firstChildElement('inverseFunctional').isNull():
                result.inverseFunctional = True
            if not iriEl.firstChildElement('symmetric').isNull():
                result.symmetric = True
            if not iriEl.firstChildElement('asymmetric').isNull():
                result.asymmetric = True
            if not iriEl.firstChildElement('reflexive').isNull():
                result.reflexive = True
            if not iriEl.firstChildElement('irreflexive').isNull():
                result.irreflexive = True
            if not iriEl.firstChildElement('transitive').isNull():
                result.transitive = True
            '''
            result.functional = bool(int(iriEl.firstChildElement('functional').text()))
            result.inverseFunctional = bool(int(iriEl.firstChildElement('inverseFunctional').text()))
            result.symmetric = bool(int(iriEl.firstChildElement('symmetric').text()))
            result.asymmetric = bool(int(iriEl.firstChildElement('asymmetric').text()))
            result.reflexive = bool(int(iriEl.firstChildElement('reflexive').text()))
            result.irreflexive = bool(int(iriEl.firstChildElement('irreflexive').text()))
            result.transitive = bool(int(iriEl.firstChildElement('transitive').text()))
            '''
            annotationsEl = iriEl.firstChildElement('annotations')
            if not annotationsEl.isNull():
                annotationEl = annotationsEl.firstChildElement('annotation')
                while not annotationEl.isNull():
                    try:
                        result.addAnnotationAssertion(self.getAnnotationAssertion(annotationEl))
                    except Exception as e:
                        LOGGER.exception('Failed to import annotation element for iri {} [{}]'.format(iriString,e))
                    finally:
                        annotationEl = annotationEl.nextSiblingElement('annotation')
            return result

    def getAnnotationAssertion(self,annotationEl):
        subjectEl = annotationEl.firstChildElement('subject')
        subject = self.nproject.getIRI(subjectEl.text())
        propertyEl = annotationEl.firstChildElement('property')
        property = self.nproject.getIRI(propertyEl.text())
        value = None
        type = None
        language = None
        objectEl = annotationEl.firstChildElement('object')
        iriObjEl = objectEl.firstChildElement('iri')
        if not iriObjEl.isNull():
            value = self.nproject.getIRI(iriObjEl.text())
        else:
            value = objectEl.firstChildElement('lexicalForm').text()
            datatypeEl = objectEl.firstChildElement('datatype')
            if datatypeEl.text():
                type = self.nproject.getIRI(datatypeEl.text())
            languageEl = objectEl.firstChildElement('language')
            if languageEl.text():
                language = languageEl.text()
        return AnnotationAssertion(subject,property,value,type,language)

    def getAnnotation(self,annotationEl):
        propertyEl = annotationEl.firstChildElement('property')
        property = self.nproject.getIRI(propertyEl.text())
        value = None
        type = None
        language = None
        objectEl = annotationEl.firstChildElement('object')
        iriObjEl = objectEl.firstChildElement('iri')
        if not iriObjEl.isNull():
            value = self.nproject.getIRI(iriObjEl.text())
        else:
            value = objectEl.firstChildElement('lexicalForm').text()
            datatypeEl = objectEl.firstChildElement('datatype')
            if datatypeEl.text():
                type = self.nproject.getIRI(datatypeEl.text())
            languageEl = objectEl.firstChildElement('language')
            if languageEl.text():
                language = languageEl.text()
        return Annotation(property,value,type,language)

    def getPrefixMap(self, ontologyEl):
        prefixMap = dict()
        prefixesEl = ontologyEl.firstChildElement('prefixes')
        prefixEl = prefixesEl.firstChildElement('prefix')
        while not prefixEl.isNull():
            try:
                value = prefixEl.firstChildElement('value').text()
                ns = prefixEl.firstChildElement('namespace').text()
                prefixMap[value] = ns
            except Exception as e:
                LOGGER.exception('Failed to import prefix element ')
            finally:
                prefixEl = prefixEl.nextSiblingElement('prefix')
        return prefixMap

    def getAnnotationproperties(self, ontologyEl):
        result = set()
        annotationPropertiesEl = ontologyEl.firstChildElement('annotationProperties')
        annotationPropertyEl = annotationPropertiesEl.firstChildElement('annotationProperty')
        while not annotationPropertyEl.isNull():
            try:
                iriStr = annotationPropertyEl.text()
                result.add(iriStr)
            except Exception as e:
                LOGGER.exception('Failed to import annotationProperty element ')
            finally:
                annotationPropertyEl = annotationPropertyEl.nextSiblingElement('annotationProperty')
        return result

    def getDatatypes(self, ontologyEl):
        result = set()
        datatypesEl = ontologyEl.firstChildElement('datatypes')
        datatypeEl = datatypesEl.firstChildElement('datatype')
        while not datatypeEl.isNull():
            try:
                iriStr = datatypeEl.text()
                result.add(iriStr)
            except Exception as e:
                LOGGER.exception('Failed to import datatype element ')
            finally:
                datatypeEl = datatypeEl.nextSiblingElement('datatype')
        return result

    def getFacets(self, ontologyEl):
        result = set()
        facetsEls = ontologyEl.firstChildElement('facets')
        facetEl = facetsEls.firstChildElement('facet')
        while not facetEl.isNull():
            try:
                iriStr = facetEl.text()
                result.add(iriStr)
            except Exception as e:
                LOGGER.exception('Failed to import facet element ')
            finally:
                facetEl = facetEl.nextSiblingElement('facet')
        return result

    def getLanguages(self, ontologyEl):
        result = set()
        languagesEl = ontologyEl.firstChildElement('languages')
        languageEl = languagesEl.firstChildElement('language')
        while not languageEl.isNull():
            try:
                lang = languageEl.text()
                result.add(lang)
            except Exception as e:
                LOGGER.exception('Failed to import language element ')
            finally:
                languageEl = languageEl.nextSiblingElement('language')
        return result

    def getImports(self, ontologyEl):
        result = set()
        importsEl = ontologyEl.firstChildElement('imports')
        importEl = importsEl.firstChildElement('import')
        while not importEl.isNull():
            try:
                ontIri = importEl.attribute('iri')
                versionIri = importEl.attribute('version')
                location = importEl.attribute('location')
                isLocal = False
                if importEl.attribute('isLocal'):
                    isLocal = bool(int(importEl.attribute('isLocal')))
                ontImp = ImportedOntology(ontIri, location, versionIri, isLocal, self.nproject)
                result.add(ontImp)
            except Exception as e:
                LOGGER.exception('Failed to import element. {}'.format(str(e)))
            finally:
                importEl = importEl.nextSiblingElement('import')
        return result

    def projectRender(self):
        """
        Render all the elements in the Project ontology.
        """
        for item in self.nproject.items():
            QtWidgets.QApplication.processEvents()
            item.updateEdgeOrNode()

    #############################################
    #   DIAGRAM
    #################################
    def createDiagrams(self):
        """
        Create ontology diagrams by parsing the 'diagrams' section of the QDomDocument.
        """
        counter = 1
        section = self.document.documentElement().firstChildElement('project').firstChildElement('diagrams')
        element = section.firstChildElement('diagram')
        while not element.isNull():
            self.nproject.addDiagram(self.importDiagram(element, counter))
            element = element.nextSiblingElement('diagram')
            counter += 1

    def importDiagram(self, diagramElement, i):
        """
        Create a diagram from the given QDomElement.
        :type e: QDomElement
        :type i: int
        :rtype: Diagram
        """
        QtWidgets.QApplication.processEvents()
        ## PARSE DIAGRAM INFORMATION
        name = diagramElement.attribute('name', 'diagram_{0}'.format(i))
        size = max(int(diagramElement.attribute('width', '10000')), int(diagramElement.attribute('height', '10000')))
        ## CREATE NEW DIAGRAM
        LOGGER.info('Loading diagram: %s', name)
        diagram = Diagram.create(name, size, self.nproject)
        self.buffer[diagram.name] = dict()
        ## LOAD DIAGRAM NODES
        nodeElement = diagramElement.firstChildElement('node')
        while not nodeElement.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(nodeElement)
                func = self.importFuncForItem[item]
                node = func(diagram, nodeElement)
            except Exception as e:
                LOGGER.exception('Failed to create node {}. [{}]'.format(nodeElement.attribute('id'), e))
            else:
                diagram.addItem(node)
                diagram.guid.update(node.id)
                self.buffer[diagram.name][node.id] = node
            finally:
                nodeElement = nodeElement.nextSiblingElement('node')

        ## LOAD DIAGRAM EDGES
        edgeElement = diagramElement.firstChildElement('edge')
        while not edgeElement.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(edgeElement)
                func = self.importFuncForItem[item]
                edge = func(diagram, edgeElement)
            except Exception as e:
                LOGGER.exception('Failed to create edge {}. [{}]'.format(edgeElement.attribute('id'), e))
            else:
                diagram.addItem(edge)
                diagram.guid.update(edge.id)
                self.buffer[diagram.name][edge.id] = edge
            finally:
                edgeElement = edgeElement.nextSiblingElement('edge')
        ## IDENTIFY NEUTRAL NODES
        nodes = [x for x in diagram.items(edges=False) if Identity.Neutral in x.identities()]
        if nodes:
            LOGGER.debug('Running identification algorithm for %s nodes', len(nodes))
            for node in nodes:
                diagram.sgnNodeIdentification.emit(node)
        ## CONFIGURE DIAGRAM SIGNALS
        connect(diagram.sgnItemAdded, self.nproject.doAddItem)
        connect(diagram.sgnItemRemoved, self.nproject.doRemoveItem)
        connect(diagram.selectionChanged, self.session.doUpdateState)
        ## RETURN GENERATED DIAGRAM
        return diagram

    #############################################
    #   NODES
    #################################

    def importAttributeNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.AttributeNode)

    def importRoleNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.RoleNode)

    def importConceptNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.ConceptNode)

    def importIndividualNode(self, diagram, nodeElement):
        labelElement = nodeElement.firstChildElement('label')
        labelText = labelElement.text()
        doubleQuote = '"'
        if doubleQuote in labelText:
            return self.importLiteralNode(diagram, nodeElement)
        return self.getIriPredicateNode(diagram, nodeElement, Item.IndividualNode)

    def importValueDomainNode(self, diagram, nodeElement):
        return self.getIriPredicateNode(diagram, nodeElement, Item.ValueDomainNode)

    def getIriPredicateNode(self, diagram, nodeElement, itemType):
        labelElement = nodeElement.firstChildElement('label')
        iriEl = nodeElement.firstChildElement('iri')
        iri = self.nproject.getIRI(iriEl.text())
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(itemType, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'iri': None
        })
        node.iri = iri
        node.setBrush(QtGui.QBrush(QtGui.QColor(nodeElement.attribute('color', '#fcfcfc'))))
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.setTextPos(
            node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))

        customLabelSize = bool(int(labelElement.attribute('customSize', '0')))
        if customLabelSize:
            node.setFontSize(int(labelElement.attribute('size', '12')))

        #node.doUpdateNodeLabel()
        return node

    def importLiteralNode(self, diagram, nodeElement):
        literalEl = nodeElement.firstChildElement('literal')
        lexicalFormEl = literalEl.firstChildElement('lexicalForm')
        lexicalForm = lexicalFormEl.text()
        datatype = None
        datatypeEl = literalEl.firstChildElement('datatype')
        if datatypeEl.text():
            datatype = self.nproject.getIRI(datatypeEl.text())
        language = None
        languageEl = literalEl.firstChildElement('language')
        if languageEl.text():
            language = self.nproject.getIRI(languageEl.text())
        literal = Literal(lexicalForm, datatype,language)

        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(Item.LiteralNode, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'literal': None
        })
        node.literal = literal
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        labelElement = nodeElement.firstChildElement('label')
        node.setTextPos(
            node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))

        customLabelSize = bool(int(labelElement.attribute('customSize', '0')))
        if customLabelSize:
            node.setFontSize(int(labelElement.attribute('size', '12')))

        #node.doUpdateNodeLabel()
        return node

    def importFacetNode(self, diagram, nodeElement):
        facetEl = nodeElement.firstChildElement('facet')
        constrFacetEl = facetEl.firstChildElement('constrainingFacet')
        constrFacetIRI = self.nproject.getIRI(constrFacetEl.text())
        literalEl = facetEl.firstChildElement('literal')
        lexForm = literalEl.firstChildElement('lexicalForm').text()



        datatypeStr = literalEl.firstChildElement('datatype').text()
        if datatypeStr:
            datatypeIRI = self.nproject.getIRI(datatypeStr)
        else:
            datatypeIRI = OWL2Datatype.PlainLiteral.value

        literal = Literal(lexForm,datatypeIRI)
        facet = Facet(constrFacetIRI, literal)
        geometryElement = nodeElement.firstChildElement('geometry')
        node = diagram.factory.create(Item.FacetNode, **{
            'id': nodeElement.attribute('id'),
            'height': int(geometryElement.attribute('height')),
            'width': int(geometryElement.attribute('width')),
            'facet': facet
        })
        node.setPos(QtCore.QPointF(int(geometryElement.attribute('x')), int(geometryElement.attribute('y'))))
        node.doUpdateNodeLabel()
        labelElement = nodeElement.firstChildElement('label')
        node.setTextPos(
            node.mapFromScene(QtCore.QPointF(int(labelElement.attribute('x')), int(labelElement.attribute('y')))))
        return node

    def importComplementNode(self, diagram, e):
        """
        Build a Complement node using the given QDomElement.
        :type e: QDomElement
        :rtype: ComplementNode
        """
        return self.importGenericNode(diagram, Item.ComplementNode, e)

    def importDatatypeRestrictionNode(self, diagram, e):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.importGenericNode(diagram, Item.DatatypeRestrictionNode, e)

    def importDisjointUnionNode(self, diagram, e):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type e: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.importGenericNode(diagram, Item.DisjointUnionNode, e)

    def importDomainRestrictionNode(self, diagram, e):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DomainRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(diagram, Item.DomainRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importEnumerationNode(self, diagram, e):
        """
        Build an Enumeration node using the given QDomElement.
        :type e: QDomElement
        :rtype: EnumerationNode
        """
        return self.importGenericNode(diagram, Item.EnumerationNode, e)

    def importIntersectionNode(self, diagram, e):
        """
        Build an Intersection node using the given QDomElement.
        :type e: QDomElement
        :rtype: IntersectionNode
        """
        return self.importGenericNode(diagram, Item.IntersectionNode, e)

    def importPropertyAssertionNode(self, diagram, e):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type e: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(diagram, Item.PropertyAssertionNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRangeRestrictionNode(self, diagram, e):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: RangeRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(diagram, Item.RangeRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importRoleChainNode(self, diagram, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleChainNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(diagram, Item.RoleChainNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRoleInverseNode(self, diagram, e):
        """
        Build a RoleInverse node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleInverseNode
        """
        return self.importGenericNode(diagram, Item.RoleInverseNode, e)

    def importUnionNode(self, diagram, e):
        """
        Build a Union node using the given QDomElement.
        :type e: QDomElement
        :rtype: UnionNode
        """
        return self.importGenericNode(diagram, Item.UnionNode, e)

    def importHasKeyNode(self, diagram, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type e: QDomElement
        :rtype: HasKeyNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(diagram, Item.HasKeyNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    #############################################
    #   EDGES
    #################################

    def importEquivalenceEdge(self, d, e):
        """
        Build an Equivalence edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: EquivalenceEdge
        """
        return self.importAxiomEdge(d, Item.EquivalenceEdge, e)

    def importInclusionEdge(self, d, e):
        """
        Build an Inclusion edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: InclusionEdge
        """
        return self.importAxiomEdge(d, Item.InclusionEdge, e)

    def importInputEdge(self, d, e):
        """
        Build an Input edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: InputEdge
        """
        return self.importGenericEdge(d, Item.InputEdge, e)

    def importMembershipEdge(self, d, e):
        """
        Build a Membership edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: MembershipEdge
        """
        return self.importAxiomEdge(d, Item.MembershipEdge, e)

    def importSameEdge(self, d, e):
        """
        Build a Same edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: SameEdge
        """
        return self.importAxiomEdge(d, Item.SameEdge, e)

    def importDifferentEdge(self, d, e):
        """
        Build a Different edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DifferentEdge
        """
        return self.importAxiomEdge(d, Item.DifferentEdge, e)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def itemFromXmlNode(self, e):
        """
        Returns the item matching the given Graphol XML node.
        :type e: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[e.attribute('type').lower().strip()]
        except KeyError:
            return None

    def importGenericEdge(self, d, i, e):
        """
        Build an edge using the given item type and QDomElement.
        :type d: Diagram
        :type i: Item
        :type e: QDomElement
        :rtype: AbstractEdge
        """
        points = []
        point = e.firstChildElement('point')
        while not point.isNull():
            points.append(QtCore.QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = point.nextSiblingElement('point')

        source = self.buffer[d.name][e.attribute('source')]
        target = self.buffer[d.name][e.attribute('target')]
        edge = d.factory.create(i, **{
            'id': e.attribute('id'),
            'source': source,
            'target': target,
            'breakpoints': [p for p in points[1:-1]
                            if not (source.painterPath().contains(source.mapFromScene(p)) or
                                    target.painterPath().contains(target.mapFromScene(p)))]
        })

        path = edge.source.painterPath()
        if path.contains(edge.source.mapFromScene(points[0])):
            edge.source.setAnchor(edge, points[0])

        path = edge.target.painterPath()
        if path.contains(edge.target.mapFromScene(points[-1])):
            edge.target.setAnchor(edge, points[-1])

        edge.source.addEdge(edge)
        edge.target.addEdge(edge)
        return edge

    def importAxiomEdge(self, d, i, e):
        edge = self.importGenericEdge(d,i,e)

        annSetEl = e.firstChildElement('annotations')
        if not annSetEl.isNull():
            annotationEl = annSetEl.firstChildElement('annotation')
            while not annotationEl.isNull():
                try:
                    edge.addAnnotation(self.getAnnotation(annotationEl))
                except Exception as e:
                    LOGGER.exception('Failed to import annotation element for edge {} [{}]'.format(str(edge), e))
                finally:
                    annotationEl = annotationEl.nextSiblingElement('annotation')
        return edge

    def importGenericNode(self, diagram, item, e):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type e: QDomElement
        :rtype: AbstractNode
        """
        labelElement = e.firstChildElement('label')
        geometry = self.getGeometryFromElement(e)
        node = diagram.factory.create(item, **{
            'id': e.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width'))
        })
        node.setPos(QtCore.QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        customLabelSize = bool(int(labelElement.attribute('customSize', '0')))
        if customLabelSize:
            node.setFontSize(int(labelElement.attribute('size', '12')))
        return node

    @staticmethod
    def getEdgeEquivalenceFromElement(e):
        """
        Returns the value of the 'equivalence' attribute from the given element.
        :type e: QDomElement
        :rtype: bool
        """
        if e.hasAttribute('equivalence'):
            return bool(int(e.attribute('equivalence', '0')))
        return bool(int(e.attribute('complete', '0')))

    @staticmethod
    def getGeometryFromElement(e):
        """
        Returns the geometry element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('geometry')
        if search.isNull():
            search = e.firstChildElement('shape:geometry')
        return search

    @staticmethod
    def getLabelFromElement(e):
        """
        Returns the label element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('label')
        if search.isNull():
            search = e.firstChildElement('shape:label')
        return search

    @staticmethod
    def getPointBesideElement(e):
        """
        Returns the point element beside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.nextSiblingElement('point')
        if search.isNull():
            search = e.nextSiblingElement('line:point')
        return search

    @staticmethod
    def getPointInsideElement(e):
        """
        Returns the point element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('point')
        if search.isNull():
            search = e.firstChildElement('line:point')
        return search

    def itemFromGrapholNode(self, e):
        """
        Returns the item matching the given graphol node.
        :type e: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[e.attribute('type').lower().strip()]
        except KeyError:
            return None


class GrapholOntologyIRILoader_v3(AbstractOntologyLoader, GrapholProjectIRILoaderMixin_3):
    """
    Extends AbstractOntologyLoader with facilities to load ontologies from Graphol file format and merge them with current project
    """

    def __init__(self, path, project, session):
        """
        Initialize the Graphol importer.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(expandPath(path), project, session)
        self._owlOntologyImportErrors = set()

    @property
    def owlOntologyImportErrors(self):
        return self._owlOntologyImportErrors

    def projectMerge(self):
        """
        Merge the loaded project with the one currently loaded in Eddy session.
        """
        worker = ProjectIRIMergeWorker_v3(self.project, self.nproject, self.session)
        connect(worker.sgnErrorManagingOWLOntologyImport, self.onImportError)
        worker.run()
        disconnect(worker.sgnErrorManagingOWLOntologyImport, self.onImportError)

    @QtCore.pyqtSlot(str, Exception)
    def onImportError(self, location, exc):
        self._owlOntologyImportErrors.update([(location,str(exc))])

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform ontology import from Graphol file format and merge the loaded ontology with the current project.
        """
        self.createDomDocument()
        self.createProject()
        self.createDiagrams()
        self.projectRender()
        self.projectMerge()


class GrapholIRIProjectLoader_v3(AbstractProjectLoader, GrapholProjectIRILoaderMixin_3):
    """
    Extends AbstractProjectLoader with facilities to load Graphol projects.
    """

    def __init__(self, path, session):
        """
        Initialize the Project loader.
        :type path: str
        :type session: Session
        """
        path = expandPath(path)
        #path = os.path.join(path, os.path.basename(path))
        #path = postfix(path, File.Graphol.extension)
        super().__init__(path, session)

    def createLegacyProject(self):
        """
        Create a Project using the @deprecated Graphol project loader (v2).
        """
        worker = GrapholIRIProjectLoader_v2(self.path, self.session)
        worker.run()
        worker = GrapholIRIProjectExporter(self.session.project)
        worker.run()

    def projectLoaded(self):
        """
        Initialize the Session Project to be the loaded one.
        """
        self.session.project = self.nproject

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform project import.
        """
        try:
            self.createDomDocument()
        except (ProjectNotFoundError, ProjectVersionError):
            self.createLegacyProject()
        else:
            self.createProject()
            self.createDiagrams()
            self.projectRender()
            self.projectLoaded()


class ProjectIRIMergeWorker_v3(QtCore.QObject):
    """
    Extends QObject with facilities to merge the content of 2 distinct projects.
    """

    sgnErrorManagingOWLOntologyImport = QtCore.pyqtSignal(str, Exception)

    def __init__(self, project, other, session):
        """
        Initialize the project merge worker.
        :type project: Project
        :type other: Project
        :type session: Session
        """
        super().__init__(session)
        self.commands = list()
        self.project = project
        self.other = other

        self.selected_diagrams = None
        self.all_names_in_selected_diagrams = []

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session (alias for ProjectMergeWorker.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################
    def run(self):
        """
        Perform the merge of the 2 projects.
        """
        try:
            LOGGER.info('Performing project import: %s <- %s...', self.project.name, self.other.name)
            self.mergeDiagrams()
            self.importPrefixesTypesAndAnnotations()
            self.importImportedOntologies()
        except ProjectStopImportingError as e:
            LOGGER.exception('Fatal error during project merge: {}'.format(str(e)))
        else:
            self.mergeFinished()

    def importPrefixesTypesAndAnnotations(self):
        for prefix,ns in self.other.prefixDictItems():
            if not prefix in self.project.getManagedPrefixes():
                self.commands.append(CommandProjectAddPrefix(self.project,prefix,ns))
                #self.project.setPrefix(prefix, ns)
        '''
        for datatypeIRI in self.other.getDatatypeIRIs():
            self.project.addDatatype(str(datatypeIRI))
        '''

        for annPropIRI in self.other.getAnnotationPropertyIRIs():
            self.commands.append(CommandProjectAddAnnotationProperty(self.project, str(annPropIRI)))
            #self.project.addAnnotationProperty(str(annPropIRI))

    def importImportedOntologies(self):
        alreadyLoadedOntIRIs = [str(x.ontologyIRI) for x in self.project.importedOntologies]
        for otherImpOnt in self.other.importedOntologies:
            if not str(otherImpOnt.ontologyIRI) in alreadyLoadedOntIRIs:
                self.currImpOnt = ImportedOntology(otherImpOnt.ontologyIRI, otherImpOnt.docLocation, otherImpOnt.versionIRI, otherImpOnt.isLocalDocument, self.project)
                self.worker = OwlOntologyImportWorker(self.currImpOnt.docLocation, self.session, isLocalImport=self.currImpOnt.isLocalDocument)
                connect(self.worker.sgnCompleted, self.onImportCompleted)
                connect(self.worker.sgnErrored, self.onImportError)
                connect(self.worker.sgnClassFetched, self.onClassFetched)
                connect(self.worker.sgnObjectPropertyFetched, self.onObjectPropertyFetched)
                connect(self.worker.sgnDataPropertyFetched, self.onDataPropertyFetched)
                connect(self.worker.sgnIndividualFetched, self.onIndividualFetched)
                self.worker.run()

    @QtCore.pyqtSlot(str)
    def onClassFetched(self, iri):
        self.currImpOnt.addClass(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot(str)
    def onObjectPropertyFetched(self, iri):
        self.currImpOnt.addObjectProperty(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot(str)
    def onDataPropertyFetched(self, iri):
        self.currImpOnt.addDataProperty(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot(str)
    def onIndividualFetched(self, iri):
        self.currImpOnt.addIndividual(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot()
    def onImportCompleted(self):
        command = CommandProjectAddOntologyImport(self.project, self.currImpOnt)
        self.commands.append(command)
        disconnect(self.worker.sgnCompleted, self.onImportCompleted)
        disconnect(self.worker.sgnErrored, self.onImportError)
        disconnect(self.worker.sgnClassFetched, self.onClassFetched)
        disconnect(self.worker.sgnObjectPropertyFetched, self.onObjectPropertyFetched)
        disconnect(self.worker.sgnDataPropertyFetched, self.onDataPropertyFetched)
        disconnect(self.worker.sgnIndividualFetched, self.onIndividualFetched)
        self.currImpOnt = None
        self.worker = None

    @QtCore.pyqtSlot(str, Exception)
    def onImportError(self, location, exc):
        LOGGER.exception('OWL 2 import located in {} could not be completed during merge. Error: {}'.format(location,str(exc)))
        command = CommandProjectAddOntologyImport(self.project, self.currImpOnt)
        self.commands.append(command)
        self.currImpOnt = None
        disconnect(self.worker.sgnCompleted, self.onImportCompleted)
        disconnect(self.worker.sgnErrored, self.onImportError)
        disconnect(self.worker.sgnClassFetched, self.onClassFetched)
        disconnect(self.worker.sgnObjectPropertyFetched, self.onObjectPropertyFetched)
        disconnect(self.worker.sgnDataPropertyFetched, self.onDataPropertyFetched)
        disconnect(self.worker.sgnIndividualFetched, self.onIndividualFetched)
        self.sgnErrorManagingOWLOntologyImport.emit(location, exc)

    def mergeDiagrams(self):
        """
        Perform the merge of the diagrams by importing all the diagrams in the 'other' project in the loaded one.
        """
        try:
            diagrams_selection_dialog = DiagramSelectionDialog(self.session, project=self.other)
            diagrams_selection_dialog.exec_()
            self.selected_diagrams = diagrams_selection_dialog.selectedDiagrams()
        except Exception as e:
            print(e)

        alreadyAdded = set()
        alreadyAddedDiagram = set()
        for diagram in self.selected_diagrams:
            self.replaceIRIs(diagram,alreadyAdded)
            # We may be in the situation in which we are importing a diagram with name 'X'
            # even though we already have a diagram 'X' in our project. Because we do not
            # want to overwrite diagrams, we perform a rename of the diagram being imported,
            # to be sure to have a unique diagram name, in the current project namespace.
            occurrence = 1
            name = diagram.name
            while self.project.diagram(diagram.name) or diagram.name in alreadyAddedDiagram:
                diagram.name = '{0}_{1}'.format(name, occurrence)
                occurrence += 1
            ## SWITCH SIGNAL SLOTS
            disconnect(diagram.sgnItemAdded, self.other.doAddItem)
            disconnect(diagram.sgnItemRemoved, self.other.doRemoveItem)
            connect(diagram.sgnItemAdded, self.project.doAddItem)
            connect(diagram.sgnItemRemoved, self.project.doRemoveItem)
            ## MERGE THE DIAGRAM IN THE CURRENT PROJECT
            self.commands.append(CommandDiagramAdd(diagram, self.project))
            alreadyAddedDiagram.add(diagram.name)

    def replaceIRIs(self,diagram,alreadyAdded):
        for node in diagram.nodes():
            if isinstance(node, PredicateNodeMixin):
                otherIRI = node.iri
                projIRI = None
                if not str(otherIRI) in alreadyAdded and self.project.existIRI(str(otherIRI)):
                    LOGGER.warning('The IRI <{}> occurs in both projects...'.format(str(otherIRI)))
                    #TODO Gestisci possibili incongruenze: funct, asymm, annotation assertions, etc, etc,...
                    projIRI = self.project.getIRI(str(otherIRI))
                elif str(otherIRI) in alreadyAdded:
                    projIRI = self.project.getIRI(str(otherIRI))
                else:
                    projIRI = self.project.getIRI(str(otherIRI))
                    projIRI.functional = otherIRI.functional
                    projIRI.inverseFunctional = otherIRI.inverseFunctional
                    projIRI.asymmetric = otherIRI.asymmetric
                    projIRI.symmetric = otherIRI.symmetric
                    projIRI.reflexive = otherIRI.reflexive
                    projIRI.irreflexive = otherIRI.irreflexive
                    projIRI.transitive = otherIRI.transitive
                    for annAss in otherIRI.annotationAssertions:
                        newAss = AnnotationAssertion(projIRI,annAss.assertionProperty, annAss.value, annAss.datatype, annAss.language)
                        projIRI.addAnnotationAssertion(newAss)
                    alreadyAdded.add(str(otherIRI))
                node.iri = projIRI

    def mergeFinished(self):
        """
        Completes the merge by executing the commands in the buffer on the undostack.
        """
        if self.commands:
            self.session.undostack.beginMacro(
                'import project "{0}" into "{1}"'.format(self.other.name, self.project.name))
            for command in self.commands:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()



