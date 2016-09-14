# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


import logging
import jnius_config
import os
import sys

from eddy.core.functions.path import expandPath
from eddy.core.functions.fsystem import cpdir, mkdir, rmdir

LINUX = sys.platform.startswith('linux')
MACOS = sys.platform.startswith('darwin')
WIN32 = sys.platform.startswith('win32')

#############################################
# BEGIN JAVA VIRTUAL MACHINE SETUP
#################################

if os.path.isdir(expandPath('@resources/java/')):
    os.environ['JAVA_HOME'] = expandPath('@resources/java/')

if WIN32:
    path = os.getenv('Path', '')
    path = path.split(os.pathsep)
    path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'bin', 'client'))
    os.environ['Path'] = os.pathsep.join(path)

classpath = []
resources = expandPath('@resources/lib/')
for name in os.listdir(resources):
    path = os.path.join(resources, name)
    if os.path.isfile(path):
        classpath.append(path)

jnius_config.add_options('-ea', '-Xmx512m')
jnius_config.set_classpath(*classpath)

#############################################
# END JAVA VIRTUAL MACHINE SETUP
#################################

from argparse import ArgumentParser
from unittest import TestCase
from unittest.util import safe_repr

from PyQt5 import QtTest

from eddy.core.application import Eddy
# noinspection PyUnresolvedReferences
from eddy.ui import images_rc


class EddyTestCase(TestCase):
    """
    Base class for all Eddy test cases.
    """
    def setUp(self):
        """
        Initialize test case environment.
        """
        # COPY TEST PROJECT OVER
        rmdir('@tests/.test_project/')
        mkdir('@tests/.test_project/')
        cpdir('@resources/test_project/', '@tests/.test_project/test_project')
        # CREATE AN INSTANCE OF EDDY
        arguments = ['--nosplash', '--tests', '--open', '@tests/.test_project/test_project']
        parser = ArgumentParser()
        parser.add_argument('--nosplash', dest='nosplash', action='store_true')
        parser.add_argument('--tests', dest='tests', action='store_true')
        parser.add_argument('--open', dest='open', default=None)
        options, _ = parser.parse_known_args(args=arguments)
        self.eddy = Eddy(options, arguments)
        self.eddy.configure(options)
        self.eddy.start(options)
        # WAIT FOR THE SESSION TO BE COMPLETELY INITIALIZED
        QtTest.QTest.qWaitForWindowActive(self.eddy.session)
        # CREATE SOME USEFUL SHORTCUTS
        self.session = self.eddy.session
        self.project = self.eddy.session.project
        # GIVE FOCUS TO THE TEST DIAGRAM
        self.session.sgnDiagramFocus.emit(self.project.diagram(expandPath('@tests/.test_project/test_project/diagram.graphol')))

    def tearDown(self):
        """
        Perform operation on test end.
        """
        # SHUTDOWN EDDY
        self.eddy.quit()
        # REMOVE TEST DIRECTORY
        rmdir('@tests/.test_project/')

    #############################################
    #   CUSTOM ASSERTIONS
    #################################

    def assertAll(self, iterable, msg=None):
        """Check for all the value in the given iterable to be True"""
        if not all(iterable):
            standardMsg = 'found false value in {0}'.format(safe_repr(iterable))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertAny(self, iterable, msg=None):
        """Check for at least a True value in the given iterable"""
        if not any(iterable):
            standardMsg = 'true value not found in {0}'.format(safe_repr(iterable))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertDictHasKey(self, key, container, msg=None):
        """Check for a given key to be in the given dictionary."""
        if key not in container.keys():
            standardMsg = '{0} not found in {1}'.format(safe_repr(key), safe_repr(container))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertDictHasValue(self, value, container, msg=None):
        """Check for a given value to be in the given dictionary."""
        if value not in container.value():
            standardMsg = '{0} not found in {1}'.format(safe_repr(value), safe_repr(container))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertEmpty(self, container, msg=None):
        """Assert for a given container to be empty."""
        if len(container) != 0:
            standardMsg = '{0} is not empty: found {1} elements'.format(safe_repr(container), len(container))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertLen(self, count, container, msg=None):
        """Check for a given container to have the specified length."""
        if len(container) != count:
            standardMsg = 'found {0} elements in {1}: expecting {2}'.format(len(container), safe_repr(container), count)
            self.fail(self._formatMessage(msg, standardMsg))

    def assertNotEmpty(self, container, msg=None):
        """Assert for a given container to be empty."""
        if len(container) == 0:
            standardMsg = '{0} unexpectedly empty: found {1} elements'.format(safe_repr(container), len(container))
            self.fail(self._formatMessage(msg, standardMsg))