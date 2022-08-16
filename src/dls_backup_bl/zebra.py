from logging import getLogger
from time import sleep

from cothread.catools import caget, caput

from dls_backup_bl.defaults import Defaults

log = getLogger(__name__)


def backup_zebra(name: str, defaults: Defaults):
    desc = "zebra {}".format(name)

    for AttemptNum in range(defaults.retries):
        # noinspection PyBroadException
        try:
            log.info("Backing up {}".format(desc))

            folder = defaults.zebra_folder / name

            # todo may need a (empty) temp path and then copy to zebra_folder
            caput("%s:%s" % (str(name), "CONFIG_FILE"), folder, datatype=999)
            caput("%s:%s" % (str(name), "CONFIG_WRITE.PROC"), 1, timeout=60, wait=True)
            # Store button PV triggered successfully
            pv_name = f"{str(name)}:CONFIG_STATUS"
            log.info(f"checking status {pv_name}")
            pv = str(caget(pv_name, datatype=999, timeout=20))
            while "Writing" in pv:
                # Waiting for write to complete
                sleep(1)
                pv = str(caget(pv_name, datatype=999))
            if pv.startswith("Too soon"):
                log.warning(pv)
                log.warning("Waiting 3 seconds...")
                sleep(3)
                continue
            elif str(pv).startswith("Can't open '"):
                raise RuntimeWarning(pv)
            elif pv == "Done":
                log.critical("SUCCESS backed up {}".format(desc))

        except TimeoutError:
            msg = "ERROR: Timeout connecting to {} check IOC".format(desc)
            log.error(msg)
            continue
        except BaseException:
            msg = "ERROR: Problem backing up {}".format(name)
            log.debug(msg, exc_info=True)
            log.error(msg)
            continue
        break
    else:
        msg = "ERROR: {} all {} attempts failed".format(defaults.retries, desc)
        log.critical(msg)
