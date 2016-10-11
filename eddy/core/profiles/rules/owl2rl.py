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


from eddy.core.datatypes.graphol import Item, Identity, Restriction, Special
from eddy.core.datatypes.owl import Datatype, OWLProfile
from eddy.core.profiles.common import ProfileError
from eddy.core.profiles.rules.common import ProfileNodeRule
from eddy.core.profiles.rules.common import ProfileEdgeRule


class UnsupportedDatatypeRule(ProfileNodeRule):
    """
    Prevents from using datatypes which are outside of the OWL 2 RL profile.
    """
    def __call__(self, node):
        if node.type() is Item.ValueDomainNode:
            if node.datatype not in Datatype.forProfile(OWLProfile.OWL2RL):
                raise ProfileError('Datatype {} is forbidden in OWL 2 RL'.format(node.datatype.value))


class UnsupportedOperatorRule(ProfileNodeRule):
    """
    Prevents from using operator nodes which are not supported by the OWL 2 RL profile.
    """
    def __call__(self, node):
        if node.type() in {Item.DatatypeRestrictionNode, Item.FacetNode}:
            raise ProfileError('Usage of {} operator is forbidden in OWL 2 RL'.format(node.shortName))


class UnsupportedSpecialOnRoleAndAttributeNode(ProfileNodeRule):
    """
    Make sure that TOP and BOTTOM are not used in Role and Attribute nodes.
    """
    def __call__(self, node):
        if node.type() in {Item.AttributeNode, Item.RoleNode}:
            if Special.forValue(node.text()) is not None:
                raise ProfileError('Usage of {} {} is forbidden in OWL 2 RL'.format(node.text(), node.shortName))


class InclusionBetweenConceptExpressionRule(ProfileEdgeRule):
    """
    Make sure that inclusion edges are traced according to OWL 2 RL subClass and superClass definition.
    More information: https://www.w3.org/TR/owl2-profiles/
    """
    def __call__(self, source, edge, target):

        if edge.type() is Item.InclusionEdge:
            # We need to provide rules for OWL 2 RL concept inclusion. Value-Domain inclusions
            # are already forbidden by OWL 2 rules, so here we just consider the case where we
            # are connecting endpoints that either both Neutral, or at least one of the 2 is
            # identified as a Concept expression.
            if not {Identity.Role, Identity.Attribute, Identity.Unknown} & {source.identity(), target.identity()}:

                #############################################
                # EVALUATE INCLUSION SOURCE
                #################################

                # TOP concept cannot be source of concept inclusion in OWL 2 RL.
                if source.type() is Item.ConceptNode:
                    if Special.forValue(source.text()) is Special.Top:
                        raise ProfileError('Inclusion edges with a TOP concept as source are forbidden in OWL 2 RL')
                # Complement nodes cannot be source of concept inclusion in OWL 2 RL.
                elif source.type() is Item.ComplementNode:
                    raise ProfileError('Inclusion edges with a concept complement as source are forbidden in OWL 2 RL')
                # Universal domain/range restriction cannot be source of concept inclusion in OWL 2 RL.
                elif source.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                    if source.restriction() is Restriction.Forall:
                        raise ProfileError('Inclusion edges with a universal {} as source are forbidden in OWL 2 RL'.format(source.shortName))

                #############################################
                # EVALUATE INCLUSION TARGET
                #################################

                # TOP concept cannot be target of concept inclusion in OWL 2 RL.
                if target.type() is Item.ConceptNode:
                    if Special.forValue(target.text()) is Special.Top:
                        raise ProfileError('Inclusion edges with a TOP concept as target are forbidden in OWL 2 RL')
                # Enumeration nodes cannot be target of concept inclusion in OWL 2 RL.
                elif target.type() is Item.EnumerationNode:
                    raise ProfileError('Inclusion edges with an enumeration of individuals as target are forbidden in OWL 2 RL')
                # Union of concept expressions cannot be target of concept inclusion in OWL 2 RL.
                elif target.type() is Item.EnumerationNode:
                    raise ProfileError('Inclusion edges with a union of concept expressions as target are forbidden in OWL 2 RL')
                # Existential domain/range restriction and cardinality check.
                elif target.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                    if target.restriction() is Restriction.Exists:
                        raise ProfileError('Inclusion edges with an existential {} as target are forbidden in OWL 2 RL'.format(source.shortName))
                    elif target.restriction() is Restriction.Cardinality:
                        if target.cardinality('min') != 0 or target.cardinality('max') != 1:
                            raise ProfileError('Inclusion edges can only target cardinality {} with cardinality (0, 1) in OWL 2 RL'.format(target.shortName))


class InputValueToEnumerationNodeRule(ProfileEdgeRule):
    """
    Prevent the construction of value-domain expression composed of a oneOf of values.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.InputEdge:
            if target.type() is Item.EnumerationNode:
                if source.identity() is Identity.Value:
                    raise ProfileError('Enumeration of values is forbidden in OWL 2 RL')


class InputValueDomainToUnionNodeRule(ProfileEdgeRule):
    """
    Prevent the construction of union of value domain expressions.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.InputEdge:
            if target.type() in {Item.DisjointUnionNode, Item.UnionNode}:
                if Identity.ValueDomain in {source.identity(), target.identity()}:
                    raise ProfileError('{} of value-domain expressions is forbidden in OWL 2 RL'.format(target.shortName.capitalize()))