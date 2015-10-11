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


class Item(object):
    """
    Base class for all the graph elements.
    NOTE: node types MUST be lower than edge type!!!
    """
    ## NODES TYPES
    ConceptNode = 1
    AttributeNode = 2
    RoleNode = 3
    ValueDomainNode = 4
    IndividualNode = 5
    ValueRestrictionNode = 6
    DomainRestrictionNode = 7
    RangeRestrictionNode = 8
    UnionNode = 9
    EnumerationNode = 10
    ComplementNode = 11
    RoleChainNode = 12
    IntersectionNode = 13
    RoleInverseNode = 14
    DatatypeRestrictionNode = 15
    DisjointUnionNode = 16
    PropertyAssertionNode = 17

    ## EDGES TYPES
    InclusionEdge = 18
    InputEdge = 19
    InstanceOfEdge = 20

    ################### !!! THE FOLLOWING ATTRIBUTES MUST BE INITIALIZED IN INHERITED CLASSES !!! ######################

    id = None # the item id (generated using grapholed.tools.UniqueID()
    shape = None # the shape implementing this item
    type = None # the item type

    name = 'item' # a lowercase name which identifies this object
    xmlname = 'item' # a lowercase identifier used to identify this node in XML related documents

    ############################################# BASIC ITEM INTERFACE #################################################

    def __init__(self):
        """
        Initialize the item.
        """
        super().__init__()

    def isEdge(self):
        """
        Tells whether the current element is a graph Edge.
        :return: True if the item is an edge, False otherwise.
        :rtype: bool
        """
        return Item.InclusionEdge <= self.type <= Item.InstanceOfEdge

    def isNode(self):
        """
        Tells whether the current element is a graph Node.
        :return: True if the item is a node, False otherwise.
        :rtype: bool
        """
        return Item.ConceptNode <= self.type <= Item.PropertyAssertionNode

    ################################################## ITEM EXPORT #####################################################

    def exportToGraphol(self, document):
        """
        Export the current node in Graphol format.
        :type document: QDomDocument
        :param document: the XML document where this item will be inserted
        :rtype: QDomElement
        """
        raise NotImplementedError('method `exportToGraphol` must be implemented in inherited class')

    ################################################## ITEM DRAWING ####################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        raise NotImplementedError('method `image` must be implemented in inherited class')

    ############################################# STRING REPRESENTATION ################################################

    def __repr__(self):
        """
        Object representaton.
        """
        return '%s:%s' % (self.__class__.__name__, self.id)


from grapholed.items.nodes import *
from grapholed.items.edges import *


__mapping__ = {
    ConceptNode.xmlname: ConceptNode,
    ValueDomainNode.xmlname: ValueDomainNode,
    RoleNode.xmlname: RoleNode,
    IndividualNode.xmlname: IndividualNode,
    AttributeNode.xmlname: AttributeNode,
    ValueRestrictionNode.xmlname: ValueRestrictionNode,
    DomainRestrictionNode.xmlname: DomainRestrictionNode,
    RangeRestrictionNode.xmlname: RangeRestrictionNode,
    UnionNode.xmlname: UnionNode,
    EnumerationNode.xmlname: EnumerationNode,
    ComplementNode.xmlname: ComplementNode,
    RoleChainNode.xmlname: RoleChainNode,
    IntersectionNode.xmlname: IntersectionNode,
    RoleInverseNode.xmlname: RoleInverseNode,
    DatatypeRestrictionNode.xmlname: DatatypeRestrictionNode,
    DisjointUnionNode.xmlname: DisjointUnionNode,
    PropertyAssertionNode.xmlname: PropertyAssertionNode,
    InclusionEdge.xmlname: InclusionEdge,
    InputEdge.xmlname: InputEdge,
    InstanceOfEdge.xmlname: InstanceOfEdge,
}


__all__ = [
    'ConceptNode',
    'ValueDomainNode',
    'RoleNode',
    'IndividualNode',
    'AttributeNode',
    'ValueRestrictionNode',
    'DomainRestrictionNode',
    'RangeRestrictionNode',
    'UnionNode',
    'EnumerationNode',
    'ComplementNode',
    'RoleChainNode',
    'IntersectionNode',
    'RoleInverseNode',
    'DatatypeRestrictionNode',
    'DisjointUnionNode',
    'PropertyAssertionNode',
    'InclusionEdge',
    'InputEdge',
    'InstanceOfEdge',
]