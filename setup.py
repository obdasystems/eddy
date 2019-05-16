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

import distutils
import os
import pkg_resources
import platform
import py_compile
import re
import requests.certs
import setuptools
import stat
import subprocess
import sys
import textwrap
import zipfile

from eddy import APPNAME, APPID, BUG_TRACKER, COPYRIGHT
from eddy import DIAG_HOME, GRAPHOL_HOME, LICENSE
from eddy import ORGANIZATION, PROJECT_HOME, VERSION
from eddy.core.functions.misc import rstrip
from eddy.core.functions.fsystem import fexists, fremove, isdir
from eddy.core.functions.fsystem import mkdir, rmdir
from eddy.core.functions.path import expandPath

from PyQt5 import QtCore

###################################
# SETUP CONSTANTS DECLARATION
###########################


LINUX = sys.platform.startswith('linux')
MACOS = sys.platform.startswith('darwin')
WIN32 = sys.platform.startswith('win32')

EXEC_ARCH = None
EXEC_BASE = None
EXEC_ICON = None
EXEC_NAME = None

if LINUX:
    EXEC_ARCH = platform.machine().lower()
    EXEC_BASE = None
    EXEC_ICON = expandPath('@resources/images/eddy.png')
    EXEC_NAME = APPNAME

if MACOS:
    EXEC_ARCH = platform.machine().lower()
    EXEC_BASE = None
    EXEC_ICON = expandPath('@resources/images/eddy.icns')
    EXEC_NAME = APPNAME

if WIN32:
    # On Windows use the PROCESSOR_ARCHITECTURE environment variable to detect if we
    # are running a 32-bit or 64-bit version of Python
    EXEC_ARCH = os.environ['PROCESSOR_ARCHITECTURE'].lower() if 'PROCESSOR_ARCHITECTURE' in os.environ else platform.machine().lower()
    EXEC_BASE = 'Win32GUI'
    EXEC_ICON = expandPath('@resources/images/eddy.ico')
    EXEC_NAME = '%s.exe' % APPNAME

BUILD_DIR = os.path.join(expandPath(os.path.dirname(__file__)), 'build')
DIST_DIR = os.path.join(expandPath(os.path.dirname(__file__)), 'dist')
DIST_NAME = '%s-%s-%s_%s' % (APPNAME, VERSION, platform.system().lower(), EXEC_ARCH)
DIST_PATH = os.path.join(BUILD_DIR, DIST_NAME)

JRE_DIR = os.path.join(expandPath(os.path.dirname(__file__)), 'resources', 'java')

QT_BASE_PATH = os.path.join(QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PrefixPath), '..')
QT_LIB_PATH = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.LibrariesPath)
QT_PLUGINS_PATH = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PluginsPath)

###################################
# CUSTOM COMMANDS IMPLEMENTATION
###########################

cmdclass = {}


class clean(setuptools.Command):
    """
    Custom clean command to tidy up the project root.
    """
    description = "clean up temporary files from 'build' command"
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
        rmdir(BUILD_DIR)
        rmdir(DIST_DIR)


cmdclass['clean'] = clean


if len(sys.argv) == len(set(sys.argv) - {'build_exe', 'bdist_archive', 'bdist_dmg',
                                         'bdist_mac', 'bdist_innosetup', 'install_exe'}):
    from setuptools import setup
    executables = None
