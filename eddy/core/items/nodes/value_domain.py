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


from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPainterPath
from PyQt5.QtGui import QPen, QBrush, QColor

from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.owl import Datatype
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.polygon import Polygon


class ValueDomainNode(AbstractNode):
    """
    This class implements the 'Value-Domain' node.
    """
    DefaultBrush = QBrush(QColor(252, 252, 252, 255))
    DefaultPen = QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    Identities = {Identity.ValueDomain}
    Type = Item.ValueDomainNode

    def __init__(self, width=90, height=40, brush=None, **kwargs):
        """
        Initialize the ValueDomain node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super(ValueDomainNode, self).__init__(**kwargs)
        brush = brush or ValueDomainNode.DefaultBrush
        pen = ValueDomainNode.DefaultPen
        self.background = Polygon(QRectF(-49, -24, 98, 48))
        self.selection = Polygon(QRectF(-49, -24, 98, 48))
        self.polygon = Polygon(QRectF(-45, -20, 90, 40), brush, pen)
        self.label = NodeLabel(Datatype.string.value, pos=self.center, editable=False, movable=False, parent=self)
        self.updateNode()
        self.updateTextPos()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def datatype(self):
        """
        Returns the datatype associated with this node.
        :rtype: Datatype
        """
        return Datatype.forValue(self.text())

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
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

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.geometry().height()

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
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawRoundedRect(self.background.geometry(), 8, 8)
        # SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawRoundedRect(self.polygon.geometry(), 8, 8)

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRoundedRect(self.polygon.geometry(), 8, 8)
        return path

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        datatype = Datatype.forValue(text) or Datatype.string
        self.label.setText(datatype.value)
        self.updateNode()

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRoundedRect(self.polygon.geometry(), 8, 8)
        return path

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

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)

    def updateNode(self, *args, **kwargs):
        """
        Update the current node.
        """
        width = max(self.label.width() + 16, 90)
        self.polygon.setGeometry(QRectF(-width / 2, -20, width, 40))
        self.background.setGeometry(QRectF(-(width + 8) / 2, -24, width + 8, 48))
        self.selection.setGeometry(QRectF(-(width + 8) / 2, -24, width + 8, 48))
        self.updateTextPos()
        self.updateEdges()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon.geometry().width()