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


from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsView

from eddy.core.datatypes import DiagramMode
from eddy.core.functions import clamp, connect, disconnect, rangeF

from eddy.ui.scene import DiagramScene
from eddy.ui.toolbar import ZoomControl


class MainView(QGraphicsView):
    """
    This class implements the main view displayed in the MDI area.
    """
    MoveRate = 40
    MoveBound = 10
    RubberBandDragBrush = QColor(97, 153, 242, 40)
    RubberBandDragPen = QPen(QColor(46, 97, 179), 1.0, Qt.SolidLine)

    zoomChanged = pyqtSignal(float)

    def __init__(self, scene):
        """
        Initialize the main scene.
        :type scene: DiagramScene
        """
        super().__init__(scene)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setOptimizationFlags(QGraphicsView.DontAdjustForAntialiasing)
        self.setOptimizationFlags(QGraphicsView.DontSavePainterState)
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.settings = scene.settings
        self.mousePressCenterPos = None
        self.mousePressPos = None
        self.mousePressRubberBand = None
        self.viewMove = None
        self.zoom = 1.00

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(float)
    def scaleChanged(self, zoom):
        """
        Executed when the scale factor changes (triggered by the Zoom control in the Toolbar).
        :type zoom: float
        """
        self.scaleView(zoom)

    @pyqtSlot()
    def updateView(self):
        """
        Update the Overview.
        """
        viewport = self.viewport()
        viewport.update()

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def drawBackground(self, painter, rect):
        """
        Draw the scene background.
        :type painter: QPainter
        :type rect: QRectF
        """
        if self.settings.value('scene/snap_to_grid', False, bool):
            startX = int(rect.left()) - (int(rect.left()) % DiagramScene.GridSize)
            startY = int(rect.top()) - (int(rect.top()) % DiagramScene.GridSize)
            painter.setPen(DiagramScene.GridPen)
            painter.drawPoints(*(QPointF(x, y) for x in rangeF(startX, rect.right(), DiagramScene.GridSize) \
                                                 for y in rangeF(startY, rect.bottom(), DiagramScene.GridSize)))

    def drawForeground(self, painter, rect):
        """
        Draw the navigation cursor.
        :type painter: QPainter
        :type rect: QRectF
        """
        scene = self.scene()

        if scene.mode is DiagramMode.RubberBandDrag:
            if self.mousePressRubberBand is not None:
                painter.setPen(MainView.RubberBandDragPen)
                painter.setBrush(MainView.RubberBandDragBrush)
                painter.drawRect(self.mousePressRubberBand)

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if mouseEvent.buttons() & Qt.RightButton:

            visibleRect = self.visibleRect()
            self.mousePressCenterPos = visibleRect.center()
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRubberBand = None

        else:

            if mouseEvent.buttons() & Qt.LeftButton:
                if scene.mode is DiagramMode.Idle and not self.itemAt(mouseEvent.pos()):
                    self.mousePressPos = self.mapToScene(mouseEvent.pos())
                    self.mousePressRubberBand = None
                    scene.setMode(DiagramMode.RubberBandDrag)

            super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()
        viewport = self.viewport()

        if mouseEvent.buttons() & Qt.RightButton:

            if scene.mode is not DiagramMode.SceneDrag:
                scene.setMode(DiagramMode.SceneDrag)
                viewport.setCursor(Qt.ClosedHandCursor)

            self.centerOn(self.mousePressCenterPos - mouseEvent.pos() + self.mousePressPos)

        else:

            super().mouseMoveEvent(mouseEvent)

            if mouseEvent.buttons() & Qt.LeftButton:

                # Always call this before doing anything else: if we miss this call we may end up
                # with multiple move timers running and we won't be able to stop the view move.
                self.stopViewMove()

                if scene.mode is DiagramMode.RubberBandDrag:

                    ####################################################################################################
                    #                                                                                                  #
                    #   RUBBERBAND SELECTION                                                                           #
                    #                                                                                                  #
                    ####################################################################################################

                    x = self.mousePressPos.x()
                    y = self.mousePressPos.y()
                    w = self.mapToScene(mouseEvent.pos()).x() - x
                    h = self.mapToScene(mouseEvent.pos()).y() - y

                    self.mousePressRubberBand = QRectF(x, y, w, h)

                    items = scene.items()
                    selected = {x for x in scene.items(self.mousePressRubberBand) if x.node or x.edge}

                    for item in items:
                        item.setSelected(item in selected)

                    viewport.update()

                if scene.mode in {DiagramMode.EdgeInsert, DiagramMode.NodeMove,
                                  DiagramMode.NodeResize, DiagramMode.EdgeBreakPointMove,
                                  DiagramMode.RubberBandDrag}:

                    ####################################################################################################
                    #                                                                                                  #
                    #   VIEW SCROLLING                                                                                 #
                    #                                                                                                  #
                    ####################################################################################################

                    viewportRect = viewport.rect()
                    if not viewportRect.contains(mouseEvent.pos()):

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
                            delta.setX(clamp(delta.x(), -MainView.MoveBound, +MainView.MoveBound))
                            delta.setY(clamp(delta.y(), -MainView.MoveBound, +MainView.MoveBound))
                            self.startViewMove(delta, MainView.MoveRate)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        self.mousePressCenterPos = None
        self.mousePressPos = None
        self.mousePressRubberBand = None
        self.stopViewMove()

        scene = self.scene()
        viewport = self.viewport()
        viewport.setCursor(Qt.ArrowCursor)
        viewport.update()

        super().mouseReleaseEvent(mouseEvent)

        if scene.mode in {DiagramMode.SceneDrag, DiagramMode.RubberBandDrag}:
            # reset scene mode to idle only if the main view changed mode in the first place
            scene.setMode(DiagramMode.Idle)

    def wheelEvent(self, wheelEvent):
        """
        Executed when the mouse wheel is moved on the scene.
        :type wheelEvent: QWheelEvent
        """
        if wheelEvent.modifiers() & Qt.ControlModifier:

            # allow zooming with the mouse wheel
            zoom = self.zoom
            zoom += +ZoomControl.Step if wheelEvent.angleDelta().y() > 0 else -ZoomControl.Step
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

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def moveBy(self, *__args):
        """
        Move the view by the given delta.
        """
        if len(__args) == 1:
            delta = __args[0]
        elif len(__args) == 2:
            delta = QPointF(__args[0], __args[1])
        else:
            raise TypeError('too many arguments; expected {}, got {}'.format(2, len(__args)))
        self.centerOn(self.visibleRect().center() + delta)

    def scaleView(self, zoom):
        """
        Scale the Main View according to the given zoom.
        :type zoom: float
        """
        transform = self.transform()
        self.resetTransform()
        self.translate(transform.dx(), transform.dy())
        self.scale(zoom, zoom)
        self.zoom = zoom

    def startViewMove(self, delta, rate):
        """
        Start the view movement.
        :type delta: QPointF
        :type rate: float
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
        connect(self.viewMove.timeout, self.moveBy, delta)
        self.viewMove.start(rate)

    def stopViewMove(self):
        """
        Stop the view movement by destroying the timer object causing it.
        """
        if self.viewMove:
            self.viewMove.stop()
            disconnect(self.viewMove.timeout)
            self.viewMove = None

    def visibleRect(self):
        """
        Returns the visible area in scene coordinates.
        :rtype: QRectF
        """
        return self.mapToScene(self.viewport().rect()).boundingRect()