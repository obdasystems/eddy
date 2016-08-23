# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


from PyQt5.QtCore import Qt, QEvent, QSize, pyqtSlot
from PyQt5.QtGui import QIcon, QPainter, QBrush, QColor
from PyQt5.QtWidgets import QScrollArea, QStackedWidget, QWidget
from PyQt5.QtWidgets import QStyleOption, QPushButton, QLabel
from PyQt5.QtWidgets import QFormLayout, QVBoxLayout, QMenu
from PyQt5.QtWidgets import QMdiSubWindow, QSizePolicy, QStyle

from abc import ABCMeta, abstractmethod
from verlib import NormalizedVersion

from eddy.core.commands.common import CommandSetProperty
from eddy.core.commands.labels import CommandLabelChange
from eddy.core.commands.project import CommandProjectSetIRI
from eddy.core.commands.project import CommandProjectSetPrefix
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.owl import Facet, Datatype
from eddy.core.datatypes.qt import BrushIcon, Font
from eddy.core.functions.misc import first, clamp, isEmpty
from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin
from eddy.core.project import Project
from eddy.core.regex import RE_CAMEL_SPACE

from eddy.ui.dock import DockWidget
from eddy.ui.fields import IntegerField, StringField
from eddy.ui.fields import CheckBox, ComboBox


