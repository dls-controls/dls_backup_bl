import shutil
import telnetlib
from logging import getLogger

from dls_backup_bl.defaults import Defaults
from dls_pmacanalyse import GlobalConfig
from dls_pmaclib.dls_pmacremote import PmacTelnetInterface, \
    PmacEthernetInterface, RemotePmacInterface

log = getLogger(__name__)


class Brick:
    def __init__(
            self,
            controller: str,
            server: str,
            port: int,
            t_serv: bool,
            defaults: Defaults
    ):
        self.controller = controller
        self.server = server
        self.port = port
        self.t_serv = t_serv
        self.defaults = defaults
        self.pti: RemotePmacInterface = None
        self.desc = f"pmac {controller} at {server}:{port}"

    def check_connection(self):
        for attempt_num in range(self.defaults.retries):
            # noinspection PyBroadException
            try:
                t = telnetlib.Telnet()
                t.open(self.server, self.port, timeout=2)
                t.close()
            except BaseException:
                msg = f"connection attempt failed for {self.desc}"
                log.debug(msg, exc_info=True)
            else:
                break
        else:
            msg = f"ERROR: {self.desc} is offline"
            log.critical(msg)
            return False
        return True

    def connect(self):
        # make sure the pmac config we have backed up is also saved
        # on the brick itself
        if self.t_serv:
            self.pti = PmacTelnetInterface(verbose=False)
        else:
            self.pti = PmacEthernetInterface(verbose=False)
        self.pti.setConnectionParams(self.server, self.port)
        self.pti.connect()

    def backup_positions(self):
        if not self.check_connection():
            return

    def backup_controller(self):
        if not self.check_connection():
            return

        # Call dls-pmacanalyse backup
        # If backup fails retry specified number of times before giving up
        msg = f"Backing up {self.desc}."
        log.info(msg)
        for attempt_num in range(self.defaults.retries):
            # noinspection PyBroadException
            try:
                config_object = GlobalConfig()
                pmac_object = config_object.createOrGetPmac(self.controller)
                pmac_object.setProtocol(self.server, self.port, self.t_serv)
                # None means that readHardware will decide for itself
                pmac_object.setGeobrick(None)
                pmac_object.readHardware(
                    self.defaults.temp_dir, False, False, False, False)

                f_name = f"{self.controller}.pmc"
                new_file = self.defaults.temp_dir / f_name
                old_file = self.defaults.motion_folder / f_name
                shutil.move(str(new_file), str(old_file))

                self.connect()
                self.pti.sendCommand("save")
                self.pti.disconnect()

                log.critical(f"SUCCESS: {self.desc} backed up")
            except Exception:
                num = attempt_num + 1
                msg = f"ERROR: {self.desc} backup failed on attempt {num} " \
                      f"of {self.defaults.retries}"
                log.debug(msg, exc_info=True)
                log.error(msg)
                continue
            break
        else:
            msg = f"ERROR: {self.desc} all {self.defaults.retries} " \
                  f"attempts failed"
            log.critical(msg)
