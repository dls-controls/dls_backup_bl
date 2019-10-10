import sys
import argparse
import json
from multiprocessing.pool import ThreadPool
from typing import List

from cothread.catools import *
from pathlib import Path

from dls_backup_bl.util import EmailMessage
from .brick import backup_motor_controller
from .zebra import backup_zebra
from .tserver import backup_terminal_server


class BackupBeamline:
    def __init__(self):
        self.args = None

        self.json_data: object = object()
        self.thread_pool: ThreadPool = ThreadPool()
        self.email: str = str()
        self.backup_dir: Path = Path()
        self.retries: int = int()
        self.beamline: str = str()

        self.motor_controllers: List = []
        self.terminal_servers: List = []
        self.zebras: List = []

    def parse_args(self):
        # Setup an argument Parser
        Parser = argparse.ArgumentParser(
            description='Backup PMAC & GeoBrick motor controllers, terminal '
                        'servers, '
                        'and Zebra boxes',
            usage="%(prog)s -j <JSON File> [options]")
        Parser.add_argument('-j', action="store", dest="json_file",
                            help="JSON file of devices to be backed up")
        Parser.add_argument('-b', '--dir', action="store",
                            help="Directory to save backups to")
        Parser.add_argument('-r', '--retries', action="store", type=int,
                            default=3,
                            help="Number of times to attempt backup (Default "
                                 "of 3)")
        Parser.add_argument('-t', '--threads', action="store", type=int,
                            default=10,
                            help="Number of processor threads to use (Number "
                                 "of simultaneous backups) (Default of 10)")
        Parser.add_argument('-n', '--beamline', action="store",
                            help="Name of beamline backup is for")
        Parser.add_argument('-e', '--email', action="store",
                            help="Email address to send backup reports to")

        # Parse the command line arguments
        self.args = Parser.parse_args()

    def main(self):
        self.parse_args()
        self.backup_dir = self.args.dir
        self.retries = self.args.retries

        assert self.backup_dir is not None, "backup directory required"
        assert self.beamline is not None, "beamline name required"

        # get info on what to backup
        self.load_config(self.args.json_file)
        # Initiate a thread pool with the desired number of threads
        self.thread_pool = ThreadPool(self.args.threads)
        self.email = EmailMessage()

        # launch threads for each type of backup
        self.do_geobricks()
        # self.do_t_servers()
        # self.do_zebras()

        # Wait for completion of all backup threads
        self.thread_pool.close()
        self.thread_pool.join()
        print("\nBackup run complete!\n")

        self.wrap_up()

    def load_config(self, filename):
        if not filename:
            raise ValueError("a json configuration file is required")
        # Add the .json file extension if not specified
        if not filename.lower().endswith('.json'):
            filename += '.json'

        # Open JSON file of device details
        # noinspection PyBroadException
        try:
            with open(filename) as json_file:
                # Read out the JSON data, then close the file
                self.json_data = json.load(json_file)

            self.motor_controllers = self.json_data["MotorControllers"]
            self.terminal_servers = self.json_data["TerminalServers"]
            self.zebras = self.json_data["Zebras"]

        # Capture problems opening or reading the file
        except BaseException:
            print("\nInvalid json file name or path or invalid JSON\n")
            raise

    def do_geobricks(self):
        # Go through every motor controller listed in JSON file
        motor_controller_property_list = []
        for controller_type in self.motor_controllers:
            for motor_controller in self.motor_controllers[controller_type]:
                properties = []
                # Pull out the controller details
                controller = motor_controller["Controller"]
                server = motor_controller["Server"]
                port = motor_controller["Port"]

                # Check whether the controller is a GeoBrick or PMAC
                is_geobrick = controller_type == "GeoBricks"
                # Check whether a terminal server is used or not
                uses_ts = port != "1025"

                # Keep a record of properties for the results table
                properties.append(str(controller))
                properties.append(str(controller_type))
                properties.append(str(server))
                properties.append(str(port))

                # Add a backup job to the pool
                args = (controller, server,
                        port, is_geobrick, uses_ts,
                        self.backup_dir, self.retries,
                        self.email, properties)
                self.thread_pool.apply_async(backup_motor_controller, args)
                # Add properties to master list
                motor_controller_property_list.append(properties)

    def do_t_servers(self):
        # Go through every terminal server listed in JSON file
        terminal_server_property_list = []
        for terminal_server in self.terminal_servers:
            property_list = []
            # Pull out the server details
            server = terminal_server["Server"]
            ts_type = terminal_server["Type"]
            # Keep a record of properties for the results table
            property_list.append(str(server))
            property_list.append(str(ts_type))
            # Add a backup job to the pool
            args = (
                server, ts_type, self.backup_dir, self.retries, self.email,
                property_list
            )
            self.thread_pool.apply_async(backup_terminal_server, args)
            # Add properties to master list
            terminal_server_property_list.append(property_list)

    def do_zebras(self):
        # Go through every zebra listed in JSON file
        zebra_property_list = []
        for zebra in self.zebras:
            PropertyList = []
            # Pull out the PV name detail
            name = zebra["Name"]
            # Keep a record of properties for the results table
            PropertyList.append(str(name))
            # Add a backup job to the pool
            args = (name, self.backup_dir, PropertyList)
            self.thread_pool.apply_async(backup_zebra, args)
            # Add properties to master list
            zebra_property_list.append(PropertyList)

    def report(self):
        pass

    def wrap_up(self):
        # Order the results alphabetically to make them easier to read
        # self.motor_controllers.sort()
        # self.terminal_servers.sort()
        # self.zebras.sort()
        #
        # if self.email:
        #     print(self.email.print_message())
        #     self.email.send()
        #
        # # Link to beamline backup git repository in the motion area
        # GitRepo = git.Repo("/dls_sw/work/motion/Backups/" + self.beamline)
        #
        # # Gather up any changes
        # UntrackedFiles = GitRepo.untracked_files
        # ModifiedFiles = [diff.a_blob.name for diff in GitRepo.index.diff(None)]
        # ChangeList = UntrackedFiles + ModifiedFiles
        #
        # # If there are changes, commit them
        # if ChangeList:
        #     if UntrackedFiles:
        #         print("The following files are untracked:")
        #         for File in UntrackedFiles:
        #             print(File)
        #     if ModifiedFiles:
        #         print("The following files are modified or deleted:")
        #         for File in ModifiedFiles:
        #             print(File)
        #     print("Adding them to the staging area")
        #     # repo.index.add(ChangeList)
        #     # Note repo.git.add is used to handle deleted files
        #     GitRepo.git.add(all=True)
        #     GitRepo.index.commit("Modified files commited")
        #     print("Committed changes")
        # else:
        #     print("Repository up to date. No actions taken")

        print("Done")


if __name__ == '__main__':
    bb = BackupBeamline()
    bb.main()
