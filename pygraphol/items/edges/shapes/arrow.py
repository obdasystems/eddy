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
from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtCore import QPointF, Qt, QLineF
from PyQt5.QtGui import QPolygonF, QPixmap, QPainter, QPen, QColor, QIcon, QPainterPath


class Arrow(BaseEdge):
    """
    This class implements a arrow which is used to render the inclusion edge.
    """

    ##################################################### GEOMETRY #####################################################

    def shape(self):
        """
        Return the shape of the Edge.
        :rtype: QPainterPath
        """
        path = super().shape()
        if self.tail:
            path.addPolygon(self.tail)
        return path

    ################################################ AUXILIARY METHODS #################################################

    def contextMenu(self, pos):
        """
        Returns the basic edge context menu.
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = self.breakpointIndex(pos)
        if breakpoint is not None:
            action = QAction(QIcon(':/icons/delete'), 'Remove breakpoint', self.scene())
            action.triggered.connect(partial(self.breakpointDel, breakpoint=breakpoint))
            menu.addAction(action)
        else:
            completness = QAction('Complete', self.scene())
            completness.setCheckable(True)
            completness.setChecked(self.edge.complete)
            completness.triggered.connect(self.handleToggleCompletness)
            menu.addAction(self.scene().actionItemDelete)
            menu.addSeparator()
            menu.addAction(completness)
        return menu

    def handleToggleCompletness(self):
        """
        Toggle the complete attribute for this edge.
        """
        self.edge.complete = not self.edge.complete
        self.updateEdge()

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used to detect the collision between items in the graphics scene).
        :rtype: QPainterPath
        """
        path = super().painterPath()
        if self.tail:
            path.addPolygon(self.tail)
        return path

    def updateHead(self):
        """
        Update the Edge head polygon.
        """
        if self.path:

            if not self.edge.target:
                subpath = self.path[0]
                ending = subpath.line
                p1 = ending.p2()
            else:
                collection = self.intersections(self.edge.target.shape)
                if collection:
                    index = collection[-1][0]
                    subpath = self.path[index]
                    ending = subpath.line
                    p1 = collection[-1][1]
                else:
                    subpath = self.path[-1]
                    ending = subpath.line
                    p1 = ending.p2()

            angle = radians(ending.angle())

            p2 = p1 - QPointF(sin(angle + M_PI / 3.0) * self.size, cos(angle + M_PI / 3.0) * self.size)
            p3 = p1 - QPointF(sin(angle + M_PI - M_PI / 3.0) * self.size, cos(angle + M_PI - M_PI / 3.0) * self.size)

            self.head = QPolygonF([p1, p2, p3])

    def updateTail(self):
        """
        Update the Edge tail line.
        """
        if self.edge.complete:
            collection = self.intersections(self.edge.source.shape)
            if collection:
                index = collection[0][0]
                starting = self.path[index].line
                angle = radians(starting.angle())
                p1 = collection[0][1]
                p2 = p1 + QPointF(sin(angle + M_PI / 3.0) * self.size, cos(angle + M_PI / 3.0) * self.size)
                p3 = p1 + QPointF(sin(angle + M_PI - M_PI / 3.0) * self.size, cos(angle + M_PI - M_PI / 3.0) * self.size)
                self.tail = QPolygonF([p1, p2, p3])
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

        angle = line.angle()

        # Calculate head coordinates
        p1 = QPointF(line.p2().x() + (head_span / 2), line.p2().y())
        p2 = p1 - QPointF(sin(angle + M_PI / 3.0) * head_size, cos(angle + M_PI / 3.0) * head_size)
        p3 = p1 - QPointF(sin(angle + M_PI - M_PI / 3.0) * head_size, cos(angle + M_PI - M_PI / 3.0) * head_size)

        # Initialize edge head
        head = QPolygonF([p1, p2, p3])

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(line)

        # Draw the head
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QColor(0, 0, 0))
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
                painter.setBrush(self.tailBrush)
                painter.drawPolygon(self.tail)