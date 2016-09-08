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


import sys

from PyQt5.QtCore import Qt, QEvent, QMimeData, pyqtSlot
from PyQt5.QtCore import QRectF, QPointF, QLineF, QSize, QSettings
from PyQt5.QtGui import QDrag, QIcon, QPixmap, QPainter
from PyQt5.QtGui import QPolygonF, QPen, QColor, QBrush
from PyQt5.QtWidgets import QApplication, QToolButton, QStyle
from PyQt5.QtWidgets import QMenu, QAction, QActionGroup
from PyQt5.QtWidgets import QWidget, QGridLayout, QStyleOption

from math import ceil, sin, cos, pi as M_PI, sqrt
from verlib import NormalizedVersion

from eddy import APPNAME, ORGANIZATION
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.owl import Facet
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin

from eddy.ui.dock import DockWidget


LINUX = sys.platform.startswith('linux')
MACOS = sys.platform.startswith('darwin')
WIN32 = sys.platform.startswith('win32')


class Palette(AbstractPlugin):
    """
    This plugin provides the Graphol palette for Eddy.
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

    @pyqtSlot('QGraphicsScene')
    def onDiagramAdded(self, diagram):
        """
        Executed when a diagram is added to the project.
        :typw diagram: Diagram
        """
        self.debug('Connecting to diagram: %s', diagram.name)
        connect(diagram.sgnItemInsertionCompleted, self.onDiagramItemInsertionCompleted)
        connect(diagram.sgnModeChanged, self.onDiagramModeChanged)

    @pyqtSlot('QGraphicsItem', int)
    def onDiagramItemInsertionCompleted(self, _, modifiers):
        """
        Executed after an item MANUAL insertion process ends (not triggered for item added programmatically).
        :type _: AbstractItem
        :type modifiers: int
        """
        diagram = self.session.mdi.activeDiagram()
        if diagram:
            if not modifiers & Qt.ControlModifier:
                self.widget('palette').reset()
                diagram.setMode(DiagramMode.Idle)

    @pyqtSlot(DiagramMode)
    def onDiagramModeChanged(self, mode):
        """
        Executed when the diagram operational mode changes.
        :type mode: DiagramMode
        """
        if mode not in (DiagramMode.NodeAdd, DiagramMode.EdgeAdd):
            self.widget('palette').reset()

    @pyqtSlot('QGraphicsScene')
    def onDiagramRemoved(self, diagram):
        """
        Executed when a diagram is removed to the project.
        :typw diagram: Diagram
        """
        self.debug('Disconnecting from diagram: %s', diagram.name)
        disconnect(diagram.sgnItemInsertionCompleted, self.onDiagramItemInsertionCompleted)
        disconnect(diagram.sgnModeChanged, self.onDiagramModeChanged)

    @pyqtSlot(bool)
    def onMenuButtonClicked(self, _=False):
        """
        Executed when a button in the widget menu is clicked.
        """
        # FIXME: https://bugreports.qt.io/browse/QTBUG-36862
        self.widget('palette_toggle').setAttribute(Qt.WA_UnderMouse, False)

    @pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        connect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        for diagram in self.project.diagrams():
            self.debug('Connecting to diagram: %s', diagram.name)
            connect(diagram.sgnItemInsertionCompleted, self.onDiagramItemInsertionCompleted)
            connect(diagram.sgnModeChanged, self.onDiagramModeChanged)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def name(cls):
        """
        Returns the readable name of the plugin.
        :rtype: str
        """
        return 'Palette'

    def objectName(self):
        """
        Returns the system name of the plugin.
        :rtype: str
        """
        return 'palette'

    def startup(self):
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
        group = QActionGroup(self, objectName='palette_toggle')
        group.setExclusive(False)
        for item in widget.items:
            action = QAction(item.realName.title(), group, objectName=item.name, checkable=True)
            action.setChecked(widget.display[item])
            action.setData(item)
            action.setFont(Font('Arial', 11))
            connect(action.triggered, widget.onMenuButtonClicked)
            connect(action.triggered, self.onMenuButtonClicked)
            group.addAction(action)
        self.addAction(group)

        # CREATE TOGGLE MENU
        self.debug('Creating palette toggle menu')
        menu = QMenu(objectName='palette_toggle')
        menu.addActions(self.action('palette_toggle').actions())
        self.addMenu(menu)

        # CREATE CONTROL WIDGET
        self.debug('Creating palette toggle control widget')
        button = QToolButton(objectName='palette_toggle')
        button.setIcon(QIcon(':/icons/18/ic_settings_black'))
        button.setContentsMargins(0, 0, 0, 0)
        button.setFixedSize(18, 18)
        button.setMenu(self.menu('palette_toggle'))
        button.setPopupMode(QToolButton.InstantPopup)
        self.addWidget(button)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Palette', QIcon(':/icons/18/ic_palette_black'), self.session)
        widget.addTitleBarButton(self.widget('palette_toggle'))
        widget.installEventFilter(self)
        widget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        widget.setObjectName('palette_dock')
        widget.setWidget(self.widget('palette'))
        self.addWidget(widget)

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('palette_dock').toggleViewAction())

        self.debug('Configuring session specific signals')
        connect(self.session.sgnReady, self.onSessionReady)

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(Qt.LeftDockWidgetArea, self.widget('palette_dock'))

    @classmethod
    def version(cls):
        """
        Returns the version of the plugin.
        :rtype: NormalizedVersion
        """
        return NormalizedVersion('0.1')


class PaletteWidget(QWidget):
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
            Item.DisjointUnionNode,
            Item.PropertyAssertionNode,
            Item.InclusionEdge,
            Item.InputEdge,
            Item.MembershipEdge,
        ]

        # CREATE BUTTONS
        for item in self.items:
            button = PaletteButton(item)
            button.installEventFilter(self)
            connect(button.clicked, self.onButtonClicked)
            self.addButton(item, button)

        # LOAD BUTTONS DISPLAY SETTINGS
        settings = QSettings(ORGANIZATION, APPNAME)
        for item in self.items:
            self.display[item] = settings.value('plugins/palette/{0}'.format(item.name), True, bool)

        # SETUP LAYOUT
        self.mainLayout = QGridLayout(self)
        self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 6, 0, 6)
        self.mainLayout.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

        self.setStyleSheet("""
        QDockWidget PaletteWidget {
        background: #F0F0F0;
        }
        QDockWidget PaletteWidget PaletteButton:checked {
        background: #42A5F5;
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

    @pyqtSlot()
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
                elif Item.InclusionEdge <= button.item <= Item.MembershipEdge:
                    diagram.setMode(DiagramMode.EdgeAdd, button.item)

    @pyqtSlot(bool)
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
        settings = QSettings(ORGANIZATION, APPNAME)
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
        :type event: QEvent
        :rtype: bool
        """
        if event.type() in {QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseMove}:
            if isinstance(source, PaletteButton):
                if not self.isEnabled():
                    return True
        return super().eventFilter(source, event)

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
            # COMPUTE NEW BUTTONS LOCATION
            zipped = list(zip([x for x in range(rows) for _ in range(columns)], list(range(columns)) * rows))
            zipped = zipped[:len(items)]
            # CLEAR CURRENTY LAYOUT
            for i in reversed(range(self.mainLayout.count())):
                item = self.mainLayout.itemAt(i)
                self.mainLayout.removeItem(item)
            # DISPOSE NEW BUTTONS
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
        :rtype: QSize
        """
        return QSize(216, 342)


class PaletteButton(QToolButton):
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
        self.setContentsMargins(0, 0, 0, 0)
        self.setIcon(PaletteButton.iconFor(item))
        self.setIconSize(QSize(60, 44))

    #############################################
    #   EVENTS
    #################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the button.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            self.startPos = mouseEvent.pos()
        super().mousePressEvent(mouseEvent)

    # noinspection PyArgumentList
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse if moved while a button is being pressed.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            if Item.ConceptNode <= self.item < Item.InclusionEdge:
                distance = (mouseEvent.pos() - self.startPos).manhattanLength()
                if distance >= QApplication.startDragDistance():
                    mimeData = QMimeData()
                    mimeData.setText(str(self.item.value))
                    drag = QDrag(self)
                    drag.setMimeData(mimeData)
                    drag.setPixmap(self.icon().pixmap(60, 40))
                    drag.setHotSpot(self.startPos - self.rect().topLeft())
                    drag.exec_(Qt.CopyAction)

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when a mouse button is released.
        :type mouseEvent: QMouseEvent
        """
        super().mouseReleaseEvent(mouseEvent)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def iconFor(cls, item):
        """
        Returns the appropriate icon for the given item.
        :type item: Item
        :rtype: QIcon
        """
        icon = QIcon()

        for i in (1.0, 2.0):

            pixmap = QPixmap(60 * i, 44 * i)
            pixmap.setDevicePixelRatio(i)
            pixmap.fill(Qt.transparent)

            #############################################
            # CONCEPT NODE
            #################################

            if item is Item.ConceptNode:
                painter = QPainter(pixmap)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawRect(QRectF(-27, -17, 54, 34))
                painter.setFont(Font('Arial', 11, Font.Light))
                painter.drawText(QRectF(-27, -17, 54, 34), Qt.AlignCenter, 'concept')
                painter.end()

            #############################################
            # ROLE NODE
            #################################

            elif item is Item.RoleNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-23, 0),
                    QPointF(0, +17),
                    QPointF(+23, 0),
                    QPointF(0, -17),
                    QPointF(-23, 0),
                ]))
                painter.setFont(Font('Arial', 11, Font.Light))
                painter.drawText(QRectF(-23, -17, 46, 34), Qt.AlignCenter, 'role')
                painter.end()

            #############################################
            # ATTRIBUTE NODE
            #################################

            elif item is Item.AttributeNode:

                painter = QPainter(pixmap)
                painter.setFont(Font('Arial', 9, Font.Light))
                painter.translate(0, 0)
                painter.drawText(QRectF(0, 0, 60, 22), Qt.AlignCenter, 'attribute')
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 30)
                painter.drawEllipse(QRectF(-9, -9, 18, 18))
                painter.end()

            #############################################
            # VALUE-DOMAIN NODE
            #################################

            elif item is Item.ValueDomainNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawRoundedRect(QRectF(-27, -17, 54, 34), 6, 6)
                painter.setFont(Font('Arial', 10, Font.Light))
                painter.drawText(QRectF(-27, -17, 54, 34), Qt.AlignCenter, 'xsd:string')
                painter.end()

            #############################################
            # INDIVIDUAL NODE
            #################################

            elif item is Item.IndividualNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-20, -((40 / (1 + sqrt(2))) / 2)),
                    QPointF(-20, +((40 / (1 + sqrt(2))) / 2)),
                    QPointF(-((40 / (1 + sqrt(2))) / 2), +20),
                    QPointF(+((40 / (1 + sqrt(2))) / 2), +20),
                    QPointF(+20, +((40 / (1 + sqrt(2))) / 2)),
                    QPointF(+20, -((40 / (1 + sqrt(2))) / 2)),
                    QPointF(+((40 / (1 + sqrt(2))) / 2), -20),
                    QPointF(-((40 / (1 + sqrt(2))) / 2), -20),
                    QPointF(-20, -((40 / (1 + sqrt(2))) / 2)),
                ]))
                painter.setFont(Font('Arial', 8, Font.Light))
                painter.drawText(-16, 4, 'individual')
                painter.end()

            #############################################
            # FACET NODE
            #################################

            elif item is Item.FacetNode:

                polygonA = QPolygonF([
                    QPointF(-54 / 2 + 4, -32 / 2),
                    QPointF(+54 / 2, -32 / 2),
                    QPointF(+54 / 2 - 4 / 2, 0),
                    QPointF(-54 / 2 + 4 / 2, 0),
                    QPointF(-54 / 2 + 4, -32 / 2),
                ])
                polygonB = QPolygonF([
                    QPointF(-54 / 2 + 4 / 2, 0),
                    QPointF(+54 / 2 - 4 / 2, 0),
                    QPointF(+54 / 2 - 4, +32 / 2),
                    QPointF(-54 / 2, +32 / 2),
                    QPointF(-54 / 2 + 4 / 2, 0),
                ])
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.setBrush(QBrush(QColor(222, 222, 222, 255)))
                painter.drawPolygon(polygonA)
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.drawPolygon(polygonB)
                painter.setFont(Font('Arial', 9, Font.Light))
                painter.drawText(QPointF(-19, -5), Facet.length.value)
                painter.drawText(QPointF(-8, 12), '"32"')
                painter.end()

            #############################################
            # DOMAIN RESTRICTION NODE
            #################################

            elif item is Item.DomainRestrictionNode:

                painter = QPainter(pixmap)
                painter.setFont(Font('Arial', 9, Font.Light))
                painter.translate(0, 0)
                painter.drawText(QRectF(0, 0, 60, 22), Qt.AlignCenter, 'restriction')
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawRect(QRectF(-18 / 2, -18 / 2 + 6, 18, 18))
                painter.end()

            #############################################
            # RANGE RESTRICTION NODE
            #################################

            elif item is Item.RangeRestrictionNode:

                painter = QPainter(pixmap)
                painter.setFont(Font('Arial', 9, Font.Light))
                painter.translate(0, 0)
                painter.drawText(QRectF(0, 0, 60, 22), Qt.AlignCenter, 'restriction')
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
                painter.translate(30, 22)
                painter.drawRect(QRectF(-18 / 2, -18 / 2 + 6, 18, 18))
                painter.end()

            #############################################
            # INTERSECTION NODE
            #################################

            elif item is Item.IntersectionNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-23, 0),
                    QPointF(-23 + 6, +15),
                    QPointF(+23 - 6, +15),
                    QPointF(+23, 0),
                    QPointF(+23 - 6, -15),
                    QPointF(-23 + 6, -15),
                    QPointF(-23, 0),
                ]))
                painter.setFont(Font('Arial', 11, Font.Light))
                painter.drawText(QRectF(-23, -15, 46, 30), Qt.AlignCenter, 'and')
                painter.end()

            #############################################
            # ROLE CHAIN NODE
            #################################

            elif item is Item.RoleChainNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-23, 0),
                    QPointF(-23 + 6, +15),
                    QPointF(+23 - 6, +15),
                    QPointF(+23, 0),
                    QPointF(+23 - 6, -15),
                    QPointF(-23 + 6, -15),
                    QPointF(-23, 0),
                ]))
                painter.setFont(Font('Arial', 11, Font.Light))
                painter.drawText(QRectF(-23, -15, 46, 30), Qt.AlignCenter, 'chain')
                painter.end()

            #############################################
            # DATATYPE RESTRICTION NODE
            #################################

            elif item is Item.DatatypeRestrictionNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-23, 0),
                    QPointF(-23 + 6, +15),
                    QPointF(+23 - 6, +15),
                    QPointF(+23, 0),
                    QPointF(+23 - 6, -15),
                    QPointF(-23 + 6, -15),
                    QPointF(-23, 0),
                ]))
                painter.setFont(Font('Arial', 11, Font.Light))
                painter.drawText(QRectF(-23, -15, 46, 30), Qt.AlignCenter, 'data')
                painter.end()

            #############################################
            # ROLE INVERSE NODE
            #################################

            elif item is Item.RoleInverseNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-23, 0),
                    QPointF(-23 + 6, +15),
                    QPointF(+23 - 6, +15),
                    QPointF(+23, 0),
                    QPointF(+23 - 6, -15),
                    QPointF(-23 + 6, -15),
                    QPointF(-23, 0),
                ]))
                painter.setFont(Font('Arial', 11, Font.Light))
                painter.drawText(QRectF(-23, -15, 46, 30), Qt.AlignCenter, 'inv')
                painter.end()

            #############################################
            # COMPLEMENT NODE
            #################################

            elif item is Item.ComplementNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-23, 0),
                    QPointF(-23 + 6, +15),
                    QPointF(+23 - 6, +15),
                    QPointF(+23, 0),
                    QPointF(+23 - 6, -15),
                    QPointF(-23 + 6, -15),
                    QPointF(-23, 0),
                ]))
                painter.setFont(Font('Arial', 11, Font.Light))
                painter.drawText(QRectF(-23, -15, 46, 30), Qt.AlignCenter, 'inv')
                painter.end()

            #############################################
            # ENUMERATION NODE
            #################################

            elif item is Item.EnumerationNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-23, 0),
                    QPointF(-23 + 6, +15),
                    QPointF(+23 - 6, +15),
                    QPointF(+23, 0),
                    QPointF(+23 - 6, -15),
                    QPointF(-23 + 6, -15),
                    QPointF(-23, 0),
                ]))
                painter.setFont(Font('Arial', 11, Font.Light))
                painter.drawText(QRectF(-23, -15, 46, 30), Qt.AlignCenter, 'oneOf')
                painter.end()

            #############################################
            # UNION NODE
            #################################

            elif item is Item.UnionNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-23, 0),
                    QPointF(-23 + 6, +15),
                    QPointF(+23 - 6, +15),
                    QPointF(+23, 0),
                    QPointF(+23 - 6, -15),
                    QPointF(-23 + 6, -15),
                    QPointF(-23, 0),
                ]))
                painter.setFont(Font('Arial', 11, Font.Light))
                painter.drawText(QRectF(-23, -15, 46, 30), Qt.AlignCenter, 'or')
                painter.end()

            #############################################
            # DISJOINT-UNION NODE
            #################################

            elif item is Item.DisjointUnionNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
                painter.translate(30, 22)
                painter.drawPolygon(QPolygonF([
                    QPointF(-23, 0),
                    QPointF(-23 + 6, +15),
                    QPointF(+23 - 6, +15),
                    QPointF(+23, 0),
                    QPointF(+23 - 6, -15),
                    QPointF(-23 + 6, -15),
                    QPointF(-23, 0),
                ]))
                painter.end()

            #############################################
            # PROPERTY ASSERTION NODE
            #################################

            elif item is Item.PropertyAssertionNode:

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.translate(30, 22)
                painter.drawRoundedRect(QRectF(-23, -15, 46, 30), 14, 14)
                painter.end()

            #############################################
            # INCLUSION EDGE
            #################################

            elif item is Item.InclusionEdge:

                P1 = QPointF(3, 22)
                P2 = QPointF(55, 22)
                L1 = QLineF(P1, P2)
                A1 = L1.angle()
                P1 = QPointF(L1.p2().x() + 2, L1.p2().y())
                P2 = P1 - QPointF(sin(A1 + M_PI / 3.0) * 8, cos(A1 + M_PI / 3.0) * 8)
                P3 = P1 - QPointF(sin(A1 + M_PI - M_PI / 3.0) * 8, cos(A1 + M_PI - M_PI / 3.0) * 8)
                H1 = QPolygonF([P1, P2, P3])
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.drawLine(L1)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
                painter.drawPolygon(H1)
                painter.end()

            #############################################
            # INPUT EDGE
            #################################

            elif item is Item.InputEdge:

                P1 = QPointF(3, 22)
                P2 = QPointF(55, 22)
                L1 = QLineF(P1, P2)
                A1 = L1.angle()
                P1 = QPointF(L1.p2().x() + 2, L1.p2().y())
                P2 = P1 - QPointF(sin(A1 + M_PI / 4.0) * 8, cos(A1 + M_PI / 4.0) * 8)
                P3 = P2 - QPointF(sin(A1 + 3.0 / 4.0 * M_PI) * 8, cos(A1 + 3.0 / 4.0 * M_PI) * 8)
                p4 = P3 - QPointF(sin(A1 - 3.0 / 4.0 * M_PI) * 8, cos(A1 - 3.0 / 4.0 * M_PI) * 8)
                H1 = QPolygonF([P1, P2, P3, p4])
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                pen = QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
                pen.setDashPattern([3, 3])
                painter.setPen(pen)
                painter.drawLine(L1)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(252, 252, 252, 255)))
                painter.drawPolygon(H1)
                painter.end()

            #############################################
            # MEMBERSHIP EDGE
            #################################

            elif item is Item.MembershipEdge:

                PP1 = QPointF(2, 22)
                PP2 = QPointF(55, 22)
                L1 = QLineF(PP1, PP2)
                A1 = L1.angle()
                P1 = QPointF(L1.p2().x() + 2, L1.p2().y())
                P2 = P1 - QPointF(sin(A1 + M_PI / 3.0) * 8, cos(A1 + M_PI / 3.0) * 8)
                P3 = P1 - QPointF(sin(A1 + M_PI - M_PI / 3.0) * 8, cos(A1 + M_PI - M_PI / 3.0) * 8)
                H1 = QPolygonF([P1, P2, P3])
                S1 = 2 if MACOS else 0
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.drawLine(L1)
                painter.setPen(QPen(QBrush(QColor(0, 0, 0, 255)), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
                painter.drawPolygon(H1)
                painter.setFont(Font('Arial', 9, Font.Light))
                painter.drawText(PP1.x() + S1, 18, 'instanceOf')
                painter.end()

            #############################################
            # ADD THE GENERATED PIXMAP TO THE ICON
            #################################

            icon.addPixmap(pixmap)

        return icon
