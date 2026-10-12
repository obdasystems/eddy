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

from eddy.core.tags import Tag


class TestTags:
    """Tests for the Tag class."""

    def test_tag_eq(self):
        T1a = Tag('T1', 'Test tag 1', id='t1')
        T1b = Tag('T1', 'Test tag 1', id='t1b')
        T1c = Tag('T1', 'Test tag 1', id='t1')
        T2a = Tag('T2')
        T2b = Tag('T2', description='Other desc')
        T2c = Tag(' T2 ')
        assert T1a == T1a  # Same object
        assert T1a == T1c  # Other object with same fields
        assert id(T1a) != id(T1c)
        assert T1a != T1b  # Different id
        assert T2a != T2b  # T2b has no description
        assert T2a != T2c  # Spaces in T2c name

    def test_tree_init_nested(self):
        T = Tag('N0')
        T.addTag(Tag('N1')).addTag(Tag('N2').addTag(Tag('N3')))
        assert T.name == 'N0'
        assert T.subtag[0].name == 'N1'
        assert T.subtag[0].path == f'N0 {Tag.BRANCH} N1'
        assert T.subtag[1].name == 'N2'
        assert T.subtag[1].path == f'N0 {Tag.BRANCH} N2'
        assert T.subtag[1].subtag[0].path == f'N0 {Tag.BRANCH} N2 {Tag.BRANCH} N3'
        assert T.parent is None
        assert T.subtag[0].parent is T
        assert T.subtag[1].parent is T
        assert T.subtag[1].subtag[0].parent is T.subtag[1]
        assert T.path == 'N0'

    def test_tree_init_sequential(self):
        T = Tag('N0')
        N1 = Tag('N1', parent=T)
        N2 = Tag('N2', parent=T)
        N3 = Tag('N3', parent=N2)
        assert T.name == 'N0'
        assert N1.name == 'N1'
        assert N1.path == f'N0 {Tag.BRANCH} N1'
        assert N2.name == 'N2'
        assert N2.path == f'N0 {Tag.BRANCH} N2'
        assert N2.subtag[0].path == f'N0 {Tag.BRANCH} N2 {Tag.BRANCH} N3'
        assert T.parent is None
        assert N1.parent is T
        assert N2.parent is T
        assert N3.parent is N2
        assert T.path == 'N0'

    def test_tree_find(self):
        T = Tag('N0')
        N1_1 = Tag('N1_1', parent=T)
        N1_2 = Tag('N1_2', parent=T)
        N2_1 = Tag('N2_1', parent=N1_2)
        N2_2 = Tag('N2_2', parent=N1_2)
        N3_1 = Tag('N3_1', parent=N2_1)
        assert T.find('N2_.*') == [N2_1, N2_2]
        assert T.find('N3.*') == T.find('N3_1')

    def test_tree_getitem(self):
        T = Tag('N0')
        N1 = Tag('N1', parent=T)
        N2 = Tag('N2', parent=T)
        N3 = Tag('N3', parent=N2)
        assert T[T.id] == T
        assert T[N1.id] == N1
        assert T[N2.id] == N2
        assert T[N3.id] == N3
