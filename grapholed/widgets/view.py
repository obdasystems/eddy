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


from abc import ABCMeta, abstractmethod
from functools import partial

from grapholed.functions import clamp
from grapholed.widgets import ZoomControl, PaneWidget

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QEvent, pyqtSlot, QPointF, QTimer
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QGraphicsView


class MainView(QGraphicsView):
    """
    This class implements the main view displayed in the MDI area.
    """
    updated = pyqtSignal()
    zoomChanged = pyqtSignal(float)

    def __init__(self, scene):
        """
        Initialize the main scene.
        :param scene: the graphics scene to render in the main view.
        """
        super().__init__(scene)
        self.viewMove = None
        self.viewMoveRate = 20
        self.viewMoveBound = 10
        self.mousePressCenterPos = None
        self.mousePressPos = None
        self.zoom = 1.00

    ############################################### SIGNAL HANDLERS ####################################################

    @pyqtSlot(float)
    def handleScaleChanged(self, zoom):
        """
        Executed when the scale factor changes (triggered by the Main Slider in the Toolbar)
        :param zoom: the scale factor.
        """
        self.scaleView(zoom)

    ############################################### EVENT HANDLERS #####################################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the view.
        :param mouseEvent: the mouse event instance.
        """
        self.mousePressCenterPos = self.visibleRect().center()
        self.mousePressPos = mouseEvent.pos()
        if mouseEvent.buttons() & Qt.MidButton:
            viewport = self.viewport()
            viewport.setCursor(Qt.ClosedHandCursor)
        else:
            # middle button is used to move the viewport => everything
            # else needs to be forwared to the scene and graphicsitems
            super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the view.
        :param mouseEvent: the mouse event instance.
        """
        viewport = self.viewport()

        if mouseEvent.buttons() & Qt.MidButton:
            # move the view according to the delta between current mouse post and stored one
            viewport.setCursor(Qt.ClosedHandCursor)
            self.centerOn(self.mousePressCenterPos - mouseEvent.pos() + self.mousePressPos)
        else:
            # handle the movement of graphics item before anything else
            super().mouseMoveEvent(mouseEvent)

            if mouseEvent.buttons() & Qt.LeftButton:

                self.stopViewMove()

                # see if the mouse is outside the viewport
                viewportRect = viewport.rect()
                if not viewportRect.contains(mouseEvent.pos()):

                    # check if we have an item under the mouse => we are
                    # dragging it outside the viewport rect, hence we need
                    # to move the view so that the item stays visible
                    if self.scene().itemOnTopOf(self.mapToScene(mouseEvent.pos()), edges=False):

                        delta = QPointF()
                        
                        if mouseEvent.pos().x() < viewportRect.left():
                            delta.setX(mouseEvent.pos().x() - viewportRect.left())
                        elif mouseEvent.pos().x() > viewportRect.right():
                            delta.setX(mouseEvent.pos().x() - viewportRect.right())
                            
                        if mouseEvent.pos().y() < viewportRect.top():
                            delta.setY(mouseEvent.pos().y() - viewportRect.top())
                        elif mouseEvent.pos().y() > viewportRect.bottom():
                            delta.setY(mouseEvent.pos().y() - viewportRect.bottom())

                        if delta:
                            # clamp the value so the moving operation won't be too fast
                            delta.setX(clamp(delta.x(), -self.viewMoveBound, +self.viewMoveBound))
                            delta.setY(clamp(delta.y(), -self.viewMoveBound, +self.viewMoveBound))
                            # start the view move using the predefined rate
                            self.startViewMove(delta, self.viewMoveRate)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the view.
        :param mouseEvent: the mouse event instance.
        """
        self.mousePressCenterPos = None
        self.mousePressPos = None
        self.stopViewMove()
        viewport = self.viewport()
        viewport.setCursor(Qt.ArrowCursor)
        if mouseEvent.button() != Qt.MidButton:
            super().mouseReleaseEvent(mouseEvent)

    def viewportEvent(self, event):
        """
        Executed whenever the viewport changes.
        :param event: the viewport event instance.
        """
        # if the main view has been repainted, emit a
        # signal so that also the navigator can update
        if event.type() == QEvent.Paint:
            self.updated.emit()
        return super().viewportEvent(event)

    def wheelEvent(self, wheelEvent):
        """
        Executed when the mouse wheel is moved on the scene.
        :param wheelEvent: the mouse wheel event.
        """
        if wheelEvent.modifiers() & Qt.ControlModifier:

            # allow zooming with the mouse wheel
            zoom = self.zoom
            zoom += +(1 / ZoomControl.Step) if wheelEvent.angleDelta().y() > 0 else -(1 / ZoomControl.Step)
            zoom = clamp(zoom, ZoomControl.MinScale, ZoomControl.MaxScale)

            if zoom != self.zoom:
                # set transformations anchors
                self.setTransformationAnchor(QGraphicsView.NoAnchor)
                self.setResizeAnchor(QGraphicsView.NoAnchor)
                # save the old position
                old = self.mapToScene(wheelEvent.pos())
                # change the zoom level
                self.scaleView(zoom)
                self.zoomChanged.emit(zoom)
                # get the new position
                new = self.mapToScene(wheelEvent.pos())
                # move the scene so the mouse is centered
                move = new - old
                self.translate(move.x(), move.y())

        else:
            # handle default behavior (view scrolling)
            super().wheelEvent(wheelEvent)

    ############################################# AUXILIARY METHODS ####################################################

    def moveBy(self, *__args):
        """
        Move the view by the given delta.
        """
        if len(__args) == 1:
            delta = __args[0]
        elif len(__args) == 2:
            delta = QPointF(__args[0], __args[1])
        else:
            raise TypeError('too many arguments; expected {0}, got {1}'.format(2, len(__args)))
        self.centerOn(self.visibleRect().center() + delta)

    def scaleView(self, zoom):
        """
        Scale the Main View according to the given zoom.
        :param zoom: the zoom factor.
        """
        transform = self.transform()
        self.resetTransform()
        self.translate(transform.dx(), transform.dy())
        self.scale(zoom, zoom)
        self.zoom = zoom

    def startViewMove(self, delta, rate):
        """
        Start the view movement.
        :param delta: the delta movement.
        :param rate: amount of milliseconds between refresh.
        """
        if self.viewMove:
            self.stopViewMove()

        # move the view: this is needed before the timer so that if we keep
        # moving the mouse fast outside the viewport rectangle we still are able
        # to move the view; if we don't do this the timer may not have kicked in
        # and thus we remain with a non-moving view with a unfocused graphicsitem
        self.moveBy(delta)

        # setup a timer for future move, so the view keeps moving
        # also if we are not moving the mouse anymore but we are
        # holding the position outside the viewport rect
        self.viewMove = QTimer()
        self.viewMove.timeout.connect(partial(self.moveBy, delta))
        self.viewMove.start(rate)

    def stopViewMove(self):
        """
        Stop the view movement by destroying the timer object causing it.
        """
        if self.viewMove:

            try:
                self.viewMove.stop()
                self.viewMove.timeout.disconnect()
            except RuntimeError:
                pass
            finally:
                self.viewMove = None

    def visibleRect(self):
        """
        Returns the visible area in scene coordinates.
        :rtype: QRectF
        """
        return self.mapToScene(self.viewport().rect()).boundingRect()


class MainViewInspector(PaneWidget):
    """
    Base class for all the pane widgets used to inspect the main view.
    """
    __metaclass__ = ABCMeta

    ############################################## WIDGET INTERFACE ####################################################

    @abstractmethod
    def clearView(self):
        """
        Clear the widget from inspecting a diagram scene.
        """
        pass

    @abstractmethod
    def setView(self, mainview):
        """
        Set the widget view over the given main view.
        :param mainview: the main view from where to pick the scene to display.
        """
        pass


class Navigator(MainViewInspector):
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

        ############################################ SIGNAL HANDLERS ###################################################

        @pyqtSlot()
        def handleMainViewUpdated(self):
            """
            Executed whenever the navigator view needs to be updated.
            """
            self.viewport().update()

        @pyqtSlot('QRectF')
        def handleSceneRectChanged(self, rect):
            """
            Executed whenever the rectangle of the scene rendered in the navigator changes.
            :param rect: the new rectangle.
            """
            self.fitInView(rect, Qt.KeepAspectRatio)

        ############################################ WIDGET INTERFACE ##################################################

        def clearView(self):
            """
            Clear the widget from inspecting a diagram scene.
            """
            if self.mainview:

                try:
                    scene = self.mainview.scene()
                    scene.sceneRectChanged.disconnect()
                    self.mainview.updated.disconnect()
                except (RuntimeError, TypeError):
                    pass

                self.mainview = None

            self.viewport().update()

        def setView(self, mainview):
            """
            Set the navigator to display the DiagramScene in the given Main View.
            :param mainview: the mainView from where to pick the scene for the navigator.
            """
            self.clearView()

            if mainview:
                scene = mainview.scene()
                # attach signals to new slots
                scene.sceneRectChanged.connect(self.handleSceneRectChanged)
                mainview.updated.connect(self.handleMainViewUpdated)
                # fit the scene in the view
                self.setScene(scene)
                self.fitInView(mainview.sceneRect(), Qt.KeepAspectRatio)

            self.mainview = mainview
            self.viewport().update()

    def __init__(self, collapsed=False):
        """
        Initialize the navigator.
        :param collapsed: whether the widget should be collapsed by default.
        """
        super().__init__('Navigator', ':/icons/zoom', Navigator.Widget(), collapsed)

    ############################################## WIDGET INTERFACE ####################################################

    def clearView(self):
        """
        Clear the widget from inspecting a diagram scene.
        """
        self.widget.clearView()

    def setView(self, mainview):
        """
        Set the navigator over the given main view.
        :param mainview: the main view from where to pick the scene for the navigator.
        """
        self.widget.setView(mainview)

    ################################################ LAYOUT UPDATE #####################################################

    def update(self, *__args):
        """
        Update the widget refreshing all the children.
        """
        self.head.update()
        self.body.update()
        super().update(*__args)


class Overview(MainViewInspector):
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
            pass

        ############################################ EVENT HANDLERS ####################################################

        def contextMenuEvent(self, menuEvent):
            """
            Turn off the context menu for this view.
            :param menuEvent: the context menu event instance.
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

        ############################################ SIGNAL HANDLERS ###################################################

        @pyqtSlot()
        def handleSceneUpdated(self):
            """
            Executed whenever the overview view needs to be updated.
            """
            self.updateView()

        ############################################ WIDGET INTERFACE ##################################################

        def clearView(self):
            """
            Clear the widget from inspecting a diagram scene.
            """
            if self.mainview:

                try:
                    scene = self.mainview.scene()
                    scene.selectionChanged.disconnect()
                    scene.updated.disconnect()
                except (RuntimeError, TypeError):
                    pass
                finally:
                    self.mainview = None

            self.viewport().update()

        def updateView(self):
            """
            Update the Overview so that it renders only the elements in the scene discarding empty space.
            """
            if self.mainview:
                scene = self.mainview.scene()
                items = scene.items()
                if items:
                    X = set()
                    Y = set()
                    for item in items:
                        B = item.mapRectToScene(item.boundingRect())
                        X |= {B.left(), B.right()}
                        Y |= {B.top(), B.bottom()}

                    margin = 10
                    self.fitInView(QRectF(QPointF(min(X) - margin, min(Y) - margin),
                                          QPointF(max(X) + margin, max(Y) + margin)), Qt.KeepAspectRatio)

            self.viewport().update()

        def setView(self, mainview):
            """
            Set the navigator over the given main view.
            :param mainview: the mainView from where to pick the scene for the navigator.
            """
            self.clearView()

            if mainview:
                scene = mainview.scene()
                scene.selectionChanged.connect(self.handleSceneUpdated)
                scene.updated.connect(self.handleSceneUpdated)
                self.setScene(scene)

            self.mainview = mainview
            self.updateView()

    def __init__(self, collapsed=False):
        """
        Initialize the overview.
        :param collapsed: whether the widget should be collapsed by default.
        """
        super().__init__('Overview', ':/icons/zoom', Overview.Widget(), collapsed)

    ############################################## WIDGET INTERFACE ####################################################

    def clearView(self):
        """
        Clear the widget from inspecting a diagram scene.
        """
        self.widget.clearView()

    def setView(self, mainview):
        """
        Set the navigator over the given main view.
        :param mainview: the main view from where to pick the scene for the navigator.
        """
        self.widget.setView(mainview)

    ################################################ LAYOUT UPDATE #####################################################

    def update(self, *__args):
        """
        Update the widget refreshing all the children.
        """
        self.head.update()
        self.body.update()
        super().update(*__args)