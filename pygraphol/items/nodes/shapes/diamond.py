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


from pygraphol.functions import snapPointToGrid
from pygraphol.items.nodes.shapes.common import Label
from pygraphol.items.nodes.shapes.mixins import ShapeResizableMixin
from PyQt5.QtCore import QPointF, Qt, QRectF, QLineF
from PyQt5.QtGui import QColor, QPen,  QPainterPath, QPolygonF, QPainter, QFont, QPixmap
from PyQt5.QtWidgets import QGraphicsPolygonItem


class Diamond(QGraphicsPolygonItem, ShapeResizableMixin):
    """
    This class implements a diamond which is used to render the 'Role' node.
    """
    MinWidth = 80.0
    MinHeight = 60.0

    indexL = 0
    indexB = 1
    indexT = 3
    indexR = 2
    indexE = 4

    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine)

    def __init__(self, **kwargs):
        """
        Initialize the diamond.
        """
        shape_w = max(kwargs.pop('width', self.MinWidth), self.MinWidth)
        shape_h = max(kwargs.pop('height', self.MinHeight), self.MinHeight)

        super().__init__(**kwargs)

        # initialize the polygon
        self.setPolygon(Diamond.getPolygon(shape_w, shape_h))

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
        x = polygon[self.indexL].x()
        y = polygon[self.indexT].y()
        w = polygon[self.indexR].x() - x
        h = polygon[self.indexB].y() - y
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

            toPoly[self.indexT] = QPointF(toRect.left() + toRect.width() / 2, toRect.top() + offset)
            toPoly[self.indexB] = QPointF(toRect.left() + toRect.width() / 2, toPoly[self.indexB].y())
            toPoly[self.indexL] = QPointF(toRect.left() + offset, toRect.top() + toRect.height() / 2)
            toPoly[self.indexE] = QPointF(toRect.left() + offset, toRect.top() + toRect.height() / 2)
            toPoly[self.indexR] = QPointF(toPoly[self.indexR].x(), toRect.top() + toRect.height() / 2)

        elif handle == self.handleTM:

            newY = fromRect.top() + mousePos.y() - mousePressedPos.y()
            newY = snapPointToGrid(newY, scene.GridSize, -offset, doSnap)
            toRect.setTop(newY)

            ## CLAMP SIZE
            if toRect.height() < minBoundingRectHeight:
                toRect.setTop(toRect.top() - minBoundingRectHeight + toRect.height())

            toPoly[self.indexT] = QPointF(toPoly[self.indexT].x(), toRect.top() + offset)
            toPoly[self.indexL] = QPointF(toPoly[self.indexL].x(), toRect.top() + toRect.height() / 2)
            toPoly[self.indexE] = QPointF(toPoly[self.indexE].x(), toRect.top() + toRect.height() / 2)
            toPoly[self.indexR] = QPointF(toPoly[self.indexR].x(), toRect.top() + toRect.height() / 2)

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

            toPoly[self.indexT] = QPointF(toRect.right() - toRect.width() / 2, toRect.top() + offset)
            toPoly[self.indexB] = QPointF(toRect.right() - toRect.width() / 2, toPoly[self.indexB].y())
            toPoly[self.indexL] = QPointF(toPoly[self.indexL].x(), toRect.top() + toRect.height() / 2)
            toPoly[self.indexE] = QPointF(toPoly[self.indexE].x(), toRect.top() + toRect.height() / 2)
            toPoly[self.indexR] = QPointF(toRect.right() - offset, toRect.top() + toRect.height() / 2)

        elif handle == self.handleML:

            newX = fromRect.left() + mousePos.x() - mousePressedPos.x()
            newX = snapPointToGrid(newX, scene.GridSize, -offset, doSnap)
            toRect.setLeft(newX)

            ## CLAMP SIZE
            if toRect.width() < minBoundingRectWidth:
                toRect.setLeft(toRect.left() - minBoundingRectWidth + toRect.width())

            toPoly[self.indexL] = QPointF(toRect.left() + offset, fromRect.top() + fromRect.height() / 2)
            toPoly[self.indexE] = QPointF(toRect.left() + offset, fromRect.top() + fromRect.height() / 2)
            toPoly[self.indexT] = QPointF(toRect.left() + toRect.width() / 2, toPoly[self.indexT].y())
            toPoly[self.indexB] = QPointF(toRect.left() + toRect.width() / 2, toPoly[self.indexB].y())

        elif handle == self.handleMR:

            newX = fromRect.right() + mousePos.x() - mousePressedPos.x()
            newX = snapPointToGrid(newX, scene.GridSize, +offset, doSnap)
            toRect.setRight(newX)

            ## CLAMP SIZE
            if toRect.width() < minBoundingRectWidth:
                toRect.setRight(toRect.right() + minBoundingRectWidth - toRect.width())

            toPoly[self.indexR] = QPointF(toRect.right() - offset, fromRect.top() + fromRect.height() / 2)
            toPoly[self.indexT] = QPointF(toRect.right() - toRect.width() / 2, toPoly[self.indexT].y())
            toPoly[self.indexB] = QPointF(toRect.right() - toRect.width() / 2, toPoly[self.indexB].y())

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

            toPoly[self.indexT] = QPointF(toRect.left() + toRect.width() / 2, toPoly[self.indexT].y())
            toPoly[self.indexB] = QPointF(toRect.left() + toRect.width() / 2, toRect.bottom() - offset)
            toPoly[self.indexL] = QPointF(toRect.left() + offset, toRect.bottom() - toRect.height() / 2)
            toPoly[self.indexE] = QPointF(toRect.left() + offset, toRect.bottom() - toRect.height() / 2)
            toPoly[self.indexR] = QPointF(toPoly[self.indexR].x(), toRect.bottom() - toRect.height() / 2)

        elif handle == self.handleBM:

            newY = fromRect.bottom() + mousePos.y() - mousePressedPos.y()
            newY = snapPointToGrid(newY, scene.GridSize, +offset, doSnap)
            toRect.setBottom(newY)

            ## CLAMP SIZE
            if toRect.height() < minBoundingRectHeight:
                toRect.setBottom(toRect.bottom() + minBoundingRectHeight - toRect.height())

            toPoly[self.indexB] = QPointF(toPoly[self.indexB].x(), toRect.bottom() - offset)
            toPoly[self.indexL] = QPointF(toPoly[self.indexL].x(), toRect.top() + toRect.height() / 2)
            toPoly[self.indexE] = QPointF(toPoly[self.indexE].x(), toRect.top() + toRect.height() / 2)
            toPoly[self.indexR] = QPointF(toPoly[self.indexR].x(), toRect.top() + toRect.height() / 2)

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

            toPoly[self.indexT] = QPointF(toRect.right() - toRect.width() / 2, toPoly[self.indexT].y())
            toPoly[self.indexB] = QPointF(toRect.right() - toRect.width() / 2, toRect.bottom() - offset)
            toPoly[self.indexL] = QPointF(toPoly[self.indexL].x(), toRect.bottom() - toRect.height() / 2)
            toPoly[self.indexE] = QPointF(toPoly[self.indexE].x(), toRect.bottom() - toRect.height() / 2)
            toPoly[self.indexR] = QPointF(toRect.right() - offset, toRect.bottom() - toRect.height() / 2)

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
            QPointF(-shape_w / 2, 0),
            QPointF(0, +shape_h / 2),
            QPointF(+shape_w / 2, 0),
            QPointF(0, -shape_h / 2),
            QPointF(-shape_w / 2, 0)
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
        shape_w = 46
        shape_h = 34

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the shape
        polygon = Diamond.getPolygon(shape_w, shape_h)

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)

        # Draw the text within the rectangle
        painter.setFont(QFont('Arial', 11, QFont.Light))
        painter.drawText(polygon.boundingRect(), Qt.AlignCenter, 'role')

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

        # # Draw the polygon
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