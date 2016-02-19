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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import pyqtSlot, Qt, QEvent
from PyQt5.QtGui import QBrush, QColor, QPainter
from PyQt5.QtWidgets import QWidget, QFormLayout, QLabel, QVBoxLayout, QPushButton, QScrollBar, QStyleOption, QStyle
from PyQt5.QtWidgets import QMenu, QSizePolicy, QScrollArea

from eddy.core.commands import CommandNodeLabelChange, CommandSetProperty
from eddy.core.datatypes import Item, XsdDatatype, Facet, Identity
from eddy.core.functions import disconnect, connect, isEmpty
from eddy.core.qt import ColoredIcon, Font, StackedWidget
from eddy.core.regex import RE_CAMEL_SPACE

from eddy.ui.fields import IntField, StringField, CheckBox, ComboBox


class Info(QScrollArea):
    """
    This class implements the information box.
    """
    Width = 216

    def __init__(self, mainwindow):
        """
        Initialize the info box.
        :type mainwindow: MainWindow
        """
        super().__init__(mainwindow)
        self.scene = None
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(Info.Width)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.stacked = StackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)
        self.infoEmpty = QWidget(self.stacked)
        self.infoDiagram = DiagramInfo(mainwindow, self.stacked)
        self.infoEdge = EdgeInfo(mainwindow, self.stacked)
        self.infoInclusionEdge = InclusionEdgeInfo(mainwindow, self.stacked)
        self.infoNode = NodeInfo(mainwindow, self.stacked)
        self.infoPredicateNode = PredicateNodeInfo(mainwindow, self.stacked)
        self.infoEditableNode = EditableNodeInfo(mainwindow, self.stacked)
        self.infoAttributeNode = AttributeNodeInfo(mainwindow, self.stacked)
        self.infoRoleNode = RoleNodeInfo(mainwindow, self.stacked)
        self.infoValueNode = ValueNodeInfo(mainwindow, self.stacked)
        self.infoValueDomainNode = ValueDomainNodeInfo(mainwindow, self.stacked)
        self.infoValueRestrictionNode = ValueRestrictionNodeInfo(mainwindow, self.stacked)
        self.stacked.addWidget(self.infoEmpty)
        self.stacked.addWidget(self.infoDiagram)
        self.stacked.addWidget(self.infoEdge)
        self.stacked.addWidget(self.infoInclusionEdge)
        self.stacked.addWidget(self.infoNode)
        self.stacked.addWidget(self.infoPredicateNode)
        self.stacked.addWidget(self.infoEditableNode)
        self.stacked.addWidget(self.infoAttributeNode)
        self.stacked.addWidget(self.infoRoleNode)
        self.stacked.addWidget(self.infoValueNode)
        self.stacked.addWidget(self.infoValueDomainNode)
        self.stacked.addWidget(self.infoValueRestrictionNode)
        self.setWidget(self.stacked)
        self.setWidgetResizable(True)
        scrollbar = self.verticalScrollBar()
        scrollbar.installEventFilter(self)
        self.updateLayout()

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def eventFilter(self, source, event):
        """
        Filter incoming events.
        :type source: QObject
        :type event: QEvent
        """
        if isinstance(source, QScrollBar):
            if event.type() == QEvent.Show:
                widget = self.stacked.currentWidget()
                widget.setFixedWidth(Info.Width - source.width())
                self.stacked.setFixedWidth(Info.Width - source.width())
            elif event.type() == QEvent.Hide:
                widget = self.stacked.currentWidget()
                widget.setFixedWidth(Info.Width)
                self.stacked.setFixedWidth(Info.Width)
        return super().eventFilter(source, event)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def updateLayout(self):
        """
        Update widget layout.
        """
        if self.scene:
            selected = self.scene.selectedItems()
            if not selected or len(selected) > 1:
                show = self.infoDiagram
                show.updateData(self.scene)
            else:
                item = selected[0]
                if item.node:
                    if item.predicate:
                        if item.item is Item.ValueDomainNode:
                            show = self.infoValueDomainNode
                            show.updateData(item)
                        elif item.item is Item.ValueRestrictionNode:
                            show = self.infoValueRestrictionNode
                            show.updateData(item)
                        elif item.item is Item.RoleNode:
                            show = self.infoRoleNode
                            show.updateData(item)
                        elif item.item is Item.AttributeNode:
                            show = self.infoAttributeNode
                            show.updateData(item)
                        elif item.item is Item.IndividualNode and item.identity is Identity.Value:
                            show = self.infoValueNode
                            show.updateData(item)
                        elif item.label.editable:
                            show = self.infoEditableNode
                            show.updateData(item)
                        else:
                            show = self.infoPredicateNode
                            show.updateData(item)
                    else:
                        show = self.infoNode
                        show.updateData(item)
                else:
                    if item.item is Item.InclusionEdge:
                        show = self.infoInclusionEdge
                        show.updateData(item)
                    else:
                        show = self.infoEdge
                        show.updateData(item)
        else:
            show = self.infoEmpty

        prev = self.stacked.currentWidget()
        self.stacked.setCurrentWidget(show)
        self.stacked.setFixedSize(show.size())
        if prev is not show:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(0)

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def clear(self):
        """
        Clear the widget from inspecting the current view.
        """
        if self.scene:

            try:
                disconnect(self.scene.index.added, self.updateLayout)
                disconnect(self.scene.index.removed, self.updateLayout)
                disconnect(self.scene.index.cleared, self.updateLayout)
                disconnect(self.scene.selectionChanged, self.updateLayout)
                disconnect(self.scene.updated, self.updateLayout)
            except RuntimeError:
                pass
            finally:
                self.scene = None

        self.updateLayout()

    def setScene(self, scene):
        """
        Set the widget to inspect the given scene.
        :type scene: DiagramScene
        """
        self.clear()
        self.scene = scene

        if self.scene:
            connect(scene.index.added, self.updateLayout)
            connect(scene.index.removed, self.updateLayout)
            connect(scene.index.cleared, self.updateLayout)
            connect(scene.selectionChanged, self.updateLayout)
            connect(scene.updated, self.updateLayout)
            self.updateLayout()


