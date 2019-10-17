import shutil
import telnetlib
from logging import getLogger

from dls_backup_bl.defaults import Defaults
from dls_pmacanalyse.dls_pmacanalyse import Pmac, PmacReadError
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
        self.analyse: Pmac = None
        self.desc = f"pmac {controller} at {server}:{port}"

    # this destructor saves having loads of disconnect logic in the exception
    # handlers. Without it the test brick quickly ran out of connections
    def __del__(self):
        if self.pti:
            self.pti.disconnect()

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

    def connect_analyse(self):
        analyse_config = GlobalConfig()
        self.analyse = analyse_config.createOrGetPmac(self.controller)
        self.analyse.setProtocol(self.server, self.port, self.t_serv)
        # None means that readHardware will decide for itself
        self.analyse.setGeobrick(None)

    def connect_direct(self):
        # make sure the pmac config we have backed up is also saved
        # on the brick itself
        if self.t_serv:
            self.pti = PmacTelnetInterface(verbose=False)
        else:
            self.pti = PmacEthernetInterface(verbose=False)
        self.pti.setConnectionParams(self.server, self.port)
        self.pti.connect()

    def determine_axes(self):
        # each installed macro station supports 8 axes
        (return_str, status) = self.pti.sendCommand('i20 i21 i22 i23')
        if not status:
            raise PmacReadError(return_str)
        macroIcAddresses = return_str[:-2].split('\r')
        macro_ic_stations = 0
        for i in range(4):
            if macroIcAddresses[i] != '$0' and macroIcAddresses[i] != '0':
                macro_ic_stations += 1
        axis_count = macro_ic_stations * 8

        # if this is a geobrick add 8 built-in axes
        (return_str, status) = self.pti.sendCommand('cid')
        if not status:
            raise PmacReadError(return_str)
        pmac_id = return_str[:-2]
        if pmac_id == '603382':
            axis_count += 8

        return axis_count

    def backup_positions(self):
        log.info(f"Getting motor positions for {self.desc}.")
        if not self.check_connection():
            return

        for attempt_num in range(self.defaults.retries):
            # noinspection PyBroadException
            try:
                self.connect_direct()
                axes = self.determine_axes()

                pmc = []
                for axis in range(axes):
                    cmd = f"M{axis + 1}62"
                    (return_str, status) = self.pti.sendCommand(cmd)
                    if not status:
                        raise PmacReadError(return_str)
                    pmc.append(f"{cmd} = {return_str[:-2]}\n")

                self.pti.disconnect()
                self.pti = None

                f_name = f"{self.controller}_positions.pmc"
                new_file = self.defaults.motion_folder / f_name
                with new_file.open("w") as f:
                    f.writelines(pmc)

                log.critical(f"SUCCESS: positions retrieved for {self.desc}")
            except Exception:
                num = attempt_num + 1
                msg = f"ERROR: position retrieval for {self.desc} failed on " \
                    f"attempt {num} of {self.defaults.retries}"
                log.debug(msg, exc_info=True)
                log.error(msg)
                continue
            break
        else:
            msg = f"ERROR: {self.desc} all {self.defaults.retries} " \
                  f"attempts to save positions failed"
            log.critical(msg)

    def restore_positions(self):
        pass

    def backup_controller(self):
        if not self.check_connection():
            return

        # Call dls-pmacanalyse backup
        # If backup fails retry specified number of times before giving up
        log.info(f"Backing up {self.desc}.")
        for attempt_num in range(self.defaults.retries):
            # noinspection PyBroadException
            try:
                self.connect_analyse()
                self.analyse.readHardware(
                    self.defaults.temp_dir, False, False, False, False)

                f_name = f"{self.controller}.pmc"
                new_file = self.defaults.temp_dir / f_name
                old_file = self.defaults.motion_folder / f_name
                shutil.move(str(new_file), str(old_file))

                self.connect_direct()
                self.pti.sendCommand("save")
                self.pti.disconnect()
                self.pti = None

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
                  f"backup attempts failed"
            log.critical(msg)
