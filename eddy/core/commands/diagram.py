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


class CommandDiagramAdd(QtWidgets.QUndoCommand):
    """
    Extends QtWidgets.QUndoCommand with facilities to add a Diagram to a Project.
    """
    def __init__(self, diagram, project):
        """
        Initialize the command.
        :type diagram: Diagram
        :type project: Project
        """
        super().__init__("add diagram '{0}'".format(diagram.name))
        self.project = project
        self.diagram = diagram
        self.parents = dict(undo=diagram.parent(), redo=self.project)

    def redo(self):
        """redo the command"""
        self.diagram.setParent(self.parents['redo'])
        self.project.addDiagram(self.diagram)
        for item in self.project.items():
            item.updateEdgeOrNode()
        self.project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.diagram.setParent(self.parents['undo'])
        self.project.removeDiagram(self.diagram)
        self.project.sgnUpdated.emit()


class CommandDiagramRemove(QtWidgets.QUndoCommand):
    """
    Extends QtWidgets.QUndoCommand with facilities to remove a Diagram from a Project.
    """
    def __init__(self, diagram, project):
        """
        Initialize the command.
        :type diagram: Diagram
        :type project: Project
        """
        super().__init__("remove diagram '{0}'".format(diagram.name))
        self.diagram = diagram
        self.project = project

    def redo(self):
        """redo the command"""
        self.project.removeDiagram(self.diagram)
        self.project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.project.addDiagram(self.diagram)
        self.project.sgnUpdated.emit()


class CommandDiagramRename(QtWidgets.QUndoCommand):
    """
    Extends QtWidgets.QUndoCommand with facilities to rename a Diagram.
    """
    def __init__(self, undo, redo, diagram, project):
        """
        Initialize the command.
        :type undo: str
        :type redo: str
        :type diagram: Diagram
        :type project: Project
        """
        super().__init__("rename diagram '{0}' to '{1}'".format(undo, redo))
        self.diagram = diagram
        self.project = project
        self.undo = undo
        self.redo = redo

    def redo(self):
        """redo the command"""
        self.project.removeDiagram(self.diagram)
        self.diagram.name = self.redo
        self.project.addDiagram(self.diagram)
        self.project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.project.removeDiagram(self.diagram)
        self.diagram.name = self.undo
        self.project.addDiagram(self.diagram)
        self.project.sgnUpdated.emit()


class CommandDiagramResize(QtWidgets.QUndoCommand):
    """
    This command is used to resize the size of a diagram.
    """
    def __init__(self, diagram, rect):
        """
        Initialize the command.
        :type diagram: Diagram
        :type rect: QRectF
        """
        super().__init__('resize diagram')
        self.diagram = diagram
        self.rect = {'redo': rect, 'undo': diagram.sceneRect()}

    def redo(self):
        """redo the command"""
        self.diagram.setSceneRect(self.rect['redo'])
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.diagram.setSceneRect(self.rect['undo'])
        self.diagram.sgnUpdated.emit()