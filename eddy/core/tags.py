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


from __future__ import annotations

import re

from eddy.core.generators import GUID

guid = GUID()  # id generator for tags


class Tag:
    """
    A tree-based metadata structure that can be associated with IRIs.
    """
    BRANCH: str = '>>'  # Tree branch symbol when serialized as a string.

    def __init__(
        self,
        name: str,
        description: str | None = None,
        parent: Tag | None = None,
        id: str | None = None,
    ):
        """Initialize the tag with the given fields."""
        # Validate arguments
        if not isinstance(name, str):
            raise TypeError('Tag name must be a string')
        if description is not None and not isinstance(description, str):
            raise TypeError('Tag description if present must be a string')
        if parent is not None and not isinstance(parent, Tag):
            raise TypeError('Tag parent if present must be another Tag instance')
        # Init instance fields
        if id:
            guid.parse(id)  # Try validating id for tag
            self._id: str = id
            guid.update(self._id)
        else:
            self._id: str = guid.next('t')
        self._name: str = name
        self._description: str | None = description
        self._subtag: list[Tag] = []
        self._parent: Tag | None = parent

        if parent:
            self._parent.addTag(self)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def id(self) -> str:
        """Returns the id of this tag."""
        return self._id

    @property
    def name(self) -> str:
        """Returns the name of this tag."""
        return self._name

    @property
    def description(self) -> str:
        """Returns the description of this tag."""
        return self._description

    @property
    def parent(self) -> Tag | None:
        """Returns the parent of this node, if any, or `None` if it is the root of the tree. """
        return self._parent

    @property
    def path(self) -> str:
        """Returns the path representation of this tag."""
        return str(self)

    @property
    def subtag(self) -> list[Tag] | None:
        """Returns the list of sub-tags of this tree node, or `None` if it is a leaf."""
        return self._subtag

    #############################################
    #   INTERFACE
    #################################

    def addTag(self, tag: Tag) -> Tag:
        """Adds the given tag as a subtag of the current tag."""
        if not isinstance(tag, self.__class__):
            raise TypeError(f"Cannot append tree node type: {type(tag)}")
        self._subtag.append(tag)
        tag._parent = self
        return self

    def find(
        self,
        regexp: str | re.Pattern[bytes | str],
        matches: list[Tag] = None,
    ) -> list[Tag]:
        """Returns the tags in the subtree whose name or description matches the given regex."""
        pattern = re.compile(regexp) if isinstance(regexp, (bytes, str)) else regexp
        # Init empty match list is not passed
        if matches is None:
            matches = []
        # First check match on name
        if pattern.search(self.name):
            matches.append(self)
        # then check match on description if present
        elif self.description and pattern.search(self.description):
            matches.append(self)
        # Recursive step
        for tag in self.subtag:
            tag.find(regexp, matches)
        return matches

    def __eq__(self, other: Tag) -> bool:
        """Tests whether this item is equal to the given item."""
        return (
            other and
            self.id == other.id and
            self.name == other.name and
            self.description == other.description
        )

    def __getitem__(self, item: str) -> Tag | None:
        """Search the tag subtree for a tag with the given id."""
        if self.id == item:
            return self
        for tag in self.subtag:
            c = tag[item]
            if c:
                return c
        return None

    def __str__(self) -> str:
        """String representation of this node in the tree."""
        if self.parent:
            path = f'{str(self.parent)} {self.BRANCH} {self._name}'
        else:
            path = self._name

        return path

    def __repr__(self):
        """Plain string representation of this node in the tree."""
        return repr(str(self))
