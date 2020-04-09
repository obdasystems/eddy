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

from eddy.core.functions.misc import first
from eddy.core.items.common import AbstractItem


class CommandNodeAdd(QtWidgets.QUndoCommand):
    """
    This command is used to add a node to a diagram.
    """
    def __init__(self, diagram, node):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node: AbstractNode
        """
        super().__init__('add {0}'.format(node.name))
        self.diagram = diagram
        self.node = node

    def redo(self):
        """redo the command"""
        self.diagram.addItem(self.node)
        self.diagram.sgnItemAdded.emit(self.diagram, self.node)
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.diagram.removeItem(self.node)
        self.diagram.sgnItemRemoved.emit(self.diagram, self.node)
        self.diagram.sgnUpdated.emit()

class CommandNodeSetDepth(QtWidgets.QUndoCommand):
    """
    This command is used to change the Z value of diagram nodes.
    """
    def __init__(self, diagram, node, zValue):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node: AbstractNode
        :type zValue: float
        """
        super().__init__('change {0} depth'.format(node.name))
        self.node = node
        self.diagram = diagram
        self.depth = {'redo': zValue, 'undo': node.zValue()}

    def redo(self):
        """redo the command"""
        self.node.setZValue(self.depth['redo'])
        self.node.updateEdges()
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.node.setZValue(self.depth['undo'])
        self.node.updateEdges()
        self.diagram.sgnUpdated.emit()

class CommandNodeRezize(QtWidgets.QUndoCommand):
    """
    This command is used to resize nodes.
    """
    def __init__(self, diagram, node, data):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node: AbstractNode
        :type data: dict
        """
        super().__init__('resize {0}'.format(node.name))
        self.diagram = diagram
        self.node = node
        self.data = data

    def redo(self):
        """redo the command"""
        # TURN CACHING OFF
        for edge in self.node.edges:
            edge.setCacheMode(AbstractItem.NoCache)

        self.node.background.setGeometry(self.data['redo']['background'])
        self.node.selection.setGeometry(self.data['redo']['selection'])
        self.node.polygon.setGeometry(self.data['redo']['polygon'])

        for edge, pos in self.data['redo']['anchors'].items():
            self.node.setAnchor(edge, pos)

        self.node.updateTextPos(moved=self.data['redo']['moved'])
        self.node.updateNode()
        self.node.updateEdges()
        self.node.update()

        # TURN CACHING ON
        for edge in self.node.edges:
            edge.setCacheMode(AbstractItem.DeviceCoordinateCache)

        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # TURN CACHING OFF
        for edge in self.node.edges:
            edge.setCacheMode(AbstractItem.NoCache)

        self.node.background.setGeometry(self.data['undo']['background'])
        self.node.selection.setGeometry(self.data['undo']['selection'])
        self.node.polygon.setGeometry(self.data['undo']['polygon'])

        for edge, pos in self.data['undo']['anchors'].items():
            self.node.setAnchor(edge, pos)

        self.node.updateTextPos(moved=self.data['undo']['moved'])
        self.node.updateNode()
        self.node.updateEdges()
        self.node.update()

        # TURN CACHING ON
        for edge in self.node.edges:
            edge.setCacheMode(AbstractItem.DeviceCoordinateCache)

        self.diagram.sgnUpdated.emit()

class CommandNodeMove(QtWidgets.QUndoCommand):
    """
    This command is used to move nodes (1 or more).
    """
    def __init__(self, diagram, undo, redo):
        """
        Initialize the command.
        :type diagram: Diagram
        :type undo: dict
        :type redo: dict
        """
        self._diagram = diagram
        self._edges = set()
        self._redo = redo
        self._undo = undo
        
        for node in self._redo['nodes']:
            self._edges |= node.edges

        if len(self._redo['nodes']) != 1:
            name = 'move {0} nodes'.format(len(self._redo['nodes']))
        else:
            name = 'move {0}'.format(first(self._redo['nodes'].keys()).name)

        super().__init__(name)

    def redo(self):
        """redo the command"""
        # Turn off caching.
        for edge in self._edges:
            edge.setCacheMode(AbstractItem.NoCache)
        # Update edges breakpoints.
        for edge, breakpoints in self._redo['edges'].items():
            for i in range(len(breakpoints)):
                edge.breakpoints[i] = breakpoints[i]
        # Update nodes positions.
        for node, data in self._redo['nodes'].items():
            node.setPos(data['pos'])
            # Update edge anchors.
            for edge, pos in data['anchors'].items():
                node.setAnchor(edge, pos)
        # Update edges.
        for edge in self._edges:
            edge.updateEdge()
        # Turn on caching.
        for edge in self._edges:
            edge.setCacheMode(AbstractItem.DeviceCoordinateCache)
        # Emit updated signal.
        self._diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # Turn off caching.
        for edge in self._edges:
            edge.setCacheMode(AbstractItem.NoCache)
        # Update edges breakpoints.
        for edge, breakpoints in self._undo['edges'].items():
            for i in range(len(breakpoints)):
                edge.breakpoints[i] = breakpoints[i]
        # Update nodes positions.
        for node, data in self._undo['nodes'].items():
            node.setPos(data['pos'])
            # Update edge anchors.
            for edge, pos in data['anchors'].items():
                node.setAnchor(edge, pos)
        # Update edges.
        for edge in self._edges:
            edge.updateEdge()
        # Turn caching ON.
        for edge in self._edges:
            edge.setCacheMode(AbstractItem.DeviceCoordinateCache)
        # Emit updated signal.
        self._diagram.sgnUpdated.emit()

class CommandNodeSwitchTo(QtWidgets.QUndoCommand):
    """
    This command is used to swap between 2 nodes.
    """
    def __init__(self, diagram, node1, node2):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node1: AbstractNode
        :type node2: AbstractNode
        """
        super().__init__('switch {0} to {1}'.format(node1.name, node2.name))
        self.node = {'redo': node2, 'undo': node1}
        self.diagram = diagram

    def redo(self):
        """redo the command"""
        # Add the new node to the diagram.
        self.diagram.addItem(self.node['redo'])
        self.diagram.sgnItemAdded.emit(self.diagram, self.node['redo'])

        # Move the anchor points.
        for edge, point in self.node['undo'].anchors.items():
            self.node['redo'].setAnchor(edge, point)

        # Move the edges.
        for edge in self.node['undo'].edges:
            if edge.source is self.node['undo']:
                edge.source = self.node['redo']
            if edge.target is self.node['undo']:
                edge.target = self.node['redo']

            self.node['redo'].addEdge(edge)
            # IMPORTANT: clear anchors dict in the edge or we
            # will have also the reference of the previous node
            # since it's a dict indexed by item!
            edge.anchors.clear()
            edge.updateEdge()

        # Identify the new node.
        self.diagram.sgnNodeIdentification.emit(self.node['redo'])

        # Clear edge and anchor references from node1.
        self.node['undo'].anchors.clear()
        self.node['undo'].edges.clear()

        # Remove the old node from the diagram.
        self.diagram.removeItem(self.node['undo'])
        self.diagram.sgnItemRemoved.emit(self.diagram, self.node['undo'])
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # Add back to the diagram the old node.
        self.diagram.addItem(self.node['undo'])
        self.diagram.sgnItemAdded.emit(self.diagram, self.node['undo'])

        # Move the anchor points back.
        for edge, point in self.node['redo'].anchors.items():
            self.node['undo'].setAnchor(edge, point)

        # Move the edges.
        for edge in self.node['redo'].edges:
            if edge.source is self.node['redo']:
                edge.source = self.node['undo']
            if edge.target is self.node['redo']:
                edge.target = self.node['undo']

            self.node['undo'].addEdge(edge)
            # IMPORTANT: clear anchors dict in the edge or we
            # will have also the reference of the previous node
            # since it's a dict indexed by item!
            edge.anchors.clear()
            edge.updateEdge()

        # Identify the old node.
        self.diagram.sgnNodeIdentification.emit(self.node['undo'])

        # Clear edge and anchor references from node2.
        self.node['redo'].anchors.clear()
        self.node['redo'].edges.clear()

        # Remove the new node from the diagram.
        self.diagram.removeItem(self.node['redo'])
        self.diagram.sgnItemRemoved.emit(self.diagram, self.node['redo'])
        self.diagram.sgnUpdated.emit()