class Info(AbstractPlugin):
    """
    This plugin provides the Info widget.
    """
    def __init__(self, session):
        """
        Initialize the plugin.
        :type session: session
        """
        super().__init__(session)

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :type source: QObject
        :type event: QEvent
        :rtype: bool
        """
        if event.type() == QEvent.Resize:
            widget = source.widget()
            widget.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def onDiagramItemAdded(self):
        """
        Executed whenever a new element is added to the active diagram.
        """
        self.widget('info').stack()

    @pyqtSlot()
    def onDiagramItemRemoved(self):
        """
        Executed whenever a new element is removed from the active diagram.
        """
        self.widget('info').stack()

    @pyqtSlot()
    def onDiagramSelectionChanged(self):
        """
        Executed whenever the selection of the active diagram changes.
        """
        self.widget('info').stack()

    @pyqtSlot()
    def onDiagramUpdated(self):
        """
        Executed whenever the active diagram is updated.
        """
        self.widget('info').stack()

    @pyqtSlot()
    def onProjectUpdated(self):
        """
        Executed whenever the current project is updated.
        """
        self.widget('info').stack()

    @pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnUpdated, self.onProjectUpdated)

    @pyqtSlot(QMdiSubWindow)
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        if subwindow:
            # If we have an active subwindow, we change the info
            # widget to browse the diagram within such subwindow.
            widget = self.widget('info')
            if widget.diagram:
                # If the info widget is currently inspecting a
                # diagram, detach signals from the subwindow which
                # is going out of focus, before connecting new ones.
                self.debug('Disconnecting from diagram: %s', widget.diagram.name)
                disconnect(widget.diagram.selectionChanged, self.onDiagramSelectionChanged)
                disconnect(widget.diagram.sgnItemAdded, self.onDiagramItemAdded)
                disconnect(widget.diagram.sgnItemRemoved, self.onDiagramItemRemoved)
                disconnect(widget.diagram.sgnUpdated, self.onDiagramUpdated)
            # Attach the new view/diagram to the info widget.
            self.debug('Connecting to diagram: %s', subwindow.diagram.name)
            connect(subwindow.diagram.selectionChanged, self.onDiagramSelectionChanged)
            connect(subwindow.diagram.sgnItemAdded, self.onDiagramItemAdded)
            connect(subwindow.diagram.sgnItemRemoved, self.onDiagramItemRemoved)
            connect(subwindow.diagram.sgnUpdated, self.onDiagramUpdated)
            widget.setDiagram(subwindow.diagram)
            widget.stack()
        else:
            if not self.session.mdi.subWindowList():
                # If we don't have any active subwindow (which means that
                # they have been all closed and not just out of focus) we
                # detach the widget from the last inspected diagram.
                widget = self.widget('info')
                if widget.diagram:
                    self.debug('Disconnecting from diagram: %s', widget.diagram.name)
                    disconnect(widget.diagram.selectionChanged, self.onDiagramSelectionChanged)
                    disconnect(widget.diagram.sgnItemAdded, self.onDiagramItemAdded)
                    disconnect(widget.diagram.sgnItemRemoved, self.onDiagramItemRemoved)
                    disconnect(widget.diagram.sgnUpdated, self.onDiagramUpdated)
                widget.setDiagram(None)
                widget.stack()

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def name(cls):
        """
        Returns the readable name of the plugin.
        :rtype: str
        """
        return 'Info'

    def objectName(self):
        """
        Returns the system name of the plugin.
        :rtype: str
        """
        return 'info'

    def startup(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Creating info widget')
        widget = InfoWidget(self)
        widget.setObjectName('info')
        self.addWidget(widget)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Info', QIcon(':/icons/18/ic_info_outline_black'), self.session)
        widget.installEventFilter(self)
        widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        widget.setObjectName('info_dock')
        widget.setWidget(self.widget('info'))
        self.addWidget(widget)

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('info_dock').toggleViewAction())

        # CONFIGURE SIGNAL/SLOTS
        self.debug('Configuring session and MDI area specific signals')
        connect(self.session.sgnReady, self.onSessionReady)
        connect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(Qt.RightDockWidgetArea, self.widget('info_dock'))

        super().startup()

    @classmethod
    def version(cls):
        """
        Returns the version of the plugin.
        :rtype: NormalizedVersion
        """
        return NormalizedVersion('0.1')


class InfoWidget(QScrollArea):
    """
    This class implements the information box widget.
    """
    def __init__(self, plugin):
        """
        Initialize the info box.
        :type plugin: Info
        """
        super().__init__(plugin.session)

        self.diagram = None
        self.plugin = plugin

        self.stacked = QStackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)
        self.infoEmpty = QWidget(self.stacked)
        self.infoProject = ProjectInfo(self.session, self.stacked)
        self.infoEdge = EdgeInfo(self.session, self.stacked)
        self.infoInclusionEdge = InclusionEdgeInfo(self.session, self.stacked)
        self.infoNode = NodeInfo(self.session, self.stacked)
        self.infoPredicateNode = PredicateNodeInfo(self.session, self.stacked)
        self.infoAttributeNode = AttributeNodeInfo(self.session, self.stacked)
        self.infoRoleNode = RoleNodeInfo(self.session, self.stacked)
        self.infoValueNode = ValueNodeInfo(self.session, self.stacked)
        self.infoValueDomainNode = ValueDomainNodeInfo(self.session, self.stacked)
        self.infoFacet = FacetNodeInfo(self.session, self.stacked)
        self.stacked.addWidget(self.infoEmpty)
        self.stacked.addWidget(self.infoProject)
        self.stacked.addWidget(self.infoEdge)
        self.stacked.addWidget(self.infoInclusionEdge)
        self.stacked.addWidget(self.infoNode)
        self.stacked.addWidget(self.infoPredicateNode)
        self.stacked.addWidget(self.infoAttributeNode)
        self.stacked.addWidget(self.infoRoleNode)
        self.stacked.addWidget(self.infoValueNode)
        self.stacked.addWidget(self.infoValueDomainNode)
        self.stacked.addWidget(self.infoFacet)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QSize(216, 120))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidget(self.stacked)
        self.setWidgetResizable(True)

        self.setStyleSheet("""
        InfoWidget {
        background: #FFFFFF;
        }
        InfoWidget Header {
        background: #5A5050;
        padding-left: 4px;
        color: #FFFFFF;
        }
        InfoWidget Key {
        background: #BBDEFB;
        border-bottom: 1px solid #BABABA;
        padding-left: 4px;
        }
        InfoWidget Button,
        InfoWidget Integer,
        InfoWidget String,
        InfoWidget Select,
        InfoWidget Parent {
        background: #E3F2FD;
        border-bottom: 1px solid #BABABA;
        border-left: 1px solid #BABABA;
        padding-left: 4px;
        }
        InfoWidget Button {
        text-align:left;
        }
        InfoWidget Button::menu-indicator {
        image: none;
        }
        InfoWidget Select:!editable,
        InfoWidget Select::drop-down:editable {
        background: #FFFFFF;
        }
        InfoWidget Select:!editable:on,
        InfoWidget Select::drop-down:editable:on {
        background: #FFFFFF;
        }
        InfoWidget QCheckBox {
        background: #FFFFFF;
        spacing: 0;
        margin-left: 4px;
        margin-top: 2px;
        }""")

        scrollbar = self.verticalScrollBar()
        scrollbar.installEventFilter(self)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the reference to the active project.
        :rtype: Session
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the active session.
        :rtype: Session
        """
        return self.plugin.parent()

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filter incoming events.
        :type source: QObject
        :type event: QEvent
        """
        if source is self.verticalScrollBar():
            if event.type() in {QEvent.Show, QEvent.Hide}:
                self.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   INTERFACE
    #################################

    def redraw(self):
        """
        Redraw the content of the widget.
        """
        width = self.width()
        scrollbar = self.verticalScrollBar()
        if scrollbar.isVisible():
            width -= scrollbar.width()
        widget = self.stacked.currentWidget()
        widget.setFixedWidth(width)
        sizeHint = widget.sizeHint()
        height = sizeHint.height()
        self.stacked.setFixedWidth(width)
        self.stacked.setFixedHeight(clamp(height, 0))

    def setDiagram(self, diagram):
        """
        Sets the widget to inspect the given diagram.
        :type diagram: diagram
        """
        self.diagram = diagram

    def stack(self):
        """
        Set the current stacked widget.
        """
        if self.diagram:
            selected = self.diagram.selectedItems()
            if not selected or len(selected) > 1:
                show = self.infoProject
                show.updateData(self.project)
            else:
                item = first(selected)
                if item.isNode():
                    if item.isPredicate():
                        if item.type() is Item.ValueDomainNode:
                            show = self.infoValueDomainNode
                        elif item.type() is Item.RoleNode:
                            show = self.infoRoleNode
                        elif item.type() is Item.AttributeNode:
                            show = self.infoAttributeNode
                        elif item.type() is Item.IndividualNode and item.identity is Identity.Value:
                            show = self.infoValueNode
                        else:
                            show = self.infoPredicateNode
                    else:
                        if item.type() is Item.FacetNode:
                            show = self.infoFacet
                        else:
                            show = self.infoNode
                else:
                    if item.type() is Item.InclusionEdge:
                        show = self.infoInclusionEdge
                    else:
                        show = self.infoEdge
                show.updateData(item)
        elif self.project:
            show = self.infoProject
            show.updateData(self.project)
        else:
            show = self.infoEmpty

        prev = self.stacked.currentWidget()
        self.stacked.setCurrentWidget(show)
        self.redraw()
        if prev is not show:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(0)


#############################################
#   COMPONENTS
#################################


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
        self.setFixedSize(88, 20)


class Button(QPushButton):
    """
    This class implements the button to which associate a QMenu instance of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the button.
        """
        super().__init__(*args)


class Integer(IntegerField):
    """
    This class implements the integer value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class String(StringField):
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


