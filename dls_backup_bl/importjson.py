from logging import getLogger
from pathlib import Path

from dls_backup_bl.defaults import Defaults
from dls_pmacanalyse import GlobalConfig

log = getLogger(__name__)


def import_json(cfg_file: Path, defaults: Defaults):
    config_object = GlobalConfig()
    config_object.configFile = str(cfg_file)
    config_object.processConfigFile()

    for pmac, details in config_object.pmacs.items():
        log.info("imported pmac {} at {}:{}".format(
            pmac, details.host, details.port
        ))
        if details.port == 1025:
            pass
