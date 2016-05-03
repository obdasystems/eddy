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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush

from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.items.nodes.common.operator import OperatorNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.qt import Font


class RoleChainNode(OperatorNode):
    """
    This class implements the 'Role Chain' node.
    """
    Identities = {Identity.Role}
    Type = Item.RoleChainNode

    def __init__(self, brush=None, inputs=None, **kwargs):
        """
        Initialize the node.
        :type brush: QBrush
        :type inputs: DistinctList
        """
        super().__init__(brush=QBrush(QColor(252, 252, 252)), **kwargs)
        self.inputs = inputs or DistinctList()
        self.label = NodeLabel(template='chain',
                               editable=False,
                               movable=False,
                               pos=lambda: self.center(),
                               parent=self)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Role

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

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
        kwargs = {'id': self.id, 'height': self.height(), 'width': self.width()}
        node = diagram.factory.create(self.type(), **kwargs)
        node.setPos(self.pos())
        node.setText(self.text())
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

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
        polygon = cls.createPolygon(46, 30)
        # ITEM SHAPE
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)
        # TEXT WITHIN THE SHAPE
        painter.setFont(Font('Arial', 11, Font.Light))
        painter.drawText(polygon.boundingRect(), Qt.AlignCenter, 'chain')
        return pixmap

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