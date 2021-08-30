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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5 import QtCore

from eddy.core.commands.labels import CommandLabelChange
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.misc import isEmpty
from eddy.core.items.common import AbstractLabel


class NodeLabel(AbstractLabel):
    """
    This class implements the label to be attached to the graphol nodes.
    """
    def __init__(self, template='', pos=None, movable=True, editable=True, parent=None):
        """
        Initialize the label.
        :type template: str
        :type pos: callable
        :type movable: bool
        :type editable: bool
        :type parent: QObject
        """
        defaultPos = lambda: QtCore.QPointF(0, 0)
        self.defaultPos = pos or defaultPos
        super().__init__(template, movable, editable, parent=parent)
        self.setPos(self.defaultPos())

    #############################################
    #   EVENTS
    #################################

    def keyPressEvent(self, keyEvent):
        """
        Executed when a key is pressed.
        :type keyEvent: QKeyEvent
        """
        moved = self.isMoved()
        super().keyPressEvent(keyEvent)
        self.updatePos(moved)

    #############################################
    #   INTERFACE
    #################################

    def isMoved(self):
        """
        Returns True if the label has been moved from its default location, else False.
        :return: bool
        """
        return (self.pos() - self.defaultPos()).manhattanLength() >= 1

    def setText(self, text):
        """
        Set the given text as plain text.
        :type text: str.
        """
        moved = self.isMoved()
        super().setText(text)
        self.updatePos(moved)

    def updatePos(self, moved=False):
        """
        Update the current text position with respect to its parent node.
        :type moved: bool.
        """
        if not moved:
            self.setPos(self.defaultPos())


class FacetQuotedLabel(NodeLabel):
    """
    This class implements the quoted label of Facet nodes.
    """
    def __init__(self, **kwargs):
        """
        Initialize the label.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self.focusInFacet = None

    #############################################
    #   EVENTS
    #################################

    def focusInEvent(self, focusEvent):
        """
        Executed when the text item is focused.
        :type focusEvent: QFocusEvent
        """
        # Make the label focusable only by performing a double click on the
        # text: this will exclude any other type of focus action (dunno why
        # but sometime the label gets the focus when hovering the mouse cursor
        # on the text: mostly happens when loading a diagram from file)
        if focusEvent.reason() == QtCore.Qt.OtherFocusReason:
            node = self.parentItem()
            self.focusInData = self.text()
            self.focusInFacet = node.facet
            self.setText(self.text().strip('"'))
            self.diagram.clearSelection()
            self.diagram.setMode(DiagramMode.LabelEdit)
            self.setSelectedText(True)
            super(AbstractLabel, self).focusInEvent(focusEvent)
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
            currentData = '"{0}"'.format(self.text().strip('"'))

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
                item = self.parentItem()
                undo = item.compose(self.focusInFacet, focusInData)
                redo = item.compose(self.focusInFacet, currentData)
                command = CommandLabelChange(self.diagram, self.parentItem(), undo, redo)
                self.session.undostack.push(command)

            self.focusInData = None
            self.focusInFacet = None
            self.setSelectedText(False)
            self.setAlignment(self.alignment())
            self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
            self.diagram.setMode(DiagramMode.Idle)
            self.diagram.sgnUpdated.emit()

        super(AbstractLabel, self).focusOutEvent(focusEvent)
