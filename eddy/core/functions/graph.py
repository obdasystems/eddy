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


from collections import deque


def bfs(source, filter_on_edges=lambda x: True, filter_on_nodes=lambda x: True, filter_on_visit=lambda x: True):
    """
    Perform a customized BFS returning a list of visited nodes.
    The function accepts 3 callable parameters:

        * filter_on_edges: a callable which takes as input an edge and returns
           True iff the search has to proceed along the edge; if instead
           the callable returns False, the given edge is excluded
           from the search.
        * filter_on_nodes: a callable which takes as input a node and returns
           True iff the search has to take the node into consideration; else
           the callable MUST return False (NOTE: the node is not included
           in the returned set of visited nodes, nor its neighbours are
           being visited, unless they are connected through some other
           nodes for which the callable returns True).
        * filter_on_visit: a callable which takes as input a node and returns
           True iff the search algoritm should visit the given node neighbours;
           else the callable MUST return False (NOTE: the node IS included
           in the returned set of visited nodes, but its neighbours are not
           being visited, unless they are connected through some other nodes
           for which the callable returns True).

    :type source: AbstractNode
    :type filter_on_edges: callable
    :type filter_on_nodes callable
    :type filter_on_visit: callable
    :type: list
    """
    queue = deque([source])
    extend = queue.extend
    ordered = []
    visited = set()
    while queue:
        node = queue.popleft()
        ordered.append(node)
        visited.add(node)
        if filter_on_visit(node):
            extend([n for n in [e.other(node) for e in node.edges if filter_on_edges(e)] if n not in visited and filter_on_nodes(n)])
    return ordered


def dfs(source, filter_on_edges=lambda x: True, filter_on_nodes=lambda x: True, filter_on_visit=lambda x: True):
    """
    Perform a customized DFS returning a list of visited nodes.
    The function accepts 3 callable parameters:

        * filter_on_edges: a callable which takes as input an edge and returns
           True iff the search has to proceed along the edge; if instead
           the callable returns False, the given edge is excluded
           from the search.
        * filter_on_nodes: a callable which takes as input a node and returns
           True iff the search has to take the node into consideration; else
           the callable MUST return False (NOTE: the node is not included
           in the returned set of visited nodes, nor its neighbours are
           being visited, unless they are connected through some other
           nodes for which the callable returns True).
        * filter_on_visit: a callable which takes as input a node and returns
           True iff the search algoritm should visit the given node neighbours;
           else the callable MUST return False (NOTE: the node IS included
           in the returned set of visited nodes, but its neighbours are not
           being visited, unless they are connected through some other nodes
           for which the callable returns True).

    :type source: AbstractNode
    :type filter_on_edges: callable
    :type filter_on_nodes callable
    :type filter_on_visit: callable
    :type: list
    """
    stack = [source]
    extend = stack.extend
    ordered = []
    visited = set()
    while stack:
        node = stack.pop()
        if node not in visited:
            ordered.append(node)
            visited.add(node)
            if filter_on_visit(node):
                extend([n for n in [e.other(node) for e in node.edges if filter_on_edges(e)] if n not in visited and filter_on_nodes(n)])
    return visited