import json
import sys
from enum import IntEnum
from logging import getLogger
from pathlib import Path
from typing import List

import attr

log = getLogger(__name__)


# The classes MotorController, TerminalServer, Zebra, TsType
# define the schema of the configuration file and the object graph that
# represents the configuration in memory the class BackupsConfig is the
# root of those representations and provides load and save methods


class JsonAbleDictionaryTuple:
    def __getitem__(self, item):
        return self.__dict__[item]

    @classmethod
    def keys(cls):
        return cls.__annotations__.keys()

    def items(self):
        return self.__dict__.items()


@attr.s(auto_attribs=True)
class MotorController(JsonAbleDictionaryTuple):
    controller: str
    port: int = attr.ib(converter=int)
    server: str


class TsType(IntEnum):
    moxa = 0
    acs = 1
    old_acs = 2


@attr.s(auto_attribs=True)
class TerminalServer(JsonAbleDictionaryTuple):
    server: str
    ts_type: TsType


@attr.s(auto_attribs=True)
class Zebra(JsonAbleDictionaryTuple):
    Name: str


@attr.s(auto_attribs=True)
class BackupsConfig(JsonAbleDictionaryTuple):
    motion_controllers: List[MotorController]
    terminal_servers: List[TerminalServer]
    zebras: List[Zebra]

    @classmethod
    def my_types(cls):
        return [MotorController, TerminalServer, Zebra]

    @classmethod
    def empty(cls):
        return cls([], [], [])

    # noinspection PyBroadException
    @staticmethod
    def from_json(json_file: Path):
        try:
            with json_file.open() as f:
                raw_items = json.loads(f.read())
            m = [MotorController(*i.values()) for i in raw_items["motion_controllers"]]
            t = [TerminalServer(*i.values()) for i in raw_items["terminal_servers"]]
            z = [Zebra(*i.values()) for i in raw_items["zebras"]]
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
            raise

    def dumps(self):
        return json.dumps(self, cls=ComplexEncoder, sort_keys=True, indent=4)

    def count_devices(self):
        return (
            len(self.motion_controllers) + len(self.terminal_servers) + len(self.zebras)
        )


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return json.JSONEncoder.default(self, obj)
