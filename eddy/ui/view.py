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
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsView, QApplication, QRubberBand

from eddy.core.datatypes import DiagramMode
from eddy.core.functions import clamp, connect, disconnect, rangeF

from eddy.ui.scene import DiagramScene
from eddy.ui.toolbar import Zoom


class MainView(QGraphicsView):
    """
    This class implements the main view displayed in the MDI area.
    """
    MoveRate = 40
    MoveBound = 10

    scaled = pyqtSignal(float)

    def __init__(self, mainwindow, scene):
        """
        Initialize the main scene.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        """
        super().__init__(scene)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setOptimizationFlags(QGraphicsView.DontAdjustForAntialiasing)
        self.setOptimizationFlags(QGraphicsView.DontSavePainterState)
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.mainwindow = mainwindow
        self.mousePressCenterPos = None
        self.mousePressPos = None
        self.moveTimer = None
        self.rubberBandOrigin = None
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.hide()
        self.zoom = 1.00

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def updateView(self):
        """
        Update the Overview.
        """
        viewport = self.viewport()
        viewport.update()

    @pyqtSlot(float)
    def zoomChanged(self, zoom):
        """
        Executed when the zoom factor changes (triggered by the Zoom widget).
        :type zoom: float
        """
        self.scaleView(zoom)

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
        if self.mainwindow.snapToGrid:
            s = DiagramScene.GridSize
            x = int(rect.left()) - (int(rect.left()) % s)
            y = int(rect.top()) - (int(rect.top()) % s)
            painter.setPen(DiagramScene.GridPen)
            painter.drawPoints(*(QPointF(i, j) for i in rangeF(x, rect.right(), s) for j in rangeF(y, rect.bottom(), s)))

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def keyPressEvent(self, keyEvent):
        """
        Executed when a combination of key is pressed.
        :type keyEvent: QKeyEvent
        """
        scene = self.scene()
        key = keyEvent.key()
        modifiers = keyEvent.modifiers()

        if scene.mode is DiagramMode.Idle and \
            modifiers & Qt.ControlModifier and \
                key in {Qt.Key_Minus, Qt.Key_Plus, Qt.Key_0}:

            if key == Qt.Key_Minus:
                zoom = self.zoom - Zoom.Step
            elif key == Qt.Key_Plus:
                zoom = self.zoom + Zoom.Step
            else:
                zoom = Zoom.Default

            zoom = clamp(zoom, Zoom.Min, Zoom.Max)

            if zoom != self.zoom:
                self.setTransformationAnchor(QGraphicsView.NoAnchor)
                self.setResizeAnchor(QGraphicsView.NoAnchor)
                self.scaleView(zoom)
                self.scaled.emit(zoom)

        else:
            super().keyPressEvent(keyEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()
        mouseButtons = mouseEvent.buttons()
        mousePos = mouseEvent.pos()

        if mouseButtons & Qt.RightButton:

            ############################################################################################################
            #                                                                                                          #
            #                                              SCENE DRAG                                                  #
            #                                                                                                          #
            ############################################################################################################

            visibleRect = self.visibleRect()
            self.mousePressCenterPos = visibleRect.center()
            self.mousePressPos = mousePos

        else:

            if mouseButtons & Qt.LeftButton:

                ########################################################################################################
                #                                                                                                      #
                #                                      RUBBERBAND SELECTION                                            #
                #                                                                                                      #
                ########################################################################################################

                if scene.mode is DiagramMode.Idle and not self.itemAt(mousePos):
                    self.rubberBandOrigin = self.mapToScene(mousePos)
                    self.rubberBand.setGeometry(QRectF(mousePos, mousePos).toRect())
                    self.rubberBand.show()
                    scene.setMode(DiagramMode.RubberBandDrag)

            super().mousePressEvent(mouseEvent)

    # noinspection PyArgumentList
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()
        mousePos = mouseEvent.pos()
        mouseButtons = mouseEvent.buttons()
        viewport = self.viewport()

        if mouseButtons & Qt.RightButton:

            if (mouseEvent.pos() - self.mousePressPos).manhattanLength() >= QApplication.startDragDistance():

                ########################################################################################################
                #                                                                                                      #
                #                                            SCENE DRAG                                                #
                #                                                                                                      #
                ########################################################################################################

                if scene.mode is not DiagramMode.SceneDrag:
                    scene.setMode(DiagramMode.SceneDrag)
                    viewport.setCursor(Qt.ClosedHandCursor)

                mousePos /= self.zoom
                mousePressPos = self.mousePressPos / self.zoom
                self.centerOn(self.mousePressCenterPos - mousePos + mousePressPos)

        else:

            super().mouseMoveEvent(mouseEvent)

            if mouseButtons & Qt.LeftButton:
                
                self.stopMove()

                if scene.mode is DiagramMode.RubberBandDrag:

                    ####################################################################################################
                    #                                                                                                  #
                    #                                       RUBBERBAND DRAG                                            #
                    #                                                                                                  #
                    ####################################################################################################

                    area = QRectF(self.mapFromScene(self.rubberBandOrigin), mousePos).normalized()
                    path = QPainterPath()
                    path.addRect(area)
                    scene.setSelectionArea(self.mapToScene(path))
                    self.rubberBand.setGeometry(area.toRect())

                if scene.mode in { DiagramMode.BreakPointMove,
                                   DiagramMode.InsertEdge,
                                   DiagramMode.MoveNode,
                                   DiagramMode.ResizeNode,
                                   DiagramMode.RubberBandDrag }:

                    ####################################################################################################
                    #                                                                                                  #
                    #                                      VIEW SCROLLING                                              #
                    #                                                                                                  #
                    ####################################################################################################

                    R = viewport.rect()
                    if not R.contains(mousePos):

                        move = QPointF(0, 0)

                        if mousePos.x() < R.left():
                            move.setX(mousePos.x() - R.left())
                        elif mousePos.x() > R.right():
                            move.setX(mousePos.x() - R.right())

                        if mousePos.y() < R.top():
                            move.setY(mousePos.y() - R.top())
                        elif mousePos.y() > R.bottom():
                            move.setY(mousePos.y() - R.bottom())

                        if move:
                            move.setX(clamp(move.x(), -MainView.MoveBound, +MainView.MoveBound))
                            move.setY(clamp(move.y(), -MainView.MoveBound, +MainView.MoveBound))
                            self.startMove(move, MainView.MoveRate)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        self.mousePressCenterPos = None
        self.mousePressPos = None
        self.rubberBandOrigin = None
        self.rubberBand.hide()

        self.stopMove()

        scene = self.scene()
        viewport = self.viewport()
        viewport.setCursor(Qt.ArrowCursor)
        viewport.update()

        super().mouseReleaseEvent(mouseEvent)

        if scene.mode in {DiagramMode.RubberBandDrag, DiagramMode.SceneDrag}:
            scene.setMode(DiagramMode.Idle)

    def wheelEvent(self, wheelEvent):
        """
        Executed when the mouse wheel is moved on the scene.
        :type wheelEvent: QWheelEvent
        """
        if wheelEvent.modifiers() & Qt.ControlModifier:

            wheelPos = wheelEvent.pos()
            wheelAngle = wheelEvent.angleDelta()

            zoom = self.zoom
            zoom += +Zoom.Step if wheelAngle.y() > 0 else -Zoom.Step
            zoom = clamp(zoom, Zoom.Min, Zoom.Max)

            if zoom != self.zoom:
                self.setTransformationAnchor(QGraphicsView.NoAnchor)
                self.setResizeAnchor(QGraphicsView.NoAnchor)
                p1 = self.mapToScene(wheelPos)
                self.scaleView(zoom)
                self.scaled.emit(zoom)
                p2 = self.mapToScene(wheelPos)
                move = p2 - p1
                self.translate(move.x(), move.y())

        else:
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
        Scale the view according to the given zoom.
        :type zoom: float
        """
        transform = self.transform()
        self.resetTransform()
        self.translate(transform.dx(), transform.dy())
        self.scale(zoom, zoom)
        self.zoom = zoom

    def startMove(self, delta, rate):
        """
        Start the view movement.
        :type delta: QPointF
        :type rate: float
        """
        if self.moveTimer:
            self.stopMove()

        # move the view: this is needed before the timer so that if we keep
        # moving the mouse fast outside the viewport rectangle we still are able
        # to move the view; if we don't do this the timer may not have kicked in
        # and thus we remain with a non-moving view with a unfocused graphicsitem
        self.moveBy(delta)

        # setup a timer for future move, so the view keeps moving
        # also if we are not moving the mouse anymore but we are
        # holding the position outside the viewport rect
        self.moveTimer = QTimer()
        connect(self.moveTimer.timeout, self.moveBy, delta)
        self.moveTimer.start(rate)

    def stopMove(self):
        """
        Stop the view movement by destroying the timer object causing it.
        """
        if self.moveTimer:
            self.moveTimer.stop()
            disconnect(self.moveTimer.timeout)
            self.moveTimer = None

    def visibleRect(self):
        """
        Returns the visible area in scene coordinates.
        :rtype: QRectF
        """
        return self.mapToScene(self.viewport().rect()).boundingRect()