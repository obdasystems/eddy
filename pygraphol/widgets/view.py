# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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


from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QEvent, pyqtSlot
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import QGraphicsView, QWidget, QLabel, QHBoxLayout, QStyleOption, QStyle, QVBoxLayout


class MainView(QGraphicsView):
    """
    This class implements the main view displayed in the MDI area.
    """
    signalNavUpdate = pyqtSignal()

    def __init__(self, scene):
        """
        Initialize the main scene.
        :param scene: the graphics scene to render in the main view.
        """
        super().__init__(scene)
        self.zoom = 1.00

    ############################################### SIGNAL HANDLERS ####################################################

    def handleScaleChangedSignal(self, zoom):
        """
        Executed when the scale factor changes (triggered by the Main Slider in the Toolbar)
        :param zoom: the scale factor.
        """
        transform = self.transform()
        self.resetTransform()
        self.translate(transform.dx(), transform.dy())
        self.scale(zoom, zoom)
        self.zoom = zoom

    ############################################### EVENT HANDLERS #####################################################

    def viewportEvent(self, event):
        """
        Executed whenever the viewport changes.
        :param event: the viewport event instance.
        """
        # if the main view has been repainted, emit a
        # signal so that also the navigator can update
        if event.type() == QEvent.Paint:
            self.signalNavUpdate.emit()
        return super().viewportEvent(event)

    ############################################# AUXILIARY METHODS ####################################################

    def visibleRect(self):
        """
        Returns the visible area in scene coordinates.
        :rtype: QRectF
        """
        return self.mapToScene(self.viewport().rect()).boundingRect()


class Navigator(QWidget):
    """
    This class is used to display the current scene navigator.
    """

    ####################################################################################################################
    #                                                                                                                  #
    #   OVERVIEW                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    class Overview(QGraphicsView):
        """
        This class implements the view shown in the navigator.
        """
        navBrush = QColor(250, 140, 140, 100)
        navPen = QPen(QColor(250, 0, 0, 100), 1.0, Qt.SolidLine)

        def __init__(self, parent=None):
            """
            Initialize the overview.
            :param parent: the parent widget.
            """
            super().__init__(parent)
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

        ######################################### MOUSE EVENT HANDLERS #################################################

        def mousePressEvent(self, mouseEvent):
            """
            Executed when the mouse is pressed on the view.
            :param mouseEvent: the mouse event instance.
            """
            if self.mainview:
                self.mousepressed = True
                self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

        def mouseMoveEvent(self, mouseEvent):
            """
            Executed when the mouse is moved on the view.
            :param mouseEvent: the mouse event instance.
            """
            if self.mainview and self.mousepressed:
                self.mainview.centerOn(self.mapToScene(mouseEvent.pos()))

        def mouseReleaseEvent(self, mouseEvent):
            """
            Executed when the mouse is released from the view.
            :param mouseEvent: the mouse event instance.
            """
            if self.mainview:
                self.mousepressed = False

        ############################################ SIGNAL HANDLERS ###################################################

        @pyqtSlot()
        def handleNavUpdateSignal(self):
            """
            Triggered whenever the navigator view needs to be updated.
            """
            self.viewport().update()

        ########################################### AUXILIARY METHODS ##################################################

        def setView(self, mainview):
            """
            Set the navigator over the given main view.
            :param mainview: the mainView from where to pick the scene for the navigator.
            """
            if self.mainview:

                try:
                    self.mainview.signalNavUpdate.disconnect()
                except RuntimeError:
                    # which happens when the subwindow containing the view is closed
                    pass

            self.mainview = mainview

            if self.mainview:
                self.setScene(self.mainview.scene())
                self.fitInView(self.mainview.sceneRect(), Qt.KeepAspectRatio)
                self.mainview.signalNavUpdate.connect(self.handleNavUpdateSignal)
            else:
                # all subwindow closed => refresh so the foreground disappears
                self.viewport().update()

    ####################################################################################################################
    #                                                                                                                  #
    #   HEAD                                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    class Head(QWidget):

        def __init__(self, body, parent=None):
            """
            Initialize the header of the widget.
            :param body: the body this header is controlling.
            :param parent: the parent widget
            """
            super().__init__(parent)
            self.body = body
            self.iconUp = QPixmap(':/icons/arrow-up')
            self.iconDown = QPixmap(':/icons/arrow-down')
            self.headLabel = QLabel('Navigator')
            self.headImage = QLabel()

            self.headLayout = QHBoxLayout(self)
            self.headLayout.addWidget(self.headLabel, 1, Qt.AlignLeft)
            self.headLayout.addWidget(self.headImage, 0, Qt.AlignRight)
            self.headLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.headLayout.setContentsMargins(5, 4, 5, 4)

            self.setFixedSize(216, 26)
            self.setContentsMargins(0, 0, 0, 0)

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
            self.setCollapsed(self.body.isVisible())

        ############################################ AUXILIARY METHODS #################################################

        def setCollapsed(self, collapsed):
            """
            Set the collapsed status (of the attached body).
            :param collapsed: True if the body attached to the header should be collapsed, False otherwise.
            """
            self.body.setVisible(not collapsed)
            self.headImage.setPixmap(self.iconDown if collapsed else self.iconUp)
            self.setProperty('class', 'collapsed' if collapsed else 'normal')
            # refresh the widget stylesheet
            self.style().unpolish(self)
            self.style().polish(self)
            # refresh the label stylesheet
            self.headLabel.style().unpolish(self.headLabel)
            self.headLabel.style().polish(self.headLabel)
            self.update()

        ############################################## LAYOUT UPDATE ###################################################

        def update(self, *__args):
            """
            Update the widget refreshing all the children.
            """
            self.headLabel.update()
            self.headImage.update()
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
            self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)

    ####################################################################################################################
    #                                                                                                                  #
    #   BODY                                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    class Body(QWidget):

        def __init__(self, parent=None):
            """
            Initialize the body of the widget.
            :param parent: the parent widget.
            """
            super().__init__(parent)
            self.overview = Navigator.Overview()
            self.bodyLayout = QVBoxLayout(self)
            self.bodyLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.bodyLayout.setContentsMargins(0, 0, 0, 0)
            self.bodyLayout.addWidget(self.overview)
            self.setFixedSize(216, 216)
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
            self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def __init__(self, collapsed=False):
        """
        Initialize the navigator.
        :param collapsed: whether the widget should be collapsed by default.
        """
        super().__init__()

        self.body = Navigator.Body()
        self.head = Navigator.Head(self.body)
        self.head.setCollapsed(collapsed)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 4)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.head)
        self.mainLayout.addWidget(self.body)

    ################################################# SHORTCUTS ########################################################

    def setView(self, mainview):
        """
        Set the navigator over the given main view.
        :param mainview: the main view from where to pick the scene for the navigator.
        """
        self.body.overview.setView(mainview)

    ################################################ LAYOUT UPDATE #####################################################

    def update(self, *__args):
        """
        Update the widget refreshing all the children.
        """
        self.head.update()
        self.body.update()
        super().update(*__args)