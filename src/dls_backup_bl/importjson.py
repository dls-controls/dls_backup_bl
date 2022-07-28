from logging import getLogger
from pathlib import Path

from dls_pmacanalyse.globalconfig import GlobalConfig

from dls_backup_bl.config import BackupsConfig, MotorController

log = getLogger(__name__)


def import_json(cfg_file: Path, json_file):
    config_object = GlobalConfig()
    config_object.configFile = str(cfg_file)
    config_object.processConfigFile()

    # we append to the existing json file, overwriting any duplicate
    # entries
    json_config = BackupsConfig.from_json(json_file)

    for pmac, details in config_object.pmacs.items():
        mc = MotorController(pmac, details.port, details.host)
        for i in range(len(json_config.motion_controllers)):
            if json_config.motion_controllers[i].controller == pmac:
                json_config.motion_controllers.pop(i)
                break
        json_config.motion_controllers.append(mc)
        log.info("imported pmac {} at {}:{}".format(pmac, details.host, details.port))

    json_config.save(json_file)
