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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import math
import os
import pytest

from PyQt5 import QtCore

from eddy.core.functions.geometry import angle, distance, projection
from eddy.core.functions.geometry import intersection, midpoint
from eddy.core.functions.misc import clamp, first, last, lstrip, natsorted, rstrip
from eddy.core.functions.misc import isEmpty, rangeF, snapF
from eddy.core.functions.owl import OWLText, OWLShortIRI
from eddy.core.functions.path import compressPath


#############################################
# FUNCTIONS TESTS
#################################

def test_angle():
    assert 0.0 == angle(QtCore.QPointF(0, 0), QtCore.QPointF(+1, 0))
    assert +math.pi / 2 == angle(QtCore.QPointF(0, 0), QtCore.QPointF(0, -1))
    assert -math.pi / 2 == angle(QtCore.QPointF(0, 0), QtCore.QPointF(0, +1))
    assert math.pi == angle(QtCore.QPointF(0, 0), QtCore.QPointF(-1, 0))
    assert +math.pi / 4 == angle(QtCore.QPointF(0, 0), QtCore.QPointF(1, -1))


def test_clamp():
    assert 0.0 == clamp(val=-4.0, minval=0.0)
    assert 0.0 == clamp(val=-4.0, minval=0.0, maxval=8.0)
    assert 5.0 == clamp(val=5.0, maxval=10.0)
    assert 5.0 == clamp(val=5.0, minval=0.0, maxval=10.0)
    assert 10.0 == clamp(val=12.0, maxval=10.0)
    assert 10.0 == clamp(val=12.0, minval=0.0, maxval=10.0)


def test_clamp_with_exception():
    with pytest.raises(ValueError):
        clamp(val=4.0, minval=10.0, maxval=0.0)


def test_compress_path():
    assert 10 == len(compressPath(os.path.join('this', 'is', 'a', 'very', 'long', 'path'), 10))


def test_distance():
    assert 0.0 == distance(QtCore.QPointF(0, 0), QtCore.QPointF(0, 0))
    assert 10.0 == distance(QtCore.QPointF(0, 0), QtCore.QPointF(10, 0))
    assert 10.0 == distance(QtCore.QPointF(0, 0), QtCore.QPointF(0, 10))
    assert 14.0 == distance(QtCore.QPointF(-4, 0), QtCore.QPointF(10, 0))
    assert 14.0 == distance(QtCore.QPointF(0, -4), QtCore.QPointF(0, 10))
    assert 10.0 == distance(QtCore.QPointF(0, 8), QtCore.QPointF(6, 0))
    assert 10.0 == distance(QtCore.QPointF(0, -8), QtCore.QPointF(-6, 0))


def test_first():
    assert 5 == first([5, 7, 9, 11, 97, 4, 7, 3])
    assert 5 == first((5, 7, 9, 11, 97, 4, 7, 3))
    assert 5 == first([5, 7, 9, 11, 97, 4, 7, 3])
    assert 1 == first([], default=1)
    assert first([]) is None


def test_last():
    assert 3 == last([5, 7, 9, 11, 97, 4, 7, 3])
    assert 3 == last((5, 7, 9, 11, 97, 4, 7, 3))
    assert 3 == last([5, 7, 9, 11, 97, 4, 7, 3])
    assert 1 == last([], default=1)
    assert last([]) is None


def test_lstrip():
    assert '.graphol' == lstrip('Pizza.graphol', 'Pizza')
    assert 'graphol' == lstrip('Family.graphol', 'Family', '.')
    assert 'Message' == lstrip('ThisIsATestMessage', 'This', 'Is', 'A', 'Test')


def test_rstrip():
    assert 'Pizza' == rstrip('Pizza.graphol', '.graphol')
    assert 'Pizza.graphol' == rstrip('Pizza.graphol', 'random_string')
    assert 'Family' == rstrip('Family.graphol', 'graphol', '.')
    assert 'ThisIs' == rstrip('ThisIsATestMessage', 'Message', 'Test', 'A')


def test_projection():
    P = QtCore.QPointF(2, 8)
    L = QtCore.QLineF(QtCore.QPointF(0, 0), QtCore.QPointF(10, 0))
    D = projection(L, P)
    assert isinstance(D, tuple)
    assert D[0] == 8.0
    assert D[1] == QtCore.QPointF(2, 0)


def test_intersection():
    assert QtCore.QPointF(0, 0) == intersection(QtCore.QLineF(QtCore.QPointF(-1, 0), QtCore.QPointF(1, 0)),
                                                QtCore.QLineF(QtCore.QPointF(0, -1), QtCore.QPointF(0, 1)))
    assert QtCore.QPointF(-4, 0) == intersection(QtCore.QLineF(QtCore.QPointF(-10, 0), QtCore.QPointF(10, 0)),
                                                 QtCore.QLineF(QtCore.QPointF(-4, -12), QtCore.QPointF(-4, 14)))
    assert intersection(QtCore.QLineF(QtCore.QPointF(-1, 0), QtCore.QPointF(1, 0)),
                        QtCore.QLineF(QtCore.QPointF(-1, 2), QtCore.QPointF(1, 2))) is None


def test_empty():
    assert isEmpty(None)
    assert isEmpty('')
    assert isEmpty('   ')
    assert not isEmpty('Hello World')
    assert not isEmpty(4)


def test_midpoint():
    assert QtCore.QPointF(5, 0) == midpoint(QtCore.QPointF(0, 0), QtCore.QPointF(10, 0))
    assert QtCore.QPointF(0, 5) == midpoint(QtCore.QPointF(0, 0), QtCore.QPointF(0, 10))
    assert QtCore.QPointF(5, 5) == midpoint(QtCore.QPointF(0, 0), QtCore.QPointF(10, 10))


def test_generator():
    assert [0.0, 1.0, 2.0, 3.0] == list(rangeF(0.0, 4.0, 1.0))
    assert [0.0, 0.2, 0.4, 0.6, 0.8] == list(rangeF(0.0, 1.0, 0.2))
    assert [0.0000, 0.0001, 0.0002, 0.0003, 0.0004] == list(rangeF(0.0000, 0.0005, 0.0001))


def test_snapF():
    assert 10.0 == snapF(value=8.0, size=10.0)
    assert 10.0 == snapF(value=6.0, size=10.0)
    assert 0.0 == snapF(value=5.0, size=10.0)
    assert 0.0 == snapF(value=4.0, size=10.0)
    assert 0.0 == snapF(value=2.0, size=10.0)


def test_snapF_with_offset():
    assert 12.0 == snapF(value=8.0, size=10.0, offset=2.0)
    assert 6.0 == snapF(value=6.0, size=10.0, offset=-4.0)


def test_snapF_with_skip():
    assert 8.0 == snapF(value=8.0, size=10.0, perform=False)
    assert 6.0 == snapF(value=6.0, size=10.0, perform=False)

def test_owl_text():
    assert 'this_is_a_long_string' == OWLText('this_is_a_long_string')
    assert 'this_is_a_long_string' == OWLText('this_is_a\nlong _string')
    assert 'this_is_another_long_string' == OWLText('this is another\n\nlong string')


def test_natsorted():
    assert [] == natsorted([])
    assert ['diagram1', 'diagram9', 'diagram10'] == natsorted(['diagram1', 'diagram10', 'diagram9'], locale=QtCore.QLocale('en_US'))
    assert [1, 10, 'diagram9', 'diagram10'] == natsorted([1, 'diagram10', 'diagram9', 10], locale=QtCore.QLocale('en_US'))
