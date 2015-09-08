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
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainterPath, QPainter, QPixmap, QPen, QColor, QFont
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

    def interactiveResize(self, handle, fromRect, mousePressedPos, mousePos):
        """
        Handle the interactive resize of the shape.
        :type handle: int
        :type fromRect: QRectF
        :type mousePressedPos: QPointF
        :type mousePos: QPointF
        :param handle: the currently selected resizing handle.
        :param fromRect: the rect before the resizing operation started.
        :param mousePressedPos: the position where the mouse has been pressed.
        :param mousePos: the current mouse position.
        """
        scene = self.scene()
        toRect = self.rect()
        doSnap = scene.settings.value('scene/snap_to_grid', False, bool)

        if handle == self.handleTL:
            newX = fromRect.left() + mousePos.x() - mousePressedPos.x()
            newY = fromRect.top() + mousePos.y() - mousePressedPos.y()
            newX = snapPointToGrid(newX, scene.GridSize, snap=doSnap)
            newY = snapPointToGrid(newY, scene.GridSize, snap=doSnap)
            toRect.setLeft(newX)
            toRect.setTop(newY)
        elif handle == self.handleTM:
            newY = fromRect.top() + mousePos.y() - mousePressedPos.y()
            newY = snapPointToGrid(newY, scene.GridSize, snap=doSnap)
            toRect.setTop(newY)
        elif handle == self.handleTR:
            newX = fromRect.right() + mousePos.x() - mousePressedPos.x()
            newY = fromRect.top() + mousePos.y() - mousePressedPos.y()
            newX = snapPointToGrid(newX, scene.GridSize, snap=doSnap)
            newY = snapPointToGrid(newY, scene.GridSize, snap=doSnap)
            toRect.setRight(newX)
            toRect.setTop(newY)
        elif handle == self.handleML:
            newX = fromRect.left() + mousePos.x() - mousePressedPos.x()
            newX = snapPointToGrid(newX, scene.GridSize, snap=doSnap)
            toRect.setLeft(newX)
        elif handle == self.handleMR:
            newX = fromRect.right() + mousePos.x() - mousePressedPos.x()
            newX = snapPointToGrid(newX, scene.GridSize, snap=doSnap)
            toRect.setRight(newX)
        elif handle == self.handleBL:
            newX = fromRect.left() + mousePos.x() - mousePressedPos.x()
            newY = fromRect.bottom() + mousePos.y() - mousePressedPos.y()
            newX = snapPointToGrid(newX, scene.GridSize, snap=doSnap)
            newY = snapPointToGrid(newY, scene.GridSize, snap=doSnap)
            toRect.setLeft(newX)
            toRect.setBottom(newY)
        elif handle == self.handleBM:
            newY = fromRect.bottom() + mousePos.y() - mousePressedPos.y()
            newY = snapPointToGrid(newY, scene.GridSize, snap=doSnap)
            toRect.setBottom(newY)
        elif handle == self.handleBR:
            newX = fromRect.right() + mousePos.x() - mousePressedPos.x()
            newY = fromRect.bottom() + mousePos.y() - mousePressedPos.y()
            newX = snapPointToGrid(newX, scene.GridSize, snap=doSnap)
            newY = snapPointToGrid(newY, scene.GridSize, snap=doSnap)
            toRect.setRight(newX)
            toRect.setBottom(newY)

        ## CLAMP WIDTH
        if handle in (self.handleTL, self.handleML, self.handleBL):
            if toRect.width() < self.MinWidth:
                toRect.setLeft(toRect.left() - self.MinWidth + toRect.width())
        elif handle in (self.handleTR, self.handleMR, self.handleBR):
            if toRect.width() < self.MinWidth:
                toRect.setRight(toRect.right() + self.MinWidth - toRect.width())

        ## CLAMP HEIGHT
        if handle in (self.handleTL, self.handleTM, self.handleTR):
            if toRect.height() < self.MinHeight:
                toRect.setTop(toRect.top() - self.MinHeight + toRect.height())
        elif handle in (self.handleBL, self.handleBM, self.handleBR):
            if toRect.height() < self.MinHeight:
                toRect.setBottom(toRect.bottom() + self.MinHeight - toRect.height())

        self.prepareGeometryChange()
        self.setRect(toRect)
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