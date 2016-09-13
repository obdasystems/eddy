# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


from time import time, sleep

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy import APPNAME, COPYRIGHT, VERSION

from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import rangeF


LICENSE = 'Licensed under the GNU General Public License v3'
CREDITS = 'Eddy is developed by the DASI Lab group of the\n' \
          '"Dipartimento di Ingegneria Informatica, Automatica e\n' \
          'Gestionale A. Ruberti" at Sapienza University of Rome"'


class Splash(QtWidgets.QSplashScreen):
    """
    This class implements Eddy's splash screen.
    It can be used with the context manager, i.e:

    >>> import sys
    >>> from PyQt5 import QtWidgets
    >>> app = QtWidgets.QApplication(sys.argv)
    >>> with Splash(mtime=5):
    >>>     app.do_something_heavy()

    will draw a 5 seconds (at least) splash screen on the screen.
    The with statement body can be used to initialize the application and process heavy stuff.
    """
    def __init__(self, parent=None, mtime=2):
        """
        Initialize Eddy's splash screen.
        :type parent: QWidget
        :type mtime: float
        """
        super().__init__(parent, QtGui.QPixmap(), QtCore.Qt.WindowStaysOnTopHint)
        pixmap = QtGui.QIcon(':/images/im_eddy_splash').pixmap(380 * self.devicePixelRatio())
        pixmap.setDevicePixelRatio(self.devicePixelRatio())
        self.setPixmap(pixmap)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.mtime = time() + mtime
        self.font1 = Font('Arial', 40, Font.Light)
        self.font1.setCapitalization(Font.SmallCaps)
        self.font2 = Font('Arial', 18, Font.Light)
        self.font2.setCapitalization(Font.SmallCaps)
        self.font3 = Font('Arial', 12, Font.Light)
        self.__spaceX = 0
        self.__spaceY = 0

    #############################################
    #   INTERFACE
    #################################

    def setSpaceX(self, spaceX):
        """
        Set the text horizontal spacing.
        :type spaceX: int
        """
        self.__spaceX = spaceX

    def setSpaceY(self, spaceY):
        """
        Set the text vertical spacing.
        :type spaceY: int
        """
        self.__spaceY = spaceY

    def sleep(self):
        """
        Wait for the splash screen to be drawn for at least 'mtime' seconds.
        """
        now = time()
        if now < self.mtime:
            for _ in rangeF(start=0, stop=self.mtime - now, step=0.1):
                # noinspection PyArgumentList
                QtWidgets.QApplication.processEvents()
                sleep(0.1)

    #############################################
    #   CONTEXT MANAGER
    #################################

    def __enter__(self):
        """
        Draw the splash screen.
        """
        self.show()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Remove the splash screen from the screen.
        """
        self.sleep()
        self.close()

    #############################################
    #   EVENTS
    #################################

    def paintEvent(self, paintEvent):
        """
        Executed when the splashscreen needs to be painted.
        :type paintEvent: QPaintEvent
        """
        painter = QtGui.QPainter(self)
        # APPNAME
        painter.setFont(self.font1)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1.0, QtCore.Qt.SolidLine))
        painter.drawText(QtCore.QRect(31 + self.__spaceX, 160 + self.__spaceY, 380, 400), QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft, APPNAME)
        # VERSION
        painter.setFont(self.font2)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1.0, QtCore.Qt.SolidLine))
        painter.drawText(QtCore.QRect(34 + self.__spaceX, 204 + self.__spaceY, 380, 400), QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft, 'Version {0}'.format(VERSION))
        # COPYRIGHT
        painter.setFont(self.font3)
        painter.setPen(QtGui.QPen(QtGui.QColor(122, 101, 104), 1.0, QtCore.Qt.SolidLine))
        painter.drawText(QtCore.QRect(0 + self.__spaceX, 254 + self.__spaceY, 360, 40), QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter, COPYRIGHT)
        # CREDITS
        painter.setFont(self.font3)
        painter.setPen(QtGui.QPen(QtGui.QColor(122, 101, 104), 1.0, QtCore.Qt.SolidLine))
        painter.drawText(QtCore.QRect(0 + self.__spaceX, 278 + self.__spaceY, 360, 80), QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter, CREDITS)
        # LICENSE
        painter.setFont(self.font3)
        painter.setPen(QtGui.QPen(QtGui.QColor(122, 101, 104), 1.0, QtCore.Qt.SolidLine))
        painter.drawText(QtCore.QRect(0 + self.__spaceX, 332 + self.__spaceY, 360, 40), QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter, LICENSE)