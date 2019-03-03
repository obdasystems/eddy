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

import os
import platform
import sys
import threading

from eddy.core.functions.fsystem import cpdir, isdir, mkdir, rmdir, fexists
from eddy.core.functions.path import expandPath
from eddy.core.jvm import findJavaHome, addJVMClasspath, addJVMOptions

LINUX = sys.platform.startswith('linux')
MACOS = sys.platform.startswith('darwin')
WIN32 = sys.platform.startswith('win32')

#############################################
# BEGIN JAVA VIRTUAL MACHINE SETUP
#################################

os.environ['JAVA_HOME'] = findJavaHome()

if WIN32:
    path = os.getenv('PATH', '')
    path = path.split(os.pathsep)
    path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin'))
    if platform.architecture()[0] == '32bit':
        path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin', 'client'))
    else:
        path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin', 'server'))
    os.environ['PATH'] = os.pathsep.join(path)
resources = expandPath('@resources/lib/')
for name in os.listdir(resources):
    path = os.path.join(resources, name)
    if os.path.isfile(path):
        addJVMClasspath(path)
addJVMOptions('-ea', '-Xmx512m')

#############################################
# END JAVA VIRTUAL MACHINE SETUP
#################################

from argparse import ArgumentParser
from unittest import TestCase
from unittest.util import safe_repr

from PyQt5 import QtCore
from PyQt5 import QtTest

from eddy import APPNAME, ORGANIZATION
from eddy.core.application import Eddy
from eddy.core.output import getLogger
# noinspection PyUnresolvedReferences
from eddy.ui import fonts_rc
# noinspection PyUnresolvedReferences
from eddy.ui import images_rc


testcase_lock = threading.Lock()


class LoggingDisabled(object):
    """
    Context manager that temporarily disable logging.

    USAGE:
        with LoggingDisabled():
            # do stuff
    """
    DISABLED = False

    def __init__(self):
        self.nested = LoggingDisabled.DISABLED

    def __enter__(self):
        if not self.nested:
            Logger = getLogger()
            Logger.disabled = True
            LoggingDisabled.DISABLED = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.nested:
            Logger = getLogger()
            Logger.disabled = False
            LoggingDisabled.DISABLED = False


