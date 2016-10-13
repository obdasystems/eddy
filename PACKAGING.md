## Eddy packaging documentation

Eddy is distributed as different packages:

* `Windows x86` installer (built with InnoSetup)
* `Windows x86` standalone package
* `macOS (Intel)` app bundle (distributed as `.dmg)
* `Linux i386` standalone package
* `Linux amd64` standalone package

# Packaging

To create distribution packages you need to have installed [Python 3.4](https://www.python.org) on your system. 
You also need to have installed [GIT](http://git-scm.com/) on your system and make sure that the `git` command
is in your `$PATH` environment variable. Once the building process is completed you will find the built 
package(s) inside the *dist* directory.

## Windows

Install [Qt 5.5](http://download.qt.io/official_releases/qt/5.5/5.5.1/qt-opensource-windows-x86-mingw492-5.5.1.exe).    
Install [cx_Freeze](https://pypi.python.org/pypi/cx_Freeze/4.3.4).  
Install [InnoSetup](http://www.jrsoftware.org/isinfo.php).  
Install [Oracle JRE 1.8](http://download.oracle.com/otn-pub/java/jdk/8u102-b14/jdk-8u102-windows-i586.exe).  
Download and uncompress [SIP 4.18.1](http://downloads.sourceforge.net/project/pyqt/sip/sip-4.18.1/sip-4.18.1.zip).  
Download and uncompress [PyQt5.5.1](http://downloads.sourceforge.net/project/pyqt/PyQt5/PyQt-5.5.1/PyQt-gpl-5.5.1.zip).  
Bring up command prompt window and navigate to the uncompressed SIP 4.18.1 directory:

    >>> PATH=C:\Qt\5.5\mingw492_32\bin;C:\Qt\Tools\mingw492_32\bin;%PATH%
    >>> python configure.py -p win32-g++
    >>> mingw32-make && mingw32-make install
    
Navigate using the command prompt to the uncompressed PyQt5.5.1 directory:

    >>> python configure.py --spec win32-g++ --disable QtPositioning --no-qsci-api --no-designer-plugin --no-qml-plugin --confirm-license
    >>> mingw32-make && mingw32-make install

Install python required packages:

    >>> pip install -U pip
    >>> pip install -U cython
    >>> pip install -U verlib
    >>> pip install -U mockito-without-hardcoded-distribute-version
    >>> pip install -U mock
    >>> pip install -U nose
    >>> pip install -U nose-cov
    >>> pip install -U natsort
    >>> pip install -U coveralls
    >>> pip install -U pyyaml
    >>> pip install -U Pillow

Change the current active directory and type the following:

    >>> git clone https://github.com/danielepantaleone/eddy.git
    
Make sure to copy Oracle JRE 1.8 `jre` directory in `eddy/resources/java`.  
Go back to the command prompt, and type the following: 

    >>> cd eddy
    >>> python setup.py build_exe
    
## Mac OS

Install Xcode and Xcode command line tools.  
Install [homebrew](http://brew.sh/).  
Install [Python 3.4.4](https://www.python.org/ftp/python/3.4.4/python-3.4.4-macosx10.6.pkg).  
Install [Oracle JRE 1.8](http://download.oracle.com/otn-pub/java/jdk/8u102-b14/jdk-8u102-macosx-x64.dmg).  
Make use of the `configure-build-linux-macOS.sh` to configure the build environment.  
Bring up a terminal window and type the following:
    
    >>> cd ~/Downloads/eddy
    >>> python setup.py bdist_dmg

## Linux 32 (debian based distro)

Make use of the `configure-build-linux-i386.sh` to configure the build environment.  
Bring up a terminal window and type the following:
    
    >>> cd ~/Downloads/eddy
    >>> python setup.py build_exe
    
## Linux 64 (debian based distro)

Make use of the `configure-build-linux-amd64.sh` to configure the build environment.  
Bring up a terminal window and type the following:
    
    >>> cd ~/Downloads/eddy
    >>> python setup.py build_exe