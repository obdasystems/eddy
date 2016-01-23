# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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


from eddy.core.datatypes import Item, Identity, Restriction
from eddy.core.syntax.common import AbstractValidator


class OWLValidator(AbstractValidator):
    """
    This class can be used to validate Graphol triples according to the OWL2RL profile.
    """
    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def check(self, source, edge, target):
        """
        Validate the given triple.
        Will return True if the triple is valid, False otherwise.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        :rtype: bool
        """
        if source is target:
            # Self connection is not valid.
            return False

        if edge.isItem(Item.InclusionEdge):

            ############################################################################################################
            #                                                                                                          #
            #   INCLUSION EDGE                                                                                         #
            #                                                                                                          #
            ############################################################################################################

            if Identity.Neutral not in {source.identity, target.identity} and source.identity is not target.identity:
                # If neither of the endpoints is NEUTRAL and the two nodes are specifying
                # a different identity, then we can't create an ISA between the nodes.
                return False

        elif edge.isItem(Item.InputEdge):

            ############################################################################################################
            #                                                                                                          #
            #   INPUT EDGE                                                                                             #
            #                                                                                                          #
            ############################################################################################################

            if not target.constructor:
                # Input edges can only target constructor nodes.
                return False

            if target.isItem(Item.ComplementNode, Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode):

                ########################################################################################################
                #                                                                                                      #
                #   TARGET IN { COMPLEMENT, DISJOINT UNION, INTERSECTION, UNION }                                      #
                #                                                                                                      #
                ########################################################################################################

                if source.identity not in target.identities:
                    # Source node identity is not supported by this node despite the currently set identity.
                    return False

                if source.isItem(Item.ValueRestrictionNode):
                    # Exclude unsupported nodes despite identity matching.
                    return False

                if Identity.Neutral not in {source.identity, target.identity} and source.identity is not target.identity:
                    # Both are non neutral and we have identity mismatch.
                    return False

                ########################################################################################################
                #                                                                                                      #
                #   TARGET = COMPLEMENT                                                                                #
                #                                                                                                      #
                ########################################################################################################

                if target.isItem(Item.ComplementNode):

                    if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) > 0:
                        # The Complement operator may have at most one node connected to it.
                        return False

                    # See if the source of the node matches an ObjectPropertyExpression ({Role, RoleInv}) or a
                    # DataPropertyExpression (Attribute). If that's the case check for the node not to have any
                    # outgoing Input edge: the only supported expression are NegaiveObjectPropertyAssertion,
                    # R1 ISA NOT R2, and NegativeDataPropertyAssertion, A1 ISA NOT A2. This prevents the connection
                    # of Role expressions to Complement nodes that are given as inputs to Enumeration, Union and
                    # Disjoint Union operatore nodes.
                    if source.isItem(Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode) and \
                        len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x.source is target)) > 0:
                        # If the source of the node is a Role (ObjectPropertyExpression => chain is not included)
                        # check for the node not to have any outgoing Input edge: the only supported expression
                        # is `R1 ISA NOT R2` (this prevents the connection of Role expressions to Complement nodes
                        # that are given as inputs to Enumeration, Union and Disjoint Union operatore nodes.
                        return False

            elif target.isItem(Item.EnumerationNode):

                ########################################################################################################
                #                                                                                                      #
                #   TARGET = ENUMERATION                                                                               #
                #                                                                                                      #
                ########################################################################################################

                if not source.isItem(Item.IndividualNode):
                    # Enumeration operator (oneOf) takes as inputs individuals or literals, both represented by the
                    # Individual node, and has the job of composing a set if individuals (either Concept or DataRange,
                    # but not both together).
                    return False

                if target.identity is Identity.Unknown:
                    # Target node has an unkown identity: we do not allow the connection => the user MUST fix the
                    # error first and then try to create again the connection (this should never happen actually).
                    return False

                if target.identity is not Identity.Neutral:
                    # Target node identity has been computed already so check for identity mismatch
                    if source.identity is Identity.Individual and target.identity is Identity.DataRange or \
                        source.identity is Identity.Literal and target.identity is Identity.Concept:
                        # Identity mismatch.
                        return False

            elif target.isItem(Item.RoleInverseNode):

                ########################################################################################################
                #                                                                                                      #
                #   TARGET = ROLE INVERSE                                                                              #
                #                                                                                                      #
                ########################################################################################################

                if not source.isItem(Item.RoleNode):
                    # The Role Inverse operator takes as input a role and constructs its inverse by switching
                    # domain and range of the role. Assume to have a Role labelled 'is_owner_of' whose instances
                    # are {(o1,o2), (o1,o3), (o4,o5)}: connecting this Role in input to a Role Inverse node will
                    # construct a new Role whose instances are {(o2,o1), (o3,o1), (o5,o4)}.
                    return False

                if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) > 0:
                    # The Role Inverse operator may have at most one Role node connected to it: if we need to
                    # define multiple Role inverse we would need to use multiple Role Inverse operator nodes.
                    return False

            elif target.isItem(Item.RoleChainNode):

                ########################################################################################################
                #                                                                                                      #
                #   TARGET = ROLE CHAIN                                                                                #
                #                                                                                                      #
                ########################################################################################################

                if not source.isItem(Item.RoleNode, Item.RoleInverseNode):
                    # The Role Chain operator constructs a concatenation of roles. Assume to have 2 Role nodes
                    # defined as 'lives_in_region' and 'region_in_country': if {(o1, o2), (o3, o4)} is the
                    # instance of 'lives_in_region' and {(o2, o6)} is the instance of 'region_in_country', then
                    # {(o1, o6)} is the instance of the chain, which would match another Role 'lives_in_country'.
                    # ObjectPropertyExpression := ObjectProperty | InverseObjectProperty => we need to match only
                    # Role nodes and Role Inverse nodes as sources of our edge (it's not possible to create a chain
                    # of chains, despite the identity matches Role in both expressions).
                    return False

            elif target.isItem(Item.DatatypeRestrictionNode):

                ########################################################################################################
                #                                                                                                      #
                #   TARGET = DATATYPE RESTRICTION                                                                      #
                #                                                                                                      #
                ########################################################################################################

                if not source.isItem(Item.ValueDomainNode, Item.ValueRestrictionNode):
                    # The DatatypeRestriction node is used to compose complex datatypes and
                    # accepts as inputs a Value-Domain node together with N Value-Restriction
                    # nodes to compose the OWL 2 equivalent DatatypeRestriction.
                    return False

                if source.isItem(Item.ValueDomainNode):
                    if len(target.incomingNodes(filter_on_edges=lambda x: x.isItem(Item.InputEdge) and x is not edge,
                                                filter_on_nodes=lambda x: x.isItem(Item.ValueDomainNode))) > 0:
                        # The Value-Domain has already been attached to the DatatypeRestriction.
                        return False

            elif target.isItem(Item.PropertyAssertionNode):

                ########################################################################################################
                #                                                                                                      #
                #   TARGET = PROPERTY ASSERTION                                                                        #
                #                                                                                                      #
                ########################################################################################################

                if not source.isItem(Item.IndividualNode):
                    # Property Assertion operators accepts only Individual nodes as input: they are
                    # used to construct ObjectPropertyAssertion and DataPropertyAssertion axioms.
                    return False

                if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) >= 2:
                    # At most 2 Individual nodes can be connected to a PropertyAssertion node. As an example
                    # we can construct ObjectPropertyAssertion(presiede M.Draghi BCE) where the individuals
                    # are identified by M.Draghi and BCE, or DataPropertyAssertion(nome M.Draghi "Mario") where
                    # the individuals are identified by M.Draghi and "Mario".
                    return False

                if source.identity is Identity.Literal and \
                    len(target.incomingNodes(filter_on_edges=lambda x: x.isItem(Item.InputEdge) and x is not edge,
                                             filter_on_nodes=lambda x: x.identity is Identity.Literal)) > 0:
                    # At most one Literal can be given as input (2 Individuals | 1 Individual + 1 Literal)
                    return False

                # See if the source we are connecting to the Link is consistent with the instanceOf expression
                # if there is such expression (else we do not care since we check this in the instanceOf edge.
                node = next(iter(target.outgoingNodes(lambda x: x.isItem(Item.InstanceOfEdge))), None)

                if node:

                    if node.isItem(Item.RoleNode, Item.RoleInverseNode):
                        if source.identity is Identity.Literal:
                            # We are constructing an ObjectPropertyAssertion expression so we can't connect a Literal.
                            return False

                    if node.isItem(Item.AttributeNode):
                        if source.identity is Identity.Individual and \
                            len(target.incomingNodes(filter_on_edges=lambda x: x.isItem(Item.InputEdge) and x is not edge,
                                                     filter_on_nodes=lambda x: x.identity is Identity.Individual)) > 0:
                            # We are constructing a DataPropertyAssertion and so we can't have more than 1 Individual.
                            return False

            elif target.isItem(Item.DomainRestrictionNode):

                ########################################################################################################
                #                                                                                                      #
                #   TARGET = DOMAIN RESTRICTION                                                                        #
                #                                                                                                      #
                ########################################################################################################

                if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) >= 2:
                    # Domain Restriction node can have at most 2 inputs.
                    return False

                if source.identity not in {Identity.Neutral, Identity.Concept, Identity.Attribute, Identity.Role, Identity.DataRange}:
                    # Domain Restriction node takes as input:
                    #  - Role => OWL 2 ObjectPropertyExpression
                    #  - Attribute => OWL 2 DataPropertyExpression
                    #  - Concept => Qualified Existential/Universal Role Restriction
                    #  - DataRange => Qualified Existential Data Restriction
                    return False

                if source.isItem(Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.RoleChainNode):
                    # Exclude incompatible sources: note that while RoleChain has a correct identity
                    # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                    return False

                # SOURCE => CONCEPT EXPRESSION || NEUTRAL

                if source.identity in {Identity.Concept, Identity.Neutral}:

                    if target.restriction is Restriction.Self:
                        # Not a Qualified Restriction.
                        return False

                    # We can connect a Concept in input only if there is no other input or if the other input is a Role.
                    node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                    if node:
                        if node.identity is not Identity.Role:
                            # We found another input on this node which is not a Role
                            # so we can't construct a Qualified Restriction.
                            return False

                # SOURCE => ROLE EXPRESSION

                elif source.identity is Identity.Role:

                    # We can connect a Role in input only if there is no other input or if the
                    # other input is a Concept and the node specifies a Qualified Restriction.
                    node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                    if node:
                        if node.identity is not Identity.Concept or target.restriction is Restriction.Self:
                            # Not a Qualified Restriction.
                            return False

                # SOURCE => ATTRIBUTE

                elif source.identity is Identity.Attribute:

                    if target.restriction is Restriction.Self:
                        # Attributes don't have edge.
                        return False

                    # We can connect an Attribute in input only if there is no other input or if the
                    # other input is a DataRange and the node specifies a Qualified Restriction.
                    node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                    if node:
                        if node.identity is not Identity.DataRange:
                            # Not a Qualified Restriction.
                            return False

                # SOURCE => DATARANGE

                elif source.identity is Identity.DataRange:

                    if target.restriction is Restriction.Self:
                        # Not a Qualified Restriction.
                        return False

                    # We can connect a DataRange in input only if there is no other input or if the
                    # other input is an Attribute and the node specifies a Qualified Restriction.
                    node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                    if node:
                        if node.identity is not Identity.Attribute:
                            # Not a Qualified Restriction.
                            return False

            elif target.isItem(Item.RangeRestrictionNode):

                ########################################################################################################
                #                                                                                                      #
                #   TARGET = RANGE RESTRICTION                                                                         #
                #                                                                                                      #
                ########################################################################################################

                if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) >= 2:
                    # Range Restriction node can have at most 2 inputs.
                    return False

                if source.identity not in {Identity.Neutral, Identity.Concept, Identity.Attribute, Identity.Role, Identity.DataRange}:
                    # Range Restriction node takes as input:
                    #  - Role => OWL 2 ObjectPropertyExpression
                    #  - Attribute => OWL 2 DataPropertyExpression
                    #  - Concept => Qualified Existential/Universal Role Restriction
                    #  - DataRange => Qualified Existential Data Restriction
                    return False

                if source.isItem(Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.RoleChainNode):
                    # Exclude incompatible sources: not that while RoleChain has a correct identity
                    # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                    return False

                # SOURCE => CONCEPT EXPRESSION || NEUTRAL

                if source.identity in {Identity.Concept, Identity.Neutral}:

                    if target.restriction is Restriction.Self:
                        # Not a Qualified Restriction.
                        return False

                    # We can connect a Concept in input only if there is no other input or if the other input is a Role.
                    node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                    if node:
                        if node.identity is not Identity.Role:
                            # We found another input on this node which is not a Role
                            # so we can't construct a Qualified Restriction.
                            return False

                # SOURCE => ROLE EXPRESSION

                elif source.identity is Identity.Role:

                    # We can connect a Role in input only if there is no other input or if the
                    # other input is a Concept and the node specifies a Qualified Restriction.
                    node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                    if node:
                        if node.identity is not Identity.Concept or target.restriction is Restriction.Self:
                            # Not a Qualified Restriction.
                            return False

                # SOURCE => ATTRIBUTE NODE

                elif source.identity is Identity.Attribute:

                    if target.restriction is not Restriction.Exists:
                        # RangeRestriction of Attribute => Restriction.Exists
                        return False

                    # We can connect an Attribute in input only if there is no other input or if the
                    # other input is a DataRange and the node specifies a Qualified Restriction.
                    node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                    if node:
                        if node.identity is not Identity.DataRange:
                            # Not a Qualified Restriction.
                            return False

                # SOURCE => DATARANGE

                elif source.identity is Identity.DataRange:

                    if target.restriction is not Restriction.Exists:
                        # Qualified RangeRestriction of Attribute => Restriction.Exists
                        return False

                    # We can connect a DataRange in input only if there is no other input or if the
                    # other input is an Attribute and the node specifies a Qualified Restriction.
                    node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                    if node:
                        if node.identity is not Identity.Attribute:
                            # Not a Qualified Restriction.
                            return False

        elif edge.isItem(Item.InstanceOfEdge):

            ############################################################################################################
            #                                                                                                          #
            #   INSTANCE OF EDGE                                                                                       #
            #                                                                                                          #
            ############################################################################################################

            if source.identity not in {Identity.Individual, Identity.Link}:
                # The source of the edge must be one of Individual or Link.
                return False

            if len(source.outgoingNodes(lambda x: x.isItem(Item.InstanceOfEdge) and x is not edge)) > 0:
                # The source node MUST be instanceOf at most of one construct.
                return False

            if source.identity is Identity.Individual and target.identity is not Identity.Concept:
                # If the source of the edge is an Individual it means that we are trying to construct a ClassAssertion
                # construct, and so the target of the edge MUST be an axiom identified as Concept (Atomic or General).
                # OWL 2 syntax: ClassAssertion(axiomAnnotations ClassExpression Individual)
                return False

            if source.identity is Identity.Link:

                if not target.isItem(Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode):
                    # If the source of the edge is a Link then the target of the edge MUST be the
                    # OWL 2 equivalent of ObjectPropertyExpression and DataPropertyExpression.
                    return False

                if target.isItem(Item.RoleNode, Item.RoleInverseNode):
                    # If the target of the edge is a Role expression then we need to check
                    # not to have Literals in input to the source node (which is a Link).
                    # OWL 2 syntax: ObjectPropertyAssertion(axiomAnnotations ObjectPropertyExpression Individual Individual)
                    if len(source.incomingNodes(filter_on_edges=lambda x: x.isItem(Item.InputEdge),
                                                filter_on_nodes=lambda x: x.identity is Identity.Literal)) > 0:
                        return False

                if target.isItem(Item.AttributeNode):
                    # If the target of the edge is an Attribute expression then we need to check
                    # not to have 2 Individuals as input to the source node (which is a link).
                    # OWL 2 syntax: DataPropertyAssertion(axiomAnnotations DataPropertyExpression Individual Literal)
                    if len(source.incomingNodes(filter_on_edges=lambda x: x.isItem(Item.InputEdge),
                                                filter_on_nodes=lambda x: x.identity is Identity.Individual)) > 1:
                        return False

        return True