class EddyTestCase(TestCase):
    """
    Base class for all Eddy test cases.
    """
    #############################################
    #   HOOKS
    #################################

    def setUp(self):
        """
        Initialize test case environment.
        """
        # ACQUIRE LOCK AND FLUSH STREAMS
        testcase_lock.acquire()
        sys.stderr.flush()
        sys.stdout.flush()
        # MAKE SURE TO HAVE A CLEAN TEST ENVIRONMENT
        rmdir('@tests/.tests/')
        mkdir('@tests/.tests/')
        # MAKE SURE TO USE CORRECT SETTINGS
        QtCore.QSettings.setPath(QtCore.QSettings.NativeFormat, QtCore.QSettings.UserScope, expandPath('@tests/.tests/'))
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue('workspace/home', expandPath('@tests/.tests/'))
        settings.setValue('update/check_on_startup', False)
        settings.sync()
        # MAKE SURE THE WORKSPACE DIRECTORY EXISTS
        mkdir(expandPath('@tests/.tests/'))
        # INITIALIZED VARIABLES
        self.eddy = None
        self.project = None
        self.session = None

    def tearDown(self):
        """
        Perform operation on test end.
        """
        # SHUTDOWN EDDY
        self.eddy.quit()
        self.eddy.closeAllWindows()
        # REMOVE TEST DIRECTORY
        rmdir('@tests/.tests/')
        # RELEASE LOCK AND FLUSH STREAMS
        sys.stderr.flush()
        sys.stdout.flush()
        testcase_lock.release()

    #############################################
    #   INTERFACE
    #################################

    def init(self, project):
        """
        Create a new instance of Eddy loading the given project from the '@resources' directory.
        :type project: str
        """
        # COPY TEST PROJECT OVER
        cpdir('@tests/%s/' % project, '@tests/.tests/%s' % project)
        # CREATE AN INSTANCE OF EDDY
        arguments = [APPNAME, '--nosplash', '--tests', '--open', '@tests/.tests/%s' % project]
        parser = ArgumentParser()
        parser.add_argument('--nosplash', dest='nosplash', action='store_true')
        parser.add_argument('--tests', dest='tests', action='store_true')
        parser.add_argument('--open', dest='open', default=None)
        options, _ = parser.parse_known_args(args=arguments)
        with LoggingDisabled():
            self.eddy = Eddy(options, arguments)
            self.eddy.configure(options)
            self.eddy.start(options)
            # WAIT FOR THE SESSION TO BE COMPLETELY INITIALIZED
            QtTest.QTest.qWaitForWindowActive(self.eddy.sessions[0])
            # SET SHORTCUTS
            self.project = self.eddy.sessions[0].project
            self.session = self.eddy.sessions[0]

    #############################################
    #   CUSTOM ASSERTIONS
    #################################

    def assertAll(self, iterable, msg=None):
        """Check for all the value in the given iterable to be True"""
        if not all(iterable):
            standardMsg = 'found false value in %s' % safe_repr(iterable)
            self.fail(self._formatMessage(msg, standardMsg))

    def assertAllIn(self, iterable, container, msg=None):
        """Check for all the item in iterable to be in the given container"""
        for member in iterable:
            if member not in container:
                if member not in container:
                    standardMsg = '%s not found in %s' % (safe_repr(member), safe_repr(container))
                    self.fail(self._formatMessage(msg, standardMsg))

    def assertAny(self, iterable, msg=None):
        """Check for at least a True value in the given iterable"""
        if not any(iterable):
            standardMsg = 'true value not found in %s' % safe_repr(iterable)
            self.fail(self._formatMessage(msg, standardMsg))

    def assertAnyIn(self, iterable, container, msg=None):
        """Check for at least a one of the item in iterable to be in the given container"""
        for member in iterable:
            if member in container:
                break
        else:
            standardMsg = 'no item of %s found in %s' % (safe_repr(iterable), safe_repr(container))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertDictHasKey(self, key, container, msg=None):
        """Check for a given key to be in the given dictionary."""
        if key not in container.keys():
            standardMsg = '%s not found in %s' % (safe_repr(key), safe_repr(container))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertDictHasValue(self, value, container, msg=None):
        """Check for a given value to be in the given dictionary."""
        if value not in container.value():
            standardMsg = '%s not found in %s' % (safe_repr(value), safe_repr(container))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertEmpty(self, container, msg=None):
        """Assert for a given container to be empty."""
        if len(container) != 0:
            standardMsg = '%s is not empty: found %s elements' % (safe_repr(container), len(container))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertDirectoryExists(self, dirpath, msg=None):
        """Assert for the given path to represent a file"""
        if not isdir(dirpath):
            standardMsg = '%s is not a directory' % safe_repr(expandPath(dirpath))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertFileExists(self, filepath, msg=None):
        """Assert for the given path to represent a file"""
        if not fexists(filepath):
            standardMsg = '%s is not a file' % safe_repr(expandPath(filepath))
            self.fail(self._formatMessage(msg, standardMsg))

    def assertLen(self, count, container, msg=None):
        """Check for a given container to have the specified length."""
        if len(container) != count:
            standardMsg = 'found %s elements in %s: expecting %s' % (len(container), safe_repr(container), count)
            self.fail(self._formatMessage(msg, standardMsg))

    def assertNotEmpty(self, container, msg=None):
        """Assert for a given container to be empty."""
        if len(container) == 0:
            standardMsg = '%s unexpectedly empty: found %s elements' % (safe_repr(container), len(container))
            self.fail(self._formatMessage(msg, standardMsg))
