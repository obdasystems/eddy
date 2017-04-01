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


class DistinctList(list):
    """
    Extends python default list making sure not to have duplicated elements.
    """
    def __init__(self, collection=None):
        """
        Initialize the DistinctList.
        :type collection: iterable
        """
        super(DistinctList, self).__init__()
        if collection:
            for item in collection:
                self.append(item)

    def append(self, p_object):
        """
        Append the given element at the end of the list.
        :type p_object: mixed
        """
        if p_object not in self:
            super(DistinctList, self).append(p_object)

    def extend(self, iterable):
        """
        Extends the current list by appending items of the given iterable (if they are not in the list already).
        :type iterable: iterable
        """
        for item in iterable:
            self.append(item)

    def insert(self, index, p_object):
        """
        Insert the given element in the given index.
        :type index: int
        :type p_object: mixed
        """
        if p_object in self:
            index2 = self.index(p_object)
            if index2 < index:
                index -= 1
            self.remove(p_object)
        super(DistinctList, self).insert(index, p_object)

    def remove(self, p_object):
        """
        Silently remove the given element from the list.
        :type p_object: mixed
        """
        try:
            super(DistinctList, self).remove(p_object)
        except ValueError:
            pass

    def sanitize(self, f_sanitize):
        """
        Remove all the elements in this list for which the given callable returns False.
        :type f_sanitize: callable.
        """
        for p_object in self:
            if not f_sanitize(p_object):
                self.remove(p_object)

    def __add__(self, p_object):
        """ x.__add__(y) <==> x+y """
        copy = self[:]
        if isinstance(p_object, set) or isinstance(p_object, frozenset):
            p_object = list(p_object)
        if isinstance(p_object, list) or isinstance(p_object, tuple):
            copy.extend(p_object)
        else:
            copy.append(p_object)
        return copy

    def __radd__(self, p_object):
        """ x.__radd__(y) <==> y+x """
        copy = self[:]
        if isinstance(p_object, set) or isinstance(p_object, frozenset):
            p_object = list(p_object)
        if isinstance(p_object, list) or isinstance(p_object, tuple):
            for x in range(len(p_object)):
                copy.insert(x, p_object[x])
        else:
            copy.insert(0, p_object)
        return copy

    def __iadd__(self, p_object):
        """ x.__iadd__(y) <==> x+=y """
        if isinstance(p_object, set) or isinstance(p_object, frozenset):
            p_object = list(p_object)
        if isinstance(p_object, list) or isinstance(p_object, tuple):
            self.extend(p_object)
        else:
            self.append(p_object)
        return self

    def __getitem__(self, p_object):
        """ x.__getitem__(y) <==> x[y] """
        if isinstance(p_object, slice):
            return DistinctList([super(DistinctList, self).__getitem__(x) for x in range(*p_object.indices(len(self)))])
        else:
            return super(DistinctList, self).__getitem__(p_object)

    def __getslice__(self, i, j):
        """
        x.__getslice__(i, j) <==> x[i:j] (built-in CPython types needs this one).
        Use of negative indices is not supported.
        """
        return self[max(0, i):max(0, j):]