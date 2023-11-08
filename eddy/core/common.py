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

import time
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Type,
    Tuple,
    Union,
    TYPE_CHECKING,
)

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.datatypes.owl import OWLProfile
from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.exporters.common import AbstractOntologyExporter
from eddy.core.exporters.common import AbstractProjectExporter
from eddy.core.functions.misc import isEmpty
from eddy.core.functions.signals import connect
from eddy.core.loaders.common import AbstractDiagramLoader
from eddy.core.loaders.common import AbstractOntologyLoader
from eddy.core.loaders.common import AbstractProjectLoader
from eddy.core.output import getLogger
from eddy.core.profiles.common import AbstractProfile
from eddy.core.worker import AbstractWorker
from eddy.ui.notification import Notification

if TYPE_CHECKING:
    from eddy.core.diagram import Diagram
    from eddy.core.project import Project
    from eddy.core.plugin import AbstractPlugin
    from eddy.ui.session import Session

LOGGER = getLogger()


class HasActionSystem(object):
    """
    Mixin which adds the ability to store and retrieve actions.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._actionDict = {}  # type: Dict[str, Union[QtWidgets.QAction, QtWidgets.QActionGroup]]
        self._actionList = []  # type: List[Union[QtWidgets.QAction, QtWidgets.QActionGroup]]

    def action(self, objectName: str) -> Union[QtWidgets.QAction, QtWidgets.QActionGroup]:
        """
        Returns the reference to a QAction or to a QActionGroup given it's objectName.
        """
        return self._actionDict.get(objectName, None)

    def actions(self) -> List[Union[QtWidgets.QAction, QtWidgets.QActionGroup]]:
        """
        Returns the list of QAction.
        """
        return self._actionList

    def addAction(
        self,
        action: Union[QtWidgets.QAction, QtWidgets.QActionGroup],
    ) -> Union[QtWidgets.QAction, QtWidgets.QActionGroup]:
        """
        Add a QAction or a QActionGroup to the set.
        """
        if isEmpty(action.objectName()):
            raise ValueError("missing objectName in %s" % action.__class__.__name__)
        if action.objectName() in self._actionDict:
            raise ValueError("duplicate action found: %s" % action.objectName())
        self._actionList.append(action)
        self._actionDict[action.objectName()] = action
        return action

    def addActions(
        self,
        actions: Iterable[Union[QtWidgets.QAction, QtWidgets.QActionGroup]],
    ) -> None:
        """
        Add the given group of QAction or a QActionGroup to the set.
        """
        for action in actions:
            self.addAction(action)

    def clearActions(self) -> None:
        """
        Remove all the actions.
        """
        self._actionDict.clear()
        self._actionList.clear()

    def insertAction(
        self,
        action: Union[QtWidgets.QAction, QtWidgets.QActionGroup],
        before: Union[QtWidgets.QAction, QtWidgets.QActionGroup],
    ) -> Union[QtWidgets.QAction, QtWidgets.QActionGroup]:
        """
        Insert the given QAction or QActionGroup before the given one.
        """
        if isEmpty(action.objectName()):
            raise ValueError("missing objectName in %s" % action.__class__.__name__)
        if action.objectName() in self._actionDict:
            raise ValueError("duplicate action found: %s" % action.objectName())
        self._actionList.insert(self._actionList.index(before), action)
        self._actionDict[action.objectName()] = action
        return action

    def insertActions(
        self,
        actions: Iterable[Union[QtWidgets.QAction, QtWidgets.QActionGroup]],
        before: Union[QtWidgets.QAction, QtWidgets.QActionGroup],
    ) -> None:
        """
        Insert the given group of QAction or QActionGroup before the given one.
        """
        for action in actions:
            self.insertAction(action, before)

    def removeAction(
        self,
        action: Union[QtWidgets.QAction, QtWidgets.QActionGroup],
    ) -> Union[QtWidgets.QAction, QtWidgets.QActionGroup]:
        """
        Removes the given QAction or QActionGroup from the set.
        """
        self._actionList.remove(action)
        del self._actionDict[action.objectName()]
        return action


class HasMenuSystem(object):
    """
    Mixin which adds the ability to store and retrieve menus.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._menuDict = {}  # type: Dict[str, QtWidgets.QMenu]
        self._menuList = []  # type: List[QtWidgets.QMenu]

    def addMenu(self, menu: QtWidgets.QMenu) -> QtWidgets.QMenu:
        """
        Add a QMenu to the set.
        """
        if isEmpty(menu.objectName()):
            raise ValueError("missing objectName in %s" % menu.__class__.__name__)
        if menu.objectName() in self._menuDict:
            raise ValueError("duplicate menu found: %s" % menu.objectName())
        self._menuList.append(menu)
        self._menuDict[menu.objectName()] = menu
        return menu

    def addMenus(self, menus: Iterable[QtWidgets.QMenu]) -> None:
        """
        Add the given group of QMenu to the set.
        """
        for menu in menus:
            self.addMenu(menu)

    def clearMenus(self) -> None:
        """
        Remove all the menus.
        """
        self._menuDict.clear()
        self._menuList.clear()

    def insertMenu(
        self,
        menu: QtWidgets.QMenu,
        before: QtWidgets.QMenu,
    ) -> QtWidgets.QMenu:
        """
        Insert the given QMenu before the given one.
        """
        if isEmpty(menu.objectName()):
            raise ValueError("missing objectName in %s" % menu.__class__.__name__)
        if menu.objectName() in self._menuDict:
            raise ValueError("duplicate menu found: %s" % menu.objectName())
        self._menuList.insert(self._menuList.index(before), menu)
        self._menuDict[menu.objectName()] = menu
        return menu

    def insertMenus(
        self,
        menus: Iterable[QtWidgets.QMenu],
        before: QtWidgets.QMenu,
    ) -> None:
        """
        Insert the given group of QMenu before the given one.
        """
        for menu in menus:
            self.insertMenu(menu, before)

    def menu(self, objectName: str) -> QtWidgets.QMenu:
        """
        Returns the reference to a QMenu given it's objectName.
        """
        return self._menuDict.get(objectName, None)

    def menus(self) -> List[QtWidgets.QMenu]:
        """
        Returns the list of QMenu.
        """
        return self._menuList

    def removeMenu(self, menu: QtWidgets.QMenu) -> QtWidgets.QMenu:
        """
        Removes the given QMenu from the set.
        """
        self._menuList.remove(menu)
        del self._menuDict[menu.objectName()]
        return menu


