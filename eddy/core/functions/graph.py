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
                           the returned set of visited nodes, but its neighbours are not being vistied, unless they are
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
                           the returned set of visited nodes, but its neighbours are not being vistied, unless they are
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
    f1 = lambda x: x.isItem(Item.InclusionEdge, Item.InputEdge)
    f2 = lambda x: Identity.Neutral in x.identities

    collection = bfs(source=source, filter_on_edges=f1, filter_on_visit=f2)
    generators = partition(f2, collection)
    strong = set(generators[1])
    weak = set(generators[0])

    for node in weak:

        if node.isItem(Item.EnumerationNode):

            # Enumeration nodes needs to be analyzed separately since they do not inherit an identity
            # from their inputs but they compute it according to the nodes source of the inputs (note
            # that the Enumeration node can have as inputs source only atomic Individuals/Literals):
            #
            #   - if it has INDIVIDUALS as inputs => identity is Concept
            #   - if it has LITERALS as inputs => identity is DataRange
            #
            # We compute the identity for this node: if such identity is not NEUTRAL we put it
            # among the nodes specifying a STRONG identity so it will be excluded later when
            # computing inherited identity: computed identity >>> inherited identity.

            f3 = lambda x: x.isItem(Item.InputEdge) and x.target is node
            f4 = lambda x: x.isItem(Item.IndividualNode)

            individuals = [n for n in [e.other(node) for e in node.edges if f3(e)] if f4(n)]
            identity = [n.identity for n in individuals]

            if not identity:
                identity = Identity.Neutral
            elif identity.count(identity[0]) != len(identity):
                identity = Identity.Unknown
            elif identity[0] is Identity.Individual:
                identity = Identity.Concept
            elif identity[0] is Identity.Literal:
                identity = Identity.DataRange

            node.identity = identity

            # If it has been identified then consider it as STRONG.
            if node.identity is not Identity.Neutral:
                strong.add(node)

            # Remove all the nodes used to compute the Enumeration identity from the STRONG set
            # since we don't need them: they may lead to errors when computing the identity since
            # they do not contribute with inheritance to the identity of the Enumeration node.
            for k in individuals:
                strong.discard(k)

        elif node.isItem(Item.RangeRestrictionNode):

            # RangeRestriction nodes needs to be analyzed separately since they do not inherit an identity
            # from their inputs but they compute it according to the nodes source of the inputs.
            #
            #   - if it has ATTRIBUTES as inputs => identity is DataRange
            #   - if it has ROLES as inputs => identity is Concept
            #
            # We compute the identity for this node: if such identity is not NEUTRAL we put it
            # among the nodes specifying a STRONG identity so it will be excluded later when
            # computing inherited identity: computed identity >>> inherited identity.

            f3 = lambda x: x.isItem(Item.InputEdge) and x.target is node
            f4 = lambda x: x.identity in {Identity.Role, Identity.Attribute} and Identity.Neutral not in x.identities

            mixed = [n for n in [e.other(node) for e in node.edges if f3(e)] if f4(n)]
            identity = [n.identity for n in mixed]

            if not identity:
                identity = Identity.Neutral
            elif identity.count(identity[0]) != len(identity):
                identity = Identity.Unknown
            elif identity[0] is Identity.Role:
                identity = Identity.Concept
            elif identity[0] is Identity.Attribute:
                identity = Identity.DataRange

            node.identity = identity

            # If it has been identified then consider it as STRONG.
            if node.identity is not Identity.Neutral:
                strong.add(node)

            # Remove all the nodes used to compute the Range Restriction identity from the STRONG set
            # since  we don't need them: they may lead to errors when computing the identity since
            # they do not contribute with inheritance to the identity of the Range Restriction node.
            for k in mixed:
                strong.discard(k)

    v = [n.identity for n in strong]
    v = Identity.Neutral if not v else Identity.Unknown if v.count(v[0]) != len(v) else v[0]

    # Identify WEAK nodes using the computed identity.
    for node in weak - strong:
        node.identity = v