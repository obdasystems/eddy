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


from eddy.core.datatypes.graphol import Identity, Item, Restriction
from eddy.core.functions.graph import bfs
from eddy.core.functions.misc import first
from eddy.core.owl import OWL2Facet
from eddy.core.profiles.common import ProfileError
from eddy.core.profiles.rules.common import ProfileEdgeRule
from eddy.core.profiles.rules.common import ProfileNodeRule


class EquivalenceBetweenExpressionsRule(ProfileEdgeRule):
    """
    Make sure that an equivalence edge is traced only between graphol expressions.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.EquivalenceEdge:
            supported = {Identity.Concept, Identity.Role, Identity.Attribute, Identity.ValueDomain}
            shared = source.identities() & target.identities() - {Identity.Neutral, Identity.Unknown}
            if shared:
                raiseError = True
                for sharedId in shared:
                    if sharedId in supported or (
                        sharedId is Identity.Individual and len(source.identities()) > 1 and len(
                        target.identities()) > 1):
                        raiseError = False
                        break
                # if shared - supported:
                if raiseError:
                    raise ProfileError('Type mismatch: equivalence must involve two graphol expressions')


class EquivalenceBetweenCompatibleExpressionsRule(ProfileEdgeRule):
    """
    Make sure that an equivalence edge is traced only between compatible Graphol expressions.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.EquivalenceEdge:

            if Identity.Neutral not in {source.identity(),
                                        target.identity()} and source.identity() is not target.identity():
                # If both nodes are not NEUTRAL and they have a different identity we can't create an equivalence.
                raise ProfileError(
                    'Type mismatch: equivalence between {} and {}'.format(source.identityName, target.identityName))

            if not source.identities() & target.identities() - {Identity.Neutral, Identity.Unknown}:
                # If source and target nodes do not share a common identity then we can't create an equivalence.
                raise ProfileError('Type mismatch: {} and {} are not compatible'.format(source.name, target.name))


class EquivalenceBetweenValueDomainExpressionsRule(ProfileEdgeRule):
    """
    Prevents equivalence edges from being traced between Value-domain expressions.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.EquivalenceEdge:
            if Identity.ValueDomain in {source.identity(), target.identity()}:
                # Equivalence between value-domain expressions is not yet supported.
                raise ProfileError('Type mismatch: equivalence between value-domain expressions')


class EquivalenceBetweenRoleExpressionAndComplementRule(ProfileEdgeRule):
    """
    Prevents equivalence edges from being traced between a Role expression and a Complement node.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.EquivalenceEdge:
            if Identity.Role in {source.identity(), target.identity()}:
                if Item.ComplementNode in {source.type(), target.type()}:
                    # Equivalence edges cannot be attached to complement nodes with a Role as input.
                    raise ProfileError('Equivalence is forbidden when expressing Role disjointness')


class EquivalenceBetweenAttributeExpressionAndComplementRule(ProfileEdgeRule):
    """
    Prevents equivalence edges from being traced between an Attribute expression and a Complement node.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.EquivalenceEdge:
            if Identity.Attribute in {source.identity(), target.identity()}:
                if Item.ComplementNode in {source.type(), target.type()}:
                    # Equivalence edges cannot be attached to complement nodes with an Attribute as input.
                    raise ProfileError('Equivalence is forbidden when expressing Attribute disjointness')


class EquivalenceBetweenRoleExpressionAndRoleChainRule(ProfileEdgeRule):
    """
    Make sure that equivalence edges are never traced in presence of a Role chain node.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.EquivalenceEdge:
            if Item.RoleChainNode in {source.type(), target.type()}:
                # When connecting a Role chain node, the equivalence edge cannot be
                # used since it's not possible to target the Role chain node with an
                # inclusion edge, and the Equivalence edge express such an inclusion.
                raise ProfileError('Equivalence is forbidden in presence of a role chain node')


class InclusionBetweenExpressionsRule(ProfileEdgeRule):
    """
    Make sure that an inclusion edge is traced only between graphol expressions.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.InclusionEdge:
            supported = {Identity.Concept, Identity.Role, Identity.Attribute, Identity.ValueDomain}
            shared = source.identities() & target.identities() - {Identity.Neutral, Identity.Unknown}
            if shared:
                raiseError = True
                for sharedId in shared:
                    if sharedId in supported or (
                        sharedId is Identity.Individual and len(source.identities()) > 1 and len(
                        target.identities()) > 1):
                        raiseError = False
                        break
                # if shared - supported:
                if raiseError:
                    # Here we keep the ValueDomain as supported identity even though we deny the inclusion
                    # between value-domain expressions, unless we are creating a DataPropertyRange axiom.
                    # The reason for this is that if we remove the identity from the supported set the user
                    # will see the message which explains that the inclusion is denied because it does not
                    # involve two graphol expressions, while it actually does. We handle this special case
                    # in a separate rule which will highlight the error with a more specific message.
                    raise ProfileError('Type mismatch: inclusion must involve two graphol expressions')


class InclusionBetweenCompatibleExpressionsRule(ProfileEdgeRule):
    """
    Make sure that an inclusion edge is traced only between compatible Graphol expressions.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InclusionEdge:

            if Identity.Neutral not in {source.identity(),
                                        target.identity()} and source.identity() is not target.identity():
                # If both nodes are not NEUTRAL and they have a different identity we can't create an inclusion.
                idA = source.identityName
                idB = target.identityName
                raise ProfileError('Type mismatch: inclusion between {} and {}'.format(idA, idB))

            if not source.identities() & target.identities() - {Identity.Neutral, Identity.Unknown}:
                # If source and target nodes do not share a common identity then we can't create an inclusion.
                raise ProfileError('Type mismatch: {} and {} are not compatible'.format(source.name, target.name))


