# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QFile, QIODevice, QPointF
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes import Item, DistinctList
from eddy.core.exceptions import ParseError
from eddy.core.items.nodes.common.meta import MetaFactory
from eddy.core.loaders.common import AbstractLoader


class GrapholLoader(AbstractLoader):
    """
    This class can be used to load Graphol documents.
    """
    def __init__(self, mainwindow, filepath, parent=None):
        """
        Initialize the Graphml importer.
        :type mainwindow: MainWindow
        :type filepath: str
        :type parent: QObject
        """
        super().__init__(mainwindow, filepath, parent)
        self.metaFactory = MetaFactory(self)
        self.itemFromXml = {
            'attribute': Item.AttributeNode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptNode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
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
            'instance-of': Item.InstanceOfEdge,
        }

    ####################################################################################################################
    #                                                                                                                  #
    #   NODES                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def buildAttributeNode(self, element):
        """
        Build an Attribute node using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeNode
        """
        label = element.firstChildElement('shape:label')
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
        label = element.firstChildElement('shape:label')
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
        label = element.firstChildElement('shape:label')
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

    def buildIndividualNode(self, element):
        """
        Build an Individual node using the given QDomElement.
        :type element: QDomElement
        :rtype: IndividualNode
        """
        label = element.firstChildElement('shape:label')
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
        label = element.firstChildElement('shape:label')
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
        label = element.firstChildElement('shape:label')
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
        label = element.firstChildElement('shape:label')
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

    def buildValueRestrictionNode(self, element):
        """
        Build a ValueRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: ValueRestrictionNode
        """
        label = element.firstChildElement('shape:label')
        node = self.buildGenericNode(Item.ValueRestrictionNode, element)
        node.brush = QBrush(QColor(element.attribute('color', '#fcfcfc')))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    ####################################################################################################################
    #                                                                                                                  #
    #   EDGES                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

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

    def buildInstanceOfEdge(self, element):
        """
        Build an InstanceOf edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InstanceOfEdge
        """
        return self.buildGenericEdge(Item.InputEdge, element)

    ####################################################################################################################
    #                                                                                                                  #
    #   METADATA                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def buildPredicateMetadata(self, element):
        """
        Build predicate metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: PredicateMetaData
        """
        item = self.itemFromXml[element.attribute('type')]
        predicate = element.attribute('predicate')
        url = element.firstChildElement('data:url')
        description = element.firstChildElement('data:description')
        meta = self.metaFactory.create(item, predicate)
        meta.url = url.text()
        meta.description = description.text()
        return meta

    def buildAttributeMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeMetaData
        """
        meta = self.buildPredicateMetadata(element)
        functionality = element.firstChildElement('data:functionality')
        meta.functionality = bool(int(functionality.text()))
        return meta

    def buildRoleMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeMetaData
        """
        meta = self.buildPredicateMetadata(element)
        functionality = element.firstChildElement('data:functionality')
        inverseFunctionality = element.firstChildElement('data:inverseFunctionality')
        asymmetry = element.firstChildElement('data:asymmetry')
        irreflexivity = element.firstChildElement('data:irreflexivity')
        reflexivity = element.firstChildElement('data:reflexivity')
        symmetry = element.firstChildElement('data:symmetry')
        transitivity = element.firstChildElement('data:transitivity')
        meta.functionality = bool(int(functionality.text()))
        meta.inverseFunctionality = bool(int(inverseFunctionality.text()))
        meta.asymmetry = bool(int(asymmetry.text()))
        meta.irreflexivity = bool(int(irreflexivity.text()))
        meta.reflexivity = bool(int(reflexivity.text()))
        meta.symmetry = bool(int(symmetry.text()))
        meta.transitivity = bool(int(transitivity.text()))
        return meta

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def buildGenericEdge(self, item, edge):
        """
        Build an edge using the given item type and QDomElement.
        :type item: Item
        :type edge: QDomElement
        :rtype: AbstractEdge
        """
        points = []
        point = edge.firstChildElement('line:point')
        while not point.isNull():
            points.append(QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = point.nextSiblingElement('line:point')

        kwargs = {
            'id': edge.attribute('id'),
            'source': self.scene.node(edge.attribute('source')),
            'target': self.scene.node(edge.attribute('target')),
            'breakpoints': points[1:-1],
        }

        item = self.factory.create(item=item, scene=self.scene, **kwargs)

        # set the anchor points only if they are inside the endpoint shape: users can modify
        # the .graphol file manually, changing anchor points coordinates, which will result
        # in an edge floating in the scene without being bounded by endpoint shapes. Not
        # setting the anchor point will make the edge use the default one (node center point)

        path = item.source.painterPath()
        if path.contains(item.source.mapFromScene(points[0])):
            item.source.setAnchor(item, points[0])

        path = item.target.painterPath()
        if path.contains(item.target.mapFromScene(points[-1])):
            item.target.setAnchor(item, points[-1])

        # map the edge over the source and target nodes
        item.source.addEdge(item)
        item.target.addEdge(item)
        return item

    def buildGenericNode(self, item, node):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type node: QDomElement
        :rtype: AbstractNode
        """
        geometry = node.firstChildElement('shape:geometry')

        kwargs = {
            'id': node.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width')),
        }

        item = self.factory.create(item=item, scene=self.scene, **kwargs)
        item.setPos(QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        return item

    def itemFromGrapholNode(self, element):
        """
        Returns the item matching the given Graphol node.
        :type element: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[element.attribute('type').lower().strip()]
        except KeyError:
            return None

    ####################################################################################################################
    #                                                                                                                  #
    #   DIAGRAM SCENE GENERATION                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def run(self):
        """
        Perform ontology import from .graphol file format.
        """
        file = QFile(self.filepath)

        try:

            if not file.open(QIODevice.ReadOnly):
                raise IOError('File not found: {}'.format(self.filepath))

            document = QDomDocument()
            if not document.setContent(file):
                raise ParseError('could not initialize DOM document')

            # 1) INITIALIZE XML ROOT ELEMENT
            root = document.documentElement()

            # 2) READ GRAPH INITIALIZATION DATA
            graph = root.firstChildElement('graph')
            w = int(graph.attribute('width', str(self.mainwindow.diagramSize)))
            h = int(graph.attribute('height', str(self.mainwindow.diagramSize)))

            # 3) GENERATE DIAGRAM SCENE
            self.scene = self.mainwindow.createScene(width=w, height=h)
            self.scene.document.path = self.filepath

            # 4) GENERATE NODES
            element = graph.firstChildElement('node')
            while not element.isNull():

                # noinspection PyArgumentList
                QApplication.processEvents()

                node = None
                item = self.itemFromGrapholNode(element)

                try:

                    if item is Item.AttributeNode:
                        node = self.buildAttributeNode(element)
                    elif item is Item.ComplementNode:
                        node = self.buildComplementNode(element)
                    elif item is Item.ConceptNode:
                        node = self.buildConceptNode(element)
                    elif item is Item.DatatypeRestrictionNode:
                        node = self.buildDatatypeRestrictionNode(element)
                    elif item is Item.DisjointUnionNode:
                        node = self.buildDisjointUnionNode(element)
                    elif item is Item.DomainRestrictionNode:
                        node = self.buildDomainRestrictionNode(element)
                    elif item is Item.EnumerationNode:
                        node = self.buildEnumerationNode(element)
                    elif item is Item.IndividualNode:
                        node = self.buildIndividualNode(element)
                    elif item is Item.IntersectionNode:
                        node = self.buildIntersectionNode(element)
                    elif item is Item.PropertyAssertionNode:
                        node = self.buildPropertyAssertionNode(element)
                    elif item is Item.RangeRestrictionNode:
                        node = self.buildRangeRestrictionNode(element)
                    elif item is Item.RoleNode:
                        node = self.buildRoleNode(element)
                    elif item is Item.RoleChainNode:
                        node = self.buildRoleChainNode(element)
                    elif item is Item.RoleInverseNode:
                        node = self.buildRoleInverseNode(element)
                    elif item is Item.UnionNode:
                        node = self.buildUnionNode(element)
                    elif item is Item.ValueDomainNode:
                        node = self.buildValueDomainNode(element)
                    elif item is Item.ValueRestrictionNode:
                        node = self.buildValueRestrictionNode(element)

                    if not node:
                        raise ValueError('unknown node: {}'.format(element.attribute('type')))

                    self.scene.addItem(node)
                    self.scene.sgnItemAdded.emit(node)
                    self.scene.guid.update(node.id)
                finally:
                    element = element.nextSiblingElement('node')

            # 5) GENERATE EDGES
            element = graph.firstChildElement('edge')
            while not element.isNull():

                # noinspection PyArgumentList
                QApplication.processEvents()

                edge = None
                item = self.itemFromGrapholNode(element)

                try:

                    if item is Item.InclusionEdge:
                        edge = self.buildInclusionEdge(element)
                    elif item is Item.InputEdge:
                        edge = self.buildInputEdge(element)
                    elif item is Item.InstanceOfEdge:
                        edge = self.buildInstanceOfEdge(element)

                    if not edge:
                        raise ValueError('unknown edge: {}'.format(element.attribute('type')))

                    self.scene.addItem(edge)
                    self.scene.sgnItemAdded.emit(edge)
                    self.scene.guid.update(edge.id)
                    edge.updateEdge()
                finally:
                    element = element.nextSiblingElement('edge')

            # 6) GENERATE PREDICATE METADATA
            metadata = root.firstChildElement('metadata')
            if not metadata.isNull():

                element = metadata.firstChildElement('meta')
                while not element.isNull():

                    # noinspection PyArgumentList
                    QApplication.processEvents()

                    item = self.itemFromGrapholNode(element)

                    try:

                        if item is Item.AttributeNode:
                            meta = self.buildAttributeMetadata(element)
                        elif item is Item.RoleNode:
                            meta = self.buildRoleMetadata(element)
                        else:
                            meta = self.buildPredicateMetadata(element)

                        if meta:
                            self.scene.meta.add(meta.item, meta.predicate, meta)

                    finally:
                        element = element.nextSiblingElement('meta')

        finally:

            file.close()