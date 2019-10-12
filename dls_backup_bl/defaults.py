from pathlib import Path
from os import environ


class Defaults:
    """
    manage default values for paths and other settings
    """
    # public fixed defaults
    diamond_smtp: str = 'outbox.rl.ac.uk'
    diamond_sender: str = 'backup_bl@diamond.ac.uk'
    root_folder = Path("/dls_sw/work/motion/Backups/")
    threads: int = 10

    # internal defaults
    _motion_folder = Path("MotionControllers/")
    _zebra_folder = Path("Zebras/")
    _ts_folder = Path("TerminalServers/")
    _config_file_suffix = Path("backup.json")
    _log_file = Path("backup_detail.log")
    _critical_log_file = Path("backup.log")
    _retries: int = 3

    def __init__(
            self, beamline: str, backup_folder: Path,
            config_file: Path, retires: int
    ):
        """
        Create an object to hold important file paths.
        Pass in command line parameters which override defaults:

        :param beamline: the name of the beamline in the form 'i16'
        :param backup_folder: override the default location for backups
        """
        self._retries = retires if int(retires) > 0 else Defaults._retries

        try:
            if beamline is None:
                beamline = environ.get("BEAMLINE")
                assert beamline is not None

            bl_no = int(beamline[1:])
            self._beamline = "BL{:02d}{}".format(bl_no,  beamline[0].upper())
        except (IndexError, AssertionError, ValueError, TypeError):
            raise ValueError(
                "Beamline must be of the form i16. Check environment "
                "variable ${BEAMLINE} or use argument --beamline")

        if backup_folder:
            self._backup_folder = Path(backup_folder)
        else:
            self._backup_folder = Defaults.root_folder / self._beamline

        if config_file:
            self._config_file = Path(config_file)
        else:
            name = Path("{}-{}".format(
                self._beamline, Defaults._config_file_suffix)
            )
            self._config_file = self._backup_folder / name

    def check_folders(self):
        self.motion_folder.mkdir(parents=True, exist_ok=True)
        self.zebra_folder.mkdir(parents=True, exist_ok=True)
        self.ts_folder.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            if str(self.config_file).startswith(str(self.root_folder)):
                # create an empty json config file
                with self.config_file.open("w") as f:
                    f.write(Defaults.json)

    @property
    def beamline(self) -> str:
        return self._beamline

    @property
    def backup_folder(self) -> Path:
        return self._backup_folder

    @property
    def config_file(self) -> Path:
        return self._config_file

    @property
    def motion_folder(self) -> Path:
        return self._backup_folder / Defaults._motion_folder

    @property
    def zebra_folder(self) -> Path:
        return self._backup_folder / Defaults._zebra_folder

    @property
    def ts_folder(self) -> Path:
        return self._backup_folder / Defaults._ts_folder

    @property
    def retries(self) -> int:
        return self._retries

    @property
    def log_file(self) -> Path:
        return self._backup_folder / Defaults._log_file

    @property
    def critical_log_file(self) -> Path:
        return self._backup_folder / Defaults._critical_log_file

    json = """{
    "MotorControllers": {
        "GeoBricks": [
        ],
        "PMACs": [
        ]
    },
    "TerminalServers": [

    ],
    "Zebras": [
    ],
    "Email": ""
}"""