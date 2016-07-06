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


from abc import ABCMeta

from PyQt5.QtCore import Qt, QPointF, pyqtSlot, QObject, QRectF
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QDialog, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtWidgets import QListWidget, QAbstractItemView, QVBoxLayout
from PyQt5.QtWidgets import QDialogButtonBox, QTabWidget, QFormLayout
from PyQt5.QtWidgets import QListWidgetItem

from eddy.core.commands.diagram import CommandDiagramResize
from eddy.core.commands.labels import CommandLabelChange
from eddy.core.commands.nodes import CommandNodeChangeInputsOrder
from eddy.core.commands.nodes import CommandNodeChangeMeta
from eddy.core.commands.nodes import CommandNodeMove
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.owl import Facet, Datatype
from eddy.core.diagram import Diagram
from eddy.core.functions.misc import clamp, isEmpty, first
from eddy.core.functions.signals import connect
from eddy.core.qt import Font

from eddy.lang import gettext as _

from eddy.ui.fields import IntegerField, StringField, TextField
from eddy.ui.fields import CheckBox, ComboBox, SpinBox


class PropertyDialog(QDialog):
    """
    This is the base classe for all the property dialogs.
    """
    __metaclass__ = ABCMeta

    def __init__(self, parent=None):
        """
        Initialize the property dialog.
        :type parent: MainWindow
        """
        super().__init__(parent)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the project loaded in the main window.
        :rtype: Project 
        """
        mainwindow = self.parent()
        return mainwindow.project


class DiagramProperty(PropertyDialog):
    """
    This class implements the diagram properties dialog.
    """
    def __init__(self, diagram, parent=None):
        """
        Initialize the diagram properties dialog.
        :type diagram: Diagram
        :type parent: QWidget
        """
        super().__init__(parent)

        self.diagram = diagram

        arial12r = Font('Arial', 12)

        #############################################
        # GENERAL TAB
        #################################

        self.nodesLabel = QLabel(self)
        self.nodesLabel.setFont(arial12r)
        self.nodesLabel.setText(_('PROPERTY_DIAGRAM_LABEL_NUM_NODES'))
        self.nodesField = IntegerField(self)
        self.nodesField.setFixedWidth(300)
        self.nodesField.setFont(arial12r)
        self.nodesField.setReadOnly(True)
        self.nodesField.setValue(len(self.diagram.nodes()))

        self.edgesLabel = QLabel(self)
        self.edgesLabel.setFont(arial12r)
        self.edgesLabel.setText(_('PROPERTY_DIAGRAM_LABEL_NUM_EDGES'))
        self.edgesField = IntegerField(self)
        self.edgesField.setFixedWidth(300)
        self.edgesField.setFont(arial12r)
        self.edgesField.setReadOnly(True)
        self.edgesField.setValue(len(self.diagram.edges()))

        self.generalWidget = QWidget()
        self.generalLayout = QFormLayout(self.generalWidget)
        self.generalLayout.addRow(self.nodesLabel, self.nodesField)
        self.generalLayout.addRow(self.edgesLabel, self.edgesField)

        #############################################
        # GEOMETRY TAB
        #################################

        sceneRect = self.diagram.sceneRect()

        self.diagramSizeLabel = QLabel(self)
        self.diagramSizeLabel.setFont(arial12r)
        self.diagramSizeLabel.setText(_('PROPERTY_DIAGRAM_LABEL_SIZE'))
        self.diagramSizeField = SpinBox(self)
        self.diagramSizeField.setFont(arial12r)
        self.diagramSizeField.setRange(Diagram.MinSize, Diagram.MaxSize)
        self.diagramSizeField.setSingleStep(100)
        self.diagramSizeField.setValue(max(sceneRect.width(), sceneRect.height()))

        self.geometryWidget = QWidget()
        self.geometryLayout = QFormLayout(self.geometryWidget)
        self.geometryLayout.addRow(self.diagramSizeLabel, self.diagramSizeField)

        #############################################
        # CONFIRMATION BOX
        #################################

        self.confirmationBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)

        #############################################
        # MAIN WIDGET
        #################################

        self.mainWidget = QTabWidget(self)
        self.mainWidget.addTab(self.generalWidget, _('PROPERTY_DIAGRAM_TAB_GENERAL'))
        self.mainWidget.addTab(self.geometryWidget, _('PROPERTY_DIAGRAM_TAB_GEOMETRY'))
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, Qt.AlignRight)

        self.setWindowTitle(_('PROPERTY_DIAGRAM_WINDOW_TITLE', self.diagram.name))
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))

        connect(self.confirmationBox.accepted, self.complete)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.diagramSizeChanged()]
        if any(commands):
            self.project.undoStack.beginMacro(_('COMMAND_DIAGRAM_EDIT_PROPERTIES', self.diagram.name))
            for command in commands:
                if command:
                    self.project.undoStack.push(command)
            self.project.undoStack.endMacro()
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
            return CommandDiagramResize(self.diagram, QRectF(-size2 / 2, -size2 / 2, size2, size2))
        return None


class NodeProperty(PropertyDialog):
    """
    This class implements the 'Node property' dialog.
    """
    def __init__(self, diagram, node, parent=None):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(parent)

        self.diagram = diagram
        self.node = node

        arial12r = Font('Arial', 12)

        #############################################
        # GENERAL TAB
        #################################

        self.idLabel = QLabel(self)
        self.idLabel.setFont(arial12r)
        self.idLabel.setText(_('PROPERTY_NODE_LABEL_ID'))
        self.idField = StringField(self)
        self.idField.setFont(arial12r)
        self.idField.setReadOnly(True)
        self.idField.setFixedWidth(300)
        self.idField.setValue(self.node.id)

        self.typeLabel = QLabel(self)
        self.typeLabel.setFont(arial12r)
        self.typeLabel.setText(_('PROPERTY_NODE_LABEL_TYPE'))
        self.typeField = StringField(self)
        self.typeField.setFont(arial12r)
        self.typeField.setReadOnly(True)
        self.typeField.setFixedWidth(300)
        self.typeField.setValue(node.shortname.capitalize())

        self.identityLabel = QLabel(self)
        self.identityLabel.setFont(arial12r)
        self.identityLabel.setText(_('PROPERTY_NODE_LABEL_IDENTITY'))
        self.identityField = StringField(self)
        self.identityField.setFont(arial12r)
        self.identityField.setReadOnly(True)
        self.identityField.setFixedWidth(300)
        self.identityField.setValue(self.node.identity.value)

        self.neighboursLabel = QLabel(self)
        self.neighboursLabel.setFont(arial12r)
        self.neighboursLabel.setText(_('PROPERTY_NODE_LABEL_NEIGHBOURS'))
        self.neighboursField = IntegerField(self)
        self.neighboursField.setFont(arial12r)
        self.neighboursField.setReadOnly(True)
        self.neighboursField.setFixedWidth(300)
        self.neighboursField.setValue(len(self.node.adjacentNodes()))

        self.generalWidget = QWidget()
        self.generalLayout = QFormLayout(self.generalWidget)
        self.generalLayout.addRow(self.idLabel, self.idField)
        self.generalLayout.addRow(self.typeLabel, self.typeField)
        self.generalLayout.addRow(self.identityLabel, self.identityField)
        self.generalLayout.addRow(self.neighboursLabel, self.neighboursField)

        #############################################
        # GEOMETRY TAB
        #################################

        nodePos = self.node.pos()
        sceneRect = self.diagram.sceneRect()

        self.xLabel = QLabel(self)
        self.xLabel.setFont(arial12r)
        self.xLabel.setText(_('PROPERTY_NODE_LABEL_X'))
        self.xField = SpinBox(self)
        self.xField.setFixedWidth(60)
        self.xField.setFont(arial12r)
        self.xField.setRange(sceneRect.left(), sceneRect.right())
        self.xField.setValue(int(nodePos.x()))

        self.yLabel = QLabel(self)
        self.yLabel.setFont(arial12r)
        self.yLabel.setText(_('PROPERTY_NODE_LABEL_Y'))
        self.yField = SpinBox(self)
        self.yField.setFixedWidth(60)
        self.yField.setFont(arial12r)
        self.yField.setRange(sceneRect.top(), sceneRect.bottom())
        self.yField.setValue(int(nodePos.y()))

        self.widthLabel = QLabel(self)
        self.widthLabel.setFont(arial12r)
        self.widthLabel.setText(_('PROPERTY_NODE_LABEL_WIDTH'))
        self.widthField = SpinBox(self)
        self.widthField.setFixedWidth(60)
        self.widthField.setFont(arial12r)
        self.widthField.setRange(20, sceneRect.width())
        self.widthField.setReadOnly(True)
        self.widthField.setValue(int(self.node.width()))

        self.heightLabel = QLabel(self)
        self.heightLabel.setFont(arial12r)
        self.heightLabel.setText(_('PROPERTY_NODE_LABEL_HEIGHT'))
        self.heightField = SpinBox(self)
        self.heightField.setFixedWidth(60)
        self.heightField.setFont(arial12r)
        self.heightField.setRange(20, sceneRect.height())
        self.heightField.setReadOnly(True)
        self.heightField.setValue(int(self.node.height()))

        self.geometryWidget = QWidget()
        self.geometryLayout = QFormLayout(self.geometryWidget)
        self.geometryLayout.addRow(self.xLabel, self.xField)
        self.geometryLayout.addRow(self.yLabel, self.yField)
        self.geometryLayout.addRow(self.widthLabel, self.widthField)
        self.geometryLayout.addRow(self.heightLabel, self.heightField)

        #############################################
        # CONFIRMATION BOX
        #################################

        self.confirmationBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)

        #############################################
        # MAIN WIDGET
        #################################

        self.mainWidget = QTabWidget(self)
        self.mainWidget.addTab(self.generalWidget, _('PROPERTY_NODE_TAB_GENERAL'))
        self.mainWidget.addTab(self.geometryWidget, _('PROPERTY_NODE_TAB_GEOMETRY'))
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, Qt.AlignRight)

        self.setWindowTitle(_('PROPERTY_NODE_WINDOW_TITLE', self.node))
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))

        connect(self.confirmationBox.accepted, self.complete)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged()]
        if any(commands):
            self.project.undoStack.beginMacro(_('COMMAND_NODE_EDIT_PROPERTIES', self.node.name))
            for command in commands:
                if command:
                    self.project.undoStack.push(command)
            self.project.undoStack.endMacro()
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
        pos2 = QPointF(xPos, yPos)

        if pos1 != pos2:

            node = self.node
            data = {
                'redo': {
                    'nodes': {node: {'anchors': {k: v + pos2 - pos1 for k, v in node.anchors.items()}, 'pos': pos2}},
                    'edges': {},
                },
                'undo': {
                    'nodes': {node: {'anchors': {k: v for k, v in node.anchors.items()}, 'pos': pos1}},
                    'edges': {}
                }
            }

            return CommandNodeMove(self.diagram, data)

        return None


class PredicateNodeProperty(NodeProperty):
    """
    This class implements the property dialog for predicate nodes.
    Note that this dialog window is not used for value-domain nodes even though they are predicate nodes.
    """
    def __init__(self, diagram, node, parent=None):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(diagram, node, parent)

        arial12r = Font('Arial', 12)

        meta = diagram.project.meta(node.type(), node.text())

        self.urlLabel = QLabel(self)
        self.urlLabel.setFont(arial12r)
        self.urlLabel.setText(_('PROPERTY_NODE_LABEL_URL'))
        self.urlField = StringField(self)
        self.urlField.setFixedWidth(300)
        self.urlField.setFont(arial12r)
        self.urlField.setValue(meta.url)

        self.descriptionLabel = QLabel(self)
        self.descriptionLabel.setFont(arial12r)
        self.descriptionLabel.setText(_('PROPERTY_NODE_LABEL_DESCRIPTION'))
        self.descriptionField = TextField(self)
        self.descriptionField.setFixedSize(300, 160)
        self.descriptionField.setFont(arial12r)
        self.descriptionField.setValue(meta.description)

        self.generalLayout.addRow(self.urlLabel, self.urlField)
        self.generalLayout.addRow(self.descriptionLabel, self.descriptionField)

        #############################################
        # LABEL TAB
        #################################

        self.textLabel = QLabel(self)
        self.textLabel.setFont(arial12r)
        self.textLabel.setText(_('PROPERTY_NODE_LABEL_TEXT'))
        self.textField = StringField(self)
        self.textField.setFixedWidth(300)
        self.textField.setFont(arial12r)
        self.textField.setValue(self.node.text())

        self.refactorLabel = QLabel(self)
        self.refactorLabel.setFont(arial12r)
        self.refactorLabel.setText(_('PROPERTY_NODE_LABEL_REFACTOR'))
        self.refactorField = CheckBox(self)
        self.refactorField.setFont(arial12r)
        self.refactorField.setChecked(False)

        if node.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode}:
            if node.special is not None:
                self.refactorField.setEnabled(False)

        self.labelWidget = QWidget()
        self.labelLayout = QFormLayout(self.labelWidget)
        self.labelLayout.addRow(self.textLabel, self.textField)
        self.labelLayout.addRow(self.refactorLabel, self.refactorField)

        self.mainWidget.addTab(self.labelWidget, _('PROPERTY_NODE_TAB_LABEL'))

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged(), self.metaDataChanged()]
        commands.extend(self.textChanged())
        if any(commands):
            self.project.undoStack.beginMacro(_('COMMAND_NODE_EDIT_PROPERTIES', self.node.name))
            for command in commands:
                if command:
                    self.project.undoStack.push(command)
            self.project.undoStack.endMacro()
        super().accept()

    #############################################
    #   AUXILIARY METHODS
    #################################

    def metaDataChanged(self):
        """
        Change the url and description of the node.
        :rtype: QUndoCommand
        """
        meta = self.diagram.project.meta(self.node.type(), self.node.text())
        copy = meta.copy()
        copy.description = self.descriptionField.value()
        copy.url = self.urlField.value()
        if copy != meta:
            return CommandNodeChangeMeta(self.diagram, self.node, meta, copy)
        return None

    def textChanged(self):
        """
        Change the label of the node.
        :rtype: list
        """
        data = self.textField.value().strip()
        data = data if not isEmpty(data) else self.node.label.template
        if self.node.text() != data:
            if self.refactorField.isChecked():
                item = self.node.type()
                name = self.node.text()
                project = self.diagram.project
                return [CommandLabelChange(n.diagram, n, n.text(), data) for n in project.predicates(item, name)]
            return [CommandLabelChange(self.diagram, self.node, self.node.text(), data)]
        return [None]


class OrderedInputNodeProperty(NodeProperty):
    """
    This class implements the propertiy dialog for constructor nodes having incoming input edges
    numbered according to source nodes partecipations to the axiom (Role chain and Property assertion).
    """
    def __init__(self, diagram, node, parent=None):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(diagram, node, parent)

        #############################################
        # ORDERING TAB
        #################################

        if self.node.inputs:

            arial12r = Font('Arial', 12)

            self.sortLabel = QLabel(self)
            self.sortLabel.setFont(arial12r)
            self.sortLabel.setText(_('PROPERTY_NODE_LABEL_SORT'))
            self.list = QListWidget(self)
            for i in self.node.inputs:
                edge = self.diagram.edge(i)
                item = QListWidgetItem('{0} ({1})'.format(edge.source.text(), edge.source.id))
                item.setData(Qt.UserRole, edge.id)
                self.list.addItem(item)
            self.list.setCurrentRow(0)
            self.list.setDragDropMode(QAbstractItemView.NoDragDrop)

            self.buttonUp = QPushButton(self)
            self.buttonUp.setIcon(QIcon(':/icons/24/ic_keyboard_arrow_up_black'))
            self.buttonUp.setFixedSize(20, 20)
            connect(self.buttonUp.clicked, self.moveUp)

            self.buttonDown = QPushButton(self)
            self.buttonDown.setIcon(QIcon(':/icons/24/ic_keyboard_arrow_down_black'))
            self.buttonDown.setFixedSize(20, 20)
            connect(self.buttonDown.clicked, self.moveDown)

            inLayout = QVBoxLayout()
            inLayout.addWidget(self.buttonUp)
            inLayout.addWidget(self.buttonDown)

            outLayout = QHBoxLayout()
            outLayout.addWidget(self.list)
            outLayout.addLayout(inLayout)

            self.orderWidget = QWidget()
            self.orderLayout = QFormLayout(self.orderWidget)
            self.orderLayout.addRow(self.sortLabel, outLayout)

            self.mainWidget.addTab(self.orderWidget, _('PROPERTY_NODE_TAB_ORDERING'))

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def moveUp(self):
        """
        Move the currently selected row up.
        """
        i = self.list.currentRow()
        if i > 0:
            item = self.list.takeItem(i)
            self.list.insertItem(i - 1, item)
            self.list.setCurrentRow(i - 1)

    @pyqtSlot()
    def moveDown(self):
        """
        Move the currently selected row down.
        """
        i = self.list.currentRow()
        if i < self.list.count() - 1:
            item = self.list.takeItem(i)
            self.list.insertItem(i + 1, item)
            self.list.setCurrentRow(i + 1)

    @pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged(), self.orderingChanged()]
        if any(commands):
            self.project.undoStack.beginMacro(_('COMMAND_NODE_EDIT_PROPERTIES', self.node.name))
            for command in commands:
                if command:
                    self.project.undoStack.push(command)
            self.project.undoStack.endMacro()
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
                inputs.append(item.data(Qt.UserRole))
            if self.node.inputs != inputs:
                return CommandNodeChangeInputsOrder(self.diagram, self.node, inputs)
        return None


class FacetNodeProperty(NodeProperty):
    """
    This class implements the property dialog for facet nodes.
    """
    def __init__(self, diagram, node, parent=None):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(diagram, node, parent)

        arial12r = Font('Arial', 12)

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

        self.facetLabel = QLabel(self)
        self.facetLabel.setFont(arial12r)
        self.facetLabel.setText(_('PROPERTY_NODE_LABEL_FACET'))
        self.facetField = ComboBox(self)
        self.facetField.setFixedWidth(200)
        self.facetField.setFocusPolicy(Qt.StrongFocus)
        self.facetField.setFont(arial12r)
        for facet in admissible:
            self.facetField.addItem(facet.value, facet)
        facet = self.node.facet
        for i in range(self.facetField.count()):
            if self.facetField.itemData(i) is facet:
                self.facetField.setCurrentIndex(i)
                break
        else:
            self.facetField.setCurrentIndex(0)

        self.valueLabel = QLabel(self)
        self.valueLabel.setFont(arial12r)
        self.valueLabel.setText(_('PROPERTY_NODE_LABEL_VALUE'))
        self.valueField = StringField(self)
        self.valueField.setFixedWidth(200)
        self.valueField.setFont(arial12r)
        self.valueField.setValue(self.node.value)

        self.facetWidget = QWidget()
        self.facetLayout = QFormLayout(self.facetWidget)
        self.facetLayout.addRow(self.facetLabel, self.facetField)
        self.facetLayout.addRow(self.valueLabel, self.valueField)

        self.mainWidget.addTab(self.facetWidget, _('PROPERTY_NODE_TAB_FACET'))

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged(), self.facetChanged()]
        if any(commands):
            self.project.undoStack.beginMacro(_('COMMAND_NODE_EDIT_PROPERTIES', self.node.name))
            for command in commands:
                if command:
                    self.project.undoStack.push(command)
            self.project.undoStack.endMacro()
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
    def __init__(self, diagram, node, parent=None):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(diagram, node, parent)

        arial12r = Font('Arial', 12)

        #############################################
        # DATATYPE TAB
        #################################

        self.datatypeLabel = QLabel(self)
        self.datatypeLabel.setFont(arial12r)
        self.datatypeLabel.setText(_('PROPERTY_NODE_LABEL_DATATYPE'))
        self.datatypeField = ComboBox(self)
        self.datatypeField.setFixedWidth(200)
        self.datatypeField.setFocusPolicy(Qt.StrongFocus)
        self.datatypeField.setFont(arial12r)

        for datatype in Datatype:
            self.datatypeField.addItem(datatype.value, datatype)
        datatype = self.node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break
        else:
            self.datatypeField.setCurrentIndex(0)

        self.datatypeWidget = QWidget()
        self.datatypeLayout = QFormLayout(self.datatypeWidget)
        self.datatypeLayout.addRow(self.datatypeLabel, self.datatypeField)

        self.mainWidget.addTab(self.datatypeWidget, _('PROPERTY_NODE_TAB_DATATYPE'))

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged(), self.datatypeChanged()]
        if any(commands):
            self.project.undoStack.beginMacro(_('COMMAND_NODE_EDIT_PROPERTIES', self.node.name))
            for command in commands:
                if command:
                    self.project.undoStack.push(command)
            self.project.undoStack.endMacro()
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
    def __init__(self, diagram, node, parent=None):
        """
        Initialize the node properties dialog.
        :type diagram: Diagram
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(diagram, node, parent)

        arial12r = Font('Arial', 12)

        #############################################
        # VALUE TAB
        #################################

        self.datatypeLabel = QLabel(self)
        self.datatypeLabel.setFont(arial12r)
        self.datatypeLabel.setText(_('PROPERTY_NODE_LABEL_DATATYPE'))
        self.datatypeField = ComboBox(self)
        self.datatypeField.setFixedWidth(200)
        self.datatypeField.setFocusPolicy(Qt.StrongFocus)
        self.datatypeField.setFont(arial12r)

        for datatype in Datatype:
            self.datatypeField.addItem(datatype.value, datatype)
        datatype = self.node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break
        else:
            self.datatypeField.setCurrentIndex(0)

        self.valueLabel = QLabel(self)
        self.valueLabel.setFont(arial12r)
        self.valueLabel.setText(_('PROPERTY_NODE_LABEL_VALUE'))
        self.valueField = StringField(self)
        self.valueField.setFixedWidth(200)
        self.valueField.setFont(arial12r)
        self.valueField.setValue(self.node.value)

        self.valueWidget = QWidget()
        self.valueLayout = QFormLayout(self.valueWidget)
        self.valueLayout.addRow(self.datatypeLabel, self.datatypeField)
        self.valueLayout.addRow(self.valueLabel, self.valueField)

        self.mainWidget.addTab(self.valueWidget, _('PROPERTY_NODE_TAB_VALUE'))

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged(), self.valueChanged()]
        if any(commands):
            self.project.undoStack.beginMacro(_('COMMAND_NODE_EDIT_PROPERTIES', self.node.name))
            for command in commands:
                if command:
                    self.project.undoStack.push(command)
            self.project.undoStack.endMacro()
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
        data = self.node.composeValue(value, datatype)
        if self.node.text() != data:
            return CommandLabelChange(self.diagram, self.node, self.node.text(), data)
        return None


