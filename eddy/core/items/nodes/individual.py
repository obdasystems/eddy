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


import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPolygonF, QPainterPath, QPainter
from PyQt5.QtGui import QPen, QColor, QPixmap, QBrush, QIcon

from eddy.core.datatypes.graphol import Identity, Item
from eddy.core.datatypes.owl import Datatype
from eddy.core.functions.misc import snapF
from eddy.core.items.nodes.common.base import AbstractResizableNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.qt import Font
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
    MinHeight = 60
    MinWidth = 60

    def __init__(self, width=MinWidth, height=MinHeight, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        w = max(width, self.MinWidth)
        h = max(height, self.MinHeight)
        s = self.HandleSize
        self.brush = brush or QBrush(QColor(252, 252, 252))
        self.pen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine)
        self.polygon = self.createPolygon(w, h)
        self.background = self.createBackground(w + s, h + s)
        self.selection = self.createSelection(w + s, h + s)
        self.label = NodeLabel(template='instance',
                               pos=self.center,
                               parent=self)
        self.updateHandles()
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
        return self.selection

    @staticmethod
    def composeValue(value, datatype):
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
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 0
            QPointF(-(width / 2), +((height / (1 + math.sqrt(2))) / 2)), # 1
            QPointF(-((width / (1 + math.sqrt(2))) / 2), +(height / 2)), # 2
            QPointF(+((width / (1 + math.sqrt(2))) / 2), +(height / 2)), # 3
            QPointF(+(width / 2), +((height / (1 + math.sqrt(2))) / 2)), # 4
            QPointF(+(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 5
            QPointF(+((width / (1 + math.sqrt(2))) / 2), -(height / 2)), # 6
            QPointF(-((width / (1 + math.sqrt(2))) / 2), -(height / 2)), # 7
            QPointF(-(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 8
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
            QPointF(-(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 0
            QPointF(-(width / 2), +((height / (1 + math.sqrt(2))) / 2)), # 1
            QPointF(-((width / (1 + math.sqrt(2))) / 2), +(height / 2)), # 2
            QPointF(+((width / (1 + math.sqrt(2))) / 2), +(height / 2)), # 3
            QPointF(+(width / 2), +((height / (1 + math.sqrt(2))) / 2)), # 4
            QPointF(+(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 5
            QPointF(+((width / (1 + math.sqrt(2))) / 2), -(height / 2)), # 6
            QPointF(-((width / (1 + math.sqrt(2))) / 2), -(height / 2)), # 7
            QPointF(-(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 8
        ])
    
    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon[self.IndexTR].y() - self.polygon[self.IndexBR].y()

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
            polygon = cls.createPolygon(40, 40)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
            painter.setBrush(QColor(252, 252, 252))
            painter.translate(width / 2, height / 2)
            painter.drawPolygon(polygon)
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
        painter.setPen(self.selectionPen)
        painter.setBrush(self.selectionBrush)
        painter.drawRect(self.selection)
        # SYNTAX VALIDATION
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.backgroundPen)
        painter.setBrush(self.backgroundBrush)
        painter.drawPolygon(self.background)
        # ITEM SHAPE
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawPolygon(self.polygon)
        # RESIZE HANDLES
        painter.setRenderHint(QPainter.Antialiasing)
        for i in range(self.HandleNum):
            painter.setBrush(self.handleBrush[i])
            painter.setPen(self.handlePen[i])
            painter.drawEllipse(self.handleBound[i])

    def resize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :type mousePos: QPointF
        """
        mainwindow = self.project.parent()
        snap = mainwindow.actionSnapToGrid.isChecked()
        size = self.diagram.GridSize
        offset = self.HandleSize + self.HandleMove
        moved = self.label.isMoved()
        
        R = QRectF(self.boundingRect())
        D = QPointF(0, 0)

        mbh = self.MinHeight + offset * 2
        mbw = self.MinWidth + offset * 2

        self.prepareGeometryChange()

        if self.mousePressHandle == self.HandleTL:

            fromX = self.mousePressBound.left()
            fromY = self.mousePressBound.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, size, -offset, snap)
            toY = snapF(toY, size, -offset, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setLeft(toX)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.width() < mbw:
                D.setX(D.x() - mbw + R.width())
                R.setLeft(R.left() - mbw + R.width())
            if R.height() < mbh:
                D.setY(D.y() - mbh + R.height())
                R.setTop(R.top() - mbh + R.height())

            newSideY = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2

            self.selection.setLeft(R.left())
            self.selection.setTop(R.top())
            
            self.background[self.IndexLT] = QPointF(R.left(), newLeftRightTopY)
            self.background[self.IndexLB] = QPointF(R.left(), newLeftRightBottomY)
            self.background[self.IndexRT] = QPointF(R.right(), newLeftRightTopY)
            self.background[self.IndexRB] = QPointF(R.right(), newLeftRightBottomY)
            self.background[self.IndexTL] = QPointF(newTopBottomLeftX, R.top())
            self.background[self.IndexTR] = QPointF(newTopBottomRightX, R.top())
            self.background[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom())
            self.background[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom())
            self.background[self.IndexEE] = QPointF(R.left(), newLeftRightTopY)

            self.polygon[self.IndexLT] = QPointF(R.left() + offset, newLeftRightTopY)
            self.polygon[self.IndexLB] = QPointF(R.left() + offset, newLeftRightBottomY)
            self.polygon[self.IndexRT] = QPointF(R.right() - offset, newLeftRightTopY)
            self.polygon[self.IndexRB] = QPointF(R.right() - offset, newLeftRightBottomY)
            self.polygon[self.IndexTL] = QPointF(newTopBottomLeftX, R.top() + offset)
            self.polygon[self.IndexTR] = QPointF(newTopBottomRightX, R.top() + offset)
            self.polygon[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom() - offset)
            self.polygon[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom() - offset)
            self.polygon[self.IndexEE] = QPointF(R.left() + offset, newLeftRightTopY)

        elif self.mousePressHandle == self.HandleTM:

            fromY = self.mousePressBound.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, size, -offset, snap)
            D.setY(toY - fromY)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.height() < mbh:
                D.setY(D.y() - mbh + R.height())
                R.setTop(R.top() - mbh + R.height())

            newSide = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSide / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSide / 2
            
            self.selection.setTop(R.top())
            
            self.background[self.IndexTL] = QPointF(self.background[self.IndexTL].x(), R.top())
            self.background[self.IndexTR] = QPointF(self.background[self.IndexTR].x(), R.top())
            self.background[self.IndexLB] = QPointF(self.background[self.IndexLB].x(), newLeftRightBottomY)
            self.background[self.IndexRB] = QPointF(self.background[self.IndexRB].x(), newLeftRightBottomY)
            self.background[self.IndexLT] = QPointF(self.background[self.IndexLT].x(), newLeftRightTopY)
            self.background[self.IndexRT] = QPointF(self.background[self.IndexRT].x(), newLeftRightTopY)
            self.background[self.IndexEE] = QPointF(self.background[self.IndexEE].x(), newLeftRightTopY)
            
            self.polygon[self.IndexTL] = QPointF(self.polygon[self.IndexTL].x(), R.top() + offset)
            self.polygon[self.IndexTR] = QPointF(self.polygon[self.IndexTR].x(), R.top() + offset)
            self.polygon[self.IndexLB] = QPointF(self.polygon[self.IndexLB].x(), newLeftRightBottomY)
            self.polygon[self.IndexRB] = QPointF(self.polygon[self.IndexRB].x(), newLeftRightBottomY)
            self.polygon[self.IndexLT] = QPointF(self.polygon[self.IndexLT].x(), newLeftRightTopY)
            self.polygon[self.IndexRT] = QPointF(self.polygon[self.IndexRT].x(), newLeftRightTopY)
            self.polygon[self.IndexEE] = QPointF(self.polygon[self.IndexEE].x(), newLeftRightTopY)

        elif self.mousePressHandle == self.HandleTR:

            fromX = self.mousePressBound.right()
            fromY = self.mousePressBound.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, size, +offset, snap)
            toY = snapF(toY, size, -offset, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setRight(toX)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.width() < mbw:
                D.setX(D.x() + mbw - R.width())
                R.setRight(R.right() + mbw - R.width())
            if R.height() < mbh:
                D.setY(D.y() - mbh + R.height())
                R.setTop(R.top() - mbh + R.height())

            newSideY = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2
            
            self.selection.setRight(R.right())
            self.selection.setTop(R.top())
            
            self.background[self.IndexLT] = QPointF(R.left(), newLeftRightTopY)
            self.background[self.IndexLB] = QPointF(R.left(), newLeftRightBottomY)
            self.background[self.IndexRT] = QPointF(R.right(), newLeftRightTopY)
            self.background[self.IndexRB] = QPointF(R.right(), newLeftRightBottomY)
            self.background[self.IndexTL] = QPointF(newTopBottomLeftX, R.top())
            self.background[self.IndexTR] = QPointF(newTopBottomRightX, R.top())
            self.background[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom())
            self.background[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom())
            self.background[self.IndexEE] = QPointF(R.left(), newLeftRightTopY)
            
            self.polygon[self.IndexLT] = QPointF(R.left() + offset, newLeftRightTopY)
            self.polygon[self.IndexLB] = QPointF(R.left() + offset, newLeftRightBottomY)
            self.polygon[self.IndexRT] = QPointF(R.right() - offset, newLeftRightTopY)
            self.polygon[self.IndexRB] = QPointF(R.right() - offset, newLeftRightBottomY)
            self.polygon[self.IndexTL] = QPointF(newTopBottomLeftX, R.top() + offset)
            self.polygon[self.IndexTR] = QPointF(newTopBottomRightX, R.top() + offset)
            self.polygon[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom() - offset)
            self.polygon[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom() - offset)
            self.polygon[self.IndexEE] = QPointF(R.left() + offset, newLeftRightTopY)

        elif self.mousePressHandle == self.HandleML:

            fromX = self.mousePressBound.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, size, -offset, snap)
            D.setX(toX - fromX)
            R.setLeft(toX)

            ## CLAMP SIZE
            if R.width() < mbw:
                D.setX(D.x() - mbw + R.width())
                R.setLeft(R.left() - mbw + R.width())

            newSide = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSide / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSide / 2

            self.selection.setLeft(R.left())
            
            self.background[self.IndexLT] = QPointF(R.left(), self.background[self.IndexLT].y())
            self.background[self.IndexLB] = QPointF(R.left(), self.background[self.IndexLB].y())
            self.background[self.IndexEE] = QPointF(R.left(), self.background[self.IndexEE].y())
            self.background[self.IndexTL] = QPointF(newTopBottomLeftX, self.background[self.IndexTL].y())
            self.background[self.IndexTR] = QPointF(newTopBottomRightX, self.background[self.IndexTR].y())
            self.background[self.IndexBL] = QPointF(newTopBottomLeftX, self.background[self.IndexBL].y())
            self.background[self.IndexBR] = QPointF(newTopBottomRightX, self.background[self.IndexBR].y())
            
            self.polygon[self.IndexLT] = QPointF(R.left() + offset, self.polygon[self.IndexLT].y())
            self.polygon[self.IndexLB] = QPointF(R.left() + offset, self.polygon[self.IndexLB].y())
            self.polygon[self.IndexEE] = QPointF(R.left() + offset, self.polygon[self.IndexEE].y())
            self.polygon[self.IndexTL] = QPointF(newTopBottomLeftX, self.polygon[self.IndexTL].y())
            self.polygon[self.IndexTR] = QPointF(newTopBottomRightX, self.polygon[self.IndexTR].y())
            self.polygon[self.IndexBL] = QPointF(newTopBottomLeftX, self.polygon[self.IndexBL].y())
            self.polygon[self.IndexBR] = QPointF(newTopBottomRightX, self.polygon[self.IndexBR].y())

        elif self.mousePressHandle == self.HandleMR:

            fromX = self.mousePressBound.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, size, +offset, snap)
            D.setX(toX - fromX)
            R.setRight(toX)

            ## CLAMP SIZE
            if R.width() < mbw:
                D.setX(D.x() + mbw - R.width())
                R.setRight(R.right() + mbw - R.width())

            newSide = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomRightX = (R.x() + R.width() / 2) + newSide / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSide / 2
            
            self.selection.setRight(R.right())
            
            self.background[self.IndexRT] = QPointF(R.right(), self.background[self.IndexRT].y())
            self.background[self.IndexRB] = QPointF(R.right(), self.background[self.IndexRB].y())
            self.background[self.IndexTL] = QPointF(newTopBottomLeftX, self.background[self.IndexTL].y())
            self.background[self.IndexTR] = QPointF(newTopBottomRightX, self.background[self.IndexTR].y())
            self.background[self.IndexBL] = QPointF(newTopBottomLeftX, self.background[self.IndexBL].y())
            self.background[self.IndexBR] = QPointF(newTopBottomRightX, self.background[self.IndexBR].y())
            
            self.polygon[self.IndexRT] = QPointF(R.right() - offset, self.polygon[self.IndexRT].y())
            self.polygon[self.IndexRB] = QPointF(R.right() - offset, self.polygon[self.IndexRB].y())
            self.polygon[self.IndexTL] = QPointF(newTopBottomLeftX, self.polygon[self.IndexTL].y())
            self.polygon[self.IndexTR] = QPointF(newTopBottomRightX, self.polygon[self.IndexTR].y())
            self.polygon[self.IndexBL] = QPointF(newTopBottomLeftX, self.polygon[self.IndexBL].y())
            self.polygon[self.IndexBR] = QPointF(newTopBottomRightX, self.polygon[self.IndexBR].y())

        elif self.mousePressHandle == self.HandleBL:

            fromX = self.mousePressBound.left()
            fromY = self.mousePressBound.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, size, -offset, snap)
            toY = snapF(toY, size, +offset, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setLeft(toX)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.width() < mbw:
                D.setX(D.x() - mbw + R.width())
                R.setLeft(R.left() - mbw + R.width())
            if R.height() < mbh:
                D.setY(D.y() + mbh - R.height())
                R.setBottom(R.bottom() + mbh - R.height())

            newSideY = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2
            
            self.selection.setLeft(R.left())
            self.selection.setBottom(R.bottom())
            
            self.background[self.IndexLT] = QPointF(R.left(), newLeftRightTopY)
            self.background[self.IndexLB] = QPointF(R.left(), newLeftRightBottomY)
            self.background[self.IndexRT] = QPointF(R.right(), newLeftRightTopY)
            self.background[self.IndexRB] = QPointF(R.right(), newLeftRightBottomY)
            self.background[self.IndexTL] = QPointF(newTopBottomLeftX, R.top())
            self.background[self.IndexTR] = QPointF(newTopBottomRightX, R.top())
            self.background[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom())
            self.background[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom())
            self.background[self.IndexEE] = QPointF(R.left(), newLeftRightTopY)
            
            self.polygon[self.IndexLT] = QPointF(R.left() + offset, newLeftRightTopY)
            self.polygon[self.IndexLB] = QPointF(R.left() + offset, newLeftRightBottomY)
            self.polygon[self.IndexRT] = QPointF(R.right() - offset, newLeftRightTopY)
            self.polygon[self.IndexRB] = QPointF(R.right() - offset, newLeftRightBottomY)
            self.polygon[self.IndexTL] = QPointF(newTopBottomLeftX, R.top() + offset)
            self.polygon[self.IndexTR] = QPointF(newTopBottomRightX, R.top() + offset)
            self.polygon[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom() - offset)
            self.polygon[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom() - offset)
            self.polygon[self.IndexEE] = QPointF(R.left() + offset, newLeftRightTopY)

        elif self.mousePressHandle == self.HandleBM:

            fromY = self.mousePressBound.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, size, +offset, snap)
            D.setY(toY - fromY)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.height() < mbh:
                D.setY(D.y() + mbh - R.height())
                R.setBottom(R.bottom() + mbh - R.height())

            newSide = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightTopY = (R.y() + R.height() / 2) - newSide / 2
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSide / 2
            
            self.selection.setBottom(R.bottom())
            
            self.background[self.IndexBL] = QPointF(self.background[self.IndexBL].x(), R.bottom())
            self.background[self.IndexBR] = QPointF(self.background[self.IndexBR].x(), R.bottom())
            self.background[self.IndexLB] = QPointF(self.background[self.IndexLB].x(), newLeftRightBottomY)
            self.background[self.IndexRB] = QPointF(self.background[self.IndexRB].x(), newLeftRightBottomY)
            self.background[self.IndexLT] = QPointF(self.background[self.IndexLT].x(), newLeftRightTopY)
            self.background[self.IndexRT] = QPointF(self.background[self.IndexRT].x(), newLeftRightTopY)
            self.background[self.IndexEE] = QPointF(self.background[self.IndexEE].x(), newLeftRightTopY)
            
            self.polygon[self.IndexBL] = QPointF(self.polygon[self.IndexBL].x(), R.bottom() - offset)
            self.polygon[self.IndexBR] = QPointF(self.polygon[self.IndexBR].x(), R.bottom() - offset)
            self.polygon[self.IndexLB] = QPointF(self.polygon[self.IndexLB].x(), newLeftRightBottomY)
            self.polygon[self.IndexRB] = QPointF(self.polygon[self.IndexRB].x(), newLeftRightBottomY)
            self.polygon[self.IndexLT] = QPointF(self.polygon[self.IndexLT].x(), newLeftRightTopY)
            self.polygon[self.IndexRT] = QPointF(self.polygon[self.IndexRT].x(), newLeftRightTopY)
            self.polygon[self.IndexEE] = QPointF(self.polygon[self.IndexEE].x(), newLeftRightTopY)

        elif self.mousePressHandle == self.HandleBR:

            fromX = self.mousePressBound.right()
            fromY = self.mousePressBound.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, size, +offset, snap)
            toY = snapF(toY, size, +offset, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setRight(toX)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.width() < mbw:
                D.setX(D.x() + mbw - R.width())
                R.setRight(R.right() + mbw - R.width())
            if R.height() < mbh:
                D.setY(D.y() + mbh - R.height())
                R.setBottom(R.bottom() + mbh - R.height())

            newSideY = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2

            self.selection.setRight(R.right())
            self.selection.setBottom(R.bottom())

            self.background[self.IndexLT] = QPointF(R.left(), newLeftRightTopY)
            self.background[self.IndexLB] = QPointF(R.left(), newLeftRightBottomY)
            self.background[self.IndexRT] = QPointF(R.right(), newLeftRightTopY)
            self.background[self.IndexRB] = QPointF(R.right(), newLeftRightBottomY)
            self.background[self.IndexTL] = QPointF(newTopBottomLeftX, R.top())
            self.background[self.IndexTR] = QPointF(newTopBottomRightX, R.top())
            self.background[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom())
            self.background[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom())
            self.background[self.IndexEE] = QPointF(R.left(), newLeftRightTopY)
            
            self.polygon[self.IndexLT] = QPointF(R.left() + offset, newLeftRightTopY)
            self.polygon[self.IndexLB] = QPointF(R.left() + offset, newLeftRightBottomY)
            self.polygon[self.IndexRT] = QPointF(R.right() - offset, newLeftRightTopY)
            self.polygon[self.IndexRB] = QPointF(R.right() - offset, newLeftRightBottomY)
            self.polygon[self.IndexTL] = QPointF(newTopBottomLeftX, R.top() + offset)
            self.polygon[self.IndexTR] = QPointF(newTopBottomRightX, R.top() + offset)
            self.polygon[self.IndexBL] = QPointF(newTopBottomLeftX, R.bottom() - offset)
            self.polygon[self.IndexBR] = QPointF(newTopBottomRightX, R.bottom() - offset)
            self.polygon[self.IndexEE] = QPointF(R.left() + offset, newLeftRightTopY)

        self.updateHandles()
        self.updateTextPos(moved=moved)
        self.updateAnchors(self.mousePressData, D)

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
        for shape in self.handleBound:
            path.addEllipse(shape)
        return path

    def setText(self, text):
        """
        Set the label text: will additionally block label editing if a literal is being.
        :type text: str
        """
        self.label.setEditable(RE_VALUE.match(text) is None)
        self.label.setText(text)

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
        return self.polygon[self.IndexRT].x() - self.polygon[self.IndexLT].x()