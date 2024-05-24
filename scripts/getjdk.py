#!/usr/bin/env python3
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

"""Utility script to download JDKs from adoptium.net."""


import argparse
import json
import logging
import os
import platform
import shutil
import sys
import urllib.parse
import urllib.request
import tarfile
import zipfile

API_ENDPOINT = 'https://api.adoptium.net/v3'
ARCH = platform.machine()
IS_64BIT = sys.maxsize > 2**32
IS_CROSS = False
IS_FREEBSD = sys.platform.startswith('freebsd')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwin')
IS_WIN = sys.platform.startswith('win') or sys.platform.startswith('cygwin')
USER_AGENT = 'curl/7.79.1'

LOGGER = logging.getLogger('getjdk')
LOGGER.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))
LOGGER.addHandler(_handler)


def param_arch(sysarch):
    """
    Returns the architecture's identifier string suitable for requests to api.adoptium.net.
    :type sysarch: str
    :rtype: str
    """
    return {
        'i386': 'x32',
        'i486': 'x32',
        'i586': 'x32',
        'i686': 'x32',
        'amd64': 'x64',
        'x86_64': 'x64',
        'armvhf': 'arm',
        'armv6l': 'arm',
        'armv7l': 'arm',
        'armv8l': 'arm',
    }.get(sysarch.lower(), sysarch.lower())


def param_os(osname):
    """
    Returns the os name suitable for requests to api.adoptium.net.
    :type osname: str
    :rtype: str
    """
    if osname.lower().startswith('aix'):
        return 'aix'
    elif osname.lower().startswith('darwin'):
        return 'mac'
    elif osname.lower().startswith('linux'):
        return 'linux'
    elif osname.lower().startswith('solaris'):
        return 'solaris'
    elif osname.lower().startswith('win'):
        return 'windows'
    else:
        return osname


def progress_callback(transferred, bsize, tsize):
    """
    Callback to show download progress for urllib.request.urlretrieve.
    :param transferred: the number of transferred blocks so far
    :param bsize:  the block size in bytes
    :param tsize:  the total file size in bytes
    """
    csize = transferred * bsize
    progress = csize / tsize * 100
    mbsize = tsize >> 20
    print('\r{0:.1f}% / 100% ({1:.1f} MB)'.format(progress, mbsize),
          end='' if progress < 100.0 else '\n')


