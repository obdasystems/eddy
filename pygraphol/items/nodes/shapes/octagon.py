# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


import math

from pygraphol.functions import snapPointToGrid
from pygraphol.items.nodes.shapes.common import Label
from pygraphol.items.nodes.shapes.mixins import ShapeResizableMixin
from PyQt5.QtCore import QPointF, Qt, QRectF, QLineF
from PyQt5.QtGui import QColor, QPen,  QPainterPath, QPolygonF, QPainter, QPixmap, QFont
from PyQt5.QtWidgets import QGraphicsPolygonItem


class Octagon(QGraphicsPolygonItem, ShapeResizableMixin):
    """
    This class implements an octagon which is used to render the 'Individual' node.
    """
    MinWidth = 100.0
    MinHeight = 100.0

    indexLT = 0
    indexLB = 1
    indexBL = 2
    indexBR = 3
    indexRB = 4
    indexRT = 5
    indexTR = 6
    indexTL = 7
    indexEE = 8

    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine)

    def __init__(self, **kwargs):
        """
        Initialize the octagon shape.
        """
        shape_w = max(kwargs.pop('width', self.MinWidth), self.MinWidth)
        shape_h = max(kwargs.pop('height', self.MinHeight), self.MinHeight)

        super().__init__(**kwargs)

        # initialize the polygon
        self.setPolygon(Octagon.getPolygon(shape_w, shape_h))

        # initialize shape label with default text
        self.label = Label(self.node.name, parent=self)

        # calculate positions
        self.updateHandlesPos()
        self.updateLabelPos()

    ################################################## EVENT HANDLERS ##################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu for the given node.
        :param menuEvent: the context menu event instance.
        """
        scene = self.scene()
        scene.clearSelection()

        self.setSelected(True)

        contextMenu = self.contextMenu()

        collection = self.label.contextMenuAdd()
        if collection:
            contextMenu.addSeparator()
            for action in collection:
                contextMenu.addAction(action)

        contextMenu.exec_(menuEvent.screenPos())

    ##################################################### GEOMETRY #####################################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        polygon = self.polygon()
        offset = self.handleSize + self.handleSpan
        x = polygon[self.indexLT].x()
        y = polygon[self.indexTL].y()
        w = polygon[self.indexRT].x() - x
        h = polygon[self.indexBL].y() - y
        return QRectF(x - offset, y - offset, w + offset * 2, h + offset * 2)

    def interactiveResize(self, handle, fromRect, mousePressedPos, mousePos):
        """
        Handle the interactive resize of the shape.
        :type handle: int
        :type fromRect: QRectF
        :type mousePressedPos: QPointF
        :type mousePos: QPointF
        :param handle: the currently selected resizing handle.
        :param fromRect: the bouding rect before the resizing operation started.
        :param mousePressedPos: the position where the mouse has been pressed.
        :param mousePos: the current mouse position.
        """
        scene = self.scene()
        toPoly = self.polygon()
        toRect = self.boundingRect()
        doSnap = scene.settings.value('scene/snap_to_grid', False, bool)
        offset = self.handleSize + self.handleSpan

        minBoundingRectWidth = self.MinWidth + (self.handleSize + self.handleSpan) * 2
        minBoundingRectHeight = self.MinHeight + (self.handleSize + self.handleSpan) * 2

        if handle == self.handleTL:

            newX = fromRect.left() + mousePos.x() - mousePressedPos.x()
            newY = fromRect.top() + mousePos.y() - mousePressedPos.y()
            newX = snapPointToGrid(newX, scene.GridSize, -offset, doSnap)
            newY = snapPointToGrid(newY, scene.GridSize, -offset, doSnap)
            toRect.setLeft(newX)
            toRect.setTop(newY)

            ## CLAMP SIZE
            if toRect.width() < minBoundingRectWidth:
                toRect.setLeft(toRect.left() - minBoundingRectWidth + toRect.width())
            if toRect.height() < minBoundingRectHeight:
                toRect.setTop(toRect.top() - minBoundingRectHeight + toRect.height())

            newSideY = (toRect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (toRect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (toRect.y() + toRect.height() / 2) + newSideY / 2
            newLeftRightTopY = (toRect.y() + toRect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (toRect.x() + toRect.width() / 2) - newSideX / 2
            newTopBottomRightX = (toRect.x() + toRect.width() / 2) + newSideX / 2

            toPoly[self.indexLT] = QPointF(toRect.left() + offset, newLeftRightTopY)
            toPoly[self.indexLB] = QPointF(toRect.left() + offset, newLeftRightBottomY)
            toPoly[self.indexRT] = QPointF(toRect.right() - offset, newLeftRightTopY)
            toPoly[self.indexRB] = QPointF(toRect.right() - offset, newLeftRightBottomY)
            toPoly[self.indexTL] = QPointF(newTopBottomLeftX, toRect.top() + offset)
            toPoly[self.indexTR] = QPointF(newTopBottomRightX, toRect.top() + offset)
            toPoly[self.indexBL] = QPointF(newTopBottomLeftX, toRect.bottom() - offset)
            toPoly[self.indexBR] = QPointF(newTopBottomRightX, toRect.bottom() - offset)
            toPoly[self.indexEE] = QPointF(toRect.left() + offset, newLeftRightTopY)

        elif handle == self.handleTM:

            newY = fromRect.top() + mousePos.y() - mousePressedPos.y()
            newY = snapPointToGrid(newY, scene.GridSize, -offset, doSnap)
            toRect.setTop(newY)

            ## CLAMP SIZE
            if toRect.height() < minBoundingRectHeight:
                toRect.setTop(toRect.top() - minBoundingRectHeight + toRect.height())

            newSide = (toRect.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (toRect.y() + toRect.height() / 2) + newSide / 2
            newLeftRightTopY = (toRect.y() + toRect.height() / 2) - newSide / 2

            toPoly[self.indexTL] = QPointF(toPoly[self.indexTL].x(), toRect.top() + offset)
            toPoly[self.indexTR] = QPointF(toPoly[self.indexTR].x(), toRect.top() + offset)
            toPoly[self.indexLB] = QPointF(toPoly[self.indexLB].x(), newLeftRightBottomY)
            toPoly[self.indexRB] = QPointF(toPoly[self.indexRB].x(), newLeftRightBottomY)
            toPoly[self.indexLT] = QPointF(toPoly[self.indexLT].x(), newLeftRightTopY)
            toPoly[self.indexRT] = QPointF(toPoly[self.indexRT].x(), newLeftRightTopY)
            toPoly[self.indexEE] = QPointF(toPoly[self.indexEE].x(), newLeftRightTopY)

        elif handle == self.handleTR:

            newX = fromRect.right() + mousePos.x() - mousePressedPos.x()
            newY = fromRect.top() + mousePos.y() - mousePressedPos.y()
            newX = snapPointToGrid(newX, scene.GridSize, +offset, doSnap)
            newY = snapPointToGrid(newY, scene.GridSize, -offset, doSnap)
            toRect.setRight(newX)
            toRect.setTop(newY)

            ## CLAMP SIZE
            if toRect.width() < minBoundingRectWidth:
                toRect.setRight(toRect.right() + minBoundingRectWidth - toRect.width())
            if toRect.height() < minBoundingRectHeight:
                toRect.setTop(toRect.top() - minBoundingRectHeight + toRect.height())

            newSideY = (toRect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (toRect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (toRect.y() + toRect.height() / 2) + newSideY / 2
            newLeftRightTopY = (toRect.y() + toRect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (toRect.x() + toRect.width() / 2) - newSideX / 2
            newTopBottomRightX = (toRect.x() + toRect.width() / 2) + newSideX / 2

            toPoly[self.indexLT] = QPointF(toRect.left() + offset, newLeftRightTopY)
            toPoly[self.indexLB] = QPointF(toRect.left() + offset, newLeftRightBottomY)
            toPoly[self.indexRT] = QPointF(toRect.right() - offset, newLeftRightTopY)
            toPoly[self.indexRB] = QPointF(toRect.right() - offset, newLeftRightBottomY)
            toPoly[self.indexTL] = QPointF(newTopBottomLeftX, toRect.top() + offset)
            toPoly[self.indexTR] = QPointF(newTopBottomRightX, toRect.top() + offset)
            toPoly[self.indexBL] = QPointF(newTopBottomLeftX, toRect.bottom() - offset)
            toPoly[self.indexBR] = QPointF(newTopBottomRightX, toRect.bottom() - offset)
            toPoly[self.indexEE] = QPointF(toRect.left() + offset, newLeftRightTopY)

        elif handle == self.handleML:

            newX = fromRect.left() + mousePos.x() - mousePressedPos.x()
            newX = snapPointToGrid(newX, scene.GridSize, -offset, doSnap)
            toRect.setLeft(newX)

            ## CLAMP SIZE
            if toRect.width() < minBoundingRectWidth:
                toRect.setLeft(toRect.left() - minBoundingRectWidth + toRect.width())

            newSide = (toRect.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomLeftX = (toRect.x() + toRect.width() / 2) - newSide / 2
            newTopBottomRightX = (toRect.x() + toRect.width() / 2) + newSide / 2

            toPoly[self.indexLT] = QPointF(toRect.left() + offset, toPoly[self.indexLT].y())
            toPoly[self.indexLB] = QPointF(toRect.left() + offset, toPoly[self.indexLB].y())
            toPoly[self.indexEE] = QPointF(toRect.left() + offset, toPoly[self.indexEE].y())
            toPoly[self.indexTL] = QPointF(newTopBottomLeftX, toPoly[self.indexTL].y())
            toPoly[self.indexTR] = QPointF(newTopBottomRightX, toPoly[self.indexTR].y())
            toPoly[self.indexBL] = QPointF(newTopBottomLeftX, toPoly[self.indexBL].y())
            toPoly[self.indexBR] = QPointF(newTopBottomRightX, toPoly[self.indexBR].y())

        elif handle == self.handleMR:

            newX = fromRect.right() + mousePos.x() - mousePressedPos.x()
            newX = snapPointToGrid(newX, scene.GridSize, +offset, doSnap)
            toRect.setRight(newX)

            ## CLAMP SIZE
            if toRect.width() < minBoundingRectWidth:
                toRect.setRight(toRect.right() + minBoundingRectWidth - toRect.width())

            newSide = (toRect.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomRightX = (toRect.x() + toRect.width() / 2) + newSide / 2
            newTopBottomLeftX = (toRect.x() + toRect.width() / 2) - newSide / 2

            toPoly[self.indexRT] = QPointF(toRect.right() - offset, toPoly[self.indexRT].y())
            toPoly[self.indexRB] = QPointF(toRect.right() - offset, toPoly[self.indexRB].y())
            toPoly[self.indexTL] = QPointF(newTopBottomLeftX, toPoly[self.indexTL].y())
            toPoly[self.indexTR] = QPointF(newTopBottomRightX, toPoly[self.indexTR].y())
            toPoly[self.indexBL] = QPointF(newTopBottomLeftX, toPoly[self.indexBL].y())
            toPoly[self.indexBR] = QPointF(newTopBottomRightX, toPoly[self.indexBR].y())

        elif handle == self.handleBL:

            newX = fromRect.left() + mousePos.x() - mousePressedPos.x()
            newY = fromRect.bottom() + mousePos.y() - mousePressedPos.y()
            newX = snapPointToGrid(newX, scene.GridSize, -offset, doSnap)
            newY = snapPointToGrid(newY, scene.GridSize, +offset, doSnap)
            toRect.setLeft(newX)
            toRect.setBottom(newY)

            ## CLAMP SIZE
            if toRect.width() < minBoundingRectWidth:
                toRect.setLeft(toRect.left() - minBoundingRectWidth + toRect.width())
            if toRect.height() < minBoundingRectHeight:
                toRect.setBottom(toRect.bottom() + minBoundingRectHeight - toRect.height())

            newSideY = (toRect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (toRect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (toRect.y() + toRect.height() / 2) + newSideY / 2
            newLeftRightTopY = (toRect.y() + toRect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (toRect.x() + toRect.width() / 2) - newSideX / 2
            newTopBottomRightX = (toRect.x() + toRect.width() / 2) + newSideX / 2

            toPoly[self.indexLT] = QPointF(toRect.left() + offset, newLeftRightTopY)
            toPoly[self.indexLB] = QPointF(toRect.left() + offset, newLeftRightBottomY)
            toPoly[self.indexRT] = QPointF(toRect.right() - offset, newLeftRightTopY)
            toPoly[self.indexRB] = QPointF(toRect.right() - offset, newLeftRightBottomY)
            toPoly[self.indexTL] = QPointF(newTopBottomLeftX, toRect.top() + offset)
            toPoly[self.indexTR] = QPointF(newTopBottomRightX, toRect.top() + offset)
            toPoly[self.indexBL] = QPointF(newTopBottomLeftX, toRect.bottom() - offset)
            toPoly[self.indexBR] = QPointF(newTopBottomRightX, toRect.bottom() - offset)
            toPoly[self.indexEE] = QPointF(toRect.left() + offset, newLeftRightTopY)

        elif handle == self.handleBM:

            newY = fromRect.bottom() + mousePos.y() - mousePressedPos.y()
            newY = snapPointToGrid(newY, scene.GridSize, +offset, doSnap)
            toRect.setBottom(newY)

            ## CLAMP SIZE
            if toRect.height() < minBoundingRectHeight:
                toRect.setBottom(toRect.bottom() + minBoundingRectHeight - toRect.height())

            newSide = (toRect.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightTopY = (toRect.y() + toRect.height() / 2) - newSide / 2
            newLeftRightBottomY = (toRect.y() + toRect.height() / 2) + newSide / 2

            toPoly[self.indexBL] = QPointF(toPoly[self.indexBL].x(), toRect.bottom() - offset)
            toPoly[self.indexBR] = QPointF(toPoly[self.indexBR].x(), toRect.bottom() - offset)
            toPoly[self.indexLB] = QPointF(toPoly[self.indexLB].x(), newLeftRightBottomY)
            toPoly[self.indexRB] = QPointF(toPoly[self.indexRB].x(), newLeftRightBottomY)
            toPoly[self.indexLT] = QPointF(toPoly[self.indexLT].x(), newLeftRightTopY)
            toPoly[self.indexRT] = QPointF(toPoly[self.indexRT].x(), newLeftRightTopY)
            toPoly[self.indexEE] = QPointF(toPoly[self.indexEE].x(), newLeftRightTopY)

        elif handle == self.handleBR:

            newX = fromRect.right() + mousePos.x() - mousePressedPos.x()
            newY = fromRect.bottom() + mousePos.y() - mousePressedPos.y()
            newX = snapPointToGrid(newX, scene.GridSize, +offset, doSnap)
            newY = snapPointToGrid(newY, scene.GridSize, +offset, doSnap)
            toRect.setRight(newX)
            toRect.setBottom(newY)

            ## CLAMP SIZE
            if toRect.width() < minBoundingRectWidth:
                toRect.setRight(toRect.right() + minBoundingRectWidth - toRect.width())
            if toRect.height() < minBoundingRectHeight:
                toRect.setBottom(toRect.bottom() + minBoundingRectHeight - toRect.height())

            newSideY = (toRect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (toRect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (toRect.y() + toRect.height() / 2) + newSideY / 2
            newLeftRightTopY = (toRect.y() + toRect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (toRect.x() + toRect.width() / 2) - newSideX / 2
            newTopBottomRightX = (toRect.x() + toRect.width() / 2) + newSideX / 2

            toPoly[self.indexLT] = QPointF(toRect.left() + offset, newLeftRightTopY)
            toPoly[self.indexLB] = QPointF(toRect.left() + offset, newLeftRightBottomY)
            toPoly[self.indexRT] = QPointF(toRect.right() - offset, newLeftRightTopY)
            toPoly[self.indexRB] = QPointF(toRect.right() - offset, newLeftRightBottomY)
            toPoly[self.indexTL] = QPointF(newTopBottomLeftX, toRect.top() + offset)
            toPoly[self.indexTR] = QPointF(newTopBottomRightX, toRect.top() + offset)
            toPoly[self.indexBL] = QPointF(newTopBottomLeftX, toRect.bottom() - offset)
            toPoly[self.indexBR] = QPointF(newTopBottomRightX, toRect.bottom() - offset)
            toPoly[self.indexEE] = QPointF(toRect.left() + offset, newLeftRightTopY)

        self.prepareGeometryChange()
        self.setPolygon(toPoly)
        self.updateHandlesPos()
        self.updateLabelPos()

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    ################################################ AUXILIARY METHODS #################################################

    @staticmethod
    def getPolygon(shape_w, shape_h):
        """
        Returns the initialized polygon according to the given width/height.
        :param shape_w: the shape width
        :param shape_h: the shape height
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-(shape_w / 2), -((shape_h / (1 + math.sqrt(2))) / 2)), # 0
            QPointF(-(shape_w / 2), +((shape_h / (1 + math.sqrt(2))) / 2)), # 1
            QPointF(-((shape_w / (1 + math.sqrt(2))) / 2), +(shape_h / 2)), # 2
            QPointF(+((shape_w / (1 + math.sqrt(2))) / 2), +(shape_h / 2)), # 3
            QPointF(+(shape_w / 2), +((shape_h / (1 + math.sqrt(2))) / 2)), # 4
            QPointF(+(shape_w / 2), -((shape_h / (1 + math.sqrt(2))) / 2)), # 5
            QPointF(+((shape_w / (1 + math.sqrt(2))) / 2), -(shape_h / 2)), # 6
            QPointF(-((shape_w / (1 + math.sqrt(2))) / 2), -(shape_h / 2)), # 7
            QPointF(-(shape_w / 2), -((shape_h / (1 + math.sqrt(2))) / 2)), # 8
        ])

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.boundingRect().height() - 2 * (self.handleSize + self.handleSpan)

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :param line: the line whose intersection needs to be calculated (in scene coordinates).
        :rtype: QPointF
        """
        intersection = QPointF()
        polygon = self.mapToScene(self.polygon())

        for i in range(0, polygon.size() - 1):
            polyline = QLineF(polygon[i], polygon[i + 1])
            if polyline.intersect(line, intersection) == QLineF.BoundedIntersection:
                return intersection

        return None

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.boundingRect().width() - 2 * (self.handleSize + self.handleSpan)

    ################################################### ITEM DRAWING ###################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        shape_w = 40
        shape_h = 40

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the shape
        polygon = Octagon.getPolygon(shape_w, shape_h)

        # Draw the polygon
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)

        # Draw the text within the rectangle
        painter.setFont(QFont('Arial', 9, QFont.Light))
        painter.drawText(-18, 4, 'individual')

        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        # Select the correct brush for the shape
        shapeBrush = self.shapeSelectedBrush if self.isSelected() else self.shapeBrush

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawPolygon(self.polygon())

        if self.isSelected():
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(self.handleBrush)
            painter.setPen(self.handlePen)
            for handle, rect in self.handles.items():
                if self.selectedHandle is None or handle == self.selectedHandle:
                    painter.drawEllipse(rect)