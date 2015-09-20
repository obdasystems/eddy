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
from pygraphol.items.nodes.shapes.mixins import ShapeResizableMixin, Handle
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
        self.setPolygon(Octagon.createPolygon(shape_w, shape_h))

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

    def interactiveResize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :param mousePos: the current mouse position.
        """
        scene = self.scene()
        offset = self.handleSize + self.handleSpan
        snap = scene.settings.value('scene/snap_to_grid', False, bool)
        poly = self.polygon()
        rect = self.boundingRect()
        diff = QPointF(0, 0)
    
        minBoundingRectWidth = self.MinWidth + (self.handleSize + self.handleSpan) * 2
        minBoundingRectHeight = self.MinHeight + (self.handleSize + self.handleSpan) * 2

        if self.selectedHandle == Handle.TL:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapPointToGrid(toX, scene.GridSize, -offset, snap)
            toY = snapPointToGrid(toY, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setLeft(toX)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectWidth:
                diff.setX(diff.x() - minBoundingRectWidth + rect.width())
                rect.setLeft(rect.left() - minBoundingRectWidth + rect.width())
            if rect.height() < minBoundingRectHeight:
                diff.setY(diff.y() - minBoundingRectHeight + rect.height())
                rect.setTop(rect.top() - minBoundingRectHeight + rect.height())

            newSideY = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSideY / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSideX / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSideX / 2

            poly[self.indexLT] = QPointF(rect.left() + offset, newLeftRightTopY)
            poly[self.indexLB] = QPointF(rect.left() + offset, newLeftRightBottomY)
            poly[self.indexRT] = QPointF(rect.right() - offset, newLeftRightTopY)
            poly[self.indexRB] = QPointF(rect.right() - offset, newLeftRightBottomY)
            poly[self.indexTL] = QPointF(newTopBottomLeftX, rect.top() + offset)
            poly[self.indexTR] = QPointF(newTopBottomRightX, rect.top() + offset)
            poly[self.indexBL] = QPointF(newTopBottomLeftX, rect.bottom() - offset)
            poly[self.indexBR] = QPointF(newTopBottomRightX, rect.bottom() - offset)
            poly[self.indexEE] = QPointF(rect.left() + offset, newLeftRightTopY)

        elif self.selectedHandle == Handle.TM:

            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapPointToGrid(toY, scene.GridSize, -offset, snap)
            diff.setY(toY - fromY)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.height() < minBoundingRectHeight:
                diff.setY(diff.y() - minBoundingRectHeight + rect.height())
                rect.setTop(rect.top() - minBoundingRectHeight + rect.height())

            newSide = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSide / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSide / 2

            poly[self.indexTL] = QPointF(poly[self.indexTL].x(), rect.top() + offset)
            poly[self.indexTR] = QPointF(poly[self.indexTR].x(), rect.top() + offset)
            poly[self.indexLB] = QPointF(poly[self.indexLB].x(), newLeftRightBottomY)
            poly[self.indexRB] = QPointF(poly[self.indexRB].x(), newLeftRightBottomY)
            poly[self.indexLT] = QPointF(poly[self.indexLT].x(), newLeftRightTopY)
            poly[self.indexRT] = QPointF(poly[self.indexRT].x(), newLeftRightTopY)
            poly[self.indexEE] = QPointF(poly[self.indexEE].x(), newLeftRightTopY)

        elif self.selectedHandle == Handle.TR:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapPointToGrid(toX, scene.GridSize, +offset, snap)
            toY = snapPointToGrid(toY, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setRight(toX)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectWidth:
                diff.setX(diff.x() + minBoundingRectWidth - rect.width())
                rect.setRight(rect.right() + minBoundingRectWidth - rect.width())
            if rect.height() < minBoundingRectHeight:
                diff.setY(diff.y() - minBoundingRectHeight + rect.height())
                rect.setTop(rect.top() - minBoundingRectHeight + rect.height())

            newSideY = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSideY / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSideX / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSideX / 2

            poly[self.indexLT] = QPointF(rect.left() + offset, newLeftRightTopY)
            poly[self.indexLB] = QPointF(rect.left() + offset, newLeftRightBottomY)
            poly[self.indexRT] = QPointF(rect.right() - offset, newLeftRightTopY)
            poly[self.indexRB] = QPointF(rect.right() - offset, newLeftRightBottomY)
            poly[self.indexTL] = QPointF(newTopBottomLeftX, rect.top() + offset)
            poly[self.indexTR] = QPointF(newTopBottomRightX, rect.top() + offset)
            poly[self.indexBL] = QPointF(newTopBottomLeftX, rect.bottom() - offset)
            poly[self.indexBR] = QPointF(newTopBottomRightX, rect.bottom() - offset)
            poly[self.indexEE] = QPointF(rect.left() + offset, newLeftRightTopY)

        elif self.selectedHandle == Handle.ML:

            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapPointToGrid(toX, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            rect.setLeft(toX)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectWidth:
                diff.setX(diff.x() - minBoundingRectWidth + rect.width())
                rect.setLeft(rect.left() - minBoundingRectWidth + rect.width())

            newSide = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSide / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSide / 2

            poly[self.indexLT] = QPointF(rect.left() + offset, poly[self.indexLT].y())
            poly[self.indexLB] = QPointF(rect.left() + offset, poly[self.indexLB].y())
            poly[self.indexEE] = QPointF(rect.left() + offset, poly[self.indexEE].y())
            poly[self.indexTL] = QPointF(newTopBottomLeftX, poly[self.indexTL].y())
            poly[self.indexTR] = QPointF(newTopBottomRightX, poly[self.indexTR].y())
            poly[self.indexBL] = QPointF(newTopBottomLeftX, poly[self.indexBL].y())
            poly[self.indexBR] = QPointF(newTopBottomRightX, poly[self.indexBR].y())

        elif self.selectedHandle == Handle.MR:

            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapPointToGrid(toX, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            rect.setRight(toX)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectWidth:
                diff.setX(diff.x() + minBoundingRectWidth - rect.width())
                rect.setRight(rect.right() + minBoundingRectWidth - rect.width())

            newSide = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSide / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSide / 2

            poly[self.indexRT] = QPointF(rect.right() - offset, poly[self.indexRT].y())
            poly[self.indexRB] = QPointF(rect.right() - offset, poly[self.indexRB].y())
            poly[self.indexTL] = QPointF(newTopBottomLeftX, poly[self.indexTL].y())
            poly[self.indexTR] = QPointF(newTopBottomRightX, poly[self.indexTR].y())
            poly[self.indexBL] = QPointF(newTopBottomLeftX, poly[self.indexBL].y())
            poly[self.indexBR] = QPointF(newTopBottomRightX, poly[self.indexBR].y())

        elif self.selectedHandle == Handle.BL:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapPointToGrid(toX, scene.GridSize, -offset, snap)
            toY = snapPointToGrid(toY, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setLeft(toX)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectWidth:
                diff.setX(diff.x() - minBoundingRectWidth + rect.width())
                rect.setLeft(rect.left() - minBoundingRectWidth + rect.width())
            if rect.height() < minBoundingRectHeight:
                diff.setY(diff.y() + minBoundingRectHeight - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectHeight - rect.height())

            newSideY = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSideY / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSideX / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSideX / 2

            poly[self.indexLT] = QPointF(rect.left() + offset, newLeftRightTopY)
            poly[self.indexLB] = QPointF(rect.left() + offset, newLeftRightBottomY)
            poly[self.indexRT] = QPointF(rect.right() - offset, newLeftRightTopY)
            poly[self.indexRB] = QPointF(rect.right() - offset, newLeftRightBottomY)
            poly[self.indexTL] = QPointF(newTopBottomLeftX, rect.top() + offset)
            poly[self.indexTR] = QPointF(newTopBottomRightX, rect.top() + offset)
            poly[self.indexBL] = QPointF(newTopBottomLeftX, rect.bottom() - offset)
            poly[self.indexBR] = QPointF(newTopBottomRightX, rect.bottom() - offset)
            poly[self.indexEE] = QPointF(rect.left() + offset, newLeftRightTopY)

        elif self.selectedHandle == Handle.BM:

            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapPointToGrid(toY, scene.GridSize, +offset, snap)
            diff.setY(toY - fromY)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.height() < minBoundingRectHeight:
                diff.setY(diff.y() + minBoundingRectHeight - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectHeight - rect.height())

            newSide = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSide / 2
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSide / 2

            poly[self.indexBL] = QPointF(poly[self.indexBL].x(), rect.bottom() - offset)
            poly[self.indexBR] = QPointF(poly[self.indexBR].x(), rect.bottom() - offset)
            poly[self.indexLB] = QPointF(poly[self.indexLB].x(), newLeftRightBottomY)
            poly[self.indexRB] = QPointF(poly[self.indexRB].x(), newLeftRightBottomY)
            poly[self.indexLT] = QPointF(poly[self.indexLT].x(), newLeftRightTopY)
            poly[self.indexRT] = QPointF(poly[self.indexRT].x(), newLeftRightTopY)
            poly[self.indexEE] = QPointF(poly[self.indexEE].x(), newLeftRightTopY)

        elif self.selectedHandle == Handle.BR:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapPointToGrid(toX, scene.GridSize, +offset, snap)
            toY = snapPointToGrid(toY, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setRight(toX)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectWidth:
                diff.setX(diff.x() + minBoundingRectWidth - rect.width())
                rect.setRight(rect.right() + minBoundingRectWidth - rect.width())
            if rect.height() < minBoundingRectHeight:
                diff.setY(diff.y() + minBoundingRectHeight - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectHeight - rect.height())

            newSideY = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSideY / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSideX / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSideX / 2

            poly[self.indexLT] = QPointF(rect.left() + offset, newLeftRightTopY)
            poly[self.indexLB] = QPointF(rect.left() + offset, newLeftRightBottomY)
            poly[self.indexRT] = QPointF(rect.right() - offset, newLeftRightTopY)
            poly[self.indexRB] = QPointF(rect.right() - offset, newLeftRightBottomY)
            poly[self.indexTL] = QPointF(newTopBottomLeftX, rect.top() + offset)
            poly[self.indexTR] = QPointF(newTopBottomRightX, rect.top() + offset)
            poly[self.indexBL] = QPointF(newTopBottomLeftX, rect.bottom() - offset)
            poly[self.indexBR] = QPointF(newTopBottomRightX, rect.bottom() - offset)
            poly[self.indexEE] = QPointF(rect.left() + offset, newLeftRightTopY)

        self.prepareGeometryChange()
        self.setPolygon(poly)
        self.updateHandlesPos()
        self.updateLabelPos()

        # update edge anchors
        for edge, pos in self.mousePressData.items():
            self.setAnchor(edge, pos + diff * 0.5)

    def shape(self, controls=Handle.TL|Handle.TM|Handle.TR|Handle.ML|Handle.MR|Handle.BL|Handle.BM|Handle.BR):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :param controls: bitflag describing which controls to add to the shape.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon())

        # add resizing handles if necessary
        if controls and self.isSelected():
            for handle, shape in self.handles.items():
                if controls & handle:
                    path.addEllipse(shape)

        return path

    ################################################ AUXILIARY METHODS #################################################

    @staticmethod
    def createPolygon(shape_w, shape_h):
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

    def intersections(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :param line: the line whose intersection needs to be calculated (in scene coordinates).
        :rtype: tuple
        """
        collection = []
        path = self.shape(Handle.TM|Handle.BM|Handle.ML|Handle.MR)
        polygon = self.mapToScene(path.toFillPolygon(self.transform()))

        for i in range(0, polygon.size() - 1):
            point = QPointF()
            polyline = QLineF(polygon[i], polygon[i + 1])
            if polyline.intersect(line, point) == QLineF.BoundedIntersection:
                collection.append(point)

        return collection

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
        polygon = Octagon.createPolygon(shape_w, shape_h)

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
        shapeBrush = self.shapeSelectedBrush if self.isSelected() else self.shapeBrush

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawPolygon(self.polygon())

        self.paintHandles(painter, option, widget)