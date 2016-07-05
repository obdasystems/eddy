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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QTextBlockFormat, QTextCursor
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import Brush, Pen


class AbstractItem(QGraphicsItem):
    """
    Base class for all the diagram items.
    """
    __metaclass__ = ABCMeta

    Prefix = 'i'
    Type = Item.Undefined

    def __init__(self, diagram, id=None, **kwargs):
        """
        Initialize the item.
        :type diagram: Diagram
        :type id: str
        """
        super().__init__(**kwargs)
        self.id = id or diagram.guid.next(self.Prefix)
        self.selectionBrush = Brush.NoBrush
        self.selectionPen = Pen.NoPen
        self.brush = Brush.NoBrush
        self.pen = Pen.NoPen

    #############################################
    #   PROPERTIES
    #################################

    @property
    def diagram(self):
        """
        Returns the diagram holding this item (alias for AbstractItem.scene()).
        :rtype: Diagram
        """
        return self.scene()

    @property
    def name(self):
        """
        Returns the item readable name.
        :rtype: str
        """
        item = self.type()
        return item.realname

    @property
    def project(self):
        """
        Returns the project this item belongs to.
        :rtype: Project
        """
        return self.diagram.parent()

    @property
    def shortname(self):
        """
        Returns the item readable short name, i.e:
        * .name = datatype restriction node | .shortname = datatype restriction
        * .name = inclusion edge | .shortname = inclusion
        :rtype: str
        """
        item = self.type()
        return item.shortname

    #############################################
    #   INTERFACE
    #################################

    @abstractmethod
    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        pass

    @classmethod
    @abstractmethod
    def icon(cls, width, height, **kwargs):
        """
        Returns an icon of this item suitable for the palette.
        :type width: int
        :type height: int
        :rtype: QIcon
        """
        pass

    def isEdge(self):
        """
        Returns True if this element is an edge, False otherwise.
        :rtype: bool
        """
        return Item.InclusionEdge <= self.type() <= Item.MembershipEdge

    def isNode(self):
        """
        Returns True if this element is a node, False otherwise.
        :rtype: bool
        """
        return Item.ConceptNode <= self.type() < Item.InclusionEdge

    @abstractmethod
    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        pass

    @abstractmethod
    def redraw(self, **kwargs):
        """
        Schedule this item for redrawing.
        """
        pass

    def type(self):
        """
        Returns the type of this item.
        :rtype: Item
        """
        return self.Type

    def __repr__(self):
        """
        Returns repr(self).
        """
        return '{0}:{1}'.format(self.__class__.__name__, self.id)


class AbstractLabel(QGraphicsTextItem):
    """
    Base class for the diagram labels.
    """
    __metaclass__ = ABCMeta

    Type = Item.Label

    def __init__(self, parent=None):
        """
        Initialize the label.
        :type parent: QObject
        """
        self._alignment = Qt.AlignCenter
        super().__init__(parent)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def diagram(self):
        """
        Returns the diagram holding this label (alias for AbstractLabel.scene()).
        :rtype: Diagram
        """
        return self.scene()

    @property
    def project(self):
        """
        Returns the project this label belongs to.
        :rtype: Project
        """
        return self.diagram.parent()

    #############################################
    #   INTERFACE
    #################################

    def alignment(self):
        """
        Returns the text alignment.
        :rtype: int
        """
        return self._alignment

    def center(self):
        """
        Returns the point at the center of the shape.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def height(self):
        """
        Returns the height of the text label.
        :rtype: int
        """
        return self.boundingRect().height()

    @staticmethod
    def isEdge():
        """
        Returns True if this element is an edge, False otherwise.
        :rtype: bool
        """
        return False

    @staticmethod
    def isNode():
        """
        Returns True if this element is a node, False otherwise.
        :rtype: bool
        """
        return False

    def pos(self):
        """
        Returns the position of the label in parent's item coordinates.
        :rtype: QPointF
        """
        return self.mapToParent(self.center())

    def setSelectedText(self, selected=True):
        """
        Select/deselect the text in the label.
        :type selected: bool
        """
        cursor = self.textCursor()
        if selected:
            cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            cursor.select(QTextCursor.Document)
        else:
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        self.setTextCursor(cursor)

    def setAlignment(self, alignment):
        """
        Set the text alignment.
        :type alignment: int
        """
        self._alignment = alignment
        self.setTextWidth(-1)
        self.setTextWidth(self.boundingRect().width())
        format_ = QTextBlockFormat()
        format_.setAlignment(alignment)
        cursor = self.textCursor()
        position = cursor.position()
        selected = cursor.selectedText()
        startPos = cursor.selectionStart()
        endPos = cursor.selectionEnd()
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(format_)
        if selected:
            cursor.setPosition(startPos, QTextCursor.MoveAnchor)
            cursor.setPosition(endPos, QTextCursor.KeepAnchor)
            cursor.select(QTextCursor.BlockUnderCursor)
        else:
            cursor.setPosition(position)
        self.setTextCursor(cursor)

    def setPos(self, *__args):
        """
        Set the item position.
        QGraphicsItem.setPos(QPointF)
        QGraphicsItem.setPos(float, float)
        """
        if len(__args) == 1:
            pos = __args[0]
        elif len(__args) == 2:
            pos = QPointF(__args[0], __args[1])
        else:
            raise TypeError('too many arguments; expected {0}, got {1}'.format(2, len(__args)))
        super().setPos(pos - QPointF(self.width() / 2, self.height() / 2))

    def setText(self, text):
        """
        Set the given text as plain text.
        :type text: str.
        """
        self.setPlainText(text)

    def text(self):
        """
        Returns the text of the label.
        :rtype: str
        """
        return self.toPlainText().strip()

    def type(self):
        """
        Returns the type of this item.
        :rtype: Item
        """
        return self.Type

    def width(self):
        """
        Returns the width of the text label.
        :rtype: int
        """
        return self.boundingRect().width()

    def __repr__(self):
        """
        Returns repr(self).
        """
        return 'Label<{0}:{1}>'.format(self.parentItem().__class__.__name__, self.parentItem().id)