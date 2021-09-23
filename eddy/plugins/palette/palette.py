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


from math import (
    ceil,
    cos,
    pi as M_PI,
    sin,
    sqrt,
)

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.datatypes.owl import (
    Facet,
    OWLProfile,
)
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import (
    connect,
    disconnect,
)
from eddy.core.plugin import AbstractPlugin
from eddy.ui.dock import DockWidget


class PalettePlugin(AbstractPlugin):
    """
    This plugin provides the Graphol palette for Eddy.
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

    @QtCore.pyqtSlot()
    def doActivatePalette(self):
        """
        Activate palette buttons.
        """
        profile = self.project.profile.type()
        widget = self.widget('palette')
        widget.button(Item.UnionNode).setEnabled(profile is not OWLProfile.OWL2QL)
        widget.button(Item.DisjointUnionNode).setEnabled(profile is not OWLProfile.OWL2QL)
        widget.button(Item.DatatypeRestrictionNode).setEnabled(profile not in {OWLProfile.OWL2QL, OWLProfile.OWL2RL})
        widget.button(Item.FacetNode).setEnabled(profile not in {OWLProfile.OWL2QL, OWLProfile.OWL2RL})
        widget.button(Item.EnumerationNode).setEnabled(profile is not OWLProfile.OWL2QL)
        widget.button(Item.RoleChainNode).setEnabled(profile is not OWLProfile.OWL2QL)
        widget.button(Item.SameEdge).setEnabled(profile is not OWLProfile.OWL2QL)
        widget.button(Item.HasKeyNode).setEnabled(profile is not OWLProfile.OWL2QL)

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene)
    def onDiagramAdded(self, diagram):
        """
        Executed when a diagram is added to the project.
        :typw diagram: Diagram
        """
        self.debug('Connecting to diagram: %s', diagram.name)
        connect(diagram.sgnItemInsertionCompleted, self.onDiagramItemInsertionCompleted)
        connect(diagram.sgnModeChanged, self.onDiagramModeChanged)

    @QtCore.pyqtSlot(QtWidgets.QGraphicsItem, int)
    def onDiagramItemInsertionCompleted(self, _, modifiers):
        """
        Executed after an item MANUAL insertion process ends (not triggered for item added programmatically).
        :type _: AbstractItem
        :type modifiers: int
        """
        diagram = self.session.mdi.activeDiagram()
        if diagram:
            if not modifiers & QtCore.Qt.ControlModifier:
                self.widget('palette').reset()
                diagram.setMode(DiagramMode.Idle)

    @QtCore.pyqtSlot(DiagramMode)
    def onDiagramModeChanged(self, mode):
        """
        Executed when the diagram operational mode changes.
        :type mode: DiagramMode
        """
        if mode not in (DiagramMode.NodeAdd, DiagramMode.EdgeAdd):
            self.widget('palette').reset()

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene)
    def onDiagramRemoved(self, diagram):
        """
        Executed when a diagram is removed to the project.
        :typw diagram: Diagram
        """
        self.debug('Disconnecting from diagram: %s', diagram.name)
        disconnect(diagram.sgnItemInsertionCompleted, self.onDiagramItemInsertionCompleted)
        disconnect(diagram.sgnModeChanged, self.onDiagramModeChanged)

    @QtCore.pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        connect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        connect(self.project.sgnUpdated, self.doActivatePalette)
        for diagram in self.project.diagrams():
            self.debug('Connecting to diagram: %s', diagram.name)
            connect(diagram.sgnItemInsertionCompleted, self.onDiagramItemInsertionCompleted)
            connect(diagram.sgnModeChanged, self.onDiagramModeChanged)

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM ALL THE DIAGRAMS
        for diagram in self.project.diagrams():
            self.debug('Disconnecting from diagrams: %s', diagram.name)
            disconnect(diagram.sgnItemInsertionCompleted, self.onDiagramItemInsertionCompleted)
            disconnect(diagram.sgnModeChanged, self.onDiagramModeChanged)

        # DISCONNECT FROM CURRENT PROJECT
        self.debug('Disconnecting from project: %s', self.project.name)
        disconnect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        disconnect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        disconnect(self.project.sgnUpdated, self.doActivatePalette)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnReady, self.onSessionReady)

        # REMOVE DOCKING AREA WIDGET MENU ENTRY
        self.debug('Removing docking area widget toggle from "view" menu')
        menu = self.session.menu('view')
        menu.removeAction(self.widget('palette_dock').toggleViewAction())

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling docking area widget')
        self.session.removeDockWidget(self.widget('palette_dock'))

    # noinspection PyArgumentList
    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Creating palette widget')
        widget = PaletteWidget(self)
        widget.setObjectName('palette')
        self.addWidget(widget)

        # CREATE TOGGLE ACTIONS
        self.debug('Creating palette toggle actions')
        group = QtWidgets.QActionGroup(self, objectName='palette_toggle')
        group.setExclusive(False)
        for item in widget.items:
            action = QtWidgets.QAction(item.realName.title(), group, objectName=item.name, checkable=True)
            action.setChecked(widget.display[item])
            action.setData(item)
            connect(action.triggered, widget.onMenuButtonClicked)
            group.addAction(action)
        self.addAction(group)

        # CREATE TOGGLE MENU
        self.debug('Creating palette toggle menu')
        menu = QtWidgets.QMenu(objectName='palette_toggle')
        menu.addActions(self.action('palette_toggle').actions())
        self.addMenu(menu)

        # CREATE CONTROL WIDGET
        self.debug('Creating palette toggle control widget')
        button = QtWidgets.QToolButton(objectName='palette_toggle')
        button.setIcon(QtGui.QIcon(':/icons/18/ic_settings_black'))
        button.setContentsMargins(0, 0, 0, 0)
        button.setFixedSize(18, 18)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.setMenu(self.menu('palette_toggle'))
        button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.addWidget(button)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Palette', QtGui.QIcon(':/icons/18/ic_palette_black'), self.session)
        widget.addTitleBarButton(self.widget('palette_toggle'))
        widget.installEventFilter(self)
        widget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        widget.setObjectName('palette_dock')
        widget.setWidget(self.widget('palette'))
        self.addWidget(widget)

        # CREATE SHORTCUTS
        action = widget.toggleViewAction()
        action.setParent(self.session)
        action.setShortcut(QtGui.QKeySequence('Alt+1'))

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('palette_dock').toggleViewAction())

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.widget('palette_dock'))

        # LISTEN FOR SESSION READY SIGNAL
        self.debug('Connecting to active session')
        connect(self.session.sgnReady, self.onSessionReady)
        connect(self.session.sgnReady, self.doActivatePalette)


class PaletteWidget(QtWidgets.QWidget):
    """
    This class implements the Graphol palette widget.
    """

    def __init__(self, plugin):
        """
        Initialize the palette widget.
        :type plugin: Palette
        """
        super().__init__(plugin.parent())
        self.columns = -1
        self.buttons = {}
        self.display = {}
        self.plugin = plugin
        self.items = [
            Item.ConceptNode,
            Item.RoleNode,
            Item.AttributeNode,
            Item.ValueDomainNode,
            Item.IndividualNode,
            Item.LiteralNode,
            Item.FacetNode,
            Item.DomainRestrictionNode,
            Item.RangeRestrictionNode,
            Item.IntersectionNode,
            Item.RoleChainNode,
            Item.DatatypeRestrictionNode,
            Item.RoleInverseNode,
            Item.ComplementNode,
            Item.EnumerationNode,
            Item.UnionNode,
            Item.HasKeyNode,
            Item.DisjointUnionNode,
            Item.PropertyAssertionNode,
            Item.InclusionEdge,
            Item.EquivalenceEdge,
            Item.InputEdge,
            Item.MembershipEdge,
            Item.SameEdge,
            Item.DifferentEdge
        ]
        self.shortcutPrefix = 'Shift+Alt'
        self.itemShortcuts = {
            Item.ConceptNode: '{}+c'.format(self.shortcutPrefix),
            Item.IndividualNode: '{}+i'.format(self.shortcutPrefix),
            Item.LiteralNode: '{}+i,v'.format(self.shortcutPrefix),
            Item.RoleNode: '{}+r'.format(self.shortcutPrefix),
            Item.AttributeNode: '{}+a'.format(self.shortcutPrefix),
            Item.ValueDomainNode: '{}+v'.format(self.shortcutPrefix),
            Item.FacetNode: '{}+n,f'.format(self.shortcutPrefix),
            Item.DomainRestrictionNode: '{}+n,e'.format(self.shortcutPrefix),
            Item.RangeRestrictionNode: '{}+n,g'.format(self.shortcutPrefix),
            Item.IntersectionNode: '{}+n,a'.format(self.shortcutPrefix),
            Item.RoleChainNode: '{}+n,h'.format(self.shortcutPrefix),
            Item.DatatypeRestrictionNode: '{}+n,d'.format(self.shortcutPrefix),
            Item.RoleInverseNode: '{}+n,-'.format(self.shortcutPrefix),
            Item.ComplementNode: '{}+n,n'.format(self.shortcutPrefix),
            Item.EnumerationNode: '{}+n,y'.format(self.shortcutPrefix),
            Item.UnionNode: '{}+o'.format(self.shortcutPrefix),
            Item.HasKeyNode: '{}+k'.format(self.shortcutPrefix),
            Item.DisjointUnionNode: '{}+h'.format(self.shortcutPrefix),
            Item.PropertyAssertionNode: '{}+x'.format(self.shortcutPrefix),
            Item.InclusionEdge: '{}+e,i'.format(self.shortcutPrefix),
            Item.EquivalenceEdge: '{}+e,e'.format(self.shortcutPrefix),
            Item.InputEdge: '{}+e,n'.format(self.shortcutPrefix),
            Item.MembershipEdge: '{}+e,m'.format(self.shortcutPrefix),
            Item.SameEdge: '{}+e,s'.format(self.shortcutPrefix),
            Item.DifferentEdge: '{}+e,d'.format(self.shortcutPrefix)
        }

        # CREATE BUTTONS
        for item in self.items:
            button = PaletteButton(item)
            button.installEventFilter(self)
            button.setShortcut(QtGui.QKeySequence(self.itemShortcuts[item]))
            button.setToolTip('{} ({})'.format(item.shortName, button.shortcut().toString()))
            connect(button.clicked, self.onButtonClicked)
            self.addButton(item, button)

        # LOAD BUTTONS DISPLAY SETTINGS
        settings = QtCore.QSettings()
        for item in self.items:
            self.display[item] = settings.value('plugins/palette/{0}'.format(item.name), True, bool)

        # SETUP LAYOUT
        self.mainLayout = QtWidgets.QGridLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 6, 0, 6)
        self.mainLayout.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)
        self.setStyleSheet("""
        QDockWidget PaletteWidget {
        background: #F0F0F0;
        }""")

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session.
        :rtype: Session
        """
        return self.plugin.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(Item)
    def doFocusButton(self, item):
        """
        Set the active widget to be the palette button for the specified item.
        Executed when the palette button shortcut is activated.
        TODO: Currently button shortcuts are dealt with button's internal shortcut()
        :type item: Item
        """
        button = self.buttons.get(item, None)
        if not button:
            return
        # RAISE THE PALETTE IF IT IS HIDDEN
        if not self.isVisible():
            widget = self
            while widget != self.session:
                widget.show()
                widget.raise_()
                widget = widget.parent()
        # FOCUS THE BUTTON
        if button.isEnabled():
            button.setSelected(True)
            button.setFocus()

    @QtCore.pyqtSlot()
    def onButtonClicked(self, _=False):
        """
        Executed when a button is clicked.
        """
        button = self.sender()
        self.reset(button)
        diagram = self.session.mdi.activeDiagram()
        if diagram:
            diagram.clearSelection()
            if not button.isChecked():
                diagram.setMode(DiagramMode.Idle)
            else:
                if Item.ConceptNode <= button.item < Item.InclusionEdge:
                    diagram.setMode(DiagramMode.NodeAdd, button.item)
                elif Item.InclusionEdge <= button.item <= Item.DifferentEdge:
                    diagram.setMode(DiagramMode.EdgeAdd, button.item)

    @QtCore.pyqtSlot(bool)
    def onMenuButtonClicked(self, _=False):
        """
        Executed when a button in the widget menu is clicked.
        """
        # UPDATE THE PALETTE LAYOUT
        item = self.sender().data()
        self.display[item] = not self.display[item]
        self.buttons[item].setVisible(self.display[item])
        self.redraw(mandatory=True)
        # UPDATE SETTINGS
        settings = QtCore.QSettings()
        for item in self.items:
            settings.setValue('plugins/palette/{0}'.format(item.name), self.display[item])
        settings.sync()

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
        if event.type() in {QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.MouseMove}:
            if isinstance(source, PaletteButton):
                if not self.isEnabled():
                    return True
        return super().eventFilter(source, event)

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
    #   INTERFACE
    #################################

    def addButton(self, item, button):
        """
        Add the given button to the buttons set.
        :type item: Item
        :type button: PaletteButton
        """
        self.buttons[item] = button

    def button(self, item):
        """
        Returns the button matching the given item type.
        :type item: Item
        :rtype: PaletteButton
        """
        return self.buttons[item]

    def redraw(self, mandatory=False):
        """
        Redraw the palette.
        :type mandatory: bool
        """
        items = [i for i in self.items if self.display[i]]
        columns = int((self.width() - 12) / 60)
        rows = ceil(len(items) / columns)
        if self.columns != columns or mandatory:
            self.columns = columns
            zipped = list(zip([x for x in range(rows) for _ in range(columns)], list(range(columns)) * rows))
            zipped = zipped[:len(items)]
            for i in reversed(range(self.mainLayout.count())):
                item = self.mainLayout.itemAt(i)
                self.mainLayout.removeItem(item)
            for i in range(len(zipped)):
                self.mainLayout.addWidget(self.button(items[i]), zipped[i][0], zipped[i][1])

    def reset(self, *args):
        """
        Reset the palette selection.
        :type args: Item
        """
        for button in self.buttons.values():
            if button not in args:
                button.setChecked(False)

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 342)


