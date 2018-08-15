import sys
import os
import subprocess
import select
import json

import typing

class _a(object): pass

# config - FIXME
g_args = _a()
g_args.verbose = False

#def run_and_track(driver, app, req = None, describe = False, progress_cb: typing.Callable[..., None] = None):
def run_and_track(path, *args, data = None, progress_cb: typing.Callable[..., None] = None):
    '''
    Execute an external program and read its output line by line, expecting that each line is a valid json object.
    All decoded lines are sent to progress_cb as they arrive. In addition, the object on the last line is returned.
    Parameters:
        cmd    : command to run (passed to subprocess.Popen)
        data   : input data, if not None, sent json-encoded to the program's stdin
        progress_cb: callback function to report progress; if it raises exception, try to abort driver's operation
                Callback is called with the entire output line (decoded as json)
    '''
    # global args

    cmd = [path]
    cmd.extend(args)
    if g_args.verbose:
        print('DRIVER REQUEST:', cmd)

    # test only FIXME@@@
    if progress_cb:
        progress_cb( dict(progress = 0, message = 'starting driver') )

    # prepare stdin in-memory file if a request is provided
    if data is not None:
        stdin = json.dumps(data).encode("UTF-8")   # input descriptor -> json -> bytes
    else:
        stdin = b''         # no stdin

    # execute driver, providing request and capturing stdout/stderr
    proc = subprocess.Popen(cmd, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stderr = [] # collect all stderr here
    rsp = {"status": "nodata"} # in case driver outputs nothing at all
    wi = [proc.stdin]
    ei = [proc.stdin, proc.stdout,proc.stderr]
    eof_stdout = False
    eof_stderr = False #
    while True:
        r,w,e = select.select([proc.stdout,proc.stderr], wi, ei )
        if eof_stdout and eof_stderr and proc.poll() is not None: # process exited and no more data
            break
        for h in r:
            if h is proc.stderr:
                l = h.read(4096)
                if not l:
                    eof_stderr = True
                    continue
                stderr.append(l)
            else: # h is proc.stdout
                l = h.readline()
                if not l:
                    eof_stdout = True
                    continue
                stdout_line = l.strip().decode("UTF-8") # there will always be a complete line, driver writes one line at a time
                if g_args.verbose:
                    print('DRIVER STDOUT:', stdout_line)
                if not stdout_line:
                    continue # ignore blank lines (shouldn't be output, though)
                try:
                    stdout = json.loads(stdout_line)
                except Exception as x:
                    proc.terminate()
                    # TODO: handle exception in json.loads?
                    raise
                if stdout:
                    progress_cb(stdout)
                    rsp = stdout
        if w:
            l = min(getattr(select,'PIPE_BUF',512), len(stdin)) # write with select.PIPE_BUF bytes or less should not block
            if not l: # done sending stdin
                proc.stdin.close()
                wi = []
                ei = [proc.stdout,proc.stderr]
            else:
                proc.stdin.write(stdin[:l])
                stdin = stdin[l:]
        # if e:

    rc = proc.returncode
    if g_args.verbose or rc != 0:
        print('\n---driver stderr-----------', file=sys.stderr)
        print( (b"\n".join(stderr)).decode("UTF-8"), file=sys.stderr )  # use accumulated stderr
        print('----------------------\n', file=sys.stderr)

    if g_args.verbose:
        print('DRIVER RESPONSE:', rsp, file=sys.stderr)

    if rc != 0: # error, add verbose info to returned data
        if not rsp.get("status"): # NOTE if driver didn't return any json, status will be "nodata". Preferably, it should print structured data even on failures, so errors can be reported neatly.
            rsp["status"] = "failed"
        m = rsp.get("message", "")
        # if config[report_stderr]:
        rs = os.environ.get("OPTUNE_VERBOSE_STDERR", "all") # FIXME: default setting?
        if rs == "all":
            rsp["message"] = m + "\nstderr:\n" + (b"\n".join(stderr)).decode("UTF-8")
        elif rs == "minimal": # 1st two lines only
            rsp["message"] = m + "\nstderr:\n" + (b"\n".join(stderr[0:2])).decode("UTF-8")
        # else don't send any bit of stderr

    return rsp

