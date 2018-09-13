#!/usr/bin/env bash

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

#
# Remove unneeded files from the bundled JRE (see http://java.com/licensereadme)
#

set -e # Stop on any error

# Java Runtime Files
rm -rf resources/java/jre/lib/ext/
rm -rf resources/java/jre/bin/rmid
rm -rf resources/java/jre/bin/rmiregistry
rm -rf resources/java/jre/bin/tnameserv
rm -rf resources/java/jre/bin/keytool
rm -rf resources/java/jre/bin/kinit
rm -rf resources/java/jre/bin/klist
rm -rf resources/java/jre/bin/ktab
rm -rf resources/java/jre/bin/policytool
rm -rf resources/java/jre/bin/orbd
rm -rf resources/java/jre/bin/servertool
rm -rf resources/java/jre/bin/javaws
rm -rf resources/java/jre/lib/javaws.jar
rm -rf resources/java/jre/lib/jfr
rm -rf resources/java/jre/lib/jfr.jar
rm -rf resources/java/jre/lib/oblique-fonts
rm -rf resources/java/jre/lib/desktop
rm -rf resources/java/jre/plugin

# JavaFX Files
rm -rf resources/java/jre/THIRDPARTYLICENSEREADME-JAVAFX.txt
rm -rf resources/java/jre/lib/ant-javafx.jar
rm -rf resources/java/jre/lib/javafx.properties
rm -rf resources/java/jre/lib/jfxswt.jar

# JavaFX native libraries [Microsoft Windows]:
rm -rf resources/java/jre/bin/decora-sse.dll
rm -rf resources/java/jre/bin/fxplugins.dll
rm -rf resources/java/jre/bin/glass.dll
rm -rf resources/java/jre/bin/glib-lite.dll
rm -rf resources/java/jre/bin/gstreamer-lite.dll
rm -rf resources/java/jre/bin/javafx-font.dll
rm -rf resources/java/jre/bin/javafx_font_t2k.dll
rm -rf resources/java/jre/bin/javafx-iio.dll
rm -rf resources/java/jre/bin/jfxmedia.dll
rm -rf resources/java/jre/bin/jfxwebkit.dll
rm -rf resources/java/jre/bin/prism_common.dll
rm -rf resources/java/jre/bin/prism-d3d.dll
rm -rf resources/java/jre/bin/prism_es2.dll
rm -rf resources/java/jre/bin/prism_sw.dll

# JavaFX native libraries [Mac OS X]:
rm -rf resources/java/jre/lib/fxplugins.dylib
rm -rf resources/java/jre/lib/libdecora_sse.so
rm -rf resources/java/jre/lib/libdecora-sse.dylib
rm -rf resources/java/jre/lib/libfxplugins.so
rm -rf resources/java/jre/lib/libglass.dylib
rm -rf resources/java/jre/lib/libglib-lite.dylib
rm -rf resources/java/jre/lib/libgstreamer-lite.dylib
rm -rf resources/java/jre/lib/libjavafx_font_t2k.dylib
rm -rf resources/java/jre/lib/libjavafx-font.dylib
rm -rf resources/java/jre/lib/libjavafx-iio.dylib
rm -rf resources/java/jre/lib/libjfxmedia.dylib
rm -rf resources/java/jre/lib/libjfxwebkit.dylib
rm -rf resources/java/jre/lib/libprism_common.dylib
rm -rf resources/java/jre/lib/libprism_sw.dylib
rm -rf resources/java/jre/lib/libprism-es2.dylib

# JavaFX native libraries [Linux-i586]:
rm -rf resources/java/jre/lib/i386/libdecora_sse.so
rm -rf resources/java/jre/lib/i386/libfxplugins.so
rm -rf resources/java/jre/lib/i386/libglass.so
rm -rf resources/java/jre/lib/i386/libgstreamer-lite.so
rm -rf resources/java/jre/lib/i386/libjavafx_font_freetype.so
rm -rf resources/java/jre/lib/i386/libjavafx_font_pango.so
rm -rf resources/java/jre/lib/i386/libjavafx_font_t2k.so
rm -rf resources/java/jre/lib/i386/libjavafx-font.so
rm -rf resources/java/jre/lib/i386/libjavafx-iio.so
rm -rf resources/java/jre/lib/i386/libjfxmedia.so
rm -rf resources/java/jre/lib/i386/libjfxwebkit.so
rm -rf resources/java/jre/lib/i386/libprism_common.so
rm -rf resources/java/jre/lib/i386/libprism_es2.so
rm -rf resources/java/jre/lib/i386/libprism_sw.so

# JavaFX native libraries [Linux-x64]:
rm -rf resources/java/jre/lib/amd64/libdecora_sse.so
rm -rf resources/java/jre/lib/amd64/libprism_common.so
rm -rf resources/java/jre/lib/amd64/libprism_es2.so
rm -rf resources/java/jre/lib/amd64/libprism_sw.so
rm -rf resources/java/jre/lib/amd64/libfxplugins.so
rm -rf resources/java/jre/lib/amd64/libglass.so
rm -rf resources/java/jre/lib/amd64/libgstreamer-lite.so
rm -rf resources/java/jre/lib/amd64/libjavafx_font_freetype.so
rm -rf resources/java/jre/lib/amd64/libjavafx_font_pango.so
rm -rf resources/java/jre/lib/amd64/libjavafx_font_t2k.so
rm -rf resources/java/jre/lib/amd64/libjavafx-font.so
rm -rf resources/java/jre/lib/amd64/libjavafx-iio.so
rm -rf resources/java/jre/lib/amd64/libjfxmedia.so
rm -rf resources/java/jre/lib/amd64/libjfxwebkit.so
rm -rf resources/java/jre/lib/amd64/libprism-es2.so

exit 0
