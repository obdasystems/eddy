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


from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.qt import VersionNumber


class TestDistinctList:
    """
    Tests for the DistinctList class.
    """
    def test_constructor_with_list(self):
        D1 = DistinctList([1, 2, 3, 3, 4, 1, 4, 5, 6, 7, 7, 8, 2])
        assert D1 == DistinctList([1, 2, 3, 4, 5, 6, 7, 8])

    def test_constructor_with_tuple(self):
        D1 = DistinctList((1, 2, 3, 3, 4, 1, 4, 5, 6, 7, 7, 8, 2))
        assert D1 == DistinctList((1, 2, 3, 4, 5, 6, 7, 8))

    def test_constructor_with_set(self):
        assert 8 == len(DistinctList({1, 2, 3, 4, 5, 6, 7, 8}))

    def test_append(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.append(9)
        assert D1 == DistinctList([1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_insert(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.insert(5, 9)
        assert D1 == DistinctList([1, 2, 3, 4, 5, 9, 6, 7, 8])

    def test_extend_with_list(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.extend([9, 10, 11, 12])
        assert D1 == DistinctList([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    def test_extend_with_tuple(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.extend((9, 10, 11, 12))
        assert D1 == DistinctList([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    def test_remove_with_match(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.remove(4)
        assert D1 == DistinctList([1, 2, 3, 5, 6, 7, 8])

    def test_remove_with_no_match(self):
        D1 = DistinctList([1, 2, 3, 4, 5, 6, 7, 8])
        D1.remove(9)
        assert D1 == DistinctList([1, 2, 3, 4, 5, 6, 7, 8])


class TestVersionNumber:
    """
    Tests for the VersionNumber class.
    """
    def test_version_init(self):
        assert VersionNumber().isNull()
        assert VersionNumber().isNormalized()
        assert VersionNumber().prerelease() is None
        assert VersionNumber().build() is None
        assert not VersionNumber(0).isNull()
        assert VersionNumber(0).prerelease() is None
        assert VersionNumber(0).build() is None
        assert not VersionNumber(1).isNull()
        assert VersionNumber(1).prerelease() is None
        assert VersionNumber(1).build() is None
        assert not VersionNumber(1, 0).isNull()
        assert VersionNumber(1, 0).prerelease() is None
        assert VersionNumber(1, 0).build() is None
        assert not VersionNumber(1, 0, 0).isNull()
        assert VersionNumber(1, 0, 0).prerelease() is None
        assert VersionNumber(1, 0, 0).build() is None
        assert not VersionNumber(1, 1, 0).isNull()
        assert VersionNumber(1, 1, 0).prerelease() is None
        assert VersionNumber(1, 1, 0).build() is None
        assert not VersionNumber(1, 1, 0, 'alpha').isNull()
        assert VersionNumber(1, 1, 0, 'alpha').prerelease() == 'alpha'
        assert VersionNumber(1, 1, 0, 'alpha').build() is None
        assert not VersionNumber(1, 1, 0, 'alpha', '123').isNull()
        assert VersionNumber(1, 1, 0, 'alpha', '123').prerelease() == 'alpha'
        assert VersionNumber(1, 1, 0, 'alpha', '123').build() == '123'

    def test_version_to_string(self):
        assert VersionNumber().toString() == ''
        assert VersionNumber(0).toString() == '0.0.0'
        assert VersionNumber(0, 0).toString() == '0.0.0'
        assert VersionNumber(0, 0, 0).toString() == '0.0.0'
        assert VersionNumber(0, 1, 0).toString() == '0.1.0'
        assert VersionNumber(0, 1, 0, 'alpha').toString() == '0.1.0-alpha'
        assert VersionNumber(0, 1, 0, 'alpha', 'git123').toString() == '0.1.0-alpha+git123'
        assert VersionNumber(0, 1, 0, build='git123').toString() == '0.1.0+git123'

    def test_version_from_string(self):
        assert VersionNumber.fromString('1').isNull()
        assert VersionNumber.fromString('0.1').isNull()
        assert VersionNumber.fromString('0.0.0.0').isNull()
        assert VersionNumber.fromString('0.0.1').toString() == '0.0.1'
        assert VersionNumber.fromString('0.0.1').prerelease() is None
        assert VersionNumber.fromString('0.0.1').build() is None
        assert VersionNumber.fromString('0.0.1').segmentCount() == 3
        assert VersionNumber.fromString('1.0.0-alpha1').toString() == '1.0.0-alpha1'
        assert VersionNumber.fromString('1.0.0-alpha1').prerelease() == 'alpha1'
        assert VersionNumber.fromString('1.0.0-alpha1').build() is None
        assert VersionNumber.fromString('1.0.0-alpha1').segmentCount() == 3
        assert VersionNumber.fromString('1.0.0+git123').toString() == '1.0.0+git123'
        assert VersionNumber.fromString('1.0.0+git123').prerelease() is None
        assert VersionNumber.fromString('1.0.0+git123').build() == 'git123'
        assert VersionNumber.fromString('1.0.0+git123').segmentCount() == 3
        assert VersionNumber.fromString('1.0.0+123').toString() == '1.0.0+123'
        assert VersionNumber.fromString('1.0.0+123').prerelease() is None
        assert VersionNumber.fromString('1.0.0+123').build() == '123'
        assert VersionNumber.fromString('1.0.0+123').segmentCount() == 3
        assert VersionNumber.fromString('1.0.0-rc1+git123').toString() == '1.0.0-rc1+git123'
        assert VersionNumber.fromString('1.0.0-rc1+git123').prerelease() == 'rc1'
        assert VersionNumber.fromString('1.0.0-rc1+git123').build() == 'git123'
        assert VersionNumber.fromString('1.0.0-rc1+git123').segmentCount() == 3
        assert VersionNumber.fromString('1.0.0-rc.1+build.123').toString() == '1.0.0-rc.1+build.123'
        assert VersionNumber.fromString('1.0.0-rc.1+build.123').prerelease() == 'rc.1'
        assert VersionNumber.fromString('1.0.0-rc.1+build.123').build() == 'build.123'
        assert VersionNumber.fromString('1.0.0-rc.1+build.123').segmentCount() == 3

    def test_version_compare(self):
        # EQUALITY
        assert VersionNumber() == VersionNumber()
        assert VersionNumber(0) == VersionNumber()
        assert VersionNumber(0) == VersionNumber(0, 0)
        assert VersionNumber(0) == VersionNumber(0, 0, 0)
        assert VersionNumber(0) != VersionNumber(0, 0, 0, 'alpha')
        assert VersionNumber(0, 0, 0, 'alpha', 'b1') == VersionNumber(0, 0, 0, 'alpha', 'b2')
        assert VersionNumber(0, 0, 0, 'beta1') != VersionNumber(0, 0, 0, 'beta2')
        # ORDERING
        assert VersionNumber(0, 1) > VersionNumber(0)
        assert VersionNumber(0, 1, 1) > VersionNumber(0, 1)
        assert not VersionNumber(0, 1, 1) < VersionNumber(0, 1, 1)
        assert VersionNumber(0, 1, 1) <= VersionNumber(0, 1, 1)
        assert VersionNumber(0, 1, 1) >= VersionNumber(0, 1, 1)
        assert not VersionNumber(0, 1, 1) > VersionNumber(0, 1, 1)
        assert VersionNumber(0, 1, 0, 'alpha') < VersionNumber(0, 1, 0)
        assert VersionNumber(0, 1, 0, 'alpha') < VersionNumber(0, 1, 1)
        assert VersionNumber(0, 1, 1, 'alpha') > VersionNumber(0, 0, 1)
        assert VersionNumber(0, 1, 0, 'alpha') < VersionNumber(0, 1, 0, 'beta')
        assert VersionNumber(0, 1, 0, 'alpha') < VersionNumber(0, 1, 1, 'alpha')
        assert VersionNumber(0, 1, 1, 'alpha') > VersionNumber(0, 0, 1, 'beta')
        assert VersionNumber(0, 1, 0, 'alpha', 'b1') >= VersionNumber(0, 0, 1)
        assert VersionNumber(0, 1, 0, 'alpha', 'b1') < VersionNumber(0, 1, 1)
        assert VersionNumber(0, 1, 1, 'alpha', 'b1') > VersionNumber(0, 0, 1)
        assert VersionNumber(0, 1, 0, 'alpha', 'b1') < VersionNumber(0, 1, 0, 'beta')
        assert VersionNumber(0, 1, 0, 'alpha', 'b1') < VersionNumber(0, 1, 1, 'alpha')
        assert VersionNumber(0, 1, 1, 'alpha', 'b1') > VersionNumber(0, 0, 1, 'beta')
        # FROM STRING
        assert VersionNumber.fromString('1.1.2-rc1') < VersionNumber.fromString('1.1.2')
        assert VersionNumber.fromString('1.2.0-rc1') > VersionNumber.fromString('1.1.2')
        assert VersionNumber.fromString('1.2.0-rc1') < VersionNumber.fromString('1.2.0')
        assert VersionNumber.fromString('1.2.0-rc2') > VersionNumber.fromString('1.2.0-rc1')
        assert VersionNumber.fromString('1.2.0-alpha2') > VersionNumber.fromString('1.2.0-alpha1')
        assert VersionNumber.fromString('1.2.0-alpha10') > VersionNumber.fromString('1.2.0-alpha1')
        assert VersionNumber.fromString('1.2.0-alpha10') > VersionNumber.fromString('1.2.0-alpha2')
        assert VersionNumber.fromString('1.2.0-beta1') > VersionNumber.fromString('1.2.0-alpha1')
        assert VersionNumber.fromString('1.2.0-rc1') > VersionNumber.fromString('1.2.0-alpha1')
        assert VersionNumber.fromString('1.2.0-rc1') > VersionNumber.fromString('1.2.0-beta1')
        assert VersionNumber.fromString('1.2.0-rc1+git123') == VersionNumber.fromString('1.2.0-rc1')
