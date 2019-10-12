from logging import getLogger
from pathlib import Path

from dls_backup_bl.config import BackupConfig
from dls_backup_bl.defaults import Defaults
from dls_pmacanalyse import GlobalConfig

log = getLogger(__name__)


def import_json(cfg_file: Path, json_file):
    config_object = GlobalConfig()
    config_object.configFile = str(cfg_file)
    config_object.processConfigFile()

    json_config = BackupConfig(json_file)
    json_config.load_config()

    for pmac, details in config_object.pmacs.items():
        is_geobrick = not details.termServ
        json_config.add_pmac(pmac, details.host, details.port, is_geobrick)
        log.info("imported pmac {} at {}:{}".format(
            pmac, details.host, details.port
        ))

    json_config.write_json_file()
