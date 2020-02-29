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


import re

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets
)


class Font(QtGui.QFont):
    """
    Thin wrapper around QtGui.QFont to provide convenient constructors.
    """
    def __init__(self, family=None, size=-1, weight=-1, italic=False, **kwargs):
        """
        Contruct a new Font instance using the given parameters.
        :type family: str
        :type size: int
        :type weight: int
        :type italic: bool
        """
        font = kwargs.get('font', None)
        if font:
            # CALL COPY CONSTRUCTOR
            super().__init__(font)
        elif not family:
            # CONSTRUCT FROM DEFAULT FONT
            super().__init__()
            if size > 0:
                self.setPointSize(round(size))
            if weight > 0:
                self.setWeight(weight)
            self.setItalic(italic)
        else:
            # CALL GENERIC FONT CONSTRUCTOR
            super().__init__(family, size, weight, italic)
        # USE PIXEL SIZE IF SPECIFIED
        pixelSize = kwargs.get('pixelSize', -1)
        if pixelSize > 0:
            self.setPixelSize(round(pixelSize))
        # FONT ATTRIBUTES
        self.setItalic(italic)
        self.setBold(kwargs.get('bold', False))
        self.setCapitalization(kwargs.get('capitalization', QtGui.QFont.MixedCase))
        self.setStyleHint(kwargs.get('style', QtGui.QFont.AnyStyle))
        # SCALE FACTOR
        scale = kwargs.get('scale', None)
        if scale:
            if self.pointSize() <= 0:
                self.setPixelSize(round(self.pixelSize() * scale))
            else:
                self.setPointSizeF(self.pointSizeF() * scale)


class Collator(QtCore.QCollator):
    """
    Subclass of QtCore.QCollator that allows comparison of non-string elements.
    """
    def __init__(self, locale=QtCore.QLocale(), **kwargs):
        """
        Initialize a new Collator instance.
        :type locale: QLocale
        :type kwargs: dict
        """
        # noinspection PyArgumentList
        super().__init__(locale, **kwargs)

    def sortKey(self, item):
        """
        Returns the sort key for the given item. If the given item
        is not of type `str`, then it will be converted automatically.
        :type item: Any
        :rtype: str
        """
        return super().sortKey(item if isinstance(item, str) else str(item))


class BrushIcon(QtGui.QIcon):
    """
    This class extends QtGui.QIcon and automatically creates an icon filled with the given color.
    """
    def __init__(self, width, height, color, border=None):
        """
        Initialize the icon.
        :type width: T <= int | float
        :type height: T <= int | float
        :type color: str
        :type border: str
        """
        pixmap = QtGui.QPixmap(width, height)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        path = QtGui.QPainterPath()
        path.addRect(QtCore.QRectF(QtCore.QPointF(0, 0), QtCore.QPointF(width, height)))
        painter.fillPath(path, QtGui.QBrush(QtGui.QColor(color)))
        if border:
            painter.setPen(QtGui.QPen(QtGui.QColor(border), 0, QtCore.Qt.SolidLine))
            painter.drawPath(path)
        painter.end()
        super().__init__(pixmap)


class PHCQPushButton(QtWidgets.QPushButton):
    """
    This class extends QtWidgets.QPushButton providing mouse cursor change then the mour pointer hover the button area.
    """
    def __init__(self, parent=None):
        """
        Initialize the button.
        """
        super().__init__(parent)

    #############################################
    #   EVENTS
    #################################

    def enterEvent(self, event):
        """
        Executed when the mouse enter the widget.
        :type event: QEvent
        """
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """
        Executed when the mouse leave the widget.
        :type event: QEvent
        """
        self.unsetCursor()


class PHCQToolButton(QtWidgets.QToolButton):
    """
    This class extends QtWidgets.QToolButton providing mouse cursor change then the mour pointer hover the button area.
    """
    def __init__(self, parent=None):
        """
        Initialize the button.
        """
        super().__init__(parent)

    #############################################
    #   EVENTS
    #################################

    def enterEvent(self, event):
        """
        Executed when the mouse enter the widget.
        :type event: QEvent
        """
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """
        Executed when the mouse leave the widget.
        :type event: QEvent
        """
        self.unsetCursor()


