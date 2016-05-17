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


from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPolygonF, QPainterPath, QPainter
from PyQt5.QtGui import QPen, QColor, QPixmap, QBrush

from eddy.core.datatypes.graphol import Identity, Item
from eddy.core.datatypes.owl import Facet
from eddy.core.functions.misc import cutL, first
from eddy.core.functions.misc import cutR
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import FacetNodeQuotedLabel
from eddy.core.qt import Font
from eddy.core.regex import RE_FACET, RE_VALUE_RESTRICTION


class FacetNode(AbstractNode):
    """
    This class implements the 'Facet' node.
    """
    IndexTL = 0
    IndexTR = 1
    IndexBR = 2
    IndexBL = 3
    IndexEE = 4

    Identities = {Identity.Facet}
    Type = Item.FacetNode
    MinHeight = 40
    MinWidth = 80
    Skew = 10

    def __init__(self, width=MinWidth, height=MinHeight, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        self.brushA = QBrush(QColor(222, 222, 222))
        self.brushB = QBrush(QColor(252, 252, 252))
        self.pen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)
        self.polygon = self.createPolygon(self.MinWidth, self.MinHeight)
        self.polygonA = self.createPolygonA(self.MinWidth, self.MinHeight)
        self.polygonB = self.createPolygonB(self.MinWidth, self.MinHeight)
        self.background = self.createBackground(self.MinWidth + 8, self.MinHeight + 8)
        self.selection = self.createSelection(self.MinWidth + 8, self.MinHeight + 8)

        self.labelA = FacetNodeQuotedLabel(template=Facet.length.value,
                                           editable=False,
                                           movable=False,
                                           pos=self.centerA,
                                           parent=self)

        self.labelB = FacetNodeQuotedLabel(template='"32"',
                                           movable=False,
                                           pos=self.centerB,
                                           parent=self)

        self.updateTextPos()
        self.updateLayout()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def datatype(self):
        """
        Returns the datatype this facet is restricting, or None if the node is isolated.
        :rtype: Datatype
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.DatatypeRestrictionNode
        f3 = lambda x: x.type() is Item.ValueDomainNode
        outgoing = first(self.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if outgoing:
            incoming = first(outgoing.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            if incoming:
                return incoming.datatype
        return None

    @property
    def facet(self):
        """
        Returns the facet associated with this node.
        :rtype: Facet
        """
        return Facet.forValue(self.labelA.text())

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Facet

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    @property
    def value(self):
        """
        Returns the value of this facet node.
        :rtype: str
        """
        return cutR(cutL(self.labelB.text(), '"'), '"')

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.selection

    def centerA(self):
        """
        Returns the center point of polygon A.
        :rtype: QPointF
        """
        return self.boundingRect().center() - QPointF(0, self.MinHeight / 4)

    def centerB(self):
        """
        Returns the center point of polygon A.
        :rtype: QPointF
        """
        return self.boundingRect().center() + QPointF(0, self.MinHeight / 4)

    @staticmethod
    def compose(facet, value):
        """
        Compose the restriction string.
        :type facet: Facet
        :type value: str
        :return: str
        """
        return '{0}^^"{1}"'.format(facet.value, cutR(cutL(value.strip(), '"'), '"'))

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        kwargs = {'id': self.id, 'height': self.height(), 'width': self.width()}
        node = diagram.factory.create(self.type(), **kwargs)
        node.setPos(self.pos())
        node.setText(self.text())
        node.updateLayout()
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
        return QPolygonF([
            QPointF(-width / 2 + FacetNode.Skew, -height / 2),  # 0
            QPointF(+width / 2, -height / 2),                   # 1
            QPointF(+width / 2 - FacetNode.Skew, +height / 2),  # 2
            QPointF(-width / 2, +height / 2),                   # 3
            QPointF(-width / 2 + FacetNode.Skew, -height / 2),  # 4
        ])

    @staticmethod
    def createPolygon(width, height):
        """
        Returns the initialized polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-width / 2 + FacetNode.Skew, -height / 2),  # 0
            QPointF(+width / 2, -height / 2),                   # 1
            QPointF(+width / 2 - FacetNode.Skew, +height / 2),  # 2
            QPointF(-width / 2, +height / 2),                   # 3
            QPointF(-width / 2 + FacetNode.Skew, -height / 2),  # 4
        ])

    @staticmethod
    def createPolygonA(width, height):
        """
        Returns the initialized top-half polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-width / 2 + FacetNode.Skew, -height / 2),  # 0
            QPointF(+width / 2, -height / 2),                   # 1
            QPointF(+width / 2 - FacetNode.Skew / 2, 0),        # 2
            QPointF(-width / 2 + FacetNode.Skew / 2, 0),        # 3
            QPointF(-width / 2 + FacetNode.Skew, -height / 2),  # 4
        ])

    @staticmethod
    def createPolygonB(width, height):
        """
        Returns the initialized bottom-half polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-width / 2 + FacetNode.Skew / 2, 0),        # 0
            QPointF(+width / 2 - FacetNode.Skew / 2, 0),        # 1
            QPointF(+width / 2 - FacetNode.Skew, +height / 2),  # 2
            QPointF(-width / 2, +height / 2),                   # 3
            QPointF(-width / 2 + FacetNode.Skew / 2, 0),        # 4
        ])

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygonA[self.IndexBL].y() - self.polygonB[self.IndexTL].y()

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        # INITIALIZATION
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        w = 54
        h = 32
        s = 4

        polygonA = QPolygonF([
            QPointF(-w / 2 + s, -h / 2),  # 0
            QPointF(+w / 2, -h / 2),      # 1
            QPointF(+w / 2 - s / 2, 0),   # 2
            QPointF(-w / 2 + s / 2, 0),   # 3
            QPointF(-w / 2 + s, -h / 2),  # 4
        ])

        polygonB = QPolygonF([
            QPointF(-w / 2 + s / 2, 0),   # 0
            QPointF(+w / 2 - s / 2, 0),   # 1
            QPointF(+w / 2 - s, +h / 2),  # 2
            QPointF(-w / 2, +h / 2),      # 3
            QPointF(-w / 2 + s / 2, 0),   # 4
        ])

        # ITEM SHAPE
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(222, 222, 222))
        painter.drawPolygon(polygonA)
        painter.setBrush(QBrush(QColor(252, 252, 252)))
        painter.drawPolygon(polygonB)
        # TEXT WITHIN THE SHAPE
        painter.setFont(Font('Arial', 9, Font.Light))
        painter.drawText(QPointF(-19, -5), Facet.length.value)
        painter.drawText(QPointF(-8, 12), '"32"')
        return pixmap

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
        painter.drawRect(self.selection)
        # SYNTAX VALIDATION
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.backgroundPen)
        painter.setBrush(self.backgroundBrush)
        painter.drawPolygon(self.background)
        # SHAPE
        painter.setPen(self.pen)
        painter.setBrush(self.brushA)
        painter.drawPolygon(self.polygonA)
        painter.setBrush(self.brushB)
        painter.drawPolygon(self.polygonB)

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon)
        return path

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        match = RE_FACET.match(text)
        if match:
            self.labelA.setText((Facet.forValue(match.group('facet')) or Facet.length).value)
            self.labelB.setText('"{0}"'.format(match.group('value')))
            self.updateLayout()
        else:
            # USE THE OLD VALUE-RESTRICTION PATTERN
            match = RE_VALUE_RESTRICTION.match(text)
            if match:
                self.labelA.setText((Facet.forValue(match.group('facet')) or Facet.length).value)
                self.labelB.setText('"{0}"'.format(match.group('value')))
                self.updateLayout()

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
        path = QPainterPath()
        path.addPolygon(self.polygon)
        return path

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.compose(self.facet, self.value)

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def updateLayout(self):
        """
        Update current shape rect according to the selected datatype.
        """
        width = max(self.labelA.width() + 16,
                    self.labelB.width() + 16,
                    self.MinWidth)

        self.polygon = self.createPolygon(width, self.MinHeight)
        self.polygonA = self.createPolygonA(width, self.MinHeight)
        self.polygonB = self.createPolygonB(width, self.MinHeight)
        self.background = self.createBackground(width + 8, self.MinHeight + 8)
        self.selection = self.createSelection(width + 8, self.MinHeight + 8)
        self.updateTextPos()
        self.updateEdges()

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.labelA.updatePos()
        self.labelB.updatePos()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygonA[self.IndexTR].x() - self.polygonB[self.IndexBL].x()