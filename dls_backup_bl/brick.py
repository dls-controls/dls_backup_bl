import shutil
from logging import getLogger
from os import system
import telnetlib

from dls_backup_bl.defaults import Defaults
from dls_pmacanalyse import GlobalConfig
from dls_pmaclib.dls_pmacremote import PmacTelnetInterface, \
    PmacEthernetInterface

log = getLogger(__name__)


def backup_motor_controller(
        controller: str,
        server: str,
        port: int,
        t_serv: bool,
        defaults: Defaults
):
    desc = "pmac {} at {}:{}".format(controller, server, port)

    for attempt_num in range(defaults.retries):
        # noinspection PyBroadException
        try:
            t = telnetlib.Telnet()
            t.open(server, port, timeout=2)
            t.close()
        except BaseException:
            msg = f"connection attempt failed for {desc}"
            log.debug(msg, exc_info=True)
        else:
            break
    else:
        msg = f"ERROR: {desc} is offline"
        log.critical(msg)
        return

    # Call dls-pmacanalyse backup
    # If backup fails retry specified number of times before giving up
    msg = "Backing up {}.".format(desc)
    log.info(msg)
    for attempt_num in range(defaults.retries):
        # noinspection PyBroadException
        try:
            config_object = GlobalConfig()
            pmac_object = config_object.createOrGetPmac(controller)
            pmac_object.setProtocol(server, port, t_serv)
            # None means that readHardware will decide for itself
            pmac_object.setGeobrick(None)
            pmac_object.readHardware(
                defaults.temp_dir, False, False, False, False)

            new_file = defaults.temp_dir / "{}.pmc".format(controller)
            old_file = defaults.motion_folder / "{}.pmc".format(controller)
            shutil.move(str(new_file), str(old_file))

            # make sure the pmac config we have backed up is also saved on the
            # brick itself
            if t_serv:
                pti = PmacTelnetInterface(verbose=False)
            else:
                pti = PmacEthernetInterface(verbose=False)
            pti.setConnectionParams(server, port)
            pti.connect()
            pti.sendCommand("save")
            pti.disconnect()

            log.critical("SUCCESS: {} backed up".format(desc))
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
