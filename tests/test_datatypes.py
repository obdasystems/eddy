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

from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.qt import (
    SemVerVersionNumber,
    VersionNumber,
)


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


class TestSemVerVersionNumber:
    """
    Tests for the SemVerVersionNumber class.
    """
    def test_version_init(self):
        assert SemVerVersionNumber().isNull()
        assert SemVerVersionNumber().isNormalized()
        assert SemVerVersionNumber().prerelease() is None
        assert SemVerVersionNumber().build() is None
        assert not SemVerVersionNumber(0).isNull()
        assert SemVerVersionNumber(0).prerelease() is None
        assert SemVerVersionNumber(0).build() is None
        assert not SemVerVersionNumber(1).isNull()
        assert SemVerVersionNumber(1).prerelease() is None
        assert SemVerVersionNumber(1).build() is None
        assert not SemVerVersionNumber(1, 0).isNull()
        assert SemVerVersionNumber(1, 0).prerelease() is None
        assert SemVerVersionNumber(1, 0).build() is None
        assert not SemVerVersionNumber(1, 0, 0).isNull()
        assert SemVerVersionNumber(1, 0, 0).prerelease() is None
        assert SemVerVersionNumber(1, 0, 0).build() is None
        assert not SemVerVersionNumber(1, 1, 0).isNull()
        assert SemVerVersionNumber(1, 1, 0).prerelease() is None
        assert SemVerVersionNumber(1, 1, 0).build() is None
        assert not SemVerVersionNumber(1, 1, 0, 'alpha').isNull()
        assert SemVerVersionNumber(1, 1, 0, 'alpha').prerelease() == 'alpha'
        assert SemVerVersionNumber(1, 1, 0, 'alpha').build() is None
        assert not SemVerVersionNumber(1, 1, 0, 'alpha', '123').isNull()
        assert SemVerVersionNumber(1, 1, 0, 'alpha', '123').prerelease() == 'alpha'
        assert SemVerVersionNumber(1, 1, 0, 'alpha', '123').build() == '123'

    def test_version_to_string(self):
        assert SemVerVersionNumber().toString() == ''
        assert SemVerVersionNumber(0).toString() == '0.0.0'
        assert SemVerVersionNumber(0, 0).toString() == '0.0.0'
        assert SemVerVersionNumber(0, 0, 0).toString() == '0.0.0'
        assert SemVerVersionNumber(0, 1, 0).toString() == '0.1.0'
        assert SemVerVersionNumber(0, 1, 0, 'alpha').toString() == '0.1.0-alpha'
        assert SemVerVersionNumber(0, 1, 0, 'alpha', 'git123').toString() == '0.1.0-alpha+git123'
        assert SemVerVersionNumber(0, 1, 0, build='git123').toString() == '0.1.0+git123'

    def test_version_from_string(self):
        assert SemVerVersionNumber.fromString('1').isNull()
        assert SemVerVersionNumber.fromString('0.1').isNull()
        assert SemVerVersionNumber.fromString('0.0.0.0').isNull()
        assert SemVerVersionNumber.fromString('0.0.1').toString() == '0.0.1'
        assert SemVerVersionNumber.fromString('0.0.1').prerelease() is None
        assert SemVerVersionNumber.fromString('0.0.1').build() is None
        assert SemVerVersionNumber.fromString('0.0.1').segmentCount() == 3
        assert SemVerVersionNumber.fromString('1.0.0-alpha1').toString() == '1.0.0-alpha1'
        assert SemVerVersionNumber.fromString('1.0.0-alpha1').prerelease() == 'alpha1'
        assert SemVerVersionNumber.fromString('1.0.0-alpha1').build() is None
        assert SemVerVersionNumber.fromString('1.0.0-alpha1').segmentCount() == 3
        assert SemVerVersionNumber.fromString('1.0.0+git123').toString() == '1.0.0+git123'
        assert SemVerVersionNumber.fromString('1.0.0+git123').prerelease() is None
        assert SemVerVersionNumber.fromString('1.0.0+git123').build() == 'git123'
        assert SemVerVersionNumber.fromString('1.0.0+git123').segmentCount() == 3
        assert SemVerVersionNumber.fromString('1.0.0+123').toString() == '1.0.0+123'
        assert SemVerVersionNumber.fromString('1.0.0+123').prerelease() is None
        assert SemVerVersionNumber.fromString('1.0.0+123').build() == '123'
        assert SemVerVersionNumber.fromString('1.0.0+123').segmentCount() == 3
        assert SemVerVersionNumber.fromString('1.0.0-rc1+git123').toString() == '1.0.0-rc1+git123'
        assert SemVerVersionNumber.fromString('1.0.0-rc1+git123').prerelease() == 'rc1'
        assert SemVerVersionNumber.fromString('1.0.0-rc1+git123').build() == 'git123'
        assert SemVerVersionNumber.fromString('1.0.0-rc1+git123').segmentCount() == 3
        assert SemVerVersionNumber.fromString('1.0.0-rc.1+build.123').toString() == '1.0.0-rc.1+build.123'
        assert SemVerVersionNumber.fromString('1.0.0-rc.1+build.123').prerelease() == 'rc.1'
        assert SemVerVersionNumber.fromString('1.0.0-rc.1+build.123').build() == 'build.123'
        assert SemVerVersionNumber.fromString('1.0.0-rc.1+build.123').segmentCount() == 3

    def test_version_compare(self):
        # EQUALITY
        assert SemVerVersionNumber() == SemVerVersionNumber()
        assert SemVerVersionNumber(0) == SemVerVersionNumber()
        assert SemVerVersionNumber(0) == SemVerVersionNumber(0, 0)
        assert SemVerVersionNumber(0) == SemVerVersionNumber(0, 0, 0)
        assert SemVerVersionNumber(0) != SemVerVersionNumber(0, 0, 0, 'alpha')
        assert SemVerVersionNumber(0, 0, 0, 'alpha', 'b1') == SemVerVersionNumber(0, 0, 0, 'alpha', 'b2')
        assert SemVerVersionNumber(0, 0, 0, 'beta1') != SemVerVersionNumber(0, 0, 0, 'beta2')
        # ORDERING
        assert SemVerVersionNumber(0, 1) > SemVerVersionNumber(0)
        assert SemVerVersionNumber(0, 1, 1) > SemVerVersionNumber(0, 1)
        assert not SemVerVersionNumber(0, 1, 1) < SemVerVersionNumber(0, 1, 1)
        assert SemVerVersionNumber(0, 1, 1) <= SemVerVersionNumber(0, 1, 1)
        assert SemVerVersionNumber(0, 1, 1) >= SemVerVersionNumber(0, 1, 1)
        assert not SemVerVersionNumber(0, 1, 1) > SemVerVersionNumber(0, 1, 1)
        assert SemVerVersionNumber(0, 1, 0, 'alpha') < SemVerVersionNumber(0, 1, 0)
        assert SemVerVersionNumber(0, 1, 0, 'alpha') < SemVerVersionNumber(0, 1, 1)
        assert SemVerVersionNumber(0, 1, 1, 'alpha') > SemVerVersionNumber(0, 0, 1)
        assert SemVerVersionNumber(0, 1, 0, 'alpha') < SemVerVersionNumber(0, 1, 0, 'beta')
        assert SemVerVersionNumber(0, 1, 0, 'alpha') < SemVerVersionNumber(0, 1, 1, 'alpha')
        assert SemVerVersionNumber(0, 1, 1, 'alpha') > SemVerVersionNumber(0, 0, 1, 'beta')
        assert SemVerVersionNumber(0, 1, 0, 'alpha', 'b1') >= SemVerVersionNumber(0, 0, 1)
        assert SemVerVersionNumber(0, 1, 0, 'alpha', 'b1') < SemVerVersionNumber(0, 1, 1)
        assert SemVerVersionNumber(0, 1, 1, 'alpha', 'b1') > SemVerVersionNumber(0, 0, 1)
        assert SemVerVersionNumber(0, 1, 0, 'alpha', 'b1') < SemVerVersionNumber(0, 1, 0, 'beta')
        assert SemVerVersionNumber(0, 1, 0, 'alpha', 'b1') < SemVerVersionNumber(0, 1, 1, 'alpha')
        assert SemVerVersionNumber(0, 1, 1, 'alpha', 'b1') > SemVerVersionNumber(0, 0, 1, 'beta')
        # FROM STRING
        assert SemVerVersionNumber.fromString('1.1.2-rc1') < SemVerVersionNumber.fromString('1.1.2')
        assert SemVerVersionNumber.fromString('1.2.0-rc1') > SemVerVersionNumber.fromString('1.1.2')
        assert SemVerVersionNumber.fromString('1.2.0-rc1') < SemVerVersionNumber.fromString('1.2.0')
        assert SemVerVersionNumber.fromString('1.2.0-rc2') > SemVerVersionNumber.fromString('1.2.0-rc1')
        assert SemVerVersionNumber.fromString('1.2.0-alpha2') > SemVerVersionNumber.fromString('1.2.0-alpha1')
        assert SemVerVersionNumber.fromString('1.2.0-alpha10') > SemVerVersionNumber.fromString('1.2.0-alpha1')
        assert SemVerVersionNumber.fromString('1.2.0-alpha10') > SemVerVersionNumber.fromString('1.2.0-alpha2')
        assert SemVerVersionNumber.fromString('1.2.0-beta1') > SemVerVersionNumber.fromString('1.2.0-alpha1')
        assert SemVerVersionNumber.fromString('1.2.0-rc1') > SemVerVersionNumber.fromString('1.2.0-alpha1')
        assert SemVerVersionNumber.fromString('1.2.0-rc1') > SemVerVersionNumber.fromString('1.2.0-beta1')
        assert SemVerVersionNumber.fromString('1.2.0-rc1+git123') == SemVerVersionNumber.fromString('1.2.0-rc1')


