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


import sys
import traceback

from argparse import ArgumentParser
from grapholed import images_rc ## DO NOT REMOVE
from grapholed import Grapholed, __appname__, __version__
from grapholed.dialogs import MessageBox
from grapholed.widgets import SplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy


def main():
    """
    Application entry point.
    """
    parser = ArgumentParser(description='parse GrapholEd command line options')
    parser.add_argument('--nosplash', dest='nosplash', action='store_true')

    (options, args) = parser.parse_known_args()

    def init(application):
        """
        Initialize the application using the splash screen.
        :param application: the application to initialize.
        :return: the initialized main window instance.
        :rtype: MainWindow
        """
        with SplashScreen(min_splash_time=4):
            mainwindow = application.init()
        return mainwindow

    def init_no_splash(application):
        """
        Initialize the application WITHOUT using the splash screen.
        :param application: the application to initialize.
        :return: the initialized main window instance.
        :rtype: MainWindow
        """
        return application.init()

    try:
        app = Grapholed(sys.argv)
        window = init_no_splash(app) if options.nosplash else init(app)
    except Exception as e:
        box = MessageBox()
        box.setIconPixmap(QPixmap(':/icons/error'))
        box.setWindowTitle('Startup failure')
        box.setText('GrapholEd failed to start!')
        box.setInformativeText('ERROR: %s' % e)
        box.setDetailedText(traceback.format_exc())
        box.setStandardButtons(MessageBox.Ok)
        L = box.layout()
        L.addItem(QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), L.rowCount(), 0, 1, L.columnCount())
        box.exec_()
        sys.exit(1)
    else:
        window.showMaximized()
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()