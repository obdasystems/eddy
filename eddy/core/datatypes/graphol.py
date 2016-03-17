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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from enum import unique, IntEnum, Enum
from types import DynamicClassAttribute

from eddy.core.regex import RE_CARDINALITY


@unique
class Identity(Enum):
    """
    This class defines all the identities a graphol node may assume.
    """
    __order__ = 'Neutral Concept Role Attribute ValueDomain Instance Value RoleInstance AttributeInstance Unknown'

    Neutral = 'Neutral'
    Concept = 'Concept'
    Role = 'Role'
    Attribute = 'Attribute'
    ValueDomain = 'Value Domain'
    Instance = 'Instance'
    Value = 'Value'
    RoleInstance = 'Role Instance'
    AttributeInstance = 'Attribute Instance'
    Unknown = 'Unknown'


@unique
class Item(IntEnum):
    """
    This class defines all the available Graphol items.
    The enum is ordered according to Graphol elements' classes.
    Changing the order of the enum elements will affect node properties results such as 'predicate' and 'constructor'.
    """
    __order__ = 'ConceptNode AttributeNode RoleNode ValueDomainNode IndividualNode ValueRestrictionNode' \
                'DomainRestrictionNode RangeRestrictionNode UnionNode EnumerationNode ComplementNode RoleChainNode' \
                'RoleInverseNode DatatypeRestrictionNode DisjointUnionNode PropertyAssertionNode InclusionEdge' \
                'InputEdge InstanceOfEdge LabelEdge LabelNode Undefined'

    Undefined = 0

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

    InclusionEdge = 18
    InputEdge = 19
    InstanceOfEdge = 20

    LabelEdge = 21
    LabelNode = 22

    @classmethod
    def forValue(cls, value):
        """
        Returns the Item matching the given value.
        :type value: T <= int | str | Item
        :rtype: Item
        """
        if isinstance(value, Item):
            return value
        else:
            value = int(value)
            for x in cls:
                if x.value == value:
                    return x
        return None

    @DynamicClassAttribute
    def label(self):
        """
        The label of the Enum member.
        :rtype: str
        """
        return {
            Item.AttributeNode: 'attribute node', Item.ComplementNode: 'complement node',
            Item.ConceptNode: 'concept node', Item.DatatypeRestrictionNode: 'datatype restriction node',
            Item.DisjointUnionNode: 'disjoint union node', Item.DomainRestrictionNode: 'domain restriction node',
            Item.EnumerationNode: 'enumeration node', Item.IndividualNode: 'individual node',
            Item.IntersectionNode: 'intersection node', Item.PropertyAssertionNode: 'property assertion node',
            Item.RangeRestrictionNode: 'range restriction node', Item.RoleNode: 'role node',
            Item.RoleChainNode: 'role chain node', Item.RoleInverseNode: 'role inverse node',
            Item.UnionNode: 'union node', Item.ValueDomainNode: 'value domain node',
            Item.ValueRestrictionNode: 'value restriction node', Item.InclusionEdge: 'inclusion edge',
            Item.InputEdge: 'input edge', Item.InstanceOfEdge: 'instanceOf edge',
            Item.LabelNode: 'node label', Item.LabelEdge: 'edge label', Item.Undefined: 'undefined item',
        }[self]


@unique
class Restriction(Enum):
    """
    This class defines all the available restrictions for the Domain and Range restriction nodes.
    """
    __order__ = 'Exists Forall Cardinality Self'

    Exists = 'Existential: exists'
    Forall = 'Universal: forall'
    Cardinality = 'Cardinality: (min, max)'
    Self = 'Self: self'

    @classmethod
    def forLabel(cls, label):
        """
        Returns the restriction matching the given label.
        :type label: str
        :rtype: Restriction
        """
        label = label.lower().strip()
        for x in {Restriction.Exists, Restriction.Forall, Restriction.Self}:
            if label == x.label:
                return x
        match = RE_CARDINALITY.match(label)
        if match:
            return Restriction.Cardinality
        return None

    @DynamicClassAttribute
    def label(self):
        """
        The label of the Enum member.
        :rtype: str
        """
        return {
            Restriction.Exists: 'exists',
            Restriction.Forall: 'forall',
            Restriction.Self: 'self',
            Restriction.Cardinality: '({min},{max})',
        }[self]


@unique
class Special(Enum):
    """
    This class defines special nodes types.
    """
    __order__ = 'Top Bottom'

    Top = 'TOP'
    Bottom = 'BOTTOM'

    @classmethod
    def forValue(cls, value):
        """
        Returns the special type matching the given value.
        :type value: str
        :rtype: Special
        """
        for x in cls:
            if x.value == value.upper().strip():
                return x
        return None