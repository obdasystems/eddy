# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from PyQt5.QtWidgets import QUndoCommand


class CommandItemsMultiAdd(QUndoCommand):
    """
    This command is used to add a collection of items to the graphic scene.
    """
    def __init__(self, scene, collection):
        """
        Initialize the command.
        :param scene: the graphic scene where this command is being performed.
        :param collection: a collection of items to add to the scene.
        """
        super().__init__('add %s items' % len(collection))
        self.scene = scene
        self.collection = collection
        self.selected = scene.selectedItems()

    def redo(self):
        """redo the command"""
        self.scene.clearSelection()
        for item in self.collection:
            self.scene.itemList.append(item)
            self.scene.addItem(item.shape)
            item.shape.setSelected(True)

    def undo(self):
        """undo the command"""
        self.scene.clearSelection()
        for item in self.collection:
            self.scene.itemList.remove(item)
            self.scene.removeItem(item.shape)
        for shape in self.selected:
            shape.setSelected(True)


class CommandItemsMultiRemove(QUndoCommand):
    """
    This command is used to remove multiple items from the graphic scene.
    The selection of the items involved in the multi remove needs to be handled somewhere else.
    """
    def __init__(self, scene, collection):
        """
        Initialize the command.
        :param scene: the graphic scene where this command is being performed.
        :param collection: a collection of items to remove.
        """
        self.scene = scene
        self.nodes = {item for item in collection if item.isNode()}
        self.edges = [item for item in collection if item.isEdge()]

        if len(collection) == 1:
            super().__init__('remove %s %s' % (collection[0].name, 'node' if collection[0].isNode() else 'edge'))
        else:
            super().__init__('remove %s items' % len(collection))

    def redo(self):
        """redo the command"""
        # remove the edges
        for edge in self.edges:
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
            self.scene.itemList.remove(edge)
            self.scene.removeItem(edge.shape)
        # remove the nodes
        for node in self.nodes:
            self.scene.itemList.remove(node)
            self.scene.removeItem(node.shape)

    def undo(self):
        """undo the command"""
        # add back the nodes
        for node in self.nodes:
            self.scene.itemList.append(node)
            self.scene.addItem(node.shape)
        # add back the edges
        for edge in self.edges:
            if not edge in self.scene.itemList:
                edge.source.addEdge(edge)
                edge.target.addEdge(edge)
                self.scene.itemList.append(edge)
                self.scene.addItem(edge.shape)