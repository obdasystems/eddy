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


import unittest


from eddy.core.datatypes.collections import DistinctList


class DistinctListTestCase(unittest.TestCase):

    def test_constructor_with_list(self):
        D1 = DistinctList([1, 2, 3, 3, 4, 1, 4, 5, 6, 7, 7, 8, 2])
        self.assertSequenceEqual(D1, DistinctList([1, 2, 3, 4, 5, 6, 7, 8]), seq_type=DistinctList)

    def test_constructor_with_tuple(self):
        D1 = DistinctList((1, 2, 3, 3, 4, 1, 4, 5, 6, 7, 7, 8, 2))
        self.assertSequenceEqual(D1, DistinctList((1, 2, 3, 4, 5, 6, 7, 8)), seq_type=DistinctList)

    def test_constructor_with_set(self):
        self.assertEqual(8, len(DistinctList({1, 2, 3, 4, 5, 6, 7, 8})))

    def test_append(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.append(9)
        self.assertSequenceEqual(D1, DistinctList([1, 2, 3, 4, 5, 6, 7, 8, 9]), seq_type=DistinctList)

    def test_insert(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.insert(5, 9)
        self.assertSequenceEqual(D1, DistinctList([1, 2, 3, 4, 5, 9, 6, 7, 8]), seq_type=DistinctList)

    def test_extend_with_list(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.extend([9, 10, 11, 12])
        self.assertSequenceEqual(D1, DistinctList([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]), seq_type=DistinctList)

    def test_extend_with_tuple(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.extend((9, 10, 11, 12))
        self.assertSequenceEqual(D1, DistinctList([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]), seq_type=DistinctList)

    def test_remove_with_match(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.remove(4)
        self.assertSequenceEqual(D1, DistinctList([1, 2, 3, 5, 6, 7, 8]), seq_type=DistinctList)

    def test_remove_with_no_match(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.remove(9)
        self.assertSequenceEqual(D1, DistinctList([1, 2, 3, 4, 5, 6, 7, 8]), seq_type=DistinctList)