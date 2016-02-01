# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QObject

from eddy.core.datatypes import Item

from eddy.core.items import AttributeNode, ComplementNode, ConceptNode, DatatypeRestrictionNode
from eddy.core.items import DisjointUnionNode, DomainRestrictionNode, EnumerationNode
from eddy.core.items import IndividualNode, IntersectionNode, PropertyAssertionNode, RangeRestrictionNode
from eddy.core.items import RoleNode, RoleChainNode, RoleInverseNode, UnionNode, ValueDomainNode
from eddy.core.items import ValueRestrictionNode, InclusionEdge, InputEdge, InstanceOfEdge


class ItemFactory(QObject):
    """
    This class can be used to produce Graphol items.
    """
    def __init__(self, parent=None):
        """
        Initialize the factory.
        :type parent: QObject
        """
        super().__init__(parent)

    ####################################################################################################################
    #                                                                                                                  #
    #   FACTORY                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def create(item, scene, **kwargs):
        """
        Build and return a Graphol item instance using to the given parameters.
        :type item: Item
        :type scene: DiagramScene
        :type kwargs: dict
        :rtype: AbstractItem
        """
        # NOTE: do not use Item identity check here. While this may seem an error
        # it allow us to use the factory also when we create graphol items after
        # clicking on the palette button: the palette stores internally the type
        # of the item for each button but the Identity is lost (probably Qt handle
        # only integers as palette button id and the python to C++ conversion from
        # IntEnum to int is implicit!
        if item == Item.AttributeNode:
            return AttributeNode(scene=scene, **kwargs)
        if item == Item.ComplementNode:
            return ComplementNode(scene=scene, **kwargs)
        if item == Item.ConceptNode:
            return ConceptNode(scene=scene, **kwargs)
        if item == Item.DatatypeRestrictionNode:
            return DatatypeRestrictionNode(scene=scene, **kwargs)
        if item == Item.DisjointUnionNode:
            return DisjointUnionNode(scene=scene, **kwargs)
        if item == Item.DomainRestrictionNode:
            return DomainRestrictionNode(scene=scene, **kwargs)
        if item == Item.EnumerationNode:
            return EnumerationNode(scene=scene, **kwargs)
        if item == Item.IndividualNode:
            return IndividualNode(scene=scene, **kwargs)
        if item == Item.IntersectionNode:
            return IntersectionNode(scene=scene, **kwargs)
        if item == Item.PropertyAssertionNode:
            return PropertyAssertionNode(scene=scene, **kwargs)
        if item == Item.RangeRestrictionNode:
            return RangeRestrictionNode(scene=scene, **kwargs)
        if item == Item.RoleNode:
            return RoleNode(scene=scene, **kwargs)
        if item == Item.RoleChainNode:
            return RoleChainNode(scene=scene, **kwargs)
        if item == Item.RoleInverseNode:
            return RoleInverseNode(scene=scene, **kwargs)
        if item == Item.UnionNode:
            return UnionNode(scene=scene, **kwargs)
        if item == Item.ValueDomainNode:
            return ValueDomainNode(scene=scene, **kwargs)
        if item == Item.ValueRestrictionNode:
            return ValueRestrictionNode(scene=scene, **kwargs)
        if item == Item.InclusionEdge:
            return InclusionEdge(scene=scene, **kwargs)
        if item == Item.InputEdge:
            return InputEdge(scene=scene, **kwargs)
        if item == Item.InstanceOfEdge:
            return InstanceOfEdge(scene=scene, **kwargs)

        raise RuntimeError('unknown item ({}) in ItemFactory.create()'.format(item))