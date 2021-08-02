import os
import sys
from pathlib import Path

def get_file_paths():
    filesystem_entries = set()
    for item in ROOT_PATH.rglob("*"):
        filesystem_entries.add(str(item.absolute()))
    return list(filesystem_entries)

def delta_snapshot(old_lst):
    old_lst = set(old_lst)
    return set(get_file_paths()) - old_lst
    
def copy_changed_files(file_lst,out_path=os.getcwd()):
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
            
            
            
if __name__ == "__main__":
    out_path = os.getcwd()
    if len(sys.argv) > 1:
        out_path = sys.argv[1]
    create(out_path)            