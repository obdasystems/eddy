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


from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainterPath, QPainter, QIcon

from eddy.core.datatypes.misc import Brush, Pen
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.items.nodes.common.base import AbstractNode


class PropertyAssertionNode(AbstractNode):
    """
    This class implements the 'Property Assertion' node.
    """
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
        self._identity = Identity.Neutral
        super().__init__(**kwargs)
        self.brush = Brush.White255A
        self.pen = Pen.SolidBlack1Pt
        self.inputs = inputs or DistinctList()
        self.polygon = self.createPolygon(52, 30)
        self.background = self.createBackground(60, 38)
        self.selection = self.createSelection(60, 38)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return self._identity

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        if identity not in self.Identities:
            identity = Identity.Unknown
        self._identity = identity

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
        :rtype: QRectF
        """
        return self.selection

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        kwargs = {'id': self.id, 'height': self.height(), 'width': self.width()}
        node = diagram.factory.create(self.type(), **kwargs)
        node.setPos(self.pos())
        return node

    @staticmethod
    def createBackground(width, height):
        """
        Returns the initialized background polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: QRectF
        """
        return QRectF(-width / 2, -height / 2, width, height)

    @staticmethod
    def createPolygon(width, height):
        """
        Returns the initialized polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: QRectF
        """
        return QRectF(-width / 2, -height / 2, width, height)

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.height()

    @classmethod
    def icon(cls, width, height, **kwargs):
        """
        Returns an icon of this item suitable for the palette.
        :type width: int
        :type height: int
        :rtype: QIcon
        """
        icon = QIcon()
        for i in (1.0, 2.0):
            # CREATE THE PIXMAP
            pixmap = QPixmap(width * i, height * i)
            pixmap.setDevicePixelRatio(i)
            pixmap.fill(Qt.transparent)
            # PAINT THE SHAPE
            polygon = cls.createPolygon(46, 30)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Pen.SolidBlack1Pt)
            painter.setBrush(Brush.White255A)
            painter.translate(width / 2, height / 2)
            painter.drawRoundedRect(polygon, 14, 14)
            painter.end()
            # ADD THE PIXMAP TO THE ICON
            icon.addPixmap(pixmap)
        return icon

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
        painter.setPen(self.selectionPen)
        painter.setBrush(self.selectionBrush)
        painter.drawRect(self.background)
        # SYNTAX VALIDATION
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.backgroundPen)
        painter.setBrush(self.backgroundBrush)
        painter.drawRoundedRect(self.background, 16, 16)
        # SHAPE
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawRoundedRect(self.polygon, 16, 16)

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRoundedRect(self.polygon, 16, 16)
        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRoundedRect(self.polygon, 16, 16)
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
        return self.polygon.width()