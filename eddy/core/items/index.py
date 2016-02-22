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


from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from eddy.core.datatypes import DistinctList


class ItemIndex(QObject):
    """
    This class can be used to index diagram items for easy/fast retrieval.
    """
    sgnIndexCleared = pyqtSignal()
    sgnItemAdded = pyqtSignal('QGraphicsItem')
    sgnItemRemoved = pyqtSignal('QGraphicsItem')

    def __init__(self, parent=None):
        """
        Initialize the index.
        :type parent: QObject
        """
        super().__init__(parent)
        self.edgesById = {}
        self.itemsById = {}
        self.nodesById = {}
        self.nodesByTx = {}

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
        if item.edge:
            self.edgesById[item.id] = item
        elif item.node:
            self.nodesById[item.id] = item
            if item.predicate:
                key = item.text()
                if item.item not in self.nodesByTx:
                    self.nodesByTx[item.item] = {}
                if not key in self.nodesByTx[item.item]:
                    self.nodesByTx[item.item][key] = DistinctList()
                self.nodesByTx[item.item][key].append(item)
        self.sgnItemAdded.emit(item)

    @pyqtSlot('QGraphicsItem')
    def remove(self, item):
        """
        Remove the given element from the index.
        :type item: AbstractItem
        """
        self.itemsById.pop(item.id, None)
        if item.edge:
            self.edgesById.pop(item.id, None)
        elif item.node:
            self.nodesById.pop(item.id, None)
            if item.predicate:
                key = item.text()
                if item.item in self.nodesByTx:
                    if key in self.nodesByTx[item.item]:
                        self.nodesByTx[item.item][key].remove(item)
                        if not self.nodesByTx[item.item][key]:
                            del self.nodesByTx[item.item][key]
                    if not self.nodesByTx[item.item]:
                        del self.nodesByTx[item.item]
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
        self.nodesByTx.clear()
        self.sgnIndexCleared.emit()

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

    def predicates(self, item, key):
        """
        Returns the list of nodes of the given item type belonging to the same predicate.
        :type item: Item
        :type key: str
        :rtype: DistinctList
        """
        try:
            return self.nodesByTx[item][key]
        except KeyError:
            return DistinctList()

    def predicatesNum(self, item):
        """
        Returns the amount of predicates for the given type.
        :param item: Item
        """
        try:
            return len(self.nodesByTx[item])
        except KeyError:
            return 0

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