else:
    import cx_Freeze
    from cx_Freeze import setup

    # noinspection PyUnresolvedReferences
    class build_exe(cx_Freeze.build_exe):
        """
        Extends the build_exe command to:
           - add option 'jre_dir' (or --jre-dir as a command line parameter)
        """
        description = "build executables from Python scripts"
        user_options = cx_Freeze.build_exe.user_options
        user_options.extend([
            ('jre-dir=', None,
             "directory where to search for the bundled jre [default: {}]".format(os.path.relpath(JRE_DIR))),
            ('no-jre', None,
             "create a distribution without a bundled jre [default: False]"),
        ])
        boolean_options = cx_Freeze.build_exe.boolean_options
        boolean_options.extend(['no-jre'])

        def initialize_options(self):
            """
            Initialize command options.
            """
            super().initialize_options()
            self.jre_dir = None
            self.no_jre = 0

        def finalize_options(self):
            """
            Finalize command options.
            """
            super().finalize_options()
            if self.jre_dir is None:
                self.jre_dir = JRE_DIR
            if self.no_jre is None:
                self.no_jre = 0

        def run(self):
            """
            Command execution.
            """
            # Symlink Qt libraries into the virtualenv on macOS, since cx_Freeze assumes
            # the linker @rpath command to point there.
            if MACOS:
                self.execute(self.make_symlinks, (), msg='Symlinking Qt frameworks to Python lib dir...')
            # cx_Freeze's build_exe does not respect global dry-run option
            if not self.dry_run:
                super().run()
            self.execute(self.make_plugins, (), msg='Packaging Eddy plugins...')
            self.execute(self.make_jre, (), msg='Bundling Java Runtime Environment...')
            if LINUX:
                self.execute(self.make_run_script, (), msg='Generating launcher script')
            if WIN32:
                self.execute(self.make_win32, (), msg='Setting DOS line endings...')
            self.execute(self.make_cleanup, (), msg='Removing temporary files...')

        def make_cleanup(self):
            """
            Cleanup the build directory from garbage files.
            """
            if WIN32:
                fremove(os.path.join(self.build_exe, 'jvm.dll'))
            elif MACOS:
                # Delete symlinks to Qt frameworks created during build
                for framework in os.listdir(QT_LIB_PATH):
                    source = os.path.relpath(os.path.join(QT_LIB_PATH, framework), os.path.join(sys.exec_prefix, "lib"))
                    target = os.path.join(os.path.join(sys.exec_prefix, "lib"), framework)

                    if os.path.islink(target) and os.readlink(target) == source:
                        distutils.log.info("Removing symlink %s to %s", target, source)
                        os.unlink(target)

        def make_symlinks(self):
            """
            Symlink Qt Framework bundles into prefix lib dir on macOS.

            Workaround for: https://github.com/anthony-tuininga/cx_Freeze/issues/299
            """
            if MACOS:
                distutils.log.info("Linking Frameworks to Python lib dir...")
                for framework in os.listdir(QT_LIB_PATH):
                    source = os.path.relpath(os.path.join(QT_LIB_PATH, framework), os.path.join(sys.exec_prefix, "lib"))
                    target = os.path.join(os.path.join(sys.exec_prefix, "lib"), framework)

                    if not os.path.exists(target):
                        distutils.log.info("Linking %s to %s", source, target)
                        os.symlink(source, target)
                    else:
                        distutils.log.info("Target file %s exists, skipping", target)

        def make_jre(self):
            """
            Bundles a Java Runtime Environment.
            """
            if self.no_jre:
                distutils.log.info('Skip bundling of Java Runtime Environment in the distribution')
                return

            try:
                dest_dir = os.path.join(self.build_exe, 'resources', 'java', 'jre')
                if isdir(os.path.join(self.jre_dir, 'jre')): # Probably a JDK distribution
                    self.jre_dir = os.path.join(self.jre_dir, 'jre')
                distutils.log.info("Copying JRE from {0}".format(self.jre_dir))
                distutils.dir_util.copy_tree(self.jre_dir, os.path.join(self.build_exe, dest_dir))
            except Exception as e:
                raise distutils.errors.DistutilsFileError('Failed to bundle JRE: {0}'.format(e))

        def make_plugins(self):
            """
            Package built-in plugins into ZIP archives.
            """
            if isdir('@plugins/'):
                mkdir(os.path.join(self.build_exe, 'plugins'))
                for file_or_directory in os.listdir(expandPath('@plugins/')):
                    plugin = os.path.join(expandPath('@plugins/'), file_or_directory)
                    if isdir(plugin):
                        distutils.log.info('packaging plugin: %s', file_or_directory)
                        zippath = os.path.join(self.build_exe, 'plugins', '%s.zip' % file_or_directory)
                        with zipfile.ZipFile(zippath, 'w', zipfile.ZIP_STORED) as zipf:
                            for root, dirs, files in os.walk(plugin):
                                if not root.endswith('__pycache__'):
                                    for filename in files:
                                        path = expandPath(os.path.join(root, filename))
                                        if path.endswith('.py'):
                                            new_path = '%s.pyc' % rstrip(path, '.py')
                                            py_compile.compile(path, new_path)
                                            arcname = os.path.join(file_or_directory, os.path.relpath(new_path, plugin))
                                            zipf.write(new_path, arcname)
                                            fremove(new_path)
                                        else:
                                            arcname = os.path.join(file_or_directory, os.path.relpath(path, plugin))
                                            zipf.write(path, arcname)

        def make_win32(self):
            """
            Makes sure text files from directory have 'Windows style' end of lines.
            """
            if WIN32:
                for root, dirs, files in os.walk(self.build_exe):
                    for filename in files:
                        path = expandPath(os.path.join(root, filename))
                        if not isdir(path) and path.rsplit('.', 1)[-1] in ('txt', 'md'):
                            with open(path, mode='rb') as f:
                                data = f.read()
                            new_data = re.sub("\r?\n", "\r\n", data.decode(encoding='UTF-8'))
                            if new_data != data:
                                with open(path, mode='wb') as f:
                                    f.write(new_data.encode(encoding='UTF-8'))

        def make_run_script(self):
            """
            Properly create a shell executable launcher.
            """
            if LINUX:
                path = os.path.join(self.build_exe, 'run.sh')
                with open(path, mode='w') as f:
                    f.write(textwrap.dedent("""
                    #!/bin/sh
                    
                    APP="{0}"
                    EXEC="{1}"
                    VERSION="{2}"
                    DIRNAME=`dirname $0`
                    export LD_LIBRARY_PATH="$DIRNAME:$DIRNAME/lib:$LD_LIBRARY_PATH"
                    echo "Starting $APP $VERSION ..."
                    $DIRNAME/$EXEC "$@"
                    """[1:].format(APPNAME, EXEC_NAME, VERSION)))

                # Set exec bit on executables
                for filename in [EXEC_NAME, 'run.sh']:
                    filepath = os.path.join(self.build_exe, filename)
                    st = os.stat(filepath)
                    os.chmod(filepath, st.st_mode | stat.S_IEXEC)


    class bdist_archive(distutils.core.Command):
        """
        Create a distribution archive using the given format.
        """
        description = 'create a distribution archive using the given format'
        user_options = [
            ('bdist-dir=', 'b',
             "directory where to build the distribution [default: {}]".format(os.path.relpath(DIST_PATH))),
            ('dist-dir=', 'd',
             "directory to put final built distributions in [default: {}]".format(os.path.relpath(DIST_DIR))),
            ('format=', 'f',
             "archive format to create (tar, gztar, bztar, xztar, "
             "ztar, zip)"),
            ('jre-dir=', None,
             "directory where to search for the bundled jre [default: {}]".format(os.path.relpath(JRE_DIR))),
            ('no-jre', None,
             "create a distribution without a bundled jre [default: False]"),
            ('skip-build', None,
             "skip rebuilding everything (for testing/debugging)"),
            ('owner=', 'u',
             "Owner name used when creating a tar file [default: current user]"),
            ('group=', 'g',
             "Group name used when creating a tar file [default: current group]"),
        ]
        boolean_options = ['no-jre', 'skip-build']

        # Default format by platform
        default_format = { 'posix': 'gztar',
                           'nt': 'zip' }

        def initialize_options(self):
            self.bdist_dir = None
            self.dist_dir = None
            self.format = None
            self.jre_dir = None
            self.no_jre = 0
            self.skip_build = 0
            self.owner = None
            self.group = None

        def finalize_options(self):
            if self.bdist_dir is None:
                self.bdist_dir = DIST_PATH
            if self.dist_dir is None:
                self.dist_dir = DIST_DIR
            if self.jre_dir is None:
                self.jre_dir = JRE_DIR
            if self.no_jre is None:
                self.no_jre = 0
            if self.format is None:
                try:
                    self.format = self.default_format[os.name]
                except KeyError:
                    raise distutils.errors.DistutilsPlatformError(
                        "don't know how to create archive distribution on platform %s" % os.name)

        def run(self):
            if not self.skip_build:
                build_exe = self.reinitialize_command('build_exe', reinit_subcommands=1)
                build_exe.build_exe = self.bdist_dir
                build_exe.jre_dir = self.jre_dir
                build_exe.no_jre = self.no_jre
                self.run_command('build')
            # package the archive
            self.make_archive(os.path.join(self.dist_dir, DIST_NAME),
                              self.format, root_dir=os.path.dirname(self.bdist_dir),
                              owner=self.owner, group=self.group)


    cmdclass['build_exe'] = build_exe
    cmdclass['bdist_archive'] = bdist_archive

    if WIN32:
        class bdist_innosetup(distutils.core.Command):
            """
            Generate a Windows installer using InnoSetup.
            """
            description = 'create a MS Windows installer using InnoSetup'
            user_options = [
                ('bdist-dir=', 'b',
                 "directory where to build the distribution [default: {}]".format(os.path.relpath(DIST_PATH))),
                ('dist-dir=', 'd',
                 "directory to put final built distributions in [default: {}]".format(os.path.relpath(DIST_DIR))),
                ('jre-dir=', None,
                 "directory where to search for the bundled jre [default: {}]".format(os.path.relpath(JRE_DIR))),
                ('no-jre', None,
                 "create a distribution without a bundled jre [default: False]"),
                ('skip-build', None,
                 "skip rebuilding everything (for testing/debugging)"),
            ]
            boolean_options = ['no-jre', 'skip-build']

            def initialize_options(self):
                self.bdist_dir = None
                self.dist_dir = None
                self.jre_dir = None
                self.no_jre = 0
                self.skip_build = 0

            def finalize_options(self):
                if self.bdist_dir is None:
                    self.bdist_dir = DIST_PATH
                if self.dist_dir is None:
                    self.dist_dir = DIST_DIR
                if self.jre_dir is None:
                    self.jre_dir = JRE_DIR
                if self.no_jre is None:
                    self.no_jre = 0
                if self.skip_build is None:
                    self.skip_build = 0

            def run(self):
                """
                Command execution.
                """
                if not self.skip_build:
                    build = self.reinitialize_command('build', reinit_subcommands=1)
                    build_exe = self.reinitialize_command('build_exe', reinit_subcommands=1)
                    build.build_exe = self.bdist_dir
                    build_exe.build_exe = self.bdist_dir
                    build_exe.jre_dir = self.jre_dir
                    build_exe.no_jre = self.no_jre
                    self.run_command('build')
                self.mkpath(self.dist_dir)
                self.execute(self.make_installer, (), msg='Creating InnoSetup installer...')

            def make_installer(self):
                """
                Create a Windows installer using InnoSetup
                """
                import yaml

                with open(os.path.join('support', 'innosetup', 'build.yaml'), 'r') as f:
                    config = yaml.safe_load(f)
                if 'scripts' not in config:
                    print("ERROR: invalid config file: could not find 'scripts' section")
                    sys.exit(1)
                if not len(config['scripts']):
                    print("ERROR: invalid config file: no entry found in 'scripts' section")
                    sys.exit(1)

                # Location of the InnoSetup Compiler program taken from environment.
                config['iscc'] = os.environ.get('ISCC_EXE', config['iscc'])

                if 'iscc' not in config:
                    print("ERROR: invalid config file: could not find 'iscc' entry")
                    sys.exit(1)
                if not config['iscc'].lower().endswith('iscc.exe'):
                    print("ERROR: invalid location for the ISCC.exe program: {0}".format(config['iscc']))
                    sys.exit(1)
                if not fexists(os.path.join('support', 'innosetup', config['iscc'])):
                    print("ERROR: invalid config file: '{0}' is not a file".format(config['iscc']))
                    sys.exit(1)

                # Disable installation of 64 bit executables on 32 bit Windows
                architecturesAllowed = 'x64' if platform.architecture()[0] == '64bit' else ''

                # Build each given innosetup script
                for filename in config['scripts']:
                    script_file = os.path.join('support', 'innosetup', filename)
                    distutils.log.info("building: {0}".format(script_file))

                    try:
                        cmd = [
                            config['iscc'],
                            script_file,
                            '/Q',
                            '/O{0}'.format(self.dist_dir),
                            '/dEDDY_APPID={0}'.format(APPID),
                            '/dEDDY_APPNAME={0}'.format(APPNAME),
                            '/dEDDY_ARCHITECTURE={0}'.format(EXEC_ARCH),
                            '/dEDDY_ARCHITECTURES_ALLOWED={0}'.format(architecturesAllowed),
                            '/dEDDY_BUGTRACKER={0}'.format(BUG_TRACKER),
                            '/dEDDY_BUILD_PATH={0}'.format(self.bdist_dir),
                            '/dEDDY_COPYRIGHT={0}'.format(COPYRIGHT),
                            '/dEDDY_DOWNLOAD_URL={0}'.format(GRAPHOL_HOME),
                            '/dEDDY_EXECUTABLE={0}'.format(EXEC_NAME),
                            '/dEDDY_GRAPHOL_URL={0}'.format(GRAPHOL_HOME),
                            '/dEDDY_LICENSE={0}'.format(LICENSE.lower()),
                            '/dEDDY_ORGANIZATION={0}'.format(ORGANIZATION),
                            '/dEDDY_ORGANIZATION_URL={0}'.format(DIAG_HOME),
                            '/dEDDY_PROJECT_HOME={0}'.format(PROJECT_HOME),
                            '/dEDDY_VERSION={0}'.format(VERSION),
                        ]
                        subprocess.call(cmd)
                    except Exception as e:
                        distutils.log.error('Failed to build {0}: {1}'.format(script_file, e))

        cmdclass['bdist_innosetup'] = bdist_innosetup

    if MACOS:
        class bdist_mac(cx_Freeze.bdist_mac):
            """
            Extends bdist_mac adding the following changes:
               - properly lookup build_exe path (using DIST_PATH)
               - generate a customized Info.plist
            """
            description = 'create a macOS .app application bundle'
            user_options = cx_Freeze.bdist_mac.user_options
            user_options.extend([
                ('bdist-dir=', 'b',
                 "directory where to build the distribution [default: {}]".format(os.path.relpath(DIST_PATH))),
                ('jre-dir=', None,
                 "directory where to search for the bundled jre [default: {}]".format(os.path.relpath(JRE_DIR))),
                ('no-jre', None,
                 "create a distribution without a bundled jre [default: False]"),
                ('skip-build', None,
                 "skip rebuilding everything (for testing/debugging)"),
            ])
            boolean_options = ['no-jre', 'skip-build']

            def initialize_options(self):
                super().initialize_options()
                self.bdist_dir = None
                self.jre_dir = None
                self.no_jre = 0
                self.skip_build = 0

            def finalize_options(self):
                super().finalize_options()
                if self.bdist_dir is None:
                    self.bdist_dir = DIST_PATH
                if self.jre_dir is None:
                    self.jre_dir = JRE_DIR
                if self.no_jre is None:
                    self.no_jre = 0
                if self.skip_build is None:
                    self.skip_build = 0

            def setRelativeReferencePaths(self):
                """
                For all files in Contents/MacOS, check if they are binaries with references to other files in that dir.
                If so, make those references relative. The appropriate commands are applied to all files; they will just
                fail for files on which they do not apply.
                """
                files = []
                for root, dirs, dir_files in os.walk(self.binDir):
                    # Skip changing symbols in the resources folder
                    if not root == os.path.join(self.binDir, 'resources'):
                        files.extend([os.path.join(root, f).replace(self.binDir + '/', '') for f in dir_files])

                for filename in files:
                    if filename.endswith('.zip'):
                        continue
                    filepath = os.path.join(self.binDir, filename)
                    mode = os.stat(filepath).st_mode
                    if not mode & stat.S_IWUSR:
                        os.chmod(filepath, mode | stat.S_IWUSR)

                    subprocess.call(('install_name_tool', '-id', '@executable_path/{0}'.format(filename), filepath))
                    with subprocess.Popen(('otool', '-L', filepath), stdout=subprocess.PIPE) as otool:
                        references = otool.stdout.readlines()[1:]

                    for reference in references:
                        referenced_file = reference.decode().strip().split()[0]
                        if referenced_file.startswith('@executable_path/'):
                            continue
                        path, name = os.path.split(referenced_file)
                        # Some referenced files have not previously been copied to the executable directory - the
                        # assumption is that you don't need to copy anything from /usr or /System, just from folders
                        # like /opt this fix should probably be elsewhere though.
                        if name not in files and not path.startswith('/usr') and not path.startswith('/System'):
                            if fexists(referenced_file):
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
                            subprocess.call(('install_name_tool', '-change', referenced_file, new_reference, filepath))

            def run(self):
                if not self.skip_build:
                    build = self.reinitialize_command('build', reinit_subcommands=1)
                    build_exe = self.reinitialize_command('build_exe', reinit_subcommands=1)
                    build.build_exe = self.bdist_dir
                    build_exe.build_exe = self.bdist_dir
                    build_exe.jre_dir = self.jre_dir
                    build_exe.no_jre = self.no_jre
                    self.run_command('build')
                build = self.get_finalized_command('build')

                # Define the paths within the application bundle
                self.bundleDir = os.path.join(build.build_base,
                                              self.bundle_name + ".app")
                self.contentsDir = os.path.join(self.bundleDir, 'Contents')
                self.resourcesDir = os.path.join(self.contentsDir, 'Resources')
                self.binDir = os.path.join(self.contentsDir, 'MacOS')
                self.frameworksDir = os.path.join(self.contentsDir, 'Frameworks')

                #Find the executable name
                executable = self.distribution.executables[0].targetName
                _, self.bundle_executable = os.path.split(executable)

                # Build the app directory structure
                self.mkpath(self.resourcesDir)
                self.mkpath(self.binDir)
                self.mkpath(self.frameworksDir)

                self.copy_tree(build.build_exe, self.binDir)

                # Copy the icon
                if self.iconfile:
                    self.copy_file(self.iconfile, os.path.join(self.resourcesDir,
                                                               'icon.icns'))

                # Copy in Frameworks
                for framework in self.include_frameworks:
                    self.copy_tree(framework, self.frameworksDir + '/' +
                                   os.path.basename(framework))

                # Create the Info.plist file
                self.execute(self.create_plist, ())

                # Make all references to libraries relative
                self.execute(self.setRelativeReferencePaths, ())

                # For a Qt application, run some tweaks
                self.execute(self.prepare_qt_app, ())

                # Sign the app bundle if a key is specified
                if self.codesign_identity:
                    signargs = [
                        'codesign', '-s', self.codesign_identity
                    ]

                    if self.codesign_entitlements:
                        signargs.append('--entitlements')
                        signargs.append(self.codesign_entitlements)

                    if self.codesign_deep:
                        signargs.insert(1, '--deep')

                    if self.codesign_resource_rules:
                        signargs.insert(1, '--resource-rules=' +
                                        self.codesign_resource_rules)

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
                }

                plist = open(os.path.join(self.contentsDir, 'Info.plist'), 'wb')
                plistlib.dump(contents, plist)
                plist.close()

        class bdist_dmg(cx_Freeze.bdist_dmg):
            """
            Extends bdist_dmg adding the following changes:
               - correctly package app bundle instead of app bundle content.
            """
            description = "create a Mac DMG disk image containing the Mac application bundle"
            user_options = cx_Freeze.bdist_dmg.user_options
            user_options.extend([
                ('bdist-dir=', 'b',
                 "directory where to build the distribution [default: {}]".format(os.path.relpath(DIST_PATH))),
                ('dist-dir=', 'd',
                 "directory to put final built distributions in [default: {}]".format(os.path.relpath(DIST_DIR))),
                ('jre-dir=', None,
                 "directory where to search for the bundled jre [default: {}]".format(os.path.relpath(JRE_DIR))),
                ('no-jre', None,
                 "create a distribution without a bundled jre [default: False]"),
                ('skip-build', None,
                 "skip rebuilding everything (for testing/debugging)"),
                ('volume-background=', None,
                 "the path to use as background of the generated volume"),
                ('volume-icon=', None,
                 "the icon for the generated volume"),
            ])
            boolean_options = ['no-jre', 'skip-build']

            def initialize_options(self):
                """
                Initialize command options.
                """
                self.bdist_dir = None
                self.dist_dir = None
                self.jre_dir = None
                self.no_jre = 0
                self.skip_build = 0
                self.volume_background = None
                self.volume_icon = None
                super().initialize_options()

            def finalize_options(self):
                """
                Finalize command options.
                """
                if self.bdist_dir is None:
                    self.bdist_dir = DIST_PATH
                if self.dist_dir is None:
                    self.dist_dir = DIST_DIR
                if self.jre_dir is None:
                    self.jre_dir = JRE_DIR
                if self.no_jre is None:
                    self.no_jre = 0
                if self.skip_build is None:
                    self.skip_build = 0
                super().finalize_options()

            def buildDMG(self):
                """
                Build the DMG image.
                """
                if not isdir('@support/createdmg') or not fexists('@support/createdmg/create-dmg'):
                    raise OSError('unable to find create-dmg utility: please clone Eddy with all its submodules' )

                if fexists(self.dmgName):
                    os.unlink(self.dmgName)

                stagingDir = os.path.join(self.buildDir, 'tmp')
                if isdir(stagingDir):
                    rmdir(stagingDir)

                self.mkpath(stagingDir)

                # Move the app bundle into a separate folder that will be used as source folder for the DMG image
                if subprocess.call(['cp', '-R', self.bundleDir, stagingDir]) != 0:
                    raise OSError('could not move app bundle in staging directory')

                # We create the DMG disk image using the create-dmg submodule.
                params = [expandPath('@support/createdmg/create-dmg')]
                params.extend(['--volname', self.volume_label])
                params.extend(['--text-size', '12'])
                params.extend(['--icon-size', '48'])
                params.extend(['--icon', '{0}.app'.format(self.bundleName), '60', '50'])
                params.extend(['--hide-extension', '{0}.app'.format(self.bundleName)])

                if self.applications_shortcut:
                    params.extend(['--app-drop-link', '60', '130'])

                if self.volume_background:
                    if not fexists(self.volume_background):
                        raise OSError('DMG volume background image not found at {0}'.format(self.volume_background))
                    print('Using DMG volume background: {0}'.format(self.volume_background))
                    from PIL import Image
                    w, h = Image.open(self.volume_background).size
                    params.extend(['--background', self.volume_background, '--window-size', str(w), str(h)])

                if self.volume_icon:
                    if not fexists(self.volume_icon):
                        raise OSError('DMG volume icon not found at {0}'.format(self.volume_icon))
                    print('Using DMG volume icon: {0}'.format(self.volume_icon))
                    params.extend(['--volicon', self.volume_icon])

                params.extend([self.dmgName, stagingDir])

                subprocess.call(params)
                rmdir(stagingDir)

            def run(self):
                """
                Command execution.
                """
                if not self.skip_build:
                    bdist = self.reinitialize_command('bdist_mac', reinit_subcommands=1)
                    bdist.bdist_dir = self.bdist_dir
                    bdist.jre_dir = self.jre_dir
                    bdist.no_jre = self.no_jre
                    self.run_command('bdist_mac')
                build = self.get_finalized_command('build')
                bdist = self.get_finalized_command('bdist_mac')
                self.bundleDir = os.path.join(build.build_base, bdist.bundle_name + ".app")
                self.bundleName = bdist.bundle_name
                self.buildDir = build.build_base
                self.dmgName = os.path.join(self.buildDir, DIST_NAME + '.dmg')
                self.execute(self.buildDMG, (), msg='Building disk image...')
                self.mkpath(self.dist_dir)
                self.move_file(self.dmgName, self.dist_dir)

        cmdclass['bdist_mac'] = bdist_mac
        cmdclass['bdist_dmg'] = bdist_dmg

    executables = [
            cx_Freeze.Executable(
                script='run.py',
                initScript=expandPath('@root/scripts/initscripts/ConsoleSetLibPath.py'),
                base=EXEC_BASE,
                targetName=EXEC_NAME,
                icon=EXEC_ICON,
            )
    ]