########################################################################################################################
#                                                                                                                      #
#   COMPONENTS                                                                                                         #
#                                                                                                                      #
########################################################################################################################


class Header(QLabel):
    """
    This class implements the header of properties section.
    """
    def __init__(self, *args):
        """
        Initialize the header.
        """
        super().__init__(*args)
        self.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.setFixedHeight(24)


class Key(QLabel):
    """
    This class implements the key of an info field.
    """
    def __init__(self, *args):
        """
        Initialize the key.
        """
        super().__init__(*args)
        self.setFixedSize(84, 20)


class Button(QPushButton):
    """
    This class implements the button to which associate a QMenu instance of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the button.
        """
        super().__init__(*args)
        self.setFont(Font('Arial', 12))


class Int(IntField):
    """
    This class implements the integer value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class Str(StringField):
    """
    This class implements the string value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class Select(ComboBox):
    """
    This class implements the selection box of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFont(Font('Arial', 12))
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setScrollEnabled(False)


class Parent(QWidget):
    """
    This class implements the parent placeholder to be used to store checkbox and radio button value fields.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)


########################################################################################################################
#                                                                                                                      #
#   INFO WIDGETS                                                                                                       #
#                                                                                                                      #
########################################################################################################################


class AbstractInfo(QWidget):
    """
    This class implements the base information box.
    """
    __metaclass__ = ABCMeta

    Height = 20
    LabelWidth = 80

    def __init__(self, mainwindow, parent=None):
        """
        Initialize the base information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setFixedWidth(Info.Width)
        self.mainwindow = mainwindow

    @abstractmethod
    def updateData(self, **kwargs):
        """
        Fetch new information and fill the widget with data.
        """
        pass


class DiagramInfo(AbstractInfo):
    """
    This class implements the diagram scene information box.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the diagram scene information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(mainwindow, parent)

        self.h1 = Header('Diagram', self)

        self.nodesKey = Key('N° nodes', self)
        self.nodesField = Int(self)
        self.nodesField.setReadOnly(True)

        self.edgesKey = Key('N° edges', self)
        self.edgesField = Int(self)
        self.edgesField.setReadOnly(True)

        self.diagramLayout = QFormLayout()
        self.diagramLayout.setSpacing(0)
        self.diagramLayout.addRow(self.nodesKey, self.nodesField)
        self.diagramLayout.addRow(self.edgesKey, self.edgesField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.h1)
        self.mainLayout.addLayout(self.diagramLayout)

    def updateData(self, scene):
        """
        Fetch new information and fill the widget with data.
        :type scene: DiagramScene
        """
        self.nodesField.setValue(scene.index.size(edges=False))
        self.edgesField.setValue(scene.index.size(nodes=False))


