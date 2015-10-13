#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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

__author__ = 'Daniele Pantaleone'
__email__ = 'danielepantaleone@me.com'
__copyright__ = 'Copyright 2015, Daniele Pantaleone'
__organization__ = 'Sapienza - University Of Rome'
__appname__ = 'Grapholed'
__version__ = '0.2'
__status__ = 'Development'
__license__ = 'GPL'


import sys

from PyQt5.QtWidgets import QApplication
from grapholed import images_rc ## DO NOT REMOVE
from grapholed.functions import QSS, getPath
from grapholed.style import DefaultStyle
from grapholed.widgets import MainWindow, SplashScreen


class Grapholed(QApplication):
    """
    This class implements the main Qt application.
    """
    mainWindow = None

    def __init__(self, *args, **kwargs):
        """
        Initialize Grapholed.
        """
        super().__init__(*args, **kwargs)

    def init(self):
        """
        Run initialization tasks for Grapholed (i.e: initialize the Style, Main Window...).
        :return: the application MainWindow (:type: MainWindow)
        """
        self.setStyle(DefaultStyle())
        self.setStyleSheet(QSS(getPath('@grapholed/stylesheets/default.qss')))
        self.mainWindow = MainWindow()
        return self.mainWindow


def main():
    """
    Application main execution (without splashscreen).
    """
    app = Grapholed(sys.argv)
    mainwindow = app.init()
    mainwindow.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()