#############################################
# SETUP CONSTANTS
#################################

packages = [
    'eddy.core',
    'eddy.plugins',
    'eddy.ui',
    'packaging',
    'idna',
    'cffi',
]

excludes = [
    'tcl',
    'ttk',
    'tkinter',
    'Tkinter',
    # QT MODULES
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtWebEngine',
    'PyQt5.QtMultimedia',
]

includes = [
    # QT MODULES
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtXml',
    'PyQt5.QtSvg',
    'PyQt5.QtWidgets',
    'PyQt5.QtNetwork',
    'PyQt5.QtPrintSupport',
    # REQUIRED + 3RD PARTY MODULES
    'appdirs',
    'queue',
    'csv',
    'github3',
    'jnius',
    'natsort',
    'requests',
    'uritemplate',
    'verlib',
]

if QtCore.QVersionNumber.fromString(QtCore.QT_VERSION_STR) > QtCore.QVersionNumber.fromString('5.10.1'):
    includes.append('PyQt5.sip')

if not WIN32:
    includes.append('PyQt5.QtDBus')

include_files = [
    (requests.certs.where(), 'cacert.pem'),
    (os.path.join(QT_PLUGINS_PATH, 'printsupport'), 'printsupport'),
    ('eddy/core/jvm/lib', 'resources/lib'),
    ('examples', 'examples'),
    ('LICENSE', 'LICENSE'),
    ('CONTRIBUTING.md', 'CONTRIBUTING.md'),
    ('PACKAGING.md', 'PACKAGING.md'),
    ('README.md', 'README.md'),
]

