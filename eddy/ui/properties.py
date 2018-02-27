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

import sys
from abc import ABCMeta

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.commands.project import CommandProjectDisconnectSpecificSignals, CommandProjectConnectSpecificSignals
from eddy.core.commands.nodes_2 import CommandProjetSetIRIPrefixesNodesDict
from eddy.core.datatypes.owl import OWLStandardIRIPrefixPairsDict
from eddy.core.commands.diagram import CommandDiagramResize
from eddy.core.commands.labels import CommandLabelChange, NewlineFeedInsensitive
from eddy.core.commands.nodes import CommandNodeChangeInputsOrder
from eddy.core.commands.nodes_2 import CommandNodeSetRemainingCharacters
from eddy.core.commands.nodes import CommandNodeMove
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity, Special
from eddy.core.datatypes.owl import Facet, Datatype
from eddy.core.datatypes.qt import Font
from eddy.core.diagram import Diagram
from eddy.core.functions.misc import clamp, isEmpty, first
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger
from eddy.core.items.nodes.common.base import AbstractNode

from eddy.ui.fields import IntegerField, StringField, TextField
from eddy.ui.fields import CheckBox, ComboBox, SpinBox


LOGGER = getLogger()


class PropertyDialog(QtWidgets.QDialog):
    """
    This is the base classe for all the property dialogs.
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
        Returns the project loaded in the active session (alias for PropertyDialog.session.project).
        :rtype: Project 
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the active session (alias for PropertyDialog.parent()).
        :rtype: Session
        """
        return self.parent()


class DiagramProperty(PropertyDialog):
    """
    This class implements the diagram properties dialog.
    """
    def __init__(self, diagram, session):
        """
        Initialize the diagram properties dialog.
        :type diagram: Diagram
        :type session: Session
        """
        super().__init__(session)

        self.diagram = diagram

        #############################################
        # GENERAL TAB
        #################################

        self.nodesLabel = QtWidgets.QLabel(self)
        self.nodesLabel.setFont(Font('Roboto', 12))
        self.nodesLabel.setText('N° nodes')
        self.nodesField = IntegerField (self)
        self.nodesField.setFixedWidth(300)
        self.nodesField.setFont(Font('Roboto', 12))
        self.nodesField.setReadOnly(True)
        self.nodesField.setValue(len(self.diagram.nodes()))

        self.edgesLabel = QtWidgets.QLabel(self)
        self.edgesLabel.setFont(Font('Roboto', 12))
        self.edgesLabel.setText('N° edges')
        self.edgesField = IntegerField(self)
        self.edgesField.setFixedWidth(300)
        self.edgesField.setFont(Font('Roboto', 12))
        self.edgesField.setReadOnly(True)
        self.edgesField.setValue(len(self.diagram.edges()))

        self.generalWidget = QtWidgets.QWidget()
        self.generalLayout = QtWidgets.QFormLayout(self.generalWidget)
        self.generalLayout.addRow(self.nodesLabel, self.nodesField)
        self.generalLayout.addRow(self.edgesLabel, self.edgesField)

        #############################################
        # GEOMETRY TAB
        #################################

        sceneRect = self.diagram.sceneRect()

        self.diagramSizeLabel = QtWidgets.QLabel(self)
        self.diagramSizeLabel.setFont(Font('Roboto', 12))
        self.diagramSizeLabel.setText('Size')
        self.diagramSizeField = SpinBox(self)
        self.diagramSizeField.setFont(Font('Roboto', 12))
        self.diagramSizeField.setRange(Diagram.MinSize, Diagram.MaxSize)
        self.diagramSizeField.setSingleStep(100)
        self.diagramSizeField.setValue(max(sceneRect.width(), sceneRect.height()))

        self.geometryWidget = QtWidgets.QWidget()
        self.geometryLayout = QtWidgets.QFormLayout(self.geometryWidget)
        self.geometryLayout.addRow(self.diagramSizeLabel, self.diagramSizeField)

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

        self.mainWidget = QtWidgets.QTabWidget(self)
        self.mainWidget.addTab(self.generalWidget,'General')
        self.mainWidget.addTab(self.geometryWidget, 'Geometry')
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setWindowTitle('Properties: {0}'.format(self.diagram.name))
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))

        connect(self.confirmationBox.accepted, self.complete)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.diagramSizeChanged()]
        if any(commands):
            self.session.undostack.beginMacro('edit {0} properties'.format(self.diagram.name))
            for command in commands:
                if command:
                    self.session.undostack.push(command)
            self.session.undostack.endMacro()
        super().accept()

    #############################################
    #   AUXILIARY METHODS
    #################################

    def diagramSizeChanged(self):
        """
        Change the size of the diagram.
        :rtype: QUndoCommand
        """
        sceneRect = self.diagram.sceneRect()
        size1 = max(sceneRect.width(), sceneRect.height())
        size2 = self.diagramSizeField.value()
        if size1 != size2:
            items = self.diagram.items()
            if items:
                x = set()
                y = set()
                for item in items:
                    if item.isEdge() or item.isNode():
                        b = item.mapRectToScene(item.boundingRect())
                        x.update({b.left(), b.right()})
                        y.update({b.top(), b.bottom()})
                size2 = max(size2, abs(min(x) * 2), abs(max(x) * 2), abs(min(y) * 2), abs(max(y) * 2))
            return CommandDiagramResize(self.diagram, QtCore.QRectF(-size2 / 2, -size2 / 2, size2, size2))
        return None


