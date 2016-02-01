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

from PyQt5.QtCore import Qt, QSize, pyqtSlot
from PyQt5.QtGui import QColor, QPen, QIcon, QPainter
from PyQt5.QtWidgets import QGraphicsView, QDockWidget, QWidget, QGridLayout, QButtonGroup, QToolButton
from PyQt5.QtWidgets import QStyleOption, QStyle

from eddy.core.functions import disconnect, connect

from eddy.core.items import ConceptNode, ComplementNode, DomainRestrictionNode, InputEdge, InclusionEdge, RoleNode
from eddy.core.items import DatatypeRestrictionNode, DisjointUnionNode, PropertyAssertionNode, InstanceOfEdge
from eddy.core.items import IndividualNode, ValueRestrictionNode, AttributeNode, UnionNode, EnumerationNode
from eddy.core.items import RangeRestrictionNode, RoleChainNode, RoleInverseNode, ValueDomainNode, IntersectionNode


class SidebarWidget(QDockWidget):
    """
    This class can be used to add DockWidgets to the main window sidebars.
    """
    Width = 216

    def __init__(self, title, widget, parent=None):
        """
        Initialize the Dock widget.
        ::type title: str
        :type widget: QWidget
        :type parent: QWidget
        """
        super().__init__(title, parent, Qt.Widget)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setFixedWidth(SidebarWidget.Width)
        self.setWidget(widget)


########################################################################################################################
#                                                                                                                      #
#   DOCK WIDGETS IMPLEMENTATION                                                                                        #
#                                                                                                                      #
########################################################################################################################


class ViewBrowser(QGraphicsView):
    """
    Base class for all the Dock widgets used to inspect the Main View.
    """
    __metaclass__ = ABCMeta

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def clearView(self):
        """
        Clear the widget from browsing the current view.
        """
        pass

    @abstractmethod
    def setView(self, view):
        """
        Set the widget to browse the given view.
        :type view: QGraphicsView
        """
        pass


