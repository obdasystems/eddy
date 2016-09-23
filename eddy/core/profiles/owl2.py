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


from eddy.core.datatypes.graphol import Identity, Item, Restriction
from eddy.core.datatypes.owl import Facet
from eddy.core.functions.graph import bfs
from eddy.core.functions.misc import first
from eddy.core.profiles.common import AbstractProfile
from eddy.core.profiles.common import ProfileValidationResult


class OWL2Profile(AbstractProfile):
    """
    Extends AbstractProfile implementing the OWL2 (full) profile.
    """
    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def name(cls):
        """
        Returns the name of the profile, i.e: OWL 2, OWL 2 QL.
        :rtype: str
        """
        return 'OWL 2'

    def validate(self, source, edge, target):
        """
        Perform the validation of the given triple and generate the ProfileValidationResult.
        :param source: AbstractNode
        :param edge: AbstractEdge
        :param target: AbstractNode
        """
        try:

            #############################################
            # EDGE = INCLUSION | EQUIVALENCE
            #################################

            if edge.type() in {Item.InclusionEdge, Item.EquivalenceEdge}:

                if source is target:
                    # Self connection is forbidden.
                    raise SyntaxError('Self connection is not valid')

                # Here we keep the ValueDomain as supported identity even though we deny the inclusion
                # between value-domain expressions, unless we are creating a DataPropertyRange axiom.
                # The reason for this is that if we remove the identity from the supported set the user
                # will see the message which explains that the inclusion is denied because it does not
                # involve two graphol expressions, while it actually does. We handle this special case
                # here below, bypassing the only allowed inclusion between value-domain expressions.
                supported = {Identity.Concept, Identity.Role, Identity.Attribute, Identity.ValueDomain}
                remaining = source.identities() & target.identities() - {Identity.Neutral, Identity.Unknown}

                if remaining - supported:
                    # Inclusion assertions can be specified only between graphol expressions: Concept
                    # expressions, Role expressions, Value-Domain expressions, Attribute expressions.
                    raise SyntaxError('Type mismatch: {0} must involve two graphol expressions'.format(edge.shortName))

                if Identity.Neutral not in {source.identity(), target.identity()} and source.identity() is not target.identity():
                    # If both nodes are not NEUTRAL and they have a different identity we can't create an inclusion.
                    idA = source.identity().value
                    idB = target.identity().value
                    raise SyntaxError('Type mismatch: {0} between {1} and {2}'.format(edge.shortName, idA, idB))

                if not remaining:
                    # If source and target nodes do not share a common identity then we can't create an inclusion.
                    raise SyntaxError('Type mismatch: {0} and {1} are not compatible'.format(source.name, target.name))

                if Identity.ValueDomain in {source.identity(), target.identity()}:

                    if source.type() is not Item.RangeRestrictionNode or target.type() is Item.RangeRestrictionNode:
                        # Inclusions between value-domain expressions is not yet supported. However,
                        # we allow inclusions between value-domain expressions only if we are tracing
                        # an inclusion edge sourcing from a range restriction node (whose input is an
                        # attribute node, and therefor its identity is set to value-domain) and targeting
                        # a value-domain expression, either complex or atomic, eventually excluding the
                        # attribute range restriction as target.
                        raise SyntaxError('Type mismatch: {0} between value-domain expressions'.format(edge.shortName))

                #############################################
                # INCLUSION WITH ROLE/ATTRIBUTE COMPLEMENT
                #################################

                if {Identity.Attribute, Identity.Role} & {source.identity(), target.identity()}:

                    if edge.type() is Item.InclusionEdge:

                        if source.type() is Item.ComplementNode:
                            # Complement nodes can only be the target of Role and Attribute inclusions since they
                            # are used to generate OWLDisjointObjectPropertiesAxiom and OWLDisjointDataPropertiesAxiom.
                            # Differently we allow inclusions targeting concept nodes to source from complement nodes.
                            identity = first({source.identity(), target.identity()} - {Identity.Neutral}).value.lower()
                            raise SyntaxError('Invalid source for {0} inclusion: {1}'.format(identity, source.name))

                    if edge.type() is Item.EquivalenceEdge:

                        if Item.ComplementNode in {source.type(), target.type()}:
                            # Equivalence edges cannot be attached to complement nodes with Attribute or Role as inputs.
                            identity = first({source.identity(), target.identity()} - {Identity.Neutral}).value.lower()
                            raise SyntaxError('Equivalence is forbidden when expressing {0} disjointness'.format(identity))

                #############################################
                # INCLUSION / EQUIVALENCE WITH ROLE CHAIN
                #################################

                if edge.type() is Item.EquivalenceEdge:
                    # When connecting a Role chain node, the equivalence edge cannot be used
                    # since it's not possible to target the Role chain node with an inclusion
                    # edge, and the Equivalence edge express such an inclusion.
                    raise SyntaxError('Equivalence is forbidden in presence of a role chain node')

                if edge.type() is Item.InclusionEdge:

                    if source.type() is Item.RoleChainNode:
                        # Role expressions constructed with chain nodes can be included only
                        # in basic role expressions, that are either Role nodes or RoleInverse
                        # nodes with one input Role node (this check is done elsewhere).
                        if target.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                            idA = source.name
                            idB = target.name
                            raise SyntaxError('Inclusion between {0} and {1} is forbidden'.format(idA, idB))

                    if target.type() is Item.RoleChainNode:
                        # Role expressions constructed with chain nodes cannot be the target of any inclusion edge.
                        raise SyntaxError('Role chain nodes cannot be target of a Role inclusion')

            #############################################
            # EDGE = INPUT
            #################################

            elif edge.type() is Item.InputEdge:

                if source is target:
                    # Self connection is forbidden.
                    raise SyntaxError('Self connection is not valid')

                if not target.isConstructor():
                    # Input edges can only target constructor nodes.
                    raise SyntaxError('Input edges can only target constructor nodes')

                if target.type() in {Item.ComplementNode, Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode}:

                    #############################################
                    # TARGET = COMPLEMENT | INTERSECTION | UNION
                    #################################

                    if source.identity() not in target.identities():
                        # Source node identity is not supported by this target node.
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.identity().value))

                    if source.identity() is Identity.ValueDomain and target.identity() is Identity.Neutral:
                        # We are here connecting a Value-Domain node in input to an operator node whose
                        # identity is still NEUTRAL, hence it may be an isolated node or a chain of
                        # neutral nodes connected using input edges. We deny the connection if one of
                        # these nodes has an outgoing or incoming inclusion edge because we would then be
                        # constructing an inclusion between value-domain expressions which is not permitted.
                        # Although, we allow the connection if we only have an inclusion targeting one of
                        # the nodes in this chain, whose souce node is a range restriction node, in which case
                        # our chain will assume the value-domain identity and will then generate a
                        # DataPropertyRange axiom.
                        f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                        f2 = lambda x: x.identity() is Identity.Neutral
                        f3 = lambda x: x.type() is Item.InclusionEdge
                        f4 = lambda x: x.type() is Item.InclusionEdge and x.source.type() is not Item.RangeRestrictionNode
                        for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                            if node.outgoingNodes(filter_on_edges=f3) or node.incomingNodes(filter_on_edges=f4):
                                raise SyntaxError('Type mismatch: inclusion between value-domain expressions')

                    #############################################
                    # TARGET = COMPLEMENT
                    #################################

                    if target.type() is Item.ComplementNode:

                        if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) > 0:
                            # The Complement operator may have at most one node connected to it.
                            raise SyntaxError('Too many inputs to {0}'.format(target.name))

                        if source.type() in {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}:
                            # See if the source of the node matches an ObjectPropertyExpression
                            # ({Role, RoleInv}) or a DataPropertyExpression (Attribute). If that's
                            # the case check for the node not to have any outgoing Input edge: the only
                            # supported expression are NegativeObjectPropertyAssertion (R1 ISA NOT R2) and
                            # NegativeDataPropertyAssertion (A1 ISA NOT A2). This prevents the connection of
                            # Role expressions to Complement nodes that are given as inputs to Enumeration,
                            # Union and Disjoint Union operator nodes.
                            if len(target.outgoingNodes(lambda x: x.type() in {Item.InputEdge, Item.InclusionEdge})) > 0:
                                raise SyntaxError('Invalid negative {0} expression'.format(source.identity().value))

                    else:

                        #############################################
                        # TARGET = UNION | INTERSECTION
                        #################################

                        if Identity.Neutral not in {source.identity(), target.identity()}:

                            if source.identity() is not target.identity():
                                # Union/Intersection between different type of graphol expressions.
                                idA = source.identity().value
                                idB = target.identity().value
                                cmp = target.shortName
                                raise SyntaxError('Type mismatch: {0} between {1} and {2}'.format(cmp, idA, idB))

                        if Identity.ValueDomain in {source.identity(), target.identity()}:

                            if source.type() is Item.RangeRestrictionNode:
                                # Deny the connection of Attribute range with Union|Intersection nodes: even
                                # though the identity matches the Attribute range restriction node is used only to
                                # express a DataPropertyRange axiom and we can't give it in input to an AND|OR node.
                                raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.name))

                elif target.type() is Item.EnumerationNode:

                    #############################################
                    # TARGET = ENUMERATION
                    #################################

                    if source.type() is not Item.IndividualNode:
                        # Enumeration operator (oneOf) takes as inputs instances or values, both
                        # represented by the Individual node, and has the job of composing a set
                        # if individuals (either Concept or ValueDomain, but not both together).
                        name = source.identity().value if source.identity() is not Identity.Neutral else source.name
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, name))

                    if target.identity() is Identity.Unknown:
                        # Target node has an unkown identity: we do not allow the connection => the
                        # user MUST fix the error first and then try to create again the connection
                        # (this most likely never happens).
                        raise SyntaxError('Target node has an invalid identity: {0}'.format(target.identity().value))

                    if target.identity() is not Identity.Neutral:

                        nameA = target.name
                        nameB = source.identity().value

                        if source.identity() is Identity.Individual and target.identity() is Identity.ValueDomain:
                            raise SyntaxError('Invalid input to {0}: {1}'.format(nameA, nameB))

                        if source.identity() is Identity.Value and target.identity() is Identity.Concept:
                            raise SyntaxError('Invalid input to {0}: {1}'.format(nameA, nameB))

                elif target.type() is Item.RoleInverseNode:

                    #############################################
                    # TARGET = ROLE INVERSE
                    #################################

                    if source.type() is not Item.RoleNode:
                        # The Role Inverse operator takes as input a role and constructs its inverse by switching
                        # domain and range of the role. Assume to have a Role labelled 'is_owner_of' whose instances
                        # are {(o1,o2), (o1,o3), (o4,o5)}: connecting this Role in input to a Role Inverse node will
                        # construct a new Role whose instances are {(o2,o1), (o3,o1), (o5,o4)}.
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.name))

                    if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) > 0:
                        # The Role Inverse operator may have at most one Role node connected to it: if we need to
                        # define multiple Role inverse we would need to use multiple Role Inverse operator nodes.
                        raise SyntaxError('Too many inputs to {0}'.format(target.name))

                elif target.type() is Item.RoleChainNode:

                    #############################################
                    # TARGET = ROLE CHAIN
                    #################################

                    if source.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                        # The Role Chain operator constructs a concatenation of roles. Assume to have 2 Role nodes
                        # defined as 'lives_in_region' and 'region_in_country': if {(o1, o2), (o3, o4)} is the
                        # instance of 'lives_in_region' and {(o2, o6)} is the instance of 'region_in_country', then
                        # {(o1, o6)} is the instance of the chain, which would match another Role 'lives_in_country'.
                        # ObjectPropertyExpression := ObjectProperty | InverseObjectProperty => we need to match only
                        # Role nodes and Role Inverse nodes as sources of our edge (it's not possible to create a chain
                        # of chains, despite the identity matches Role in both expressions).
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.name))

                elif target.type() is Item.DatatypeRestrictionNode:

                    #############################################
                    # TARGET = DATATYPE RESTRICTION
                    #################################

                    if source.type() not in {Item.ValueDomainNode, Item.FacetNode}:
                        # The DatatypeRestriction node is used to compose complex datatypes and
                        # accepts as inputs one value-domain node and n >= 1 facet
                        # nodes to compose the OWL 2 equivalent DatatypeRestriction.
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.name))

                    if source.type() is Item.ValueDomainNode:

                        f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                        f2 = lambda x: x.type() is Item.ValueDomainNode
                        if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                            # The value-domain has already been attached to the DatatypeRestriction.
                            raise SyntaxError('Too many value-domain nodes in input to datatype restriction node')

                        # Check if a Facet node is already connected to this node: if
                        # so we need to check whether the datatype in input and the
                        # already connected Facet are compatible.
                        f1 = lambda x: x.type() is Item.InputEdge
                        f2 = lambda x: x.type() is Item.FacetNode
                        node = first(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                        if node:
                            if node.facet not in Facet.forDatatype(source.datatype):
                                nA = source.datatype.value
                                nB = node.facet.value
                                raise SyntaxError('Type mismatch: datatype {0} is not supported by facet {1}'.format(nA, nB))

                    if source.type() is Item.FacetNode:

                        # We need to check if the DatatypeRestriction node has already datatype
                        # connected: if that's the case we need to check whether the Facet we
                        # want to attach to the datatype restriction node supports it.
                        f1 = lambda x: x.type() is Item.InputEdge
                        f2 = lambda x: x.type() is Item.ValueDomainNode
                        node = first(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                        if node:
                            if source.facet not in Facet.forDatatype(node.datatype):
                                nA = source.facet.value
                                nB = node.datatype.value
                                raise SyntaxError('Type mismatch: facet {0} is not supported by datatype {1}'.format(nA, nB))

                elif target.type() is Item.PropertyAssertionNode:

                    #############################################
                    # TARGET = PROPERTY ASSERTION
                    #################################

                    if source.type() is not Item.IndividualNode:
                        # Property Assertion operators accepts only Individual nodes as input: they are
                        # used to construct ObjectPropertyAssertion and DataPropertyAssertion axioms.
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.identity().value))

                    if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 2:
                        # At most 2 Individual nodes can be connected to a PropertyAssertion node. As an example
                        # we can construct ObjectPropertyAssertion(presiede M.Draghi BCE) where the individuals
                        # are identified by M.Draghi and BCE, or DataPropertyAssertion(nome M.Draghi "Mario") where
                        # the individuals are identified by M.Draghi and "Mario".
                        raise SyntaxError('Too many inputs to {0}'.format(target.name))

                    if target.identity() is Identity.RoleInstance:

                        if source.identity() is Identity.Value:
                            # We are constructing an ObjectPropertyAssertion expression so we can't connect a Value.
                            idA = target.identity().value
                            idB = source.identity().value
                            raise SyntaxError('Invalid input to {0}: {1}'.format(idA, idB))

                    if target.identity() is Identity.AttributeInstance:

                        if source.identity() is Identity.Individual:

                            f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                            f2 = lambda x: x.identity() is Identity.Individual
                            if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                                # We are constructing a DataPropertyAssertion and so we can't have more than 1 instance.
                                raise SyntaxError('Too many instances in input to {0}'.format(target.identity().value))

                        if source.identity() is Identity.Value:

                            f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                            f2 = lambda x: x.identity() is Identity.Value
                            if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                                # At most one value can be given as input (2 instance | 1 instance + 1 value)
                                raise SyntaxError('Too many values in input to {0}'.format(target.identity().value))

                elif target.type() is Item.DomainRestrictionNode:

                    #############################################
                    # TARGET = DOMAIN RESTRICTION
                    #################################

                    if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 2:
                        # Domain Restriction node can have at most 2 inputs.
                        raise SyntaxError('Too many inputs to {0}'.format(target.name))

                    supported = {Identity.Concept, Identity.Attribute, Identity.Role, Identity.ValueDomain, Identity.Neutral}
                    if source.identity() not in supported:
                        # Domain Restriction node takes as input:
                        #  - Role => OWL 2 ObjectPropertyExpression
                        #  - Attribute => OWL 2 DataPropertyExpression
                        #  - Concept => Qualified Existential/Universal Role Restriction
                        #  - ValueDomain => Qualified Existential Data Restriction
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.identity().value))

                    if source.type() is Item.RoleChainNode:
                        # Exclude incompatible sources: note that while RoleChain has a correct identity
                        # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.name))

                    # SOURCE => NEUTRAL

                    if source.identity() is Identity.Neutral:

                        if not source.identities() & {Identity.Concept, Identity.Attribute, Identity.Role, Identity.ValueDomain}:
                            # We can connect a Neutral node in input only if the source node admits a supported
                            # identity among the declared ones: Concept || Attribute || Role || ValueDomain.
                            raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.name))

                        node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                        if node:

                            if node.identity() is Identity.Role and Identity.Concept not in source.identities():
                                # If the target node has a Role in input, we can connect the source
                                # node iff it admits the Concept identity among the declared ones.
                                raise SyntaxError('Unsupported input for qualified restriction: {0}'.format(source.name))

                            if node.identity() is Identity.Concept and Identity.Role not in source.identities():
                                # If the target node has a Concept in input, we can connect the source
                                # node iff it admits the Role identity among the declared ones.
                                raise SyntaxError('Unsupported input for qualified restriction: {0}'.format(source.name))

                            if node.identity() is Identity.Attribute and Identity.ValueDomain not in source.identities():
                                # If the target node has a Attribute in input, we can connect the source
                                # node iff it admits the ValueDomain identity among the declared ones.
                                raise SyntaxError('Unsupported input for qualified restriction: {0}'.format(source.name))

                            if node.identity() is Identity.ValueDomain and Identity.Attribute not in source.identities():
                                # If the target node has a Attribute in input, we can connect the source
                                # node iff it admits the ValueDomain identity among the declared ones.
                                raise SyntaxError('Unsupported input for qualified restriction: {0}'.format(source.name))

                    # SOURCE => CONCEPT EXPRESSION

                    elif source.identity() is Identity.Concept:

                        if target.restriction is Restriction.Self:
                            # Not a Qualified Restriction.
                            name = target.restriction.toString()
                            raise SyntaxError('Invalid restriction type for qualified restriction: {0}'.format(name))

                        # A Concept can be given as input only if there is no input or if the other input is a Role.
                        node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                        if node and node.identity() is not Identity.Role:
                            # Not a Qualified Restriction.
                            idA = source.identity().value
                            idB = node.identity().value
                            raise SyntaxError('Invalid qualified restriction: {0} + {1}'.format(idA, idB))

                    # SOURCE => ROLE EXPRESSION

                    elif source.identity() is Identity.Role:

                        # We can connect a Role only if there is no other input or if the other input is a Concept.
                        node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                        if node and node.identity() is not Identity.Concept:
                            # Not a Qualified Restriction.
                            idA = source.identity().value
                            idB = node.identity().value
                            raise SyntaxError('Invalid qualified restriction: {0} + {1}'.format(idA, idB))

                    # SOURCE => ATTRIBUTE

                    elif source.identity() is Identity.Attribute:

                        if target.restriction is Restriction.Self:
                            # Attributes don't have self.
                            raise SyntaxError('Attributes do not have self')

                        # We can connect an Attribute only if there is no other input or if the other input is a ValueDomain.
                        node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                        if node and node.identity() is not Identity.ValueDomain:
                            # Not a Qualified Restriction.
                            idA = source.identity().value
                            idB = node.identity().value
                            raise SyntaxError('Invalid qualified restriction: {0} + {1}'.format(idA, idB))

                    # SOURCE => VALUE-DOMAIN

                    elif source.identity() is Identity.ValueDomain:

                        if target.restriction is Restriction.Self:
                            # Not a Qualified Restriction.
                            name = target.restriction.toString()
                            raise SyntaxError('Invalid restriction type for qualified restriction: {0}'.format(name))

                        # We can connect a ValueDomain only if there is no other input or if the other input is an Attribute.
                        node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                        if node and node.identity() is not Identity.Attribute:
                            # Not a Qualified Restriction.
                            idA = source.identity().value
                            idB = node.identity().value
                            raise SyntaxError('Invalid qualified restriction: {0} + {1}'.format(idA, idB))

                elif target.type() is Item.RangeRestrictionNode:

                    #############################################
                    # TARGET = RANGE RESTRICTION
                    #################################

                    if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 2:
                        # Range Restriction node can have at most 2 inputs.
                        raise SyntaxError('Too many inputs to {0}'.format(target.name))

                    f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                    f2 = lambda x: x.type() is Item.AttributeNode
                    if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) >= 1:
                        # Range restriction node having an attribute as input can receive no other input.
                        raise SyntaxError('Too many inputs to attribute range restriction')

                    if source.identity() not in {Identity.Concept, Identity.Attribute, Identity.Role, Identity.Neutral}:
                        # Range Restriction node takes as input:
                        #  - Role => OWL 2 ObjectPropertyExpression
                        #  - Attribute => OWL 2 DataPropertyExpression
                        #  - Concept => Qualified Existential/Universal Role Restriction
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.identity().value))

                    if source.type() is Item.RoleChainNode:
                        # Exclude incompatible sources: not that while RoleChain has a correct identity
                        # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                        raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.name))

                    # SOURCE => NEUTRAL

                    if source.identity() is Identity.Neutral:

                        if not source.identities() & {Identity.Concept, Identity.Attribute, Identity.Role}:
                            # We can connect a Neutral node in input only if the source node admits a
                            # supported identity among the declared ones: Concept || Attribute || Role.
                            raise SyntaxError('Invalid input to {0}: {1}'.format(target.name, source.name))

                        node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                        if node:

                            if node.identity() is Identity.Role and Identity.Concept not in source.identities():
                                # If the target node has a Role in input, we can connect the source
                                # node iff it admits the Concept identity among the declared ones.
                                raise SyntaxError('Unsupported input for qualified restriction: {0}'.format(source.name))

                            if node.identity() is Identity.Concept and Identity.Role not in source.identities():
                                # If the target node has a Concept in input, we can connect the source
                                # node iff it admits the Role identity among the declared ones.
                                raise SyntaxError('Unsupported input for qualified restriction: {0}'.format(source.name))

                    # SOURCE => CONCEPT EXPRESSION

                    elif source.identity() is Identity.Concept:

                        # We can connect a Concept in input iff there is no other input or if the other
                        # input is either a Role or a Neutral node that can assume the Role identity.
                        node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                        if node and Identity.Role not in node.identities():
                            # Not a Qualified Restriction.
                            idA = source.identity().value
                            idB = node.identity().value
                            raise SyntaxError('Invalid qualified restriction: {0} + {1}'.format(idA, idB))

                    # SOURCE => ROLE EXPRESSION

                    elif source.identity() is Identity.Role:

                        # We can connect a Role in input only if there is no other input or if the other
                        # input is either a Concept or a Neutral node that can assume the Concept identity.
                        node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                        if node and Identity.Concept not in node.identities():
                            # Not a Qualified Restriction.
                            idA = source.identity().value
                            idB = node.identity().value
                            raise SyntaxError('Invalid qualified restriction: {0} + {1}'.format(idA, idB))

                    # SOURCE => ATTRIBUTE NODE

                    elif source.identity() is Identity.Attribute:

                        if target.restriction is Restriction.Self:
                            # Attributes don't have self.
                            raise SyntaxError('Attributes do not have self')

                        # We can connect an Attribute in input only if there is no other input.
                        if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 1:
                            # Something else is connected to this range restriction node (either a Concept
                            # or a Role) so we cannot attach the Attribute node (no DataPropertyRange).
                            raise SyntaxError('Too many inputs to attribute range restriction')

                elif target.type() is Item.FacetNode:

                    #############################################
                    # TARGET = FACET NODE
                    #################################

                    # Facet node cannot be target of any input.
                    raise SyntaxError('Facet node cannot be target of any input')

            #############################################
            # EDGE = MEMBERSHIP
            #################################

            elif edge.type() is Item.MembershipEdge:

                if source is target:
                    # Self connection is forbidden.
                    raise SyntaxError('Self connection is not valid')

                if source.identity() is not Identity.Individual and source.type() is not Item.PropertyAssertionNode:
                    # The source of the edge must be one of Instance or a Property Assertion node.
                    raise SyntaxError('Invalid source for membership edge: {0}'.format(source.identity().value))

                supported = {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}
                if target.identity() is not Identity.Concept and target.type() not in supported:
                    # The target of the edge must be a ClassExpression, ObjectPropertyExpression or DataPropertyExpression.
                    raise SyntaxError('Invalid target for membership edge: {0}'.format(target.name))

                if source.identity() is Identity.Individual:

                    if target.identity() is not Identity.Concept:
                        # If the source of the edge is an Individual it means that we are trying to construct a
                        # ClassAssertion and so the target of the edge MUST be a class expression.
                        # OWL 2: ClassAssertion(axiomAnnotations ClassExpression Individual)
                        raise SyntaxError('Invalid target for Concept assertion: {0}'.format(target.identity().value))

                if source.type() is Item.PropertyAssertionNode:

                    if source.identity() is Identity.RoleInstance and target.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                        # If the source of the edge is a Role Instance then we MUST target a Role expression.
                        raise SyntaxError('Invalid target for Role assertion: {0}'.format(target.name))

                    if source.identity() is Identity.AttributeInstance and target.type() is not Item.AttributeNode:
                        # If the source of the edge is an Attribute Instance then we MUST target an Attribute.
                        raise SyntaxError('Invalid target for Attribute assertion: {0}'.format(target.name))

        except SyntaxError as e:
            pvr = ProfileValidationResult(source, edge, target, False)
            pvr.setMessage(e.msg)
            self.setPvr(pvr)
        else:
            self.setPvr(ProfileValidationResult(source, edge, target, True))