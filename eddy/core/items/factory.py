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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QObject

from eddy.core.datatypes.graphol import Item

from eddy.core.items.edges.inclusion import InclusionEdge
from eddy.core.items.edges.input import InputEdge
from eddy.core.items.edges.membership import MembershipEdge
from eddy.core.items.nodes.attribute import AttributeNode
from eddy.core.items.nodes.complement import ComplementNode
from eddy.core.items.nodes.concept import ConceptNode
from eddy.core.items.nodes.datatype_restriction import DatatypeRestrictionNode
from eddy.core.items.nodes.disjoint_union import DisjointUnionNode
from eddy.core.items.nodes.domain_restriction import DomainRestrictionNode
from eddy.core.items.nodes.enumeration import EnumerationNode
from eddy.core.items.nodes.facet import FacetNode
from eddy.core.items.nodes.individual import IndividualNode
from eddy.core.items.nodes.intersection import IntersectionNode
from eddy.core.items.nodes.property_assertion import PropertyAssertionNode
from eddy.core.items.nodes.range_restriction import RangeRestrictionNode
from eddy.core.items.nodes.role import RoleNode
from eddy.core.items.nodes.role_chain import RoleChainNode
from eddy.core.items.nodes.role_inverse import RoleInverseNode
from eddy.core.items.nodes.union import UnionNode
from eddy.core.items.nodes.value_domain import ValueDomainNode
from eddy.core.items.nodes.value_restriction import ValueRestrictionNode


class ItemFactory(QObject):
    """
    This class can be used to produce graphol items.
    """
    def __init__(self, parent=None):
        """
        Initialize the factory.
        :type parent: Diagram
        """
        super().__init__(parent)
    
    @classmethod
    def classForItem(cls, item):
        """
        Returns the class implementing the given item.
        :type item: Item
        :rtype: class 
        """
        item = Item.forValue(item)
        if item is Item.AttributeNode:
            return AttributeNode
        if item is Item.ComplementNode:
            return ComplementNode
        if item is Item.ConceptNode:
            return ConceptNode
        if item is Item.DatatypeRestrictionNode:
            return DatatypeRestrictionNode
        if item is Item.DisjointUnionNode:
            return DisjointUnionNode
        if item is Item.DomainRestrictionNode:
            return DomainRestrictionNode
        if item is Item.EnumerationNode:
            return EnumerationNode
        if item is Item.FacetNode:
            return FacetNode
        if item is Item.IndividualNode:
            return IndividualNode
        if item is Item.IntersectionNode:
            return IntersectionNode
        if item is Item.PropertyAssertionNode:
            return PropertyAssertionNode
        if item is Item.RangeRestrictionNode:
            return RangeRestrictionNode
        if item is Item.RoleNode:
            return RoleNode
        if item is Item.RoleChainNode:
            return RoleChainNode
        if item is Item.RoleInverseNode:
            return RoleInverseNode
        if item is Item.UnionNode:
            return UnionNode
        if item is Item.ValueDomainNode:
            return ValueDomainNode
        if item is Item.ValueRestrictionNode:
            return ValueRestrictionNode
        if item is Item.InclusionEdge:
            return InclusionEdge
        if item is Item.InputEdge:
            return InputEdge
        if item is Item.MembershipEdge:
            return MembershipEdge
        raise RuntimeError('unknown item type ({0})'.format(item))

    @classmethod
    def iconForItem(cls, item, width, height):
        """
        Returns an icon representing the given item.
        :type item: Item
        :type width: int
        :type height: int
        :rtype: QIcon
        """
        return ItemFactory.classForItem(item).icon(width=width, height=height)

    def create(self, item, **kwargs):
        """
        Build and return a graphol item instance using to the given parameters.
        :type item: Item
        :type kwargs: dict
        :rtype: AbstractItem
        """
        return ItemFactory.classForItem(item)(diagram=self.parent(), **kwargs)