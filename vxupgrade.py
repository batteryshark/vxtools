import os
import sys
import json
import shutil
from convert_vxregistry import convert_vxregistry






def upgrade_vxapp(path_to_vxapp):
    info_db = {
        "name":"",
        "configuration": []
    }

    ep_template = {
        "name":"",
        "map":"smoothie.map",
        "executable":"",
        "args":"",
        "cwd":"",
        "envar":[],
        "preload":[]
    }
    path_to_info = os.path.join(path_to_vxapp,"vxapp.info")
    if os.path.exists(path_to_info):
        return
    print(f"Converting: {app}")        
    with open(os.path.join(path_to_vxapp,"metadata.json"),"r") as f:
        info_db['name'] = json.load(f)['name']
        
    # Move Smoothie Map to Content
    src_smoothie = os.path.join(path_to_vxapp,"config","default","vxfilesystem")
    dest_smoothie = os.path.join(path_to_vxapp,"content","smoothie.map")
    try:
        shutil.move(src_smoothie,dest_smoothie)
    except:
        pass

    src_reg = os.path.join(path_to_vxapp,"config","default","vxregistry")
    dest_reg = os.path.join(path_to_vxapp,"content","vxregistry.ini")
    if os.path.exists(src_reg):
        convert_vxregistry(src_reg,dest_reg)


    # Entrypoint conversion
    ep_path = os.path.join(path_to_vxapp,"config","default","entrypoint")
    with open(ep_path,"r") as f:
        data = json.load(f)
        for ek in data.keys():     
            ce = data[ek]
            ept = ep_template.copy()        
            if(os.path.exists(dest_reg)):
                ept['envar'].append("PDXREG=C:\\app\\pdxreg.ini")
                ept['preload'].append("pdxreg32.dll")
                ept['preload'].append("pdxreg64.dll")
                
            ept['name'] = ek
            ept['executable'] = ce.get("executable_path","")
            ept['args'] = ce.get("executable_arguments","")
            ept['cwd'] = ce.get("executable_origin","")
            info_db['configuration'].append(ept)
            
    with open(path_to_info,"w") as g:
        json.dump(info_db,g,indent=4)

    print("DonionRingZ")

    shutil.rmtree(os.path.join(path_to_vxapp,"config"))
    os.unlink(os.path.join(path_to_vxapp,"metadata.json"))

    for root,dirs,files in os.walk(path_to_vxapp):
        for f in files:
            if f == "desktop.ini":
                os.unlink(os.path.join(root,f))
                
if __name__ == "__main__":
    
    path_to_vxapp = os.path.abspath(sys.argv[1])
    apps = os.listdir(path_to_vxapp)
    for app in apps:        
        upgrade_vxapp(os.path.join(path_to_vxapp,app))