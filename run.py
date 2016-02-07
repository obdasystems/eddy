#!/usr/bin/env python3
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


import sys
import traceback

from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMessageBox

from eddy import BUG_TRACKER
from eddy import __appname__ as APPNAME
from eddy.core.application import Eddy
from eddy.core.functions import connect

# noinspection PyUnresolvedReferences
from eddy.ui import images_rc


app = None
box = None


def base_except_hook(exc_type, exc_value, exc_traceback):
    """
    Used to handle all uncaught exceptions.
    :type exc_type: class
    :type exc_value: Exception
    :type exc_traceback: Traceback
    """
    global app
    global box

    if issubclass(exc_type, KeyboardInterrupt):

        app.quit()

    else:

        if not box:

            m1 = 'This is embarrassing ...\n\n' \
                 'A critical error has just occurred. ' \
                 'Eddy will continue to work, however a reboot is highly recommended.'
            m2 = 'If the problem persists please <a href="{}">submit a bug report</a>.'.format(BUG_TRACKER)
            m3 = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/images/eddy-sad'))
            box.setWindowIcon(QIcon(':/images/eddy'))
            box.setWindowTitle('Unhandled error!')
            box.setText(m1)
            box.setInformativeText(m2)
            box.setDetailedText(m3)
            box.setStandardButtons(QMessageBox.Close|QMessageBox.Ok)

            buttonOk = box.button(QMessageBox.Ok)
            buttonOk.setText('Close')
            buttonQuit = box.button(QMessageBox.Close)
            buttonQuit.setText('Quit {}'.format(APPNAME))

            connect(buttonOk.clicked, box.close)
            connect(buttonQuit.clicked, app.quit)

            box.exec_()
            box = None


def main():
    """
    Application entry point.
    """
    global app
    sys.excepthook = base_except_hook
    app = Eddy(sys.argv)

    if app.isRunning:
        # If the application is already running in another process send a message to the
        # process containing all the sys.argv elements joined into a string. This will
        # cause the other process to activate itself and handle the received message.
        app.sendMessage(' '.join(sys.argv))
        sys.exit(0)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()