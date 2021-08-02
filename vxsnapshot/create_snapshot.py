from common import get_file_paths
from common import get_registry_keys
from common import BASELINE_FILENAME
import sys
import os
import json
import shutil
import winreg
import binascii

def get_new_file_list(old_lst):
    old_lst = set(old_lst)
    return set(get_file_paths()) - old_lst

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
    return {}

def get_new_registry_keys(old_keys):
    return list(set(get_registry_keys()) - set(old_keys))


def create_snapshot(root_out_path=os.getcwd()):
    with open(BASELINE_FILENAME,"r") as f:
        baseline_data = json.load(f)

    base_data_out_path = os.path.join(root_out_path,"DATA")
    if not os.path.exists(base_data_out_path):
        os.makedirs(base_data_out_path)
    
    new_file_list = get_new_file_list(baseline_data['filesystem'])
    for item in new_file_list:
        if os.path.isdir(item):
            continue
        n_item = item.replace(":","",1)
        out_path = os.path.join(base_data_out_path,n_item)
        out_parent = os.path.split(out_path)[0]
        if not os.path.exists(out_parent):
            os.makedirs(out_parent)
        if os.path.exists(out_path):
            continue
        print(f"Copying: {item}...")
        try:
            shutil.copy(item,out_path)
        except:
            print(f"Failed to Copy: {item}")

    # Get Current Registry Keys

    new_registry_keys = get_new_registry_keys(baseline_data['registry'])


    if new_registry_keys:
        with open(os.path.join(root_out_path,"pdxreg.ini"),'w') as g:
            for key in new_registry_keys:
                g.write(f"[{key}]\n")
                entries = get_vxreg_entry(key)
                for entry in entries:
                    g.write(entry)
                    g.write("\n")
                
    print(f"Created Snapshot: {len(new_file_list)} Files and {len(new_registry_keys)} Registry Keys")

def pdxenv_get_data():
    envdata = {}
    reqd = input("[Windows] Is a Custom Environment Required? [y/n] ").lower().strip()
    if reqd == "n":
        return envdata
    
    cuser = input("Custom Username? [Enter to Skip]: ")
    if not cuser:
        envdata['global'] = ["username=user"]
    else:
        envdata['global'] = [f"username={cuser}"]
    
    drive_letter = " "
    while drive_letter:
        drive_letter = input("Specify a Drive Letter or 'Enter' if no more: ").lower().strip()
        if not drive_letter:
            return envdata
        drive_info_valid = False
        while not drive_info_valid:
            print("Drive Information Input")
            print("Format: type,serial,label,filesystem")
            print("Type Enum: DRIVE_UNKNOWN (0), DRIVE_NO_ROOT_DIR(1), DRIVE_REMOVABLE(2), DRIVE_FIXED(3), DRIVE_REMOTE(4), DRIVE_CDROM(5), DRIVE_RAMDISK(6)")
            print("HDD Example: 3,0,APP,NTFS")
            print("CD Example: 5,0,CD,CDFS")
            drive_info = input("Specify Information: ")
            try:
                dtype,serial,label,filesystem = drive_info.split(",")
                dtype = int(dtype)
                serial = int(serial)
            except:
                print("Invalid Information Format")
                continue
            
            if not dtype in range(0,6):
                print("Drive Type Invalid: %d" % dtype)
                continue                
            envdata[f'drive_map_{drive_letter}'] = [
                f"type={dtype}",
                f"serial={serial}",
                f"label={label}",
                f"filesystem={filesystem}"
            ]
            drive_info_valid = True
            
    return envdata

def pdxenv_create(out_root):
    envdata = pdxenv_get_data()
    if not envdata:
        return
    
    with open(os.path.join(out_root,"pdxenv.ini"),"w") as g:
        for ek in envdata.keys():
            g.write(f"[{ek}]\n")
            for item in envdata[ek]:
                g.write(f"{item}\n")
            g.write("\n")
    

if __name__ == "__main__":
    #create_snapshot()
    pdxenv_create(os.getcwd())