class PaletteButton(QtWidgets.QToolButton):
    """
    This class implements a single palette button.
    """
    def __init__(self, item):
        """
        Initialize the palette button.
        :type item: Item
        """
        super().__init__()
        self.item = item
        self.startPos = None
        self.setCheckable(True)
        self.setFocusPolicy(QtCore.Qt.TabFocus)
        self.setContentsMargins(0, 0, 0, 0)
        self.setIcon(self.iconFor(item))
        self.setIconSize(QtCore.QSize(60, 44))

    #############################################
    #   EVENTS
    #################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the button.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & QtCore.Qt.LeftButton:
            self.startPos = mouseEvent.pos()
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse if moved while a button is being pressed.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & QtCore.Qt.LeftButton:

            if Item.ConceptNode <= self.item < Item.InclusionEdge:
                distance = (mouseEvent.pos() - self.startPos).manhattanLength()
                if distance >= QtWidgets.QApplication.startDragDistance():
                    mimeData = QtCore.QMimeData()
                    mimeData.setText(str(self.item.value))
                    drag = QtGui.QDrag(self)
                    drag.setMimeData(mimeData)
                    drag.setPixmap(self.icon().pixmap(60, 40))
                    drag.setHotSpot(self.startPos - self.rect().topLeft())
                    drag.exec_(QtCore.Qt.CopyAction)

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when a mouse button is released.
        :type mouseEvent: QMouseEvent
        """
        super().mouseReleaseEvent(mouseEvent)

    def paintEvent(self, paintEvent):
        """
        Perform the painting of the button in the palette.
        :type paintEvent: QPaintEvent
        """
        icon = self.icon()
        painter = QtGui.QPainter(self)
        if self.hasFocus():
            painter.setBrush(QtGui.QBrush(QtGui.QColor(191, 202, 208)))
            painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(191, 202, 208)), 1.0))
            painter.drawRect(0, 0, 60, 44)
        if self.isChecked():
            painter.setBrush(QtGui.QBrush(QtGui.QColor(66, 165, 245)))
            painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(66, 165, 245)), 1.0))
            painter.drawRect(0, 0, 60, 44)
        painter.setOpacity(1.0 if self.isEnabled() else 0.33)
        painter.drawPixmap(0, 0, icon.pixmap(QtCore.QSize(60, 44)))

    #############################################
    #   INTERFACE
    #################################

    def iconFor(self, item):
        """
        Returns the appropriate icon for the given item.
        :type item: Item
        :rtype: QtGui.QIcon
        """
        icon = QtGui.QIcon()

        for i in (1, 2):

            pixmap = QtGui.QPixmap(60 * i, 44 * i)
            pixmap.setDevicePixelRatio(i)
            pixmap.fill(QtCore.Qt.transparent)

            #############################################
            # CONCEPT NODE
            #################################

            if item is Item.ConceptNode:
                painter = QtGui.QPainter(pixmap)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawRect(QtCore.QRectF(-27, -17, 54, 34))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-27, -17, 54, 34), QtCore.Qt.AlignCenter, 'Class')
                painter.end()

            #############################################
            # ROLE NODE
            #################################

            elif item is Item.RoleNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(0, +17),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(0, -17),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-23, -17, 46, 34), QtCore.Qt.AlignCenter, 'Obj.\nProp.')
                painter.end()

            #############################################
            # ATTRIBUTE NODE
            #################################

            elif item is Item.AttributeNode:

                painter = QtGui.QPainter(pixmap)
                painter.setFont(Font(pixelSize=9, weight=Font.Light))
                painter.translate(0, 0)
                painter.drawText(QtCore.QRectF(0, 0, 60, 22), QtCore.Qt.AlignCenter, 'Data Prop.')
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 30)
                painter.drawEllipse(QtCore.QRectF(-9, -9, 18, 18))
                painter.end()

            #############################################
            # VALUE-DOMAIN NODE
            #################################

            elif item is Item.ValueDomainNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawRoundedRect(QtCore.QRectF(-27, -17, 54, 34), 6, 6)
                painter.setFont(Font(pixelSize=10, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-27, -17, 54, 34), QtCore.Qt.AlignCenter, 'Datatype')
                painter.end()

            #############################################
            # INDIVIDUAL NODE
            #################################

            elif item is Item.IndividualNode:
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(
                    QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
                               QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-20, -((40 / (1 + sqrt(2))) / 2)),
                    QtCore.QPointF(-20, +((40 / (1 + sqrt(2))) / 2)),
                    QtCore.QPointF(-((40 / (1 + sqrt(2))) / 2), +20),
                    QtCore.QPointF(+((40 / (1 + sqrt(2))) / 2), +20),
                    QtCore.QPointF(+20, +((40 / (1 + sqrt(2))) / 2)),
                    QtCore.QPointF(+20, -((40 / (1 + sqrt(2))) / 2)),
                    QtCore.QPointF(+((40 / (1 + sqrt(2))) / 2), -20),
                    QtCore.QPointF(-((40 / (1 + sqrt(2))) / 2), -20),
                    QtCore.QPointF(-20, -((40 / (1 + sqrt(2))) / 2)),
                ]))
                painter.setFont(Font(pixelSize=9, weight=Font.Light))
                painter.drawText(-19, 4, 'individual')
                painter.end()

            #############################################
            # VALUE NODE
            #################################

            elif item is Item.LiteralNode:
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(
                    QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
                               QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-20, -((40 / (1 + sqrt(2))) / 2)),
                    QtCore.QPointF(-20, +((40 / (1 + sqrt(2))) / 2)),
                    QtCore.QPointF(-((40 / (1 + sqrt(2))) / 2), +20),
                    QtCore.QPointF(+((40 / (1 + sqrt(2))) / 2), +20),
                    QtCore.QPointF(+20, +((40 / (1 + sqrt(2))) / 2)),
                    QtCore.QPointF(+20, -((40 / (1 + sqrt(2))) / 2)),
                    QtCore.QPointF(+((40 / (1 + sqrt(2))) / 2), -20),
                    QtCore.QPointF(-((40 / (1 + sqrt(2))) / 2), -20),
                    QtCore.QPointF(-20, -((40 / (1 + sqrt(2))) / 2)),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(-12, 4, 'literal')
                painter.end()

            #############################################
            # FACET NODE
            #################################

            elif item is Item.FacetNode:

                polygonA = QtGui.QPolygonF([
                    QtCore.QPointF(-54 / 2 + 4, -32 / 2),
                    QtCore.QPointF(+54 / 2, -32 / 2),
                    QtCore.QPointF(+54 / 2 - 4 / 2, 0),
                    QtCore.QPointF(-54 / 2 + 4 / 2, 0),
                    QtCore.QPointF(-54 / 2 + 4, -32 / 2),
                ])
                polygonB = QtGui.QPolygonF([
                    QtCore.QPointF(-54 / 2 + 4 / 2, 0),
                    QtCore.QPointF(+54 / 2 - 4 / 2, 0),
                    QtCore.QPointF(+54 / 2 - 4, +32 / 2),
                    QtCore.QPointF(-54 / 2, +32 / 2),
                    QtCore.QPointF(-54 / 2 + 4 / 2, 0),
                ])
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.setBrush(QtGui.QBrush(QtGui.QColor(222, 222, 222, 255)))
                painter.drawPolygon(polygonA)
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.drawPolygon(polygonB)
                painter.setFont(Font(pixelSize=9, weight=Font.Light))
                painter.drawText(QtCore.QPointF(-20, -5), Facet.length.value)
                painter.drawText(QtCore.QPointF(-8, 12), '"32"')
                painter.end()

            #############################################
            # DOMAIN RESTRICTION NODE
            #################################

            elif item is Item.DomainRestrictionNode:

                painter = QtGui.QPainter(pixmap)
                painter.setFont(Font(pixelSize=9, weight=Font.Light))
                painter.translate(0, 0)
                painter.drawText(QtCore.QRectF(0, 0, 60, 22), QtCore.Qt.AlignCenter, 'restriction')
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawRect(QtCore.QRectF(-18 / 2, -18 / 2 + 6, 18, 18))
                painter.end()

            #############################################
            # RANGE RESTRICTION NODE
            #################################

            elif item is Item.RangeRestrictionNode:

                painter = QtGui.QPainter(pixmap)
                painter.setFont(Font(pixelSize=9, weight=Font.Light))
                painter.translate(0, 0)
                painter.drawText(QtCore.QRectF(0, 0, 60, 22), QtCore.Qt.AlignCenter, 'restriction')
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)))
                painter.translate(30, 22)
                painter.drawRect(QtCore.QRectF(-18 / 2, -18 / 2 + 6, 18, 18))
                painter.end()

            #############################################
            # INTERSECTION NODE
            #################################

            elif item is Item.IntersectionNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(-23 + 6, +15),
                    QtCore.QPointF(+23 - 6, +15),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(+23 - 6, -15),
                    QtCore.QPointF(-23 + 6, -15),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-23, -15, 46, 30), QtCore.Qt.AlignCenter, 'and')
                painter.end()

            #############################################
            # ROLE CHAIN NODE
            #################################

            elif item is Item.RoleChainNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(-23 + 6, +15),
                    QtCore.QPointF(+23 - 6, +15),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(+23 - 6, -15),
                    QtCore.QPointF(-23 + 6, -15),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-23, -15, 46, 30), QtCore.Qt.AlignCenter, 'chain')
                painter.end()

            #############################################
            # DATATYPE RESTRICTION NODE
            #################################

            elif item is Item.DatatypeRestrictionNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(-23 + 6, +15),
                    QtCore.QPointF(+23 - 6, +15),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(+23 - 6, -15),
                    QtCore.QPointF(-23 + 6, -15),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-23, -15, 46, 30), QtCore.Qt.AlignCenter, 'data')
                painter.end()

            #############################################
            # ROLE INVERSE NODE
            #################################

            elif item is Item.RoleInverseNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(-23 + 6, +15),
                    QtCore.QPointF(+23 - 6, +15),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(+23 - 6, -15),
                    QtCore.QPointF(-23 + 6, -15),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-23, -15, 46, 30), QtCore.Qt.AlignCenter, 'inv')
                painter.end()

            #############################################
            # COMPLEMENT NODE
            #################################

            elif item is Item.ComplementNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(-23 + 6, +15),
                    QtCore.QPointF(+23 - 6, +15),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(+23 - 6, -15),
                    QtCore.QPointF(-23 + 6, -15),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-23, -15, 46, 30), QtCore.Qt.AlignCenter, 'not')
                painter.end()

            #############################################
            # ENUMERATION NODE
            #################################

            elif item is Item.EnumerationNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(-23 + 6, +15),
                    QtCore.QPointF(+23 - 6, +15),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(+23 - 6, -15),
                    QtCore.QPointF(-23 + 6, -15),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-23, -15, 46, 30), QtCore.Qt.AlignCenter, 'oneOf')
                painter.end()

            #############################################
            # UNION NODE
            #################################

            elif item is Item.UnionNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(-23 + 6, +15),
                    QtCore.QPointF(+23 - 6, +15),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(+23 - 6, -15),
                    QtCore.QPointF(-23 + 6, -15),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-23, -15, 46, 30), QtCore.Qt.AlignCenter, 'or')
                painter.end()

            #############################################
            # HASKEY NODE
            #################################

            elif item is Item.HasKeyNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(
                    QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
                               QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(-23 + 6, +15),
                    QtCore.QPointF(+23 - 6, +15),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(+23 - 6, -15),
                    QtCore.QPointF(-23 + 6, -15),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.setFont(Font(pixelSize=11, weight=Font.Light))
                painter.drawText(QtCore.QRectF(-23, -15, 46, 30), QtCore.Qt.AlignCenter, 'key')
                painter.end()

            #############################################
            # DISJOINT-UNION NODE
            #################################

            elif item is Item.DisjointUnionNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QtGui.QPolygonF([
                    QtCore.QPointF(-23, 0),
                    QtCore.QPointF(-23 + 6, +15),
                    QtCore.QPointF(+23 - 6, +15),
                    QtCore.QPointF(+23, 0),
                    QtCore.QPointF(+23 - 6, -15),
                    QtCore.QPointF(-23 + 6, -15),
                    QtCore.QPointF(-23, 0),
                ]))
                painter.end()

            #############################################
            # PROPERTY ASSERTION NODE
            #################################

            elif item is Item.PropertyAssertionNode:

                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawRoundedRect(QtCore.QRectF(-23, -15, 46, 30), 14, 14)
                painter.end()

            #############################################
            # INCLUSION EDGE
            #################################

            elif item is Item.InclusionEdge:

                P1 = QtCore.QPointF(3, 22)
                P2 = QtCore.QPointF(55, 22)
                L1 = QtCore.QLineF(P1, P2)
                A1 = L1.angle()
                P1 = QtCore.QPointF(L1.p2().x() + 2, L1.p2().y())
                P2 = P1 - QtCore.QPointF(sin(A1 + M_PI / 3.0) * 8, cos(A1 + M_PI / 3.0) * 8)
                P3 = P1 - QtCore.QPointF(sin(A1 + M_PI - M_PI / 3.0) * 8, cos(A1 + M_PI - M_PI / 3.0) * 8)
                H1 = QtGui.QPolygonF([P1, P2, P3])
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.drawLine(L1)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)))
                painter.drawPolygon(H1)
                painter.end()

            #############################################
            # EQUIVALENCE EDGE
            #################################

            elif item is Item.EquivalenceEdge:

                P1 = QtCore.QPointF(3, 22)
                P2 = QtCore.QPointF(55, 22)
                L1 = QtCore.QLineF(P1, P2)
                A1 = L1.angle()
                P1 = QtCore.QPointF(L1.p2().x(), L1.p2().y())
                P2 = P1 - QtCore.QPointF(sin(A1 + M_PI / 3.0) * 8, cos(A1 + M_PI / 3.0) * 8)
                P3 = P1 - QtCore.QPointF(sin(A1 + M_PI - M_PI / 3.0) * 8, cos(A1 + M_PI - M_PI / 3.0) * 8)
                H1 = QtGui.QPolygonF([P1, P2, P3])
                P1 = QtCore.QPointF(L1.p1().x(), L1.p1().y())
                P2 = P1 + QtCore.QPointF(sin(A1 + M_PI / 3.0) * 8, cos(A1 + M_PI / 3.0) * 8)
                P3 = P1 + QtCore.QPointF(sin(A1 + M_PI - M_PI / 3.0) * 8, cos(A1 + M_PI - M_PI / 3.0) * 8)
                T1 = QtGui.QPolygonF([P1, P2, P3])
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.drawLine(L1)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)))
                painter.drawPolygon(H1)
                painter.drawPolygon(T1)
                painter.end()

            #############################################
            # INPUT EDGE
            #################################

            elif item is Item.InputEdge:

                P1 = QtCore.QPointF(3, 22)
                P2 = QtCore.QPointF(55, 22)
                L1 = QtCore.QLineF(P1, P2)
                A1 = L1.angle()
                P1 = QtCore.QPointF(L1.p2().x() + 2, L1.p2().y())
                P2 = P1 - QtCore.QPointF(sin(A1 + M_PI / 4.0) * 8, cos(A1 + M_PI / 4.0) * 8)
                P3 = P2 - QtCore.QPointF(sin(A1 + 3.0 / 4.0 * M_PI) * 8, cos(A1 + 3.0 / 4.0 * M_PI) * 8)
                p4 = P3 - QtCore.QPointF(sin(A1 - 3.0 / 4.0 * M_PI) * 8, cos(A1 - 3.0 / 4.0 * M_PI) * 8)
                H1 = QtGui.QPolygonF([P1, P2, P3, p4])
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.CustomDashLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
                pen.setDashPattern([3, 3])
                painter.setPen(pen)
                painter.drawLine(L1)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.drawPolygon(H1)
                painter.end()

            #############################################
            # MEMBERSHIP EDGE
            #################################

            elif item is Item.MembershipEdge:

                PP1 = QtCore.QPointF(2, 22)
                PP2 = QtCore.QPointF(55, 22)
                L1 = QtCore.QLineF(PP1, PP2)
                A1 = L1.angle()
                P1 = QtCore.QPointF(L1.p2().x() + 2, L1.p2().y())
                P2 = P1 - QtCore.QPointF(sin(A1 + M_PI / 3.0) * 8, cos(A1 + M_PI / 3.0) * 8)
                P3 = P1 - QtCore.QPointF(sin(A1 + M_PI - M_PI / 3.0) * 8, cos(A1 + M_PI - M_PI / 3.0) * 8)
                H1 = QtGui.QPolygonF([P1, P2, P3])
                S1 = 0
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.DotLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.drawLine(L1)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(252, 252, 252, 255)))
                painter.drawPolygon(H1)
                painter.setFont(Font(pixelSize=9, weight=Font.Light))
                painter.end()

            #############################################
            # SAME EDGE
            #################################

            elif item is Item.SameEdge:

                PP1 = QtCore.QPointF(2, 22)
                PP2 = QtCore.QPointF(55, 22)
                L1 = QtCore.QLineF(PP1, PP2)
                S1 = (PP2.x() - PP1.x() - 25) / 2
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.drawLine(L1)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)))
                painter.setFont(Font(pixelSize=9, weight=Font.Light))
                painter.drawText(QtCore.QPointF(PP1.x() + S1, 18), 'same')
                painter.end()

            #############################################
            # DIFFERENT EDGE
            #################################

            elif item is Item.DifferentEdge:

                PP1 = QtCore.QPointF(2, 22)
                PP2 = QtCore.QPointF(55, 22)
                L1 = QtCore.QLineF(PP1, PP2)
                S1 = (PP2.x() - PP1.x() - 35) / 2
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.drawLine(L1)
                painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)))
                painter.setFont(Font(pixelSize=9, weight=Font.Light))
                painter.drawText(QtCore.QPointF(PP1.x() + S1, 18), 'different')
                painter.end()

            #############################################
            # ADD THE GENERATED PIXMAP TO THE ICON
            #################################

            icon.addPixmap(pixmap)

        return icon
