import os, subprocess


def run_command(command):
    return subprocess.run(command, shell=True, capture_output=True, check=True,)

def write_file(fname, text):
    with open(fname, 'w') as fin:
        fin.write(text)

def prepare_dir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
