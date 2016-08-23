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

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.exceptions import ProjectNotFoundError
from eddy.core.exceptions import ProjectNotValidError
from eddy.core.exceptions import DiagramNotFoundError
from eddy.core.exceptions import DiagramNotValidError
from eddy.core.functions.fsystem import fread, fexists, is_dir
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.loaders.common import AbstractDiagramLoader
from eddy.core.loaders.common import AbstractProjectLoader
from eddy.core.output import getLogger
from eddy.core.project import Project


LOGGER = getLogger(__name__)


class GrapholDiagramLoader(AbstractDiagramLoader):
    """
    Extends AbstractDiagramLoader with facilities to load diagrams from Graphol file format.
    """
    GrapholVersion = 1

    def __init__(self, path, project, session):
        """
        Initialize the Graphol diagram loader.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super(GrapholDiagramLoader, self).__init__(path, project, session)

        self.diagram = None
        self.edges = dict()
        self.nodes = dict()

        self.importFuncForItem = {
            Item.AttributeNode: self.buildAttributeNode,
            Item.ComplementNode: self.buildComplementNode,
            Item.ConceptNode: self.buildConceptNode,
            Item.DatatypeRestrictionNode: self.buildDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.buildDisjointUnionNode,
            Item.DomainRestrictionNode: self.buildDomainRestrictionNode,
            Item.EnumerationNode: self.buildEnumerationNode,
            Item.FacetNode: self.buildFacetNode,
            Item.IndividualNode: self.buildIndividualNode,
            Item.IntersectionNode: self.buildIntersectionNode,
            Item.PropertyAssertionNode: self.buildPropertyAssertionNode,
            Item.RangeRestrictionNode: self.buildRangeRestrictionNode,
            Item.RoleNode: self.buildRoleNode,
            Item.RoleChainNode: self.buildRoleChainNode,
            Item.RoleInverseNode: self.buildRoleInverseNode,
            Item.UnionNode: self.buildUnionNode,
            Item.ValueDomainNode: self.buildValueDomainNode,
            Item.InclusionEdge: self.buildInclusionEdge,
            Item.InputEdge: self.buildInputEdge,
            Item.MembershipEdge: self.buildMembershipEdge,
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
            'input': Item.InputEdge,
            'instance-of': Item.MembershipEdge,
            'membership': Item.MembershipEdge,
        }

    #############################################
    #   NODES
    #################################

    def buildAttributeNode(self, element):
        """
        Build an Attribute node using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeNode
        """
        label = self.getLabelFromElement(element)
        node = self.buildGenericNode(Item.AttributeNode, element)
        node.setBrush(QBrush(QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def buildComplementNode(self, element):
        """
        Build a Complement node using the given QDomElement.
        :type element: QDomElement
        :rtype: ComplementNode
        """
        return self.buildGenericNode(Item.ComplementNode, element)

    def buildConceptNode(self, element):
        """
        Build a Concept node using the given QDomElement.
        :type element: QDomElement
        :rtype: ConceptNode
        """
        label = self.getLabelFromElement(element)
        node = self.buildGenericNode(Item.ConceptNode, element)
        node.setBrush(QBrush(QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def buildDatatypeRestrictionNode(self, element):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.buildGenericNode(Item.DatatypeRestrictionNode, element)

    def buildDisjointUnionNode(self, element):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type element: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.buildGenericNode(Item.DisjointUnionNode, element)

    def buildDomainRestrictionNode(self, element):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: DomainRestrictionNode
        """
        label = self.getLabelFromElement(element)
        node = self.buildGenericNode(Item.DomainRestrictionNode, element)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def buildEnumerationNode(self, element):
        """
        Build an Enumeration node using the given QDomElement.
        :type element: QDomElement
        :rtype: EnumerationNode
        """
        return self.buildGenericNode(Item.EnumerationNode, element)

    def buildFacetNode(self, element):
        """
        Build a FacetNode node using the given QDomElement.
        :type element: QDomElement
        :rtype: FacetNode
        """
        label = self.getLabelFromElement(element)
        node = self.buildGenericNode(Item.FacetNode, element)
        node.setText(label.text())
        return node

    def buildIndividualNode(self, element):
        """
        Build an Individual node using the given QDomElement.
        :type element: QDomElement
        :rtype: IndividualNode
        """
        label = self.getLabelFromElement(element)
        node = self.buildGenericNode(Item.IndividualNode, element)
        node.setBrush(QBrush(QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def buildIntersectionNode(self, element):
        """
        Build an Intersection node using the given QDomElement.
        :type element: QDomElement
        :rtype: IntersectionNode
        """
        return self.buildGenericNode(Item.IntersectionNode, element)

    def buildPropertyAssertionNode(self, element):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type element: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = element.attribute('inputs', '').strip()
        node = self.buildGenericNode(Item.PropertyAssertionNode, element)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def buildRangeRestrictionNode(self, element):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: RangeRestrictionNode
        """
        label = self.getLabelFromElement(element)
        node = self.buildGenericNode(Item.RangeRestrictionNode, element)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def buildRoleNode(self, element):
        """
        Build a Role node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleNode
        """
        label = self.getLabelFromElement(element)
        node = self.buildGenericNode(Item.RoleNode, element)
        node.setBrush(QBrush(QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def buildRoleChainNode(self, element):
        """
        Build a RoleChain node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleChainNode
        """
        inputs = element.attribute('inputs', '').strip()
        node = self.buildGenericNode(Item.RoleChainNode, element)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def buildRoleInverseNode(self, element):
        """
        Build a RoleInverse node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleInverseNode
        """
        return self.buildGenericNode(Item.RoleInverseNode, element)

    def buildValueDomainNode(self, element):
        """
        Build a Value-Domain node using the given QDomElement.
        :type element: QDomElement
        :rtype: ValueDomainNode
        """
        label = self.getLabelFromElement(element)
        node = self.buildGenericNode(Item.ValueDomainNode, element)
        node.setBrush(QBrush(QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def buildUnionNode(self, element):
        """
        Build a Union node using the given QDomElement.
        :type element: QDomElement
        :rtype: UnionNode
        """
        return self.buildGenericNode(Item.UnionNode, element)

    #############################################
    #   EDGES
    #################################

    def buildInclusionEdge(self, element):
        """
        Build an Inclusion edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InclusionEdge
        """
        edge = self.buildGenericEdge(Item.InclusionEdge, element)
        edge.equivalence = self.getEdgeEquivalenceFromElement(element)
        return edge

    def buildInputEdge(self, element):
        """
        Build an Input edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InputEdge
        """
        return self.buildGenericEdge(Item.InputEdge, element)

    def buildMembershipEdge(self, element):
        """
        Build a Membership edge using the given QDomElement.
        :type element: QDomElement
        :rtype: MembershipEdge
        """
        return self.buildGenericEdge(Item.MembershipEdge, element)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def buildGenericEdge(self, item, element):
        """
        Build an edge using the given item type and QDomElement.
        :type item: Item
        :type element: QDomElement
        :rtype: AbstractEdge
        """
        points = []
        point = self.getPointInsideElement(element)
        while not point.isNull():
            points.append(QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = self.getPointBesideElement(point)

        edge = self.diagram.factory.create(item, **{
            'id': element.attribute('id'),
            'source': self.nodes[element.attribute('source')],
            'target': self.nodes[element.attribute('target')],
            'breakpoints': points[1:-1]
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

    def buildGenericNode(self, item, element):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type element: QDomElement
        :rtype: AbstractNode
        """
        geometry = self.getGeometryFromElement(element)
        node = self.diagram.factory.create(item, **{
            'id': element.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width'))
        })

        node.setPos(QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        return node

    @staticmethod
    def getEdgeEquivalenceFromElement(element):
        """
        Returns the value of the 'equivalence' attribute from the given element.
        :type element: QDomElement
        :rtype: bool
        """
        if element.hasAttribute('equivalence'):
            return bool(int(element.attribute('equivalence', '0')))
        return bool(int(element.attribute('complete', '0')))

    @staticmethod
    def getGeometryFromElement(element):
        """
        Returns the geometry element inside the given one.
        :type element: QDomElement
        :rtype: QDomElement
        """
        search = element.firstChildElement('geometry')
        if search.isNull():
            search = element.firstChildElement('shape:geometry')
        return search

    @staticmethod
    def getLabelFromElement(element):
        """
        Returns the label element inside the given one.
        :type element: QDomElement
        :rtype: QDomElement
        """
        search = element.firstChildElement('label')
        if search.isNull():
            search = element.firstChildElement('shape:label')
        return search

    @staticmethod
    def getPointBesideElement(element):
        """
        Returns the point element beside the given one.
        :type element: QDomElement
        :rtype: QDomElement
        """
        search = element.nextSiblingElement('point')
        if search.isNull():
            search = element.nextSiblingElement('line:point')
        return search

    @staticmethod
    def getPointInsideElement(element):
        """
        Returns the point element inside the given one.
        :type element: QDomElement
        :rtype: QDomElement
        """
        search = element.firstChildElement('point')
        if search.isNull():
            search = element.firstChildElement('line:point')
        return search

    def itemFromGrapholNode(self, element):
        """
        Returns the item matching the given graphol node.
        :type element: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[element.attribute('type').lower().strip()]
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

    def load(self):
        """
        Perform diagram import from Graphol file format.
        :raise DiagramNotFoundError: If the given path does not identify a Graphol module.
        :raise DiagramNotValidError: If the given path identifies an invalid Graphol module.
        :rtype: Diagram
        """
        LOGGER.info('Loading diagram: %s', self.path)

        if not fexists(self.path):
            raise DiagramNotFoundError('diagram not found: {0}'.format(self.path))

        document = QDomDocument()
        if not document.setContent(fread(self.path)):
            raise DiagramNotValidError('could not parse diagram from {0}'.format(self.path))

        root = document.documentElement()
        graph = root.firstChildElement('graph')
        size = max(int(graph.attribute('width', '10000')), int(graph.attribute('height', '10000')))

        #############################################
        # CREATE AN EMPTY DIAGRAM
        #################################

        self.diagram = Diagram(self.path, self.project)
        self.diagram.setSceneRect(QRectF(-size / 2, -size / 2, size, size))
        self.diagram.setItemIndexMethod(Diagram.NoIndex)

        LOGGER.debug('Initialzing empty diagram with size: %s', size)

        #############################################
        # LOAD NODES
        #################################

        element = graph.firstChildElement('node')
        while not element.isNull():

            QApplication.processEvents()

            try:
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

            QApplication.processEvents()

            try:
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

        nodes = [n for n in self.nodes.values() if Identity.Neutral in n.Identities]
        if nodes:
            LOGGER.debug('Running identification algorithm for %s nodes', len(nodes))
            for node in nodes:
                self.diagram.identify(node)

        #############################################
        # CONFIGURE DIAGRAM SIGNALS
        #################################

        connect(self.diagram.sgnItemAdded, self.project.doAddItem)
        connect(self.diagram.sgnItemRemoved, self.project.doRemoveItem)
        connect(self.diagram.selectionChanged, self.session.doUpdateState)

        LOGGER.debug('Diagram created: %s', self.diagram.name)

        return self.diagram


class GrapholProjectLoader(AbstractProjectLoader):
    """
    Extends AbstractProjectLoader with facilities to load Graphol projects.
    This class can be used to load projects.

    A graphol project is stored within a directory whose structure is the following:

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
        self.projectHomePath = os.path.join(self.projectMainPath, Project.Home)
        self.projectMetaDataPath = os.path.join(self.projectHomePath, Project.MetaXML)
        self.projectModulesDataPath = os.path.join(self.projectHomePath, Project.ModulesXML)

        self.metaFuncForItem = {
            Item.AttributeNode: self.buildAttributeMetadata,
            Item.ConceptNode: self.buildPredicateMetadata,
            Item.RoleNode: self.buildRoleMetadata,
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

    def buildAttributeMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeMetaData
        """
        meta = self.buildPredicateMetadata(element)
        functional = element.firstChildElement('functional')
        meta.functional = bool(int(functional.text()))
        return meta

    def buildPredicateMetadata(self, element):
        """
        Build predicate metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: PredicateMetaData
        """
        item = self.itemFromXml[element.attribute('type')]
        name = element.attribute('name')
        description = element.firstChildElement('description')
        url = element.firstChildElement('url')
        meta = self.project.meta(item, name)
        meta.description = description.text()
        meta.url = url.text()
        return meta

    def buildRoleMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeMetaData
        """
        meta = self.buildPredicateMetadata(element)
        functional = element.firstChildElement('functional')
        inverseFunctional = element.firstChildElement('inverseFunctional')
        asymmetric = element.firstChildElement('asymmetric')
        irreflexive = element.firstChildElement('irreflexive')
        reflexive = element.firstChildElement('reflexive')
        symmetric = element.firstChildElement('symmetric')
        transitive = element.firstChildElement('transitive')
        meta.functional = bool(int(functional.text()))
        meta.inverseFunctional = bool(int(inverseFunctional.text()))
        meta.asymmetric = bool(int(asymmetric.text()))
        meta.irreflexive = bool(int(irreflexive.text()))
        meta.reflexive = bool(int(reflexive.text()))
        meta.symmetric = bool(int(symmetric.text()))
        meta.transitive = bool(int(transitive.text()))
        return meta

    #############################################
    #   IMPORT PROJECT FROM XML
    #################################

    def importProjectFromXML(self):
        """
        Initialize the project instance by reading project metadata from XML file.
        :raise ProjectNotValidError: If the project metadata file is missing or not readable.
        """
        QApplication.processEvents()

        LOGGER.info('Loading project metadata from %s', self.projectMetaDataPath)

        if not fexists(self.projectMetaDataPath):
            raise ProjectNotValidError('missing project metadata: {0}'.format(self.projectMetaDataPath))

        self.metaDocument = QDomDocument()
        if not self.metaDocument.setContent(fread(self.projectMetaDataPath)):
            raise ProjectNotValidError('could read project metadata from {0}'.format(self.projectMetaDataPath))

        path = self.projectMainPath
        root = self.metaDocument.documentElement()
        ontology = root.firstChildElement('ontology')
        prefix = ontology.firstChildElement('prefix').text()
        iri = ontology.firstChildElement('iri').text()

        LOGGER.debug('Loaded ontology prefix: %s', prefix)
        LOGGER.debug('Loaded ontology IRI: %s', iri)

        self.project = Project(path, prefix, iri, self.session)

    def importMetaFromXML(self):
        """
        Import predicate metadata from XML file.
        """
        QApplication.processEvents()

        #############################################
        # LOAD PREDICATE METADATA
        #################################

        LOGGER.info('Loading ontology predicate metadata from %s', self.projectMetaDataPath)

        root = self.metaDocument.documentElement()
        predicates = root.firstChildElement('predicates')

        predicate = predicates.firstChildElement('predicate')
        while not predicate.isNull():

            QApplication.processEvents()

            try:
                item = self.itemFromXml[predicate.attribute('type')]
                func = self.metaFuncForItem[item]
                meta = func(predicate)
                self.project.addMeta(meta.item, meta.predicate, meta)
            except Exception:
                LOGGER.exception('Failed to create metadata for predicate %s', predicate)
                pass
            finally:
                predicate = predicate.nextSiblingElement('predicate')

        #############################################
        # UPDATE LAYOUT ACCORDING TO METADATA
        #################################

        predicates = self.project.predicates()
        LOGGER.info('Refreshing state for %s predicate nodes', len(predicates))
        for node in predicates:
            node.updateNode()
            node.redraw()

    def importModulesFromXML(self):
        """
        Import project modules from XML file.
        :raise ProjectNotValidError: If the project structure file is missing or not readable.
        """
        QApplication.processEvents()

        LOGGER.info('Loading project structure from %s', self.projectModulesDataPath)

        if not fexists(self.projectModulesDataPath):
            raise ProjectNotValidError('missing project structure: {0}'.format(self.projectModulesDataPath))

        self.modulesDocument = QDomDocument()
        if not self.modulesDocument.setContent(fread(self.projectModulesDataPath)):
            raise ProjectNotValidError('could read project structure from {0}'.format(self.projectModulesDataPath))

        root = self.modulesDocument.documentElement()
        modules = root.firstChildElement('modules')

        module = modules.firstChildElement('module')
        while not module.isNull():

            QApplication.processEvents()

            name = module.text()
            path = os.path.join(self.project.path, name)

            try:
                loader = GrapholDiagramLoader(path, self.project, self.session)
            except (DiagramNotFoundError, DiagramNotValidError) as e:
                LOGGER.warning('Failed to load project module %s: %s', name, e)
            except Exception:
                LOGGER.exception('Failed to load project module %s', name)
            else:
                self.project.addDiagram(loader.load())
            finally:
                module = module.nextSiblingElement('module')

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

    def load(self):
        """
        Perform project import.
        :raise ProjectNotFoundError: If the given path does not identify a project.
        :raise ProjectNotValidError: If one of the project data file is missing or not readable.
        :rtype: Project
        """
        LOGGER.header('Loading project: %s', os.path.basename(self.projectMainPath))

        #############################################
        # VALIDATE PROJECT
        #################################

        if not is_dir(self.projectMainPath):
            raise ProjectNotFoundError('project not found: {0}'.format(self.projectMainPath))

        if not is_dir(self.projectHomePath):
            raise ProjectNotValidError('missing project home: {0}'.format(self.projectHomePath))

        #############################################
        # IMPORT PROJECT
        #################################

        self.importProjectFromXML()
        self.importModulesFromXML()
        self.importMetaFromXML()

        LOGGER.separator('-')

        return self.project