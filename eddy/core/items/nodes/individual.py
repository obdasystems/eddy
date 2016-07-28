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


import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPolygonF, QPainterPath, QPainter
from PyQt5.QtGui import QPixmap, QIcon

from eddy.core.datatypes.graphol import Identity, Item
from eddy.core.datatypes.misc import Brush, Pen
from eddy.core.datatypes.owl import Datatype
from eddy.core.functions.misc import snapF
from eddy.core.items.nodes.common.base import AbstractResizableNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.polygon import Polygon
from eddy.core.datatypes.qt import Font
from eddy.core.regex import RE_VALUE


class IndividualNode(AbstractResizableNode):
    """
    This class implements the 'Individual' node.
    """
    IndexLT = 0
    IndexLB = 1
    IndexBL = 2
    IndexBR = 3
    IndexRB = 4
    IndexRT = 5
    IndexTR = 6
    IndexTL = 7
    IndexEE = 8

    Identities = {Identity.Instance, Identity.Value}
    Type = Item.IndividualNode

    def __init__(self, width=60, height=60, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)

        w = max(width, 60)
        h = max(height, 60)

        createPolygon = lambda x, y: QPolygonF([
            QPointF(-(x / 2), -((y / (1 + math.sqrt(2))) / 2)),
            QPointF(-(x / 2), +((y / (1 + math.sqrt(2))) / 2)),
            QPointF(-((x / (1 + math.sqrt(2))) / 2), +(y / 2)),
            QPointF(+((x / (1 + math.sqrt(2))) / 2), +(y / 2)),
            QPointF(+(x / 2), +((y / (1 + math.sqrt(2))) / 2)),
            QPointF(+(x / 2), -((y / (1 + math.sqrt(2))) / 2)),
            QPointF(+((x / (1 + math.sqrt(2))) / 2), -(y / 2)),
            QPointF(-((x / (1 + math.sqrt(2))) / 2), -(y / 2)),
            QPointF(-(x / 2), -((y / (1 + math.sqrt(2))) / 2)),
        ])

        self.background = Polygon(createPolygon(w + 8, h + 8))
        self.selection = Polygon(QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
        self.polygon = Polygon(createPolygon(w, h), brush or Brush.White255A, Pen.SolidBlack1Pt)
        self.label = NodeLabel(template='instance', pos=self.center, parent=self)
        self.label.setAlignment(Qt.AlignCenter)
        self.updateResizeHandles()
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
        match = RE_VALUE.match(self.text())
        if match:
            return Datatype.forValue(match.group('datatype'))
        return None

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        match = RE_VALUE.match(self.text())
        if match:
            return Identity.Value
        return Identity.Instance

    @property
    def value(self):
        """
        Returns the value value associated with this node.
        :rtype: str
        """
        match = RE_VALUE.match(self.text())
        if match:
            return match.group('value')
        return None

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.selection.geometry()

    @staticmethod
    def compose(value, datatype):
        """
        Compose the value string.
        :type value: str
        :type datatype: Datatype
        :return: str
        """
        return '"{0}"^^{1}'.format(value.strip('"'), datatype.value)

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
        polygon = self.polygon.geometry()
        return polygon[self.IndexTR].y() - polygon[self.IndexBR].y()

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
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Pen.SolidBlack1Pt)
            painter.setBrush(Brush.White255A)
            painter.translate(width / 2, height / 2)
            painter.drawPolygon(QPolygonF([
                QPointF(-20, -((40 / (1 + math.sqrt(2))) / 2)),
                QPointF(-20, +((40 / (1 + math.sqrt(2))) / 2)),
                QPointF(-((40 / (1 + math.sqrt(2))) / 2), +20),
                QPointF(+((40 / (1 + math.sqrt(2))) / 2), +20),
                QPointF(+20, +((40 / (1 + math.sqrt(2))) / 2)),
                QPointF(+20, -((40 / (1 + math.sqrt(2))) / 2)),
                QPointF(+((40 / (1 + math.sqrt(2))) / 2), -20),
                QPointF(-((40 / (1 + math.sqrt(2))) / 2), -20),
                QPointF(-20, -((40 / (1 + math.sqrt(2))) / 2)),
            ]))
            # PAINT THE TEXT INSIDE THE SHAPE
            painter.setFont(Font('Arial', 9, Font.Light))
            painter.drawText(-16, 4, 'instance')
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
        # ITEM SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawPolygon(self.polygon.geometry())
        # RESIZE HANDLES
        painter.setRenderHint(QPainter.Antialiasing)
        for polygon in self.handles:
            painter.setPen(polygon.pen())
            painter.setBrush(polygon.brush())
            painter.drawEllipse(polygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon.geometry())
        return path

    def resize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :type mousePos: QPointF
        """
        snap = self.session.action('toggle_grid').isChecked()
        size = self.diagram.GridSize
        moved = self.label.isMoved()

        background = self.background.geometry()
        selection = self.selection.geometry()
        polygon = self.polygon.geometry()
        
        R = QRectF(self.boundingRect())
        D = QPointF(0, 0)

        mbrh = 68
        mbrw = 68

        self.prepareGeometryChange()

        if self.mp_Handle == self.HandleTL:

            fromX = self.mp_Bound.left()
            fromY = self.mp_Bound.top()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toX = snapF(toX, size, -4, snap)
            toY = snapF(toY, size, -4, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setLeft(toX)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() - mbrw + R.width())
                R.setLeft(R.left() - mbrw + R.width())
            if R.height() < mbrh:
                D.setY(D.y() - mbrh + R.height())
                R.setTop(R.top() - mbrh + R.height())

            newSideY = (R.height() - 4 * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - 4 * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2

            selection.setLeft(R.left())
            selection.setTop(R.top())
            
            background[self.IndexLT] = QPointF(R.left(), newLeftRightTopY)
            background[self.IndexLB] = QPointF(R.left(), newLeftRightBottomY)
            background[self.IndexRT] = QPointF(R.right(), newLeftRightTopY)
            background[self.IndexRB] = QPointF(R.right(), newLeftRightBottomY)
            background[self.IndexTL] = QPointF(newTopBottomLeftX, R.top())
            background[self.IndexTR] = QPointF(newTopBottomRightX, R.top())
            background[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom())
            background[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom())
            background[self.IndexEE] = QPointF(R.left(), newLeftRightTopY)

            polygon[self.IndexLT] = QPointF(R.left() + 4, newLeftRightTopY)
            polygon[self.IndexLB] = QPointF(R.left() + 4, newLeftRightBottomY)
            polygon[self.IndexRT] = QPointF(R.right() - 4, newLeftRightTopY)
            polygon[self.IndexRB] = QPointF(R.right() - 4, newLeftRightBottomY)
            polygon[self.IndexTL] = QPointF(newTopBottomLeftX, R.top() + 4)
            polygon[self.IndexTR] = QPointF(newTopBottomRightX, R.top() + 4)
            polygon[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom() - 4)
            polygon[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom() - 4)
            polygon[self.IndexEE] = QPointF(R.left() + 4, newLeftRightTopY)

        elif self.mp_Handle == self.HandleTM:

            fromY = self.mp_Bound.top()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toY = snapF(toY, size, -4, snap)
            D.setY(toY - fromY)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.height() < mbrh:
                D.setY(D.y() - mbrh + R.height())
                R.setTop(R.top() - mbrh + R.height())

            newSide = (R.height() - 4 * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSide / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSide / 2
            
            selection.setTop(R.top())
            
            background[self.IndexTL] = QPointF(background[self.IndexTL].x(), R.top())
            background[self.IndexTR] = QPointF(background[self.IndexTR].x(), R.top())
            background[self.IndexLB] = QPointF(background[self.IndexLB].x(), newLeftRightBottomY)
            background[self.IndexRB] = QPointF(background[self.IndexRB].x(), newLeftRightBottomY)
            background[self.IndexLT] = QPointF(background[self.IndexLT].x(), newLeftRightTopY)
            background[self.IndexRT] = QPointF(background[self.IndexRT].x(), newLeftRightTopY)
            background[self.IndexEE] = QPointF(background[self.IndexEE].x(), newLeftRightTopY)
            
            polygon[self.IndexTL] = QPointF(polygon[self.IndexTL].x(), R.top() + 4)
            polygon[self.IndexTR] = QPointF(polygon[self.IndexTR].x(), R.top() + 4)
            polygon[self.IndexLB] = QPointF(polygon[self.IndexLB].x(), newLeftRightBottomY)
            polygon[self.IndexRB] = QPointF(polygon[self.IndexRB].x(), newLeftRightBottomY)
            polygon[self.IndexLT] = QPointF(polygon[self.IndexLT].x(), newLeftRightTopY)
            polygon[self.IndexRT] = QPointF(polygon[self.IndexRT].x(), newLeftRightTopY)
            polygon[self.IndexEE] = QPointF(polygon[self.IndexEE].x(), newLeftRightTopY)

        elif self.mp_Handle == self.HandleTR:

            fromX = self.mp_Bound.right()
            fromY = self.mp_Bound.top()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toX = snapF(toX, size, +4, snap)
            toY = snapF(toY, size, -4, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setRight(toX)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() + mbrw - R.width())
                R.setRight(R.right() + mbrw - R.width())
            if R.height() < mbrh:
                D.setY(D.y() - mbrh + R.height())
                R.setTop(R.top() - mbrh + R.height())

            newSideY = (R.height() - 4 * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - 4 * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2
            
            selection.setRight(R.right())
            selection.setTop(R.top())
            
            background[self.IndexLT] = QPointF(R.left(), newLeftRightTopY)
            background[self.IndexLB] = QPointF(R.left(), newLeftRightBottomY)
            background[self.IndexRT] = QPointF(R.right(), newLeftRightTopY)
            background[self.IndexRB] = QPointF(R.right(), newLeftRightBottomY)
            background[self.IndexTL] = QPointF(newTopBottomLeftX, R.top())
            background[self.IndexTR] = QPointF(newTopBottomRightX, R.top())
            background[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom())
            background[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom())
            background[self.IndexEE] = QPointF(R.left(), newLeftRightTopY)
            
            polygon[self.IndexLT] = QPointF(R.left() + 4, newLeftRightTopY)
            polygon[self.IndexLB] = QPointF(R.left() + 4, newLeftRightBottomY)
            polygon[self.IndexRT] = QPointF(R.right() - 4, newLeftRightTopY)
            polygon[self.IndexRB] = QPointF(R.right() - 4, newLeftRightBottomY)
            polygon[self.IndexTL] = QPointF(newTopBottomLeftX, R.top() + 4)
            polygon[self.IndexTR] = QPointF(newTopBottomRightX, R.top() + 4)
            polygon[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom() - 4)
            polygon[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom() - 4)
            polygon[self.IndexEE] = QPointF(R.left() + 4, newLeftRightTopY)

        elif self.mp_Handle == self.HandleML:

            fromX = self.mp_Bound.left()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toX = snapF(toX, size, -4, snap)
            D.setX(toX - fromX)
            R.setLeft(toX)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() - mbrw + R.width())
                R.setLeft(R.left() - mbrw + R.width())

            newSide = (R.width() - 4 * 2) / (1 + math.sqrt(2))
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSide / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSide / 2

            selection.setLeft(R.left())
            
            background[self.IndexLT] = QPointF(R.left(), background[self.IndexLT].y())
            background[self.IndexLB] = QPointF(R.left(), background[self.IndexLB].y())
            background[self.IndexEE] = QPointF(R.left(), background[self.IndexEE].y())
            background[self.IndexTL] = QPointF(newTopBottomLeftX, background[self.IndexTL].y())
            background[self.IndexTR] = QPointF(newTopBottomRightX, background[self.IndexTR].y())
            background[self.IndexBL] = QPointF(newTopBottomLeftX, background[self.IndexBL].y())
            background[self.IndexBR] = QPointF(newTopBottomRightX, background[self.IndexBR].y())
            
            polygon[self.IndexLT] = QPointF(R.left() + 4, polygon[self.IndexLT].y())
            polygon[self.IndexLB] = QPointF(R.left() + 4, polygon[self.IndexLB].y())
            polygon[self.IndexEE] = QPointF(R.left() + 4, polygon[self.IndexEE].y())
            polygon[self.IndexTL] = QPointF(newTopBottomLeftX, polygon[self.IndexTL].y())
            polygon[self.IndexTR] = QPointF(newTopBottomRightX, polygon[self.IndexTR].y())
            polygon[self.IndexBL] = QPointF(newTopBottomLeftX, polygon[self.IndexBL].y())
            polygon[self.IndexBR] = QPointF(newTopBottomRightX, polygon[self.IndexBR].y())

        elif self.mp_Handle == self.HandleMR:

            fromX = self.mp_Bound.right()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toX = snapF(toX, size, +4, snap)
            D.setX(toX - fromX)
            R.setRight(toX)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() + mbrw - R.width())
                R.setRight(R.right() + mbrw - R.width())

            newSide = (R.width() - 4 * 2) / (1 + math.sqrt(2))
            newTopBottomRightX = (R.x() + R.width() / 2) + newSide / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSide / 2
            
            selection.setRight(R.right())
            
            background[self.IndexRT] = QPointF(R.right(), background[self.IndexRT].y())
            background[self.IndexRB] = QPointF(R.right(), background[self.IndexRB].y())
            background[self.IndexTL] = QPointF(newTopBottomLeftX, background[self.IndexTL].y())
            background[self.IndexTR] = QPointF(newTopBottomRightX, background[self.IndexTR].y())
            background[self.IndexBL] = QPointF(newTopBottomLeftX, background[self.IndexBL].y())
            background[self.IndexBR] = QPointF(newTopBottomRightX, background[self.IndexBR].y())
            
            polygon[self.IndexRT] = QPointF(R.right() - 4, polygon[self.IndexRT].y())
            polygon[self.IndexRB] = QPointF(R.right() - 4, polygon[self.IndexRB].y())
            polygon[self.IndexTL] = QPointF(newTopBottomLeftX, polygon[self.IndexTL].y())
            polygon[self.IndexTR] = QPointF(newTopBottomRightX, polygon[self.IndexTR].y())
            polygon[self.IndexBL] = QPointF(newTopBottomLeftX, polygon[self.IndexBL].y())
            polygon[self.IndexBR] = QPointF(newTopBottomRightX, polygon[self.IndexBR].y())

        elif self.mp_Handle == self.HandleBL:

            fromX = self.mp_Bound.left()
            fromY = self.mp_Bound.bottom()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toX = snapF(toX, size, -4, snap)
            toY = snapF(toY, size, +4, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setLeft(toX)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() - mbrw + R.width())
                R.setLeft(R.left() - mbrw + R.width())
            if R.height() < mbrh:
                D.setY(D.y() + mbrh - R.height())
                R.setBottom(R.bottom() + mbrh - R.height())

            newSideY = (R.height() - 4 * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - 4 * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2
            
            selection.setLeft(R.left())
            selection.setBottom(R.bottom())
            
            background[self.IndexLT] = QPointF(R.left(), newLeftRightTopY)
            background[self.IndexLB] = QPointF(R.left(), newLeftRightBottomY)
            background[self.IndexRT] = QPointF(R.right(), newLeftRightTopY)
            background[self.IndexRB] = QPointF(R.right(), newLeftRightBottomY)
            background[self.IndexTL] = QPointF(newTopBottomLeftX, R.top())
            background[self.IndexTR] = QPointF(newTopBottomRightX, R.top())
            background[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom())
            background[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom())
            background[self.IndexEE] = QPointF(R.left(), newLeftRightTopY)
            
            polygon[self.IndexLT] = QPointF(R.left() + 4, newLeftRightTopY)
            polygon[self.IndexLB] = QPointF(R.left() + 4, newLeftRightBottomY)
            polygon[self.IndexRT] = QPointF(R.right() - 4, newLeftRightTopY)
            polygon[self.IndexRB] = QPointF(R.right() - 4, newLeftRightBottomY)
            polygon[self.IndexTL] = QPointF(newTopBottomLeftX, R.top() + 4)
            polygon[self.IndexTR] = QPointF(newTopBottomRightX, R.top() + 4)
            polygon[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom() - 4)
            polygon[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom() - 4)
            polygon[self.IndexEE] = QPointF(R.left() + 4, newLeftRightTopY)

        elif self.mp_Handle == self.HandleBM:

            fromY = self.mp_Bound.bottom()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toY = snapF(toY, size, +4, snap)
            D.setY(toY - fromY)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.height() < mbrh:
                D.setY(D.y() + mbrh - R.height())
                R.setBottom(R.bottom() + mbrh - R.height())

            newSide = (R.height() - 4 * 2) / (1 + math.sqrt(2))
            newLeftRightTopY = (R.y() + R.height() / 2) - newSide / 2
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSide / 2
            
            selection.setBottom(R.bottom())
            
            background[self.IndexBL] = QPointF(background[self.IndexBL].x(), R.bottom())
            background[self.IndexBR] = QPointF(background[self.IndexBR].x(), R.bottom())
            background[self.IndexLB] = QPointF(background[self.IndexLB].x(), newLeftRightBottomY)
            background[self.IndexRB] = QPointF(background[self.IndexRB].x(), newLeftRightBottomY)
            background[self.IndexLT] = QPointF(background[self.IndexLT].x(), newLeftRightTopY)
            background[self.IndexRT] = QPointF(background[self.IndexRT].x(), newLeftRightTopY)
            background[self.IndexEE] = QPointF(background[self.IndexEE].x(), newLeftRightTopY)
            
            polygon[self.IndexBL] = QPointF(polygon[self.IndexBL].x(), R.bottom() - 4)
            polygon[self.IndexBR] = QPointF(polygon[self.IndexBR].x(), R.bottom() - 4)
            polygon[self.IndexLB] = QPointF(polygon[self.IndexLB].x(), newLeftRightBottomY)
            polygon[self.IndexRB] = QPointF(polygon[self.IndexRB].x(), newLeftRightBottomY)
            polygon[self.IndexLT] = QPointF(polygon[self.IndexLT].x(), newLeftRightTopY)
            polygon[self.IndexRT] = QPointF(polygon[self.IndexRT].x(), newLeftRightTopY)
            polygon[self.IndexEE] = QPointF(polygon[self.IndexEE].x(), newLeftRightTopY)

        elif self.mp_Handle == self.HandleBR:

            fromX = self.mp_Bound.right()
            fromY = self.mp_Bound.bottom()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toX = snapF(toX, size, +4, snap)
            toY = snapF(toY, size, +4, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setRight(toX)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() + mbrw - R.width())
                R.setRight(R.right() + mbrw - R.width())
            if R.height() < mbrh:
                D.setY(D.y() + mbrh - R.height())
                R.setBottom(R.bottom() + mbrh - R.height())

            newSideY = (R.height() - 4 * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - 4 * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2

            selection.setRight(R.right())
            selection.setBottom(R.bottom())

            background[self.IndexLT] = QPointF(R.left(), newLeftRightTopY)
            background[self.IndexLB] = QPointF(R.left(), newLeftRightBottomY)
            background[self.IndexRT] = QPointF(R.right(), newLeftRightTopY)
            background[self.IndexRB] = QPointF(R.right(), newLeftRightBottomY)
            background[self.IndexTL] = QPointF(newTopBottomLeftX, R.top())
            background[self.IndexTR] = QPointF(newTopBottomRightX, R.top())
            background[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom())
            background[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom())
            background[self.IndexEE] = QPointF(R.left(), newLeftRightTopY)
            
            polygon[self.IndexLT] = QPointF(R.left() + 4, newLeftRightTopY)
            polygon[self.IndexLB] = QPointF(R.left() + 4, newLeftRightBottomY)
            polygon[self.IndexRT] = QPointF(R.right() - 4, newLeftRightTopY)
            polygon[self.IndexRB] = QPointF(R.right() - 4, newLeftRightBottomY)
            polygon[self.IndexTL] = QPointF(newTopBottomLeftX, R.top() + 4)
            polygon[self.IndexTR] = QPointF(newTopBottomRightX, R.top() + 4)
            polygon[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom() - 4)
            polygon[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom() - 4)
            polygon[self.IndexEE] = QPointF(R.left() + 4, newLeftRightTopY)

        self.background.setGeometry(background)
        self.selection.setGeometry(selection)
        self.polygon.setGeometry(polygon)
        self.updateResizeHandles()
        self.updateTextPos(moved=moved)
        self.updateAnchors(self.mp_Data, D)

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon.geometry())
        for polygon in self.handles:
            path.addEllipse(polygon.geometry())
        return path

    def setText(self, text):
        """
        Set the label text: will additionally block label editing if a literal is being.
        :type text: str
        """
        self.label.setEditable(RE_VALUE.match(text) is None)
        self.label.setText(text)
        self.label.setAlignment(Qt.AlignCenter)

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

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

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        polygon = self.polygon.geometry()
        return polygon[self.IndexRT].x() - polygon[self.IndexLT].x()