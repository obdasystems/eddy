# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QIcon

from eddy.core.datatypes.misc import Brush, Pen
from eddy.core.datatypes.graphol import Item, Identity, Restriction
from eddy.core.items.nodes.common.restriction import RestrictionNode
from eddy.core.qt import Font


class DomainRestrictionNode(RestrictionNode):
    """
    This class implements the 'Domain Restriction' node.
    """
    Identities = {Identity.Concept}
    Type = Item.DomainRestrictionNode

    def __init__(self, brush=None, **kwargs):
        """
        Initialize the node.
        :type brush: QBrush
        """
        super().__init__(brush=Brush.White255A, **kwargs)

    #############################################
    #   PROPERTIES
    #################################

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
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity in {Identity.Concept, Identity.Role}
        f3 = lambda x: x.identity in {Identity.Attribute, Identity.ValueDomain}
        if self.restriction in {Restriction.Cardinality, Restriction.Exists, Restriction.Forall}:
            if len(self.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)) >= 2:
                # Role qualified restriction => Role + Concept
                return True
            if len(self.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3)) >= 2:
                # Attribute qualified restriction => Attribute + ValueDomain
                return True
        return False

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def icon(cls, width, height, **kwargs):
        """
        Returns an icon of this item suitable for the palette.
        :type width: int
        :type height: int
        :rtype: QIcon
        """
        icon = QIcon()
        for i in (1.0, 2.0):
            # CREATE THE PIXMAP
            pixmap = QPixmap(width * i, height * i)
            pixmap.setDevicePixelRatio(i)
            pixmap.fill(Qt.transparent)
            # PAINT THE TEXT ABOVE THE SHAPE
            painter = QPainter(pixmap)
            painter.setFont(Font('Arial', 9, Font.Light))
            painter.translate(0, 0)
            painter.drawText(QRectF(0, 0, width, height / 2), Qt.AlignCenter, 'restriction')
            # PAINT THE SHAPE
            painter.setPen(Pen.SolidBlack1Pt)
            painter.setBrush(Brush.White255A)
            painter.translate(width / 2, height / 2)
            painter.drawRect(QRectF(-18 / 2, -18 / 2 + 6, 18, 18))
            painter.end()
            # ADD THE PIXMAP TO THE ICON
            icon.addPixmap(pixmap)
        return icon