class InclusionBetweenValueDomainExpressionsRule(ProfileEdgeRule):
    """
    Prevents inclusion edged from being traced between Value-domain expressions.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.InclusionEdge:
            if Identity.ValueDomain in {source.identity(), target.identity()}:
                if source.type() is not Item.RangeRestrictionNode or target.type() is Item.RangeRestrictionNode:
                    # Inclusion between value-domain expressions is not supported. However, we
                    # allow inclusions between value-domain expressions only if we are tracing
                    # an inclusion edge sourcing from a range restriction node (whose input is an
                    # attribute node, and therefore its identity is set to value-domain) and targeting
                    # a value-domain expression, either complex or atomic, eventually excluding the
                    # attribute range restriction as target.
                    raise ProfileError('Type mismatch: inclusion between value-domain expressions')


class InclusionBetweenRoleExpressionAndComplementNodeRule(ProfileEdgeRule):
    """
    Prevents inclusion edges sourcing from Complement nodes to target Role expressions.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InclusionEdge:

            if Identity.Role in {source.identity(), target.identity()}:

                if source.type() is Item.ComplementNode:
                    # Complement nodes can only be the target of Role inclusions
                    # since they generate the OWLDisjointObjectProperties axiom.
                    raise ProfileError('Invalid source for Role inclusion: {}'.format(source.name))

                if target.identity() is Identity.Neutral:

                    if target.type() is Item.ComplementNode:

                        if target.adjacentNodes(filter_on_edges=lambda x: x is not edge):
                            # Here we target a Complement node which is still Neutral, but it may be connected
                            # to many other Neutral nodes (operators), therefore we must inspect all the nodes
                            # attached to this target node and see if they admits the Role identity.
                            f1 = lambda x: x is not edge and x.type() is not Item.MembershipEdge
                            f2 = lambda x: x.identity() is Identity.Neutral
                            for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                                if Identity.Role not in node.identities():
                                    raise ProfileError('Detected unsupported operator sequence on {}'.format(node.name))


class InclusionBetweenAttributeExpressionAndComplementNodeRule(ProfileEdgeRule):
    """
    Prevents inclusion edges sourcing from Complement nodes to target Attribute expressions.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InclusionEdge:

            if Identity.Attribute in {source.identity(), target.identity()}:

                if source.type() is Item.ComplementNode:
                    # Complement nodes can only be the target of Attribute inclusions
                    # since they generate the OWLDisjointDataProperties axiom.
                    raise ProfileError('Invalid source for Attribute inclusion: {}'.format(source.name))

                if target.identity() is Identity.Neutral:

                    if target.type() is Item.ComplementNode:

                        if target.adjacentNodes(filter_on_edges=lambda x: x is not edge):
                            # Here we target a Complement node which is still Neutral, but it may be connected
                            # to many other Neutral nodes (operators), therefore we must inspect all the nodes
                            # attached to this target node and see if they admits the Attribute identity.
                            f1 = lambda x: x is not edge and x.type() is not Item.MembershipEdge
                            f2 = lambda x: x.identity() is Identity.Neutral
                            for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                                if Identity.Attribute not in node.identities():
                                    raise ProfileError('Detected unsupported operator sequence on {}'.format(node.name))


class InclusionBetweenRoleExpressionAndRoleChainNodeRule(ProfileEdgeRule):
    """
    Make sure that inclusion edges sourcing from Role chain nodes target only Role expressions.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InclusionEdge:

            if source.type() is Item.RoleChainNode:

                if target.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                    # Role expressions constructed with chain nodes can be included only
                    # in basic role expressions, that are either Role nodes or RoleInverse
                    # nodes with one input Role node (this check is done elsewhere).
                    raise ProfileError('Inclusion between {} and {} is forbidden'.format(source.name, target.name))

            if target.type() is Item.RoleChainNode:
                # Role expressions constructed with chain nodes cannot be the target of any inclusion edge.
                raise ProfileError('Role chain nodes cannot be target of a Role inclusion')


