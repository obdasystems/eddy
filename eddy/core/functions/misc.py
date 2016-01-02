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


import itertools
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap

from eddy.core.regex import RE_QUOTE_FULL


def clamp(val, minval=None, maxval=None):
    """
    Returns a copy of val making sure it fits the given bounds.
    :type val: float
    :type minval: float
    :type maxval: float
    :rtype: float
    """
    if minval is not None and maxval is not None and minval > maxval:
        raise ValueError('minval ({}) MUST be lower than maxval ({})'.format(minval, maxval))
    if minval is not None:
        val = max(val, minval)
    if maxval is not None:
        val = min(val, maxval)
    return val


def isEmpty(string):
    """
    Safely detect whether the given string is empty.
    :type string: T <= bytes | unicode | float | None
    :rtype: bool
    """
    return not string or str(string).strip() == ''


def isQuoted(string):
    """
    Checks whether the given string is quoted or not.
    :type string: T <= bytes | unicode
    :rtype: bool
    """
    return RE_QUOTE_FULL.match(string) is not None


def makeColoredIcon(width, height, code):
    """
    Create and returns a QIcon filled using the given color.
    :type width: T <= int | float
    :type height: T <= int | float
    :type code: T <= bytes | unicode
    :rtype: QIcon
    """
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(code))
    return QIcon(pixmap)


def makeShadedIcon(path, opacity=0.25):
    """
    Create a shaded icon using the given image: the shaded copy will use the given opacity value.
    :type path: T <= bytes | unicode
    :type opacity: T <= int | float
    :rtype: QIcon
    """
    icon = QIcon()
    icon.addPixmap(QPixmap(path), QIcon.Normal)
    icon.addPixmap(shaded(QPixmap(path), opacity), QIcon.Disabled)
    return icon


def partition(predicate, iterable):
    """
    Uses the given predicate to partition entries from the given iterable.
    :type predicate: callable
    :type iterable: iterable
    :rtype: tuple
    """
    t1, t2 = itertools.tee(iterable)
    return filter(predicate, t2), itertools.filterfalse(predicate, t1)


def rangeF(start, stop, step):
    """
    Generator which can be used to generate lists of float values. Floats are rounded up to 4 decimals.
    It works like the python built-in range function but accepts a floating point number as incremental step.
    :type start: float
    :type stop: float
    :type step: float
    """
    x = round(start, 4)
    while x < stop:
        yield x
        x = round(x + step, 4)


def shaded(pixmap, opacity=0.25):
    """
    Constructs a copy of the given pixmap using the specified opacity.
    :type pixmap: QPixmap
    :type opacity: T <= int | float
    :rtype: QPixmap
    """
    o = QPixmap(pixmap.size())
    o.fill(Qt.transparent)
    p = QPainter(o)
    p.setOpacity(clamp(opacity, 0.0, 1.0))
    p.drawPixmap(0, 0, pixmap)
    p.end()
    return o


def snapF(value, gridsize, offset=0, snap=True):
    """
    Snap the given value according to the given grid size.
    :type value: float
    :type gridsize: float
    :type offset: float
    :type snap: bool
    :rtype: float
    """
    if snap:
        return float(round(value / gridsize) * gridsize) + offset
    return value


def QSS(path):
    """
    Read a QSS file matching the given name and return its content.
    :raise TypeError: if an invalid QSS file is supplied.
    :raise IOError: if there is no QSS file matching the given name.
    :type path: T <= bytes | unicode
    :rtype: str
    """
    if not path.lower().endswith('.qss'):
        raise TypeError('invalid QSS file supplied: {}'.format(path))
    if not os.path.isfile(path):
        raise IOError('could not load QSS file ({}): file no found'.format(path))
    with open(path) as qss:
        return qss.read()