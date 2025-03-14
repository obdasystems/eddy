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


from time import (
    time,
    sleep,
)

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy import APPNAME, VERSION
from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import rangeF

COPYRIGHT = '  Copyright © 2015-2017 Sapienza Università di Roma\n' \
            '  Copyright © 2017-2025 OBDA Systems'
LICENSE =   '   Licensed under the GNU General Public License v3'
CREDITS =   '      Developed by OBDA Systems'


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
        pixmap = QtGui.QIcon(':/images/im_eddy_splash').pixmap(380)
        pixmap.setDevicePixelRatio(self.devicePixelRatio())
        self.setPixmap(pixmap)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.mtime = time() + mtime
        self.font1 = Font(pixelSize=40, weight=Font.Medium)
        self.font1.setCapitalization(Font.SmallCaps)
        self.font2 = Font(pixelSize=18, weight=Font.Medium)
        self.font2.setCapitalization(Font.SmallCaps)
        self.font3 = Font(pixelSize=11, weight=Font.Medium)

    #############################################
    #   INTERFACE
    #################################

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
        painter.drawText(QtCore.QRect(31, 138, 380, 400),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft,
                         APPNAME)
        # VERSION
        painter.setFont(self.font2)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1.0, QtCore.Qt.SolidLine))
        painter.drawText(QtCore.QRect(34, 185, 380, 400),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft,
                         'Version {0}'.format(VERSION))
        # COPYRIGHT
        painter.setFont(self.font3)
        painter.setPen(QtGui.QPen(QtGui.QColor(122, 101, 104), 1.0, QtCore.Qt.SolidLine))
        painter.drawText(QtCore.QRect(0, 220, 360, 40),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter,
                         COPYRIGHT)
        # CREDITS
        painter.setFont(self.font3)
        painter.setPen(QtGui.QPen(QtGui.QColor(122, 101, 104), 1.0, QtCore.Qt.SolidLine))
        painter.drawText(QtCore.QRect(0, 273, 360, 80),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter,
                         CREDITS)
        # LICENSE
        painter.setFont(self.font3)
        painter.setPen(QtGui.QPen(QtGui.QColor(122, 101, 104), 1.0, QtCore.Qt.SolidLine))
        painter.drawText(QtCore.QRect(0, 286, 360, 40),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter,
                         LICENSE)
