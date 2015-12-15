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

from eddy.datatypes import Item


class CommandEdgeAdd(QUndoCommand):
    """
    This command is used to add edges to the scene.
    """
    def __init__(self, scene, edge):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param edge: the edge being added.
        """
        super().__init__('add {0} edge'.format(edge.name))
        self.edge = edge
        self.scene = scene
        self.source = edge.source
        self.target = None
        self.inputs1 = []
        self.inputs2 = []

    def end(self, node):
        """
        Complete the Edge insertion command.
        :param node: the target node of this edge.
        """
        self.edge.target = node
        self.edge.source.addEdge(self.edge)
        self.edge.target.addEdge(self.edge)
        self.edge.updateEdge()

        self.target = self.edge.target

        if self.edge.isItem(Item.InputEdge):
            # if we are adding an input edge targeting a role chain or a property
            # assertion node we need to save the new inputs order and compute the
            # old one by removing the current edge id from the input list.
            if self.edge.target.isItem(Item.RoleChainNode, Item.PropertyAssertionNode):
                self.inputs2 = self.edge.target.inputs[:]
                self.inputs1 = self.edge.target.inputs[:]
                self.inputs1.remove(self.edge.id)

    def redo(self):
        """redo the command"""
        # IMPORTANT: don't remove this check!
        if self.edge.id not in self.scene.edgesById:
            # map source/target over the edge
            self.edge.source.addEdge(self.edge)
            self.edge.target.addEdge(self.edge)
            # remove the edge from the scene
            self.scene.addItem(self.edge)
            # switch the inputs
            if self.target.isItem(Item.RoleChainNode, Item.PropertyAssertionNode):
                self.target.inputs = self.inputs2[:]
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # IMPORTANT: don't remove this check!
        if self.edge.id in self.scene.edgesById:
            # remove source/target from the edge
            self.edge.source.removeEdge(self.edge)
            self.edge.target.removeEdge(self.edge)
            # remove the edge from the scene
            self.scene.removeItem(self.edge)
            # switch the inputs
            if self.target.isItem(Item.RoleChainNode, Item.PropertyAssertionNode):
                self.target.inputs = self.inputs1[:]
            self.scene.updated.emit()


class CommandEdgeBreakpointAdd(QUndoCommand):
    """
    This command is used to add a breakpoint on the given edge.
    """
    def __init__(self, scene, edge, index, point):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param edge: the edge on which the break point is being added.
        :param index: the index of the new breakpoint.
        :param point: the breakpoint.
        """
        super().__init__('add {0} edge breakpoint'.format(edge.name))
        self.edge = edge
        self.scene = scene
        self.index = index
        self.point = point

    def redo(self):
        """redo the command"""
        self.edge.breakpoints.insert(self.index, self.point)
        self.edge.updateEdge()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.edge.breakpoints.pop(self.index)
        self.edge.updateEdge()
        self.scene.updated.emit()


class CommandEdgeAnchorMove(QUndoCommand):
    """
    This command is used to move edge anchor points.
    """
    def __init__(self, scene, edge, node):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param edge: the edge whose anchor point is being moved.
        :param node: the shape on which the moving is happening.
        """
        super().__init__('move {0} edge anchor point'.format(edge.name))
        self.scene = scene
        self.edge = edge
        self.node = node
        self.pos1 = node.anchor(edge)
        self.pos2 = None

    def end(self):
        """
        Complete the command collecting new data.
        """
        self.pos2 = self.node.anchor(self.edge)

    def redo(self):
        """redo the command"""
        if self.pos2:
            self.node.setAnchor(self.edge, self.pos2)
            self.edge.updateEdge()
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.node.setAnchor(self.edge, self.pos1)
        self.edge.updateEdge()
        self.scene.updated.emit()


class CommandEdgeBreakpointMove(QUndoCommand):
    """
    This command is used to move edge breakpoints.
    """
    def __init__(self, scene, edge, index):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param edge: the edge whose breakpoint is being moved.
        :param index: the index of the breakpoint.
        """
        super().__init__('move {0} edge breakpoint'.format(edge.name))
        self.edge = edge
        self.scene = scene
        self.index = index
        self.pos1 = edge.breakpoints[self.index]
        self.pos2 = None

    def end(self, pos):
        """
        Complete the command collecting new data.
        :param pos: the new position of the breakpoint.
        """
        self.pos2 = pos

    def redo(self):
        """redo the command"""
        if self.pos2:
            self.edge.breakpoints[self.index] = self.pos2
            self.edge.updateEdge()
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.edge.breakpoints[self.index] = self.pos1
        self.edge.updateEdge()
        self.scene.updated.emit()


