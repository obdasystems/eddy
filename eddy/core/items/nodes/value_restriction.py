# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPolygonF, QPainterPath, QPainter, QPen, QColor, QPixmap, QBrush

from eddy.core.datatypes import Facet, Font, Identity, Item, XsdDatatype
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import Label
from eddy.core.regex import RE_FACET


class ValueRestrictionNode(AbstractNode):
    """
    This class implements the 'Value-Restriction' node.
    """
    indexTR = 0
    indexTL = 1
    indexBL = 2
    indexBR = 3
    indexRT = 4
    indexEE = 5

    identities = {Identity.DataRange}
    item = Item.ValueRestrictionNode
    minheight = 50
    minwidth = 180

    def __init__(self, width=minwidth, height=minheight, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        self.brush = brush or QBrush(QColor(252, 252, 252))
        self.pen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)
        self.polygon = self.createPolygon(self.minwidth, self.minheight)
        self.fold = self.createFold(self.polygon, self.indexTR, self.indexRT)
        self.background = self.createBackground(self.minwidth + 8, self.minheight + 8)
        self.selection = self.createSelection(self.minwidth + 8, self.minheight + 8)
        self.label = Label('xsd:length "32"^^xsd:string', movable=False, editable=False, parent=self)
        self.updateLayout()

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def datatype(self):
        """
        Returns the datatype associated with this node.
        :rtype: XsdDatatype
        """
        match = RE_FACET.match(self.text())
        if match:
            return XsdDatatype.forValue(match.group('datatype'))
        return None

    @property
    def facet(self):
        """
        Returns the facet associated with this node.
        :rtype: Facet
        """
        match = RE_FACET.match(self.text())
        if match:
            return Facet.forValue(match.group('facet'))
        return None

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.DataRange

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
        match = RE_FACET.match(self.text())
        if match:
            return match.group('value')
        return ''

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def copy(self, scene):
        """
        Create a copy of the current item.
        :type scene: DiagramScene
        """
        kwargs = {
            'id': self.id,
            'brush': self.brush,
            'description': self.description,
            'url': self.url,
            'height': self.height(),
            'width': self.width(),
        }
        node = scene.itemFactory.create(item=self.item, scene=scene, **kwargs)
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
    def createFold(polygon, indexTR, indexRT):
        """
        Returns the initialized fold polygon.
        :type polygon: QPolygonF
        :type indexTR: int
        :type indexRT: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(polygon[indexTR].x(), polygon[indexTR].y()),
            QPointF(polygon[indexTR].x(), polygon[indexTR].y() + 12),
            QPointF(polygon[indexRT].x(), polygon[indexRT].y()),
            QPointF(polygon[indexTR].x(), polygon[indexTR].y()),
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
        return self.polygon[self.indexBL].y() - self.polygon[self.indexTL].y()

    def updateLayout(self):
        """
        Update current shape rect according to the selected datatype.
        """
        width = max(self.label.width() + 16, self.minwidth)
        self.polygon = self.createPolygon(width, self.minheight)
        self.fold = self.createFold(self.polygon, self.indexTR, self.indexRT)
        self.background = self.createBackground(width + 8, self.minheight + 8)
        self.selection = self.createSelection(width + 8, self.minheight + 8)
        self.updateTextPos()
        self.updateEdges()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon[self.indexBR].x() - self.polygon[self.indexBL].x()

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.selection

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon)
        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon)
        return path

    ####################################################################################################################
    #                                                                                                                  #
    #   LABEL SHORTCUTS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.label.pos()

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        self.label.setText(text)
        self.updateLayout()

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

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

        polygon = QPolygonF([
            QPointF(+27 - 10, -17),  # 0
            QPointF(-27, -17),       # 1
            QPointF(-27, +17),       # 2
            QPointF(+27, +17),       # 3
            QPointF(+27, -17 + 10),  # 4
            QPointF(+27 - 10, -17),  # 5
        ])
        
        fold = QPolygonF([
            QPointF(polygon[cls.indexTR].x(), polygon[cls.indexTR].y()),
            QPointF(polygon[cls.indexTR].x(), polygon[cls.indexTR].y() + 10),
            QPointF(polygon[cls.indexRT].x(), polygon[cls.indexRT].y()),
            QPointF(polygon[cls.indexTR].x(), polygon[cls.indexTR].y()),
        ])

        # ITEM SHAPE
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)
        painter.drawPolygon(fold)
        # TEXT WITHIN THE SHAPE
        painter.setFont(Font('Arial', 10, Font.Light))
        painter.drawText(polygon.boundingRect(), Qt.AlignCenter, 'value\nrestriction')
        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the diagram scene.
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