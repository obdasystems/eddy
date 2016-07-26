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


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPen

from enum import Enum, unique, IntEnum


class Brush(object):
    """
    This class defines the brushes used in Eddy.
    """
    NoBrush = QBrush(Qt.NoBrush)
    Black255A = QBrush(QColor(0, 0, 0, 255))
    Blue255A = QBrush(QColor(66, 165, 245, 255))
    Green160A = QBrush(QColor(43, 173, 63, 160))
    Grey255A = QBrush(QColor(80, 80, 80, 255))
    LightGrey255A = QBrush(QColor(222, 222, 222, 255))
    Red160A = QBrush(QColor(179, 12, 12, 160))
    Yellow255A = QBrush(QColor(251, 255, 148, 255))
    White255A = QBrush(QColor(252, 252, 252, 255))


@unique
class Color(Enum):
    """
    This class defines predicate nodes available colors.
    """
    __order__ = 'White Yellow Orange Red Magenta Purple Blue Teal Green Lime Grey Brown Beige'

    White = '#fcfcfc'
    Yellow = '#f0e50c'
    Orange = '#f29210'
    Red = '#e41b20'
    Magenta = '#ff0090'
    Purple = '#724e9d'
    Blue = '#1760ab'
    Teal = '#16ccef'
    Green = '#2da735'
    Lime = '#86f42e'
    Grey = '#646b63'
    Brown = '#6f4f28'
    Beige = '#c2b078'

    @classmethod
    def forValue(cls, value):
        """
        Returns the color matching the given HEX code.
        :type value: str
        :rtype: Color
        """
        for x in cls:
            if x.value == value.lower():
                return x
        return None


@unique
class DiagramMode(IntEnum):
    """
    This class defines the diagram operational modes.
    """
    Idle = 0
    NodeAdd = 1
    NodeMove = 2
    NodeResize = 3
    EdgeAdd = 4
    EdgeAnchorMove = 5
    EdgeBreakPointMove = 6
    LabelMove = 7
    LabelEdit = 8
    RubberBandDrag = 9
    SceneDrag = 10


class Pen(object):
    """
    This class defines the pens used in Eddy.
    """
    NoPen = QPen(Qt.NoPen)
    DashedBlack1Pt = QPen(Brush.Black255A, 1.0, Qt.DashLine)
    DashedBlack1_1Pt_x3 = QPen(Brush.Black255A, 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
    DashedBlack1_1Pt_x3.setDashPattern([3, 3])
    DashedBlack1_1Pt_x5 = QPen(Brush.Black255A, 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
    DashedBlack1_1Pt_x5.setDashPattern([5, 5])
    SolidBlack1Pt = QPen(Brush.Black255A, 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    SolidBlack1_1Pt = QPen(Brush.Black255A, 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    SolidGrey0Pt = QPen(Brush.Grey255A, 0, Qt.SolidLine)