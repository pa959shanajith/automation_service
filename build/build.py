import subprocess
import os
import sys
from os.path import splitext, join, dirname
from sys import executable as python
sl = os.sep
pythondir = dirname(python)+sl #remove python.exe
errorcount = 0
cwd = os.getcwd() + sl + "src"
pymajor = str(sys.version_info.major)
pyminor = str(sys.version_info.minor)
print("Building process initiated....")
if not os.path.exists(cwd): raise RuntimeError("'src' directory not found! Aborting process...")
print("Working in " + cwd)

def build_c(full_path, ffile, exe_args=False):
    global errorcount
    try:
        exe_args = " --embed" if exe_args else ''
        cython_process = subprocess.Popen(python+" -m cython -"+pymajor+' -o '+ffile+'.c '+full_path+exe_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = cython_process.communicate()
        exitcode = cython_process.returncode
        if not exitcode == 0:
            errorcount = errorcount + 1
            out = out.decode('utf-8')
            err = err.decode('utf-8')
            print(full_path + "\n" + out + '\n' + err)
            file_refer.write(str(full_path)+"\nError:"+ str(err)+"\nOutput:"+ str(out)+"\n------- \n")
            return -1
    except subprocess.CalledProcessError as e:
        errorcount = errorcount + 1
        print(e)
        return -1

def build_o(full_path, ffile):
    global errorcount
    try:
        gcc_process = subprocess.Popen("gcc -c -I"+pythondir+"include -DMS_WIN64 -o "+ffile+".o "+ffile+".c", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True)
        out, err = gcc_process.communicate()
        exitcode = gcc_process.returncode
        if not exitcode == 0:
            errorcount = errorcount + 1
            print(ffile+".c\n" + out.decode('utf-8') + '\n' + err.decode('utf-8'))

        #if os.path.isfile(ffile+".o"):
        #    if os.path.isfile(full_path): subprocess.check_call("del "+full_path, shell = True)
    except subprocess.CalledProcessError as e:
        errorcount = errorcount + 1
        print(e)
        return -1

def build_exe(source, target):
    global errorcount
    try:
        #gcc_process = subprocess.Popen("gcc "+source+" -municode -mconsole -L"+pythondir+"libs -o "+target+" -lpython"+pymajor+pyminor, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True)
        gcc_process = subprocess.Popen("gcc -I"+pythondir+"include -DMS_WIN64 "+source+" ./build/avo_ico.res -municode -mconsole -L"+pythondir+"libs -o "+target+" -lpython"+pymajor+pyminor, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True)
        out, err = gcc_process.communicate()
        exitcode = gcc_process.returncode
        if not exitcode == 0:
            errorcount = errorcount + 1
            print("Error while generating "+os.path.basename(target)+"\n" + out.decode('utf-8') + '\n' + err.decode('utf-8'))

        #if os.path.isfile(ffile+".o"):
        #    if os.path.isfile(full_path): subprocess.check_call("del "+full_path, shell = True)
    except subprocess.CalledProcessError as e:
        errorcount = errorcount + 1
        print(e)
        return -1

def build_all(path):
    global errorcount
    files_list = ["das"]
    for root, dirs, files in os.walk(path):
        print("\n\nDirectory = "+root+"\n")
        for file in files:
            exe_args = False
            file, extn = splitext(file) #removing extesnion
            if extn == ".py":
                full_path = os.path.normpath(join(root, file+".py"))
                if file == "das_service_manager": exe_args = True
                elif file != "das": files_list.append(file)
                ffile = cwd+sl+file
                build_c(full_path, ffile, exe_args)
                #build_o(full_path, ffile)
    combine_file = os.path.abspath(dirname(__file__) + sl + "combine.py")
    combine_process = subprocess.Popen(python+' '+combine_file+' '+' '.join(files_list)+" -o "+cwd+sl+"combine.c", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True)
    out,err = combine_process.communicate()
    exitcode = combine_process.returncode
    if not exitcode == 0:
        errorcount = errorcount + 1
        print("Error while generating combine.c\n" + out.decode('utf-8') + '\n' + err.decode('utf-8'))
    #build_o(combine_file, cwd+sl+'combine')
    files_list.insert(0, "combine")
    build_exe(" ".join([cwd+sl+f+".c" for f in files_list]), "AvoAssureDAS.exe")
    build_exe(cwd+sl+"das_service_manager.c", "AvoAssureDASservice.exe")
    #os.system("del *.o *.c")

file_refer = open('../cython_error.txt','a')
build_all(cwd)
file_refer.close()
if errorcount > 0:
    raise RuntimeError("BUILD FAILED : There are "+ str(errorcount) + " no of errors")
else:
    print("Build Succeeded!")
