# Convert Regshot backups to VXRegistry Files
import json
import sys
import binascii
import struct

BASE_CONVERT = {
    "HKLM":"\\registry\\machine",
    "HKU":"\\registry\\user"
}

def create_keyreg():    
    f = open("registry_keys.txt","r")
    lines = f.readlines()
    f.close()



    KDB = {}

    for line in lines:
        line = line.strip()
        base = line.split("\\")[0]
        if not base in BASE_CONVERT:
            print("ERROR UNHNDLED: %s" % base)
            sys.exit(-1)
        
        KDB[line.replace(base,BASE_CONVERT[base]).lower()] = {}

    with open("./vxregistry","w") as g:
        json.dump(KDB,g,indent=4)


def finalize_reg():
    KDB = {}
    with open("./vxregistry","r") as f:
        KDB = json.load(f)

    f = open("registry_values.txt","r")
    lines = f.readlines()
    f.close()    
    for line in lines:
        line = line.strip()
        base = line.split("\\")[0]    
        if not base in BASE_CONVERT:
            print("ERROR UNHNDLED: %s" % base)
            sys.exit(-1)     
        try:   
            k,v = line.split(": ",1)
        except:
            #print(line)
            exit(-1)

        # line.replace(base,BASE_CONVERT[base]).lower()

        #print(f"{k} ==> {v}")
        
        if k.endswith("\\"):
            k = k[:-1]
            name = "@"

        else:
            k,name = k.rsplit('\\', 1)

        k = k.replace(base,BASE_CONVERT[base]).lower()

        if not k in KDB:
            KDB[k] = {}
            #print(f"Adding Key: {k}")

        # Figure out what the value is
        if "\"" in v:
            data = v.split("\"")[1]
            dtype = "REG_SZ"
        elif "0x" in v:
            v = v.strip()
            dtype = "REG_DWORD"
            try:
                data = int(v,16)
            except:
                print("----")
                print("Error Processing Line: %s" % line)
                print(f"K: {k} Name: {name} V: {v} ")
                print("----")
                continue
        else:
            dtype = "REG_BINARY"
            data = v.strip().replace(" ","")
        
        KDB[k][name.lower()] = {
            "type":dtype,
            "data":data
        }
        #print(f"Adding: {k} => {name.lower()}")
        #print(KDB[k][name.lower()])
    with open("vxregistry","w") as g:
        json.dump(KDB,g,indent=4)

create_keyreg()
finalize_reg()
