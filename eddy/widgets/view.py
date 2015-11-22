# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from eddy.datatypes import DiagramMode
from eddy.functions import clamp, connect, disconnect
from eddy.widgets.toolbar import ZoomControl

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QEvent, pyqtSlot, QPointF, QTimer
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsView


class MainView(QGraphicsView):
    """
    This class implements the main view displayed in the MDI area.
    """
    RubberBandDragBrush = QColor(97, 153, 242, 40)
    RubberBandDragPen = selectionPen = QPen(QColor(46, 97, 179), 1.0, Qt.SolidLine)

    updated = pyqtSignal()
    zoomChanged = pyqtSignal(float)

    def __init__(self, scene):
        """
        Initialize the main scene.
        :param scene: the graphics scene to render in the main view.
        """
        super().__init__(scene)
        self.viewMove = None
        self.viewMoveRate = 40
        self.viewMoveBound = 10
        self.mousePressCenterPos = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.zoom = 1.00

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(float)
    def onScaleChanged(self, zoom):
        """
        Executed when the scale factor changes (triggered by the Main Slider in the Toolbar)
        :param zoom: the scale factor.
        """
        self.scaleView(zoom)

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def drawForeground(self, painter, rect):
        """
        Draw the navigation cursor.
        :param painter: the active painter
        :param rect: the exposed rectangle
        """
        scene = self.scene()

        if scene.mode is DiagramMode.RubberBandDrag:
            if self.mousePressRect is not None:
                painter.setPen(MainView.RubberBandDragPen)
                painter.setBrush(MainView.RubberBandDragBrush)
                painter.drawRect(self.mousePressRect)

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the view.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()
        if mouseEvent.buttons() & Qt.MidButton:

            self.mousePressCenterPos = self.visibleRect().center()
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = None
            scene.setMode(DiagramMode.SceneDrag)
            viewport = self.viewport()
            viewport.setCursor(Qt.ClosedHandCursor)

        else:

            if mouseEvent.buttons() & Qt.LeftButton:
                if scene.mode is DiagramMode.Idle and not self.itemAt(mouseEvent.pos()):
                    self.mousePressPos = self.mapToScene(mouseEvent.pos())
                    self.mousePressRect = None
                    scene.setMode(DiagramMode.RubberBandDrag)

            super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the view.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()
        viewport = self.viewport()

        if mouseEvent.buttons() & Qt.MidButton:

            if scene.mode is DiagramMode.SceneDrag:
                viewport.setCursor(Qt.ClosedHandCursor)
                self.centerOn(self.mousePressCenterPos - mouseEvent.pos() + self.mousePressPos)

        else:

            super().mouseMoveEvent(mouseEvent)

            if mouseEvent.buttons() & Qt.LeftButton:

                # always call this before doing anything else: if we miss this call we may end up
                # with multiple move timers running and we won't be able to stop the view move
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

                    self.mousePressRect = QRectF(x, y, w, h)

                    items = scene.items()
                    selected = {x for x in scene.items(self.mousePressRect) if x.isNode() or x.isEdge()}

                    for item in items:
                        item.setSelected(item in selected)

                    viewport.update()

                if scene.mode in {DiagramMode.EdgeInsert, DiagramMode.NodeMove, DiagramMode.NodeResize,
                                  DiagramMode.EdgeBreakPointMove, DiagramMode.RubberBandDrag}:

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
                            delta.setX(clamp(delta.x(), -self.viewMoveBound, +self.viewMoveBound))
                            delta.setY(clamp(delta.y(), -self.viewMoveBound, +self.viewMoveBound))
                            self.startViewMove(delta, self.viewMoveRate)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the view.
        :param mouseEvent: the mouse event instance.
        """
        self.mousePressCenterPos = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.stopViewMove()

        scene = self.scene()
        viewport = self.viewport()
        viewport.setCursor(Qt.ArrowCursor)
        viewport.update()

        super().mouseReleaseEvent(mouseEvent)

        if scene.mode in {DiagramMode.SceneDrag, DiagramMode.RubberBandDrag}:
            # reset scene mode to idle only if the main view changed mode in the first place
            scene.setMode(DiagramMode.Idle)

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

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
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


__all__ = [
    'MainView',
]