VERSIONS = [
    "1.0.dev456",
    "1.0a1",
    "1.0a2.dev456",
    "1.0a12.dev456",
    "1.0a12",
    "1.0b1.dev456",
    "1.0b2",
    "1.0b2.post345.dev456",
    "1.0b2.post345",
    "1.0rc2",
    "1.0",
    "1.0.post456.dev34",
    "1.0.post456",
    "1.1.dev1",
    "1.2+123abc",
    "1.2+123abc456",
    "1.2+abc",
    "1.2+abc123",
    "1.2+abc123def",
    "1!1.0.dev456",
    "1!1.0a1",
    "1!1.0a2.dev456",
    "1!1.0a12.dev456",
    "1!1.0a12",
    "1!1.0b1.dev456",
    "1!1.0b2",
    "1!1.0b2.post345.dev456",
    "1!1.0b2.post345",
    "1!1.0rc2",
    "1!1.0",
    "1!1.0.post456.dev34",
    "1!1.0.post456",
    "1!1.1.dev1",
    "1!1.2+123abc",
    "1!1.2+123abc456",
    "1!1.2+abc",
    "1!1.2+abc123",
    "1!1.2+abc123def",
]


class TestVersionNumber:
    """
    Tests for the VersionNumber class.
    """

    @pytest.mark.parametrize('version', VERSIONS)
    def test_version_valid(self, version):
        assert not VersionNumber(version).isNull()

    @pytest.mark.parametrize(
        'version',
        [
            "no version",
            "1.0+a+",
            "1.0++",
            "1.0+_foobar",
            "1.0+foo&asd",
            "1.0+1+1",
        ],
    )
    def test_version_null(self, version):
        assert VersionNumber(version).isNull()

    @pytest.mark.parametrize(
        'versions',
        [reversed(VERSIONS)]
    )
    def test_version_sort(self, versions):
        assert list(map(str, sorted(map(VersionNumber, versions)))) == VERSIONS

    @pytest.mark.parametrize(
        ('version', 'expected'),
        [
            ('1.0.dev456', '1.0.dev456'),
            ('1.0a1', '1.0a1'),
            ('1.0a2.dev456', '1.0a2.dev456'),
            ('1.0a12.dev456', '1.0a12.dev456'),
            ('1.0a12', '1.0a12'),
            ('1.0b1.dev456', '1.0b1.dev456'),
            ('1.0b2', '1.0b2'),
            ('1.0b2.post345.dev456', '1.0b2.post345.dev456'),
            ('1.0b2.post345', '1.0b2.post345'),
            ('1.0rc1.dev456', '1.0rc1.dev456'),
            ('1.0rc1', '1.0rc1'),
            ('1.0', '1.0'),
            ('1.0.post456.dev34', '1.0.post456.dev34'),
            ('1.0.post456', '1.0.post456'),
            ('1.0.1', '1.0.1'),
            ('0!1.0.2', '1.0.2'),
            ('1.0.3+7', '1.0.3+7'),
            ('0!1.0.4+8.0', '1.0.4+8.0'),
            ('1.0.5+9.5', '1.0.5+9.5'),
            ('1.2+1234.abc', '1.2+1234.abc'),
            ('1.2+123456', '1.2+123456'),
            ('1.2+123abc', '1.2+123abc'),
            ('1.2+123abc456', '1.2+123abc456'),
            ('1.2+abc', '1.2+abc'),
            ('1.2+abc123', '1.2+abc123'),
            ('1.2+abc123def', '1.2+abc123def'),
            ('1.1.dev1', '1.1.dev1'),
            ('7!1.0.dev456', '7!1.0.dev456'),
            ('7!1.0a1', '7!1.0a1'),
            ('7!1.0a2.dev456', '7!1.0a2.dev456'),
            ('7!1.0a12.dev456', '7!1.0a12.dev456'),
            ('7!1.0a12', '7!1.0a12'),
            ('7!1.0b1.dev456', '7!1.0b1.dev456'),
            ('7!1.0b2', '7!1.0b2'),
            ('7!1.0b2.post345.dev456', '7!1.0b2.post345.dev456'),
            ('7!1.0b2.post345', '7!1.0b2.post345'),
            ('7!1.0rc1.dev456', '7!1.0rc1.dev456'),
            ('7!1.0rc1', '7!1.0rc1'),
            ('7!1.0', '7!1.0'),
            ('7!1.0.post456.dev34', '7!1.0.post456.dev34'),
            ('7!1.0.post456', '7!1.0.post456'),
            ('7!1.0.1', '7!1.0.1'),
            ('7!1.0.2', '7!1.0.2'),
            ('7!1.0.3+7', '7!1.0.3+7'),
            ('7!1.0.4+8.0', '7!1.0.4+8.0'),
            ('7!1.0.5+9.5', '7!1.0.5+9.5'),
            ('7!1.1.dev1', '7!1.1.dev1'),
        ],
    )
    def test_version_str_repr(self, version, expected):
        assert str(VersionNumber(version)) == expected
        assert repr(VersionNumber(version)) == "<VersionNumber({0})>".format(repr(expected))
