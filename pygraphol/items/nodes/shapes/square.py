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
#  University of Rome: http://www.dis.uniroma116t/~graphol/:             #
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
from pygraphol.datatypes import RestrictionType
from pygraphol.exceptions import ParseError
from pygraphol.items.nodes.shapes.common import Label
from pygraphol.items.nodes.shapes.mixins import ShapeMixin
from pygraphol.dialogs import CardinalityRestrictionForm
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap, QPen, QFont, QPolygonF
from PyQt5.QtWidgets import QGraphicsRectItem, QAction, QDialog


class Square(QGraphicsRectItem, ShapeMixin):
    """
    This class implements a square which is used to render 'Domain' and 'Range' restriction nodes.
    """
    shapeSide = 20.0

    def __init__(self, **kwargs):
        """
        Initialize the square shape.
        """
         # remove some data from kwargs so the super() constructor doesn't complain
        brush = QColor(*kwargs.pop('rgb', (252, 252, 252)))

        super().__init__(**kwargs)

        self.shapeBrush = brush

        # intialize shape rectangle
        self.setRect(-self.shapeSide / 2, -self.shapeSide / 2, self.shapeSide, self.shapeSide)

        # initialize node label with default text (default restriction)
        self.label = Label(self.node.restriction.label, centered=False, editable=False, parent=self)
        self.label.updatePos()

    ################################################## EVENT HANDLERS ##################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu for the given node.
        :param menuEvent: the context menu event instance.
        """
        scene = self.scene()
        scene.clearSelection()

        self.setSelected(True)

        contextMenu = self.contextMenu()
        contextMenu.addSeparator()

        subMenu = contextMenu.addMenu('Select restriction')
        subMenu.setIcon(QIcon(':/icons/refresh'))

        for restriction in RestrictionType:
            action = QAction(restriction.value, scene)
            action.setCheckable(True)
            action.setChecked(restriction == self.item.restriction)
            action.triggered.connect(partial(self.updateRestriction, restriction=restriction))
            subMenu.addAction(action)

        collection = self.label.contextMenuAdd()
        if collection:
            contextMenu.addSeparator()
            for action in collection:
                contextMenu.addAction(action)

        contextMenu.exec_(menuEvent.screenPos())

    ################################################# AUXILIARY METHODS ################################################

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.rect().height()

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :param line: the line whose intersection needs to be calculated (in scene coordinates).
        :rtype: QPointF
        """
        intersection = QPointF()
        polygon = self.mapToScene(QPolygonF(self.rect()))

        for i in range(0, polygon.size() - 1):
            polyline = QLineF(polygon[i], polygon[i + 1])
            if polyline.intersect(line, intersection) == QLineF.BoundedIntersection:
                return intersection

        return None

    def setLabelText(self, text):
        """
        Set the label text (shortcut for self.label.setText).
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

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.rect().width()

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
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(*kwargs['rgb']))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRect(QRectF(-shape_w / 2, -shape_h / 2 + 6, shape_w, shape_h))

        # Draw the text within the rectangle
        painter.setFont(QFont('Arial', 9, QFont.Light))
        painter.drawText(-28, -8, 'restriction type')

        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        shapeBrush = self.shapeSelectedBrush if self.isSelected() else self.shapeBrush

        # Draw the polygon
        painter.setBrush(shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawRect(self.rect())

        # Draw controls
        self.paintAnchors(painter, option, widget)