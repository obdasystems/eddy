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


import time

from PyQt5 import QtCore

from eddy.core.datatypes.owl import OWLProfile
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.exporters.common import AbstractProjectExporter
from eddy.core.loaders.common import AbstractDiagramLoader
from eddy.core.loaders.common import AbstractProjectLoader
from eddy.core.functions.misc import isEmpty
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger
from eddy.core.profiles.common import AbstractProfile
from eddy.core.worker import AbstractWorker

from eddy.ui.notification import NotificationPopup

LOGGER = getLogger(__name__)


class HasActionSystem(object):
    """
    Mixin which adds the ability to store and retrieve actions.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._actionDict = {}
        self._actionList = []

    def action(self, objectName):
        """
        Returns the reference to a QAction or to a QActionGroup given it's objectName.
        :type objectName: str
        :rtype: T <= QAction|QActionGroup
        """
        return self._actionDict.get(objectName, None)

    def actions(self):
        """
        Returns the list of QAction.
        :rtype: list
        """
        return self._actionList

    def addAction(self, action):
        """
        Add a QAction or a QActionGroup to the set.
        :type action: T <= QAction|QActionGroup
        :rtype: T <= QAction|QActionGroup
        """
        if isEmpty(action.objectName()):
            raise ValueError("missing objectName in %s" % action.__class__.__name__)
        if action.objectName() in self._actionDict:
            raise ValueError("duplicate action found: %s" % action.objectName())
        self._actionList.append(action)
        self._actionDict[action.objectName()] = action
        # LOGGER.debug("Added %s(%s)", action.__class__.__name__, action.objectName())
        return action

    def addActions(self, actions):
        """
        Add the given group of QAction or a QActionGroup to the set.
        :type actions: T <= list|tuple
        """
        for action in actions:
            self.addAction(action)

    def clearActions(self):
        """
        Remove all the actions.
        """
        self._actionDict.clear()
        self._actionList.clear()

    def insertAction(self, action, before):
        """
        Insert the given QAction or QActionGroup before the given one.
        :type action: T <= QAction|QActionGroup
        :type before: T <= QAction|QActionGroup
        :rtype: T <= QAction|QActionGroup
        """
        if isEmpty(action.objectName()):
            raise ValueError("missing objectName in %s" % action.__class__.__name__)
        if action.objectName() in self._actionDict:
            raise ValueError("duplicate action found: %s" % action.objectName())
        self._actionList.insert(self._actionList.index(before), action)
        self._actionDict[action.objectName()] = action
        # LOGGER.debug("Added %s(%s) before %s(%s)",
        #              action.__class__.__name__, action.objectName(),
        #              before.__class__.__name__, before.objectName())
        return action

    def insertActions(self, actions, before):
        """
        Insert the given group of QAction or QActionGroup before the given one.
        :type actions: T <= list|tuple
        :type before: T <= QAction|QActionGroup
        """
        for action in actions:
            self.insertAction(action, before)

    def removeAction(self, action):
        """
        Removes the given QAction or QActionGroup from the set.
        :type action: T <= QAction|QActionGroup
        :rtype: T <= QAction|QActionGroup
        """
        self._actionList.remove(action)
        del self._actionDict[action.objectName()]
        return action


class HasMenuSystem(object):
    """
    Mixin which adds the ability to store and retrieve menus.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._menuDict = {}
        self._menuList = []

    def addMenu(self, menu):
        """
        Add a QMenu to the set.
        :type menu: QMenu
        :rtype: QMenu
        """
        if isEmpty(menu.objectName()):
            raise ValueError("missing objectName in %s" % menu.__class__.__name__)
        if menu.objectName() in self._menuDict:
            raise ValueError("duplicate menu found: %s" % menu.objectName())
        self._menuList.append(menu)
        self._menuDict[menu.objectName()] = menu
        # LOGGER.debug("Added %s(%s)", menu.__class__.__name__, menu.objectName())
        return menu

    def addMenus(self, menus):
        """
        Add the given group of QMenu to the set.
        :type menus: T <= list|tuple
        """
        for menu in menus:
            self.addMenu(menu)

    def clearMenus(self):
        """
        Remove all the menus.
        """
        self._menuDict.clear()
        self._menuList.clear()

    def insertMenu(self, menu, before):
        """
        Insert the given QMenu before the given one.
        :type menu: QMenu
        :type before: QMenu
        :rtype: QMenu
        """
        if isEmpty(menu.objectName()):
            raise ValueError("missing objectName in %s" % menu.__class__.__name__)
        if menu.objectName() in self._menuDict:
            raise ValueError("duplicate menu found: %s" % menu.objectName())
        self._menuList.insert(self._menuList.index(before), menu)
        self._menuDict[menu.objectName()] = menu
        # LOGGER.debug("Added %s(%s) before %s(%s)",
        #              menu.__class__.__name__, menu.objectName(),
        #              before.__class__.__name__, before.objectName())
        return menu

    def insertMenus(self, menus, before):
        """
        Insert the given group of QMenu before the given one.
        :type menus: T <= list|tuple
        :type before: QMenu
        """
        for menu in menus:
            self.insertMenu(menu, before)

    def menu(self, objectName):
        """
        Returns the reference to a QMenu given it's objectName.
        :type objectName: str
        :rtype: QMenu
        """
        return self._menuDict.get(objectName, None)

    def menus(self):
        """
        Returns the list of QMenu.
        :rtype: list
        """
        return self._menuList

    def removeMenu(self, menu):
        """
        Removes the given QMenu from the set.
        :type menu: QMenu
        :rtype: QMenu
        """
        self._menuList.remove(menu)
        del self._menuDict[menu.objectName()]
        return menu


