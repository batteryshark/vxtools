import os,sys,platform
import winreg

VALUE_TYPE_REV_DB = {
    0:"REG_NONE",
    1:"REG_SZ",
    2:"REG_EXPAND_SZ",
    3:"REG_BINARY",
    4:"REG_DWORD",
    5:"REG_DWORD_BIG_ENDIAN",
    6:"REG_LINK",
    7:"REG_MULTI_SZ",
    8:"REG_RESOURCE_LIST",
    11:"REG_QWORD"
}

def anonymize_key_path(key_path):
	if key_path.startswith("\\registry\\user\\s-1-5"):
		# Split off the prefix
		working_path = key_path.split("\\registry\\user\\",1)[-1]
		path_after_sid = working_path[working_path.find("\\")+1:]
		return "\\registry\\user\\" + path_after_sid
	return key_path
    
def parse_hive(base_key,root_key_nativepath,base_subkey="/"):
    index = 0
    path_lst = []
    while 1:
        try:
            subkey = winreg.EnumKey(base_key,index)
            
        
            fpath = root_key_nativepath + base_subkey.replace("/","\\") + "\\" + subkey.replace("/","\\")
            path_lst.append(anonymize_key_path(fpath.replace("\\\\","\\")))
            hSubKey = winreg.OpenKey(base_key,subkey)
            
            path_lst.extend(parse_hive(hSubKey,root_key_nativepath,base_subkey + "/" + subkey))
            index+=1
        except OSError as e:
            if e.errno == 22:
                break
            elif e.errno == 13:
                index +=1
                continue
            else:
                print(f"Unhandled OSError: {e.errno}")
                break
    return path_lst

def get_registry_keys():    
    spl = []
    spl.extend(parse_hive(winreg.HKEY_LOCAL_MACHINE,"\\registry\\machine"))
    spl.extend(parse_hive(winreg.HKEY_USERS,"\\registry\\user"))
    return spl

def process_reg_data(vtype,vdata):
    if vtype == 3 or vtype == 8:
        return binascii.hexlify(vdata).decode('ascii')
    return vdata

def get_reg_data(bk,path):
    vdb = []
    try:
        hKey = winreg.OpenKey(bk,path)
    except:
        return {}
    index = 0
    while 1:
        try:
            vname, value, vtype = winreg.EnumValue(hKey, index)
            if vname == "":
                vname = "@"
            vname = vname.lower()            
            vdata = process_reg_data(vtype,value)
            vdb.append(f"{vname}=\"{vtype},{vdata}\"")
            index +=1            
        except OSError as e:
            if e.errno == 22:
                break
            elif e.errno == 13:
                index +=1
                continue
            else:
                print(f"Unhandled OSError: {e.errno}")
                break
    return vdb

def get_vxreg_entry(path):
    path = path.lower()
    rk = None
    if path.startswith("\\registry\\machine"):
        rk = winreg.HKEY_LOCAL_MACHINE
        opath = path.replace("\\registry\\machine\\","")
        return get_reg_data(rk,opath)
    elif path.startswith("\\registry\\user"):
        rk = winreg.HKEY_USERS
        opath = path.replace("\\registry\\user\\","")
        return get_reg_data(rk,opath)
    print("Unrecognized Path: %s" % path)
    return []
    
def delta_snapshot(old_keys):
    kvs = {}
    new_keys = list(set(get_registry_keys()) - set(old_keys))
    if not len(new_keys):
        return kvs
    for key in new_keys:
        kvs[key] = get_vxreg_entry(key)
    return kvs
        
    
    
def create(kvs,out_path):
    with open(os.path.join(out_path,"pdxreg.ini"),'w') as g:
        for key in kvs:
            g.write(f"[{key}]\n")
            for entry in kvs[key]:
                g.write(entry)
                g.write("\n")
    
    
if __name__ == "__main__":
    out_path = os.getcwd()
    if len(sys.argv) > 1:
        out_path = sys.argv[1]
    kvs = {
    "\\registry\\user\\heynow":[
    "@=\"3,0011223344\"",
    "test=\"1,wat\"",
    ]
    }
    create(kvs,out_path)    