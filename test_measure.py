import pytest

import sys
import io
import os
import signal

from measure import _init_and_run

# NOTE: tests will not work unless driver imports are hard coded to import base_measure due to pytest not appearing in subprocess sys.modules

measure_json_stdin = '''\
{
    "metrics": [
        "number of errors",
        "requests throughput",
        "time per request",
        "time per request (across all concurrent requests)",
        "time taken",
        "networkPacketsIn_ws2012_sandbox_asg",
        "networkPacketsIn_ws2012_sandbox_asg_PerInstance",
        "networkPacketsOut_ws2012_sandbox_asg",
        "networkPacketsOut_ws2012_sandbox_asg_PerInstance"
    ]
}
'''

def test_info(monkeypatch):
    with monkeypatch.context() as m:
        # replicate command line arguments fed in by servo
        m.setattr(sys, 'argv', ['', '--info', '1234'])
        with pytest.raises(SystemExit) as exit_exception:
            _init_and_run()
        assert exit_exception.type == SystemExit
        assert exit_exception.value.code == 0

def test_describe(monkeypatch):
    with monkeypatch.context() as m:
        # replicate command line arguments fed in by servo
        m.setattr(sys, 'argv', ['', '--describe', '1234'])
        with pytest.raises(SystemExit) as exit_exception:
            _init_and_run()
        assert exit_exception.type == SystemExit
        assert exit_exception.value.code == 0

def test_measure(monkeypatch):
    with monkeypatch.context() as m:
        # replicate command line arguments fed in by servo
        m.setattr(sys, 'argv', ['', '1234'])
        m.setattr(sys, 'stdin', io.StringIO(measure_json_stdin))
        _init_and_run()
        assert True
