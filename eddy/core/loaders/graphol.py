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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item
from eddy.core.diagram import Diagram
from eddy.core.exceptions import ParseError
from eddy.core.functions.fsystem import fread, fexists
from eddy.core.functions.signals import connect
from eddy.core.loaders.common import AbstractLoader


class GrapholLoader(AbstractLoader):
    """
    This class can be used to load graphol diagrams from file.
    """
    GrapholVersion = 1

    def __init__(self, project, path, parent):
        """
        Initialize the graphol loader.
        :type project: Project
        :type path: str
        :type parent: MainWindow
        """
        super().__init__(parent)
        
        self.diagram = None
        self.nodes = dict()
        self.path = path
        self.project = project
        self.mainwindow = project.parent()

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
            Item.ValueRestrictionNode: self.buildFacetNode,
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
            'value-restriction': Item.ValueRestrictionNode,
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
        label = self.extractLabelInsideElement(element)
        node = self.buildGenericNode(Item.AttributeNode, element)
        node.brush = QBrush(QColor(element.attribute('color', '#fcfcfc')))
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
        label = self.extractLabelInsideElement(element)
        node = self.buildGenericNode(Item.ConceptNode, element)
        node.brush = QBrush(QColor(element.attribute('color', '#fcfcfc')))
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
        label = self.extractLabelInsideElement(element)
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
        label = self.extractLabelInsideElement(element)
        node = self.buildGenericNode(Item.FacetNode, element)
        node.setText(label.text())
        return node

    def buildIndividualNode(self, element):
        """
        Build an Individual node using the given QDomElement.
        :type element: QDomElement
        :rtype: IndividualNode
        """
        label = self.extractLabelInsideElement(element)
        node = self.buildGenericNode(Item.IndividualNode, element)
        node.brush = QBrush(QColor(element.attribute('color', '#fcfcfc')))
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
        label = self.extractLabelInsideElement(element)
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
        label = self.extractLabelInsideElement(element)
        node = self.buildGenericNode(Item.RoleNode, element)
        node.brush = QBrush(QColor(element.attribute('color', '#fcfcfc')))
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
        label = self.extractLabelInsideElement(element)
        node = self.buildGenericNode(Item.ValueDomainNode, element)
        node.brush = QBrush(QColor(element.attribute('color', '#fcfcfc')))
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
        edge.complete = bool(int(element.attribute('complete', '0')))
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
        point = self.extractPointInsideElement(element)
        while not point.isNull():
            points.append(QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = self.extractPointBesideElement(point)

        kwargs = {
            'id': element.attribute('id'),
            'source': self.nodes[element.attribute('source')],
            'target': self.nodes[element.attribute('target')],
            'breakpoints': points[1:-1],
        }

        edge = self.diagram.factory.create(item, **kwargs)

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
        geometry = self.extractGeometryInsideElement(element)
        kwargs = {
            'id': element.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width')),
        }
        node = self.diagram.factory.create(item, **kwargs)
        node.setPos(QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        return node

    @staticmethod
    def extractGeometryInsideElement(element):
        """
        Returns the geometry element inside the given one.
        :type element: QDomElement
        :rtype: QDomElement
        """
        search = element.firstChildElement('geometry')
        if search.isNull():
            # KEEP BACKWARDS COMPATIBILITY
            search = element.firstChildElement('shape:geometry')
        return search

    @staticmethod
    def extractLabelInsideElement(element):
        """
        Returns the label element inside the given one.
        :type element: QDomElement
        :rtype: QDomElement
        """
        search = element.firstChildElement('label')
        if search.isNull():
            # KEEP BACKWARDS COMPATIBILITY
            search = element.firstChildElement('shape:label')
        return search

    @staticmethod
    def extractPointBesideElement(element):
        """
        Returns the point element beside the given one.
        :type element: QDomElement
        :rtype: QDomElement
        """
        search = element.nextSiblingElement('point')
        if search.isNull():
            # KEEP BACKWARDS COMPATIBILITY
            search = element.nextSiblingElement('line:point')
        return search

    @staticmethod
    def extractPointInsideElement(element):
        """
        Returns the point element inside the given one.
        :type element: QDomElement
        :rtype: QDomElement
        """
        search = element.firstChildElement('point')
        if search.isNull():
            # KEEP BACKWARDS COMPATIBILITY
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
    #   DIAGRAM GENERATION
    #################################

    def run(self):
        """
        Perform diagram import from .graphol file format.
        :rtype: Diagram
        """
        if not fexists(self.path):
            raise IOError('file not found: {0}'.format(self.path))

        document = QDomDocument()
        if not document.setContent(fread(self.path)):
            raise ParseError('could not initialize QDomDocument')

        # 1) INITIALIZE XML ROOT ELEMENT
        root = document.documentElement()

        # 2) READ GRAPH INITIALIZATION DATA
        graph = root.firstChildElement('graph')
        size = max(int(graph.attribute('width', '10000')), int(graph.attribute('height', '10000')))

        # 3) CREATE A DIAGRAM
        self.diagram = Diagram(self.path, self.project)
        self.diagram.setSceneRect(QRectF(-size / 2, -size / 2, size, size))
        self.diagram.setItemIndexMethod(Diagram.NoIndex)

        # 4) GENERATE NODES
        element = graph.firstChildElement('node')
        while not element.isNull():
            # noinspection PyArgumentList
            QApplication.processEvents()
            item = self.itemFromGrapholNode(element)
            func = self.importFuncForItem[item]
            node = func(element)
            self.diagram.addItem(node)
            self.diagram.guid.update(node.id)
            self.nodes[node.id] = node
            element = element.nextSiblingElement('node')

        # 5) GENERATE EDGES
        element = graph.firstChildElement('edge')
        while not element.isNull():
            # noinspection PyArgumentList
            QApplication.processEvents()
            item = self.itemFromGrapholNode(element)
            func = self.importFuncForItem[item]
            edge = func(element)
            self.diagram.addItem(edge)
            self.diagram.guid.update(edge.id)
            edge.updateEdge()
            element = element.nextSiblingElement('edge')

        # 6) RUN IDENTIFICATION ALGORITHM
        for node in self.nodes.values():
            self.diagram.identify(node)

        # 7) CONFIGURE SLOTS
        connect(self.diagram.sgnItemAdded, self.project.doAddItem)
        connect(self.diagram.sgnItemRemoved, self.project.doRemoveItem)
        connect(self.diagram.sgnActionCompleted, self.mainwindow.onDiagramActionCompleted)
        connect(self.diagram.sgnModeChanged, self.mainwindow.onDiagramModeChanged)
        connect(self.diagram.selectionChanged, self.mainwindow.doUpdateState)

        # 8) RETURN GENERATED DIAGRAM
        return self.diagram