class HasPluginSystem(object):
    """
    Mixin which adds the ability to store and retrieve plugins.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._pluginDict = {}  # type: Dict[str, AbstractPlugin]
        self._pluginList = []  # type: List[AbstractPlugin]

    def addPlugin(self, plugin: AbstractPlugin) -> AbstractPlugin:
        """
        Add a plugin to the set.
        """
        if isEmpty(plugin.objectName()):
            raise ValueError("missing objectName in %s" % plugin.__class__.__name__)
        if plugin.objectName() in self._pluginDict:
            raise ValueError("duplicate plugin found: %s" % plugin.objectName())

        self._pluginList.append(plugin)
        self._pluginDict[plugin.objectName()] = plugin
        return plugin

    def addPlugins(self, plugins: Iterable[AbstractPlugin]) -> None:
        """
        Add the given group of plugins to the set.
        """
        for plugin in plugins:
            self.addPlugin(plugin)

    def clearPlugins(self) -> None:
        """
        Remove all the plugins.
        """
        self._pluginDict.clear()
        self._pluginList.clear()

    def insertPlugin(
        self,
        plugin: AbstractPlugin,
        before: AbstractPlugin,
    ) -> AbstractPlugin:
        """
        Insert the given plugin before the given one.
        """
        if isEmpty(plugin.objectName()):
            raise ValueError("missing objectName in %s" % plugin.__class__.__name__)
        if plugin.objectName() in self._pluginDict:
            raise ValueError("duplicate plugin found: %s" % plugin.objectName())
        self._pluginList.insert(self._pluginList.index(before), plugin)
        self._pluginDict[plugin.objectName()] = plugin
        return plugin

    def insertPlugins(
        self,
        plugins: Iterable[AbstractPlugin],
        before: AbstractPlugin,
    ) -> None:
        """
        Insert the given group of plugins before the given one.
        """
        for plugin in plugins:
            self.insertPlugin(plugin, before)

    def plugin(self, objectName: str) -> AbstractPlugin:
        """
        Returns the reference to a plugin given it's objectName.
        """
        return self._pluginDict.get(objectName, None)

    def plugins(self) -> List[AbstractPlugin]:
        """
        Returns the list of plugins.
        """
        return self._pluginList

    def removePlugin(self, plugin: AbstractPlugin) -> AbstractPlugin:
        """
        Removes the given plugin from the set.
        """
        self._pluginList.remove(plugin)
        del self._pluginDict[plugin.objectName()]
        return plugin


class HasShortcutSystem(object):
    """
    Mixin which adds the ability to store and retrieve keyboard shortcuts.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._shortcutDict = {}  # type: Dict[str, QtWidgets.QShortcut]
        self._shortcutKeys = {}  # type: Dict[Union[QtGui.QKeySequence, str], QtWidgets.QShortcut]

    def shortcut(self, nameOrKey: Union[QtGui.QKeySequence, str]) -> QtWidgets.QShortcut:
        """
        Returns the reference to a QShortcut given it's objectName or QKeySequence.
        """
        if isinstance(nameOrKey, QtGui.QKeySequence):
            return self._shortcutKeys.get(nameOrKey, None)
        else:
            return self._shortcutDict.get(nameOrKey, None)

    def shortcuts(self) -> List[QtWidgets.QShortcut]:
        """
        Returns the list of QShortcut.
        """
        return list(self._shortcutDict.values())

    def addShortcut(self, shortcut: QtWidgets.QShortcut) -> QtWidgets.QShortcut:
        """
        Add a QShortcut to the set.
        """
        if isEmpty(shortcut.objectName()):
            raise ValueError("missing objectName in %s" % shortcut.__class__.__name__)
        if shortcut.objectName() in self._shortcutDict:
            raise ValueError("duplicate shortcut name found: %s" % shortcut.objectName())
        if shortcut.key() in self._shortcutKeys:
            raise ValueError("duplicate shortcut sequence found: %s" % shortcut.key().toString())
        self._shortcutKeys[shortcut.key()] = shortcut
        self._shortcutDict[shortcut.objectName()] = shortcut
        return shortcut

    def addShortcuts(self, shortcuts: Iterable[QtWidgets.QShortcut]) -> None:
        """
        Add the given list of QShortcut to the set.
        """
        for shortcut in shortcuts:
            self.addShortcut(shortcut)

    def clearShortcuts(self) -> None:
        """
        Remove all the shortcuts.
        """
        self._shortcutDict.clear()
        self._shortcutKeys.clear()

    def removeShortcut(self, shortcut: QtWidgets.QShortcut) -> QtWidgets.QShortcut:
        """
        Removes the given QShortcut from the set.
        """
        del self._shortcutKeys[shortcut.key()]
        del self._shortcutDict[shortcut.objectName()]
        return shortcut


