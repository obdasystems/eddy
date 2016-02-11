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
from eddy.core.functions import rCut
from eddy.core.syntax.common import AbstractValidator, ValidationResult


class OWL2RLValidator(AbstractValidator):
    """
    This class can be used to validate Graphol triples according to the OWL2RL profile.
    """
    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def run(self, source, edge, target):
        """
        Run the validation algorithm on the given triple and generates the ValidationResult instance.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        """
        try:

            if source is target:
                # Self connection is not valid.
                raise SyntaxError('Self connection is not valid')

            if edge.isItem(Item.InclusionEdge):

                ########################################################################################################
                #                                                                                                      #
                #   INCLUSION EDGE                                                                                     #
                #                                                                                                      #
                ########################################################################################################

                if Identity.Neutral not in {source.identity, target.identity} and source.identity is not target.identity:
                    # If neither of the endpoints is NEUTRAL and the two nodes are specifying
                    # a different identity, then we can't create an ISA between the nodes.
                    idA = source.identity.label
                    idB = target.identity.label
                    raise SyntaxError('Type mismatch: inclusion between {} and {}'.format(idA, idB))

                if Identity.DataRange in {source.identity, target.identity} and not source.isItem(Item.RangeRestrictionNode):
                    # If we are creating an ISA between 2 DataRange check whether the source of the node is a
                    # range restriction: we allow to create an inclusion only if will express a DataPropertyRange.
                    idA = source.identity.label
                    idB = target.identity.label
                    raise SyntaxError('Type mismatch: inclusion between {} and {}'.format(idA, idB))

                if Identity.Individual in {source.identity, target.identity}:
                    # Individual doesn't match OWL ClassExpression so we can't allow the connection.
                    idA = source.identity.label
                    idB = target.identity.label
                    raise SyntaxError('Type mismatch: inclusion between {} and {}'.format(idA, idB))

            elif edge.isItem(Item.InputEdge):

                ########################################################################################################
                #                                                                                                      #
                #   INPUT EDGE                                                                                         #
                #                                                                                                      #
                ########################################################################################################

                if not target.constructor:
                    # Input edges can only target constructor nodes.
                    raise SyntaxError('Input edges can only target constructor nodes')

                if target.isItem(Item.ComplementNode, Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode):

                    ####################################################################################################
                    #                                                                                                  #
                    #   TARGET IN { COMPLEMENT, DISJOINT UNION, INTERSECTION, UNION }                                  #
                    #                                                                                                  #
                    ####################################################################################################

                    if source.identity not in target.identities:
                        # Source node identity is not supported by this node despite the currently set identity.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.label))

                    if source.isItem(Item.ValueRestrictionNode):
                        # Exclude invalid nodes despite identity matching.
                        raise SyntaxError('Invalid target: {}'.format(target.name))

                    ####################################################################################################
                    #                                                                                                  #
                    #   TARGET = COMPLEMENT                                                                            #
                    #                                                                                                  #
                    ####################################################################################################

                    if target.isItem(Item.ComplementNode):

                        if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) > 0:
                            # The Complement operator may have at most one node connected to it.
                            raise SyntaxError('Too many inputs to {}'.format(target.name))

                        if source.isItem(Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode):

                            # See if the source of the node matches an ObjectPropertyExpression ({Role, RoleInv}) or a
                            # DataPropertyExpression (Attribute). If that's the case check for the node not to have any
                            # outgoing Input edge: the only supported expression are NegativeObjectPropertyAssertion,
                            # R1 ISA NOT R2, and NegativeDataPropertyAssertion, A1 ISA NOT A2. This prevents the connection
                            # of Role expressions to Complement nodes that are given as inputs to Enumeration, Union and
                            # Disjoint Union operatore nodes.
                            if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x.source is target)) > 0:
                                raise SyntaxError('Invalid negative {} expression'.format(source.identity.label))

                    else:

                        ################################################################################################
                        #                                                                                              #
                        #   TARGET IN { DISJOINT UNION, INTERSECTION, UNION }                                          #
                        #                                                                                              #
                        ################################################################################################

                        if Identity.Neutral not in {source.identity, target.identity} and source.identity is not target.identity:
                            # Both are non neutral and we have identity mismatch.
                            idA = source.identity.label
                            idB = target.identity.label
                            composition = rCut(target.name, ' node')
                            raise SyntaxError('Type mismatch: {} between {} and {}'.format(composition, idA, idB))

                elif target.isItem(Item.EnumerationNode):

                    ####################################################################################################
                    #                                                                                                  #
                    #   TARGET = ENUMERATION                                                                           #
                    #                                                                                                  #
                    ####################################################################################################

                    if not source.isItem(Item.IndividualNode):
                        # Enumeration operator (oneOf) takes as inputs individuals or literals, both represented
                        # by the Individual node, and has the job of composing a set if individuals (either Concept
                        # or DataRange, but not both together).
                        name = source.identity.label if source.identity is not Identity.Neutral else source.name
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, name))

                    if target.identity is Identity.Unknown:
                        # Target node has an unkown identity: we do not allow the connection => the user MUST fix the
                        # error first and then try to create again the connection (this should never happen actually).
                        raise SyntaxError('Target node has an invalid identity: {}'.format(target.identity.label))

                    if target.identity is not Identity.Neutral:

                        if source.identity is Identity.Individual and target.identity is Identity.DataRange:
                            raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.label))

                        if source.identity is Identity.Literal and target.identity is Identity.Concept:
                            raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.label))

                elif target.isItem(Item.RoleInverseNode):

                    ####################################################################################################
                    #                                                                                                  #
                    #   TARGET = ROLE INVERSE                                                                          #
                    #                                                                                                  #
                    ####################################################################################################

                    if not source.isItem(Item.RoleNode):
                        # The Role Inverse operator takes as input a role and constructs its inverse by switching
                        # domain and range of the role. Assume to have a Role labelled 'is_owner_of' whose instances
                        # are {(o1,o2), (o1,o3), (o4,o5)}: connecting this Role in input to a Role Inverse node will
                        # construct a new Role whose instances are {(o2,o1), (o3,o1), (o5,o4)}.
                        raise SyntaxError('Role Inverse accepts only a Role node as input')

                    if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) > 0:
                        # The Role Inverse operator may have at most one Role node connected to it: if we need to
                        # define multiple Role inverse we would need to use multiple Role Inverse operator nodes.
                        raise SyntaxError('Too many inputs to {}'.format(target.name))

                elif target.isItem(Item.RoleChainNode):

                    ####################################################################################################
                    #                                                                                                  #
                    #   TARGET = ROLE CHAIN                                                                            #
                    #                                                                                                  #
                    ####################################################################################################

                    if not source.isItem(Item.RoleNode, Item.RoleInverseNode):
                        # The Role Chain operator constructs a concatenation of roles. Assume to have 2 Role nodes
                        # defined as 'lives_in_region' and 'region_in_country': if {(o1, o2), (o3, o4)} is the
                        # instance of 'lives_in_region' and {(o2, o6)} is the instance of 'region_in_country', then
                        # {(o1, o6)} is the instance of the chain, which would match another Role 'lives_in_country'.
                        # ObjectPropertyExpression := ObjectProperty | InverseObjectProperty => we need to match only
                        # Role nodes and Role Inverse nodes as sources of our edge (it's not possible to create a chain
                        # of chains, despite the identity matches Role in both expressions).
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.name))

                elif target.isItem(Item.DatatypeRestrictionNode):

                    ####################################################################################################
                    #                                                                                                  #
                    #   TARGET = DATATYPE RESTRICTION                                                                  #
                    #                                                                                                  #
                    ####################################################################################################

                    if not source.isItem(Item.ValueDomainNode, Item.ValueRestrictionNode):
                        # The DatatypeRestriction node is used to compose complex datatypes and
                        # accepts as inputs a Value-Domain node together with N Value-Restriction
                        # nodes to compose the OWL 2 equivalent DatatypeRestriction.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.name))

                    if source.isItem(Item.ValueDomainNode):

                        f1 = lambda x: x.isItem(Item.InputEdge) and x is not edge
                        f2 = lambda x: x.isItem(Item.ValueDomainNode)
                        if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                            # The Value-Domain has already been attached to the DatatypeRestriction.
                            raise SyntaxError('Too many value-domain nodes in input to {}'.format(target.name))

                    # We need to check whether the DatatypeRestriction node has already datatype
                    # inferred: if that's the case and the datatype doesn't match the datatype of
                    # the source node, we deny the connection to prevent inconsistencies.
                    f1 = lambda x: x.isItem(Item.InputEdge) and x is not edge
                    f2 = lambda x: x.isItem(Item.ValueDomainNode, Item.ValueRestrictionNode) and x is not source
                    collection = target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
                    if collection:
                        datatype = next(iter(collection)).datatype
                        if  datatype is not source.datatype:
                            d1 = source.datatype.value
                            d2 = datatype.value
                            raise SyntaxError('Datatype mismatch: restriction between {} and {}'.format(d1, d2))

                elif target.isItem(Item.PropertyAssertionNode):

                    ####################################################################################################
                    #                                                                                                  #
                    #   TARGET = PROPERTY ASSERTION                                                                    #
                    #                                                                                                  #
                    ####################################################################################################

                    if not source.isItem(Item.IndividualNode):
                        # Property Assertion operators accepts only Individual nodes as input: they are
                        # used to construct ObjectPropertyAssertion and DataPropertyAssertion axioms.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.label))

                    if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) >= 2:
                        # At most 2 Individual nodes can be connected to a PropertyAssertion node. As an example
                        # we can construct ObjectPropertyAssertion(presiede M.Draghi BCE) where the individuals
                        # are identified by M.Draghi and BCE, or DataPropertyAssertion(nome M.Draghi "Mario") where
                        # the individuals are identified by M.Draghi and "Mario".
                        raise SyntaxError('Too many inputs to {}'.format(target.name))

                    if source.identity is Identity.Literal:

                        f1 = lambda x: x.isItem(Item.InputEdge) and x is not edge
                        f2 = lambda x: x.identity is Identity.Literal
                        if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                            # At most one Literal can be given as input (2 Individuals | 1 Individual + 1 Literal)
                            raise SyntaxError('Too many literals in input to {}'.format(target.name))

                    # See if the source we are connecting to the Link is consistent with the instanceOf expression
                    # if there is such expression (else we do not care since we check this in the instanceOf edge.
                    node = next(iter(target.outgoingNodes(lambda x: x.isItem(Item.InstanceOfEdge))), None)

                    if node:

                        if node.isItem(Item.RoleNode, Item.RoleInverseNode):

                            if source.identity is Identity.Literal:
                                # We are constructing an ObjectPropertyAssertion expression so we can't connect a Literal.
                                raise SyntaxError('Invalid input to Role assertion: Literal')

                        if node.isItem(Item.AttributeNode):

                            if source.identity is Identity.Individual:

                                f1 = lambda x: x.isItem(Item.InputEdge) and x is not edge
                                f2 = lambda x: x.identity is Identity.Individual
                                if len(target.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                                    # We are constructing a DataPropertyAssertion and so we can't have more than 1 Individual.
                                    raise SyntaxError('Too many individuals in input to Attribute assertion')

                elif target.isItem(Item.DomainRestrictionNode):

                    ####################################################################################################
                    #                                                                                                  #
                    #   TARGET = DOMAIN RESTRICTION                                                                    #
                    #                                                                                                  #
                    ####################################################################################################

                    if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) >= 2:
                        # Domain Restriction node can have at most 2 inputs.
                        raise SyntaxError('Too many inputs to {}'.format(target.name))

                    if source.identity not in {Identity.Neutral, Identity.Concept, Identity.Attribute, Identity.Role, Identity.DataRange}:
                        # Domain Restriction node takes as input:
                        #  - Role => OWL 2 ObjectPropertyExpression
                        #  - Attribute => OWL 2 DataPropertyExpression
                        #  - Concept => Qualified Existential/Universal Role Restriction
                        #  - DataRange => Qualified Existential Data Restriction
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.label))

                    if source.isItem(Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.RoleChainNode):
                        # Exclude incompatible sources: note that while RoleChain has a correct identity
                        # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.name))

                    # SOURCE => CONCEPT EXPRESSION || NEUTRAL

                    if source.identity in {Identity.Concept, Identity.Neutral}:

                        if target.restriction is Restriction.Self:
                            # Not a Qualified Restriction.
                            raise SyntaxError('Invalid restriction (self) for qualified restriction')

                        # We can connect a Concept in input only if there is no other input or if the other input is a Role.
                        node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                        if node and node.identity is not Identity.Role:
                            # We found another input on this node which is not a Role
                            # so we can't construct a Qualified Restriction.
                            idA = source.identity.label
                            idB = node.identity.label
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => ROLE EXPRESSION

                    elif source.identity is Identity.Role:

                        # We can connect a Role in input only if there is no other input or if the
                        # other input is a Concept and the node specifies a Qualified Restriction.
                        node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                        if node and node.identity is not Identity.Concept:
                            # Not a Qualified Restriction.
                            idA = source.identity.label
                            idB = node.identity.label
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => ATTRIBUTE

                    elif source.identity is Identity.Attribute:

                        if target.restriction is Restriction.Self:
                            # Attributes don't have self.
                            raise SyntaxError('Attributes don\'t have self')

                        # We can connect an Attribute in input only if there is no other input or if the
                        # other input is a DataRange and the node specifies a Qualified Restriction.
                        node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                        if node and node.identity is not Identity.DataRange:
                            # Not a Qualified Restriction.
                            idA = source.identity.label
                            idB = node.identity.label
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => DATARANGE

                    elif source.identity is Identity.DataRange:

                        if target.restriction is Restriction.Self:
                            # Not a Qualified Restriction.
                            raise SyntaxError('Invalid restriction (self) for qualified restriction')

                        # We can connect a DataRange in input only if there is no other input or if the
                        # other input is an Attribute and the node specifies a Qualified Restriction.
                        node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                        if node and node.identity is not Identity.Attribute:
                            # Not a Qualified Restriction.
                            idA = source.identity.label
                            idB = node.identity.label
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                elif target.isItem(Item.RangeRestrictionNode):

                    ####################################################################################################
                    #                                                                                                  #
                    #   TARGET = RANGE RESTRICTION                                                                     #
                    #                                                                                                  #
                    ####################################################################################################

                    if len(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)) >= 2:
                        # Range Restriction node can have at most 2 inputs.
                        raise SyntaxError('Too many inputs to {}'.format(target.name))

                    if source.identity not in {Identity.Neutral, Identity.Concept, Identity.Attribute, Identity.Role, Identity.DataRange}:
                        # Range Restriction node takes as input:
                        #  - Role => OWL 2 ObjectPropertyExpression
                        #  - Attribute => OWL 2 DataPropertyExpression
                        #  - Concept => Qualified Existential/Universal Role Restriction
                        #  - DataRange => Qualified Existential Data Restriction
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.label))

                    if source.isItem(Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.RoleChainNode):
                        # Exclude incompatible sources: not that while RoleChain has a correct identity
                        # it is excluded because it doesn't represent the OWL 2 ObjectPropertyExpression.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.name))

                    # SOURCE => CONCEPT EXPRESSION || NEUTRAL

                    if source.identity in {Identity.Concept, Identity.Neutral}:

                        # We can connect a Concept in input only if there is no other input or if the other input is a Role.
                        node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                        if node and node.identity is not Identity.Role:
                            # We found another input on this node which is not a Role
                            # so we can't construct a Qualified Restriction.
                            idA = source.identity.label
                            idB = node.identity.label
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => ROLE EXPRESSION

                    if source.identity is Identity.Role:

                        # We can connect a Role in input only if there is no other input or if the
                        # other input is a Concept and the node specifies a Qualified Restriction.
                        node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                        if node and node.identity is not Identity.Concept:
                            # Not a Qualified Restriction.
                            idA = source.identity.label
                            idB = node.identity.label
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => ATTRIBUTE NODE

                    elif source.identity is Identity.Attribute:

                        # We can connect an Attribute in input only if there is no other input or if the
                        # other input is a DataRange and the node specifies a Qualified Restriction.
                        node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                        if node and node.identity is not Identity.DataRange:
                            # Not a Qualified Restriction.
                            idA = source.identity.label
                            idB = node.identity.label
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

                    # SOURCE => DATARANGE

                    elif source.identity is Identity.DataRange:

                        # We can connect a DataRange in input only if there is no other input or if the
                        # other input is an Attribute and the node specifies a Qualified Restriction.
                        node = next(iter(target.incomingNodes(lambda x: x.isItem(Item.InputEdge) and x is not edge)), None)
                        if node and node.identity is not Identity.Attribute:
                            # Not a Qualified Restriction.
                            idA = source.identity.label
                            idB = node.identity.label
                            raise SyntaxError('Invalid inputs ({} + {}) for qualified restriction'.format(idA, idB))

            elif edge.isItem(Item.InstanceOfEdge):

                ########################################################################################################
                #                                                                                                      #
                #   INSTANCE OF EDGE                                                                                   #
                #                                                                                                      #
                ########################################################################################################

                if source.identity not in {Identity.Individual, Identity.Link}:
                    # The source of the edge must be one of Individual or Link.
                    raise SyntaxError('Invalid source for instanceOf edge: {}'.format(source.identity.label))

                if len(source.outgoingNodes(lambda x: x.isItem(Item.InstanceOfEdge) and x is not edge)) > 0:
                    # The source node MUST be instanceOf at most of one construct.
                    raise SyntaxError('Too many outputs from {}'.format(source.name))

                if source.identity is Identity.Individual and target.identity is not Identity.Concept:
                    # If the source of the edge is an Individual it means that we are trying to construct a ClassAssertion
                    # construct, and so the target of the edge MUST be an axiom identified as Concept (Atomic or General).
                    # OWL 2: ClassAssertion(axiomAnnotations ClassExpression Individual)
                    raise SyntaxError('Invalid target for Concept assertion: {}'.format(target.identity.label))

                if source.identity is Identity.Link:

                    if not target.isItem(Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode):
                        # If the source of the edge is a Link then the target of the edge MUST be the
                        # OWL 2 equivalent of ObjectPropertyExpression and DataPropertyExpression.
                        raise SyntaxError('Invalid input to {}: {}'.format(target.name, source.identity.label))

                    if target.isItem(Item.RoleNode, Item.RoleInverseNode):
                        # If the target of the edge is a Role expression then we need to check
                        # not to have Literals in input to the source node (which is a Link).
                        # OWL 2: ObjectPropertyAssertion(axiomAnnotations ObjectPropertyExpression Individual Individual)
                        f1 = lambda x: x.isItem(Item.InputEdge)
                        f2 = lambda x: x.identity is Identity.Literal
                        if len(source.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 0:
                            raise SyntaxError('Invalid in input to {} for Role assertion'.format(source.name))

                    if target.isItem(Item.AttributeNode):
                        # If the target of the edge is an Attribute expression then we need to check
                        # not to have 2 Individuals as input to the source node (which is a link).
                        # OWL 2: DataPropertyAssertion(axiomAnnotations DataPropertyExpression Individual Literal)
                        f1 = lambda x: x.isItem(Item.InputEdge)
                        f2 = lambda x: x.identity is Identity.Individual
                        if len(source.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) > 1:
                            raise SyntaxError('Invalid in input to {} for Attribute assertion'.format(source.name))

        except SyntaxError as e:
            self._result = ValidationResult(source, edge, target, False, e.msg)
        else:
            self._result = ValidationResult(source, edge, target, True, 'OK')