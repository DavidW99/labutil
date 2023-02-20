import os, subprocess, sys


def run_command(command):
    retcode = subprocess.run(
        command,
        shell=True,
        capture_output=True,
    )
    if retcode.returncode != 0:
        if retcode.stdout is not None and len(retcode.stdout) > 0:
            print(retcode.stdout.decode("ascii"), file=sys.stderr)
        if retcode.stderr is not None and len(retcode.stderr) > 0:
            print(retcode.stderr.decode("ascii"), file=sys.stderr)
    retcode.check_returncode()
    return retcode


def write_file(fname, text):
    with open(fname, "w") as fin:
        fin.write(text)


def prepare_dir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
