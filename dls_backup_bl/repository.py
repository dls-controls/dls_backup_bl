from logging import getLogger

from git import Repo, InvalidGitRepositoryError

from dls_backup_bl.defaults import Defaults

log = getLogger(__name__)


class Colours:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END_C = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# noinspection PyBroadException
def compare_changes(defaults: Defaults):
    try:
        git_repo = Repo(defaults.backup_folder)

        diff = git_repo.index.diff(
            None,
            create_patch=True,
            paths='*' + defaults.positions_suffix
        )

        output = ["\n --------- Motor Position Changes ----------"]
        for d in diff:
            output.append(f"\n{d.a_blob.path}")
            patch = d.diff.decode('utf8')
            lines = patch.split('\n')
            changes = []
            for line in lines:
                if line.startswith('-') or line.startswith('+'):
                    changes.append(line)
            # order by axis number
            changes.sort(
                key=lambda s: int(s[2:].split(' ')[0])
            )
            output += changes
        if len(diff) == 0:
            output.append("There are no changes to positions since the last "
                          "commit")
        else:
            # commit the most recent positions comparison for a record of
            # where motors had moved to before the restore
            comparison_file = str(
                defaults.motion_folder / defaults.positions_file)
            git_repo.index.add([comparison_file])
            git_repo.index.commit(
                "commit of positions comparisons by dls-backup-bl")

        filepath = defaults.motion_folder / defaults.positions_file
        with filepath.open("w") as f:
            f.writelines(map(lambda l: l+'\n', output))

        for line in output:
            if line.startswith('-'):
                line = Colours.FAIL + line + Colours.END_C
            elif line.startswith('+'):
                line = Colours.GREEN + line + Colours.END_C
            print(line)

    except BaseException:
        msg = 'ERROR: Repository positions comparison failed.'
        log.critical(msg)
        log.debug(msg, exc_info=True)


# noinspection PyBroadException
def commit_changes(defaults: Defaults):
    # Link to beamline backup git repository in the motion area
    try:
        try:
            git_repo = Repo(defaults.backup_folder)
        except InvalidGitRepositoryError:
            log.error("There is no git repo - creating a repo")
            git_repo = Repo.init(defaults.backup_folder)

        # Gather up any changes
        untracked_files = git_repo.untracked_files
        modified_files = [
            diff.a_blob.path for diff in git_repo.index.diff(None)
        ]
        change_list = untracked_files + modified_files

        # dont commit the debug log or motor positions from a recent comparison
        for ignore in [defaults.log_file.name, defaults.positions_suffix]:
            change_list = [i for i in change_list if ignore not in i]

        # If there are changes, commit them
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
            git_repo.index.commit(
                "commit of devices backup by dls-backup-bl")
            log.critical("Committed changes")
        else:
            log.critical("No changes since last backup")
    except BaseException:
        msg = "ERROR: repository not updated"
        log.debug(msg, exc_info=True)
        log.error(msg)
    else:
        log.warning("SUCCESS: _repo changes committed")


# noinspection PyBroadException
def restore_positions(defaults: Defaults):
    try:
        git_repo = Repo(defaults.backup_folder)
        cli = git_repo.git

        # restore the last committed motor positions
        cli.checkout(
            'master',
            str(defaults.motion_folder) + '/*' + defaults.positions_suffix
        )

    except BaseException:
        msg = 'ERROR: Repository positions restore failed.'
        log.critical(msg)
        log.debug(msg, exc_info=True)
