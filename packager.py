from zipfile import ZipFile
from pathlib import Path
import math
import platform
import os
import sys
import subprocess
import shutil
import tempfile

if platform.system() == "Windows":
    MKISOFS_PATH = "mkisofs.exe"
else:
    MKISOFS_PATH = "mkisofs"

GB = 1024**3
MB = 1024**2
ALLOCATION_UNIT = 0x1000

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
    if large_file or target_info['num_entries'] > 500 or target_info['size'] > 8*GB:
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
       
def create_iso(out_root,out_name,target):
    out_path = os.path.join(out_root,f"{out_name}.iso")
    out_path = out_path.replace("\\","/")
    target = str(Path(target).resolve()).replace("\\","/")
    cmd = os.system(f"{MKISOFS_PATH} -D -udf -o \"{out_path}\" \"{target}\"")
           
def create_vhdx(out_root, out_name, src_data_path, num_blocks):
    path_to_vhdx_file = os.path.abspath(os.path.join(out_root,f"{out_name}.vhdx"))
    # Due to the allocation unit size, we need to Pad the image
    # Get our Volume Size in MB - bump the buffer a smidge
    package_size_mb = int(((num_blocks*ALLOCATION_UNIT) / MB) + 64)


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
 
def create_image(target,out_root="."):
    image_name = os.path.splitext(os.path.basename(target))[0]
    info = get_target_info(target)
    if info['format'] == "ZIP":
        return create_zip(out_root,image_name,target)
    elif info['format'] == "ISO":
        return create_iso(out_root,image_name,target)
    elif info['format'] == "VHDX":
        return create_vhdx(out_root,image_name,target,info['num_blocks'])
        
 
create_image(sys.argv[1])    
#print(get_target_info("D:\\BuildGDX_with_JRE"))
#create_zip(".","test","D:\\BuildGDX_with_JRE")
#create_iso(".","test","D:\\BuildGDX_with_JRE")
