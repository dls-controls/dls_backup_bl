from logging import getLogger
from os import system

from dls_pmacanalyse import GlobalConfig

log = getLogger(__name__)


def backup_motor_controller(
        controller, server, port, geo_brick, t_serv, defaults
):
    desc = "pmac {} at {}:{}".format(controller, server, port)

    response = system("ping -c 5 {} > /dev/null 2>&1".format(server))
    if response != 0:
        msg = "ERROR: {} is offline".format(desc)
        log.critical(msg)
        return

    # Call dls-pmacanalyse backup
    # If backup fails retry specified number of times before giving up
    for attempt_num in range(defaults.retries):
        # noinspection PyBroadException
        try:
            msg = "Backing up {}.".format(desc)
            log.info(msg)

            config_object = GlobalConfig()
            pmac_object = config_object.createOrGetPmac(controller)
            pmac_object.setProtocol(server, port, t_serv)
            pmac_object.setGeobrick(geo_brick)
            pmac_object.readHardware(
                defaults.motion_folder, False, False, False, False)
            log.critical("SUCCESS: {} backed up".format(desc))

        except Exception:
            msg = "ERROR: {} backup failed on attempt {} of {}".format(
                desc, attempt_num + 1, defaults.retries)
            log.exception(msg)
            continue
        break
    else:
        msg = "ERROR: {} all {} attempts failed".format(
            desc, defaults.retries
        )
        log.critical(msg)
