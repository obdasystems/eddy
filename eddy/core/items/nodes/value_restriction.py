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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPolygonF, QPainterPath, QPainter
from PyQt5.QtGui import QPixmap, QIcon

from eddy.core.datatypes.graphol import Identity, Item
from eddy.core.datatypes.misc import Brush, Pen
from eddy.core.datatypes.owl import Datatype, Facet
from eddy.core.functions.misc import cutL, cutR, first
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.qt import Font
from eddy.core.regex import RE_VALUE_RESTRICTION


class ValueRestrictionNode(AbstractNode):
    """
    This class implements the 'Value-Restriction' node.
    """
    IndexTR = 0
    IndexTL = 1
    IndexBL = 2
    IndexBR = 3
    IndexRT = 4
    IndexEE = 5

    Identities = {Identity.ValueDomain}
    Type = Item.ValueRestrictionNode
    MinHeight = 50
    MinWidth = 180

    def __init__(self, width=MinWidth, height=MinHeight, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        self.brush = brush or Brush.White255A
        self.pen = Pen.SolidBlack1Pt
        self.polygon = self.createPolygon(self.MinWidth, self.MinHeight)
        self.fold = self.createFold(self.polygon, self.IndexTR, self.IndexRT)
        self.background = self.createBackground(self.MinWidth + 8, self.MinHeight + 8)
        self.selection = self.createSelection(self.MinWidth + 8, self.MinHeight + 8)
        self.label = NodeLabel(template='xsd:length "32"^^xsd:string',
                               editable=False,
                               movable=False,
                               pos=self.center,
                               parent=self)
        self.updateTextPos()
        self.updateLayout()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def constrained(self):
        """
        Tells whether the datatype of this restriction is constrained by graph composition.
        :rtype: bool
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.DatatypeRestrictionNode
        f3 = lambda x: x.type() is Item.ValueDomainNode
        xx = first(self.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if xx:
            return first(xx.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)) is not None
        return False

    @property
    def datatype(self):
        """
        Returns the datatype associated with this node.
        :rtype: Datatype
        """
        match = RE_VALUE_RESTRICTION.match(self.text())
        if match:
            return Datatype.forValue(match.group('datatype'))
        return None

    @property
    def facet(self):
        """
        Returns the facet associated with this node.
        :rtype: Facet
        """
        match = RE_VALUE_RESTRICTION.match(self.text())
        if match:
            return Facet.forValue(match.group('facet'))
        return None

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.ValueDomain

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
        Returns the value of the restriction.
        :rtype: str
        """
        match = RE_VALUE_RESTRICTION.match(self.text())
        if match:
            return match.group('value')
        return ''

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.selection

    @staticmethod
    def compose(facet, value, datatype):
        """
        Compose the restriction string.
        :type facet: Facet
        :type value: str
        :type datatype: Datatype
        :return: str
        """
        return '{} "{}"^^{}'.format(facet.value, cutR(cutL(value.strip(), '"'), '"'), datatype.value)

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        kwargs = {'id': self.id, 'brush': self.brush, 'height': self.height(), 'width': self.width()}
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
    def createFold(polygon, IndexTR, IndexRT):
        """
        Returns the initialized fold polygon.
        :type polygon: QPolygonF
        :type IndexTR: int
        :type IndexRT: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(polygon[IndexTR].x(), polygon[IndexTR].y()),
            QPointF(polygon[IndexTR].x(), polygon[IndexTR].y() + 12),
            QPointF(polygon[IndexRT].x(), polygon[IndexRT].y()),
            QPointF(polygon[IndexTR].x(), polygon[IndexTR].y()),
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
            QPointF(+(width / 2) - 12, -(height / 2)),  # 0
            QPointF(-(width / 2), -(height / 2)),       # 1
            QPointF(-(width / 2), +(height / 2)),       # 2
            QPointF(+(width / 2), +(height / 2)),       # 3
            QPointF(+(width / 2), -(height / 2) + 12),  # 4
            QPointF(+(width / 2) - 12, -(height / 2)),  # 5
        ])

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon[self.IndexBL].y() - self.polygon[self.IndexTL].y()

    @classmethod
    def icon(cls, width, height, **kwargs):
        """
        Returns an icon of this item suitable for the palette.
        :type width: int
        :type height: int
        :rtype: QIcon
        """
        # LOW RESOLUTION PIXMAP
        pixmap1 = QPixmap(width, height)
        pixmap1.setDevicePixelRatio(1.0)
        pixmap1.fill(Qt.transparent)
        polygonA = QPolygonF([
            QPointF(+27 - 10, -17),  # 0
            QPointF(-27, -17),       # 1
            QPointF(-27, +17),       # 2
            QPointF(+27, +17),       # 3
            QPointF(+27, -17 + 10),  # 4
            QPointF(+27 - 10, -17),  # 5
        ])
        polygonB = QPolygonF([
            QPointF(polygonA[cls.IndexTR].x(), polygonA[cls.IndexTR].y()),
            QPointF(polygonA[cls.IndexTR].x(), polygonA[cls.IndexTR].y() + 10),
            QPointF(polygonA[cls.IndexRT].x(), polygonA[cls.IndexRT].y()),
            QPointF(polygonA[cls.IndexTR].x(), polygonA[cls.IndexTR].y()),
        ])
        painter = QPainter(pixmap1)
        painter.setPen(Pen.SolidBlack1Pt)
        painter.setBrush(Brush.White255A)
        painter.translate(width / 2, height / 2)
        painter.drawPolygon(polygonA)
        painter.drawPolygon(polygonB)
        painter.setFont(Font('Arial', 10, Font.Light))
        painter.drawText(polygonA.boundingRect(), Qt.AlignCenter, 'value\nrestriction')
        painter.end()
        # HIGH RESOLUTION PIXMAP
        pixmap2 = QPixmap(width * 2, height * 2)
        pixmap2.setDevicePixelRatio(2.0)
        pixmap2.fill(Qt.transparent)
        polygonA = QPolygonF([
            QPointF(+27 - 10, -17),  # 0
            QPointF(-27, -17),       # 1
            QPointF(-27, +17),       # 2
            QPointF(+27, +17),       # 3
            QPointF(+27, -17 + 10),  # 4
            QPointF(+27 - 10, -17),  # 5
        ])
        polygonB = QPolygonF([
            QPointF(polygonA[cls.IndexTR].x(), polygonA[cls.IndexTR].y()),
            QPointF(polygonA[cls.IndexTR].x(), polygonA[cls.IndexTR].y() + 10),
            QPointF(polygonA[cls.IndexRT].x(), polygonA[cls.IndexRT].y()),
            QPointF(polygonA[cls.IndexTR].x(), polygonA[cls.IndexTR].y()),
        ])
        painter = QPainter(pixmap2)
        painter.setPen(Pen.SolidBlack1Pt)
        painter.setBrush(Brush.White255A)
        painter.translate(width, height)
        painter.drawPolygon(polygonA)
        painter.drawPolygon(polygonB)
        painter.setFont(Font('Arial', 20, Font.Light))
        painter.drawText(polygonA.boundingRect(), Qt.AlignCenter, 'value\nrestriction')
        painter.end()
        # BUILD THE ICON
        icon = QIcon()
        icon.addPixmap(pixmap1)
        icon.addPixmap(pixmap2)
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
        painter.drawRect(self.selection)
        # SYNTAX VALIDATION
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.backgroundPen)
        painter.setBrush(self.backgroundBrush)
        painter.drawRect(self.background)
        # SHAPE
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawPolygon(self.polygon)
        painter.drawPolygon(self.fold)

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
        self.label.setText(text)
        self.updateLayout()

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
        path.addPolygon(self.polygon)
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

    def updateLayout(self):
        """
        Update current shape rect according to the selected datatype.
        """
        width = max(self.label.width() + 16, self.MinWidth)
        self.polygon = self.createPolygon(width, self.MinHeight)
        self.fold = self.createFold(self.polygon, self.IndexTR, self.IndexRT)
        self.background = self.createBackground(width + 8, self.MinHeight + 8)
        self.selection = self.createSelection(width + 8, self.MinHeight + 8)
        self.updateTextPos()
        self.updateEdges()

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
        return self.polygon[self.IndexBR].x() - self.polygon[self.IndexBL].x()