class InputToConstructorNodeRule(ProfileEdgeRule):
    """
    Make sure that input edges only target constructor nodes.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.InputEdge:
            if not target.isConstructor():
                # Input edges MUST target constructor nodes only.
                raise ProfileError('Input edges can only target constructor nodes')
            if source.type() is Item.PropertyAssertionNode:
                # Property assertion node cannot be given in input to anything.
                raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))


class InputToComplementNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting Complement nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() is Item.ComplementNode:

                if source.identity() not in target.identities():
                    # Source node identity is not supported by the target node.
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.identityName))

                if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) > 0:
                    # The Complement operator may have at most one node connected to it.
                    raise ProfileError('Too many inputs to {}'.format(target.name))

                if source.type() in {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}:
                    # If the source of the node matches an ObjectPropertyExpression or a
                    # DataPropertyExpression, we check for the node not to have any outgoing
                    # Input edge: the only supported expression are NegativeObjectPropertyAssertion
                    # and NegativeDataPropertyAssertion. This prevents the connection of Role
                    # expressions to Complement nodes that are given as inputs to Enumeration,
                    # Union and Disjoint Union operator nodes.
                    if len(target.outgoingNodes(lambda x: x.type() in {Item.InputEdge, Item.InclusionEdge})) > 0:
                        raise ProfileError('Invalid negative {} expression'.format(source.identityName))

                if source.identity() is Identity.ValueDomain and target.identity() is Identity.Neutral:
                    # We are here connecting a Value-Domain expression in input to a complement node
                    # whose identity is still NEUTRAL, hence it may be an isolated node or a chain of
                    # neutral nodes connected using input edges. We deny the connection if one of
                    # these nodes has an outgoing or incoming inclusion edge because we would then be
                    # constructing an inclusion between value-domain expressions which is not permitted.
                    # Although, we allow the connection if we only have an inclusion targeting one of
                    # the nodes in this chain, whose souce node is a range restriction node, in which
                    # case our chain will assume the value-domain identity and will then generate a
                    # DataPropertyRange axiom.
                    f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                    f2 = lambda x: x.identity() is Identity.Neutral
                    f3 = lambda x: x.type() is Item.InclusionEdge
                    f4 = lambda x: x.type() is Item.InclusionEdge and x.source.type() is not Item.RangeRestrictionNode
                    for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                        if node.outgoingNodes(filter_on_edges=f3) or node.incomingNodes(filter_on_edges=f4):
                            raise ProfileError('Type mismatch: inclusion between value-domain expressions')


class InputToIntersectionOrUnionNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting either Intersection or (Disjoint)Union nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() in {Item.IntersectionNode, Item.UnionNode, Item.DisjointUnionNode}:

                if source.identity() not in target.identities():
                    # Source node identity is not supported by the target node.
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.identityName))

                if Identity.Neutral not in {source.identity(), target.identity()}:
                    if source.identity() is not target.identity():
                        # Union/Intersection between different type of graphol expressions.
                        idA = source.identityName
                        idB = target.identityName
                        raise ProfileError('Type mismatch: {} between {} and {}'.format(target.shortName, idA, idB))

                if Identity.ValueDomain in {source.identity(), target.identity()}:

                    if source.type() is Item.RangeRestrictionNode:
                        # Deny the connection of Attribute range with Union|Intersection nodes: even
                        # though the identity matches the Attribute range restriction node is used only to
                        # express a DataPropertyRange axiom and we can't give it in input to an AND|OR node.
                        raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                if source.identity() is Identity.ValueDomain and target.identity() is Identity.Neutral:
                    # We are here connecting a Value-Domain expression in input to an intersection/union
                    # node whose identity is still NEUTRAL, hence it may be an isolated node or a chain
                    # of neutral nodes connected using input edges. We deny the connection if one of
                    # these nodes has an outgoing or incoming inclusion edge because we would then be
                    # constructing an inclusion between value-domain expressions which is not permitted.
                    # Although, we allow the connection if we only have an inclusion targeting one of
                    # the nodes in this chain, whose souce node is a range restriction node, in which
                    # case our chain will assume the value-domain identity and will then generate a
                    # DataPropertyRange axiom.
                    f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                    f2 = lambda x: x.identity() is Identity.Neutral
                    f3 = lambda x: x.type() is Item.InclusionEdge
                    f4 = lambda x: x.type() is Item.InclusionEdge and x.source.type() is not Item.RangeRestrictionNode
                    for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                        if node.outgoingNodes(filter_on_edges=f3) or node.incomingNodes(filter_on_edges=f4):
                            raise ProfileError('Type mismatch: inclusion between value-domain expressions')


class InputToEnumerationNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting Enumeration nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() is Item.EnumerationNode:

                if not (source.type() is Item.IndividualNode or source.type() is Item.LiteralNode or Identity.Individual in source.identities()):
                    # Enumeration operator (oneOf) takes as inputs Individuals or Values, both
                    # represented by the Individual node, and has the job of composing a set
                    # if individuals (either Concept or ValueDomain, but not both together).
                    name = source.identityName if source.identity() is not Identity.Neutral else source.name
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, name))

                if target.identity() is not Identity.Neutral:
                    # Exclude incompatible identities from being given in input to the Enumeration node.
                    if Identity.Individual in source.identities() and target.identity() is Identity.ValueDomain:
                        raise ProfileError('Invalid input to {}: {}'.format(target.name, source.identityName))
                    if source.identity() is Identity.Value and target.identity() is Identity.Concept:
                        raise ProfileError('Invalid input to {}: {}'.format(target.name, source.identityName))

                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
                f3 = lambda x: x.type() is Item.InputEdge and x is not edge
                node = first(target.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                if node:
                    # If this Enumeration node is acting as filler for a domain/range restriction
                    # we need to check for the Enumeration node to have at most one input.
                    if len(target.incomingNodes(filter_on_edges=f3)) > 0:
                        raise ProfileError(
                            'Enumeration acting as filler for qualified {} can have at most one input'.format(
                                node.shortName))


class InputToRoleInverseNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting Role Inverse nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() is Item.RoleInverseNode:

                if source.type() is not Item.RoleNode:
                    # The Role Inverse operator takes as input a Role (ObjectProperty) and constructs its inverse
                    # by switching domain and range of the role. Assume to have a Role labelled 'is_owner_of' whose
                    # instances are {(o1,o2), (o1,o3), (o4,o5)}: connecting this Role in input to a Role Inverse
                    # node will construct a new Role whose instances are {(o2,o1), (o3,o1), (o5,o4)}.
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) > 0:
                    # The Role Inverse operator may have at most one Role node connected to it: if we need to
                    # define multiple Role inverse we would need to use multiple Role Inverse operator nodes.
                    raise ProfileError('Too many inputs to {}'.format(target.name))


class InputToRoleChainNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting Role Chain nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() is Item.RoleChainNode:

                if source.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                    # The Role Chain operator constructs a concatenation of roles. Assume to have 2 Role nodes
                    # defined as 'lives_in_region' and 'region_in_country': if {(o1, o2), (o3, o4)} is the
                    # instance of 'lives_in_region' and {(o2, o6)} is the instance of 'region_in_country', then
                    # {(o1, o6)} is the instance of the chain, which would match another Role 'lives_in_country'.
                    # ObjectPropertyExpression := ObjectProperty | InverseObjectProperty => we need to match only
                    # Role nodes and Role Inverse nodes as sources of our edge (it's not possible to create a chain
                    # of chains, despite the identity matches Role in both expressions).
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))


class InputToDatatypeRestrictionNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting Role Chain nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() is Item.DatatypeRestrictionNode:

                if source.type() not in {Item.ValueDomainNode, Item.FacetNode}:
                    # The DatatypeRestriction node is used to compose complex datatypes and
                    # accepts as inputs one value-domain node and n >= 1 facet
                    # nodes to compose the OWL 2 equivalent DatatypeRestriction.
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                if source.type() is Item.ValueDomainNode:

                    f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                    f2 = lambda x: x.type() is Item.ValueDomainNode
                    if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                        # The value-domain has already been attached to the DatatypeRestriction.
                        raise ProfileError('Too many value-domain nodes in input to datatype restriction node')

                    # Check if a Facet node is already connected to this node: if
                    # so we need to check whether the datatype in input and the
                    # already connected Facet are compatible.
                    f1 = lambda x: x.type() is Item.InputEdge
                    f2 = lambda x: x.type() is Item.FacetNode
                    node = first(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                    if node:
                        if node.facet.constrainingFacet not in OWL2Facet.forDatatype(source.datatype):
                            nA = source.datatype
                            nB = node.facet.constrainingFacet
                            raise ProfileError(
                                'Type mismatch: datatype {} is not compatible by facet {}'.format(nA, nB))

                if source.type() is Item.FacetNode:

                    # We need to check if the DatatypeRestriction node has already datatype
                    # connected: if that's the case we need to check whether the Facet we
                    # want to attach to the datatype restriction node supports it.
                    f1 = lambda x: x.type() is Item.InputEdge
                    f2 = lambda x: x.type() is Item.ValueDomainNode
                    node = first(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                    if node:
                        if source.facet.constrainingFacet not in OWL2Facet.forDatatype(node.datatype):
                            nA = source.facet.constrainingFacet
                            nB = node.datatype
                            raise ProfileError(
                                'Type mismatch: facet {} is not compatible by datatype {}'.format(nA, nB))


class InputToPropertyAssertionNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting Property Assertion nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() is Item.PropertyAssertionNode:

                if not (Identity.Individual in source.identities() or Identity.Value in source.identities()):
                    # Property Assertion operators accepts only Individual and Literal nodes as input: they are
                    # used to construct ObjectPropertyAssertion and DataPropertyAssertion axioms.
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                if source.identity() is Identity.Value:
                    # Individuals representing values can only be connected as
                    # the second component of any PropertyAssertionNode.
                    if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) != 1:
                        raise ProfileError('Value cannot be used as the first component of a property assertion')

                if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 2:
                    # At most 2 Individual nodes can be connected to a PropertyAssertion node. As an example
                    # we can construct ObjectPropertyAssertion(presiede M.Draghi BCE) where the individuals
                    # are identified by M.Draghi and BCE, or DataPropertyAssertion(nome M.Draghi "Mario") where
                    # the individuals are identified by M.Draghi and "Mario".
                    raise ProfileError('Too many inputs to {}'.format(target.name))

                if target.identity() is Identity.RoleInstance:

                    if source.identity() is Identity.Value:
                        # We are constructing an ObjectPropertyAssertion expression so we can't connect a Value.
                        raise ProfileError('Invalid input to {}: {}'.format(target.identityName, source.identityName))

                if target.identity() is Identity.AttributeInstance:

                    if source.identity() is Identity.Individual:

                        f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                        f2 = lambda x: x.identity() is Identity.Individual
                        if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                            # We are constructing a DataPropertyAssertion and so we can't have more than 1 instance.
                            raise ProfileError('Too many individuals in input to {}'.format(target.identityName))

                    if source.identity() is Identity.Value:

                        f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                        f2 = lambda x: x.identity() is Identity.Value
                        if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                            # At most one value can be given as input (2 instance | 1 instance + 1 value)
                            raise ProfileError('Too many values in input to {}'.format(target.identityName))

class InputToHasKeyNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting HasKey nodes.
    """
    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() is Item.HasKeyNode:

                if not (Identity.Concept in source.identities() or Identity.Role in source.identities() or Identity.Attribute in source.identities()):
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                if source.identity() is Identity.Concept:
                    if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge and Identity.Concept in x.source.identities())) != 0:
                        raise ProfileError('A key can be defined over one and only one class expression')
                    else:
                        return
                elif source.identity() is Identity.Role or source.identity() is Identity.Attribute:
                    if source.identity() is Identity.Role:
                        if not (source.type() is Item.RoleNode or source.type() is Item.RoleInverseNode):
                            raise ProfileError('Only object (resp. data) property expressions can be used to define a key over a class expression')
                    if source.identity() is Identity.Attribute:
                        if not (source.type() is Item.AttributeNode ):
                            raise ProfileError('Only object (resp. data) property expressions can be used to define a key over a class expression')
                else:
                    raise ProfileError(
                        'Only object (resp. data) property expressions can be used to define a key over a class expression')




class InputToDomainRestrictionNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting Domain Restriction nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() is Item.DomainRestrictionNode:

                if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 2:
                    # Domain Restriction node can have at most 2 inputs.
                    raise ProfileError('Too many inputs to {}'.format(target.name))

                supported = {Identity.Concept, Identity.Attribute, Identity.Role, Identity.ValueDomain,
                             Identity.Neutral}
                if source.identity() not in supported:
                    # Domain Restriction node takes as input:
                    #  - Role => OWL 2 ObjectPropertyExpression
                    #  - Attribute => OWL 2 DataPropertyExpression
                    #  - Concept => Qualified Existential/Universal Role Restriction
                    #  - ValueDomain => Qualified Existential Data Restriction
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.identityName))

                if source.type() is Item.RoleChainNode:
                    # Exclude incompatible sources: note that while RoleChain has a correct identity
                    # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                # SOURCE => NEUTRAL

                if source.identity() is Identity.Neutral:

                    if not source.identities() & {Identity.Concept, Identity.Attribute, Identity.Role,
                                                  Identity.ValueDomain}:
                        # We can connect a Neutral node in input only if the source node admits a supported
                        # identity among the declared ones: Concept || Attribute || Role || ValueDomain.
                        raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                    node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                    if node:
                        if node.identity() is Identity.Role and Identity.Concept not in source.identities():
                            # If the target node has a Role in input, we can connect the source
                            # node iff it admits the Concept identity among the declared ones.
                            raise ProfileError(
                                'Unsupported input for qualified {}: {}'.format(target.shortName, source.name))
                        if node.identity() is Identity.Concept and Identity.Role not in source.identities():
                            # If the target node has a Concept in input, we can connect the source
                            # node iff it admits the Role identity among the declared ones.
                            raise ProfileError(
                                'Unsupported input for qualified {}: {}'.format(target.shortName, source.name))
                        if node.identity() is Identity.Attribute and Identity.ValueDomain not in source.identities():
                            # If the target node has a Attribute in input, we can connect the source
                            # node iff it admits the ValueDomain identity among the declared ones.
                            raise ProfileError(
                                'Unsupported input for qualified {}: {}'.format(target.shortName, source.name))
                        if node.identity() is Identity.ValueDomain and Identity.Attribute not in source.identities():
                            # If the target node has a Attribute in input, we can connect the source
                            # node iff it admits the ValueDomain identity among the declared ones.
                            raise ProfileError(
                                'Unsupported input for qualified {}: {}'.format(target.shortName, source.name))

                # SOURCE => CONCEPT EXPRESSION

                elif source.identity() is Identity.Concept:

                    if target.restriction() is Restriction.Self:
                        # Not a Qualified Restriction.
                        name = target.restriction().toString()
                        raise ProfileError(
                            'Invalid restriction type for qualified {}: {}'.format(target.shortName, name))

                    # A Concept can be given as input only if there is no input or if the other input is a Role.
                    node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                    if node and node.identity() is not Identity.Role:
                        # Not a Qualified Restriction.
                        idA = source.identityName
                        idB = node.identityName
                        raise ProfileError('Invalid qualified {}: {} + {}'.format(target.shortName, idA, idB))

                    # If we have an Enumeration of individuals as input, we need to check for such a
                    # node to have only one individual as input. This is the graphol syntax to express
                    # a ObjectSomeValuesFrom(ObjectPropertyExpression ObjectOneOf(A)) which is the extended
                    # version of ObjectHasValue(ObjectPropertyExpression A), where A is an individual.
                    if source.type() is Item.EnumerationNode:
                        if len(source.incomingNodes(lambda x: x.type() is Item.InputEdge)) > 1:
                            raise ProfileError(
                                'Enumeration acting as filler for qualified {} can have at most one input'.format(
                                    target.shortName))

                # SOURCE => ROLE EXPRESSION

                elif source.identity() is Identity.Role:

                    # We can connect a Role only if there is no other input or if the other input is a Concept.
                    node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                    if node and node.identity() is not Identity.Concept:
                        # Not a Qualified Restriction.
                        idA = source.identityName
                        idB = node.identityName
                        raise ProfileError('Invalid qualified {}: {} + {}'.format(target.shortName, idA, idB))

                # SOURCE => ATTRIBUTE

                elif source.identity() is Identity.Attribute:

                    if target.restriction() is Restriction.Self:
                        # Attributes don't have self.
                        raise ProfileError('Attributes do not have self')

                    # We can connect an Attribute only if there is no other input or if the other input is a ValueDomain.
                    node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                    if node and node.identity() is not Identity.ValueDomain:
                        # Not a Qualified Restriction.
                        idA = source.identityName
                        idB = node.identityName
                        raise ProfileError('Invalid qualified {}: {} + {}'.format(target.shortName, idA, idB))

                # SOURCE => VALUE-DOMAIN

                elif source.identity() is Identity.ValueDomain:

                    if target.restriction() is Restriction.Self:
                        # Not a Qualified Restriction.
                        name = target.restriction().toString()
                        raise ProfileError(
                            'Invalid restriction type for qualified {}: {}'.format(target.shortName, name))

                    # We can connect a ValueDomain only if there is no other input or if the other input is an Attribute.
                    node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                    if node and node.identity() is not Identity.Attribute:
                        # Not a Qualified Restriction.
                        idA = source.identityName
                        idB = node.identityName
                        raise ProfileError('Invalid qualified {}: {} + {}'.format(target.shortName, idA, idB))


class InputToRangeRestrictionNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting Range Restriction nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.InputEdge:

            if target.type() is Item.RangeRestrictionNode:

                if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 2:
                    # Range Restriction node can have at most 2 inputs.
                    raise ProfileError('Too many inputs to {}'.format(target.name))

                f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                f2 = lambda x: x.type() is Item.AttributeNode
                if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) >= 1:
                    # Range restriction node having an attribute as input can receive no other input.
                    raise ProfileError('Too many inputs to attribute {}'.format(target.shortName))

                if source.identity() not in {Identity.Concept, Identity.Attribute, Identity.Role, Identity.Neutral}:
                    # Range Restriction node takes as input:
                    #  - Role => OWL 2 ObjectPropertyExpression
                    #  - Attribute => OWL 2 DataPropertyExpression
                    #  - Concept => Qualified Existential/Universal Role Restriction
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.identityName))

                if source.type() is Item.RoleChainNode:
                    # Exclude incompatible sources: not that while RoleChain has a correct identity
                    # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                    raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                # SOURCE => NEUTRAL

                if source.identity() is Identity.Neutral:

                    if not source.identities() & {Identity.Concept, Identity.Attribute, Identity.Role}:
                        # We can connect a Neutral node in input only if the source node admits a
                        # supported identity among the declared ones: Concept || Attribute || Role.
                        raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                    node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                    if node:
                        if node.identity() is Identity.Role and Identity.Concept not in source.identities():
                            # If the target node has a Role in input, we can connect the source
                            # node iff it admits the Concept identity among the declared ones.
                            raise ProfileError(
                                'Unsupported input for qualified {}: {}'.format(target.shortName, source.name))
                        if node.identity() is Identity.Concept and Identity.Role not in source.identities():
                            # If the target node has a Concept in input, we can connect the source
                            # node iff it admits the Role identity among the declared ones.
                            raise ProfileError(
                                'Unsupported input for qualified {}: {}'.format(target.shortName, source.name))

                # SOURCE => CONCEPT EXPRESSION

                elif source.identity() is Identity.Concept:

                    # We can connect a Concept in input only if the identity is either Neutral or Concept:
                    if target.identity() not in {Identity.Neutral, Identity.Concept}:
                        # Must be a Value-Domain, so we cannot add a Concept to obtain a Qualified Restriction.
                        raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                    # We can connect a Concept in input iff there is no other input or if the other
                    # input is either a Role or a Neutral node that can assume the Role identity.
                    node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                    if node and Identity.Role not in node.identities():
                        # Not a Qualified Restriction.
                        idA = source.identityName
                        idB = node.identityName
                        raise ProfileError('Invalid qualified {}: {} + {}'.format(target.shortName, idA, idB))

                    # If we have an Enumeration of individuals as input, we need to check for such a
                    # node to have only one individual as input. This is the graphol syntax to express
                    # a ObjectSomeValuesFrom(ObjectPropertyExpression ObjectOneOf(A)) which is the extended
                    # version of ObjectHasValue(ObjectPropertyExpression A), where A is an individual.
                    if source.type() is Item.EnumerationNode:
                        if len(source.incomingNodes(lambda x: x.type() is Item.InputEdge)) > 1:
                            raise ProfileError(
                                'Enumeration acting as filler for qualified {} can have at most one input'.format(
                                    target.shortName))

                # SOURCE => ROLE EXPRESSION

                elif source.identity() is Identity.Role:

                    # We can connect a Role in input only if the identity is either Neutral or Concept:
                    if target.identity() not in {Identity.Neutral, Identity.Concept}:
                        # Must be a Value-Domain, so we cannot create the connection with the Role.
                        raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                    # We can connect a Role in input only if there is no other input or if the other
                    # input is either a Concept or a Neutral node that can assume the Concept identity.
                    node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                    if node and Identity.Concept not in node.identities():
                        # Not a Qualified Restriction.
                        idA = source.identityName
                        idB = node.identityName
                        raise ProfileError('Invalid qualified {}: {} + {}'.format(target.shortName, idA, idB))

                # SOURCE => ATTRIBUTE NODE

                elif source.identity() is Identity.Attribute:

                    if target.restriction() is Restriction.Self:
                        # Attributes don't have self.
                        raise ProfileError('Attributes do not have self')

                    # We can connect an Attribute in input only if the identity is either Neutral or Value-Domain:
                    if target.identity() not in {Identity.Neutral, Identity.ValueDomain}:
                        # Must be a concept, so we cannot create the connection with the Attribute.
                        raise ProfileError('Invalid input to {}: {}'.format(target.name, source.name))

                    # We can connect an Attribute in input only if there is no other input.
                    if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 1:
                        # Something else is connected to this range restriction node (either a Concept
                        # or a Role) so we cannot attach the Attribute node (no DataPropertyRange).
                        raise ProfileError('Too many inputs to attribute {}'.format(target.shortName))


