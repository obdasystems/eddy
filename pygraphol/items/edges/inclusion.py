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


from pygraphol.items.edges import Edge
from pygraphol.items.edges.shapes import InclusionEdgeShape


class InclusionEdge(Edge):
    """
    This class implements the Inclusion node.
    """
    name = 'inclusion'
    xmlname = 'inclusion'
    type = Edge.InclusionEdge

    def __init__(self, scene, source, target=None, **kwargs):
        """
        Initialize the node.
        :param scene: the scene where this edge is being added.
        :param source: the edge source node.
        :param target: the edge target node (if any).
        """
        super().__init__(scene, source, target, **kwargs)
        self.shape = InclusionEdgeShape(item=self, **kwargs)
        self.complete = False

    ############################################ EDGE REPRESENTATION ###################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        return InclusionEdgeShape.image(**kwargs)