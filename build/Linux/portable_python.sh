#!/bin/sh

PYVER=3.7
PYINCLUDE=${PYVER}
if [ ${PYINCLUDE} == '3.7' ]; then
  PYINCLUDE=3.7m
fi


#PYSRC=/usr/local/ (if python present in system level)
PYSRC=~/python${PYVER}.6
#BASE=$(pwd)/LicenseServer
BASE=$(pwd)
#BASE=$(pwd)/PP_cloud
echo "Cleared Old files"
rm -rf ${BASE}
echo "Initializing VENV Setup"
mkdir ${BASE}
echo "Copying python lib items from Framework install"
cp -R -f ${PYSRC}/lib ${BASE}/
echo "Setting up VENV"
${PYSRC}/bin/python${PYVER} -m pip install virtualenv==16.7.10
${PYSRC}/bin/python${PYVER} -m virtualenv --always-copy ${BASE}
${PYSRC}/bin/python${PYVER} -m virtualenv --relocatable ${BASE}
cd ${BASE}

echo "Creating symlinks"
ln -s -f bin/python python

cd ${BASE}/bin
echo "Rectifying Portability of virtualenv"
echo 'import sys, os'>rectify_portability.py
echo 'with open("activate","r") as f:'>>rectify_portability.py
echo '  data = f.readlines()'>>rectify_portability.py
echo 'for i in range(len(data)):'>>rectify_portability.py
echo '  if data[i].startswith("VIRTUAL_ENV="):'>>rectify_portability.py
echo '    data[i]="""VIRTUAL_ENV="$(cd "$(dirname $(dirname ${BASH_SOURCE-}))"; pwd)" """[:-1]+data[i][-1:]'>>rectify_portability.py
echo 'with open("activate","w") as f:'>>rectify_portability.py
echo '  f.write("".join(data))'>>rectify_portability.py
echo 'name=os.environ.get("_PYTHON_SYSCONFIGDATA_NAME","_sysconfigdata_{abi}_{platform}_{multiarch}".format(abi=sys.abiflags,platform=sys.platform,multiarch=getattr(sys.implementation, "_multiarch", "")))'>>rectify_portability.py
echo 'cp=os.path.abspath(os.getcwd()+"/../lib/python'$PYVER'/"+name+".py")'>>rectify_portability.py
echo 'with open(cp,"r") as f:'>>rectify_portability.py
echo '  data = f.readlines()'>>rectify_portability.py
echo 'data=[data[0],"import sys, os\n","pydir=os.path.dirname(os.path.abspath(sys.executable))\n","""if pydir[-3:] == "bin": pydir=os.path.dirname(pydir)\n"""]+data[1:]'>>rectify_portability.py
echo 'pysrc="'$PYSRC'"'>>rectify_portability.py
echo 'for i in range(len(data)):'>>rectify_portability.py
echo '  if pysrc in data[i]:'>>rectify_portability.py
echo '    data[i]=data[i].replace(pysrc,"'"'"'+pydir+'"'"'")'>>rectify_portability.py
echo 'with open(cp,"w") as f:'>>rectify_portability.py
echo '  f.write("".join(data))'>>rectify_portability.py
./python -B rectify_portability.py
rm -f rectify_portability.py
cd ${BASE}
if [ -f "pip-selfcheck.json" ]; then rm -f pip-selfcheck.json; fi
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

echo "completed creating portable python"
