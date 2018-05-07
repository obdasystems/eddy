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
#from eddy.ui.ontology_consistency_check import InconsistentOntologyDialog

class FetchReasonerVariables:

    def __init__(self, project, **kwargs):

        ###  variables controlled by reasoners  ###
        self.ontology_OWL = project.ontology_OWL
        self.axioms_to_nodes_edges_mapping = project.axioms_to_nodes_edges_mapping

        self.unsatisfiable_classes = project.unsatisfiable_classes
        self.explanations_for_unsatisfiable_classes = project.explanations_for_unsatisfiable_classes
        self.unsatisfiable_attributes = project.unsatisfiable_attributes
        self.explanations_for_unsatisfiable_attributes = project.explanations_for_unsatisfiable_attributes
        self.unsatisfiable_roles = project.unsatisfiable_roles
        self.explanations_for_unsatisfiable_roles = project.explanations_for_unsatisfiable_roles

        self.inconsistent_ontology = project.inconsistent_ontology
        self.explanations_for_inconsistent_ontology = project.explanations_for_inconsistent_ontology

        self.uc_as_input_for_explanation_explorer = project.uc_as_input_for_explanation_explorer
        self.nodes_of_unsatisfiable_entities = project.nodes_of_unsatisfiable_entities
        self.nodes_or_edges_of_axioms_to_display_in_widget = project.nodes_or_edges_of_axioms_to_display_in_widget
        self.nodes_or_edges_of_explanations_to_display_in_widget = project.nodes_or_edges_of_explanations_to_display_in_widget

        self.converted_nodes = project.converted_nodes

        ### $$ END $$ variables controlled by reasoners $$ END $$ ###



class CommandProjectSetVariablesControlledByReasoner(QtWidgets.QUndoCommand):

    def __init__(self, project, session, undo, redo, **kwargs):
        super().__init__("set variables controlled by reasoner ")
        self._project = project
        self._undo = undo
        self._redo = redo
        self._session = session
        self.reasoner_active = kwargs.get('reasoner_active', 'inactive')

    def redo(self):
        """redo the command"""
        if (self._redo is None) or (self._redo == 'empty'):

            ###  variables controlled by reasoners  ###
            self._session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='Unsatisfiable_Entity_Explorer')
            self._session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='Explanation_explorer')
            self._session.BackgrounddeColourNodesAndEdges(call_ClearInconsistentEntitiesAndDiagItemsData=True)

            ### $$ END $$ variables controlled by reasoners $$ END $$ ###

        else:

            ###  variables controlled by reasoners  ###
            self._project.ontology_OWL = self._redo.ontology_OWL
            self._project.axioms_to_nodes_edges_mapping = self._redo.axioms_to_nodes_edges_mapping

            self._project.unsatisfiable_classes = self._redo.unsatisfiable_classes
            self._project.explanations_for_unsatisfiable_classes = self._redo.explanations_for_unsatisfiable_classes
            self._project.unsatisfiable_attributes = self._redo.unsatisfiable_attributes
            self._project.explanations_for_unsatisfiable_attributes = self._redo.explanations_for_unsatisfiable_attributes
            self._project.unsatisfiable_roles = self._redo.unsatisfiable_roles
            self._project.explanations_for_unsatisfiable_roles = self._redo.explanations_for_unsatisfiable_roles

            self._project.inconsistent_ontology = self._redo.inconsistent_ontology
            self._project.explanations_for_inconsistent_ontology = self._redo.explanations_for_inconsistent_ontology

            self._project.uc_as_input_for_explanation_explorer = self._redo.uc_as_input_for_explanation_explorer
            self._project.nodes_of_unsatisfiable_entities = self._redo.nodes_of_unsatisfiable_entities
            self._project.nodes_or_edges_of_axioms_to_display_in_widget = self._redo.nodes_or_edges_of_axioms_to_display_in_widget
            self._project.nodes_or_edges_of_explanations_to_display_in_widget = self._redo.nodes_or_edges_of_explanations_to_display_in_widget

            self._project.converted_nodes = self._redo.converted_nodes

            if self.reasoner_active == 'was_unsatisfiable':
                self._session.pmanager.create_add_and_start_plugin('Unsatisfiable_Entity_Explorer')
            elif self.reasoner_active == 'was_inconsistent':
                pass
                #dialog = InconsistentOntologyDialog(self.project, None, self.session)
                #dialog.exec_()
            else:
                pass

            ### $$ END $$ variables controlled by reasoners $$ END $$ ###

        self._project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        if (self._undo is None) or (self._undo == 'empty'):

            ###  variables controlled by reasoners  ###
            self._session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='Unsatisfiable_Entity_Explorer')
            self._session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='Explanation_explorer')
            self._session.BackgrounddeColourNodesAndEdges(call_ClearInconsistentEntitiesAndDiagItemsData=True)

            ### $$ END $$ variables controlled by reasoners $$ END $$ ###

        else:

            ###  variables controlled by reasoners  ###
            self._project.ontology_OWL = self._undo.ontology_OWL
            self._project.axioms_to_nodes_edges_mapping = self._undo.axioms_to_nodes_edges_mapping

            self._project.unsatisfiable_classes = self._undo.unsatisfiable_classes
            self._project.explanations_for_unsatisfiable_classes = self._undo.explanations_for_unsatisfiable_classes
            self._project.unsatisfiable_attributes = self._undo.unsatisfiable_attributes
            self._project.explanations_for_unsatisfiable_attributes = self._undo.explanations_for_unsatisfiable_attributes
            self._project.unsatisfiable_roles = self._undo.unsatisfiable_roles
            self._project.explanations_for_unsatisfiable_roles = self._undo.explanations_for_unsatisfiable_roles

            self._project.inconsistent_ontology = self._undo.inconsistent_ontology
            self._project.explanations_for_inconsistent_ontology = self._undo.explanations_for_inconsistent_ontology

            self._project.uc_as_input_for_explanation_explorer = self._undo.uc_as_input_for_explanation_explorer
            self._project.nodes_of_unsatisfiable_entities = self._undo.nodes_of_unsatisfiable_entities
            self._project.nodes_or_edges_of_axioms_to_display_in_widget = self._undo.nodes_or_edges_of_axioms_to_display_in_widget
            self._project.nodes_or_edges_of_explanations_to_display_in_widget = self._undo.nodes_or_edges_of_explanations_to_display_in_widget

            self._project.converted_nodes = self._undo.converted_nodes

            if self.reasoner_active == 'was_unsatisfiable':
                self._session.pmanager.create_add_and_start_plugin('Unsatisfiable_Entity_Explorer')
            elif self.reasoner_active == 'was_inconsistent':
                pass
                #dialog = InconsistentOntologyDialog(self.project, None, self.session)
                #dialog.exec_()
            else:
                pass

            ### $$ END $$ variables controlled by reasoners $$ END $$ ###

        self._project.sgnUpdated.emit()


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
        self._project.iri = self._redo
        self._project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        #print('CommandProjectSetIRI >>> undo')
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