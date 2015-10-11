# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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


from grapholed.datatypes import DistinctList
from grapholed.items import Item
from grapholed.items.edges import Edge
from PyQt5.QtCore import QPointF


class Node(Item):
    """
    This is the base class for all the graph nodes (ALL NODES MUST INHERIT FROM THIS CLASS!!!).
    """
    name = 'node'
    xmlname = 'node'

    def __init__(self, scene, description='', url='', **kwargs):
        """
        Initialize the node.
        :param scene: the scene where this node is being added.
        :param description: the description of this node.
        :param url: the url this node is referencing.
        """
        super().__init__()

        self._id = kwargs.get('id') if 'id' in kwargs else scene.uniqueID.next('n')
        self._description = description
        self._url = url

        self.edges = DistinctList()

    ################################################### PROPERTIES #####################################################

    @property
    def id(self):
        """
        Returns the node id.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, value):
        """
        Set the node id.
        :param value: the new node id.
        """
        self._id = value

    @property
    def description(self):
        """
        Returns the description of the node.
        :rtype: str
        """
        return self._description.strip()

    @description.setter
    def description(self, value):
        """
        Set the description of the node.
        :param value: the description of the node.
        """
        self._description = value.strip()

    @property
    def url(self):
        """
        Returns the url attached to the  node.
        :rtype: str
        """
        return self._url.strip()

    @url.setter
    def url(self, value):
        """
        Set the url attached to the node.
        :param value: the url to attach to the node.
        """
        self._url = value.strip()

    ################################################ AUXILIARY METHODS #################################################

    def copy(self, scene):
        """
        Create a copy of the current item (connected edges won't be copied).
        :param scene: a reference to the scene where this item is being copied.
        """
        shapePos = self.shape.mapToScene(self.shape.center())
        labelPos = self.shape.mapToScene(self.shape.label.mapToItem(self.shape, self.shape.label.center()))
        labelPos -= QPointF(self.shape.label.width() / 2, self.shape.label.height() / 2)

        node = self.__class__(scene=scene,
                              id=self.id,
                              description=self.description,
                              url=self.url,
                              width=self.shape.width(),
                              height=self.shape.height())

        node.shape.setPos(shapePos)
        node.shape.setLabelText(self.shape.labelText())
        node.shape.setLabelPos(node.shape.mapFromScene(labelPos))

        return node

    def addEdge(self, edge):
        """
        Add the given edge to the current node.
        :param edge: the edge to be added.
        """
        if not isinstance(edge, Edge):
            edge = edge.item
        self.edges.append(edge)

    def removeEdge(self, edge):
        """
        Remove the given edge from the current node.
        :param edge: the edge to be removed.
        """
        if not isinstance(edge, Edge):
            edge = edge.item
        self.edges.remove(edge)

    ################################################## ITEM EXPORT #####################################################

    def exportToGraphol(self, document):
        """
        Export the current node in Graphol format.
        :type document: QDomDocument
        :param document: the XML document where this item will be inserted.
        :rtype: QDomElement
        """
        shape_pos = self.shape.mapToScene(self.shape.center())
        label_pos = self.shape.mapToScene(self.shape.label.mapToItem(self.shape, self.shape.label.center()))

        # create the root element for this node
        node = document.createElement('node')
        node.setAttribute('id', self.id)
        node.setAttribute('type', self.xmlname)

        # add node attributes
        url = document.createElement('data:url')
        url.appendChild(document.createTextNode(self.url))
        description = document.createElement('data:description')
        description.appendChild(document.createTextNode(self.description))

        # add the shape geometry
        geometry = document.createElement('shape:geometry')
        geometry.setAttribute('height', self.shape.height())
        geometry.setAttribute('width', self.shape.width())
        geometry.setAttribute('x', shape_pos.x())
        geometry.setAttribute('y', shape_pos.y())

        # add the shape label
        label = document.createElement('shape:label')
        label.setAttribute('height', self.shape.label.height())
        label.setAttribute('width', self.shape.label.width())
        label.setAttribute('x', label_pos.x())
        label.setAttribute('y', label_pos.y())
        label.appendChild(document.createTextNode(self.shape.label.text()))

        node.appendChild(url)
        node.appendChild(description)
        node.appendChild(geometry)
        node.appendChild(label)

        return node

    ################################################## ITEM DRAWING ####################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        raise NotImplementedError('method `image` must be implemented in inherited class')


from grapholed.items.nodes.attribute import AttributeNode
from grapholed.items.nodes.concept import ConceptNode
from grapholed.items.nodes.complement import ComplementNode
from grapholed.items.nodes.datatype_restriction import DatatypeRestrictionNode
from grapholed.items.nodes.disjoint_union import DisjointUnionNode
from grapholed.items.nodes.domain_restriction import DomainRestrictionNode
from grapholed.items.nodes.enumeration import EnumerationNode
from grapholed.items.nodes.individual import IndividualNode
from grapholed.items.nodes.intersection import IntersectionNode
from grapholed.items.nodes.property_assertion import PropertyAssertionNode
from grapholed.items.nodes.range_restriction import RangeRestrictionNode
from grapholed.items.nodes.role import RoleNode
from grapholed.items.nodes.role_chain import RoleChainNode
from grapholed.items.nodes.role_inverse import RoleInverseNode
from grapholed.items.nodes.union import UnionNode
from grapholed.items.nodes.value_domain import ValueDomainNode
from grapholed.items.nodes.value_restriction import ValueRestrictionNode


__all__ = [
    'AttributeNode',
    'ConceptNode',
    'ComplementNode',
    'DatatypeRestrictionNode',
    'DisjointUnionNode',
    'DomainRestrictionNode',
    'EnumerationNode',
    'IndividualNode',
    'IntersectionNode',
    'PropertyAssertionNode',
    'RangeRestrictionNode',
    'RoleNode',
    'RoleChainNode',
    'RoleInverseNode',
    'UnionNode',
    'ValueDomainNode',
    'ValueRestrictionNode',
]
