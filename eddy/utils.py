# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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

from eddy.commands import CommandItemsMultiAdd
from eddy.regex import RE_DIGIT, RE_ITEM_PREFIX


class Clipboard(QObject):
    """
    Clipboard implementation.
    """
    PasteOffsetX = 20
    PasteOffsetY = 10

    def __init__(self, parent=None):
        """
        Initialize the clipboard.
        :param parent: the parent object.
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
        :param scene: the scene where to paste items.
        :param pos: the position where to paste items.
        """
        def ncopy(node):
            """
            Create a copy of the given node generating a new id.
            :param node: the node to copy.
            """
            copy = node.copy(self)
            copy.id = scene.uniqueID.next('n')
            return copy

        # create a copy of all the nodes in the clipboard and store them in a dict using the old
        # node id: this is needed so we can attach copied edges to the copy of the nodes in the
        # clipboard and to do so we need a mapping between the old node id and the new node id.
        nodes = {x:ncopy(n) for x, n in self.nodes.items()}

        def ecopy(edge):
            """
            Create a copy of the given edge generating a new id and attaching the
            copied edge to the correspondent previously copied source/target nodes.
            :param edge: the edge to copy.
            """
            copy = edge.copy(self)
            copy.id = scene.uniqueID.next('e')
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
            scene.clipboardPasteOffsetX = offset.x() + Clipboard.PasteOffsetX
            scene.clipboardPasteOffsetY = offset.y() + Clipboard.PasteOffsetY

        else:

            # no paste position given => use offsets set in the scene instance
            for item in items:
                item.moveBy(scene.clipboardPasteOffsetX, scene.clipboardPasteOffsetY)
                if item.node:
                    item.setZValue(zValue + 0.1)
                    zValue += 0.1
                elif item.edge:
                    item.updateEdge()

            # adjust scene offsets for a possible next paste using shortcuts
            scene.clipboardPasteOffsetX += Clipboard.PasteOffsetX
            scene.clipboardPasteOffsetY += Clipboard.PasteOffsetY

        scene.undostack.push(CommandItemsMultiAdd(scene=scene, collection=items))

    def size(self):
        """
        Returns the amount of elements in the clipboard.
        """
        return len(self.edges) + len(self.nodes)

    def update(self, scene):
        """
        Update the clipboard collecting new selected items.
        :param scene: the diagram scene from where to pick elements.
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


class UniqueID(object):
    """
    Helper class used to generate sequential IDs for GraphicScene items.
    """
    START = 0 # the initial id number
    STEP = 1 # incremental step

    def __init__(self):
        """
        Initialize the UniqueID generator.
        """
        self.ids = dict()

    def next(self, prefix):
        """
        Returns the next id available prepending the given prefix.
        :param prefix: the prefix to be added before the node (usually 'n' for nodes and 'e' for edges).
        :raise ValueError: if the given prefix contains digits.
        :rtype: str
        """
        if RE_DIGIT.search(prefix):
            raise ValueError('invalid prefix supplied ({}): id prefix MUST not contain any digit'.format(prefix))
        try:
            last = self.ids[prefix]
        except KeyError:
            self.ids[prefix] = UniqueID.START
        else:
            self.ids[prefix] = last + UniqueID.STEP
        finally:
            return '{PREFIX}{ID}'.format(PREFIX=prefix, ID=self.ids[prefix])

    @staticmethod
    def parse(unique_id):
        """
        Parse the given unique id returning a tuple in the format (prefix, value).
        :raise ValueError: if the given value has an invalid format.
        :param unique_id: the unique id to parse.
        :rtype: tuple
        """
        match = RE_ITEM_PREFIX.match(unique_id)
        if not match:
            raise ValueError('invalid id supplied ({})'.format(unique_id))
        return match.group('prefix'), int(match.group('value'))

    def update(self, unique_id):
        """
        Update the last incremental value according to the given id.
        :raise ValueError: if the given value has an invalid format.
        :param unique_id: the for incremental adjustment.
        """
        prefix, value = self.parse(unique_id)
        try:
            last = self.ids[prefix]
        except KeyError:
            self.ids[prefix] = value
        else:
            self.ids[prefix] = max(last, value)