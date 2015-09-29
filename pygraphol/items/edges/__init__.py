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


from pygraphol.items import Item


class Edge(Item):
    """
    This is the base class for all the graph edges (ALL EDGES MUST INHERIT FROM THIS CLASS!!!).
    """
    name = 'edge'
    xmlname = 'edge'

    def __init__(self, scene, source, target=None, **kwargs):
        """
        Initialize the node.
        :param scene: the scene where this edge is being added.
        :param source: the edge source node.
        :param target: the edge target node (if any).
        """
        super(Edge, self).__init__()

        self._id = kwargs.get('id') if 'id' in kwargs else scene.uniqueID.next('e')

        self.source = source
        self.target = target

    ################################################### PROPERTIES #####################################################

    @property
    def id(self):
        """
        Returns the edge id.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, value):
        """
        Set the edge id.
        :param value: the new edge id.
        """
        self._id = value

    ############################################### AUXILIARY METHODS ##################################################

    def copy(self, scene):
        """
        Create a copy of the current edge.
        :param scene: a reference to the scene where this item is being copied.
        """
        edge = self.__class__(scene=scene, id=self.id, source=self.source, target=self.target)
        edge.shape.breakpoints = self.shape.breakpoints[:]
        return edge

    def other(self, node):
        """
        Returns the opposite endpoint of the given node.
        :raise AttributeError: if the given node is not an endpoint of this edge.
        :param node: the node we want to find the opposite endpoint.
        :rtype: Edge
        """
        if node == self.source:
            return self.target
        elif node == self.target:
            return self.source
        raise AttributeError('node %r is not attached to edge %r' % (node, self))

    ################################################## ITEM EXPORT #####################################################

    def exportToGraphol(self, document):
        """
        Export the current edge in Graphol format.
        :type document: QDomDocument
        :param document: the XML document where this item will be inserted.
        :rtype: QDomElement
        """
        ## ROOT ELEMENT
        edge = document.createElement('edge')
        edge.setAttribute('source', self.source.id)
        edge.setAttribute('target', self.target.id)
        edge.setAttribute('id', self.id)
        edge.setAttribute('type', self.xmlname)

        ## LINE GEOMETRY
        source = self.source.shape.anchor(self.shape)
        target = self.target.shape.anchor(self.shape)

        for p in [source] + self.shape.breakpoints + [target]:
            point = document.createElement('line:point')
            point.setAttribute('x', p.x())
            point.setAttribute('y', p.y())
            edge.appendChild(point)

        return edge

    ################################################## ITEM DRAWING ####################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        raise NotImplementedError('method `image` must be implemented in inherited class')


from pygraphol.items.edges.inclusion import InclusionEdge
from pygraphol.items.edges.input import InputEdge
from pygraphol.items.edges.instance_of import InstanceOfEdge

__all__ = [
    'InclusionEdge',
    'InputEdge',
    'InstanceOfEdge'
]