class HasPluginSystem(object):
    """
    Mixin which adds the ability to store and retrieve plugins.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._pluginDict = {}
        self._pluginList = []

    def addPlugin(self, plugin):
        """
        Add a plugin to the set.
        :type plugin: AbstractPlugin
        :rtype: AbstractPlugin
        """
        if isEmpty(plugin.objectName()):
            raise ValueError("missing objectName in %s" % plugin.__class__.__name__)
        if plugin.objectName() in self._pluginDict:
            raise ValueError("duplicate plugin found: %s" % plugin.objectName())
        self._pluginList.append(plugin)
        self._pluginDict[plugin.objectName()] = plugin
        # LOGGER.debug("Added %s(%s)", plugin.__class__.__name__, plugin.objectName())
        return plugin

    def addPlugins(self, plugins):
        """
        Add the given group of plugins to the set.
        :type plugins: T <= list|tuple
        """
        for plugin in plugins:
            self.addPlugin(plugin)

    def clearPlugins(self):
        """
        Remove all the plugins.
        """
        self._pluginDict.clear()
        self._pluginList.clear()

    def insertPlugin(self, widget, before):
        """
        Insert the given plugin before the given one.
        :type widget: AbstractPlugin
        :type before: AbstractPlugin
        :rtype: AbstractPlugin
        """
        if isEmpty(widget.objectName()):
            raise ValueError("missing objectName in %s" % widget.__class__.__name__)
        if widget.objectName() in self._pluginDict:
            raise ValueError("duplicate plugin found: %s" % widget.objectName())
        self._pluginList.insert(self._pluginList.index(before), widget)
        self._pluginDict[widget.objectName()] = widget
        # LOGGER.debug("Added %s(%s) before %s(%s)",
        #              plugin.__class__.__name__, plugin.objectName(),
        #              before.__class__.__name__, before.objectName())
        return widget

    def insertPlugins(self, plugins, before):
        """
        Insert the given group of plugins before the given one.
        :type plugins: T <= list|tuple
        :type before: AbstractPlugin
        """
        for plugin in plugins:
            self.insertPlugin(plugin, before)

    def plugin(self, objectName):
        """
        Returns the reference to a plugin given it's objectName.
        :type objectName: str
        :rtype: AbstractPlugin
        """
        return self._pluginDict.get(objectName, None)

    def plugins(self):
        """
        Returns the list of plugins.
        :rtype: list
        """
        return self._pluginList

    def removePlugin(self, plugin):
        """
        Removes the given plugin from the set.
        :type plugin: AbstractPlugin
        :rtype: AbstractPlugin
        """
        self._pluginList.remove(plugin)
        del self._pluginDict[plugin.objectName()]
        return plugin


class HasWidgetSystem(object):
    """
    Mixin which adds the ability to store and retrieve widgets.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._widgetDict = {}
        self._widgetList = []

    def addWidget(self, widget):
        """
        Add a QWidget to the set.
        :type widget: QWidget
        :rtype: QWidget
        """
        if isEmpty(widget.objectName()):
            raise ValueError("missing objectName in %s" % widget.__class__.__name__)
        if widget.objectName() in self._widgetDict:
            raise ValueError("duplicate widget found: %s" % widget.objectName())
        self._widgetList.append(widget)
        self._widgetDict[widget.objectName()] = widget
        # LOGGER.debug("Added %s(%s)", widget.__class__.__name__, widget.objectName())
        return widget

    def addWidgets(self, widgets):
        """
        Add the given group of QWidget to the set.
        :type widgets: T <= list|tuple
        """
        for widget in widgets:
            self.addWidget(widget)

    def clearWidgets(self):
        """
        Remove all the widgets.
        """
        self._widgetDict.clear()
        self._widgetList.clear()

    def insertWidget(self, widget, before):
        """
        Insert the given QWidget before the given one.
        :type widget: QWidget
        :type before: QWidget
        :rtype: QWidget
        """
        if isEmpty(widget.objectName()):
            raise ValueError("missing objectName in %s" % widget.__class__.__name__)
        if widget.objectName() in self._widgetDict:
            raise ValueError("duplicate widget found: %s" % widget.objectName())
        self._widgetList.insert(self._widgetList.index(before), widget)
        self._widgetDict[widget.objectName()] = widget
        # LOGGER.debug("Added %s(%s) before %s(%s)",
        #              widget.__class__.__name__, widget.objectName(),
        #              before.__class__.__name__, before.objectName())
        return widget

    def insertWidgets(self, widgets, before):
        """
        Insert the given group of QWidget before the given one.
        :type widgets: T <= list|tuple
        :type before: QWidget
        """
        for widget in widgets:
            self.insertWidget(widget, before)

    def widget(self, objectName):
        """
        Returns the reference to a QWidget given it's objectName.
        :type objectName: str
        :rtype: QWidget
        """
        return self._widgetDict.get(objectName, None)

    def widgets(self):
        """
        Returns the list of QWidget.
        :rtype: list
        """
        return self._widgetList

    def removeWidget(self, widget):
        """
        Removes the given QWidget from the set.
        :type widget: QWidget
        :rtype: QWidget
        """
        self._widgetList.remove(widget)
        del self._widgetDict[widget.objectName()]
        return widget


