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


from abc import ABCMeta

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QRegExp

from eddy.core.commands.nodes import CommandNodeSetMeta
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.qt import Font
from eddy.core.diagram import Diagram
from eddy.core.functions.signals import connect
from eddy.core.project import K_DESCRIPTION
from eddy.core.datatypes.graphol import Item
from eddy.ui.fields import StringField

class DescriptionDialog(QtWidgets.QDialog):
    """
    This is the base class for all the description dialogs.
    """
    __metaclass__ = ABCMeta

    def __init__(self, session):
        """
        Initialize the property dialog.
        :type session: Session
        """
        super().__init__(session)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the project loaded in the active session (alias for DescriptionDialog.session.project).
        :rtype: Project
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the active session (alias for DescriptionDialog.parent()).
        :rtype: Session
        """
        return self.parent()

class NodeDescriptionDialog(DescriptionDialog):
    """
    This class implements the 'Node description' dialog.
    """
    def __init__(self, diagram, node, session):
        """
        Initialize the node description dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type session: Session
        """
        super().__init__(session)

        self.diagram = diagram
        self.node = node
        meta = diagram.project.meta(node.type(), node.text())

        #############################################
        # DEFAULT CHAR FORMAT
        #################################
        self.defaultCharFormat = QtGui.QTextCharFormat()
        self.defaultCharFormat.setFont(Font('Roboto', 12))
        self.defaultCharFormat.setAnchor(False)

        #############################################
        # CONFIRMATION BOX
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(Font('Roboto', 12))

        #############################################
        # MAIN WIDGET
        #################################
        self.text = QtWidgets.QTextEdit()
        self.text.setText(meta.get(K_DESCRIPTION, ''))
        self.text.setMouseTracking(True)
        self.text.setReadOnly(False)
        self.text.moveCursor(QtGui.QTextCursor.End)
        self.text.setFont(Font('Roboto', 12))
        self.text.setCurrentFont(Font('Roboto', 12))
        self.text.setTabStopWidth(33)
        self.text.setFixedSize(800, 600)
        self.text.setMaximumSize(1000,800)

        #############################################
        # UPPER TOOLBAR WIDGET
        #################################

        self.alignLeftText = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_align_left_black"), "Align Left", self)
        self.alignLeftText.triggered.connect(self.alignLeft)

        self.alignCenterText = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_align_center_black"), "Align Center", self)
        self.alignCenterText.triggered.connect(self.alignCenter)

        self.alignRightText = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_align_right_black"), "Align Right", self)
        self.alignRightText.triggered.connect(self.alignRight)

        self.alignJustifyText = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_align_justify_black"), "Align Justify", self)
        self.alignJustifyText.triggered.connect(self.alignJustify)

        self.indentAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_indent_increase_black"), "Indent Area", self)
        self.indentAction.triggered.connect(self.indent)

        self.dedentAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_indent_decrease_black"), "Dedent Area", self)
        self.dedentAction.triggered.connect(self.dedent)

        self.undoAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_undo_black_"), "Undo", self)
        self.undoAction.triggered.connect(self.text.undo)

        self.redoAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_redo_black_"), "Redo", self)
        self.redoAction.triggered.connect(self.text.redo)

        self.bulletAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_list_bulleted_black"), "Insert Bullet List", self)
        self.bulletAction.triggered.connect(self.bulletList)

        self.numberedAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_list_numbered_black"), "Insert Numbered List", self)
        self.numberedAction.triggered.connect(self.numberList)

        self.clearAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_clear_black"), "Clear Formatting", self)
        self.clearAction.triggered.connect(self.clearFormatting)

        # TODO: add EditSource dialog and connect it
        self.editSourceAction = QtWidgets.QAction(QtGui.QIcon(":icons/48/ic_code_black"), "Edit Source", self)
        self.editSourceAction.triggered.connect(lambda: print(self.text.toHtml()))

        self.insertURL = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_insert_link_black"), "Insert URL Link", self)
        self.insertURL.triggered.connect(UrlDialog(self).show)

        self.insertImage = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_photo_black"), "Insert URL Image", self)
        self.insertImage.triggered.connect(UrlImageDialog(self).show)

        self.wikiTagDialog = WikiTagDialog(self)
        self.wikiTag = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_insert_wiki_link_black"), "Insert Wiki Tag", self)
        self.wikiTag.triggered.connect(self.wikiTagDialog.show)

        #############################################
        # LOWER TOOLBAR WIDGET
        #################################
        self.fontBox = QtWidgets.QFontComboBox()
        self.fontBox.currentFontChanged.connect(lambda font: self.text.setCurrentFont(font))
        self.fontBox.setMaximumHeight(30)

        self.fontSize = QtWidgets.QSpinBox()
        self.fontSize.setSuffix(" pt")
        self.fontSize.setValue(12)
        self.fontSize.setMaximumHeight(30)
        self.fontSize.valueChanged.connect(lambda size: self.text.setFontPointSize(size))

        self.fontColor = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_text_color_black"), "Change Font Color", self)
        self.fontColor.triggered.connect(self.fontColorChanged)

        self.backColor = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_highlight_black"), "Change Background Color", self)
        self.backColor.triggered.connect(self.highlight)

        #code for active and deactive format buttons
        self.boldAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_bold_black"), "Bold", self)
        self.boldAction.triggered.connect(self.bold)

        self.italicAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_italic_black"), "Italic", self)
        self.italicAction.triggered.connect(self.italic)

        self.underlAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_format_underlined_black"), "Underline", self)
        self.underlAction.triggered.connect(self.underline)

        self.superAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_superscript_black"), "Superscript", self)
        self.superAction.triggered.connect(self.superScript)

        self.subAction = QtWidgets.QAction(QtGui.QIcon(":/icons/48/ic_subscript_black"), "Subscript", self)
        self.subAction.triggered.connect(self.subScript)

        #############################################
        #  SET UP TOOLBAR WIDGETS
        #################################

        #Upper Toolbar
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setObjectName("Options")

        self.toolbar.addAction(self.undoAction)
        self.toolbar.addAction(self.redoAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.editSourceAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.clearAction)

        self.toolbar.addSeparator()

        ############################################################
        # Moved from lower toolbar to upper toolbar
        # after disabling font selection: redmine issue 414
        self.toolbar.addAction(self.boldAction)
        self.toolbar.addAction(self.italicAction)
        self.toolbar.addAction(self.underlAction)
        self.toolbar.addAction(self.superAction)
        self.toolbar.addAction(self.subAction)
        ############################################################

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.alignLeftText)
        self.toolbar.addAction(self.alignCenterText)
        self.toolbar.addAction(self.alignRightText)
        self.toolbar.addAction(self.alignJustifyText)

        self.toolbar.addSeparator()


        self.toolbar.addAction(self.bulletAction)
        self.toolbar.addAction(self.numberedAction)
        self.toolbar.addAction(self.indentAction)
        self.toolbar.addAction(self.dedentAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.insertURL)
        self.toolbar.addAction(self.insertImage)
        self.toolbar.addAction(self.wikiTag)

        # Lower Toolbar
        #self.formatbar = QtWidgets.QToolBar()
        #self.formatbar.setObjectName("Format")
        #self.formatbar.addWidget(self.fontBox)
        #self.formatbar.addWidget(self.fontSize)

        #self.formatbar.addSeparator()

        #self.formatbar.addAction(self.fontColor)
        #self.formatbar.addAction(self.backColor)

        #self.formatbar.addSeparator()

        #self.formatbar.addAction(self.boldAction)
        #self.formatbar.addAction(self.italicAction)
        #self.formatbar.addAction(self.underlAction)
        #self.formatbar.addAction(self.superAction)
        #self.formatbar.addAction(self.subAction)

        # Status Toolbar
        self.statusbar = QtWidgets.QStatusBar()

        # Main Layout
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.toolbar, 0, QtCore.Qt.AlignTop)
        #self.mainLayout.addWidget(self.formatbar)
        self.mainLayout.addWidget(self.text)
        self.mainLayout.addWidget(self.statusbar)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setWindowTitle('Description: {0}'.format(self.node.text().replace('\n','')))
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))

        connect(self.confirmationBox.accepted, self.complete)
        connect(self.confirmationBox.rejected, self.reject)
        connect(self.text.cursorPositionChanged, self.cursorPosition)
        connect(self.wikiTagDialog.sgnWikiTagSelected, self.insertWikiTag)

    def cursorPosition(self):
        """
        Returns the position of the curson in  QTextEdit
        """
        cursor = self.text.textCursor()

        line = cursor.blockNumber() + 1
        col = cursor.columnNumber()

        self.statusbar.showMessage("Line: {} | Column: {}".format(line,col))

    def bulletList(self):
        """
        Create the bullet list in QTextEditor
        """
        cursor = self.text.textCursor()

        # Insert bulleted list
        cursor.insertList(QtGui.QTextListFormat.ListDisc)

    def numberList(self):
        """
        Create the number list in QTextEditor
        """
        cursor = self.text.textCursor()

        # Insert list with numbers
        cursor.insertList(QtGui.QTextListFormat.ListDecimal)

    def fontColorChanged(self):
        """
        Change the font color in QTextEditor
        """

        # Get a color from the text dialog
        color = QtWidgets.QColorDialog.getColor()

        # Set it as the new text color
        self.text.setTextColor(color)

    def highlight(self):
        """
        Change the background color of font in QTextEditor
        """
        color = QtWidgets.QColorDialog.getColor()

        self.text.setTextBackgroundColor(color)

    def bold(self):
        """
        Change the character font in bold
        """
        if self.text.fontWeight() == QtGui.QFont.Bold:

            self.text.setFontWeight(QtGui.QFont.Normal)

        else:

            self.text.setFontWeight(QtGui.QFont.Bold)

    def italic(self):
        """
        Change the character font in italic
        """
        state = self.text.fontItalic()

        self.text.setFontItalic(not state)

    def underline(self):
        """
        Change the character font in underline
        """
        state = self.text.fontUnderline()

        self.text.setFontUnderline(not state)

    def strike(self):
        """
        Change the character font in strike
        """
        # Grab the text's format
        fmt = self.text.currentCharFormat()

        # Set the fontStrikeOut property to its opposite
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())

        # And set the next char format
        self.text.setCurrentCharFormat(fmt)

    def superScript(self):
        """
        Allow to create the character super script
        """

        # Grab the current format
        fmt = self.text.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QtGui.QTextCharFormat.AlignNormal:

            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)

        else:

            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)

    def subScript(self):
        """
        Allow to create the character sub script
        """
        # Grab the current format
        fmt = self.text.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QtGui.QTextCharFormat.AlignNormal:

            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)

        else:

            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)

    def clearFormatting(self):
        """
        Restore the char format that is used when inserting new text.
        If the editor has a selection then clear the char format of the selection.
        """
        self.text.setCurrentCharFormat(self.defaultCharFormat)

    def alignLeft(self):
        """
        Align the text to left
        """
        self.text.setAlignment(Qt.AlignLeft)

    def alignRight(self):
        """
        Align the text to right
        """
        self.text.setAlignment(Qt.AlignRight)

    def alignCenter(self):
        """
        Align the text to center
        """
        self.text.setAlignment(Qt.AlignCenter)

    def alignJustify(self):
        """
        Align the text in justify mode
        """
        self.text.setAlignment(Qt.AlignJustify)

    def indent(self):
        """
        Ident the text
        """

        # Grab the cursor
        cursor = self.text.textCursor()

        if cursor.hasSelection():

            # Store the current line/block number
            temp = cursor.blockNumber()

            # Move to the selection's end
            cursor.setPosition(cursor.anchor())

            # Calculate range of selection
            diff = cursor.blockNumber() - temp

            direction = QtGui.QTextCursor.Up if diff > 0 else QtGui.QTextCursor.Down

            # Iterate over lines (diff absolute value)
            for n in range(abs(diff) + 1):
                # Move to start of each line
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)

                # Insert tabbing
                cursor.insertText("\t")


                # And move back up
                cursor.movePosition(direction)

        # If there is no selection, just insert a tab
        else:

            cursor.insertText("\t")

    def handleDedent(self, cursor):
        """
        Manage the Dedent of the text
        """

        cursor.movePosition(QtGui.QTextCursor.StartOfLine)

        # Grab the current line
        line = cursor.block().text()

        # If the line starts with a tab character, delete it
        if line.startswith("\t"):

            # Delete next character
            cursor.deleteChar()

        # Otherwise, delete all spaces until a non-space character is met
        else:
            for char in line[:8]:

                if char != " ":
                    break

                cursor.deleteChar()

    def dedent(self):
        """
        Dedent the text
        """

        cursor = self.text.textCursor()

        if cursor.hasSelection():

            # Store the current line/block number
            temp = cursor.blockNumber()

            # Move to the selection's last line
            cursor.setPosition(cursor.anchor())

            # Calculate range of selection
            diff = cursor.blockNumber() - temp

            direction = QtGui.QTextCursor.Up if diff > 0 else QtGui.QTextCursor.Down

            # Iterate over lines
            for n in range(abs(diff) + 1):
                self.handleDedent(cursor)

                # Move up
                cursor.movePosition(direction)

        else:
            self.handleDedent(cursor)


    ############################################################
    # SLOTS
    ############################################################

    @QtCore.pyqtSlot(str, str)
    def insertWikiTag(self, wikiTagURL, wikiLabel):
        """
        Executed to insert a wiki tag.
        :param wikiTag: the wiki tag URL to insert
        :type wikiTagURL: str
        :param wikiLabel: the wiki tag label to insert
        :type wikiLabel: str
        """
        linkFormat = QtGui.QTextCharFormat()
        linkFormat.setForeground(QtGui.QColor("blue"))
        linkFormat.setFont(self.text.currentFont())
        linkFormat.setFontPointSize(self.text.fontPointSize())
        linkFormat.setAnchor(True)
        linkFormat.setAnchorHref(wikiTagURL)
        linkFormat.setToolTip(wikiTagURL)
        linkFormatSpace = QtGui.QTextCharFormat()
        linkFormatSpace.setFont(self.text.currentFont())
        linkFormatSpace.setFontPointSize(self.text.fontPointSize())

        self.text.textCursor().insertText(wikiLabel, linkFormat)
        self.text.textCursor().insertText(" ", linkFormatSpace)

    @QtCore.pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.metaDataChanged()]
        if any(commands):
            self.session.undostack.beginMacro('edit {0} description'.format(self.node.name))
            for command in commands:
                if command:
                    self.session.undostack.push(command)
            self.session.undostack.endMacro()
        super().accept()

    def metaDataChanged(self):
        """
        Change the description of the node.
        :rtype: QUndoCommand
        """
        undo = self.diagram.project.meta(self.node.type(), self.node.text())
        redo = undo.copy()
        redo[K_DESCRIPTION] = self.text.toHtml()

        if redo != undo:
            return CommandNodeSetMeta(
                self.diagram.project,
                self.node.type(),
                self.node.text(),
                undo, redo)
        return None


class UrlDialog(QtWidgets.QDialog):
    """
    This is the class that manages the insertion of url address for description dialogs.
    """
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        self.parent = parent
        self.initUI()

    def initUI(self):
        #############################################
        # CONFIRMATION BOX
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(Font('Roboto', 12))

        insert = QtWidgets.QPushButton("Insert", self)
        insert.clicked.connect(self.insert)

        cancel = QtWidgets.QPushButton("Cancel", self)
        cancel.clicked.connect(self.closeDialog)

        self.confirmationBox.addButton(cancel, QtWidgets.QDialogButtonBox.ActionRole)
        self.confirmationBox.addButton(insert, QtWidgets.QDialogButtonBox.ActionRole)

        #############################################
        # URL BOX
        #################################
        self.URLLabel = QtWidgets.QLabel(self)
        self.URLLabel.setFont(Font('Roboto', 12))
        self.URLLabel.setText('URL Link')
        self.insertBoxURL = QtWidgets.QTextEdit(self)
        self.insertBoxURL.setMaximumHeight(40)

        #############################################
        # ALIAS BOX
        #################################
        self.AliasLabel = QtWidgets.QLabel(self)
        self.AliasLabel.setFont(Font('Roboto', 12))
        self.AliasLabel.setText('Alias')
        self.insertBoxAlias = QtWidgets.QTextEdit(self)
        self.insertBoxAlias.setMaximumHeight(40)

        #############################################
        # DIALOG WINDOW LAYOUT
        #################################
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.URLLabel)
        self.layout.addWidget(self.insertBoxURL)
        self.layout.addWidget(self.AliasLabel)
        self.layout.addWidget(self.insertBoxAlias)
        self.layout.addWidget(self.confirmationBox, 5, QtCore.Qt.AlignCenter)

        self.setMaximumSize(500,200)
        self.setWindowTitle("Insert URL")
        self.setLayout(self.layout)

        self.setWindowModality(QtCore.Qt.WindowModal)

    def closeDialog(self):
        """
        Executed when the dialog is closed.
        """
        self.insertBoxAlias.clear()
        self.insertBoxURL.clear()
        self.close()

    def insert(self):
        """
        Executed when the dialog is accepted.
        """

        # Grab cursor
        cursor = self.parent.text.textCursor()
        valid= len(self.insertBoxURL.toPlainText())

        if valid > 4:
             linkFormat = QtGui.QTextCharFormat()
             linkFormatSpace = QtGui.QTextCharFormat()
             linkFormatSpace.setFont(self.parent.text.currentFont())
             linkFormatSpace.setFontPointSize(self.parent.text.fontPointSize())
             linkFormat.setForeground(QtGui.QColor("blue"))
             linkFormat.setFont(self.parent.text.currentFont())
             linkFormat.setFontPointSize(self.parent.text.fontPointSize())
             linkFormat.setFontUnderline(True)
             linkFormat.setAnchor(True)
             linkFormat.setAnchorHref(self.insertBoxURL.toPlainText())
             linkFormat.setToolTip(self.insertBoxURL.toPlainText())
             cursor.insertText(self.insertBoxAlias.toPlainText(),linkFormat)
             cursor.insertText(" ",linkFormatSpace)

        # Close the window
        self.insertBoxAlias.clear()
        self.insertBoxURL.clear()
        self.close()

class UrlImageDialog(QtWidgets.QDialog):
    """
    This is the class that manages the insertion of image url address for description dialogs.
    """

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        self.parent = parent


        self.initUI()

    def initUI(self):
        #############################################
        # URL BOX
        #################################
        self.URLLabel = QtWidgets.QLabel(self)
        self.URLLabel.setFont(Font('Roboto', 12))
        self.URLLabel.setText('URL Image')
        self.insertBoxURL = QtWidgets.QTextEdit(self)
        self.insertBoxURL.setMaximumHeight(40)


        #############################################
        # HEIGHT BOX
        #################################
        #self.heightLabel = QtWidgets.QLabel(self)
        #self.heightLabel.setFont(Font('Roboto', 12))
        #self.heightLabel.setText('Height of Image (px)')
        #self.heightBox = QtWidgets.QTextEdit(self)
        #self.heightBox.setMaximumHeight(40)


        #############################################
        # WIDTH BOX
        #################################
        #self.widthLabel = QtWidgets.QLabel(self)
        #self.widthLabel.setFont(Font('Roboto', 12))
        #self.widthLabel.setText('Width of Image (px)')
        #self.widthBox = QtWidgets.QTextEdit(self)
        #self.widthBox.setMaximumHeight(40)

        #############################################
        # CONFIRMATION BOX
        #################################
        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(Font('Roboto', 12))

        insert = QtWidgets.QPushButton("Insert", self)
        insert.clicked.connect(self.insert)

        cancel = QtWidgets.QPushButton("Cancel", self)
        cancel.clicked.connect(self.closeDialog)

        self.confirmationBox.addButton(cancel, QtWidgets.QDialogButtonBox.ActionRole)
        self.confirmationBox.addButton(insert, QtWidgets.QDialogButtonBox.ActionRole)

        #############################################
        # DIALOG WINDOW LAYOUT
        #################################
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.URLLabel)
        self.layout.addWidget(self.insertBoxURL)

        #self.layout.addWidget(self.heightLabel)
        #self.layout.addWidget(self.heightBox)
        #self.layout.addWidget(self.widthLabel)
        #self.layout.addWidget(self.widthBox)

        self.layout.addWidget(self.confirmationBox, 5, QtCore.Qt.AlignCenter)

        self.setMaximumSize(350,150)
        self.setWindowTitle("Insert URL")
        self.setLayout(self.layout)

        self.setWindowModality(QtCore.Qt.WindowModal)

    def closeDialog(self):
        """
        Executed when the dialog is closed.
        """
        self.insertBoxURL.clear()
        self.close()

    def insert(self):
        """
        Executed when the dialog is accepted.
        """

        # Grab cursor
        cursor = self.parent.text.textCursor()
        valid= len(self.insertBoxURL.toPlainText())
        linkFormat = QtGui.QTextCharFormat()
        linkFormat.setFont(self.parent.text.currentFont())
        linkFormat.setFontPointSize(self.parent.text.fontPointSize())

        if valid > 4:
               completeURL= '<img src= "'+self.insertBoxURL.toPlainText()+'" />'
               #completeURL = '<img src="' + self.insertBoxURL.toPlainText() + '" width="'+self.widthBox.toPlainText()+ '" height="'+self.heightBox.toPlainText()+ '" />'

        # Insert the url link
               cursor.insertHtml(completeURL)
               cursor.insertText(" ", linkFormat)

        # Close the window
        self.insertBoxURL.clear()
        self.close()

class WikiTagDialog(DescriptionDialog):
    """
    This is the class that manages the insertion of wiki tag for the description dialogs.
    """
    sgnWikiTagSelected = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
        """
        Initialize the WikiDialog widget.
        :param parent: the parent widget
        """
        super().__init__(parent)

        self.iconAttribute = QtGui.QIcon(':/icons/18/ic_treeview_attribute')
        self.iconConcept = QtGui.QIcon(':/icons/18/ic_treeview_concept')
        self.iconInstance = QtGui.QIcon(':/icons/18/ic_treeview_instance')
        self.iconRole = QtGui.QIcon(':/icons/18/ic_treeview_role')
        self.iconValue = QtGui.QIcon(':/icons/18/ic_treeview_value')

        self.model = QtGui.QStandardItemModel(self)
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.initUI()

        # nodes allowed in the list view
        self.nodeTypes = {Item.IndividualNode, Item.ConceptNode, Item.AttributeNode, Item.RoleNode}
        self.nodeKeys = set()

        # extract the list of nodes in the diagram
        for node in [node for node in self.session.diagram.project.nodes() if node.type() in self.nodeTypes]:
            if self.nodeKey(node) not in self.nodeKeys:
                self.nodeKeys.add(self.nodeKey(node))
                self.doAddNode(node)

        connect(self.search.textChanged, self.doFilterItem)
        connect(self.search.returnPressed, self.onSearchReturnPressed)
        connect(self.predicateView.doubleClicked, self.onItemDoubleClicked)
        connect(self.predicateView.sgnCurrentItemChanged, self.onItemChanged)
        connect(self.sgnWikiTagSelected, self.dismissDialog)

    def initUI(self):
        """
        Initialize the UI components of the widget.
        """
        #############################################
        # LIST WIDGET BOX
        #################################
        self.boxLabel = QtWidgets.QLabel(self)
        self.boxLabel.setFont(Font('Roboto', 12))
        self.boxLabel.setText('Select Ontology Predicate')
        self.search = StringField(self)
        self.search.setAcceptDrops(False)
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Search...')
        self.search.setFixedHeight(30)
        self.predicateView = OntologyPredicateView(self)
        self.predicateView.setModel(self.proxy)

        #############################################
        # CONFIRMATION BOX
        #################################
        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(Font('Roboto', 12))

        self.cancelButton = QtWidgets.QPushButton("Cancel", self)
        self.cancelButton.clicked.connect(self.dismissDialog)

        self.insertButton = QtWidgets.QPushButton("Insert", self)
        self.insertButton.clicked.connect(self.confirmDialog)
        self.insertButton.setEnabled(False)

        self.confirmationBox.addButton(self.cancelButton, QtWidgets.QDialogButtonBox.ActionRole)
        self.confirmationBox.addButton(self.insertButton, QtWidgets.QDialogButtonBox.ActionRole)

        #############################################
        # WIKI LABEL BOX
        #################################
        self.wikiLabel = QtWidgets.QLabel(self)
        self.wikiLabel.setFont(Font('Roboto', 12))
        self.wikiLabel.setText('Wiki Label')
        self.wikiLabelLineEdit = QtWidgets.QLineEdit(self)
        self.wikiLabelLineEdit.setFont(self.session.font())
        self.wikiLabelLineEdit.setMaximumHeight(40)

        #############################################
        # DIALOG WINDOW LAYOUT
        #################################
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.boxLabel)
        self.layout.addWidget(self.search)
        self.layout.addWidget(self.predicateView)
        self.layout.addWidget(self.wikiLabel)
        self.layout.addWidget(self.wikiLabelLineEdit)
        self.layout.addWidget(self.confirmationBox, 5, QtCore.Qt.AlignCenter)
        self.setTabOrder(self.search, self.predicateView)
        self.setTabOrder(self.predicateView, self.wikiLabelLineEdit)
        self.setTabOrder(self.wikiLabelLineEdit, self.confirmationBox)

        self.setFixedSize(450, 400)
        self.setMaximumSize(800,600)
        self.setWindowTitle("Insert Wiki Tag")
        self.setLayout(self.layout)

        self.setWindowModality(QtCore.Qt.WindowModal)

    def nodeKey(self, node):
        """
        Return the key for the given node
        :type node: AbstractNode
        :rtype: str
        :return: the key for the given node
        """
        return node.text().replace("\n", "")

    def iconFor(self, node):
        """
        Returns the icon for the given node.
        :type node:
        """
        if node.type() is Item.AttributeNode:
            return self.iconAttribute
        if node.type() is Item.ConceptNode:
            return self.iconConcept
        if node.type() is Item.IndividualNode:
            if node.identity() is Identity.Individual:
                return self.iconInstance
            if node.identity() is Identity.Value:
                return self.iconValue
        if node.type() is Item.RoleNode:
            return self.iconRole

    def doAddNode(self, node):
        """
        Add a node in the list view.
        :type node: AbstractItem
        """
        if node.type() in self.nodeTypes:
            item = QtGui.QStandardItem(self.nodeKey(node))
            item.setData(node)
            item.setIcon(self.iconFor(node))
            self.model.appendRow(item)
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    def validate(self):
        """
        Executed to validate all the fields the wiki tag form.
        :return: True if the wiki tag form is valid.
        """
        return self.predicateView.currentIndex().isValid()

    ##################################################
    # SLOTS
    ##################################################

    @QtCore.pyqtSlot('QModelIndex')
    def onItemDoubleClicked(self, index):
        """
        Executed when an item in the list view is double clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                self.wikiTagSelected(item.data())

    @QtCore.pyqtSlot(str)
    def doFilterItem(self, key):
        """
        Executed when the search box is filled with data.
        :type key: str
        """
        self.proxy.setFilterRegExp(QRegExp(key.replace(' ', '.*')))
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.sort(QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot()
    def onSearchReturnPressed(self):
        """
        Executed when the enter key is pressed in the search field.
        """
        self.predicateView.setFocus()

    @QtCore.pyqtSlot('QModelIndex', 'QModelIndex')
    def onItemChanged(self, currentIndex, previousIndex):
        if currentIndex is not None:
            self.insertButton.setEnabled(currentIndex.isValid())

    @QtCore.pyqtSlot('QGraphicsItem')
    def wikiTagSelected(self, item):
        """
        Validate the input and insert the wiki tag.
        :param item: the ontology predicate item
        :type item: QGraphicsItem
        """
        if item is None or not self.validate():
            # Perform here tasks like highlighting incorrect form fields
            return

        nodeName = self.nodeKey(item)
        wikiLabel = self.wikiLabelLineEdit.text()

        nodeType = item.type()
        nodeTypeToAppend = None

        if nodeType is Item.IndividualNode:
            nodeTypeToAppend = '/predicate/individual/'
        elif nodeType is Item.ConceptNode:
            nodeTypeToAppend = '/predicate/concept/'
        elif nodeType is Item.AttributeNode:
            nodeTypeToAppend = '/predicate/attribute/'
        elif nodeType is Item.RoleNode:
            nodeTypeToAppend = '/predicate/role/'

        wikiTagURL = nodeTypeToAppend + nodeName

        # Signal wiki tag insertion
        self.sgnWikiTagSelected.emit(wikiTagURL, wikiLabel if wikiLabel else nodeName)

    @QtCore.pyqtSlot()
    def confirmDialog(self):
        """
        Executed to when the dialog is accepted.
        """
        itemIndex = self.predicateView.currentIndex()

        if itemIndex.isValid():
            item = self.model.itemFromIndex(self.proxy.mapToSource(itemIndex))
            self.wikiTagSelected(item.data())

    @QtCore.pyqtSlot()
    def dismissDialog(self):
        """
        Executed when the dialog is closed.
        """
        self.search.clear()
        self.predicateView.clearSelection()
        self.wikiLabelLineEdit.clear()
        self.close()

class OntologyPredicateView(QtWidgets.QListView):
    """
    This class implements the ontology predicate view.
    """
    sgnCurrentItemChanged = QtCore.pyqtSignal('QModelIndex', 'QModelIndex')

    def __init__(self, parent=None):
        """
        Initialize the ontology predicate view.
        :param parent: the parent widget
        :type param: QWidget
        """
        super().__init__(parent)

        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setAlternatingRowColors(True)

    ############################################################
    # SLOTS
    ############################################################

    @QtCore.pyqtSlot('QModelIndex', 'QModelIndex')
    def currentChanged(self, currentIndex, previousIndex):
        """
        Executed when the current selection changes in the view.
        :param currentIndex: the index of the newly selected item
        :type currentIndex: QModelIndex
        :param previousIndex: the index of the previously selected item
        :type previousIndex: QModelIndex
        """
        self.scrollTo(currentIndex, QtWidgets.QAbstractItemView.EnsureVisible)
        self.sgnCurrentItemChanged.emit(currentIndex, previousIndex)

