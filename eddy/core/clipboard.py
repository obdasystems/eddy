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


from PyQt5 import QtCore

from eddy.core.commands.nodes_2 import CommandProjetSetIRIPrefixesNodesDict, CommandCommandProjetSetIRIofCutNodes
from eddy.core.commands.common import CommandItemsAdd
from eddy.core.output import getLogger


LOGGER = getLogger()


class Clipboard(QtCore.QObject):
    """
    Extension of QtCore.QObject which implements the Clipboard.
    Additionally to built-in signals, this class emits:

    * sgnCleared: whenever the clipboard is cleared.
    * sgnUpdated: whenever the clipboard is updated with new elements.
    """
    PasteOffsetX = 20
    PasteOffsetY = 10

    sgnCleared = QtCore.pyqtSignal()
    sgnUpdated = QtCore.pyqtSignal()

    def __init__(self, session):
        """
        Initialize the clipboard.
        :type session: Session
        """
        super().__init__(session)
        self.edges = {}
        self.nodes = {}

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session (alias for Clipboard.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def clear(self):
        """
        Clear the clipboard.
        """
        self.edges.clear()
        self.nodes.clear()
        LOGGER.debug('Clipboard cleared!')
        self.sgnCleared.emit()

    def empty(self):
        """
        Tells whether the clipboard is empty.
        :rtype: bool
        """
        return not self.edges and not self.nodes

    def paste(self, diagram, pos=None):
        """
        Paste currently copied items in the given diagram.
        :type diagram: Diagram
        :type pos: QPointF
        """
        def ncopy(node):
            """
            Create a copy of the given node generating a new id.
            :type node: AbstractNode
            """
            #print('ncopy >>> node',node)
            copy = node.copy(diagram)
            copy.id = diagram.guid.next('n')
            #print('copy.id',copy.id)
            return copy

        # Create a copy of all the nodes in the clipboard and store them in a dict using the old
        # node id: this is needed so we can attach copied edges to the copy of the nodes in the
        # clipboard and to do so we need a mapping between the old node id and the new node id.
        nodes = {x:ncopy(n) for x, n in self.nodes.items()}

        #print('nodes',nodes)
        #print('self.nodes.items()',self.nodes.items())

        def ecopy(edge):
            """
            Create a copy of the given edge generating a new id and attaching the
            copied edge to the correspondent previously copied source/target nodes.
            :type edge: AbstractEdge
            """
            copy = edge.copy(diagram)
            copy.id = diagram.guid.next('e')
            copy.source = nodes[edge.source.id]
            copy.target = nodes[edge.target.id]
            copy.source.setAnchor(copy, edge.source.anchor(edge))
            copy.target.setAnchor(copy, edge.target.anchor(edge))
            nodes[edge.source.id].addEdge(copy)
            nodes[edge.target.id].addEdge(copy)
            copy.updateEdge()
            return copy

        # Copy all the needed edges
        edges = [ecopy(e) for e in self.edges.values()]
        nodes = [n for n in nodes.values()]
        items = nodes + edges

        try:
            zValue = max(diagram.items(), key=lambda x: x.zValue()).zValue()
        except ValueError:
            zValue = 0  # Diagram is empty

        if pos:
            # Paste position has been given manually => figure out which node to use as anchor item and
            # adjust the paste position so that the anchor item is pasted right after the given position
            item = min(nodes, key=lambda x: x.boundingRect().top())
            offset = pos - item.pos() + QtCore.QPointF(item.width() / 2, item.height() / 2)
            for item in items:
                item.moveBy(offset.x(), offset.y())
                if item.isNode():
                    item.setZValue(zValue + 0.1)
                    zValue += 0.1
                elif item.isEdge():
                    item.updateEdge()

            # Adjust offsets for a possible next paste using shortcuts.
            diagram.pasteX = offset.x() + self.PasteOffsetX
            diagram.pasteY = offset.y() + self.PasteOffsetY

        else:

            # No paste position given => use offsets set in the diagram instance.
            for item in items:
                item.moveBy(diagram.pasteX, diagram.pasteY)
                if item.isNode():
                    item.setZValue(zValue + 0.1)
                    zValue += 0.1
                elif item.isEdge():
                    item.updateEdge()

            # Adjust diagram offsets for a possible next paste using shortcuts.
            diagram.pasteX += self.PasteOffsetX
            diagram.pasteY += self.PasteOffsetY

        Duplicate_dict_1 = diagram.project.copy_IRI_prefixes_nodes_dictionaries(diagram.project.IRI_prefixes_nodes_dict, dict())
        Duplicate_dict_2 = diagram.project.copy_IRI_prefixes_nodes_dictionaries(diagram.project.IRI_prefixes_nodes_dict, dict())

        iris_to_be_updated = []
        nodes_to_be_updated = []
        count = 0

        #print('len(nodes)',len(nodes))

        #print('diagram.project.iri_of_cut_nodes',diagram.project.iri_of_cut_nodes)

        #Dup_1B = diagram.project.copy_list(diagram.project.iri_of_cut_nodes, [])
        #Dup_2B = diagram.project.copy_list(diagram.project.iri_of_cut_nodes, [])

        for x,n in self.nodes.items():

            flag = False

            for c,ele in enumerate(diagram.project.iri_of_cut_nodes):
                #print('ele',ele)
                if (n is ele) or (str(n) == str(ele)):
                    iri = diagram.project.iri_of_cut_nodes[c+1]
                    flag = True
            if flag is False:
                iri = diagram.project.get_iri_of_node(n)

            new_nd = nodes[count]
            #print('n',n)
            #print('new_nd',new_nd)

            #print('paste    >>>',iri)
            nodes_to_be_updated.append(n)
            iris_to_be_updated.append(iri)
            Duplicate_dict_1[iri][1].add(new_nd)
            count = count + 1

        #Dup_1B[:] = []

        commands = []

        #commands.append(CommandCommandProjetSetIRIofCutNodes(Dup_2B, Dup_1B, diagram.project))
        commands.append(CommandProjetSetIRIPrefixesNodesDict(diagram.project, Duplicate_dict_2, Duplicate_dict_1, iris_to_be_updated, nodes_to_be_updated))
        commands.append(CommandItemsAdd(diagram, items))
        #commands.append(CommandProjetSetIRIPrefixesNodesDict(diagram.project, Duplicate_dict_2, Duplicate_dict_1, iris_to_be_updated, nodes_to_be_updated))
        #commands.append(CommandCommandProjetSetIRIofCutNodes(Dup_2B, Dup_1B, self.project))

        self.session.undostack.beginMacro('edit paste >>')
        for command in commands:
            if command:
                self.session.undostack.push(command)
        self.session.undostack.endMacro()

    def size(self):
        """
        Returns the amount of elements in the clipboard.
        """
        return len(self.edges) + len(self.nodes)

    def update(self, diagram):
        """
        Update the clipboard collecting new selected items.
        :type diagram: Diagram
        """
        nodes = diagram.selectedNodes()
        if nodes:

            self.edges = {}
            self.nodes = {node.id: node.copy(diagram) for node in nodes}
            for node in nodes:
                for edge in node.edges:
                    if edge.id not in self.edges and edge.isSelected() and edge.other(node).isSelected():
                        copy = edge.copy(diagram)
                        copy.source = self.nodes[edge.source.id]
                        copy.source.setAnchor(copy, edge.source.anchor(edge))
                        copy.target = self.nodes[edge.target.id]
                        copy.target.setAnchor(copy, edge.target.anchor(edge))
                        self.edges[edge.id] = copy

            LOGGER.debug('Clipboard updated: nodes=%s, edges=%s', len(self.nodes), len(self.edges))
            self.sgnUpdated.emit()

    def __repr__(self):
        """
        Return repr(self).
        """
        return 'Clipboard<nodes:{0},edges:{1}>'.format(len(self.nodes), len(self.edges))