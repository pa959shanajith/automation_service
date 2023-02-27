import os
import json
import sqlite3
from Crypto.Cipher import AES
import codecs


KEY_SERVER = "".join(['n','I','N','3','t','3','e','n','6','8','l','I','(','e','N','s','!','n','G','S','3','R','^','e','R','s','E','r','V','e','Rr'])

def pad(data):
    BS = 16
    padding = BS - len(data) % BS
    return data + padding * chr(padding).encode('utf-8')
    
def unpad(data):
    return data[0:-ord(data[-1])]

def decrypt_node(hex_data, key, iv=b'0'*16):
    data = codecs.decode(hex_data.strip(), 'hex')
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    return unpad(aes.decrypt(data).decode('utf-8'))

def encrypt_node(data, key, iv=b'0'*16):
    aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
    hex_data = aes.encrypt(pad(data.encode('utf-8')))
    return codecs.encode(hex_data, 'hex').decode('utf-8')

def dbConnector(ops,*args):
    data = False
    if ops=='check':
        if os.access(db_path,os.R_OK):
            data = True
    else:
        # CREATE DATABASE CONNECTION
        conn = sqlite3.connect(db_path)
        if ops=='select':
            #Retrieve the data from db and decrypt it
            cursor = conn.cursor()
            result = cursor.execute("SELECT info from lsdetails WHERE lsid = 'LS001'")
            data = list(result)
            if len(data) >= 0:
                data = data[0][0]
            data = decrypt_node(data, KEY_SERVER)
            data = json.loads(data)
            # Backward compatibility
            old_key = "nd"+"ac"
            if old_key in data:
                data["das"] = data[old_key]
                del data[old_key]
                datatodb = encrypt_node(json.dumps(data), KEY_SERVER)
                cursor.execute("UPDATE lsdetails SET info = ? WHERE lsid = 'LS001'",[datatodb])
        elif ops=='update':
            #Encrypt data and update in db
            datatodb = json.dumps(args[0])
            datatodb = encrypt_node(datatodb, KEY_SERVER)
            cursor1 = conn.execute("UPDATE lsdetails SET info = ? WHERE lsid = 'LS001'",[datatodb])
            data=True
        conn.commit()
        conn.close()
    return data


def getLSData(LS_Path):
    global db_path
    db_path=LS_Path
    if os.path.isfile(db_path):
        dbdata=dbConnector('select')
        msg=dbdata
        if dbdata:
            return msg
    else:
        return False  

