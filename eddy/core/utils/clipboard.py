# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QObject, QPointF

from eddy.core.commands import CommandItemsMultiAdd


class Clipboard(QObject):
    """
    Clipboard implementation.
    """
    PasteOffsetX = 20
    PasteOffsetY = 10

    def __init__(self, parent=None):
        """
        Initialize the clipboard.
        :type parent: QObject
        """
        super().__init__(parent)
        self.edges = {}
        self.nodes = {}

    def clear(self):
        """
        Clear the clipboard.
        """
        self.edges.clear()
        self.nodes.clear()

    def empty(self):
        """
        Tells whether the clipboard is empty.
        :rtype: bool
        """
        return not self.edges and not self.nodes

    def paste(self, scene, pos=None):
        """
        Paste currently copied items in the given scene.
        :type scene: DiagramScene
        :type pos: QPointF
        """
        def ncopy(node):
            """
            Create a copy of the given node generating a new id.
            :type node: AbstractNode
            """
            copy = node.copy(scene)
            copy.id = scene.guid.next('n')
            return copy

        # create a copy of all the nodes in the clipboard and store them in a dict using the old
        # node id: this is needed so we can attach copied edges to the copy of the nodes in the
        # clipboard and to do so we need a mapping between the old node id and the new node id.
        nodes = {x:ncopy(n) for x, n in self.nodes.items()}

        def ecopy(edge):
            """
            Create a copy of the given edge generating a new id and attaching the
            copied edge to the correspondent previously copied source/target nodes.
            :type edge: AbstractEdge
            """
            copy = edge.copy(scene)
            copy.id = scene.guid.next('e')
            copy.source = nodes[edge.source.id]
            copy.target = nodes[edge.target.id]
            copy.source.setAnchor(copy, edge.source.anchor(edge))
            copy.target.setAnchor(copy, edge.target.anchor(edge))
            nodes[edge.source.id].addEdge(copy)
            nodes[edge.target.id].addEdge(copy)
            copy.updateEdge()
            return copy

        # copy all the needed edges
        edges = [ecopy(e) for e in self.edges.values()]
        nodes = [n for n in nodes.values()]
        items = nodes + edges

        try:
            zValue = max(scene.items(), key=lambda x: x.zValue()).zValue()
        except ValueError:
            zValue = 0  # scene is empty

        if pos:

            # paste position has been given manually => figure out which node to use as anchor item and
            # adjust the paste position so that the anchor item is pasted right after the given position
            item = min(nodes, key=lambda x: x.boundingRect().top())
            offset = pos - item.pos() + QPointF(item.width() / 2, item.height() / 2)
            for item in items:
                item.moveBy(offset.x(), offset.y())
                if item.node:
                    item.setZValue(zValue + 0.1)
                    zValue += 0.1
                elif item.edge:
                    item.updateEdge()

            # adjust scene offsets for a possible next paste using shortcuts
            scene.pasteOffsetX = offset.x() + Clipboard.PasteOffsetX
            scene.pasteOffsetY = offset.y() + Clipboard.PasteOffsetY

        else:

            # no paste position given => use offsets set in the scene instance
            for item in items:
                item.moveBy(scene.pasteOffsetX, scene.pasteOffsetY)
                if item.node:
                    item.setZValue(zValue + 0.1)
                    zValue += 0.1
                elif item.edge:
                    item.updateEdge()

            # adjust scene offsets for a possible next paste using shortcuts
            scene.pasteOffsetX += Clipboard.PasteOffsetX
            scene.pasteOffsetY += Clipboard.PasteOffsetY

        scene.undostack.push(CommandItemsMultiAdd(scene=scene, collection=items))

    def size(self):
        """
        Returns the amount of elements in the clipboard.
        """
        return len(self.edges) + len(self.nodes)

    def update(self, scene):
        """
        Update the clipboard collecting new selected items.
        :type scene: DiagramScene
        """
        nodes = scene.selectedNodes()

        if nodes:

            self.edges = {}
            self.nodes = {node.id: node.copy(scene) for node in nodes}

            for node in nodes:
                for edge in node.edges:
                    if edge.id not in self.edges and edge.other(node).isSelected():
                        copy = edge.copy(scene)
                        copy.source = self.nodes[edge.source.id]
                        copy.source.setAnchor(copy, edge.source.anchor(edge))
                        copy.target = self.nodes[edge.target.id]
                        copy.target.setAnchor(copy, edge.target.anchor(edge))
                        self.edges[edge.id] = copy

    def __repr__(self):
        """
        Return repr(self).
        """
        return 'Clipboard<nodes:{},edges:{}>'.format(len(self.nodes), len(self.edges))