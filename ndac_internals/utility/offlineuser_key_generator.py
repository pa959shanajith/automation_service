#-------------------------------------------------------------------------------
# Name:        offlineuser_key_generator.py
# Purpose:      POC keyfile generator
#
# Author:      vishvas.a
#
# Created:     07/08/2017
# Copyright:   (c) vishvas.a 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import argparse
import sys
import ast
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
##subparsers = parser.add_subparsers()
##parser_start = subparsers.add_parser("User Details", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("INPUT DETAILS:", help="{MACADDRESS};STARTDATE;ENDDATE"
                    +"\n\nDATE FORMAT : mm/dd/yyyy{-hhmmss}"
                    +"\nSPECIFYING MACADDRESS and TIME IS OPTIONAL"
                    +"\nSpecify NO , if MACADDRESS is not provided.")
args = parser.parse_args()

from Crypto import Random
from Crypto.Cipher import AES
BS = 16
offgen='\x69\x41\x6d\x4e\x6f\x74\x4f\x6e\x6c\x69\x6e\x65\x55\x73\x65\x72\x49\x4e\x65\x65\x64\x4e\x6f\x74\x52\x65\x67\x69\x73\x74\x65\x72'
contents =   {
	"offlinereginfo": {
		"mac": "",
		"startdate": "",
		"enddate": ""
	},
    "licensedata": {
        "allowedIceSessions" : 5,
        "allowedMacAddresses": ["XX-XX-XX-XX-XX-XX"],
        "plugins" : {
            "alm" : True,
            "deadcode" : True,
            "weboccular" : True,
            "mindmap" : True,
            "ice" : {
                "web" : True,
                "mobileapp" : True,
                "desktop" : True,
                "mainframe" : True,
                "webservice" : True,
                "oebs" : True,
                "sap" : True,
                "mobileweb" : True
            },
            "neuron3d" : True,
            "reports" : True,
            "neuron2d" : True,
            "dashboard" : True,
            "autogenpath" : True,
            "oxbowcode" : True
        }
    }
}

def pad(data):
    padding = BS - len(data) % BS
    return data + padding * chr(padding)

##def unpad(data):
##    return data[0:-ord(data[-1])]
##
##def unwrap(hex_data, key, iv='0'*16):
##    data = ''.join(map(chr, bytearray.fromhex(hex_data)))
##    aes = AES.new(key, AES.MODE_CBC, iv)
##    return unpad(aes.decrypt(data))

def wrap(data, key, iv='0'*16):
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(data)).encode('hex')

def jsoncreator(macid,startdate,enddate,allowedMacs):
##    global contents
##    contents = ast.literal_eval(contents)
##    print contents
    contents['offlinereginfo']['mac'] = macid
    contents['offlinereginfo']['startdate'] = startdate
    contents['offlinereginfo']['enddate'] = enddate
    allowedMacs=allowedMacs.split(',')
    contents['licensedata']['allowedMacAddresses'] = allowedMacs
    return contents

def filegenerator(jsonifieddata):
    encry = wrap(jsonifieddata, offgen)
    file = open('offlineuser.key','w')
    file.write(encry)
    file.close()
    validity_file=open('validity.txt','w')
    validity_file.write(startdate+" to "+enddate)
    validity_file.close()

if __name__ == '__main__':
    try:
        allinputs = str(sys.argv[-1])
        allinputs=allinputs.split(';')
        if len(allinputs) >= 3:
            macid = allinputs[0]
            startdate = allinputs[1]
            enddate = allinputs[2]
            if len(allinputs) == 4:
                allowedMacs = allinputs[3]
            else:
                allowedMacs = macid
            jsonifieddata = jsoncreator(macid,startdate,enddate,allowedMacs)
            filegenerator(str(jsonifieddata))
            print ("A file with name offlineuser.key is generated,\n"
            +"Please use it for Offline Registration to Nineteen68")
        else:
            print 'File should be run with the following command\n'
            print 'python.exe offlineuser_key_generator.py {MACADDRESS};<startdate[mm/dd/yyyy{-hhmmss}]>;<enddate[mm/dd/yyyy{-hhmmss}]>;<mac1>,<mac2>,..,<macN> \n Specify NO , if MACADDRESS is not provided.'
    except Exception as e:
        import traceback
        traceback.print_exc()
        print 'Something went wrong... Contact Nineteen68 Development Team'