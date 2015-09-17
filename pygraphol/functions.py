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


import math
import os
import sys

from pygraphol.exceptions import ProgrammingError
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QLayout, QApplication


def clamp(val, minval=None, maxval=None):
    """
    Returns a copy of val making sure it fits the bound.
    :param val: the value to be clamped.
    :param minval: the minimum value.
    :param maxval: the maximum value.
    """
    if minval is not None and maxval is not None and minval > maxval:
        raise ProgrammingError('minval (%s) MUST be lower than maxval (%s)' % (minval, maxval))
    if minval is not None:
        val = max(val, minval)
    if maxval is not None:
        val = min(val, maxval)
    return val


def distance(p1, p2):
    """
    Calculate the distance between the given points.
    :type p1: QPointF
    :type p2: QPointF
    :param p1: the first point.
    :param p2: the second point.
    :rtype: float
    """
    return math.sqrt(math.pow(p2.x() - p1.x(), 2) + math.pow(p2.y() - p1.y(), 2))


def getHomePath():
    """
    Returns the path to the pygraphol home directory.
    :rtype: str
    """
    homepath = os.path.normpath(os.path.expanduser('~/.pygraphol'))
    if not os.path.isdir(homepath):
        os.mkdir(homepath)
    return homepath


def getModulePath():
    """
    Returns the path to the pygraphol directory.
    :rtype: str
    """
    if main_is_frozen():
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(sys.modules['pygraphol'].__file__)
    return os.path.normpath(os.path.expanduser(path))


def getPath(path):
    """
    Return an absolute path by expanding the given relative one.
    The following tokens will be expanded:

        - @pygraphol => will be expanded to the pygraphol directory path
        - @home => will be expanded to the pygraphol home directory path (.pygraphol in $HOME)
        - ~ => will be expanded to the user home directory ($HOME)

    :param path: the relative path to expand
    :rtype: str
    """
    if path.startswith('@pygraphol\\') or path.startswith('@pygraphol/'):
        path = os.path.join(getModulePath(), path[11:])
    elif path.startswith('@home\\') or path.startswith('@home/'):
        path = os.path.join(getHomePath(), path[6:])
    return os.path.normpath(os.path.expanduser(path))


def isEmpty(text):
    """
    Safely detect whether the given string is empty.
    :param text: the text to check for emptiness.
    :rtype: bool
    """
    return not text or str(text).strip() == ''


def itemsInLayout(layout):
    """
    Returns all the widgets in the given layout.
    :param layout: the layout from where to pick widgets
    :rtype: tuple
    """
    if not isinstance(layout, QLayout):
        raise ProgrammingError('invalid argument specified (%s): expecting QLayout' % layout.__class__.__name__)
    return (layout.itemAt(i) for i in range(layout.count()))


def main_is_frozen():
    """
    Detects whether we are running a Frozen application.
    :rtype: bool
    """
    return hasattr(sys, 'frozen')


def midpoint(p1, p2):
    """
    Calculate the midpoint between the given points.
    :type p1: QPointF
    :type p2: QPointF
    :param p1: the first point.
    :param p2: the second point.
    :rtype: QPointF
    """
    return QPointF(((p1.x() + p2.x()) / 2), ((p1.y() + p2.y()) / 2))


def rangeF(start, stop, step):
    """
    Generator which can be used to generate lists of float values.
    It works like the python built-in range function but accepts a floating point number as incremental step.
    :param start: the start value
    :param stop: the end value
    :param step: the incremental step
    """
    x = start
    while x < stop:
        yield x
        x += step


def scaleFont(pixels):
    """
    Scale the given font size so it looks good on different platforms.
    :param pixels: the amount of pixels to scale
    :rtype: int
    """
    # noinspection PyArgumentList
    SCREEN_DPI = QApplication.primaryScreen().physicalDotsPerInch()
    RENDER_DPI = 96 if sys.platform.startswith('win32') else 72
    return int(float(pixels) * SCREEN_DPI / RENDER_DPI)


def shaded(pixmap, opacity=0.5):
    """
    Constructs a copy of the given pixmap using the specified opacity.
    :param pixmap: the pixmap to shade.
    :param opacity: the opacity to use for the shade.
    :rtype: QPixmap
    """
    o = QPixmap(pixmap.size())
    o.fill(Qt.transparent)
    p = QPainter(o)
    p.setOpacity(clamp(opacity, 0.0, 1.0))
    p.drawPixmap(0, 0, pixmap)
    p.end()
    return o


def snapPointToGrid(value, gridsize, offset=0, snap=True):
    """
    Snap the given point according to the given grid size.
    :param value: the value to snap.
    :param gridsize: the size of the grid.
    :param offset: an offset valut to add to the result of the snap.
    :param snap: whether or not to perform the snap.
    :rtype: float
    """
    if snap:
        return float(round(value / gridsize) * gridsize) + offset
    return value


def QSS(path):
    """
    Read a QSS file matching the given name and return its content.
    :param path: the path of the QSS file.
    :raise TypeError: if an invalid QSS file is supplied.
    :raise IOError: if there is no QSS file matching the given name.
    :rtype: str
    """
    if not path.lower().endswith('.qss'):
        raise TypeError('invalid QSS file supplied: %s' % path)
    if not os.path.isfile(path):
        raise IOError('could not load QSS file (%s): file no found' % path)
    with open(path) as qss:
        return qss.read()