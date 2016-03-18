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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from collections import deque

from eddy.core.datatypes import Identity, Item
from eddy.core.functions.misc import partition


def bfs(source, filter_on_edges=None, filter_on_nodes=None, filter_on_visit=None):
    """
    Perform a customized BFS returning a list of nodes ordered according to the visit time.
    The function accepts 3 callable parameters:

        * filter_on_edges: a callable which takes as input an edge and returns True iff the search has to proceed along
                           the edge; if instead the callable returns False, the given edge is excluded from the search.
        * filter_on_nodes: a callable which takes as input a node and returns True iff the search has to take the node
                           into consideration; else the callable MUST return False (NOTE: the node is not included
                           in the returned set of visited nodes, nor its neighbours are being visited, unless they are
                           connected through some other nodes for which the callable returns True).
        * filter_on_visit: a callable which takes as input a node and returns True iff the search algoritm should visit
                           the given node neighbours; else the callable MUST return False (NOTE: the node IS included in
                           the returned set of visited nodes, but its neighbours are not being visited, unless they are
                           connected through some other nodes for which the callable returns True).

    :type source: Node
    :type filter_on_edges: callable
    :type filter_on_nodes callable
    :type filter_on_visit: callable
    :type: list
    """
    f0 = lambda x: True
    f1 = filter_on_edges or f0
    f2 = filter_on_nodes or f0
    f3 = filter_on_visit or f0
    queue = deque([source])
    extend = queue.extend
    ordered = []
    visited = set()
    while queue:
        node = queue.popleft()
        ordered.append(node)
        visited.add(node)
        if f3(node):
            extend([n for n in [e.other(node) for e in node.edges if f1(e)] if n not in visited and f2(n)])
    return ordered


def dfs(source, filter_on_edges=None, filter_on_nodes=None, filter_on_visit=None):
    """
    Perform a customized DFS returning a list of nodes ordered according to the visit time.
    The function accepts 3 callable parameters:

        * filter_on_edges: a callable which takes as input an edge and returns True iff the search has to proceed along
                           the edge; if instead the callable returns False, the given edge is excluded from the search.
        * filter_on_nodes: a callable which takes as input a node and returns True iff the search has to take the node
                           into consideration; else the callable MUST return False (NOTE: the node is not included
                           in the returned set of visited nodes, nor its neighbours are being visited, unless they are
                           connected through some other nodes for which the callable returns True).
        * filter_on_visit: a callable which takes as input a node and returns True iff the search algoritm should visit
                           the given node neighbours; else the callable MUST return False (NOTE: the node IS included in
                           the returned set of visited nodes, but its neighbours are not being visited, unless they are
                           connected through some other nodes for which the callable returns True).

    :type source: Node
    :type filter_on_edges: callable
    :type filter_on_nodes callable
    :type filter_on_visit: callable
    :type: list
    """
    f0 = lambda x: True
    f1 = filter_on_edges or f0
    f2 = filter_on_nodes or f0
    f3 = filter_on_visit or f0
    stack = [source]
    extend = stack.extend
    ordered = []
    visited = set()
    while stack:
        node = stack.pop()
        if node not in visited:
            ordered.append(node)
            visited.add(node)
            if f3(node):
                extend([n for n in [e.other(node) for e in node.edges if f1(e)] if n not in visited and f2(n)])
    return visited


