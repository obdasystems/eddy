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

from eddy.core.datatypes.graphol import Item, Identity, Restriction
from eddy.core.functions.misc import first
from eddy.core.items.nodes.common.restriction import RestrictionNode
from eddy.core.items.nodes.has_key import HasKeyNode


class RangeRestrictionNode(RestrictionNode):
    """
    This class implements the 'Range Restriction' node.
    """
    Identities = {Identity.Concept, Identity.ValueDomain, Identity.Neutral}
    Type = Item.RangeRestrictionNode

    def __init__(self, brush=None, **kwargs):
        """
        Initialize the node.
        :type brush: QBrush
        """
        super().__init__(brush=QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), **kwargs)

    #############################################
    #   INTERFACE
    #################################

    def identify(self):
        """
        Perform the node identification step for this RangeRestriction node.
        The identity of the node is calculated as follows:

        * If the node has an Attribute as input => Identity == ValueDomain
        * If the node has a Role or a Concept as input => Identity == Concept

        After establishing the identity for this node, we remove all the
        nodes we used to compute such identity from the STRONG set and make
        sure this enumeration node is added to the STRONG set, so it will
        contribute to the computation of the final identity for all the
        WEAK nodes being examined during the identification process.
        :rtype: tuple
        """
        supported = {Identity.Role, Identity.Attribute, Identity.Concept}
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() in supported and Identity.Neutral not in x.identities()
        f3 = lambda x: Identity.Concept if x.identity() in {Identity.Role, Identity.Concept} else Identity.ValueDomain
        inputs = self.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
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
        Set the label text making sure not to have 'self' as range.
        :type text: str
        """
        restriction = Restriction.forLabel(text)
        if not restriction:
            text = Restriction.Exists.toString()
        self.label.setText(text)
