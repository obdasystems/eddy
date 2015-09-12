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


from math import sin, cos, radians, pi as M_PI
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QFont, QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsTextItem


class Label(QGraphicsTextItem):
    """
    This class implements the label to be attached to the graph edges.
    """
    textBrush = QColor(0, 0, 0, 255)
    textFont = QFont('Arial', 9, QFont.Light)

    def __init__(self, text='', parent=None):
        """
        Initialize the label.
        :param parent: the parent node.
        """
        super().__init__(parent)
        self.moved = False
        self.command = None
        self.setDefaultTextColor(self.textBrush)
        self.setFont(self.textFont)
        self.setText(text)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    ################################################ AUXILIARY METHODS #################################################

    def center(self):
        """
        Returns the point at the center of the shape.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def defaultPos(self):
        """
        Returns the label default position.
        :rtype: QPointF
        """
        parent = self.parentItem()
        if not parent.path:
            # which happens when the Edge is first created before updateEdge is called
            return None

        if len(parent.path) % 2 == 0:

            # if we have an even number of subpaths compute the position
            # of the label according the breakpoint in the middle (eventually
            # adjusting the distance of the label form the subpath not to overlap text)
            middleP = parent.breakpoints[int(len(parent.breakpoints) / 2)]
            middleP = QPointF(middleP.x() - (self.width() / 2), middleP.y() - (self.height() / 2))

            # get the subpaths which have the selected breakpoint in common
            subpath1 = parent.path[int(len(parent.path) / 2) - 1]
            subpath2 = parent.path[int(len(parent.path) / 2)]

            spaceX1 = 0
            spaceX2 = 0
            spaceY = -16

            # compute the required space factors
            angle = radians(subpath1.line.angleTo(subpath2.line))
            if angle < M_PI:
                # FIXME: THIS NEEDS SEVERAL IMPROVEMENTS!!
                spaceX1 = -80 * sin(radians(subpath1.line.angle()))
                spaceX2 = -80 * sin(radians(subpath2.line.angle()))
                spaceY += spaceY * sin(angle) * 1.8

            return QPointF(middleP.x() + spaceX1 + spaceX2, middleP.y() + spaceY)

        else:

            # if we have an odd number of subpaths compute the position of the label
            # according to the center point of the subpath in the middle (eventually
            # adjusting the distance of the label form the subpath not to overlap text)
            subpath = parent.path[int(len(parent.path) / 2)]

            try:
                # if the subpath is the first one, use as source point the intersection if
                # the subpath with the source shape to better approximate the label position
                if parent.path.index(subpath) != 0:
                    raise IndexError
                sourceP = parent.intersection(parent.edge.source.shape)[1]
            except (TypeError, IndexError, AttributeError):
                # use the default breakpoint position
                sourceP = subpath.source

            try:
                # if the subpath is the last one, use as source point the intersection if
                # the subpath with the target shape to better approximate the label position
                if parent.path.index(subpath) != len(parent.path) - 1:
                    raise IndexError
                targetP = parent.intersection(parent.edge.target.shape)[1]
            except (TypeError, IndexError, AttributeError):
                # use the default breakpoint position
                targetP = subpath.target

            # spaces to be added to the position of the label according the the subpath angle
            spaceX = -40
            spaceY = -16

            # calculate the center of the label, which is moved from the center of the subpath
            middleP = QPointF(((sourceP.x() + targetP.x()) / 2) - (self.width() / 2),
                              ((sourceP.y() + targetP.y()) / 2) - (self.height() / 2))

            # increment the distance from the edge subpath according the angle
            return QPointF(middleP.x() + spaceX * sin(radians(subpath.line.angle())),
                           middleP.y() + spaceY * cos(radians(subpath.line.angle())))

    def height(self):
        """
        Returns the height of the text label.
        :rtype: int
        """
        return self.boundingRect().height()

    def painterPath(self):
        """
        Returns the current label as QPainterPath (used to detect the collision between items in the graphics scene).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def setText(self, text):
        """
        Set the given text as plain text.
        :param text: the text value to set.
        """
        self.setPlainText(text)
        self.updatePos()

    def text(self):
        """
        Returns the current shape text (shortcut for self.toPlainText()).
        :return: str
        """
        return self.toPlainText()

    def updatePos(self):
        """
        Update the current text position with respect to the shape.
        """
        self.setPos(self.defaultPos() or self.pos())

    def width(self):
        """
        Returns the width of the text label.
        :rtype: int
        """
        return self.boundingRect().width()