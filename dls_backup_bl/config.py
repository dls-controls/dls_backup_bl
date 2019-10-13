import json
import sys
from collections import OrderedDict
from logging import getLogger
from pathlib import Path
from typing import List

log = getLogger(__name__)


class BackupConfig:
    def __init__(self, json_file: Path):
        self.json_file = json_file
        self.json_data = None
        self.motion_controllers: List = None
        self.terminal_servers: List = None
        self.zebras: List = None

    def load_config(self, check_empty: bool = False):
        # Open JSON file of device details
        result = True
        # noinspection PyBroadException
        try:
            self.read_json_file()

            # use [] instead of get() to verify JSON
            self.motion_controllers = self.json_data["MotorControllers"]
            self.terminal_servers = self.json_data["TerminalServers"]
            self.zebras = self.json_data["Zebras"]

        # Capture problems opening or reading the file
        except BaseException:
            msg = "Invalid json configuration file"
            log.debug(msg, exc_info=True)
            log.error(msg)
            raise

        if check_empty:
            total_items = len(self.motion_controllers) + \
                          len(self.terminal_servers) + len(self.zebras)
            if total_items == 0:
                result = False
                log.critical("No configured devices")
                print("No devices in  {}".format(self.json_file))
                print(self.empty_message)
            return result

    def add_pmac(self, name: str, server: str, port: str):
        new_item = {"Controller": name, "Server": server, "Port": port}
        self.motion_controllers.append(new_item)

    def read_json_file(self):
        # Attempt to open the JSON file
        # noinspection PyBroadException
        try:
            with self.json_file.open() as f:
                # Maintain order using a dictionary
                self.json_data = json.load(f, object_pairs_hook=OrderedDict)
        # Capture problems opening or reading the file
        except Exception:
            msg = "JSON file missing or invalid"
            log.debug(msg, exc_info=True)
            log.error(msg)
            sys.exit()

    def write_json_file(self):
        # Overwrite the JSON file including the changes
        # noinspection PyBroadException
        try:
            with self.json_file.open("w") as f:
                # Write the data keeping a readable style
                # Note that sort_keys is not used as this undoes the chosen
                # ordering
                data = json.dumps(
                    self.json_data, indent=4, separators=(',', ': ')
                )
                f.write(data)
        # Capture problems opening or saving the file
        except Exception:
            msg = "Invalid JSON file name"
            log.debug(msg, exc_info=True)
            log.error(msg)

    empty_message = """
BACKUP ABORTED

The configuration file contains no devices for backup. 
Please import the dls-pmac-analyse cfg file with --import-cfg and then 
use dls-edit-backup.py to complete the device configuration.
"""
