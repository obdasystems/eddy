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

        if self.selectedHandle == self.handleTL:

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

            poly[self.indexT] = QPointF(rect.left() + rect.width() / 2, rect.top() + offset)
            poly[self.indexB] = QPointF(rect.left() + rect.width() / 2, poly[self.indexB].y())
            poly[self.indexL] = QPointF(rect.left() + offset, rect.top() + rect.height() / 2)
            poly[self.indexE] = QPointF(rect.left() + offset, rect.top() + rect.height() / 2)
            poly[self.indexR] = QPointF(poly[self.indexR].x(), rect.top() + rect.height() / 2)

        elif self.selectedHandle == self.handleTM:

            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapPointToGrid(toY, scene.GridSize, -offset, snap)
            diff.setY(toY - fromY)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.height() < minBoundingRectHeight:
                diff.setY(diff.y() - minBoundingRectHeight + rect.height())
                rect.setTop(rect.top() - minBoundingRectHeight + rect.height())

            poly[self.indexT] = QPointF(poly[self.indexT].x(), rect.top() + offset)
            poly[self.indexL] = QPointF(poly[self.indexL].x(), rect.top() + rect.height() / 2)
            poly[self.indexE] = QPointF(poly[self.indexE].x(), rect.top() + rect.height() / 2)
            poly[self.indexR] = QPointF(poly[self.indexR].x(), rect.top() + rect.height() / 2)

        elif self.selectedHandle == self.handleTR:

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

            poly[self.indexT] = QPointF(rect.right() - rect.width() / 2, rect.top() + offset)
            poly[self.indexB] = QPointF(rect.right() - rect.width() / 2, poly[self.indexB].y())
            poly[self.indexL] = QPointF(poly[self.indexL].x(), rect.top() + rect.height() / 2)
            poly[self.indexE] = QPointF(poly[self.indexE].x(), rect.top() + rect.height() / 2)
            poly[self.indexR] = QPointF(rect.right() - offset, rect.top() + rect.height() / 2)

        elif self.selectedHandle == self.handleML:

            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapPointToGrid(toX, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            rect.setLeft(toX)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectWidth:
                diff.setX(diff.x() - minBoundingRectWidth + rect.width())
                rect.setLeft(rect.left() - minBoundingRectWidth + rect.width())

            poly[self.indexL] = QPointF(rect.left() + offset, self.mousePressRect.top() + self.mousePressRect.height() / 2)
            poly[self.indexE] = QPointF(rect.left() + offset, self.mousePressRect.top() + self.mousePressRect.height() / 2)
            poly[self.indexT] = QPointF(rect.left() + rect.width() / 2, poly[self.indexT].y())
            poly[self.indexB] = QPointF(rect.left() + rect.width() / 2, poly[self.indexB].y())

        elif self.selectedHandle == self.handleMR:

            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapPointToGrid(toX, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            rect.setRight(toX)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectWidth:
                diff.setX(diff.x() + minBoundingRectWidth - rect.width())
                rect.setRight(rect.right() + minBoundingRectWidth - rect.width())

            poly[self.indexR] = QPointF(rect.right() - offset, self.mousePressRect.top() + self.mousePressRect.height() / 2)
            poly[self.indexT] = QPointF(rect.right() - rect.width() / 2, poly[self.indexT].y())
            poly[self.indexB] = QPointF(rect.right() - rect.width() / 2, poly[self.indexB].y())

        elif self.selectedHandle == self.handleBL:

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

            poly[self.indexT] = QPointF(rect.left() + rect.width() / 2, poly[self.indexT].y())
            poly[self.indexB] = QPointF(rect.left() + rect.width() / 2, rect.bottom() - offset)
            poly[self.indexL] = QPointF(rect.left() + offset, rect.bottom() - rect.height() / 2)
            poly[self.indexE] = QPointF(rect.left() + offset, rect.bottom() - rect.height() / 2)
            poly[self.indexR] = QPointF(poly[self.indexR].x(), rect.bottom() - rect.height() / 2)

        elif self.selectedHandle == self.handleBM:

            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapPointToGrid(toY, scene.GridSize, +offset, snap)
            diff.setY(toY - fromY)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.height() < minBoundingRectHeight:
                diff.setY(diff.y() + minBoundingRectHeight - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectHeight - rect.height())

            poly[self.indexB] = QPointF(poly[self.indexB].x(), rect.bottom() - offset)
            poly[self.indexL] = QPointF(poly[self.indexL].x(), rect.top() + rect.height() / 2)
            poly[self.indexE] = QPointF(poly[self.indexE].x(), rect.top() + rect.height() / 2)
            poly[self.indexR] = QPointF(poly[self.indexR].x(), rect.top() + rect.height() / 2)

        elif self.selectedHandle == self.handleBR:

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

            poly[self.indexT] = QPointF(rect.right() - rect.width() / 2, poly[self.indexT].y())
            poly[self.indexB] = QPointF(rect.right() - rect.width() / 2, rect.bottom() - offset)
            poly[self.indexL] = QPointF(poly[self.indexL].x(), rect.bottom() - rect.height() / 2)
            poly[self.indexE] = QPointF(poly[self.indexE].x(), rect.bottom() - rect.height() / 2)
            poly[self.indexR] = QPointF(rect.right() - offset, rect.bottom() - rect.height() / 2)

        self.prepareGeometryChange()
        self.setPolygon(poly)
        self.updateHandlesPos()
        self.updateLabelPos()

        # update edge anchors
        for edge, pos in self.mousePressData.items():
            self.setAnchor(edge, pos + diff * 0.5)

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

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used to detect the collision between items in the graphics scene).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon())
        return path

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
        shapeBrush = self.shapeSelectedBrush if self.isSelected() else self.shapeBrush

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawPolygon(self.polygon())

        self.paintHandles(painter, option, widget)