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


from PyQt5.QtGui import QPolygonF

from datatypes.misc import Brush, Pen


class Polygon(object):
    """
    This class is used to store shape data for Diagram item objects.
    For each object it will store:

        - geometrical data to be drawn on screen (either QRectF, QPolygonF or QPainterPath);
        - the brush used to draw the geometrical shape;
        - the pen used to draw the geometrical shape.
    """
    def __init__(self, geometry=QPolygonF(), brush=Brush.NoBrush, pen=Pen.NoPen):
        """
        Initialize the polygon.
        :type geometry: T <= QRectF|QPolygonF|QPainterPath
        :type brush: QBrush
        :type pen: QPen
        """
        self._geometry = geometry
        self._brush = brush
        self._pen = pen

    #############################################
    #   INTERFACE
    #################################

    def brush(self):
        """
        Returns the brush used to draw the shape.
        :rtype: QBrush
        """
        return self._brush

    def geometry(self):
        """
        Returns the polygon geometry.
        :rtype: T <= QRectF|QPolygonF|QPainterPath
        """
        return self._geometry

    def pen(self):
        """
        Returns the pen used to draw the shape.
        :rtype: QPen
        """
        return self._pen

    def setBrush(self, brush):
        """
        Set the brush used to draw the shape.
        :type brush: QBrush
        """
        self._brush = brush

    def setGeometry(self, geometry):
        """
        Set the shape polygon.
        :type geometry: T <= QRectF|QPolygonF|QPainterPath
        """
        self._geometry = geometry

    def setPen(self, pen):
        """
        Set the brush used to draw the shape.
        :type pen: QPen
        """
        self._pen = pen