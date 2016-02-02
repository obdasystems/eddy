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


from PyQt5.QtCore import QFile, QIODevice, QPointF, QSettings
from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes import Item, DistinctList
from eddy.core.exceptions import ParseError
from eddy.core.functions import expandPath
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
        self.settings = QSettings(expandPath('@home/Eddy.ini'), QSettings.IniFormat)
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

    def buildAttributeNode(self, node):
        """
        Build an Attribute node using the given QDomElement.
        :type node: QDomElement
        :rtype: AttributeNode
        """
        label = node.firstChildElement('shape:label')
        item = self.buildGenericNode(Item.AttributeNode, node)
        item.brush = node.attribute('color', '#fcfcfc')
        item.setText(label.text())
        item.setTextPos(item.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return item

    def buildComplementNode(self, node):
        """
        Build a Complement node using the given QDomElement.
        :type node: QDomElement
        :rtype: ComplementNode
        """
        return self.buildGenericNode(Item.ComplementNode, node)

    def buildConceptNode(self, node):
        """
        Build a Concept node using the given QDomElement.
        :type node: QDomElement
        :rtype: ConceptNode
        """
        label = node.firstChildElement('shape:label')
        item = self.buildGenericNode(Item.ConceptNode, node)
        item.brush = node.attribute('color', '#fcfcfc')
        item.setText(label.text())
        item.setTextPos(item.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return item

    def buildDatatypeRestrictionNode(self, node):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type node: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.buildGenericNode(Item.DatatypeRestrictionNode, node)

    def buildDisjointUnionNode(self, node):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type node: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.buildGenericNode(Item.DisjointUnionNode, node)

    def buildDomainRestrictionNode(self, node):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type node: QDomElement
        :rtype: DomainRestrictionNode
        """
        label = node.firstChildElement('shape:label')
        item = self.buildGenericNode(Item.DomainRestrictionNode, node)
        item.setText(label.text())
        item.setTextPos(item.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return item

    def buildEnumerationNode(self, node):
        """
        Build an Enumeration node using the given QDomElement.
        :type node: QDomElement
        :rtype: EnumerationNode
        """
        return self.buildGenericNode(Item.EnumerationNode, node)

    def buildIndividualNode(self, node):
        """
        Build an Individual node using the given QDomElement.
        :type node: QDomElement
        :rtype: IndividualNode
        """
        label = node.firstChildElement('shape:label')
        item = self.buildGenericNode(Item.IndividualNode, node)
        item.brush = node.attribute('color', '#fcfcfc')
        item.setText(label.text())
        item.setTextPos(item.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return item

    def buildIntersectionNode(self, node):
        """
        Build an Intersection node using the given QDomElement.
        :type node: QDomElement
        :rtype: IntersectionNode
        """
        return self.buildGenericNode(Item.IntersectionNode, node)

    def buildPropertyAssertionNode(self, node):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type node: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = node.attribute('inputs', '').strip()
        item = self.buildGenericNode(Item.PropertyAssertionNode, node)
        item.inputs = DistinctList(inputs.split(',') if inputs else [])
        return item

    def buildRangeRestrictionNode(self, node):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type node: QDomElement
        :rtype: RangeRestrictionNode
        """
        label = node.firstChildElement('shape:label')
        item = self.buildGenericNode(Item.RangeRestrictionNode, node)
        item.setText(label.text())
        item.setTextPos(item.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return item

    def buildRoleNode(self, node):
        """
        Build a Role node using the given QDomElement.
        :type node: QDomElement
        :rtype: RoleNode
        """
        label = node.firstChildElement('shape:label')
        item = self.buildGenericNode(Item.RoleNode, node)
        item.brush = node.attribute('color', '#fcfcfc')
        item.setText(label.text())
        item.setTextPos(item.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return item

    def buildRoleChainNode(self, node):
        """
        Build a RoleChain node using the given QDomElement.
        :type node: QDomElement
        :rtype: RoleChainNode
        """
        inputs = node.attribute('inputs', '').strip()
        item = self.buildGenericNode(Item.RoleChainNode, node)
        item.inputs = DistinctList(inputs.split(',') if inputs else [])
        return item

    def buildRoleInverseNode(self, node):
        """
        Build a RoleInverse node using the given QDomElement.
        :type node: QDomElement
        :rtype: RoleInverseNode
        """
        return self.buildGenericNode(Item.RoleInverseNode, node)

    def buildValueDomainNode(self, node):
        """
        Build a Value-Domain node using the given QDomElement.
        :type node: QDomElement
        :rtype: ValueDomainNode
        """
        label = node.firstChildElement('shape:label')
        item = self.buildGenericNode(Item.ValueDomainNode, node)
        item.brush = node.attribute('color', '#fcfcfc')
        item.setText(label.text())
        item.setTextPos(item.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return item

    def buildUnionNode(self, node):
        """
        Build a Union node using the given QDomElement.
        :type node: QDomElement
        :rtype: UnionNode
        """
        return self.buildGenericNode(Item.UnionNode, node)

    def buildValueRestrictionNode(self, node):
        """
        Build a ValueRestriction node using the given QDomElement.
        :type node: QDomElement
        :rtype: ValueRestrictionNode
        """
        label = node.firstChildElement('shape:label')
        item = self.buildGenericNode(Item.ValueRestrictionNode, node)
        item.brush = node.attribute('color', '#fcfcfc')
        item.setText(label.text())
        item.setTextPos(item.mapFromScene(QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return item

    ####################################################################################################################
    #                                                                                                                  #
    #   EDGES                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def buildInclusionEdge(self, edge):
        """
        Build an Inclusion edge using the given QDomElement.
        :type edge: QDomElement
        :rtype: InclusionEdge
        """
        item = self.buildGenericEdge(Item.InclusionEdge, edge)
        item.complete = bool(int(edge.attribute('complete', '0')))
        return item

    def buildInputEdge(self, edge):
        """
        Build an Input edge using the given QDomElement.
        :type edge: QDomElement
        :rtype: InputEdge
        """
        item = self.buildGenericEdge(Item.InputEdge, edge)
        item.functional = bool(int(edge.attribute('functional', '0')))
        return item

    def buildInstanceOfEdge(self, edge):
        """
        Build an InstanceOf edge using the given QDomElement.
        :type edge: QDomElement
        :rtype: InstanceOfEdge
        """
        return self.buildGenericEdge(Item.InputEdge, edge)

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

        item = self.itemFactory.create(item=item, scene=self.scene, **kwargs)

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
        item.updateEdge()
        return item

    def buildGenericNode(self, item, node):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type node: QDomElement
        :rtype: AbstractNode
        """
        url = node.firstChildElement('data:url')
        description = node.firstChildElement('data:description')
        geometry = node.firstChildElement('shape:geometry')

        kwargs = {
            'description': description.text(),
            'height': int(geometry.attribute('height')),
            'id': node.attribute('id'),
            'url': url.text(),
            'width': int(geometry.attribute('width')),
        }

        item = self.itemFactory.create(item=item, scene=self.scene, **kwargs)
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
        Perform ontology import from .graphml file format.
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
            w = int(graph.attribute('width', self.settings.value('diagram/size', '5000', str)))
            h = int(graph.attribute('height', self.settings.value('diagram/size', '5000', str)))

            # 3) GENERATE DIAGRAM SCENE
            self.scene = self.mainwindow.createScene(width=w, height=h)
            self.scene.document.path = self.filepath

            # 4) GENERATE NODES
            node = graph.firstChildElement('node')
            while not node.isNull():

                temp = None
                item = self.itemFromGrapholNode(node)

                try:

                    if item is Item.AttributeNode:
                        temp = self.buildAttributeNode(node)
                    elif item is Item.ComplementNode:
                        temp = self.buildComplementNode(node)
                    elif item is Item.ConceptNode:
                        temp = self.buildConceptNode(node)
                    elif item is Item.DatatypeRestrictionNode:
                        temp = self.buildDatatypeRestrictionNode(node)
                    elif item is Item.DisjointUnionNode:
                        temp = self.buildDisjointUnionNode(node)
                    elif item is Item.DomainRestrictionNode:
                        temp = self.buildDomainRestrictionNode(node)
                    elif item is Item.EnumerationNode:
                        temp = self.buildEnumerationNode(node)
                    elif item is Item.IndividualNode:
                        temp = self.buildIndividualNode(node)
                    elif item is Item.IntersectionNode:
                        temp = self.buildIntersectionNode(node)
                    elif item is Item.PropertyAssertionNode:
                        temp = self.buildPropertyAssertionNode(node)
                    elif item is Item.RangeRestrictionNode:
                        temp = self.buildRangeRestrictionNode(node)
                    elif item is Item.RoleNode:
                        temp = self.buildRoleNode(node)
                    elif item is Item.RoleChainNode:
                        temp = self.buildRoleChainNode(node)
                    elif item is Item.RoleInverseNode:
                        temp = self.buildRoleInverseNode(node)
                    elif item is Item.UnionNode:
                        temp = self.buildUnionNode(node)
                    elif item is Item.ValueDomainNode:
                        temp = self.buildValueDomainNode(node)
                    elif item is Item.ValueRestrictionNode:
                        temp = self.buildValueRestrictionNode(node)

                    if not temp:
                        raise ValueError('unknown node: {}'.format(node.attribute('type')))

                    self.scene.addItem(temp)
                    self.scene.guid.update(temp.id)
                finally:
                    node = node.nextSiblingElement('node')

            # 5) GENERATE EDGES
            edge = graph.firstChildElement('edge')
            while not edge.isNull():

                temp = None
                item = self.itemFromGrapholNode(edge)

                try:

                    if item is Item.InclusionEdge:
                        temp = self.buildInclusionEdge(edge)
                    elif item is Item.InputEdge:
                        temp = self.buildInputEdge(edge)
                    elif item is Item.InstanceOfEdge:
                        temp = self.buildInstanceOfEdge(edge)

                    if not temp:
                        raise ValueError('unknown edge: {}'.format(edge.attribute('type')))

                    self.scene.addItem(temp)
                    self.scene.guid.update(temp.id)
                finally:
                    edge = edge.nextSiblingElement('edge')

        finally:

            file.close()