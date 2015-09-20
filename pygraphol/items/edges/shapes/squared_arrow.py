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


from functools import partial
from math import sin, cos, radians, pi as M_PI
from pygraphol.items.edges.shapes.base import BaseEdge
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import QPointF, Qt, QLineF
from PyQt5.QtGui import QPolygonF, QPen, QColor, QIcon, QPainter, QPixmap, QPainterPath


class SquaredArrow(BaseEdge):
    """
    This class implements a squared arrow which is used to render the input edge.
    """
    size = 10.0

    headPen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    headBrush = QColor(252, 252, 252)

    linePen = QPen(QColor(0, 0, 0), 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
    linePen.setDashPattern([5, 5])

    ##################################################### GEOMETRY #####################################################

    def shape(self, *args, **kwargs):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()

        for subpath in self.path:
            path.addPolygon(subpath.selection)
            path.moveTo(subpath.p1())
            path.lineTo(subpath.p2())

        if self.isSelected():
            for handle in self.handles.values():
                path.addEllipse(handle)
            for handle in self.anchors.values():
                path.addEllipse(handle)

        path.addPolygon(self.head)

        if self.tail:
            path.moveTo(self.tail.p1())
            path.lineTo(self.tail.p2())

        return path

    ################################################ AUXILIARY METHODS #################################################

    def contextMenu(self, pos):
        """
        Returns the basic edge context menu.
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = self.breakpointAt(pos)
        if breakpoint is not None:
            action = QAction(QIcon(':/icons/delete'), 'Remove breakpoint', self.scene())
            action.triggered.connect(partial(self.breakpointDel, breakpoint=breakpoint))
            menu.addAction(action)
        else:
            functionality = QAction('Functionality', self.scene())
            functionality.setCheckable(True)
            functionality.setChecked(self.edge.functionality)
            functionality.triggered.connect(self.handleToggleFunctionality)
            menu.addAction(self.scene().actionItemDelete)
            menu.addSeparator()
            menu.addAction(functionality)
        return menu

    def handleToggleFunctionality(self):
        """
        Toggle the functionality attribute for this edge.
        """
        self.edge.functionality = not self.edge.functionality
        self.updateEdge()

    def updateHead(self):
        """
        Update the Edge head polygon.
        """
        if self.path:
            subpath = self.path[0] if not self.edge.target else self.path[-1]
            angle = radians(subpath.line.angle())
            p1 = subpath.p2()
            p2 = p1 - QPointF(sin(angle + M_PI / 4.0) * self.size, cos(angle + M_PI / 4.0) * self.size)
            p3 = p2 - QPointF(sin(angle + 3.0 / 4.0 * M_PI) * self.size, cos(angle + 3.0 / 4.0 * M_PI) * self.size)
            p4 = p3 - QPointF(sin(angle - 3.0 / 4.0 * M_PI) * self.size, cos(angle - 3.0 / 4.0 * M_PI) * self.size)
            self.head = QPolygonF([p1, p2, p3, p4])

    def updateTail(self):
        """
        Update the Edge tail line.
        """
        if self.edge.functionality and self.path:
            subpath = self.path[0]
            angle = radians(subpath.line.angle())
            p0 = subpath.p1()
            p1 = p0 + QPointF(sin(angle + M_PI / 3.0) * self.size, cos(angle + M_PI / 3.0) * self.size)
            p2 = p0 + QPointF(sin(angle + M_PI - M_PI / 3.0) * self.size, cos(angle + M_PI - M_PI / 3.0) * self.size)
            self.tail = QLineF(p1, p2)
        else:
            self.tail = None

    def updateEdge(self, target=None):
        """
        Update the Edge line.
        :type target: QPointF
        :param target: the Edge new end point (when there is no endNode attached yet).
        """
        self.updateAnchors()
        self.updateHandles()
        self.updatePath(target)
        self.updateZValue()
        self.updateHead()
        self.updateTail()
        self.update()

    ################################################### ITEM DRAWING ###################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        line_w = 54
        head_size = 8  # length of the head side
        head_span = 4  # offset between line end and head end (this is needed
                       # to prevent artifacts to be visible on low res screens)

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the line
        line_p1 = QPointF(((kwargs['w'] - line_w) / 2), kwargs['h'] / 2)
        line_p2 = QPointF(((kwargs['w'] - line_w) / 2) + line_w - (head_span / 2), kwargs['h'] / 2)
        line = QLineF(line_p1, line_p2)

        angle = radians(line.angle())

        # Calculate head coordinates
        p1 = QPointF(line.p2().x() + (head_span / 2), line.p2().y())
        p2 = p1 - QPointF(sin(angle + M_PI / 4.0) * head_size, cos(angle + M_PI / 4.0) * head_size)
        p3 = p2 - QPointF(sin(angle + 3.0 / 4.0 * M_PI) * head_size, cos(angle + 3.0 / 4.0 * M_PI) * head_size)
        p4 = p3 - QPointF(sin(angle - 3.0 / 4.0 * M_PI) * head_size, cos(angle - 3.0 / 4.0 * M_PI) * head_size)

        # Initialize edge head
        head = QPolygonF([p1, p2, p3, p4])

        # Initialize dashed pen for the line
        linePen = QPen(QColor(0, 0, 0), 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
        linePen.setDashPattern([3, 3])

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(linePen)
        painter.drawLine(line)

        # Draw the head
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QColor(252, 252, 252))
        painter.drawPolygon(head)

        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        if self.canDraw():
            super().paint(painter, option, widget)
            if self.tail:
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(self.tailPen)
                painter.drawLine(self.tail)