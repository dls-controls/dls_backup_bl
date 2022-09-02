import subprocess
import sys

from dls_backup_bl import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "dls_backup_bl", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
