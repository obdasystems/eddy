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

from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.functions.misc import first
from eddy.core.items.nodes.common.operator import OperatorNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.items.nodes.has_key import HasKeyNode


class EnumerationNode(OperatorNode):
    """
    This class implements the 'Enumeration' node.
    """
    Identities = {Identity.Concept, Identity.ValueDomain, Identity.Neutral}
    Type = Item.EnumerationNode

    def __init__(self, brush=None, **kwargs):
        """
        Initialize the node.
        :type brush: QBrush
        """
        super().__init__(brush=QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)), **kwargs)
        self.label = NodeLabel('oneOf', pos=self.center, editable=False, movable=False, parent=self)

    #############################################
    #   INTERFACE
    #################################

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

    def identify(self):
        """
        Perform the node identification step for this Enumeration node.
        The identity of the node is calculated as follows:

        * If the node has Individuals as inputs => Identity == Concept
        * If the node has Values as inputs => Identity == ValueDomain

        After establishing the identity for this node, we remove all the
        nodes we used to compute such identity from the STRONG set and make
        sure this enumeration node is added to the STRONG set, so it will
        contribute to the computation of the final identity for all the
        WEAK nodes being examined during the identification process.
        :rtype: tuple
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.IndividualNode
        f3 = lambda x: Identity.Concept if x.identity() is Identity.Individual else Identity.ValueDomain
        f4 = lambda x: x.type() is Item.LiteralNode
        inputs = self.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2).union(self.incomingNodes(filter_on_edges=f1, filter_on_nodes=f4))
        identities = set(map(f3, inputs))
        computed = Identity.Neutral
        if identities:
            computed = first(identities)
            if len(identities) > 1:
                computed = Identity.Unknown

        if computed is Identity.Unknown:
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.identity() is Identity.Neutral and isinstance(x, HasKeyNode)
            outgoing = self.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2)
            if outgoing:
                self.setIdentity(Identity.Concept)
                return {self}, outgoing, set()

        self.setIdentity(computed)
        strong_add = set()
        if self.identity() is not Identity.Neutral:
            strong_add.add(self)
        return strong_add, inputs, set()

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
