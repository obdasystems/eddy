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


from eddy.core.datatypes.graphol import Identity, Item, Restriction
from eddy.core.functions.misc import cutR, first
from eddy.core.syntax.common import AbstractValidator, ValidationResult


class OWL2Validator(AbstractValidator):
    """
    This class can be used to validate Graphol triples according to the OWL2 syntax.
    """
    #############################################
    #   INTERFACE
    #################################

    def run(self, source, edge, target):
        """
        Run the validation algorithm on the given triple and generates the ValidationResult instance.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        """
        try:

            if source is target:
                # We do not allow the connection if source and target are the same node.
                raise SyntaxError('Self connection is not valid')

            if edge.item is Item.InclusionEdge:

                #############################################
                # INCLUSION EDGE
                #################################

                supported = {Identity.Concept, Identity.Role, Identity.Attribute, Identity.ValueDomain}
                remaining = source.identities & target.identities - {Identity.Neutral, Identity.Unknown}

                if remaining - supported:
                    # Inclusion assertions can be specified only between Graphol expressions: Concept
                    # expressions, Role expressions, Value-Domain expressions, Attribute expressions.
                    raise SyntaxError('Type mismatch: inclusion must involve two graphol expressions')

                if not remaining:
                    # If source and target nodes do not share a common identity then we can't create an inclusion.
                    raise SyntaxError('Type mismatch: {} and {} are not compatible'.format(source.name, target.name))

                if Identity.Neutral not in {source.identity, target.identity} and source.identity is not target.identity:
                    # If both nodes are not NEUTRAL and they specify a different identity we can't create an inclusion.
                    idA = source.identity.value
                    idB = target.identity.value
                    raise SyntaxError('Type mismatch: inclusion between {} and {}'.format(idA, idB))

                if Identity.ValueDomain in {source.identity, target.identity}:

                    # We exclude from the following check inclusion edges sourcing from a RangeRestriction
                    # node since it will be translated into OWL DataPropertyRange that accepts ValueDomain
                    # i.e. complex datatypes and not only atomic ones.
                    if source.item is not Item.RangeRestrictionNode:

                        if source.item is not Item.ValueDomainNode and target.item is not Item.ValueDomainNode:
                            # Inclusion assertions between value-domain expressions must involve at least an atomic
                            # datatype (i.e., the source or the target of the assertion must be an atomic datatype).
                            raise SyntaxError('Inclusion between value-domain expressions must include at least an '
                                              'atomic datatype')

                if source.item is Item.ComplementNode:

                    identity = first({source.identity, target.identity} - {Identity.Neutral})
                    if identity and identity in {Identity.Attribute, Identity.Role}:
                        # Role and attribute expressions whose sink node is a
                        # complement node cannot be the source of any inclusion edge.
                        raise SyntaxError('Invalid source for {} inclusion: {}'.format(identity.value, source.name))

                if target.item is Item.RoleChainNode:
                    # Role expressions constructed with chain nodes cannot be the target of any inclusion edge.
                    raise SyntaxError('Type mismatch: role chain nodes cannot be target of a Role inclusion')

                if source.item is Item.RoleChainNode:
                    # Role expressions constructed with chain nodes can be included only in basic role expressions, that
                    # are either Role nodes or RoleInverse nodes with one input Role node (this check is done elsewhere)
                    if target.item not in {Item.RoleNode, Item.RoleInverseNode}:
                        raise SyntaxError('Inclusion between {} and {} is forbidden'.format(source.name, target.name))

            elif edge.item is Item.InputEdge:

                #############################################
                # INPUT EDGE
                #################################

                if not target.constructor:
                    # Input edges can only target constructor nodes.
                    raise SyntaxError('Input edges can only target constructor nodes')

                if target.item in {Item.ComplementNode, Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode}:

                    #############################################
                    # TARGET = COMPLEMENT | INTERSECTION | UNION
                    #################################

                    if source.identity not in target.identities:
                        # Source node identity is not supported by this node despite the currently set identity.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.value))

                    if source.item is Item.ValueRestrictionNode:
                        # Exclude invalid nodes despite identity matching.
                        raise SyntaxError('Invalid target: {}'.format(target.name))

                    #############################################
                    # TARGET = COMPLEMENT
                    #################################

                    if target.item is Item.ComplementNode:

                        if len(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge)) > 0:
                            # The Complement operator may have at most one node connected to it.
                            raise SyntaxError('Too many inputs to {}'.format(target.name))

                        if source.item in {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}:

                            # See if the source of the node matches an ObjectPropertyExpression ({Role, RoleInv}) or a
                            # DataPropertyExpression (Attribute). If that's the case check for the node not to have any
                            # outgoing Input edge: the only supported expression are NegativeObjectPropertyAssertion,
                            # R1 ISA NOT R2, and NegativeDataPropertyAssertion, A1 ISA NOT A2. This prevents the
                            # connection of Role expressions to Complement nodes that are given as inputs to Enumeration,
                            # Union and Disjoint Union operatore nodes.
                            if len(target.incomingNodes(lambda x: x.item is Item.InputEdge and x.source is target)) > 0:
                                raise SyntaxError('Invalid negative {} expression'.format(source.identity.value))

                    else:

                        #############################################
                        # TARGET = UNION | INTERSECTION
                        #################################

                        if Identity.Neutral not in {source.identity, target.identity}:

                            if source.identity is not target.identity:
                                # Union/Intersection between different type of graphol expressions.
                                idA = source.identity.value
                                idB = target.identity.value
                                composition = cutR(target.name, ' node')
                                raise SyntaxError('Type mismatch: {} between {} and {}'.format(composition, idA, idB))

                elif target.item is Item.EnumerationNode:

                    #############################################
                    # TARGET = ENUMERATION
                    #################################

                    if source.item is not Item.IndividualNode:
                        # Enumeration operator (oneOf) takes as inputs instances or values, both represented
                        # by the Individual node, and has the job of composing a set if individuals (either Concept
                        # or ValueDomain, but not both together).
                        name = source.identity.value if source.identity is not Identity.Neutral else source.name
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, name))

                    if target.identity is Identity.Unknown:
                        # Target node has an unkown identity: we do not allow the connection => the user MUST fix the
                        # error first and then try to create again the connection (this should never happen actually).
                        raise SyntaxError('Target node has an invalid identity: {}'.format(target.identity.value))

                    if target.identity is not Identity.Neutral:

                        if source.identity is Identity.Instance and target.identity is Identity.ValueDomain:
                            raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.value))

                        if source.identity is Identity.Value and target.identity is Identity.Concept:
                            raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.value))

                elif target.item is Item.RoleInverseNode:

                    #############################################
                    # TARGET = ROLE INVERSE
                    #################################

                    if source.item is not Item.RoleNode:
                        # The Role Inverse operator takes as input a role and constructs its inverse by switching
                        # domain and range of the role. Assume to have a Role labelled 'is_owner_of' whose instances
                        # are {(o1,o2), (o1,o3), (o4,o5)}: connecting this Role in input to a Role Inverse node will
                        # construct a new Role whose instances are {(o2,o1), (o3,o1), (o5,o4)}.
                        raise SyntaxError('Role Inverse accepts only a Role node as input')

                    if len(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge)) > 0:
                        # The Role Inverse operator may have at most one Role node connected to it: if we need to
                        # define multiple Role inverse we would need to use multiple Role Inverse operator nodes.
                        raise SyntaxError('Too many inputs to {}'.format(target.name))

                elif target.item is Item.RoleChainNode:

                    #############################################
                    # TARGET = ROLE CHAIN
                    #################################

                    if source.item not in {Item.RoleNode, Item.RoleInverseNode}:
                        # The Role Chain operator constructs a concatenation of roles. Assume to have 2 Role nodes
                        # defined as 'lives_in_region' and 'region_in_country': if {(o1, o2), (o3, o4)} is the
                        # instance of 'lives_in_region' and {(o2, o6)} is the instance of 'region_in_country', then
                        # {(o1, o6)} is the instance of the chain, which would match another Role 'lives_in_country'.
                        # ObjectPropertyExpression := ObjectProperty | InverseObjectProperty => we need to match only
                        # Role nodes and Role Inverse nodes as sources of our edge (it's not possible to create a chain
                        # of chains, despite the identity matches Role in both expressions).
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.name))

                elif target.item is Item.DatatypeRestrictionNode:

                    #############################################
                    # TARGET = DATATYPE RESTRICTION
                    #################################

                    if source.item not in {Item.ValueDomainNode, Item.ValueRestrictionNode}:
                        # The DatatypeRestriction node is used to compose complex datatypes and
                        # accepts as inputs one value-domain node and n >= 1 value-restriction
                        # nodes to compose the OWL 2 equivalent DatatypeRestriction.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.name))

                    if source.item is Item.ValueDomainNode:

                        f1 = lambda x: x.item is Item.InputEdge and x is not edge
                        f2 = lambda x: x.item is Item.ValueDomainNode
                        if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                            # The value-domain has already been attached to the DatatypeRestriction.
                            raise SyntaxError('Too many value-domain nodes in input to {}'.format(target.name))

                    # We need to check whether the DatatypeRestriction node has already datatype
                    # inferred: if that's the case and the datatype doesn't match the datatype of
                    # the source node, we deny the connection to prevent inconsistencies.
                    f1 = lambda x: x.item is Item.InputEdge and x is not edge
                    f2 = lambda x: x.item in {Item.ValueDomainNode, Item.ValueRestrictionNode} and x is not source
                    collection = target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
                    if collection:
                        datatype = first(collection).datatype
                        if  datatype is not source.datatype:
                            d1 = source.datatype.value
                            d2 = datatype.value
                            raise SyntaxError('Datatype mismatch: restriction between {} and {}'.format(d1, d2))

                elif target.item is Item.PropertyAssertionNode:

                    #############################################
                    # TARGET = PROPERTY ASSERTION
                    #################################

                    if source.item is not Item.IndividualNode:
                        # Property Assertion operators accepts only Individual nodes as input: they are
                        # used to construct ObjectPropertyAssertion and DataPropertyAssertion axioms.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.value))

                    if len(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge)) >= 2:
                        # At most 2 Individual nodes can be connected to a PropertyAssertion node. As an example
                        # we can construct ObjectPropertyAssertion(presiede M.Draghi BCE) where the individuals
                        # are identified by M.Draghi and BCE, or DataPropertyAssertion(nome M.Draghi "Mario") where
                        # the individuals are identified by M.Draghi and "Mario".
                        raise SyntaxError('Too many inputs to {}'.format(target.name))

                    if target.identity is Identity.RoleInstance:

                        if source.identity is Identity.Value:
                            # We are constructing an ObjectPropertyAssertion expression so we can't connect a Value.
                            raise SyntaxError('Invalid input to {}: Value'.format(target.identity.value))

                    if target.identity is Identity.AttributeInstance:

                        if source.identity is Identity.Instance:

                            f1 = lambda x: x.item is Item.InputEdge and x is not edge
                            f2 = lambda x: x.identity is Identity.Instance
                            if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                                # We are constructing a DataPropertyAssertion and so we can't have more than 1 instance.
                                raise SyntaxError('Too many instances in input to {}'.format(target.identity.value))

                        if source.identity is Identity.Value:

                            f1 = lambda x: x.item is Item.InputEdge and x is not edge
                            f2 = lambda x: x.identity is Identity.Value
                            if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                                # At most one Literal can be given as input (2 instance | 1 instance + 1 value)
                                raise SyntaxError('Too many values in input to {}'.format(target.identity.value))

                elif target.item is Item.DomainRestrictionNode:

                    #############################################
                    # TARGET = DOMAIN RESTRICTION
                    #################################

                    if len(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge)) >= 2:
                        # Domain Restriction node can have at most 2 inputs.
                        raise SyntaxError('Too many inputs to {}'.format(target.name))

                    supported = {Identity.Concept, Identity.Attribute, Identity.Role, Identity.ValueDomain}
                    if source.identity is not Identity.Neutral and source.identity not in supported:
                        # Domain Restriction node takes as input:
                        #  - Role => OWL 2 ObjectPropertyExpression
                        #  - Attribute => OWL 2 DataPropertyExpression
                        #  - Concept => Qualified Existential/Universal Role Restriction
                        #  - ValueDomain => Qualified Existential Data Restriction
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.value))

                    if source.item in {Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.RoleChainNode}:
                        # Exclude incompatible sources: note that while RoleChain has a correct identity
                        # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.name))

                    # SOURCE => CONCEPT EXPRESSION || NEUTRAL

                    if source.identity in {Identity.Concept, Identity.Neutral}:

                        if target.restriction is Restriction.Self:
                            # Not a Qualified Restriction.
                            raise SyntaxError('Invalid restriction (self) for qualified restriction')

                        # A Concept can be given as input only if there is no input or if the other input is a Role.
                        node = first(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge))
                        if node and node.identity is not Identity.Role:
                            # We found another input on this node which is not a Role
                            # so we can't construct a Qualified Restriction.
                            idA = source.identity.value
                            idB = node.identity.value
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => ROLE EXPRESSION

                    elif source.identity is Identity.Role:

                        # We can connect a Role in input only if there is no other input or if the
                        # other input is a Concept and the node specifies a Qualified Restriction.
                        node = first(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge))
                        if node and node.identity is not Identity.Concept:
                            # Not a Qualified Restriction.
                            idA = source.identity.value
                            idB = node.identity.value
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => ATTRIBUTE

                    elif source.identity is Identity.Attribute:

                        if target.restriction is Restriction.Self:
                            # Attributes don't have self.
                            raise SyntaxError('Attributes don\'t have self')

                        # We can connect an Attribute in input only if there is no other input or if the
                        # other input is a ValueDomain and the node specifies a Qualified Restriction.
                        node = first(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge))
                        if node and node.identity is not Identity.ValueDomain:
                            # Not a Qualified Restriction.
                            idA = source.identity.value
                            idB = node.identity.value
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => VALUE-DOMAIN

                    elif source.identity is Identity.ValueDomain:

                        if target.restriction is Restriction.Self:
                            # Not a Qualified Restriction.
                            raise SyntaxError('Invalid restriction (self) for qualified restriction')

                        # We can connect a ValueDomain in input only if there is no other input or if the
                        # other input is an Attribute and the node specifies a Qualified Restriction.
                        node = first(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge))
                        if node and node.identity is not Identity.Attribute:
                            # Not a Qualified Restriction.
                            idA = source.identity.value
                            idB = node.identity.value
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                elif target.item is Item.RangeRestrictionNode:

                    #############################################
                    # TARGET = RANGE RESTRICTION
                    #################################

                    if len(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge)) >= 2:
                        # Range Restriction node can have at most 2 inputs.
                        raise SyntaxError('Too many inputs to {}'.format(target.name))

                    supported = {Identity.Concept, Identity.Attribute, Identity.Role, Identity.ValueDomain}
                    if source.identity is not Identity.Neutral and source.identity not in supported:
                        # Range Restriction node takes as input:
                        #  - Role => OWL 2 ObjectPropertyExpression
                        #  - Attribute => OWL 2 DataPropertyExpression
                        #  - Concept => Qualified Existential/Universal Role Restriction
                        #  - ValueDomain => Qualified Existential Data Restriction
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.value))

                    if source.item in {Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.RoleChainNode}:
                        # Exclude incompatible sources: not that while RoleChain has a correct identity
                        # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.name))

                    # SOURCE => CONCEPT EXPRESSION || NEUTRAL

                    if source.identity in {Identity.Concept, Identity.Neutral}:

                        # We can connect a Concept in input iff there is no other input or if the other input is a Role.
                        node = first(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge))
                        if node and node.identity is not Identity.Role:
                            # We found another input on this node which is not a Role
                            # so we can't construct a Qualified Restriction.
                            idA = source.identity.value
                            idB = node.identity.value
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => ROLE EXPRESSION

                    if source.identity is Identity.Role:

                        # We can connect a Role in input only if there is no other input or if the
                        # other input is a Concept and the node specifies a Qualified Restriction.
                        node = first(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge))
                        if node and node.identity is not Identity.Concept:
                            # Not a Qualified Restriction.
                            idA = source.identity.value
                            idB = node.identity.value
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => ATTRIBUTE NODE

                    elif source.identity is Identity.Attribute:

                        # We can connect an Attribute in input only if there is no other input or if the
                        # other input is a ValueDomain and the node specifies a Qualified Restriction.
                        node = first(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge))
                        if node and node.identity is not Identity.ValueDomain:
                            # Not a Qualified Restriction.
                            idA = source.identity.value
                            idB = node.identity.value
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => VALUE-DOMAIN

                    elif source.identity is Identity.ValueDomain:

                        # We can connect a ValueDomain in input only if there is no other input or if the
                        # other input is an Attribute and the node specifies a Qualified Restriction.
                        node = first(target.incomingNodes(lambda x: x.item is Item.InputEdge and x is not edge))
                        if node and node.identity is not Identity.Attribute:
                            # Not a Qualified Restriction.
                            idA = source.identity.value
                            idB = node.identity.value
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

            elif edge.item is Item.MembershipEdge:

                #############################################
                # MEMBERSHIP EDGE
                #################################

                if source.identity is not Identity.Instance and source.item is not Item.PropertyAssertionNode:
                    # The source of the edge must be one of Instance or a Property Assertion node.
                    raise SyntaxError('Invalid source for instanceOf edge: {}'.format(source.identity.value))

                if target.identity is not Identity.Concept and target.item not in {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}:
                    # The target of the edge must be a ClassExpression, ObjectPropertyExpression or DataPropertyExpression.
                    raise SyntaxError('Invalid target for instanceOf edge: {}'.format(target.name))

                if source.identity is Identity.Instance:

                    if target.identity is not Identity.Concept:
                        # If the source of the edge is an Instance it means that we are trying to construct a
                        # ClassAssertion and so the target of the edge MUST be a class expression.
                        # OWL 2: ClassAssertion(axiomAnnotations ClassExpression Individual)
                        raise SyntaxError('Invalid target for Concept assertion: {}'.format(target.identity.value))

                if source.item is Item.PropertyAssertionNode:

                    if source.identity is Identity.RoleInstance and target.item not in {Item.RoleNode, Item.RoleInverseNode}:
                        # If the source of the edge is a Role Instance then we MUST target a Role expression.
                        raise SyntaxError('Invalid target for Role assertion: {}'.format(target.name))

                    if source.identity is Identity.AttributeInstance and target.item is not Item.AttributeNode:
                        # If the source of the edge is an Attribute Instance then we MUST target an Attribute.
                        raise SyntaxError('Invalid target for Attribute assertion: {}'.format(target.name))

        except SyntaxError as e:
            self._result = ValidationResult(source, edge, target, False, e.msg)
        else:
            self._result = ValidationResult(source, edge, target, True)