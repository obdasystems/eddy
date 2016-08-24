# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import itertools

from PyQt5.QtCore import QPointF
from traceback import format_exception as f_exc
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
        raise ValueError('minval ({0}) MUST be lower than maxval ({1})'.format(minval, maxval))
    if minval is not None:
        val = max(val, minval)
    if maxval is not None:
        val = min(val, maxval)
    return val


def cutL(text, *args):
    """
    Removes from 'text' all the given starting prefixes.
    :type text: str
    :type args: list
    :rtype: str
    """
    for token in args:
        if token and text.startswith(token):
            text = text[len(token):]
    return text


def cutR(text, *args):
    """
    Removes from 'text' all the given ending suffixes.
    :type text: str
    :type args: list
    :rtype: str
    """
    for token in args:
        if token and text.endswith(token):
            text = text[:-len(token)]
    return text


def first(iterable, default=None):
    """
    Returns the first element in 'iterable' if it exists, otherwise it returns the given default.
    :type iterable: T <= list | tuple | set | generator
    :type default: any
    :rtype: mixed
    """
    if iterable:
        for item in iterable:
            return item
    return default


def format_exception(e):
    """
    Format the given exception returning a string representation of it.
    :type e: Exception
    :rtype: str
    """
    return ''.join(f_exc(type(e), e, e.__traceback__))


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


def last(iterable, default=None):
    """
    Returns the last element in 'iterable' if it exists, otherwise it returns the given default.
    :type iterable: T <= list | tuple | set | generator
    :type default: any
    :rtype: mixed
    """
    if iterable:
        for item in reversed(iterable):
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


def postfix(string, value):
    """
    Add te given suffix to te given string (if it's not there already).
    :type string: str
    :type value: str
    :rtype: str
    """
    if not string.endswith(value):
        return '{0}{1}'.format(string, value)


def prefix(string, value):
    """
    Add te given prefix to te given string (if it's not there already).
    :type string: str
    :type value: str
    :rtype: str
    """
    if not string.startswith(value):
        return '{0}{1}'.format(value, string)


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


def snap(point, size, perform=True):
    """
    Snap each component of the given point according to the given size.
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


def snapF(value, size, offset=0, perform=True):
    """
    Snap the given value according to the given size.
    :type value: float
    :type size: float
    :type offset: float
    :type perform: bool
    :rtype: float
    """
    if perform:
        return float(round(value / size) * size) + offset
    return value


def uncapitalize(s):
    """
    Returns a copy of the given string with the first characted uncapitalized.
    :type s: str
    :rtype: str
    """
    return '{0}{1}'.format(s[:1].lower(), s[1:])