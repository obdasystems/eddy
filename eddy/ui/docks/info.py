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

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QWidget, QFormLayout, QLabel, QVBoxLayout
from PyQt5.QtWidgets import QMenu, QToolButton, QSizePolicy, QScrollArea, QStackedWidget

from eddy.core.datatypes import Item
from eddy.core.functions import disconnect, connect, coloredIcon
from eddy.core.qt import Font
from eddy.ui.fields import IntField, DoubleField, StringField, CheckBox


class Info(QScrollArea):
    """
    This class implements the information box.
    """
    def __init__(self, mainwindow):
        """
        Initialize the info box.
        :type mainwindow: MainWindow
        """
        super().__init__(mainwindow)
        self.scene = None
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.stacked = QStackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)
        self.infoEmpty = QWidget(self.stacked)
        self.infoDiagram = DiagramInfo(mainwindow, self.stacked)
        self.infoEdge = EdgeInfo(mainwindow, self.stacked)
        self.infoInclusionEdge = InclusionEdgeInfo(mainwindow, self.stacked)
        self.infoNode = NodeInfo(mainwindow, self.stacked)
        self.infoPredicateNode = PredicateNodeInfo(mainwindow, self.stacked)
        self.stacked.addWidget(self.infoEmpty)
        self.stacked.addWidget(self.infoDiagram)
        self.stacked.addWidget(self.infoEdge)
        self.stacked.addWidget(self.infoInclusionEdge)
        self.stacked.addWidget(self.infoNode)
        self.stacked.addWidget(self.infoPredicateNode)
        self.setWidget(self.stacked)
        self.setWidgetResizable(True)
        self.updateLayout()

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

        self.stacked.setCurrentWidget(show)
        self.stacked.setFixedHeight(show.height())
        self.verticalScrollBar().setValue(0)

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
#   INFO WIDGETS                                                                                                       #
#                                                                                                                      #
########################################################################################################################


