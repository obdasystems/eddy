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


class CommandProjectSetIRI(QtWidgets.QUndoCommand):
    """
    This command is used to set the IRI of a project.
    """
    def __init__(self, project, undo, redo):
        """
        Initialize the command.
        :type project: Project
        :type undo: str
        :type redo: str
        """
        super().__init__("set ontology IRI to '{0}'".format(redo))
        self._project = project
        self._undo = undo
        self._redo = redo

    def redo(self):
        """redo the command"""
        self._project.iri = self._redo
        self._project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self._project.iri = self._undo
        self._project.sgnUpdated.emit()


class CommandProjectSetPrefix(QtWidgets.QUndoCommand):
    """
    This command is used to set the prefix of a project.
    """
    def __init__(self, project, undo, redo):
        """
        Initialize the command.
        :type project: Project
        :type undo: str
        :type redo: str
        """
        super().__init__("set ontology prefix to '{0}'".format(redo))
        self._project = project
        self._undo = undo
        self._redo = redo

    def redo(self):
        """redo the command"""
        self._project.prefix = self._redo
        self._project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self._project.prefix = self._undo
        self._project.sgnUpdated.emit()


class CommandProjectSetVersion(QtWidgets.QUndoCommand):
    """
    This command is used to set the version of an ontology.
    """
    def __init__(self, project, undo, redo):
        """
        Initialize the command.
        :type project: Project
        :type undo: str
        :type redo: str
        """
        super().__init__("set ontology version to '{0}'".format(redo))
        self._project = project
        self._undo = undo
        self._redo = redo

    def redo(self):
        """redo the command"""
        self._project.version = self._redo
        self._project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self._project.version = self._undo
        self._project.sgnUpdated.emit()


class CommandProjectSetProfile(QtWidgets.QUndoCommand):
    """
    This command is used to set the profile of a project.
    """
    def __init__(self, project, undo, redo):
        """
        Initialize the command.
        :type project: Project
        :type undo: OWLProfile
        :type redo: OWLProfile
        """
        super().__init__("set project profile to '{0}'".format(redo))
        self.project = project
        self.data = {'undo': undo, 'redo': redo}

    def redo(self):
        """redo the command"""
        self.project.profile = self.project.session.createProfile(self.data['redo'], self.project)
        # Reshape all the Role and Attribute nodes to show/hide functionality and inverse functionality.
        for node in self.project.nodes():
            if node.type() in {Item.RoleNode, Item.AttributeNode}:
                node.updateNode(selected=node.isSelected())
        # Emit updated signals.
        self.project.session.sgnUpdateState.emit()
        self.project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.project.profile = self.project.session.createProfile(self.data['undo'], self.project)
        # Reshape all the Role and Attribute nodes to show/hide functionality and inverse functionality.
        for node in self.project.nodes():
            if node.type() in {Item.RoleNode, Item.AttributeNode}:
                node.updateNode(selected=node.isSelected())
                # Emit updated signals.
        self.project.session.sgnUpdateState.emit()
        self.project.sgnUpdated.emit()