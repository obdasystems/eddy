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

from eddy.core.datatypes.owl import OWLStandardIRIPrefixPairsDict
from eddy.core.commands.labels import CommandLabelChange, GenerateNewLabel

class CommandNodeSetIRIPrefixAndRemainingCharacters(QtWidgets.QUndoCommand):

    def __init__(self, project, node, undo_iri, redo_iri, undo_prefix, redo_prefix, undo_remaining_characters, redo_remaining_characters, new_label_undo=None, new_label_redo=None):

        super().__init__('switch iri from {0} to {1} ,prefix from {2} to {3} and remaining characters from {4} to {5}'.format(undo_iri, redo_iri, undo_prefix, redo_prefix, undo_remaining_characters, redo_remaining_characters))

        self.project = project
        self.node = node
        self.undo_iri = undo_iri
        self.undo_prefix = undo_prefix
        self.undo_remaining_characters = undo_remaining_characters
        self.redo_iri = redo_iri
        self.redo_prefix = redo_prefix
        self.redo_remaining_characters = redo_remaining_characters
        self.new_label_to_set_redo = new_label_redo
        self.new_label_to_set_undo = new_label_undo

    def redo(self):
        """redo the command"""

        print('>>>          CommandNodeSetIRIPrefixAndRemainingCharacters (redo)')

        self.node.iri = self.redo_iri
        self.node.prefix = self.redo_prefix
        self.node.remaining_characters = self.redo_remaining_characters

        if self.node.iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
            self.node.label._editable = False
        else:
            self.node.label._editable = True

        if self.new_label_to_set_redo is not None:
            new_text = self.new_label_to_set_redo
        else:
            new_text = GenerateNewLabel(self.project,self.redo_iri,self.redo_prefix,\
                                        self.redo_remaining_characters).return_label()

        print('new_text',new_text)

        CommandLabelChange(self.node.diagram,self.node,self.node.text(),new_text).redo()

    def undo(self):
        """undo the command"""
        print('>>>          CommandNodeSetIRIPrefixAndRemainingCharacters (undo)')

        self.node.iri = self.undo_iri
        self.node.prefix = self.undo_prefix
        self.node.remaining_characters = self.undo_remaining_characters

        if self.node.iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
            self.node.label._editable = False
        else:
            self.node.label._editable = True

        if self.new_label_to_set_undo is not None:
            old_text = self.new_label_to_set_undo
        else:
            old_text = GenerateNewLabel(self.project,self.undo_iri,self.undo_prefix,\
                                        self.undo_remaining_characters).return_label()

        CommandLabelChange(self.node.diagram, self.node, self.node.text(), old_text).redo()