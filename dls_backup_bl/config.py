import json
import sys
from enum import IntEnum
from logging import getLogger
from pathlib import Path
from typing import List, NamedTuple

log = getLogger(__name__)


# The classes MotorController, TerminalServer, Zebra, Backups, TsType
# define the schema of the configuration file
class MotorController(NamedTuple):
    Controller: str
    Server: str
    Port: int


class TsType(IntEnum):
    moxa = 0
    acs = 1
    old_acs = 2


class TerminalServer(NamedTuple):
    Server: str
    Type: TsType


class Zebra(NamedTuple):
    Name: str


class Backups(NamedTuple):
    motion_controllers: List[MotorController]
    terminal_servers: List[TerminalServer]
    zebras: List[Zebra]

    @staticmethod
    def empty():
        return Backups([], [], [])

    # gk 10/2019 this is my crude attempt to reconstruct useful named tuples
    # from the serialized data. Is there no generic way to do this though json?
    # I created a json schema, thinking that this would allow it but apart from
    # the very out of date https://github.com/cwacek/python-jsonschema-objects
    # I see no solution out there.
    # the crude approach works OK for this simple structure
    @staticmethod
    def load(json_file: Path):
        with json_file.open() as f:
            raw_items = json.loads(f.read())
        m = [MotorController(*i) for i in raw_items[0]]
        t = [TerminalServer(*i) for i in raw_items[1]]
        z = [Zebra(*i) for i in raw_items[2]]
        return Backups(m, t, z)

    def dump(self, json_file: Path):
        with json_file.open("w") as f:
            f.write(json.dumps(self))

    def count_devices(self):
        return len(self.motion_controllers) + \
               len(self.terminal_servers) + \
               len(self.zebras)


# Todo - to get the old schema we need some dictionaries
#  but tuples are nicer for in memory structure - can we get both?
mc = MotorController(
    Controller="BL00G-MO-STEP-01",
    Server="192.168.0·1",
    Port=1025)

b = Backups.empty()
b.motion_controllers.append(mc)

print(b)
f = Path('/tmp/b.json')
b.dump(f)
b2 = Backups.load(f)
print(b2)
print(b2.motion_controllers[0].Controller)

exit(0)

# does not work since dumps can only serialize dict, list etc.
print(json.dumps(b))

class BackupConfig():
    def __init__(self, json_file: Path):
        self.json_file: Path = json_file
        self.json_data: Backups = Backups.empty()

    def load_config(self, check_empty: bool = False):
        # Open JSON file of device details
        result = True
        # noinspection PyBroadException
        try:
            self.read_json_file()

        # Capture problems opening or reading the file
        except BaseException:
            msg = "Invalid json configuration file"
            log.debug(msg, exc_info=True)
            log.error(msg)
            raise

        if check_empty:
            if self.json_data.count_devices == 0:
                result = False
                log.critical("No configured devices")
                print("No devices in  {}".format(self.json_file))
                print(self.empty_message)
            return result

    def add_pmac(self, name: str, server: str, port: int):
        mc = MotorController(name, server, port)
        self.json_data.motion_controllers.append(mc)

    def read_json_file(self):
        # noinspection PyBroadException
        try:
            self.json_data = Backups.load(self.json_file)
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
            self.json_data.dump(self.json_file)
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