class InputToFacetNodeRule(ProfileEdgeRule):
    """
    Perform validation procedures on input edges targeting Facet nodes.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.InputEdge:
            if target.type() is Item.FacetNode:
                raise ProfileError('Facet node cannot be target of any input')


class MembershipFromAssertionCompatibleNodeRule(ProfileEdgeRule):
    """
    Make sure that membership assertion edges source from either Individual or Property Assertion nodes.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.MembershipEdge:
            # if source.identity() is not Identity.Individual and source.type() is not Item.PropertyAssertionNode:
            if Identity.Individual not in source.identities() and source.type() is not Item.PropertyAssertionNode:
                # The source of the edge must be either an Individual or a Property Assertion node.
                raise ProfileError('Invalid source for membership edge: {}'.format(source.identityName))


class MembershipFromIndividualRule(ProfileEdgeRule):
    """
    Perform validation procedures on membership edges sourcing from Individuals.
    """

    def __call__(self, source, edge, target):
        if edge.type() is Item.MembershipEdge:
            if Identity.Individual in source.identities():
                if Identity.Concept not in target.identities():
                    # If the source of the edge is an Individual it means that we are trying to construct a
                    # ClassAssertion and so the target of the edge MUST be a class expression.
                    # OWL 2: ClassAssertion(axiomAnnotations ClassExpression Individual)
                    raise ProfileError('Invalid target for Concept assertion: {}'.format(target.identityName))