class HasWidgetSystem(object):
    """
    Mixin which adds the ability to store and retrieve widgets.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._widgetDict = {}  # type: Dict[str, QtWidgets.QWidget]
        self._widgetList = []  # type: List[QtWidgets.QWidget]

    def addWidget(self, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        """
        Add a QWidget to the set.
        """
        if isEmpty(widget.objectName()):
            raise ValueError("missing objectName in %s" % widget.__class__.__name__)
        if widget.objectName() in self._widgetDict:
            raise ValueError("duplicate widget found: %s" % widget.objectName())
        self._widgetList.append(widget)
        self._widgetDict[widget.objectName()] = widget
        return widget

    def addWidgets(self, widgets: Iterable[QtWidgets.QWidget]) -> None:
        """
        Add the given group of QWidget to the set.
        """
        for widget in widgets:
            self.addWidget(widget)

    def clearWidgets(self) -> None:
        """
        Remove all the widgets.
        """
        self._widgetDict.clear()
        self._widgetList.clear()

    def insertWidget(
        self,
        widget: QtWidgets.QWidget,
        before: QtWidgets.QWidget,
    ) -> QtWidgets.QWidget:
        """
        Insert the given QWidget before the given one.
        """
        if isEmpty(widget.objectName()):
            raise ValueError("missing objectName in %s" % widget.__class__.__name__)
        if widget.objectName() in self._widgetDict:
            raise ValueError("duplicate widget found: %s" % widget.objectName())
        self._widgetList.insert(self._widgetList.index(before), widget)
        self._widgetDict[widget.objectName()] = widget
        return widget

    def insertWidgets(
        self,
        widgets: Iterable[QtWidgets.QWidget],
        before: QtWidgets.QWidget,
    ) -> None:
        """
        Insert the given group of QWidget before the given one.
        """
        for widget in widgets:
            self.insertWidget(widget, before)

    def widget(self, objectName: str) -> QtWidgets.QWidget:
        """
        Returns the reference to a QWidget given it's objectName.
        """
        return self._widgetDict.get(objectName, None)

    def widgets(self) -> List[QtWidgets.QWidget]:
        """
        Returns the list of QWidget.
        """
        return self._widgetList

    def removeWidget(self, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        """
        Removes the given QWidget from the set.
        """
        self._widgetList.remove(widget)
        del self._widgetDict[widget.objectName()]
        return widget


class HasDiagramExportSystem(object):
    """
    Mixin which adds the ability to store and retrieve Diagram exporters.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._diagramExporterDict = {}  # type: Dict[File, Type[AbstractDiagramExporter]]
        self._diagramExporterList = []  # type: List[Type[AbstractDiagramExporter]]

    def addDiagramExporter(self, exporter: Type[AbstractDiagramExporter]) -> None:
        """
        Add a diagram exporter class to the set.
        """
        if not issubclass(exporter, AbstractDiagramExporter):
            raise ValueError("diagram exporter must be subclass of "
                             "eddy.core.exporters.common.AbstractDiagramExporter")
        filetype = exporter.filetype()
        if filetype in self._diagramExporterDict:
            raise ValueError("duplicate diagram exporter found for filetype %s" % filetype.value)
        self._diagramExporterList.append(exporter)
        self._diagramExporterDict[filetype] = exporter

    def addDiagramExporters(self, exporters: Iterable[Type[AbstractDiagramExporter]]) -> None:
        """
        Add the given group of diagram exporter classes to the set.
        """
        for exporter in exporters:
            self.addDiagramExporter(exporter)

    def clearDiagramExporters(self) -> None:
        """
        Remove all the diagram exporters.
        """
        self._diagramExporterDict.clear()
        self._diagramExporterList.clear()

    def createDiagramExporter(
        self,
        filetype: File,
        diagram: Diagram,
        session: Session = None,
    ) -> AbstractDiagramExporter:
        """
        Creates an instance of a diagram exporter for the given filetype.
        """
        exporter = self.diagramExporter(filetype)
        if not exporter:
            raise ValueError("missing diagram exporter for filetype %s" % filetype.value)
        return exporter(diagram, session)

    def diagramExporter(self, filetype: File) -> Type[AbstractDiagramExporter]:
        """
        Returns the reference to a diagram exporter class given a filetype.
        """
        return self._diagramExporterDict.get(filetype, None)

    def diagramExporterNameFilters(self, exclude: Iterable[File] = None) -> List[str]:
        """
        Returns the list of diagram exporter name filters.
        """
        collection = [x.filetype() for x in self.diagramExporters(exclude)]
        collection = [x.value for x in collection]
        return collection

    def diagramExporters(
        self,
        exclude: Iterable[File] = None,
    ) -> List[Type[AbstractDiagramExporter]]:
        """
        Returns the list of diagram exporter classes.
        """
        collection = self._diagramExporterList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def insertDiagramExporter(
        self,
        exporter: Type[AbstractDiagramExporter],
        before: Type[AbstractDiagramExporter],
    ) -> None:
        """
        Insert the given diagram exporter class before the given one.
        """
        if not issubclass(exporter, AbstractDiagramExporter):
            raise ValueError("diagram exporter must be subclass of "
                             "eddy.core.exporters.common.AbstractDiagramExporter")
        filetype1 = exporter.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._diagramExporterDict:
            raise ValueError("duplicate diagram exporter found for filetype %s" % filetype1.value)
        self._diagramExporterList.insert(self._diagramExporterList.index(before), exporter)
        self._diagramExporterDict[filetype1] = exporter

    def insertDiagramExporters(
        self,
        exporters: Iterable[Type[AbstractDiagramExporter]],
        before: Type[AbstractDiagramExporter],
    ) -> None:
        """
        Insert the given group of diagram exporter classes before the given one.
        """
        for exporter in exporters:
            self.insertDiagramExporter(exporter, before)

    def removeDiagramExporter(
        self,
        exporter: Type[AbstractDiagramExporter],
    ) -> Type[AbstractDiagramExporter]:
        """
        Removes the given diagram exporter class from the set.
        """
        exporter = self._diagramExporterDict.pop(exporter.filetype())
        self._diagramExporterList.remove(exporter)
        return exporter