#############################################
#   INFO WIDGETS
#################################


class AbstractInfo(QWidget):
    """
    This class implements the base information box.
    """
    __metaclass__ = ABCMeta

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(parent)
        self.session = session
        self.setContentsMargins(0, 0, 0, 0)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the project loaded in the current session.
        :rtype: Project
        """
        return self.session.project

    #############################################
    #   INTERFACE
    #################################

    @abstractmethod
    def updateData(self, **kwargs):
        """
        Fetch new information and fill the widget with data.
        """
        pass


class ProjectInfo(AbstractInfo):
    """
    This class implements the project information box.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the project information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.prefixKey = Key('Prefix', self)
        self.prefixKey.setFont(arial12r)
        self.prefixField = String(self)
        self.prefixField.setFont(arial12r)
        self.prefixField.setReadOnly(False)
        connect(self.prefixField.editingFinished, self.prefixEditingFinished)

        self.iriKey = Key('IRI', self)
        self.iriKey.setFont(arial12r)
        self.iriField = String(self)
        self.iriField.setFont(arial12r)
        self.iriField.setReadOnly(False)
        connect(self.iriField.editingFinished, self.iriEditingFinished)

        self.ontologyPropHeader = Header('Ontology properties', self)
        self.ontologyPropHeader.setFont(arial12r)

        self.ontologyPropLayout = QFormLayout()
        self.ontologyPropLayout.setSpacing(0)
        self.ontologyPropLayout.addRow(self.prefixKey, self.prefixField)
        self.ontologyPropLayout.addRow(self.iriKey, self.iriField)

        self.conceptsKey = Key('Concept', self)
        self.conceptsKey.setFont(arial12r)
        self.conceptsField = Integer(self)
        self.conceptsField.setFont(arial12r)
        self.conceptsField.setReadOnly(True)

        self.rolesKey = Key('Role', self)
        self.rolesKey.setFont(arial12r)
        self.rolesField = Integer(self)
        self.rolesField.setFont(arial12r)
        self.rolesField.setReadOnly(True)

        self.attributesKey = Key('Attribute', self)
        self.attributesKey.setFont(arial12r)
        self.attributesField = Integer(self)
        self.attributesField.setFont(arial12r)
        self.attributesField.setReadOnly(True)

        self.inclusionsKey = Key('Inclusion', self)
        self.inclusionsKey.setFont(arial12r)
        self.inclusionsField = Integer(self)
        self.inclusionsField.setFont(arial12r)
        self.inclusionsField.setReadOnly(True)

        self.membershipKey = Key('Membership', self)
        self.membershipKey.setFont(arial12r)
        self.membershipField = Integer(self)
        self.membershipField.setFont(arial12r)
        self.membershipField.setReadOnly(True)

        self.atomicPredHeader = Header('Atomic predicates', self)
        self.atomicPredHeader.setFont(arial12r)

        self.atomicPredLayout = QFormLayout()
        self.atomicPredLayout.setSpacing(0)
        self.atomicPredLayout.addRow(self.conceptsKey, self.conceptsField)
        self.atomicPredLayout.addRow(self.rolesKey, self.rolesField)
        self.atomicPredLayout.addRow(self.attributesKey, self.attributesField)

        self.assertionsHeader = Header('Assertions', self)
        self.assertionsHeader.setFont(arial12r)

        self.assertionsLayout = QFormLayout()
        self.assertionsLayout.setSpacing(0)
        self.assertionsLayout.addRow(self.inclusionsKey, self.inclusionsField)
        self.assertionsLayout.addRow(self.membershipKey, self.membershipField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.ontologyPropHeader)
        self.mainLayout.addLayout(self.ontologyPropLayout)
        self.mainLayout.addWidget(self.atomicPredHeader)
        self.mainLayout.addLayout(self.atomicPredLayout)
        self.mainLayout.addWidget(self.assertionsHeader)
        self.mainLayout.addLayout(self.assertionsLayout)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def iriEditingFinished(self):
        """
        Executed whenever we finish to edit the ontology prefix
        """
        project = self.project
        iri = self.iriField.value()
        if project.iri != iri:
            self.session.undostack.push(CommandProjectSetIRI(project, project.iri, iri))
        self.iriField.clearFocus()

    @pyqtSlot()
    def prefixEditingFinished(self):
        """
        Executed whenever we finish to edit the ontology prefix
        """
        project = self.project
        prefix = self.prefixField.value()
        if project.prefix != prefix:
            self.session.undostack.push(CommandProjectSetPrefix(project, project.prefix, prefix))
        self.prefixField.clearFocus()

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, project):
        """
        Fetch new information and fill the widget with data.
        :type project: Project
        """
        self.prefixField.setValue(project.prefix)
        self.prefixField.home(True)
        self.prefixField.clearFocus()
        self.prefixField.deselect()
        self.iriField.setValue(project.iri)
        self.iriField.home(True)
        self.iriField.clearFocus()
        self.iriField.deselect()
        self.attributesField.setValue(project.count(predicate=Item.AttributeNode))
        self.conceptsField.setValue(project.count(predicate=Item.ConceptNode))
        self.rolesField.setValue(project.count(predicate=Item.RoleNode))
        self.inclusionsField.setValue(project.count(item=Item.InclusionEdge))
        self.membershipField.setValue(project.count(item=Item.MembershipEdge))


