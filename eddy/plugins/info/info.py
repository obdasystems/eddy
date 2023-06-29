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


from abc import (
    ABCMeta,
    abstractmethod,
)
from typing import (
    cast,
    Any,
    Optional,
)

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.commands.iri import CommandIRISetMeta
from eddy.core.commands.labels import CommandLabelChange
from eddy.core.commands.project import (
    CommandProjectSetOntologyIRIAndVersion,
    CommandProjectSetProfile,
)
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.qt import BrushIcon
from eddy.core.diagram import Diagram
from eddy.core.functions.misc import (
    clamp,
    first,
    isEmpty,
)
from eddy.core.functions.signals import (
    connect,
    disconnect,
)
from eddy.core.items.common import AbstractItem
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.owl import OWL2Profiles
from eddy.core.plugin import AbstractPlugin
from eddy.core.project import (
    K_ASYMMETRIC,
    K_DEPRECATED,
    K_FUNCTIONAL,
    K_INVERSE_FUNCTIONAL,
    K_IRREFLEXIVE,
    K_REFLEXIVE,
    K_SYMMETRIC,
    K_TRANSITIVE,
)
from eddy.core.project import Project
from eddy.core.regex import RE_CAMEL_SPACE
from eddy.ui.dock import DockWidget
from eddy.ui.fields import (
    CheckBox,
    ComboBox,
)
from eddy.ui.fields import (
    IntegerField,
    StringField,
)
from eddy.ui.mdi import MdiSubWindow
from eddy.ui.session import Session


class InfoPlugin(AbstractPlugin):
    """
    This plugin provides the Information widget.
    """
    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """
        Filters events if this object has been installed as an event filter for the watched object.
        """
        if event.type() == QtCore.QEvent.Resize:
            widget = source.widget()
            widget.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene)
    def onDiagramAdded(self, _diagram: Diagram) -> None:
        """
        Executed whenever a diagram is added to the active project.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene)
    def onDiagramRemoved(self, _diagram: Diagram) -> None:
        """
        Executed whenever a diagram is removed from the active project.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot()
    def onDiagramSelectionChanged(self) -> None:
        """
        Executed whenever the selection of the active diagram changes.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot()
    def onDiagramUpdated(self) -> None:
        """
        Executed whenever the active diagram is updated.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    def onProjectItemAdded(self, _diagram: Diagram, _item: AbstractItem) -> None:
        """
        Executed whenever a new element is added to the active project.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    def onProjectItemRemoved(self, _diagram: Diagram, _item: AbstractItem) -> None:
        """
        Executed whenever a new element is removed from the active project.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot()
    def onProjectUpdated(self) -> None:
        """
        Executed whenever the current project is updated.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot()
    def onSessionReady(self) -> None:
        """
        Executed whenever the main session completes the startup sequence.
        """
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnUpdated, self.onProjectUpdated)
        connect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        connect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        connect(self.project.sgnItemAdded, self.onProjectItemAdded)
        connect(self.project.sgnItemRemoved, self.onProjectItemRemoved)
        connect(self.project.sgnUpdated, self.onProjectUpdated)
        self.widget('info').stack()

    @QtCore.pyqtSlot(QtWidgets.QMdiSubWindow)
    def onSubWindowActivated(self, subwindow: MdiSubWindow) -> None:
        """
        Executed when the active subwindow changes.
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
                disconnect(widget.diagram.sgnUpdated, self.onDiagramUpdated)
            # Attach the new view/diagram to the info widget.
            self.debug('Connecting to diagram: %s', subwindow.diagram.name)
            connect(subwindow.diagram.selectionChanged, self.onDiagramSelectionChanged)
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
                    disconnect(widget.diagram.sgnUpdated, self.onDiagramUpdated)
                widget.setDiagram(None)
                widget.stack()

    #############################################
    #   HOOKS
    #################################

    def dispose(self) -> None:
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM CURRENT PROJECT
        self.debug('Disconnecting from project: %s', self.project.name)
        disconnect(self.project.sgnUpdated, self.onProjectUpdated)
        disconnect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        disconnect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        disconnect(self.project.sgnItemAdded, self.onProjectItemAdded)
        disconnect(self.project.sgnItemRemoved, self.onProjectItemRemoved)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnReady, self.onSessionReady)
        disconnect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)

        # REMOVE DOCKING AREA WIDGET MENU ENTRY
        self.debug('Removing docking area widget toggle from "view" menu')
        menu = self.session.menu('view')
        menu.removeAction(self.widget('info_dock').toggleViewAction())

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling docking area widget')
        self.session.removeDockWidget(cast(QtWidgets.QDockWidget, self.widget('info_dock')))

    def start(self) -> None:
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
        widget = DockWidget('Info', QtGui.QIcon(':/icons/18/ic_info_outline_black'), self.session)
        widget.installEventFilter(self)
        widget.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea
            | QtCore.Qt.RightDockWidgetArea
            | QtCore.Qt.BottomDockWidgetArea
        )
        widget.setObjectName('info_dock')
        widget.setWidget(self.widget('info'))
        self.addWidget(widget)

        # CREATE SHORTCUTS
        action = widget.toggleViewAction()
        action.setParent(self.session)
        action.setShortcut(QtGui.QKeySequence('Alt+2'))

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('info_dock').toggleViewAction())

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(
            QtCore.Qt.RightDockWidgetArea,
            cast(QtWidgets.QDockWidget, self.widget('info_dock'))
        )

        # CONFIGURE SIGNAL/SLOTS
        self.debug('Connecting to active session')
        connect(self.session.sgnReady, self.onSessionReady)
        connect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)


class InfoWidget(QtWidgets.QScrollArea):
    """
    This class implements the information box widget.
    """
    def __init__(self, plugin: AbstractPlugin) -> None:
        """
        Initialize the info box.
        """
        super().__init__(plugin.session)

        self.diagram = None  # type: Optional[Diagram]
        self.plugin = plugin  # type: AbstractPlugin

        self.stacked = QtWidgets.QStackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)
        self.infoEmpty = QtWidgets.QWidget(self.stacked)
        self.infoProject = ProjectInfo(self.session, self.stacked)
        self.infoEdge = EdgeInfo(self.session, self.stacked)
        self.infoNode = NodeInfo(self.session, self.stacked)
        self.infoPredicateNode = IRIInfo(self.session, self.stacked)
        self.infoAttributeNode = AttributeIRIInfo(self.session, self.stacked)
        self.infoRoleNode = RoleIRIInfo(self.session, self.stacked)
        self.infoLiteral = LiteralInfo(self.session, self.stacked)
        self.infoFacet = FacetIRIInfo(self.session, self.stacked)
        # Old names, for reference
        # self.infoPredicateNode = PredicateNodeInfo(self.session, self.stacked)
        # self.infoAttributeNode = AttributeNodeInfo(self.session, self.stacked)
        # self.infoRoleNode = RoleNodeInfo(self.session, self.stacked)
        # self.infoValueNode = ValueNodeInfo(self.session, self.stacked)
        # self.infoValueDomainNode = ValueDomainNodeInfo(self.session, self.stacked)
        # self.infoFacet = FacetNodeInfo(self.session, self.stacked)
        self.stacked.addWidget(self.infoProject)
        self.stacked.addWidget(self.infoEdge)
        self.stacked.addWidget(self.infoNode)
        self.stacked.addWidget(self.infoAttributeNode)
        self.stacked.addWidget(self.infoPredicateNode)
        self.stacked.addWidget(self.infoRoleNode)
        self.stacked.addWidget(self.infoLiteral)
        self.stacked.addWidget(self.infoFacet)
        # self.stacked.addWidget(self.infoValueNode)
        # self.stacked.addWidget(self.infoValueDomainNode)
        # self.stacked.addWidget(self.infoFacet)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QtCore.QSize(216, 120))
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
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
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB;
          border-left: none;
          padding: 0 0 0 4px;
        }
        InfoWidget Button,
        InfoWidget Button:focus,
        InfoWidget Button:hover,
        InfoWidget Button:hover:focus,
        InfoWidget Button:pressed,
        InfoWidget Button:pressed:focus,
        InfoWidget Integer,
        InfoWidget String,
        InfoWidget Select,
        InfoWidget Parent {
          background: #E3F2FD;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB !important;
          border-left: 1px solid #BBDEFB !important;
          padding: 0 0 0 4px;
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
        }
        InfoWidget QCheckBox::indicator:disabled {
          background-color: #BABABA;
        }
        """)

        scrollbar = self.verticalScrollBar()
        scrollbar.installEventFilter(self)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self) -> Project:
        """
        Returns the reference to the active project.
        """
        return self.plugin.project

    @property
    def session(self) -> Session:
        """
        Returns the reference to the active session.
        """
        return self.plugin.session

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """
        Filter incoming events.
        """
        if source is self.verticalScrollBar():
            if event.type() in {QtCore.QEvent.Show, QtCore.QEvent.Hide}:
                self.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   INTERFACE
    #################################

    def redraw(self) -> None:
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

    def setDiagram(self, diagram: Diagram) -> None:
        """
        Sets the widget to inspect the given diagram.
        """
        self.diagram = diagram

    def stack(self) -> None:
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
                        if item.type() is Item.AttributeNode:
                            show = self.infoAttributeNode
                        elif item.type() is Item.RoleNode:
                            show = self.infoRoleNode
                        elif item.type() is Item.LiteralNode:
                            show = self.infoLiteral
                        elif item.type() is Item.FacetNode:
                            show = self.infoFacet
                        else:
                            show = self.infoPredicateNode
                    else:
                        show = self.infoNode
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


class Header(QtWidgets.QLabel):
    """
    This class implements the header of properties section.
    """
    def __init__(self, *args: Any) -> None:
        """
        Initialize the header.
        """
        super().__init__(*args)
        self.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.setFixedHeight(24)


class Key(QtWidgets.QLabel):
    """
    This class implements the key of an info field.
    """
    def __init__(self, *args: Any) -> None:
        """
        Initialize the key.
        """
        super().__init__(*args)
        self.setFixedSize(88, 20)


class Button(QtWidgets.QPushButton):
    """
    This class implements the button to which associate a QtWidgets.QMenu instance of an info field.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the button.
        """
        super().__init__(*args)


class Integer(IntegerField):
    """
    This class implements the integer value of an info field.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class String(StringField):
    """
    This class implements the string value of an info field.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class Select(ComboBox):
    """
    This class implements the selection box of an info field.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setScrollEnabled(False)


class Parent(QtWidgets.QWidget):
    """
    This class implements the parent placeholder to be used
    to store checkbox and radio button value fields.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)

    def paintEvent(self, paintEvent: QtGui.QPaintEvent) -> None:
        """
        This is needed for the widget to pick the stylesheet.
        """
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        painter = QtGui.QPainter(self)
        style = self.style()
        style.drawPrimitive(QtWidgets.QStyle.PE_Widget, option, painter, self)


#############################################
#   INFO WIDGETS
#################################

class AbstractInfo(QtWidgets.QWidget):
    """
    This class implements the base information box.
    """
    __metaclass__ = ABCMeta

    def __init__(self, session: Session, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the base information box.
        """
        super().__init__(parent)
        self.session = session
        self.setContentsMargins(0, 0, 0, 0)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self) -> Project:
        """
        Returns the project loaded in the current session.
        """
        return self.session.project

    #############################################
    #   INTERFACE
    #################################

    @abstractmethod
    def updateData(self, **kwargs: Any) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        pass


class ProjectInfo(AbstractInfo):
    """
    This class implements the project information box.
    """
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the project information box.
        """
        super().__init__(session, parent)

        self.versionKey = Key('Version', self)
        self.versionField = String(self)
        self.versionField.setReadOnly(True)
        connect(self.versionField.editingFinished, self.onVersionEditingFinished)

        # self.prefixKey = Key('Prefix', self)
        # self.prefixField = String(self)
        # self.prefixField.setReadOnly(True)
        # connect(self.prefixField.editingFinished, self.onPrefixEditingFinished)

        self.iriKey = Key('IRI', self)
        self.iriField = String(self)
        self.iriField.setReadOnly(True)
        connect(self.iriField.editingFinished, self.onIRIEditingFinished)

        # self.profileKey = Key('Profile', self)
        # self.profileField = Select(self)
        # self.profileField.addItems(self.session.profileNames())
        # connect(self.profileField.activated, self.onProfileChanged)

        self.ontologyPropHeader = Header('Ontology properties', self)
        self.ontologyPropLayout = QtWidgets.QFormLayout()
        self.ontologyPropLayout.setSpacing(0)
        self.ontologyPropLayout.addRow(self.iriKey, self.iriField)
        self.ontologyPropLayout.addRow(self.versionKey, self.versionField)
        # self.ontologyPropLayout.addRow(self.prefixKey, self.prefixField)
        # self.ontologyPropLayout.addRow(self.prefixesKey, self.prefixesField)
        # self.ontologyPropLayout.addRow(self.profileKey, self.profileField)

        self.conceptsKey = Key('Classes', self)
        self.conceptsField = Integer(self)
        self.conceptsField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.conceptsField.setReadOnly(True)

        self.rolesKey = Key('Obj prop.', self)
        self.rolesField = Integer(self)
        self.rolesField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rolesField.setReadOnly(True)

        self.attributesKey = Key('Data prop.', self)
        self.attributesField = Integer(self)
        self.attributesField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.attributesField.setReadOnly(True)

        self.individualsKey = Key('Individuals', self)
        self.individualsField = Integer(self)
        self.individualsField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.individualsField.setReadOnly(True)

        self.inclusionsKey = Key('Inclusion', self)
        self.inclusionsField = Integer(self)
        self.inclusionsField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.inclusionsField.setReadOnly(True)

        self.membershipKey = Key('Membership', self)
        self.membershipField = Integer(self)
        self.membershipField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.membershipField.setReadOnly(True)

        self.atomicPredHeader = Header('Ontology Metrics', self)
        self.atomicPredLayout = QtWidgets.QFormLayout()
        self.atomicPredLayout.setSpacing(0)
        self.atomicPredLayout.addRow(self.conceptsKey, self.conceptsField)
        self.atomicPredLayout.addRow(self.rolesKey, self.rolesField)
        self.atomicPredLayout.addRow(self.attributesKey, self.attributesField)
        self.atomicPredLayout.addRow(self.individualsKey, self.individualsField)

        # self.assertionsHeader = Header('Assertions', self)
        # self.assertionsLayout = QtWidgets.QFormLayout()
        # self.assertionsLayout.setSpacing(0)
        # self.assertionsLayout.addRow(self.inclusionsKey, self.inclusionsField)
        # self.assertionsLayout.addRow(self.membershipKey, self.membershipField)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.insertWidget(2,self.ontologyPropHeader)
        self.mainLayout.insertLayout(3,self.ontologyPropLayout)
        self.mainLayout.insertWidget(0,self.atomicPredHeader)
        self.mainLayout.insertLayout(1,self.atomicPredLayout)
        # self.mainLayout.addWidget(self.assertionsHeader)
        # self.mainLayout.addLayout(self.assertionsLayout)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onIRIEditingFinished(self) -> None:
        """
        Executed whenever we finish to edit the ontology prefix
        """
        self.iriField.clearFocus()

    @QtCore.pyqtSlot()
    def onPrefixEditingFinished(self) -> None:
        """
        Executed whenever we finish to edit the ontology prefix
        """
        self.prefixField.clearFocus()

    @QtCore.pyqtSlot()
    def onProfileChanged(self) -> None:
        """
        Executed when we need to change the project profile.
        """
        profile = self.profileField.currentText()
        if self.project.profile.name() != profile:
            self.session.undostack.push(CommandProjectSetProfile(self.project, self.project.profile.name(), profile))
        self.profileField.clearFocus()

    @QtCore.pyqtSlot()
    def onVersionEditingFinished(self) -> None:
        """
        Executed whenever we finish to edit the ontology prefix
        """
        version = self.versionField.value()
        if self.project.version != version:
            # FIXME: Why are arguments in the call missing?
            self.session.undostack.push(CommandProjectSetOntologyIRIAndVersion(self.project, self.project.version, version))
        self.versionField.clearFocus()

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, project: Project) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        # self.prefixField.setValue(project.prefix)
        # self.prefixField.home(True)
        # self.prefixField.clearFocus()
        # self.prefixField.deselect()

        self.iriField.setValue(str(project.ontologyIRI))
        self.iriField.home(True)
        self.iriField.clearFocus()
        self.iriField.deselect()

        self.versionField.setValue(project.version)
        self.versionField.home(True)
        self.versionField.clearFocus()
        self.versionField.deselect()

        # for i in range(self.profileField.count()):
        #     if self.profileField.itemText(i) == self.project.profile.name():
        #         self.profileField.setCurrentIndex(i)
        #         break

        self.attributesField.setValue(len(project.itemIRIs(Item.AttributeNode)))
        self.conceptsField.setValue(len(project.itemIRIs(Item.ConceptNode)))
        self.rolesField.setValue(len(project.itemIRIs(Item.RoleNode)))
        self.individualsField.setValue(len(project.itemIRIs(Item.IndividualNode)))
        # self.inclusionsField.setValue(project.itemNum(Item.InclusionEdge))
        # self.membershipField.setValue(project.itemNum(Item.MembershipEdge))


class EdgeInfo(AbstractInfo):
    """
    This class implements the information box for generic edges.
    """
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the generic edge information box.
        """
        super().__init__(session, parent)

        self.h1 = Header('General', self)

        self.typeKey = Key('Type', self)
        self.typeField = String(self)
        self.typeField.setReadOnly(True)

        self.sourceKey = Key('Source', self)
        self.sourceField = String(self)
        self.sourceField.setReadOnly(True)

        self.targetKey = Key('Target', self)
        self.targetField = String(self)
        self.targetField.setReadOnly(True)

        self.generalLayout = QtWidgets.QFormLayout()
        self.generalLayout.setSpacing(0)
        self.generalLayout.addRow(self.typeKey, self.typeField)
        self.generalLayout.addRow(self.sourceKey, self.sourceField)
        self.generalLayout.addRow(self.targetKey, self.targetField)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.h1)
        self.mainLayout.addLayout(self.generalLayout)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, edge: AbstractEdge) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        self.sourceField.setValue(edge.source.id)
        self.targetField.setValue(edge.target.id)
        self.typeField.setValue(edge.shortName.capitalize())
        self.typeField.home(True)
        self.typeField.deselect()


class NodeInfo(AbstractInfo):
    """
    This class implements the information box for generic nodes.
    """
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the generic node information box.
        """
        super().__init__(session, parent)

        self.node = None

        self.idKey = Key('ID', self)
        self.idField = String(self)
        self.idField.setReadOnly(True)

        self.identityKey = Key('Identity', self)
        self.identityField = String(self)
        self.identityField.setReadOnly(True)

        self.nodePropHeader = Header('Node properties', self)
        self.nodePropLayout = QtWidgets.QFormLayout()
        self.nodePropLayout.setSpacing(0)
        self.nodePropLayout.addRow(self.idKey, self.idField)
        self.nodePropLayout.addRow(self.identityKey, self.identityField)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.nodePropHeader)
        self.mainLayout.addLayout(self.nodePropLayout)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node: AbstractNode) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        self.idField.setValue(node.id)
        self.identityField.setValue(node.identityName)
        self.node = node


#############################################
#   IRI INFO WIDGETS
#################################

class IRIInfo(NodeInfo):
    """
    This class implements the information box for nodes having an associated IRI.
    """
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the predicate node information box.
        """
        super().__init__(session, parent)

        self.textKey = Key('Label', self)
        self.textField = String(self)
        # self.textField.setReadOnly(False)
        self.textField.setReadOnly(True)
        connect(self.textField.editingFinished, self.onEditingFinished)

        self.brushKey = Key('Color', self)
        self.brushMenu = QtWidgets.QMenu(self)
        self.brushButton = Button()
        self.brushButton.setMenu(self.brushMenu)
        self.brushButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Preferred)

        self.nodePropLayout.addRow(self.brushKey, self.brushButton)

        self.nameKey = Key('Simple name', self)
        self.nameField = String(self)
        # self.nameField.setReadOnly(False)
        self.nameField.setReadOnly(True)
        # connect(self.nameField.editingFinished, self.editingFinished)

        self.fullIRIKey = Key('IRI', self)
        self.fullIRIField = String(self)
        # self.nameField.setReadOnly(False)
        self.fullIRIField.setReadOnly(True)
        # connect(self.fullIRIField.editingFinished, self.editingFinished)

        self.deprKey = Key('Deprecated', self)
        deprParent = Parent(self)
        self.deprBox = CheckBox(deprParent)
        self.deprBox.setCheckable(True)
        self.deprBox.setProperty('key', K_DEPRECATED)
        connect(self.deprBox.clicked, self.onFlagChanged)

        self.predPropHeader = Header('IRI properties', self)
        self.labelKey = Key('Label', self)
        self.labelField = String(self)
        # self.textField.setReadOnly(False)
        self.labelField.setReadOnly(True)
        # connect(self.labelField.editingFinished, self.editingFinished)

        self.predPropHeader = Header('IRI properties', self)
        self.predPropLayout = QtWidgets.QFormLayout()
        self.predPropLayout.setSpacing(0)
        self.predPropLayout.addRow(self.fullIRIKey, self.fullIRIField)
        self.predPropLayout.addRow(self.nameKey, self.nameField)
        self.predPropLayout.addRow(self.labelKey, self.labelField)
        self.predPropLayout.addRow(self.deprKey, deprParent)

        self.mainLayout.insertWidget(0, self.predPropHeader)
        self.mainLayout.insertLayout(1, self.predPropLayout)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onEditingFinished(self) -> None:
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
                            self.session.undostack.push(CommandLabelChange(n.diagram, n, n.text(), data, refactor=True))
                        self.session.undostack.endMacro()
                    else:
                        self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data))
            except RuntimeError:
                pass

        self.nameField.clearFocus()
        self.textField.clearFocus()

    @QtCore.pyqtSlot()
    def onFlagChanged(self) -> None:
        """
        Executed whenever one of the property fields changes.
        """
        sender = self.sender()
        checked = sender.isChecked()
        key = sender.property('key')
        undo = self.node.iri.getMetaProperties()
        redo = undo.copy()
        redo[key] = checked
        if redo != undo:
            prop = RE_CAMEL_SPACE.sub(r'\g<1> \g<2>', key).lower()
            name = "{0}set '{1}' {2} property".format('' if checked else 'un', self.node.iri, prop)
            self.session.undostack.push(
                CommandIRISetMeta(self.project, self.node.type(), self.node.iri, undo, redo, name)
            )

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node: AbstractNode) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        super().updateData(node)

        #############################################
        # BRUSH FIELD
        #################################

        if self.brushMenu.isEmpty():
            self.brushMenu.addActions(self.session.action('brush').actions())
        for action in self.session.action('brush').actions():
            color = action.data()
            brush = QtGui.QBrush(QtGui.QColor(color.value))
            if node.brush() == brush:
                self.brushButton.setIcon(BrushIcon(12, 12, color.value, '#000000'))
                self.brushButton.setText(color.value)
                break

        #############################################
        # IRI FIELDS
        #################################

        if node.iri:
            self.fullIRIField.setValue(str(node.iri))
            self.nameField.setValue(str(node.iri.getSimpleName()))
            settings = QtCore.QSettings()
            lang = settings.value('ontology/iri/render/language', 'it')
            labelAssertion = self.node.iri.getLabelAnnotationAssertion(lang)
            if labelAssertion:
                self.labelField.setValue(labelAssertion.getObjectResourceString(True))
            else:
                self.labelField.setValue('')
            self.deprBox.setChecked(node.iri.deprecated)


class FacetIRIInfo(NodeInfo):
    """
    This class implements the information box for nodes having an associated Facet.
    """
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the predicate node information box.
        """
        super().__init__(session, parent)

        self.brushKey = Key('Color', self)
        self.brushMenu = QtWidgets.QMenu(self)
        self.brushButton = Button()
        self.brushButton.setMenu(self.brushMenu)
        self.brushButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Preferred)

        self.nodePropLayout.addRow(self.brushKey, self.brushButton)
        # self.nodePropLayout.addRow(self.textKey, self.textField)

        self.facetKey = Key('Constr. facet', self)
        self.facetField = String(self)
        # self.nameField.setReadOnly(False)
        self.facetField.setReadOnly(True)
        connect(self.facetField.editingFinished, self.onEditingFinished)

        self.valueKey = Key('Constr. value', self)
        self.valueField = String(self)
        # self.nameField.setReadOnly(False)
        self.valueField.setReadOnly(True)
        connect(self.valueField.editingFinished, self.onEditingFinished)

        self.predPropHeader = Header('Literal properties', self)
        self.predPropLayout = QtWidgets.QFormLayout()
        self.predPropLayout.setSpacing(0)
        self.predPropLayout.addRow(self.facetKey, self.facetField)
        self.predPropLayout.addRow(self.valueKey, self.valueField)

        self.mainLayout.insertWidget(0, self.predPropHeader)
        self.mainLayout.insertLayout(1, self.predPropLayout)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onEditingFinished(self) -> None:
        """
        Executed whenever we finish to edit the predicate/node name.
        """
        self.facetField.clearFocus()
        self.textField.clearFocus()

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node: AbstractNode) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        super().updateData(node)

        #############################################
        # FACET FIELDS
        #################################

        if node.facet:
            self.valueField.setValue(str(node.facet.literal))
            self.facetField.setValue(str(node.facet.constrainingFacet))


class AttributeIRIInfo(IRIInfo):
    """
    This class implements the information box for the Attribute node.
    """
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the Attribute node information box.
        """
        super().__init__(session, parent)

        self.functKey = Key('Funct.', self)
        functParent = Parent(self)
        self.functBox = CheckBox(functParent)
        self.functBox.setCheckable(True)
        self.functBox.setProperty('key', K_FUNCTIONAL)
        connect(self.functBox.clicked, self.onFlagChanged)

        self.predPropLayout.addRow(self.functKey, functParent)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onFlagChanged(self) -> None:
        """
        Executed whenever one of the property fields changes.
        """
        sender = self.sender()
        checked = sender.isChecked()
        key = sender.property('key')
        undo = self.node.iri.getMetaProperties()
        redo = undo.copy()
        redo[key] = checked
        if redo != undo:
            prop = RE_CAMEL_SPACE.sub(r'\g<1> \g<2>', key).lower()
            name = "{0}set '{1}' {2} property".format('' if checked else 'un', self.node.iri, prop)
            self.session.undostack.push(
                CommandIRISetMeta(self.project, self.node.type(), self.node.iri, undo, redo, name)
            )

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node: AbstractNode) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        super().updateData(node)
        self.functBox.setChecked(node.isFunctional())

        functEnabled = self.functBox.isChecked() or (self.project.profile.type() is not OWL2Profiles.OWL2QL)
        self.functBox.setEnabled(functEnabled)
        self.functKey.setEnabled(functEnabled)


class RoleIRIInfo(IRIInfo):
    """
    This class implements the information box for the Role node.
    """
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the Role node information box.
        """
        super().__init__(session, parent)

        self.functKey = Key('Funct.', self)
        functParent = Parent(self)
        self.functBox = CheckBox(functParent)
        self.functBox.setCheckable(True)
        self.functBox.setProperty('key', K_FUNCTIONAL)
        connect(self.functBox.clicked, self.onFlagChanged)

        self.invFunctKey = Key('Inv. Funct.', self)
        invFunctParent = Parent(self)
        self.invFunctBox = CheckBox(invFunctParent)
        self.invFunctBox.setCheckable(True)
        self.invFunctBox.setProperty('key', K_INVERSE_FUNCTIONAL)
        connect(self.invFunctBox.clicked, self.onFlagChanged)

        self.asymmetricKey = Key('Asymmetric', self)
        asymmetricParent = Parent(self)
        self.asymmetricBox = CheckBox(asymmetricParent)
        self.asymmetricBox.setCheckable(True)
        self.asymmetricBox.setProperty('key', K_ASYMMETRIC)
        connect(self.asymmetricBox.clicked, self.onFlagChanged)

        self.irreflexiveKey = Key('Irreflexive', self)
        irreflexiveParent = Parent(self)
        self.irreflexiveBox = CheckBox(irreflexiveParent)
        self.irreflexiveBox.setCheckable(True)
        self.irreflexiveBox.setProperty('key', K_IRREFLEXIVE)
        connect(self.irreflexiveBox.clicked, self.onFlagChanged)

        self.reflexiveKey = Key('Reflexive', self)
        reflexiveParent = Parent(self)
        self.reflexiveBox = CheckBox(reflexiveParent)
        self.reflexiveBox.setCheckable(True)
        self.reflexiveBox.setProperty('key', K_REFLEXIVE)
        connect(self.reflexiveBox.clicked, self.onFlagChanged)

        self.symmetricKey = Key('Symmetric', self)
        symmetricParent = Parent(self)
        self.symmetricBox = CheckBox(symmetricParent)
        self.symmetricBox.setCheckable(True)
        self.symmetricBox.setProperty('key', K_SYMMETRIC)
        connect(self.symmetricBox.clicked, self.onFlagChanged)

        self.transitiveKey = Key('Transitive', self)
        transitiveParent = Parent(self)
        self.transitiveBox = CheckBox(transitiveParent)
        self.transitiveBox.setCheckable(True)
        self.transitiveBox.setProperty('key', K_TRANSITIVE)
        connect(self.transitiveBox.clicked, self.onFlagChanged)

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

    @QtCore.pyqtSlot()
    def onFlagChanged(self) -> None:
        """
        Executed whenever one of the property fields changes.
        """
        sender = self.sender()
        checked = sender.isChecked()
        key = sender.property('key')
        # undo = self.project.meta(self.node.type(), self.node.text())
        undo = self.node.iri.getMetaProperties()
        redo = undo.copy()
        redo[key] = checked
        if redo != undo:
            prop = RE_CAMEL_SPACE.sub(r'\g<1> \g<2>', key).lower()
            name = "{0}set '{1}' {2} property".format('' if checked else 'un', self.node.iri, prop)
            self.session.undostack.push(
                CommandIRISetMeta(self.project, self.node.type(), self.node.iri, undo, redo, name)
            )

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node: AbstractNode) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        super().updateData(node)

        self.asymmetricBox.setChecked(node.isAsymmetric())

        self.functBox.setChecked(node.isFunctional())
        functEnabled = self.functBox.isChecked() or self.project.profile.type() is not OWL2Profiles.OWL2QL
        self.functBox.setEnabled(functEnabled)
        self.functKey.setEnabled(functEnabled)

        self.invFunctBox.setChecked(node.isInverseFunctional())
        invfunctEnabled = self.invFunctBox.isChecked() or self.project.profile.type() is not OWL2Profiles.OWL2QL
        self.invFunctBox.setEnabled(invfunctEnabled)
        self.invFunctKey.setEnabled(invfunctEnabled)

        self.irreflexiveBox.setChecked(node.isIrreflexive())

        self.reflexiveBox.setChecked(node.isReflexive())
        reflexiveEnabled = self.reflexiveBox.isChecked() or self.project.profile.type() is not OWL2Profiles.OWL2RL
        self.reflexiveBox.setEnabled(reflexiveEnabled)
        self.reflexiveKey.setEnabled(reflexiveEnabled)

        self.symmetricBox.setChecked(node.isSymmetric())

        self.transitiveBox.setChecked(node.isTransitive())
        transitiveEnabled = self.transitiveBox.isChecked() or self.project.profile.type() is not OWL2Profiles.OWL2QL
        self.transitiveBox.setEnabled(transitiveEnabled)
        self.transitiveKey.setEnabled(transitiveEnabled)


class LiteralInfo(NodeInfo):
    """
    This class implements the information box for nodes having an associated IRI.
    """
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the predicate node information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)

        self.brushKey = Key('Color', self)
        self.brushMenu = QtWidgets.QMenu(self)
        self.brushButton = Button()
        self.brushButton.setMenu(self.brushMenu)
        self.brushButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Preferred)

        self.nodePropLayout.addRow(self.brushKey, self.brushButton)
        # self.nodePropLayout.addRow(self.textKey, self.textField)

        self.lexicalSpaceKey = Key('Lexical space', self)
        self.lexicalFormField = String(self)
        # self.nameField.setReadOnly(False)
        self.lexicalFormField.setReadOnly(True)
        connect(self.lexicalFormField.editingFinished, self.onEditingFinished)

        self.datatypeKey = Key('Datatype', self)
        self.datatypeField = String(self)
        # self.nameField.setReadOnly(False)
        self.datatypeField.setReadOnly(True)
        connect(self.datatypeField.editingFinished, self.onEditingFinished)

        self.langKey = Key('Language', self)
        self.langField = String(self)
        # self.textField.setReadOnly(False)
        self.langField.setReadOnly(True)
        connect(self.langField.editingFinished, self.onEditingFinished)

        self.predPropHeader = Header('Literal properties', self)
        self.predPropLayout = QtWidgets.QFormLayout()
        self.predPropLayout.setSpacing(0)
        self.predPropLayout.addRow(self.datatypeKey, self.datatypeField)
        self.predPropLayout.addRow(self.lexicalSpaceKey, self.lexicalFormField)
        self.predPropLayout.addRow(self.langKey, self.langField)

        self.mainLayout.insertWidget(0, self.predPropHeader)
        self.mainLayout.insertLayout(1, self.predPropLayout)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onEditingFinished(self) -> None:
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
                    if sender is self.lexicalFormField:
                        self.session.undostack.beginMacro('change predicate "{0}" to "{1}"'.format(node.text(), data))
                        for n in project.predicates(node.type(), node.text()):
                            self.session.undostack.push(CommandLabelChange(n.diagram, n, n.text(), data, refactor=True))
                        self.session.undostack.endMacro()
                    else:
                        self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data))
            except RuntimeError:
                pass

        self.lexicalFormField.clearFocus()
        self.textField.clearFocus()

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node: AbstractNode) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        super().updateData(node)

        #############################################
        # BRUSH FIELD
        #################################

        if self.brushMenu.isEmpty():
            self.brushMenu.addActions(self.session.action('brush').actions())
        for action in self.session.action('brush').actions():
            color = action.data()
            brush = QtGui.QBrush(QtGui.QColor(color.value))
            if node.brush() == brush:
                self.brushButton.setIcon(BrushIcon(12, 12, color.value, '#000000'))
                self.brushButton.setText(color.value)
                break

        #############################################
        # LITERAL FIELDS
        #################################

        if node.literal:
            self.datatypeField.setValue(str(node.datatype))
            self.lexicalFormField.setValue(str(node.lexicalForm))
            if node.language:
                self.langField.setValue(str(node.language))
