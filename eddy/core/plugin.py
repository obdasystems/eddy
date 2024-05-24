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

from abc import ABCMeta
from configparser import (
    ConfigParser,
    NoOptionError,
)
import importlib
from importlib.machinery import PathFinder
import inspect
import keyword
import os
import re
import sys
from typing import (
    cast,
    Any,
    Dict,
    List,
    Tuple,
    Type,
    TYPE_CHECKING,
)
from zipfile import (
    is_zipfile,
    ZipFile,
)

from PyQt5 import QtCore

from eddy.core.common import (
    HasActionSystem,
    HasMenuSystem,
    HasShortcutSystem,
    HasWidgetSystem,
)
from eddy.core.datatypes.system import (
    File,
    IS_FROZEN,
)
from eddy.core.functions.fsystem import (
    fcopy,
    fexists,
    fread,
    fremove,
)
from eddy.core.functions.fsystem import (
    isdir,
    mkdir,
    rmdir,
)
from eddy.core.functions.misc import (
    first,
    lstrip,
)
from eddy.core.functions.path import (
    expandPath,
    isSubPath,
)
from eddy.core.output import getLogger

if TYPE_CHECKING:
    from types import ModuleType
    from importlib.metadata import EntryPoint
    from eddy.core.project import Project
    from eddy.ui.session import Session

LOGGER = getLogger()


