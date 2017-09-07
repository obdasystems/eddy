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

#This file is written by ASHWIN RAVISHANKAR


import inspect
import os
import re

from abc import ABCMeta
from configparser import ConfigParser, NoOptionError
from importlib.machinery import SourceFileLoader
from zipfile import ZipFile
from zipimport import zipimporter
from verlib import NormalizedVersion

from PyQt5 import QtCore

from eddy.core.common import HasActionSystem, HasMenuSystem, HasWidgetSystem
from eddy.core.datatypes.system import File
from eddy.core.functions.misc import first, lstrip, rstrip
from eddy.core.functions.fsystem import fcopy, fexists, fread, fremove
from eddy.core.functions.fsystem import isdir, mkdir, rmdir
from eddy.core.functions.path import expandPath, isSubPath
from eddy.core.output import getLogger


LOGGER = getLogger()


class AbstractReasoner(QtCore.QObject, HasActionSystem, HasMenuSystem, HasWidgetSystem):
    """
    Extension QtCore.QObject which implements a reasoner.
    """
    __metaclass__ = ABCMeta

    def __init__(self, spec, session):
        """
        Initialize the reasoner.
        :type spec: ReasonerSpec
        :type session: session
        """
        super().__init__(session)
        self.spec = spec

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the reference to the active project.
        :rtype: Project
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for AbstractReasoner.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def author(self):
        """
        Returns the author of the reasoner.
        :rtype: str
        """
        return self.spec.get('reasoner', 'author', fallback='<unknown>')

    def contact(self):
        """
        Returns the contact address for this reasoner.
        :rtype: str
        """
        return self.spec.get('reasoner', 'contact', fallback='<unknown>')

    def id(self):
        """
        Returns the reasoner identifier.
        :rtype: str
        """
        return self.spec.get('reasoner', 'id')

    def isBuiltIn(self):
        """
        Returns True if this reasoner is a built-in one, False otherwise.
        :rtype: bool
        """
        return isSubPath('@reasoners/', inspect.getfile(self.__class__))

    def name(self):
        """
        Returns the name of the reasoner.
        :rtype: str
        """
        return self.spec.get('reasoner', 'name')

    def objectName(self):
        """
        Returns the system name of the reasoner.
        :rtype: str
        """
        return self.spec.get('reasoner', 'id')

    def path(self):
        """
        Returns the path to the the reasoner (either a directory of a ZIP file).
        :rtype: str
        """
        path = lstrip(inspect.getfile(self.__class__), expandPath('@reasoners/'), expandPath('@home/reasoners/'))
        home = first(filter(None, path.split(os.path.sep)))
        root = expandPath('@reasoners/' if self.isBuiltIn() else '@home/reasoners/')
        return os.path.join(root, home)

    @classmethod
    def subclasses(cls):
        """
        Returns the list of subclasses subclassing this very class.
        :rtype: list
        """
        return cls.__subclasses__() + [c for i in cls.__subclasses__() for c in i.subclasses()]

    def version(self):
        """
        Returns the version of the reasoner.
        :rtype: NormalizedVersion
        """
        return NormalizedVersion(self.spec.get('reasoner', 'version'))

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the reasoner is going to be destroyed.
        """
        pass

    def start(self):
        """
        Executed whenever the reasoner is to be started, after all the reasoners have been loaded.
        NOTE: this method is executed before the project is loaded in the main session, so any
        attempt to refer to self.project from within this method will raise an exception.
        To setup project specific signals/slots, it's possible to make use of the sgnReady
        signal emitted by the main session when the startup sequence completes.
        """
        pass

    #############################################
    #   LOGGING UTILITIES
    #################################

    def critical(self, message, *args, **kwargs):
        """
        Log a 'CRITICAL' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.critical('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        """
        Log a 'DEBUG' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.debug('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """
        Log a 'ERROR' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.error('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def info(self, message, *args, **kwargs):
        """
        Log a 'INFO' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.info('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """
        Log a 'WARNING' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.warning('{0}: {1}'.format(self.name(), message), *args, **kwargs)


class ReasonerSpec(ConfigParser):
    """
    Reasoner .spec configuration file instance.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the reasoner .spec configuration.
        """
        super().__init__(*args, **kwargs)

    #############################################
    #   INTERFACE
    #################################

    def getList(self, section, option):
        """
        Get the content of the given section/option combination returning it as a list.
        :type section: str
        :type option: str
        :rtype: list
        """
        return list(filter(None, re.split("[,\s\-]+", self.get(section, option))))

    def getPath(self, section, option):
        """
        Get the content of the given section/option performing path expansion.
        :type section: str
        :type option: str
        :rtype: str
        """
        return expandPath(self.get(section, option))


class ReasonerManager(QtCore.QObject):
    """
    Reasoner manager class which takes case of performing some specific operations on reasoners.
    """
    info = []

    def __init__(self, session):
        """
        Initialize the reasoner manager.
        :type session: Session
        """
        super().__init__(session)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for ReasonerManager.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def clear(self):
        """
        Remove all the reasoners from the active Session.
        """
        self.session.clearReasoners()

    def create(self, clazz, spec):
        """
        Create an instance of the given reasoner.
        :type clazz: class
        :type spec: ReasonerSpec
        :rtype: AbstractReasoner
        """
        return clazz(spec, self.session)

    def dispose(self, reasoner):
        """
        Dispose the given reasoner.
        Will return True if the reasoner has been disposed successfully, False otherwise.
        :type reasoner: AbstractReasoner
        :rtype: bool
        """
        LOGGER.info('Disposing reasoner: %s v%s', reasoner.name(), reasoner.version())
        try:
            reasoner.dispose()
        except Exception:
            LOGGER.exception('An error occurred while disposing reasoner: %s v%s', reasoner.name(), reasoner.version())
            return False
        else:
            self.session.sgnReasonerDisposed.emit(reasoner.id())
            return True

    @classmethod
    def find_class(cls, mod, name):
        """
        Find and returns the reference to the reasoner class in the given module.
        :type mod: module
        :type name: str
        :rtype: class
        """
        return getattr(mod, '%sReasoner' % ''.join(i.title() for i in list(filter(None, re.split("[_\-]+", name)))))

    @classmethod
    def import_reasoner_from_directory(cls, directory):
        """
        Import a reasoner from the given directory:
        * Lookup for the reasoner .spec configuration file.
        * Search for the module where the reasoner is implemented.
        * Search for the class implementing the reasoner.
        * Import the reasoner module.
        :type directory: str
        :rtype: tuple
        """
        if isdir(directory):
            reasoner_spec_path = os.path.join(directory, 'reasoner.spec')
            if fexists(reasoner_spec_path):
                try:
                    #LOGGER.debug('Found reasoner .spec: %s', reasoner_spec_path)
                    reasoner_spec = ReasonerManager.spec(fread(reasoner_spec_path))
                    reasoner_name = reasoner_spec.get('reasoner', 'id')
                    for extension in ('.pyc', '.pyo', '.py'):
                        reasoner_path = os.path.join(directory, '%s%s' % (reasoner_name, extension))
                        if fexists(reasoner_path):
                            #LOGGER.debug('Found reasoner module: %s', reasoner_path)
                            reasoner_module = SourceFileLoader(reasoner_name, reasoner_path).load_module()
                            reasoner_class = ReasonerManager.find_class(reasoner_module, reasoner_name)
                            return reasoner_spec, reasoner_class
                    else:
                        raise ReasonerError('missing reasoner module: %s.py(c|o)' % os.path.join(directory, reasoner_name))
                except Exception as e:
                    LOGGER.exception('Failed to import reasoner: %s', e)

    @classmethod
    def import_reasoner_from_zip(cls, archive):
        """
        Import a reasoner from the given zip archive:
        * Lookup for the reasoner .spec configuration file.
        * Search for the module where the reasoner is implemented.
        * Search for the class implementing the reasoner.
        * Import the reasoner module.
        :type archive: str
        :rtype: tuple
        """
        if fexists(archive) and File.forPath(archive) is File.Zip:
            zf = ZipFile(archive)
            zf_name_list = zf.namelist()
            for file_or_directory in zf_name_list:
                if file_or_directory.endswith('reasoner.spec'):
                    try:
                        #LOGGER.debug('Found reasoner .spec: %s', os.path.join(archive, file_or_directory))
                        reasoner_spec_content = zf.read(file_or_directory).decode('utf8')
                        reasoner_spec = ReasonerManager.spec(reasoner_spec_content)
                        reasoner_name = reasoner_spec.get('reasoner', 'id')
                        reasoner_zip_base_path = rstrip(file_or_directory, 'reasoner.spec')
                        reasoner_abs_base_path = os.path.join(archive, reasoner_zip_base_path)
                        reasoner_zip_module_base_path = os.path.join(reasoner_zip_base_path, reasoner_name)
                        reasoner_abs_module_base_path = os.path.join(archive, reasoner_zip_module_base_path)
                        for extension in ('.pyc', '.pyo', '.py'):
                            reasoner_zip_module_path = '%s%s' % (reasoner_zip_module_base_path, extension)
                            if reasoner_zip_module_path in zf_name_list:
                                #LOGGER.debug('Found reasoner module: %s', os.path.join(archive, reasoner_zip_module_path))
                                reasoner_module = zipimporter(reasoner_abs_base_path).load_module(reasoner_name)
                                reasoner_class = ReasonerManager.find_class(reasoner_module, reasoner_name)
                                return reasoner_spec, reasoner_class
                        else:
                            raise ReasonerError('missing reasoner module: %s.py(c|o)' % reasoner_abs_module_base_path)
                    except Exception as e:
                        LOGGER.exception('Failed to import reasoner: %s', e)

    def init(self):
        """
        Initialize previously looked up reasoners returning the list of successfully initialized reasoners.
        :rtype: list
        """
        if not ReasonerManager.info:
            LOGGER.info('No reasoner to be initialized')
            return []

        LOGGER.info('Loading %s reasoner(s):', len(ReasonerManager.info))
        for entry in ReasonerManager.info:
            reasoner_author = entry[0].get('reasoner', 'author', fallback='<unknown>')
            reasoner_contact = entry[0].get('reasoner', 'contact', fallback='<unknown>')
            reasoner_name = entry[0].get('reasoner', 'name')
            reasoner_version = entry[0].get('reasoner', 'version')
            LOGGER.info('* %s v%s (%s - %s)', reasoner_name, reasoner_version, reasoner_author, reasoner_contact)

        reasonersList = []
        reasonersLoadedSet = set()
        for entry in ReasonerManager.info:
            reasoner_id = entry[0].get('reasoner', 'id')
            reasoner_name = entry[0].get('reasoner', 'name')
            reasoner_version = entry[0].get('reasoner', 'version')
            if reasoner_id not in reasonersLoadedSet:
                try:
                    LOGGER.info('Loading reasoner: %s v%s', reasoner_name, reasoner_version)
                    reasoner = self.create(entry[1], entry[0])
                except Exception:
                    LOGGER.exception('Failed to load reasoner: %s v%s', reasoner_name, reasoner_version)
                else:
                    reasonersList.append(reasoner)
                    reasonersLoadedSet.add(reasoner.id())
            else:
                LOGGER.warning('Loading reasoner: %s v%s -> skipped: reasoner already loaded', reasoner_name, reasoner_version)

        started = []
        for reasoner in reasonersList:
            if self.start(reasoner):
                started.append(reasoner)

        return started

    def install(self, archive):
        """
        Install the given reasoner archive.
        During the installation process we'll check for a correct reasoner structure,
        i.e. for the .spec file and the reasoner module to be available. We won't check if
        the reasoner actually runs since this will be handle by the application statt sequence.
        :type archive: str
        :rtype: ReasonerSpec
        """
        try:

            ## CHECK FOR CORRECT REASONER ARCHIVE
            if not fexists(archive):
                raise ReasonerError('file not found: %s' % archive)
            if not File.forPath(archive) is File.Zip:
                raise ReasonerError('%s is not a valid reasoner' % archive)

            ## LOOKUP THE SPEC FILE
            zf = ZipFile(archive)
            zf_name_list = zf.namelist()
            for file_or_directory in zf_name_list:
                if file_or_directory.endswith('reasoner.spec'):
                    LOGGER.debug('Found reasoner .spec: %s', os.path.join(archive, file_or_directory))
                    reasoner_spec_content = zf.read(file_or_directory).decode('utf8')
                    reasoner_spec = self.spec(reasoner_spec_content)
                    break
            else:
                raise ReasonerError('missing reasoner.spec in %s' % archive)

            ## LOOKUP THE REASONER MODULE
            reasoner_name = reasoner_spec.get('reasoner', 'id')
            reasoner_zip_base_path = rstrip(file_or_directory, 'reasoner.spec')
            reasoner_zip_module_base_path = os.path.join(reasoner_zip_base_path, reasoner_name)
            for extension in ('.pyc', '.pyo', '.py'):
                reasoner_zip_module_path = '%s%s' % (reasoner_zip_module_base_path, extension)
                if reasoner_zip_module_path in zf_name_list:
                    LOGGER.debug('Found reasoner module: %s', os.path.join(archive, reasoner_zip_module_path))
                    break
            else:
                raise ReasonerError('missing reasoner module: %s.py(c|o) in %s' % (reasoner_zip_module_base_path, archive))

            # CHECK FOR THE REASONER TO BE ALREADY RUNNING
            reasoner_id = reasoner_spec.get('reasoner', 'id')
            reasoner_name = reasoner_spec.get('reasoner', 'name')
            if self.session.reasoner(reasoner_spec.get('reasoner', 'id')):
                raise ReasonerError('reasoner %s (id: %s) is already installed' % (reasoner_name, reasoner_id))

            # CHECK FOR THE REASONER NAMESPACE TO BE UNIQUE
            reasoner_module_base_path = rstrip(first(filter(None, reasoner_zip_module_path.split(os.path.sep))), File.Zip.extension)
            for path in (expandPath('@reasoners/'), expandPath('@home/reasoners/')):
                for entry in os.listdir(path):
                    if reasoner_module_base_path == rstrip(entry, File.Zip.extension):
                        raise ReasonerError('reasoner %s (id: %s) is already installed' % (reasoner_name, reasoner_id))

            # COPY THE REASONER
            mkdir('@home/reasoners/')
            fcopy(archive, '@home/reasoners/')

        except Exception as e:
            LOGGER.error('Failed to install reasoner: %s', e, exc_info=not isinstance(e, ReasonerError))
            raise e
        else:
            return reasoner_spec

    @classmethod
    def scan(cls, *args):
        """
        Scan the given paths looking for reasoners.
        """
        info = []
        for base in map(expandPath, args):
            if isdir(base):
                LOGGER.info('Looking for reasoners in %s', base)
                for file_or_directory in os.listdir(base):
                    file_or_directory_path = os.path.join(base, file_or_directory)
                    info.append(ReasonerManager.import_reasoner_from_directory(file_or_directory_path))
                    info.append(ReasonerManager.import_reasoner_from_zip(file_or_directory_path))
        ReasonerManager.info = list(filter(None, info))

    @classmethod
    def spec(cls, content):
        """
        Parse and validate a reasoner configuration file (.spec) content.
        :type content: str
        :rtype: ReasonerSpec
        """
        spec = ReasonerSpec()
        spec.read_string(content)
        for key in ('id', 'name', 'version'):
            if not spec.has_option('reasoner', key):
                raise NoOptionError('reasoner', key)
        return spec

    def start(self, reasoner):
        """
        Start the given reasoner.
        Will return True if the reasoner has been started successfully, False otherwise.
        :type reasoner: AbstractReasoner
        :rtype: bool
        """
        LOGGER.info('Starting reasoner: %s v%s', reasoner.name(), reasoner.version())
        try:
            reasoner.start()
        except Exception:
            LOGGER.exception('An error occurred while starting reasoner: %s v%s', reasoner.name(), reasoner.version())
            return False
        else:
            self.session.sgnReasonerStarted.emit(reasoner.id())
            return True

    def uninstall(self, reasoner):
        """
        Uninstall the given reasoner.
        :type reasoner: AbstractReasoner
        """
        if self.dispose(reasoner):
            self.session.removeReasoner(reasoner)
            path = reasoner.path()
            if isdir(path):
                rmdir(path)
            elif fexists(path):
                fremove(path)


class ReasonerError(RuntimeError):
    """
    Raised whenever a given reasoner doesn't have a correct reasoner structure.
    """
    pass