class HasOntologyExportSystem(object):
    """
    Mixin which adds the ability to store and retrieve Ontology exporters.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._ontologyExporterDict = {}  # type: Dict[File, Type[AbstractOntologyExporter]]
        self._ontologyExporterList = []  # type: List[Type[AbstractOntologyExporter]]

    def addOntologyExporter(self, exporter: Type[AbstractOntologyExporter]) -> None:
        """
        Add an ontology exporter class to the set.
        """
        if not issubclass(exporter, AbstractOntologyExporter):
            raise ValueError("ontology exporter must be subclass of "
                             "eddy.core.exporters.common.AbstractOntologyExporter")
        filetype = exporter.filetype()
        if filetype in self._ontologyExporterDict:
            raise ValueError("duplicate ontology exporter found for filetype %s" % filetype.value)
        self._ontologyExporterList.append(exporter)
        self._ontologyExporterDict[filetype] = exporter

    def addOntologyExporters(self, exporters: Iterable[Type[AbstractOntologyExporter]]) -> None:
        """
        Add the given group of ontology exporter classes to the set.
        """
        for exporter in exporters:
            self.addOntologyExporter(exporter)

    def clearOntologyExporters(self) -> None:
        """
        Remove all the ontology exporters.
        """
        self._ontologyExporterDict.clear()
        self._ontologyExporterList.clear()

    def createOntologyExporter(
        self,
        filetype: File,
        project: Project,
        session: Session = None,
    ) -> AbstractOntologyExporter:
        """
        Creates an instance of an ontology exporter for the given filetype.
        """
        exporter = self.ontologyExporter(filetype)
        if not exporter:
            raise ValueError("missing ontology exporter for filetype %s" % filetype.value)
        return exporter(project, session)

    def insertOntologyExporter(
        self,
        exporter: Type[AbstractOntologyExporter],
        before: Type[AbstractOntologyExporter],
    ) -> None:
        """
        Insert the given ontology exporter class before the given one.
        """
        if not issubclass(exporter, AbstractOntologyExporter):
            raise ValueError("ontology exporter must be subclass of "
                             "eddy.core.exporters.common.AbstractOntologyExporter")
        filetype1 = exporter.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._ontologyExporterDict:
            raise ValueError("duplicate ontology exporter found for filetype %s" % filetype1.value)
        self._ontologyExporterList.insert(self._ontologyExporterList.index(before), exporter)
        self._ontologyExporterDict[filetype1] = exporter

    def insertOntologyExporters(
        self,
        exporters: Iterable[Type[AbstractOntologyExporter]],
        before: Type[AbstractOntologyExporter],
    ) -> None:
        """
        Insert the given group of ontology exporter classes before the given one.
        """
        for exporter in exporters:
            self.insertOntologyExporter(exporter, before)

    def ontologyExporter(self, filetype: File) -> Type[AbstractOntologyExporter]:
        """
        Returns the reference to a ontology exporter class given a filetype.
        """
        return self._ontologyExporterDict.get(filetype, None)

    def ontologyExporterNameFilters(self, exclude: Iterable[File] = None) -> List[str]:
        """
        Returns the list of ontology exporter name filters.
        """
        collection = [x.filetype() for x in self.ontologyExporters(exclude)]
        collection = [x.value for x in collection]
        return collection

    def ontologyExporters(
        self,
        exclude: Iterable[File] = None,
    ) -> List[Type[AbstractOntologyExporter]]:
        """
        Returns the list of ontology exporter classes.
        """
        collection = self._ontologyExporterList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def removeOntologyExporter(
        self,
        exporter: Type[AbstractOntologyExporter],
    ) -> Type[AbstractOntologyExporter]:
        """
        Removes the given ontology exporter class from the set.
        """
        exporter = self._ontologyExporterDict.pop(exporter.filetype())
        self._ontologyExporterList.remove(exporter)
        return exporter


class HasProjectExportSystem(object):
    """
    Mixin which adds the ability to store and retrieve Project exporters.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._projectExporterDict = {}  # type: Dict[File, Type[AbstractProjectExporter]]
        self._projectExporterList = []  # type: List[Type[AbstractProjectExporter]]

    def addProjectExporter(self, exporter: Type[AbstractProjectExporter]) -> None:
        """
        Add a project exporter class to the set.
        """
        if not issubclass(exporter, AbstractProjectExporter):
            raise ValueError("project exporter must be subclass of "
                             "eddy.core.exporters.common.AbstractProjectExporter")
        filetype = exporter.filetype()
        if filetype in self._projectExporterDict:
            raise ValueError("duplicate project exporter found for filetype %s" % filetype.value)
        self._projectExporterList.append(exporter)
        self._projectExporterDict[filetype] = exporter

    def addProjectExporters(self, exporters: Iterable[Type[AbstractProjectExporter]]) -> None:
        """
        Add the given group of project exporter classes to the set.
        """
        for exporter in exporters:
            self.addProjectExporter(exporter)

    def clearProjectExporters(self) -> None:
        """
        Remove all the project exporters.
        """
        self._projectExporterDict.clear()
        self._projectExporterList.clear()

    def createProjectExporter(
        self,
        filetype: File,
        project: Project,
        session: Session = None,
        # FIXME: Remove next two parameters, they are not part of the generic API
        exportPath: str = None,
        selectDiagrams: bool = False,
    ) -> AbstractProjectExporter:
        """
        Creates an instance of a project exporter for the given filetype.
        """
        exporter = self.projectExporter(filetype)
        if not exporter:
            raise ValueError("missing project exporter for filetype %s" % filetype.value)
        return exporter(project, session, exportPath=exportPath,selectDiagrams=selectDiagrams)

    def insertProjectExporter(
        self,
        exporter: Type[AbstractProjectExporter],
        before: Type[AbstractProjectExporter],
    ) -> None:
        """
        Insert the given project exporter class before the given one.
        """
        if not issubclass(exporter, AbstractProjectExporter):
            raise ValueError("project exporter must be subclass of "
                             "eddy.core.exporters.common.AbstractProjectExporter")
        filetype1 = exporter.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._projectExporterDict:
            raise ValueError("duplicate project exporter found for filetype %s" % filetype1.value)
        self._projectExporterList.insert(self._projectExporterList.index(before), exporter)
        self._projectExporterDict[filetype1] = exporter

    def insertProjectExporters(
        self,
        exporters: Iterable[Type[AbstractProjectExporter]],
        before: Type[AbstractProjectExporter],
    ) -> None:
        """
        Insert the given group of project exporter classes before the given one.
        """
        for exporter in exporters:
            self.insertProjectExporter(exporter, before)

    def projectExporter(self, filetype: File) -> Type[AbstractProjectExporter]:
        """
        Returns the reference to a project exporter class given a filetype.
        """
        return self._projectExporterDict.get(filetype, None)

    def projectExporterNameFilters(self, exclude: Iterable[File] = None) -> List[str]:
        """
        Returns the list of project exporter name filters.
        """
        collection = [x.filetype() for x in self.projectExporters(exclude)]
        collection = [x.value for x in collection]
        return collection

    def projectExporters(
        self,
        exclude: Iterable[File] = None,
    ) -> List[Type[AbstractProjectExporter]]:
        """
        Returns the list of project exporter classes.
        """
        collection = self._projectExporterList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def removeProjectExporter(
        self,
        exporter: Type[AbstractProjectExporter],
    ) -> Type[AbstractProjectExporter]:
        """
        Removes the given project exporter class from the set.
        """
        exporter = self._projectExporterDict.pop(exporter.filetype())
        self._projectExporterList.remove(exporter)
        return exporter