class HasDiagramExportSystem(object):
    """
    Mixin which adds the ability to store and retrieve Diagram exporters.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._diagramExporterDict = {}
        self._diagramExporterList = []

    def addDiagramExporter(self, exporter):
        """
        Add a diagram exporter class to the set.
        :type exporter: class
        """
        if not issubclass(exporter, AbstractDiagramExporter):
            raise ValueError("diagram exporter must be subclass of eddy.core.exporters.common.AbstractDiagramExporter")
        filetype = exporter.filetype()
        if filetype in self._diagramExporterDict:
            raise ValueError("duplicate diagram exporter found for filetype %s" % filetype.value)
        self._diagramExporterList.append(exporter)
        self._diagramExporterDict[filetype] = exporter
        #LOGGER.debug("Added diagram exporter %s -> %s", exporter.__name__, filetype.value)

    def addDiagramExporters(self, exporters):
        """
        Add the given group of diagram exporter classes to the set.
        :type exporters: T <= list|tuple
        """
        for exporter in exporters:
            self.addDiagramExporter(exporter)

    def clearDiagramExporters(self):
        """
        Remove all the diagram exporters.
        """
        self._diagramExporterDict.clear()
        self._diagramExporterList.clear()

    def createDiagramExporter(self, filetype, diagram, session=None):
        """
        Creates an instance of a diagram exporter for the given filetype.
        :type filetype: File
        :type diagram: Diagram
        :type session: Session
        :rtype: AbstractDiagramExporter
        """
        exporter = self.diagramExporter(filetype)
        if not exporter:
            raise ValueError("missing diagram exporter for filetype %s", filetype.value)
        return exporter(diagram, session)

    def diagramExporter(self, filetype):
        """
        Returns the reference to a diagram exporter class given a filetype.
        :type filetype: File
        :rtype: class
        """
        return self._diagramExporterDict.get(filetype, None)

    def diagramExporterNameFilters(self, exclude=None):
        """
        Returns the list of diagram exporter name filters.
        :type exclude: T <= list|tuple|set
        :rtype: list
        """
        collection = [x.filetype() for x in self.diagramExporters(exclude)]
        collection = [x.value for x in collection]
        return collection

    def diagramExporters(self, exclude=None):
        """
        Returns the list of diagram exporter classes.
        :type exclude: T <= list|tuple|set
        :rtype: list
        """
        collection = self._diagramExporterList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def insertDiagramExporter(self, exporter, before):
        """
        Insert the given diagram exporter class before the given one.
        :type exporter: class
        :type before: class
        """
        if not issubclass(exporter, AbstractDiagramExporter):
            raise ValueError("diagram exporter must be subclass of eddy.core.exporters.common.AbstractDiagramExporter")
        filetype1 = exporter.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._diagramExporterDict:
            raise ValueError("duplicate diagram exporter found for filetype %s" % filetype1.value)
        self._diagramExporterList.insert(self._diagramExporterList.index(before), exporter)
        self._diagramExporterDict[filetype1] = exporter
        # LOGGER.debug("Added diagram exporter %s -> %s before diagram exporter %s -> %s",
        #              exporter.__name__, filetype.value,
        #              before.__name__, filetype1.value)

    def insertDiagramExporters(self, exporters, before):
        """
        Insert the given group of diagram exporter classes before the given one.
        :type exporters: T <= list|tuple
        :type before: class
        """
        for exporter in exporters:
            self.insertDiagramExporter(exporter, before)

    def removeDiagramExporter(self, exporter):
        """
        Removes the given diagram exporter class from the set.
        :type exporter: class
        :rtype: class
        """
        self._diagramExporterList.remove(exporter)
        del self._diagramExporterDict[exporter.filetype()]
        return exporter


class HasProjectExportSystem(object):
    """
    Mixin which adds the ability to store and retrieve Project exporters.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._projectExporterDict = {}
        self._projectExporterList = []

    def addProjectExporter(self, exporter):
        """
        Add a project exporter class to the set.
        :type exporter: class
        """
        if not issubclass(exporter, AbstractProjectExporter):
            raise ValueError("project exporter must be subclass of eddy.core.exporters.common.AbstractProjectExporter")
        filetype = exporter.filetype()
        if filetype in self._projectExporterDict:
            raise ValueError("duplicate project exporter found for filetype %s" % filetype.value)
        self._projectExporterList.append(exporter)
        self._projectExporterDict[filetype] = exporter
        #LOGGER.debug("Added project exporter %s -> %s", exporter.__name__, filetype.value)

    def addProjectExporters(self, exporters):
        """
        Add the given group of project exporter classes to the set.
        :type exporters: T <= list|tuple
        """
        for exporter in exporters:
            self.addProjectExporter(exporter)

    def clearProjectExporters(self):
        """
        Remove all the project exporters.
        """
        self._projectExporterDict.clear()
        self._projectExporterList.clear()

    def createProjectExporter(self, filetype, project, session=None):
        """
        Creates an instance of a project exporter for the given filetype.
        :type filetype: File
        :type project: Project
        :type session: Session
        :rtype: AbstractProjectExporter
        """
        exporter = self.projectExporter(filetype)
        if not exporter:
            raise ValueError("missing project exporter for filetype %s", filetype.value)
        return exporter(project, session)

    def insertProjectExporter(self, exporter, before):
        """
        Insert the given project exporter class before the given one.
        :type exporter: class
        :type before: class
        """
        if not issubclass(exporter, AbstractProjectExporter):
            raise ValueError("project exporter must be subclass of eddy.core.exporters.common.AbstractProjectExporter")
        filetype1 = exporter.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._projectExporterDict:
            raise ValueError("duplicate project exporter found for filetype %s" % filetype1.value)
        self._projectExporterList.insert(self._projectExporterList.index(before), exporter)
        self._projectExporterDict[filetype1] = exporter
        # LOGGER.debug("Added project exporter %s -> %s before project exporter %s -> %s",
        #              exporter.__name__, filetype.value,
        #              before.__name__, filetype1.value)

    def insertProjectExporters(self, exporters, before):
        """
        Insert the given group of project exporter classes before the given one.
        :type exporters: T <= list|tuple
        :type before: class
        """
        for exporter in exporters:
            self.insertProjectExporter(exporter, before)

    def projectExporter(self, filetype):
        """
        Returns the reference to a project exporter class given a filetype.
        :type filetype: File
        :rtype: class
        """
        return self._projectExporterDict.get(filetype, None)

    def projectExporterNameFilters(self, exclude=None):
        """
        Returns the list of project exporter name filters.
        :type exclude: T <= list|tuple|set
        :rtype: list
        """
        collection = [x.filetype() for x in self.projectExporters(exclude)]
        collection = [x.value for x in collection]
        return collection

    def projectExporters(self, exclude=None):
        """
        Returns the list of project exporter classes.
        :type exclude: T <= list|tuple|set
        :rtype: list
        """
        collection = self._projectExporterList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def removeProjectExporter(self, exporter):
        """
        Removes the given project exporter class from the set.
        :type exporter: class
        :rtype: class
        """
        self._projectExporterList.remove(exporter)
        del self._projectExporterDict[exporter.filetype()]
        return exporter


