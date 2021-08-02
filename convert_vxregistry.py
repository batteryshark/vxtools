import json
import sys



lines = []

TYPE_DB = {
"REG_SZ":"1",
"REG_BINARY":"3",
"REG_DWORD":"4",
"REG_QWORD":"11"
}

def anonymize_key_path(key_path):
	if key_path.startswith("\\registry\\user\\s-1-5"):
		# Split off the prefix
		working_path = key_path.split("\\registry\\user\\s-1-5",1)[-1]
		path_after_sid = working_path[working_path.find("\\")+1:]
		return "\\registry\\user\\" + path_after_sid
	return key_path

def convert_vxregistry(in_path, out_path):
    f = open(in_path,"r")
    data = json.load(f)
    f.close()

    for kp in data.keys():
        nkp = kp.replace("wow6432node\\","")
        nkp = anonymize_key_path(nkp)
        lines.append(f"[{nkp}]")
        if not len(data[kp].keys()):
            lines.append("@=\"1,\"")
        else:
            for kn in data[kp].keys():
                nn = f"[{nkp}]"
                ntype = TYPE_DB[data[kp][kn]['type']]
                ndata = data[kp][kn]['data']
                if ntype == "1":
                    ndata = f"{ndata}"
                lines.append(f"{kn}=\"{ntype},{ndata}\"")
            
    with open(out_path,"w") as g:
        for line in lines:
            g.write(line)
            g.write("\n")
        
if __name__ == "__main__":
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    convert_vxregistry(in_path,out_path)


        
