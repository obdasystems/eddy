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


from abc import ABCMeta, abstractmethod

from PyQt5 import QtCore
from PyQt5 import QtGui

from eddy.core.datatypes.graphol import Item
from eddy.core.items.common import Polygon
from eddy.core.items.nodes.common.base import AbstractNode


class OperatorNode(AbstractNode):
    """
    This is the base class for operator nodes.
    """
    __metaclass__ = ABCMeta

    DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)

    IndexML = 0
    IndexBL = 1
    IndexBR = 2
    IndexMR = 3
    IndexTR = 4
    IndexTL = 5
    IndexEE = 6

    def __init__(self, width=50, height=30, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)

        createPolygon = lambda x, y: QtGui.QPolygonF([
            QtCore.QPointF(-x / 2, 0),
            QtCore.QPointF(-x / 2 + 6, +y / 2),
            QtCore.QPointF(+x / 2 - 6, +y / 2),
            QtCore.QPointF(+x / 2, 0),
            QtCore.QPointF(+x / 2 - 6, -y / 2),
            QtCore.QPointF(-x / 2 + 6, -y / 2),
            QtCore.QPointF(-x / 2, 0),
        ])

        self.background = Polygon(createPolygon(58, 38))
        self.selection = Polygon(createPolygon(58, 38))
        self.polygon = Polygon(createPolygon(50, 30), brush or OperatorNode.DefaultBrush, OperatorNode.DefaultPen)

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QtCore.QRectF
        """
        path = QtGui.QPainterPath()
        path.addPolygon(self.selection.geometry())
        return path.boundingRect()

    @abstractmethod
    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        pass

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
        polygon = self.polygon.geometry()
        return polygon[self.IndexBL].y() - polygon[self.IndexTL].y()

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
        painter.drawPolygon(self.selection.geometry())
        # SYNTAX VALIDATION
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawPolygon(self.background.geometry())
        # ITEM SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawPolygon(self.polygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addPolygon(self.polygon.geometry())
        return path

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

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addPolygon(self.polygon.geometry())
        return path

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
        polygon = self.polygon.geometry()
        return polygon[self.IndexMR].x() - polygon[self.IndexML].x()