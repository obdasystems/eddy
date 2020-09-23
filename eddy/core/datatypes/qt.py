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
    Extends QtCore.QVersionNumber to provide version numbers compatible with
    a strict subset of PEP 440.
    """
    RE_VERSION = re.compile(r'''
        ^\s*
        v?
        (?:
            (?:(?P<epoch>[0-9]+)!)?                           # epoch
            (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
            (?P<pre>                                          # pre-release
                [-_\.]?
                (?P<pre_l>(a|b|rc))
                [-_\.]?
                (?P<pre_n>[0-9]+)?
            )?
            (?P<post>                                         # post release
                [-_\.]?
                (?P<post_l>post)
                [-_\.]?
                (?P<post_n>[0-9]+)?
            )?
            (?P<dev>                                          # dev release
                [-_\.]?
                (?P<dev_l>dev)
                [-_\.]?
                (?P<dev_n>[0-9]+)?
            )?
        )
        (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
        \s*$
    ''', re.VERBOSE)

    def __init__(self, version=None):
        """
        Initializes the VersionNumber.
        :type version: str
        """
        # Validate the version and parse it into pieces
        match = self.RE_VERSION.search(version)
        if not match:
            super().__init__()

        else:
            # Store the parsed out pieces of the version
            self._epoch = int(match.group('epoch')) if match.group('epoch') else 0
            self._release = tuple(int(i) for i in match.group('release').split('.'))
            self._pre = (match.group('pre_l'),
                         match.group('pre_n')) if match.group('pre_l') else None
            self._post = (match.group('post_l'),
                          match.group('post_n')) if match.group('post_l') else None
            self._dev = (match.group('dev_l'),
                         match.group('dev_n')) if match.group('dev_l') else None
            self._local = match.group('local')

            super().__init__(self._release)

    #############################################
    #   INTERFACE
    #################################

    def patchVersion(self):
        """
        Returns the patch number for this version (alias for microVersion()).
        :rtype: int
        """
        return self.microVersion()

    def epoch(self):
        """
        Returns the epoch of this version number.
        :rtype: int
        """
        return self._epoch

    def prerelease(self):
        """
        Returns the pre-release identifier for this version as a string
        or `None` if this is not a pre-release.
        :rtype: str
        """
        return ''.join(self._pre) if self._pre else None

    def post(self):
        """
        Returns the post-release identifier for this version as a string
        or `None` if this is not a post-release.
        :rtype: str
        """
        return ''.join(self._post) if self._post else None

    def dev(self):
        """
        Returns the development release identifier for this version as a string
        or `None` if this is not a development release.
        :rtype: str
        """
        return ''.join(self._dev) if self._dev else None

    def local(self):
        """
        Returns the local release identifier for this version as a string
        or `None` if this is not a local release.
        :rtype: str
        """
        return self._local

    def isPrerelease(self):
        """
        Returns `True` if this version is a pre-release, `False` otherwise.
        :rtype: bool
        """
        return self._pre is not None

    def isPost(self):
        """
        Returns `True` if this version is a post-release, `False` otherwise.
        :rtype: bool
        """
        return self._post is not None

    def isDev(self):
        """
        Returns `True` if this version is a development release, `False` otherwise.
        :rtype: bool
        """
        return self._dev is not None

    def isLocal(self):
        """
        Returns `True` if this version is a local release, `False` otherwise.
        :rtype: bool
        """
        return self._local is not None

    @classmethod
    def compare(cls, v1, v2):
        """
        Compares v1 with v2 and returns -1, 0 or +1 if v1 is, respectively,
        less than, equal or greater than v2.
        :type v1: VersionNumber
        :type v2: VersionNumber
        :rtype: int
        """
        # COMPARE EPOCH
        if v1.epoch() != v2.epoch():
            return max(-1, min(v1.epoch() - v2.epoch(), 1))
        # COMPARE RELEASE
        value = super().compare(v1.normalized(), v2.normalized())
        if value != 0:
            return value
        # COMPARE (PRE|POST|DEV|LOCAL)RELEASE IDENTIFIERS
        # Implementation is mostly taken from the packaging _cmpkey function.
        inf = 1    # Sentinel value to represent infinity
        ninf = -1  # Sentinel value to represent negative infinity
        pre1 = v1.prerelease()
        pre2 = v2.prerelease()
        post1 = v1.post()
        post2 = v2.post()
        dev1 = v1.dev()
        dev2 = v2.dev()
        local1 = v1.local()
        local2 = v2.local()

        # This is needed to sort versions like 1.0.dev1 before 1.0a0
        # but only if there is no pre or post segments.
        if not pre1 and not post1 and dev1:
            pre1 = ninf
        elif not pre1:
            pre1 = inf
        if not pre2 and not post2 and dev2:
            pre2 = ninf
        elif not pre2:
            pre2 = inf

        # No dev segment is greater than any dev segment
        if not dev1:
            dev1 = inf
        if not dev2:
            dev2 = inf

        # No local segment is smaller than any local segment
        if not local1:
            local1 = ninf
        if not local2:
            local2 = ninf

        collator = Collator(QtCore.QLocale('en_US'))
        collator.setNumericMode(True)
        t1 = (pre1, post1, dev1, local1)
        t2 = (pre2, post2, dev2, local2)
        for i in range(len(t1)):
            if t1[i] != t2[i]:
                if isinstance(t1[i], int) and isinstance(t2[i], int):
                    return max(-1, min(t1[i] - t2[i], 1))
                elif isinstance(t1[i], int):
                    return 1 if t1[i] == inf else -1
                elif isinstance(t2[i], int):
                    return -1 if t2[i] == inf else 1
                else:
                    return collator.compare(t1[i], t2[i])
        return 0

    @classmethod
    def fromString(cls, versionStr):
        """
        Constructs a VersionNumber from a formatted string.
        Differently from QtCore.QVersionNumber implementation, this method
        does not return the suffix index after the numerical segments.
        :type versionStr: str
        :rtype: VersionNumber
        """
        return VersionNumber(versionStr)

    def toString(self):
        """
        Returns a string representation of this VersionNumber.
        :rtype: str
        """
        return str(self)

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
        return '<{0}({1})>'.format(self.__class__.__name__, repr(self.toString()))

    def __str__(self):
        """
        Returns a string representation of this VersionNumber.
        :rtype: str
        """
        return '{epoch}{release}{pre}{post}{dev}{local}'.format(
            epoch='{0}!'.format(self._epoch) if self._epoch != 0 else '',
            release='.'.join(str(x) for x in self._release),
            pre=''.join(self.prerelease()) if self.prerelease() else '',
            post='.{0}'.format(self.post()) if self.post() else '',
            dev='.{0}'.format(self.dev()) if self.dev() else '',
            local='+{0}'.format(self.local()) if self.local() else ''
        )


class SemVerVersionNumber(QtCore.QVersionNumber):
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
        Initializes the SemVerVersionNumber.
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
        :rtype: str
        """
        return self._prerelease

    def isPrerelease(self):
        """
        Return `True` if this version is a prerelease, `False` otherwise.
        :rtype: bool
        """
        return self._prerelease is not None

    @classmethod
    def compare(cls, v1, v2):
        """
        Compares v1 with v2 and returns -1, 0 or +1 if v1 is, respectively,
        less than, equal or greater than v2.
        :type v1: SemVerVersionNumber
        :type v2: SemVerVersionNumber
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
        Constructs a SemVerVersionNumber from a formatted string.
        Differently from QtCore.QVersionNumber implementation, this method
        does not return the suffix index after the numerical segments.
        :type versionStr: str
        :rtype: SemVerVersionNumber
        """
        match = cls.RE_SEMVER.match(versionStr)
        if not match:
            return SemVerVersionNumber()
        groups = match.groupdict()
        major = int(groups['major'])
        minor = int(groups['minor'])
        patch = int(groups['patch'])
        return SemVerVersionNumber(major, minor, patch, groups['prerelease'], groups['build'])

    def toString(self):
        """
        Returns a string representation of this SemVerVersionNumber.
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
        :type other: SemVerVersionNumber
        :rtype: bool
        """
        return SemVerVersionNumber.compare(self, other) == 0

    def __ge__(self, other):
        """
        Returns `True` if this version is greater than or equal to the other version.
        :type other: SemVerVersionNumber
        :rtype: bool
        """
        return SemVerVersionNumber.compare(self, other) >= 0

    def __gt__(self, other):
        """
        Returns `True` if this version is strictly greater than the other version.
        :type other: SemVerVersionNumber
        :rtype: bool
        """
        return SemVerVersionNumber.compare(self, other) > 0

    def __le__(self, other):
        """
        Returns `True` if this version is less than or equal to the other version.
        :type other: SemVerVersionNumber
        :rtype: bool
        """
        return SemVerVersionNumber.compare(self, other) <= 0

    def __lt__(self, other):
        """
        Returns `True` if this version is strictly less than the other version.
        :type other: SemVerVersionNumber
        :rtype: bool
        """
        return SemVerVersionNumber.compare(self, other) < 0

    def __ne__(self, other):
        """
        Returns `True` if this version is *not* equal to the other version.
        :type other: SemVerVersionNumber
        :rtype: bool
        """
        return SemVerVersionNumber.compare(self, other) != 0

    def __repr__(self):
        """
        Returns a string representation of this SemVerVersionNumber.
        :rtype: str
        """
        return '<{0}({1})>'.format(self.__class__.__name__, repr(self.toString()))

    def __str__(self):
        """
        Returns a string representation of this SemVerVersionNumber.
        :rtype: str
        """
        return self.toString()
