# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from abc import ABCMeta

from grapholed import __appname__, __organization__
from grapholed.exceptions import ProgrammingError
from grapholed.functions import shaded, connect, disconnect

from PyQt5.QtCore import Qt, QEvent, QSize, pyqtSignal, pyqtSlot, QSettings
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtWidgets import QScrollArea, QVBoxLayout, QWidget, QFrame, QScrollBar, QLabel, QGraphicsView, QGridLayout
from PyQt5.QtWidgets import QHBoxLayout, QStyleOption, QStyle, QListWidget, QListWidgetItem


########################################################################################################################
#                                                                                                                      #
#   SIDEBAR IMPLEMENTATION                                                                                             #
#                                                                                                                      #
########################################################################################################################

class Sidebar(QScrollArea):

    MinWidth = 216  # without scrollbars
    MaxWidth = 234  # with scrollbars displayed

    def __init__(self, parent=None):
        """
        Initialize the Sidebar.
        :param parent: the parent widget.
        """
        super().__init__(parent)

        self.itemList = QListWidget()
        self.itemList.setContentsMargins(0, 0, 0, 0)
        self.itemList.setSpacing(0)

        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameStyle(QFrame.NoFrame)
        self.setFixedWidth(Sidebar.MinWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.setWidgetResizable(True)
        self.setWidget(self.itemList)
        self.verticalScrollBar().installEventFilter(self)

    ################################################# INTERFACE ########################################################

    def addWidget(self, widget):
        """
        Add a widget to the Sidebar.
        :param widget: the widget to add.
        """
        if not isinstance(widget, SidebarWidget):
            raise ProgrammingError('invalid argument specified ({0}): '
                                   'expecting PaneItem'.format(widget.__class__.__name__))
        item = SidebarWidgetItem()
        item.setFlags(item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
        item.setSizeHint(widget.sizeHint())

        connect(widget.sizeChanged, item.onSizeChanged)

        self.itemList.addItem(item)
        self.itemList.setItemWidget(item, widget)

    ############################################## EVENT HANDLERS ######################################################

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :param source: the watched object.
        :param event: the event instance.
        """
        if isinstance(source, QScrollBar):
            if event.type() == QEvent.Show:
                self.setFixedWidth(Sidebar.MaxWidth)
            elif event.type() == QEvent.Hide:
                self.setFixedWidth(Sidebar.MinWidth)
        return super().eventFilter(source, event)

    ################################################### UPDATE #########################################################

    def update(self, *__args):
        """
        Update the widget refreshing all the children.
        """
        for item in (self.itemList.item(i) for i in range(self.itemList.count())):
            self.itemList.itemWidget(item).update()
        super().update(*__args)


########################################################################################################################
#                                                                                                                      #
#   SIDEBAR WIDGETS BASE IMPLEMENTATION                                                                                #
#                                                                                                                      #
########################################################################################################################


class SidebarWidget(QWidget):
    """
    This the base class for all the Sidebar widgets.
    """
    __metaclass__ = ABCMeta

    sizeChanged = pyqtSignal()

    ####################################################################################################################
    #                                                                                                                  #
    #   HEAD                                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    class Head(QWidget):

        def __init__(self, title, icon, body, parent=None):
            """
            Initialize the header of the widget.
            :param title: the title of the widget.
            :param icon: the path of the icon to display in the header.
            :param body: the body this header is controlling.
            :param parent: the parent widget
            """
            super().__init__(parent)

            self.settings = QSettings(__organization__, __appname__)

            self.body = body
            self.icon = shaded(QPixmap(icon), 0.7)
            self.title = QLabel(title)

            self.iconUp = QPixmap(':/icons/arrow-up')
            self.iconDown = QPixmap(':/icons/arrow-down')

            self.image = QLabel()
            self.image.setPixmap(self.icon)
            self.arrow = QLabel()

            self.mainLayout = QHBoxLayout(self)
            self.mainLayout.addWidget(self.image, 0, Qt.AlignLeft)
            self.mainLayout.addWidget(self.title, 1, Qt.AlignLeft)
            self.mainLayout.addWidget(self.arrow, 0, Qt.AlignRight)
            self.mainLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.mainLayout.setContentsMargins(5, 4, 5, 4)

            self.setContentsMargins(0, 0, 0, 0)
            self.setFixedSize(QSize(Sidebar.MinWidth, 30))
            self.setClosed(self.settings.value('sidebar/{0}/closed'.format(title), False, bool))

        ############################################## EVENT HANDLERS ##################################################

        def enterEvent(self, event):
            """
            Executed when the mouse enter the widget area.
            :param event: the event instance.
            """
            self.setCursor(Qt.PointingHandCursor)

        def leaveEvent(self, event):
            """
            Executed when the mouse leaves the widget area.
            :param event: the event instance.
            """
            self.setCursor(Qt.ArrowCursor)

        def mousePressEvent(self, mouseEvent):
            """
            Executed when the mouse is pressed on the widget.
            :param mouseEvent: the event instance.
            """
            self.setClosed(self.body.isVisible())

        ############################################ AUXILIARY METHODS #################################################

        def setClosed(self, closed):
            """
            Set the closed status (of the attached body).
            :param closed: True if the body attached to the header should be closed, False otherwise.
            """
            parent = self.parent()
            self.settings.setValue('sidebar/{0}/closed'.format(parent.objectName()), closed)
            self.body.setVisible(not closed)
            self.arrow.setPixmap(self.iconDown if closed else self.iconUp)
            self.setProperty('class', 'closed' if closed else 'normal')

            # emit a signal so other widgets can react on the size change
            parent.sizeChanged.emit()

            # refresh the widget stylesheet
            style = self.style()
            style.unpolish(self)
            style.polish(self)

            # refresh the label stylesheet
            style = self.title.style()
            style.unpolish(self.title)
            style.polish(self.title)

            self.update()

        ############################################## LAYOUT UPDATE ###################################################

        def update(self, *__args):
            """
            Update the widget refreshing all the children.
            """
            self.title.update()
            self.image.update()
            self.arrow.update()
            super().update(*__args)

        ############################################## ITEM PAINTING ###################################################

        def paintEvent(self, paintEvent):
            """
            This is needed for the widget to pick the stylesheet.
            :param paintEvent: the paint event instance.
            """
            option = QStyleOption()
            option.initFrom(self)
            painter = QPainter(self)
            style = self.style()
            style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    ####################################################################################################################
    #                                                                                                                  #
    #   BODY                                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    class Body(QWidget):

        def __init__(self, widget, parent=None):
            """
            Initialize the body of the widget.
            :param widget: the widget to be rendered in the body.
            :param parent: the parent widget.
            """
            super().__init__(parent)
            self.mainLayout = QVBoxLayout(self)
            self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.mainLayout.setContentsMargins(0, 0, 0, 0)
            self.mainLayout.addWidget(widget)
            self.mainLayout.setSpacing(0)
            self.setContentsMargins(0, 0, 0, 0)

        ############################################# ITEM PAINTING ####################################################

        def paintEvent(self, paintEvent):
            """
            This is needed for the widget to pick the stylesheet.
            :param paintEvent: the paint event instance.
            """
            option = QStyleOption()
            option.initFrom(self)
            painter = QPainter(self)
            style = self.style()
            style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def __init__(self, title, icon, widget):
        """
        Initialize the Sidebar widget.
        :param title: the title of the widget.
        :param icon: the path of the icon to display as widget icon.
        :param widget: the widget to be rendered inside the body of the Pane widget.
        """
        super().__init__()

        self._widget = widget

        self.body = SidebarWidget.Body(widget, self)
        self.head = SidebarWidget.Head(title, icon, self.body, self)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 4)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.head)
        self.mainLayout.addWidget(self.body)

        self.setFixedWidth(Sidebar.MinWidth)
        self.setObjectName(title)

    @property
    def widget(self):
        """
        Returns the widget displayed inside this Pane widget.
        """
        return self._widget

    ################################################ LAYOUT UPDATE #####################################################

    def update(self, *__args):
        """
        Update the widget refreshing all the children.
        """
        self.head.update()
        self.body.update()
        super().update(*__args)


class SidebarWidgetItem(QListWidgetItem):
    """
    This class is used to store widgets inside the QListWidget.
    """
    @pyqtSlot(bool)
    def onSizeChanged(self):
        """
        Executed when size of the widget attached to this item changes.
        """
        self.setSizeHint(self.listWidget().itemWidget(self).sizeHint())


########################################################################################################################
#                                                                                                                      #
#   PALETTE                                                                                                            #
#                                                                                                                      #
########################################################################################################################


class Palette(SidebarWidget):
    """
    This class implements a single palette section.
    """
    padding = 6
    spacing = 4

    class Widget(QWidget):
        """
        This class is used to dispose palette elements withing the Palette block.
        """
        def __init__(self, parent=None):
            """
            Initialize the palette block inner widget.
            :param parent: the parent widget.
            """
            super().__init__(parent)
            self.mainLayout = QGridLayout(self)
            self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.mainLayout.setContentsMargins(0, Palette.padding, 0, Palette.padding)
            self.mainLayout.setSpacing(Palette.spacing)
            self.setContentsMargins(0, 0, 0, 0)
            self.setFixedWidth(Sidebar.MinWidth)
            self.numcol = 3
            self.indexC = 0
            self.indexR = 0

        ############################################### INTERFACE ######################################################

        def addButton(self, button):
            """
            Appened the given button to the palette.
            :param button: the button to add.
            """
            self.mainLayout.addWidget(button, self.indexR, self.indexC)
            self.indexC += 1
            if self.indexC >= self.numcol:
                self.indexC = 0
                self.indexR += 1

        ############################################# ITEM PAINTING ####################################################

        def paintEvent(self, paintEvent):
            """
            This is needed for the widget to pick the stylesheet.
            :param paintEvent: the paint event instance.
            """
            option = QStyleOption()
            option.initFrom(self)
            painter = QPainter(self)
            style = self.style()
            style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def __init__(self, title, icon):
        """
        Initialize the palette block.
        :param title: the title of the widget.
        :param icon: the path of the icon to display as widget icon.
        """
        super().__init__(title, icon, Palette.Widget())
        self.body.setFixedWidth(Sidebar.MinWidth)

    ################################################# INTERFACE ########################################################

    def addButton(self, button):
        """
        Appened the given button to the palette.
        :param button: the button to add.
        """
        self.widget.addButton(button)
        # IMPORTANT: do not remove this otherwise the palette won't be rendered properly due to
        # the fact that it doesn't specify a fixed height in the constructor (because we don't know
        # the exact height) so we need to continuously recalculate it.
        sizeHint = self.widget.mainLayout.sizeHint()
        self.body.setFixedHeight(sizeHint.height() - 2 * self.widget.mainLayout.rowCount())


########################################################################################################################
#                                                                                                                      #
#   MAIN VIEW BROWSERS                                                                                                 #
#                                                                                                                      #
########################################################################################################################


class ViewBrowser(SidebarWidget):
    """
    Base class for all the Sidebar widgets used to inspect the Main View.
    """
    __metaclass__ = ABCMeta

    ############################################## WIDGET INTERFACE ####################################################

    def clearView(self):
        """
        Clear the widget from browsing the current view.
        """
        self.widget.clearView()

    def setView(self, view):
        """
        Set the widget to browse the given view.
        :param view: the view from where to pick the scene to display.
        """
        self.widget.setView(view)


class Navigator(ViewBrowser):
    """
    This class is used to display the active scene navigator.
    """
    class Widget(QGraphicsView):
        """
        This class implements the view shown in the navigator.
        """
        def __init__(self, parent=None):
            """
            Initialize the navigator inner widget.
            :param parent: the parent widget.
            """
            super().__init__(parent)
            self.navBrush = QColor(250, 140, 140, 100)
            self.navPen = QPen(QColor(250, 0, 0, 100), 1.0, Qt.SolidLine)
            self.mousepressed = False
            self.mainview = None

        ########################################## CUSTOM VIEW DRAWING #################################################

        def drawBackground(self, painter, rect):
            """
            Override scene drawBackground method so the grid is not rendered in the overview.
            :param painter: the active painter
            :param rect: the exposed rectangle
            """
            pass

        def drawForeground(self, painter, rect):
            """
            Draw the navigation cursor.
            :param painter: the active painter
            :param rect: the exposed rectangle
            """
            if self.mainview:
                painter.setPen(self.navPen)
                painter.setBrush(self.navBrush)
                painter.drawRect(self.mainview.visibleRect())

        ############################################ EVENT HANDLERS ####################################################

        def contextMenuEvent(self, menuEvent):
            """
            Turn off the context menu for this view.
            :param menuEvent: the context menu event instance.
            """
            pass

        def mouseDoubleClickEvent(self, mouseEvent):
            """
            Executed when the mouse is double clicked on the view.
            :param mouseEvent: the mouse event instance.
            """
            pass

        def mousePressEvent(self, mouseEvent):
            """
            Executed when the mouse is pressed on the view.
            :param mouseEvent: the mouse event instance.
            """
            if mouseEvent.buttons() & Qt.LeftButton:
                if self.mainview:
                    self.mousepressed = True
                    self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

        def mouseMoveEvent(self, mouseEvent):
            """
            Executed when the mouse is moved on the view.
            :param mouseEvent: the mouse event instance.
            """
            if mouseEvent.buttons() & Qt.LeftButton:
                if self.mainview and self.mousepressed:
                    self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

        def mouseReleaseEvent(self, mouseEvent):
            """
            Executed when the mouse is released from the view.
            :param mouseEvent: the mouse event instance.
            """
            if mouseEvent.buttons() & Qt.LeftButton:
                if self.mainview:
                    self.mousepressed = False

        def wheelEvent(self, wheelEvent):
            """
            Turn off wheel event since we don't need to scroll anything.
            :param wheelEvent: the mouse wheel event.
            """
            pass

        ############################################ WIDGET INTERFACE ##################################################

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
            :param rect: the new rectangle.
            """
            self.fitInView(rect, Qt.KeepAspectRatio)

        def setView(self, view):
            """
            Set the widget to browse the given view.
            :param view: the view from where to pick the scene to display.
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

    def __init__(self):
        """
        Initialize the navigator.
        """
        super().__init__('Navigator', ':/icons/zoom', Navigator.Widget())
        self.body.setFixedSize(QSize(Sidebar.MinWidth, Sidebar.MinWidth))


class Overview(ViewBrowser):
    """
    This class is used to display the active scene overview.
    """
    class Widget(QGraphicsView):
        """
        This class implements the view shown in the navigator.
        """
        def __init__(self, parent=None):
            """
            Initialize the overview.
            :param parent: the parent widget.
            """
            super().__init__(parent)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setViewportUpdateMode(QGraphicsView.NoViewportUpdate)
            self.mousepressed = False
            self.mainview = None

        ########################################## CUSTOM VIEW DRAWING #################################################

        def drawBackground(self, painter, rect):
            """
            Override scene drawBackground method so the grid is not rendered in the overview.
            :param painter: the active painter.
            :param rect: the exposed rectangle.
            """
            pass

        def drawForeground(self, painter, rect):
            """
            Draw the navigation cursor.
            :param painter: the active painter.
            :param rect: the exposed rectangle.
            """
            pass

        ############################################ EVENT HANDLERS ####################################################

        def contextMenuEvent(self, menuEvent):
            """
            Turn off the context menu for this view.
            :param menuEvent: the context menu event instance.
            """
            pass

        def mouseDoubleClickEvent(self, mouseEvent):
            """
            Executed when the mouse is double clicked on the view.
            :param mouseEvent: the mouse event instance.
            """
            pass

        def mousePressEvent(self, mouseEvent):
            """
            Executed when the mouse is pressed on the view.
            :param mouseEvent: the mouse event instance.
            """
            if mouseEvent.buttons() & Qt.LeftButton:
                if self.mainview:
                    self.mousepressed = True
                    self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

        def mouseMoveEvent(self, mouseEvent):
            """
            Executed when the mouse is moved on the view.
            :param mouseEvent: the mouse event instance.
            """
            if mouseEvent.buttons() & Qt.LeftButton:
                if self.mainview and self.mousepressed:
                    self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

        def mouseReleaseEvent(self, mouseEvent):
            """
            Executed when the mouse is released from the view.
            :param mouseEvent: the mouse event instance.
            """
            if mouseEvent.buttons() & Qt.LeftButton:
                if self.mainview:
                    self.mousepressed = False

        def wheelEvent(self, wheelEvent):
            """
            Turn off wheel event since we don't need to scroll anything.
            :param wheelEvent: the mouse wheel event.
            """
            pass

        ############################################# WIDGET INTERFACE #################################################

        def clearView(self):
            """
            Clear the widget from inspecting a diagram scene.
            """
            if self.mainview:

                try:
                    scene = self.mainview.scene()
                    # make sure to disconnect only the signals connected to the slots provided by this
                    # widget otherwise we will experiences bugs when the MainWindow goes out of focus: for more
                    # details on the matter read: https://github.com/danielepantaleone/grapholed/issues/15
                    disconnect(scene.selectionChanged, self.updateView)
                    disconnect(scene.updated, self.updateView)
                except RuntimeError:
                    # subwindow closed => we don't have the scene reference anymore
                    pass
                finally:
                    self.mainview = None

            self.viewport().update()

        def setView(self, mainview):
            """
            Set the navigator over the given main view.
            :param mainview: the mainView from where to pick the scene for the navigator.
            """
            self.clearView()

            if mainview:
                scene = mainview.scene()
                connect(scene.selectionChanged, self.updateView)
                connect(scene.updated, self.updateView)
                self.setScene(scene)

            self.mainview = mainview
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

    def __init__(self,):
        """
        Initialize the overview.
        """
        super().__init__('Overview', ':/icons/zoom', Overview.Widget())
        self.body.setFixedSize(QSize(Sidebar.MinWidth, Sidebar.MinWidth))