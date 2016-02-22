# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtWidgets import QUndoCommand

from eddy.core.datatypes import Item


class CommandItemsMultiAdd(QUndoCommand):
    """
    This command is used to add a collection of items to the graphic scene.
    """
    def __init__(self, scene, collection):
        """
        Initialize the command.
        """
        self.scene = scene
        self.collection = collection
        self.selected = scene.selectedItems()

        if len(collection) == 1:
            super().__init__('add {}'.format(next(iter(collection)).name))
        else:
            super().__init__('add {} items'.format(len(collection)))

    def redo(self):
        """redo the command"""
        self.scene.clearSelection()
        for item in self.collection:
            self.scene.addItem(item)
            self.scene.sgnItemAdded.emit(item)
            item.setSelected(True)
        # emit updated signal
        self.scene.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.scene.clearSelection()
        for item in self.collection:
            self.scene.removeItem(item)
            self.scene.sgnItemRemoved.emit(item)
        for item in self.selected:
            item.setSelected(True)
        # emit updated signal
        self.scene.sgnUpdated.emit()


class CommandItemsMultiRemove(QUndoCommand):
    """
    This command is used to remove multiple items from the scene.
    The selection of the items involved in the multi remove needs to be handled somewhere else.
    """
    def __init__(self, scene, collection):
        """
        Initialize the command.
        """
        self.scene = scene
        self.nodes = {item for item in collection if item.node}
        self.edges = {item for item in collection if item.edge}

        # compute the new inputs order for role chain and property assertion nodes
        # which are not being removed but whose other endpoint is being detached.
        self.inputs = {n: {
            'undo': n.inputs[:],
            'redo': n.inputs[:],
        } for edge in self.edges \
            if edge.isItem(Item.InputEdge) \
                for n in {edge.source, edge.target} \
                    if n.isItem(Item.RoleChainNode, Item.PropertyAssertionNode) and \
                        n not in self.nodes}

        for node in self.inputs:
            for edge in node.edges:
                if edge.isItem(Item.InputEdge) and edge in self.edges and edge.target is node:
                    self.inputs[node]['redo'].remove(edge.id)

        if len(collection) == 1:
            super().__init__('remove {}'.format(next(iter(collection)).name))
        else:
            super().__init__('remove {} items'.format(len(collection)))

    def redo(self):
        """redo the command"""
        # remove the edges
        for edge in self.edges:
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
            self.scene.removeItem(edge)
            self.scene.sgnItemRemoved.emit(edge)
        # remove the nodes
        for node in self.nodes:
            self.scene.removeItem(node)
            self.scene.sgnItemRemoved.emit(node)
        # update node inputs
        for node in self.inputs:
            node.inputs = self.inputs[node]['redo'][:]
            for edge in node.edges:
                edge.updateEdge()
        # emit updated signal
        self.scene.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # add back the nodes
        for node in self.nodes:
            self.scene.addItem(node)
            self.scene.sgnItemAdded.emit(node)
        # add back the edges
        for edge in self.edges:
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            self.scene.addItem(edge)
            self.scene.sgnItemAdded.emit(edge)
        # update node inputs
        for node in self.inputs:
            node.inputs = self.inputs[node]['undo'][:]
            for edge in node.edges:
                edge.updateEdge()
        # emit updated signal
        self.scene.sgnUpdated.emit()


class CommandComposeAxiom(QUndoCommand):
    """
    This command is used to compose axioms.
    """
    def __init__(self, name, scene, source, nodes, edges):
        """
        Initialize the command.
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
            self.scene.sgnItemAdded.emit(item)
        # map edges over source and target nodes
        for edge in self.edges:
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            edge.updateEdge()
        # emit updated signal
        self.scene.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # remove edge mappings from source and target nodes
        for edge in self.edges:
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
        # remove items from the scene
        for item in self.nodes | self.edges:
            self.scene.removeItem(item)
            self.scene.sgnItemRemoved.emit(item)
        # emit updated signal
        self.scene.sgnUpdated.emit()


class CommandRefactor(QUndoCommand):
    """
    This command is used to perform refactoring by applying multiple QUndoCommand.
    """
    def __init__(self, name, scene, commands):
        """
        Initialize the command.
        """
        super().__init__(name)
        self.scene = scene
        self.commands = commands

    def redo(self):
        """redo the command"""
        for command in self.commands:
            command.redo()
        self.scene.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        for command in self.commands:
            command.undo()
        self.scene.sgnUpdated.emit()


class CommandItemsTranslate(QUndoCommand):
    """
    This command is used to translate items.
    """
    def __init__(self, scene, collection, moveX, moveY, name=None):
        """
        Initialize the command.
        """
        self.scene = scene
        self.collection = collection
        self.moveX = moveX
        self.moveY = moveY
        name = name or 'move {} item{}'.format(len(collection), 's' if len(collection) != 1 else '')
        super().__init__(name)

    def redo(self):
        """redo the command"""
        moveX = self.moveX
        moveY = self.moveY
        for item in self.collection:
            item.moveBy(moveX, moveY)
        for item in self.collection:
            if item.edge:
                item.updateEdge()
        self.scene.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        moveX = -self.moveX
        moveY = -self.moveY
        for item in self.collection:
            item.moveBy(moveX, moveY)
        for item in self.collection:
            if item.edge:
                item.updateEdge()
        self.scene.sgnUpdated.emit()


class CommandSetProperty(QUndoCommand):
    """
    This command is used to set properties of graphol items.
    """
    def __init__(self, scene, node, collection, name):
        """
        Initialize the command.
        """
        if not isinstance(collection, (list, tuple)):
            collection = [collection]
        self.node = node
        self.scene = scene
        self.collection = collection
        super().__init__(name)

    def redo(self):
        """redo the command"""
        for data in self.collection:
            setattr(self.node, data['attribute'], data['redo'])
        self.scene.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        for data in self.collection:
            setattr(self.node, data['attribute'], data['undo'])
        self.scene.sgnUpdated.emit()