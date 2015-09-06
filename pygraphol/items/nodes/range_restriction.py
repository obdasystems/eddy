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


from pygraphol.datatypes import RestrictionType
from pygraphol.items.nodes import Node
from pygraphol.items.nodes.shapes import Square


class RangeRestrictionNode(Node):
    """
    This class implements the 'Range restriction' node.
    """
    name = 'range restriction'
    xmlname = 'range-restriction'
    type = Node.RangeRestrictionNode

    def __init__(self, scene, **kwargs):
        """
        Initialize the 'Range restriction' node.
        :param scene: the scene where this node is being added.
        """
        super().__init__(scene, **kwargs)
        self.cardinality = dict(min=None, max=None)
        self.restriction = RestrictionType.exists
        self.shape = Square(item=self, rgb=(0, 0, 0), **kwargs)

    ############################################ NODE REPRESENTATION ###################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        return Square.image(rgb=(0, 0, 0), **kwargs)