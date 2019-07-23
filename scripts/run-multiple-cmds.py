import subprocess
import os
import time
import sys

# for running multiple command lines in parallel
# usage: python run-multiple-cmds.py <file containing a list of commands> <number of parallel processes>

print(sys.argv)

cmdFileName = sys.argv[1]

with open(cmdFileName, 'rt') as f:
	cmds = f.readlines()

processes = set()

max_processes = int(sys.argv[2])

for cmd in cmds:
    processes.add(subprocess.Popen(cmd, shell=True))
    if len(processes) >= max_processes:
        os.wait()
        processes.difference_update(
            [p for p in processes if p.poll() is not None])
#Check if all the child processes were closed

for p in processes:
    if p.poll() is None:
        p.wait()
