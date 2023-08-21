#!/bin/sh
echo 0000
sudo yum install gcc openssl-devel bzip2-devel libffi-devel sqlite-devel;
#rm -rf Python-3.7.6.tgz Python-3.7.6
echo 11111
wget https://www.python.org/ftp/python/3.7.6/Python-3.7.6.tgz;
tar xzf Python-3.7.6.tgz;
#mkdir -p ~/Build/Python3.7.6
#DIR=~/Build/Python3.7.6
#if [ -d "$DIR" ]; then
#    echo "Python3.7.6 is already present"
#else
    #echo "Python3.7.6 NOT found."
    #mkdir -p ~/Build/Python3.7.6 
    #cd Python-3.7.6
    #export pypath=~/Build/Python3.7.6 
    #echo $pypath
    #./configure --enable-optimizations --prefix=$pypath --enable-shared LDFLAGS="-Wl,-rpath,'\$\$ORIGIN/../lib'"
    #make altinstall
#fi

#rm -rf custom_python3.7.6
echo 222222
mkdir custom_python3.7.6;
echo 333333
export pypath=$(pwd)/custom_python3.7.6;
echo 44444
cd Python-3.7.6;
echo $pypath;
./configure --enable-optimizations --prefix=$pypath --enable-shared LDFLAGS="-Wl,-rpath,'\$\$ORIGIN/../lib'";
echo 555555
make altinstall;
echo 66666