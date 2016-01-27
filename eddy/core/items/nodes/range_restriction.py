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
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor

from eddy.core.datatypes import Font, Item, Identity, Restriction
from eddy.core.functions import identify
from eddy.core.items.nodes.common.square import SquaredNode


class RangeRestrictionNode(SquaredNode):
    """
    This class implements the 'Range Restriction' node.
    """
    identities = {Identity.Concept, Identity.DataRange, Identity.Neutral}
    item = Item.RangeRestrictionNode
    xmlname = 'range-restriction'

    def __init__(self, brush=None, **kwargs):
        """
        Initialize the node.
        :type brush: T <= QBrush | QColor | Color | tuple | list | bytes | unicode
        """
        super().__init__(brush='#000000', **kwargs)
        self._identity = Identity.Neutral

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
        return self._identity

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        if identity not in self.identities:
            identity = Identity.Unknown
        self._identity = identity

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        scene = self.scene()

        f1 = lambda x: x.isItem(Item.InputEdge)
        f2 = lambda x: x.identity is Identity.Attribute

        menu = super().contextMenu()

        # Allow to change the restriction type only if it's not an Attribute range restriction
        if not next(iter(self.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None):
            menu.addSeparator()
            menu.insertMenu(scene.mainwindow.actionOpenNodeProperties, scene.mainwindow.menuRestrictionChange)
            for action in scene.mainwindow.actionsRestrictionChange:
                action.setChecked(self.restriction is action.data())
                action.setVisible(action.data() is not Restriction.Self)

        collection = self.label.contextMenuAdd()
        if collection:
            menu.addSeparator()
            for action in collection:
                menu.insertAction(scene.mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(scene.mainwindow.actionOpenNodeProperties)
        return menu

    def addEdge(self, edge):
        """
        Add the given edge to the current node.
        :type edge: AbstractEdge
        """
        super().addEdge(edge)
        identify(self)

    def removeEdge(self, edge):
        """
        Remove the given edge from the current node.
        :type edge: AbstractEdge
        """
        super().removeEdge(edge)
        identify(self)

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
        shape_w = 18
        shape_h = 18

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Draw the text above the shape
        painter.setFont(Font('Arial', 9, Font.Light))
        painter.translate(0, 0)
        painter.drawText(QRectF(0, 0, kwargs['w'], kwargs['h'] / 2), Qt.AlignCenter, 'restriction')

        # Draw the rectangle
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(0, 0, 0))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRect(QRectF(-shape_w / 2, -shape_h / 2 + 6, shape_w, shape_h))

        return pixmap