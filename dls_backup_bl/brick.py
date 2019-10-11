from logging import getLogger
from os import path

from dls_pmacanalyse import GlobalConfig

log = getLogger(__name__)


def backup_motor_controller(
        controller, server, port, geo_brick, t_serv, backup_directory, retries,
        my_email, property_list
):
    # Call dls-pmacanalyse backup
    # If backup fails retry specified number of times before giving up
    for attempt_num in range(retries):
        # noinspection PyBroadException
        try:
            msg = "Backing up {} on server {}:{}. Attempt {} of {}".format(
                controller, server, port, attempt_num + 1, retries
            )
            log.info(msg)

            config_object = GlobalConfig()
            config_object.backupDir = path.join(
                backup_directory, "MotionControllers"
            )
            config_object.writeAnalysis = False
            pmac_object = config_object.createOrGetPmac(controller)
            pmac_object.setProtocol(server, port, t_serv)
            pmac_object.setGeobrick(geo_brick)
            config_object.analyse()
            log.info("Finished backing up {}".format(controller))
            property_list.append("Successful")

        except Exception as e:
            msg = "ERROR: Problem backing up {} on server {}:{}".format(
                controller, server, port
            )
            my_email.add_to_message(msg)
            log.exception(msg)
            continue
        break
    else:
        error_message = "All {} attempts to backup {} failed".format(
            retries, controller
        )
        my_email.add_to_message(error_message)
        log.error(error_message)
        property_list.append("Failed")
