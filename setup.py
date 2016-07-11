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
######################                              ######################
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


import distutils.core
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import zipfile

from cx_Freeze import setup
from cx_Freeze import Executable
from cx_Freeze import build_exe

from eddy import APPNAME, LICENSE, VERSION, COPYRIGHT, ORGANIZATION
from eddy import APPID, BUG_TRACKER, DIAG_HOME, GRAPHOL_HOME, PROJECT_HOME

from PyQt5 import QtCore


# noinspection PyArgumentList
OPTS = {
    'BUILD_DIR': os.path.join(os.path.abspath(os.path.dirname(__file__)), 'build'),
    'DIST_DIR': os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dist'),
    'PROJECT_DIR': os.path.abspath(os.path.dirname(__file__)),
    'QT_BASE_PATH': os.path.join(QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PrefixPath), '..'),
    'QT_LIB_PATH': QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.LibrariesPath),
    'QT_PLUGINS_PATH': QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PluginsPath)
}


if sys.platform.startswith('darwin'):
    OPTS['AS_TO_EXE'] = None
    OPTS['DIST_NAME'] = '{0}-{1}-{2}-darwin'.format(APPNAME, VERSION, LICENSE.lower())
    OPTS['EXEC_BASE'] = None
    OPTS['EXEC_NAME'] = APPNAME
    OPTS['EXEC_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'resources', 'artwork', 'images', 'eddy.icns')
    OPTS['DOCUMENT_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'resources', 'artwork', 'images', 'document.icns')
    OPTS['DMG_BACKGROUND'] = os.path.join(OPTS['PROJECT_DIR'], 'resources', 'artwork', 'images', 'macos_background_dmg.png')
    OPTS['DMG_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'resources', 'artwork', 'images', 'macos_icon_dmg.icns')
elif sys.platform.startswith('win32'):
    OPTS['AS_TO_EXE'] = True
    OPTS['DIST_NAME'] = '{0}-{1}-{2}-win{3}'.format(APPNAME, VERSION, LICENSE.lower(), platform.architecture()[0][:-3])
    OPTS['EXEC_BASE'] = 'Win32GUI'
    OPTS['EXEC_NAME'] = '{0}.exe'.format(APPNAME)
    OPTS['EXEC_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'resources', 'artwork', 'images', 'eddy.ico')
    OPTS['DOCUMENT_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'resources', 'artwork', 'images', 'document.ico')
    OPTS['DMG_BACKGROUND'] = None
    OPTS['DMG_ICON'] = None
else:
    OPTS['AS_TO_EXE'] = None
    OPTS['DIST_NAME'] = '{0}-{1}-{2}-linux{3}'.format(APPNAME, VERSION, LICENSE.lower(), platform.architecture()[0][:-3])
    OPTS['EXEC_BASE'] = None
    OPTS['EXEC_NAME'] = APPNAME
    OPTS['EXEC_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'resources', 'artwork', 'images', 'eddy.png')
    OPTS['DOCUMENT_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'resources', 'artwork', 'images', 'document.png')
    OPTS['DMG_BACKGROUND'] = None
    OPTS['DMG_ICON'] = None


OPTS['BUILD_PATH'] = os.path.join(OPTS['BUILD_DIR'], OPTS['DIST_NAME'])


class Clean(distutils.core.Command):
    """
    Custom clean command to tidy up the project root.
    """
    user_options = []

    def initialize_options(self):
        """
        Initialize command options.
        """
        pass

    def finalize_options(self):
        """
        Finalize command options.
        """
        pass

    def run(self):
        """
        Command execution.
        """
        if os.path.isdir(OPTS['BUILD_DIR']):
            shutil.rmtree(OPTS['BUILD_DIR'])
        if os.path.isdir(OPTS['DIST_DIR']):
            shutil.rmtree(OPTS['DIST_DIR'])


class BuildExe(build_exe):
    """
    Extends the build_exe command to:
       - add option 'dist_dir' (or --dist-dir as a command line parameter)
       - produce a zip file
       - produce a windows installer using InnoSetup (ony on windows platform)
    """
    dist_dir = None
    user_options = build_exe.user_options
    user_options.extend([('dist-dir=', 'd', "directory where to put final distributions in [default: dist]")])

    def initialize_options(self):
        """
        Initialize command options.
        """
        self.dist_dir = None
        super().initialize_options()

    def finalize_options(self):
        """
        Finalize command options.
        """
        if self.dist_dir is None:
            self.dist_dir = self.build_exe
        super().finalize_options()

    def run(self):
        """
        Command execution.
        """
        super().run()
        self.execute(self.make_dist, ())
        self.execute(self.unix_2_dos, ())
        self.execute(self.unix_exec, ())
        self.execute(self.clean_build, ())
        self.execute(self.make_zip, ())
        self.execute(self.make_installer, ())

    def clean_build(self):
        """
        Cleanup the build directory from garbage files.
        """
        path = os.path.join(self.build_exe, 'jvm.dll')
        if os.path.isfile(path):
            os.remove(path)

    def make_dist(self):
        """
        Create 'dist' directory.
        """
        if not os.path.isdir(self.dist_dir):
            os.mkdir(self.dist_dir)

    def unix_2_dos(self):
        """
        Makes sure text files from directory have 'Windows style' end of lines.
        """
        if sys.platform == 'win32':
            for root, dirs, files in os.walk(self.build_exe):
                for filename in files:
                    path = os.path.abspath(os.path.join(root, filename))
                    if not os.path.isdir(path) and path.rsplit('.', 1)[-1] in ('txt', 'md'):
                        with open(path, mode='rb') as f:
                            data = f.read()
                        new_data = re.sub("\r?\n", "\r\n", data.decode(encoding='UTF-8'))
                        if new_data != data:
                            with open(path, mode='wb') as f:
                                f.write(new_data.encode(encoding='UTF-8'))

    def unix_exec(self):
        """
        Properly create a Linux executable.
        """
        if sys.platform.startswith('linux'):
             path = os.path.join(self.build_exe, 'run.sh')
             with open(path, mode='w') as f:
                f.write("""#!/bin/sh
APP="{0}"
EXEC="{1}"
VERSION="{2}"
DIRNAME=`dirname $0`
LD_LIBRARY_PATH=$DIRNAME
export LD_LIBRARY_PATH
echo "Starting $APP $VERSION ..."
chmod +x $DIRNAME/$EXEC
$DIRNAME/$EXEC "$@"
echo "... bye!"
""".format(APPNAME, OPTS['EXEC_NAME'], VERSION))

             for filename in [OPTS['EXEC_NAME'], 'run.sh']:
                 filepath = os.path.join(self.build_exe, filename)
                 st = os.stat(filepath)
                 os.chmod(filepath, st.st_mode | stat.S_IEXEC)

    def make_zip(self):
        """
        Create a ZIP distribution.
        """
        zip_file = os.path.join(self.dist_dir, '{0}.zip'.format(OPTS['DIST_NAME']))
        zipf = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(self.build_exe):
            for filename in files:
                path = os.path.abspath(os.path.join(root, filename))
                zipf.write(path, arcname=os.path.join(APPNAME, path[len(self.build_exe):]))
        zipf.close()

    def make_installer(self):
        """
        Create a Windows installer using InnoSetup
        """
        if sys.platform.startswith('win32'):

            import yaml
            with open(os.path.join('support', 'innosetup', 'build.yaml'), 'r') as f:
                config = yaml.load(f)
            if 'scripts' not in config:
                print("ERROR: invalid config file: could not find 'scripts' section")
                sys.exit(1)
            if not len(config['scripts']):
                print("ERROR: invalid config file: no entry found in 'scripts' section")
                sys.exit(1)
            if 'iscc' not in config:
                print("ERROR: invalid config file: could not find 'iscc' entry")
                sys.exit(1)
            if not os.path.isfile(os.path.join('support', 'innosetup', config['iscc'])):
                print("ERROR: invalid config file: '{0}' is not a file".format(config['iscc']))
                sys.exit(1)

            # Location of the InnoSetup Compiler program taken from environment.
            config['iscc'] = os.environ.get('ISCC_EXE', config['iscc'])
            if not config['iscc'].lower().endswith('iscc.exe'):
                print("ERROR: invalid location for the ISCC.exe program: {0}".format(config['iscc']))
                sys.exit(1)

            # Build each given innosetup script
            for filename in config['scripts']:

                script_file = os.path.join('support', 'innosetup', filename)
                print("building: {0}".format(script_file))

                try:
                    cmd = [
                        config['iscc'],
                        script_file,
                        '/Q',
                        '/O{0}'.format(OPTS['DIST_DIR']),
                        '/dEDDY_APPID={0}'.format(APPID),
                        '/dEDDY_APPNAME={0}'.format(APPNAME),
                        '/dEDDY_ARCHITECTURE={0}'.format(platform.architecture()[0][:-3]),
                        '/dEDDY_BUGTRACKER={0}'.format(BUG_TRACKER),
                        '/dEDDY_BUILD_PATH={0}'.format(self.build_exe),
                        '/dEDDY_COPYRIGHT={0}'.format(COPYRIGHT),
                        '/dEDDY_DOWNLOAD_URL={0}'.format(GRAPHOL_HOME),
                        '/dEDDY_EXECUTABLE={0}'.format(OPTS['EXEC_NAME']),
                        '/dEDDY_GRAPHOL_URL={0}'.format(GRAPHOL_HOME),
                        '/dEDDY_LICENSE={0}'.format(LICENSE.lower()),
                        '/dEDDY_ORGANIZATION={0}'.format(ORGANIZATION),
                        '/dEDDY_ORGANIZATION_URL={0}'.format(DIAG_HOME),
                        '/dEDDY_PROJECT_HOME={0}'.format(PROJECT_HOME),
                        '/dEDDY_VERSION={0}'.format(VERSION),
                    ]
                    subprocess.call(cmd)
                except Exception as e:
                    print('ERROR: failed to build {0}: {1}'.format(script_file, e))


commands = {
    'clean': Clean,
    'build_exe': BuildExe
}


if sys.platform.startswith('darwin'):

    from cx_Freeze import bdist_mac
    from cx_Freeze import bdist_dmg

    class BDistMac(bdist_mac):
        """
        Extends bdist_mac adding the following changes:
           - properly lookup build_exe path (using OPTS['BUILD_PATH'])
           - generate a customized Info.plist
        """
        binDir = None
        bundleDir = None
        bundle_executable = None
        contentsDir = None
        frameworksDir = None
        resourcesDir = None

        def find_qt_menu_nib(self):
            """
            Returns the location of the qt_menu.nib.
            """
            if self.qt_menu_nib:
                return self.qt_menu_nib

            path = os.path.join(OPTS['QT_BASE_PATH'], 'Src', 'qtbase', 'src', 'plugins', 'platforms', 'cocoa', 'qt_menu.nib')
            if os.path.exists(path):
                return path

            raise IOError("could not find qt_menu.nib: please install Qt5 source components")

        def setRelativeReferencePaths(self):
            """
            For all files in Contents/MacOS, check if they are binaries with references to other files in that dir.
            If so, make those references relative. The appropriate commands are applied to all files; they will just
            fail for files on which they do not apply.
            """
            files = []

            for root, dirs, dir_files in os.walk(self.binDir):
                files.extend([os.path.join(root, f).replace(self.binDir + '/', '') for f in dir_files])

            for filename in files:

                # Skip ZIP files since install_name_tool can't handle them.
                if filename.endswith('.zip'):
                    continue

                # Get the absolute filepath.
                filepath = os.path.join(self.binDir, filename)

                # Ensure write permissions.
                mode = os.stat(filepath).st_mode
                if not mode & stat.S_IWUSR:
                    os.chmod(filepath, mode | stat.S_IWUSR)

                # Let the file itself know its place.
                subprocess.call(('install_name_tool', '-id', '@executable_path/{0}'.format(filename), filepath))

                # Find the references: call otool -L on the file.
                otool = subprocess.Popen(('otool', '-L', filepath), stdout=subprocess.PIPE)
                references = otool.stdout.readlines()[1:]

                for reference in references:

                    # Find the actual referenced file name.
                    referenced_file = reference.decode().strip().split()[0]

                    if referenced_file.startswith('@executable_path/'):
                        # The referenced_file is already a relative path.
                        continue

                    path, name = os.path.split(referenced_file)

                    # Some referenced files have not previously been copied to the executable directory - the
                    # assumption is that you don't need to copy anything from /usr or /System, just from folders
                    # like /opt this fix should probably be elsewhere though.
                    if name not in files and not path.startswith('/usr') and not path.startswith('/System'):
                        if os.path.isfile(referenced_file):
                            self.copy_file(referenced_file, os.path.join(self.binDir, name))
                            files.append(name)

                    new_reference = None
                    if name in files:
                        new_reference = '@executable_path/{0}'.format(name)
                    elif path.startswith('@rpath'):
                        for i in files:
                            if i.endswith(name):
                                new_reference = '@executable_path/{0}'.format(i)

                    if new_reference:
                        # We provide the referenced file so change the reference.
                        subprocess.call(('install_name_tool', '-change', referenced_file, new_reference, filepath))

        def run(self):
            """
            Command execution.
            """
            self.run_command('build')
            build = self.get_finalized_command('build')

            self.bundleDir = os.path.join(build.build_base, self.bundle_name + ".app")
            self.contentsDir = os.path.join(self.bundleDir, 'Contents')
            self.resourcesDir = os.path.join(self.contentsDir, 'Resources')
            self.binDir = os.path.join(self.contentsDir, 'MacOS')
            self.frameworksDir = os.path.join(self.contentsDir, 'Frameworks')

            executable = self.distribution.executables[0].targetName
            _, self.bundle_executable = os.path.split(executable)

            self.mkpath(self.resourcesDir)
            self.mkpath(self.binDir)
            self.mkpath(self.frameworksDir)

            self.copy_tree(OPTS['BUILD_PATH'], self.binDir)

            if self.iconfile:
                self.copy_file(self.iconfile, os.path.join(self.resourcesDir, 'icon.icns'))

            if os.path.isfile(OPTS['DOCUMENT_ICON']):
                self.copy_file(OPTS['DOCUMENT_ICON'], os.path.join(self.resourcesDir, os.path.basename(OPTS['DOCUMENT_ICON'])))

            for framework in self.include_frameworks:
                self.copy_tree(framework, os.path.join(self.frameworksDir, os.path.basename(framework)))

            self.execute(self.create_plist, ())
            self.execute(self.setRelativeReferencePaths, ())
            self.execute(self.prepare_qt_app, ())

            if self.codesign_identity:

                signargs = ['codesign', '-s', self.codesign_identity]

                if self.codesign_entitlements:
                    signargs.append('--entitlements')
                    signargs.append(self.codesign_entitlements)

                if self.codesign_deep:
                    signargs.insert(1, '--deep')

                if self.codesign_resource_rules:
                    signargs.insert(1, '--resource-rules=' + self.codesign_resource_rules)

                signargs.append(self.bundleDir)

                if os.spawnvp(os.P_WAIT, 'codesign', signargs) != 0:
                    raise OSError('Code signing of app bundle failed')

        def create_plist(self):
            """
            Create the Contents/Info.plist file.
            """
            import plistlib
            contents = {
                'CFBundleName': APPNAME,
                'CFBundleGetInfoString': VERSION,
                'CFBundleShortVersionString': VERSION,
                'CFBundleVersion': VERSION,
                'CFBundlePackageType': 'APPL',
                'CFBundleIconFile': 'icon.icns',
                'CFBundleIdentifier': 'it.uniroma1.eddy',
                'CFBundleInfoDictionaryVersion': '6.0',
                'CFBundleDevelopmentRegion': 'English',
                'CFBundleSpokenName': APPNAME,
                'CFBundleExecutable': self.bundle_executable,
                'NSPrincipalClass': 'NSApplication',
                'NSHighResolutionCapable': 'True',

                'CFBundleDocumentTypes': [{
                    'CFBundleTypeExtensions': ['graphol'],
                    'CFBundleTypeName': 'Graphol document (.graphol)',
                    'CFBundleTypeRole': 'Editor',
                    'CFBundleTypeIconFile': 'document.icns',
                    'LSHandlerRank': 'Owner',
                    'LSItemContentTypes': ['it.uniroma1.graphol'],
                }],

                'UTExportedTypeDeclarations': [{
                    'UTTypeConformsTo': ['public.data'],
                    'UTTypeDescription': 'Graphol document (.graphol)',
                    'UTTypeIdentifier': 'it.uniroma1.graphol',
                    'UTTypeIconFile': 'document.icns',
                    'UTTypeTagSpecification': {
                        'public.filename-extension': 'graphol',
                        'public.mime-type': 'application/octet-stream',
                    }
                }]

            }

            plist = open(os.path.join(self.contentsDir, 'Info.plist'), 'wb')
            plistlib.dump(contents, plist)
            plist.close()

    class BDistDmg(bdist_dmg):
        """
        Extends bdist_dmg adding the following changes:
           - correctly package app bundle instead of app bundle content.
        """
        dist_dir = None
        volume_background = None
        volume_icon = None
        user_options = bdist_dmg.user_options
        user_options.extend([
            ('dist-dir=', 'd', "directory where to put final distributions in [default: dist]"),
            ('volume-background=', 'b', "the path to use as background of the generated volume"),
            ('volume-icon=', 'i', "the icon for the generated volume"),
        ])

        bundleDir = None
        bundleName = None
        buildDir = None
        dmgName = None

        def initialize_options(self):
            """
            Initialize command options.
            """
            self.dist_dir = None
            self.volume_background = None
            self.volume_icon = None
            super().initialize_options()

        def finalize_options(self):
            """
            Finalize command options.
            """
            if self.dist_dir is None:
                self.dist_dir = 'dist'
            super().finalize_options()

        def buildDMG(self):
            """
            Build the DMG image.
            """
            if os.path.exists(self.dmgName):
                os.unlink(self.dmgName)

            stagingDir = os.path.join(self.buildDir, 'tmp')
            if os.path.exists(stagingDir):
                shutil.rmtree(stagingDir)

            self.mkpath(stagingDir)

            # Move the app bundle into a separate folder that will be used as source folder for the DMG image
            if subprocess.call(['cp', '-R', self.bundleDir, stagingDir]) != 0:
                raise OSError('could not move app bundle in staging directory')

            # We create the DMG disk image using the create-dmg submodule.
            params = [os.path.join(OPTS['PROJECT_DIR'], 'support', 'createdmg', 'create-dmg')]
            params.extend(['--volname', self.volume_label])
            params.extend(['--text-size', '12'])
            params.extend(['--icon-size', '48'])
            params.extend(['--icon', '{0}.app'.format(self.bundleName), '60', '50'])
            params.extend(['--hide-extension', '{0}.app'.format(self.bundleName)])

            if self.applications_shortcut:
                params.extend(['--app-drop-link', '60', '130'])

            if self.volume_background:
                if not os.path.isfile(self.volume_background):
                    raise OSError('DMG volume background image not found at {0}'.format(self.volume_background))
                print('Using DMG volume background: {0}'.format(self.volume_background))
                from PIL import Image
                w, h = Image.open(self.volume_background).size
                params.extend(['--background', self.volume_background, '--window-size', str(w), str(h)])

            if self.volume_icon:
                if not os.path.isfile(self.volume_icon):
                    raise OSError('DMG volume icon not found at {0}'.format(self.volume_icon))
                print('Using DMG volume icon: {0}'.format(self.volume_icon))
                params.extend(['--volicon', self.volume_icon])

            params.extend([self.dmgName, stagingDir])

            subprocess.call(params)
            shutil.rmtree(stagingDir)

        def make_dist(self):
            """
            Create 'dist' directory.
            """
            if not os.path.isdir(self.dist_dir):
                os.mkdir(self.dist_dir)

        def run(self):
            """
            Command execution.
            """
            self.make_dist()
            self.run_command('bdist_mac')
            self.bundleDir = self.get_finalized_command('bdist_mac').bundleDir
            self.bundleName = self.get_finalized_command('bdist_mac').bundle_name
            self.buildDir = self.get_finalized_command('build').build_base
            self.dmgName = os.path.join(self.buildDir, OPTS['DIST_NAME'] + '.dmg')
            self.execute(self.buildDMG, ())
            self.move_file(self.dmgName, self.dist_dir)

    commands['bdist_mac'] = BDistMac
    commands['bdist_dmg'] = BDistDmg


#############################################
# SETUP
#################################


packages = [
    'eddy.core',
    'eddy.lang',
    'eddy.ui',
]

excludes = [
    'tcl',
    'ttk',
    'tkinter',
    'Tkinter'
]

includes = [
    'PyQt5.QtCore',
    'PyQt5.QtDBus',
    'PyQt5.QtGui',
    'PyQt5.QtPrintSupport',
    'PyQt5.QtNetwork',
    'PyQt5.QtSvg',
    'PyQt5.QtWidgets',
    'PyQt5.QtXml',
]

include_files = [
    (OPTS['DOCUMENT_ICON'], os.path.basename(OPTS['DOCUMENT_ICON'])),
    (os.path.join(OPTS['QT_PLUGINS_PATH'], 'printsupport'), 'printsupport'),
    ('examples', 'examples'),
    ('resources/java', 'resources/java'),
    ('resources/lib', 'resources/lib'),
    ('resources/styles', 'resources/styles'),
    ('LICENSE', 'LICENSE'),
    ('CONTRIBUTING.md', 'CONTRIBUTING.md'),
    ('PACKAGING.md', 'PACKAGING.md'),
    ('README.md', 'README.md'),
]

if sys.platform.startswith('linux'):
    include_files.extend([
        (os.path.join(OPTS['QT_LIB_PATH'], 'libQt5DBus.so.5'), 'libQt5DBus.so.5'),
        (os.path.join(OPTS['QT_LIB_PATH'], 'libQt5XcbQpa.so.5'), 'libQt5XcbQpa.so.5'),
    ])


setup(
    cmdclass=commands,
    name=APPNAME,
    version=VERSION,
    author="Daniele Pantaleone",
    author_email="danielepantaleone@me.com",
    description="Eddy is a graphical editor for the specification and visualization of Graphol ontologies.",
    keywords = "eddy graphol sapienza",
    license=LICENSE,
    url="https://github.com/danielepantaleone/eddy",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: MacOS X :: Cocoa',
        'Environment :: Win32 (MS Windows)'
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Utilities'
    ],
    options={
        'bdist_mac': {
            'bundle_name': APPNAME,
            'iconfile': OPTS['EXEC_ICON'],
        },
        'bdist_dmg': {
            'dist_dir': OPTS['DIST_DIR'],
            'applications_shortcut': True,
            'volume_label': '{0} {1}'.format(APPNAME, VERSION),
            'volume_background': OPTS['DMG_BACKGROUND'],
            'volume_icon': OPTS['DMG_ICON'],
        },
        'build_exe': {
            'append_script_to_exe': OPTS['AS_TO_EXE'],
            'build_exe': OPTS['BUILD_PATH'],
            'dist_dir': OPTS['DIST_DIR'],
            'excludes': excludes,
            'includes': includes,
            'include_files': include_files,
            'optimize': 1,
            'packages': packages,
            'silent': False,
        }
    },
    executables=[
        Executable(
            script='run.py',
            base=OPTS['EXEC_BASE'],
            targetName=OPTS['EXEC_NAME'],
            icon=OPTS['EXEC_ICON'],
        )
    ]
)