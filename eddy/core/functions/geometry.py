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


import math

from PyQt5 import QtCore
from PyQt5 import QtGui


def angle(p1, p2):
    """
    Returns the angle (measured in radians) of the line connecting the given points.
    :type p1: QPointF
    :type p2: QPointF
    :rtype: float
    """
    return math.atan2(p1.y() - p2.y(), p2.x() - p1.x())


def distance(p1, p2):
    """
    Calculate the distance between the given points.
    :type p1: QPointF
    :type p2: QPointF
    :rtype: float
    """
    return math.sqrt(math.pow(p2.x() - p1.x(), 2) + math.pow(p2.y() - p1.y(), 2))


def intersection(l1, l2):
    """
    Return the intersection point of the given lines.
    Will return None if there is no intersection point.
    :type l1: QLineF
    :type l2: QLineF
    :rtype: QPointF
    """
    L = max(min(l1.p1().x(), l1.p2().x()), min(l2.p1().x(), l2.p2().x()))
    R = min(max(l1.p1().x(), l1.p2().x()), max(l2.p1().x(), l2.p2().x()))
    T = max(min(l1.p1().y(), l1.p2().y()), min(l2.p1().y(), l2.p2().y()))
    B = min(max(l1.p1().y(), l1.p2().y()), max(l2.p1().y(), l2.p2().y()))
    if (T, L) == (B, R):
        return QtCore.QPointF(L, T)
    return None


def createArea(p1, p2, degrees, size):
    """
    Creates an area between the given QPointF and according to the given angle and size.
    :type p1: QPointF
    :type p2: QPointF
    :type degrees: float
    :type size: int
    :rtype: QPolygonF
    """
    rad = math.radians(degrees)
    x = size / 2 * math.sin(rad)
    y = size / 2 * math.cos(rad)
    a = QtCore.QPointF(+x, +y)
    b = QtCore.QPointF(-x, -y)
    return QtGui.QPolygonF([p1 + a, p1 + b, p2 + b, p2 + a])


def midpoint(p1, p2):
    """
    Calculate the midpoint between the given points.
    :type p1: QQPointF
    :type p2: QPointF
    :rtype: QPointF
    """
    return QtCore.QPointF(((p1.x() + p2.x()) / 2), ((p1.y() + p2.y()) / 2))


def projection(line, p):
    """
    Calculate the projection of the given point on the given line.
    Will return a tuple containing the length of the segment connecting the
    original point with its projection, and the coordinate of the projected point.
    :type line: QLineF
    :type p: QPointF
    :rtype: tuple
    """
    x1 = line.x1()
    y1 = line.y1()
    x2 = line.x2()
    y2 = line.y2()
    x3 = p.x()
    y3 = p.y()

    kk = ((y2 - y1) * (x3 - x1) - (x2 - x1) * (y3 - y1)) / (math.pow(y2 - y1, 2) + math.pow(x2 - x1, 2))
    x4 = x3 - kk * (y2 - y1)
    y4 = y3 + kk * (x2 - x1)

    p1 = QtCore.QPointF(x3, y3)
    p2 = QtCore.QPointF(x4, y4)

    return distance(p1, p2), p2