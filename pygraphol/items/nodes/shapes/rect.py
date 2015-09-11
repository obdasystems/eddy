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
from PyQt5.QtCore import QPointF, QRectF, Qt, QLineF
from PyQt5.QtGui import QPainterPath, QPainter, QPixmap, QPen, QColor, QFont, QPolygonF
from PyQt5.QtWidgets import QGraphicsRectItem


class Rect(QGraphicsRectItem, ShapeResizableMixin):
    """
    This class implements a rectangle which is used to render the 'Concept' node.
    """
    MinWidth = 140.0
    MinHeight = 60.0

    def __init__(self, **kwargs):
        """
        Initialize the rectangle shape.
        """
        shape_w = max(kwargs.pop('width', self.MinWidth), self.MinWidth)
        shape_h = max(kwargs.pop('height', self.MinHeight), self.MinHeight)
        
        super().__init__(**kwargs)

        # initialize shape rectangle
        self.setRect(Rect.getRect(shape_w, shape_h))

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
        offset = self.handleSize + self.handleSpan
        return self.rect().adjusted(-offset, -offset, offset, offset)

    def interactiveResize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :param mousePos: the current mouse position.
        """
        scene = self.scene()
        snap = scene.settings.value('scene/snap_to_grid', False, bool)
        rect = self.rect()
        diff = QPointF(0, 0)

        if self.selectedHandle == self.handleTL:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapPointToGrid(toX, scene.GridSize, snap=snap)
            toY = snapPointToGrid(toY, scene.GridSize, snap=snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setLeft(toX)
            rect.setTop(toY)

        elif self.selectedHandle == self.handleTM:

            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapPointToGrid(toY, scene.GridSize, snap=snap)
            diff.setY(toY - fromY)
            rect.setTop(toY)

        elif self.selectedHandle == self.handleTR:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapPointToGrid(toX, scene.GridSize, snap=snap)
            toY = snapPointToGrid(toY, scene.GridSize, snap=snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setRight(toX)
            rect.setTop(toY)

        elif self.selectedHandle == self.handleML:

            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapPointToGrid(toX, scene.GridSize, snap=snap)
            diff.setX(toX - fromX)
            rect.setLeft(toX)

        elif self.selectedHandle == self.handleMR:

            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapPointToGrid(toX, scene.GridSize, snap=snap)
            diff.setX(toX - fromX)
            rect.setRight(toX)

        elif self.selectedHandle == self.handleBL:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapPointToGrid(toX, scene.GridSize, snap=snap)
            toY = snapPointToGrid(toY, scene.GridSize, snap=snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setLeft(toX)
            rect.setBottom(toY)

        elif self.selectedHandle == self.handleBM:

            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapPointToGrid(toY, scene.GridSize, snap=snap)
            diff.setY(toY - fromY)
            rect.setBottom(toY)

        elif self.selectedHandle == self.handleBR:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapPointToGrid(toX, scene.GridSize, snap=snap)
            toY = snapPointToGrid(toY, scene.GridSize, snap=snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setRight(toX)
            rect.setBottom(toY)

        ## CLAMP WIDTH
        if self.selectedHandle in (self.handleTL, self.handleML, self.handleBL):
            if rect.width() < self.MinWidth:
                diff.setX(diff.x() - self.MinWidth + rect.width())
                rect.setLeft(rect.left() - self.MinWidth + rect.width())
        elif self.selectedHandle in (self.handleTR, self.handleMR, self.handleBR):
            if rect.width() < self.MinWidth:
                diff.setX(diff.x() + self.MinWidth - rect.width())
                rect.setRight(rect.right() + self.MinWidth - rect.width())

        ## CLAMP HEIGHT
        if self.selectedHandle in (self.handleTL, self.handleTM, self.handleTR):
            if rect.height() < self.MinHeight:
                diff.setY(diff.y() - self.MinHeight + rect.height())
                rect.setTop(rect.top() - self.MinHeight + rect.height())
        elif self.selectedHandle in (self.handleBL, self.handleBM, self.handleBR):
            if rect.height() < self.MinHeight:
                diff.setY(diff.y() + self.MinHeight - rect.height())
                rect.setBottom(rect.bottom() + self.MinHeight - rect.height())

        self.prepareGeometryChange()
        self.setRect(rect)
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
    def getRect(shape_w, shape_h):
        """
        Returns the initialized rect according to the given width/height.
        :param shape_w: the shape width
        :param shape_h: the shape height
        :rtype: QRectF
        """
        return QRectF(-shape_w / 2, -shape_h / 2, shape_w, shape_h)

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.rect().height()

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :param line: the line whose intersection needs to be calculated (in scene coordinates).
        :rtype: QPointF
        """
        intersection = QPointF()
        polygon = self.mapToScene(QPolygonF(self.rect()))

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
        return self.rect().width()

    ################################################### ITEM DRAWING ###################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        shape_w = 54
        shape_h = 34

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)

        # Initialize the shape
        rect = Rect.getRect(shape_w, shape_h)

        # Draw the rectangle
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRect(rect)

        # Draw the text within the rectangle
        painter.setFont(QFont('Arial', 11, QFont.Light))
        painter.drawText(rect, Qt.AlignCenter, 'concept')

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
        painter.drawRect(self.rect())

        if self.isSelected():
            # Draw resize handles only if the shape is selected
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(self.handleBrush)
            painter.setPen(self.handlePen)
            for handle, rect in self.handles.items():
                if self.selectedHandle is None or handle == self.selectedHandle:
                    painter.drawEllipse(rect)