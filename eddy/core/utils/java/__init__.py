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


import os
import jpype

from PyQt5.QtCore import QObject, pyqtSlot

from memoized_property import memoized_property
from verlib import NormalizedVersion

from eddy import expandPath
from eddy.core.datatypes import Platform
from eddy.core.decorators import memoized
from eddy.core.regex import RE_JAVA_VERSION


class JVM(QObject):
    """
    This class is used to startup and shutdown the Java Virtual Machine.
    It serves as a bridge between PyQt5 and JPype so we can used signals to perform startup and shutdown.
    """
    def __init__(self, parent=None):
        """
        Initialize the Java Virtual Machine.
        :type parent: QObject
        :raise JVMNotFoundException: if no JVM could be found.
        :raise JVMNotSupportedException: if an unsupported JVM is found.
        """
        super().__init__(parent)
        self.path = self.find()

    @memoized
    def find(self):
        """
        Search a valid JVM in the filesystem.
        Will attempt to search inside Eddy's path at first: if no JVM is found it will search system wide.
        :raise JVMNotFoundException: if no JVM could be found.
        :raise JVMNotSupportedException: if an unsupported JVM is found.
        :rtype: str
        """
        platform = Platform.identify()
        if platform is Platform.Windows:
            from eddy.core.utils.java.windows import WindowsJVMFinder_
            finder = WindowsJVMFinder_()
        elif platform is Platform.Darwin:
            from eddy.core.utils.java.darwin import DarwinJVMFinder_
            finder = DarwinJVMFinder_()
        else:
            from eddy.core.utils.java.linux import LinuxJVMFinder_
            finder = LinuxJVMFinder_()
        return finder.get_jvm_path()

    @memoized_property
    def version(self):
        """
        Returns the version of the currently running JVM.
        :raise EnvironmentError: if the JVM is not running.
        :rtype: NormalizedVersion
        """
        if not self.isRunning():
            raise EnvironmentError('JVM is not running')
        System = jpype.JClass("java.lang.System")
        match = RE_JAVA_VERSION.match(System.getProperty("java.version"))
        return NormalizedVersion.from_parts((match.group('major'), match.group('minor'), match.group('patch')))

    @staticmethod
    def isRunning():
        """
        Tells whether the JVM is running.
        :rtype: bool
        """
        return jpype.isJVMStarted()

    isStarted = isRunning

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def startup(self):
        """
        Start the Java Virtual Machine.
        """
        if not self.isRunning():

            # Include all the JARs in the classpath.
            classpath = []
            resources = expandPath('@resources/')
            for name in os.listdir(resources):
                path = os.path.join(resources, name)
                if os.path.isfile(path):
                    classpath.append(path)

            # Start the Java Virtual Machine.
            jpype.startJVM(self.path, '-Djava.class.path={}'.format(os.pathsep.join(classpath)),
                                      '-Dfile.encoding=UTF8',
                                      '-ea', '-Xmx512m')

    @pyqtSlot()
    def shutdown(self):
        """
        Shutdown the Java Virtual Machine.
        """
        if self.isRunning():
            jpype.shutdownJVM()