# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
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

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPixmap

from eddy.core.regex import RE_QUOTED


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
    :type string: str | float | None
    :rtype: bool
    """
    return not string or str(string).strip() == ''


def isQuoted(string):
    """
    Checks whether the given string is quoted or not.
    :type string: str
    :rtype: bool
    """
    return RE_QUOTED.match(string) is not None


def cutL(text, cut):
    """
    Remove 'cut' from 'text' if found as starting prefix.
    :type text: str
    :type cut: str
    :rtype: str
    """
    if text.startswith(cut):
        return text[len(cut)+1:]
    return text


def first(iterable, default=None):
    """
    Returns the first element of iterable if it exists, otherwise it returns the given default.
    :type iterable: T <= list | tuple | set | generator
    :type default: any
    :rtype: mixed
    """
    if iterable:
        for item in iterable:
            return item
    return default


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


def cutR(text, cut):
    """
    Remove 'cut' from 'text' if found as ending suffix.
    :type text: str
    :type cut: str
    :rtype: str
    """
    if text.endswith(cut):
        return text[:-len(cut)]
    return text


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


def snapF(value, size, offset=0, perform=True):
    """
    Snap the given value according to the given grid size.
    :type value: float
    :type size: float
    :type offset: float
    :type perform: bool
    :rtype: float
    """
    if perform:
        return float(round(value / size) * size) + offset
    return value


def snap(point, size, perform=True):
    """
    Snap the given point according to the given grid size.
    :type point: QPointF
    :type size: float
    :type perform: bool
    :rtype: QPointF
    """
    if perform:
        x = snapF(point.x(), size, 0, perform)
        y = snapF(point.y(), size, 0, perform)
        return QPointF(x, y)
    return point


def uncapitalize(s):
    """
    Returns a copy of the given string with the first characted uncapitalized.
    :type s: str
    :rtype: str
    """
    return '{}{}'.format(s[:1].lower(), s[1:])