class NodeProperty(PropertyDialog):
    """
    This class implements the 'Node property' dialog.
    """
    def __init__(self, diagram, node, session):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type session: Session
        """
        super().__init__(session)

        self.diagram = diagram
        self.node = node

        #############################################
        # GENERAL TAB
        #################################

        self.idLabel = QtWidgets.QLabel(self)
        self.idLabel.setFont(Font('Roboto', 12))
        self.idLabel.setText('ID')
        self.idField = StringField(self)
        self.idField.setFont(Font('Roboto', 12))
        self.idField.setFixedWidth(300)
        self.idField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.idField.setReadOnly(True)
        self.idField.setValue(self.node.id)

        self.typeLabel = QtWidgets.QLabel(self)
        self.typeLabel.setFont(Font('Roboto', 12))
        self.typeLabel.setText('Type')
        self.typeField = StringField(self)
        self.typeField.setFont(Font('Roboto', 12))
        self.typeField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.typeField.setFixedWidth(300)
        self.typeField.setReadOnly(True)
        self.typeField.setValue(node.shortName.capitalize())

        self.identityLabel = QtWidgets.QLabel(self)
        self.identityLabel.setFont(Font('Roboto', 12))
        self.identityLabel.setText('Identity')
        self.identityField = StringField(self)
        self.identityField.setFont(Font('Roboto', 12))
        self.identityField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.identityField.setFixedWidth(300)
        self.identityField.setReadOnly(True)
        self.identityField.setValue(self.node.identityName)

        self.neighboursLabel = QtWidgets.QLabel(self)
        self.neighboursLabel.setFont(Font('Roboto', 12))
        self.neighboursLabel.setText('Neighbours')
        self.neighboursField = IntegerField(self)
        self.neighboursField.setFont(Font('Roboto', 12))
        self.neighboursField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.neighboursField.setFixedWidth(300)
        self.neighboursField.setReadOnly(True)
        self.neighboursField.setValue(len(self.node.adjacentNodes()))

        self.generalWidget = QtWidgets.QWidget()
        self.generalLayout = QtWidgets.QFormLayout(self.generalWidget)
        self.generalLayout.addRow(self.idLabel, self.idField)
        self.generalLayout.addRow(self.typeLabel, self.typeField)
        self.generalLayout.addRow(self.identityLabel, self.identityField)
        self.generalLayout.addRow(self.neighboursLabel, self.neighboursField)

        #############################################
        # GEOMETRY TAB
        #################################

        nodePos = self.node.pos()
        sceneRect = self.diagram.sceneRect()

        self.xLabel = QtWidgets.QLabel(self)
        self.xLabel.setFont(Font('Roboto', 12))
        self.xLabel.setText('X')
        self.xField = SpinBox(self)
        self.xField.setFixedWidth(60)
        self.xField.setFont(Font('Roboto', 12))
        self.xField.setRange(sceneRect.left(), sceneRect.right())
        self.xField.setValue(int(nodePos.x()))

        self.yLabel = QtWidgets.QLabel(self)
        self.yLabel.setFont(Font('Roboto', 12))
        self.yLabel.setText('Y')
        self.yField = SpinBox(self)
        self.yField.setFixedWidth(60)
        self.yField.setFont(Font('Roboto', 12))
        self.yField.setRange(sceneRect.top(), sceneRect.bottom())
        self.yField.setValue(int(nodePos.y()))

        self.widthLabel = QtWidgets.QLabel(self)
        self.widthLabel.setFont(Font('Roboto', 12))
        self.widthLabel.setText('Width')
        self.widthField = SpinBox(self)
        self.widthField.setFixedWidth(60)
        self.widthField.setFont(Font('Roboto', 12))
        self.widthField.setRange(20, sceneRect.width())
        self.widthField.setReadOnly(True)
        self.widthField.setValue(int(self.node.width()))

        self.heightLabel = QtWidgets.QLabel(self)
        self.heightLabel.setFont(Font('Roboto', 12))
        self.heightLabel.setText('Height')
        self.heightField = SpinBox(self)
        self.heightField.setFixedWidth(60)
        self.heightField.setFont(Font('Roboto', 12))
        self.heightField.setRange(20, sceneRect.height())
        self.heightField.setReadOnly(True)
        self.heightField.setValue(int(self.node.height()))

        self.geometryWidget = QtWidgets.QWidget()
        self.geometryLayout = QtWidgets.QFormLayout(self.geometryWidget)
        self.geometryLayout.addRow(self.xLabel, self.xField)
        self.geometryLayout.addRow(self.yLabel, self.yField)
        self.geometryLayout.addRow(self.widthLabel, self.widthField)
        self.geometryLayout.addRow(self.heightLabel, self.heightField)

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

        self.mainWidget = QtWidgets.QTabWidget(self)
        self.mainWidget.addTab(self.generalWidget, 'General')
        self.mainWidget.addTab(self.geometryWidget, 'Geometry')
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setWindowTitle('Properties: {0}'.format(self.node))
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))

        connect(self.confirmationBox.accepted, self.complete)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged()]
        if any(commands):
            self.session.undostack.beginMacro('edit {0} properties'.format(self.node.name))
            for command in commands:
                if command:
                    self.session.undostack.push(command)
            self.session.undostack.endMacro()
        super().accept()

    #############################################
    #   AUXILIARY METHODS
    #################################

    def positionChanged(self):
        """
        Move the node properly if the position has been changed.
        :rtype: QUndoCommand
        """
        rect = self.diagram.sceneRect()
        xPos = clamp(self.xField.value(), rect.left(), rect.right())
        yPos = clamp(self.yField.value(), rect.top(), rect.bottom())
        pos1 = self.node.pos()
        pos2 = QtCore.QPointF(xPos, yPos)
        if pos1 != pos2:
            initData = self.diagram.setupMove([self.node])
            moveData = self.diagram.completeMove(initData, pos2 - pos1)
            return CommandNodeMove(self.diagram, initData, moveData)
        return None


class PredicateNodeProperty(NodeProperty):
    """
    This class implements the property dialog for predicate nodes.
    Note that this dialog window is not used for value-domain nodes even though they are predicate nodes.
    """
    def __init__(self, diagram, node, session):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type session: Session
        """
        super().__init__(diagram, node, session)

        meta = diagram.project.meta(node.type(), node.text())

        self.iriLabel = QtWidgets.QLabel(self)
        self.iriLabel.setFont(Font('Roboto', 12))
        self.iriLabel.setText('IRI')
        self.iriField = StringField(self)
        self.iriField.setFixedWidth(300)
        self.iriField.setFont(Font('Roboto', 12))

        self.iriField.setValue(self.diagram.project.get_iri_of_node(node))

        """
        self.iriversionLabel = QtWidgets.QLabel(self)
        self.iriversionLabel.setFont(Font('Roboto', 12))
        self.iriversionLabel.setText('IRI version')
        self.iriversionField = StringField(self)
        self.iriversionField.setFixedWidth(300)
        self.iriversionField.setFont(Font('Roboto', 12))

        self.iriversionField.setValue(self.node.IRI_version(diagram.project))
        """
        #############################################
        # LABEL TAB
        #################################

        self.textLabel = QtWidgets.QLabel(self)
        self.textLabel.setFont(Font('Roboto', 12))
        self.textLabel.setText('Label')
        self.textField = StringField(self)
        self.textField.setFixedWidth(300)
        self.textField.setFont(Font('Roboto', 12))
        #if node.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode, Item.IndividualNode}:
        if (('AttributeNode' in str(type(node))) or ('ConceptNode' in str(type(node))) or (
                    'IndividualNode' in str(type(node))) or ('RoleNode' in str(type(node)))):
            self.textField.setValue(self.node.remaining_characters.replace('\n',''))
        else:
            self.textField.setValue(self.node.text().replace('\n',''))

        #if ((node.type() is Item.IndividualNode) and (node.identity() is Identity.Value)) or \
        if(('IndividualNode' in str(type(node))) and (node.identity() is Identity.Value)) or \
            (('IndividualNode' not in str(type(node))) and (node.special() is not None)):
            self.textField.setReadOnly(True)
            self.iriField.setReadOnly(True)

        self.refactorLabel = QtWidgets.QLabel(self)
        self.refactorLabel.setFont(Font('Roboto', 12))
        self.refactorLabel.setText('Refactor')
        self.refactorField = CheckBox(self)
        self.refactorField.setFont(Font('Roboto', 12))
        self.refactorField.setChecked(False)

        #if node.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode}:
        if (('AttributeNode' in str(type(node))) or ('ConceptNode' in str(type(node))) or ('RoleNode' in str(type(node)))):
            if node.special() is not None:
                self.refactorField.setEnabled(False)

        self.FulliriLabel = QtWidgets.QLabel(self)
        self.FulliriLabel.setFont(Font('Roboto', 12))
        self.FulliriLabel.setText('Full IRI')
        self.FulliriField = StringField(self)
        self.FulliriField.setFixedWidth(300)
        self.FulliriField.setFont(Font('Roboto', 12))
        full_iri = self.project.get_full_IRI(self.iriField.value(), None, self.textField.value().strip())
        self.FulliriField.setValue(full_iri)
        # self.FulliriField.setValue(self.iriField.value()+'#'+self.textField.value().strip())
        self.FulliriField.setReadOnly(True)

        self.labelWidget = QtWidgets.QWidget()
        self.labelLayout = QtWidgets.QFormLayout(self.labelWidget)
        self.labelLayout.addRow(self.iriLabel, self.iriField)
        self.labelLayout.addRow(self.textLabel, self.textField)
        self.labelLayout.addRow(self.FulliriLabel, self.FulliriField)
        self.labelLayout.addRow(self.refactorLabel, self.refactorField)

        self.mainWidget.addTab(self.labelWidget, 'IRI')

        self.metaDataChanged_ADD_OK_var = None
        self.metaDataChanged_REMOVE_OK_var = None
        self.metaDataChanged_IGNORE_var = None
    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged()]

        iri_changed_result = self.IRIChanged()

        if iri_changed_result is not None:
            if (str(type(iri_changed_result)) is '<class \'str\'>') and ('Error in' in iri_changed_result):
                super().reject()
                return
            else:

                commands.extend(iri_changed_result)

        text_changed_result = self.textChanged()
        if text_changed_result is not None:
            commands.extend(text_changed_result)


        if any(commands):
            self.session.undostack.beginMacro('edit {0} properties'.format(self.node.name))
            for command in commands:
                if command:
                    self.session.undostack.push(command)
            self.session.undostack.endMacro()
        super().accept()

    #############################################
    #   AUXILIARY METHODS
    #################################
    def textChanged(self):

        unprocessed_new_text = self.textField.value().strip()
        unprocessed_new_text = unprocessed_new_text if not isEmpty(unprocessed_new_text) else self.node.label.template

        exception_list = ['-','_','.','~','\n']
        new_rc = ''

        flag = False

        for i,c in enumerate(unprocessed_new_text):
            if c == '':
                pass
            elif i < (len(unprocessed_new_text) - 1) and (c == '\\' and unprocessed_new_text[i + 1] == 'n'):
                new_rc = new_rc + '\n'
            elif i > 0 and (c == 'n' and unprocessed_new_text[i - 1] == '\\'):
                pass
            elif (not c.isalnum()) and (c not in exception_list):
                new_rc = new_rc + '_'
                flag = True
            else:
                new_rc = new_rc + c

        #new_rc = new_rc.replace('\n','')

        if flag is True:
            self.session.statusBar().showMessage('Spaces in between alphanumeric characters and special characters were replaced by an underscore character.',15000)

        return_list = []

        if (unprocessed_new_text != self.node.remaining_characters):

            #print('unprocessed_new_text',unprocessed_new_text)
            #print('self.node.remaining_characters',self.node.remaining_characters)
            #print(NewlineFeedInsensitive(new_rc, self.node.remaining_characters).result())

            return_list.append(CommandProjectDisconnectSpecificSignals(self.project))

            if self.refactorField.isChecked():
                for n in self.project.nodes():
                    if n.text() == self.node.text():
                        return_list.append(
                            CommandNodeSetRemainingCharacters(n.remaining_characters, new_rc, n, self.project,
                                                              refactor=True))
            else:
                refactor_var = NewlineFeedInsensitive(new_rc, self.node.remaining_characters).result()

                return_list.append(
                        CommandNodeSetRemainingCharacters(self.node.remaining_characters, new_rc, self.node, self.project, refactor=refactor_var))

            return_list.append(CommandProjectConnectSpecificSignals(self.project))

            return return_list

        return None


    def IRIChanged(self):
        #Change the iri of the node.
        #:rtype: Command

        IRI_valid = self.project.check_validity_of_IRI(self.iriField.value())

        if IRI_valid is False:
            self.session.statusBar().showMessage('Invalid IRI.', 15000)
            return None
        else:

            old_iri = self.project.get_iri_of_node(self.node)
            new_iri = self.iriField.value()

            #if (self.iriField.value() != self.project.get_iri_of_node(node)) or (self.iriversionField.value() != self.node.IRI_version(self.project)):
            if new_iri != old_iri:
                connect(self.project.sgnIRINodeEntryAdded, self.metaDataChanged_ADD_OK)
                connect(self.project.sgnIRINodeEntryRemoved, self.metaDataChanged_REMOVE_OK)
                connect(self.project.sgnIRINodeEntryIgnored, self.metaDataChanged_IGNORE)

                # check for conflict in prefixes
                # transaction = remove(old) + add(new)
                # perform transaction on duplicate dict.
                # if successful, original_dict = duplicate_dict
                # else duplicate_dict = original_dict


                Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())
                Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())

                list_of_nodes_to_process = []

                if self.refactorField.isChecked():
                    for n in self.project.nodes():
                        if (self.project.get_iri_of_node(n) == old_iri) and (n.remaining_characters == self.node.remaining_characters):
                            list_of_nodes_to_process.append(n)
                else:
                    list_of_nodes_to_process.append(self.node)

                commands = []

                for nd in list_of_nodes_to_process:

                    self.project.removeIRINodeEntry(Duplicate_dict_1, old_iri, nd)
                    self.project.addIRINodeEntry(Duplicate_dict_1, new_iri, nd)

                    if (self.metaDataChanged_REMOVE_OK_var is True) and (self.metaDataChanged_ADD_OK_var is True):
                        self.metaDataChanged_REMOVE_OK_var = False
                        self.metaDataChanged_ADD_OK_var = False
                        self.metaDataChanged_IGNORE_var = False
                    else:
                        LOGGER.warning('redo != undo but transaction was not executed correctly')
                        self.metaDataChanged_REMOVE_OK_var = False
                        self.metaDataChanged_ADD_OK_var = False
                        self.metaDataChanged_IGNORE_var = False
                        return str('Error in '+str(nd))

                if len(Duplicate_dict_1[new_iri][0]) == 0:
                    ###
                    if 'display_in_widget' in Duplicate_dict_1[new_iri][2]:
                        new_label = ':'+self.node.remaining_characters
                    else:
                        new_label = self.project.get_full_IRI(new_iri, None, self.node.remaining_characters)
                else:
                    new_label = str(Duplicate_dict_1[new_iri][0][len(Duplicate_dict_1[new_iri][0]) - 1] + ':' + self.node.remaining_characters)

                commands.append(CommandProjectDisconnectSpecificSignals(self.project))

                for nd in list_of_nodes_to_process:
                    commands.append(CommandLabelChange(nd.diagram, nd, nd.text(), new_label))

                commands.append(CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1,
                                                                     [new_iri, old_iri], list_of_nodes_to_process))

                for nd in list_of_nodes_to_process:
                    commands.append(CommandLabelChange(nd.diagram, nd, nd.text(), new_label))

                commands.append(CommandProjectConnectSpecificSignals(self.project))

                return commands

            self.metaDataChanged_REMOVE_OK_var = False
            self.metaDataChanged_ADD_OK_var = False
            self.metaDataChanged_IGNORE_var = False

            return None

    @QtCore.pyqtSlot(str, str, str)
    def metaDataChanged_REMOVE_OK(self, iri, node, message):

        #print('metaDataChanged_REMOVE_OK -', iri, ',', node, ',', message)
        self.metaDataChanged_REMOVE_OK_var = True

    @QtCore.pyqtSlot(str, str, str)
    def metaDataChanged_ADD_OK(self, iri, node, message):

        #print('metaDataChanged_ADD_OK -', iri, ',', node, ',', message)
        self.metaDataChanged_ADD_OK_var = True

    @QtCore.pyqtSlot(str, str, str)
    def metaDataChanged_IGNORE(self, iri, node, message):

        #if node.id is None:
            #print('metaDataChanged_IGNORE >', iri, '-', 'None', '-', message)
        #else:
        #print('metaDataChanged_IGNORE >', iri, '-', node, '-', message)
        self.metaDataChanged_IGNORE_var = True


