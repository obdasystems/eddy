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


from PyQt5 import QtCore

from eddy.core.regex import RE_DIGIT, RE_ITEM_PREFIX


class GUID(QtCore.QObject):
    """
    Class used to generate sequential ids for diagram elements.
    """
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
            raise ValueError('invalid prefix supplied ({0}): id prefix MUST not contain any digit'.format(prefix))
        try:
            uid = self.ids[prefix]
        except KeyError:
            self.ids[prefix] = 0
        else:
            self.ids[prefix] = uid + 1
        return '{}{}'.format(prefix, self.ids[prefix])

    @staticmethod
    def parse(uid):
        """
        Parse the given unique id returning a tuple in the format (prefix -> str, value -> int).
        :type uid: str
        :rtype: tuple
        """
        match = RE_ITEM_PREFIX.match(uid)
        if not match:
            raise ValueError('invalid id supplied ({0})'.format(uid))
        return match.group('prefix'), int(match.group('value'))

    def update(self, uid):
        """
        Update the last incremental value according to the given id.
        :type uid: str
        """
        prefix, value = self.parse(uid)
        try:
            uid = self.ids[prefix]
        except KeyError:
            self.ids[prefix] = value
        else:
            self.ids[prefix] = max(uid, value)

    def __repr__(self):
        """
        Return repr(self).
        """
        return 'GUID<{0}>'.format(','.join(['{0}:{1}'.format(k, v) for k, v in self.ids.items()]))