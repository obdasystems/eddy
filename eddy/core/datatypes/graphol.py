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


from enum import unique, IntEnum, Enum

from eddy.core.functions.misc import cutR
from eddy.core.regex import RE_CARDINALITY, RE_CAMEL_SPACE


@unique
class Identity(Enum):
    """
    This class defines graphol expression identities.
    """
    __order__ = 'Neutral Concept Role Attribute ValueDomain ' \
                'Instance Value RoleInstance AttributeInstance ' \
                'Facet Unknown'

    Neutral = 'Neutral'
    Concept = 'Concept'
    Role = 'Role'
    Attribute = 'Attribute'
    ValueDomain = 'Value Domain'
    Instance = 'Instance'
    Value = 'Value'
    RoleInstance = 'Role Instance'
    AttributeInstance = 'Attribute Instance'
    Facet = 'Facet'
    Unknown = 'Unknown'


@unique
class Item(IntEnum):
    """
    This class defines all the available elements for graphol diagrams.
    """
    __order__ = 'ConceptNode AttributeNode RoleNode ValueDomainNode IndividualNode ' \
                'ValueRestrictionNode DomainRestrictionNode RangeRestrictionNode ' \
                'UnionNode EnumerationNode ComplementNode RoleChainNode RoleInverseNode ' \
                'DatatypeRestrictionNode DisjointUnionNode PropertyAssertionNode ' \
                'FacetNode InclusionEdge InputEdge MembershipEdge Label Undefined'

    # PREDICATES
    ConceptNode = 65537
    AttributeNode = 65538
    RoleNode = 65539
    ValueDomainNode = 65540
    IndividualNode = 65541
    ValueRestrictionNode = 65542

    # CONSTRUCTORS
    DomainRestrictionNode = 65543
    RangeRestrictionNode = 65544
    UnionNode = 65545
    EnumerationNode = 65546
    ComplementNode = 65547
    RoleChainNode = 65548
    IntersectionNode = 65549
    RoleInverseNode = 65550
    DatatypeRestrictionNode = 65551
    DisjointUnionNode = 65552
    PropertyAssertionNode = 65553
    FacetNode = 65554

    # EDGES
    InclusionEdge = 65555
    InputEdge = 65556
    MembershipEdge = 65557

    # EXTRA
    Label = 65558
    Undefined = 65559

    @classmethod
    def forValue(cls, value):
        """
        Returns the item type matching the given value.
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

    @property
    def realName(self):
        """
        Returns the item readable name, i.e: attribute node, concept node.
        :rtype: str
        """
        return RE_CAMEL_SPACE.sub('\g<1> \g<2>', self.name).lower()

    @property
    def shortName(self):
        """
        Returns the item short name, i.e: attribute, concept.
        :rtype: str
        """
        return cutR(self.realName, ' node', ' edge')
    

@unique
class Restriction(Enum):
    """
    This class defines all the available restrictions for domain and range restriction nodes.
    """
    __order__ = 'Exists Forall Cardinality Self'

    Exists = 'Existential: exists'
    Forall = 'Universal: forall'
    Cardinality = 'Cardinality: (min, max)'
    Self = 'Self: self'

    @classmethod
    def forLabel(cls, value):
        """
        Returns the restriction matching the given label.
        :type value: str
        :rtype: Restriction
        """
        value = value.lower().strip()
        for x in {Restriction.Exists, Restriction.Forall, Restriction.Self}:
            if value == x.toString():
                return x
        match = RE_CARDINALITY.match(value)
        if match:
            return Restriction.Cardinality
        return None

    def toString(self, *args):
        """
        Returns a formatted representation of the restriction.
        :rtype: str
        """
        return {
            Restriction.Exists: 'exists',
            Restriction.Forall: 'forall',
            Restriction.Self: 'self',
            Restriction.Cardinality: '({0},{1})',
        }[self].format(*args)


@unique
class Special(Enum):
    """
    This class defines special nodes types.
    """
    __order__ = 'Top Bottom'

    Top = 'TOP'
    Bottom = 'BOTTOM'

    @classmethod
    def forLabel(cls, value):
        """
        Returns the special type matching the given label.
        :type value: str
        :rtype: Special
        """
        for x in cls:
            if x.value == value.upper().strip():
                return x
        return None