class AbstractInfo(QWidget):
    """
    This class implements the base information box.
    """
    __metaclass__ = ABCMeta

    LabelWidth = 80

    def __init__(self, mainwindow, parent=None):
        """
        Initialize the base information box.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(parent)
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

        self.h1 = QLabel('DIAGRAM', self)
        self.h1.setAlignment(Qt.AlignCenter)
        self.h1.setFixedHeight(24)
        self.h1.setObjectName('heading')

        self.nodesLabel = QLabel('N° nodes', self)
        self.nodesLabel.setObjectName('index')
        self.nodesLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.nodesField = IntField(self)
        self.nodesField.setReadOnly(True)

        self.edgesLabel = QLabel('N° edges', self)
        self.edgesLabel.setObjectName('index')
        self.edgesLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.edgesField = IntField(self)
        self.edgesField.setReadOnly(True)

        self.diagramLayout = QFormLayout()
        self.diagramLayout.setSpacing(0)
        self.diagramLayout.addRow(self.nodesLabel, self.nodesField)
        self.diagramLayout.addRow(self.edgesLabel, self.edgesField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
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

        self.h1 = QLabel('GENERAL', self)
        self.h1.setAlignment(Qt.AlignCenter)
        self.h1.setFixedHeight(24)
        self.h1.setObjectName('heading')

        self.typeLabel = QLabel('Type', self)
        self.typeLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.typeLabel.setObjectName('index')
        self.typeField = StringField(self)
        self.typeField.setReadOnly(True)

        self.sourceLabel = QLabel('Source', self)
        self.sourceLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.sourceLabel.setObjectName('index')
        self.sourceField = StringField(self)
        self.sourceField.setReadOnly(True)

        self.targetLabel = QLabel('Target', self)
        self.targetLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.targetLabel.setObjectName('index')
        self.targetField = StringField(self)
        self.targetField.setReadOnly(True)

        self.generalLayout = QFormLayout()
        self.generalLayout.setSpacing(0)
        self.generalLayout.addRow(self.typeLabel, self.typeField)
        self.generalLayout.addRow(self.sourceLabel, self.sourceField)
        self.generalLayout.addRow(self.targetLabel, self.targetField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
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

        self.completeLabel = QLabel('Complete', self)
        self.completeLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.completeLabel.setObjectName('index')

        self.completeBox = CheckBox(self)
        self.completeBox.setCheckable(True)
        connect(self.completeBox.clicked, self.mainwindow.toggleEdgeComplete)

        self.generalLayout.addRow(self.completeLabel, self.completeBox)

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

        self.h1 = QLabel('GENERAL', self)
        self.h1.setAlignment(Qt.AlignCenter)
        self.h1.setFixedHeight(24)
        self.h1.setObjectName('heading')

        self.idLabel = QLabel('ID', self)
        self.idLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.idLabel.setObjectName('index')
        self.idField = StringField(self)
        self.idField.setReadOnly(True)

        self.typeLabel = QLabel('Type', self)
        self.typeLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.typeLabel.setObjectName('index')
        self.typeField = StringField(self)
        self.typeField.setReadOnly(True)

        self.identityLabel = QLabel('Identity', self)
        self.identityLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.identityLabel.setObjectName('index')
        self.identityField = StringField(self)
        self.identityField.setReadOnly(True)

        self.neighboursLabel = QLabel('Neighbours', self)
        self.neighboursLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.neighboursLabel.setObjectName('index')
        self.neighboursField = IntField(self)
        self.neighboursField.setReadOnly(True)

        self.generalLayout = QFormLayout()
        self.generalLayout.setSpacing(0)
        self.generalLayout.addRow(self.idLabel, self.idField)
        self.generalLayout.addRow(self.typeLabel, self.typeField)
        self.generalLayout.addRow(self.identityLabel, self.identityField)
        self.generalLayout.addRow(self.neighboursLabel, self.neighboursField)

        self.h2 = QLabel('GEOMETRY', self)
        self.h2.setAlignment(Qt.AlignCenter)
        self.h2.setFixedHeight(24)
        self.h2.setObjectName('heading')

        self.xLabel = QLabel('X', self)
        self.xLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.xLabel.setObjectName('index')
        self.xField = DoubleField(self)
        self.xField.setReadOnly(True)

        self.yLabel = QLabel('Y', self)
        self.yLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.yLabel.setObjectName('index')
        self.yField = DoubleField(self)
        self.yField.setReadOnly(True)

        self.wLabel = QLabel('Width', self)
        self.wLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.wLabel.setObjectName('index')
        self.wField = IntField(self)
        self.wField.setReadOnly(True)

        self.hLabel = QLabel('Height', self)
        self.hLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.hLabel.setObjectName('index')
        self.hField = IntField(self)
        self.hField.setReadOnly(True)

        self.geometryLayout = QFormLayout()
        self.geometryLayout.setSpacing(0)
        self.geometryLayout.addRow(self.xLabel, self.xField)
        self.geometryLayout.addRow(self.yLabel, self.yField)
        self.geometryLayout.addRow(self.wLabel, self.wField)
        self.geometryLayout.addRow(self.hLabel, self.hField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
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
        self.xField.setValue(pos.x())
        self.yField.setValue(pos.y())
        self.wField.setValue(int(node.width()))
        self.hField.setValue(int(node.height()))
        self.idField.setValue(node.id)
        self.identityField.setValue(node.identity.label)
        self.neighboursField.setValue(len(node.edges))
        self.typeField.setValue(node.shortname.capitalize())
        self.typeField.home(True)
        self.typeField.deselect()


class PredicateNodeInfo(NodeInfo):
    """
    This class implements the information box for predicate nodes.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the predicate node information box.
        """
        super().__init__(mainwindow, parent)

        self.h3 = QLabel('PREDICATE', self)
        self.h3.setAlignment(Qt.AlignCenter)
        self.h3.setFixedHeight(24)
        self.h3.setObjectName('heading')

        self.brushLabel = QLabel('Color', self)
        self.brushLabel.setFixedWidth(AbstractInfo.LabelWidth)
        self.brushLabel.setObjectName('index')

        self.brushMenu = QMenu(self)
        for action in self.mainwindow.actionsChangeNodeBrush:
            self.brushMenu.addAction(action)

        self.brushButton = QToolButton()
        self.brushButton.setFont(Font('Arial', 12))
        self.brushButton.setMenu(self.brushMenu)
        self.brushButton.setPopupMode(QToolButton.InstantPopup)
        self.brushButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.brushButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.predicateLayout = QFormLayout()
        self.predicateLayout.setSpacing(0)
        self.predicateLayout.addRow(self.brushLabel, self.brushButton)

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
                self.brushButton.setIcon(coloredIcon(12, 12, color.value, '#000000'))
                self.brushButton.setText(color.value)
                break