class CommandNodeChangeInputsOrder(QtWidgets.QUndoCommand):
    """
    This command is used to change the order of Role chain and Property assertion inputs.
    """
    def __init__(self, diagram, node, inputs):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node: AbstractNode
        :type inputs: DistinctList
        """
        self.node = node
        self.diagram = diagram
        self.inputs = {'redo': inputs, 'undo': node.inputs}
        super().__init__('change {0} inputs order'.format(node.name))

    def redo(self):
        """redo the command"""
        self.node.inputs = self.inputs['redo']
        self.node.updateEdges()
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """redo the command"""
        self.node.inputs = self.inputs['undo']
        self.node.updateEdges()
        self.diagram.sgnUpdated.emit()

class CommandNodeSetBrush(QtWidgets.QUndoCommand):
    """
    This command is used to change the brush of predicate nodes.
    """
    def __init__(self, diagram, nodes, brush):
        """
        Initialize the command.
        :type diagram: Diagram
        :type nodes: T <= tuple|list|set
        :type brush: QBrush
        """
        self.nodes = nodes
        self.brush = {x: {'undo': x.brush(), 'redo': brush} for x in nodes}
        self.diagram = diagram
        super().__init__('set {0} brush on {1} node(s)'.format(brush.color().name(), len(nodes)))

    def redo(self):
        """redo the command"""
        for node in self.nodes:
            node.setBrush(self.brush[node]['redo'])
            node.updateNode(selected=node.isSelected())
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """redo the command"""
        for node in self.nodes:
            node.setBrush(self.brush[node]['undo'])
            node.updateNode(selected=node.isSelected())
        self.diagram.sgnUpdated.emit()

class CommandNodeSetFont(QtWidgets.QUndoCommand):
    """
    This command is used to change the brush of predicate nodes.
    """
    def __init__(self, diagram, nodes, size):
        """
        Initialize the command.
        :type nodes: T <= tuple|list|set
        :type size: int
        """
        self.diagram = diagram
        self.nodes = nodes
        self.size = {x: {'undo': x.fontSize, 'redo': size} for x in nodes}
        super().__init__('set {0} font size on {1} node(s)'.format(size, len(nodes)))

    def redo(self):
        """redo the command"""
        for node in self.nodes:
            node.setFontSize(self.size[node]['redo'])
            node.updateNode(selected=node.isSelected())
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """redo the command"""
        for node in self.nodes:
            node.setFontSize(self.size[node]['undo'])
            node.updateNode(selected=node.isSelected())
        self.diagram.sgnUpdated.emit()