class HasDiagramLoadSystem(object):
    """
    Mixin which adds the ability to store and retrieve Diagram loaders.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._diagramLoaderDict = {}  # type: Dict[File, Type[AbstractDiagramLoader]]
        self._diagramLoaderList = []  # type: List[Type[AbstractDiagramLoader]]

    def addDiagramLoader(self, loader: Type[AbstractDiagramLoader]) -> None:
        """
        Add a diagram loader class to the set.
        """
        if not issubclass(loader, AbstractDiagramLoader):
            raise ValueError("diagram loader must be subclass of "
                             "eddy.core.loaders.common.AbstractDiagramLoader")
        filetype = loader.filetype()
        if filetype in self._diagramLoaderDict:
            raise ValueError("duplicate diagram loader found for filetype %s" % filetype.value)
        self._diagramLoaderList.append(loader)
        self._diagramLoaderDict[filetype] = loader

    def addDiagramLoaders(self, loaders: Iterable[Type[AbstractDiagramLoader]]) -> None:
        """
        Add the given group of diagram loader classes to the set.
        """
        for loader in loaders:
            self.addDiagramLoader(loader)

    def clearDiagramLoaders(self) -> None:
        """
        Remove all the diagram loaders.
        """
        self._diagramLoaderDict.clear()
        self._diagramLoaderList.clear()

    def createDiagramLoader(
        self,
        filetype: File,
        path: str,
        project: Project,
        session: Session = None,
    ) -> AbstractDiagramLoader:
        """
        Creates an instance of a diagram loader for the given filetype.
        """
        loader = self.diagramLoader(filetype)
        if not loader:
            raise ValueError("missing diagram loader for filetype %s" % filetype.value)
        return loader(path, project, session)

    def diagramLoader(self, filetype: File) -> Type[AbstractDiagramLoader]:
        """
        Returns the reference to a diagram loader class given a filetype.
        """
        return self._diagramLoaderDict.get(filetype, None)

    def diagramLoaderNameFilters(self, exclude: Iterable[File] = None) -> List[str]:
        """
        Returns the list of diagram loader name filters.
        """
        collection = [x.filetype() for x in self.diagramLoaders(exclude)]
        collection = [x.value for x in collection]
        return collection

    def diagramLoaders(
        self,
        exclude: Iterable[File] = None,
    ) -> List[Type[AbstractDiagramLoader]]:
        """
        Returns the list of diagram loader classes.
        """
        collection = self._diagramLoaderList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def insertDiagramLoader(
        self,
        loader: Type[AbstractDiagramLoader],
        before: Type[AbstractDiagramLoader],
    ) -> None:
        """
        Insert the given diagram loader class before the given one.
        """
        if not issubclass(loader, AbstractDiagramLoader):
            raise ValueError("diagram loader must be subclass of "
                             "eddy.core.loaders.common.AbstractDiagramLoader")
        filetype1 = loader.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._diagramLoaderDict:
            raise ValueError("duplicate diagram loader found for filetype %s" % filetype1.value)
        self._diagramLoaderList.insert(self._diagramLoaderList.index(before), loader)
        self._diagramLoaderDict[filetype1] = loader

    def insertDiagramLoaders(
        self,
        loaders: Iterable[Type[AbstractDiagramLoader]],
        before: Type[AbstractDiagramLoader],
    ) -> None:
        """
        Insert the given group of diagram loader classes before the given one.
        """
        for loader in loaders:
            self.insertDiagramLoader(loader, before)

    def removeDiagramLoader(
        self,
        loader: Type[AbstractDiagramLoader],
    ) -> Type[AbstractDiagramLoader]:
        """
        Removes the given diagram loader class from the set.
        """
        loader = self._diagramLoaderDict.pop(loader.filetype())
        self._diagramLoaderList.remove(loader)
        return loader


class HasOntologyLoadSystem(object):
    """
    Mixin which adds the ability to store and retrieve Ontology loaders.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._ontologyLoaderDict = {}  # type: Dict[File, Type[AbstractOntologyLoader]]
        self._ontologyLoaderList = []  # type: List[Type[AbstractOntologyLoader]]

    def addOntologyLoader(self, loader: Type[AbstractOntologyLoader]) -> None:
        """
        Add a ontology loader class to the set.
        """
        if not issubclass(loader, AbstractOntologyLoader):
            raise ValueError("ontology loader must be subclass of "
                             "eddy.core.loaders.common.AbstractOntologyLoader")
        filetype = loader.filetype()
        if filetype in self._ontologyLoaderDict:
            raise ValueError("duplicate ontology loader found for filetype %s" % filetype.value)
        self._ontologyLoaderList.append(loader)
        self._ontologyLoaderDict[filetype] = loader

    def addOntologyLoaders(self, loaders: Iterable[Type[AbstractOntologyLoader]]) -> None:
        """
        Add the given group of ontology loader classes to the set.
        """
        for loader in loaders:
            self.addOntologyLoader(loader)

    def clearOntologyLoaders(self) -> None:
        """
        Remove all the ontology loaders.
        """
        self._ontologyLoaderDict.clear()
        self._ontologyLoaderList.clear()

    def createOntologyLoader(
        self,
        filetype: File,
        path: str,
        project: Project,
        session: Session = None,
    ) -> AbstractOntologyLoader:
        """
        Creates an instance of a ontology loader for the given filetype.
        """
        loader = self.ontologyLoader(filetype)
        if not loader:
            raise ValueError("missing ontology loader for filetype %s" % filetype.value)
        return loader(path, project, session)

    def ontologyLoader(self, filetype: File) -> Type[AbstractOntologyLoader]:
        """
        Returns the reference to a ontology loader class given a filetype.
        """
        return self._ontologyLoaderDict.get(filetype, None)

    def ontologyLoaderNameFilters(self, exclude: Iterable[File] = None) -> List[str]:
        """
        Returns the list of ontology loader name filters.
        """
        collection = [x.filetype() for x in self.ontologyLoaders(exclude)]
        collection = [x.value for x in collection]
        return collection

    def ontologyLoaders(
        self,
        exclude: Iterable[File] = None,
    ) -> List[Type[AbstractOntologyLoader]]:
        """
        Returns the list of ontology loader classes.
        """
        collection = self._ontologyLoaderList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def insertOntologyLoader(
        self,
        loader: Type[AbstractOntologyLoader],
        before: Type[AbstractOntologyLoader],
    ) -> None:
        """
        Insert the given ontology loader class before the given one.
        """
        if not issubclass(loader, AbstractOntologyLoader):
            raise ValueError("ontology loader must be subclass of "
                             "eddy.core.loaders.common.AbstractOntologyLoader")
        filetype1 = loader.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._ontologyLoaderDict:
            raise ValueError("duplicate ontology loader found for filetype %s" % filetype1.value)
        self._ontologyLoaderList.insert(self._ontologyLoaderList.index(before), loader)
        self._ontologyLoaderDict[filetype1] = loader

    def insertOntologyLoaders(
        self,
        loaders: Iterable[Type[AbstractOntologyLoader]],
        before: Type[AbstractOntologyLoader],
    ) -> None:
        """
        Insert the given group of ontology loader classes before the given one.
        """
        for loader in loaders:
            self.insertOntologyLoader(loader, before)

    def removeOntologyLoader(
        self,
        loader: Type[AbstractOntologyLoader],
    ) -> Type[AbstractOntologyLoader]:
        """
        Removes the given ontology loader class from the set.
        """
        loader = self._ontologyLoaderDict.pop(loader.filetype())
        self._ontologyLoaderList.remove(loader)
        return loader


