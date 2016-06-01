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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt, QRectF, QLineF, QPointF, QTimer, QEvent
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsView, QApplication, QRubberBand

from eddy.core.datatypes.misc import DiagramMode
from eddy.core.diagram import Diagram
from eddy.core.functions.geometry import midpoint
from eddy.core.functions.misc import clamp, rangeF, snapF
from eddy.core.functions.signals import disconnect, connect

from eddy.ui.widgets.zoom import Zoom


class DiagramView(QGraphicsView):
    """
    This class implements the main view used to display diagrams within the MDI area.
    """
    MoveRate = 40
    MoveBound = 10
    PinchSize = 0.12

    sgnScaled = pyqtSignal(float)

    def __init__(self, diagram, mainwindow):
        """
        Initialize the view to browse the given diagram.
        :type diagram: Diagram
        :type mainwindow: MainWindow
        """
        super().__init__(diagram)

        self.mainwindow = mainwindow
        self.mousePressCenterPos = None
        self.mousePressPos = None
        self.moveTimer = None
        self.rubberBandOrigin = None
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.hide()
        self.pinchFactor = 1.0
        self.zoom = 1.0

        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setDragMode(DiagramView.NoDrag)
        self.setOptimizationFlags(DiagramView.DontAdjustForAntialiasing)
        self.setOptimizationFlags(DiagramView.DontSavePainterState)
        self.setViewportUpdateMode(DiagramView.MinimalViewportUpdate)
        connect(diagram.sgnUpdated, self.doUpdateView)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def diagram(self):
        """
        Returns the diagram being displayed by this view (alias for DiagramView.scene()).
        :rtype: Diagram
        """
        return self.scene()

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def doUpdateView(self):
        """
        Perform the redraw of the currently displayed diagram.
        """
        viewport = self.viewport()
        viewport.update()

    @pyqtSlot(float)
    def onZoomChanged(self, zoom):
        """
        Executed when the zoom factor changes (triggered by the Zoom widget).
        :type zoom: float
        """
        self.scaleView(zoom)

    #############################################
    #   EVENTS
    #################################

    def keyPressEvent(self, keyEvent):
        """
        Executed when a combination of key is pressed.
        :type keyEvent: QKeyEvent
        """
        key = keyEvent.key()
        modifiers = keyEvent.modifiers()

        if self.diagram.mode is DiagramMode.Idle and \
            modifiers & Qt.ControlModifier and \
                key in {Qt.Key_Minus, Qt.Key_Plus, Qt.Key_0}:

            zoom = Zoom.Default
            if key in {Qt.Key_Minus, Qt.Key_Plus}:
                zoom = self.zoom
                zoom += +Zoom.Step if key == Qt.Key_Plus else -Zoom.Step
                zoom = clamp(zoom, Zoom.Min, Zoom.Max)

            if zoom != self.zoom:
                self.scaleView(zoom)

        else:
            super().keyPressEvent(keyEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        mouseButtons = mouseEvent.buttons()
        mousePos = mouseEvent.pos()

        if mouseButtons & Qt.RightButton:

            #############################################
            # SCENE DRAG
            #################################

            visibleRect = self.visibleRect()
            self.mousePressCenterPos = visibleRect.center()
            self.mousePressPos = mousePos

        else:

            if mouseButtons & Qt.LeftButton:

                #############################################
                # RUBBERBAND SELECTION
                #################################

                if self.diagram.mode is DiagramMode.Idle and not self.itemAt(mousePos):
                    self.diagram.setMode(DiagramMode.RubberBandDrag)
                    self.rubberBandOrigin = self.mapToScene(mousePos)
                    self.rubberBand.setGeometry(QRectF(mousePos, mousePos).toRect())
                    self.rubberBand.show()

            super().mousePressEvent(mouseEvent)

    # noinspection PyArgumentList
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        mousePos = mouseEvent.pos()
        mouseButtons = mouseEvent.buttons()
        viewport = self.viewport()

        if mouseButtons & Qt.RightButton:

            if (mouseEvent.pos() - self.mousePressPos).manhattanLength() >= QApplication.startDragDistance():

                #############################################
                # SCENE DRAG
                #################################

                if self.diagram.mode is not DiagramMode.SceneDrag:
                    self.diagram.setMode(DiagramMode.SceneDrag)
                    viewport.setCursor(Qt.ClosedHandCursor)

                mousePos /= self.zoom
                mousePressPos = self.mousePressPos / self.zoom
                self.centerOn(self.mousePressCenterPos - mousePos + mousePressPos)

        else:

            super().mouseMoveEvent(mouseEvent)

            if mouseButtons & Qt.LeftButton:
                
                self.stopMove()

                if self.diagram.mode is DiagramMode.RubberBandDrag:

                    #############################################
                    # RUBBERBAND SELECTION
                    #################################

                    area = QRectF(self.mapFromScene(self.rubberBandOrigin), mousePos).normalized()
                    path = QPainterPath()
                    path.addRect(area)
                    self.diagram.setSelectionArea(self.mapToScene(path))
                    self.rubberBand.setGeometry(area.toRect())

                if self.diagram.mode in { DiagramMode.BreakPointMove,
                                          DiagramMode.InsertEdge,
                                          DiagramMode.MoveNode,
                                          DiagramMode.ResizeNode,
                                          DiagramMode.RubberBandDrag }:

                    #############################################
                    # VIEW SCROLLING
                    #################################

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
                            move.setX(clamp(move.x(), -DiagramView.MoveBound, DiagramView.MoveBound))
                            move.setY(clamp(move.y(), -DiagramView.MoveBound, DiagramView.MoveBound))
                            self.startMove(move, DiagramView.MoveRate)

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

        viewport = self.viewport()
        viewport.setCursor(Qt.ArrowCursor)
        viewport.update()

        super().mouseReleaseEvent(mouseEvent)

        if self.diagram.mode in {DiagramMode.RubberBandDrag, DiagramMode.SceneDrag}:
            self.diagram.setMode(DiagramMode.Idle)

    def wheelEvent(self, wheelEvent):
        """
        Executed when the mouse wheel is rotated on the diagram.
        :type wheelEvent: QWheelEvent
        """
        if wheelEvent.modifiers() & Qt.ControlModifier:

            wheelPos = wheelEvent.pos()
            wheelAngle = wheelEvent.angleDelta()

            zoom = self.zoom
            zoom += +Zoom.Step if wheelAngle.y() > 0 else -Zoom.Step
            zoom = clamp(zoom, Zoom.Min, Zoom.Max)

            if zoom != self.zoom:
                self.scaleViewOnPoint(zoom, wheelPos)

        else:
            super().wheelEvent(wheelEvent)

    def viewportEvent(self, viewportEvent):
        """
        Perform pinch to zoom feature to scale the viewport.
        :type viewportEvent: QTouchEvent
        """
        if viewportEvent.type() in {QEvent.TouchBegin, QEvent.TouchUpdate, QEvent.TouchEnd}:

            if viewportEvent.type() in {QEvent.TouchBegin, QEvent.TouchEnd}:
                self.pinchFactor = 1.0

            pts = viewportEvent.touchPoints()
            if len(pts) == 2:
                p0 = pts[0]
                p1 = pts[1]
                p2 = midpoint(p0.pos(), p1.pos())
                pinchFactor = QLineF(p0.pos(), p1.pos()).length() / QLineF(p0.startPos(), p1.startPos()).length()
                pinchFactor = snapF(pinchFactor, DiagramView.PinchSize)
                if pinchFactor != self.pinchFactor:
                    zoom = self.zoom
                    zoom += +Zoom.Step if pinchFactor > self.pinchFactor else -Zoom.Step
                    zoom = clamp(zoom, Zoom.Min, Zoom.Max)
                    self.pinchFactor = pinchFactor
                    if zoom != self.zoom:
                        self.scaleViewOnPoint(zoom, p2.toPoint())

        return super(DiagramView, self).viewportEvent(viewportEvent)

    #############################################
    #   INTERFACE
    #################################

    def drawBackground(self, painter, rect):
        """
        Draw the diagram background (grid).
        :type painter: QPainter
        :type rect: QRectF
        """
        if self.mainwindow.actionSnapToGrid.isChecked():
            s = Diagram.GridSize
            x = int(rect.left()) - (int(rect.left()) % s)
            y = int(rect.top()) - (int(rect.top()) % s)
            points = (QPointF(i, j) for i in rangeF(x, rect.right(), s) for j in rangeF(y, rect.bottom(), s))
            painter.setPen(Diagram.GridPen)
            painter.drawPoints(*points)

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
        Scale the view according to the given zoom.
        :type zoom: float
        """
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.resetTransform()
        self.translate(self.transform().dx(), self.transform().dy())
        self.scale(zoom, zoom)
        self.sgnScaled.emit(zoom)
        self.zoom = zoom

    def scaleViewOnPoint(self, zoom, point):
        """
        Scale the view according to the given zoom and make sure that the given point stays focused.
        :type zoom: float
        :type point: QPoint
        """
        p0 = self.mapToScene(point)
        self.scaleView(zoom)
        p1 = self.mapToScene(point)
        move = p1 - p0
        self.translate(move.x(), move.y())

    def startMove(self, delta, rate):
        """
        Start the view movement.
        :type delta: QPointF
        :type rate: float
        """
        if self.moveTimer:
            self.stopMove()

        # Move the view: this is needed before the timer so that if we keep
        # moving the mouse fast outside the viewport rectangle we still are able
        # to move the view; if we don't do this the timer may not have kicked in
        # and thus we remain with a non-moving view with a unfocused graphics item.
        self.moveBy(delta)

        # Setup a timer for future move, so the view keeps moving
        # also if we are not moving the mouse anymore but we are
        # holding the position outside the viewport rect.
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