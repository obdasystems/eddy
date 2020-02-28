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


from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.functions.signals import connect
from eddy.core.timer import PausableTimer


class Notification(QtWidgets.QWidget):
    """
    Extends QtWidgets.QWidget providing a notification popup widget.
    """
    def __init__(self, session, num):
        """
        Initialize the popup window.
        :type num: int
        """
        super().__init__(session)

        self.num = num

        self.hideAnimation = QtCore.QPropertyAnimation(self, b'windowOpacity', self)
        self.hideAnimation.setDuration(400)
        self.hideAnimation.setStartValue(1.0)
        self.hideAnimation.setEndValue(0.0)

        self.showAnimation = QtCore.QPropertyAnimation(self, b'windowOpacity', self)
        self.showAnimation.setDuration(400)
        self.showAnimation.setStartValue(0.0)
        self.showAnimation.setEndValue(1.0)

        self.sleepTimer = PausableTimer()
        self.sleepTimer.setSingleShot(True)

        self.session.installEventFilter(self)

        #############################################
        # SETUP UI
        #################################

        self.btnClose = QtWidgets.QPushButton(self)
        self.btnClose.setContentsMargins(0, 0, 0, 0)
        self.btnClose.setIcon(QtGui.QIcon(':/icons/18/ic_close_black'))
        self.btnClose.setIconSize(QtCore.QSize(18, 18))

        self.popupLabel = QtWidgets.QLabel(self)
        self.popupLabel.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.popupLabel.setFixedSize(QtCore.QSize(216, 88))
        self.popupLabel.setOpenExternalLinks(True)
        self.popupLabel.setTextFormat(QtCore.Qt.RichText)
        self.popupLabel.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.popupLabel.setWordWrap(True)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.addWidget(self.popupLabel, 1, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.mainLayout.addWidget(self.btnClose, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)

        self.setFixedSize(QtCore.QSize(260, 100))
        self.setWindowOpacity(0)
        self.setWindowFlags(QtCore.Qt.SplashScreen | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        connect(self.btnClose.clicked, self.onButtonCloseClicked)
        connect(self.hideAnimation.finished, self.onHideAnimationFinished)
        connect(self.showAnimation.finished, self.onShowAnimationFinished)
        connect(self.sleepTimer.timeout, self.onSleepTimerTimeout)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session (alias for Notification.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onButtonCloseClicked(self):
        """
        Executed when the close button is clicked.
        """
        self.dismiss()

    @QtCore.pyqtSlot()
    def onHideAnimationFinished(self):
        """
        Executed when the hide animation terminate.
        """
        self.hide()

    @QtCore.pyqtSlot()
    def onShowAnimationFinished(self):
        """
        Executed when the show animation terminate.
        """
        self.sleepTimer.start(5000)

    @QtCore.pyqtSlot()
    def onSleepTimerTimeout(self):
        """
        Executed when the sleep timer times out.
        """
        self.hideAnimation.start()

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, target, event):
        """
        Executed when the Session receives an event in order
        to keep the notification within the Session geometry boundaries.
        :type target: QtCore.QObject
        :type event: QtCore.QEvent
        :rtype: bool
        """
        if event.type() in {QtCore.QEvent.Move, QtCore.QEvent.Resize}:
            # UPDATE THE NOTIFICATION GEOMETRY
            self.setNotificationPos()
        return False

    def enterEvent(self, event):
        """
        Executed when the mouse enters the widget.
        :type event: QEvent
        """
        if self.sleepTimer.isActive() and not self.sleepTimer.isPaused():
            self.sleepTimer.pause()
        return super().enterEvent(event)

    def leaveEvent(self, event):
        """
        Executed when the mouse leaves the widget.
        :type event: QEvent
        """
        if self.sleepTimer.isPaused():
            self.sleepTimer.resume()
        return super().leaveEvent(event)

    def showEvent(self, showEvent):
        """
        Executed when the widget is shown.
        :type showEvent: QShowEvent
        """
        self.setNotificationPos()
        self.showAnimation.start()

    #############################################
    #   INTERFACE
    #################################

    def dismiss(self):
        """
        Dismiss the popup.
        """
        self.hideAnimation.stop()
        self.showAnimation.stop()
        self.sleepTimer.reset()
        self.hide()

    def setNotificationPos(self):
        """
        Set the position of the notification popup on the curret screen.
        """
        alignedRect = QtWidgets.QStyle.alignedRect(
            QtCore.Qt.LeftToRight,
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTop,
            self.size(),
            self.session.geometry())
        # MOVE TO CORRECT LOCATION
        alignedRect.translate(-10, (self.num * (self.height() + 10)) + 40)
        # SET THE NOTIFICATION GEOMETRY
        self.setGeometry(alignedRect)

    def setText(self, text):
        """
        Set the notification text.
        :type text: str
        """
        self.popupLabel.setText(text)