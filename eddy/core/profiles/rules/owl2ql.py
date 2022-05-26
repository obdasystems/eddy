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


from eddy.core.datatypes.graphol import Item, Identity, Special, Restriction
from eddy.core.functions.graph import bfs
from eddy.core.items.nodes.common.base import PredicateNodeMixin
from eddy.core.owl import OWL2Datatype, OWL2Profiles
from eddy.core.profiles.common import ProfileError
from eddy.core.profiles.rules.common import ProfileNodeRule
from eddy.core.profiles.rules.common import ProfileEdgeRule


class FunctionalityUnsupported(ProfileNodeRule):
    """
    Prevents from using functionality in attributes or roles which is outside of the OWL 2 QL profile.
    """
    def __call__(self, node):
        if isinstance(node, PredicateNodeMixin):
            if node.iri and node.iri.functional:
                raise ProfileError('({}) Functionality of roles and attributes is forbidden in OWL 2 QL'.format(str(node.iri)))


class InverseFunctionalityUnsupported(ProfileNodeRule):
    """
    Prevents from using inverse-functionality in roles which is outside of the OWL 2 QL profile.
    """
    def __call__(self, node):
        if isinstance(node, PredicateNodeMixin):
            if node.iri and node.iri.inverseFunctional:
                raise ProfileError('({}) Functionality of roles is forbidden in OWL 2 QL'.format(str(node.iri)))


#Ashwin
class TransitivityUnsupported(ProfileNodeRule):
    """
    Prevents from using transitivity in  roles which is outside of the OWL 2 QL profile.
    """
    def __call__(self, node):
        if isinstance(node, PredicateNodeMixin):
            if node.iri and node.iri.transitive:
                raise ProfileError('({}) Transitivity of roles is forbidden in OWL 2 QL'.format(str(node.iri)))


class UnsupportedDatatypeRule(ProfileNodeRule):
    """
    Prevents from using datatypes which are outside of the OWL 2 QL profile.
    """
    def __call__(self, node):
        if node.type() is Item.ValueDomainNode:
            if node.iri and not OWL2Datatype.forProfile(OWL2Profiles.OWL2RL):
                raise ProfileError('Use of datatype {} is forbidden in OWL 2 QL'.format(str(node.iri)))


class UnsupportedOperatorRule(ProfileNodeRule):
    """
    Prevents from using operator nodes which are not supported by the OWL 2 QL profile.
    """
    def __call__(self, node):
        if node.type() in {Item.UnionNode, Item.DisjointUnionNode,
            Item.DatatypeRestrictionNode, Item.FacetNode,
            Item.EnumerationNode, Item.RoleChainNode}:
            raise ProfileError('Usage of {} operator is forbidden in OWL 2 QL'.format(node.shortName))


class UnsupportedIndividualEqualityRule(ProfileEdgeRule):
    """
    Prevents from using individual equality assertion edges which are not supported by the OWL 2 QL profile.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.SameEdge:
            raise ProfileError('Usage of SameIndividual axiom is forbidden in OWL 2 QL')


class EquivalenceBetweenConceptExpressionRule(ProfileEdgeRule):
    """
    Make sure that equivalence edges are not from/to intersection or complement nodes.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.EquivalenceEdge:
            # Similarily as for the Inclusion edge, here we deny the equivalence in presence
            # of an intersection or a complement node, since it express a double inclusion and
            # we'll violate the constraint imposed by the rule here below.
            if not {Identity.Role, Identity.Attribute, Identity.Unknown} & {source.identity(), target.identity()}:
                for node in (source, target):
                    if node.type() is Item.IntersectionNode:
                        raise ProfileError('Equivalence in presence of concepts intersection is forbidden in OWL 2 QL')
                    if node.type() is Item.ComplementNode:
                        raise ProfileError('Equivalence in presence of concept complement is forbidden in OWL 2 QL')
                    if node.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                        if node.isRestrictionQualified():
                            raise ProfileError('Equivalence in presence of qualified {} is forbidden in OWL 2 QL'.format(node.shortName))
                        elif node.restriction() is not Restriction.Exists:
                            r = node.restriction()
                            raise ProfileError('Equivalence with a {} {} is forbidden in OWL 2 QL'.format(r.shortName, node.shortName))