class EdgeInfo(AbstractInfo):
    """
    This class implements the information box for generic edges.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the generic edge information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(mainwindow, parent)

        self.h1 = Header('General', self)

        self.typeKey = Key('Type', self)
        self.typeField = Str(self)
        self.typeField.setReadOnly(True)

        self.sourceKey = Key('Source', self)
        self.sourceField = Str(self)
        self.sourceField.setReadOnly(True)

        self.targetKey = Key('Target', self)
        self.targetField = Str(self)
        self.targetField.setReadOnly(True)

        self.generalLayout = QFormLayout()
        self.generalLayout.setSpacing(0)
        self.generalLayout.addRow(self.typeKey, self.typeField)
        self.generalLayout.addRow(self.sourceKey, self.sourceField)
        self.generalLayout.addRow(self.targetKey, self.targetField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.h1)
        self.mainLayout.addLayout(self.generalLayout)

    def updateData(self, edge):
        """
        Fetch new information and fill the widget with data.
        :type edge: AbstractEdge
        """
        self.sourceField.setValue(edge.source.id)
        self.targetField.setValue(edge.target.id)
        self.typeField.setValue(edge.shortname.capitalize())
        self.typeField.home(True)
        self.typeField.deselect()


class InclusionEdgeInfo(EdgeInfo):
    """
    This class implements the information box for inclusion edges.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the inclusion edge information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(mainwindow, parent)

        self.completeKey = Key('Complete', self)
        parent = Parent(self)
        self.completeBox = CheckBox(parent)
        self.completeBox.setCheckable(True)
        connect(self.completeBox.clicked, self.mainwindow.toggleEdgeComplete)

        self.generalLayout.addRow(self.completeKey, parent)

    def updateData(self, edge):
        """
        Fetch new information and fill the widget with data.
        :type edge: AbstractEdge
        """
        super().updateData(edge)
        self.completeBox.setChecked(edge.complete)


