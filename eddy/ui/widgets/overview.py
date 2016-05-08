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


from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtWidgets import QGraphicsView

from eddy.core.functions.signals import connect, disconnect


class Overview(QGraphicsView):
    """
    This class is used to display the active diagram overview.
    """
    def __init__(self, parent=None):
        """
        Initialize the Overview.
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setMinimumSize(QSize(216, 216))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setOptimizationFlags(QGraphicsView.DontAdjustForAntialiasing)
        self.setOptimizationFlags(QGraphicsView.DontSavePainterState)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.NoViewportUpdate)
        self.mousepressed = False
        self.view = None

    #############################################
    #   EVENTS
    #################################

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
            if self.view:
                self.mousepressed = True
                self.view.centerOn(self.mapToScene(mouseEvent.pos()))

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is moved on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            if self.view and self.mousepressed:
                self.view.centerOn(self.mapToScene(mouseEvent.pos()))

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            if self.view:
                self.mousepressed = False

    def wheelEvent(self, wheelEvent):
        """
        Turn off wheel event since we don't need to scroll anything.
        :type wheelEvent: QGraphicsSceneWheelEvent
        """
        pass

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def redraw(self):
        """
        Redraw the diagram within the overview.
        """
        if self.view:
            diagram = self.view.scene()
            shape = diagram.visibleRect(margin=10)
            if shape:
                self.fitInView(shape, Qt.KeepAspectRatio)
        viewport = self.viewport()
        viewport.update()

    #############################################
    #   INTERFACE
    #################################

    def browse(self, view):
        """
        Set the widget to browse the given view.
        :type view: DiagramView
        """
        self.reset()

        if view:
            diagram = view.scene()
            connect(diagram.selectionChanged, self.redraw)
            connect(diagram.sgnUpdated, self.redraw)
            self.setScene(diagram)

        self.view = view
        self.redraw()

    def reset(self):
        """
        Clear the widget from browsing the current view.
        """
        if self.view:

            try:
                diagram = self.view.scene()
                disconnect(diagram.selectionChanged, self.redraw)
                disconnect(diagram.sgnUpdated, self.redraw)
            except RuntimeError:
                pass
            finally:
                self.view = None

        viewport = self.viewport()
        viewport.update()

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QSize
        """
        return QSize(216, 216)