import os,sys




def get_data():
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

def create(out_root=os.getcwd()):
    envdata = get_data()
    if not envdata:
        return
    
    with open(os.path.join(out_root,"pdxenv.ini"),"w") as g:
        for ek in envdata.keys():
            g.write(f"[{ek}]\n")
            for item in envdata[ek]:
                g.write(f"{item}\n")
            g.write("\n")
    





if __name__ == "__main__":
    out_path = os.getcwd()
    if len(sys.argv) > 1:
        out_path = sys.argv[1]
    create(out_path)