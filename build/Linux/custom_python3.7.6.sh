#!/bin/sh
sudo yum install gcc openssl-devel bzip2-devel libffi-devel sqlite-devel;
wget https://www.python.org/ftp/python/3.7.6/Python-3.7.6.tgz
tar xzf Python-3.7.6.tgz;
mkdir -p ~/Build/Python3.7.6
DIR=~/Build/Python3.7.6
if [ -d "$DIR" ]; then
    echo "Python3.7.6 is already present"
else
    echo "Python3.7.6 NOT found."
    #mkdir -p ~/Build/Python3.7.6 
    cd Python-3.7.6
    export pypath=~/Build/Python3.7.6 
    echo $pypath
    ./configure --enable-optimizations --prefix=$pypath --enable-shared LDFLAGS="-Wl,-rpath,'\$\$ORIGIN/../lib'"
    make altinstall
fi