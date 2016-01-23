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


class CommandEdgeAdd(QUndoCommand):
    """
    This command is used to add edges to the scene.
    """
    def __init__(self, scene, edge):
        """
        Initialize the command.
        """
        super().__init__('add {}'.format(edge.item.label))
        self.edge = edge
        self.scene = scene
        self.inputs = {'redo': [], 'undo': []}

    def end(self, node):
        """
        Complete the Edge insertion command.
        :type node: AbstractNode
        """
        self.edge.target = node
        self.edge.source.addEdge(self.edge)
        self.edge.target.addEdge(self.edge)
        self.edge.updateEdge()

        if self.edge.isItem(Item.InputEdge):
            # if we are adding an input edge targeting a role chain or a property
            # assertion node we need to save the new inputs order and compute the
            # old one by removing the current edge id from the input list.
            if self.edge.target.isItem(Item.RoleChainNode, Item.PropertyAssertionNode):
                self.inputs['redo'] = self.edge.target.inputs[:]
                self.inputs['undo'] = self.edge.target.inputs[:]
                self.inputs['undo'].remove(self.edge.id)

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
            if self.edge.target.isItem(Item.RoleChainNode, Item.PropertyAssertionNode):
                self.edge.target.inputs = self.inputs['redo'][:]
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
            if self.edge.target.isItem(Item.RoleChainNode, Item.PropertyAssertionNode):
                self.edge.target.inputs = self.inputs['undo'][:]
            self.scene.updated.emit()


class CommandEdgeBreakpointAdd(QUndoCommand):
    """
    This command is used to add a breakpoint on the given edge.
    """
    def __init__(self, scene, edge, index, point):
        """
        Initialize the command.
        """
        super().__init__('add {} breakpoint'.format(edge.item.label))
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
        """
        super().__init__('move {} anchor point'.format(edge.item.label))
        self.scene = scene
        self.edge = edge
        self.node = node
        self.pos = {'undo': node.anchor(edge)}

    def end(self):
        """
        Complete the command collecting new data.
        """
        self.pos['redo'] = self.node.anchor(self.edge)

    def redo(self):
        """redo the command"""
        if 'redo' in self.pos:
            self.node.setAnchor(self.edge, self.pos['redo'])
            self.edge.updateEdge()
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.node.setAnchor(self.edge, self.pos['undo'])
        self.edge.updateEdge()
        self.scene.updated.emit()


class CommandEdgeBreakpointMove(QUndoCommand):
    """
    This command is used to move edge breakpoints.
    """
    def __init__(self, scene, edge, index):
        """
        Initialize the command.
        """
        super().__init__('move {} breakpoint'.format(edge.item.label))
        self.edge = edge
        self.scene = scene
        self.index = index
        self.pos = {'undo': edge.breakpoints[self.index] }

    def end(self, pos):
        """
        Complete the command collecting new data.
        :type pos: QPointF
        """
        self.pos['redo'] = pos

    def redo(self):
        """redo the command"""
        if 'redo' in self.pos:
            self.edge.breakpoints[self.index] = self.pos['redo']
            self.edge.updateEdge()
            self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        self.edge.breakpoints[self.index] = self.pos['undo']
        self.edge.updateEdge()
        self.scene.updated.emit()


class CommandEdgeBreakpointDel(QUndoCommand):
    """
    This command is used to delete edge breakpoints.
    """
    def __init__(self, scene, edge, index):
        """
        Initialize the command.
        """
        super().__init__('remove {} breakpoint'.format(edge.item.label))
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
        """
        if len(data) == 1:
            super().__init__('toggle {} completness'.format(next(iter(data.keys())).item.label))
        else:
            super().__init__('toggle completness for {} edges'.format(len(data)))

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
        """
        if len(data) == 1:
            super().__init__('toggle {} functionality'.format(next(iter(data.keys())).item.label))
        else:
            super().__init__('toggle functionality for {} edges'.format(len(data)))

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
        """
        if len(edges) == 1:
            super().__init__('swap {}'.format(next(iter(edges)).item.label))
        else:
            super().__init__('swap {} edges'.format(len(edges)))

        self.scene = scene
        self.edges = edges

        self.inputs = {n: {
            'undo': n.inputs[:],
            'redo': n.inputs[:],
        } for edge in self.edges \
            if edge.isItem(Item.InputEdge) \
                for n in {edge.source, edge.target} \
                    if n.isItem(Item.RoleChainNode, Item.PropertyAssertionNode)}

        for edge in self.edges:
            if edge.isItem(Item.InputEdge) and edge.target in self.inputs:
                self.inputs[edge.target]['redo'].remove(edge.id)

        for edge in self.edges:
            if edge.isItem(Item.InputEdge) and edge.source in self.inputs:
                self.inputs[edge.source]['redo'].append(edge.id)

    def redo(self):
        """redo the command"""
        for edge in self.edges:
            edge.source, edge.target = edge.target, edge.source
            edge.breakpoints = edge.breakpoints[::-1]
            for node in {edge.source, edge.target}:
                if node in self.inputs:
                    node.inputs = self.inputs[node]['redo'][:]
            edge.updateEdge()
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        for edge in self.edges:
            edge.source, edge.target = edge.target, edge.source
            edge.breakpoints = edge.breakpoints[::-1]
            for node in {edge.source, edge.target}:
                if node in self.inputs:
                    node.inputs = self.inputs[node]['undo'][:]
            edge.updateEdge()
        self.scene.updated.emit()