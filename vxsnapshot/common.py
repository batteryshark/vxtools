from pathlib import Path
import winreg

BASELINE_FILENAME = "baseline.json"
ROOT_PATH = Path("C:\\")


def get_file_paths():
    filesystem_entries = set()
    for item in ROOT_PATH.rglob("*"):
        filesystem_entries.add(str(item.absolute()))
    return list(filesystem_entries)


def parse_hive(base_key,root_key_nativepath,base_subkey="/"):
    index = 0
    path_lst = []
    while 1:
        try:
            subkey = winreg.EnumKey(base_key,index)
            
        
            fpath = root_key_nativepath + base_subkey.replace("/","\\") + "\\" + subkey.replace("/","\\")
            path_lst.append(fpath.replace("\\\\","\\"))
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
