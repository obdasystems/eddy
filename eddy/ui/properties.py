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

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.commands.diagram import CommandDiagramResize
from eddy.core.commands.labels import CommandLabelChange
from eddy.core.commands.nodes import CommandNodeChangeInputsOrder
from eddy.core.commands.nodes import CommandNodeMove
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.owl import Facet, Datatype
from eddy.core.diagram import Diagram
from eddy.core.functions.misc import (
    clamp,
    first,
    isEmpty,
)
from eddy.core.functions.signals import connect
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.ui.fields import (
    CheckBox,
    ComboBox,
    SpinBox,
)
from eddy.ui.fields import (
    IntegerField,
    StringField,
)


class PropertyDialog(QtWidgets.QDialog):
    """
    This is the base class for all the property dialogs.
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
        self.nodesLabel.setText('N° nodes')
        self.nodesField = IntegerField(self)
        self.nodesField.setFixedWidth(300)
        self.nodesField.setReadOnly(True)
        self.nodesField.setValue(len(self.diagram.nodes()))

        self.edgesLabel = QtWidgets.QLabel(self)
        self.edgesLabel.setText('N° edges')
        self.edgesField = IntegerField(self)
        self.edgesField.setFixedWidth(300)
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
        self.diagramSizeLabel.setText('Size')
        self.diagramSizeField = SpinBox(self)
        self.diagramSizeField.setRange(Diagram.MinSize, Diagram.MaxSize)
        self.diagramSizeField.setSingleStep(100)
        self.diagramSizeField.setValue(int(max(sceneRect.width(), sceneRect.height())))

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
        self.idLabel.setText('ID')
        self.idField = StringField(self)
        self.idField.setFixedWidth(300)
        self.idField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.idField.setReadOnly(True)
        self.idField.setValue(self.node.id)

        self.typeLabel = QtWidgets.QLabel(self)
        self.typeLabel.setText('Type')
        self.typeField = StringField(self)
        self.typeField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.typeField.setFixedWidth(300)
        self.typeField.setReadOnly(True)
        self.typeField.setValue(node.shortName.capitalize())

        self.identityLabel = QtWidgets.QLabel(self)
        self.identityLabel.setText('Identity')
        self.identityField = StringField(self)
        self.identityField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.identityField.setFixedWidth(300)
        self.identityField.setReadOnly(True)
        self.identityField.setValue(self.node.identityName)

        self.neighboursLabel = QtWidgets.QLabel(self)
        self.neighboursLabel.setText('Neighbours')
        self.neighboursField = IntegerField(self)
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
        sceneRect = self.diagram.sceneRect().toAlignedRect()

        self.xLabel = QtWidgets.QLabel(self)
        self.xLabel.setText('X')
        self.xField = SpinBox(self)
        self.xField.setFixedWidth(60)
        self.xField.setRange(sceneRect.left(), sceneRect.right())
        self.xField.setValue(int(nodePos.x()))

        self.yLabel = QtWidgets.QLabel(self)
        self.yLabel.setText('Y')
        self.yField = SpinBox(self)
        self.yField.setFixedWidth(60)
        self.yField.setRange(sceneRect.top(), sceneRect.bottom())
        self.yField.setValue(int(nodePos.y()))

        self.widthLabel = QtWidgets.QLabel(self)
        self.widthLabel.setText('Width')
        self.widthField = SpinBox(self)
        self.widthField.setFixedWidth(60)
        self.widthField.setRange(20, sceneRect.width())
        self.widthField.setReadOnly(True)
        self.widthField.setValue(int(self.node.width()))

        self.heightLabel = QtWidgets.QLabel(self)
        self.heightLabel.setText('Height')
        self.heightField = SpinBox(self)
        self.heightField.setFixedWidth(60)
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

        # meta = diagram.project.meta(node.type(), node.text())
        #
        # self.urlLabel = QtWidgets.QLabel(self)
        # self.urlLabel.setText('URL')
        # self.urlField = StringField(self)
        # self.urlField.setFixedWidth(300)
        # self.urlField.setValue(meta.get(K_URL, ''))
        #
        # self.descriptionLabel = QtWidgets.QLabel(self)
        # self.descriptionLabel.setText('Description')
        # self.descriptionField = TextField(self)
        # self.descriptionField.setFixedSize(300, 160)
        # self.descriptionField.setValue(meta.get(K_DESCRIPTION, ''))
        #
        # self.generalLayout.addRow(self.urlLabel, self.urlField)
        # self.generalLayout.addRow(self.descriptionLabel, self.descriptionField)

        #############################################
        # LABEL TAB
        #################################

        self.textLabel = QtWidgets.QLabel(self)
        self.textLabel.setText('Text')
        self.textField = StringField(self)
        self.textField.setFixedWidth(300)
        self.textField.setValue(self.node.text())

        self.refactorLabel = QtWidgets.QLabel(self)
        self.refactorLabel.setText('Refactor')
        self.refactorField = CheckBox(self)
        self.refactorField.setChecked(False)

        if node.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode}:
            if node.special() is not None:
                self.refactorField.setEnabled(False)

        self.labelWidget = QtWidgets.QWidget()
        self.labelLayout = QtWidgets.QFormLayout(self.labelWidget)
        self.labelLayout.addRow(self.textLabel, self.textField)
        self.labelLayout.addRow(self.refactorLabel, self.refactorField)

        self.mainWidget.addTab(self.labelWidget, 'Label')

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def complete(self):
        """
        Executed when the dialog is accepted.
        """
        commands = [self.positionChanged(), self.metaDataChanged()]
        commands.extend(self.textChanged())
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

    def metaDataChanged(self):
        """
        Change the url and description of the node.
        :rtype: QUndoCommand
        """
        # undo = self.diagram.project.meta(self.node.type(), self.node.text())
        # redo = undo.copy()
        # redo[K_DESCRIPTION] = self.descriptionField.value()
        # redo[K_URL] = self.urlField.value()
        # if redo != undo:
        #     return CommandNodeSetMeta(
        #         self.diagram.project,
        #         self.node.type(),
        #         self.node.text(),
        #         undo, redo)
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
        self.facetLabel.setText('Facet')
        self.facetField = ComboBox(self)
        self.facetField.setFixedWidth(200)
        self.facetField.setFocusPolicy(QtCore.Qt.StrongFocus)
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
        self.valueLabel.setText('Value')
        self.valueField = StringField(self)
        self.valueField.setFixedWidth(200)
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
        self.datatypeLabel.setText('Datatype')
        self.datatypeField = ComboBox(self)
        self.datatypeField.setFixedWidth(200)
        self.datatypeField.setFocusPolicy(QtCore.Qt.StrongFocus)

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

        #############################################
        # VALUE TAB
        #################################

        self.datatypeLabel = QtWidgets.QLabel(self)
        self.datatypeLabel.setText('Datatype')
        self.datatypeField = ComboBox(self)
        self.datatypeField.setFixedWidth(200)
        self.datatypeField.setFocusPolicy(QtCore.Qt.StrongFocus)

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
        self.valueLabel.setText('Value')
        self.valueField = StringField(self)
        self.valueField.setFixedWidth(200)
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
        commands = [self.positionChanged(), self.valueChanged()]
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
            return CommandLabelChange(self.diagram, self.node, self.node.text(), data)
        return None
