# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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


import re

from functools import partial
from pygraphol.commands import CommandNodeSquareChangeRestriction
from pygraphol.datatypes import RestrictionType, Font
from pygraphol.dialogs import CardinalityRestrictionForm
from pygraphol.exceptions import ParseError
from pygraphol.items.nodes.shapes.common.label import Label
from pygraphol.items.nodes.shapes.common.square import Square
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon
from PyQt5.QtWidgets import QAction, QDialog


class DomainRestrictionNodeShape(Square):
    """
    This class implements the 'Domain Restriction' node shape.
    """

    def __init__(self, **kwargs):
        """
        Initialize the Domain Restriction node shape.
        """
        super().__init__(brush=(252, 252, 252), **kwargs)
        self.label = Label(self.node.restriction.label, centered=False, editable=False, parent=self)
        self.label.updatePos()

    ################################################ AUXILIARY METHODS #################################################

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        menu = super().contextMenu()
        menu.addSeparator()

        subMenu = menu.addMenu('Select restriction')
        subMenu.setIcon(QIcon(':/icons/refresh'))

        scene = self.scene()

        for restriction in RestrictionType:
            action = QAction(restriction.value, scene)
            action.setCheckable(True)
            action.setChecked(restriction == self.item.restriction)
            action.triggered.connect(partial(self.updateRestriction, restriction=restriction))
            subMenu.addAction(action)

        return menu

    ################################################## ACTION HANDLERS #################################################

    def updateRestriction(self, restriction):
        """
        Update the node restriction.
        :param restriction: the restriction type.
        """
        scene = self.scene()
        if restriction == RestrictionType.cardinality:
            form = CardinalityRestrictionForm()
            if form.exec_() == QDialog.Accepted:
                cardinality = dict(min=form.minCardinalityValue, max=form.maxCardinalityValue)
                scene.undoStack.push(CommandNodeSquareChangeRestriction(self.node, restriction, cardinality))
        else:
            scene.undoStack.push(CommandNodeSquareChangeRestriction(self.node, restriction))

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
        Set the label text: will additionally parse the text value and set the restriction type accordingly.
        :raise ParseError: if an invalid text value is supplied.
        :param text: the text value to set.
        """
        text = text.strip()
        if text == RestrictionType.exists.label:
            self.node.restriction = RestrictionType.exists
            self.label.setText(text)
        elif text == RestrictionType.forall.label:
            self.node.restriction = RestrictionType.forall
            self.label.setText(text)
        elif text == RestrictionType.self.label:
            self.node.restriction = RestrictionType.self
            self.label.setText(text)
        else:
            RE_PARSE = re.compile("""^\(\s*(?P<min>[\d-]+)\s*,\s*(?P<max>[\d-]+)\s*\)$""")
            match = RE_PARSE.match(text)
            if match:
                self.node.restriction = RestrictionType.cardinality
                self.node.cardinality['min'] = None if match.group('min') == '-' else int(match.group('min'))
                self.node.cardinality['max'] = None if match.group('max') == '-' else int(match.group('max'))
                self.label.setText(text)
            else:
                raise ParseError('invalid restriction supplied: %s' % text)

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
        shape_w = 18
        shape_h = 18

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Draw the rectangle
        painter.setPen(Square.shapePen)
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRect(QRectF(-shape_w / 2, -shape_h / 2 + 6, shape_w, shape_h))

        # Draw the text within the rectangle
        painter.setFont(Font('Arial', 9, Font.Light))
        painter.drawText(-21, -8, 'restriction')

        return pixmap