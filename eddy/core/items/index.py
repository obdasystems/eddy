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


from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from eddy.core.datatypes import Item


class ItemIndex(QObject):
    """
    This class can be used to index diagram items for easy/fast retrieval.
    """
    sgnCleared = pyqtSignal()
    sgnItemAdded = pyqtSignal('QGraphicsItem')
    sgnItemRemoved = pyqtSignal('QGraphicsItem')

    def __init__(self, parent=None):
        """
        Initialize the index.
        :type parent: QObject
        """
        super().__init__(parent)
        self.itemsById = {}
        self.edgesById = {}
        self.nodesById = {}
        self.nodesByName = {}
        self.itemsByType = {}

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot('QGraphicsItem')
    def add(self, item):
        """
        Add the given element to the index.
        :type item: AbstractItem
        """
        self.itemsById[item.id] = item

        if item.item not in self.itemsByType:
            self.itemsByType[item.item] = set()
        self.itemsByType[item.item].add(item)

        if item.node:
            self.nodesById[item.id] = item
            if item.predicate:
                key = item.text()
                if item.item not in self.nodesByName:
                    self.nodesByName[item.item] = {}
                if not key in self.nodesByName[item.item]:
                    self.nodesByName[item.item][key] = set()
                self.nodesByName[item.item][key].add(item)

        if item.edge:
            self.edgesById[item.id] = item

        self.sgnItemAdded.emit(item)

    @pyqtSlot('QGraphicsItem')
    def remove(self, item):
        """
        Remove the given element from the index.
        :type item: AbstractItem
        """
        self.itemsById.pop(item.id, None)

        if item.item in self.itemsByType:
            self.itemsByType[item.item].discard(item)
            if not self.itemsByType[item.item]:
                del self.itemsByType[item.item]

        if item.node:
            self.nodesById.pop(item.id, None)
            if item.predicate:
                key = item.text()
                if item.item in self.nodesByName:
                    if key in self.nodesByName[item.item]:
                        self.nodesByName[item.item][key].discard(item)
                        if not self.nodesByName[item.item][key]:
                            del self.nodesByName[item.item][key]
                    if not self.nodesByName[item.item]:
                        del self.nodesByName[item.item]

        if item.edge:
            self.edgesById.pop(item.id, None)

        self.sgnItemRemoved.emit(item)

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def clear(self):
        """
        Clear the index.
        """
        self.edgesById.clear()
        self.itemsById.clear()
        self.nodesById.clear()
        self.nodesByName.clear()
        self.itemsByType.clear()
        self.sgnCleared.emit()

    def edgeForId(self, eid):
        """
        Returns the edge matching the given edge id.
        :type eid: str
        :rtype: AbstractEdge
        """
        try:
            return self.edgesById[eid]
        except KeyError:
            return None

    def edges(self):
        """
        Returns a view on all the edges in the index.
        :rtype: view
        """
        return self.edgesById.values()

    def hasEdges(self):
        """
        Tells whether there are edges in the index.
        :rtype: bool
        """
        return len(self.edgesById) != 0

    def hasItems(self):
        """
        Tells whether there are items in the index.
        :rtype: bool
        """
        return len(self.itemsById) != 0

    def hasNodes(self):
        """
        Tells whether there are nodes in the index.
        :rtype: bool
        """
        return len(self.nodesById) != 0

    def itemForId(self, iid):
        """
        Returns the item matching the given item id.
        :type iid: str
        :rtype: AbstractItem
        """
        try:
            return self.itemById[iid]
        except KeyError:
            return None

    def itemNum(self, item):
        """
        Returns the amount of items of the given type.
        :type item: Item
        """
        try:
            return len(self.itemsByType[item])
        except KeyError:
            return 0

    def items(self):
        """
        Returns a view on all the items in the index.
        :rtype: view
        """
        return self.itemsById.values()

    def nodeForId(self, nid):
        """
        Returns the node matching the given node id.
        :type nid: str
        :rtype: AbstractNode
        """
        try:
            return self.nodesById[nid]
        except KeyError:
            return None

    def nodes(self):
        """
        Returns a view on all the nodes in the index.
        :rtype: view
        """
        return self.nodesById.values()

    def predicates(self, item, name):
        """
        Returns the list of nodes of the given item type belonging to the same predicates.
        Will return a 'set' of 'AbstractNode' instances (predicate instances).
        :type item: Item
        :type name: str
        :rtype: set
        """
        try:
            return self.nodesByName[item][name]
        except KeyError:
            return set()

    def predicatesNum(self, item):
        """
        Returns the amount of predicates for the given type.
        :type item: Item
        """
        try:
            return len(self.nodesByName[item])
        except KeyError:
            return 0

    def predicateSubClassOf(self, item, name):
        """
        Returns a set of atomic predicate names the given one is subClassOf.
        In other words this method compute a set containing the name of the predicate being targeted by an inclusion
        edge sourcing from every node in the diagram that is of the given type and matches the given predicate name.

            - C3 -> C1
            - C3 -> C2
                => predicateSubClassOf(Item.ConceptNode, 'C1') = {}
                => predicateSubClassOf(Item.ConceptNode, 'C2') = {}
                => predicateSubClassOf(Item.ConceptNode, 'C3') = {'C1', 'C2'}

            - C3 <-> C1
            - C3  -> C2
                => predicateSubClassOf(Item.ConceptNode, 'C1') = {'C3'}
                => predicateSubClassOf(Item.ConceptNode, 'C2') = {}
                => predicateSubClassOf(Item.ConceptNode, 'C3') = {'C1', 'C2'}

        :type item: Item
        :type name: str
        :rtype: set
        """
        f1 = lambda x: x.item is Item.InclusionEdge
        f2 = lambda x: x.item is item
        return {x.text() for n in self.predicates(item, name) for x in n.outgoingNodes(f1, f2)}

    def size(self, nodes=True, edges=True):
        """
        Returns the amount of items in the index.
        :type nodes: bool
        :type edges: bool
        :rtype: int
        """
        if nodes and edges:
            return len(self.itemsById)
        if nodes and not edges:
            return len(self.nodesById)
        if edges and not nodes:
            return len(self.edgesById)
        return 0

    def __repr__(self):
        """
        Index visual representation.
        :rtype: str
        """
        return 'Index<edges:{},nodes:{}>'.format(len(self.edgesById), len(self.nodesById))