class HasDiagramLoadSystem(object):
    """
    Mixin which adds the ability to store and retrieve Diagram loaders.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._diagramLoaderDict = {}
        self._diagramLoaderList = []

    def addDiagramLoader(self, loader):
        """
        Add a diagram loader class to the set.
        :type loader: class
        """
        if not issubclass(loader, AbstractDiagramLoader):
            raise ValueError("diagram loader must be subclass of eddy.core.loaders.common.AbstractDiagramLoader")
        filetype = loader.filetype()
        if filetype in self._diagramLoaderDict:
            raise ValueError("duplicate diagram loader found for filetype %s" % filetype.value)
        self._diagramLoaderList.append(loader)
        self._diagramLoaderDict[filetype] = loader
        #LOGGER.debug("Added diagram loader %s -> %s", loader.__name__, filetype.value)

    def addDiagramLoaders(self, loaders):
        """
        Add the given group of diagram loader classes to the set.
        :type loaders: T <= list|tuple
        """
        for loader in loaders:
            self.addDiagramLoader(loader)

    def clearDiagramLoaders(self):
        """
        Remove all the diagram loaders.
        """
        self._diagramLoaderDict.clear()
        self._diagramLoaderList.clear()

    def createDiagramLoader(self, filetype, path, project, session=None):
        """
        Creates an instance of a diagram loader for the given filetype.
        :type filetype: File
        :type path: str
        :type project: Project
        :type session: Session
        :rtype: AbstractDiagramLoader
        """
        loader = self.diagramLoader(filetype)
        if not loader:
            raise ValueError("missing diagram loader for filetype %s", filetype.value)
        return loader(path, project, session)

    def diagramLoader(self, filetype):
        """
        Returns the reference to a diagram loader class given a filetype.
        :type filetype: File
        :rtype: class
        """
        return self._diagramLoaderDict.get(filetype, None)

    def diagramLoaderNameFilters(self, exclude=None):
        """
        Returns the list of diagram loader name filters.
        :type exclude: T <= list|tuple|set
        :rtype: list
        """
        collection = [x.filetype() for x in self.diagramLoaders(exclude)]
        collection = [x.value for x in collection]
        return collection

    def diagramLoaders(self, exclude=None):
        """
        Returns the list of diagram loader classes.
        :type exclude: T <= list|tuple|set
        :rtype: list
        """
        collection = self._diagramLoaderList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def insertDiagramLoader(self, loader, before):
        """
        Insert the given diagram loader class before the given one.
        :type loader: class
        :type before: class
        """
        if not issubclass(loader, AbstractDiagramLoader):
            raise ValueError("diagram loader must be subclass of eddy.core.loaders.common.AbstractDiagramLoader")
        filetype1 = loader.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._diagramLoaderDict:
            raise ValueError("duplicate diagram loader found for filetype %s" % filetype1.value)
        self._diagramLoaderList.insert(self._diagramLoaderList.index(before), loader)
        self._diagramLoaderDict[filetype1] = loader
        # LOGGER.debug("Added diagram loader %s -> %s before diagram loader %s -> %s",
        #              loader.__name__, filetype.value,
        #              before.__name__, filetype1.value)

    def insertDiagramLoaders(self, loaders, before):
        """
        Insert the given group of diagram loader classes before the given one.
        :type loaders: T <= list|tuple
        :type before: class
        """
        for loader in loaders:
            self.insertDiagramLoader(loader, before)

    def removeDiagramLoader(self, loader):
        """
        Removes the given diagram loader class from the set.
        :type loader: class
        :rtype: class
        """
        self._diagramLoaderList.remove(loader)
        del self._diagramLoaderDict[loader.filetype()]
        return loader


class HasProjectLoadSystem(object):
    """
    Mixin which adds the ability to store and retrieve Project loaders.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._projectLoaderDict = {}
        self._projectLoaderList = []

    def addProjectLoader(self, loader):
        """
        Add a project loader class to the set.
        :type loader: class
        """
        if not issubclass(loader, AbstractProjectLoader):
            raise ValueError("project loader must be subclass of eddy.core.loaders.common.AbstractProjectLoader")
        filetype = loader.filetype()
        if filetype in self._projectLoaderDict:
            raise ValueError("duplicate project loader found for filetype %s" % filetype.value)
        self._projectLoaderList.append(loader)
        self._projectLoaderDict[filetype] = loader
        #LOGGER.debug("Added project loader %s -> %s", loader.__name__, filetype.value)

    def addProjectLoaders(self, loaders):
        """
        Add the given group of project loader classes to the set.
        :type loaders: T <= list|tuple
        """
        for loader in loaders:
            self.addProjectLoader(loader)

    def clearProjectLoaders(self):
        """
        Remove all the project loaders.
        """
        self._projectLoaderDict.clear()
        self._projectLoaderList.clear()

    def createProjectLoader(self, filetype, path, session=None):
        """
        Creates an instance of a diagram loader for the given filetype.
        :type filetype: File
        :type path: str
        :type session: Session
        :rtype: AbstractDiagramLoader
        """
        loader = self.projectLoader(filetype)
        if not loader:
            raise ValueError("missing project loader for filetype %s", filetype.value)
        return loader(path, session)

    def insertProjectLoader(self, loader, before):
        """
        Insert the given project loader class before the given one.
        :type loader: class
        :type before: class
        """
        if not issubclass(loader, AbstractProjectLoader):
            raise ValueError("project loader must be subclass of eddy.core.loaders.common.AbstractProjectLoader")
        filetype1 = loader.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._projectLoaderDict:
            raise ValueError("duplicate project loader found for filetype %s" % filetype1.value)
        self._projectLoaderList.insert(self._projectLoaderList.index(before), loader)
        self._projectLoaderDict[filetype1] = loader
        # LOGGER.debug("Added project loader %s -> %s before project loader %s -> %s",
        #              loader.__name__, filetype.value,
        #              before.__name__, filetype1.value)

    def insertProjectLoaders(self, loaders, before):
        """
        Insert the given group of project loader classes before the given one.
        :type loaders: T <= list|tuple
        :type before: class
        """
        for loader in loaders:
            self.insertProjectLoader(loader, before)

    def projectLoader(self, filetype):
        """
        Returns the reference to a project loader class given a filetype.
        :type filetype: File
        :rtype: class
        """
        return self._projectLoaderDict.get(filetype, None)

    def projectLoaderNameFilters(self, exclude=None):
        """
        Returns the list of project loader name filters.
        :type exclude: T <= list|tuple|set
        :rtype: list
        """
        collection = [x.filetype() for x in self.projectLoaders(exclude)]
        collection = [x.value for x in collection]
        return collection

    def projectLoaders(self, exclude=None):
        """
        Returns the list of project loader classes.
        :type exclude: T <= list|tuple|set
        :rtype: list
        """
        collection = self._projectLoaderList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def removeProjectLoader(self, loader):
        """
        Removes the given project loader class from the set.
        :type loader: class
        :rtype: class
        """
        self._projectLoaderList.remove(loader)
        del self._projectLoaderDict[loader.filetype()]
        return loader