class CommandEdgeBreakpointDel(QUndoCommand):
    """
    This command is used to delete edge breakpoints.
    """
    def __init__(self, scene, edge, index):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param edge: the edge whose breakpoint is being deleted.
        :param index: the index of the breakpoint.
        """
        super().__init__('remove {0} edge breakpoint'.format(edge.name))
        self.edge = edge
        self.scene = scene
        self.index = index
        self.point = edge.breakpoints[self.index]

    def redo(self):
        """redo the command"""
        self.edge.breakpoints.pop(self.index)
        self.edge.updateEdge()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.edge.breakpoints.insert(self.index, self.point)
        self.edge.updateEdge()
        self.scene.updated.emit()


class CommandEdgeInclusionToggleComplete(QUndoCommand):
    """
    This command is used to toggle the complete attribute of Inclusion edges.
    """
    def __init__(self, scene, data):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param data: a mapping containing 'complete' data change for each edge.
        """
        if len(data) == 1:
            super().__init__('toggle {0} edge completness'.format(next(iter(data.keys())).name))
        else:
            super().__init__('toggle completness for {0} edges'.format(len(data)))

        self.scene = scene
        self.data = data

    def redo(self):
        """redo the command"""
        for edge in self.data:
            edge.complete = self.data[edge]['to']
            edge.updateEdge()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        for edge in self.data:
            edge.complete = self.data[edge]['from']
            edge.updateEdge()
        self.scene.updated.emit()


class CommandEdgeInputToggleFunctional(QUndoCommand):
    """
    This command is used to toggle the functional attribute of Input edges.
    """
    def __init__(self, scene, data):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param data: a mapping containing 'functional' data change for each edge.
        """
        if len(data) == 1:
            super().__init__('toggle {0} edge functionality'.format(next(iter(data.keys())).name))
        else:
            super().__init__('toggle functionality for {0} edges'.format(len(data)))

        self.scene = scene
        self.data = data

    def redo(self):
        """redo the command"""
        for edge in self.data:
            edge.functional = self.data[edge]['to']
            edge.updateEdge()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        for edge in self.data:
            edge.functional = self.data[edge]['from']
            edge.updateEdge()
        self.scene.updated.emit()


class CommandEdgeSwap(QUndoCommand):
    """
    This command is used to swap edges' source/target.
    """
    def __init__(self, scene, edges):
        """
        Initialize the command.
        :param scene: the scene where this command is being performed.
        :param edges: a collection of edges to swap.
        """
        if len(edges) == 1:
            super().__init__('swap {0} edge'.format(next(iter(edges)).name))
        else:
            super().__init__('swap {0} edges'.format(len(edges)))

        self.scene = scene
        self.edges = edges

        # backup inputs order for role chain and property assertion
        self.inputs1 = {node: node.inputs[:] for edge in self.edges \
                        if edge.isItem(Item.InputEdge) \
                        for node in {edge.source, edge.target} \
                        if node.isItem(Item.RoleChainNode,
                                       Item.PropertyAssertionNode)}

        # exec dict comprehension again since we need a copy of the order and not the reference
        self.inputs2 = {node: node.inputs[:] for edge in self.edges \
                        if edge.isItem(Item.InputEdge) \
                        for node in {edge.source, edge.target} \
                        if node.isItem(Item.RoleChainNode,
                                       Item.PropertyAssertionNode)}

        for edge in self.edges:
            if edge.target in self.inputs2:
                self.inputs2[edge.target].remove(edge.id)

        for edge in self.edges:
            if edge.source in self.inputs2:
                self.inputs2[edge.source].append(edge.id)

    def redo(self):
        """redo the command"""
        for edge in self.edges:
            edge.source, edge.target = edge.target, edge.source
            edge.breakpoints = edge.breakpoints[::-1]
            for node in {edge.source, edge.target}:
                if node in self.inputs2:
                    node.inputs = self.inputs2[node]
            edge.updateEdge()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        for edge in self.edges:
            edge.source, edge.target = edge.target, edge.source
            edge.breakpoints = edge.breakpoints[::-1]
            for node in {edge.source, edge.target}:
                if node in self.inputs1:
                    node.inputs = self.inputs1[node]
            edge.updateEdge()
        self.scene.updated.emit()