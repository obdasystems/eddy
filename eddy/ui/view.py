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


from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.commands.nodes import CommandNodeMove
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.diagram import Diagram
from eddy.core.functions.geometry import midpoint
from eddy.core.functions.misc import clamp, snapF
from eddy.core.functions.signals import disconnect, connect


class DiagramView(QtWidgets.QGraphicsView):
    """
    This class implements the main view used to display diagrams within the MDI area.
    """
    MoveRate = 40
    MoveBound = 10
    MoveModes = {
        DiagramMode.EdgeBreakPointMove,
        DiagramMode.EdgeAdd,
        DiagramMode.NodeMove,
        DiagramMode.NodeResize,
        DiagramMode.LabelMove,
        DiagramMode.RubberBandDrag
    }

    PinchGuard = (0.70, 1.50)
    PinchSize = 0.12
    ZoomDefault = 1.00
    ZoomMin = 0.10
    ZoomMax = 5.00
    ZoomStep = 0.10

    sgnScaled = QtCore.pyqtSignal(float)

    def __init__(self, diagram, session):
        """
        Initialize the view to browse the given diagram.
        :type diagram: Diagram
        :type session: Session
        """
        super().__init__(diagram)

        self.mp_CenterPos = None
        self.mp_Pos = None
        self.mv_Timer = None

        self.rubberBandOrigin = None
        self.rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.rubberBand.hide()
        self.pinchFactor = 1.0
        self.session = session
        self.zoom = 1.0

        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setDragMode(DiagramView.NoDrag)
        self.setGridSize(Diagram.GridSize)
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

    @QtCore.pyqtSlot()
    def doUpdateView(self):
        """
        Perform the redraw of the currently displayed diagram.
        """
        viewport = self.viewport()
        viewport.update()

    @QtCore.pyqtSlot(float)
    def onZoomChanged(self, zoom):
        """
        Executed when the zoom factor changes (triggered by the Zoom widget).
        :type zoom: float
        """
        self.scaleView(zoom)

    #############################################
    #   EVENTS
    #################################

    # noinspection PyTypeChecker
    def keyPressEvent(self, keyEvent):
        """
        Executed when a combination of key is pressed.
        :type keyEvent: QKeyEvent
        """
        key = keyEvent.key()
        modifiers = keyEvent.modifiers()
        if self.diagram.mode is DiagramMode.Idle:

            if modifiers & QtCore.Qt.ControlModifier and \
                key in {QtCore.Qt.Key_Minus, QtCore.Qt.Key_Plus, QtCore.Qt.Key_0}:

                #############################################
                # ZOOM SHORTCUT
                #################################

                zoom = DiagramView.ZoomDefault
                if key in {QtCore.Qt.Key_Minus, QtCore.Qt.Key_Plus}:
                    zoom = self.zoom
                    zoom += +DiagramView.ZoomStep if key == QtCore.Qt.Key_Plus else -DiagramView.ZoomStep
                    zoom = clamp(zoom, DiagramView.ZoomMin, DiagramView.ZoomMax)

                if zoom != self.zoom:
                    self.scaleView(zoom)

            else:

                #############################################
                # NODE MOVEMENT
                #################################

                # NOTE: while usually node movement is handled in the Diagram class,
                # movements performed using the keyboard needs to be handled right here.
                # The reason behind is that keyboard arrows are used to scroll the DiagramView
                # viewport, we if we intercept the event in the Diagram class (by calling
                # super().keyPressEvent()) to perform the node move, we will also see the
                # viewport moving, and this is not the desired behavior. We intercept the
                # event here instead and perform the node move.

                selected = self.diagram.selectedNodes()
                if selected and key in {QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Left, QtCore.Qt.Key_Right}:
                    self.diagram.setMode(DiagramMode.NodeMove)
                    offset = QtCore.QPointF(0, 0)
                    if keyEvent.key() == QtCore.Qt.Key_Up:
                        offset += QtCore.QPointF(0, -Diagram.KeyMoveFactor)
                    if keyEvent.key() == QtCore.Qt.Key_Down:
                        offset += QtCore.QPointF(0, +Diagram.KeyMoveFactor)
                    if keyEvent.key() == QtCore.Qt.Key_Left:
                        offset += QtCore.QPointF(-Diagram.KeyMoveFactor, 0)
                    if keyEvent.key() == QtCore.Qt.Key_Right:
                        offset += QtCore.QPointF(+Diagram.KeyMoveFactor, 0)
                    initData = self.diagram.setupMove(selected)
                    moveData = self.diagram.completeMove(initData, offset)
                    self.session.undostack.push(CommandNodeMove(self.diagram, initData, moveData))
                    self.diagram.setMode(DiagramMode.Idle)
                else:
                    super().keyPressEvent(keyEvent)
        else:
            super().keyPressEvent(keyEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        mouseButtons = mouseEvent.buttons()
        mousePos = mouseEvent.pos()

        if mouseButtons & QtCore.Qt.RightButton:

            #############################################
            # SCENE DRAG
            #################################

            visibleRect = self.visibleRect()
            self.mp_CenterPos = visibleRect.center()
            self.mp_Pos = mousePos

        else:

            if mouseButtons & QtCore.Qt.LeftButton:

                #############################################
                # RUBBERBAND SELECTION
                #################################

                if self.diagram.mode is DiagramMode.Idle and not self.itemAt(mousePos):
                    self.diagram.setMode(DiagramMode.RubberBandDrag)
                    self.rubberBandOrigin = self.mapToScene(mousePos)
                    self.rubberBand.setGeometry(QtCore.QRectF(mousePos, mousePos).toRect())
                    self.rubberBand.show()

            super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        mousePos = mouseEvent.pos()
        mouseButtons = mouseEvent.buttons()
        viewport = self.viewport()

        if mouseButtons & QtCore.Qt.RightButton:

            if self.mp_Pos is not None:

                if (mousePos - self.mp_Pos).manhattanLength() >= QtWidgets.QApplication.startDragDistance():

                    #############################################
                    # SCENE DRAG
                    #################################

                    if self.diagram.mode is not DiagramMode.SceneDrag:
                        self.diagram.setMode(DiagramMode.SceneDrag)
                        viewport.setCursor(QtCore.Qt.ClosedHandCursor)

                    mousePos /= self.zoom
                    mousePressPos = self.mp_Pos / self.zoom
                    self.centerOn(self.mp_CenterPos - mousePos + mousePressPos)

        else:

            super().mouseMoveEvent(mouseEvent)

            if mouseButtons & QtCore.Qt.LeftButton:
                
                self.stopMove()

                if self.diagram.mode is DiagramMode.RubberBandDrag:

                    #############################################
                    # RUBBERBAND SELECTION
                    #################################

                    originPos = self.mapFromScene(self.rubberBandOrigin)
                    area = QtCore.QRectF(originPos, mousePos).normalized()
                    self.rubberBand.setGeometry(area.toRect())

                if self.diagram.mode in DiagramView.MoveModes:

                    #############################################
                    # VIEW MOVE
                    #################################

                    R = viewport.rect()
                    if not R.contains(mousePos):

                        move = QtCore.QPointF(0, 0)
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
        mousePos = mouseEvent.pos()
        mouseButton = mouseEvent.button()

        self.stopMove()

        if mouseButton == QtCore.Qt.LeftButton:

            if self.diagram.mode is DiagramMode.RubberBandDrag:

                #############################################
                # RUBBERBAND SELECTION
                #################################

                area = QtCore.QRectF(self.rubberBandOrigin, self.mapToScene(mousePos)).normalized()
                collection = set(self.diagram.items(area, edges=False))
                for node in collection:
                    node.setSelected(True)
                    for edge in node.edges:
                        if edge.other(node) in collection:
                            edge.setSelected(True)

        #############################################
        # RESET STATE
        #################################

        self.rubberBandOrigin = None
        self.rubberBand.hide()
        self.mp_CenterPos = None
        self.mp_Pos = None

        viewport = self.viewport()
        viewport.setCursor(QtCore.Qt.ArrowCursor)
        viewport.update()

        super().mouseReleaseEvent(mouseEvent)

        if self.diagram.mode in {DiagramMode.RubberBandDrag, DiagramMode.SceneDrag}:
            self.diagram.setMode(DiagramMode.Idle)

    def wheelEvent(self, wheelEvent):
        """
        Executed when the mouse wheel is rotated on the diagram.
        :type wheelEvent: QWheelEvent
        """
        if wheelEvent.modifiers() & QtCore.Qt.ControlModifier:
            pos = wheelEvent.pos()
            angle = wheelEvent.angleDelta()
            zoom = self.zoom
            zoom += +DiagramView.ZoomStep if angle.y() > 0 else -DiagramView.ZoomStep
            zoom = clamp(zoom, DiagramView.ZoomMin, DiagramView.ZoomMax)
            if zoom != self.zoom:
                self.scaleViewOnPoint(zoom, pos)
        else:
            super().wheelEvent(wheelEvent)

    def viewportEvent(self, viewportEvent):
        """
        Perform pinch to zoom feature to scale the viewport.
        :type viewportEvent: QTouchEvent
        """
        if viewportEvent.type() in {QtCore.QEvent.TouchBegin, QtCore.QEvent.TouchUpdate, QtCore.QEvent.TouchEnd}:

            if viewportEvent.type() in {QtCore.QEvent.TouchBegin, QtCore.QEvent.TouchEnd}:
                self.pinchFactor = 1.0

            pts = viewportEvent.touchPoints()
            if len(pts) == 2:
                p0 = pts[0]
                p1 = pts[1]
                p2 = midpoint(p0.pos(), p1.pos())
                pinchFactor = QtCore.QLineF(p0.pos(), p1.pos()).length() / QtCore.QLineF(p0.startPos(), p1.startPos()).length()
                pinchFactor = snapF(pinchFactor, DiagramView.PinchSize)
                if pinchFactor < DiagramView.PinchGuard[0] or pinchFactor > DiagramView.PinchGuard[1]:
                    if pinchFactor != self.pinchFactor:
                        zoom = self.zoom
                        zoom += +DiagramView.ZoomStep if pinchFactor > self.pinchFactor else -DiagramView.ZoomStep
                        zoom = clamp(zoom, DiagramView.ZoomMin, DiagramView.ZoomMax)
                        self.pinchFactor = pinchFactor
                        if zoom != self.zoom:
                            self.scaleViewOnPoint(zoom, p2.toPoint())

        return super().viewportEvent(viewportEvent)

    #############################################
    #   INTERFACE
    #################################

    def moveBy(self, *__args):
        """
        Move the view by the given delta.
        """
        if len(__args) == 1:
            delta = __args[0]
        elif len(__args) == 2:
            delta = QtCore.QPointF(__args[0], __args[1])
        else:
            raise TypeError('too many arguments; expected {0}, got {1}'.format(2, len(__args)))
        self.centerOn(self.visibleRect().center() + delta)

    def scaleView(self, zoom):
        """
        Scale the view according to the given zoom.
        :type zoom: float
        """
        self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)
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

    def setGridSize(self, size):
        """
        Sets the grid size.
        """
        action = self.session.action('toggle_grid')
        size = clamp(size, 0)
        if size <= 0 or not action.isChecked():
            brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        else:
            image = QtGui.QImage(size, size, QtGui.QImage.Format_RGB32)
            image.fill(QtCore.Qt.white)
            painter = QtGui.QPainter(image)
            painter.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(80, 80, 80, 255)), 1, QtCore.Qt.SolidLine))
            painter.drawPoint(QtCore.QPointF(0, 0))
            painter.end()
            brush = QtGui.QBrush(image)
        self.setBackgroundBrush(brush)

    def startMove(self, delta, rate):
        """
        Start the view movement.
        :type delta: QtCore.QPointF
        :type rate: float
        """
        if self.mv_Timer:
            self.stopMove()

        # Move the view: this is needed before the timer so that if we keep
        # moving the mouse fast outside the viewport rectangle we still are able
        # to move the view; if we don't do this the timer may not have kicked in
        # and thus we remain with a non-moving view with a unfocused graphics item.
        self.moveBy(delta)

        # Setup a timer for future move, so the view keeps moving
        # also if we are not moving the mouse anymore but we are
        # holding the position outside the viewport rect.
        self.mv_Timer = QtCore.QTimer()
        connect(self.mv_Timer.timeout, self.moveBy, delta)
        self.mv_Timer.start(rate)

    def stopMove(self):
        """
        Stop the view movement by destroying the timer object causing it.
        """
        if self.mv_Timer:
            self.mv_Timer.stop()
            disconnect(self.mv_Timer.timeout)
            self.mv_Timer = None

    def visibleRect(self):
        """
        Returns the visible area in scene coordinates.
        :rtype: QtCore.QRectF
        """
        return self.mapToScene(self.viewport().rect()).boundingRect()