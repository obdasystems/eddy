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


from PyQt5 import QtWidgets

from eddy.core.datatypes.graphol import Item
from eddy.core.functions.misc import first


class CommandItemsAdd(QtWidgets.QUndoCommand):
    """
    This command is used to add a collection of items to a diagram.
    """
    def __init__(self, diagram, items):
        """
        Initialize the command.
        :type diagram: Diagram
        :type items: T <= tuple|list|set
        """
        self.items = items
        self.diagram = diagram
        self.selected = diagram.selectedItems()
        if len(items) == 1:
            name = 'add {0}'.format(first(items).name)
        else:
            name = 'add {0} items'.format(len(items))
        super().__init__(name)

    def redo(self):
        """redo the command"""
        self.diagram.clearSelection()
        # Add all the items to the diagram.
        for item in self.items:
            self.diagram.addItem(item)
            self.diagram.sgnItemAdded.emit(self.diagram, item)
            item.setSelected(True)
            item.updateEdgeOrNode(selected=True)
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.diagram.clearSelection()
        # Remove all the items from the diagram.
        for item in self.items:
            self.diagram.removeItem(item)
            self.diagram.sgnItemRemoved.emit(self.diagram, item)
        # Restore the old selection.
        for item in self.selected:
            item.setSelected(True)
            item.updateEdgeOrNode(selected=True)
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()


# TODO: restore selection
class CommandItemsRemove(QtWidgets.QUndoCommand):
    """
    This command is used to remove multiple items from a diagram.
    """
    def __init__(self, diagram, items):
        """
        Initialize the command.
        :type diagram: Diagram
        :type items: T <= tuple|list|set
        """
        self.diagram = diagram
        self.nodes = {item for item in items if item.isNode()}
        self.edges = {item for item in items if item.isEdge()}

        self.inputs = {n: {
            'undo': n.inputs[:],
            'redo': n.inputs[:],
        } for edge in self.edges \
            if edge.type() is Item.InputEdge \
                for n in {edge.source, edge.target} \
                    if n.type() in {Item.RoleChainNode, Item.PropertyAssertionNode} and \
                        n not in self.nodes}

        for node in self.inputs:
            for edge in node.edges:
                if edge.type() is Item.InputEdge and edge in self.edges and edge.target is node:
                    self.inputs[node]['redo'].remove(edge.id)

        if len(items) == 1:
            name = 'remove {0}'.format(first(items).name)
        else:
            name = 'remove {0} items'.format(len(items))

        super().__init__(name)

    def redo(self):
        """redo the command"""
        # Remove the edges.
        for edge in self.edges:
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
            self.diagram.removeItem(edge)
            self.diagram.sgnItemRemoved.emit(self.diagram, edge)
        # Remove the nodes.
        for node in self.nodes:
            self.diagram.removeItem(node)
            self.diagram.sgnItemRemoved.emit(self.diagram, node)
        # Update node inputs.
        for node in self.inputs:
            node.inputs = self.inputs[node]['redo'][:]
            for edge in node.edges:
                edge.updateEdge()
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # Add back the nodes.
        for node in self.nodes:
            self.diagram.addItem(node)
            self.diagram.sgnItemAdded.emit(self.diagram, node)
        # Add back the edges.
        for edge in self.edges:
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            self.diagram.addItem(edge)
            self.diagram.sgnItemAdded.emit(self.diagram, edge)
        # Update node inputs.
        for node in self.inputs:
            node.inputs = self.inputs[node]['undo'][:]
            for edge in node.edges:
                edge.updateEdge()
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()


class CommandComposeAxiom(QtWidgets.QUndoCommand):
    """
    This command is used to compose axioms.
    """
    def __init__(self, name, diagram, source, nodes, edges):
        """
        Initialize the command.
        :type name: str
        :type diagram: Diagram
        :type source: AbstractNode
        :type nodes: T <= tuple|list|set
        :type edges: T <= tuple|list|set
        """
        super().__init__(name)
        self.diagram = diagram
        self.source = source
        self.nodes = nodes
        self.edges = edges

    def redo(self):
        """redo the command"""
        # Map edges over source and target nodes.
        for edge in self.edges:
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
        # Add items to the diagram.
        for item in self.nodes | self.edges:
            self.diagram.addItem(item)
            self.diagram.sgnItemAdded.emit(self.diagram, item)
        # Update edges.
        for edge in self.edges:
            edge.updateEdge()
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # Remove items from the diagram.
        for item in self.nodes | self.edges:
            self.diagram.removeItem(item)
            self.diagram.sgnItemRemoved.emit(self.diagram, item)
        # Remove edge mappings from source and target nodes.
        for edge in self.edges:
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()


class CommandItemsTranslate(QtWidgets.QUndoCommand):
    """
    This command is used to translate items.
    """
    def __init__(self, diagram, items, moveX, moveY, name=None):
        """
        Initialize the command.
        :type diagram: Diagram
        :type items: T <= tuple|list|set
        :type moveX: float
        :type moveY: float
        :type name: str
        """
        super().__init__(name or 'move {0} item(s)'.format(len(items)))
        self.diagram = diagram
        self.items = items
        self.moveX = moveX
        self.moveY = moveY

    def redo(self):
        """redo the command"""
        moveX = self.moveX
        moveY = self.moveY
        for item in self.items:
            item.moveBy(moveX, moveY)
        for item in self.items:
            if item.isEdge():
                item.updateEdge()
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        moveX = -self.moveX
        moveY = -self.moveY
        for item in self.items:
            item.moveBy(moveX, moveY)
        for item in self.items:
            if item.isEdge():
                item.updateEdge()
        self.diagram.sgnUpdated.emit()


class CommandSnapItemsToGrid(QtWidgets.QUndoCommand):
    """
    This command is used to snap diagram elements to the grid.
    """
    def __init__(self, diagram, data, name=None):
        """
        Initialize the command.
        :type diagram: Diagram
        :type data: dict
        :type name: str
        """
        num = len(data['undo']['nodes']) + len(data['redo']['edges'])
        super().__init__(name or 'snap {0} item(s) to the grid'.format(num))
        self.diagram = diagram
        self.data = data

    def redo(self):
        """redo the command"""
        edges = set()
        # Snap the nodes.
        for node in self.data['redo']['nodes']:
            node.anchors = self.data['redo']['nodes'][node]['anchors']
            node.setPos(self.data['redo']['nodes'][node]['pos'])
            edges |= node.edges
        # Snap the edges.
        for edge in self.data['redo']['edges']:
            edge.breakpoints = self.data['redo']['edges'][edge]['breakpoints']
            edges.add(edge)
        # Update all the edges.
        for edge in edges:
            edge.updateEdge()
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        edges = set()
        # Un-snap the nodes.
        for node in self.data['undo']['nodes']:
            node.anchors = self.data['undo']['nodes'][node]['anchors']
            node.setPos(self.data['undo']['nodes'][node]['pos'])
            edges |= node.edges
        # Un-snap the edges.
        for edge in self.data['undo']['edges']:
            edge.breakpoints = self.data['undo']['edges'][edge]['breakpoints']
            edges.add(edge)
        # Update all the edges.
        for edge in edges:
            edge.updateEdge()
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()