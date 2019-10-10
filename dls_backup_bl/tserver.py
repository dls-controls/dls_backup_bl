import hashlib
import re
from http.cookiejar import CookieJar
from os import path, system
from urllib.parse import urlencode
from urllib.request import urlopen, build_opener, HTTPCookieProcessor

import pexpect

from .util import mkdir_p


class TsConfig:
    def __init__(self, ts, backup_directory, username=None, password=None,
                 ts_type=None):
        self.ts = ts
        self.path = path.join(backup_directory, "TerminalServers", self.ts)
        mkdir_p(self.path)
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
        txt = path.join(self.path, remote_path)
        print("Saving config to", txt)
        open(txt, "w").write(opener.open(url + "/" + remote_path).read())
        return True

    def get_acs_config(self, username, password, remote_path):
        tar = path.join(self.path, "config.tar.gz")
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
            system("tar --no-overwrite-dir -xzf %s -C %s" % (tar, self.path))
            system("chmod -f -R g+rwX,o+rX %s" % self.path)
            system("find %s -type d -exec chmod -f g+s {} +" % self.path)
            return True


def backup_terminal_server(
        server, ts_type, backup_directory, num_retries, my_email, property_list
):
    # If backup fails retry specified number of times before giving up
    for AttemptNum in range(num_retries):
        # noinspection PyBroadException
        try:
            print(
                "Backing up terminal server " + server + " of type " + ts_type +
                ". Attempt " + str(
                    AttemptNum + 1) + " of " + str(num_retries))
            TsConfig(server, backup_directory, None, None, ts_type)
            print("\rFinished backing up " + server)
            property_list.append("Successful")
        except Exception as e:
            error_message = "ERROR: Problem backing up {}\n".format(server)
            error_message += str(e)
            my_email.add_to_message(error_message)
            print(error_message)
            continue
        break
    else:
        error_message = "All " + str(
            num_retries) + " attempts to backup " + server + " failed"
        my_email.add_to_message(error_message)
        print(error_message)
        property_list.append("Failed")
