"""CLI functionality"""

import sys
from typing import List, Sequence, Optional, Callable

import click
from prettytable import PrettyTable
import toml

from kicad_resource_system.model.core import Core
from kicad_resource_system.model.types import Color, Entry
from kicad_resource_system.model import errors

from kicad_resource_system.model.operations import (
    create_branch,
    checkin_branch,
    checkout_branch,
    save_branch,
    branch_status,
    move_branch,
)


def color(msg: str, *colors: Sequence[Color]) -> str:
    """Wrap text with special color characters"""
    res = ""
    for clr in colors:
        res += clr.value
    return f"{res}{msg}{Color.ENDC.value}"


error_msgs = {
    errors.MissingConfigParameterError: color(
        "config.toml file missing entry", Color.RED
    ),
    errors.MissingConfigFileError: color("config.toml file missing", Color.RED),
    errors.UnsavedError: color("Work not saved", Color.RED),
    errors.InvalidRepositoryError: color(
        "Working directory is not a repository", Color.RED
    ),
    errors.UnknownPlatformError: color("Unknown operating system", Color.RED),
    errors.UnspecifiedFoldersError: color(
        "Specify folder(s) for branch creation", Color.RED
    ),
    errors.InvalidFolderError: color(
        "Can only specify relative folders in branch", Color.RED
    ),
    errors.MissingFolderError: color("Folder missing", Color.RED),
    errors.ApplyPermissionsError: color(
        "Failed to apply permision to folder", Color.YELLOW
    ),
    errors.DuplicateRemoteBranchError: color(
        "Branch already exists remotely", Color.RED
    ),
    errors.DuplicateLocalBranchError: color("Branch already exists localy", Color.RED),
    errors.DuplicateStatusBranchError: color("Remove local status branch", Color.RED),
    errors.MissingBranchError: color("Branch does not exist", Color.RED),
    errors.UnassociatedBranchError: color("Branch has no entry", Color.RED),
    errors.UnownedBranchError: color("Branch has no owner", Color.RED),
    errors.ProtectedBranchError: color("Branch is protected", Color.RED),
    errors.AlreadyOwnedError: color("Branch already owned", Color.YELLOW),
}


# run operation method operation(core, branch, [opt]folders) -> [opt]entries
OperationMethod = Callable[[Core, str, Optional[List[str]]], Optional[List[Entry]]]


def run_operation_log_result(
    core: Core,
    func: OperationMethod,
    *args: Sequence[str],
) -> Optional[List[Entry]]:
    """Calls operation with args and handles error. Exits if error"""
    try:
        return func(core, *args)
    except errors.ProgramError as e:
        if type(e) in error_msgs:
            print(error_msgs[type(e)])
        else:
            print(f"Encountered an unexpected error: {e}")
        sys.exit(1)


pass_core = click.make_pass_decorator(Core)


@click.group()
@click.option("--config", "-c")
@click.pass_context
def main(ctx, config: str) -> None:
    """KiCAD Resource system commands"""
    try:
        with open("config.toml", "r", encoding="utf-8") as file:
            config = toml.load(file)
            status_branch = config["status_file"]["branch"]
            status_file = config["status_file"]["path"]
    except FileNotFoundError as e:
        raise errors.MissingConfigFileError() from e
    except KeyError as e:
        raise errors.MissingConfigParameterError() from e

    try:
        ctx.obj = Core(status_branch, status_file)
    except errors.ProgramError as err:
        if type(err) in error_msgs:
            print(error_msgs[type(err)])
        else:
            print(f"Encountered an unexpected error: {err}")
        sys.exit(1)


@main.command()
@click.argument("branch")
@click.argument(
    "folders",
    nargs=-1,
)
@pass_core
def new_branch(core: Core, branch: str, folders: List[str]) -> None:
    """Creates new branch for project"""
    run_operation_log_result(core, create_branch, branch, folders)
    print(color(f"Successfully created branch {branch}", Color.GREEN))


@main.command()
@click.argument("branch")
@pass_core
def checkin(core: Core, branch: str) -> None:
    """Checks in branch"""
    run_operation_log_result(core, checkin_branch, branch)
    print(color(f"Successfully checked in branch {branch}", Color.GREEN))


@main.command()
@click.argument("branch")
@pass_core
def checkout(core: Core, branch: str) -> None:
    """Checks out branch"""
    run_operation_log_result(core, checkout_branch, branch)
    print(color(f"Successfully checked out branch {branch}", Color.GREEN))


@main.command()
@click.argument("message")
@pass_core
def commit(core: Core, message: str) -> None:
    """Saves and commits your progress"""
    run_operation_log_result(core, save_branch, message)
    print(color(f"Successfully saved branch {core.get_working_branch()}", Color.GREEN))


@main.command()
@pass_core
def status(core: Core) -> None:
    """Returns own status of repo or project"""
    result = run_operation_log_result(core, branch_status)

    table = PrettyTable()
    table.field_names = [
        color("Branch", Color.BOLD),
        color("Folders", Color.BOLD),
        color("Owner", Color.BOLD),
    ]
    for branch, folders, owner in result:
        owner_color = Color.GREEN if owner == core.get_user_name() else Color.RED
        table.add_row(
            [
                color(branch, Color.BLUE),
                color(" ".join(folders), Color.CYAN),
                (color(owner, owner_color) if owner else color("None", Color.YELLOW)),
            ]
        )

    print(table)


@main.command()
@click.argument("branch")
@pass_core
def move(core: Core, branch: str) -> None:
    """Changes branch to specific project"""
    run_operation_log_result(core, move_branch, branch)
    print(color(f"Successfully moved to branch {branch}", Color.GREEN))


if __name__ == "__main__":
    main(None, None)
