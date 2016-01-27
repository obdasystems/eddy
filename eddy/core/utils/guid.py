# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QObject

from eddy.core.regex import RE_DIGIT, RE_ITEM_PREFIX


class GUID(QObject):
    """
    Class used to generate sequential IDs for DiagramScene items.
    """
    Start = 0
    Step = 1

    def __init__(self, parent=None):
        """
        Initialize the the unique id generator.
        :type parent: QObject
        """
        super().__init__(parent)
        self.ids = dict()

    def next(self, prefix):
        """
        Returns the next id available prepending the given prefix.
        :raise ValueError: if the given prefix contains digits.
        :type prefix: str
        :rtype: str
        """
        if RE_DIGIT.search(prefix):
            raise ValueError('invalid prefix supplied ({}): id prefix MUST not contain any digit'.format(prefix))
        try:
            last = self.ids[prefix]
        except KeyError:
            self.ids[prefix] = GUID.Start
        else:
            self.ids[prefix] = last + GUID.Step
        finally:
            return '{PREFIX}{ID}'.format(PREFIX=prefix, ID=self.ids[prefix])

    @staticmethod
    def parse(unique_id):
        """
        Parse the given unique id returning a tuple in the format (prefix, value).
        :raise ValueError: if the given value has an invalid format.
        :type unique_id: str
        :rtype: tuple
        """
        match = RE_ITEM_PREFIX.match(unique_id)
        if not match:
            raise ValueError('invalid id supplied ({})'.format(unique_id))
        return match.group('prefix'), int(match.group('value'))

    def update(self, unique_id):
        """
        Update the last incremental value according to the given id.
        :raise ValueError: if the given value has an invalid format.
        :type unique_id: str
        """
        prefix, value = self.parse(unique_id)
        try:
            last = self.ids[prefix]
        except KeyError:
            self.ids[prefix] = value
        else:
            self.ids[prefix] = max(last, value)

    def __repr__(self):
        """
        Return repr(self).
        """
        return 'GUID<{}>'.format(','.join(['{}:{}'.format(k, v) for k, v in self.ids.items()]))