class MembershipFromRoleInstanceRule(ProfileEdgeRule):
    """
    Perform validation procedures on membership edges sourcing from a Role Instance.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.MembershipEdge:

            if source.identity() is Identity.RoleInstance:

                if target.identity() not in {Identity.Role, Identity.Neutral}:
                    # Role instance can only target a Role expression or a Neutral node which may turn into
                    # a Role (the only practical case is the Complement node).
                    raise ProfileError('Invalid target for Role assertion: {}'.format(target.identityName))

                # TARGET => ROLE

                if target.identity() is Identity.Role:

                    if target.type() is Item.RoleChainNode:
                        # Exclude Role chain nodes since they do no match OWL 2 ObjectPropertyExpression.
                        raise ProfileError('Invalid target for Role assertion: {}'.format(target.name))

                # TARGET => NEUTRAL

                if target.identity() is Identity.Neutral:

                    if Identity.Role not in target.identities():
                        # Here we target an incompatible node (i.e. a node which cannot express a Role).
                        raise ProfileError('Invalid target for Role assertion: {}'.format(target.name))

                    if target.adjacentNodes(filter_on_edges=lambda x: x is not edge):
                        # Here we target a Neutral node which is attached to something (either with
                        # inputs or outputs), therefore we must inspect all the nodes attached to this
                        # target node which are still Neutral and see if they admits the Role identity.
                        f1 = lambda x: x is not edge and x.type() is not Item.MembershipEdge
                        f2 = lambda x: x.identity() is Identity.Neutral
                        for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                            if Identity.Role not in node.identities():
                                raise ProfileError('Detected unsupported operator sequence on {}'.format(node.name))


class MembershipFromAttributeInstanceRule(ProfileEdgeRule):
    """
    Perform validation procedures on membership edges sourcing from an Attribute Instance.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.MembershipEdge:

            if source.identity() is Identity.AttributeInstance:

                if target.identity() not in {Identity.Attribute, Identity.Neutral}:
                    # Attribute instance can only target an Attribute expression or a Neutral node which may
                    # turn into an Attribute (the only practical case is the Complement node).
                    raise ProfileError('Invalid target for Attribute assertion: {}'.format(target.identityName))

                if target.identity() is Identity.Neutral:

                    if Identity.Attribute not in target.identities():
                        # Here we target an incompatible node (i.e. a node which cannot express an Attribute).
                        raise ProfileError('Invalid target for Attribute assertion: {}'.format(target.name))

                    if target.adjacentNodes(filter_on_edges=lambda x: x is not edge):
                        # Here we target a Neutral node which is attached to something (either with
                        # inputs or outputs), therefore we must inspect all the nodes attached to this
                        # target node which are still Neutral and see if they admits the Attribute identity.
                        f1 = lambda x: x is not edge and x.type() is not Item.MembershipEdge
                        f2 = lambda x: x.identity() is Identity.Neutral
                        for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                            if Identity.Attribute not in node.identities():
                                raise ProfileError('Detected unsupported operator sequence on {}'.format(node.name))


