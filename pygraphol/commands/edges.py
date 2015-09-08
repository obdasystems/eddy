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


class CommandEdgeAdd(QUndoCommand):
    """
    This command is used to add edges to the graphic scene.
    """
    def __init__(self, scene, edge):
        """
        Initialize the command.
        :param scene: the graphic scene where this command is being performed.
        :param edge: the edge being added.
        """
        super().__init__('add %s edge' % edge.name)
        self.scene = scene
        self.edge = edge

    def redo(self):
        """redo the command"""
        self.scene.itemList.append(self.edge)
        self.scene.addItem(self.edge.shape)

    def undo(self):
        """undo the command"""
        self.scene.itemList.remove(self.edge)
        self.scene.removeItem(self.edge.shape)


class CommandEdgeAddBreakPoint(QUndoCommand):
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
        super().__init__('add %s edge breakpoint' % edge.name)
        self.edge = edge
        self.index = index
        self.point = point

    def redo(self):
        """redo the command"""
        self.edge.shape.breakpoints.insert(self.index, self.point)
        self.edge.shape.updateEdge()

    def undo(self):
        """undo the command"""
        self.edge.shape.breakpoints.pop(self.index)
        self.edge.shape.updateEdge()


class CommandEdgeMoveBreakPoint(QUndoCommand):
    """
    This command is used to move edge breakpoints.
    """
    def __init__(self, edge, index):
        """
        Initialize the command.
        :param edge: the edge whose breakpoint is being moved.
        :param index: the index of the breakpoint.
        """
        super().__init__('move %s edge breakpoint' % edge.name)
        self.edge = edge
        self.index = index
        self.old = edge.shape.breakpoints[self.index]
        self.new = None

    def redo(self):
        """redo the command"""
        if self.new:
            self.edge.shape.breakpoints[self.index] = self.new
            self.edge.shape.breakpoints[self.index] = self.new
            self.edge.shape.updateEdge()

    def undo(self):
        """undo the command"""
        self.edge.shape.breakpoints[self.index] = self.old
        self.edge.shape.breakpoints[self.index] = self.old
        self.edge.shape.updateEdge()


class CommandEdgeRemoveBreakPoint(QUndoCommand):
    """
    This command is used to delete edge breakpoints.
    """
    def __init__(self, edge, index):
        """
        Initialize the command.
        :param edge: the edge whose breakpoint is being deleted.
        :param index: the index of the breakpoint.
        """
        super().__init__('remove %s edge breakpoint' % edge.name)
        self.edge = edge
        self.index = index
        self.point = edge.shape.breakpoints[self.index]

    def redo(self):
        """redo the command"""
        self.edge.shape.breakpoints.pop(self.index)
        self.edge.shape.updateEdge()

    def undo(self):
        """undo the command"""
        self.edge.shape.breakpoints.insert(self.index, self.point)
        self.edge.shape.updateEdge()


class CommandEdgeLabelMove(QUndoCommand):
    """
    This command is used to move edge labels.
    """
    def __init__(self, edge, moved):
        """
        Initialize the command
        :param edge: the edge whose label is being moved.
        :param moved: whether the label was moved already or not
        """
        super().__init__('move %s edge label' % edge.name)
        self.moved = moved
        self.edge = edge
        self.old = edge.shape.label.pos()
        self.new = None

    def redo(self):
        """redo the command"""
        if self.new:
            self.edge.shape.label.setPos(self.new)
            self.edge.shape.label.moved = not self.moved

    def undo(self):
        """undo the command"""
        self.edge.shape.label.setPos(self.old)
        self.edge.shape.label.moved = self.moved