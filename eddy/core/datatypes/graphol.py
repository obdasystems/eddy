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
from eddy.core.functions.misc import rstrip
from eddy.core.regex import RE_CARDINALITY, RE_CAMEL_SPACE


@unique
class Identity(Enum_):
    """
    This class defines graphol expression identities.
    """
    Neutral = 'Neutral'
    Concept = 'Concept'
    Role = 'Role'
    Attribute = 'Attribute'
    ValueDomain = 'Value Domain'
    Individual = 'Individual'
    Value = 'Value'
    RoleInstance = 'Role Instance'
    AttributeInstance = 'Attribute Instance'
    Facet = 'Facet'
    Unknown = 'Unknown'


@unique
class Item(IntEnum_):
    """
    This class defines all the available elements for graphol diagrams.
    """
    # PREDICATES IRI BASED
    ConceptIRINode = 95531
    AttributeIRINode = 95532
    RoleIRINode = 95533
    ValueDomainIRINode = 95534
    IndividualIRINode = 95535

    # PREDICATES
    ConceptNode = 65537
    AttributeNode = 65538
    RoleNode = 65539
    ValueDomainNode = 65540
    IndividualNode = 65541

    # CONSTRUCTORS
    DomainRestrictionNode = 65542
    RangeRestrictionNode = 65543
    UnionNode = 65544
    EnumerationNode = 65545
    ComplementNode = 65546
    RoleChainNode = 65547
    IntersectionNode = 65548
    RoleInverseNode = 65549
    DatatypeRestrictionNode = 65550
    DisjointUnionNode = 65551
    PropertyAssertionNode = 65552
    FacetNode = 65553

    # EDGES
    InclusionEdge = 65554
    EquivalenceEdge = 65555
    InputEdge = 65556
    MembershipEdge = 65557
    SameEdge = 65558
    DifferentEdge = 65559

    # EXTRA
    Label = 65560
    Undefined = 65561

    @property
    def realName(self):
        """
        Returns the item readable name, i.e: attribute node, concept node.
        :rtype: str
        """
        return RE_CAMEL_SPACE.sub(r'\g<1> \g<2>', self.name).lower()

    @property
    def shortName(self):
        """
        Returns the item short name, i.e: attribute, concept.
        :rtype: str
        """
        return rstrip(self.realName, ' node', ' edge')


@unique
class Restriction(Enum_):
    """
    This class defines all the available restrictions for domain and range restriction nodes.
    """
    Exists = 'Existential: exists'
    Forall = 'Universal: forall'
    Cardinality = 'Cardinality: (min, max)'
    Self = 'Self: self'

    @property
    def shortName(self):
        """
        Returns the restriction short name, i.e: existential, universal, cardinality, self.
        :rtype: str
        """
        return self.value[:self.value.index(':')].lower()

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
        }[self].format(*('-' if x is None else x for x in args))


@unique
class Special(Enum_):
    """
    This class defines special nodes types.
    """
    Top = 'TOP'

    #TopConcept = 'owl:Thing | owl:thing'
    TopConcept = {}
    TopConcept[1] = 'owl:Thing'
    TopConcept[2] = 'owl:thing'

    #TopAttribute = 'owl:TopDataProperty | owl:topDataProperty | owl:topdataproperty'
    TopAttribute = {}
    TopAttribute[1] = 'owl:TopDataProperty'
    TopAttribute[2] = 'owl:topDataProperty'
    TopAttribute[3] = 'owl:topdataproperty'

    #TopRole = 'owl:TopObjectProperty | owl:topObjectProperty | owl:topobjectproperty'
    TopRole = {}
    TopRole[1] = 'owl:TopObjectProperty'
    TopRole[2] = 'owl:topObjectProperty'
    TopRole[3] = 'owl:topobjectproperty'

    TopEntities = {}

    TopEntities[1] = 'owl:Thing'
    TopEntities[2] = 'owl:thing'
    TopEntities[3] = 'owl:TopDataProperty'
    TopEntities[4] = 'owl:topDataProperty'
    TopEntities[5] = 'owl:topdataproperty'
    TopEntities[6] = 'owl:TopObjectProperty'
    TopEntities[7] = 'owl:topObjectProperty'
    TopEntities[8] = 'owl:topobjectproperty'

    AllTopEntities = 'TOP | owl:Thing | owl:thing | owl:TopDataProperty | owl:topDataProperty | owl:topdataproperty | \
    #                 owl:TopObjectProperty | owl:topObjectProperty | owl:topobjectproperty'

    Bottom = 'BOTTOM'

    BottomConcept = {}
    #BottomConcept = 'owl:Nothing | owl:nothing'
    BottomConcept[1] = 'owl:Nothing'
    BottomConcept[2] = 'owl:nothing'


    #BottomAttribute = 'owl:BottomDataProperty | owl:bottomDataProperty | owl:bottomdataproperty'
    BottomAttribute = {}
    BottomAttribute[1] = 'owl:BottomDataProperty'
    BottomAttribute[2] = 'owl:bottomDataProperty'
    BottomAttribute[3] = 'owl:bottomdataproperty'

    #BottomRole = 'owl:BottomObjectProperty | owl:bottomObjectProperty | owl:bottomobjectproperty'
    BottomRole = {}
    BottomRole[1] = 'owl:BottomObjectProperty'
    BottomRole[2] = 'owl:bottomObjectProperty'
    BottomRole[3] = 'owl:bottomobjectproperty'

    BottomEntities = {}

    BottomEntities[1] = 'owl:Nothing'
    BottomEntities[2] = 'owl:nothing'
    BottomEntities[3] = 'owl:BottomDataProperty'
    BottomEntities[4] = 'owl:bottomDataProperty'
    BottomEntities[5] = 'owl:bottomdataproperty'
    BottomEntities[6] = 'owl:BottomObjectProperty'
    BottomEntities[7] = 'owl:bottomObjectProperty'
    BottomEntities[8] = 'owl:bottomobjectproperty'

    AllBottomEntities = 'BOTTOM | owl:Nothing | owl:nothing | owl:BottomDataProperty | owl:bottomDataProperty | \
    #                   owl:bottomdataproperty | owl:BottomObjectProperty | owl:bottomObjectProperty | owl:bottomobjectproperty'

    def return_group(input):

        if (input is Special.TopConcept):
            return ['owl:Thing','owl:thing']
        if (input is Special.TopAttribute):
            return ['owl:TopDataProperty', 'owl:topDataProperty', 'owl:topdataproperty']
        if (input is Special.TopRole):
            return ['owl:TopObjectProperty','owl:topObjectProperty','owl:topobjectproperty']
        if (input is Special.AllTopEntities):
            return ['TOP','owl:Thing','owl:thing','owl:TopDataProperty','owl:topDataProperty','owl:topdataproperty', \
                      'owl:TopObjectProperty', 'owl:topObjectProperty', 'owl:topobjectproperty']

        if (input is Special.BottomConcept):
            return ['owl:Nothing','owl:nothing']
        if (input is Special.BottomAttribute):
            return ['owl:BottomDataProperty','owl:bottomDataProperty','owl:bottomdataproperty']
        if (input is Special.BottomRole):
            return ['owl:BottomObjectProperty','owl:bottomObjectProperty','owl:bottomobjectproperty']
        if (input is Special.AllBottomEntities):
            return ['BOTTOM','owl:Nothing','owl:nothing','owl:BottomDataProperty','owl:bottomDataProperty',\
                 'owl:bottomdataproperty','owl:BottomObjectProperty','owl:bottomObjectProperty','owl:bottomobjectproperty']