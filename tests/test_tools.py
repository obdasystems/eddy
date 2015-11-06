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


import unittest

from grapholed.tools import UniqueID


class Test_UniqueID(unittest.TestCase):

    def test_unique_id_generation(self):
        uniqueid = UniqueID()
        self.assertEqual('n0', uniqueid.next('n'))
        self.assertEqual('n1', uniqueid.next('n'))
        self.assertEqual('e0', uniqueid.next('e'))
        self.assertEqual('n2', uniqueid.next('n'))
        self.assertEqual('e1', uniqueid.next('e'))
        self.assertEqual({'n': 2, 'e': 1}, uniqueid.ids)

    def test_unique_id_generation_with_exception(self):
        uniqueid = UniqueID()
        self.assertRaises(ValueError, uniqueid.next, '1')
        self.assertRaises(ValueError, uniqueid.next, 'n1')
        self.assertRaises(ValueError, uniqueid.next, 'n 1')

    def test_unique_id_update(self):
        uniqueid = UniqueID()
        uniqueid.update('n19')
        uniqueid.update('e7')
        self.assertEqual({'n': 19, 'e': 7}, uniqueid.ids)

    def test_unique_id_parse(self):
        self.assertEqual(('n', 8), UniqueID.parse('n8'))
        self.assertEqual(('e', 122), UniqueID.parse('e122'))

    def test_unique_id_parse_with_exception(self):
        self.assertRaises(ValueError, UniqueID.parse, '1')
        self.assertRaises(ValueError, UniqueID.parse, 'n')
        self.assertRaises(ValueError, UniqueID.parse, 'n 8')