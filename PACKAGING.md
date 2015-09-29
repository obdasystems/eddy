## pyGraphol packaging documentation

pyGraphol is distributed as different packages:

* Python sources package as a zip file
* Python wheel package
* Win32 zip package
* Win32 installer package (built with InnoSetup Installer)
* Linux32 zip package
* Linux64 zip package
* Mac OS .dmg disk image

# Packaging

To create distribution packages you need to have installed Python 3 on your system. You also need 
to have installed [GIT](http://git-scm.com/) on your system and make sure that the `git` command
is in your PATH environment. Once the building process is completed you will find the built package(s) 
inside the  *dist* directory.

## Source and wheel distribution

Bring up a terminal window (or command prompt if on win32 platform) and type the following:
    
    >>> git clone https://github.com/danielepantaleone/pygraphol.git
    >>> cd pygraphol
    >>> python setup.py release

## Windows

Install [Qt 5.5](http://download.qt.io/official_releases/qt/5.5/5.5.0/qt-opensource-windows-x86-mingw492-5.5.0.exe).  
Install [PyQt 5.5](http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5/PyQt5-5.5-gpl-Py3.4-Qt5.5.0-x32.exe).   
Install [cx_Freeze](https://pypi.python.org/pypi/cx_Freeze/4.3.4).  
Bring up command prompt window and type the following:

    >>> git clone https://github.com/danielepantaleone/pygraphol.git
    >>> cd pygraphol
    >>> python setup.py build_exe
    
## Mac OS

Make sure you have installed Xcode and Xcode command line tools.  
Install [homebrew](http://brew.sh/).  
Install [Qt 5.5](http://download.qt.io/official_releases/qt/5.5/5.5.0/qt-opensource-mac-x64-clang-5.5.0.dmg).  
Add `qmake` to your path environment variable: `export PATH=$PATH:~/Qt/5.5/clang_64/bin`.  
Bring up a terminal window and type the following:

    >>> brew install wget
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.9/sip-4.16.9.tar.gz
    >>> tar xzf sip-4.16.9.tar.gz && cd sip-4.16.9
    >>> python3 configure.py
    >>> make -j 5 && make install
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5/PyQt-gpl-5.5.tar.gz
    >>> tar xzf PyQt-gpl-5.5.tar.gz && cd PyQt-gpl-5.5
    >>> python3 configure.py --confirm-license
    >>> make -j 5 && make install
    >>> cd ~/Downloads
    >>> git clone https://github.com/danielepantaleone/pygraphol.git
    >>> cd ~/Downloads/pygraphol
    >>> pip install -r build-requirements.txt
    >>> python setup.py bdist_dmg