class AbstractPlugin(
    HasActionSystem,
    HasMenuSystem,
    HasShortcutSystem,
    HasWidgetSystem,
    QtCore.QObject,
):
    """
    Extension QtCore.QObject which implements a plugin.
    """
    __metaclass__ = ABCMeta

    def __init__(self, spec: PluginSpec, session: Session) -> None:
        """
        Initialize the plugin.
        """
        super().__init__(parent=session)
        self.spec = spec

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self) -> Project:
        """
        Returns the reference to the active project.
        """
        return self.session.project

    @property
    def session(self) -> Session:
        """
        Returns the reference to the plugin session.
        """
        return cast('Session', self.parent())

    #############################################
    #   INTERFACE
    #################################

    def author(self) -> str:
        """
        Returns the author of the plugin.
        """
        return self.spec.get('plugin', 'author', fallback='<unknown>')

    def contact(self) -> str:
        """
        Returns the contact address for this plugin.
        """
        return self.spec.get('plugin', 'contact', fallback='<unknown>')

    def id(self) -> str:
        """
        Returns the plugin identifier.
        """
        return self.spec.get('plugin', 'id')

    def isBuiltIn(self) -> bool:
        """
        Returns `True` if this plugin is a built-in one, `False` otherwise.
        """
        return isSubPath('@plugins/', inspect.getfile(self.__class__))

    def name(self) -> str:
        """
        Returns the name of the plugin.
        """
        return self.spec.get('plugin', 'name')

    def objectName(self) -> str:
        """
        Returns the system name of the plugin.
        """
        return self.spec.get('plugin', 'id')

    def path(self) -> str:
        """
        Returns the path to the the plugin (either a directory of a ZIP file).
        """
        path = lstrip(
            inspect.getfile(self.__class__),
            expandPath('@plugins/'),
            expandPath('@data/plugins/'),
        )
        home = first(filter(None, path.split(os.path.sep)))
        root = expandPath('@plugins/' if self.isBuiltIn() else '@data/plugins/')
        return os.path.join(root, home)

    @classmethod
    def subclasses(cls) -> List[Type[AbstractPlugin]]:
        """
        Returns the list of subclasses subclassing this very class.
        """
        return cls.__subclasses__() + [c for i in cls.__subclasses__() for c in i.subclasses()]

    def version(self) -> str:
        """
        Returns the version of the plugin.
        """
        return self.spec.get('plugin', 'version')

    #############################################
    #   HOOKS
    #################################

    def dispose(self) -> None:
        """
        Executed whenever the plugin is going to be destroyed.
        """
        pass

    def start(self) -> None:
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

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a 'CRITICAL' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        """
        LOGGER.critical('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a 'DEBUG' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        """
        LOGGER.debug('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a 'ERROR' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        """
        LOGGER.error('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a 'INFO' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        """
        LOGGER.info('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a 'WARNING' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        """
        LOGGER.warning('{0}: {1}'.format(self.name(), message), *args, **kwargs)


class PluginSpec(ConfigParser):
    """
    Plugin .spec configuration file instance.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin .spec configuration.
        """
        super().__init__(*args, **kwargs)

    #############################################
    #   INTERFACE
    #################################

    def getList(self, section: str, option: str) -> List[str]:
        """
        Get the content of the given section/option combination returning it as a list.
        """
        return list(filter(None, re.split(r'[,\s\-]+', self.get(section, option))))

    def getPath(self, section: str, option: str) -> str:
        """
        Get the content of the given section/option performing path expansion.
        """
        return expandPath(self.get(section, option))


class PluginManager(QtCore.QObject):
    """
    Plugin manager class which takes case of performing some specific operations on plugins.
    """
    info = {}  # type: Dict[str, Tuple]

    def __init__(self, session: Session) -> None:
        """
        Initialize the plugin manager.
        """
        super().__init__(session)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self) -> Session:
        """
        Returns the reference to the plugin manager session.
        """
        return cast('Session', self.parent())

    #############################################
    #   INTERFACE
    #################################

    def clear(self) -> None:
        """
        Remove all the plugins from the active Session.
        """
        self.session.clearPlugins()

    def create(self, clazz: Type[AbstractPlugin], spec: PluginSpec) -> AbstractPlugin:
        """
        Create an instance of the given plugin.
        """
        return clazz(spec, self.session)

    def dispose(self, plugin: AbstractPlugin) -> bool:
        """
        Dispose the given plugin.
        Will return `True` if the plugin has been disposed successfully, `False` otherwise.
        """
        LOGGER.info('Disposing plugin: %s v%s', plugin.name(), plugin.version())
        try:
            plugin.dispose()
        except Exception:
            LOGGER.exception('An error occurred while disposing plugin: %s v%s', plugin.name(), plugin.version())
            return False
        else:
            self.session.sgnPluginDisposed.emit(plugin.id())
            return True

    @classmethod
    def find_class(cls, mod: ModuleType, name: str) -> Type[AbstractPlugin]:
        """
        Find and returns the reference to the plugin class in the given module.
        """
        plugin_classes = []
        for obj in mod.__dict__.values():
            if obj in AbstractPlugin.subclasses():
                plugin_classes.append(obj)
        if len(plugin_classes) == 0:
            raise PluginError('No plugin class found for plugin: %s' % name)
        if len(plugin_classes) > 1:
            plugin_classes.sort(key=lambda item: (getattr(item, '__module__', None) or '').count('.'))
        return plugin_classes[0]

    @classmethod
    def find_spec(cls, file_or_directory: str) -> PluginSpec:
        """
        Searches the given file or directory for a 'plugin.spec' file and tries to load it,
        or returns 'None' if no such file exists.
        """
        file_or_directory = expandPath(file_or_directory)
        try:
            if os.path.exists(file_or_directory) and os.access(file_or_directory, os.R_OK):
                # READ SPEC FILE FROM DIRECTORY
                if isdir(file_or_directory):
                    plugin_spec_path = os.path.join(file_or_directory, 'plugin.spec')
                    if fexists(plugin_spec_path):
                        return cls.spec(fread(plugin_spec_path))
                # READ SPEC FILE FROM ZIP ARCHIVE
                elif is_zipfile(file_or_directory):
                    zf = ZipFile(file_or_directory)
                    zf_name_list = zf.namelist()
                    if 'plugin.spec' in zf_name_list:
                        plugin_spec_content = zf.read('plugin.spec').decode('utf8')
                        return cls.spec(plugin_spec_content)
        except Exception as e:
            LOGGER.exception('Failed to load plugin spec: %s', e)

    @classmethod
    def import_plugin_from_path(cls, path: str) -> Tuple:
        """
        Import a plugin from the given path by lookup for the plugin .spec
        configuration file in the given file or directory. Allowed values for 'path'
        are path to directories or zip archives.

        For a zip file or directory to be recognized as a plugin there must be a
        file named 'plugin.spec' at the top level.

        This method will not try to load the plugin module since we wait until the
        initialization time to perform plugin imports. This allows the scan for plugins
        to be completed before attempting any import.
        """
        try:
            plugin_path = expandPath(path)
            plugin_spec = cls.find_spec(plugin_path)
            if plugin_spec:
                return plugin_spec, plugin_path, None
        except Exception as e:
            LOGGER.exception('Failed to import plugin: %s', e)

    @classmethod
    def import_plugin_from_entry_point(cls, entry_point: EntryPoint) -> Tuple:
        """
        Import a plugin from the given entry point:
        * Lookup for the plugin .spec configuration file from the entry point distribution.
        * Find the class implementing the plugin.

        This method always returns 'None' for the plugin path since the plugin class
        can be located by looking at entries in sys.path.
        """
        try:
            if not IS_FROZEN:
                # We search for entry points only if the application is not frozen.
                for pkg_file in entry_point.dist.files:
                    if pkg_file.match('plugin.spec'):
                        plugin_spec = PluginManager.spec(pkg_file.read_text())
                        plugin_class = entry_point.load()
                        if isinstance(plugin_class, AbstractPlugin):
                            return plugin_spec, None, plugin_class
                        else:
                            raise PluginError('Invalid plugin class: %s' % plugin_class)
        except Exception as e:
            LOGGER.exception('Failed to import plugin: %s', e)

    def init(self) -> List[AbstractPlugin]:
        """
        Initialize previously looked up plugins returning the list
        of successfully initialized plugins.
        """
        if not PluginManager.info:
            LOGGER.info('No plugin to be initialized')
            return []

        LOGGER.info('Loading %s plugin(s):', len(PluginManager.info))
        for entry in PluginManager.info.values():
            plugin_author = entry[0].get('plugin', 'author', fallback='<unknown>')
            plugin_contact = entry[0].get('plugin', 'contact', fallback='<unknown>')
            plugin_name = entry[0].get('plugin', 'name')
            plugin_version = entry[0].get('plugin', 'version')
            LOGGER.info('* %s v%s (%s - %s)', plugin_name, plugin_version, plugin_author, plugin_contact)

        pluginsList = []
        pluginsLoadedSet = set()
        for spec, plugin_path, plugin_class in PluginManager.info.values():
            plugin_id = spec.get('plugin', 'id')
            plugin_name = spec.get('plugin', 'name')
            plugin_version = spec.get('plugin', 'version')
            if plugin_id not in pluginsLoadedSet:
                try:
                    LOGGER.info('Loading plugin: %s v%s', plugin_name, plugin_version)
                    if not plugin_class:
                        plugin_mod = importlib.import_module('eddy.plugins.%s' % plugin_id)
                        plugin_class = PluginManager.find_class(plugin_mod, plugin_id)
                    plugin = self.create(plugin_class, spec)
                except Exception as e:
                    LOGGER.exception('Failed to load plugin: %s v%s: %s', plugin_name, plugin_version, e)
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

    def install(self, archive: str) -> PluginSpec:
        """
        Install the given plugin archive.
        During the installation process we'll check for a correct plugin structure,
        i.e. for the .spec file and the plugin module to be available. We won't check if
        the plugin actually runs since this will be handle by the application start sequence.
        """
        try:
            # CHECK FOR CORRECT PLUGIN ARCHIVE
            if not fexists(archive):
                raise PluginError('file not found: %s' % archive)
            if not File.forPath(archive) is File.Zip:
                raise PluginError('%s is not a valid plugin' % archive)

            # LOOKUP THE SPEC FILE
            zf = ZipFile(archive)
            zf_name_list = zf.namelist()
            if 'plugin.spec' in zf_name_list:
                LOGGER.debug('Found plugin .spec: %s', os.path.join(archive, 'plugin.spec'))
                plugin_spec_content = zf.read('plugin.spec').decode('utf8')
                plugin_spec = self.spec(plugin_spec_content)
            else:
                raise PluginError('missing plugin.spec in %s' % archive)

            # LOOKUP THE PLUGIN MODULE
            plugin_name = plugin_spec.get('plugin', 'id')
            for extension in importlib.machinery.all_suffixes() + ['/']:
                plugin_zip_module_path = '%s%s' % (plugin_name, extension)
                if plugin_zip_module_path in zf_name_list:
                    LOGGER.debug('Found plugin module: %s', os.path.join(archive, plugin_zip_module_path))
                    break
            else:
                raise PluginError('missing plugin module in %s' % archive)

            # CHECK FOR THE PLUGIN TO BE ALREADY RUNNING
            plugin_id = plugin_spec.get('plugin', 'id')
            plugin_name = plugin_spec.get('plugin', 'name')
            if self.session.plugin(plugin_spec.get('plugin', 'id')):
                raise PluginError('plugin %s (id: %s) is already installed' % (plugin_name, plugin_id))

            # CHECK FOR THE PLUGIN NAMESPACE TO BE UNIQUE
            if plugin_id in self.info:
                raise PluginError('plugin %s (id: %s) is already installed' % (plugin_name, plugin_id))

            # COPY THE PLUGIN
            mkdir('@data/plugins/')
            fcopy(archive, '@data/plugins/')

        except Exception as e:
            LOGGER.error('Failed to install plugin: %s', e, exc_info=not isinstance(e, PluginError))
            raise e
        else:
            return plugin_spec

    @classmethod
    def scan(cls, *args: Any, **kwargs: Any) -> None:
        """
        Scan the given paths looking for plugins.
        This method can also scan setuptools entry points when called with
        the 'entry_point' keyword argument set to the entry point name to scan.
        """
        info = []
        # SCAN THE GIVEN PATHS
        for base in map(expandPath, args):
            if isdir(base):
                LOGGER.info('Looking for plugins in %s', base)
                for file_or_directory in os.listdir(base):
                    file_or_directory_path = os.path.join(base, file_or_directory)
                    info.append(cls.import_plugin_from_path(file_or_directory_path))
        # SCAN THEN GIVEN ENTRY POINTS
        if not IS_FROZEN:
            from importlib.metadata import entry_points
            entry_point_name = kwargs.get('entry_point')
            if entry_point_name:
                LOGGER.info('Looking for plugins in entry point %s', entry_point_name)
                for entry_point in entry_points().get(entry_point_name, []):
                    info.append(PluginManager.import_plugin_from_entry_point(entry_point))
        # BUILD THE PLUGIN CACHE
        for entry in filter(None, info):
            plugin_id = entry[0].get('plugin', 'id')
            if plugin_id not in cls.info:
                cls.info[plugin_id] = entry

    @classmethod
    def spec(cls, content: str) -> PluginSpec:
        """
        Parse and validate a plugin configuration file (.spec) content.
        A valid configuration file must have a 'plugin' section, with
        at least the 'id', 'name', and 'version' keys defined.
        The value for 'id' key *must* be a valid Python identifier.

        e.g.:
        [plugin]
        id = my_plugin
        name = My Plugin Name
        version = 0.1

        """
        spec = PluginSpec()
        spec.read_string(content)
        for key in ('id', 'name', 'version'):
            if not spec.has_option('plugin', key):
                raise NoOptionError('plugin', key)
            plugin_id = spec.get('plugin', 'id')
            if not plugin_id.isidentifier() or keyword.iskeyword(plugin_id):
                raise ValueError('plugin id is not a valid identifier: %s' % plugin_id)
        return spec

    def start(self, plugin: AbstractPlugin) -> bool:
        """
        Start the given plugin.
        Will return `True` if the plugin has been started successfully, `False` otherwise.
        """
        LOGGER.info('Starting plugin: %s v%s', plugin.name(), plugin.version())
        try:
            plugin.start()
        except Exception:
            LOGGER.exception('An error occurred while starting plugin: %s v%s', plugin.name(), plugin.version())
            return False
        else:
            self.session.sgnPluginStarted.emit(plugin.id())
            return True

    def uninstall(self, plugin: AbstractPlugin) -> None:
        """
        Uninstall the given plugin.
        """
        if self.dispose(plugin):
            self.session.removePlugin(plugin)
            path = plugin.path()
            if isdir(path):
                rmdir(path)
            elif fexists(path):
                fremove(path)


class PluginFinder(object):
    """
    Finder for plugin modules based on the import protocol originally defined in PEP 302
    and now part of the language reference for imports described at:
    https://docs.python.org/3/reference/import.html.
    """
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        """
        From the official documentation:
         - path is the list of paths where to look for the module,
                if set to 'None', then search for sys.path.
         - target is set only in case this is a module reload request,
                  otherwise it will always be 'None'.
        """
        splitname = fullname.split('.')

        # CHECK IF NAME MATCHES THE PLUGIN PACKAGE PATH
        if splitname[:2] == ['eddy', 'plugins'] and len(splitname) >= 3:
            if splitname[2] in PluginManager.info:
                plugin_spec, plugin_path, plugin_class = PluginManager.info.get(splitname[2])
                plugin_path = expandPath(plugin_path)
                return PathFinder.find_spec(fullname, [plugin_path])
        return None


sys.meta_path.insert(0, PluginFinder)


class PluginError(RuntimeError):
    """
    Raised whenever a given plugin doesn't have a correct plugin structure.
    """
    pass
