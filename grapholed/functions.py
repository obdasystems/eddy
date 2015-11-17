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


import functools
import math
import os
import sys

from grapholed.exceptions import ProgrammingError

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QIcon, QColor


def angleP(p1, p2):
    """
    Returns the angle of the line connecting the given points.
    NOTE: the Y axis on Qt is inverted (increas down, decrease up)
    :param p1: the first point.
    :param p2: the second point.
    :rtype: float
    """
    return math.atan2(p1.y() - p2.y(), p2.x() - p1.x())


def clamp(val, minval=None, maxval=None):
    """
    Returns a copy of val making sure it fits the bound.
    :param val: the value to be clamped.
    :param minval: the minimum value.
    :param maxval: the maximum value.
    """
    if minval is not None and maxval is not None and minval > maxval:
        raise ProgrammingError('minval ({min}) MUST be lower than maxval ({max})'.format(min=minval, max=maxval))
    if minval is not None:
        val = max(val, minval)
    if maxval is not None:
        val = min(val, maxval)
    return val


def connect(signal, slot, *args, **kwargs):
    """
    Connect the given signal to the specified slots passing all arguments to the slot.
    Note that this function make use of functools.partial to hand parameters over to the function slot.
    This ia actually highly discouraged because the the function slot will be treated as a normal python function,
    losing all the properties of Qt slot. Whenever it's possible make use of self.sender() to retrieve the action
    executing the slot execution, and action.data() to retrieve function slot's parameters (previously set with setData)
    :param signal: the signal to attach.
    :param slot: the slot where to attach the signal.
    :param args: positional arguments specifying slot function parameters.
    :param kwargs: positional key-value pairs specifying slot function parameters.
    """
    if not args and not kwargs:
        signal.connect(slot)
    else:
        signal.connect(functools.partial(slot, *args, **kwargs))


def disconnect(signal, *args):
    """
    Disconnect the given signal.
    :param signal: the signal to disconnect.
    :param args: positional arguments specifying the slots to disconnect.
    """
    if args:
        for slot in args:
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError, AttributeError):
                pass
    else:
        try:
            signal.disconnect()
        except (RuntimeError, TypeError, AttributeError):
            pass


def distanceP(p1, p2):
    """
    Calculate the distance between the given points.
    :type p1: QPointF
    :type p2: QPointF
    :param p1: the first point.
    :param p2: the second point.
    :rtype: float
    """
    return math.sqrt(math.pow(p2.x() - p1.x(), 2) + math.pow(p2.y() - p1.y(), 2))


def distanceL(line, p):
    """
    Returns a tuple containing the distance between the given line and the given point, and the intersection point.
    :type line: QLineF
    :type p: QPointF
    :param line: the line.
    :param p: the point.
    :rtype: tuple
    """
    x1 = line.x1()
    y1 = line.y1()
    x2 = line.x2()
    y2 = line.y2()
    x3 = p.x()
    y3 = p.y()

    kk = ((y2 - y1) * (x3 - x1) - (x2 - x1) * (y3 - y1)) / (math.pow(y2 - y1, 2) + math.pow(x2 - x1, 2))
    x4 = x3 - kk * (y2 - y1)
    y4 = y3 + kk * (x2 - x1)

    p1 = QPointF(x3, y3)
    p2 = QPointF(x4, y4)

    return distanceP(p1, p2), p2


def getHomePath():
    """
    Returns the path to the grapholed home directory.
    :rtype: str
    """
    homepath = os.path.normpath(os.path.expanduser('~/.grapholed'))
    if not os.path.isdir(homepath):
        os.mkdir(homepath)
    return homepath


def getModulePath():
    """
    Returns the path to the grapholed directory.
    :rtype: str
    """
    if main_is_frozen():
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(sys.modules['grapholed'].__file__)
    return os.path.normpath(os.path.expanduser(path))


def getPath(path):
    """
    Return an absolute path by expanding the given relative one.
    The following tokens will be expanded:

        - @grapholed => will be expanded to the grapholed directory path
        - @home => will be expanded to the grapholed home directory path (.grapholed in $HOME)
        - ~ => will be expanded to the user home directory ($HOME)

    :param path: the relative path to expand.
    :rtype: str
    """
    if path.startswith('@grapholed\\') or path.startswith('@grapholed/'):
        path = os.path.join(getModulePath(), path[11:])
    elif path.startswith('@home\\') or path.startswith('@home/'):
        path = os.path.join(getHomePath(), path[6:])
    return os.path.normpath(os.path.expanduser(path))


def intersectionL(l1, l2):
    """
    Return the intersection point of the given lines.
    Will return None if there is no intersection point.
    :type l1: QLineF
    :type l2: QlineF
    :param l1: the first line.
    :param l2: the second line.
    :rtype: QPointF
    """
    L = max(min(l1.p1().x(), l1.p2().x()), min(l2.p1().x(), l2.p2().x()))
    R = min(max(l1.p1().x(), l1.p2().x()), max(l2.p1().x(), l2.p2().x()))
    T = max(min(l1.p1().y(), l1.p2().y()), min(l2.p1().y(), l2.p2().y()))
    B = min(max(l1.p1().y(), l1.p2().y()), max(l2.p1().y(), l2.p2().y()))
    if (T, L) == (B, R):
        return QPointF(L, T)
    return None


def isEmpty(text):
    """
    Safely detect whether the given string is empty.
    :param text: the text to check for emptiness.
    :rtype: bool
    """
    return not text or str(text).strip() == ''

def main_is_frozen():
    """
    Detects whether we are running a Frozen application.
    :rtype: bool
    """
    return hasattr(sys, 'frozen')


def make_colored_pixmap(width, height, code):
    """
    Create and returns a QPixmap filled using the given color.
    :param width: the width of the pixmap.
    :param height: the height of the pixmap.
    :param code: the HEX color code to use to fill the icon.
    :rtype: QPixmap
    """
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(code))
    return pixmap


def make_shaded_icon(path, opacity=0.25):
    """
    Create a shaded icon using the given image: the shaded copy will use the given opacity value.
    :param path: the path of the image.
    :param opacity: the opacity of the shaded icon.
    :rtype: QIcon
    """
    icon = QIcon()
    icon.addPixmap(QPixmap(path), QIcon.Normal)
    icon.addPixmap(shaded(QPixmap(path), opacity), QIcon.Disabled)
    return icon


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
    Generator which can be used to generate lists of float values. Floats are rounded up to 4 decimals.
    It works like the python built-in range function but accepts a floating point number as incremental step.
    :param start: the start value
    :param stop: the end value
    :param step: the incremental step
    """
    x = round(start, 4)
    while x < stop:
        yield x
        x = round(x + step, 4)


def shaded(pixmap, opacity=0.25):
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


def snapToGrid(value, gridsize, offset=0, snap=True):
    """
    Snap the given value according to the given grid size.
    :param value: the value to snap.
    :param gridsize: the size of the grid.
    :param offset: an offset value to add to the result of the snap.
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
        raise TypeError('invalid QSS file supplied: {0}'.format(path))
    if not os.path.isfile(path):
        raise IOError('could not load QSS file ({0}): file no found'.format(path))
    with open(path) as qss:
        return qss.read()