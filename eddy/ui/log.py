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
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.functions.signals import connect
from eddy.core.output import getLogger
from eddy.core.datatypes.qt import Font


LOGGER = getLogger()


class LogDialog(QtWidgets.QDialog):
    """
    Extends QtWidgets.QDialog providing a log message viewer.
    """
    def __init__(self, parent=None):
        """
        Initialize the dialog.
        :type parent: QWidget
        """
        super().__init__(parent)

        stream = LOGGER.getDefaultStream()

        #############################################
        # MESSAGE AREA
        #################################

        self.messageArea = QtWidgets.QPlainTextEdit(self)
        self.messageArea.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.messageArea.setContentsMargins(10, 0, 0, 0)
        self.messageArea.setFont(Font('Monospace', style=Font.TypeWriter))
        self.messageArea.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.messageArea.setMinimumSize(800, 500)
        self.highlighter = LogHighlighter(self.messageArea.document())
        self.messageArea.setPlainText(stream.getvalue())
        self.messageArea.setReadOnly(True)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok, QtCore.Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 0, 0)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.addWidget(self.messageArea)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        connect(self.confirmationBox.accepted, self.accept)

        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Log')


class LogHighlighter(QtGui.QSyntaxHighlighter):
    """
    Extends QtGui.QSyntaxHighlighter providing a syntax highlighter for log messages.
    """
    def __init__(self, document):
        """
        Initialize the syntax highlighter.
        :type document: QTextDocument
        """
        super().__init__(document)
        self.rules = [
            (QtCore.QRegExp(r'^(.{10})\s(.{8})\s+CRITICAL\s+(.*)$'), 0, self.fmt('#8000FF')),
            (QtCore.QRegExp(r'^(.{10})\s(.{8})\s+ERROR\s+(.*)$'), 0, self.fmt('#FF0000')),
            (QtCore.QRegExp(r'^(.{10})\s(.{8})\s+WARNING\s+(.*)$'), 0, self.fmt('#FFAE00')),
        ]

    @staticmethod
    def fmt(color):
        """
        Return a QTextCharFormat with the given attributes.
        """
        _color = QtGui.QColor()
        _color.setNamedColor(color)
        _format = QtGui.QTextCharFormat()
        _format.setForeground(_color)
        return _format

    def highlightBlock(self, text):
        """
        Apply syntax highlighting to the given block of text.
        :type text: str
        """
        for exp, nth, fmt in self.rules:
            index = exp.indexIn(text, 0)
            while index >= 0:
                index = exp.pos(nth)
                length = len(exp.cap(nth))
                self.setFormat(index, length, fmt)
                index = exp.indexIn(text, index + length)