def identify(source):
    """
    Perform node identification by traversing all the nodes in the graph which are directly/indirectly
    connected with the given one. This function will also update the identity of all the other related
    nodes which are specifying a "WEAK" identity.
    :type source: Node
    """
    predicate = lambda x: Identity.Neutral in x.identities
    collection = bfs(source=source, filter_on_visit=predicate)
    generators = partition(predicate, collection)
    excluded = set()
    strong = set(generators[1])
    weak = set(generators[0])

    for node in weak:

        if node.item is Item.EnumerationNode:

            # Enumeration nodes needs to be analyzed separately since they do not inherit an identity
            # from their inputs but they compute it according to the nodes source of the inputs (note
            # that the Enumeration node can have as inputs source only atomic instance/value nodes):
            #
            #   - if it has INDIVIDUALS as inputs => identity is Concept
            #   - if it has VALUES as inputs => identity is ValueDomain
            #
            # We compute the identity for this node: if such identity is not NEUTRAL we put it
            # among the nodes specifying a STRONG identity so it will be excluded later when
            # computing inherited identity: computed identity >>> inherited identity.
            # We will also remove all the individuals used to compute the Enumeration node identity
            # from the STRONG set since they will lead to errors when computing the final identity.

            f1 = lambda x: x.isItem(Item.InputEdge)
            f2 = lambda x: x.isItem(Item.IndividualNode)

            individuals = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
            identity = [n.identity for n in individuals]

            if not identity:
                identity = Identity.Neutral
            elif identity.count(identity[0]) != len(identity):
                identity = Identity.Unknown
            elif identity[0] is Identity.Instance:
                identity = Identity.Concept
            elif identity[0] is Identity.Value:
                identity = Identity.ValueDomain

            node.identity = identity

            if node.identity is not Identity.Neutral:
                strong.add(node)

            for k in individuals:
                strong.discard(k)

        elif node.item is Item.RangeRestrictionNode:

            # RangeRestriction nodes needs to be analyzed separately since they do not inherit an identity
            # from their inputs but they compute it according to the nodes source of the inputs:
            #
            #   - if it has ATTRIBUTES || VALUE DOMAIN as inputs => identity is ValueDomain
            #   - if it has ROLES || CONCEPTS as inputs => identity is Concept
            #
            # We compute the identity for this node: if such identity is not NEUTRAL we put it
            # among the nodes specifying a STRONG identity so it will be excluded later when
            # computing inherited identity: computed identity >>> inherited identity.
            # We will also remove all the nodes used to compute the RangeRestriction node identity
            # from the STRONG set since they will lead to errors when computing the final identity.

            f1 = lambda x: Identity.Concept if x.identity in {Identity.Role, Identity.Concept} else Identity.ValueDomain
            f2 = lambda x: x.isItem(Item.InputEdge) and x.target is node
            f3 = lambda x: x.identity in {Identity.Role,
                                          Identity.Attribute,
                                          Identity.Concept,
                                          Identity.ValueDomain} and Identity.Neutral not in x.identities

            mixed = node.adjacentNodes(filter_on_edges=f2, filter_on_nodes=f3)
            identity = {f1(n) for n in mixed}

            if not identity:
                identity = Identity.Neutral
            elif len(identity) > 1:
                identity = Identity.Unknown
            else:
                identity = identity.pop()

            node.identity = identity

            if node.identity is not Identity.Neutral:
                strong.add(node)

            for k in mixed:
                strong.discard(k)

        elif node.item is Item.PropertyAssertionNode:

            # PropertyAssertion nodes needs to be analyzed separately since they do not inherit an identity
            # identity from their inputs nor from the outgoing instanceOf edge, but they compute it according
            # to the other endpoint of the outgoing instanceOf edge or according to the nodes source of the inputs:
            #
            #   - if it's targeting a Role/RoleInverse node using an instanceOf edge => identity is RoleInstance
            #   - if it's targeting an Attribute node using an instanceOf edge => identity is AttributeInstance
            #
            #   OR
            #
            #   - if it has 2 Instance as inputs => identity is RoleInstance
            #   - if it has 1 Instance and 1 Value as inputs => identity is AttributeInstance
            #
            # In any case, either we identify this node or we don't, we exclude it from the WEAK and STRONG sets:
            # this is due to the fact that the PropertyAssertion node is used to perform assertions at ABox level
            # while every other node in the graph is used at TBox level. Additionally we discard the inputs of
            # the node from the STRONG set since they are individual nodes that do not contribute with identity
            # inheritance (as for the Enumeration node).

            f1 = lambda x: x.item is Item.InstanceOfEdge
            f2 = lambda x: x.item in {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}
            f3 = lambda x: x.item is Item.InputEdge
            f4 = lambda x: x.item is Item.IndividualNode
            f5 = lambda x: Identity.RoleInstance if x.identity is Identity.Role else Identity.AttributeInstance

            outgoing = node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2)
            incoming = node.incomingNodes(filter_on_edges=f3, filter_on_nodes=f4)

            identity = Identity.Neutral

            # 1) Use if instanceOf edge to determine the identity of the node.
            identities = [f5(n) for n in outgoing]
            if identities:
                identity = identities[0]
                if identities.count(identities[0]) != len(identities):
                    identity = Identity.Unknown

            # 2) If there is no instanceOf edge then use the inputs.
            if identity is Identity.Neutral and len(incoming) >= 2:
                identity = Identity.RoleInstance
                if len([x for x in incoming if x.identity is Identity.Value]) > 0:
                    identity = Identity.AttributeInstance

            node.identity = identity

            excluded.add(node)

            for k in incoming:
                strong.discard(k)

    identity = Identity.Neutral
    identities = [n.identity for n in strong]
    if identities:
        identity = identities[0]
        if identities.count(identities[0]) != len(identities):
            identity = Identity.Unknown

    for node in weak - strong - excluded:
        node.identity = identity