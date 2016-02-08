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


from time import time, sleep

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtWidgets import QSplashScreen, QApplication

from eddy import APPNAME, COPYRIGHT, VERSION

from eddy.core.datatypes import Font
from eddy.core.functions import rangeF


class SplashScreen(QSplashScreen):
    """
    This class implements Eddy's splash screen.
    It can be used with the context manager, i.e:

    >>> import sys
    >>> from PyQt5.QtWidgets import QApplication
    >>> app = QApplication(sys.argv)
    >>> with SplashScreen(min_splash_time=5):
    >>>     app.do_something_heavy()

    will draw a 5 seconds (at least) splash screen on the screen.
    The with statement body can be used to initialize the application and process heavy stuff.
    """
    def __init__(self, min_splash_time=2):
        """
        Initialize Eddy's splash screen.
        :type min_splash_time: float
        """
        super().__init__(QPixmap(':/images/splash'), Qt.WindowStaysOnTopHint)
        self.min_splash_time = time() + min_splash_time
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMask(self.pixmap().mask())
        self.setFixedSize(self.pixmap().width(), self.pixmap().height())

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def remaining(self):
        """
        Returns the amount of extra time the splashscreen needs to stay visible on the screen.
        :rtype: float
        """
        now = time()
        if now < self.min_splash_time:
            return self.min_splash_time - now
        return 0

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def wait(amount):
        """
        Sleep for the given amount of time.
        :type amount: float
        """
        if amount > 0:
            for _ in rangeF(start=0, stop=amount, step=0.1):
                # noinspection PyArgumentList
                QApplication.processEvents()
                sleep(0.1)

    ####################################################################################################################
    #                                                                                                                  #
    #   CONTEXT MANAGER                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def __enter__(self):
        """
        Draw the splash screen.
        """
        self.show()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Remove the splash screen from the screen.
        This will make sure that the splash screen is displayed for at least min_splash_time seconds.
        """
        self.wait(self.remaining)
        self.close()

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def paintEvent(self, paintEvent):
        """
        Executed when the splashscreen needs to be painted.
        :type paintEvent: QPaintEvent
        """
        super().paintEvent(paintEvent)
        painter = QPainter(self)
        painter.setFont(Font('Arial', 12, Font.Light))
        ## BOUNDING RECT (0, 194, 400, 86)
        painter.setPen(QPen(QColor(212, 212, 212), 1.0, Qt.SolidLine))
        painter.drawText(QRect(0, 202, 396, 14), Qt.AlignTop|Qt.AlignRight, '{} v{}'.format(APPNAME, VERSION))
        painter.drawText(QRect(0, 216, 396, 14), Qt.AlignTop|Qt.AlignRight, COPYRIGHT)
        painter.drawText(QRect(0, 230, 396, 14), Qt.AlignTop|Qt.AlignRight, 'Licensed under the GNU GPL v3')
        painter.drawText(QRect(0, 258, 396, 14), Qt.AlignTop|Qt.AlignRight, 'Starting up...')