class InclusionBetweenConceptExpressionRule(ProfileEdgeRule):
    """
    Make sure that inclusion edges do not source from intersection or complement nodes.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.InclusionEdge:
            # We need to prevent inclusions sourcing from Complement nodes and Intersection nodes.
            # Value-Domain inclusions are already forbidden by OWL 2 rules, and Attribute and Role
            # inclusions, with a complement node as enpoint, are already handled in an OWL 2 rule.
            # So here we just consider the case where we are connecting endpoints that either both
            # Neutral, or at least one of the 2 is identified as a Concept expression.
            if not {Identity.Role, Identity.Attribute, Identity.Unknown} & {source.identity(), target.identity()}:
                if source.type() is Item.IntersectionNode:
                    raise ProfileError('Inclusion with an intersection of concept expressions as source is forbidden in OWL 2 QL')
                if source.type() is Item.ComplementNode:
                    raise ProfileError('Inclusion with a concept complement as source is forbidden in OWL 2 QL')
                if source.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                    if source.isRestrictionQualified():
                        raise ProfileError('Inclusion with a qualified {} as source is forbidden in OWL 2 QL'.format(source.shortName))
                    elif source.restriction() is not Restriction.Exists:
                        r = source.restriction()
                        raise ProfileError('Inclusion with a {} {} as source is forbidden in OWL 2 QL'.format(r.shortName, source.shortName))


                if target.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                    if target.restriction() is not Restriction.Exists:
                        r = target.restriction()
                        raise ProfileError('Inclusion with a {} {} as target is forbidden in OWL 2 QL'.format(r.shortName, target.shortName))


class InputConceptToRestrictionNodeRule(ProfileEdgeRule):
    """
    Make sure to construct qualified Role domain/range restrictions using only atomic Concept nodes.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.InputEdge:
            if target.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
                # OWL 2 QL admits only atomic concepts for role qualified restriction.
                if source.identity() is Identity.Concept:
                    if source.type() is not Item.ConceptNode:
                        raise ProfileError('OWL 2 QL admits only an atomic concept as filler for a qualified {}'.format(target.shortName))
                    # Given the fact that we are connecting an atomic concept in input to this
                    # restriction node, we need to see if the node is currently being used
                    # as source for a concept expression inclusion, and if so, deny the connection
                    # because OWL 2 QL admits concept inclusion sourcing only from unqualified role
                    # restrictions (we need to skip TOP though, since it won't be qualified then).
                    if source.iri and not (source.iri.isOwlThing() or source.iri.isTopObjectProperty() or source.iri.isTopDataProperty()):
                        # We found an outgoing inclusion edge and our restriction filler is not TOP.
                        if target.outgoingNodes(filter_on_edges=lambda x: x.type() is Item.InclusionEdge):
                            raise ProfileError('Inclusion with a qualified {} as source is forbidden in OWL 2 QL'.format(target.shortName))
                        # Similarly we block the input in case of equivalence edges attached to the restriction node.
                        if target.adjacentNodes(filter_on_edges=lambda x: x.type() is Item.EquivalenceEdge):
                            raise ProfileError('Equivalence in presence of qualified {} is forbidden in OWL 2 QL'.format(target.shortName))


class InputValueDomainToComplementNodeRule(ProfileEdgeRule):
    """
    Prevent the construction of complement of value-domain expressions.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.InputEdge:
            if target.type() is Item.ComplementNode:
                if source.identity() is Identity.ValueDomain:
                    # We found a complement node with a value-domain expression in input so we must deny it.
                    raise ProfileError('Complement of a value-domain expression is forbidden in OWL 2 QL')


class InputValueDomainToIntersectionNodeRule(ProfileEdgeRule):
    """
    Prevent the construction of intersection of value-domains which are given in input to complement nodes.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.InputEdge:
            if target.type() is Item.IntersectionNode:
                if source.identity() is Identity.ValueDomain:
                    f1 = lambda x: x.type() in {Item.InputEdge, Item.InclusionEdge, Item.EquivalenceEdge}
                    f2 = lambda x: Identity.Neutral in x.identities()
                    for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                        if node.type() is Item.ComplementNode:
                            # We found a complement node along the path, so any input to this intersection node,
                            # would cause the complement node to identify itself as a value-domain, but in OWL 2 QL
                            # it is not possible to construct complement of value domain expressions.
                            raise ProfileError('Complement of a value-domain expression is forbidden in OWL 2 QL')


class MembershipFromAttributeInstanceToComplementNodeRule(ProfileEdgeRule):
    """
    Prevent the construction of NegativeDataPropertyAssertion axioms.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.MembershipEdge:
            if source.identity() is Identity.AttributeInstance:
                if target.type() is Item.ComplementNode:
                    raise ProfileError('Negative attribute assertion is forbidden in OWL 2 QL')


class MembershipFromRoleInstanceToComplementNodeRule(ProfileEdgeRule):
    """
    Prevent the construction of NegativeObjectPropertyAssertion axioms.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.MembershipEdge:
            if source.identity() is Identity.RoleInstance:
                if target.type() is Item.ComplementNode:
                    raise ProfileError('Negative role assertion is forbidden in OWL 2 QL')


class MembershipFromPropertyAssertionToComplementNodeRule(ProfileEdgeRule):
    """
    Prevent the construction of NegativeObjectPropertyAssertion and NegativeDataPropertyAssertion axioms.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.MembershipEdge:
            if source.type() is Item.PropertyAssertionNode:
                if source.identity() is Identity.Neutral:
                    if target.type() is Item.ComplementNode:
                        raise ProfileError('Negative attribute/role assertion is forbidden in OWL 2 QL')
