import subprocess
import sys

from dls_backup_bl import __version__

# Can't easily support this test on github - the import of cothread
# tries to go and find the channel access library, which is not installed
# this project should really be built in an EPICS container on github

# def test_cli_version():
#     cmd = [sys.executable, "-m", "dls_backup_bl.backup", "--version"]
#     assert subprocess.check_output(cmd).decode().strip() == __version__


def test_gui_version():
    cmd = [sys.executable, "-m", "dls_backup_gui.dls_backup_gui", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