class PropertyFactory(QObject):
    """
    This class can be used to produce properties dialog windows.
    """
    def __init__(self, parent=None):
        """
        Initialize the factory.
        :type parent: MainWindow
        """
        super().__init__(parent)

    #############################################
    #   PROPERTIES
    #################################
    
    @property
    def project(self):
        """
        Returns the project loaded in the main window.
        :rtype: Project 
        """
        mainwindow = self.parent()
        return mainwindow.project

    #############################################
    #   INTERFACE
    #################################
    
    def create(self, diagram, node=None):
        """
        Build and return a property dialog according to the given parameters.
        :type diagram: Diagram
        :type node: AbstractNode
        :rtype: QDialog
        """
        if not node:
            properties = DiagramProperty(diagram, self.parent())
        else:
            if node.type() is Item.AttributeNode:
                properties = PredicateNodeProperty(diagram, node, self.parent())
            elif node.type() is Item.ConceptNode:
                properties = PredicateNodeProperty(diagram, node, self.parent())
            elif node.type() is Item.RoleNode:
                properties = PredicateNodeProperty(diagram, node, self.parent())
            elif node.type() is Item.ValueDomainNode:
                properties = ValueDomainNodeProperty(diagram, node, self.parent())
            elif node.type() is Item.IndividualNode:
                if node.identity is Identity.Instance:
                    properties = PredicateNodeProperty(diagram, node, self.parent())
                else:
                    properties = ValueNodeProperty(diagram, node, self.parent())
            elif node.type() is Item.PropertyAssertionNode:
                properties = OrderedInputNodeProperty(diagram, node, self.parent())
            elif node.type() is Item.RoleChainNode:
                properties = OrderedInputNodeProperty(diagram, node, self.parent())
            elif node.type() is Item.FacetNode:
                properties = FacetNodeProperty(diagram, node, self.parent())
            else:
                properties = NodeProperty(diagram, node, self.parent())
        properties.setFixedSize(properties.sizeHint())
        return properties