# INCLUDE JNIUS > 1.1.0 JAVA HELPERS
jnius_src = os.path.realpath(pkg_resources.resource_filename('jnius_config', 'jnius/src'))
if os.path.isdir(jnius_src):
    include_files.append((jnius_src, 'resources/lib'))

if LINUX:
    include_files.extend([
        (os.path.join(QT_LIB_PATH, 'libQt5DBus.so.5'), 'lib/libQt5DBus.so.5'),
        (os.path.join(QT_LIB_PATH, 'libQt5XcbQpa.so.5'), 'lib/libQt5XcbQpa.so.5'),
    ])

zip_includes = [
    (os.path.join('eddy', 'ui', 'style', qss), os.path.join('eddy', 'ui', 'style', qss))
    for qss in os.listdir(os.path.join('eddy', 'ui', 'style')) if qss.endswith('.qss')
]

#############################################
# SETUP
#################################

setup(
    cmdclass=cmdclass,
    name=APPNAME,
    version=VERSION,
    author="Daniele Pantaleone",
    author_email="pantaleone@dis.uniroma1.it",
    description="Eddy is a graphical editor for the specification and visualization of Graphol ontologies.",
    long_description="Eddy is a graphical editor for the construction of Graphol ontologies. Eddy features a "
                     "design environment specifically thought out for generating Graphol ontologies through ad-hoc "
                     "functionalities. Drawing features allow designers to comfortably edit ontologies in a central "
                     "viewport area, while lateral docking areas contains specifically-tailored widgets for "
                     "editing, navigation and inspection of the diagram. Eddy is written in [Python 3] and the UI is "
                     "implemented through the PyQt5 bindings for the Qt5 framework. Eddy is licensed under the GNU "
                     "General Public License v3.",
    keywords = "eddy graphol sapienza",
    license=LICENSE,
    url="https://github.com/obdasystems/eddy",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: MacOS X :: Cocoa',
        'Environment :: Win32 (MS Windows)'
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Utilities'
    ],
    python_requires='>=3.5',
    install_requires=[
        'github3.py',
        'natsort',
        'pyjnius',
        'requests',
        'rfc3987',
        'verlib'
    ],
    packages=setuptools.find_packages(exclude=['tests', 'scripts', 'support']),
    include_package_data=True,
    entry_points={
        'gui_scripts': [
            'eddy = eddy.core.application:main'
        ]
    },
    zip_safe=False,
    options={
        'bdist_mac': {
            'bundle_name': APPNAME,
            'iconfile': EXEC_ICON,
        },
        'bdist_dmg': {
            'dist_dir': DIST_DIR,
            'applications_shortcut': 1,
            'volume_label': '%s %s' % (APPNAME, VERSION),
            'volume_background': expandPath('@resources/images/macos_background_dmg.png'),
            'volume_icon': expandPath('@resources/images/macos_icon_dmg.icns'),
        },
        'bdist_gztar': {
            'dist_dir': DIST_DIR,
        },
        'bdist_zip': {
            'dist_dir': DIST_DIR,
        },
        'build_exe': {
            'bin_includes': ['libssl.so', 'libcrypto.so'],
            'build_exe': DIST_PATH,
            'jre_dir': JRE_DIR,
            'excludes': excludes,
            'includes': includes,
            'include_files': include_files,
            'optimize': 1,
            'packages': packages,
            'zip_includes': zip_includes,
            'zip_include_packages': '*',
            'zip_exclude_packages': '',
            'silent': 0,
        },
        'install_exe': {
            'build_dir': DIST_PATH,
            'install_dir': os.path.join(DIST_DIR, DIST_NAME),
        }
    },
    executables=executables
)
