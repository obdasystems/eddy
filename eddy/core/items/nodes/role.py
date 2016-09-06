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


from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QBrush, QPen
from PyQt5.QtGui import QPolygonF, QPainterPath, QPainter

from eddy.core.datatypes.graphol import Item, Special, Identity
from eddy.core.functions.misc import snapF
from eddy.core.items.nodes.common.base import AbstractResizableNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.polygon import Polygon


class RoleNode(AbstractResizableNode):
    """
    This class implements the 'Role' node.
    """
    IndexL = 0
    IndexB = 1
    IndexR = 2
    IndexT = 3
    IndexE = 4

    DefaultBrush = QBrush(QColor(252, 252, 252, 255))
    DefaultPen = QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    Identities = {Identity.Role}
    Type = Item.RoleNode

    def __init__(self, width=70, height=50, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super(RoleNode, self).__init__(**kwargs)
        
        w = max(width, 70)
        h = max(height, 50)
        brush = brush or RoleNode.DefaultBrush
        pen = RoleNode.DefaultPen

        createPolygon = lambda x, y: QPolygonF([
            QPointF(-x / 2, 0),
            QPointF(0, +y / 2),
            QPointF(+x / 2, 0),
            QPointF(0, -y / 2),
            QPointF(-x / 2, 0)
        ])

        self.fpolygon = Polygon(QPainterPath())
        self.ipolygon = Polygon(QPainterPath())
        self.background = Polygon(createPolygon(w + 8, h + 8))
        self.selection = Polygon(QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
        self.polygon = Polygon(createPolygon(w, h), brush, pen)
        self.label = NodeLabel(template='role', pos=self.center, parent=self)
        self.label.setAlignment(Qt.AlignCenter)
        self.updateNode()
        self.updateTextPos()

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
        try:
            meta = self.project.meta(self.type(), self.text())
            return meta.functional
        except (AttributeError, KeyError):
            return False

    @functional.setter
    def functional(self, value):
        """
        Set the functional property of the predicated represented by this node.
        :type value: bool
        """
        functional = bool(value)
        meta = self.project.meta(self.type(), self.text())
        meta.functional = functional
        self.project.addMeta(self.type(), self.text(), meta)
        for node in self.project.predicates(self.type(), self.text()):
            node.updateNode(functional=functional, selected=node.isSelected())

    @property
    def inverseFunctional(self):
        """
        Returns True if the predicate represented by this node is inverse functional, else False.
        :rtype: bool
        """
        try:
            meta = self.project.meta(self.type(), self.text())
            return meta.inverseFunctional
        except (AttributeError, KeyError):
            return False

    @inverseFunctional.setter
    def inverseFunctional(self, value):
        """
        Set the inverse functional property of the predicated represented by this node.
        :type value: bool
        """
        inverseFunctional = bool(value)
        meta = self.project.meta(self.type(), self.text())
        meta.inverseFunctional = inverseFunctional
        self.project.addMeta(self.type(), self.text(), meta)
        for node in self.project.predicates(self.type(), self.text()):
            node.updateNode(inverseFunctional=inverseFunctional, selected=node.isSelected())
    
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
        return self.selection.geometry()

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

    def definition(self):
        """
        Returns the list of nodes which contribute to the definition of this very node.
        :rtype: set
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
        return self.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2)

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        polygon = self.polygon.geometry()
        return polygon[self.IndexB].y() - polygon[self.IndexT].y()

    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Role

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
        # FUNCTIONALITY
        painter.setPen(self.fpolygon.pen())
        painter.setBrush(self.fpolygon.brush())
        painter.drawPath(self.fpolygon.geometry())
        # INVERSE FUNCTIONALITY
        painter.setPen(self.ipolygon.pen())
        painter.setBrush(self.ipolygon.brush())
        painter.drawPath(self.ipolygon.geometry())
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

        mbrh = 58
        mbrw = 78

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
            
            selection.setLeft(R.left())
            selection.setTop(R.top())
            
            background[self.IndexT] = QPointF(R.left() + R.width() / 2, R.top())
            background[self.IndexB] = QPointF(R.left() + R.width() / 2, background[self.IndexB].y())
            background[self.IndexL] = QPointF(R.left(), R.top() + R.height() / 2)
            background[self.IndexE] = QPointF(R.left(), R.top() + R.height() / 2)
            background[self.IndexR] = QPointF(background[self.IndexR].x(), R.top() + R.height() / 2)
            
            polygon[self.IndexT] = QPointF(R.left() + R.width() / 2, R.top() + 4)
            polygon[self.IndexB] = QPointF(R.left() + R.width() / 2, polygon[self.IndexB].y())
            polygon[self.IndexL] = QPointF(R.left() + 4, R.top() + R.height() / 2)
            polygon[self.IndexE] = QPointF(R.left() + 4, R.top() + R.height() / 2)
            polygon[self.IndexR] = QPointF(polygon[self.IndexR].x(), R.top() + R.height() / 2)

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
            
            selection.setTop(R.top())
            
            background[self.IndexT] = QPointF(background[self.IndexT].x(), R.top())
            background[self.IndexL] = QPointF(background[self.IndexL].x(), R.top() + R.height() / 2)
            background[self.IndexE] = QPointF(background[self.IndexE].x(), R.top() + R.height() / 2)
            background[self.IndexR] = QPointF(background[self.IndexR].x(), R.top() + R.height() / 2)
            
            polygon[self.IndexT] = QPointF(polygon[self.IndexT].x(), R.top() + 4)
            polygon[self.IndexL] = QPointF(polygon[self.IndexL].x(), R.top() + R.height() / 2)
            polygon[self.IndexE] = QPointF(polygon[self.IndexE].x(), R.top() + R.height() / 2)
            polygon[self.IndexR] = QPointF(polygon[self.IndexR].x(), R.top() + R.height() / 2)

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
            
            selection.setRight(R.right())
            selection.setTop(R.top())
            
            background[self.IndexT] = QPointF(R.right() - R.width() / 2, R.top())
            background[self.IndexB] = QPointF(R.right() - R.width() / 2, background[self.IndexB].y())
            background[self.IndexL] = QPointF(background[self.IndexL].x(), R.top() + R.height() / 2)
            background[self.IndexE] = QPointF(background[self.IndexE].x(), R.top() + R.height() / 2)
            background[self.IndexR] = QPointF(R.right(), R.top() + R.height() / 2)
            
            polygon[self.IndexT] = QPointF(R.right() - R.width() / 2, R.top() + 4)
            polygon[self.IndexB] = QPointF(R.right() - R.width() / 2, polygon[self.IndexB].y())
            polygon[self.IndexL] = QPointF(polygon[self.IndexL].x(), R.top() + R.height() / 2)
            polygon[self.IndexE] = QPointF(polygon[self.IndexE].x(), R.top() + R.height() / 2)
            polygon[self.IndexR] = QPointF(R.right() - 4, R.top() + R.height() / 2)

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
            
            selection.setLeft(R.left())
            
            background[self.IndexL] = QPointF(R.left(), self.mp_Bound.top() + self.mp_Bound.height() / 2)
            background[self.IndexE] = QPointF(R.left(), self.mp_Bound.top() + self.mp_Bound.height() / 2)
            background[self.IndexT] = QPointF(R.left() + R.width() / 2, background[self.IndexT].y())
            background[self.IndexB] = QPointF(R.left() + R.width() / 2, background[self.IndexB].y())
            
            polygon[self.IndexL] = QPointF(R.left() + 4, self.mp_Bound.top() + self.mp_Bound.height() / 2)
            polygon[self.IndexE] = QPointF(R.left() + 4, self.mp_Bound.top() + self.mp_Bound.height() / 2)
            polygon[self.IndexT] = QPointF(R.left() + R.width() / 2, polygon[self.IndexT].y())
            polygon[self.IndexB] = QPointF(R.left() + R.width() / 2, polygon[self.IndexB].y())

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
            
            selection.setRight(R.right())
            
            background[self.IndexR] = QPointF(R.right(), self.mp_Bound.top() + self.mp_Bound.height() / 2)
            background[self.IndexT] = QPointF(R.right() - R.width() / 2, background[self.IndexT].y())
            background[self.IndexB] = QPointF(R.right() - R.width() / 2, background[self.IndexB].y())
            
            polygon[self.IndexR] = QPointF(R.right() - 4, self.mp_Bound.top() + self.mp_Bound.height() / 2)
            polygon[self.IndexT] = QPointF(R.right() - R.width() / 2, polygon[self.IndexT].y())
            polygon[self.IndexB] = QPointF(R.right() - R.width() / 2, polygon[self.IndexB].y())

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
            
            selection.setLeft(R.left())
            selection.setBottom(R.bottom())
            
            background[self.IndexT] = QPointF(R.left() + R.width() / 2, background[self.IndexT].y())
            background[self.IndexB] = QPointF(R.left() + R.width() / 2, R.bottom())
            background[self.IndexL] = QPointF(R.left(), R.bottom() - R.height() / 2)
            background[self.IndexE] = QPointF(R.left(), R.bottom() - R.height() / 2)
            background[self.IndexR] = QPointF(background[self.IndexR].x(), R.bottom() - R.height() / 2)
            
            polygon[self.IndexT] = QPointF(R.left() + R.width() / 2, polygon[self.IndexT].y())
            polygon[self.IndexB] = QPointF(R.left() + R.width() / 2, R.bottom() - 4)
            polygon[self.IndexL] = QPointF(R.left() + 4, R.bottom() - R.height() / 2)
            polygon[self.IndexE] = QPointF(R.left() + 4, R.bottom() - R.height() / 2)
            polygon[self.IndexR] = QPointF(polygon[self.IndexR].x(), R.bottom() - R.height() / 2)

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
            
            selection.setBottom(R.bottom())
            
            background[self.IndexB] = QPointF(background[self.IndexB].x(), R.bottom())
            background[self.IndexL] = QPointF(background[self.IndexL].x(), R.top() + R.height() / 2)
            background[self.IndexE] = QPointF(background[self.IndexE].x(), R.top() + R.height() / 2)
            background[self.IndexR] = QPointF(background[self.IndexR].x(), R.top() + R.height() / 2)
            
            polygon[self.IndexB] = QPointF(polygon[self.IndexB].x(), R.bottom() - 4)
            polygon[self.IndexL] = QPointF(polygon[self.IndexL].x(), R.top() + R.height() / 2)
            polygon[self.IndexE] = QPointF(polygon[self.IndexE].x(), R.top() + R.height() / 2)
            polygon[self.IndexR] = QPointF(polygon[self.IndexR].x(), R.top() + R.height() / 2)

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

            selection.setRight(R.right())
            selection.setBottom(R.bottom())

            background[self.IndexT] = QPointF(R.right() - R.width() / 2, background[self.IndexT].y())
            background[self.IndexB] = QPointF(R.right() - R.width() / 2, R.bottom())
            background[self.IndexL] = QPointF(background[self.IndexL].x(), R.bottom() - R.height() / 2)
            background[self.IndexE] = QPointF(background[self.IndexE].x(), R.bottom() - R.height() / 2)
            background[self.IndexR] = QPointF(R.right(), R.bottom() - R.height() / 2)
            
            polygon[self.IndexT] = QPointF(R.right() - R.width() / 2, polygon[self.IndexT].y())
            polygon[self.IndexB] = QPointF(R.right() - R.width() / 2, R.bottom() - 4)
            polygon[self.IndexL] = QPointF(polygon[self.IndexL].x(), R.bottom() - R.height() / 2)
            polygon[self.IndexE] = QPointF(polygon[self.IndexE].x(), R.bottom() - R.height() / 2)
            polygon[self.IndexR] = QPointF(R.right() - 4, R.bottom() - R.height() / 2)

        self.background.setGeometry(background)
        self.selection.setGeometry(selection)
        self.polygon.setGeometry(polygon)

        self.updateNode(selected=True, handle=self.mp_Handle, anchors=(self.mp_Data, D))
        self.updateTextPos(moved=moved)

    def setIdentity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

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
        self.label.setAlignment(Qt.AlignCenter)

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

    def updateNode(self, functional=None, inverseFunctional=None, **kwargs):
        """
        Update the current node.
        :type functional: bool
        :type inverseFunctional: bool
        """
        if functional is None:
            functional = self.functional
        if inverseFunctional is None:
            inverseFunctional = self.inverseFunctional

        polygon = self.polygon.geometry()

        # FUNCTIONAL POLYGON (SHAPE)
        fpolygon = QPainterPath()
        if functional and not inverseFunctional:
            path = QPainterPath()
            path.addPolygon(QPolygonF([
                polygon[self.IndexL] + QPointF(+5, 0),
                polygon[self.IndexB] + QPointF(0, -4),
                polygon[self.IndexR] + QPointF(-5, 0),
                polygon[self.IndexT] + QPointF(0, +4),
                polygon[self.IndexL] + QPointF(+5, 0),
            ]))
            fpolygon.addPolygon(polygon)
            fpolygon = fpolygon.subtracted(path)

        # INVERSE FUNCTIONAL POLYGON (SHAPE)
        ipolygon = QPainterPath()
        if not functional and inverseFunctional:
            path = QPainterPath()
            path.addPolygon(QPolygonF([
                polygon[self.IndexL] + QPointF(+5, 0),
                polygon[self.IndexB] + QPointF(0, -4),
                polygon[self.IndexR] + QPointF(-5, 0),
                polygon[self.IndexT] + QPointF(0, +4),
                polygon[self.IndexL] + QPointF(+5, 0),
            ]))
            ipolygon.addPolygon(polygon)
            ipolygon = ipolygon.subtracted(path)

        # FUNCTIONAL + INVERSE FUNCTIONAL POLYGONS (SHAPE)
        if functional and inverseFunctional:
            path = QPainterPath()
            path.addPolygon(QPolygonF([
                polygon[self.IndexL] + QPointF(+5, 0),
                polygon[self.IndexB] + QPointF(0, -4),
                polygon[self.IndexB],
                polygon[self.IndexR],
                polygon[self.IndexT],
                polygon[self.IndexT] + QPointF(0, +4),
                polygon[self.IndexL] + QPointF(+5, 0),
            ]))
            fpolygon.addPolygon(polygon)
            fpolygon = fpolygon.subtracted(path)
            path = QPainterPath()
            path.addPolygon(QPolygonF([
                polygon[self.IndexL],
                polygon[self.IndexB],
                polygon[self.IndexB] + QPointF(0, -4),
                polygon[self.IndexR] + QPointF(-5, 0),
                polygon[self.IndexT] + QPointF(0, +4),
                polygon[self.IndexT],
                polygon[self.IndexL],
            ]))
            ipolygon.addPolygon(polygon)
            ipolygon = ipolygon.subtracted(path)

        # FUNCTIONAL POLYGON (PEN + BRUSH)
        fpen = QPen(Qt.NoPen)
        fbrush = QBrush(Qt.NoBrush)
        if functional:
            fpen = QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            fbrush = QBrush(QColor(252, 252, 252, 255))

        # INVERSE FUNCTIONAL POLYGON (PEN + BRUSH)
        ipen = QPen(Qt.NoPen)
        ibrush = QBrush(Qt.NoBrush)
        if inverseFunctional:
            ipen = QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            ibrush = QBrush(QColor(0, 0, 0, 255))

        self.fpolygon.setPen(fpen)
        self.fpolygon.setBrush(fbrush)
        self.fpolygon.setGeometry(fpolygon)
        self.ipolygon.setPen(ipen)
        self.ipolygon.setBrush(ibrush)
        self.ipolygon.setGeometry(ipolygon)

        # SELECTION + BACKGROUND + HANDLES + ANCHORS + CACHE REFRESH
        super(RoleNode, self).updateNode(**kwargs)

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
        return polygon[self.IndexR].x() - polygon[self.IndexL].x()