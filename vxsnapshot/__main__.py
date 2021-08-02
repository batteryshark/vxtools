import sys
import os
from common import BASELINE_FILENAME
from create_snapshot import create_snapshot
from generate_baseline import generate_baseline

if __name__=="__main__":
    if not os.path.exists(BASELINE_FILENAME):
        generate_baseline()
    else:
        create_snapshot()

