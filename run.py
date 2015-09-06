#!/usr/bin/env python3
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

import sys
import traceback

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox, QSpacerItem, QSizePolicy
from pygraphol import images_rc ## DO NOT REMOVE
from pygraphol import PyGraphol
from pygraphol.widgets import SplashScreen


def main():
    """
    Application main execution.
    """
    try:
        app = PyGraphol(sys.argv)
        with SplashScreen(min_splash_time=2):
            mainwindow = app.init()
    except Exception as e:
        box = QMessageBox()
        box.setIconPixmap(QPixmap(':/icons/error'))
        box.setWindowTitle('FATAL')
        box.setText('pyGraphol failed to start!')
        box.setInformativeText('ERROR: %s' % e)
        box.setDetailedText(traceback.format_exc())
        box.setStandardButtons(QMessageBox.Ok)
        # this will trick Qt and resize a bit the QMessageBox so the exception stack trace is printed nice
        foo = QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        box.layout().addItem(foo, box.layout().rowCount(), 0, 1, box.layout().columnCount())
        box.exec_()
        sys.exit(127)
    else:
        mainwindow.show()
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()