class HasProfileSystem(object):
    """
    Mixin which adds the ability to store and retrieve ontology profiles.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._profileDict = {}
        self._profileList = []

    def addProfile(self, profile):
        """
        Add an ontology profile class to the set.
        :type profile: class
        """
        if not issubclass(profile, AbstractProfile):
            raise ValueError("ontology profile must be subclass of eddy.core.profiles.common.AbstractProfile")
        if profile.type() in self._profileDict:
            raise ValueError("duplicate ontology profile found: %s" % profile.name())
        self._profileList.append(profile)
        self._profileDict[profile.type()] = profile
        # LOGGER.debug("Added ontology profile: %s", profile.name())

    def addProfiles(self, profiles):
        """
        Add the given group of ontology profile classes to the set.
        :type profiles: T <= list|tuple
        """
        for profile in profiles:
            self.addProfile(profile)

    def clearProfiles(self):
        """
        Remove all the profiles.
        """
        self._profileDict.clear()
        self._profileList.clear()

    def createProfile(self, name_or_type, project=None):
        """
        Creates an instance of an ontology profile for the given name.
        :type name_or_type: T <= OWLProfile|str
        :type project: Project
        :rtype: AbstractProfile
        """
        profile = self.profile(OWLProfile.forValue(name_or_type))
        if not profile:
            LOGGER.warning("Missing profile %s: defaulting to OWL 2", name_or_type)
            profile = self.profile(OWLProfile.OWL2)
        return profile(project)

    def insertProfile(self, profile, before):
        """
        Insert the given ontology profile before the given one.
        :type profile: class
        :type before: class
        """
        if not issubclass(profile, AbstractProfile):
            raise ValueError("ontology profile must be subclass of eddy.core.profiles.common.AbstractProfile")
        if profile.type() in self._profileDict:
            raise ValueError("duplicate ontology profile found: %s" % profile.name())
        self._profileList.insert(self._profileList.index(before), profile)
        self._profileDict[profile.type()] = profile
        # LOGGER.debug("Added ontology profile %s before project loader %s", profile.name(), before.name())

    def insertProfiles(self, profiles, before):
        """
        Insert the given group of ontology profile classes before the given one.
        :type profiles: T <= list|tuple
        :type before: class
        """
        for profile in profiles:
            self.insertProfile(profile, before)

    def profile(self, name_or_type):
        """
        Returns the reference to an ontology profile class given it's name.
        :type name_or_type: T <= OWLProfile|str
        :rtype: class
        """
        return self._profileDict.get(OWLProfile.forValue(name_or_type), None)

    def profiles(self):
        """
        Returns the list of ontology profiles.
        :rtype: list
        """
        return sorted(self._profileList, key=lambda x: x.name())

    def profileNames(self):
        """
        Returns the list of profile names.
        :rtype: list
        """
        return [x.name() for x in self.profiles()]

    def removeProfile(self, profile):
        """
        Removes the given ontology profile class from the set.
        :type profile: class
        :rtype: class
        """
        self._profileList.remove(profile)
        del self._profileDict[profile.type()]
        return profile


class HasThreadingSystem(object):
    """
    Mixin which adds the ability to easily start and stop Qt threads.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._threads = {}
        self._started = {}
        self._workers = {}

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onQThreadFinished(self):
        """
        Executed when a QThread finish it's job.
        """
        self.stopThread(self.sender())

    #############################################
    #   INTERFACE
    #################################

    def startThread(self, name, worker):
        """
        Start a thread using the given worker.
        :type name: str
        :type worker: QtCore.QObject
        """
        LOGGER.debug("Requested threaded execution of worker instance: %s", worker.__class__.__name__)
        # SANITY CHECK
        if name in self._threads or name in self._workers:
            raise RuntimeError('already running (%s)' % name)
        if not isinstance(worker, AbstractWorker):
            raise ValueError('worker class must be subclass of eddy.core.threading.AbstractWorker')
        # START THE WORKER THREAD
        qthread = QtCore.QThread()
        qthread.setObjectName(name)
        LOGGER.debug("Moving worker '%s' in a new thread '%s'", worker.__class__.__name__, name)
        worker.moveToThread(qthread)
        connect(qthread.finished, self.onQThreadFinished)
        connect(qthread.finished, qthread.deleteLater)
        connect(worker.finished, qthread.quit)
        connect(worker.finished, worker.deleteLater)
        connect(qthread.started, worker.run)
        LOGGER.debug("Starting thread: %s", name)
        qthread.start()
        # STORE LOCALLY
        self._started[name] = time.monotonic()
        self._threads[name] = qthread
        self._workers[name] = worker

    def stopRunningThreads(self):
        """
        Stops all the running threads.
        """
        LOGGER.debug('Terminating running thread(s)...')
        for name in [name for name in self._threads.keys()]:
            self.stopThread(name)

    def stopThread(self, name_or_qthread):
        """
        Stop a running thread.
        :type name_or_qthread: T <= str | QThread
        """
        name = name_or_qthread
        if not isinstance(name, str):
            name = name_or_qthread.objectName()
        if name in self._threads:
            LOGGER.debug("Terminating thread: %s (runtime=%.2fms)", name, time.monotonic() - self._started[name])
            qthread = self._threads[name]
            qthread.quit()
            if not qthread.wait(2000):
                qthread.terminate()
                qthread.wait()
            del self._threads[name]
        if name in self._workers:
            del self._workers[name]

    def thread(self, name):
        """
        Returns the reference to a running QThread.
        :type name: str
        :rtype: QtCore.QThread
        """
        return self._threads.get(name, None)

    def threads(self):
        """
        Returns a list of QThread instances in the form (name, QThread).
        :rtype: list
        """
        return [(name, qthread) for name, qthread in self._threads.items()]

    def worker(self, name):
        """
        Returns the reference to a worker which is running in a QThread.
        :type name: str
        :rtype: AbstractWorker
        """
        return self._workers.get(name, None)

    def workers(self):
        """
        Returns a list of AbstractWorker instances in the form (name, AbstractWorker).
        :rtype: list
        """
        return [(name, worker) for name, worker in self._workers.items()]


class HasNotificationSystem(object):
    """
    Mixin which adds the ability to display notification popups.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._popupList = [NotificationPopup(self, i) for i in range(0, 8)]

    def addNotification(self, message):
        """
        Add a notification popup.
        :type message: str
        """
        for popup in self._popupList:
            if not popup.isVisible():
                popup.setText(message)
                popup.show()
                break
        else:
            LOGGER.warning('Missed notification (%s): no free notification popup available', message)

    def hideNotifications(self):
        """
        Make sure to dismiss all the notification popups.
        """
        for popup in self._popupList:
            popup.dismiss()