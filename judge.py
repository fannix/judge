""" Compile the source and judge the program
"""

import os.path
import sys
from paver.runtime import sh
import judge_sandbox

def compile_gcc(source_file, target_file="a.out"):
    """Compile the source file using the gcc compiler

    return target_file and output message
    """
    command = "g++ %s -o %s 2>&1"
    if os.path.exists(target_file):
        sh('rm %s' % target_file)
    output = sh(command % (source_file, target_file), capture=True)
    if not os.path.exists(target_file):
        return None, output
    else:
        return target_file, output


def run(target_file, resource_limit, input_file, output_file):
    """Run the target file under the resource limit
    """
    command_template = "%s < %s > %s"
    command = command_template % (os.path.abspath(target_file), input_file, output_file)

    configuration = {
        'args': "/home/mxf/online_judge/a.out",               # targeted program
        'stdin': open(input_file),             # input to targeted program
        'stdout': open(output_file, 'w'),           # output from targeted program
        'stderr': sys.stderr,           # error from targeted program
        'quota': dict(wallclock=30000,  # 30 sec
                      cpu=5000,         # 5 sec
                      memory=20000000,   # 20 MB
                      disk=10048576)    # 1 MB
        }
    judge_sandbox.run(command, configuration)

    print open(output_file).read()

def main():
    target, message = compile_gcc("helloworld.c")
    #target, message = compile_gcc("infinite_loop.c")

    if not target:
        print message
        return -1
    run(target, None, 'in', 'out')


if __name__ == "__main__":
    main()
