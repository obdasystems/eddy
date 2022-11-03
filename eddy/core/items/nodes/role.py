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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5 import (
    QtCore,
    QtGui,
)

from eddy.core.datatypes.graphol import (
    Item,
    Identity,
    Special,
)
from eddy.core.functions.misc import snapF
from eddy.core.functions.signals import (
    connect,
    disconnect,
)
from eddy.core.items.common import Polygon
from eddy.core.items.nodes.common.base import (
    AbstractResizableNode,
    PredicateNodeMixin,
)


class RoleNode(PredicateNodeMixin, AbstractResizableNode):
    """
    This class implements the 'Role' node.
    """
    IndexL = 0
    IndexB = 1
    IndexR = 2
    IndexT = 3
    IndexE = 4

    DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    Identities = {Identity.Role, Identity.Individual}
    Type = Item.RoleNode

    def __init__(self, width=70, height=50, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)

        w = max(width, 70)
        h = max(height, 50)
        brush = brush or RoleNode.DefaultBrush
        pen = RoleNode.DefaultPen

        createPolygon = lambda x, y: QtGui.QPolygonF([
            QtCore.QPointF(-x / 2, 0),
            QtCore.QPointF(0, +y / 2),
            QtCore.QPointF(+x / 2, 0),
            QtCore.QPointF(0, -y / 2),
            QtCore.QPointF(-x / 2, 0)
        ])

        self.fpolygon = Polygon(QtGui.QPainterPath())
        self.ipolygon = Polygon(QtGui.QPainterPath())
        self.background = Polygon(createPolygon(w + 8, h + 8))
        self.selection = Polygon(createPolygon(w + 8, h + 8))
        self.polygon = Polygon(createPolygon(w, h), brush, pen)

        self.updateNode()

    #############################################
    #   INTERFACE
    #################################

    def connectIRIMetaSignals(self):
        connect(self.iri.sgnFunctionalModified,self.onFunctionalModified)
        connect(self.iri.sgnInverseFunctionalModified, self.onFunctionalModified)

    def disconnectIRIMetaSignals(self):
        disconnect(self.iri.sgnFunctionalModified,self.onFunctionalModified)
        disconnect(self.iri.sgnInverseFunctionalModified, self.onFunctionalModified)

    def initialLabelPosition(self):
        return self.center() - QtCore.QPointF(0, 30)

    def occursAsIndividual(self):
        # Class Assertion
        for instEdge in [x for x in self.edges if x.type() is Item.MembershipEdge]:
            if instEdge.source is self:
                return True
        # Object[Data] Property Assertion
        for inputEdge in [x for x in self.edges if x.type() is Item.InputEdge]:
            if inputEdge.source is self and inputEdge.target.type() is Item.PropertyAssertionNode:
                return True
        # SameAs and Different
        for inputEdge in [x for x in self.edges if (x.type() is Item.SameEdge or x.type() is Item.DifferentEdge)]:
            if inputEdge.source is self or inputEdge.target is self:
                return True
        return False

    @QtCore.pyqtSlot()
    def onFunctionalModified(self):
        self.updateNode()

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QtCore.QRectF
        """
        path = QtGui.QPainterPath()
        path.addPolygon(self.selection.geometry())
        return path.boundingRect()

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        node = diagram.factory.create(self.type(), **{
            'id': self.id,
            'iri': None,
            'brush': self.brush(),
            'height': self.height(),
            'width': self.width(),
        })
        node.setPos(self.pos())
        # node.setText(self.text())
        node.iri = self.iri
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

    def isAsymmetric(self):
        """
        Returns True if the predicate represented by this node is asymmetric, False otherwise.
        :rtype: bool
        """
        return self.iri.asymmetric or False

    def isFunctional(self):
        """
        Returns True if the predicate represented by this node is functional, else False.
        :rtype: bool
        """
        return self.iri.functional or False

    def isInverseFunctional(self):
        """
        Returns True if the predicate represented by this node is inverse functional, else False.
        :rtype: bool
        """
        return self.iri.inverseFunctional or False

    def isIrreflexive(self):
        """
        Returns True if the predicate represented by this node is irreflexive, False otherwise.
        :rtype: bool
        """
        return self.iri.irreflexive or False

    def isReflexive(self):
        """
        Returns True if the predicate represented by this node is reflexive, False otherwise.
        :rtype: bool
        """
        return self.iri.reflexive or False

    def isSymmetric(self):
        """
        Returns True if the predicate represented by this node is symmetric, False otherwise.
        :rtype: bool
        """
        return self.iri.symmetric or False

    def isTransitive(self):
        """
        Returns True if the transitive represented by this node is symmetric, False otherwise.
        :rtype: bool
        """
        return self.iri.transitive or False

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
        painter.drawPolygon(self.selection.geometry())
        # SYNTAX VALIDATION
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
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
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        for polygon in self.handles:
            painter.setPen(polygon.pen())
            painter.setBrush(polygon.brush())
            painter.drawEllipse(polygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addPolygon(self.polygon.geometry())
        return path

    def resize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :type mousePos: QtCore.QPointF
        """
        snap = self.session.action('toggle_grid').isChecked()
        size = self.diagram.GridSize
        moved = self.label.isMoved()

        background = self.background.geometry()
        selection = self.selection.geometry()
        polygon = self.polygon.geometry()

        R = QtCore.QRectF(self.boundingRect())
        D = QtCore.QPointF(0, 0)

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

            selection[self.IndexT] = QtCore.QPointF(R.left() + R.width() / 2, R.top())
            selection[self.IndexB] = QtCore.QPointF(R.left() + R.width() / 2, selection[self.IndexB].y())
            selection[self.IndexL] = QtCore.QPointF(R.left(), R.top() + R.height() / 2)
            selection[self.IndexE] = QtCore.QPointF(R.left(), R.top() + R.height() / 2)
            selection[self.IndexR] = QtCore.QPointF(selection[self.IndexR].x(), R.top() + R.height() / 2)

            background[self.IndexT] = QtCore.QPointF(R.left() + R.width() / 2, R.top())
            background[self.IndexB] = QtCore.QPointF(R.left() + R.width() / 2, background[self.IndexB].y())
            background[self.IndexL] = QtCore.QPointF(R.left(), R.top() + R.height() / 2)
            background[self.IndexE] = QtCore.QPointF(R.left(), R.top() + R.height() / 2)
            background[self.IndexR] = QtCore.QPointF(background[self.IndexR].x(), R.top() + R.height() / 2)

            polygon[self.IndexT] = QtCore.QPointF(R.left() + R.width() / 2, R.top() + 4)
            polygon[self.IndexB] = QtCore.QPointF(R.left() + R.width() / 2, polygon[self.IndexB].y())
            polygon[self.IndexL] = QtCore.QPointF(R.left() + 4, R.top() + R.height() / 2)
            polygon[self.IndexE] = QtCore.QPointF(R.left() + 4, R.top() + R.height() / 2)
            polygon[self.IndexR] = QtCore.QPointF(polygon[self.IndexR].x(), R.top() + R.height() / 2)

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

            selection[self.IndexT] = QtCore.QPointF(selection[self.IndexT].x(), R.top())
            selection[self.IndexL] = QtCore.QPointF(selection[self.IndexL].x(), R.top() + R.height() / 2)
            selection[self.IndexE] = QtCore.QPointF(selection[self.IndexE].x(), R.top() + R.height() / 2)
            selection[self.IndexR] = QtCore.QPointF(selection[self.IndexR].x(), R.top() + R.height() / 2)

            background[self.IndexT] = QtCore.QPointF(background[self.IndexT].x(), R.top())
            background[self.IndexL] = QtCore.QPointF(background[self.IndexL].x(), R.top() + R.height() / 2)
            background[self.IndexE] = QtCore.QPointF(background[self.IndexE].x(), R.top() + R.height() / 2)
            background[self.IndexR] = QtCore.QPointF(background[self.IndexR].x(), R.top() + R.height() / 2)

            polygon[self.IndexT] = QtCore.QPointF(polygon[self.IndexT].x(), R.top() + 4)
            polygon[self.IndexL] = QtCore.QPointF(polygon[self.IndexL].x(), R.top() + R.height() / 2)
            polygon[self.IndexE] = QtCore.QPointF(polygon[self.IndexE].x(), R.top() + R.height() / 2)
            polygon[self.IndexR] = QtCore.QPointF(polygon[self.IndexR].x(), R.top() + R.height() / 2)

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

            selection[self.IndexT] = QtCore.QPointF(R.right() - R.width() / 2, R.top())
            selection[self.IndexB] = QtCore.QPointF(R.right() - R.width() / 2, selection[self.IndexB].y())
            selection[self.IndexL] = QtCore.QPointF(selection[self.IndexL].x(), R.top() + R.height() / 2)
            selection[self.IndexE] = QtCore.QPointF(selection[self.IndexE].x(), R.top() + R.height() / 2)
            selection[self.IndexR] = QtCore.QPointF(R.right(), R.top() + R.height() / 2)

            background[self.IndexT] = QtCore.QPointF(R.right() - R.width() / 2, R.top())
            background[self.IndexB] = QtCore.QPointF(R.right() - R.width() / 2, background[self.IndexB].y())
            background[self.IndexL] = QtCore.QPointF(background[self.IndexL].x(), R.top() + R.height() / 2)
            background[self.IndexE] = QtCore.QPointF(background[self.IndexE].x(), R.top() + R.height() / 2)
            background[self.IndexR] = QtCore.QPointF(R.right(), R.top() + R.height() / 2)

            polygon[self.IndexT] = QtCore.QPointF(R.right() - R.width() / 2, R.top() + 4)
            polygon[self.IndexB] = QtCore.QPointF(R.right() - R.width() / 2, polygon[self.IndexB].y())
            polygon[self.IndexL] = QtCore.QPointF(polygon[self.IndexL].x(), R.top() + R.height() / 2)
            polygon[self.IndexE] = QtCore.QPointF(polygon[self.IndexE].x(), R.top() + R.height() / 2)
            polygon[self.IndexR] = QtCore.QPointF(R.right() - 4, R.top() + R.height() / 2)

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

            selection[self.IndexL] = QtCore.QPointF(R.left(), self.mp_Bound.top() + self.mp_Bound.height() / 2)
            selection[self.IndexE] = QtCore.QPointF(R.left(), self.mp_Bound.top() + self.mp_Bound.height() / 2)
            selection[self.IndexT] = QtCore.QPointF(R.left() + R.width() / 2, selection[self.IndexT].y())
            selection[self.IndexB] = QtCore.QPointF(R.left() + R.width() / 2, selection[self.IndexB].y())

            background[self.IndexL] = QtCore.QPointF(R.left(), self.mp_Bound.top() + self.mp_Bound.height() / 2)
            background[self.IndexE] = QtCore.QPointF(R.left(), self.mp_Bound.top() + self.mp_Bound.height() / 2)
            background[self.IndexT] = QtCore.QPointF(R.left() + R.width() / 2, background[self.IndexT].y())
            background[self.IndexB] = QtCore.QPointF(R.left() + R.width() / 2, background[self.IndexB].y())

            polygon[self.IndexL] = QtCore.QPointF(R.left() + 4, self.mp_Bound.top() + self.mp_Bound.height() / 2)
            polygon[self.IndexE] = QtCore.QPointF(R.left() + 4, self.mp_Bound.top() + self.mp_Bound.height() / 2)
            polygon[self.IndexT] = QtCore.QPointF(R.left() + R.width() / 2, polygon[self.IndexT].y())
            polygon[self.IndexB] = QtCore.QPointF(R.left() + R.width() / 2, polygon[self.IndexB].y())

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

            selection[self.IndexR] = QtCore.QPointF(R.right(), self.mp_Bound.top() + self.mp_Bound.height() / 2)
            selection[self.IndexT] = QtCore.QPointF(R.right() - R.width() / 2, selection[self.IndexT].y())
            selection[self.IndexB] = QtCore.QPointF(R.right() - R.width() / 2, selection[self.IndexB].y())

            background[self.IndexR] = QtCore.QPointF(R.right(), self.mp_Bound.top() + self.mp_Bound.height() / 2)
            background[self.IndexT] = QtCore.QPointF(R.right() - R.width() / 2, background[self.IndexT].y())
            background[self.IndexB] = QtCore.QPointF(R.right() - R.width() / 2, background[self.IndexB].y())

            polygon[self.IndexR] = QtCore.QPointF(R.right() - 4, self.mp_Bound.top() + self.mp_Bound.height() / 2)
            polygon[self.IndexT] = QtCore.QPointF(R.right() - R.width() / 2, polygon[self.IndexT].y())
            polygon[self.IndexB] = QtCore.QPointF(R.right() - R.width() / 2, polygon[self.IndexB].y())

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

            selection[self.IndexT] = QtCore.QPointF(R.left() + R.width() / 2, selection[self.IndexT].y())
            selection[self.IndexB] = QtCore.QPointF(R.left() + R.width() / 2, R.bottom())
            selection[self.IndexL] = QtCore.QPointF(R.left(), R.bottom() - R.height() / 2)
            selection[self.IndexE] = QtCore.QPointF(R.left(), R.bottom() - R.height() / 2)
            selection[self.IndexR] = QtCore.QPointF(selection[self.IndexR].x(), R.bottom() - R.height() / 2)

            background[self.IndexT] = QtCore.QPointF(R.left() + R.width() / 2, background[self.IndexT].y())
            background[self.IndexB] = QtCore.QPointF(R.left() + R.width() / 2, R.bottom())
            background[self.IndexL] = QtCore.QPointF(R.left(), R.bottom() - R.height() / 2)
            background[self.IndexE] = QtCore.QPointF(R.left(), R.bottom() - R.height() / 2)
            background[self.IndexR] = QtCore.QPointF(background[self.IndexR].x(), R.bottom() - R.height() / 2)

            polygon[self.IndexT] = QtCore.QPointF(R.left() + R.width() / 2, polygon[self.IndexT].y())
            polygon[self.IndexB] = QtCore.QPointF(R.left() + R.width() / 2, R.bottom() - 4)
            polygon[self.IndexL] = QtCore.QPointF(R.left() + 4, R.bottom() - R.height() / 2)
            polygon[self.IndexE] = QtCore.QPointF(R.left() + 4, R.bottom() - R.height() / 2)
            polygon[self.IndexR] = QtCore.QPointF(polygon[self.IndexR].x(), R.bottom() - R.height() / 2)

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

            selection[self.IndexB] = QtCore.QPointF(selection[self.IndexB].x(), R.bottom())
            selection[self.IndexL] = QtCore.QPointF(selection[self.IndexL].x(), R.top() + R.height() / 2)
            selection[self.IndexE] = QtCore.QPointF(selection[self.IndexE].x(), R.top() + R.height() / 2)
            selection[self.IndexR] = QtCore.QPointF(selection[self.IndexR].x(), R.top() + R.height() / 2)

            background[self.IndexB] = QtCore.QPointF(background[self.IndexB].x(), R.bottom())
            background[self.IndexL] = QtCore.QPointF(background[self.IndexL].x(), R.top() + R.height() / 2)
            background[self.IndexE] = QtCore.QPointF(background[self.IndexE].x(), R.top() + R.height() / 2)
            background[self.IndexR] = QtCore.QPointF(background[self.IndexR].x(), R.top() + R.height() / 2)

            polygon[self.IndexB] = QtCore.QPointF(polygon[self.IndexB].x(), R.bottom() - 4)
            polygon[self.IndexL] = QtCore.QPointF(polygon[self.IndexL].x(), R.top() + R.height() / 2)
            polygon[self.IndexE] = QtCore.QPointF(polygon[self.IndexE].x(), R.top() + R.height() / 2)
            polygon[self.IndexR] = QtCore.QPointF(polygon[self.IndexR].x(), R.top() + R.height() / 2)

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

            selection[self.IndexT] = QtCore.QPointF(R.right() - R.width() / 2, selection[self.IndexT].y())
            selection[self.IndexB] = QtCore.QPointF(R.right() - R.width() / 2, R.bottom())
            selection[self.IndexL] = QtCore.QPointF(selection[self.IndexL].x(), R.bottom() - R.height() / 2)
            selection[self.IndexE] = QtCore.QPointF(selection[self.IndexE].x(), R.bottom() - R.height() / 2)
            selection[self.IndexR] = QtCore.QPointF(R.right(), R.bottom() - R.height() / 2)

            background[self.IndexT] = QtCore.QPointF(R.right() - R.width() / 2, background[self.IndexT].y())
            background[self.IndexB] = QtCore.QPointF(R.right() - R.width() / 2, R.bottom())
            background[self.IndexL] = QtCore.QPointF(background[self.IndexL].x(), R.bottom() - R.height() / 2)
            background[self.IndexE] = QtCore.QPointF(background[self.IndexE].x(), R.bottom() - R.height() / 2)
            background[self.IndexR] = QtCore.QPointF(R.right(), R.bottom() - R.height() / 2)

            polygon[self.IndexT] = QtCore.QPointF(R.right() - R.width() / 2, polygon[self.IndexT].y())
            polygon[self.IndexB] = QtCore.QPointF(R.right() - R.width() / 2, R.bottom() - 4)
            polygon[self.IndexL] = QtCore.QPointF(polygon[self.IndexL].x(), R.bottom() - R.height() / 2)
            polygon[self.IndexE] = QtCore.QPointF(polygon[self.IndexE].x(), R.bottom() - R.height() / 2)
            polygon[self.IndexR] = QtCore.QPointF(R.right() - 4, R.bottom() - R.height() / 2)

        self.background.setGeometry(background)
        self.selection.setGeometry(selection)
        self.polygon.setGeometry(polygon)

        self.updateNode(selected=True, handle=self.mp_Handle, anchors=(self.mp_Data, D))
        self.label.wrapLabel()
        self.updateTextPos(moved=moved)

    def setAsymmetric(self, asymmetric):
        """
        Set the asymmetric property for the predicate represented by this node.
        :type asymmetric: bool
        """
        self.iri.asymmetric = asymmetric

    def setFunctional(self, functional):
        """
        Set the functional property of the predicate represented by this node.
        :type functional: bool
        """
        self.iri.functional = functional

    def setIdentity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    def setInverseFunctional(self, inverseFunctional):
        """
        Set the inverse functional property of the predicate represented by this node.
        :type inverseFunctional: bool
        """
        self.iri.inverseFunctional = inverseFunctional

    def setIrreflexive(self, irreflexive):
        """
        Set the irreflexive property for the predicate represented by this node.
        :type irreflexive: bool
        """
        self.iri.irreflexive = irreflexive

    def setReflexive(self, reflexive):
        """
        Set the reflexive property for the predicate represented by this node.
        :type reflexive: bool
        """
        self.iri.reflexive = reflexive

    def setSymmetric(self, symmetric):
        """
        Set the symmetric property for the predicate represented by this node.
        :type symmetric: bool
        """
        self.iri.symmetric = symmetric

    def setTransitive(self, transitive):
        """
        Set the transitive property for the predicate represented by this node.
        :type transitive: bool
        """
        self.iri.transitive = transitive

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
        self.label.setAlignment(QtCore.Qt.AlignCenter)

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addPolygon(self.polygon.geometry())
        for polygon in self.handles:
            path.addEllipse(polygon.geometry())
        return path

    def special(self):
        """
        Returns the special type of this node.
        :rtype: Special
        """
        return Special.valueOf(self.text())

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
            if self.iri:
                functional = self.isFunctional()
        if inverseFunctional is None:
            if self.iri:
                inverseFunctional = self.isInverseFunctional()

        polygon = self.polygon.geometry()

        # FUNCTIONAL POLYGON (SHAPE)
        fpolygon = QtGui.QPainterPath()
        if functional and not inverseFunctional:
            path = QtGui.QPainterPath()
            path.addPolygon(QtGui.QPolygonF([
                polygon[self.IndexL] + QtCore.QPointF(+5, 0),
                polygon[self.IndexB] + QtCore.QPointF(0, -4),
                polygon[self.IndexR] + QtCore.QPointF(-5, 0),
                polygon[self.IndexT] + QtCore.QPointF(0, +4),
                polygon[self.IndexL] + QtCore.QPointF(+5, 0),
            ]))
            fpolygon.addPolygon(polygon)
            fpolygon = fpolygon.subtracted(path)

        # INVERSE FUNCTIONAL POLYGON (SHAPE)
        ipolygon = QtGui.QPainterPath()
        if not functional and inverseFunctional:
            path = QtGui.QPainterPath()
            path.addPolygon(QtGui.QPolygonF([
                polygon[self.IndexL] + QtCore.QPointF(+5, 0),
                polygon[self.IndexB] + QtCore.QPointF(0, -4),
                polygon[self.IndexR] + QtCore.QPointF(-5, 0),
                polygon[self.IndexT] + QtCore.QPointF(0, +4),
                polygon[self.IndexL] + QtCore.QPointF(+5, 0),
            ]))
            ipolygon.addPolygon(polygon)
            ipolygon = ipolygon.subtracted(path)

        # FUNCTIONAL + INVERSE FUNCTIONAL POLYGONS (SHAPE)
        if functional and inverseFunctional:
            path = QtGui.QPainterPath()
            path.addPolygon(QtGui.QPolygonF([
                polygon[self.IndexL] + QtCore.QPointF(+5, 0),
                polygon[self.IndexB] + QtCore.QPointF(0, -4),
                polygon[self.IndexB],
                polygon[self.IndexR],
                polygon[self.IndexT],
                polygon[self.IndexT] + QtCore.QPointF(0, +4),
                polygon[self.IndexL] + QtCore.QPointF(+5, 0),
            ]))
            fpolygon.addPolygon(polygon)
            fpolygon = fpolygon.subtracted(path)
            path = QtGui.QPainterPath()
            path.addPolygon(QtGui.QPolygonF([
                polygon[self.IndexL],
                polygon[self.IndexB],
                polygon[self.IndexB] + QtCore.QPointF(0, -4),
                polygon[self.IndexR] + QtCore.QPointF(-5, 0),
                polygon[self.IndexT] + QtCore.QPointF(0, +4),
                polygon[self.IndexT],
                polygon[self.IndexL],
            ]))
            ipolygon.addPolygon(polygon)
            ipolygon = ipolygon.subtracted(path)

        # FUNCTIONAL POLYGON (PEN + BRUSH)
        fpen = QtGui.QPen(QtCore.Qt.NoPen)
        fbrush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if functional:
            fpen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            fbrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))

        # INVERSE FUNCTIONAL POLYGON (PEN + BRUSH)
        ipen = QtGui.QPen(QtCore.Qt.NoPen)
        ibrush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if inverseFunctional:
            ipen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            ibrush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 255))

        self.fpolygon.setPen(fpen)
        self.fpolygon.setBrush(fbrush)
        self.fpolygon.setGeometry(fpolygon)
        self.ipolygon.setPen(ipen)
        self.ipolygon.setBrush(ibrush)
        self.ipolygon.setGeometry(ipolygon)

        # SELECTION + BACKGROUND + HANDLES + ANCHORS + CACHE REFRESH
        super().updateNode(**kwargs)

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

    def __repr__(self):
        """
        Returns repr(self).
        """
        return '{0}:{1}:{2}'.format(self.__class__.__name__, self.text(), self.id)
