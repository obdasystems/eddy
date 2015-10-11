# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from functools import partial
from PyQt5.QtWidgets import QAction
from grapholed.commands import CommandNodeValueDomainSelectDatatype
from grapholed.datatypes import XsdDatatype, Font
from grapholed.exceptions import ParseError
from grapholed.items.nodes.shapes.common.label import Label
from grapholed.items.nodes.shapes.common.rounded_rect import RoundedRect

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QIcon, QColor, QPen


class ValueDomainNodeShape(RoundedRect):
    """
    This class implements the 'Value-Domain' node shape.
    """

    def __init__(self, **kwargs):
        """
        Initialize the Value-Domain node shape.
        """
        super().__init__(**kwargs)
        self.label = Label(self.node.datatype.value, movable=False, editable=False, parent=self)
        self.updateShape()

    ################################################ AUXILIARY METHODS #################################################

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        menu = super().contextMenu()
        menu.addSeparator()

        subMenu = menu.addMenu('Select type')
        subMenu.setIcon(QIcon(':/icons/refresh'))

        scene = self.scene()

        for datatype in XsdDatatype:
            action = QAction(datatype.value, scene)
            action.setCheckable(True)
            action.setChecked(datatype == self.node.datatype)
            action.triggered.connect(partial(self.updateDatatype, datatype=datatype))
            subMenu.addAction(action)

        return menu

    def updateDatatype(self, datatype):
        """
        Switch the selected domain node datatype.
        :param datatype: the datatype to select.
        """
        scene = self.scene()
        scene.undoStack.push(CommandNodeValueDomainSelectDatatype(node=self.node, datatype=datatype))

    def updateShape(self):
        """
        Update current shape geometry according to the selected datatype.
        Will also center the shape text after the width adjustment.
        """
        shape_w = max(self.label.width() + self.padding, self.minW)
        self.rect = RoundedRect.createRect(shape_w, RoundedRect.minH)
        self.updateLabelPos()

    ################################################# LABEL SHORTCUTS ##################################################

    def labelPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
        """
        return self.label.pos()

    def labelText(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def setLabelPos(self, pos):
        """
        Set the label position.
        :param pos: the node position.
        """
        self.label.setPos(pos)

    def setLabelText(self, text):
        """
        Set the label text.
        :raise ParseError: if an invalid datatype is given.
        :param text: the text value to set.
        """
        text = text.strip()
        for datatype in XsdDatatype:
            if datatype.value == text:
                self.node.datatype = datatype
                self.label.setText(datatype.value)
                self.updateShape()
                self.updateEdges()
                return

        # raise an error in case the given text doesn't match any XsdDatatype value
        raise ParseError('invalid datatype supplied: %s' % text)

    def updateLabelPos(self):
        """
        Update the label text position.
        """
        self.label.updatePos()

    ################################################### ITEM DRAWING ###################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        shape_w = 54
        shape_h = 34

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)

        # Initialize the shape
        rect = RoundedRect.createRect(shape_w, shape_h)

        # Draw the rectangle
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRoundedRect(rect, 6.0, 6.0)

        # Draw the text within the rectangle
        painter.setFont(Font('Arial', 10, Font.Light))
        painter.drawText(rect, Qt.AlignCenter, 'xsd:string')

        return pixmap