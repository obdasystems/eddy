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


from math import sin, cos, pi as M_PI

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QPainterPath

from eddy.core.datatypes.graphol import Item
from eddy.core.functions.geometry import angle, midpoint
from eddy.core.items.common import AbstractLabel
from eddy.core.qt import Font


class EdgeLabel(AbstractLabel):
    """
    This class implements the label to be attached to the graphol edges.
    """
    Type = Item.Label

    def __init__(self, text='', centered=True, parent=None):
        """
        Initialize the label.
        :type text: str
        :type centered: bool
        :type parent: QObject
        """
        super().__init__(parent)
        self.centered = centered
        self.setDefaultTextColor(QColor(0, 0, 0, 255))
        self.setFont(Font('Arial', 12, Font.Light))
        self.setText(text)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    #############################################
    #   INTERFACE
    #################################

    def isCentered(self):
        """
        Returns True if the label should be centered, False otherwise.
        :rtype: bool
        """
        return self.centered

    def paint(self, painter, option, widget=None):
        """
        Paint the label in the graphic view.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        parent = self.parentItem()
        if not parent.path.isEmpty():
            super().paint(painter, option, widget)

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def updatePos(self, points):
        """
        Update the current text position with respect to the shape.
        :type points: T <= tuple | list
        """
        if not points:
            return

        if self.centered:
            # Here the label should be centered in the edge path => we need to compute 2 different positions:
            #   1. when the edge path is composed of an even number of points (odd subpaths)
            #   2. when the edge path is composed of an odd number of points (even subpaths)
            if len(points) % 2 == 0:
                # If we have an even number of points, compute the position of the label
                # according to the middle point of the subpath connecting the middle points.
                p1 = points[int(len(points) / 2) - 1]
                p2 = points[int(len(points) / 2)]
                mid = midpoint(p1, p2)
                rad = angle(p1, p2)
                spaceX = -40
                spaceY = -16
                self.setPos(QPointF(mid.x() + spaceX * sin(rad), mid.y() + spaceY * cos(rad)))
            else:
                # If we have an odd number of points compute the
                # position of the label according the point in the middle.
                mid = points[int(len(points) / 2)]
                rad1 = angle(points[int(len(points) / 2) - 1], mid)
                rad2 = angle(mid, points[int(len(points) / 2) + 1])
                diff = rad2 - rad1
                spaceX1 = 0
                spaceX2 = 0
                spaceY = -16
                if 0 < diff < M_PI:
                    spaceX1 = -80 * sin(rad1)
                    spaceX2 = -80 * sin(rad2)
                    spaceY += spaceY * sin(diff) * 1.8
                self.setPos(QPointF(mid.x() + spaceX1 + spaceX2, mid.y() + spaceY))
        else:
            # Here instead we will place the label near the intersection with the target shape: this is mostly
            # used for input edges connecting role chain nodes and property assertion nodes, so we can inspect
            # visually the partecipation order of connected nodes without having to scroll the diagram.
            rad = angle(points[-2], points[-1])
            pos = points[-1] - QPointF(sin(rad + M_PI / 3.0) * 20, cos(rad + M_PI / 3.0) * 20)
            self.setPos(pos)