class EdgeInfo(AbstractInfo):
    """
    This class implements the information box for generic edges.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the generic edge information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.h1 = Header('General', self)
        self.h1.setFont(arial12r)

        self.typeKey = Key('Type', self)
        self.typeKey.setFont(arial12r)
        self.typeField = String(self)
        self.typeField.setFont(arial12r)
        self.typeField.setReadOnly(True)

        self.sourceKey = Key('Source', self)
        self.sourceKey.setFont(arial12r)
        self.sourceField = String(self)
        self.sourceField.setFont(arial12r)
        self.sourceField.setReadOnly(True)

        self.targetKey = Key('Target', self)
        self.targetKey.setFont(arial12r)
        self.targetField = String(self)
        self.targetField.setFont(arial12r)
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

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, edge):
        """
        Fetch new information and fill the widget with data.
        :type edge: AbstractEdge
        """
        self.sourceField.setValue(edge.source.id)
        self.targetField.setValue(edge.target.id)
        self.typeField.setValue(edge.shortName.capitalize())
        self.typeField.home(True)
        self.typeField.deselect()


class InclusionEdgeInfo(EdgeInfo):
    """
    This class implements the information box for inclusion edges.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the inclusion edge information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.equivalenceKey = Key('Equivalence', self)
        self.equivalenceKey.setFont(arial12r)
        parent = Parent(self)
        self.equivalenceBox = CheckBox(parent)
        self.equivalenceBox.setFont(arial12r)
        self.equivalenceBox.setCheckable(True)
        connect(self.equivalenceBox.clicked, self.session.doToggleEdgeEquivalence)

        self.generalLayout.addRow(self.equivalenceKey, parent)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, edge):
        """
        Fetch new information and fill the widget with data.
        :type edge: InclusionEdge
        """
        super().updateData(edge)
        self.equivalenceBox.setChecked(edge.equivalence)


