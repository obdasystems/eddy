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
import textwrap

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtXml

from eddy import APPNAME
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.diagram import DiagramNotFoundError
from eddy.core.diagram import DiagramNotValidError
from eddy.core.exporters.graphol import GrapholProjectExporter
from eddy.core.functions.fsystem import fread, fexists, isdir, rmdir
from eddy.core.functions.misc import rstrip, postfix
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.loaders.common import AbstractDiagramLoader
from eddy.core.loaders.common import AbstractProjectLoader
from eddy.core.output import getLogger
from eddy.core.project import Project
from eddy.core.project import ProjectNotFoundError
from eddy.core.project import ProjectNotValidError
from eddy.core.project import ProjectVersionError
from eddy.core.project import ProjectStopLoadingError


LOGGER = getLogger(__name__)


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
            Item.EquivalenceEdge: self.buildEquivalenceEdge,
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
            'equivalence': Item.EquivalenceEdge,
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
        node.setBrush(QtGui.QBrush(QtGui.QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
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
        node.setBrush(QtGui.QBrush(QtGui.QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
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
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
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
        node.setBrush(QtGui.QBrush(QtGui.QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
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
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def buildRoleNode(self, element):
        """
        Build a Role node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleNode
        """
        label = self.getLabelFromElement(element)
        node = self.buildGenericNode(Item.RoleNode, element)
        node.setBrush(QtGui.QBrush(QtGui.QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
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
        node.setBrush(QtGui.QBrush(QtGui.QColor(element.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
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

    def buildEquivalenceEdge(self, element):
        """
        Build an Equivalence edge using the given QDomElement.
        :type element: QDomElement
        :rtype: EquivalenceEdge
        """
        return self.buildGenericEdge(Item.EquivalenceEdge, element)

    def buildInclusionEdge(self, element):
        """
        Build an Inclusion edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InclusionEdge
        """
        if self.getEdgeEquivalenceFromElement(element):
            return self.buildEquivalenceEdge(element)
        return self.buildGenericEdge(Item.InclusionEdge, element)

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
            points.append(QtCore.QPointF(int(point.attribute('x')), int(point.attribute('y'))))
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

        node.setPos(QtCore.QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
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
        Perform diagram import from Graphol file format and add it to the project.
        :raise DiagramNotFoundError: If the given path does not identify a Graphol module.
        :raise DiagramNotValidError: If the given path identifies an invalid Graphol module.
        :rtype: Diagram
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

            QtWidgets.QApplication.processEvents()

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

            QtWidgets.QApplication.processEvents()

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

        #############################################
        # NOTIFY THAT THE DIAGRAM HAS BEEN LOADED
        #################################

        self.session.sgnDiagramLoaded.emit(self.diagram)

        return self.diagram


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
        :rtype: dict
        """
        meta = self.buildPredicateMetadata(element)
        meta['functional'] = bool(int(element.firstChildElement('functional').text()))
        return meta

    def buildPredicateMetadata(self, element):
        """
        Build predicate metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: PredicateMetaData
        """
        item = self.itemFromXml[element.attribute('type')]
        name = element.attribute('name')
        meta = self.project.meta(item, name)
        meta['description'] = element.firstChildElement('description').text()
        meta['url'] = element.firstChildElement('url').text()
        return meta

    def buildRoleMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: dict
        """
        meta = self.buildPredicateMetadata(element)
        meta['functional'] = bool(int( element.firstChildElement('functional').text()))
        meta['inverseFunctional'] = bool(int(element.firstChildElement('inverseFunctional').text()))
        meta['asymmetric'] = bool(int(element.firstChildElement('asymmetric').text()))
        meta['irreflexive'] = bool(int(element.firstChildElement('irreflexive').text()))
        meta['reflexive'] = bool(int(element.firstChildElement('reflexive').text()))
        meta['symmetric'] = bool(int(element.firstChildElement('symmetric').text()))
        meta['transitive'] = bool(int(element.firstChildElement('transitive').text()))
        return meta

    #############################################
    #   IMPORT PROJECT FROM XML
    #################################

    def importProjectFromXML(self):
        """
        Initialize the project instance by reading project metadata from XML file.
        :raise ProjectNotValidError: If the project metadata file is missing or not readable.
        """
        QtWidgets.QApplication.processEvents()

        LOGGER.info('Loading project metadata from %s', self.projectMetaDataPath)

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
        self.project = Project(path, prefix, iri, profile, self.session)

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
                meta = func(predicate)
                self.project.setMeta(item, predicate.attribute('name'), meta)
            except Exception:
                LOGGER.exception('Failed to create metadata for predicate %s', predicate.attribute('name'))
            finally:
                predicate = predicate.nextSiblingElement('predicate')

        #############################################
        # UPDATE LAYOUT ACCORDING TO METADATA
        #################################

        predicates = self.project.predicates()
        LOGGER.info('Refreshing state for %s predicate nodes', len(predicates))
        for node in predicates:
            node.updateNode()

    def importModulesFromXML(self):
        """
        Import project modules from XML file.
        :raise ProjectNotValidError: If the project structure file is missing or not readable.
        """
        QtWidgets.QApplication.processEvents()

        LOGGER.info('Loading project structure from %s', self.projectModulesDataPath)

        if not fexists(self.projectModulesDataPath):
            raise ProjectNotValidError('missing project structure: {0}'.format(self.projectModulesDataPath))

        self.modulesDocument = QtXml.QDomDocument()
        if not self.modulesDocument.setContent(fread(self.projectModulesDataPath)):
            raise ProjectNotValidError('could read project structure from {0}'.format(self.projectModulesDataPath))

        root = self.modulesDocument.documentElement()
        modules = root.firstChildElement('modules')
        module = modules.firstChildElement('module')
        while not module.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                name = module.text()
                path = os.path.join(self.project.path, name)
                loader = GrapholDiagramLoader_v1(path, self.project, self.session)
                loader.load()
            except (DiagramNotFoundError, DiagramNotValidError) as e:
                LOGGER.warning('Failed to load project diagram %s: %s', name, e)
            except Exception:
                LOGGER.exception('Failed to load diagram module %s', name)
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
        Perform project import (LEGACY MODE).
        :raise ProjectNotFoundError: If the given path does not identify a project.
        :raise ProjectNotValidError: If one of the project data file is missing or not readable.
        :raise ProjectStopLoadingError: If the use decides not to load the project.
        :rtype: Project
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

        LOGGER.header('Loading project: %s (LEGACY MODE)', os.path.basename(self.projectMainPath))

        self.importProjectFromXML()
        self.importModulesFromXML()
        self.importMetaFromXML()

        #############################################
        # CLEANUP PROJECT DIRECTORY
        #################################

        rmdir(self.projectMainPath)

        LOGGER.separator('-')

        return self.project


class GrapholProjectLoader_v2(AbstractProjectLoader):
    """
    Extends AbstractProjectLoader with facilities to load Graphol projects.
    A Graphol project is stored in a directory, whose structure is the following:
    -----------------------
    - projectname/
    -   projectname.graphol     # contains information on the ontology
    -   ...
    """
    def __init__(self, path, session):
        """
        Initialize the Project loader.
        :type path: str
        :type session: Session
        """
        super().__init__(path, session)

        self.path = expandPath(path)
        self.project = None
        self.document = None
        self.buffer = dict()

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
        }

        self.importMetaFuncForItem = {
            Item.AttributeNode: self.buildAttributeMeta,
            Item.ConceptNode: self.buildPredicateMeta,
            Item.RoleNode: self.buildRoleMeta,
        }

    #############################################
    #   ONTOLOGY PREDICATES IMPORT
    #################################

    def buildAttributeMeta(self, e):
        """
        Build role metadata using the given QDomElement.
        :type e: QDomElement
        :rtype: dict
        """
        meta = self.buildPredicateMeta(e)
        meta['functional'] = bool(int(e.firstChildElement('functional').text()))
        return meta

    def buildPredicateMeta(self, e):
        """
        Build predicate metadata using the given QDomElement.
        :type e: QDomElement
        :rtype: dict
        """
        item = self.itemFromXml[e.attribute('type')]
        name = e.attribute('name')
        meta = self.project.meta(item, name)
        meta['description'] = e.firstChildElement('description').text()
        meta['url'] = e.firstChildElement('url').text()
        return meta

    def buildRoleMeta(self, e):
        """
        Build role metadata using the given QDomElement.
        :type e: QDomElement
        :rtype: dict
        """
        meta = self.buildPredicateMeta(e)
        meta['functional'] = bool(int(e.firstChildElement('functional').text()))
        meta['inverseFunctional'] = bool(int(e.firstChildElement('inverseFunctional').text()))
        meta['asymmetric'] = bool(int(e.firstChildElement('asymmetric').text()))
        meta['irreflexive'] = bool(int(e.firstChildElement('irreflexive').text()))
        meta['reflexive'] = bool(int(e.firstChildElement('reflexive').text()))
        meta['symmetric'] = bool(int(e.firstChildElement('symmetric').text()))
        meta['transitive'] = bool(int(e.firstChildElement('transitive').text()))
        return meta
    
    #############################################
    #   ONTOLOGY DIAGRAMS IMPORT : NODES
    #################################

    def importAttributeNode(self, d, e):
        """
        Build an Attribute node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: AttributeNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.AttributeNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importComplementNode(self, d, e):
        """
        Build a Complement node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: ComplementNode
        """
        return self.importGenericNode(d, Item.ComplementNode, e)

    def importConceptNode(self, d, e):
        """
        Build a Concept node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: ConceptNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.ConceptNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importDatatypeRestrictionNode(self, d, e):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.importGenericNode(d, Item.DatatypeRestrictionNode, e)

    def importDisjointUnionNode(self, d, e):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.importGenericNode(d, Item.DisjointUnionNode, e)

    def importDomainRestrictionNode(self, d, e):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DomainRestrictionNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.DomainRestrictionNode, e)
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importEnumerationNode(self, d, e):
        """
        Build an Enumeration node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: EnumerationNode
        """
        return self.importGenericNode(d, Item.EnumerationNode, e)

    def importFacetNode(self, d, e):
        """
        Build a FacetNode node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: FacetNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.FacetNode, e)
        n.setText(x.text())
        return n

    def importIndividualNode(self, d, e):
        """
        Build an Individual node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: IndividualNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.IndividualNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importIntersectionNode(self, d, e):
        """
        Build an Intersection node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: IntersectionNode
        """
        return self.importGenericNode(d, Item.IntersectionNode, e)

    def importPropertyAssertionNode(self, d, e):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = e.attribute('inputs', '').strip()
        n = self.importGenericNode(d, Item.PropertyAssertionNode, e)
        n.inputs = DistinctList(inputs.split(',') if inputs else [])
        return n

    def importRangeRestrictionNode(self, d, e):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: RangeRestrictionNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.RangeRestrictionNode, e)
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importRoleNode(self, d, e):
        """
        Build a Role node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: RoleNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.RoleNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importRoleChainNode(self, d, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: RoleChainNode
        """
        inputs = e.attribute('inputs', '').strip()
        n = self.importGenericNode(d, Item.RoleChainNode, e)
        n.inputs = DistinctList(inputs.split(',') if inputs else [])
        return n

    def importRoleInverseNode(self, d, e):
        """
        Build a RoleInverse node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: RoleInverseNode
        """
        return self.importGenericNode(d, Item.RoleInverseNode, e)

    def importValueDomainNode(self, d, e):
        """
        Build a Value-Domain node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: ValueDomainNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.ValueDomainNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importUnionNode(self, d, e):
        """
        Build a Union node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: UnionNode
        """
        return self.importGenericNode(d, Item.UnionNode, e)

    #############################################
    #   ONTOLOGY DIAGRAMS IMPORT : EDGES
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

    #############################################
    #   ONTOLOGY DIAGRAMS IMPORT : GENERICS
    #################################

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

        edge = d.factory.create(i, **{
            'id': e.attribute('id'),
            'source': self.buffer[d.name][e.attribute('source')],
            'target': self.buffer[d.name][e.attribute('target')],
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

    @staticmethod
    def importGenericNode(d, i, e):
        """
        Build a node using the given item type and QDomElement.
        :type d: Diagram
        :type i: Item
        :type e: QDomElement
        :rtype: AbstractNode
        """
        geometry = e.firstChildElement('geometry')
        node = d.factory.create(i, **{
            'id': e.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width'))
        })
        node.setPos(QtCore.QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        return node

    #############################################
    #   ONTOLOGY DIAGRAMS : MAIN IMPORT
    #################################

    def importDiagram(self, e, i):
        """
        Create a diagram from the given QDomElement.
        :type e: QDomElement
        :type i: int
        :rtype: Diagram
        """
        QtWidgets.QApplication.processEvents()
        ## PARSE DIAGRAM INFORMATION
        name = e.attribute('name', 'diagram_{0}'.format(i))
        size = max(int(e.attribute('width', '10000')), int(e.attribute('height', '10000')))
        ## CREATE NEW DIAGRAM
        LOGGER.info('Loading diagram: %s', name)
        diagram = Diagram.create(name, size, self.project)
        self.buffer[diagram.name] = dict()
        ## LOAD DIAGRAM NODES
        sube = e.firstChildElement('node')
        while not sube.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(sube)
                func = self.importFuncForItem[item]
                node = func(diagram, sube)
            except Exception:
                LOGGER.exception('Failed to create node %s', sube.attribute('id'))
            else:
                diagram.addItem(node)
                diagram.guid.update(node.id)
                self.buffer[diagram.name][node.id] = node
            finally:
                sube = sube.nextSiblingElement('node')
        ## LOAD DIAGRAM EDGES
        sube = e.firstChildElement('edge')
        while not sube.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(sube)
                func = self.importFuncForItem[item]
                edge = func(diagram, sube)
            except Exception:
                LOGGER.exception('Failed to create edge %s', sube.attribute('id'))
            else:
                diagram.addItem(edge)
                diagram.guid.update(edge.id)
                self.buffer[diagram.name][edge.id] = edge
            finally:
                sube = sube.nextSiblingElement('edge')
        ## IDENTIFY NEUTRAL NODES
        nodes = [x for x in diagram.items(edges=False) if Identity.Neutral in x.identities()]
        if nodes:
            LOGGER.debug('Running identification algorithm for %s nodes', len(nodes))
            for node in nodes:
                diagram.sgnNodeIdentification.emit(node)
        ## CONFIGURE DIAGRAM SIGNALS
        connect(diagram.sgnItemAdded, self.project.doAddItem)
        connect(diagram.sgnItemRemoved, self.project.doRemoveItem)
        connect(diagram.selectionChanged, self.session.doUpdateState)
        ## RETURN GENERATED DIAGRAM
        return diagram

    def importMeta(self, e):
        """
        Create predicate metadata from the given QDomElement.
        :type e: QDomElement
        :rtype: tuple
        """
        try:
            QtWidgets.QApplication.processEvents()
            item = self.itemFromXml[e.attribute('type')]
            func = self.importMetaFuncForItem[item]
            meta = func(e)
        except Exception:
            LOGGER.exception('Failed to create meta for predicate %s', e.attribute('name'))
            return None
        else:
            return item, e.attribute('name'), meta

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

    #############################################
    #   MAIN IMPORT
    #################################

    def createDiagrams(self):
        """
        Create ontology diagrams by parsing the 'diagrams' section of the QDomDocument.
        """
        counter = 1
        section = self.document.documentElement().firstChildElement('diagrams')
        element = section.firstChildElement('diagram')
        while not element.isNull():
            self.project.addDiagram(self.importDiagram(element, counter))
            element = element.nextSiblingElement('diagram')
            counter += 1

    def createDomDocument(self):
        """
        Create the QDomDocument from where to parse Project information.
        """
        QtWidgets.QApplication.processEvents()
        filename = postfix(os.path.basename(self.path), File.Graphol.extension)
        filepath = os.path.join(self.path, filename)
        if not fexists(filepath):
            raise ProjectNotFoundError('missing project ontology: %s' % filepath)
        self.document = QtXml.QDomDocument()
        if not self.document.setContent(fread(filepath)):
            raise ProjectNotValidError('invalid project ontology supplied: %s' % filepath)
        graphol = self.document.documentElement()
        version = int(graphol.attribute('version', '2'))
        if version != 2:
            raise ProjectVersionError('project version mismatch: %s != 2' % version)

    def createLegacyProject(self):
        """
        Create a Project using the @deprecated Graphol project loader (v1).
        """
        worker = GrapholProjectLoader_v1(self.path, self.session)
        self.project = worker.load()
        worker = GrapholProjectExporter(self.project)
        worker.export()

    def createPredicatesMeta(self):
        """
        Create ontology predicated metadata by parsing the 'predicates' section of the QDomDocument.
        """
        QtWidgets.QApplication.processEvents()
        section = self.document.documentElement().firstChildElement('predicates')
        element = section.firstChildElement('predicate')
        while not element.isNull():
            meta = self.importMeta(element)
            if meta:
                self.project.setMeta(meta[0], meta[1], meta[2])
            element = element.nextSiblingElement('predicate')

    def createProject(self):
        """
        Create the Project by reading data from the parsed QDomDocument.
        """
        section = self.document.documentElement().firstChildElement('ontology')

        def parse(tag, default='unknown'):
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
            if not content:
                LOGGER.warning('Empty tag <%s> in ontology section, using default: %s', tag, default)
                return default
            LOGGER.debug('Loaded ontology %s: %s', tag, content)
            return content

        self.project = Project(
            self.path,
            parse('prefix'),
            parse('iri'),
            self.session.createProfile(parse('profile', 'OWL 2')),
            self.session)

    def projectRender(self):
        """
        Render all the elements in the Project ontology.
        """
        for item in self.project.items():
            item.updateEdgeOrNode()

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
        try:
            self.createDomDocument()
        except (ProjectNotFoundError, ProjectVersionError):
            self.createLegacyProject()
        else:
            LOGGER.header('Loading project: %s', os.path.basename(self.path))
            self.createProject()
            self.createDiagrams()
            self.createPredicatesMeta()
            self.projectRender()
            LOGGER.separator('-')

        return self.project