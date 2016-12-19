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


import math
import os
import unittest

from PyQt5 import QtCore

from eddy.core.functions.misc import isEmpty, rangeF, snapF
from eddy.core.functions.misc import clamp, first, last, lstrip, rstrip
from eddy.core.functions.geometry import angle, distance, projection
from eddy.core.functions.geometry import intersection, midpoint
from eddy.core.functions.owl import OWLText, OWLShortIRI
from eddy.core.functions.path import compressPath


class FunctionsTestCase(unittest.TestCase):

    def test_angle(self):
        self.assertEqual(0.0, angle(QtCore.QPointF(0, 0), QtCore.QPointF(+1, 0)))
        self.assertEqual(+math.pi / 2, angle(QtCore.QPointF(0, 0), QtCore.QPointF(0, -1)))
        self.assertEqual(-math.pi / 2, angle(QtCore.QPointF(0, 0), QtCore.QPointF(0, +1)))
        self.assertEqual(math.pi, angle(QtCore.QPointF(0, 0), QtCore.QPointF(-1, 0)))
        self.assertEqual(+math.pi / 4, angle(QtCore.QPointF(0, 0), QtCore.QPointF(1, -1)))

    def test_clamp(self):
        self.assertEqual(0.0, clamp(val=-4.0, minval=0.0))
        self.assertEqual(0.0, clamp(val=-4.0, minval=0.0, maxval=8.0))
        self.assertEqual(5.0, clamp(val=5.0, maxval=10.0))
        self.assertEqual(5.0, clamp(val=5.0, minval=0.0, maxval=10.0))
        self.assertEqual(10.0, clamp(val=12.0, maxval=10.0))
        self.assertEqual(10.0, clamp(val=12.0, minval=0.0, maxval=10.0))

    def test_clamp_with_exception(self):
        self.assertRaises(ValueError, clamp, val=4.0, minval=10.0, maxval=0.0)

    def test_compress_path(self):
        self.assertEqual(10, len(compressPath(os.path.join('this', 'is', 'a', 'very', 'long', 'path'), 10)))

    def test_distance(self):
        self.assertEqual(0.0, distance(QtCore.QPointF(0, 0), QtCore.QPointF(0, 0)))
        self.assertEqual(10.0, distance(QtCore.QPointF(0, 0), QtCore.QPointF(10, 0)))
        self.assertEqual(10.0, distance(QtCore.QPointF(0, 0), QtCore.QPointF(0, 10)))
        self.assertEqual(14.0, distance(QtCore.QPointF(-4, 0), QtCore.QPointF(10, 0)))
        self.assertEqual(14.0, distance(QtCore.QPointF(0, -4), QtCore.QPointF(0, 10)))
        self.assertEqual(10.0, distance(QtCore.QPointF(0, 8), QtCore.QPointF(6, 0)))
        self.assertEqual(10.0, distance(QtCore.QPointF(0, -8), QtCore.QPointF(-6, 0)))

    def test_first(self):
        self.assertEqual(5, first([5, 7, 9, 11, 97, 4, 7, 3]))
        self.assertEqual(5, first((5, 7, 9, 11, 97, 4, 7, 3)))
        self.assertEqual(5, first([5, 7, 9, 11, 97, 4, 7, 3]))
        self.assertEqual(1, first([], default=1))
        self.assertIsNone(first([]))

    def test_last(self):
        self.assertEqual(3, last([5, 7, 9, 11, 97, 4, 7, 3]))
        self.assertEqual(3, last((5, 7, 9, 11, 97, 4, 7, 3)))
        self.assertEqual(3, last([5, 7, 9, 11, 97, 4, 7, 3]))
        self.assertEqual(1, last([], default=1))
        self.assertIsNone(last([]))

    def test_lstrip(self):
        self.assertEqual('.graphol', lstrip('Pizza.graphol', 'Pizza'))
        self.assertEqual('graphol', lstrip('Family.graphol', 'Family', '.'))
        self.assertEqual('Message', lstrip('ThisIsATestMessage', 'This', 'Is', 'A', 'Test'))

    def test_rstrip(self):
        self.assertEqual('Pizza', rstrip('Pizza.graphol', '.graphol'))
        self.assertEqual('Pizza.graphol', rstrip('Pizza.graphol', 'random_string'))
        self.assertEqual('Family', rstrip('Family.graphol', 'graphol', '.'))
        self.assertEqual('ThisIs', rstrip('ThisIsATestMessage', 'Message', 'Test', 'A'))

    def test_projection(self):
        P = QtCore.QPointF(2, 8)
        L = QtCore.QLineF(QtCore.QPointF(0, 0), QtCore.QPointF(10, 0))
        D = projection(L, P)
        self.assertIsInstance(D, tuple)
        self.assertEqual(D[0], 8.0)
        self.assertEqual(D[1], QtCore.QPointF(2, 0))

    def test_intersection(self):
        self.assertEqual(QtCore.QPointF(0, 0), intersection(QtCore.QLineF(QtCore.QPointF(-1, 0), QtCore.QPointF(1, 0)), QtCore.QLineF(QtCore.QPointF(0, -1), QtCore.QPointF(0, 1))))
        self.assertEqual(QtCore.QPointF(-4, 0), intersection(QtCore.QLineF(QtCore.QPointF(-10, 0), QtCore.QPointF(10, 0)), QtCore.QLineF(QtCore.QPointF(-4, -12), QtCore.QPointF(-4, 14))))
        self.assertIsNone(intersection(QtCore.QLineF(QtCore.QPointF(-1, 0), QtCore.QPointF(1, 0)), QtCore.QLineF(QtCore.QPointF(-1, 2), QtCore.QPointF(1, 2))))

    def test_empty(self):
        self.assertTrue(isEmpty(None))
        self.assertTrue(isEmpty(''))
        self.assertTrue(isEmpty('   '))
        self.assertFalse(isEmpty('Hello World'))
        self.assertFalse(isEmpty(4))

    def test_midpoint(self):
        self.assertEqual(QtCore.QPointF(5, 0), midpoint(QtCore.QPointF(0, 0), QtCore.QPointF(10, 0)))
        self.assertEqual(QtCore.QPointF(0, 5), midpoint(QtCore.QPointF(0, 0), QtCore.QPointF(0, 10)))
        self.assertEqual(QtCore.QPointF(5, 5), midpoint(QtCore.QPointF(0, 0), QtCore.QPointF(10, 10)))

    def test_generator(self):
        self.assertEqual([0.0, 1.0, 2.0, 3.0], list(rangeF(0.0, 4.0, 1.0)))
        self.assertEqual([0.0, 0.2, 0.4, 0.6, 0.8], list(rangeF(0.0, 1.0, 0.2)))
        self.assertEqual([0.0000, 0.0001, 0.0002, 0.0003, 0.0004], list(rangeF(0.0000, 0.0005, 0.0001)))

    def test_snapF(self):
        self.assertEqual(10.0, snapF(value=8.0, size=10.0))
        self.assertEqual(10.0, snapF(value=6.0, size=10.0))
        self.assertEqual(0.0, snapF(value=5.0, size=10.0))
        self.assertEqual(0.0, snapF(value=4.0, size=10.0))
        self.assertEqual(0.0, snapF(value=2.0, size=10.0))
        
    def test_snapF_with_offset(self):
        self.assertEqual(12.0, snapF(value=8.0, size=10.0, offset=2.0))
        self.assertEqual(6.0, snapF(value=6.0, size=10.0, offset=-4.0))

    def test_snapF_with_skip(self):
        self.assertEqual(8.0, snapF(value=8.0, size=10.0, perform=False))
        self.assertEqual(6.0, snapF(value=6.0, size=10.0, perform=False))

    def test_owl_short_iri(self):
        self.assertEqual('prefix:this_is_my_content', OWLShortIRI('prefix', 'this_is my content'))
        self.assertEqual('prefix:this_is_my_content', OWLShortIRI('prefix', 'this\n\nis_my content'))

    def test_owl_text(self):
        self.assertEqual('this_is_a_long_string', OWLText('this_is_a_long_string'))
        self.assertEqual('this_is_a_long_string', OWLText('this_is_a\nlong _string'))
        self.assertEqual('this_is_another_long_string', OWLText('this is another\n\nlong string'))