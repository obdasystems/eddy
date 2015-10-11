# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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


import re


RE_DIGIT = re.compile("""\d""")
RE_PARSE = re.compile("""^(?P<prefix>[^\d])(?P<value>\d+)$""")


class UniqueID(object):
    """
    Helper class used to generate sequential IDs for GraphicScene items.
    """
    start = 0 # the initial id number
    step = 1 # incremental step

    def __init__(self):
        """
        Initialize the UniqueID generator.
        """
        self.ids = dict()

    def next(self, prefix):
        """
        Returns the next id available prepending the given prefix.
        :param prefix: the prefix to be added before the node (usually 'n' for nodes and 'e' for edges).
        :raise ValueError: if the given prefix contains digits.
        :rtype: str
        """
        if RE_DIGIT.search(prefix):
            raise ValueError('invalid prefix supplied (%s): id prefix MUST not contain any digit' % prefix)
        try:
            last = self.ids[prefix]
        except KeyError:
            self.ids[prefix] = UniqueID.start
        else:
            self.ids[prefix] = last + UniqueID.step
        finally:
            return '%s%s' % (prefix, self.ids[prefix])

    @staticmethod
    def parse(unique_id):
        """
        Parse the given unique id returning a tuple in the format (prefix, value).
        :raise ValueError: if the given value has an invalid format.
        :param unique_id: the unique id to parse.
        :rtype: tuple
        """
        match = RE_PARSE.match(unique_id)
        if not match:
            raise ValueError('invalid id supplied (%s)' % unique_id)
        return match.group('prefix'), int(match.group('value'))

    def update(self, unique_id):
        """
        Update the last incremental value according to the given id.
        :raise ValueError: if the given value has an invalid format.
        :param unique_id: the for incremental adjustment.
        """
        prefix, value = self.parse(unique_id)

        try:
            last = self.ids[prefix]
        except KeyError:
            self.ids[prefix] = value
        else:
            self.ids[prefix] = max(last, value)