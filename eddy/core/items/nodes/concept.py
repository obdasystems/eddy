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


from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QPainterPath, QPainter, QPixmap, QColor, QPen, QBrush

from eddy.core.datatypes import Font, Item, Special, Identity
from eddy.core.functions import snapF
from eddy.core.items.nodes.common.base import AbstractResizableNode
from eddy.core.items.nodes.common.label import Label


class ConceptNode(AbstractResizableNode):
    """
    This class implements the 'Concept' node.
    """
    identities = {Identity.Concept}
    item = Item.ConceptNode
    minheight = 50
    minwidth = 110

    def __init__(self, width=minwidth, height=minheight, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)

        w = max(width, self.minwidth)
        h = max(height, self.minheight)
        s = self.handleSize

        self.brush = brush or QBrush(QColor(252, 252, 252))
        self.pen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)
        self.polygon = self.createPolygon(w, h)
        self.background = self.createBackground(w + s, h + s)
        self.selection = self.createSelection(w + s, h + s)
        self.label = Label('concept', parent=self)
        self.label.updatePos()
        self.updateHandles()

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Concept

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    @property
    def special(self):
        """
        Returns the special type of this node.
        :rtype: Special
        """
        return Special.forValue(self.text())

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
        node = scene.factory.create(item=self.item, scene=scene, **kwargs)
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
    def createPolygon(width, height):
        """
        Returns the initialized polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: QRectF
        """
        return QRectF(-width / 2, -height / 2, width, height)

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.height()

    def interactiveResize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :type mousePos: QPointF
        """
        scene = self.scene()
        snap = scene.mainwindow.snapToGrid
        size = scene.GridSize
        offset = self.handleSize + self.handleMove
        moved = self.label.moved

        R = QRectF(self.boundingRect())
        D = QPointF(0, 0)

        minBoundW = self.minwidth + offset * 2
        minBoundH = self.minheight + offset * 2

        self.prepareGeometryChange()

        if self.mousePressHandle == self.handleTL:

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
            if R.width() < minBoundW:
                D.setX(D.x() - minBoundW + R.width())
                R.setLeft(R.left() - minBoundW + R.width())
            if R.height() < minBoundH:
                D.setY(D.y() - minBoundH + R.height())
                R.setTop(R.top() - minBoundH + R.height())

            self.background.setLeft(R.left())
            self.background.setTop(R.top())
            self.selection.setLeft(R.left())
            self.selection.setTop(R.top())
            self.polygon.setLeft(R.left() + offset)
            self.polygon.setTop(R.top() + offset)

        elif self.mousePressHandle == self.handleTM:

            fromY = self.mousePressBound.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, size, -offset, snap)
            D.setY(toY - fromY)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.height() < minBoundH:
                D.setY(D.y() - minBoundH + R.height())
                R.setTop(R.top() - minBoundH + R.height())

            self.background.setTop(R.top())
            self.selection.setTop(R.top())
            self.polygon.setTop(R.top() + offset)

        elif self.mousePressHandle == self.handleTR:

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
            if R.width() < minBoundW:
                D.setX(D.x() + minBoundW - R.width())
                R.setRight(R.right() + minBoundW - R.width())
            if R.height() < minBoundH:
                D.setY(D.y() - minBoundH + R.height())
                R.setTop(R.top() - minBoundH + R.height())

            self.background.setRight(R.right())
            self.background.setTop(R.top())
            self.selection.setRight(R.right())
            self.selection.setTop(R.top())
            self.polygon.setRight(R.right() - offset)
            self.polygon.setTop(R.top() + offset)

        elif self.mousePressHandle == self.handleML:

            fromX = self.mousePressBound.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, size, -offset, snap)
            D.setX(toX - fromX)
            R.setLeft(toX)

             ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() - minBoundW + R.width())
                R.setLeft(R.left() - minBoundW + R.width())

            self.background.setLeft(R.left())
            self.selection.setLeft(R.left())
            self.polygon.setLeft(R.left() + offset)

        elif self.mousePressHandle == self.handleMR:

            fromX = self.mousePressBound.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, size, +offset, snap)
            D.setX(toX - fromX)
            R.setRight(toX)

            ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() + minBoundW - R.width())
                R.setRight(R.right() + minBoundW - R.width())

            self.background.setRight(R.right())
            self.selection.setRight(R.right())
            self.polygon.setRight(R.right() - offset)

        elif self.mousePressHandle == self.handleBL:

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
            if R.width() < minBoundW:
                D.setX(D.x() - minBoundW + R.width())
                R.setLeft(R.left() - minBoundW + R.width())
            if R.height() < minBoundH:
                D.setY(D.y() + minBoundH - R.height())
                R.setBottom(R.bottom() + minBoundH - R.height())

            self.background.setLeft(R.left())
            self.background.setBottom(R.bottom())
            self.selection.setLeft(R.left())
            self.selection.setBottom(R.bottom())
            self.polygon.setLeft(R.left() + offset)
            self.polygon.setBottom(R.bottom() - offset)

        elif self.mousePressHandle == self.handleBM:

            fromY = self.mousePressBound.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, size, +offset, snap)
            D.setY(toY - fromY)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.height() < minBoundH:
                D.setY(D.y() + minBoundH - R.height())
                R.setBottom(R.bottom() + minBoundH - R.height())

            self.background.setBottom(R.bottom())
            self.selection.setBottom(R.bottom())
            self.polygon.setBottom(R.bottom() - offset)

        elif self.mousePressHandle == self.handleBR:

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
            if R.width() < minBoundW:
                D.setX(D.x() + minBoundW - R.width())
                R.setRight(R.right() + minBoundW - R.width())
            if R.height() < minBoundH:
                D.setY(D.y() + minBoundH - R.height())
                R.setBottom(R.bottom() + minBoundH - R.height())

            self.background.setRight(R.right())
            self.background.setBottom(R.bottom())
            self.selection.setRight(R.right())
            self.selection.setBottom(R.bottom())
            self.polygon.setRight(R.right() - offset)
            self.polygon.setBottom(R.bottom() - offset)

        self.updateHandles()
        self.updateTextPos(moved=moved)
        self.updateAnchors(self.mousePressData, D)

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon.width()

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
        path.addRect(self.polygon)
        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.polygon)
        for shape in self.handleBound:
            path.addEllipse(shape)
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
        self.label.editable = Special.forValue(text) is None
        self.label.setText(text)

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
        rect = cls.createPolygon(54, 34)
        # DRAW THE RECTANGLE
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRect(rect)
        # TEXT WITHIN THE RECTANGLE
        painter.setFont(Font('Arial', 11, Font.Light))
        painter.drawText(rect, Qt.AlignCenter, 'concept')
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
        painter.setPen(self.backgroundPen)
        painter.setBrush(self.backgroundBrush)
        painter.drawRect(self.background)
        # ITEM SHAPE
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawRect(self.polygon)
        # RESIZE HANDLES
        painter.setRenderHint(QPainter.Antialiasing)
        for i in range(self.handleNum):
            painter.setBrush(self.handleBrush[i])
            painter.setPen(self.handlePen[i])
            painter.drawEllipse(self.handleBound[i])