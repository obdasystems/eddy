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


from math import sin, cos, radians, pi as M_PI

from PyQt5 import QtCore
from PyQt5 import QtGui

from eddy.core.datatypes.graphol import Item
from eddy.core.functions.geometry import createArea
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.edges.common.label import EdgeLabel


class InputEdge(AbstractEdge):
    """
    This class implements the 'Input' edge.
    """
    Type = Item.InputEdge

    def __init__(self, **kwargs):
        """
        Initialize the edge.
        """
        super().__init__(**kwargs)
        self.label = EdgeLabel('', centered=False, parent=self)

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rect.
        :rtype: QRectF
        """
        path = QtGui.QPainterPath()
        path.addPath(self.selection.geometry())
        path.addPolygon(self.head.geometry())
        for polygon in self.handles:
            path.addEllipse(polygon.geometry())
        for polygon in self.anchors.values():
            path.addEllipse(polygon.geometry())
        return path.controlPointRect()

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        return diagram.factory.create(self.type(), **{
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'breakpoints': self.breakpoints[:],
        })

    @staticmethod
    def createHead(p1, angle, size):
        """
        Create the head polygon.
        :type p1: QPointF
        :type angle: float
        :type size: int
        :rtype: QPolygonF
        """
        rad = radians(angle)
        p2 = p1 - QtCore.QPointF(sin(rad + M_PI / 4.0) * size, cos(rad + M_PI / 4.0) * size)
        p3 = p2 - QtCore.QPointF(sin(rad + 3.0 / 4.0 * M_PI) * size, cos(rad + 3.0 / 4.0 * M_PI) * size)
        p4 = p3 - QtCore.QPointF(sin(rad - 3.0 / 4.0 * M_PI) * size, cos(rad - 3.0 / 4.0 * M_PI) * size)
        return QtGui.QPolygonF([p1, p2, p3, p4])

    def paint(self, painter, option, widget=None):
        """
        Paint the edge in the diagram scene.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        # SET THE RECT THAT NEEDS TO BE REPAINTED
        painter.setClipRect(option.exposedRect)
        # SELECTION AREA
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillPath(self.selection.geometry(), self.selection.brush())
        # EDGE LINE
        painter.setPen(self.path.pen())
        painter.drawPath(self.path.geometry())
        # HEAD POLYGON
        painter.setPen(self.head.pen())
        painter.setBrush(self.head.brush())
        painter.drawPolygon(self.head.geometry())
        # BREAKPOINTS
        for polygon in self.handles:
            painter.setPen(polygon.pen())
            painter.setBrush(polygon.brush())
            painter.drawEllipse(polygon.geometry())
        # ANCHOR POINTS
        for polygon in self.anchors.values():
            painter.setPen(polygon.pen())
            painter.setBrush(polygon.brush())
            painter.drawEllipse(polygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addPath(self.path.geometry())
        path.addPolygon(self.head.geometry())
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
        path = QtGui.QPainterPath()
        path.addPath(self.selection.geometry())
        path.addPolygon(self.head.geometry())
        if self.isSelected():
            for polygon in self.handles:
                path.addEllipse(polygon.geometry())
            for polygon in self.anchors.values():
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
        Returns the current label position.
        :rtype: QPointF
        """
        return self.label.pos()

    def updateEdge(self, selected=None, visible=None, breakpoint=None, anchor=None, target=None, **kwargs):
        """
        Update the current edge.
        :type selected: bool
        :type visible: bool
        :type breakpoint: int
        :type anchor: AbstractNode
        :type target: QPointF
        """
        if visible is None:
            visible = self.canDraw()

        sourceNode = self.source
        targetNode = self.target
        sourcePos = sourceNode.anchor(self)
        targetPos = target
        if targetPos is None:
            targetPos = targetNode.anchor(self)

        self.prepareGeometryChange()

        ##########################################
        # PATH, SELECTION, HEAD (GEOMETRY)
        #################################

        collection = self.createPath(sourceNode, targetNode, [sourcePos] + self.breakpoints + [targetPos])

        selection = QtGui.QPainterPath()
        path = QtGui.QPainterPath()
        head = QtGui.QPolygonF()

        points = []
        append = points.append
        extend = points.extend

        if len(collection) == 1:
            subpath = collection[0]
            p1 = sourceNode.intersection(subpath)
            p2 = targetNode.intersection(subpath) if targetNode else subpath.p2()
            if p1 is not None and p2 is not None:
                path.moveTo(p1)
                path.lineTo(p2)
                selection.addPolygon(createArea(p1, p2, subpath.angle(), 8))
                head = self.createHead(p2, subpath.angle(), 10)
                extend((p1, p2))
        elif len(collection) > 1:
            subpath1 = collection[0]
            subpathN = collection[-1]
            p11 = sourceNode.intersection(subpath1)
            p22 = targetNode.intersection(subpathN)
            if p11 and p22:
                p12 = subpath1.p2()
                p21 = subpathN.p1()
                path.moveTo(p11)
                path.lineTo(p12)
                selection.addPolygon(createArea(p11, p12, subpath1.angle(), 8))
                extend((p11, p12))
                for subpath in collection[1:-1]:
                    p1 = subpath.p1()
                    p2 = subpath.p2()
                    path.moveTo(p1)
                    path.lineTo(p2)
                    selection.addPolygon(createArea(p1, p2, subpath.angle(), 8))
                    append(p2)
                path.moveTo(p21)
                path.lineTo(p22)
                selection.addPolygon(createArea(p21, p22, subpathN.angle(), 8))
                head = self.createHead(p22, subpathN.angle(), 10)
                append(p22)

        self.path.setGeometry(path)
        self.head.setGeometry(head)
        self.selection.setGeometry(selection)

        ##########################################
        # PATH, HEAD (BRUSH)
        #################################

        headBrush = QtGui.QBrush(QtCore.Qt.NoBrush)
        headPen = QtGui.QPen(QtCore.Qt.NoPen)
        pathPen = QtGui.QPen(QtCore.Qt.NoPen)

        if visible:
            headBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
            headPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            pathPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.CustomDashLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            pathPen.setDashPattern([5, 5])

        self.head.setBrush(headBrush)
        self.head.setPen(headPen)
        self.path.setPen(pathPen)

        ##########################################
        # LABEL (POSITION)
        #################################

        if self.target and self.target.type() in {Item.PropertyAssertionNode, Item.RoleChainNode}:
            self.label.setVisible(True)
            self.label.setText(str(self.target.inputs.index(self.id) + 1))
            self.label.updatePos(points)
        else:
            self.label.setVisible(False)

        super().updateEdge(selected, visible, breakpoint, anchor, **kwargs)