# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  GrapholEd: an editor for the Graphol ontology language.               #
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
        :param scene: the scene where this command is being performed.
        :param collection: a collection of items to add to the scene.
        """
        self.scene = scene
        self.collection = collection
        self.selected = scene.selectedItems()

        if len(collection) == 1:
            super().__init__('add {0} {1}'.format(collection[0].name, 'node' if collection[0].isNode() else 'edge'))
        else:
            super().__init__('add {0} items'.format(len(collection)))

    def redo(self):
        """redo the command"""
        self.scene.clearSelection()
        for item in self.collection:
            self.scene.addItem(item)
            item.setSelected(True)
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.scene.clearSelection()
        for item in self.collection:
            self.scene.removeItem(item)
        for item in self.selected:
            item.setSelected(True)
        # emit updated signal
        self.scene.updated.emit()


class CommandItemsMultiRemove(QUndoCommand):
    """
    This command is used to remove multiple items from the scene.
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
            super().__init__('remove {0} {1}'.format(collection[0].name, 'node' if collection[0].isNode() else 'edge'))
        else:
            super().__init__('remove {0} items'.format(len(collection)))

    def redo(self):
        """redo the command"""
        # remove the edges
        for edge in self.edges:
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
            self.scene.removeItem(edge)
        # remove the nodes
        for node in self.nodes:
            self.scene.removeItem(node)
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # add back the nodes
        for node in self.nodes:
            self.scene.addItem(node)
        # add back the edges
        for edge in self.edges:
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            self.scene.addItem(edge)
        # emit updated signal
        self.scene.updated.emit()


class CommandComposeAxiom(QUndoCommand):
    """
    This command is used to compose an axioms.
    """
    def __init__(self, name, scene, source, nodes, edges):
        """
        Initialize the command.
        :param name: the name of the undo command
        :param scene: the graphic scene where this command is being performed.
        :param source: the source node of the composition
        :param nodes: a set of nodes to be used in the composition.
        :param edges: a set of edges to be used in the composition.
        """
        super().__init__(name)
        self.scene = scene
        self.source = source
        self.nodes = nodes
        self.edges = edges

    def redo(self):
        """redo the command"""
        # add items to the scene
        for item in self.nodes | self.edges:
            self.scene.addItem(item)
        # map edges over source and target nodes
        for edge in self.edges:
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            edge.updateEdge()
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # remove edge mappings from source and target nodes
        for edge in self.edges:
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
        # remove items from the scene
        for item in self.nodes | self.edges:
            self.scene.removeItem(item)
        # emit updated signal
        self.scene.updated.emit()