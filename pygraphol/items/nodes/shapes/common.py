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


from pygraphol.commands import CommandNodeLabelMove, CommandNodeLabelEdit
from pygraphol.functions import isEmpty
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QFont, QColor, QTextCursor, QIcon, QPainterPath
from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsItem, QAction


class Label(QGraphicsTextItem):
    """
    This class implements the label to be attached to the graph shapes.
    """

    textBrush = QColor(0, 0, 0, 255)
    textFont = QFont('Arial', 9, QFont.Light)

    def __init__(self, default='', centered=True, movable=True, editable=True, parent=None):
        """
        Initialize the label.
        :param default: the text to be drawn when the shape is first created.
        :param centered: whether the text should be centered in the shape by default.
        :param movable: whether the text can be moved using the mouse.
        :param editable: whether the text can be edited by the user.
        :param parent: the parent node.
        """
        super().__init__(parent)
        self.defaultText = default
        self.centered = centered
        self.editable = editable
        self.movable = movable
        self.moved = False
        self.commandEdit = None
        self.commandMove = None
        self.setFlag(QGraphicsItem.ItemIsMovable, self.movable)
        self.setFlag(QGraphicsItem.ItemIsSelectable, self.movable)
        self.setFlag(QGraphicsItem.ItemIsFocusable, self.editable)
        self.setDefaultTextColor(self.textBrush)
        self.setFont(self.textFont)
        self.setText(self.defaultText)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    ################################################## EVENT HANDLERS ##################################################

    def focusInEvent(self, focusEvent):
        """
        Executed when the text item lose the focus.
        :param focusEvent: the focus event instance.
        """
        cursor = self.textCursor()
        cursor.select(QTextCursor.BlockUnderCursor)
        self.setTextCursor(cursor)
        if not self.commandEdit:
            parent = self.parentItem()
            self.commandEdit = CommandNodeLabelEdit(parent.node)
        super().focusInEvent(focusEvent)

    def focusOutEvent(self, focusEvent):
        """
        Executed when the text item lose the focus.
        :param focusEvent: the focus event instance.
        """
        # make sure we have something in the label
        if isEmpty(self.text()) or self.text() == self.defaultText:
            self.setText(self.defaultText)
            self.updatePos()

        # push the edit command in the stack only if the label actually changed
        if self.commandEdit and self.text() != self.commandEdit.old:
            self.commandEdit.new = self.text()
            scene = self.scene()
            scene.undoStack.push(self.commandEdit)

        # clear label state
        self.commandEdit = None
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        super().focusOutEvent(focusEvent)

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse move over the text area (NOT PRESSED).
        :param moveEvent: the move event instance.
        """
        if self.editable and self.hasFocus():
            self.setCursor(Qt.IBeamCursor)
            super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the text area (NOT PRESSED).
        :param moveEvent: the move event instance.
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def keyPressEvent(self, keyEvent):
        """
        Executed when a key is pressed.
        :param keyEvent: the key press event.
        """
        super().keyPressEvent(keyEvent)
        self.updatePos()

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Executed when the mouse is double clicked on the text item.
        :param mouseEvent: the mouse event instance.
        """
        if self.editable:
            super().mouseDoubleClickEvent(mouseEvent)
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.setFocus()

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the text item.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()
        if scene.mode == scene.MoveItem:
            # this is needed so the label outline will
            # not appear when adding edges between nodes
            super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the text is moved with the mouse.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()
        if scene.mode == scene.MoveItem:
            super().mouseMoveEvent(mouseEvent)
            if not self.commandMove:
                parent = self.parentItem()
                self.commandMove = CommandNodeLabelMove(parent.node, self.moved)
            self.moved = True

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the label.
        :param mouseEvent: the mouse event instance.
        """
        super().mouseReleaseEvent(mouseEvent)
        scene = self.scene()
        if scene.mode == scene.MoveItem:
            if self.commandMove:
                self.commandMove.end()
                scene.undoStack.push(self.commandMove)
        self.commandMove = None

    ##################################################### GEOMETRY #####################################################

    def shape(self, *args, **kwargs):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    ################################################ AUXILIARY METHODS #################################################

    def center(self):
        """
        Returns the point at the center of the shape.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def contextMenuAdd(self):
        """
        Returns a list of actions for the item shape context menu.
        :rtype: list
        """
        collection = []
        if self.flags() & QGraphicsItem.ItemIsMovable and self.moved:
            parent = self.parentItem()
            action = QAction('Reset text position', parent.scene())
            action.setIcon(QIcon(':/icons/refresh'))
            action.triggered.connect(self.handleResetTextPosition)
            collection.append(action)
        return collection

    def defaultPos(self):
        """
        Returns the label default position.
        :rtype: QPointF
        """
        b1 = self.boundingRect()
        b2 = self.parentItem().boundingRect()
        # default to the center of the shape
        x = b2.center().x() - b1.width() / 2
        y = b2.center().y() - b1.height() / 2
        if not self.centered:
            # move above the shape if that's the case
            y -= b1.height() + 1.0
        return QPointF(x, y)

    def height(self):
        """
        Returns the height of the text label.
        :rtype: int
        """
        return self.boundingRect().height()

    def setText(self, text):
        """
        Set the given text as plain text.
        :param text: the text value to set.
        """
        self.setPlainText(text)
        self.updatePos()

    def text(self):
        """
        Returns the current shape text (shortcut for self.toPlainText()).
        :return: str
        """
        return self.toPlainText()

    def updatePos(self):
        """
        Update the current text position with respect to the shape.
        """
        if not self.moved:
            self.setPos(self.defaultPos())

    def width(self):
        """
        Returns the width of the text label.
        :rtype: int
        """
        return self.boundingRect().width()

    ################################################# ACTION HANDLERS ##################################################

    def handleResetTextPosition(self):
        """
        Reset the text position to the default value.
        """
        if self.flags() & QGraphicsItem.ItemIsMovable:
            parent = self.parentItem()
            command = CommandNodeLabelMove(parent.node, self.moved)
            command.new = self.defaultPos()
            scene = self.scene()
            scene.undoStack.push(command)
            self.updatePos()