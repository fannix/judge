import os
import sys

from sandbox import Sandbox, SandboxPolicy
from sandbox import S_RESULT_RF, S_EVENT_SYSCALL, \
        S_EVENT_SYSRET, S_ACTION_KILL, S_ACTION_CONT


def run(args, configuration=None):
    """Run the program in the sandbox
    """

    # sandbox configuration
    default_configuration = {
        'args': args[1:],               # targeted program
        'stdin': sys.stdin,             # input to targeted program
        'stdout': sys.stdout,           # output from targeted program
        'stderr': sys.stderr,           # error from targeted program
        'quota': dict(wallclock=30000,  # 30 sec
                      cpu=7000,         # 2 sec
                      memory=8388608,   # 8 MB
                      disk=10048576)    # 1 MB
        }
    if not configuration:
        configuration = default_configuration

    # create a sandbox instance and execute till end
    msb = MiniSandbox(**configuration)
    print "running"
    msb.run()
    # verbose statistics
    sys.stderr.write("result: %(result)s\ncpu: %(cpu)dms\nmem: %(mem)dkB\n" %
        msb.probe())
    return os.EX_OK


class MiniSandbox(SandboxPolicy, Sandbox):
    """mini sandbox with embedded policy
    """

    system, machine = os.uname()[0], os.uname()[4]
    sc_table = None
    # white list of essential linux syscalls for statically-linked C programs
    sc_safe = dict(i686=set([0, 3, 4, 19, 45, 54, 90, 91, 122, 125, 140,
        163, 192, 197, 224, 243, 252, ]), x86_64=set([0, 1, 5, 8, 9, 10,
        11, 12, 16, 25, 63, 158, 219, 231, 59, 21, 2, 3, ]), )

    def __init__(self, *args, **kwds):
        # initialize table of system call rules
        self.sc_table = [self._KILL_RF, ] * 1024
        for scno in MiniSandbox.sc_safe[self.machine]:
            self.sc_table[scno] = self._CONT
        # initialize as a polymorphic sandbox-and-policy object
        SandboxPolicy.__init__(self)
        Sandbox.__init__(self, *args, **kwds)
        self.policy = self

    def probe(self):
        # add custom entries into the probe dict
        d = Sandbox.probe(self, False)
        d['cpu'] = d['cpu_info'][0]
        d['mem'] = d['mem_info'][1]
        d['result'] = ('PD', 'OK', 'RF', 'ML', 'OL', 'TL', 'RT', 'AT', 'IE', 'BP')[self.result]

        return d

    def __call__(self, e, a):
        # handle SYSCALL/SYSRET events with local rules
        #print "calling"
        if e.type in (S_EVENT_SYSCALL, S_EVENT_SYSRET):
            if self.machine == 'x86_64' and e.ext0 != 0:
                print "calling"
                return self._KILL_RF(e, a)
            return self.sc_table[e.data](e, a)
        # bypass other events to base class
        return SandboxPolicy.__call__(self, e, a)

    def _CONT(self, e, a):  # continue
        a.type = S_ACTION_CONT
        return a

    def _KILL_RF(self, e, a):  # restricted func.
        #return a
        print "killing"
        a.type, a.data = S_ACTION_KILL, S_RESULT_RF
        return a


if __name__ == "__main__":
    sys.exit(run(sys.argv))
