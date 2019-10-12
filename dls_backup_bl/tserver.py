import hashlib
import re
from http.cookiejar import CookieJar
from logging import getLogger
from os import system
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, build_opener, HTTPCookieProcessor

import pexpect

from .defaults import Defaults

log = getLogger(__name__)


# todo make ts_type an enum
# todo use Path instead of system
class TsConfig:
    def __init__(self, ts: str, backup_directory: Path, username: str = None,
                 password: str = None, ts_type: str = None):
        self.ts = ts
        self.path: Path = backup_directory / self.ts

        self.success = False
        if ts_type in [None, "moxa"]:
            self.success = self.get_moxa_config(
                username or "admin", password or "tslinux", "Config.txt"
            )
        if self.success == ts_type in [None, "acs"]:
            self.success = self.get_acs_config(
                username or "root", password or "tslinux",
                "/mnt/flash/config.tgz"
            )
        if self.success == ts_type in [None, "acsold"]:
            self.success = self.get_acs_config(
                username or "root", password or "tslinux", "/proc/flash/script"
            )

    def get_moxa_config(self, username, password, remote_path):
        # get the base page to pickup the "fake_challenge" variable
        url = "https://" + self.ts
        base = urlopen(url).read()
        match = re.search(
            "<INPUT type=hidden name=fake_challenge value=([^>]*)>", base)
        if match is None:
            print(
                "This returns a web page that doesn't look like a moxa login "
                "screen")
            return False
        fake_challenge = match.groups()[0]

        # do what the function SetPass() does on the login screen
        md = hashlib.md5(fake_challenge).hexdigest()
        p = ""
        for c in password:
            p += "%x" % ord(c)
        md5_pass = ""
        for i in range(len(p)):
            m = int(p[i], 16)
            n = int(md[i], 16)
            md5_pass += "%x" % (m ^ n)

        # store login cookie
        cj = CookieJar()
        opener = build_opener(HTTPCookieProcessor(cj))
        login_data = urlencode(dict(Username=username, MD5Password=md5_pass))
        resp = opener.open(url, login_data)
        if "Login Failed" in resp.read():
            print("Wrong password for this moxa")
            return False
        cfg_path = self.path / remote_path
        print("Saving config to", cfg_path)
        open(cfg_path, "w").write(opener.open(url + "/" + remote_path).read())
        return True

    def get_acs_config(self, username, password, remote_path):
        tar = self.path / "config.tar.gz"
        child = pexpect.spawn(
            'scp %s@%s:%s %s' % (username, self.ts, remote_path, tar))
        i = child.expect(
            ['Are you sure you want to continue connecting (yes/no)?',
             'Password:'], timeout=120)
        if i == 0:
            child.sendline("yes")
            child.expect('Password:', timeout=120)
        child.sendline(password)
        i = child.expect([pexpect.EOF, "scp: [^ ]* No such file or directory"])
        if i == 1:
            print("Remote path %s doesn't exist on this ACS" % remote_path)
            return False
        else:
            print("Un-tarring", tar)
            system("tar --no-overwrite-dir -xzf %s -C %s" % (
                tar, str(self.path)))
            system("chmod -f -R g+rwX,o+rX %s" % str(self.path))
            system("find %s -type d -exec chmod -f g+s {} +" %
                   str(self.path))
            return True


def backup_terminal_server(server: str, ts_type: str, defaults: Defaults):
    desc = "terminal server {} type {}".format(server, ts_type)

    # If backup fails retry specified number of times before giving up
    for attempt_num in range(defaults.retries):
        # noinspection PyBroadException
        try:
            log.info('Backing up {}'.format(desc))
            TsConfig(server, defaults.ts_folder, None, None, ts_type)
            log.critical("SUCCESS backed up {}".format(desc))
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
