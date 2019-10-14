import json
import sys
from enum import IntEnum
from logging import getLogger
from pathlib import Path
from typing import List, NamedTuple

log = getLogger(__name__)


# The classes MotorController, TerminalServer, Zebra, TsType
# define the schema of the configuration file and the object graph that
# represents the configuration in memory the class BackupsConfig is the
# root of those representations

class MotorController(object):
    def __init__(self, controller, server, port):
        self.controller: str = controller
        self.server: str = server
        self.port: int = port

    def json_repr(self):
        return {
            "Controller": self.controller,
            "Server": self.server,
            "Port": self.port
        }


class TsType(IntEnum):
    moxa = 0
    acs = 1
    old_acs = 2


class TerminalServer(object):
    def __init__(self, server, ts_type):
        self.server: str = server
        self.ts_type: TsType = ts_type

    def json_repr(self):
        return {
            "Server": self.server,
            "Type": self.ts_type
        }


class Zebra(NamedTuple):
    Name: str


class BackupsConfig(object):
    def __init__(self, motion_controllers, terminal_servers, zebras):
        self.motion_controllers: List[MotorController] = motion_controllers
        self.terminal_servers: List[TerminalServer] = terminal_servers
        self.zebras: List[Zebra] = zebras

    def json_repr(self):
        return {
            "MotionControllers": self.motion_controllers,
            "TerminalServers": self.terminal_servers,
            "Zebras": self.zebras
        }

    @staticmethod
    def empty():
        return BackupsConfig([], [], [])

    @staticmethod
    def load(json_file: Path):
        with json_file.open() as f:
            raw_items = json.loads(f.read())
        m = [MotorController(*i.values()) for i in
             raw_items["MotionControllers"]]
        t = [TerminalServer(*i.values()) for i in
             raw_items["TerminalServers"]]
        z = [Zebra(*i.values()) for i in 
             raw_items["Zebras"]]
        return BackupsConfig(m, t, z)

    def dump(self, json_file: Path):
        with json_file.open("w") as f:
            json.dump(self, f, cls=ComplexEncoder, sort_keys=True, indent=4)

    def dumps(self):
        return json.dumps(self, cls=ComplexEncoder, sort_keys=True, indent=4)

    def count_devices(self):
        return len(self.motion_controllers) + \
               len(self.terminal_servers) + \
               len(self.zebras)


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'json_repr'):
            return obj.json_repr()
        else:
            return json.JSONEncoder.default(self, obj)


mc = MotorController(
    controller="BL00G-MO-STEP-01",
    server="192.168.001",
    port=1025)
mc2 = MotorController(
    controller="BL00G-MO-STEP-02",
    server="192.168.002",
    port=1025)
ts = TerminalServer(server="ts1", ts_type=TsType.moxa)

b = BackupsConfig.empty()
b.motion_controllers += [mc, mc2]
b.terminal_servers.append(ts)

f = Path("/tmp/tstBackup.json")
b.dump(f)
b2 = BackupsConfig.load(f)
print(b2.dumps())
exit(0)


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
