#TODO : use pycdlib for iso: https://clalancette.github.io/pycdlib/example-creating-udf-iso.html
#TODO : use virtdisk and deviocontrol for vhdx formatting: 
# Link: https://github.com/mkropat/MlkDiskWiper/blob/58d289d0e4148d101bf48910a7b4f3d4333a4c80/MlkDiskWiperWinApiAdapter/IoCtl.cpp
# Link: https://github.com/AustinWise/FormatSdCard/blob/e390cac2243592eda34788963ae414c8768c0ac4/FormatSdCard.cpp
# Link: https://github.com/lordjeb/nullFS/blob/672d03d1cfd9ce25d2cd6f65bfad4022006ac2c8/test/integrationTests/VirtualDisk.cpp

from zipfile import ZipFile
from pathlib import Path
import math
import platform
import os
import sys
import subprocess
import shutil
import tempfile
import json

if platform.system() == "Windows":
    MKISOFS_PATH = "mkisofs.exe"
else:
    MKISOFS_PATH = "mkisofs"

GB = 1024**3
MB = 1024**2
ALLOCATION_UNIT = 32768

# Generates some info for the packager to know how to create the smoothie data.
# Format depends upon some criteria:
# If there are more than 500 files or the target is over 8GB in size, VHDX
# Else, if the target has over 50 files or is over 128MB in size, ISO
# Otherwise, it's a ZIP
def get_target_info(target="."):
    target_info = {
        "num_entries":0,
        "size":0,
        "num_blocks":0,
        "format":"ZIP"
    }
    tpath = Path(target)
    large_file = False
    for item in tpath.rglob("*"):
        # ISO Can't handle >4GB Files
        if item.stat().st_size > 4 * GB:
            large_file = True
        target_info['num_entries'] += 1
        target_info['size'] += item.stat().st_size
        target_info['num_blocks'] += math.ceil((item.stat().st_size / ALLOCATION_UNIT))
    if large_file or target_info['num_entries'] > 1000 or target_info['size'] > 8*GB:
        target_info['format'] = "VHDX"
    elif target_info['num_entries'] > 50 or target_info['size'] > 128*MB:
        target_info['format'] = "ISO"
        
    return target_info
    
def create_zip(out_root,out_name,target="."):
    tpath = Path(target)
    out_path = os.path.join(out_root,f"{out_name}.zip")
    with ZipFile(out_path,'w') as zipObj:        
        for item in tpath.rglob("*"):
            zipObj.write(item,item.relative_to(tpath))
    return out_path
       
def create_iso(out_root,out_name,target):
    out_path = os.path.join(out_root,f"{out_name}.iso")
    out_path = out_path.replace("\\","/")
    target = str(Path(target).resolve()).replace("\\","/")
    cmd = os.system(f"{MKISOFS_PATH} -D -udf -o \"{out_path}\" \"{target}\"")
    return out_path
           
