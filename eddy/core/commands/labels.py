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

from eddy.core.datatypes.graphol import Identity, Item


class CommandLabelChange(QtWidgets.QUndoCommand):
    """
    This command is used to edit items' labels.
    """
    def __init__(self, diagram, item, undo, redo, refactor=False, name=None):
        """
        Initialize the command.
        :type diagram: Diagram
        :type item: AbstractItem
        :type undo: str
        :type redo: str
        :type refactor: bool
        :type name: str
        """
        super().__init__(name or 'edit {0} label'.format(item.name))
        self.diagram = diagram
        self.project = diagram.project
        self.refactor = refactor
        self.data = {'undo': undo, 'redo': redo}
        self.item = item

    def redo(self):
        """redo the command"""
        '''
        meta = None
        # BACKUP METADATA
        if self.item.isNode() and self.refactor:
            meta = self.project.meta(self.item.type(), self.data['undo'])
            if meta:
                self.project.unsetMeta(self.item.type(), self.data['undo'])
        '''

        # CHANGE THE CONTENT OF THE LABEL
        if self.item.isNode():
            self.project.doRemoveItem(self.diagram, self.item)
        self.item.setText(self.data['redo'])
        if self.item.isNode():
            self.project.doAddItem(self.diagram, self.item)

        # RESTORE METADATA
        '''
        if meta:
            self.project.setMeta(self.item.type(), self.data['redo'], meta)
        '''

        # UPDATE PREDICATE NODE STATE TO REFLECT THE CHANGES
        '''
        for key in ('undo', 'redo'):
            for node in self.project.predicates(self.item.type(), self.data[key]):
                node.updateNode()

        # IDENTITFY NEIGHBOURS
        if self.item.type() is Item.IndividualNode:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() in {Item.EnumerationNode, Item.PropertyAssertionNode}
            for node in self.item.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                self.diagram.sgnNodeIdentification.emit(node)
            f3 = lambda x: x.type() is Item.MembershipEdge
            f4 = lambda x: Identity.Neutral in x.identities()
            for node in self.item.outgoingNodes(filter_on_edges=f3, filter_on_nodes=f4):
                self.diagram.sgnNodeIdentification.emit(node)
        '''

        # EMIT UPDATED SIGNAL
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        '''
        meta = None
        # BACKUP METADATA
        if self.item.isNode() and self.refactor:
            meta = self.project.meta(self.item.type(), self.data['redo'])
            if meta:
                self.project.unsetMeta(self.item.type(), self.data['redo'])
        '''

        # CHANGE THE CONTENT OF THE LABEL
        if self.item.isNode():
            self.project.doRemoveItem(self.diagram, self.item)
        self.item.setText(self.data['undo'])
        if self.item.isNode():
            self.project.doAddItem(self.diagram, self.item)

        '''
        # RESTORE METADATA
        if meta:
            self.project.setMeta(self.item.type(), self.data['undo'], meta)

        # UPDATE PREDICATE NODE STATE TO REFLECT THE CHANGES
        for key in ('undo', 'redo'):
            for node in self.project.predicates(self.item.type(), self.data[key]):
                node.updateNode()

        # IDENTITFY NEIGHBOURS
        if self.item.type() is Item.IndividualNode:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() in {Item.EnumerationNode, Item.PropertyAssertionNode}
            for node in self.item.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2):
                self.diagram.sgnNodeIdentification.emit(node)
            f3 = lambda x: x.type() is Item.MembershipEdge
            f4 = lambda x: Identity.Neutral in x.identities()
            for node in self.item.outgoingNodes(filter_on_edges=f3, filter_on_nodes=f4):
                self.diagram.sgnNodeIdentification.emit(node)
        '''

        # EMIT UPDATED SIGNAL
        self.diagram.sgnUpdated.emit()


class CommandLabelMove(QtWidgets.QUndoCommand):
    """
    This command is used to move items' labels.
    """
    def __init__(self, diagram, item, pos1, pos2):
        """
        Initialize the command.
        :type diagram: Diagram
        :type item: AbstractItem
        :type pos1: QPointF
        :type pos2: QPointF
        """
        super().__init__('move {0} label'.format(item.name))
        self.diagram = diagram
        self.item = item
        self.data = {'undo': pos1, 'redo': pos2}

    def redo(self):
        """redo the command"""
        self.item.setTextPos(self.data['redo'])
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.item.setTextPos(self.data['undo'])
        self.diagram.sgnUpdated.emit()
