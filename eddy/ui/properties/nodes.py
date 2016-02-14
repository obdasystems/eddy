# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt, QPointF, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QDialog, QPushButton, QHBoxLayout, QListWidget, QAbstractItemView
from PyQt5.QtWidgets import QVBoxLayout, QDialogButtonBox, QTabWidget, QFormLayout, QListWidgetItem

from eddy.core.commands import CommandNodeChangeMeta, CommandNodeChangeInputOrder
from eddy.core.commands import CommandNodeLabelChange, CommandNodeMove
from eddy.core.datatypes import DistinctList
from eddy.core.functions import clamp, connect, isEmpty, rCut

from eddy.ui.fields import StringField, TextField, SpinBox


########################################################################################################################
#                                                                                                                      #
#   NODE GENERIC                                                                                                       #
#                                                                                                                      #
########################################################################################################################


class NodeProperty(QDialog):
    """
    This class implements the 'Node property' dialog.
    """
    def __init__(self, scene, node, parent=None):
        """
        Initialize the node properties dialog.
        :type scene: DiagramScene
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(parent)

        self.node = node
        self.scene = scene

        # GENERAL
        self.generalWidget = QWidget()
        self.generalLayout = QFormLayout(self.generalWidget)

        self.idField = StringField(self.generalWidget)
        self.idField.setReadOnly(True)
        self.idField.setFixedWidth(300)
        self.idField.setValue(self.node.id)

        self.itemField = StringField(self.generalWidget)
        self.itemField.setReadOnly(True)
        self.itemField.setFixedWidth(300)
        self.itemField.setValue(' '.join(i.capitalize() for i in rCut(self.node.name, ' node').split()))

        self.showIdentityField = StringField(self.generalWidget)
        self.showIdentityField.setReadOnly(True)
        self.showIdentityField.setFixedWidth(300)
        self.showIdentityField.setValue(self.node.identity.label)

        self.generalLayout.addRow('ID', self.idField)
        self.generalLayout.addRow('Type', self.itemField)
        self.generalLayout.addRow('Identity', self.showIdentityField)

        # GEOMETRY
        self.geometryWidget = QWidget()
        self.geometryLayout = QFormLayout(self.geometryWidget)

        P = self.node.pos()
        R = self.scene.sceneRect()

        self.xField = SpinBox(self.geometryWidget)
        self.xField.setFixedWidth(60)
        self.xField.setRange(R.left(), R.right())
        self.xField.setValue(int(P.x()))

        self.yField = SpinBox(self.geometryWidget)
        self.yField.setFixedWidth(60)
        self.yField.setRange(R.top(), R.bottom())
        self.yField.setValue(int(P.y()))

        self.wField = SpinBox(self.geometryWidget)
        self.wField.setRange(20, R.width())
        self.wField.setReadOnly(True)
        self.wField.setFixedWidth(60)
        self.wField.setValue(int(self.node.width()))

        self.hField = SpinBox(self.geometryWidget)
        self.hField.setRange(20, R.height())
        self.hField.setReadOnly(True)
        self.hField.setFixedWidth(60)
        self.hField.setValue(int(self.node.height()))

        self.geometryLayout.addRow('X', self.xField)
        self.geometryLayout.addRow('Y', self.yField)
        self.geometryLayout.addRow('Width', self.wField)
        self.geometryLayout.addRow('Height', self.hField)

        # MAIN
        self.mainWidget = QTabWidget(self)
        self.mainWidget.addTab(self.generalWidget, 'General')
        self.mainWidget.addTab(self.geometryWidget, 'Geometry')

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.buttonBox, 0, Qt.AlignRight)

        self.setWindowTitle('Properties')
        self.setWindowIcon(QIcon(':/images/eddy'))

        connect(self.finished, self.completed)
        connect(self.buttonBox.accepted, self.accept)
        connect(self.buttonBox.rejected, self.reject)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(int)
    def completed(self, code):
        """
        Executed when the dialog is terminated.
        :type code: int
        """
        if code == QDialog.Accepted:
            self.positionChanged()

    def positionChanged(self):
        """
        Move the node properly if the position has been changed.
        """
        R = self.scene.sceneRect()
        x = clamp(self.xField.value(), R.left(), R.right())
        y = clamp(self.yField.value(), R.top(), R.bottom())
        pos1 = self.node.pos()
        pos2 = QPointF(x, y)

        if pos1 != pos2:

            commandData = {
                'redo': {
                    'nodes': {
                        self.node: {
                            'anchors': {k: v + pos2 - pos1 for k, v in self.node.anchors.items()},
                            'pos': pos2,
                        }
                    },
                    'edges': {},
                },
                'undo': {
                    'nodes': {
                        self.node: {
                            'anchors': {k: v for k, v in self.node.anchors.items()},
                            'pos': pos1,
                        }
                    },
                    'edges': {}
                }
            }

            self.scene.undostack.push(CommandNodeMove(scene=self.scene, data=commandData))
            

########################################################################################################################
#                                                                                                                      #
#   PREDICATE NODES                                                                                                    #
#                                                                                                                      #
########################################################################################################################


class PredicateNodeProperty(NodeProperty):
    """
    This class implements the property dialog for predicate nodes.
    """
    def __init__(self, scene, node, parent=None):
        """
        Initialize the predicate node properties dialog.
        :type scene: DiagramScene
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(scene, node, parent)

        meta = scene.metaIndex.metaFor(node.item, node.text())

        self.urlField = StringField(self.generalWidget)
        self.urlField.setFixedWidth(300)
        self.urlField.setValue(meta.url)

        self.descriptionField = TextField(self.generalWidget)
        self.descriptionField.setFixedSize(300, 160)
        self.descriptionField.setValue(meta.description)

        self.generalLayout.addRow('URL', self.urlField)
        self.generalLayout.addRow('Description', self.descriptionField)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(int)
    def completed(self, code):
        """
        Executed when the dialog is terminated.
        :type code: int
        """
        if code == QDialog.Accepted:
            super().completed(code)
            self.metaDataChanged()

    def metaDataChanged(self):
        """
        Change the url and description of the node.
        """
        meta = self.scene.metaIndex.metaFor(self.node.item, self.node.text())

        copy = meta.copy()
        copy.description = self.descriptionField.value()
        copy.url = self.urlField.value()

        if copy != meta:
            command = CommandNodeChangeMeta(self.scene, self.node, meta, copy)
            self.scene.undostack.push(command)


