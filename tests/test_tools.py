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


import pytest

from eddy.core.generators import GUID


class TestGUID:

    def test_unique_id_generation(self):
        guid = GUID()
        assert 'n0' == guid.next('n')
        assert 'n1' == guid.next('n')
        assert 'e0' == guid.next('e')
        assert 'n2' == guid.next('n')
        assert 'e1' == guid.next('e')
        assert {'n': 2, 'e': 1} == guid.ids

    def test_unique_id_generation_with_exception(self):
        guid = GUID()
        with pytest.raises(ValueError):
            guid.next('1')
        with pytest.raises(ValueError):
            guid.next('n1')
        with pytest.raises(ValueError):
            guid.next('n 1')

    def test_unique_id_update(self):
        guid = GUID()
        guid.update('n19')
        guid.update('e7')
        assert {'n': 19, 'e': 7} == guid.ids

    def test_unique_id_parse(self):
        assert ('n', 8) == GUID.parse('n8')
        assert ('e', 122) == GUID.parse('e122')

    def test_unique_id_parse_with_exception(self):
        with pytest.raises(ValueError):
            GUID.parse('1')
        with pytest.raises(ValueError):
            GUID.parse('n')
        with pytest.raises(ValueError):
            GUID.parse('n 8')