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


from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPolygonF, QPainterPath, QPixmap, QPainter, QPen, QColor, QBrush

from eddy.core.datatypes.graphol import Item, Special, Identity
from eddy.core.functions.misc import snapF
from eddy.core.items.nodes.common.base import AbstractResizableNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.qt import Font


class RoleNode(AbstractResizableNode):
    """
    This class implements the 'Role' node.
    """
    IndexL = 0
    IndexB = 1
    IndexT = 3
    IndexR = 2
    IndexE = 4

    Identities = {Identity.Role}
    Type = Item.RoleNode
    MinHeight = 50
    MinWidth = 70

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
        self.label = NodeLabel(template='role',
                               pos=self.center,
                               parent=self)
        self.updateTextPos()
        self.updateHandles()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def asymmetric(self):
        """
        Returns True if the predicate represented by this node is asymmetric, False otherwise.
        :rtype: bool
        """
        meta = self.project.meta(self.type(), self.text())
        return meta.asymmetric

    @asymmetric.setter
    def asymmetric(self, value):
        """
        Set the asymmetric property for the predicate represented by this node.
        :type value: bool
        """
        meta = self.project.meta(self.type(), self.text())
        meta.asymmetric = bool(value)
        self.project.addMeta(self.type(), self.text(), meta)

    @property
    def functional(self):
        """
        Returns True if the predicate represented by this node is functional, else False.
        :rtype: bool
        """
        meta = self.project.meta(self.type(), self.text())
        return meta.functional

    @functional.setter
    def functional(self, value):
        """
        Set the functional property of the predicated represented by this node.
        :type value: bool
        """
        meta = self.project.meta(self.type(), self.text())
        meta.functional = bool(value)
        self.project.addMeta(self.type(), self.text(), meta)

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Role

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass
    
    @property
    def inverseFunctional(self):
        """
        Returns True if the predicate represented by this node is inverse functional, else False.
        :rtype: bool
        """
        meta = self.project.meta(self.type(), self.text())
        return meta.inverseFunctional

    @inverseFunctional.setter
    def inverseFunctional(self, value):
        """
        Set the inverse functional property of the predicated represented by this node.
        :type value: bool
        """
        meta = self.project.meta(self.type(), self.text())
        meta.inverseFunctional = bool(value)
        self.project.addMeta(self.type(), self.text(), meta)
    
    @property
    def irreflexive(self):
        """
        Returns True if the predicate represented by this node is irreflexive, False otherwise.
        :rtype: bool
        """
        meta = self.project.meta(self.type(), self.text())
        return meta.irreflexive

    @irreflexive.setter
    def irreflexive(self, value):
        """
        Set the irreflexive property for the predicate represented by this node.
        :type value: bool
        """
        meta = self.project.meta(self.type(), self.text())
        meta.irreflexive = bool(value)
        self.project.addMeta(self.type(), self.text(), meta)

    @property
    def reflexive(self):
        """
        Returns True if the predicate represented by this node is reflexive, False otherwise.
        :rtype: bool
        """
        meta = self.project.meta(self.type(), self.text())
        return meta.reflexive

    @reflexive.setter
    def reflexive(self, value):
        """
        Set the reflexive property for the predicate represented by this node.
        :type value: bool
        """
        meta = self.project.meta(self.type(), self.text())
        meta.reflexive = bool(value)
        self.project.addMeta(self.type(), self.text(), meta)

    @property
    def special(self):
        """
        Returns the special type of this node.
        :rtype: Special
        """
        return Special.forLabel(self.text())

    @property
    def symmetric(self):
        """
        Returns True if the predicate represented by this node is symmetric, False otherwise.
        :rtype: bool
        """
        meta = self.project.meta(self.type(), self.text())
        return meta.symmetric

    @symmetric.setter
    def symmetric(self, value):
        """
        Set the symmetric property for the predicate represented by this node.
        :type value: bool
        """
        meta = self.project.meta(self.type(), self.text())
        meta.symmetric = bool(value)
        self.project.addMeta(self.type(), self.text(), meta)

    @property
    def transitive(self):
        """
        Returns True if the transitive represented by this node is symmetric, False otherwise.
        :rtype: bool
        """
        meta = self.project.meta(self.type(), self.text())
        return meta.transitive

    @transitive.setter
    def transitive(self, value):
        """
        Set the transitive property for the predicate represented by this node.
        :type value: bool
        """
        meta = self.project.meta(self.type(), self.text())
        meta.transitive = bool(value)
        self.project.addMeta(self.type(), self.text(), meta)

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.selection

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
            QPointF(-width / 2, 0),
            QPointF(0, +height / 2),
            QPointF(+width / 2, 0),
            QPointF(0, -height / 2),
            QPointF(-width / 2, 0)
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
            QPointF(-width / 2, 0),
            QPointF(0, +height / 2),
            QPointF(+width / 2, 0),
            QPointF(0, -height / 2),
            QPointF(-width / 2, 0)
        ])

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon[self.IndexB].y() - self.polygon[self.IndexT].y()

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
        polygon = cls.createPolygon(46, 34)
        # ITEM SHAPE
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)
        # TEXT WITHIN SHAPE
        painter.setFont(Font('Arial', 11, Font.Light))
        painter.drawText(polygon.boundingRect(), Qt.AlignCenter, 'role')
        return pixmap

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

        minBoundW = self.MinWidth + offset * 2
        minBoundH = self.MinHeight + offset * 2

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
            if R.width() < minBoundW:
                D.setX(D.x() - minBoundW + R.width())
                R.setLeft(R.left() - minBoundW + R.width())
            if R.height() < minBoundH:
                D.setY(D.y() - minBoundH + R.height())
                R.setTop(R.top() - minBoundH + R.height())
            
            self.selection.setLeft(R.left())
            self.selection.setTop(R.top())
            
            self.background[self.IndexT] = QPointF(R.left() + R.width() / 2, R.top())
            self.background[self.IndexB] = QPointF(R.left() + R.width() / 2, self.background[self.IndexB].y())
            self.background[self.IndexL] = QPointF(R.left(), R.top() + R.height() / 2)
            self.background[self.IndexE] = QPointF(R.left(), R.top() + R.height() / 2)
            self.background[self.IndexR] = QPointF(self.background[self.IndexR].x(), R.top() + R.height() / 2)
            
            self.polygon[self.IndexT] = QPointF(R.left() + R.width() / 2, R.top() + offset)
            self.polygon[self.IndexB] = QPointF(R.left() + R.width() / 2, self.polygon[self.IndexB].y())
            self.polygon[self.IndexL] = QPointF(R.left() + offset, R.top() + R.height() / 2)
            self.polygon[self.IndexE] = QPointF(R.left() + offset, R.top() + R.height() / 2)
            self.polygon[self.IndexR] = QPointF(self.polygon[self.IndexR].x(), R.top() + R.height() / 2)

        elif self.mousePressHandle == self.HandleTM:

            fromY = self.mousePressBound.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, size, -offset, snap)
            D.setY(toY - fromY)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.height() < minBoundH:
                D.setY(D.y() - minBoundH + R.height())
                R.setTop(R.top() - minBoundH + R.height())
            
            self.selection.setTop(R.top())
            
            self.background[self.IndexT] = QPointF(self.background[self.IndexT].x(), R.top())
            self.background[self.IndexL] = QPointF(self.background[self.IndexL].x(), R.top() + R.height() / 2)
            self.background[self.IndexE] = QPointF(self.background[self.IndexE].x(), R.top() + R.height() / 2)
            self.background[self.IndexR] = QPointF(self.background[self.IndexR].x(), R.top() + R.height() / 2)
            
            self.polygon[self.IndexT] = QPointF(self.polygon[self.IndexT].x(), R.top() + offset)
            self.polygon[self.IndexL] = QPointF(self.polygon[self.IndexL].x(), R.top() + R.height() / 2)
            self.polygon[self.IndexE] = QPointF(self.polygon[self.IndexE].x(), R.top() + R.height() / 2)
            self.polygon[self.IndexR] = QPointF(self.polygon[self.IndexR].x(), R.top() + R.height() / 2)

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
            if R.width() < minBoundW:
                D.setX(D.x() + minBoundW - R.width())
                R.setRight(R.right() + minBoundW - R.width())
            if R.height() < minBoundH:
                D.setY(D.y() - minBoundH + R.height())
                R.setTop(R.top() - minBoundH + R.height())
            
            self.selection.setRight(R.right())
            self.selection.setTop(R.top())
            
            self.background[self.IndexT] = QPointF(R.right() - R.width() / 2, R.top())
            self.background[self.IndexB] = QPointF(R.right() - R.width() / 2, self.background[self.IndexB].y())
            self.background[self.IndexL] = QPointF(self.background[self.IndexL].x(), R.top() + R.height() / 2)
            self.background[self.IndexE] = QPointF(self.background[self.IndexE].x(), R.top() + R.height() / 2)
            self.background[self.IndexR] = QPointF(R.right(), R.top() + R.height() / 2)
            
            self.polygon[self.IndexT] = QPointF(R.right() - R.width() / 2, R.top() + offset)
            self.polygon[self.IndexB] = QPointF(R.right() - R.width() / 2, self.polygon[self.IndexB].y())
            self.polygon[self.IndexL] = QPointF(self.polygon[self.IndexL].x(), R.top() + R.height() / 2)
            self.polygon[self.IndexE] = QPointF(self.polygon[self.IndexE].x(), R.top() + R.height() / 2)
            self.polygon[self.IndexR] = QPointF(R.right() - offset, R.top() + R.height() / 2)

        elif self.mousePressHandle == self.HandleML:

            fromX = self.mousePressBound.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, size, -offset, snap)
            D.setX(toX - fromX)
            R.setLeft(toX)

            ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() - minBoundW + R.width())
                R.setLeft(R.left() - minBoundW + R.width())
            
            self.selection.setLeft(R.left())
            
            self.background[self.IndexL] = QPointF(R.left(), self.mousePressBound.top() + self.mousePressBound.height() / 2)
            self.background[self.IndexE] = QPointF(R.left(), self.mousePressBound.top() + self.mousePressBound.height() / 2)
            self.background[self.IndexT] = QPointF(R.left() + R.width() / 2, self.background[self.IndexT].y())
            self.background[self.IndexB] = QPointF(R.left() + R.width() / 2, self.background[self.IndexB].y())
            
            self.polygon[self.IndexL] = QPointF(R.left() + offset, self.mousePressBound.top() + self.mousePressBound.height() / 2)
            self.polygon[self.IndexE] = QPointF(R.left() + offset, self.mousePressBound.top() + self.mousePressBound.height() / 2)
            self.polygon[self.IndexT] = QPointF(R.left() + R.width() / 2, self.polygon[self.IndexT].y())
            self.polygon[self.IndexB] = QPointF(R.left() + R.width() / 2, self.polygon[self.IndexB].y())

        elif self.mousePressHandle == self.HandleMR:

            fromX = self.mousePressBound.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, size, +offset, snap)
            D.setX(toX - fromX)
            R.setRight(toX)

            ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() + minBoundW - R.width())
                R.setRight(R.right() + minBoundW - R.width())
            
            self.selection.setRight(R.right())
            
            self.background[self.IndexR] = QPointF(R.right(), self.mousePressBound.top() + self.mousePressBound.height() / 2)
            self.background[self.IndexT] = QPointF(R.right() - R.width() / 2, self.background[self.IndexT].y())
            self.background[self.IndexB] = QPointF(R.right() - R.width() / 2, self.background[self.IndexB].y())
            
            self.polygon[self.IndexR] = QPointF(R.right() - offset, self.mousePressBound.top() + self.mousePressBound.height() / 2)
            self.polygon[self.IndexT] = QPointF(R.right() - R.width() / 2, self.polygon[self.IndexT].y())
            self.polygon[self.IndexB] = QPointF(R.right() - R.width() / 2, self.polygon[self.IndexB].y())

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
            if R.width() < minBoundW:
                D.setX(D.x() - minBoundW + R.width())
                R.setLeft(R.left() - minBoundW + R.width())
            if R.height() < minBoundH:
                D.setY(D.y() + minBoundH - R.height())
                R.setBottom(R.bottom() + minBoundH - R.height())
            
            self.selection.setLeft(R.left())
            self.selection.setBottom(R.bottom())
            
            self.background[self.IndexT] = QPointF(R.left() + R.width() / 2, self.background[self.IndexT].y())
            self.background[self.IndexB] = QPointF(R.left() + R.width() / 2, R.bottom())
            self.background[self.IndexL] = QPointF(R.left(), R.bottom() - R.height() / 2)
            self.background[self.IndexE] = QPointF(R.left(), R.bottom() - R.height() / 2)
            self.background[self.IndexR] = QPointF(self.background[self.IndexR].x(), R.bottom() - R.height() / 2)
            
            self.polygon[self.IndexT] = QPointF(R.left() + R.width() / 2, self.polygon[self.IndexT].y())
            self.polygon[self.IndexB] = QPointF(R.left() + R.width() / 2, R.bottom() - offset)
            self.polygon[self.IndexL] = QPointF(R.left() + offset, R.bottom() - R.height() / 2)
            self.polygon[self.IndexE] = QPointF(R.left() + offset, R.bottom() - R.height() / 2)
            self.polygon[self.IndexR] = QPointF(self.polygon[self.IndexR].x(), R.bottom() - R.height() / 2)

        elif self.mousePressHandle == self.HandleBM:

            fromY = self.mousePressBound.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, size, +offset, snap)
            D.setY(toY - fromY)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.height() < minBoundH:
                D.setY(D.y() + minBoundH - R.height())
                R.setBottom(R.bottom() + minBoundH - R.height())
            
            self.selection.setBottom(R.bottom())
            
            self.background[self.IndexB] = QPointF(self.background[self.IndexB].x(), R.bottom())
            self.background[self.IndexL] = QPointF(self.background[self.IndexL].x(), R.top() + R.height() / 2)
            self.background[self.IndexE] = QPointF(self.background[self.IndexE].x(), R.top() + R.height() / 2)
            self.background[self.IndexR] = QPointF(self.background[self.IndexR].x(), R.top() + R.height() / 2)
            
            self.polygon[self.IndexB] = QPointF(self.polygon[self.IndexB].x(), R.bottom() - offset)
            self.polygon[self.IndexL] = QPointF(self.polygon[self.IndexL].x(), R.top() + R.height() / 2)
            self.polygon[self.IndexE] = QPointF(self.polygon[self.IndexE].x(), R.top() + R.height() / 2)
            self.polygon[self.IndexR] = QPointF(self.polygon[self.IndexR].x(), R.top() + R.height() / 2)

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
            if R.width() < minBoundW:
                D.setX(D.x() + minBoundW - R.width())
                R.setRight(R.right() + minBoundW - R.width())
            if R.height() < minBoundH:
                D.setY(D.y() + minBoundH - R.height())
                R.setBottom(R.bottom() + minBoundH - R.height())

            self.selection.setRight(R.right())
            self.selection.setBottom(R.bottom())

            self.background[self.IndexT] = QPointF(R.right() - R.width() / 2, self.background[self.IndexT].y())
            self.background[self.IndexB] = QPointF(R.right() - R.width() / 2, R.bottom())
            self.background[self.IndexL] = QPointF(self.background[self.IndexL].x(), R.bottom() - R.height() / 2)
            self.background[self.IndexE] = QPointF(self.background[self.IndexE].x(), R.bottom() - R.height() / 2)
            self.background[self.IndexR] = QPointF(R.right(), R.bottom() - R.height() / 2)
            
            self.polygon[self.IndexT] = QPointF(R.right() - R.width() / 2, self.polygon[self.IndexT].y())
            self.polygon[self.IndexB] = QPointF(R.right() - R.width() / 2, R.bottom() - offset)
            self.polygon[self.IndexL] = QPointF(self.polygon[self.IndexL].x(), R.bottom() - R.height() / 2)
            self.polygon[self.IndexE] = QPointF(self.polygon[self.IndexE].x(), R.bottom() - R.height() / 2)
            self.polygon[self.IndexR] = QPointF(R.right() - offset, R.bottom() - R.height() / 2)

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

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        self.label.setText(text)

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

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
        return self.polygon[self.IndexR].x() - self.polygon[self.IndexL].x()