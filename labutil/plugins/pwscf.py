import numpy, os, copy
from labutil.objects import TextFile, ExternalCode, File, Param
from labutil.util import prepare_dir, run_command


class PWscf_inparam(Param):
    """
    Data class containing parameters for a Quantum Espresso PWSCF calculation
    it does not include info on the cell itself, since that will be taken from a Struc object
    """

    pass


def qe_value_map(value):
    """
    Function used to interpret correctly values for different
    fields in a Quantum Espresso input file (i.e., if the user
    specifies the string '1.0d-4', the quotes must be removed
    when we write it to the actual input file)
    :param: a string
    :return: formatted string to be used in QE input file
    """
    if isinstance(value, bool):
        if value:
            return ".true."
        else:
            return ".false."
    elif isinstance(value, (float, numpy.floating, int, numpy.integer)):
        return str(value)
    elif isinstance(value, str):
        return "'{}'".format(value)
    else:
        print("Strange value ", value)
        raise ValueError


def write_pwscf_input(runpath, params, struc, kpoints, pseudopots, constraint=None):
    """Make input param string for PW"""
    # automatically fill in missing values
    pcont = copy.deepcopy(params.content)
    pcont["SYSTEM"]["ntyp"] = struc.n_species
    pcont["SYSTEM"]["nat"] = struc.n_atoms
    pcont["SYSTEM"]["ibrav"] = 0
    # Write the main input block
    inptxt = ""
    for namelist in ["CONTROL", "SYSTEM", "ELECTRONS", "IONS", "CELL"]:
        inptxt += "&{}\n".format(namelist)
        for key, value in pcont[namelist].items():
            inptxt += "    {} = {}\n".format(key, qe_value_map(value))
        inptxt += "/ \n"
    # write the K_POINTS block
    if kpoints.content["option"] == "automatic":
        inptxt += "K_POINTS {automatic}\n"
    inptxt += " {:d} {:d} {:d}".format(*kpoints.content["gridsize"])
    if kpoints.content["offset"]:
        inptxt += "  1 1 1\n"
    else:
        inptxt += "  0 0 0\n"

    # write the ATOMIC_SPECIES block
    inptxt += "ATOMIC_SPECIES\n"
    for elem, spec in struc.species.items():
        inptxt += "  {} {} {}\n".format(
            elem, spec["mass"], pseudopots[elem].content["name"]
        )

    # Write the CELL_PARAMETERS block
    inptxt += "CELL_PARAMETERS {angstrom}\n"
    for vector in struc.content["cell"]:
        inptxt += " {} {} {}\n".format(*vector)

    # Write the ATOMIC_POSITIONS in crystal coords
    inptxt += "ATOMIC_POSITIONS {angstrom}\n"
    for index, positions in enumerate(struc.content["positions"]):
        inptxt += "  {} {:1.5f} {:1.5f} {:1.5f}".format(positions[0], *positions[1])
        if (
            constraint
            and constraint.content["atoms"]
            and str(index) in constraint.content["atoms"]
        ):
            inptxt += " {} {} {} \n".format(*constraint.content["atoms"][str(index)])
        else:
            inptxt += "\n"

    infile = TextFile(path=os.path.join(runpath.path, "pwscf.in"), text=inptxt)
    infile.write()
    return infile

def write_sbatch(runpath, ncpu=8):
    """Write the sbatch file"""
    sbatchtxt = f"""\
#!/bin/bash
#SBATCH --job-name=qe
#SBATCH -N 1 # Number of nodes requested
#SBATCH -n {ncpu} # Number of cores requested
#SBATCH -t 00-08:00 # Runtime in minutes
#SBATCH -p test # Partition to submit to kozinsky
#SBATCH --mem-per-cpu=3000 # Memory per cpu in MB (see also--mem) 3800 5000

module load intel/17.0.4-fasrc01 intel-mkl/2017.2.174-fasrc01 impi/2017.2.174-fasrc01
module list

mpirun -np $SLURM_NTASKS $QE_PW_COMMAND < pwscf.in """
    sbatchfile = TextFile(path=os.path.join(runpath.path, "bat_qe.sh"), text=sbatchtxt)
    sbatchfile.write()
    # run sbatch
    os.system(f"cd {runpath.path}; sbatch bat_qe.sh")
    return 

def run_qe_pwscf(
    struc, runpath, pseudopots, params, kpoints, constraint=None, ncpu=1, nkpool=1
):
    pwscf_code = ExternalCode({"path": os.environ["QE_PW_COMMAND"]})
    prepare_dir(runpath.path)
    infile = write_pwscf_input(
        params=params,
        struc=struc,
        kpoints=kpoints,
        runpath=runpath,
        pseudopots=pseudopots,
        constraint=constraint,
    )
    write_sbatch(runpath)
    outfile = File({"path": os.path.join(runpath.path, "pwscf.out")})
    # `run_command` will helpfully print stdout/err if something fails, but
    # to do that we need the QE output to go to stderr/out in addition to the log
    # so we use `tee`. But we also need the failure of QE to propagate to the final
    # returncode, so we need pipefail, but /bin/sh doesn't have that, so we also
    # need to run in bash:
    # pwscf_command = (
    #     'bash -c "set -eo pipefail; mpirun -np {} {} -nk {} < {} | tee {}"'.format(
    #         ncpu, pwscf_code.path, nkpool, infile.path, outfile.path
    #     )
    # )
    # run_command(pwscf_command)
    return outfile


def parse_qe_pwscf_output(outfile):
    with open(outfile.path, "r") as outf:
        for line in outf:
            if line.lower().startswith("     pwscf"):
                walltime = line.split()[-3] + line.split()[-2]
            if line.lower().startswith("     total force"):
                total_force = float(line.split()[3]) * (13.605698066 / 0.529177249)
            if line.lower().startswith("!    total energy"):
                total_energy = float(line.split()[-2]) * 13.605698066
            if line.lower().startswith("          total   stress"):
                pressure = float(line.split()[-1])
    result = {
        "energy": total_energy,
        "force": total_force,
        "pressure": pressure,
        "walltime": walltime,
    }
    return result
