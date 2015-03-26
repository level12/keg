import subprocess
import pathlib

cdir = pathlib.Path(__file__).parent


def build(req_fpath):
    pip_args = ['wheel', '--wheel-dir=wheelhouse', '--use-wheel', '--find-links=wheelhouse',
                '-r']
    subprocess.check_call(['pip'] + pip_args + [req_fpath])
    subprocess.check_call(['pip3.4'] + pip_args + [req_fpath])

build(str(cdir.joinpath('runtime.txt')))
build(str(cdir.joinpath('testing.txt')))