class VersionNumber(QtCore.QVersionNumber):
    """
    Extends QtCore.QVersionNumber to provide support for SemVer version numbers.
    """
    RE_SEMVER = re.compile(r'''
        ^(?P<major>0|[1-9]\d*)
        \.(?P<minor>0|[1-9]\d*)
        \.(?P<patch>0|[1-9]\d*)
        (?:-(?P<prerelease>
            (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
            (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
        ))?
        (?:\+(?P<build>
            [0-9a-zA-Z-]+
            (?:\.[0-9a-zA-Z-]+)*
        ))?
        $
    ''', re.VERBOSE)

    def __init__(self, major=None, minor=0, patch=0, prerelease=None, build=None):
        """
        Initializes the VersionNumber.
        :type major: int
        :type minor: int
        :type patch: int
        :type prerelease: str
        :type build: str
        """
        if major is not None:
            # CONSTRUCT EXPLICIT VERSION
            super().__init__(int(major), minor, patch)
        else:
            # CONSTRUCT A NULL VERSION NUMBER
            super().__init__()
        self._prerelease = prerelease if prerelease is None else str(prerelease)
        self._build = build if build is None else str(build)

    #############################################
    #   INTERFACE
    #################################

    def patchVersion(self):
        """
        Returns the patch number for this version (alias for microVersion()).
        :rtype: int
        """
        return self.microVersion()

    def build(self):
        """
        Returns the build number for this version as a string.
        :rtype: str
        """
        return self._build

    def prerelease(self):
        """
        Returns the prerelease identifier for this version as a string.
        :rtype str:
        """
        return self._prerelease

    @classmethod
    def compare(cls, v1, v2):
        """
        Compares v1 with v2 and returns -1, 0 or +1 if v1 is, respectively,
        less than, equal or greater than v2.
        :type v1: VersionNumber
        :type v2: VersionNumber
        :rtype: int
        """
        value = super().compare(v1.normalized(), v2.normalized())
        if value != 0:
            return value
        # COMPARE PRERELEASE IDENTIFIERS
        rc1 = v1.prerelease()
        rc2 = v2.prerelease()
        collator = Collator(QtCore.QLocale('en_US'))
        collator.setNumericMode(True)
        rccmp = collator.compare(v1.prerelease(), v2.prerelease())
        if not rccmp:
            return 0
        elif not rc1:
            return 1
        elif not rc2:
            return -1
        return rccmp

    @classmethod
    def fromString(cls, versionStr):
        """
        Constructs a VersionNumber from a formatted string.
        Differently from QtCore.QVersionNumber implementation, this method
        does not return the suffix index after the numerical segments.
        :type versionStr: str
        :rtype: VersionNumber
        """
        match = cls.RE_SEMVER.match(versionStr)
        if not match:
            return VersionNumber()
        groups = match.groupdict()
        major = int(groups['major'])
        minor = int(groups['minor'])
        patch = int(groups['patch'])
        return VersionNumber(major, minor, patch, groups['prerelease'], groups['build'])

    def toString(self):
        """
        Returns a string representation of this VersionNumber.
        :rtype: str
        """
        return '{0}{1}{2}'.format(
            '{0}.{1}.{2}'.format(self.majorVersion(), self.minorVersion(), self.patchVersion()),
            '-{}'.format(self.prerelease()) if self.prerelease() else '',
            '+{}'.format(self.build()) if self.build() else ''
        ) if not self.isNull() else ''

    def __eq__(self, other):
        """
        Returns `True` if this version is equal to the other version.
        :type other: VersionNumber
        :rtype: bool
        """
        return VersionNumber.compare(self, other) == 0

    def __ge__(self, other):
        """
        Returns `True` if this version is greater than or equal to the other version.
        :type other: VersionNumber
        :rtype: bool
        """
        return VersionNumber.compare(self, other) >= 0

    def __gt__(self, other):
        """
        Returns `True` if this version is strictly greater than the other version.
        :type other: VersionNumber
        :rtype: bool
        """
        return VersionNumber.compare(self, other) > 0

    def __le__(self, other):
        """
        Returns `True` if this version is less than or equal to the other version.
        :type other: VersionNumber
        :rtype: bool
        """
        return VersionNumber.compare(self, other) <= 0

    def __lt__(self, other):
        """
        Returns `True` if this version is strictly less than the other version.
        :type other: VersionNumber
        :rtype: bool
        """
        return VersionNumber.compare(self, other) < 0

    def __ne__(self, other):
        """
        Returns `True` if this version is *not* equal to the other version.
        :type other: VersionNumber
        :rtype: bool
        """
        return VersionNumber.compare(self, other) != 0

    def __repr__(self):
        """
        Returns a string representation of this VersionNumber.
        :rtype: str
        """
        return '{0}({1})'.format(self.__class__.__name__, self.toString())

    def __str__(self):
        """
        Returns a string representation of this VersionNumber.
        :rtype: str
        """
        return self.toString()
