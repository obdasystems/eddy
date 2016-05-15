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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtWidgets import QUndoCommand

from eddy.core.datatypes.graphol import Item
from eddy.core.functions.misc import first
from eddy.core.items.common import AbstractItem

from eddy.lang import gettext as _


class CommandNodeAdd(QUndoCommand):
    """
    This command is used to add a node to a diagram.
    """
    def __init__(self, diagram, node):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node: AbstractNode
        """
        super().__init__(_('COMMAND_NODE_ADD', node.name))
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


class CommandNodeSetDepth(QUndoCommand):
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
        super().__init__(_('COMMAND_NODE_SET_DEPTH', node.name))
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


class CommandNodeRezize(QUndoCommand):
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
        super().__init__(_('COMMAND_NODE_RESIZE', node.name))
        self.diagram = diagram
        self.node = node
        self.data = data

    def redo(self):
        """redo the command"""
        # TURN CACHING OFF
        for edge in self.node.edges:
            edge.setCacheMode(AbstractItem.NoCache)

        self.node.background = self.data['redo']['background']
        self.node.selection = self.data['redo']['selection']
        self.node.polygon = self.data['redo']['polygon']

        for edge, pos in self.data['redo']['anchors'].items():
            self.node.setAnchor(edge, pos)

        self.node.updateHandles()
        self.node.updateTextPos(moved=self.data['redo']['moved'])
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

        self.node.background = self.data['undo']['background']
        self.node.selection = self.data['undo']['selection']
        self.node.polygon = self.data['undo']['polygon']

        for edge, pos in self.data['undo']['anchors'].items():
            self.node.setAnchor(edge, pos)

        self.node.updateHandles()
        self.node.updateTextPos(moved=self.data['undo']['moved'])
        self.node.updateEdges()
        self.node.update()

        # TURN CACHING ON
        for edge in self.node.edges:
            edge.setCacheMode(AbstractItem.DeviceCoordinateCache)

        self.diagram.sgnUpdated.emit()


class CommandNodeMove(QUndoCommand):
    """
    This command is used to move nodes (1 or more).
    """
    def __init__(self, diagram, data):
        """
        Initialize the command.
        :type diagram: Diagram
        :type data: dict
        """
        self.data = data
        self.diagram = diagram
        self.edges = set()

        for node in data['redo']['nodes']:
            self.edges |= node.edges

        if len(data['redo']['nodes']) != 1:
            name = _('COMMAND_NODE_MOVE_MULTI', len(data['redo']['nodes']))
        else:
            name = _('COMMAND_NODE_MOVE', first(data['redo']['nodes'].keys()).name)

        super().__init__(name)

    def redo(self):
        """redo the command"""
        # Turn off caching.
        for edge in self.edges:
            edge.setCacheMode(AbstractItem.NoCache)
        # Update edges breakpoints.
        for edge, breakpoints in self.data['redo']['edges'].items():
            for i in range(len(breakpoints)):
                edge.breakpoints[i] = breakpoints[i]
        # Update nodes positions.
        for node, data in self.data['redo']['nodes'].items():
            node.setPos(data['pos'])
            # Update edge anchors.
            for edge, pos in data['anchors'].items():
                node.setAnchor(edge, pos)
        # Update edges.
        for edge in self.edges:
            edge.updateEdge()
        # Turn on caching.
        for edge in self.edges:
            edge.setCacheMode(AbstractItem.DeviceCoordinateCache)
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # Turn off caching.
        for edge in self.edges:
            edge.setCacheMode(AbstractItem.NoCache)
        # Update edges breakpoints.
        for edge, breakpoints in self.data['undo']['edges'].items():
            for i in range(len(breakpoints)):
                edge.breakpoints[i] = breakpoints[i]
        # Update nodes positions.
        for node, data in self.data['undo']['nodes'].items():
            node.setPos(data['pos'])
            # Update edge anchors.
            for edge, pos in data['anchors'].items():
                node.setAnchor(edge, pos)
        # Update edges.
        for edge in self.edges:
            edge.updateEdge()
        # Turn caching ON.
        for edge in self.edges:
            edge.setCacheMode(AbstractItem.DeviceCoordinateCache)
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()


class CommandNodeLabelMove(QUndoCommand):
    """
    This command is used to move nodes labels.
    """
    def __init__(self, diagram, node, pos1, pos2):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node: AbstractNode
        :type pos1: QPointF
        :type pos2: QPointF
        """
        super().__init__(_('COMMAND_NODE_MOVE_LABEL', node.name))
        self.diagram = diagram
        self.node = node
        self.data = {'undo': pos1, 'redo': pos2}

    def redo(self):
        """redo the command"""
        self.node.setTextPos(self.data['redo'])
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.node.setTextPos(self.data['undo'])
        self.diagram.sgnUpdated.emit()


