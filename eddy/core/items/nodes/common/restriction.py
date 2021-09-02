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


from abc import ABCMeta

from PyQt5 import QtCore
from PyQt5 import QtGui

from eddy.core.datatypes.graphol import Item, Identity, Restriction, Special
from eddy.core.functions.misc import first
from eddy.core.items.common import Polygon
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.regex import RE_CARDINALITY


class RestrictionNode(AbstractNode):
    """
    This is the base class for all the Restriction nodes.
    """
    __metaclass__ = ABCMeta

    DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)

    def __init__(self, width=20, height=20, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        brush = brush or RestrictionNode.DefaultBrush
        pen = RestrictionNode.DefaultPen
        self.background = Polygon(QtCore.QRectF(-14, -14, 28, 28))
        self.selection = Polygon(QtCore.QRectF(-14, -14, 28, 28))
        self.polygon = Polygon(QtCore.QRectF(-10, -10, 20, 20), brush, pen)
        self.label = NodeLabel(Restriction.Exists.toString(),
           pos=lambda: self.center() - QtCore.QPointF(0, 22),
           editable=False, parent=self)

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QtCore.QRectF
        """
        return self.selection.geometry()

    def cardinality(self, *args):
        """
        Returns the cardinality of the node.
        :rtype: T <= int|dict
        """
        cardinality = {'min': None, 'max': None}
        match = RE_CARDINALITY.match(self.text())
        if match:
            if match.group('min') != '-':
                cardinality['min'] = int(match.group('min'))
            if match.group('max') != '-':
                cardinality['max'] = int(match.group('max'))
        if args:
            cardinality = {k:v for k, v in cardinality.items() if k in args}
            if len(cardinality) == 1:
                cardinality = first(cardinality.values())
        return cardinality

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        node = diagram.factory.create(self.type(), **{
            'id': self.id,
            'height': self.height(),
            'width': self.width()
        })
        node.setPos(self.pos())
        node.setText(self.text())
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.geometry().height()

    def isRestrictionQualified(self):
        """
        Returna True if this node expresses a qualified restriction (exists R.C), False otherwise.
        :rtype: bool
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() in {Identity.Concept, Identity.Role}
        f3 = lambda x: x.identity() in {Identity.Attribute, Identity.ValueDomain}
        f4 = lambda x: x.identity() is Identity.Concept
        if self.restriction() in {Restriction.Cardinality, Restriction.Exists, Restriction.Forall}:
            # CHECK FOR ROLE QUALIFIED RESTRICTION
            collection = self.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
            if len(collection) >= 2:
                node = first(collection, filter_on_item=f4)
                if node and Special.valueOf(node.text()) is not Special.Top:
                    return True
            # CHECK FOR ATTRIBUTE QUALIFIED RESTRICTION
            return len(self.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)) >= 2
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
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawRect(self.background.geometry())
        # ITEM SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawRect(self.polygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addRect(self.polygon.geometry())
        return path

    def restriction(self):
        """
        Returns the restriction type of the node.
        :rtype: Restriction
        """
        return Restriction.forLabel(self.text())

    def setText(self, text):
        """
        Set the label text.
        Will additionally parse the given value checking for a consistent restriction type.
        :type text: str
        """
        restriction = Restriction.forLabel(text)
        if not restriction:
            text = Restriction.Exists.toString()
        self.label.setText(text)

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

    def shape(self, *args, **kwargs):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addRect(self.polygon.geometry())
        return path

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def textPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
        """
        return self.label.pos()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon.geometry().width()

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)
