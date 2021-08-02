import os
import hashlib
base_dir = "G:\\My Drive\\VXAPPS\\"
apps = os.listdir(base_dir)

CODE_POOL = [
    '0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F',
    'G','H','J','K','L','M','N','P','Q','R','S','T','U','V','W','X',
    'Y'
]

def generate_app_id(app_name):
    o_code = ""
    s = hashlib.sha1()
    s.update(app_name.encode('ascii'))
    h_code = []
    for cv in bytearray(s.digest()):
        h_code.append(CODE_POOL[cv % len(CODE_POOL)])
    o_code = "".join(h_code)
    return f"{o_code[0:3]}-{o_code[3:6]}-{o_code[6:9]}"
    
for app in sorted(apps):
    app_id = "?"
    app_name = os.path.splitext(os.path.basename(app))[0]
    with open(os.path.join(base_dir,app,"config","id"), "r") as f:
        app_id = f.read()
    
    print(f"{app_name}: {app_id} - {generate_app_id(app_name)}")