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
# root of those representations and provides load and save methods
# todo this works fine but soooo much boilerplate code - work out how to
#  create a base class like NamedTuple that automatically does json_repr
#  and __init__()

class MotorController(object):
    def __init__(self, controller, port, server):
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
            "MotorControllers": self.motion_controllers,
            "TerminalServers": self.terminal_servers,
            "Zebras": self.zebras
        }

    @staticmethod
    def empty():
        return BackupsConfig([], [], [])

    # noinspection PyBroadException
    @staticmethod
    def load(json_file: Path):
        try:
            with json_file.open() as f:
                raw_items = json.loads(f.read())
            m = [MotorController(*i.values()) for i in
                 raw_items["MotorControllers"]]
            t = [TerminalServer(*i.values()) for i in
                 raw_items["TerminalServers"]]
            z = [Zebra(*i.values()) for i in
                 raw_items["Zebras"]]
        except Exception:
            msg = "JSON file missing or invalid"
            log.debug(msg, exc_info=True)
            log.error(msg)
            sys.exit()
        return BackupsConfig(m, t, z)

    # noinspection PyBroadException
    def save(self, json_file: Path):
        try:
            with json_file.open("w") as f:
                json.dump(self, f, cls=ComplexEncoder, sort_keys=True, indent=4)
        except Exception:
            msg = "Unable to configuration file"
            log.debug(msg, exc_info=True)
            log.error(msg)

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




