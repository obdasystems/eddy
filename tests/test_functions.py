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


import math
import unittest

from eddy.exceptions import ProgrammingError
from eddy.functions import angleP, clamp, distanceP, distanceL, intersectionL
from eddy.functions import isEmpty, midpoint, rangeF, snapF

from PyQt5.QtCore import QPointF, QLineF


class Test_AngleP(unittest.TestCase):

    def test_angle(self):
        self.assertEqual(0.0, angleP(QPointF(0, 0), QPointF(+1, 0)))
        self.assertEqual(+math.pi / 2, angleP(QPointF(0, 0), QPointF(0, -1)))
        self.assertEqual(-math.pi / 2, angleP(QPointF(0, 0), QPointF(0, +1)))
        self.assertEqual(math.pi, angleP(QPointF(0, 0), QPointF(-1, 0)))
        self.assertEqual(+math.pi / 4, angleP(QPointF(0, 0), QPointF(1, -1)))

class Test_Clamp(unittest.TestCase):

    def test_clamp(self):
        self.assertEqual(0.0, clamp(val=-4.0, minval=0.0))
        self.assertEqual(0.0, clamp(val=-4.0, minval=0.0, maxval=8.0))
        self.assertEqual(5.0, clamp(val=5.0, maxval=10.0))
        self.assertEqual(5.0, clamp(val=5.0, minval=0.0, maxval=10.0))
        self.assertEqual(10.0, clamp(val=12.0, maxval=10.0))
        self.assertEqual(10.0, clamp(val=12.0, minval=0.0, maxval=10.0))

    def test_clamp_with_exception(self):
        self.assertRaises(ProgrammingError, clamp, val=4.0, minval=10.0, maxval=0.0)


class Test_DistanceP(unittest.TestCase):

    def test_distance(self):
        self.assertEqual(0.0, distanceP(QPointF(0, 0), QPointF(0, 0)))
        self.assertEqual(10.0, distanceP(QPointF(0, 0), QPointF(10, 0)))
        self.assertEqual(10.0, distanceP(QPointF(0, 0), QPointF(0, 10)))
        self.assertEqual(14.0, distanceP(QPointF(-4, 0), QPointF(10, 0)))
        self.assertEqual(14.0, distanceP(QPointF(0, -4), QPointF(0, 10)))
        self.assertEqual(10.0, distanceP(QPointF(0, 8), QPointF(6, 0)))
        self.assertEqual(10.0, distanceP(QPointF(0, -8), QPointF(-6, 0)))


class Test_DistanceL(unittest.TestCase):

    def test_distance(self):
        P = QPointF(2, 8)
        L = QLineF(QPointF(0, 0), QPointF(10, 0))
        D = distanceL(L, P)
        self.assertIsInstance(D, tuple)
        self.assertEqual(D[0], 8.0)
        self.assertEqual(D[1], QPointF(2, 0))


class Test_IntersectionL(unittest.TestCase):

    def test_intersection(self):
        self.assertEqual(QPointF(0, 0), intersectionL(QLineF(QPointF(-1, 0), QPointF(1, 0)), QLineF(QPointF(0, -1), QPointF(0, 1))))
        self.assertEqual(QPointF(-4, 0), intersectionL(QLineF(QPointF(-10, 0), QPointF(10, 0)), QLineF(QPointF(-4, -12), QPointF(-4, 14))))
        self.assertIsNone(intersectionL(QLineF(QPointF(-1, 0), QPointF(1, 0)), QLineF(QPointF(-1, 2), QPointF(1, 2))))


class Test_IsEmpty(unittest.TestCase):

    def test_empty(self):
        self.assertTrue(isEmpty(None))
        self.assertTrue(isEmpty(''))
        self.assertTrue(isEmpty('   '))
        self.assertFalse(isEmpty('Hello World'))
        self.assertFalse(isEmpty(4))

class Test_Midpoint(unittest.TestCase):

    def test_midpoint(self):
        self.assertEqual(QPointF(5, 0), midpoint(QPointF(0, 0), QPointF(10, 0)))
        self.assertEqual(QPointF(0, 5), midpoint(QPointF(0, 0), QPointF(0, 10)))
        self.assertEqual(QPointF(5, 5), midpoint(QPointF(0, 0), QPointF(10, 10)))


class Test_RangeF(unittest.TestCase):

    def test_generator(self):
        self.assertEqual([0.0, 1.0, 2.0, 3.0], list(rangeF(0.0, 4.0, 1.0)))
        self.assertEqual([0.0, 0.2, 0.4, 0.6, 0.8], list(rangeF(0.0, 1.0, 0.2)))
        self.assertEqual([0.0000, 0.0001, 0.0002, 0.0003, 0.0004], list(rangeF(0.0000, 0.0005, 0.0001)))


class Test_SnapF(unittest.TestCase):

    def test_snap_to_grid(self):
        self.assertEqual(10.0, snapF(value=8.0, gridsize=10.0))
        self.assertEqual(10.0, snapF(value=6.0, gridsize=10.0))
        self.assertEqual(0.0, snapF(value=5.0, gridsize=10.0))
        self.assertEqual(0.0, snapF(value=4.0, gridsize=10.0))
        self.assertEqual(0.0, snapF(value=2.0, gridsize=10.0))
        
    def test_snap_to_grid_with_offset(self):
        self.assertEqual(12.0, snapF(value=8.0, gridsize=10.0, offset=2.0))
        self.assertEqual(6.0, snapF(value=6.0, gridsize=10.0, offset=-4.0))

    def test_snap_to_grid_with_skip(self):
        self.assertEqual(8.0, snapF(value=8.0, gridsize=10.0, snap=False))
        self.assertEqual(6.0, snapF(value=6.0, gridsize=10.0, snap=False))