class NodeInfo(AbstractInfo):
    """
    This class implements the information box for generic nodes.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the generic node information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.node = None

        self.idKey = Key('ID', self)
        self.idKey.setFont(arial12r)
        self.idField = String(self)
        self.idField.setFont(arial12r)
        self.idField.setReadOnly(True)

        self.identityKey = Key('Identity', self)
        self.identityKey.setFont(arial12r)
        self.identityField = String(self)
        self.identityField.setFont(arial12r)
        self.identityField.setReadOnly(True)

        self.nodePropHeader = Header('Node properties', self)
        self.nodePropHeader.setFont(arial12r)
        self.nodePropLayout = QFormLayout()
        self.nodePropLayout.setSpacing(0)
        self.nodePropLayout.addRow(self.idKey, self.idField)
        self.nodePropLayout.addRow(self.identityKey, self.identityField)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.nodePropHeader)
        self.mainLayout.addLayout(self.nodePropLayout)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        self.idField.setValue(node.id)
        self.identityField.setValue(node.identity.value)
        self.node = node


class PredicateNodeInfo(NodeInfo):
    """
    This class implements the information box for predicate nodes.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the predicate node information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.textKey = Key('Label', self)
        self.textKey.setFont(arial12r)
        self.textField = String(self)
        self.textField.setFont(arial12r)
        self.textField.setReadOnly(False)
        connect(self.textField.editingFinished, self.editingFinished)

        self.brushKey = Key('Color', self)
        self.brushKey.setFont(arial12r)
        self.brushMenu = QMenu(self)
        self.brushButton = Button()
        self.brushButton.setFont(arial12r)
        self.brushButton.setMenu(self.brushMenu)
        self.brushButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.nodePropLayout.addRow(self.brushKey, self.brushButton)
        self.nodePropLayout.addRow(self.textKey, self.textField)

        self.nameKey = Key('Name', self)
        self.nameKey.setFont(arial12r)
        self.nameField = String(self)
        self.nameField.setFont(arial12r)
        self.nameField.setReadOnly(False)
        connect(self.nameField.editingFinished, self.editingFinished)

        self.predPropHeader = Header('Predicate properties', self)
        self.predPropHeader.setFont(arial12r)
        self.predPropLayout = QFormLayout()
        self.predPropLayout.setSpacing(0)
        self.predPropLayout.addRow(self.nameKey, self.nameField)

        self.mainLayout.insertWidget(0, self.predPropHeader)
        self.mainLayout.insertLayout(1, self.predPropLayout)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def editingFinished(self):
        """
        Executed whenever we finish to edit the predicate/node name.
        """
        if self.node:

            try:
                sender = self.sender()
                node = self.node
                data = sender.value()
                data = data if not isEmpty(data) else node.label.template
                if data != node.text():
                    diagram = node.diagram
                    project = node.project
                    if sender is self.nameField:
                        self.session.undostack.beginMacro('change predicate "{0}" to "{1}"'.format(node.text(), data))
                        for n in project.predicates(node.type(), node.text()):
                            self.session.undostack.push(CommandLabelChange(n.diagram, n, n.text(), data))
                        self.session.undostack.endMacro()
                    else:
                        self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data))
            except RuntimeError:
                pass

        self.nameField.clearFocus()
        self.textField.clearFocus()

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)

        #############################################
        # BRUSH FIELD
        #################################

        if self.brushMenu.isEmpty():
            self.brushMenu.addActions(self.session.action('brush').actions())
        for action in self.session.action('brush').actions():
            color = action.data()
            brush = QBrush(QColor(color.value))
            if node.brush() == brush:
                self.brushButton.setIcon(BrushIcon(12, 12, color.value, '#000000'))
                self.brushButton.setText(color.value)
                break

        #############################################
        # NAME / TEXT FIELDS
        #################################

        self.nameField.setValue(node.text())
        self.textField.setValue(node.text())

        #############################################
        # ENABLE / DISABLE REFACTORING
        #################################

        refactor = True
        if node.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode}:
            if node.special is not None:
                refactor = False
        self.nameField.setReadOnly(not refactor)


class AttributeNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Attribute node.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the Attribute node information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.functKey = Key('Funct.', self)
        self.functKey.setFont(arial12r)
        functParent = Parent(self)
        self.functBox = CheckBox(functParent)
        self.functBox.setCheckable(True)
        self.functBox.setFont(arial12r)
        self.functBox.setProperty('attribute', 'functional')
        connect(self.functBox.clicked, self.flagChanged)

        self.predPropLayout.addRow(self.functKey, functParent)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def flagChanged(self):
        """
        Executed whenever one of the property fields changes.
        """
        node = self.node
        diagram = node.diagram
        project = node.project
        sender = self.sender()
        checked = sender.isChecked()
        attribute = sender.property('attribute')
        name = '{0}set {1} {2} property'.format('un' if checked else '', node.shortName, attribute)
        data = {'attribute': attribute, 'undo': getattr(node, attribute), 'redo': checked}
        self.session.undostack.push(CommandSetProperty(diagram, node, data, name))

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        self.functBox.setChecked(node.functional)


class RoleNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Role node.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the Role node information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.functKey = Key('Funct.', self)
        self.functKey.setFont(arial12r)
        functParent = Parent(self)
        self.functBox = CheckBox(functParent)
        self.functBox.setCheckable(True)
        self.functBox.setFont(arial12r)
        self.functBox.setProperty('attribute', 'functional')
        connect(self.functBox.clicked, self.flagChanged)

        self.invFunctKey = Key('Inv. Funct.', self)
        self.invFunctKey.setFont(arial12r)
        invFunctParent = Parent(self)
        self.invFunctBox = CheckBox(invFunctParent)
        self.invFunctBox.setCheckable(True)
        self.invFunctBox.setFont(arial12r)
        self.invFunctBox.setProperty('attribute', 'inverseFunctional')
        connect(self.invFunctBox.clicked, self.flagChanged)

        self.asymmetricKey = Key('Asymmetric', self)
        self.asymmetricKey.setFont(arial12r)
        asymmetricParent = Parent(self)
        self.asymmetricBox = CheckBox(asymmetricParent)
        self.asymmetricBox.setCheckable(True)
        self.asymmetricBox.setFont(arial12r)
        self.asymmetricBox.setProperty('attribute', 'asymmetric')
        connect(self.asymmetricBox.clicked, self.flagChanged)

        self.irreflexiveKey = Key('Irreflexive', self)
        self.irreflexiveKey.setFont(arial12r)
        irreflexiveParent = Parent(self)
        self.irreflexiveBox = CheckBox(irreflexiveParent)
        self.irreflexiveBox.setCheckable(True)
        self.irreflexiveBox.setFont(arial12r)
        self.irreflexiveBox.setProperty('attribute', 'irreflexive')
        connect(self.irreflexiveBox.clicked, self.flagChanged)

        self.reflexiveKey = Key('Reflexive', self)
        self.reflexiveKey.setFont(arial12r)
        reflexiveParent = Parent(self)
        self.reflexiveBox = CheckBox(reflexiveParent)
        self.reflexiveBox.setCheckable(True)
        self.reflexiveBox.setFont(arial12r)
        self.reflexiveBox.setProperty('attribute', 'reflexive')
        connect(self.reflexiveBox.clicked, self.flagChanged)

        self.symmetricKey = Key('Symmetric', self)
        self.symmetricKey.setFont(arial12r)
        symmetricParent = Parent(self)
        self.symmetricBox = CheckBox(symmetricParent)
        self.symmetricBox.setCheckable(True)
        self.symmetricBox.setFont(arial12r)
        self.symmetricBox.setProperty('attribute', 'symmetric')
        connect(self.symmetricBox.clicked, self.flagChanged)

        self.transitiveKey = Key('Transitive', self)
        self.transitiveKey.setFont(arial12r)
        transitiveParent = Parent(self)
        self.transitiveBox = CheckBox(transitiveParent)
        self.transitiveBox.setCheckable(True)
        self.transitiveBox.setFont(arial12r)
        self.transitiveBox.setProperty('attribute', 'transitive')
        connect(self.transitiveBox.clicked, self.flagChanged)

        self.predPropLayout.addRow(self.functKey, functParent)
        self.predPropLayout.addRow(self.invFunctKey, invFunctParent)
        self.predPropLayout.addRow(self.asymmetricKey, asymmetricParent)
        self.predPropLayout.addRow(self.irreflexiveKey, irreflexiveParent)
        self.predPropLayout.addRow(self.reflexiveKey, reflexiveParent)
        self.predPropLayout.addRow(self.symmetricKey, symmetricParent)
        self.predPropLayout.addRow(self.transitiveKey, transitiveParent)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def flagChanged(self):
        """
        Executed whenever one of the property fields changes.
        """
        node = self.node
        diagram = node.diagram
        project = node.project
        sender = self.sender()
        checked = sender.isChecked()
        attribute = sender.property('attribute')
        prop = RE_CAMEL_SPACE.sub('\g<1> \g<2>', attribute).lower()
        name = '{0}set {1} {2} property'.format('un' if checked else '', node.shortName, prop)
        data = {'attribute': attribute, 'undo': getattr(node, attribute), 'redo': checked}
        self.session.undostack.push(CommandSetProperty(diagram, node, data, name))

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        self.asymmetricBox.setChecked(node.asymmetric)
        self.functBox.setChecked(node.functional)
        self.invFunctBox.setChecked(node.inverseFunctional)
        self.irreflexiveBox.setChecked(node.irreflexive)
        self.reflexiveBox.setChecked(node.reflexive)
        self.symmetricBox.setChecked(node.symmetric)
        self.transitiveBox.setChecked(node.transitive)


