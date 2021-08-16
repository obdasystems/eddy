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


from PyQt5 import QtCore
from PyQt5 import QtGui

from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.functions.misc import first
from eddy.core.items.common import Polygon
from eddy.core.items.nodes.common.base import AbstractNode


class PropertyAssertionNode(AbstractNode):
    """
    This class implements the 'Property Assertion' node.
    """
    DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    Identities = {Identity.RoleInstance, Identity.AttributeInstance, Identity.Neutral}
    Type = Item.PropertyAssertionNode

    def __init__(self, width=52, height=30, brush=None, inputs=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        :type inputs: DistinctList
        """
        super().__init__(**kwargs)
        brush = PropertyAssertionNode.DefaultBrush
        pen = PropertyAssertionNode.DefaultPen
        self.inputs = inputs or DistinctList()
        self.background = Polygon(QtCore.QRectF(-34, -19, 68, 38))
        self.selection = Polygon(QtCore.QRectF(-34, -19, 68, 38))
        self.polygon = Polygon(QtCore.QRectF(-26, -15, 52, 30), brush, pen)

    #############################################
    #   INTERFACE
    #################################

    def addEdge(self, edge):
        """
        Add the given edge to the current node.
        :type edge: AbstractEdge
        """
        super().addEdge(edge)
        if edge.type() is Item.InputEdge and edge.target is self:
            self.inputs.append(edge.id)
            edge.updateEdge()

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QtCore.QRectF
        """
        return self.selection.geometry()

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        kwargs = {'id': self.id, 'height': self.height(), 'width': self.width()}
        node = diagram.factory.create(self.type(), **kwargs)
        node.setPos(self.pos())
        return node

    def definition(self):
        """
        Returns the list of nodes which contribute to the definition of this very node.
        :rtype: set
        """
        return set(self.incomingNodes(filter_on_edges=lambda x: x.type() is Item.InputEdge))

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.geometry().height()

    def identify(self):
        """
        Perform the node identification step for this PropertyAssertion node.
        The identity of the node is calculated as follows:

        * If the node is targeting a Role with a membership edge => Identity == RoleInstance
        * If the node is targeting an Attribute with a membership edge => Identity == AttributeInstance

        else

        * If the node has 2 individuals as inputs => Identity == RoleInstance
        * If the node has 1 individual and 1 value as inputs => Identity == AttributeInstance

        In both the cases, whether we establish or not an identity for this node,
        we mark it for EXCLUSION from the STRONG and WEAK sets. This is due to the
        PropertyAssertion node being used to perform assertions at ABox level
        while every other node in the graph is used at TBox level. Additionally we
        discard the inputs of this node from the STRONG set because they are either
        Individual or Value nodes and they are not needed to compute the final identity
        for all the WEAK nodes being examined during the identification process.
        :rtype: tuple
        """
        f1 = lambda x: x.type() is Item.MembershipEdge
        f2 = lambda x: x.type() in {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}
        f3 = lambda x: x.type() is Item.InputEdge
        f4 = lambda x: x.type() is Item.IndividualNode
        f5 = lambda x: Identity.RoleInstance if x.identity() is Identity.Role else Identity.AttributeInstance
        f6 = lambda x: x.identity() is Identity.Value
        # MODIFIED TO MANAGE SEPARATION OF INDIVIDUALS AND VALUES
        f7 = lambda x: x.type() is Item.LiteralNode
        outgoing = self.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2)
        incomingIndividuals = self.incomingNodes(filter_on_edges=f3, filter_on_nodes=f4)
        incomingValues = self.incomingNodes(filter_on_edges=f3, filter_on_nodes=f7)
        incoming = incomingIndividuals.union(incomingValues)

        computed = Identity.Neutral
        # 1) USE MEMBERSHIP EDGE
        identities = set(map(f5, outgoing))
        if identities:
            computed = first(identities)
            if len(identities) > 1:
                computed = Identity.Unknown
        # 2) USE INPUT EDGES
        if computed is Identity.Neutral and len(incoming) >= 2:
            computed = Identity.RoleInstance
            if sum(map(f6, incoming)):
                computed = Identity.AttributeInstance
        self.setIdentity(computed)
        return set(), incoming, {self}

    def inputNodes(self, filter_on_nodes=lambda x: True):
        """
        Returns the list of nodes connected via an input edge
        ordered according to the input edge label.

        :type filter_on_nodes: callable
        :rtype: list
        """
        f1 = lambda e: e.id in self.inputs
        f2 = lambda e: self.inputs.index(e.id)
        return [x for x in [e.other(self) for e in sorted(filter(f1, self.edges), key=f2) \
                            if e.target is self] if filter_on_nodes(x)]

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the diagram.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        # SET THE RECT THAT NEEDS TO BE REPAINTED
        painter.setClipRect(option.exposedRect)
        # SELECTION AREA
        painter.setPen(self.selection.pen())
        painter.setBrush(self.selection.brush())
        painter.drawRoundedRect(self.selection.geometry(), 16, 16)
        # SYNTAX VALIDATION
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawRoundedRect(self.background.geometry(), 16, 16)
        # SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawRoundedRect(self.polygon.geometry(), 16, 16)

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addRoundedRect(self.polygon.geometry(), 16, 16)
        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addRoundedRect(self.polygon.geometry(), 16, 16)
        return path

    def removeEdge(self, edge):
        """
        Remove the given edge from the current node.
        :type edge: AbstractEdge
        """
        super().removeEdge(edge)
        self.inputs.remove(edge.id)
        for i in self.inputs:
            try:
                edge = self.diagram.edge(i)
                edge.updateEdge()
            except KeyError:
                pass

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        pass

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        pass

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        pass

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon.geometry().width()
