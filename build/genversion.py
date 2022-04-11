#-------------------------------------------------------------------------------
# Name:        Generate Package Build and Release Version
# Purpose:
#
# Author:      ranjan.agrawal
#
# Created:     26-02-2019
# Copyright:   (c) ranjan.agrawal 2019
#-------------------------------------------------------------------------------

import os
import re
import sys
import platform
from subprocess import Popen, PIPE
from datetime import datetime

if platform.system() == "Windows": FILTER_ARG = "find"
else: FILTER_ARG = "grep"
GRAPH_CMD = ["git", "log", "--graph", "--decorate", "--oneline"]
FILTER_CMD = ["origin/master", "origin/production_3.", "origin/production_2.", "production"]
TAG_CMD = ["git", "ls-remote", "--tags", ".git"]
OUT_FILE = './out.txt'
RUNTIME_ERROR = RuntimeError("Error while generating version")

def env(key):
    if key in os.environ:
        #print(key+" is "+os.environ[key])
        return os.environ[key]
    return ""

def process_out(refs):
    file_ref = open(OUT_FILE, 'r')
    chk = Popen(FILTER_ARG + ' "'+refs+'"', stderr=PIPE, stdout=PIPE, stdin=file_ref)
    out, err = chk.communicate()
    file_ref.close()
    if err:
        print(err)
        return "error"
    if sys.version_info.major == 3:
        out = out.decode('utf-8')
    if len(out.strip()) == 0: return ''
    if "master" in refs: return env("MINOR_VERSION")
    pstr = r"production_3\.[0-9]+"
    if "2" in refs: r"production_2\.[0-9]+"
    matches = re.findall(pstr, out)
    if len(matches) == 0: return ''
    return matches[0][13:]

def get_minor_ver():
    global DEV_ENV, MAJOR_VERSION
    if BRANCH == "master" or env("DEV_BUILD").strip()=="TRUE": return env("MINOR_VERSION")
    elif BRANCH.startswith("production_3."): return BRANCH[13:]
    elif BRANCH.startswith("production_2."):
        MAJOR_VERSION = "2"
        return BRANCH[13:]

    file_ref = open(OUT_FILE, 'w+')
    graph_out = Popen(GRAPH_CMD, stderr=PIPE, stdout=file_ref)
    file_ref.close()
    err = graph_out.communicate()[1]
    if err:
        print(err)
        raise RUNTIME_ERROR
    processed = ""
    for c in FILTER_CMD:
        processed = process_out(c)
        if processed == "error":
            raise RUNTIME_ERROR
        elif len(processed) != 0:
            if "2" in c:
                MAJOR_VERSION = "2"
            break
    if len(processed) == 0:
        DEV_ENV = True
        processed = env("MINOR_VERSION")
        print("Failed to find a parent branch to get minor version.\n"+
            "Assuming 'master' as parent.\n"+
            "Since, branch source is invalid, switching build to DEV mode")
    os.remove(OUT_FILE)
    return processed


def get_patch_ver():
    ver = MAJOR_VERSION+r"\."+MINOR_VERSION+r"\."
    TAG_CMD.append(ver+"[0-9]*")
    tag_out = Popen(TAG_CMD, stderr=PIPE, stdout=PIPE)
    out, err = tag_out.communicate()
    if err:
        print(err)
        raise RUNTIME_ERROR
    if sys.version_info.major == 3:
        out = out.decode('utf-8')
    if len(out) == 0: return ("0" + (DEV_ENV and "-rc.1"))
    matches = re.findall(ver+"([0-9]{0,9})\n", out)
    matches.sort(key=int)
    iver = str(int(matches[-1])+1) if len(matches) > 0 else "0"
    ser = ""
    if DEV_ENV:
        ser = iver + r"-rc."
        ver = ver + ser[:-1] + r"\."
        matches = re.findall(ver+"([0-9]{0,9})\n", out)
        matches.sort(key=int)
        iver = str(int(matches[-1])+1) if len(matches) > 0 else "1"
    return ser + iver

DEV_ENV = len(env("PROD").strip()) == 0
CBU = env("CBU").strip() or "Internal"
BRANCH = env("TARGET_BRANCH").strip() or "master"
MAJOR_VERSION = env("MAJOR_VERSION").strip()
MINOR_VERSION = get_minor_ver()
PATCH_VERSION = get_patch_ver()

RELEASE_VERSION = MAJOR_VERSION+"."+MINOR_VERSION+"."+PATCH_VERSION
print("Release number for patch is "+RELEASE_VERSION)
os.system("echo "+RELEASE_VERSION+">buildno.txt")
TAG_MSG = "Release Version "+RELEASE_VERSION.split("-")[0]+((" RC "+PATCH_VERSION.split('.')[-1]) if DEV_ENV else '')
if platform.system() == "Windows":
    with open("env.bat","w+") as exportenv:
        exportenv.write("SET BUILD_ENV="+("DEV" if DEV_ENV else "PROD")+"\nSET BUILD_VERSION="+
          RELEASE_VERSION+"\nSET MAJOR_VERSION="+MAJOR_VERSION+"\nSET MINOR_VERSION="+
          MINOR_VERSION+"\nSET PATCH_VERSION="+PATCH_VERSION+"\nSET TAG_MSG="+TAG_MSG)
else:
    with open("env.sh","w+") as exportenv:
        exportenv.write("#!/bin/sh\nexport BUILD_ENV="+("DEV" if DEV_ENV else "PROD")+
          "\nexport BUILD_VERSION="+RELEASE_VERSION+"\nexport MAJOR_VERSION="+MAJOR_VERSION+
          "\nexport MINOR_VERSION="+MINOR_VERSION+"\nexport PATCH_VERSION="+PATCH_VERSION+
          '\nexport TAG_MSG="'+TAG_MSG+'"')
    try:
        os.system("chmod +x ./env.sh")
    except:
        pass
