# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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

from eddy.functions import connect

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSlider, QWidget, QHBoxLayout, QLineEdit, QLabel


class ZoomControl(QWidget):
    """
    This class implements the Zoom control which is used to Zoom the graphics scene.
    """
    MinScale = 0.25 # the minimum scale value
    MaxScale = 5.00 # the maximum scale value
    Step = 4 # scale tick step

    scaleChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        """
        Inizialize the zoom controller.
        :param parent: the parent widget.
        """
        super().__init__(parent)

        # This is a bit ugly but prevents the user from selecting values which do not match the set step (which
        # in this case is 1 / 4 = 0.25 = 25%. If we set the min size and max size on the slider and set
        # the single step the user is still able to select values which are not multiple of step.
        self.zoom = {v[0]:v[1] for v in enumerate(map(lambda x: x / ZoomControl.Step,
                                                  range(int(ZoomControl.MinScale * ZoomControl.Step),
                                                        int(ZoomControl.MaxScale * ZoomControl.Step + 1), 1)), start=1)}

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setEnabled(False)
        self.slider.setFixedWidth(120)
        self.slider.setRange(1, len(self.zoom))
        self.slider.setSingleStep(1)
        self.slider.setTickPosition(QSlider.NoTicks)
        self.slider.setTickInterval(1)

        connect(self.slider.valueChanged, self.onSliderValueChanged)

        self.label = QLineEdit(self)
        self.label.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(50, 20)
        self.label.setFocusPolicy(Qt.NoFocus)
        self.label.setReadOnly(True)

        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.addWidget(self.slider)
        self.mainLayout.addWidget(self.label)
        self.mainLayout.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.mainLayout.setSpacing(6)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

    ############################################## SIGNAL HANDLERS #####################################################

    @pyqtSlot()
    def onSliderValueChanged(self):
        """
        Executed when the value of the slider changes.
        """
        if self.isEnabled():
            self.scaleChanged.emit(self.zoom[self.slider.value()])
            self.setZoomText(self.slider.value())

    @pyqtSlot(float)
    def onMainViewZoomChanged(self, zoom):
        """
        Executed when the main view zoom value changes.
        :param zoom: the zoom value.
        """
        if self.isEnabled():
            self.slider.setValue(self.index(zoom))
            self.setZoomText(self.slider.value())

    ################################################# OVERRIDES ########################################################

    def isEnabled(self):
        """
        Tells whether this widget is enabled.
        :return: True if the widget is enabled, False otherwise.
        """
        return self.slider.isEnabled() and self.label.isEnabled() and super().isEnabled()

    def setDisabled(self, disabled):
        """
        Set the widget enabled state.
        :param disabled: True if the widget is disabled, False otherwise.
        """
        self.slider.setDisabled(disabled)
        self.label.setDisabled(disabled)
        super().setDisabled(disabled)

    def setEnabled(self, enabled):
        """
        Set the widget enabled state.
        :param enabled: True if the widget is enabled, False otherwise.
        """
        self.slider.setEnabled(enabled)
        self.label.setEnabled(enabled)
        super().setEnabled(enabled)

    ############################################# AUXILIARY METHODS ####################################################

    def index(self, zoom):
        """
        Returns the Zoom control tick index given the scale factor.
        :param zoom: the scale factor.
        :raise IndexError: if the given scale factor is not valid.
        """
        return [k for k in self.zoom if self.zoom[k] == zoom][0]

    def reset(self):
        """
        Reset the zoom control to the default index.
        """
        self.slider.setValue(1)
        self.label.setText('')

    def setZoomLevel(self, index):
        """
        Set the zoom control value.
        :param index: the index of the position of the slider.
        """
        self.slider.setValue(index)
        self.setZoomText(index)

    def setZoomText(self, index):
        """
        Set the zoom text value.
        :param index: the index of the position of the slider.
        """
        self.label.setText('%d%%' % int(self.zoom[index] * 100))


class SplashScreen(QLabel):
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
        Initialize the Eddy's splash screen.
        :param min_splash_time: the minimum amount of seconds the splash screen should be drawn.
        """
        super().__init__(None, Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.SplashScreen)
        self.min_splash_time = time() + min_splash_time
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setPixmap(QPixmap(':/images/splash'))
        self.setMask(self.pixmap().mask())
        self.setFixedSize(self.pixmap().width(), self.pixmap().height())

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
        now = time()
        if now < self.min_splash_time:
            sleep(self.min_splash_time - now)
        self.close()