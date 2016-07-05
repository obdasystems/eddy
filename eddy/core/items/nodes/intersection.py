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
from PyQt5.QtGui import QIcon, QPixmap, QPainter

from eddy.core.datatypes.misc import Brush, Pen
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.items.nodes.common.operator import OperatorNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.qt import Font


class IntersectionNode(OperatorNode):
    """
    This class implements the 'Intersection' node.
    """
    Identities = {Identity.Concept, Identity.ValueDomain, Identity.Neutral}
    Type = Item.IntersectionNode

    def __init__(self, brush=None, **kwargs):
        """
        Initialize the node.
        :type brush: QBrush
        """
        self._identity = Identity.Neutral
        super().__init__(brush=Brush.White255A, **kwargs)
        self.label = NodeLabel(template='and',
                               editable=False,
                               movable=False,
                               pos=self.center,
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
        return self._identity

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        if identity not in self.Identities:
            identity = Identity.Unknown
        self._identity = identity

    #############################################
    #   INTERFACE
    #################################

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
            # PAINT THE SHAPE
            polygon = cls.createPolygon(46, 30)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Pen.SolidBlack1Pt)
            painter.setBrush(Brush.White255A)
            painter.translate(width / 2, height / 2)
            painter.drawPolygon(polygon)
            # PAINT THE TEXT INSIDE THE SHAPE
            painter.setFont(Font('Arial', 11, Font.Light))
            painter.drawText(polygon.boundingRect(), Qt.AlignCenter, 'and')
            painter.end()
            # ADD THE PIXMAP TO THE ICON
            icon.addPixmap(pixmap)
        return icon

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