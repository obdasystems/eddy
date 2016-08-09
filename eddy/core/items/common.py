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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import Qt, QPointF, pyqtSlot
from PyQt5.QtGui import QTextBlockFormat, QTextCursor, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem

from eddy.core.commands.labels import CommandLabelChange
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import Brush, DiagramMode
from eddy.core.functions.misc import isEmpty
from eddy.core.functions.signals import connect
from eddy.core.datatypes.qt import Font


class DiagramItemMixin:
    """
    Mixin implementation for all the diagram elements (nodes, edges and labels).
    """
    #############################################
    #   PROPERTIES
    #################################

    @property
    def diagram(self):
        """
        Returns the diagram holding this item (alias for DiagramItemMixin.scene()).
        :rtype: Diagram
        """
        return self.scene()

    @property
    def project(self):
        """
        Returns the project this item belongs to (alias for DiagramItemMixin.diagram.parent()).
        :rtype: Project
        """
        return self.diagram.parent()

    @property
    def session(self):
        """
        Returns the session this item belongs to (alias for DiagramItemMixin.project.parent()).
        :rtype: Session
        """
        return self.project.parent()

    #############################################
    #   INTERFACE
    #################################

    def isEdge(self):
        """
        Returns True if this element is an edge, False otherwise.
        :rtype: bool
        """
        return Item.InclusionEdge <= self.type() <= Item.MembershipEdge

    def isLabel(self):
        """
        Returns True if this element is a label, False otherwise.
        """
        return self.type() is Item.Label

    def isNode(self):
        """
        Returns True if this element is a node, False otherwise.
        :rtype: bool
        """
        return Item.ConceptNode <= self.type() < Item.InclusionEdge


class AbstractItem(QGraphicsItem, DiagramItemMixin):
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

    #############################################
    #   PROPERTIES
    #################################

    @property
    def name(self):
        """
        Returns the item readable name.
        :rtype: str
        """
        item = self.type()
        return item.realName

    @property
    def shortName(self):
        """
        Returns the item readable short name, i.e:
        * .name = datatype restriction node | .shortName = datatype restriction
        * .name = inclusion edge | .shortName = inclusion
        :rtype: str
        """
        item = self.type()
        return item.shortName

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
        Perform the redrawing of this item.
        """
        pass

    @abstractmethod
    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        pass

    @abstractmethod
    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        pass

    @abstractmethod
    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass

    @abstractmethod
    def textPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
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


class AbstractLabel(QGraphicsTextItem, DiagramItemMixin):
    """
    Base class for the diagram labels.
    """
    __metaclass__ = ABCMeta

    Type = Item.Label

    def __init__(self, template='', movable=True, editable=True, parent=None):
        """
        Initialize the label.
        :type template: str
        :type movable: bool
        :type editable: bool
        :type parent: QObject
        """
        self._alignment = Qt.AlignCenter
        self._editable = bool(editable)
        self._movable = bool(movable)
        super().__init__(parent)
        self.focusInData = None
        self.template = template
        self.setDefaultTextColor(Brush.Black255A.color())
        self.setFlag(AbstractLabel.ItemIsFocusable, self.isEditable())
        self.setFont(Font('Arial', 12, Font.Light))
        self.setText(self.template)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

        document = self.document()
        connect(document.contentsChange[int, int, int], self.onContentsChanged)

    #############################################
    #   EVENTS
    #################################

    def focusInEvent(self, focusEvent):
        """
        Executed when the text item is focused.
        :type focusEvent: QFocusEvent
        """
        # FOCUS ONLY ON DOUBLE CLICK
        if focusEvent.reason() == Qt.OtherFocusReason:
            self.focusInData = self.text()
            self.diagram.clearSelection()
            self.diagram.setMode(DiagramMode.LabelEdit)
            self.setSelectedText(True)
            super().focusInEvent(focusEvent)
        else:
            self.clearFocus()

    def focusOutEvent(self, focusEvent):
        """
        Executed when the text item lose the focus.
        :type focusEvent: QFocusEvent
        """
        if self.diagram.mode is DiagramMode.LabelEdit:

            if isEmpty(self.text()):
                self.setText(self.template)

            focusInData = self.focusInData
            currentData = self.text()

            ###########################################################
            # IMPORTANT!                                              #
            # ####################################################### #
            # The code below is a bit tricky: to be able to properly  #
            # update the node in the project index we need to force   #
            # the value of the label to it's previous one and let the #
            # command implementation update the index.                #
            ###########################################################

            self.setText(focusInData)

            if focusInData and focusInData != currentData:
                node = self.parentItem()
                command = CommandLabelChange(self.diagram, node, focusInData, currentData)
                self.session.undostack.push(command)

            self.focusInData = None
            self.setSelectedText(False)
            self.setAlignment(self.alignment())
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            self.diagram.setMode(DiagramMode.Idle)
            self.diagram.sgnUpdated.emit()

        super().focusOutEvent(focusEvent)

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse move over the text area (NOT PRESSED).
        :type moveEvent: QGraphicsSceneHoverEvent
        """
        if self.isEditable() and self.hasFocus():
            self.setCursor(Qt.IBeamCursor)
            super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the text area (NOT PRESSED).
        :type moveEvent: QGraphicsSceneHoverEvent
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def keyPressEvent(self, keyEvent):
        """
        Executed when a key is pressed.
        :type keyEvent: QKeyEvent
        """
        if keyEvent.key() in {Qt.Key_Enter, Qt.Key_Return}:
            if keyEvent.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(keyEvent)
            else:
                self.clearFocus()
        else:
            super().keyPressEvent(keyEvent)

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Executed when the mouse is double clicked on the text item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if self.isEditable():
            super().mouseDoubleClickEvent(mouseEvent)
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.setFocus()

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot(int, int, int)
    def onContentsChanged(self, position, charsRemoved, charsAdded):
        """
        Executed whenever the content of the text item changes.
        :type position: int
        :type charsRemoved: int
        :type charsAdded: int
        """
        self.setAlignment(self.alignment())

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

    def isEditable(self):
        """
        Returns True if the label is editable, else False.
        :rtype: bool
        """
        return self._editable

    def isMovable(self):
        """
        Returns True if the label is movable, else False.
        :rtype: bool
        """
        return self._movable

    def pos(self):
        """
        Returns the position of the label in parent's item coordinates.
        :rtype: QPointF
        """
        return self.mapToParent(self.center())

    def setEditable(self, editable):
        """
        Set the editable status of the label.
        :type editable: bool.
        """
        self._editable = bool(editable)
        self.setFlag(AbstractLabel.ItemIsFocusable, self._editable)

    def setMovable(self, movable):
        """
        Set the movable status of the Label.
        :type movable: bool.
        """
        self._movable = bool(movable)

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

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

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

    @abstractmethod
    def updatePos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass

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