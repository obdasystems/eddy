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
from eddy.core.commands.labels import CommandLabelChange, GenerateNewLabel


class CommandProjetSetIRIPrefixesNodesDict(QtWidgets.QUndoCommand):

    def __init__(self, project, dict_old_val, dict_new_val, iris_to_update, nodes_to_update):

        #print('>>>      CommandProjetSetIRIPrefixesNodesDict  __init__')

        super().__init__('update dictionary')

        self.project = project
        self.dict_old_val = dict_old_val
        self.dict_new_val = dict_new_val
        self.iris_to_update = iris_to_update
        self.nodes_to_update = nodes_to_update

    def redo(self):
        #print('>>>      CommandProjetSetIRIPrefixesNodesDict  (redo)')

        self.project.IRI_prefixes_nodes_dict.clear()
        self.project.IRI_prefixes_nodes_dict = self.project.copy_IRI_prefixes_nodes_dictionaries(self.dict_new_val,dict())

        if len(self.iris_to_update) > 0:
            for iri in self.iris_to_update:
                if self.nodes_to_update is None:
                    #print('self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, None) -', iri)
                    self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, None, None)
                else:
                    for n in self.nodes_to_update:
                        #print('self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, n)', iri, ' - ',n)
                        if n.diagram is not None:
                            self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, str(n), str(n.diagram.name))
                        else:
                            self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, str(n), None)

            self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(None, None, None)

        #print('>>>      CommandProjetSetIRIPrefixesNodesDict  (redo) END')

    def undo(self):
        #print('>>>      CommandProjetSetIRIPrefixesNodesDict  (undo)')

        self.project.IRI_prefixes_nodes_dict.clear()
        self.project.IRI_prefixes_nodes_dict = self.project.copy_IRI_prefixes_nodes_dictionaries(self.dict_old_val,dict())

        if len(self.iris_to_update) > 0:
            for iri in self.iris_to_update:
                if self.nodes_to_update is None:
                    #print('self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, None) -', iri)
                    self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, None, None)
                else:
                    for n in self.nodes_to_update:
                        #print('self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, n)', iri, ' - ',n)
                        if n.diagram is not None:
                            self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, str(n), str(n.diagram.name))
                        else:
                            self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(iri, str(n), None)
        else:
            self.project.sgnIRIPrefixNodeDictionaryUpdated.emit(None, None, None)

        #print('>>>      CommandProjetSetIRIPrefixesNodesDict  (undo) END')


class CommandProjetSetIRIofCutNodes(QtWidgets.QUndoCommand):


    def __init__(self, list_undo, list_redo, project):

        super().__init__('add {0}'.format(project.name))
        self.list_undo = list_undo
        self.list_redo = list_redo
        self.project = project

    def redo(self):
        """redo the command"""
        new_list = []
        for ele in self.list_redo:
            new_list.append(ele)
        self.project.iri_of_cut_nodes = new_list

    def undo(self):
        """undo the command"""
        old_list = []
        for ele in self.list_undo:
            old_list.append(ele)
        self.project.iri_of_cut_nodes = old_list


class CommandNodeSetRemainingCharacters(QtWidgets.QUndoCommand):

    def __init__(self, rc_undo, rc_redo, node, project, **kwargs):
        """
        Initialize the command.
        :type project: Project
        :type node: AbstractNode
        """
        super().__init__('add {0}'.format(node.name))
        self.rc_undo = rc_undo
        self.rc_redo = rc_redo
        self.node = node
        self.project = project
        self.regenerate_label = kwargs.get('regenerate_label',True)

    def redo(self):
        """redo the command"""
        self.node.remaining_characters = self.rc_redo.replace('\n','')

        if self.regenerate_label is True:
            old_text = self.node.text()
            new_text = GenerateNewLabel(self.project, self.node, remaining_characters=self.rc_redo).return_label()

            CommandLabelChange(self.node.diagram, self.node, old_text, new_text).redo()


    def undo(self):
        """undo the command"""
        self.node.remaining_characters = self.rc_undo.replace('\n','')

        if self.regenerate_label is True:
            new_text = self.node.text()
            old_text = GenerateNewLabel(self.project, self.node, remaining_characters=self.rc_undo).return_label()

            CommandLabelChange(self.node.diagram, self.node, old_text, new_text).undo()


class CommandProjectORNodeSetPreferedPrefix(QtWidgets.QUndoCommand):

    def __init__(self, project, dict_old_val, dict_new_val, iri_to_update, nodes_to_update):
        super().__init__('update dictionary')

        self.project = project
        self.dict_old_val = dict_old_val
        self.dict_new_val = dict_new_val
        self.iri_to_update = iri_to_update
        self.nodes_to_update = nodes_to_update

    def redo(self):
        #print('>>>      CommandProjectORNodeSetPreferedPrefix  (redo)')

        prefered_prefix = self.dict_new_val[self.iri_to_update]

        self.project.prefered_prefix_dict.clear()
        self.project.prefered_prefix_dict = self.project.copy_prefered_prefix_dictionaries(self.dict_new_val,dict())

        if self.nodes_to_update is None:
            #print('self.project.sgnPreferedPrefixeDictionaryUpdated.emit(iri, None) -', self.iri_to_update)
            self.project.sgnPreferedPrefixDictionaryUpdated.emit(self.iri_to_update, None, prefered_prefix)
        else:
            for n in self.nodes_to_update:
                #print('self.project.sgnPreferedPrefixeDictionaryUpdated.emit(iri, n)', self.iri_to_update, ' - ',n)
                self.project.sgnPreferedPrefixDictionaryUpdated.emit(self.iri_to_update, str(n), prefered_prefix)


        #print('>>>      CommandProjectORNodeSetPreferedPrefix  (redo) END')

    def undo(self):
        #print('>>>      CommandProjectORNodeSetPreferedPrefix  (undo)')

        prefered_prefix = self.dict_old_val[self.iri_to_update]

        self.project.prefered_prefix_dict.clear()
        self.project.prefered_prefix_dict = self.project.copy_prefered_prefix_dictionaries(self.dict_old_val,dict())

        if self.nodes_to_update is None:
            #print('self.project.sgnPreferedPrefixeDictionaryUpdated.emit(iri, None) -', self.iri_to_update)
            self.project.sgnPreferedPrefixDictionaryUpdated.emit(self.iri_to_update, None, prefered_prefix)
        else:
            for n in self.nodes_to_update:
                #print('self.project.sgnPreferedPrefixeDictionaryUpdated.emit(iri, n)', self.iri_to_update, ' - ',n)
                self.project.sgnPreferedPrefixDictionaryUpdated.emit(self.iri_to_update, str(n), prefered_prefix)

        #print('>>>      CommandProjectORNodeSetPreferedPrefix  (undo) END')