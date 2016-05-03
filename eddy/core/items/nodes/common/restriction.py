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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QColor, QPainterPath, QPen, QBrush

from eddy.core.datatypes.graphol import Restriction
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.regex import RE_CARDINALITY


class RestrictionNode(AbstractNode):
    """
    This is the base class for all the Restriction nodes.
    """
    __metaclass__ = ABCMeta

    def __init__(self, width=20, height=20, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        self.brush = brush or QBrush(QColor(252, 252, 252))
        self.pen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)
        self.polygon = self.createPolygon(20, 20)
        self.background = self.createBackground(28, 28)
        self.selection = self.createSelection(28, 28)
        self.label = NodeLabel(template='attribute',
                               editable=False,
                               pos=lambda: self.center() - QPointF(0, 22),
                               parent=self)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def cardinality(self):
        """
        Returns the cardinality of the node.
        :rtype: dict
        """
        cardinality = {'min': None, 'max': None}
        match = RE_CARDINALITY.match(self.text())
        if match:
            if match.group('min') != '-':
                cardinality['min'] = int(match.group('min'))
            if match.group('max') != '-':
                cardinality['max'] = int(match.group('max'))
        return cardinality

    @property
    @abstractmethod
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        pass

    @identity.setter
    @abstractmethod
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    @property
    def restriction(self):
        """
        Returns the restriction type of the node.
        :rtype: Restriction
        """
        return Restriction.forLabel(self.text())

    #############################################
    #   INTERFACE
    #################################

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
        node.setText(self.text())
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
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
    @abstractmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        pass

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the diagram.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        # SELECTION AREA
        painter.setPen(self.selectionPen)
        painter.setBrush(self.selectionBrush)
        painter.drawRect(self.selection)
        # SYNTAX VALIDATION
        painter.setPen(self.backgroundPen)
        painter.setBrush(self.backgroundBrush)
        painter.drawRect(self.background)
        # SHAPE
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawRect(self.polygon)

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.polygon)
        return path

    def setText(self, text):
        """
        Set the label text.
        Will additionally parse the given value checking for a consistent restriction type.
        :type text: str
        """
        restriction = Restriction.forLabel(text)
        if not restriction:
            text = Restriction.Exists.format()
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
        path = QPainterPath()
        path.addRect(self.polygon)
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
        return self.polygon.width()

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)