class Navigator(ViewBrowser):
    """
    This class implements the main view Navigator.
    """
    def __init__(self, *args):
        """
        Initialize the Navigator.
        """
        super().__init__(*args)
        self.setFixedSize(SidebarWidget.Width, SidebarWidget.Width)
        self.navBrush = QColor(250, 140, 140, 100)
        self.navPen = QPen(QColor(250, 0, 0, 100), 1.0, Qt.SolidLine)
        self.mousepressed = False
        self.mainview = None

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def drawBackground(self, painter, rect):
        """
        Override scene drawBackground method so the grid is not rendered in the overview.
        :type painter: QPainter
        :type rect: QRectF
        """
        pass

    def drawForeground(self, painter, rect):
        """
        Draw the navigation cursor.
        :type painter: QPainter
        :type rect: QRectF
        """
        if self.mainview:
            painter.setPen(self.navPen)
            painter.setBrush(self.navBrush)
            painter.drawRect(self.mainview.visibleRect())

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenuEvent(self, menuEvent):
        """
        Turn off the context menu for this view.
        :type menuEvent: QGraphicsSceneContextMenuEvent
        """
        pass

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Executed when the mouse is double clicked on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        pass

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            if self.mainview:
                self.mousepressed = True
                self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is moved on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            if self.mainview and self.mousepressed:
                self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            if self.mainview:
                self.mousepressed = False

    def wheelEvent(self, wheelEvent):
        """
        Turn off wheel event since we don't need to scroll anything.
        :type wheelEvent: QGraphicsSceneWheelEvent
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def clearView(self):
        """
        Clear the widget from browsing the current view.
        """
        if self.mainview:

            try:
                scene = self.mainview.scene()
                disconnect(scene.sceneRectChanged, self.fitRectInView)
                disconnect(self.mainview.updated, self.updateView)
            except RuntimeError:
                # subwindow closed => we don't have the scene reference anymore
                pass
            finally:
                self.mainview = None

        self.updateView()

    @pyqtSlot('QRectF')
    def fitRectInView(self, rect):
        """
        Make sure that the given rectangle is fully visible in the navigator.
        :type rect: QRectF
        """
        self.fitInView(rect, Qt.KeepAspectRatio)

    def setView(self, view):
        """
        Set the widget to browse the given view.
        :type view: QGraphicsView
        """
        self.clearView()

        if view:
            scene = view.scene()
            # attach signals to new slots
            connect(scene.sceneRectChanged, self.fitRectInView)
            connect(view.updated, self.updateView)
            # fit the scene in the view
            self.setScene(scene)
            self.fitRectInView(view.sceneRect())

        self.mainview = view
        self.updateView()

    @pyqtSlot()
    def updateView(self):
        """
        Update the Navigator.
        """
        self.viewport().update()


class Overview(ViewBrowser):
    """
    This class is used to display the active scene overview.
    """
    def __init__(self, *args):
        """
        Initialize the Overview.
        """
        super().__init__(*args)
        self.setFixedSize(SidebarWidget.Width, SidebarWidget.Width)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.NoViewportUpdate)
        self.mousepressed = False
        self.mainview = None

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def drawBackground(self, painter, rect):
        """
        Override scene drawBackground method so the grid is not rendered in the overview.
        :type painter: QPainter
        :type rect: QRectF
        """
        pass

    def drawForeground(self, painter, rect):
        """
        Draw the navigation cursor.
        :type painter: QPainter
        :type rect: QRectF
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenuEvent(self, menuEvent):
        """
        Turn off the context menu for this view.
        :type menuEvent: QGraphicsSceneContextMenuEvent
        """
        pass

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Executed when the mouse is double clicked on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        pass

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            if self.mainview:
                self.mousepressed = True
                self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is moved on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            if self.mainview and self.mousepressed:
                self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            if self.mainview:
                self.mousepressed = False

    def wheelEvent(self, wheelEvent):
        """
        Turn off wheel event since we don't need to scroll anything.
        :type wheelEvent: QGraphicsSceneWheelEvent
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def clearView(self):
        """
        Clear the widget from browsing the current view.
        """
        if self.mainview:

            try:
                scene = self.mainview.scene()
                # make sure to disconnect only the signals connected to the slots provided by this
                # widget otherwise we will experiences bugs when the MainWindow goes out of focus: for more
                # details on the matter read: https://github.com/danielepantaleone/eddy/issues/15
                disconnect(scene.selectionChanged, self.updateView)
                disconnect(scene.updated, self.updateView)
            except RuntimeError:
                # subwindow closed => we don't have the scene reference anymore
                pass
            finally:
                self.mainview = None

        self.viewport().update()

    def setView(self, view):
        """
        Set the widget to browse the given view.
        :type view: QGraphicsView
        """
        self.clearView()

        if view:
            scene = view.scene()
            connect(scene.selectionChanged, self.updateView)
            connect(scene.updated, self.updateView)
            self.setScene(scene)

        self.mainview = view
        self.updateView()

    @pyqtSlot()
    def updateView(self):
        """
        Update the Overview.
        """
        if self.mainview:
            scene = self.mainview.scene()
            shape = scene.visibleRect(margin=10)
            if shape:
                self.fitInView(shape, Qt.KeepAspectRatio)
        self.viewport().update()


class Palette(QWidget):
    """
    This class implements the Graphol palette.
    """
    ButtonWidth = 60
    ButtonHeight = 44
    Padding = 6
    Spacing = 4

    def __init__(self, *args):
        """
        Initialize the Palette.
        """
        super().__init__(*args)
        self.buttonById = {}
        self.buttonGroup = QButtonGroup()
        self.buttonGroup.setExclusive(False)
        self.buttonClicked = self.buttonGroup.buttonClicked
        self.mainLayout = QGridLayout(self)
        self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, Palette.Padding, 0, Palette.Padding)
        self.mainLayout.setSpacing(Palette.Spacing)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(SidebarWidget.Width)
        self.initUI()

    def initUI(self):
        """
        Initialize the Palette user interface.
        """
        self.addButton(ConceptNode, 0, 0)
        self.addButton(RoleNode, 0, 1)
        self.addButton(ValueDomainNode, 0, 2)
        self.addButton(IndividualNode, 1, 0)
        self.addButton(ValueRestrictionNode, 1, 1)
        self.addButton(AttributeNode, 1, 2)
        self.addButton(DomainRestrictionNode, 2, 0)
        self.addButton(RangeRestrictionNode, 2, 1)
        self.addButton(IntersectionNode, 2, 2)
        self.addButton(RoleChainNode, 3, 0)
        self.addButton(DatatypeRestrictionNode, 3, 1)
        self.addButton(RoleInverseNode, 3, 2)
        self.addButton(ComplementNode, 4, 0)
        self.addButton(EnumerationNode, 4, 1)
        self.addButton(UnionNode, 4, 2)
        self.addButton(DisjointUnionNode, 5, 0)
        self.addButton(PropertyAssertionNode, 5, 1)
        self.addButton(InclusionEdge, 5, 2)
        self.addButton(InputEdge, 6, 0)
        self.addButton(InstanceOfEdge, 6, 1)

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

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

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def addButton(self, item, row, col):
        """
        Add a button to the palette.
        :type item: class
        :type row: int
        :type col: int
        """
        button = QToolButton()
        button.setIcon(QIcon(item.image(w=Palette.ButtonWidth, h=Palette.ButtonHeight)))
        button.setIconSize(QSize(60, 44))
        button.setCheckable(True)
        button.setContentsMargins(0, 0, 0, 0)
        self.buttonById[item.item] = button
        self.buttonGroup.addButton(button, item.item)
        self.mainLayout.addWidget(button, row, col)
        self.setFixedHeight(self.mainLayout.sizeHint().height() - 2 * self.mainLayout.rowCount())

    def button(self, button_id):
        """
        Returns the button matching the given id.
        :type button_id: Item
        """
        return self.buttonById[button_id]

    def buttons(self):
        """
        Returns a view of the buttons in the Palette.
        """
        return self.buttonById.values()

    def clear(self, *args):
        """
        Clear the palette selection.
        :type args: Item
        """
        for button in self.buttonById.values():
            if button not in args:
                button.setChecked(False)