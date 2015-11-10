## Grapholed packaging documentation

Grapholed is distributed as different packages:

* Python sources distribution
* Win32 zip package
* Mac OS .dmg disk image
* Linux32 zip package
* Linux64 zip package

# Packaging

To create distribution packages you need to have installed Python 3 on your system. You also need 
to have installed [GIT](http://git-scm.com/) on your system and make sure that the `git` command
is in your PATH environment. Once the building process is completed you will find the built package(s) 
inside the  *dist* directory.

## Source distribution

Bring up a terminal window (or command prompt if on win32 platform) and type the following:
    
    >>> git clone https://github.com/danielepantaleone/grapholed.git
    >>> cd grapholed
    >>> python setup.py release

## Windows

Install [Qt 5.5](http://download.qt.io/official_releases/qt/5.5/5.5.0/qt-opensource-windows-x86-mingw492-5.5.0.exe).    
Install [cx_Freeze](https://pypi.python.org/pypi/cx_Freeze/4.3.4).  
Download and uncompress [SIP 4.17](http://sourceforge.net/projects/pyqt/files/sip/sip-4.17/sip-4.17.zip).
Download and uncompress [PyQt5.5](http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5/PyQt-gpl-5.5.zip)
Bring up command prompt window and navigate to the uncompressed SIP 4.17 directory:

    >>> PATH=C:\Qt\5.5\mingw492_32\bin;C:\Qt\Tools\mingw492_32\bin;%PATH%
    >>> python configure.py -p win32-g++
    >>> mingw32-make && mingw32-make install
    
Navigate using the command prompt to the uncompressed PyQt5.5 directory:

    >>> python configure.py --spec win32-g++
    >>> mingw32-make && mingw32-make install

Change the current active directory and type the following:

    >>> git clone https://github.com/danielepantaleone/grapholed.git
    >>> cd grapholed
    >>> python setup.py build_exe
    
## Mac OS

Make sure you have installed Xcode and Xcode command line tools.  
Install [homebrew](http://brew.sh/).  
Install [Qt 5.5](http://download.qt.io/official_releases/qt/5.5/5.5.0/qt-opensource-mac-x64-clang-5.5.0.dmg).  
Bring up a terminal window and type the following:
    
    >>> export PATH=$PATH:~/Qt/5.5/clang_64/bin
    >>> brew install wget
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.17/sip-4.17.tar.gz
    >>> tar xzf sip-4.17.tar.gz && cd sip-4.17
    >>> python3 configure.py
    >>> make -j 5 && make install
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5/PyQt-gpl-5.5.tar.gz
    >>> tar xzf PyQt-gpl-5.5.tar.gz && cd PyQt-gpl-5.5
    >>> python3 configure.py --confirm-license
    >>> make -j 5 && make install
    >>> cd ~/Downloads
    >>> git clone https://github.com/danielepantaleone/grapholed.git
    >>> cd ~/Downloads/grapholed
    >>> pip install -r build-requirements.txt
    >>> python setup.py bdist_dmg

## Linux 32 (debian based distro)

Install [Qt 5.5](http://download.qt.io/official_releases/qt/5.5/5.5.0/qt-opensource-linux-x86-5.5.0.run).
Bring up a terminal window and type the following:

    >>> sudo apt-get install build-essentials libssl-dev python3-pip python3-dev git
    >>> sudo pip3 install setuptools --upgrade
    >>> sudo pip3 install pip --upgrade
    >>> PATH="~/Qt/5.5/gcc/bin:$PATH"
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.17/sip-4.17.tar.gz
    >>> tar xzf sip-4.17.tar.gz && cd sip-4.17
    >>> python3 configure.py
    >>> make -j 5 && sudo make install
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5/PyQt-gpl-5.5.tar.gz
    >>> tar xzf PyQt-gpl-5.5.tar.gz && cd PyQt-gpl-5.5
    >>> python3 configure.py --confirm-license
    >>> make -j 5 && sudo make install
    >>> cd ~/Downloads
    >>> git clone https://github.com/danielepantaleone/grapholed.git
    >>> cd ~/Downloads/grapholed
    >>> sudo pip3 install -r build-requirements.txt
    >>> python setup.py build_exe
    
## Linux 64 (debian based distro)

Install [Qt 5.5](http://download.qt.io/official_releases/qt/5.5/5.5.0/qt-opensource-linux-x64-5.5.0-2.run).
Bring up a terminal window and type the following:

    >>> sudo apt-get install build-essentials libssl-dev python3-pip python3-dev git
    >>> sudo pip3 install setuptools --upgrade
    >>> sudo pip3 install pip --upgrade
    >>> PATH="~/Qt/5.5/gcc_64/bin:$PATH"
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.17/sip-4.17.tar.gz
    >>> tar xzf sip-4.17.tar.gz && cd sip-4.17
    >>> python3 configure.py
    >>> make -j 5 && sudo make install
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5/PyQt-gpl-5.5.tar.gz
    >>> tar xzf PyQt-gpl-5.5.tar.gz && cd PyQt-gpl-5.5
    >>> python3 configure.py --confirm-license
    >>> make -j 5 && sudo make install
    >>> cd ~/Downloads
    >>> git clone https://github.com/danielepantaleone/grapholed.git
    >>> cd ~/Downloads/grapholed
    >>> sudo pip3 install -r build-requirements.txt
    >>> python setup.py build_exe
    
