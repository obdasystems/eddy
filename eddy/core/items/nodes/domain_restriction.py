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


from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush

from eddy.core.datatypes import Item, Identity, Restriction
from eddy.core.items.nodes.common.restriction import RestrictionNode
from eddy.core.qt import Font


class DomainRestrictionNode(RestrictionNode):
    """
    This class implements the 'Domain Restriction' node.
    """
    identities = {Identity.Concept}
    item = Item.DomainRestrictionNode

    def __init__(self, brush=None, **kwargs):
        """
        Initialize the node.
        :type brush: QBrush
        """
        super().__init__(brush=QBrush(QColor(252, 252, 252)), **kwargs)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Concept

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    @property
    def qualified(self):
        """
        Tells whether this node expresses a qualified restriction.
        :rtype: bool
        """
        f1 = lambda x: x.isItem(Item.InputEdge) and x.target is self
        f2 = lambda x: x.identity in {Identity.Concept, Identity.Role}
        if self.restriction in {Restriction.Cardinality, Restriction.Exists, Restriction.Forall}:
            if len([n for n in [e.other(self) for e in self.edges if f1(e)] if f2(n)]) >= 2:
                return True
        return False

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        # INITIALIZATION
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        # TEXT ABOVE THE SHAPE
        painter.setFont(Font('Arial', 9, Font.Light))
        painter.translate(0, 0)
        painter.drawText(QRectF(0, 0, kwargs['w'], kwargs['h'] / 2), Qt.AlignCenter, 'restriction')
        # ITEM SHAPE
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRect(QRectF(-18 / 2, -18 / 2 + 6, 18, 18))
        return pixmap