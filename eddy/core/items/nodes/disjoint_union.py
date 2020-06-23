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
from eddy.core.items.nodes.has_key import HasKeyNode


class DisjointUnionNode(OperatorNode):
    """
    This class implements the 'Disjoint Union' node.
    """
    Identities = {Identity.Concept, Identity.ValueDomain, Identity.Neutral}
    Type = Item.DisjointUnionNode

    def __init__(self, brush=None, **kwargs):
        """
        Initialize the node.
        :type brush: QBrush
        """
        super().__init__(brush=QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), **kwargs)

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
        return node

    def identify(self):
        """
        Perform the node identification step for this Union node.
        Because this node can assume a Concept identity, whenever this node
        is being targeted by an Individual node using a Membership edge, we
        set the identity and move this node in the STRONG set. We'll also make
        sure to remove from the STRONG set the individual node used to compute
        the identity of this very node since Individual nodes do not contribute
        with inheritance to the computation of the final identity for all the
        WEAK nodes being examined during the identification process.
        :rtype: tuple
        """
        f1 = lambda x: x.type() is Item.MembershipEdge
        f2 = lambda x: x.identity() is Identity.Individual
        incoming = self.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
        if incoming:
            computed = Identity.Unknown
            identities = set(x.identity() for x in incoming)
            if len(identities) == 1 and first(identities) is Identity.Individual:
                computed = Identity.Concept
            self.setIdentity(computed)
            return {self}, incoming, set()

        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() is Identity.Neutral and isinstance(x,HasKeyNode)
        outgoing = self.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2)
        if outgoing:
            self.setIdentity(Identity.Concept)
            return {self}, outgoing, set()

        return None

    def setIdentity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        if identity not in self.identities():
            identity = Identity.Unknown
        self._identity = identity

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
        pass

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        pass

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass
