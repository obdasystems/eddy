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


from abc import ABCMeta, abstractmethod
from operator import attrgetter

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.commands.labels import CommandLabelChange
from eddy.core.commands.nodes_2 import CommandProjetSetIRIPrefixesNodesDict, CommandProjectORNodeSetPreferedPrefix
from eddy.core.commands.nodes import CommandNodeSetMeta
from eddy.core.commands.project import CommandProjectSetIRI
from eddy.core.commands.project import CommandProjectSetPrefix
from eddy.core.commands.project import CommandProjectSetProfile
from eddy.core.commands.project import CommandProjectSetVersion
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.owl import Facet, Datatype, OWLProfile
from eddy.core.datatypes.qt import BrushIcon, Font
from eddy.core.functions.misc import first, clamp, isEmpty
from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin
from eddy.core.project import K_FUNCTIONAL, K_INVERSE_FUNCTIONAL
from eddy.core.project import K_ASYMMETRIC, K_IRREFLEXIVE, K_REFLEXIVE
from eddy.core.project import K_SYMMETRIC, K_TRANSITIVE
from eddy.core.regex import RE_CAMEL_SPACE

from eddy.ui.dock import DockWidget
from eddy.ui.fields import IntegerField, StringField
from eddy.ui.fields import CheckBox, ComboBox


class InfoPlugin(AbstractPlugin):
    """
    This plugin provides the Information widget.
    """
    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :type source: QObject
        :type event: QtCore.QEvent
        :rtype: bool
        """
        if event.type() == QtCore.QEvent.Resize:
            widget = source.widget()
            widget.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot('QGraphicsScene')
    def onDiagramAdded(self, diagram):
        """
        Executed whenever a diagram is added to the active project.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot('QGraphicsScene')
    def onDiagramRemoved(self, diagram):
        """
        Executed whenever a diagram is removed from the active project.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot()
    def onDiagramSelectionChanged(self):
        """
        Executed whenever the selection of the active diagram changes.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot()
    def onDiagramUpdated(self):
        """
        Executed whenever the active diagram is updated.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def onProjectItemAdded(self, diagram, item):
        """
        Executed whenever a new element is added to the active project.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def onProjectItemRemoved(self, diagram, item):
        """
        Executed whenever a new element is removed from the active project.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot()
    def onProjectUpdated(self):
        """
        Executed whenever the current project is updated.
        """
        self.widget('info').stack()

    @QtCore.pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnUpdated, self.onProjectUpdated)
        connect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        connect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        connect(self.project.sgnItemAdded, self.onProjectItemAdded)
        connect(self.project.sgnItemRemoved, self.onProjectItemRemoved)
        self.widget('info').stack()

    @QtCore.pyqtSlot(QtWidgets.QMdiSubWindow)
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

    def dispose(self):
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
        self.session.removeDockWidget(self.widget('info_dock'))

    def start(self):
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
        widget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        widget.setObjectName('info_dock')
        widget.setWidget(self.widget('info'))
        self.addWidget(widget)

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('info_dock').toggleViewAction())

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget('info_dock'))

        # CONFIGURE SIGNAL/SLOTS
        self.debug('Connecting to active session')
        connect(self.session.sgnReady, self.onSessionReady)
        connect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)


class InfoWidget(QtWidgets.QScrollArea):
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

        self.stacked = QtWidgets.QStackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)
        self.infoEmpty = QtWidgets.QWidget(self.stacked)
        self.infoProject = ProjectInfo(self.session, self.stacked)
        self.infoEdge = EdgeInfo(self.session, self.stacked)
        self.infoNode = NodeInfo(self.session, self.stacked)
        self.infoPredicateNode = PredicateNodeInfo(self.session, self.stacked)
        self.infoAttributeNode = AttributeNodeInfo(self.session, self.stacked)
        self.infoRoleNode = RoleNodeInfo(self.session, self.stacked)
        self.infoValueNode = ValueNodeInfo(self.session, self.stacked)
        self.infoValueDomainNode = ValueDomainNodeInfo(self.session, self.stacked)
        self.infoFacet = FacetNodeInfo(self.session, self.stacked)
        self.stacked.addWidget(self.infoProject)
        self.stacked.addWidget(self.infoEdge)
        self.stacked.addWidget(self.infoNode)
        self.stacked.addWidget(self.infoPredicateNode)
        self.stacked.addWidget(self.infoAttributeNode)
        self.stacked.addWidget(self.infoRoleNode)
        self.stacked.addWidget(self.infoValueNode)
        self.stacked.addWidget(self.infoValueDomainNode)
        self.stacked.addWidget(self.infoFacet)

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
        :type event: QtCore.QEvent
        """
        if source is self.verticalScrollBar():
            if event.type() in {QtCore.QEvent.Show, QtCore.QEvent.Hide}:
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
                        else:
                            show = self.infoPredicateNode
                    else:
                        if item.type() is Item.FacetNode:
                            show = self.infoFacet
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
    def __init__(self, *args):
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
    def __init__(self, *args):
        """
        Initialize the key.
        """
        super().__init__(*args)
        self.setFixedSize(88, 20)


class Button(QtWidgets.QPushButton):
    """
    This class implements the button to which associate a QtWidgets.QMenu instance of an info field.
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
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setScrollEnabled(False)


class Parent(QtWidgets.QWidget):
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

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
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
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)

        self.versionKey = Key('Version', self)
        self.versionKey.setFont(Font('Roboto', 12))
        self.versionField = String(self)
        self.versionField.setFont(Font('Roboto', 12))
        self.versionField.setReadOnly(True)
        connect(self.versionField.editingFinished, self.versionEditingFinished)

        self.prefixKey = Key('Prefix', self)
        self.prefixKey.setFont(Font('Roboto', 12))
        self.prefixField = String(self)
        self.prefixField.setFont(Font('Roboto', 12))
        self.prefixField.setReadOnly(True)
        connect(self.prefixField.editingFinished, self.prefixEditingFinished)
        """
        self.prefixesKey = Key('Prefix(es)', self)
        self.prefixesKey.setFont(Font('Roboto', 12))
        self.prefixesField = String(self)
        self.prefixesField.setFont(Font('Roboto', 12))
        #self.prefixesField.setReadOnly(True)
        connect(self.prefixesField.editingFinished, self.prefixesEditingFinished)
        """
        self.iriKey = Key('IRI', self)
        self.iriKey.setFont(Font('Roboto', 12))
        self.iriField = String(self)
        self.iriField.setFont(Font('Roboto', 12))
        self.iriField.setReadOnly(True)
        connect(self.iriField.editingFinished, self.iriEditingFinished)

        """
        self.profileKey = Key('Profile', self)
        self.profileKey.setFont(Font('Roboto', 12))
        self.profileField = Select(self)
        self.profileField.setFont(Font('Roboto', 12))
        self.profileField.addItems(self.session.profileNames())
        connect(self.profileField.activated, self.profileChanged)
        """
        self.ontologyPropHeader = Header('Ontology properties', self)
        self.ontologyPropHeader.setFont(Font('Roboto', 12))

        self.ontologyPropLayout = QtWidgets.QFormLayout()
        self.ontologyPropLayout.setSpacing(0)
        self.ontologyPropLayout.addRow(self.versionKey, self.versionField)
        self.ontologyPropLayout.addRow(self.prefixKey, self.prefixField)
        #self.ontologyPropLayout.addRow(self.prefixesKey, self.prefixesField)
        self.ontologyPropLayout.addRow(self.iriKey, self.iriField)
        #self.ontologyPropLayout.addRow(self.profileKey, self.profileField)

        self.conceptsKey = Key('Concept', self)
        self.conceptsKey.setFont(Font('Roboto', 12))
        self.conceptsField = Integer(self)
        self.conceptsField.setFont(Font('Roboto', 12))
        self.conceptsField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.conceptsField.setReadOnly(True)

        self.rolesKey = Key('Role', self)
        self.rolesKey.setFont(Font('Roboto', 12))
        self.rolesField = Integer(self)
        self.rolesField.setFont(Font('Roboto', 12))
        self.rolesField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rolesField.setReadOnly(True)

        self.attributesKey = Key('Attribute', self)
        self.attributesKey.setFont(Font('Roboto', 12))
        self.attributesField = Integer(self)
        self.attributesField.setFont(Font('Roboto', 12))
        self.attributesField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.attributesField.setReadOnly(True)

        self.inclusionsKey = Key('Inclusion', self)
        self.inclusionsKey.setFont(Font('Roboto', 12))
        self.inclusionsField = Integer(self)
        self.inclusionsField.setFont(Font('Roboto', 12))
        self.inclusionsField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.inclusionsField.setReadOnly(True)

        self.membershipKey = Key('Membership', self)
        self.membershipKey.setFont(Font('Roboto', 12))
        self.membershipField = Integer(self)
        self.membershipField.setFont(Font('Roboto', 12))
        self.membershipField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.membershipField.setReadOnly(True)

        self.atomicPredHeader = Header('Atomic predicates', self)
        self.atomicPredHeader.setFont(Font('Roboto', 12))

        self.atomicPredLayout = QtWidgets.QFormLayout()
        self.atomicPredLayout.setSpacing(0)
        self.atomicPredLayout.addRow(self.conceptsKey, self.conceptsField)
        self.atomicPredLayout.addRow(self.rolesKey, self.rolesField)
        self.atomicPredLayout.addRow(self.attributesKey, self.attributesField)

        self.assertionsHeader = Header('Assertions', self)
        self.assertionsHeader.setFont(Font('Roboto', 12))

        self.assertionsLayout = QtWidgets.QFormLayout()
        self.assertionsLayout.setSpacing(0)
        self.assertionsLayout.addRow(self.inclusionsKey, self.inclusionsField)
        self.assertionsLayout.addRow(self.membershipKey, self.membershipField)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.ontologyPropHeader)
        self.mainLayout.addLayout(self.ontologyPropLayout)
        self.mainLayout.addWidget(self.atomicPredHeader)
        self.mainLayout.addLayout(self.atomicPredLayout)
        self.mainLayout.addWidget(self.assertionsHeader)
        self.mainLayout.addLayout(self.assertionsLayout)

        self.ENTRY_MODIFIED_OK_var = set()
        self.ENTRY_IGNORE_var = set()

        #connect(self.project.sgnIRIPrefixesEntryModified, self.entry_MODIFIED_ok)
        #connect(self.project.sgnIRIPrefixesEntryIgnored, self.entry_NOT_OK)


    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(str, str, str, str)
    def entry_MODIFIED_ok(self, iri_from, prefixes_from, iri_to, prefixes_to):

        self.ENTRY_MODIFIED_OK_var.add(True)
        #print('entry_ADD_ok(self): ', iri_from, ',', prefixes_from, ',', iri_to, ',',prefixes_to)

    @QtCore.pyqtSlot(str, str, str)
    def entry_NOT_OK(self, iri, prefix, message):

        self.ENTRY_IGNORE_var.add(True)
        #print('entry_NOT_OK(self): ', iri, ',', prefix, ',', message)

    @QtCore.pyqtSlot()
    def iriEditingFinished(self):
        """
        Executed whenever we finish to edit the ontology prefix
        """
        new_iri = self.iriField.value()

        if new_iri == '':
            self.session.statusBar().showMessage('IRI field is blank.', 15000)
            self.updateData(self.project)
            return

        IRI_valid = self.project.check_validity_of_IRI(new_iri)

        if(IRI_valid is False):
            self.session.statusBar().showMessage('IRI is invalid.', 15000)
            self.updateData(self.project)
            return

        if (self.project.iri != new_iri) and (new_iri != ''):
            #self.session.undostack.push(CommandProjectSetIRI(self.project, self.project.iri, iri))

            self.ENTRY_MODIFIED_OK_var = set()
            self.ENTRY_IGNORE_var = set()

            connect(self.project.sgnIRIPrefixesEntryModified, self.entry_MODIFIED_ok)
            connect(self.project.sgnIRIPrefixesEntryIgnored, self.entry_NOT_OK)

            Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())
            Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())

            self.project.modifyIRIPrefixesEntry(self.project.iri, None, new_iri, None, Duplicate_dict_1)
            if (True in self.ENTRY_MODIFIED_OK_var) and (True not in self.ENTRY_IGNORE_var):
                self.ENTRY_MODIFIED_OK_var = set()
                self.ENTRY_IGNORE_var = set()

                command = CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1, [self.project.iri, new_iri], None)
                self.session.undostack.push(command)

            self.ENTRY_MODIFIED_OK_var = set()
            self.ENTRY_IGNORE_var = set()

        self.iriField.clearFocus()

    @QtCore.pyqtSlot()
    def prefixEditingFinished(self):
        """
        Executed whenever we finish to edit the ontology prefix
        """
        prefix_in_field = self.prefixField.value().strip()

        flag = False


        for c in prefix_in_field:
            if c == '':
                pass
            elif (not c.isalnum()):
                flag = True
                break
            else:
                pass

        if prefix_in_field == '':
            self.session.statusBar().showMessage('Prefix field is blank.', 15000)
            self.updateData(self.project)
            return

        if flag is True:
            self.session.statusBar().showMessage(
                '(Spaces in between alphanumeric characters) and (special characters) are not allowed in a prefix.',
                15000)
            self.updateData(self.project)
            return
        else:

            if self.project.prefix != prefix_in_field:
                # self.session.undostack.push(CommandProjectSetPrefix(self.project, self.project.prefix, prefix))

                prefixes_of_project = self.project.prefixes

                commands = []

                Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(
                    self.project.IRI_prefixes_nodes_dict, dict())
                Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(
                    self.project.IRI_prefixes_nodes_dict, dict())

                if prefix_in_field in prefixes_of_project:

                    #just change the order
                    new_order = []
                    new_order.extend(prefixes_of_project)
                    new_order.remove(prefix_in_field)
                    new_order.append(prefix_in_field)

                    Duplicate_dict_1[self.project.iri][0] = new_order

                    command_1 = CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2,
                                                                     Duplicate_dict_1,
                                                                     [self.project.iri], None)

                    commands.append(command_1)

                else:

                    #try to append (prefix_in_field) to (prefixes_of_project)

                    self.ENTRY_MODIFIED_OK_var = set()
                    self.ENTRY_IGNORE_var = set()

                    connect(self.project.sgnIRIPrefixesEntryModified, self.entry_MODIFIED_ok)
                    connect(self.project.sgnIRIPrefixesEntryIgnored, self.entry_NOT_OK)

                    prefixes_new = []
                    prefixes_new.extend(prefixes_of_project)
                    prefixes_new.append(prefix_in_field)

                    self.project.modifyIRIPrefixesEntry(self.project.iri, prefixes_of_project, self.project.iri,
                                                        prefixes_new, Duplicate_dict_1)

                    # self.project.print_dictionary(Duplicate_dict_1)

                    if (True in self.ENTRY_MODIFIED_OK_var) and (True not in self.ENTRY_IGNORE_var):
                        self.ENTRY_MODIFIED_OK_var = set()
                        self.ENTRY_IGNORE_var = set()

                        command_1 = CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2,
                                                                         Duplicate_dict_1,
                                                                         [self.project.iri], None)

                        commands.append(command_1)

                    self.ENTRY_MODIFIED_OK_var = set()
                    self.ENTRY_IGNORE_var = set()

                if commands:
                    if len(commands) > 1:
                        self.session.undostack.beginMacro('change the depth of {0} nodes'.format(len(commands)))
                        for command in commands:
                            self.session.undostack.push(command)
                        self.session.undostack.endMacro()
                    else:
                        self.session.undostack.push(first(commands))

        self.prefixField.clearFocus()

    # not used
    @QtCore.pyqtSlot()
    def prefixEditingFinished_2(self):
        """
        Executed whenever we finish to edit the ontology prefix
        """
        prefix_in_field = self.prefixField.value().strip()

        flag = False

        for c in prefix_in_field:
            if c == '':
                pass
            elif (not c.isalnum()):
                flag = True
                break
            else:
                pass

        if flag is True:
            self.session.statusBar().showMessage(
                'Spaces in between alphanumeric characters and special characters are not allowed in a prefix.',
                15000)
        else:

            if self.project.prefix != prefix_in_field:
                #self.session.undostack.push(CommandProjectSetPrefix(self.project, self.project.prefix, prefix))

                prefixes_of_project = self.project.prefixes

                commands = []

                if prefix_in_field in prefixes_of_project:

                    Duplicate_dict_1B = self.project.copy_prefered_prefix_dictionaries( \
                        self.project.prefered_prefix_dict, dict())
                    Duplicate_dict_2B = self.project.copy_prefered_prefix_dictionaries( \
                        self.project.prefered_prefix_dict, dict())

                    Duplicate_dict_1B[self.project.iri] = prefix_in_field

                    nodes_corr_project_iri = self.project.IRI_prefixes_nodes_dict[self.project.iri][1]

                    for node in nodes_corr_project_iri:
                        Duplicate_dict_1B[str(node)] = prefix_in_field

                    command = CommandProjectORNodeSetPreferedPrefix(self.project, Duplicate_dict_2B, Duplicate_dict_1B,\
                                                        self.project.iri, None)

                    commands.append(command)

                else:

                    self.ENTRY_MODIFIED_OK_var = set()
                    self.ENTRY_IGNORE_var = set()

                    connect(self.project.sgnIRIPrefixesEntryModified, self.entry_MODIFIED_ok)
                    connect(self.project.sgnIRIPrefixesEntryIgnored, self.entry_NOT_OK)

                    Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(
                        self.project.IRI_prefixes_nodes_dict, dict())
                    Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(
                        self.project.IRI_prefixes_nodes_dict, dict())

                    prefixes_new = set()
                    prefixes_new = prefixes_new.union(prefixes_of_project)
                    prefixes_new.add(prefix_in_field)

                    self.project.modifyIRIPrefixesEntry(self.project.iri, prefixes_of_project, self.project.iri,
                                                        prefixes_new, Duplicate_dict_1)

                    # self.project.print_dictionary(Duplicate_dict_1)

                    if (True in self.ENTRY_MODIFIED_OK_var) and (True not in self.ENTRY_IGNORE_var):
                        self.ENTRY_MODIFIED_OK_var = set()
                        self.ENTRY_IGNORE_var = set()

                        command_1 = CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1,
                                                                       [self.project.iri], None)

                        Duplicate_dict_1B = self.project.copy_prefered_prefix_dictionaries(\
                            self.project.prefered_prefix_dict, dict())
                        Duplicate_dict_2B = self.project.copy_prefered_prefix_dictionaries( \
                            self.project.prefered_prefix_dict, dict())

                        nodes_corr_project_iri = Duplicate_dict_1[self.project.iri][1]

                        Duplicate_dict_1B[self.project.iri] = prefix_in_field
                        for node in nodes_corr_project_iri:
                            Duplicate_dict_1B[str(node)] = prefix_in_field

                        command_2 = CommandProjectORNodeSetPreferedPrefix(self.project, Duplicate_dict_2B, Duplicate_dict_1B,\
                                                        self.project.iri, None)

                        commands.append(command_1)
                        commands.append(command_2)

                    self.ENTRY_MODIFIED_OK_var = set()
                    self.ENTRY_IGNORE_var = set()


                if commands:
                    if len(commands) > 1:
                        self.session.undostack.beginMacro('change the depth of {0} nodes'.format(len(commands)))
                        for command in commands:
                            self.session.undostack.push(command)
                        self.session.undostack.endMacro()
                    else:
                        self.session.undostack.push(first(commands))

        self.prefixField.clearFocus()

    #not used
    @QtCore.pyqtSlot()
    def prefixesEditingFinished(self):
        """
        Executed whenever we finish to edit the ontology prefix
        """
        prefixes_str = self.prefixesField.value()

        prefixes_new = set()

        prefixes_str_split = prefixes_str.split(', ')

        for p in prefixes_str_split:
            if p !='':
                prefixes_new.add(p)

        if (self.project.prefixes.issubset(prefixes_new)) and (prefixes_new.issubset(self.project.prefixes)) :
            #do nothing
            pass
        else:
            self.ENTRY_MODIFIED_OK_var = set()
            self.ENTRY_IGNORE_var = set()

            connect(self.project.sgnIRIPrefixesEntryModified, self.entry_MODIFIED_ok)
            connect(self.project.sgnIRIPrefixesEntryIgnored, self.entry_NOT_OK)

            Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())
            Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())

            self.project.modifyIRIPrefixesEntry(self.project.iri,self.project.prefixes,self.project.iri,prefixes_new,Duplicate_dict_1)

            #self.project.print_dictionary(Duplicate_dict_1)

            if (True in self.ENTRY_MODIFIED_OK_var) and (True not in self.ENTRY_IGNORE_var):
                self.ENTRY_MODIFIED_OK_var = set()
                self.ENTRY_IGNORE_var = set()

                command = CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1, [self.project.iri], None)
                self.session.undostack.push(command)

            self.ENTRY_MODIFIED_OK_var = set()
            self.ENTRY_IGNORE_var = set()

        self.prefixesField.clearFocus()

    @QtCore.pyqtSlot()
    def profileChanged(self):
        """
        Executed when we need to change the project profile.
        """
        profile = self.profileField.currentText()
        if self.project.profile.name() != profile:
            self.session.undostack.push(CommandProjectSetProfile(self.project, self.project.profile.name(), profile))
        self.profileField.clearFocus()

    @QtCore.pyqtSlot()
    def versionEditingFinished(self):
        """
        Executed whenever we finish to edit the ontology prefix
        """
        version = self.versionField.value()
        if self.project.version != version:
            self.session.undostack.push(CommandProjectSetVersion(self.project, self.project.version, version))
        #self.iriField.clearFocus()
        self.versionField.clearFocus()
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
        """
        prefixes_str_to_set = ''
        project_prefixes = project.prefixes
        if project_prefixes is None:
            self.prefixesField.setValue('')
        else:
            for p in project_prefixes:
                prefixes_str_to_set = prefixes_str_to_set+p+', '

            prefixes_str_to_set = prefixes_str_to_set[0:len(prefixes_str_to_set)-2]
            self.prefixesField.setValue(prefixes_str_to_set)
        
        self.prefixesField.home(True)
        self.prefixesField.clearFocus()
        self.prefixesField.deselect()
        """
        self.iriField.setValue(project.iri)
        self.iriField.home(True)
        self.iriField.clearFocus()
        self.iriField.deselect()

        self.versionField.setValue(project.version)
        self.versionField.home(True)
        self.versionField.clearFocus()
        self.versionField.deselect()

        """
        for i in range(self.profileField.count()):
            if self.profileField.itemText(i) == self.project.profile.name():
                self.profileField.setCurrentIndex(i)
                break
        """

        self.attributesField.setValue(project.predicateNum(Item.AttributeNode))
        self.conceptsField.setValue(project.predicateNum(Item.ConceptNode))
        self.rolesField.setValue(project.predicateNum(Item.RoleNode))
        self.inclusionsField.setValue(project.itemNum(Item.InclusionEdge))
        self.membershipField.setValue(project.itemNum(Item.MembershipEdge))


class EdgeInfo(AbstractInfo):
    """
    This class implements the information box for generic edges.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the generic edge information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)

        self.h1 = Header('General', self)
        self.h1.setFont(Font('Roboto', 12))

        self.typeKey = Key('Type', self)
        self.typeKey.setFont(Font('Roboto', 12))
        self.typeField = String(self)
        self.typeField.setFont(Font('Roboto', 12))
        self.typeField.setReadOnly(True)

        self.sourceKey = Key('Source', self)
        self.sourceKey.setFont(Font('Roboto', 12))
        self.sourceField = String(self)
        self.sourceField.setFont(Font('Roboto', 12))
        self.sourceField.setReadOnly(True)

        self.targetKey = Key('Target', self)
        self.targetKey.setFont(Font('Roboto', 12))
        self.targetField = String(self)
        self.targetField.setFont(Font('Roboto', 12))
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


class NodeInfo(AbstractInfo):
    """
    This class implements the information box for generic nodes.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the generic node information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)

        self.node = None

        self.idKey = Key('ID', self)
        self.idKey.setFont(Font('Roboto', 12))
        self.idField = String(self)
        self.idField.setFont(Font('Roboto', 12))
        self.idField.setReadOnly(True)

        self.identityKey = Key('Identity', self)
        self.identityKey.setFont(Font('Roboto', 12))
        self.identityField = String(self)
        self.identityField.setFont(Font('Roboto', 12))
        self.identityField.setReadOnly(True)

        self.nodePropHeader = Header('Node properties', self)
        self.nodePropHeader.setFont(Font('Roboto', 12))
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

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        self.idField.setValue(node.id)
        self.identityField.setValue(node.identityName)
        self.node = node


class PredicateNodeInfo(NodeInfo):
    """
    This class implements the information box for predicate nodes.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the predicate node information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)

        self.textKey = Key('Label', self)
        self.textKey.setFont(Font('Roboto', 12))
        self.textField = String(self)
        self.textField.setFont(Font('Roboto', 12))
        #self.textField.setReadOnly(False)
        self.textField.setReadOnly(True)
        connect(self.textField.editingFinished, self.editingFinished)

        self.brushKey = Key('Color', self)
        self.brushKey.setFont(Font('Roboto', 12))
        self.brushMenu = QtWidgets.QMenu(self)
        self.brushButton = Button()
        self.brushButton.setFont(Font('Roboto', 12))
        self.brushButton.setMenu(self.brushMenu)
        self.brushButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self.nodePropLayout.addRow(self.brushKey, self.brushButton)
        #self.nodePropLayout.addRow(self.textKey, self.textField)

        self.nameKey = Key('Name', self)
        self.nameKey.setFont(Font('Roboto', 12))
        self.nameField = String(self)
        self.nameField.setFont(Font('Roboto', 12))
        #self.nameField.setReadOnly(False)
        self.nameField.setReadOnly(True)
        connect(self.nameField.editingFinished, self.editingFinished)

        self.predPropHeader = Header('Predicate properties', self)
        self.predPropHeader.setFont(Font('Roboto', 12))
        self.predPropLayout = QtWidgets.QFormLayout()
        self.predPropLayout.setSpacing(0)
        self.predPropLayout.addRow(self.nameKey, self.nameField)

        self.mainLayout.insertWidget(0, self.predPropHeader)
        self.mainLayout.insertLayout(1, self.predPropLayout)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
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
                            self.session.undostack.push(CommandLabelChange(n.diagram, n, n.text(), data, refactor=True))
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
            brush = QtGui.QBrush(QtGui.QColor(color.value))
            if node.brush() == brush:
                self.brushButton.setIcon(BrushIcon(12, 12, color.value, '#000000'))
                self.brushButton.setText(color.value)
                break

        #############################################
        # NAME / TEXT FIELDS
        #################################

        self.nameField.setValue(node.text().replace('\n',''))
        self.nameField.home(True)
        self.nameField.deselect()
        self.textField.setValue(node.text().replace('\n',''))
        self.textField.home(True)
        self.textField.deselect()

        #############################################
        # ENABLE / DISABLE REFACTORING
        #################################

        refactor = True
        #if node.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode}:
        if (('AttributeNode' in str(type(node))) or ('ConceptNode' in str(type(node))) or ('RoleNode' in str(type(node)))):
            if node.special() is not None:
                refactor = False
        #self.nameField.setReadOnly(not refactor)


class AttributeNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Attribute node.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the Attribute node information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)

        self.functKey = Key('Funct.', self)
        self.functKey.setFont(Font('Roboto', 12))
        functParent = Parent(self)
        self.functBox = CheckBox(functParent)
        self.functBox.setCheckable(True)
        self.functBox.setFont(Font('Roboto', 12))
        self.functBox.setProperty('key', K_FUNCTIONAL)
        connect(self.functBox.clicked, self.flagChanged)

        self.predPropLayout.addRow(self.functKey, functParent)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def flagChanged(self):
        """
        Executed whenever one of the property fields changes.
        """
        sender = self.sender()
        checked = sender.isChecked()
        key = sender.property('key')
        undo = self.project.meta(self.node.type(), self.node.text())
        redo = undo.copy()
        redo[key] = checked
        if redo != undo:
            prop = RE_CAMEL_SPACE.sub('\g<1> \g<2>', key).lower()
            name = "{0}set '{1}' {2} property".format('' if checked else 'un', self.node.text(), prop)
            self.session.undostack.push(
                CommandNodeSetMeta(
                    self.project,
                    self.node.type(),
                    self.node.text(),
                    undo, redo, name))

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)
        self.functBox.setChecked(node.isFunctional())

        #enable if already checked and profile is not OWLProfile.OWL2QL

        condition = self.functBox.isChecked() or (self.project.profile.type() is not OWLProfile.OWL2QL)

        self.functBox.setEnabled(condition)
        self.functKey.setEnabled(condition)
        #self.functBox.setEnabled(self.project.profile.type() is not OWLProfile.OWL2QL)
        #self.functKey.setEnabled(self.project.profile.type() is not OWLProfile.OWL2QL)
        #self.functBox.setEnabled(True)
        #self.functKey.setEnabled(True)

class RoleNodeInfo(PredicateNodeInfo):
    """
    This class implements the information box for the Role node.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the Role node information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)

        self.functKey = Key('Funct.', self)
        self.functKey.setFont(Font('Roboto', 12))
        functParent = Parent(self)
        self.functBox = CheckBox(functParent)
        self.functBox.setCheckable(True)
        self.functBox.setFont(Font('Roboto', 12))
        self.functBox.setProperty('key', K_FUNCTIONAL)
        connect(self.functBox.clicked, self.flagChanged)

        self.invFunctKey = Key('Inv. Funct.', self)
        self.invFunctKey.setFont(Font('Roboto', 12))
        invFunctParent = Parent(self)
        self.invFunctBox = CheckBox(invFunctParent)
        self.invFunctBox.setCheckable(True)
        self.invFunctBox.setFont(Font('Roboto', 12))
        self.invFunctBox.setProperty('key', K_INVERSE_FUNCTIONAL)
        connect(self.invFunctBox.clicked, self.flagChanged)

        self.asymmetricKey = Key('Asymmetric', self)
        self.asymmetricKey.setFont(Font('Roboto', 12))
        asymmetricParent = Parent(self)
        self.asymmetricBox = CheckBox(asymmetricParent)
        self.asymmetricBox.setCheckable(True)
        self.asymmetricBox.setFont(Font('Roboto', 12))
        self.asymmetricBox.setProperty('key', K_ASYMMETRIC)
        connect(self.asymmetricBox.clicked, self.flagChanged)

        self.irreflexiveKey = Key('Irreflexive', self)
        self.irreflexiveKey.setFont(Font('Roboto', 12))
        irreflexiveParent = Parent(self)
        self.irreflexiveBox = CheckBox(irreflexiveParent)
        self.irreflexiveBox.setCheckable(True)
        self.irreflexiveBox.setFont(Font('Roboto', 12))
        self.irreflexiveBox.setProperty('key', K_IRREFLEXIVE)
        connect(self.irreflexiveBox.clicked, self.flagChanged)

        self.reflexiveKey = Key('Reflexive', self)
        self.reflexiveKey.setFont(Font('Roboto', 12))
        reflexiveParent = Parent(self)
        self.reflexiveBox = CheckBox(reflexiveParent)
        self.reflexiveBox.setCheckable(True)
        self.reflexiveBox.setFont(Font('Roboto', 12))
        self.reflexiveBox.setProperty('key', K_REFLEXIVE)
        connect(self.reflexiveBox.clicked, self.flagChanged)

        self.symmetricKey = Key('Symmetric', self)
        self.symmetricKey.setFont(Font('Roboto', 12))
        symmetricParent = Parent(self)
        self.symmetricBox = CheckBox(symmetricParent)
        self.symmetricBox.setCheckable(True)
        self.symmetricBox.setFont(Font('Roboto', 12))
        self.symmetricBox.setProperty('key', K_SYMMETRIC)
        connect(self.symmetricBox.clicked, self.flagChanged)

        self.transitiveKey = Key('Transitive', self)
        self.transitiveKey.setFont(Font('Roboto', 12))
        transitiveParent = Parent(self)
        self.transitiveBox = CheckBox(transitiveParent)
        self.transitiveBox.setCheckable(True)
        self.transitiveBox.setFont(Font('Roboto', 12))
        self.transitiveBox.setProperty('key', K_TRANSITIVE)
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

    @QtCore.pyqtSlot()
    def flagChanged(self):
        """
        Executed whenever one of the property fields changes.
        """
        sender = self.sender()
        checked = sender.isChecked()
        key = sender.property('key')
        undo = self.project.meta(self.node.type(), self.node.text())
        redo = undo.copy()
        redo[key] = checked
        if redo != undo:
            prop = RE_CAMEL_SPACE.sub('\g<1> \g<2>', key).lower()
            name = "{0}set '{1}' {2} property".format('' if checked else 'un', self.node.text(), prop)
            self.session.undostack.push(
                CommandNodeSetMeta(
                    self.project,
                    self.node.type(),
                    self.node.text(),
                    undo, redo, name))

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, node):
        """
        Fetch new information and fill the widget with data.
        :type node: AbstractNode
        """
        super().updateData(node)

        self.asymmetricBox.setChecked(node.isAsymmetric())

        self.functBox.setChecked(node.isFunctional())
        condition_funct = self.functBox.isChecked() or (self.project.profile.type() is not OWLProfile.OWL2QL)
        #self.functBox.setEnabled(self.project.profile.type() is not OWLProfile.OWL2QL)
        #self.functKey.setEnabled(self.project.profile.type() is not OWLProfile.OWL2QL)
        self.functBox.setEnabled(condition_funct)
        self.functKey.setEnabled(condition_funct)

        self.invFunctBox.setChecked(node.isInverseFunctional())
        condition_invfunct = self.invFunctBox.isChecked() or (self.project.profile.type() is not OWLProfile.OWL2QL)
        #self.invFunctBox.setEnabled(self.project.profile.type() is not OWLProfile.OWL2QL)
        #self.invFunctKey.setEnabled(self.project.profile.type() is not OWLProfile.OWL2QL)
        self.invFunctBox.setEnabled(condition_invfunct)
        self.invFunctKey.setEnabled(condition_invfunct)

        self.irreflexiveBox.setChecked(node.isIrreflexive())

        self.reflexiveBox.setChecked(node.isReflexive())
        condition_reflexive = self.reflexiveBox.isChecked() or (self.project.profile.type() is not OWLProfile.OWL2RL)
        #self.reflexiveBox.setEnabled(self.project.profile.type() is not OWLProfile.OWL2RL)
        #self.reflexiveKey.setEnabled(self.project.profile.type() is not OWLProfile.OWL2RL)
        self.reflexiveBox.setEnabled(condition_reflexive)
        self.reflexiveKey.setEnabled(condition_reflexive)

        self.symmetricBox.setChecked(node.isSymmetric())

        self.transitiveBox.setChecked(node.isTransitive())
        condition_transitive = self.transitiveBox.isChecked() or (self.project.profile.type() is not OWLProfile.OWL2QL)
        #self.transitiveBox.setEnabled(self.project.profile.type() is not OWLProfile.OWL2QL)
        #self.transitiveKey.setEnabled(self.project.profile.type() is not OWLProfile.OWL2QL)
        self.transitiveBox.setEnabled(condition_transitive)
        self.transitiveKey.setEnabled(condition_transitive)

class ValueDomainNodeInfo(NodeInfo):
    """
    This class implements the information box for the Value Domain node.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the Value Domain node information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)
        self.datatypeKey = Key('Datatype', self)
        self.datatypeKey.setFont(Font('Roboto', 12))
        self.datatypeField = Select(self)
        self.datatypeField.setFont(Font('Roboto', 12))
        connect(self.datatypeField.activated, self.datatypeChanged)
        self.nodePropLayout.addRow(self.datatypeKey, self.datatypeField)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def datatypeChanged(self):
        """
        Executed when we need to change the datatype.
        """
        if self.node:
            node = self.node
            diagram = node.diagram
            datatype = self.datatypeField.currentData()
            data = datatype.value
            if node.text() != data:
                name = 'change {0} to {1}'.format(node.shortName, data)
                self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))
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
        self.datatypeField.clear()
        for datatype in sorted(Datatype.forProfile(self.project.profile.type()), key=attrgetter('value')):
            self.datatypeField.addItem(datatype.value, datatype)
        self.datatypeField.setCurrentText(node.datatype.value)


class ValueNodeInfo(NodeInfo):
    """
    This class implements the information box for the Individual node with identity 'Value'.
    """
    def __init__(self, session, parent=None):
        """
        Initialize the Value node information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)
        self.datatypeKey = Key('Datatype', self)
        self.datatypeKey.setFont(Font('Roboto', 12))
        self.datatypeField = Select(self)
        self.datatypeField.setFont(Font('Roboto', 12))
        connect(self.datatypeField.activated, self.valueChanged)
        self.valueKey = Key('Value', self)
        self.valueKey.setFont(Font('Roboto', 12))
        self.valueField = String(self)
        self.valueField.setFont(Font('Roboto', 12))
        self.valueField.setReadOnly(False)
        connect(self.valueField.editingFinished, self.valueChanged)
        self.nodePropLayout.addRow(self.datatypeKey, self.datatypeField)
        self.nodePropLayout.addRow(self.valueKey, self.valueField)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def valueChanged(self):
        """
        Executed when we need to recompute the Value.
        """
        if self.node:

            try:
                node = self.node
                diagram = node.diagram
                datatype = self.datatypeField.currentData()
                value = self.valueField.value()
                data = node.compose(value, datatype)
                if node.text() != data:
                    name = 'change value to {0}'.format(data)
                    self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))
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

        self.datatypeField.clear()
        for datatype in sorted(Datatype.forProfile(self.project.profile.type()), key=attrgetter('value')):
            self.datatypeField.addItem(datatype.value, datatype)
        self.datatypeField.setCurrentText(node.datatype.value)

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
        :type parent: QtWidgets.QWidget
        """
        super().__init__(session, parent)

        self.facetKey = Key('Facet', self)
        self.facetKey.setFont(Font('Roboto', 12))
        self.facetField = Select(self)
        self.facetField.setFont(Font('Roboto', 12))
        connect(self.facetField.activated, self.facetChanged)

        self.valueKey = Key('Value', self)
        self.valueKey.setFont(Font('Roboto', 12))
        self.valueField = String(self)
        self.valueField.setFont(Font('Roboto', 12))
        self.valueField.setReadOnly(False)
        connect(self.valueField.editingFinished, self.facetChanged)

        self.nodePropLayout.addRow(self.facetKey, self.facetField)
        self.nodePropLayout.addRow(self.valueKey, self.valueField)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def facetChanged(self):
        """
        Executed when we need to recompute the value of the node.
        """
        if self.node:
            node = self.node
            diagram = node.diagram
            data = node.compose(self.facetField.currentData(), self.valueField.value())
            if node.text() != data:
                name = 'change {0} to {1}'.format(node.text(), data)
                self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))

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