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


from functools import partial
from pygraphol.commands import CommandNodeValueDomainSelectDatatype
from pygraphol.datatypes import XsdDatatype
from pygraphol.exceptions import ParseError
from pygraphol.items.nodes.shapes.common import Label
from pygraphol.items.nodes.shapes.mixins import ShapeMixin
from PyQt5.QtCore import QRectF, Qt, QPointF, QLineF
from PyQt5.QtGui import QPainter, QPainterPath, QIcon, QPixmap, QFont, QColor, QPen, QPolygonF
from PyQt5.QtWidgets import QGraphicsRectItem, QAction


class RoundedRect(QGraphicsRectItem, ShapeMixin):
    """
    This class implements a rounded rectangle which is used to render the 'Domain' node.
    """
    BorderRadius = 8
    MinWidth = 100
    MinHeight = 50
    ShapePadding = 16

    def __init__(self, **kwargs):
        """
        Initialize the rounded rectangle shape.
        """
        super().__init__(**kwargs)
        self.label = Label(self.node.datatype.value, movable=False, editable=False, parent=self)
        self.updateShape()

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

        subMenu = contextMenu.addMenu('Select type')
        subMenu.setIcon(QIcon(':/icons/refresh'))

        for datatype in XsdDatatype:
            action = QAction(datatype.value, scene)
            action.setCheckable(True)
            action.setChecked(datatype == self.node.datatype)
            action.triggered.connect(partial(self.updateDatatype, datatype=datatype))
            subMenu.addAction(action)

        contextMenu.exec_(menuEvent.screenPos())

    ##################################################### GEOMETRY #####################################################

    def shape(self, *args, **kwargs):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.BorderRadius, self.BorderRadius)
        return path

    ################################################## AUXILIARY METHODS ###############################################

    @staticmethod
    def getRect(shape_w, shape_h):
        """
        Returns the initialized rect according to the given width/height.
        :param shape_w: the shape width
        :param shape_h: the shape height
        :rtype: QRectF
        """
        return QRectF(-shape_w / 2, -shape_h / 2, shape_w, shape_h)

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.rect().height()

    def setLabelText(self, text):
        """
        Set the label text (shortcut for self.label.setText).
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
        shape_w = max(self.label.width() + RoundedRect.ShapePadding, RoundedRect.MinWidth)
        self.setRect(RoundedRect.getRect(shape_w, RoundedRect.MinHeight))
        self.updateLabelPos()

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
        shape_w = 54
        shape_h = 32

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)

        # Initialize the shape
        rect = RoundedRect.getRect(shape_w, shape_h)

        # Draw the rectangle
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRoundedRect(rect, 6.0, 6.0)

        # Draw the text within the rectangle
        painter.setFont(QFont('Arial', 10, QFont.Light))
        painter.setBrush(QColor(0, 0, 0))
        painter.drawText(rect, Qt.AlignCenter, 'xsd:string')

        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        shapeBrush = self.shapeSelectedBrush if self.isSelected() else self.shapeBrush

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawRoundedRect(self.rect(), self.BorderRadius, self.BorderRadius)