class NodeInfo(AbstractInfo):
    """
    This class implements the information box for generic nodes.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the generic node information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(mainwindow, parent)

        self.node = None

        self.h1 = Header('General', self)

        self.idKey = Key('ID', self)
        self.idField = Str(self)
        self.idField.setReadOnly(True)

        self.typeKey = Key('Type', self)
        self.typeField = Str(self)
        self.typeField.setReadOnly(True)

        self.identityKey = Key('Identity', self)
        self.identityField = Str(self)
        self.identityField.setReadOnly(True)

        self.neighboursKey = Key('Neighbours', self)
        self.neighboursField = Int(self)
        self.neighboursField.setReadOnly(True)

        self.generalLayout = QFormLayout()
        self.generalLayout.setSpacing(0)
        self.generalLayout.addRow(self.idKey, self.idField)
        self.generalLayout.addRow(self.typeKey, self.typeField)
        self.generalLayout.addRow(self.identityKey, self.identityField)
        self.generalLayout.addRow(self.neighboursKey, self.neighboursField)

        self.h2 = Header('Geometry', self)

        self.xKey = Key('X', self)
        self.xField = Int(self)
        self.xField.setReadOnly(True)

        self.yKey = Key('Y', self)
        self.yField = Int(self)
        self.yField.setReadOnly(True)

        self.wKey = Key('Width', self)
        self.wField = Int(self)
        self.wField.setReadOnly(True)

        self.hKey = Key('Height', self)
        self.hField = Int(self)
        self.hField.setReadOnly(True)

        self.geometryLayout = QFormLayout()
        self.geometryLayout.setSpacing(0)
        self.geometryLayout.addRow(self.xKey, self.xField)
        self.geometryLayout.addRow(self.yKey, self.yField)
        self.geometryLayout.addRow(self.wKey, self.wField)
        self.geometryLayout.addRow(self.hKey, self.hField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.h1)
        self.mainLayout.addLayout(self.generalLayout)
        self.mainLayout.addWidget(self.h2)
        self.mainLayout.addLayout(self.geometryLayout)

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        pos = node.pos()
        self.xField.setValue(int(pos.x()))
        self.yField.setValue(int(pos.y()))
        self.wField.setValue(int(node.width()))
        self.hField.setValue(int(node.height()))
        self.idField.setValue(node.id)
        self.identityField.setValue(node.identity.label)
        self.neighboursField.setValue(len(node.edges))
        self.typeField.setValue(node.shortname.capitalize())
        self.typeField.home(True)
        self.typeField.deselect()
        self.node = node


class PredicateNodeInfo(NodeInfo):
    """
    This class implements the information box for predicate nodes.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the predicate node information box.
        """
        super().__init__(mainwindow, parent)

        self.h3 = Header('Predicate', self)

        self.brushKey = Key('Color', self)
        self.brushMenu = QMenu(self)
        for action in self.mainwindow.actionsChangeNodeBrush:
            self.brushMenu.addAction(action)
        self.brushButton = Button()
        self.brushButton.setMenu(self.brushMenu)
        self.brushButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.predicateLayout = QFormLayout()
        self.predicateLayout.setSpacing(0)
        self.predicateLayout.addRow(self.brushKey, self.brushButton)

        self.mainLayout.insertWidget(2, self.h3)
        self.mainLayout.insertLayout(3, self.predicateLayout)

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        for action in self.mainwindow.actionsChangeNodeBrush:
            color = action.data()
            brush = QBrush(QColor(color.value))
            if node.brush == brush:
                self.brushButton.setIcon(ColoredIcon(12, 12, color.value, '#000000'))
                self.brushButton.setText(color.value)
                break


class EditableNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the predicate nodes with editable label.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the editable node information box.
        """
        super().__init__(mainwindow, parent)

        self.textKey = Key('Label', self)
        self.textField = Str(self)
        self.textField.setReadOnly(False)
        connect(self.textField.editingFinished, self.editingFinished)

        self.predicateLayout.addRow(self.textKey, self.textField)

    @pyqtSlot()
    def editingFinished(self):
        """
        Executed when the Return or Enter key is pressed or the line edit loses focus.
        """
        if self.node:
            node = self.node
            data = self.textField.value()
            data = data if not isEmpty(data) else node.label.template
            if data != node.text():
                scene = node.scene()
                scene.undostack.push(CommandNodeLabelChange(scene, node, node.text(), data))


    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        self.textField.setValue(node.text())


class AttributeNodeInfo(EditableNodeInfo):
    """
    This class implements the information box for the Attribute node.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Attribute node information box.
        """
        super().__init__(mainwindow, parent)

        self.h4 = Header('Properties', self)

        self.functionalKey = Key('Funct.', self)
        functionalParent = Parent(self)
        self.functionalBox = CheckBox(functionalParent)
        self.functionalBox.setCheckable(True)
        self.functionalBox.setProperty('attribute', 'functional')
        connect(self.functionalBox.clicked, self.propertyChanged)

        self.propertiesLayout = QFormLayout()
        self.propertiesLayout.setSpacing(0)
        self.propertiesLayout.addRow(self.functionalKey, functionalParent)

        self.mainLayout.insertWidget(4, self.h4)
        self.mainLayout.insertLayout(5, self.propertiesLayout)

    @pyqtSlot()
    def propertyChanged(self):
        """
        Executed whenever one of the property fields changes.
        """
        node = self.node
        scene = node.scene()
        sender = self.sender()
        checked = sender.isChecked()
        attribute = sender.property('attribute')
        name = '{}set {} {} property'.format('un' if checked else '', node.shortname, attribute)
        data = {'attribute': attribute, 'undo': getattr(node, attribute), 'redo': checked}
        scene.undostack.push(CommandSetProperty(scene, node, data, name))

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        self.functionalBox.setChecked(node.functional)