class MembershipFromNeutralPropertyAssertionRule(ProfileEdgeRule):
    """
    Perform validation procedures on membership edges sourcing from Neutral Property Assertion nodes.
    """

    def __call__(self, source, edge, target):

        if edge.type() is Item.MembershipEdge:

            if source.type() is Item.PropertyAssertionNode:

                if source.identity() is Identity.Neutral:

                    if target.identity() not in {Identity.Attribute, Identity.Role, Identity.Neutral}:
                        # PropertyAssertion nodes can only target Attributes, Roles or Neutral node
                        # which supports either Attribute or Role identity (i.e: the complement node).
                        raise ProfileError('Invalid target for property assertion node: {}'.format(target.name))

                    if target.type() is Item.RoleChainNode:
                        # Exclude Role chain nodes since since they can never be target of a membership assertion.
                        raise ProfileError('Invalid target for property assertion node: {}'.format(target.name))

                    if target.identity() is Identity.Neutral:

                        if not {Identity.Attribute, Identity.Role} & target.identities():
                            # Here we target an incompatible node (i.e. a node which cannot express an Attribute or a Role).
                            raise ProfileError('Invalid target for property assertion node: {}'.format(target.name))

                        if target.adjacentNodes(filter_on_edges=lambda x: x is not edge):
                            # Here we target a Neutral node which is attached to something (either with
                            # inputs or outputs), therefore we must inspect all the nodes attached to this
                            # target node which are still Neutral and see if they all share an identity among
                            # Role and Attribute.
                            f1 = lambda x: x is not edge and x.type() is not Item.MembershipEdge
                            f2 = lambda x: x.identity() is Identity.Neutral
                            for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                                if not {Identity.Attribute, Identity.Role} & node.identities():
                                    raise ProfileError('Detected unsupported operator sequence on {}'.format(node.name))


class SameFromCompatibleNodeRule(ProfileEdgeRule):
    """
    Permit same edges only for nodes of the same type. This also accounts for OWL 2 punning.
    """

    def __call__(self, source, edge, target):
        if edge.type() == Item.SameEdge:
            if source.type() not in {Item.IndividualNode, Item.ConceptNode, Item.RoleNode, Item.AttributeNode}:
                raise ProfileError('Invalid source for same assertion: {0}'.format(source.name))
            # if source.type() != target.type():
            if not source.identities().intersection(target.identities()):
                raise ProfileError('Invalid target for same assertion: {0}'.format(target.name))


class DifferentFromCompatibleNodeRule(ProfileEdgeRule):
    """
    Permit different edges only for nodes of the same type. This also accounts for OWL 2 punning.
    """

    def __call__(self, source, edge, target):
        if edge.type() == Item.DifferentEdge:
            if source.type() not in {Item.IndividualNode, Item.ConceptNode, Item.RoleNode, Item.AttributeNode}:
                raise ProfileError('Invalid source for different assertion: {0}'.format(source.name))
            #if source.type() != target.type():
            if not source.identities().intersection(target.identities()):
                raise ProfileError('Invalid target for different assertion: {0}'.format(target.name))


class SelfConnectionRule(ProfileEdgeRule):
    """
    Prevents from generating self connections.
    """

    def __call__(self, source, edge, target):
        if source is target:
            # We never allow self connection, no matter the edge type.
            raise ProfileError('Self connection detected on {}'.format(source))


class CardinalityRestrictionNodeRule(ProfileNodeRule):
    """
    Make sure that the cardinality specified is consistent.
    """

    def __call__(self, node):
        if node.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
            if node.restriction() is Restriction.Cardinality:
                minc = node.cardinality('min')
                maxc = node.cardinality('max')
                if minc is not None and minc < 0:
                    raise ProfileError('Negative minimum cardinality detected on {}'.format(node))
                if maxc is not None and maxc < 0:
                    raise ProfileError('Negative maximum cardinality detected on {}'.format(node))
                if minc is not None and maxc is not None and minc > maxc:
                    raise ProfileError('Invalid cardinality range ({},{}) detected on {}'.format(minc, maxc, node))


class UnknownIdentityNodeRule(ProfileNodeRule):
    """
    Make sure that the no node has an unknown identity.
    """

    def __call__(self, node):
        if node.identity() is Identity.Unknown:
            raise ProfileError('Unknown node identity detected on {}'.format(node))
