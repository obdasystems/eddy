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

from eddy.core.datatypes.graphol import Item, Identity, Restriction, Special
from eddy.core.items.nodes.common.base import PredicateNodeMixin
from eddy.core.owl import OWL2Datatype, OWL2Profiles
from eddy.core.profiles.common import ProfileError
from eddy.core.profiles.rules.common import ProfileNodeRule
from eddy.core.profiles.rules.common import ProfileEdgeRule

class ReflexivityUnsupported(ProfileNodeRule):
    """
    Prevents from using reflexivity in roles which is outside of the OWL 2 QL profile.
    """
    def __call__(self, node):
        if isinstance(node, PredicateNodeMixin):
            if node.iri:
                if node.iri.reflexive:
                    raise ProfileError('({}) Reflexivity of roles is forbidden in OWL 2 RL'.format(str(node.iri)))


class UnsupportedDatatypeRule(ProfileNodeRule):
    """
    Prevents from using datatypes which are outside of the OWL 2 RL profile.
    """
    def __call__(self, node):
        if node.type() is Item.ValueDomainNode:
            if node.iri and not OWL2Datatype.forProfile(OWL2Profiles.OWL2RL):
                raise ProfileError('Use of datatype {} is forbidden in OWL 2 RL'.format(str(node.iri)))
            '''
            if node.datatype not in Datatype.forProfile(OWL2Profile.OWL2RL):
                raise ProfileError('Datatype {} is forbidden in OWL 2 RL'.format(node.datatype.value))
            '''


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
            if node.iri and (node.iri.isTopObjectProperty() or node.iri.isBottomObjectProperty() or  node.iri.isTopDataProperty() or node.iri.isBottomDataProperty()):
                raise ProfileError('Use of {} is forbidden in OWL 2 RL'.format(str(node.iri)))
            '''
            if Special.valueOf(node.text()) is not None:
                raise ProfileError('Usage of {} {} is forbidden in OWL 2 RL'.format(node.text(), node.shortName))
            '''


class EquivalenceBetweenConceptExpressionRule(ProfileEdgeRule):
    """
    Make sure that equivalence edges are traced according to OWL 2 RL subClass and superClass definition.
    More information: https://www.w3.org/TR/owl2-profiles/
    """
    def __call__(self, source, edge, target):

        if edge.type() is Item.InclusionEdge:
            # Similarily as for the Inclusion edge, we provide rules for OWL 2 RL concept expressions equivalence.
            # Because equivalence express a double inclusion we treat each of the endpoints in the same way.
            if not {Identity.Role, Identity.Attribute, Identity.Unknown} & {source.identity(), target.identity()}:
                for node in (source, target):
                    # TOP concept cannot be part of concept equivalence in OWL 2 RL.
                    if node.type() is Item.ConceptNode:
                        if node.iri and (node.iri.isOwlThing() or node.iri.isTopObjectProperty() or node.iri.isTopDataProperty()):
                            raise ProfileError('Use of Equivalence axioms involving a TOP predicate is forbidden in OWL 2 RL')
                    # Complement nodes cannot be part of concept equivalence in OWL 2 RL.
                    elif node.type() is Item.ComplementNode:
                        raise ProfileError('Use of Equivalence axioms involving a concept complement is forbidden in OWL 2 RL')
                    # Enumeration nodes cannot be part of concept equivalence in OWL 2 RL.
                    elif node.type() is Item.EnumerationNode:
                        raise ProfileError('Use of Equivalence axioms involving an enumeration of individuals is forbidden in OWL 2 RL')
                    # Union of concept expressions cannot be part of concept equivalence in OWL 2 RL.
                    elif node.type() is Item.EnumerationNode:
                        raise ProfileError('Use of Equivalence axioms involving an union of concept expressions is forbidden in OWL 2 RL')
                    # Domain/range restriction cannot be part of concept equivalence in OWL 2 RL.
                    elif node.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                        f1 = lambda x: x.type() is Item.InputEdge
                        f2 = lambda x: x.type() is Item.EnumerationNode
                        if not node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                            raise ProfileError('Existential {} must specify an Enumeration as filler when involved '
                                               'in an equivalence between concept expressions in OWL 2 RL'.format(target.shortName))


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
                    if source.iri and (
                            source.iri.isOwlThing() or source.iri.isTopObjectProperty() or source.iri.isTopDataProperty()):
                        raise ProfileError('Inclusion axioms involving a TOP predicate is forbidden in OWL 2 RL')
                # Complement nodes cannot be source of concept inclusion in OWL 2 RL.
                elif source.type() is Item.ComplementNode:
                    raise ProfileError('Inclusion with a concept complement as source is forbidden in OWL 2 RL')
                # OWL 2 RL admits only existential restriction as source for inclusion.
                elif source.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                    if source.restriction() is not Restriction.Exists:
                        r = source.restriction()
                        raise ProfileError('Inclusion with a {} {} as source is forbidden in OWL 2 RL'.format(r.shortName, source.shortName))

                #############################################
                # EVALUATE INCLUSION TARGET
                #################################

                # TOP concept cannot be target of concept inclusion in OWL 2 RL.
                if target.type() is Item.ConceptNode:
                    if target.iri and (
                            target.iri.isOwlThing() or target.iri.isTopObjectProperty() or target.iri.isTopDataProperty()):
                        raise ProfileError('Use of inclusion axioms involving a TOP predicate is forbidden in OWL 2 RL')
                # Enumeration nodes cannot be target of concept inclusion in OWL 2 RL.
                elif target.type() is Item.EnumerationNode:
                    raise ProfileError('Inclusion with an enumeration of individuals as target is forbidden in OWL 2 RL')
                # Union of concept expressions cannot be target of concept inclusion in OWL 2 RL.
                elif target.type() is Item.EnumerationNode:
                    raise ProfileError('Inclusion with a union of concept expressions as target is forbidden in OWL 2 RL')
                # Existential domain/range restriction and cardinality check.
                elif target.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                    if target.restriction() is Restriction.Exists:
                        # We need to check for the restriction to have a an Enumeration as filler.
                        f1 = lambda x: x.type() is Item.InputEdge
                        f2 = lambda x: x.type() is Item.EnumerationNode
                        if not target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                            raise ProfileError('Existential {} must specify an Enumeration as filler when acting as '
                                               'target for a concept expression inclusion in OWL 2 RL'.format(target.shortName))
                    elif target.restriction() is Restriction.Cardinality:
                        if target.cardinality('max') not in (0, 1):
                            raise ProfileError('Cardinality {} must specify a max cardinality of 0 or 1 when acting as '
                                               'target for a concept expression inclusion in OWL 2 RL'.format(target.shortName))


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
                    raise ProfileError('Union of of value-domain expressions is forbidden in OWL 2 RL')
