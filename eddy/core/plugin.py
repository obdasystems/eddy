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
from eddy.core.functions.misc import rstrip
from eddy.core.functions.fsystem import fcopy, fexists, fread, is_dir, mkdir
from eddy.core.functions.path import expandPath
from eddy.core.output import getLogger


LOGGER = getLogger(__name__)


class AbstractPlugin(QtCore.QObject, HasActionSystem, HasMenuSystem, HasWidgetSystem):
    """
    Extension QtCore.QObject which implements a plugin.
    """
    __metaclass__ = ABCMeta

    def __init__(self, spec, session):
        """
        Initialize the plugin.
        :type spec: PluginSpec
        :type session: session
        """
        super(AbstractPlugin, self).__init__(session)
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
        Returns the reference to the main session (alias for AbstractPlugin.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def author(self):
        """
        Returns the author of the plugin.
        :rtype: str
        """
        return self.spec.get('plugin', 'author', None)

    def contact(self):
        """
        Returns the contact address for this plugin.
        :rtype: str
        """
        return self.spec.get('plugin', 'contact', None)

    def id(self):
        """
        Returns the plugin identifier.
        :rtype: str
        """
        return self.spec.get('plugin', 'id')

    def name(self):
        """
        Returns the name of the plugin.
        :rtype: str
        """
        return self.spec.get('plugin', 'name')

    def objectName(self):
        """
        Returns the system name of the plugin.
        :rtype: str
        """
        return self.spec.get('plugin', 'id')

    @classmethod
    def subclasses(cls):
        """
        Returns the list of subclasses subclassing this very class.
        :rtype: list
        """
        return cls.__subclasses__() + [c for i in cls.__subclasses__() for c in i.subclasses()]

    def version(self):
        """
        Returns the version of the plugin.
        :rtype: NormalizedVersion
        """
        return NormalizedVersion(self.spec.get('plugin', 'version'))

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        pass

    def start(self):
        """
        Executed whenever the plugin is to be started, after all the plugins have been loaded.
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


class PluginSpec(ConfigParser):
    """
    Plugin .spec configuration file instance.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the plugin .spec configuration.
        """
        super(PluginSpec, self).__init__(*args, **kwargs)

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


class PluginManager(QtCore.QObject):
    """
    Plugin manager class which takes case of performing some specific operations on plugins.
    """
    def __init__(self, session):
        """
        Initialize the plugin manager.
        :type session: Session
        """
        super(PluginManager, self).__init__(session)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for PluginManager.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def create(self, clazz, spec):
        """
        Create an instance of the given plugin.
        :type clazz: class
        :type spec: PluginSpec
        :rtype: AbstractPlugin
        """
        return clazz(spec, self.session)

    def dispose(self, plugin):
        """
        Dispose the given plugin.
        Will return True if the plugin has been disposed successfully, False otherwise.
        :type plugin: AbstractPlugin
        :rtype: bool
        """
        LOGGER.debug('Disposing plugin: %s v%s', plugin.name(), plugin.version())
        try:
            plugin.dispose()
        except Exception:
            LOGGER.exception('An error occurred while disposing plugin: %s v%s', plugin.name(), plugin.version())
            return False
        else:
            self.session.sgnPluginDisposed.emit(plugin.id())
            return True

    @classmethod
    def find_class(cls, module, name):
        """
        Find and returns the reference to the plugin class in the given module.
        :type module: module
        :type name: str
        :rtype: class
        """
        return getattr(module, '%sPlugin' % ''.join(i.title() for i in list(filter(None, re.split("[_\-]+", name)))))

    def import_plugin_from_directory(self, directory):
        """
        Import a plugin from the given directory:
        * Lookup for the plugin .spec configuration file.
        * Search for the module where the plugin is implemented.
        * Search for the class implementing the plugin.
        * Import the plugin module.
        :type directory: str
        :rtype: tuple
        """
        if is_dir(directory):
            plugin_spec_path = os.path.join(directory, 'plugin.spec')
            if fexists(plugin_spec_path):
                try:
                    LOGGER.debug('Found plugin .spec: %s', plugin_spec_path)
                    plugin_spec = self.spec(fread(plugin_spec_path))
                    plugin_name = plugin_spec.get('plugin', 'id')
                    for extension in ('.pyc', '.pyo', '.py'):
                        plugin_path = os.path.join(directory, '%s%s' % (plugin_name, extension))
                        if fexists(plugin_path):
                            LOGGER.debug('Found plugin module: %s', plugin_path)
                            plugin_module = SourceFileLoader(plugin_name, plugin_path).load_module()
                            plugin_class = self.find_class(plugin_module, plugin_name)
                            return plugin_spec, plugin_class
                    else:
                        raise PluginError('missing plugin module: %s.py(c|o)' % os.path.join(directory, plugin_name))
                except Exception as e:
                    LOGGER.exception('Failed to import plugin: %s', e)

    def import_plugin_from_zip(self, archive):
        """
        Import a plugin from the given zip archive:
        * Lookup for the plugin .spec configuration file.
        * Search for the module where the plugin is implemented.
        * Search for the class implementing the plugin.
        * Import the plugin module.
        :type archive: str
        """
        if fexists(archive) and File.forPath(archive) is File.Zip:
            zf = ZipFile(archive)
            zf_name_list = zf.namelist()
            for file_or_directory in zf_name_list:
                if file_or_directory.endswith('plugin.spec'):
                    try:
                        LOGGER.debug('Found plugin .spec: %s', os.path.join(archive, file_or_directory))
                        plugin_spec_content = zf.read(file_or_directory).decode('utf8')
                        plugin_spec = self.spec(plugin_spec_content)
                        plugin_name = plugin_spec.get('plugin', 'id')
                        plugin_zip_base_path = rstrip(file_or_directory, 'plugin.spec')
                        plugin_abs_base_path = os.path.join(archive, plugin_zip_base_path)
                        plugin_zip_module_base_path = os.path.join(plugin_zip_base_path, plugin_name)
                        plugin_abs_module_base_path = os.path.join(archive, plugin_zip_module_base_path)
                        for extension in ('.pyc', '.pyo', '.py'):
                            plugin_zip_module_path = '%s%s' % (plugin_zip_module_base_path, extension)
                            if plugin_zip_module_path in zf_name_list:
                                LOGGER.debug('Found plugin module: %s', os.path.join(archive, plugin_zip_module_path))
                                plugin_module = zipimporter(plugin_abs_base_path).load_module(plugin_name)
                                plugin_class = self.find_class(plugin_module, plugin_name)
                                return plugin_spec, plugin_class
                        else:
                            raise PluginError('missing plugin module: %s.py(c|o)' % plugin_abs_module_base_path)
                    except Exception as e:
                        LOGGER.exception('Failed to import plugin: %s', e)

    def init(self, info):
        """
        Initialize previously looked up plugins returning the list of successfully initialized plugins.
        :type info: list
        :rtype: list
        """
        if not info:
            LOGGER.info('No plugin to be initialized')
            return []

        LOGGER.info('Loading %s plugin(s):', len(info))
        for entry in info:
            plugin_author = entry[0].get('plugin', 'author', fallback='<unknown>')
            plugin_contact = entry[0].get('plugin', 'contact', fallback='<unknown>')
            plugin_name = entry[0].get('plugin', 'name')
            plugin_version = entry[0].get('plugin', 'version')
            LOGGER.info('* %s v%s (%s - %s)', plugin_name, plugin_version, plugin_author, plugin_contact)

        pluginsList = []
        pluginsLoadedSet = set()
        for entry in info:
            plugin_id = entry[0].get('plugin', 'id')
            plugin_name = entry[0].get('plugin', 'name')
            plugin_version = entry[0].get('plugin', 'version')
            if plugin_id not in pluginsLoadedSet:
                try:
                    LOGGER.info('Loading plugin: %s v%s', plugin_name, plugin_version)
                    plugin = self.create(entry[1], entry[0])
                except Exception:
                    LOGGER.exception('Failed to load plugin: %s v%s', plugin_name, plugin_version)
                else:
                    pluginsList.append(plugin)
                    pluginsLoadedSet.add(plugin.id())
            else:
                LOGGER.warning('Loading plugin: %s v%s -> skipped: plugin already loaded', plugin_name, plugin_version)

        started = []
        for plugin in pluginsList:
            if self.start(plugin):
                started.append(plugin)

        return started

    def install(self, archive):
        """
        Install the given plugin archive.
        During the installation process we'll check for a correct plugin structure,
        i.e. for the .spec file and the plugin module to be available. We won't check if
        the plugin actually runs since this will be handle by the application statt sequence.
        :type archive: str
        :rtype: PluginSpec
        """
        try:

            ## CHECK FOR CORRECT PLUGIN ARCHIVE
            if not fexists(archive):
                raise PluginError('file not found: %s' % archive)
            if not File.forPath(archive) is File.Zip:
                raise PluginError('%s is not a valid plugin' % archive)

            ## LOOKUP THE SPEC FILE
            zf = ZipFile(archive)
            zf_name_list = zf.namelist()
            for file_or_directory in zf_name_list:
                if file_or_directory.endswith('plugin.spec'):
                    LOGGER.debug('Found plugin .spec: %s', os.path.join(archive, file_or_directory))
                    plugin_spec_content = zf.read(file_or_directory).decode('utf8')
                    plugin_spec = self.spec(plugin_spec_content)
                    break
            else:
                raise PluginError('missing plugin.spec in %s' % archive)

            ## LOOKUP THE PLUGIN MODULE
            plugin_name = plugin_spec.get('plugin', 'id')
            plugin_zip_base_path = rstrip(file_or_directory, 'plugin.spec')
            plugin_zip_module_base_path = os.path.join(plugin_zip_base_path, plugin_name)
            for extension in ('.pyc', '.pyo', '.py'):
                plugin_zip_module_path = '%s%s' % (plugin_zip_module_base_path, extension)
                if plugin_zip_module_path in zf_name_list:
                    LOGGER.debug('Found plugin module: %s', os.path.join(archive, plugin_zip_module_path))
                    break
            else:
                raise PluginError('missing plugin module: %s.py(c|o) in %s' % (plugin_zip_module_base_path, archive))

            # CHECK FOR THE PLUGIN TO BE ALREADY INSTALLED
            plugin_id = plugin_spec.get('plugin', 'id')
            plugin_name = plugin_spec.get('plugin', 'name')
            if self.session.plugin(plugin_spec.get('plugin', 'id')):
                raise PluginError('plugin %s (id: %s) is already installed' % (plugin_name, plugin_id))

            # COPY THE PLUGIN
            mkdir('@home/plugins/')
            fcopy(archive, '@home/plugins/')

        except Exception as e:
            LOGGER.error('Failed to install plugin: %s', e, exc_info=not isinstance(e, PluginError))
            raise e
        else:
            return plugin_spec

    def lookup(self, base):
        """
        Lookup for a plugin in the given base path.
        :type base: str
        :rtype: list
        """
        info = []
        if is_dir(base):
            LOGGER.info('Looking for plugins in %s', base)
            for file_or_directory in os.listdir(base):
                file_or_directory_path = os.path.join(base, file_or_directory)
                info.append(self.import_plugin_from_directory(file_or_directory_path))
                info.append(self.import_plugin_from_zip(file_or_directory_path))
        return list(filter(None, info))

    @classmethod
    def spec(cls, content):
        """
        Parse and validate a plugin configuration file (.spec) content.
        :type content: str
        :rtype: PluginSpec
        """
        spec = PluginSpec()
        spec.read_string(content)
        for key in ('id', 'name', 'version'):
            if not spec.has_option('plugin', key):
                raise NoOptionError('plugin', key)
        return spec

    def start(self, plugin):
        """
        Start the given plugin.
        Will return True if the plugin has been started successfully, False otherwise.
        :type plugin: AbstractPlugin
        :rtype: bool
        """
        LOGGER.debug('Starting plugin: %s v%s', plugin.name(), plugin.version())
        try:
            plugin.start()
        except Exception:
            LOGGER.exception('An error occurred while starting plugin: %s v%s', plugin.name(), plugin.version())
            return False
        else:
            self.session.sgnPluginStarted.emit(plugin.id())
            return True


class PluginError(RuntimeError):
    """
    Raised whenever a given plugin doesn't have a correct plugin structure.
    """
    pass