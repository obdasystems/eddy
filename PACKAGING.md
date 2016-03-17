## Eddy packaging documentation

Eddy is distributed as different packages:

* `Win32` installer (built with InnoSetup)
* `Win32` zip package
* `Mac OS` .dmg disk image
* `Linux32` zip package
* `Linux64` zip package

# Packaging

To create distribution packages you need to have installed [Python 3.4](https://www.python.org) on your system. 
You also need to have installed [GIT](http://git-scm.com/) on your system and make sure that the `git` command
is in your `$PATH` environment variable. Once the building process is completed you will find the built 
package(s) inside the *dist* directory.

## Windows

Install [Qt 5.5](http://download.qt.io/official_releases/qt/5.5/5.5.1/qt-opensource-windows-x86-mingw492-5.5.1.exe).    
Install [cx_Freeze](https://pypi.python.org/pypi/cx_Freeze/4.3.4).  
Install [InnoSetup](http://www.jrsoftware.org/isinfo.php).  
Download and uncompress [SIP 4.17](http://sourceforge.net/projects/pyqt/files/sip/sip-4.17/sip-4.17.zip).  
Download and uncompress [PyQt5.5](http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5.1/PyQt-gpl-5.5.1.zip).  
Bring up command prompt window and navigate to the uncompressed SIP 4.17 directory:

    >>> PATH=C:\Qt\5.5\mingw492_32\bin;C:\Qt\Tools\mingw492_32\bin;%PATH%
    >>> python configure.py -p win32-g++
    >>> mingw32-make && mingw32-make install
    
Navigate using the command prompt to the uncompressed PyQt5.5.1 directory:

    >>> python configure.py --spec win32-g++
    >>> mingw32-make && mingw32-make install

Install python required packages:

    >>> pip install -r build-requirements.txt
    >>> pip install -r requirements.txt

Change the current active directory and type the following:

    >>> git clone https://github.com/danielepantaleone/eddy.git
    >>> cd eddy
    >>> python setup.py build_exe
    
## Mac OS

Make sure you have installed Xcode and Xcode command line tools.  
Install [homebrew](http://brew.sh/).  
Install [Qt 5.5.1](http://download.qt.io/official_releases/qt/5.5/5.5.1/qt-opensource-mac-x64-clang-5.5.1.dmg).  
Bring up a terminal window and type the following:
    
    >>> brew install wget
    >>> pip install virtualenv --upgrade
    >>> cd ~
    >>> virtualenv python34
    >>> source python34/bin/activate
    >>> pip install setuptools --upgrade
    >>> pip install pip --upgrade
    >>> pip install cx_Freeze --upgrade
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.17/sip-4.17.tar.gz
    >>> tar xf sip-4.17.tar.gz
    >>> cd sip-4.17
    >>> python configure.py
    >>> make
    >>> make install
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5.1/PyQt-gpl-5.5.1.tar.gz
    >>> tar xf PyQt-gpl-5.5.1.tar.gz
    >>> cd PyQt-gpl-5.5.1
    >>> python configure.py --qmake ~/Qt/5.5/clang_64/bin/qmake --disable QtPositioning --no-qsci-api --no-designer-plugin --no-qml-plugin --confirm-license
    >>> make
    >>> make install
    >>> cd ~/Downloads
    >>> git clone https://github.com/danielepantaleone/eddy.git
    >>> cd ~/Downloads/eddy
    >>> pip install -r build-requirements.txt
    >>> pip install -r requirements.txt
    >>> python setup.py bdist_dmg

## Linux 32 (debian based distro)

Bring up a terminal window and type the following:

    >>> sudo apt-get install -y build-essential libgl1-mesa-dev libx11-dev libxext-dev libxfixes-dev libxi-dev
    >>> sudo apt-get install -y libxrender-dev libxcb1-dev libx11-xcb-dev libxcb-glx0-dev libfontconfig1-dev 
    >>> sudo apt-get install -y libfreetype6-dev libcups2-dev git mercurial python3 python3-dev
    >>> sudo pip3 install virtualenv --upgrade
    >>> cd ~
    >>> virtualenv python34
    >>> source python34/bin/activate
    >>> sudo pip3 install setuptools --upgrade
    >>> sudo pip3 install pip --upgrade
    >>> cd ~/Downloads
    >>> wget wget http://download.qt.io/official_releases/qt/5.5/5.5.1/qt-opensource-linux-x86-5.5.1.run
    >>> chmod +x qt-opensource-linux-x86-5.5.1.run
    >>> ./ qt-opensource-linux-x86-5.5.1.run
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.17/sip-4.17.tar.gz
    >>> tar xf sip-4.17.tar.gz
    >>> cd sip-4.17
    >>> python configure.py
    >>> make -j 3
    >>> sudo make install
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5.1/PyQt-gpl-5.5.1.tar.gz
    >>> tar xf PyQt-gpl-5.5.1.tar.gz
    >>> cd PyQt-gpl-5.5.1
    >>> python configure.py --qmake ~/Qt5.5.1/5.5/gcc/bin/qmake --disable QtPositioning --no-qsci-api --no-designer-plugin --no-qml-plugin --confirm-license
    >>> make -j 3
    >>> sudo make install
    >>> cd ~/Downloads
    >>> hg clone https://danielepantaleone@bitbucket.org/danielepantaleone/cx_freeze
    >>> cd cx_freeze
    >>> hg pull && hg update ubuntu
    >>> python setup.py build
    >>> python setup.py install
    >>> cd ~/Downloads
    >>> git clone https://github.com/danielepantaleone/eddy.git
    >>> cd eddy
    >>> pip install -r build-requirements.txt
    >>> pip install -r requirements.txt
    >>> python setup.py build_exe
    
## Linux 64 (debian based distro)

Bring up a terminal window and type the following:
    
    >>> sudo apt-get install -y build-essential libgl1-mesa-dev libx11-dev libxext-dev libxfixes-dev libxi-dev
    >>> sudo apt-get install -y libxrender-dev libxcb1-dev libx11-xcb-dev libxcb-glx0-dev libfontconfig1-dev 
    >>> sudo apt-get install -y libfreetype6-dev libcups2-dev git mercurial python3 python3-dev
    >>> sudo pip3 install virtualenv --upgrade
    >>> cd ~
    >>> virtualenv python34
    >>> source python34/bin/activate
    >>> sudo pip3 install setuptools --upgrade
    >>> sudo pip3 install pip --upgrade
    >>> cd ~/Downloads
    >>> wget wget http://download.qt.io/official_releases/qt/5.5/5.5.1/qt-opensource-linux-x64-5.5.1.run
    >>> chmod +x qt-opensource-linux-x64-5.5.1.run
    >>> ./ qt-opensource-linux-x64-5.5.1.run
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.17/sip-4.17.tar.gz
    >>> tar xf sip-4.17.tar.gz
    >>> cd sip-4.17
    >>> python configure.py
    >>> make -j 3
    >>> sudo make install
    >>> cd ~/Downloads
    >>> wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5.1/PyQt-gpl-5.5.1.tar.gz
    >>> tar xf PyQt-gpl-5.5.1.tar.gz
    >>> cd PyQt-gpl-5.5.1
    >>> python configure.py --qmake ~/Qt5.5.1/5.5/gcc_64/bin/qmake --disable QtPositioning --no-qsci-api --no-designer-plugin --no-qml-plugin --confirm-license
    >>> make -j 3
    >>> sudo make install
    >>> cd ~/Downloads
    >>> hg clone https://danielepantaleone@bitbucket.org/danielepantaleone/cx_freeze
    >>> cd cx_freeze
    >>> hg pull && hg update ubuntu
    >>> python setup.py build
    >>> python setup.py install
    >>> cd ~/Downloads
    >>> git clone https://github.com/danielepantaleone/eddy.git
    >>> cd eddy
    >>> pip install -r build-requirements.txt
    >>> pip install -r requirements.txt
    >>> python setup.py build_exe