class ValueDomainNodeInfo(NodeInfo):
    """
    This class implements the information box for the Value Domain node.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the Value Domain node information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.datatypeKey = Key('Datatype', self)
        self.datatypeKey.setFont(arial12r)
        self.datatypeField = Select(self)
        self.datatypeField.setFont(arial12r)
        connect(self.datatypeField.activated, self.datatypeChanged)

        for datatype in Datatype:
            self.datatypeField.addItem(datatype.value, datatype)

        self.nodePropLayout.addRow(self.datatypeKey, self.datatypeField)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def datatypeChanged(self):
        """
        Executed when we need to change the datatype.
        """
        if self.node:
            node = self.node
            diagram = node.diagram
            project = node.project
            datatype = self.datatypeField.currentData()
            data = datatype.value
            if node.text() != data:
                name = 'change {0} to {1}'.format(node.shortName, data)
                self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name))

        self.datatypeField.clearFocus()

    #############################################
    #   INTERFACE
    #################################

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


class ValueNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Individual node with identity 'Value'.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the Value node information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.datatypeKey = Key('Datatype', self)
        self.datatypeKey.setFont(arial12r)
        self.datatypeField = Select(self)
        self.datatypeField.setFont(arial12r)
        connect(self.datatypeField.activated, self.valueChanged)

        self.valueKey = Key('Value', self)
        self.valueKey.setFont(arial12r)
        self.valueField = String(self)
        self.valueField.setFont(arial12r)
        self.valueField.setReadOnly(False)
        connect(self.valueField.editingFinished, self.valueChanged)

        for datatype in Datatype:
            if Facet.forDatatype(datatype):
                self.datatypeField.addItem(datatype.value, datatype)

        self.nodePropLayout.addRow(self.datatypeKey, self.datatypeField)
        self.nodePropLayout.addRow(self.valueKey, self.valueField)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def valueChanged(self):
        """
        Executed when we need to recompute the Value.
        """
        if self.node:

            try:
                node = self.node
                diagram = node.diagram
                project = node.project
                datatype = self.datatypeField.currentData()
                value = self.valueField.value()
                data = node.compose(value, datatype)
                if node.text() != data:
                    name = 'change value to {0}'.format(data)
                    self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name))
            except RuntimeError:
                pass

        self.datatypeField.clearFocus()
        self.valueField.clearFocus()

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)

        #############################################
        # DATATYPE FIELD
        #################################

        datatype = node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break

        #############################################
        # VALUE FIELD
        #################################

        self.valueField.setValue(node.value)


class FacetNodeInfo(NodeInfo):
    """
    This class implements the information box for the Facet node.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the Value Restriction node information box.
        :type session: Session
        :type parent: QWidget
        """
        super().__init__(session, parent)

        arial12r = Font('Arial', 12)

        self.facetKey = Key('Facet', self)
        self.facetKey.setFont(arial12r)
        self.facetField = Select(self)
        self.facetField.setFont(arial12r)
        connect(self.facetField.activated, self.facetChanged)

        self.valueKey = Key('Value', self)
        self.valueKey.setFont(arial12r)
        self.valueField = String(self)
        self.valueField.setFont(arial12r)
        self.valueField.setReadOnly(False)
        connect(self.valueField.editingFinished, self.facetChanged)

        self.nodePropLayout.addRow(self.facetKey, self.facetField)
        self.nodePropLayout.addRow(self.valueKey, self.valueField)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def facetChanged(self):
        """
        Executed when we need to recompute the value of the node.
        """
        if self.node:
            node = self.node
            diagram = node.diagram
            project = node.project
            data = node.compose(self.facetField.currentData(), self.valueField.value())
            if node.text() != data:
                name = 'change {0} to {1}'.format(node.text(), data)
                self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name))

        self.facetField.clearFocus()
        self.valueField.clearFocus()

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)

        #############################################
        # FACET FIELD
        #################################

        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.DatatypeRestrictionNode
        f3 = lambda x: x.type() is Item.ValueDomainNode
        admissible = [x for x in Facet]
        restriction = first(node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if restriction:
            valuedomain = first(restriction.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            if valuedomain:
                admissible = Facet.forDatatype(valuedomain.datatype)

        self.facetField.clear()
        for facet in admissible:
            self.facetField.addItem(facet.value, facet)

        facet = node.facet
        for i in range(self.facetField.count()):
            if self.facetField.itemData(i) is facet:
                self.facetField.setCurrentIndex(i)
                break
        else:
            self.facetField.setCurrentIndex(0)

        #############################################
        # VALUE FIELD
        #################################

        self.valueField.setValue(node.value)