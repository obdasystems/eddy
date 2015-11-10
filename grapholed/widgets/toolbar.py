# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  GrapholEd: an editor for the Graphol ontology language.               #
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


from grapholed.functions import connect

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QSlider, QWidget, QHBoxLayout, QLineEdit


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
        self.label.setFixedSize(48, 20)
        self.label.setFocusPolicy(Qt.NoFocus)
        self.label.setProperty('class', 'zoom-value')
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