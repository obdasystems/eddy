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


from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import QPolygonF, QPainterPath, QPainter
from PyQt5.QtGui import QPixmap, QIcon

from eddy.core.datatypes.misc import Brush, Pen
from eddy.core.datatypes.graphol import Identity, Item
from eddy.core.datatypes.owl import Facet
from eddy.core.functions.misc import first
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import FacetQuotedLabel, NodeLabel
from eddy.core.polygon import Polygon
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

    def __init__(self, width=80, height=40, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        self.background = Polygon(self.createPolygon(88, 48))
        self.selection = Polygon(QRectF(-44, -24, 88, 48))
        self.polygon = Polygon(self.createPolygon(80, 40))
        self.polygonA = Polygon(self.createPolygonA(80, 40), Brush.LightGrey255A, Pen.SolidBlack1Pt)
        self.polygonB = Polygon(self.createPolygonA(80, 40), Brush.White255A, Pen.SolidBlack1Pt)
        self.labelA = NodeLabel(Facet.length.value, pos=self.centerA, editable=False, movable=False, parent=self)
        self.labelB = FacetQuotedLabel('"32"', movable=False, pos=self.centerB, parent=self)
        self.updateTextPos()
        self.updateGeometry()

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
        return self.labelB.text().strip('"')

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.selection.geometry()

    def brushA(self):
        """
        Returns the brush used to paint the shape A of this node.
        :rtype: QBrush
        """
        return self.polygonA.brush()

    def brushB(self):
        """
        Returns the brush used to paint the shape B of this node.
        :rtype: QBrush
        """
        return self.polygonB.brush()

    def centerA(self):
        """
        Returns the center point of polygon A.
        :rtype: QPointF
        """
        return self.boundingRect().center() - QPointF(0, 40 / 4)

    def centerB(self):
        """
        Returns the center point of polygon A.
        :rtype: QPointF
        """
        return self.boundingRect().center() + QPointF(0, 40 / 4)

    @staticmethod
    def compose(facet, value):
        """
        Compose the restriction string.
        :type facet: Facet
        :type value: str
        :return: str
        """
        return '{0}^^"{1}"'.format(facet.value, value.strip().strip('"'))

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
        node.updateGeometry()
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    @staticmethod
    def createPolygon(w, h):
        """
        Returns the initialized polygon according to the given width/height.
        :type w: int
        :type h: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-w / 2 + 10, -h / 2),
            QPointF(+w / 2, -h / 2),
            QPointF(+w / 2 - 10, +h / 2),
            QPointF(-w / 2, +h / 2),
            QPointF(-w / 2 + 10, -h / 2),
        ])

    @staticmethod
    def createPolygonA(w, h):
        """
        Returns the initialized top-half polygon according to the given width/height.
        :type w: int
        :type h: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-w / 2 + 10, -h / 2),
            QPointF(+w / 2, -h / 2),
            QPointF(+w / 2 - 10 / 2, 0),
            QPointF(-w / 2 + 10 / 2, 0),
            QPointF(-w / 2 + 10, -h / 2),
        ])

    @staticmethod
    def createPolygonB(w, h):
        """
        Returns the initialized bottom-half polygon according to the given width/height.
        :type w: int
        :type h: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-w / 2 + 10 / 2, 0),
            QPointF(+w / 2 - 10 / 2, 0),
            QPointF(+w / 2 - 10, +h / 2),
            QPointF(-w / 2, +h / 2),
            QPointF(-w / 2 + 10 / 2, 0),
        ])

    def geometryA(self):
        """
        Returns the geometry of the shape A of this node.
        :rtype: QPolygonF
        """
        return self.polygonA.geometry()

    def geometryB(self):
        """
        Returns the geometry of the shape B of this node.
        :rtype: QPolygonF
        """
        return self.polygonB.geometry()

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        polygonA = self.polygonA.geometry()
        polygonB = self.polygonB.geometry()
        return polygonA[self.IndexBL].y() - polygonB[self.IndexTL].y()

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
            # PAINT THE SHAPES
            polygonA = QPolygonF([
                QPointF(-54 / 2 + 4, -32 / 2),
                QPointF(+54 / 2, -32 / 2),
                QPointF(+54 / 2 - 4 / 2, 0),
                QPointF(-54 / 2 + 4 / 2, 0),
                QPointF(-54 / 2 + 4, -32 / 2),
            ])
            polygonB = QPolygonF([
                QPointF(-54 / 2 + 4 / 2, 0),
                QPointF(+54 / 2 - 4 / 2, 0),
                QPointF(+54 / 2 - 4, +32 / 2),
                QPointF(-54 / 2, +32 / 2),
                QPointF(-54 / 2 + 4 / 2, 0),
            ])
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Pen.SolidBlack1Pt)
            painter.setBrush(Brush.White255A)
            painter.translate(width / 2, height / 2)
            painter.setBrush(Brush.LightGrey255A)
            painter.drawPolygon(polygonA)
            painter.setBrush(Brush.White255A)
            painter.drawPolygon(polygonB)
            # PAINT THE TEXT INSIDE THE SHAPES
            painter.setFont(Font('Arial', 9, Font.Light))
            painter.drawText(QPointF(-19, -5), Facet.length.value)
            painter.drawText(QPointF(-8, 12), '"32"')
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
        painter.setPen(self.selection.pen())
        painter.setBrush(self.selection.brush())
        painter.drawRect(self.selection.geometry())
        # SYNTAX VALIDATION
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawPolygon(self.background.geometry())
        # SHAPE
        painter.setPen(self.polygonA.pen())
        painter.setBrush(self.polygonA.brush())
        painter.drawPolygon(self.polygonA.geometry())
        painter.setPen(self.polygonB.pen())
        painter.setBrush(self.polygonB.brush())
        painter.drawPolygon(self.polygonB.geometry())

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon.geometry())
        return path

    def penA(self):
        """
        Returns the pen used to paint the shape A of this node.
        :rtype: QPen
        """
        return self.polygonA.pen()

    def penB(self):
        """
        Returns the pen used to paint the shape B of this node.
        :rtype: QPen
        """
        return self.polygonB.pen()

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        match = RE_FACET.match(text)
        if match:
            self.labelA.setText((Facet.forValue(match.group('facet')) or Facet.length).value)
            self.labelB.setText('"{0}"'.format(match.group('value')))
            self.updateGeometry()
        else:
            # USE THE OLD VALUE-RESTRICTION PATTERN
            match = RE_VALUE_RESTRICTION.match(text)
            if match:
                self.labelA.setText((Facet.forValue(match.group('facet')) or Facet.length).value)
                self.labelB.setText('"{0}"'.format(match.group('value')))
                self.updateGeometry()

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
        path.addPolygon(self.polygon.geometry())
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

    def updateGeometry(self):
        """
        Update current geometry rect according to the selected facet.
        """
        width = max(self.labelA.width() + 16, self.labelB.width() + 16, 80)
        self.background.setGeometry(self.createPolygon(width + 8, 48))
        self.selection.setGeometry(QRectF(-(width + 8) / 2, -24, width + 8, 48))
        self.polygon.setGeometry(self.createPolygon(width, 40))
        self.polygonA.setGeometry(self.createPolygonA(width, 40))
        self.polygonB.setGeometry(self.createPolygonB(width, 40))
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
        polygonA = self.polygonA.geometry()
        polygonB = self.polygonB.geometry()
        return polygonA[self.IndexTR].x() - polygonB[self.IndexBL].x()