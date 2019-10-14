import json
import sys
from enum import IntEnum
from logging import getLogger
from pathlib import Path
from typing import List, NamedTuple

from attr import dataclass

log = getLogger(__name__)


# The classes MotorController, TerminalServer, Zebra, TsType
# define the schema of the configuration file and the object graph that
# represents the configuration in memory the class BackupsConfig is the
# root of those representations and provides load and save methods
# todo this works fine but soooo much boilerplate code - work out how to
#  create a base class like NamedTuple that automatically does json_repr
#  and __init__()

@dataclass
class MotorController:
    controller: str
    port: int
    server: str

    # todo put these in a base class
    def __getitem__(self, item):
        return self.__dict__[item]

    def keys(self):
        return self.__dict__.keys()


class TsType(IntEnum):
    moxa = 0
    acs = 1
    old_acs = 2


@dataclass
class TerminalServer:
    server: str
    ts_type: TsType


@dataclass
class Zebra:
    Name: str


@dataclass
class BackupsConfig(object):
    motion_controllers: List[MotorController]
    terminal_servers: List[TerminalServer]
    zebras: List[Zebra]

    # todo put this in a base class
    def __getitem__(self, item):
        return self.__dict__[item]

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
                 raw_items["motion_controllers"]]
            t = [TerminalServer(*i.values()) for i in
                 raw_items["terminal_servers"]]
            z = [Zebra(*i.values()) for i in
                 raw_items["zebras"]]
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
            msg = "Unable to save configuration file"
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
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return json.JSONEncoder.default(self, obj)