class RoleNodeInfo(EditableNodeInfo):
    """
    This class implements the information box for the Role node.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Role node information box.
        """
        super().__init__(mainwindow, parent)

        self.h4 = Header('Properties', self)

        self.functionalKey = Key('Funct.', self)
        functionalParent = Parent(self)
        self.functionalBox = CheckBox(functionalParent)
        self.functionalBox.setCheckable(True)
        self.functionalBox.setProperty('attribute', 'functional')
        connect(self.functionalBox.clicked, self.propertyChanged)

        self.inverseFunctionalKey = Key('Inv. Funct.', self)
        inverseFunctionalParent = Parent(self)
        self.inverseFunctionalBox = CheckBox(inverseFunctionalParent)
        self.inverseFunctionalBox.setCheckable(True)
        self.inverseFunctionalBox.setProperty('attribute', 'inverseFunctional')
        connect(self.inverseFunctionalBox.clicked, self.propertyChanged)

        self.asymmetricKey = Key('Asymmetric', self)
        asymmetricParent = Parent(self)
        self.asymmetricBox = CheckBox(asymmetricParent)
        self.asymmetricBox.setCheckable(True)
        self.asymmetricBox.setProperty('attribute', 'asymmetric')
        connect(self.asymmetricBox.clicked, self.propertyChanged)

        self.irreflexiveKey = Key('Irreflexive', self)
        irreflexiveParent = Parent(self)
        self.irreflexiveBox = CheckBox(irreflexiveParent)
        self.irreflexiveBox.setCheckable(True)
        self.irreflexiveBox.setProperty('attribute', 'irreflexive')
        connect(self.irreflexiveBox.clicked, self.propertyChanged)
        
        self.reflexiveKey = Key('Reflexive', self)
        reflexiveParent = Parent(self)
        self.reflexiveBox = CheckBox(reflexiveParent)
        self.reflexiveBox.setCheckable(True)
        self.reflexiveBox.setProperty('attribute', 'reflexive')
        connect(self.reflexiveBox.clicked, self.propertyChanged)
        
        self.symmetricKey = Key('Symmetric', self)
        symmetricParent = Parent(self)
        self.symmetricBox = CheckBox(symmetricParent)
        self.symmetricBox.setCheckable(True)
        self.symmetricBox.setProperty('attribute', 'symmetric')
        connect(self.symmetricBox.clicked, self.propertyChanged)
        
        self.transitiveKey = Key('Transitive', self)
        transitiveParent = Parent(self)
        self.transitiveBox = CheckBox(transitiveParent)
        self.transitiveBox.setCheckable(True)
        self.transitiveBox.setProperty('attribute', 'transitive')
        connect(self.transitiveBox.clicked, self.propertyChanged)

        self.propertiesLayout = QFormLayout()
        self.propertiesLayout.setSpacing(0)
        self.propertiesLayout.addRow(self.functionalKey, functionalParent)
        self.propertiesLayout.addRow(self.inverseFunctionalKey, inverseFunctionalParent)
        self.propertiesLayout.addRow(self.asymmetricKey, asymmetricParent)
        self.propertiesLayout.addRow(self.irreflexiveKey, irreflexiveParent)
        self.propertiesLayout.addRow(self.reflexiveKey, reflexiveParent)
        self.propertiesLayout.addRow(self.symmetricKey, symmetricParent)
        self.propertiesLayout.addRow(self.transitiveKey, transitiveParent)

        self.mainLayout.insertWidget(4, self.h4)
        self.mainLayout.insertLayout(5, self.propertiesLayout)

    @pyqtSlot()
    def propertyChanged(self):
        """
        Executed whenever one of the property fields changes.
        """
        node = self.node
        scene = node.scene()
        sender = self.sender()
        checked = sender.isChecked()
        attribute = sender.property('attribute')
        prop = RE_CAMEL_SPACE.sub('\g<1> \g<2>', attribute).lower()
        name = '{}set {} {} property'.format('un' if checked else '', node.shortname, prop)
        data = {'attribute': attribute, 'undo': getattr(node, attribute), 'redo': checked}
        scene.undostack.push(CommandSetProperty(scene, node, data, name))

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        self.functionalBox.setChecked(node.functional)
        self.inverseFunctionalBox.setChecked(node.inverseFunctional)
        self.asymmetricBox.setChecked(node.asymmetric)
        self.irreflexiveBox.setChecked(node.irreflexive)
        self.reflexiveBox.setChecked(node.reflexive)
        self.symmetricBox.setChecked(node.symmetric)
        self.transitiveBox.setChecked(node.transitive)


class ValueDomainNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Value Domain node.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Value Domain node information box.
        """
        super().__init__(mainwindow, parent)

        self.datatypeKey = Key('Datatype', self)
        self.datatypeMenu = QMenu(self)
        for action in self.mainwindow.actionsChangeValueDomainDatatype:
            self.datatypeMenu.addAction(action)
        self.datatypeButton = Button()
        self.datatypeButton.setMenu(self.datatypeMenu)
        self.datatypeButton.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.predicateLayout.addRow(self.datatypeKey, self.datatypeButton)

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        datatype = node.datatype
        for action in self.mainwindow.actionsChangeValueDomainDatatype:
            action.setChecked(action.data() is datatype)
        self.datatypeButton.setText(datatype.value)


class ValueRestrictionNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Value Restriction node.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Value Restriction node information box.
        """
        super().__init__(mainwindow, parent)

        self.datatypeKey = Key('Datatype', self)
        self.datatypeField = Select(self)
        connect(self.datatypeField.activated, self.restrictionChanged)

        self.facetKey = Key('Facet', self)
        self.facetField = Select(self)
        connect(self.facetField.activated, self.restrictionChanged)

        self.restrictionKey = Key('Restriction', self)
        self.restrictionField = Str(self)
        self.restrictionField.setReadOnly(False)
        connect(self.restrictionField.editingFinished, self.restrictionChanged)

        for datatype in XsdDatatype:
            if Facet.forDatatype(datatype):
                self.datatypeField.addItem(datatype.value, datatype)

        self.predicateLayout.addRow(self.datatypeKey, self.datatypeField)
        self.predicateLayout.addRow(self.facetKey, self.facetField)
        self.predicateLayout.addRow(self.restrictionKey, self.restrictionField)

    @pyqtSlot()
    def restrictionChanged(self):
        """
        Executed when we need to recompute the restriction of the node.
        """
        if self.node:

            try:

                node = self.node
                scene = node.scene()
                datatype = self.datatypeField.currentData()
                facet = self.facetField.currentData()
                value = self.restrictionField.value()

                allowed = Facet.forDatatype(datatype)
                if facet not in allowed:
                    facet = allowed[0]

                data = node.compose(facet, value, datatype)
                if node.text() != data:
                    name = 'change value restriction to {}'.format(data)
                    scene.undostack.push(CommandNodeLabelChange(scene, node, node.text(), data, name))

            except RuntimeError:
                # We need to catch this exception because sometime when we close the active
                # scene while having a combobox active this slot is triggered but we don't
                # have a scene object anymore, so we'll end up with an exception.
                pass


    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)

        datatype = node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break

        self.datatypeField.setEnabled(not node.constrained)

        self.facetField.clear()
        for facet in Facet.forDatatype(datatype):
            self.facetField.addItem(facet.value, facet)

        facet = node.facet
        for i in range(self.facetField.count()):
            if self.facetField.itemData(i) is facet:
                self.facetField.setCurrentIndex(i)
                break
        else:
            self.facetField.setCurrentIndex(0)

        self.restrictionField.setValue(node.value)


class ValueNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Individual node with identity 'Value'.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the Literal node information box.
        """
        super().__init__(mainwindow, parent)

        self.datatypeKey = Key('Datatype', self)
        self.datatypeField = Select(self)
        connect(self.datatypeField.activated, self.valueChanged)

        self.valueKey = Key('Value', self)
        self.valueField = Str(self)
        self.valueField.setReadOnly(False)
        connect(self.valueField.editingFinished, self.valueChanged)

        for datatype in XsdDatatype:
            if Facet.forDatatype(datatype):
                self.datatypeField.addItem(datatype.value, datatype)

        self.predicateLayout.addRow(self.datatypeKey, self.datatypeField)
        self.predicateLayout.addRow(self.valueKey, self.valueField)

    @pyqtSlot()
    def valueChanged(self):
        """
        Executed when we need to recompute the Literal.
        """
        if self.node:

            try:

                node = self.node
                scene = node.scene()
                datatype = self.datatypeField.currentData()
                value = self.valueField.value()

                data = node.composeValue(value, datatype)
                if node.text() != data:
                    name = 'change individual node to {}'.format(data)
                    scene.undostack.push(CommandNodeLabelChange(scene, node, node.text(), data, name))

            except RuntimeError:
                # We need to catch this exception because sometime when we close the active
                # scene while having a combobox active this slot is triggered but we don't
                # have a scene object anymore, so we'll end up with an exception.
                pass


    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)

        datatype = node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break

        self.valueField.setValue(node.value)