########################################################################################################################
#                                                                                                                      #
#   EDITABLE NODES                                                                                                     #
#                                                                                                                      #
########################################################################################################################


class EditableNodeProperty(PredicateNodeProperty):
    """
    This class implements the property dialog for label editable predicate nodes.
    """
    def __init__(self, scene, node, parent=None):
        """
        Initialize the editable node properties dialog.
        :type scene: DiagramScene
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(scene, node, parent)

        ################################################################################################################
        #                                                                                                              #
        #   LABEL TAB                                                                                                  #
        #                                                                                                              #
        ################################################################################################################

        self.labelWidget = QWidget()
        self.labelLayout = QFormLayout(self.labelWidget)

        self.textField = StringField(self.labelWidget)
        self.textField.setFixedWidth(300)
        self.textField.setValue(self.node.text())
        self.textField.setEnabled(self.node.label.editable)

        self.labelLayout.addRow('Text', self.textField)

        self.mainWidget.addTab(self.labelWidget, 'Label')

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def completed(self, code):
        """
        Executed when the dialog is terminated.
        :type code: int
        """
        if code == QDialog.Accepted:
            super().completed(code)
            self.labelEdited()

    def labelEdited(self):
        """
        Change the label of the node.
        """
        data = self.textField.value().strip()
        data = data if not isEmpty(data) else self.node.label.template
        if self.node.text() != data:
            command = CommandNodeLabelChange(self.scene, self.node, self.node.text(), data)
            self.scene.undostack.push(command)


########################################################################################################################
#                                                                                                                      #
#   ORDERED INPUT NODES => {ROLE CHAIN, PROPERTY ASSERTION}                                                            #
#                                                                                                                      #
########################################################################################################################


class OrderedInputNodeProperty(NodeProperty):
    """
    This class implements the propertiy dialog for constructor nodes having incoming input edges
    numbered according to source nodes partecipations to the axiom (Role chain and Property assertion).
    """
    def __init__(self, scene, node, parent=None):
        """
        Initialize the editable node properties dialog.
        :type scene: DiagramScene
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(scene, node, parent)

        ################################################################################################################
        #                                                                                                              #
        #   ORDERING TAB                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        if self.node.inputs:

            self.orderWidget = QWidget()
            self.orderLayout = QFormLayout(self.orderWidget)

            self.list = QListWidget(self.orderWidget)
            for i in self.node.inputs:
                edge = self.scene.edge(i)
                item = QListWidgetItem('{} ({})'.format(edge.source.text(), edge.source.id))
                item.setData(Qt.UserRole, edge.id)
                self.list.addItem(item)

            self.list.setCurrentRow(0)
            self.list.setDragDropMode(QAbstractItemView.NoDragDrop)

            self.buttonUp = QPushButton(self)
            self.buttonUp.setIcon(QIcon(':/icons/arrow-up'))
            self.buttonUp.setFixedSize(20, 20)
            connect(self.buttonUp.clicked, self.moveUp)

            self.buttonDown = QPushButton(self)
            self.buttonDown.setIcon(QIcon(':/icons/arrow-down'))
            self.buttonDown.setFixedSize(20, 20)

            inLayout = QVBoxLayout()
            inLayout.addWidget(self.buttonUp)
            inLayout.addWidget(self.buttonDown)
            connect(self.buttonDown.clicked, self.moveDown)

            outLayout = QHBoxLayout()
            outLayout.addWidget(self.list)
            outLayout.addLayout(inLayout)

            self.orderLayout.addRow('Sort', outLayout)

            self.mainWidget.addTab(self.orderWidget, 'Ordering')

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def moveUp(self):
        """
        Move the currently selected row up.
        """
        row = self.list.currentRow()
        if row > 0:
            item = self.list.takeItem(row)
            self.list.insertItem(row - 1, item)
            self.list.setCurrentRow(row -1)

    @pyqtSlot()
    def moveDown(self):
        """
        Move the currently selected row down.
        """
        row = self.list.currentRow()
        if row < self.list.count() - 1:
            item = self.list.takeItem(row)
            self.list.insertItem(row + 1, item)
            self.list.setCurrentRow(row + 1)

    @pyqtSlot(int)
    def completed(self, code):
        """
        Executed when the dialog is terminated.
        :type code: int
        """
        if code == QDialog.Accepted:
            super().completed(code)
            self.inputsOrderChanged()

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def inputsOrderChanged(self):
        """
        Change the order of inputs edges.
        """
        if self.node.inputs:

            inputs = DistinctList()
            for i in range(0, self.list.count()):
                item = self.list.item(i)
                inputs.append(item.data(Qt.UserRole))

            if self.node.inputs != inputs:
                self.scene.undostack.push(CommandNodeChangeInputOrder(self.scene, self.node, inputs))