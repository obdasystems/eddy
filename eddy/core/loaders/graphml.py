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


from PyQt5.QtCore import QPointF, QRectF, QObject
from PyQt5.QtWidgets import QApplication
from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes.graphol import Item
from eddy.core.diagram import Diagram
from eddy.core.exceptions import ParseError
from eddy.core.functions.fsystem import fexists
from eddy.core.functions.fsystem import fread
from eddy.core.functions.misc import snapF
from eddy.core.functions.signals import connect


class GraphmlLoader(QObject):
    """
    This class can be used to import graphol ontologies created using the graphol paletter for yEd.
    """
    def __init__(self, project, path, parent=None):
        """
        Initialize the graphml importer.
        :type project: Project
        :type path: str
        :type parent: QObject
        """
        super().__init__(parent)
        self.diagram = None
        self.errors = []
        self.project = project
        self.path = path
        self.keys = dict()

    #############################################
    #   NODES
    #################################

    def buildAttributeNode(self, element):
        """
        Build an Attribute node using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeNode
        """
        return self.buildNodeFromGenericNode(Item.AttributeNode, element)

    def buildComplementNode(self, element):
        """
        Build a Complement node using the given QDomElement.
        :type element: QDomElement
        :rtype: ComplementNode
        """
        return self.buildNodeFromShapeNode(Item.ComplementNode, element)

    def buildConceptNode(self, element):
        """
        Build a Concept node using the given QDomElement.
        :type element: QDomElement
        :rtype: ConceptNode
        """
        return self.buildNodeFromGenericNode(Item.ConceptNode, element)

    def buildDatatypeRestrictionNode(self, element):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.buildNodeFromShapeNode(Item.DatatypeRestrictionNode, element)

    def buildDisjointUnionNode(self, element):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type element: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.buildNodeFromShapeNode(Item.DisjointUnionNode, element)

    def buildDomainRestrictionNode(self, element):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: DomainRestrictionNode
        """
        node = self.buildNodeFromShapeNode(Item.DomainRestrictionNode, element)
        if node:
            data = element.firstChildElement('data')
            while not data.isNull():
                if data.attribute('key', '') == self.keys['node_key']:
                    shapeNode = data.firstChildElement('y:ShapeNode')
                    nodeLabel = shapeNode.firstChildElement('y:NodeLabel')
                    node.setText(nodeLabel.text())
                data = data.nextSiblingElement('data')
        return node

    def buildEnumerationNode(self, element):
        """
        Build an Enumeration node using the given QDomElement.
        :type element: QDomElement
        :rtype: EnumerationNode
        """
        return self.buildNodeFromShapeNode(Item.EnumerationNode, element)

    def buildIndividualNode(self, element):
        """
        Build an Individual node using the given QDomElement.
        :type element: QDomElement
        :rtype: IndividualNode
        """
        node = self.buildNodeFromShapeNode(Item.IndividualNode, element)
        if node:
            data = element.firstChildElement('data')
            while not data.isNull():
                if data.attribute('key', '') == self.keys['node_key']:
                    shapeNode = data.firstChildElement('y:ShapeNode')
                    nodeLabel = shapeNode.firstChildElement('y:NodeLabel')
                    node.setText(nodeLabel.text())
                data = data.nextSiblingElement('data')
        return node

    def buildIntersectionNode(self, element):
        """
        Build an Intersection node using the given QDomElement.
        :type element: QDomElement
        :rtype: IntersectionNode
        """
        return self.buildNodeFromShapeNode(Item.IntersectionNode, element)

    def buildRangeRestrictionNode(self, element):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: RangeRestrictionNode
        """
        node = self.buildNodeFromShapeNode(Item.RangeRestrictionNode, element)
        if node:
            data = element.firstChildElement('data')
            while not data.isNull():
                if data.attribute('key', '') == self.keys['node_key']:
                    shapeNode = data.firstChildElement('y:ShapeNode')
                    nodeLabel = shapeNode.firstChildElement('y:NodeLabel')
                    node.setText(nodeLabel.text())
                data = data.nextSiblingElement('data')
        return node

    def buildRoleNode(self, element):
        """
        Build a Role node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleNode
        """
        return self.buildNodeFromGenericNode(Item.RoleNode, element)

    def buildRoleChainNode(self, element):
        """
        Build a RoleChain node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleChainNode
        """
        return self.buildNodeFromShapeNode(Item.RoleChainNode, element)

    def buildRoleInverseNode(self, element):
        """
        Build a RoleInverse node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleInverseNode
        """
        return self.buildNodeFromShapeNode(Item.RoleInverseNode, element)

    def buildValueDomainNode(self, element):
        """
        Build a Value-Domain node using the given QDomElement.
        :type element: QDomElement
        :rtype: ValueDomainNode
        """
        node = self.buildNodeFromShapeNode(Item.ValueDomainNode, element)
        if node:
            data = element.firstChildElement('data')
            while not data.isNull():
                if data.attribute('key', '') == self.keys['node_key']:
                    shapeNode = data.firstChildElement('y:ShapeNode')
                    nodeLabel = shapeNode.firstChildElement('y:NodeLabel')
                    node.setText(nodeLabel.text())
                data = data.nextSiblingElement('data')
        return node

    def buildUnionNode(self, element):
        """
        Build a Union node using the given QDomElement.
        :type element: QDomElement
        :rtype: UnionNode
        """
        return self.buildNodeFromShapeNode(Item.UnionNode, element)

    def buildValueRestrictionNode(self, element):
        """
        Build a ValueRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: ValueRestrictionNode
        """
        return self.buildNodeFromUMLNoteNode(Item.ValueRestrictionNode, element)

    #############################################
    #   NODES
    #################################

    def buildInclusionEdge(self, element):
        """
        Build an Inclusion edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InclusionEdge
        """
        edge = self.buildEdgeFromGenericEdge(Item.InclusionEdge, element)
        if edge:
            data = element.firstChildElement('data')
            while not data.isNull():
                if data.attribute('key', '') == self.keys['edge_key']:
                    polyLineEdge = data.firstChildElement('y:PolyLineEdge')
                    arrows = polyLineEdge.firstChildElement('y:Arrows')
                    if arrows.attribute('source', '') == 'standard' and arrows.attribute('target', '') == 'standard':
                        edge.complete = True
                data = data.nextSiblingElement('data')
            edge.updateEdge()
        return edge

    def buildInputEdge(self, element):
        """
        Build an Input edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InputEdge
        """
        edge = self.buildEdgeFromGenericEdge(Item.InputEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    def buildMembershipEdge(self, element):
        """
        Build a Membership edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InputEdge
        """
        edge = self.buildEdgeFromGenericEdge(Item.MembershipEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    #############################################
    #   AUXILIARY METHODS
    #################################

    def buildEdgeFromGenericEdge(self, item, element):
        """
        Build an edge using the given item type and QDomElement.
        :type item: Item
        :type element: QDomElement
        :rtype: AbstractEdge
        """
        data = element.firstChildElement('data')
        while not data.isNull():

            if data.attribute('key', '') == self.keys['edge_key']:

                points = []
                polyLineEdge = data.firstChildElement('y:PolyLineEdge')
                path = polyLineEdge.firstChildElement('y:Path')
                collection = path.elementsByTagName('y:Point')
                for i in range(0, collection.count()):
                    point = collection.at(i).toElement()
                    pos = QPointF(float(point.attribute('x')), float(point.attribute('y')))
                    pos = QPointF(snapF(pos.x(), Diagram.GridSize), snapF(pos.y(), Diagram.GridSize))
                    points.append(pos)

                kwargs = {
                    'id': element.attribute('id'),
                    'source': self.diagram.node(element.attribute('source')),
                    'target': self.diagram.node(element.attribute('target')),
                    'breakpoints': points,
                }

                edge = self.project.itemFactory.create(item, **kwargs)

                # yEd, differently from the node pos whose origin matches the TOP-LEFT corner,
                # consider the center of the shape as original anchor point (0,0). So if the
                # anchor point hs a negative X it's moved a bit on the left with respect to
                # the center of the shape (the same applies for the Y axis)
                sourceP = QPointF(float(path.attribute('sx')), float(path.attribute('sy')))
                sourceP = edge.source.pos() + sourceP
                sourceP = QPointF(snapF(sourceP.x(), Diagram.GridSize), snapF(sourceP.y(), Diagram.GridSize))

                targetP = QPointF(float(path.attribute('tx')), float(path.attribute('ty')))
                targetP = edge.target.pos() + targetP
                targetP = QPointF(snapF(targetP.x(), Diagram.GridSize), snapF(targetP.y(), Diagram.GridSize))

                painterPath = edge.source.painterPath()
                if painterPath.contains(edge.source.mapFromScene(sourceP)):
                    edge.source.setAnchor(edge, sourceP)

                painterPath = edge.target.painterPath()
                if painterPath.contains(edge.target.mapFromScene(targetP)):
                    edge.target.setAnchor(edge, targetP)

                edge.source.addEdge(edge)
                edge.target.addEdge(edge)
                return edge

            data = data.nextSiblingElement('data')

        return None

    def buildNodeFromGenericNode(self, item, element):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type element: QDomElement
        :rtype: AbstractNode
        """
        data = element.firstChildElement('data')
        while not data.isNull():

            if data.attribute('key', '') == self.keys['node_key']:

                genericNode = data.firstChildElement('y:GenericNode')
                geometry = genericNode.firstChildElement('y:Geometry')
                nodeLabel = genericNode.firstChildElement('y:NodeLabel')

                kwargs = {
                    'id': element.attribute('id'),
                    'height': float(geometry.attribute('height')),
                    'width': float(geometry.attribute('width')),
                }

                node = self.project.itemFactory.create(item, **kwargs)

                # yEd uses the TOP-LEFT corner as (0,0) coordinate => we need to translate our
                # position (0,0), which is instead at the center of the shape, so that the TOP-LEFT
                # corner of the shape in yEd matches the TOP-LEFT corner of the shape in Eddy.
                # Additionally we force-snap the position to the grid so that items say aligned.
                pos = QPointF(float(geometry.attribute('x')), float(geometry.attribute('y')))
                pos = pos + QPointF(node.width() / 2, node.height() / 2)
                pos = QPointF(snapF(pos.x(), Diagram.GridSize), snapF(pos.y(), Diagram.GridSize))
                node.setPos(pos)
                node.setText(nodeLabel.text())
                return node

            data = data.nextSiblingElement('data')

        return None

    def buildNodeFromShapeNode(self, item, element):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type element: QDomElement
        :rtype: AbstractNode
        """
        data = element.firstChildElement('data')
        while not data.isNull():

            if data.attribute('key', '') == self.keys['node_key']:

                shapeNode = data.firstChildElement('y:ShapeNode')
                geometry = shapeNode.firstChildElement('y:Geometry')

                kwargs = {
                    'id': element.attribute('id'),
                    'height': float(geometry.attribute('height')),
                    'width': float(geometry.attribute('width')),
                }

                node = self.project.itemFactory.create(item, **kwargs)

                # yEd uses the TOP-LEFT corner as (0,0) coordinate => we need to translate our
                # position (0,0), which is instead at the center of the shape, so that the TOP-LEFT
                # corner of the shape in yEd matches the TOP-LEFT corner of the shape in Eddy.
                # Additionally we force-snap the position to the grid so that items say aligned.
                pos = QPointF(float(geometry.attribute('x')), float(geometry.attribute('y')))
                pos = pos + QPointF(node.width() / 2, node.height() / 2)
                pos = QPointF(snapF(pos.x(), Diagram.GridSize), snapF(pos.y(), Diagram.GridSize))
                node.setPos(pos)
                return node

            data = data.nextSiblingElement('data')

        return None

    def buildNodeFromUMLNoteNode(self, item, element):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type element: QDomElement
        :rtype: AbstractNode
        """
        data = element.firstChildElement('data')
        while not data.isNull():

            if data.attribute('key', '') == self.keys['node_key']:

                umlNoteNode = data.firstChildElement('y:UMLNoteNode')
                geometry = umlNoteNode.firstChildElement('y:Geometry')
                nodeLabel = umlNoteNode.firstChildElement('y:NodeLabel')

                kwargs = {
                    'id': element.attribute('id'),
                    'height': float(geometry.attribute('height')),
                    'width': float(geometry.attribute('width')),
                }

                node = self.project.itemFactory.create(item, **kwargs)

                # yEd uses the TOP-LEFT corner as (0,0) coordinate => we need to translate our
                # position (0,0), which is instead at the center of the shape, so that the TOP-LEFT
                # corner of the shape in yEd matches the TOP-LEFT corner of the shape in Eddy.
                # Additionally we force-snap the position to the grid so that items say aligned.
                pos = QPointF(float(geometry.attribute('x')), float(geometry.attribute('y')))
                pos = pos + QPointF(node.width() / 2, node.height() / 2)
                pos = QPointF(snapF(pos.x(), Diagram.GridSize), snapF(pos.y(), Diagram.GridSize))
                node.setPos(pos)
                node.setText(nodeLabel.text())
                return node

            data = data.nextSiblingElement('data')

        return None

    def itemFromGraphmlNode(self, element):
        """
        Returns the item matching the given Graphml node.
        :type element: QDomElement
        :rtype: Item
        """
        data = element.firstChildElement('data')
        while not data.isNull():

            # NODE
            if data.attribute('key', '') == self.keys['node_key']:

                # GENERIC NODE
                genericNode = data.firstChildElement('y:GenericNode')
                if not genericNode.isNull():

                    configuration = genericNode.attribute('configuration', '')
                    if configuration == 'com.yworks.entityRelationship.small_entity':
                        return Item.ConceptNode
                    if configuration == 'com.yworks.entityRelationship.attribute':
                        return Item.AttributeNode
                    if configuration == 'com.yworks.entityRelationship.relationship':
                        return Item.RoleNode

                # SHAPE NODE
                shapeNode = data.firstChildElement('y:ShapeNode')
                if not shapeNode.isNull():

                    shape = shapeNode.firstChildElement('y:Shape')
                    if not shape.isNull():

                        shapeType = shape.attribute('type', '')
                        if shapeType == 'octagon':
                            return Item.IndividualNode
                        if shapeType == 'roundrectangle':
                            return Item.ValueDomainNode

                        if shapeType == 'hexagon':

                            # We need to identify DisjointUnion from the color and not by checking the empty label
                            # because in some ontologies created under yEd another operator node has been copied
                            # over and the background color has been changed despite the label not being removed.
                            fill = shapeNode.firstChildElement('y:Fill')
                            if not fill.isNull():
                                color = fill.attribute('color', '')
                                if color == '#000000':
                                    return Item.DisjointUnionNode

                            nodeLabel = shapeNode.firstChildElement('y:NodeLabel')
                            if not nodeLabel.isNull():
                                nodeText = nodeLabel.text().strip()
                                if nodeText == 'and':
                                    return Item.IntersectionNode
                                if nodeText == 'or':
                                    return Item.UnionNode
                                if nodeText == 'not':
                                    return Item.ComplementNode
                                if nodeText == 'oneOf':
                                    return Item.EnumerationNode
                                if nodeText == 'chain':
                                    return Item.RoleChainNode
                                if nodeText == 'inv':
                                    return Item.RoleInverseNode
                                if nodeText == 'data':
                                    return Item.DatatypeRestrictionNode

                        if shapeType == 'rectangle':
                            fill = shapeNode.firstChildElement('y:Fill')
                            if not fill.isNull():
                                color = fill.attribute('color', '')
                                if color == '#000000':
                                    return Item.RangeRestrictionNode
                                return Item.DomainRestrictionNode

                # UML NOTE NODE
                umlNoteNode = data.firstChildElement('y:UMLNoteNode')
                if not umlNoteNode.isNull():
                    return Item.ValueRestrictionNode

            if data.attribute('key', '') == self.keys['edge_key']:

                polyLineEdge = data.firstChildElement('y:PolyLineEdge')
                if not polyLineEdge.isNull():
                    lineStyle = polyLineEdge.firstChildElement('y:LineStyle')
                    if not lineStyle.isNull():
                        lineType = lineStyle.attribute('type', '')
                        if lineType == 'line':
                            edgeLabel = polyLineEdge.firstChildElement('y:EdgeLabel')
                            if not edgeLabel.isNull():
                                edgeText = edgeLabel.text().strip()
                                if  edgeText == 'instanceOf':
                                    return Item.MembershipEdge
                            return Item.InclusionEdge
                        if lineType == 'dashed':
                            return Item.InputEdge

            data = data.nextSiblingElement('data')

        return None

    #############################################
    #   DIAGRAM GENERATION
    #################################

    def run(self):
        """
        Perform diagram import from .graphml file format.
        """
        if not fexists(self.path):
            raise IOError('could not find file: {0}'.format(self.file))

        document = QDomDocument()
        if not document.setContent(fread(self.path)):
            raise ParseError('could not initialize QDomDocument')

        # 1) INITIALIZE XML ROOT ELEMENT
        root = document.documentElement()

        # 2) READ KEYS FROM THE DOCUMENT
        key = root.firstChildElement('key')
        while not key.isNull():
            if key.attribute('yfiles.type', '') == 'nodegraphics':
                self.keys['node_key'] = key.attribute('id')
            if key.attribute('yfiles.type', '') == 'edgegraphics':
                self.keys['edge_key'] = key.attribute('id')
            key = key.nextSiblingElement('key')

        # 3) CREATE AN ARBIRARY DIAGRAM
        self.diagram = Diagram(self.path, self.project)
        self.diagram.setSceneRect(QRectF(-Diagram.MaxSize / 2, -Diagram.MaxSize / 2, Diagram.MaxSize, Diagram.MaxSize))
        self.diagram.setItemIndexMethod(Diagram.NoIndex)
        connect(self.diagram.sgnItemAdded, self.project.doAddItem)
        connect(self.diagram.sgnItemRemoved, self.project.doRemoveItem)

        # 4) INITIALIZE GRAPH ELEMENT
        graph = root.firstChildElement('graph')

        # 5) GENERATE NODES
        element = graph.firstChildElement('node')
        while not element.isNull():

            # noinspection PyArgumentList
            QApplication.processEvents()

            node = None
            item = self.itemFromGraphmlNode(element)

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
                    raise ValueError('unknown node with id {0}'.format(element.attribute('id')))

            except Exception as e:
                self.errors.append(e)
            else:
                self.diagram.addItem(node)
                self.diagram.sgnItemAdded.emit(self.diagram, node)
                self.project.guid.update(node.id)
            finally:
                element = element.nextSiblingElement('node')

        # 6) GENERATE EDGES
        element = graph.firstChildElement('edge')
        while not element.isNull():

            # noinspection PyArgumentList
            QApplication.processEvents()

            edge = None
            item = self.itemFromGraphmlNode(element)

            try:

                if item is Item.InclusionEdge:
                    edge = self.buildInclusionEdge(element)
                elif item is Item.InputEdge:
                    edge = self.buildInputEdge(element)
                elif item is Item.MembershipEdge:
                    edge = self.buildMembershipEdge(element)

                if not edge:
                    raise ValueError('unknown edge with id {}'.format(element.attribute('id')))

            except Exception as e:
                self.errors.append(e)
            else:
                self.diagram.addItem(edge)
                self.diagram.sgnItemAdded.emit(self.diagram, edge)
                self.project.guid.update(edge.id)
            finally:
                element = element.nextSiblingElement('edge')

        # 7) CENTER DIAGRAM
        R1 = self.diagram.sceneRect()
        R2 = self.diagram.visibleRect(margin=0)
        moveX = snapF(((R1.right() - R2.right()) - (R2.left() - R1.left())) / 2, Diagram.GridSize)
        moveY = snapF(((R1.bottom() - R2.bottom()) - (R2.top() - R1.top())) / 2, Diagram.GridSize)
        if moveX or moveY:
            collection = [x for x in self.diagram.items() if x.isNode() or x.isEdge()]
            for item in collection:
                # noinspection PyArgumentList
                QApplication.processEvents()
                item.moveBy(moveX, moveY)
            for item in collection:
                # noinspection PyArgumentList
                QApplication.processEvents()
                if item.edge:
                    item.updateEdge()

        # 8) RESIZE DIAGRAM SCENE
        R3 = self.diagram.visibleRect(margin=20)
        size = max(R3.width(), R3.height(), Diagram.MinSize)
        self.diagram.setSceneRect(QRectF(-size / 2, -size / 2, size, size))

        # 7) RETURN GENERATED DIAGRAM
        return self.diagram