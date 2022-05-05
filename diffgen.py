import os
import sys
import hashlib
import shutil
from pathlib import Path

def file_hash_md5(src_path):
    md5_object = hashlib.md5()
    block_size = 128 * md5_object.block_size
    a_file = open(src_path, 'rb')

    chunk = a_file.read(block_size)
    while chunk:
        md5_object.update(chunk)
        chunk = a_file.read(block_size)

    return md5_object.digest()
    
    
def usage():
    print("Usage: OLD NEW VIRTUAL_ROOT OUTPUT")
    sys.exit(-1)
    
deleted_entries = []
added_entries = []
changed_entries = []

if __name__ =="__main__":
    if len(sys.argv) < 5:
        usage()
    old_path = os.path.abspath(sys.argv[1])
    new_path = os.path.abspath(sys.argv[2])
    v_path = os.path.abspath(sys.argv[3])
    out_path = os.path.abspath(sys.argv[4])
    if not os.path.exists(old_path):
        print("Old Path Does not Exist!")
        sys.exit(1)
    if not os.path.exists(new_path):
        print("New Path Does not Exist!")
        sys.exit(1)
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    
    for root,dirs,files in os.walk(old_path):
        for d in dirs:
            full_path = os.path.join(root,d)
            test_path = full_path.replace(old_path,new_path)
            if not os.path.exists(test_path):
                deleted_entries.append(test_path.replace(new_path,v_path))
        for f in files:
            full_path = os.path.join(root,f)
            test_path = full_path.replace(old_path,new_path)
            if not os.path.exists(test_path):
                deleted_entries.append(test_path.replace(new_path,v_path))
            else:
                old_md5 = file_hash_md5(full_path)
                new_md5 = file_hash_md5(test_path)
                if(old_md5 != new_md5):
                    changed_entries.append(test_path)
                    
    for root,dirs,files in os.walk(new_path):
        for d in dirs:
            full_path = os.path.join(root,d)
            test_path = full_path.replace(new_path,old_path)
            if not os.path.exists(test_path):
                added_entries.append(full_path)
        for f in files:
            full_path = os.path.join(root,f)
            test_path = full_path.replace(new_path,old_path)
            if not os.path.exists(test_path):
                added_entries.append(full_path)

    
    # Make the Diff
    for entry in added_entries:
        dest_path = entry.replace(new_path,out_path)
        dest_ppath = Path(dest_path).parent.absolute()
        if not os.path.exists(dest_ppath):
            os.makedirs(dest_ppath)
        if os.path.isdir(entry):
            if(not os.path.exists(dest_path)):
                os.makedirs(dest_path)
            continue
        shutil.copy(entry,dest_path)
    for entry in changed_entries:
        dest_path = entry.replace(new_path,out_path)
        dest_ppath = Path(dest_path).parent.absolute()
        if not os.path.exists(dest_ppath):
            os.makedirs(dest_ppath)
        shutil.copy(entry,dest_path)
    with open(os.path.join(out_path,"smoothie_addon.map"),"w") as g:
        for entry in deleted_entries:
            g.write(f"REMOVE;{entry}\n")
    print("DONE!")
        