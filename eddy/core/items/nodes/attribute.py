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


from PyQt5 import QtCore
from PyQt5 import QtGui

from eddy.core.datatypes.graphol import Identity, Item, Special
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.polygon import Polygon


class AttributeNode(AbstractNode):
    """
    This class implements the 'Attribute' node.
    """
    DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    Identities = {Identity.Attribute}
    Type = Item.AttributeNode

    def __init__(self, width=20, height=20, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super(AttributeNode, self).__init__(**kwargs)
        brush = brush or AttributeNode.DefaultBrush
        pen = AttributeNode.DefaultPen
        self.fpolygon = Polygon(QtGui.QPainterPath())
        self.background = Polygon(QtCore.QRectF(-14, -14, 28, 28))
        self.selection = Polygon(QtCore.QRectF(-14, -14, 28, 28))
        self.polygon = Polygon(QtCore.QRectF(-10, -10, 20, 20), brush, pen)
        self.label = NodeLabel(template='attribute', pos=lambda: self.center() - QtCore.QPointF(0, 22), parent=self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

    #############################################
    #   INTERFACE
    #################################

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
        node = diagram.factory.create(self.type(), **{
            'id': self.id,
            'brush': self.brush(),
            'height': self.height(),
            'width': self.width()
        })
        node.setPos(self.pos())
        node.setText(self.text())
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    def definition(self):
        """
        Returns the list of nodes which contribute to the definition of this very node.
        :rtype: set
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
        return set(self.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.geometry().height()

    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Attribute

    def isFunctional(self):
        """
        Returns True if the predicate represented by this node is functional, else False.
        :rtype: bool
        """
        try:
            return self.project.meta(self.type(), self.text())['functional']
        except (AttributeError, KeyError):
            return False

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
        painter.drawRect(self.selection.geometry())
        # SYNTAX VALIDATION
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawEllipse(self.background.geometry())
        # ITEM SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawEllipse(self.polygon.geometry())
        # FUNCTIONALITY
        painter.setPen(self.fpolygon.pen())
        painter.setBrush(self.fpolygon.brush())
        painter.drawPath(self.fpolygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addEllipse(self.polygon.geometry())
        return path

    def setFunctional(self, functional):
        """
        Set the functional property of the predicate represented by this node.
        :type functional: bool
        """
        meta = self.project.meta(self.type(), self.text())
        meta['functional'] = bool(functional)
        self.project.addMeta(self.type(), self.text(), meta)
        for node in self.project.predicates(self.type(), self.text()):
            node.updateNode(functional=functional, selected=node.isSelected())

    def setIdentity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        self.label.setText(text)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QtCore.QPointF
        """
        self.label.setPos(pos)

    def shape(self):
        """
        Returns the shape of this item as a QtGui.QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addEllipse(self.polygon.geometry())
        return path

    def special(self):
        """
        Returns the special type of this node.
        :rtype: Special
        """
        return Special.forLabel(self.text())

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.label.pos()

    def updateNode(self, functional=None, **kwargs):
        """
        Update the current node.
        :type functional: bool
        """
        if functional is None:
            functional = self.isFunctional()

        # FUNCTIONAL POLYGON (SHAPE)
        path1 = QtGui.QPainterPath()
        path1.addEllipse(self.polygon.geometry())
        path2 = QtGui.QPainterPath()
        path2.addEllipse(QtCore.QRectF(-7, -7, 14, 14))
        self.fpolygon.setGeometry(path1.subtracted(path2))

        # FUNCTIONAL POLYGON (PEN & BRUSH)
        pen = QtGui.QPen(QtCore.Qt.NoPen)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if functional:
            pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            brush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
        self.fpolygon.setPen(pen)
        self.fpolygon.setBrush(brush)

        # SELECTION + BACKGROUND + CACHE REFRESH
        super(AttributeNode, self).updateNode(**kwargs)

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon.geometry().width()