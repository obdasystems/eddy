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


from enum import unique

from eddy.core.datatypes.common import Enum_, IntEnum_


@unique
class Color(Enum_):
    """
    This class defines predicate nodes available colors.
    """
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


@unique
class DiagramMode(IntEnum_):
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
