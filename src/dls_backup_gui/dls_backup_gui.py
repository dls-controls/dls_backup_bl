import argparse
import logging
import signal
import sys
from logging import getLogger

from PyQt5.QtWidgets import QApplication, QMessageBox

from dls_backup_bl import __version__
from dls_backup_bl.defaults import Defaults

from .backup_editor import BackupEditor

log = getLogger(__name__)


def parse_args():
    # Setup an argument Parser
    parser = argparse.ArgumentParser(
        description="Edit a dls-backup-bl beamline configuration file",
        usage="%(prog)s [options]",
    )
    parser.add_argument(
        "-b",
        "--beamline",
        action="store",
        help="Name of the beamline to backup. "
        "The format is 'i16' or 'b07'. Defaults to "
        "the current beamline",
    )
    parser.add_argument(
        "--domain",
        action="store",
        help="When BLXXY is not appropriate, use domain for"
        " the backup folder name. e.g. --domain ME01D",
    )
    parser.add_argument(
        "-j",
        action="store",
        dest="json_file",
        help="JSON file of devices to be backed up. "
        "Defaults to DIR/$(BEAMLINE)-backup.json",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        action="store",
        default="info",
        help="Set logging to error, warning, info, debug",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="report version and exit",
    )

    # Parse the command line arguments
    return parser.parse_args()


# Start the application
def main():
    args = parse_args()
    if args.version:
        print(__version__)
        exit(0)

    # console log file for immediate feedback
    numeric_level = getattr(logging, args.log_level.upper(), None)
    logging.basicConfig(level=numeric_level)

    defaults = Defaults(
        beamline=args.beamline,
        config_file=args.json_file,
        config_file_only=True,
        domain=args.domain,
    )

    app = QApplication(sys.argv)
    if not defaults.config_file.exists():
        go = QMessageBox.question(
            None,
            "New Backup Area",
            f"There is no backup area for {defaults.beamline}\n"
            f"do you want to create one ?",
            QMessageBox.Yes,
            QMessageBox.No,
        )
    else:
        go = True

    if go:
        defaults.check_folders()
        app.lastWindowClosed.connect(app.quit)
        win = BackupEditor(defaults.config_file)
        win.show()
        # catch CTRL-C
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        app.exec_()


if __name__ == "__main__":
    main()
