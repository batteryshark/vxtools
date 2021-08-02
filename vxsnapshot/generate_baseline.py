
import os 
import sys
import winreg
import json
import binascii
import struct

from common import get_file_paths
from common import get_registry_keys
from common import BASELINE_FILENAME



def generate_baseline():
    n_data = {
        "filesystem":{},
        "registry":{}
    }
    # Get Filesystem Baseline First        
    n_data['filesystem'] = get_file_paths()
    # Get Registry Baseline
    n_data['registry'] = get_registry_keys()

    with open(BASELINE_FILENAME,"w") as g:
        json.dump(n_data,g)

    print("Done!")





if __name__ == "__main__":
    generate_baseline()