class HasProjectLoadSystem(object):
    """
    Mixin which adds the ability to store and retrieve Project loaders.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._projectLoaderDict = {}  # type: Dict[File, Type[AbstractProjectLoader]]
        self._projectLoaderList = []  # type: List[Type[AbstractProjectLoader]]

    def addProjectLoader(self, loader: Type[AbstractProjectLoader]) -> None:
        """
        Add a project loader class to the set.
        """
        if not issubclass(loader, AbstractProjectLoader):
            raise ValueError("project loader must be subclass of "
                             "eddy.core.loaders.common.AbstractProjectLoader")
        filetype = loader.filetype()
        if filetype in self._projectLoaderDict:
            raise ValueError("duplicate project loader found for filetype %s" % filetype.value)
        self._projectLoaderList.append(loader)
        self._projectLoaderDict[filetype] = loader

    def addProjectLoaders(self, loaders: Iterable[Type[AbstractProjectLoader]]) -> None:
        """
        Add the given group of project loader classes to the set.
        """
        for loader in loaders:
            self.addProjectLoader(loader)

    def clearProjectLoaders(self) -> None:
        """
        Remove all the project loaders.
        """
        self._projectLoaderDict.clear()
        self._projectLoaderList.clear()

    def createProjectLoader(
        self,
        filetype: File,
        path: str,
        session: Session = None,
    ) -> AbstractProjectLoader:
        """
        Creates an instance of a diagram loader for the given filetype.
        """
        loader = self.projectLoader(filetype)
        if not loader:
            raise ValueError("missing project loader for filetype %s" % filetype.value)
        return loader(path, session)

    def insertProjectLoader(
        self,
        loader: Type[AbstractProjectLoader],
        before: Type[AbstractProjectLoader],
    ) -> None:
        """
        Insert the given project loader class before the given one.
        """
        if not issubclass(loader, AbstractProjectLoader):
            raise ValueError("project loader must be subclass of "
                             "eddy.core.loaders.common.AbstractProjectLoader")
        filetype1 = loader.filetype()
        # filetype2 = before.filetype()
        if filetype1 in self._projectLoaderDict:
            raise ValueError("duplicate project loader found for filetype %s" % filetype1.value)
        self._projectLoaderList.insert(self._projectLoaderList.index(before), loader)
        self._projectLoaderDict[filetype1] = loader

    def insertProjectLoaders(
        self,
        loaders: Iterable[Type[AbstractProjectLoader]],
        before: Type[AbstractProjectLoader],
    ) -> None:
        """
        Insert the given group of project loader classes before the given one.
        """
        for loader in loaders:
            self.insertProjectLoader(loader, before)

    def projectLoader(self, filetype: File) -> Type[AbstractProjectLoader]:
        """
        Returns the reference to a project loader class given a filetype.
        """
        return self._projectLoaderDict.get(filetype, None)

    def projectLoaderNameFilters(self, exclude: Iterable[File] = None) -> List[str]:
        """
        Returns the list of project loader name filters.
        """
        collection = [x.filetype() for x in self.projectLoaders(exclude)]
        collection = [x.value for x in collection]
        return collection

    def projectLoaders(self, exclude: Iterable[File] = None) -> List[Type[AbstractProjectLoader]]:
        """
        Returns the list of project loader classes.
        """
        collection = self._projectLoaderList
        if exclude:
            collection = [x for x in collection if x.filetype() not in exclude]
        return sorted(collection, key=lambda x: x.filetype())

    def removeProjectLoader(
        self,
        loader: Type[AbstractProjectLoader],
    ) -> Type[AbstractProjectLoader]:
        """
        Removes the given project loader class from the set.
        """
        loader = self._projectLoaderDict.pop(loader.filetype())
        self._projectLoaderList.remove(loader)
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
        profile = self.profile(OWLProfile.valueOf(name_or_type))
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
        return self._profileDict.get(OWLProfile.valueOf(name_or_type), None)

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
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._threads = {}  # type: Dict[str, QtCore.QThread]
        self._started = {}  # type: Dict[str, float]
        self._workers = {}  # type: Dict[str, AbstractWorker]

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onQThreadFinished(self) -> None:
        """
        Executed when a QThread finish it's job.
        """
        self.stopThread(self.sender())

    #############################################
    #   INTERFACE
    #################################

    def startThread(self, name: str, worker: AbstractWorker) -> None:
        """
        Start a thread using the given worker.
        """
        if not isinstance(worker, AbstractWorker):
            raise ValueError('[THREADS] worker class must be subclass of '
                             'eddy.core.threading.AbstractWorker')
        if name not in self._threads and name not in self._workers:
            LOGGER.debug("[THREADS] Requested threaded execution of worker instance: %s",
                         worker.__class__.__name__)
            # START THE WORKER THREAD
            qthread = QtCore.QThread()
            qthread.setObjectName(name)
            LOGGER.debug("[THREADS] Moving worker '%s' in a new thread '%s'",
                         worker.__class__.__name__, name)
            worker.moveToThread(qthread)
            connect(qthread.finished, self.onQThreadFinished)
            connect(qthread.finished, qthread.deleteLater)
            connect(worker.finished, qthread.quit)
            connect(worker.finished, worker.deleteLater)
            connect(qthread.started, worker.run)
            LOGGER.debug("[THREADS] Starting thread: %s", name)
            qthread.start()
            # STORE LOCALLY
            self._started[name] = time.monotonic()
            self._threads[name] = qthread
            self._workers[name] = worker

    def stopRunningThreads(self) -> None:
        """
        Stops all the running threads.
        """
        LOGGER.debug('[THREADS] Terminating running thread(s)...')
        for name in [name for name in self._threads.keys()]:
            self.stopThread(name)

    def stopThread(self, name_or_qthread: Union[QtCore.QThread, str]) -> None:
        """
        Stop a running thread.
        """
        if name_or_qthread:
            name = name_or_qthread
            if not isinstance(name, str):
                name = name_or_qthread.objectName()
            if name in self._threads:
                try:
                    LOGGER.debug("[THREADS] Terminate thread: %s (runtime=%.2fms)",
                                 name, time.monotonic() - self._started[name])
                    qthread = self._threads[name]
                    qthread.quit()
                    if not qthread.wait(2000):
                        qthread.terminate()
                        qthread.wait()
                except Exception as e:
                    LOGGER.exception('[THREADS] Thread shutdown could not be completed: %s', e)
                del self._threads[name]
            if name in self._workers:
                del self._workers[name]
            if name in self._started:
                del self._started[name]

    def thread(self, name: str) -> QtCore.QThread:
        """
        Returns the reference to a running QThread.
        """
        return self._threads.get(name, None)

    def threads(self) -> List[Tuple[str, QtCore.QThread]]:
        """
        Returns a list of QThread instances in the form (name, QThread).
        """
        return [(name, qthread) for name, qthread in self._threads.items()]

    def worker(self, name: str) -> AbstractWorker:
        """
        Returns the reference to a worker which is running in a QThread.
        """
        return self._workers.get(name, None)

    def workers(self) -> List[Tuple[str, AbstractWorker]]:
        """
        Returns a list of AbstractWorker instances in the form (name, AbstractWorker).
        """
        return [(name, worker) for name, worker in self._workers.items()]


class HasNotificationSystem(object):
    """
    Mixin which adds the ability to display notification popups.
    """
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)
        self._popupList = [Notification(self, i) for i in range(0, 8)]

    def addNotification(self, message: str) -> None:
        """
        Add a notification popup.
        """
        for popup in self._popupList:
            if not popup.isVisible():
                popup.setText(message)
                popup.show()
                break
        else:
            LOGGER.warning('Missed notification (%s): no free notification popup available', message)

    def hideNotifications(self) -> None:
        """
        Make sure to dismiss all the notification popups.
        """
        for popup in self._popupList:
            popup.dismiss()