class CommandNodeLabelChange(QUndoCommand):
    """
    This command is used to edit nodes labels.
    """
    def __init__(self, diagram, node, undo, redo, name=None):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node: AbstractNode
        :type undo: str
        :type redo: str
        :type name: str
        """
        super().__init__(name or _('COMMAND_NODE_EDIT_LABEL', node.name))
        self.diagram = diagram
        self.project = diagram.project
        self.node = node
        self.data = {'undo': undo, 'redo': redo}

    def redo(self):
        """redo the command"""
        # If the command is executed in a "refactor" command we won't have
        # any meta except for the first node in the refactored collection
        # so we don't have to remove nor add predicates from the meta index.
        meta = self.project.meta(self.node.type(), self.data['undo'])
        if meta:
            self.project.removeMeta(self.node.type(), self.data['undo'])

        self.project.doRemoveItem(self.diagram, self.node)
        self.node.setText(self.data['redo'])
        self.project.doAddItem(self.diagram, self.node)

        if meta:
            meta.predicate = self.data['redo']
            self.project.addMeta(self.node.type(), self.data['redo'], meta)

        if self.node.type() is Item.IndividualNode:
            # Perform re-identification of connected Enumeration nodes.
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.EnumerationNode
            for node in self.node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                self.diagram.identify(node)

        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # If the command is executed in a "refactor" command we won't have
        # any meta except for the first node in the refactored collection
        # so we don't have to remove nor add predicates from the meta index.
        meta = self.project.meta(self.node.type(), self.data['redo'])
        if meta:
            self.project.removeMeta(self.node.type(), self.data['redo'])

        self.project.doRemoveItem(self.diagram, self.node)
        self.node.setText(self.data['undo'])
        self.project.doAddItem(self.diagram, self.node)

        if meta:
            meta.predicate = self.data['undo']
            self.project.addMeta(self.node.type(), self.data['undo'], meta)

        if self.node.type() is Item.IndividualNode:
            # Perform re-identification of connected Enumeration nodes.
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.EnumerationNode
            for node in self.node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                self.diagram.identify(node)

        self.diagram.sgnUpdated.emit()


class CommandNodeOperatorSwitchTo(QUndoCommand):
    """
    This command is used to change the type of hexagon based operator nodes.
    """
    def __init__(self, diagram, node1, node2):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node1: OperatorNode
        :type node2: OperatorNode
        """
        super().__init__(_('COMMAND_NODE_OPERATOR_SWITCH', node1.name, node2.name))
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
        self.diagram.identify(self.node['redo'])

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
        self.diagram.identify(self.node['undo'])

        # Clear edge and anchor references from node2.
        self.node['redo'].anchors.clear()
        self.node['redo'].edges.clear()

        # Remove the new node from the diagram.
        self.diagram.removeItem(self.node['redo'])
        self.diagram.sgnItemRemoved.emit(self.diagram, self.node['redo'])
        self.diagram.sgnUpdated.emit()


class CommandNodeChangeMeta(QUndoCommand):
    """
    This command is used to change predicate nodes metadata.
    """
    def __init__(self, diagram, node, undo, redo, name=None):
        """
        Initialize the command.
        :type diagram: Diagram
        :type node: AbstractNode
        :type undo: PredicateMetadata
        :type redo: PredicateMetadata
        :type name: str
        """
        super().__init__(name or _('COMMAND_NODE_CHANGE_META', node.name))
        self.project = diagram.project
        self.data = {'redo': redo, 'undo': undo}
        self.node = node

    def redo(self):
        """redo the command"""
        self.project.addMeta(self.node.type(), self.node.text(), self.data['redo'])

    def undo(self):
        """undo the command"""
        self.project.addMeta(self.node.type(), self.node.text(), self.data['undo'])


class CommandNodeChangeInputsOrder(QUndoCommand):
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
        super().__init__(_('COMMAND_NODE_CHANGE_INPUTS_ORDER', node.name))

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


class CommandNodeSetBrush(QUndoCommand):
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
        self.brush = {x: {'undo': x.brush, 'redo': brush} for x in nodes}
        self.diagram = diagram
        super().__init__(_('COMMAND_NODE_SET_BRUSH', brush.color().name(), len(nodes)))

    def redo(self):
        """redo the command"""
        for node in self.nodes:
            node.brush = self.brush[node]['redo']
            node.redraw(selected=node.isSelected())
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """redo the command"""
        for node in self.nodes:
            node.brush = self.brush[node]['undo']
            node.redraw(selected=node.isSelected())
        self.diagram.sgnUpdated.emit()