def create_vhdx(out_root, out_name, src_data_path, num_blocks):
    path_to_vhdx_file = os.path.abspath(os.path.join(out_root,f"{out_name}.vhdx"))
    # Due to the allocation unit size, we need to Pad the image
    # Get our Volume Size in MB - bump the buffer a smidge
    package_size_mb = int(((num_blocks*ALLOCATION_UNIT) / MB)) + 1
    # 16384 for GPT
    # For every 100 MB / 4 MB is needed for NTFS formatting - 40KB per MB
    package_size_mb += ((40964 * package_size_mb) / MB) + 1
    


    print(f"Generating RO Volume of {int(package_size_mb)} MB...") 

    # Create a temporary mount path to copy our stuff.
    mounted_root_path = tempfile.mkdtemp()

    START_SCRIPT = """
    CREATE VDISK FILE="%s" maximum=%d type=expandable
    SELECT VDISK FILE="%s"
    ATTACH VDISK
    CLEAN
    CREATE PART PRI
    SELECT PART 1    
    FORMAT FS=NTFS QUICK
    ASSIGN MOUNT=%s
    EXIT
    """ % (path_to_vhdx_file, package_size_mb, path_to_vhdx_file, mounted_root_path)

    END_SCRIPT = """
    SELECT VDISK FILE="%s"
    SELECT PARTITION 1
    REMOVE
    DETACH VDISK
    EXIT
    """ % path_to_vhdx_file

    print("Creating VHDX of Size: %d" % package_size_mb)

    start_script_file = tempfile.NamedTemporaryFile(delete=False)
    start_script_file.write(START_SCRIPT.encode('ascii'))
    start_script_file.close()

    os.system("DISKPART /s %s" % start_script_file.name)
    os.unlink(start_script_file.name)

    print("Copying Data to Partition...")


    for item in os.listdir(src_data_path):
        s = os.path.join(src_data_path, item)
        d = os.path.join(mounted_root_path, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, False, None)
        else:
            shutil.copy2(s, d)

    print("Finalizing VHDX...")
    end_script_file = tempfile.NamedTemporaryFile(delete=False)
    end_script_file.write(END_SCRIPT.encode('ascii'))
    end_script_file.close()
    os.system("DISKPART /s %s" % end_script_file.name)
    os.unlink(end_script_file.name)
    shutil.rmtree(mounted_root_path)

    print("VHDX Created!")
    return path_to_vhdx_file
 
def create_image(target,out_root="."):
    image_name = os.path.splitext(os.path.basename(target))[0]
    info = get_target_info(target)
    if info['format'] == "ZIP":
        return create_zip(out_root,image_name,target)
    elif info['format'] == "ISO":
        return create_iso(out_root,image_name,target)
    elif info['format'] == "VHDX":
        return create_vhdx(out_root,image_name,target,info['num_blocks'])
        
def write_vxapp_config(config_path):
    entry = ""
    epdata = []
    while 1:
        entry = input("Input an Entrypoint;title[optional], blank to end: ")
        if(entry == ""):
            break
        name = "Play Game"
        epath = entry
        args = ""
        if(";" in entry):
            if(entry.count(";") == 1):
                epath,name = entry.split(";")
            elif(entry.count(";") == 2):
                epath,name,args = entry.split(";")
        epdata.append(
        {"name": name, "map": "smoothie.map", "executable": f"C:\\app\\{epath}", "args": args, "cwd": "", "envar": [], "preload": ["pdxproc.dlldynamic", "pdxfs.dlldynamic"]}
        
        )
    with open(config_path,"w") as f:
        json.dump(epdata,f)
    

if __name__ == "__main__":
    app_name = os.path.split(sys.argv[1])[-1] 
    app_base = os.path.split(sys.argv[1])[0] 
    app_root = os.path.join(app_base,"__staging",app_name + ".vxapp")
    if not os.path.exists(os.path.join(app_base,"__staging")):
        os.makedirs(os.path.join(app_base,"__staging"))
    content_root = os.path.join(app_root,"content")
    if not os.path.exists(app_root):
        os.makedirs(app_root)
    if not os.path.exists(content_root):
        os.makedirs(content_root)
    print(f"Processing: {app_name}")
    smoothie_path = os.path.join(content_root,"smoothie.map")
    config_path = os.path.join(app_root,"vxapp.config")
    sconfig_path = app_name+"_vxapp.config"
    if(len(sys.argv) > 2):
        sconfig_path = sys.argv[2]
    
    if os.path.exists(sconfig_path):
        shutil.copy2(sconfig_path,config_path)
    else:
        write_vxapp_config(config_path)
    image_path = create_image(sys.argv[1],content_root)
    shutil.copy2("windows_base.zip",os.path.join(content_root,"windows_base.zip"))
    with open(smoothie_path,"w") as f:
        f.write("MAP;windows_base.zip;C:\\\n")
        f.write(f"MAP;{os.path.split(image_path)[-1]};C:\\app\n")
    
