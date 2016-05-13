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
from eddy.core.datatypes.owl import Facet
from eddy.core.functions.graph import bfs
from eddy.core.functions.misc import cutR, first
from eddy.core.syntax.common import AbstractValidator
from eddy.core.syntax.common import SyntaxValidationResult

from eddy.lang import gettext as _


class OWL2Validator(AbstractValidator):
    """
    This class can be used to validate graphol triples according to the OWL2 syntax.
    """
    def __init__(self, parent=None):
        """
        Initialize the validator.
        :type parent: QObject
        """
        super().__init__(parent)
        self.funcForEdge = {
            Item.InclusionEdge: self.inclusion,
            Item.InputEdge: self.input,
            Item.MembershipEdge: self.membership,
        }

    #############################################
    #   AUXILIARY METHODS
    #################################

    @staticmethod
    def inclusion(source, edge, target):
        """
        Validates the inclusion between the given source and the given target.
        :type source: AbstractNode
        :type edge: InclusionEdge
        :type target: AbstractNode
        :raise SyntaxError: if the connection is not valid.
        """
        if source is target:
            # Self connection is forbidden.
            raise SyntaxError(_('SYNTAX_SELF_CONNECTION'))

        # Here we keep the ValueDomain as supported identity even though we deny the inclusion
        # between value-domain expressions, unless we are creating a DataPropertyRange axiom.
        # The reason for this is that if we remove the identity from the supported set the user
        # will see the message which explains that the inclusion is denied because it does not
        # involve two graphol expressions, while it actually does. We handle this special case
        # here below, by passing the only allowed inclusion between value-domain expressions.
        supported = {Identity.Concept, Identity.Role, Identity.Attribute, Identity.ValueDomain}
        remaining = source.Identities & target.Identities - {Identity.Neutral, Identity.Unknown}

        if remaining - supported:
            # Inclusion assertions can be specified only between graphol expressions: Concept
            # expressions, Role expressions, Value-Domain expressions, Attribute expressions.
            raise SyntaxError(_('SYNTAX_INCLUSION_NO_GRAPHOL_EXPRESSION'))

        if Identity.Neutral not in {source.identity, target.identity} and source.identity is not target.identity:
            # If both nodes are not NEUTRAL and they have a different identity we can't create an inclusion.
            idA = source.identity.value
            idB = target.identity.value
            raise SyntaxError(_('SYNTAX_INCLUSION_TYPE_MISMATCH', idA, idB))

        if not remaining:
            # If source and target nodes do not share a common identity then we can't create an inclusion.
            raise SyntaxError(_('SYNTAX_INCLUSION_NOT_COMPATIBLE', source.name, target.name))

        if Identity.ValueDomain in {source.identity, target.identity}:

            if source.type() is not Item.RangeRestrictionNode:
                # Inclusions between value-domain expressions is not yet supported. However,
                # we allow inclusions between value-domain expressions only if we are tracing
                # an inclusion edge sourcing from a range restriction node (whose input is an
                # attribute node, and therefor its identity is set to value-domain) and targeting
                # a value-domain expression, either complex or atomic, eventually excluding the
                # attribute range restriction as target.
                raise SyntaxError(_('SYNTAX_INCLUSION_VALUE_DOMAIN_EXPRESSIONS'))

        if source.type() is Item.ComplementNode:

            identity = first({source.identity, target.identity} - {Identity.Neutral})
            if identity and identity in {Identity.Attribute, Identity.Role}:
                # Complement nodes can only be the target of Role and Attribute inclusions since they
                # are used to generate OWLDisjointObjectPropertiesAxiom and OWLDisjointDataPropertiesAxiom.
                # Differently we allow inclusions targeting concept nodes to source from complement nodes.
                raise SyntaxError(_('SYNTAX_INCLUSION_COMPLEMENT_INVALID_SOURCE', identity.value, source.name))

        if target.type() is Item.RoleChainNode:
            # Role expressions constructed with chain nodes cannot be the target of any inclusion edge.
            raise SyntaxError(_('SYNTAX_INCLUSION_CHAIN_AS_TARGET'))

        if source.type() is Item.RoleChainNode:
            # Role expressions constructed with chain nodes can be included only
            # in basic role expressions, that are either Role nodes or RoleInverse
            # nodes with one input Role node (this check is done elsewhere).
            if target.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                raise SyntaxError(_('SYNTAX_INCLUSION_CHAIN_AS_SOURCE_INVALID_TARGET', source.name, target.name))

    @staticmethod
    def input(source, edge, target):
        """
        Validates the input between the given source and the given target.
        :type source: AbstractNode
        :type edge: InputEdge
        :type target: AbstractNode
        :raise SyntaxError: if the connection is not valid.
        """
        if source is target:
            # Self connection is forbidden.
            raise SyntaxError(_('SYNTAX_SELF_CONNECTION'))

        if not target.isConstructor():
            # Input edges can only target constructor nodes.
            raise SyntaxError(_('SYNTAX_INPUT_INVALID_TARGET'))

        if target.type() in {Item.ComplementNode, Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode}:

            #############################################
            # TARGET = COMPLEMENT | INTERSECTION | UNION
            #################################

            if source.identity not in target.Identities:
                # Source node identity is not supported by this target node.
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, source.identity.value))

            if source.identity is Identity.ValueDomain and target.identity is Identity.Neutral:
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
                f2 = lambda x: x.identity is Identity.Neutral
                f3 = lambda x: x.type() is Item.InclusionEdge
                f4 = lambda x: x.type() is Item.InclusionEdge and x.source.type() is not Item.RangeRestrictionNode
                for node in bfs(source=target, filter_on_edges=f1, filter_on_nodes=f2):
                    if node.outgoingNodes(filter_on_edges=f3) or node.incomingNodes(filter_on_edges=f4):
                        raise SyntaxError(_('SYNTAX_INCLUSION_VALUE_DOMAIN_EXPRESSIONS'))

            #############################################
            # TARGET = COMPLEMENT
            #################################

            if target.type() is Item.ComplementNode:

                if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) > 0:
                    # The Complement operator may have at most one node connected to it.
                    raise SyntaxError(_('SYNTAX_INPUT_TOO_MANY_OPERANDS', target.name))

                if source.type() in {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}:
                    # See if the source of the node matches an ObjectPropertyExpression
                    # ({Role, RoleInv}) or a DataPropertyExpression (Attribute). If that's
                    # the case check for the node not to have any outgoing Input edge: the only
                    # supported expression are NegativeObjectPropertyAssertion (R1 ISA NOT R2) and
                    # NegativeDataPropertyAssertion (A1 ISA NOT A2). This prevents the connection of
                    # Role expressions to Complement nodes that are given as inputs to Enumeration,
                    # Union and Disjoint Union operatore nodes.
                    if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x.source is target)) > 0:
                        raise SyntaxError(_('SYNTAX_INPUT_COMPLEMENT_INVALID_EXPRESSION', source.identity.value))

            else:

                #############################################
                # TARGET = UNION | INTERSECTION
                #################################

                if Identity.Neutral not in {source.identity, target.identity}:

                    if source.identity is not target.identity:
                        # Union/Intersection between different type of graphol expressions.
                        idA = source.identity.value
                        idB = target.identity.value
                        cmp = cutR(target.name, ' node')
                        raise SyntaxError(_('SYNTAX_INPUT_INVALID_COMPOSITION', cmp, idA, idB))

        elif target.type() is Item.EnumerationNode:

            #############################################
            # TARGET = ENUMERATION
            #################################

            if source.type() is not Item.IndividualNode:
                # Enumeration operator (oneOf) takes as inputs instances or values, both
                # represented by the Individual node, and has the job of composing a set
                # if individuals (either Concept or ValueDomain, but not both together).
                name = source.identity.value if source.identity is not Identity.Neutral else source.name
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, name))

            if target.identity is Identity.Unknown:
                # Target node has an unkown identity: we do not allow the connection => the
                # user MUST fix the error first and then try to create again the connection
                # (this most likely never happens).
                raise SyntaxError(_('SYNTAX_INPUT_ENUMERATION_INVALID_TARGET_IDENTITY', target.identity.value))

            if target.identity is not Identity.Neutral:

                nameA = target.name
                nameB = source.identity.value

                if source.identity is Identity.Instance and target.identity is Identity.ValueDomain:
                    raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', nameA, nameB))

                if source.identity is Identity.Value and target.identity is Identity.Concept:
                    raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', nameA, nameB))

        elif target.type() is Item.RoleInverseNode:

            #############################################
            # TARGET = ROLE INVERSE
            #################################

            if source.type() is not Item.RoleNode:
                # The Role Inverse operator takes as input a role and constructs its inverse by switching
                # domain and range of the role. Assume to have a Role labelled 'is_owner_of' whose instances
                # are {(o1,o2), (o1,o3), (o4,o5)}: connecting this Role in input to a Role Inverse node will
                # construct a new Role whose instances are {(o2,o1), (o3,o1), (o5,o4)}.
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, source.name))

            if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) > 0:
                # The Role Inverse operator may have at most one Role node connected to it: if we need to
                # define multiple Role inverse we would need to use multiple Role Inverse operator nodes.
                raise SyntaxError(_('SYNTAX_INPUT_TOO_MANY_OPERANDS', target.name))

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
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, source.name))

        elif target.type() is Item.DatatypeRestrictionNode:

            #############################################
            # TARGET = DATATYPE RESTRICTION
            #################################

            if source.type() not in {Item.ValueDomainNode, Item.FacetNode}:
                # The DatatypeRestriction node is used to compose complex datatypes and
                # accepts as inputs one value-domain node and n >= 1 facet
                # nodes to compose the OWL 2 equivalent DatatypeRestriction.
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, source.name))

            if source.type() is Item.ValueDomainNode:

                f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                f2 = lambda x: x.type() is Item.ValueDomainNode
                if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                    # The value-domain has already been attached to the DatatypeRestriction.
                    raise SyntaxError(_('SYNTAX_INPUT_DATA_TOO_MANY_DATATYPE'))

            if source.type() is Item.FacetNode:

                # We need to check if the DatatypeRestriction node has already datatype
                # connected: if that's the case we need to check whether the Facet we
                # want to attach to the datatype restriction node supports it.
                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.type() is Item.ValueDomainNode
                node = first(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                if node:
                    if source.facet not in Facet.forDatatype(node.datatype):
                        nameA = source.facet.value
                        nameB = node.datatype.value
                        raise SyntaxError(_('SYNTAX_INPUT_DATA_INVALID_FACET', nameA , nameB))

        elif target.type() is Item.PropertyAssertionNode:

            #############################################
            # TARGET = PROPERTY ASSERTION
            #################################

            if source.type() is not Item.IndividualNode:
                # Property Assertion operators accepts only Individual nodes as input: they are
                # used to construct ObjectPropertyAssertion and DataPropertyAssertion axioms.
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, source.identity.value))

            if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 2:
                # At most 2 Individual nodes can be connected to a PropertyAssertion node. As an example
                # we can construct ObjectPropertyAssertion(presiede M.Draghi BCE) where the individuals
                # are identified by M.Draghi and BCE, or DataPropertyAssertion(nome M.Draghi "Mario") where
                # the individuals are identified by M.Draghi and "Mario".
                raise SyntaxError(_('SYNTAX_INPUT_TOO_MANY_OPERANDS', target.name))

            if target.identity is Identity.RoleInstance:

                if source.identity is Identity.Value:
                    # We are constructing an ObjectPropertyAssertion expression so we can't connect a Value.
                    idA = target.identity.value
                    idB = source.identity.value
                    raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', idA, idB))

            if target.identity is Identity.AttributeInstance:

                if source.identity is Identity.Instance:

                    f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                    f2 = lambda x: x.identity is Identity.Instance
                    if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                        # We are constructing a DataPropertyAssertion and so we can't have more than 1 instance.
                        raise SyntaxError(_('SYNTAX_INPUT_PROP_ASSERTION_TOO_MANY_INSTANCES', target.identity.value))

                if source.identity is Identity.Value:

                    f1 = lambda x: x.type() is Item.InputEdge and x is not edge
                    f2 = lambda x: x.identity is Identity.Value
                    if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                        # At most one value can be given as input (2 instance | 1 instance + 1 value)
                        raise SyntaxError(_('SYNTAX_INPUT_PROP_ASSERTION_TOO_MANY_VALUES', target.identity.value))

        elif target.type() is Item.DomainRestrictionNode:

            #############################################
            # TARGET = DOMAIN RESTRICTION
            #################################

            if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 2:
                # Domain Restriction node can have at most 2 inputs.
                raise SyntaxError(_('SYNTAX_INPUT_TOO_MANY_OPERANDS', target.name))

            supported = {Identity.Concept, Identity.Attribute, Identity.Role, Identity.ValueDomain}
            if source.identity is not Identity.Neutral and source.identity not in supported:
                # Domain Restriction node takes as input:
                #  - Role => OWL 2 ObjectPropertyExpression
                #  - Attribute => OWL 2 DataPropertyExpression
                #  - Concept => Qualified Existential/Universal Role Restriction
                #  - ValueDomain => Qualified Existential Data Restriction
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, source.identity.value))

            if source.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.RoleChainNode}:
                # Exclude incompatible sources: note that while RoleChain has a correct identity
                # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, source.name))

            # SOURCE => CONCEPT EXPRESSION || NEUTRAL

            if source.identity in {Identity.Concept, Identity.Neutral}:

                if target.restriction is Restriction.Self:
                    # Not a Qualified Restriction.
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION', target.restriction.format()))

                # A Concept can be given as input only if there is no input or if the other input is a Role.
                node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                if node and node.identity is not Identity.Role:
                    # We found another input on this node which is not a Role
                    # so we can't construct a Qualified Restriction.
                    idA = source.identity.value
                    idB = node.identity.value
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION_OPERANDS', idA, idB))

            # SOURCE => ROLE EXPRESSION

            elif source.identity is Identity.Role:

                # We can connect a Role in input only if there is no other input or if the
                # other input is a Concept and the node specifies a Qualified Restriction.
                node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                if node and node.identity is not Identity.Concept:
                    # Not a Qualified Restriction.
                    idA = source.identity.value
                    idB = node.identity.value
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION_OPERANDS', idA, idB))

            # SOURCE => ATTRIBUTE

            elif source.identity is Identity.Attribute:

                if target.restriction is Restriction.Self:
                    # Attributes don't have self.
                    raise SyntaxError(_('SYNTAX_INPUT_DR_ATTRIBUTE_NO_SELF'))

                # We can connect an Attribute in input only if there is no other input or if the
                # other input is a ValueDomain and the node specifies a Qualified Restriction.
                node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                if node and node.identity is not Identity.ValueDomain:
                    # Not a Qualified Restriction.
                    idA = source.identity.value
                    idB = node.identity.value
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION_OPERANDS', idA, idB))

            # SOURCE => VALUE-DOMAIN

            elif source.identity is Identity.ValueDomain:

                if target.restriction is Restriction.Self:
                    # Not a Qualified Restriction.
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION', target.restriction.format()))

                # We can connect a ValueDomain in input only if there is no other input or if the
                # other input is an Attribute and the node specifies a Qualified Restriction.
                node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                if node and node.identity is not Identity.Attribute:
                    # Not a Qualified Restriction.
                    idA = source.identity.value
                    idB = node.identity.value
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION_OPERANDS', idA, idB))

        elif target.type() is Item.RangeRestrictionNode:

            #############################################
            # TARGET = RANGE RESTRICTION
            #################################

            if len(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge)) >= 2:
                # Range Restriction node can have at most 2 inputs.
                raise SyntaxError(_('SYNTAX_INPUT_TOO_MANY_OPERANDS', target.name))

            supported = {Identity.Concept, Identity.Attribute, Identity.Role, Identity.ValueDomain}
            if source.identity is not Identity.Neutral and source.identity not in supported:
                # Range Restriction node takes as input:
                #  - Role => OWL 2 ObjectPropertyExpression
                #  - Attribute => OWL 2 DataPropertyExpression
                #  - Concept => Qualified Existential/Universal Role Restriction
                #  - ValueDomain => Qualified Existential Data Restriction
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, source.identity.value))

            if source.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.RoleChainNode}:
                # Exclude incompatible sources: not that while RoleChain has a correct identity
                # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                raise SyntaxError(_('SYNTAX_INPUT_INVALID_OPERAND', target.name, source.name))

            # SOURCE => CONCEPT EXPRESSION || NEUTRAL

            if source.identity in {Identity.Concept, Identity.Neutral}:

                # We can connect a Concept in input iff there is no other input or if the other input is a Role.
                node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                if node and node.identity is not Identity.Role:
                    # We found another input on this node which is not a Role
                    # so we can't construct a Qualified Restriction.
                    idA = source.identity.value
                    idB = node.identity.value
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION_OPERANDS', idA, idB))

            # SOURCE => ROLE EXPRESSION

            if source.identity is Identity.Role:

                # We can connect a Role in input only if there is no other input or if the
                # other input is a Concept and the node specifies a Qualified Restriction.
                node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                if node and node.identity is not Identity.Concept:
                    # Not a Qualified Restriction.
                    idA = source.identity.value
                    idB = node.identity.value
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION_OPERANDS', idA, idB))

            # SOURCE => ATTRIBUTE NODE

            elif source.identity is Identity.Attribute:

                if target.restriction is Restriction.Self:
                    # Attributes don't have self.
                    raise SyntaxError(_('SYNTAX_INPUT_DR_ATTRIBUTE_NO_SELF'))

                # We can connect an Attribute in input only if there is no other input or if the
                # other input is a ValueDomain and the node specifies a Qualified Restriction.
                node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                if node and node.identity is not Identity.ValueDomain:
                    # Not a Qualified Restriction.
                    idA = source.identity.value
                    idB = node.identity.value
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION_OPERANDS', idA, idB))

            # SOURCE => VALUE-DOMAIN

            elif source.identity is Identity.ValueDomain:

                # We can connect a ValueDomain in input only if there is no other input or if the
                # other input is an Attribute and the node specifies a Qualified Restriction.
                node = first(target.incomingNodes(lambda x: x.type() is Item.InputEdge and x is not edge))
                if node and node.identity is not Identity.Attribute:
                    # Not a Qualified Restriction.
                    idA = source.identity.value
                    idB = node.identity.value
                    raise SyntaxError(_('SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION_OPERANDS', idA, idB))

    @staticmethod
    def membership(source, edge, target):
        """
        Validates the membership assertion between the given source and the given target.
        :type source: AbstractNode
        :type edge: MembershipEdge
        :type target: AbstractNode
        :raise SyntaxError: if the connection is not valid.
        """
        if source is target:
            # Self connection is forbidden.
            raise SyntaxError(_('SYNTAX_SELF_CONNECTION'))

        if source.identity is not Identity.Instance and source.type() is not Item.PropertyAssertionNode:
            # The source of the edge must be one of Instance or a Property Assertion node.
            raise SyntaxError(_('SYNTAX_MEMBERSHIP_INVALID_SOURCE', source.identity.value))

        if target.identity is not Identity.Concept and target.type() not in {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}:
            # The target of the edge must be a ClassExpression, ObjectPropertyExpression or DataPropertyExpression.
            raise SyntaxError(_('SYNTAX_MEMBERSHIP_INVALID_TARGET', target.name))

        if source.identity is Identity.Instance:

            if target.identity is not Identity.Concept:
                # If the source of the edge is an Instance it means that we are trying to construct a
                # ClassAssertion and so the target of the edge MUST be a class expression.
                # OWL 2: ClassAssertion(axiomAnnotations ClassExpression Individual)
                raise SyntaxError(_('SYNTAX_MEMBERSHIP_INVALID_ASSERTION_TARGET', 'Concept', target.identity.value))

        if source.type() is Item.PropertyAssertionNode:

            if source.identity is Identity.RoleInstance and target.type() not in {Item.RoleNode, Item.RoleInverseNode}:
                # If the source of the edge is a Role Instance then we MUST target a Role expression.
                raise SyntaxError(_('SYNTAX_MEMBERSHIP_INVALID_ASSERTION_TARGET', 'Role', target.name))

            if source.identity is Identity.AttributeInstance and target.type() is not Item.AttributeNode:
                # If the source of the edge is an Attribute Instance then we MUST target an Attribute.
                raise SyntaxError(_('SYNTAX_MEMBERSHIP_INVALID_ASSERTION_TARGET', 'Attribute', target.name))

    #############################################
    #   INTERFACE
    #################################

    def run(self, source, edge, target):
        """
        Run the validation algorithm on the given triple and generates the SyntaxValidationResult instance.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        """
        try:
            func = self.funcForEdge[edge.type()]
            func(source, edge, target)
        except SyntaxError as e:
            self.result = SyntaxValidationResult(source, edge, target, False, e.msg)
        else:
            self.result = SyntaxValidationResult(source, edge, target, True)