class OrderedInputNodeProperty(NodeProperty):
    """
    This class implements the property dialog for constructor nodes having incoming input edges
    numbered according to source nodes partecipations to the axiom (Role chain and Property assertion).
    """
    def __init__(self, diagram, node, session):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type session: Session
        """
        super().__init__(diagram, node, session)

        #############################################
        # ORDERING TAB
        #################################

        if self.node.inputs:

            self.sortLabel = QtWidgets.QLabel(self)
            self.sortLabel.setFont(Font('Roboto', 12))
            self.sortLabel.setText('Sort')
            self.list = QtWidgets.QListWidget(self)
            for i in self.node.inputs:
                edge = self.diagram.edge(i)
                item = QtWidgets.QListWidgetItem('{0} ({1})'.format(edge.source.text(), edge.source.id))
                item.setData(QtCore.Qt.UserRole, edge.id)
                self.list.addItem(item)
            self.list.setCurrentRow(0)
            self.list.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)

            self.buttonUp = QtWidgets.QPushButton(self)
            self.buttonUp.setIcon(QtGui.QIcon(':/icons/24/ic_keyboard_arrow_up_black'))
            self.buttonUp.setFixedSize(20, 20)
            connect(self.buttonUp.clicked, self.moveUp)

            self.buttonDown = QtWidgets.QPushButton(self)
            self.buttonDown.setIcon(QtGui.QIcon(':/icons/24/ic_keyboard_arrow_down_black'))
            self.buttonDown.setFixedSize(20, 20)
            connect(self.buttonDown.clicked, self.moveDown)

            inLayout = QtWidgets.QVBoxLayout()
            inLayout.addWidget(self.buttonUp)
            inLayout.addWidget(self.buttonDown)

            outLayout = QtWidgets.QHBoxLayout()
            outLayout.addWidget(self.list)
            outLayout.addLayout(inLayout)

            self.orderWidget = QtWidgets.QWidget()
            self.orderLayout = QtWidgets.QFormLayout(self.orderWidget)
            self.orderLayout.addRow(self.sortLabel, outLayout)

            self.mainWidget.addTab(self.orderWidget, 'Ordering')

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def moveUp(self):
        """
        Move the currently selected row up.
        """
        i = self.list.currentRow()
        if i > 0:
            item = self.list.takeItem(i)
            self.list.insertItem(i - 1, item)
            self.list.setCurrentRow(i - 1)

    @QtCore.pyqtSlot()
    def moveDown(self):
        """
        Move the currently selected row down.
        """
        i = self.list.currentRow()
        if i < self.list.count() - 1:
            item = self.list.takeItem(i)
            self.list.insertItem(i + 1, item)
            self.list.setCurrentRow(i + 1)

    @QtCore.pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged(), self.orderingChanged()]
        if any(commands):
            self.session.undostack.beginMacro('edit {0} properties'.format(self.node.name))
            for command in commands:
                if command:
                    self.session.undostack.push(command)
            self.session.undostack.endMacro()
        super().accept()

    #############################################
    #   AUXILIARY METHODS
    #################################

    def orderingChanged(self):
        """
        Change the order of inputs edges.
        :rtype: QUndoCommand
        """
        if self.node.inputs:
            inputs = DistinctList()
            for i in range(0, self.list.count()):
                item = self.list.item(i)
                inputs.append(item.data(QtCore.Qt.UserRole))
            if self.node.inputs != inputs:
                return CommandNodeChangeInputsOrder(self.diagram, self.node, inputs)
        return None


class FacetNodeProperty(NodeProperty):
    """
    This class implements the property dialog for facet nodes.
    """
    def __init__(self, diagram, node, session):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type session: Session
        """
        super().__init__(diagram, node, session)

        #############################################
        # FACET TAB
        #################################

        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.DatatypeRestrictionNode
        f3 = lambda x: x.type() is Item.ValueDomainNode
        admissible = [x for x in Facet]
        restriction = first(self.node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if restriction:
            valuedomain = first(restriction.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            if valuedomain:
                admissible = Facet.forDatatype(valuedomain.datatype)

        self.facetLabel = QtWidgets.QLabel(self)
        self.facetLabel.setFont(Font('Roboto', 12))
        self.facetLabel.setText('Facet')
        self.facetField = ComboBox(self)
        self.facetField.setFixedWidth(200)
        self.facetField.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.facetField.setFont(Font('Roboto', 12))
        for facet in admissible:
            self.facetField.addItem(facet.value, facet)
        facet = self.node.facet
        for i in range(self.facetField.count()):
            if self.facetField.itemData(i) is facet:
                self.facetField.setCurrentIndex(i)
                break
        else:
            self.facetField.setCurrentIndex(0)

        self.valueLabel = QtWidgets.QLabel(self)
        self.valueLabel.setFont(Font('Roboto', 12))
        self.valueLabel.setText('Value')
        self.valueField = StringField(self)
        self.valueField.setFixedWidth(200)
        self.valueField.setFont(Font('Roboto', 12))
        self.valueField.setValue(self.node.value)

        self.facetWidget = QtWidgets.QWidget()
        self.facetLayout = QtWidgets.QFormLayout(self.facetWidget)
        self.facetLayout.addRow(self.facetLabel, self.facetField)
        self.facetLayout.addRow(self.valueLabel, self.valueField)

        self.mainWidget.addTab(self.facetWidget, 'Facet')

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged(), self.facetChanged()]
        if any(commands):
            self.session.undostack.beginMacro('edit {0} properties'.format(self.node.name))
            for command in commands:
                if command:
                    self.session.undostack.push(command)
            self.session.undostack.endMacro()
        super().accept()

    #############################################
    #   AUXILIARY METHODS
    #################################

    def facetChanged(self):
        """
        Change the facet value of the node of the node.
        :rtype: QUndoCommand
        """
        data = self.node.compose(self.facetField.currentData(), self.valueField.value())
        if self.node.text() != data:
            return CommandLabelChange(self.diagram, self.node, self.node.text(), data)
        return None


class ValueDomainNodeProperty(NodeProperty):
    """
    This class implements the property dialog for value-domain nodes.
    """
    def __init__(self, diagram, node, session):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type session: Session
        """
        super().__init__(diagram, node, session)

        #############################################
        # DATATYPE TAB
        #################################

        self.datatypeLabel = QtWidgets.QLabel(self)
        self.datatypeLabel.setFont(Font('Roboto', 12))
        self.datatypeLabel.setText('Datatype')
        self.datatypeField = ComboBox(self)
        self.datatypeField.setFixedWidth(200)
        self.datatypeField.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.datatypeField.setFont(Font('Roboto', 12))

        for datatype in Datatype:
            self.datatypeField.addItem(datatype.value, datatype)
        datatype = self.node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break
        else:
            self.datatypeField.setCurrentIndex(0)

        self.datatypeWidget = QtWidgets.QWidget()
        self.datatypeLayout = QtWidgets.QFormLayout(self.datatypeWidget)
        self.datatypeLayout.addRow(self.datatypeLabel, self.datatypeField)

        self.mainWidget.addTab(self.datatypeWidget, 'Datatype')

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged(), self.datatypeChanged()]
        if any(commands):
            self.session.undostack.beginMacro('edit {0} properties'.format(self.node.name))
            for command in commands:
                if command:
                    self.session.undostack.push(command)
            self.session.undostack.endMacro()
        super().accept()

    #############################################
    #   AUXILIARY METHODS
    #################################

    def datatypeChanged(self):
        """
        Change the datatype of the node.
        :rtype: QUndoCommand
        """
        datatype = self.datatypeField.currentData()
        data = datatype.value
        if self.node.text() != data:
            return CommandLabelChange(self.diagram, self.node, self.node.text(), data)
        return None


class ValueNodeProperty(NodeProperty):
    """
    This class implements the property dialog for value nodes.
    """
    def __init__(self, diagram, node, session):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type session: Session
        """
        super().__init__(diagram, node, session)

        self.node = node

        #############################################
        # VALUE TAB
        #################################

        self.datatypeLabel = QtWidgets.QLabel(self)
        self.datatypeLabel.setFont(Font('Roboto', 12))
        self.datatypeLabel.setText('Datatype')
        self.datatypeField = ComboBox(self)
        self.datatypeField.setFixedWidth(200)
        self.datatypeField.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.datatypeField.setFont(Font('Roboto', 12))

        for datatype in Datatype:
            self.datatypeField.addItem(datatype.value, datatype)
        datatype = self.node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break
        else:
            self.datatypeField.setCurrentIndex(0)

        self.valueLabel = QtWidgets.QLabel(self)
        self.valueLabel.setFont(Font('Roboto', 12))
        self.valueLabel.setText('Value')
        self.valueField = StringField(self)
        self.valueField.setFixedWidth(200)
        self.valueField.setFont(Font('Roboto', 12))
        self.valueField.setValue(self.node.value)

        self.valueWidget = QtWidgets.QWidget()
        self.valueLayout = QtWidgets.QFormLayout(self.valueWidget)
        self.valueLayout.addRow(self.datatypeLabel, self.datatypeField)
        self.valueLayout.addRow(self.valueLabel, self.valueField)

        self.mainWidget.addTab(self.valueWidget, 'Datatype')

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged()]
        commands_value_changed = self.valueChanged()

        if commands_value_changed is not None:
            commands.extend(commands_value_changed)

        if any(commands):
            self.session.undostack.beginMacro('edit {0} properties'.format(self.node.name))
            for command in commands:
                if command:
                    self.session.undostack.push(command)
            self.session.undostack.endMacro()
        super().accept()

    #############################################
    #   AUXILIARY METHODS
    #################################

    def valueChanged(self):
        """
        Change the value of the node.
        :rtype: QUndoCommand
        """
        datatype = self.datatypeField.currentData()
        value = self.valueField.value()
        data = self.node.compose(value, datatype)
        if self.node.text() != data:

            new_prefix = datatype.value[0:datatype.value.index(':')]
            new_remaining_characters = datatype.value[datatype.value.index(':') + 1:len(datatype.value)]
            #new_remaining_characters = new_remaining_characters.replace('\n','')
            new_iri = None

            for std_iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
                std_prefix = OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict[std_iri]
                if std_prefix == new_prefix:
                    new_iri = std_iri

            Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict,dict())
            Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict,dict())

            old_iri = self.project.get_iri_of_node(self.node)

            Duplicate_dict_1[old_iri][1].remove(self.node)
            Duplicate_dict_1[new_iri][1].add(self.node)

            commands = []

            commands.append(CommandLabelChange(self.diagram, self.node, self.node.text(), data))
            commands.append(CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1, [old_iri, new_iri], [self.node]))
            commands.append(CommandNodeSetRemainingCharacters(self.node.remaining_characters,\
                                                              new_remaining_characters,self.node,self.project))
            commands.append(CommandLabelChange(self.diagram, self.node, self.node.text(), data))

            return commands

        return None