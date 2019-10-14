from logging import getLogger
from pathlib import Path

from dls_backup_bl.config import BackupsConfig, MotorController
from dls_pmacanalyse import GlobalConfig

log = getLogger(__name__)


def import_json(cfg_file: Path, json_file):
    config_object = GlobalConfig()
    config_object.configFile = str(cfg_file)
    config_object.processConfigFile()

    # the below could be used to append but is this likely desirable?
    #json_config = BackupsConfig.load(json_file)
    json_config = BackupsConfig.empty()

    for pmac, details in config_object.pmacs.items():
        mc = MotorController(pmac, details.port, details.host)
        json_config.motion_controllers.append(mc)
        log.info("imported pmac {} at {}:{}".format(
            pmac, details.host, details.port
        ))

    json_config.save(json_file)
