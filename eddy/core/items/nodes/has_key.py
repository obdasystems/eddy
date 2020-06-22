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


from PyQt5 import QtGui

from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.items.nodes.common.operator import OperatorNode
from eddy.core.items.nodes.common.label import NodeLabel


class HasKeyNode(OperatorNode):
    """
    This class implements the 'Union' node.
    """
    Identities = {Identity.Neutral}
    Type = Item.HasKeyNode

    def __init__(self, brush=None, inputs=None, **kwargs):
        """
        Initialize the node.
        :type brush: QBrush
        """
        super().__init__(brush=QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)), **kwargs)
        self.inputs = inputs or DistinctList()
        self.label = NodeLabel('key', pos=self.center, editable=False, movable=False, parent=self)

    #############################################
    #   INTERFACE
    #################################

    def addEdge(self, edge):
        """
        Add the given edge to the current node.
        :type edge: AbstractEdge
        """
        super().addEdge(edge)
        if edge.type() is Item.InputEdge and edge.target is self:
            self.inputs.append(edge.id)
            edge.updateEdge()

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        node = diagram.factory.create(self.type(), **{
            'id': self.id,
            'height': self.height(),
            'width': self.width()
        })
        node.setPos(self.pos())
        node.setText(self.text())
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Neutral

    def inputNodes(self, filter_on_nodes=lambda x: True):
        """
        Returns the list of nodes connected via an input edge
        ordered according to the input edge label.

        :type filter_on_nodes: callable
        :rtype: list
        """
        f1 = lambda e: e.id in self.inputs
        f2 = lambda e: self.inputs.index(e.id)
        return [x for x in [e.other(self) for e in sorted(filter(f1, self.edges), key=f2) \
                            if e.target is self] if filter_on_nodes(x)]

    def removeEdge(self, edge):
        """
        Remove the given edge from the current node.
        :type edge: AbstractEdge
        """
        super().removeEdge(edge)
        self.inputs.remove(edge.id)
        for i in self.inputs:
            try:
                edge = self.diagram.edge(i)
                edge.updateEdge()
            except KeyError:
                pass

    def setIdentity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        pass

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.label.pos()

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)