def main(args):
    """
    Entry point.
    :type args: list
    """
    # PARSE COMMAND LINE ARGUMENTS
    parser = argparse.ArgumentParser(
        description='Client to interact with api.adoptium.net.',
        epilog='example:\n'
               '  %(prog)s --binary --os linux --arch x64 --feature-version 11 --image-type jdk')
    # MAIN QUERY PARAMETERS
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--assets', action='store_true',
        help='List all assets that match the specified parameters.')
    group.add_argument(
        '--binary', action='store_true',
        help='Download the JDK binary that matches the specified parameters.')
    #group.add_argument(
    #    '--info', action='store_true',
    #    help='Query info about available JDKs matching the specified parameters.')
    group.add_argument(
        '--latest', action='store_true',
        help='Query for latest asset that matches the specified parameters.')
    # QUERY PARAMETERS
    parser.add_argument('--arch', type=str,
                        default=param_arch(platform.machine()),
                        help='Query for the specified cpu architecture, '
                             'defaults to current architecture.')
    parser.add_argument('--extract-to', type=str,
                        help='Path where to extract the downloaded asset.')
    parser.add_argument('--feature-version', type=int, required=True,
                        help='The JDK feature version to query for. '
                             'Feature versions are whole numbers (e.g. 8,11,17).')
    parser.add_argument('--heap-size', type=str, default='normal',
                        choices=('normal', 'large'),
                        help='Heap size, defaults to normal.')
    parser.add_argument('--image-type', type=str, default='jdk',
                        choices=('jdk', 'jre', 'testimage', 'debugimage',
                                 'staticlibs', 'sources'),
                        help='Query for image type, defaults to jdk.')
    parser.add_argument('--jvm-impl', type=str, default='hotspot',
                        choices=('hotspot', 'openj9', 'dragonwell'),
                        help='JVM implementation, defaults to hotspot.')
    parser.add_argument('--os', type=str, default=param_os(sys.platform),
                        choices=('linux', 'windows', 'mac',
                                 'solaris', 'aix', 'alpine-linux'),
                        help='Query for the specified os, defaults to the current os.')
    parser.add_argument('--output-file', type=argparse.FileType('w'),
                        help='The file name to save the output to.')
    parser.add_argument('--release-type', type=str, default='ga',
                        choices=('ga', 'ea'),
                        help='The type of release. Either a release version, '
                             'known as General Availability(ga) or an Early Access(ea). '
                             'Defaults to ga.')
    parser.add_argument('--vendor', type=str, default='eclipse',
                        choices=('adoptopenjdk', 'openjdk',
                                 'eclipse', 'alibaba', 'ibm'),
                        help='The JVM vendor, defaults to eclipse.')
    parser.add_argument('--libc', type=str, default=None,
                        choices=('glibc', 'musl'),
                        help='C library type, implies image_type set to staticlibs.')
    parser.add_argument('--project', type=str, default=None,
                        choices=('jdk', 'valhalla', 'metropolis',
                                 'jfr', 'shenandoah'),
                        help='Project to query for, defaults to jdk.')
    options = parser.parse_args(args)

    # PROCESS REQUEST
    try:
        # LIST ASSET(S)
        if options.assets or options.latest:
            url = '{api_endpoint}/assets/latest' \
                  '/{feature_version}/{jvm_impl}' \
                .format(api_endpoint=API_ENDPOINT,
                        feature_version=options.feature_version,
                        jvm_impl=options.jvm_impl)
            LOGGER.info('API request: %s', url)
            request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read())
                if options.latest:
                    # APPLY ADDITIONAL FILTERS
                    data = list(filter(
                        lambda asset: asset['binary']['os'] == options.os and
                                      asset['binary']['architecture'] == options.arch and
                                      asset['binary']['heap_size'] == options.heap_size and
                                      asset['binary']['image_type'] == options.image_type and
                                      asset['binary']['jvm_impl'] == options.jvm_impl and
                                      asset['version']['major'] == options.feature_version,
                        data))
                # DUMP ASSET(S)
                print(json.dumps(data, indent=2))
        # DOWNLOAD BINARY REQUEST
        elif options.binary:
            url = '{api_endpoint}/binary/latest' \
                  '/{feature_version}/{release_type}' \
                  '/{os}/{arch}/{image_type}' \
                  '/{jvm_impl}/{heap_size}/{vendor}' \
                .format(api_endpoint=API_ENDPOINT,
                        feature_version=options.feature_version,
                        release_type=options.release_type,
                        os=options.os,
                        arch=options.arch,
                        image_type=options.image_type,
                        jvm_impl=options.jvm_impl,
                        heap_size=options.heap_size,
                        vendor=options.vendor)
            params = urllib.parse.urlencode({k: v for k, v in {
                'c_lib': options.libc,
                'project': options.project,
            }.items() if v})
            if params:
                url += '?' + params
            LOGGER.info('API request: %s', url)
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', USER_AGENT)]
            urllib.request.install_opener(opener)
            path, response = urllib.request.urlretrieve(url, reporthook=progress_callback)
            # EXTRACT TO DIR IF REQUESTED
            if options.extract_to:
                os.makedirs(os.path.normpath(options.extract_to), exist_ok=True)
                LOGGER.info('Extracting to: %s', options.extract_to)
                if param_os(options.os) == 'windows':
                    with zipfile.ZipFile(path, 'r') as archive:
                        archive.extractall(options.extract_to)
                else:
                    with tarfile.open(path, 'r:gz') as archive:
                        archive.extractall(options.extract_to, filter='tar')
            # OR MOVE FROM TEMP AS IS
            else:
                if options.output_file:
                    LOGGER.info('Saving to: %s', options.output_file)
                    shutil.move(path, options.output_file)
                elif response.get_filename():
                    LOGGER.info('Saving to: %s', response.get_filename())
                    shutil.move(path, response.get_filename())
                else:
                    LOGGER.warning('Unable to determine output file name, '
                                   'leaving as: %s', path)
            urllib.request.urlcleanup()
        else:
            LOGGER.error('Unknown request type')
            return 2
    except BaseException as e:
        LOGGER.exception('Error during request: %s', e)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        # PERFORM ANY LAST MOMENT CLEANUP
        urllib.request.urlcleanup()
        sys.exit(1)
