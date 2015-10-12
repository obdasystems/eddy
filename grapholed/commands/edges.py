# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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
        self.scene = scene
        self.edge = edge

    def redo(self):
        """redo the command"""
        self.scene.addItem(self.edge)

    def undo(self):
        """undo the command"""
        self.scene.removeItem(self.edge)


class CommandEdgeBreakpointAdd(QUndoCommand):
    """
    This command is used to add a breakpoint on the given edge.
    """
    def __init__(self, edge, index, point):
        """
        Initialize the command.
        :param edge: the edge on which the break point is being added.
        :param index: the index of the new breakpoint.
        :param point: the breakpoint.
        """
        super().__init__('add {0} edge breakpoint'.format(edge.name))
        self.edge = edge
        self.index = index
        self.point = point

    def redo(self):
        """redo the command"""
        self.edge.breakpoints.insert(self.index, self.point)
        self.edge.updateEdge()

    def undo(self):
        """undo the command"""
        self.edge.breakpoints.pop(self.index)
        self.edge.updateEdge()


class CommandEdgeAnchorMove(QUndoCommand):
    """
    This command is used to move edge anchor points.
    """
    def __init__(self, edge, node):
        """
        Initialize the command.
        :param edge: the edge whose anchor point is being moved.
        :param node: the shape on which the moving is happening.
        """
        super().__init__('move {0} anchor point'.format(edge.name))
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

    def undo(self):
        """undo the command"""
        self.node.setAnchor(self.edge, self.pos1)
        self.edge.updateEdge()


class CommandEdgeBreakpointMove(QUndoCommand):
    """
    This command is used to move edge breakpoints.
    """
    def __init__(self, edge, index):
        """
        Initialize the command.
        :param edge: the edge whose breakpoint is being moved.
        :param index: the index of the breakpoint.
        """
        super().__init__('move {0} edge breakpoint'.format(edge.name))
        self.edge = edge
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

    def undo(self):
        """undo the command"""
        self.edge.breakpoints[self.index] = self.pos1
        self.edge.updateEdge()


class CommandEdgeBreakpointDel(QUndoCommand):
    """
    This command is used to delete edge breakpoints.
    """
    def __init__(self, edge, index):
        """
        Initialize the command.
        :param edge: the edge whose breakpoint is being deleted.
        :param index: the index of the breakpoint.
        """
        super().__init__('remove {0} edge breakpoint'.format(edge.name))
        self.edge = edge
        self.index = index
        self.point = edge.breakpoints[self.index]

    def redo(self):
        """redo the command"""
        self.edge.breakpoints.pop(self.index)
        self.edge.updateEdge()

    def undo(self):
        """undo the command"""
        self.edge.breakpoints.insert(self.index, self.point)
        self.edge.updateEdge()