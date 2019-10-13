import argparse
import json
import logging
import smtplib
from logging import getLogger
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import List

from git import Repo, InvalidGitRepositoryError

from dls_backup_bl.config import BackupConfig
from dls_backup_bl.importjson import import_json
from .brick import backup_motor_controller
from .defaults import Defaults
from .tserver import backup_terminal_server
from .zebra import backup_zebra

log = getLogger(__name__)


class BackupBeamline:
    def __init__(self):
        self.args = None

        self.json_data: object = None
        self.thread_pool: ThreadPool = None
        self.defaults: Defaults = None
        self.config: BackupConfig = None

        self.motor_controllers: List = None
        self.terminal_servers: List = None
        self.zebras: List = None

    def setup_logging(self, level: str):
        """
        set up 3 logging handlers:
            A file logger to record debug information
            A file logger to record Critical messages
            A console logger
        The critical logger will be stored in the repo for a record of
        success/failure of each backup
        The debug logger will be in .gitignore so can be used to diagnose
        the most recent backup only
        The console logger level is configurable at the command line
        """

        # basic config sets up the debugging log file
        msg_f = '%(asctime)s %(levelname)-8s %(message)s        (%(name)s)'
        date_f = '%y-%m-%d %H:%M:%S'
        logging.basicConfig(
            level=logging.DEBUG, format=msg_f, datefmt=date_f,
            filename=str(self.defaults.log_file), filemode='w'
        )

        # critical log file for emails and record of activity
        critical = logging.FileHandler(
            filename=str(self.defaults.critical_log_file), mode='w'
        )
        critical.setLevel(logging.CRITICAL)

        # console log file for immediate feedback
        numeric_level = getattr(logging, level.upper(), None)

        # suppress verbose logging in dependent libraries
        if numeric_level > logging.DEBUG:
            logging.getLogger("dls_pmacanalyse").setLevel(logging.ERROR)
            logging.getLogger("dls_pmaclib").setLevel(logging.ERROR)

        # control logging for all modules in this package to the console
        console = logging.StreamHandler()
        # set a format which is simpler for console use
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)-10s %(message)s      (%(name)s)',
            datefmt='%y-%m-%d %H:%M:%S'
        )
        # tell the handler to use this format
        console.setFormatter(formatter)
        console.setLevel(numeric_level)

        # add the extra handlers to the root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(console)
        root_logger.addHandler(critical)

    def parse_args(self):
        # Setup an argument Parser
        parser = argparse.ArgumentParser(
            description='Backup PMAC & GeoBrick motor controllers, terminal '
                        'servers, and Zebra boxes. '
                        'RECOMMENDATION: run this program from a '
                        'workstation on the beamline to be backed up and '
                        'provide NO arguments except --email (see below for '
                        'defaults).',
            usage="%(prog)s [options]")
        parser.add_argument('-i', '--import-cfg', action="store",
                            help="import brick configuration from a "
                                 "dls-pmac-analyse configuration file.")
        parser.add_argument('-n', '--beamline', action="store",
                            help="Name of the beamline to backup. "
                                 "The format is 'i16' or 'b07'. Defaults to "
                                 "the current beamline")
        parser.add_argument('-b', '--dir', action="store",
                            help="Directory to save backups to. Defaults to"
                                 "/dls_sw/motion/Backups/$(BEAMLINE)")
        parser.add_argument('-j', action="store", dest="json_file",
                            help="JSON file of devices to be backed up. "
                                 "Defaults to DIR/$(BEAMLINE)-backup.json")
        parser.add_argument('-r', '--retries', action="store", type=int,
                            default=4,
                            help="Number of times to attempt backup. "
                                 "Defaults to 4")
        parser.add_argument('-t', '--threads', action="store", type=int,
                            default=Defaults.threads,
                            help="Number of processor threads to use (Number "
                                 "of simultaneous backups). Defaults to"
                                 "10")
        parser.add_argument('-e', '--email', action="store",
                            help="Email address to send backup reports to.")
        parser.add_argument('-l', '--log-level', action="store",
                            default='info',
                            help="Set logging to error, warning, info, debug")
        parser.add_argument('-o', '--one', action="store",
                            help="only backup the one named device")

        # Parse the command line arguments
        self.args = parser.parse_args()

    def do_geobricks(self, pmac: str = None):
        # Go through every motor controller listed in JSON file
        for motor_controller in self.config.motion_controllers:
            # Pull out the controller details
            controller = motor_controller["Controller"]
            server = motor_controller["Server"]
            port = motor_controller["Port"]

            # Check whether a terminal server is used or not
            uses_ts = int(port) != 1025

            # Add a backup job to the pool
            args = (
                controller, server, port, uses_ts, self.defaults
            )

            if not pmac or pmac == controller:
                self.thread_pool.apply_async(backup_motor_controller, args)

    def do_t_servers(self, t_server: str = None):
        # Go through every terminal server listed in JSON file
        for terminal_server in self.terminal_servers:
            # Pull out the server details
            server = terminal_server["Server"]
            ts_type = terminal_server["Type"]
            # Add a backup job to the pool
            args = (
                server, ts_type, self.defaults
            )
            if not t_server or t_server == server:
                self.thread_pool.apply_async(backup_terminal_server, args)

    def do_zebras(self, zebra: str = None):
        # Go through every zebra listed in JSON file
        for z in self.zebras:
            # Pull out the PV name detail
            name = z["Name"]
            # Add a backup job to the pool
            args = (name, self.defaults)

            if not zebra or zebra == name:
                self.thread_pool.apply_async(backup_zebra, args)

    # noinspection PyBroadException
    def commit_changes(self):
        # Link to beamline backup git repository in the motion area
        try:
            try:
                git_repo = Repo(self.defaults.backup_folder)
            except InvalidGitRepositoryError:
                log.error("There is no git repo - creating a repo")
                git_repo = Repo.init(self.defaults.backup_folder)

            # Gather up any changes
            untracked_files = git_repo.untracked_files
            modified_files = [
                diff.a_blob.path for diff in git_repo.index.diff(None)
            ]
            change_list = untracked_files + modified_files
            ignore = self.defaults.log_file.name

            # If there are changes, commit them
            if ignore in change_list:
                change_list.remove(ignore)
            if change_list:
                if untracked_files:
                    log.info("The following files are untracked:")
                    for File in untracked_files:
                        log.info('\t' + File)
                if modified_files:
                    log.info("The following files are modified or deleted:")
                    for File in modified_files:
                        log.info('\t' + File)

                git_repo.index.add(change_list)
                # Note repo.git.add is used to handle deleted files
                # todo not doing this since it overrides ignore (OK?)
                # git_repo.git.add(all=True)
                git_repo.index.commit("commit by dls-backup-bl")
                log.critical("Committed changes")
            else:
                log.critical("No changes since last backup")
        except BaseException:
            msg = "ERROR: _repo not updated"
            log.debug(msg, exc_info=True)
            log.error(msg)
        else:
            log.warning("SUCCESS: _repo changes committed")

    def sort_log(self):
        # Order the results alphabetically to make them easier to read
        with self.defaults.critical_log_file.open("r") as f:
            sorted_text = sorted(f.readlines())

        with self.defaults.critical_log_file.open("w") as f:
            f.writelines(sorted_text)

    def send_email(self, email: str):
        with self.defaults.critical_log_file.open("r") as f:
            e_text = f.read()

        if email is None:
            log.info("Email address not supplied")
            return

        # noinspection PyBroadException
        try:
            e_from = "From: {}\r\n".format(self.defaults.diamond_sender)
            e_to = "To: {}\r\n".format(email)
            e_subject = "Subject: {} Backup Report\r\n\r\n".format(
                self.defaults.beamline
            )
            msg = e_from + e_to + e_subject + e_text
            mail_server = smtplib.SMTP(self.defaults.diamond_smtp)
            mail_server.sendmail(
                self.defaults.diamond_sender, email, msg
            )
            mail_server.quit()
            log.critical("Sent Email report")
        except BaseException:
            msg = "Sending Email FAILED"
            log.critical(msg)
            log.debug(msg, exc_info=True)

    def main(self):
        self.parse_args()
        self.defaults = Defaults(
            self.args.beamline, self.args.dir, self.args.json_file,
            self.args.retries
        )
        self.defaults.check_folders()
        # logging is only set up now since defaults chooses logfile location
        self.setup_logging(self.args.log_level)

        self.config = BackupConfig(self.defaults.config_file)
        if self.args.import_cfg:
            import_file = Path(self.args.import_cfg)
            import_json(import_file, self.defaults.config_file)

        elif self.config.load_config(check_empty=True):
            log.info("START OF BACKUP for beamline %s to %s",
                     self.defaults.beamline, self.defaults.backup_folder)

            # Initiate a thread pool with the desired number of threads
            self.thread_pool = ThreadPool(self.args.threads)

            # queue threads for each type of backup
            self.do_geobricks(pmac=self.args.one)
            # self.do_t_servers()
            # self.do_zebras()

            # Wait for completion of all backup threads
            self.thread_pool.close()
            self.thread_pool.join()

            # finish up
            self.sort_log()
            self.commit_changes()
            self.send_email(self.args.email)

            log.warning("END OF BACKUP for beamline %s to %s",
                        self.defaults.beamline, self.defaults.backup_folder)

            print("\n\n\n--------- Summary ----------")
            with self.defaults.critical_log_file.open() as f:
                print(f.read())
