import hashlib
import re
import shutil
from http.cookiejar import CookieJar
from logging import getLogger
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, build_opener, HTTPCookieProcessor

import pexpect
import requests
from requests.auth import HTTPBasicAuth

from .defaults import Defaults

log = getLogger(__name__)


# todo make ts_type an enum
# todo use Path instead of system
class TsConfig:
    def __init__(self, ts: str, backup_directory: Path, username: str = None,
                 password: str = None, ts_type: str = None):
        self.ts = ts
        self.path: Path = backup_directory
        self.desc = f"Terminal server {ts} type {ts_type}"

        log.info(f"backing up {self.desc}")

        self.success = False
        if ts_type == "moxa":
            self.success = self.get_moxa_config(
                username or "admin", password or "tslinux", "Config.txt"
            )
        elif ts_type == "acs":
            self.success = self.get_acs_config(
                username or "root", password or "tslinux",
                "/mnt/flash/config.tgz"
            )
        elif ts_type == "acsold":
            self.success = self.get_acs_config(
                username or "root", password or "tslinux", "/proc/flash/script"
            )
        else:
            log.error(f"unknown type for {desc}")

    def get_moxa_config(self, username, password, remote_path):
        # get the base page to pickup the "fake_challenge" variable

        cfg_path = self.path / (self.ts + "_config.dec")

        url = f"http://{self.ts}/{remote_path}"

        session = requests.Session()
        session.auth = (username, password)

        auth = session.post('http://' + self.ts)
        response = session.get(url, stream=True)
        response.raise_for_status()
        with cfg_path.open("wb") as f:
            shutil.copyfileobj(response.raw, f)
        return True

    def get_acs_config(self, username, password, remote_path):
        tar = self.path / (self.ts + "_config.tar.gz")
        child = pexpect.spawn(
            'scp %s@%s:%s %s' % (username, self.ts, remote_path, str(tar)))
        i = child.expect(
            ['Are you sure you want to continue connecting (yes/no)?',
             'Password:'], timeout=120)
        if i == 0:
            child.sendline("yes")
            child.expect('Password:', timeout=120)
        child.sendline(password)
        i = child.expect([pexpect.EOF, "scp: [^ ]* No such file or directory"])
        if i == 1:
            log.error("Remote path %s doesn't exist on this ACS" % remote_path)
            return False
        else:
            return True


def backup_terminal_server(server: str, ts_type: str, defaults: Defaults):
    desc = "terminal server {} type {}".format(server, ts_type)

    # If backup fails retry specified number of times before giving up
    for attempt_num in range(defaults.retries):
        # noinspection PyBroadException
        try:
            t = TsConfig(server, defaults.ts_folder, None, None, ts_type)
            if t.success:
                log.critical("SUCCESS backed up {}".format(desc))
            else:
                log.critical("ERROR failed to back up {}".format(desc))
        except Exception:
            msg = "ERROR: {} backup failed on attempt {} of {}".format(
                desc, attempt_num + 1, defaults.retries)
            log.debug(msg, exc_info=True)
            log.error(msg)
            continue
        break
    else:
        msg = "ERROR: {} all {} attempts failed".format(
            desc, defaults.retries
        )
        log.critical(msg)
