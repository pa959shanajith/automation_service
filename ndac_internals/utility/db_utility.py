#-------------------------------------------------------------------------------
# Name:        NDAC DB Generator
# Purpose:
#
# Author: ranjan.agrawal
#
# Created:     08-08-2017
# Copyright:   (c) sakshi.goyal 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os.path
import sys
import uuid
from Crypto.Cipher import AES
import codecs
import sqlite3
import json

KEY_NDAC = "\x4e\x36\x38\x53\x51\x4c\x69\x74\x65\x44\x61\x74\x61\x53\x65\x63\x72\x65\x74\x4b\x65\x79\x43\x6f\x6d\x70\x4f\x4e\x65\x6e\x74\x73"

#############################ENCRYPTION UTILITY START##############################
def pad(data):
    BS = 16
    padding = BS - len(data) % BS
    return data + padding * chr(padding).encode('utf-8')

def wrap(data, key, iv=b'0'*16):
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    hex_data = aes.encrypt(pad(data.encode('utf-8')))
    return codecs.encode(hex_data, 'hex')
#############################ENCRYPTION UTILITY END##############################

#############################DB UTILITY START ###################################
def filldb():
    #create a database
    conn = sqlite3.connect("data.db")
    #create cursor
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS lsdetails (lsid TEXT PRIMARY KEY,info TEXT );")
    data = {
    	"macid": "",
    	"tkn": "",
    }
    datatodb = wrap(json.dumps(data),KEY_NDAC)
    cursor.execute("CREATE TABLE IF NOT EXISTS clndls (sysid TEXT PRIMARY KEY, intrtkndt TEXT);")
    cursor.execute("INSERT INTO clndls(sysid,intrtkndt) VALUES (?,?)",('ndackey',datatodb))
    conn.commit()
    conn.close()
#############################DB UTILITY END ###################################

filldb()