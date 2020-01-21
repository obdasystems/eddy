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
from eddy.core.functions.signals import connect, disconnect
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
        #print('CommandProjectSetIRI >>> init')
        super().__init__("set ontology IRI to '{0}'".format(redo))
        self._project = project
        self._undo = undo
        self._redo = redo


    def redo(self):
        """redo the command"""
        #print('CommandProjectSetIRI >>> redo')
        self._project.ontologyIRI = self._redo
        self._project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        #print('CommandProjectSetIRI >>> undo')
        self._project.ontologyIRI = self._undo
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
        #print('CommandProjectSetPrefix >>> init')
        super().__init__("set ontology prefix to '{0}'".format(redo))
        self._project = project
        self._undo = undo
        self._redo = redo

    def redo(self):
        """redo the command"""
        #print('CommandProjectSetPrefix >>> redo')
        self._project.prefix = self._redo
        self._project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        #print('CommandProjectSetPrefix >>> undo')
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

        # Emit updated signals.
        self.project.session.sgnUpdateState.emit()
        self.project.sgnUpdated.emit()


class CommandProjectDisconnectSpecificSignals(QtWidgets.QUndoCommand):

    def __init__(self, project, **kwargs):

        super().__init__("Connect/disconnect specific signals")
        self.project = project
        self.add_item_to_IRI_prefixes_nodes_dict = kwargs.get('add_item_to_IRI_prefixes_nodes_dict', True)
        self.remove_item_from_IRI_prefixes_nodes_dict = kwargs.get('remove_item_from_IRI_prefixes_nodes_dict', True)
        self.regenerate_label_of_nodes_for_iri = kwargs.get('regenerate_label_of_nodes_for_iri', True)

    def undo(self):

        if self.add_item_to_IRI_prefixes_nodes_dict is True:
            connect(self.project.sgnItemAdded, self.project.add_item_to_IRI_prefixes_nodes_dict)
        if self.remove_item_from_IRI_prefixes_nodes_dict is True:
            connect(self.project.sgnItemRemoved, self.project.remove_item_from_IRI_prefixes_nodes_dict)
        if self.regenerate_label_of_nodes_for_iri is True:
            connect(self.project.sgnIRIPrefixNodeDictionaryUpdated, self.project.regenerate_label_of_nodes_for_iri)

    def redo(self):

        if self.add_item_to_IRI_prefixes_nodes_dict is True:
            disconnect(self.project.sgnItemAdded, self.project.add_item_to_IRI_prefixes_nodes_dict)
        if self.remove_item_from_IRI_prefixes_nodes_dict is True:
            disconnect(self.project.sgnItemRemoved, self.project.remove_item_from_IRI_prefixes_nodes_dict)
        if self.regenerate_label_of_nodes_for_iri is True:
            disconnect(self.project.sgnIRIPrefixNodeDictionaryUpdated, self.project.regenerate_label_of_nodes_for_iri)


class CommandProjectConnectSpecificSignals(QtWidgets.QUndoCommand):

    def __init__(self, project, **kwargs):

        super().__init__("Connect/disconnect specific signals")
        self.project = project
        self.add_item_to_IRI_prefixes_nodes_dict = kwargs.get('add_item_to_IRI_prefixes_nodes_dict', True)
        self.remove_item_from_IRI_prefixes_nodes_dict = kwargs.get('remove_item_from_IRI_prefixes_nodes_dict', True)
        self.regenerate_label_of_nodes_for_iri = kwargs.get('regenerate_label_of_nodes_for_iri', True)

    def redo(self):

        if self.add_item_to_IRI_prefixes_nodes_dict is True:
            connect(self.project.sgnItemAdded, self.project.add_item_to_IRI_prefixes_nodes_dict)
        if self.remove_item_from_IRI_prefixes_nodes_dict is True:
            connect(self.project.sgnItemRemoved, self.project.remove_item_from_IRI_prefixes_nodes_dict)
        if self.regenerate_label_of_nodes_for_iri is True:
            connect(self.project.sgnIRIPrefixNodeDictionaryUpdated, self.project.regenerate_label_of_nodes_for_iri)

    def undo(self):

        if self.add_item_to_IRI_prefixes_nodes_dict is True:
            disconnect(self.project.sgnItemAdded, self.project.add_item_to_IRI_prefixes_nodes_dict)
        if self.remove_item_from_IRI_prefixes_nodes_dict is True:
            disconnect(self.project.sgnItemRemoved, self.project.remove_item_from_IRI_prefixes_nodes_dict)
        if self.regenerate_label_of_nodes_for_iri is True:
            disconnect(self.project.sgnIRIPrefixNodeDictionaryUpdated, self.project.regenerate_label_of_nodes_for_iri)