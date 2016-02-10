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


from PyQt5.QtCore import QObject, pyqtSignal

from eddy.core.datatypes import DistinctList


class ItemIndex(QObject):
    """
    This class can be used to index Diagram Scene items for easy/fast retrieval.
    """
    cleared = pyqtSignal()
    itemAdded = pyqtSignal('QGraphicsItem')
    itemRemoved = pyqtSignal('QGraphicsItem')

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
                if not key in self.nodesByTx:
                    self.nodesByTx[key] = DistinctList()
                self.nodesByTx[key].append(item)
        self.itemAdded.emit(item)

    def clear(self):
        """
        Clear the index.
        """
        self.edgesById.clear()
        self.itemsById.clear()
        self.nodesById.clear()
        self.nodesByTx.clear()
        self.cleared.emit()

    def edgeForId(self, eid):
        """
        Returns the edge matching the given edge id.
        :type eid: str
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

    def itemForId(self, iid):
        """
        Returns the item matching the given item id.
        :type iid: str
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

    def nodesForLabel(self, key):
        """
        Returns the list of nodes sharing the given label (only for predicate nodes).
        :type key: str
        :rtype: DistinctList
        """
        try:
            return self.nodesByTx[key]
        except KeyError:
            return DistinctList()

    def predicates(self):
        """
        Returns a list of predicates in the index.
        :rtype: str
        """
        return list(self.nodesByTx.keys())

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
                if key in self.nodesByTx:
                    self.nodesByTx[key].remove(item)
                    if not self.nodesByTx[key]:
                        del self.nodesByTx[key]
        self.itemRemoved.emit(item)

    def size(self):
        """
        Returns the amount of items in the index.
        :rtype: int
        """
        return len(self.itemsById)

    def __repr__(self):
        """
        Index visual representation.
        :rtype: str
        """
        return 'Index<edges:{},nodes:{}>'.format(len(self.edgesById), len(self.nodesById))