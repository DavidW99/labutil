import os, subprocess, sys


def run_command(command):
    retcode = subprocess.run(
        command,
        shell=True,
        capture_output=True,
    )
    if retcode.returncode != 0:
        print(
            f"=== Execution of command failed with returncode {retcode.returncode} ==="
        )
        print(f"Command:  {command}")
        if retcode.stdout is not None and len(retcode.stdout) > 0:
            print("== stdout from command ==")
            print(retcode.stdout.decode("ascii"), file=sys.stderr)
            print("== end stdout from command ==")
        if retcode.stderr is not None and len(retcode.stderr) > 0:
            print("== stderr from command ==")
            print(retcode.stderr.decode("ascii"), file=sys.stderr)
            print("== end stderr from command ==")
    retcode.check_returncode()
    return retcode


def write_file(fname, text):
    with open(fname, "w") as fin:
        fin.write(text)


def prepare_dir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
