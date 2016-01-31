import os
import jnius_config

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from eddy.core.functions.system import expandPath

########################################################
##         BEGIN JAVA VIRTUAL MACHINE SETUP           ##
########################################################

os.environ['JAVA_HOME'] = expandPath('@resources/java/')

classpath = []
resources = expandPath('@resources/lib/')
for name in os.listdir(resources):
    path = os.path.join(resources, name)
    if os.path.isfile(path):
        classpath.append(path)

jnius_config.add_options('-ea', '-Xmx512m')
jnius_config.set_classpath(*classpath)

########################################################
##          END JAVA VIRTUAL MACHINE SETUP            ##
########################################################

from eddy.ui.mainwindow import MainWindow
from eddy.ui.styles import Style


class Eddy(QApplication):
    """
    This class implements the main Qt application.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize Eddy.
        """
        super().__init__(*args, **kwargs)
        self.settings = QSettings(expandPath('@home/Eddy.ini'), QSettings.IniFormat)

    def init(self):
        """
        Run initialization tasks for Eddy.
        :raise JVMNotFoundException: if the JVM could not be found on the system.
        :raise JVMNotSupportedException: if the JVM found in the system is not supported.
        :rtype: MainWindow
        """
        ######################################
        ## SETUP LAYOUT
        ######################################

        style = Style.forName(self.settings.value('appearance/style', 'light', str))

        self.setStyle(style)
        self.setStyleSheet(style.qss())

        ######################################
        ## INITIALIZE RECENT DOCUMENTS
        ######################################

        if not self.settings.contains('document/recent_documents'):
            # From PyQt5 documentation: if the value of the setting is a container (corresponding to either
            # QVariantList, QVariantMap or QVariantHash) then the type is applied to the contents of the
            # container. So according to this we can't use an empty list as default value because PyQt5 needs
            # to know the type of the contents added to the collection: we avoid this problem by placing
            # the list of examples file in the recentDocumentList (only if there is no list defined already).
            self.settings.setValue('document/recent_documents', [
                expandPath('@examples/Animals.graphol'),
                expandPath('@examples/Family.graphol'),
                expandPath('@examples/Pizza.graphol'),
            ])

        ######################################
        ## CREATE THE MAIN WINDOW
        ######################################

        return MainWindow()