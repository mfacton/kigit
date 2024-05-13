"""This module contains functions for the various operations (branch, check-out, commit, etc.)"""

import os
from typing import List, Tuple, Generator

from kicad_resource_system.model.core import Core
from kicad_resource_system.model.types import (
    Perm,
    OwnershipType,
    Entry,
    Platform,
    file_flags,
)
from kicad_resource_system.model import errors

# ==============================
# > Helper Functions
# ==============================


class SaveBranch:
    """Stores current progress in stash and unstashes it"""

    def __init__(self, core: Core) -> None:
        self.core = core
        self.branch = None
        self.stash = None

    def __enter__(self) -> None:
        # Save before moving branches
        self.branch = self.core.get_working_branch()
        self.stash = self.core.stash_untracked()

    def __exit__(self, _type, _value, _traceback) -> None:
        self.core.to_branch(self.branch)
        if self.stash:
            self.core.stash_pop()


def create_status_branch(core: Core) -> None:
    """Creates status branch if missing"""
    if "status" in core.get_local_branches():
        raise errors.DuplicateStatusBranchError()

    with SaveBranch(core):
        core.create_orphan_branch(core.status_branch)

        # Create empty status file in status branch
        with open(core.status_file, "w", encoding="utf-8") as file:
            file.write("")

        core.add([core.status_file])
        core.commit("Add status file")
        core.push_upstream_origin(core.status_branch)


def get_entries(core: Core, remote_branches: List[str]) -> List[Entry]:
    """Returns proper entries and remote branches"""
    if not core.status_branch in remote_branches:
        create_status_branch(core)

    status_str = core.show_file_from_origin(core.status_branch, core.status_file).strip(
        "\n"
    )
    if not status_str:
        return []

    entries = []
    for entry_str in status_str.split("\n"):
        branch, folderstr, owner = entry_str.split(";")

        if branch in remote_branches:
            entries.append((branch, folderstr.split(","), owner))

    return entries


def set_folder_perms(platform: Platform, folder: str, perm: Perm) -> None:
    """Apply file mode to every file in directory"""
    for root, _, files in os.walk(folder):
        for file_name in files:
            os.chmod(
                os.path.join(root, file_name),
                file_flags[platform][perm.value],
            )


def update_perms_using_entries(
    platform: Platform,
    user_email: str,
    entries: List[Entry],
    branch: str,
) -> None:
    """Updates permissions on working branch"""
    try:
        free_folders, owner = next(
            (folders, owr) for br, folders, owr in entries if br == branch
        )
    except StopIteration:  # not in entry branch, totally fine
        return

    checked = owner == user_email
    free_count = 0  # counts free folders found
    for folder in os.scandir("."):
        if not folder.name.startswith(".") and folder.is_dir():
            if checked and folder.name in free_folders:
                set_folder_perms(platform, folder.name, Perm.READ_WRITE)
                free_count += 1
            else:
                set_folder_perms(platform, folder.name, Perm.READ_ONLY)

    # true when a folder was missing and you are owner
    if checked and free_count != len(free_folders):
        raise errors.ApplyPermissionsError()


def get_filtered_entries(core: Core, branch: str) -> Tuple[List[Entry], Entry]:
    """Returns list of entries and entry related to branch"""
    remote_branches = core.get_remote_branches()
    entries = get_entries(core, remote_branches)

    if not branch in remote_branches:
        raise errors.MissingBranchError()

    try:
        branch_entry = next(entry for entry in entries if entry[0] == branch)
        entries.remove(branch_entry)

        return (entries, branch_entry)
    except StopIteration as e:
        raise errors.UnassociatedBranchError() from e


def check_ownership(user_email: str, owner: str, ownership_type: OwnershipType) -> None:
    """Makes sure ownership is in the proper state to continue"""
    if ownership_type == OwnershipType.UNCLAIMED:
        if owner == user_email:
            raise errors.AlreadyOwnedError()
        if owner != "":
            raise errors.ProtectedBranchError()
    else:
        if owner == "":
            raise errors.UnownedBranchError()
        if owner != user_email:
            raise errors.ProtectedBranchError()


def save_entries(
    core: Core, entries: List[Entry], msg: str
) -> Generator[Core, List[Entry], str]:
    """Save current state then go to status branch and write"""
    core.to_branch(core.status_branch)
    core.pull()

    with open(core.status_file, "w", encoding="utf-8") as file:
        for branch, folders, owner in entries:
            file.write(f"{branch};{','.join(folders)};{owner}\n")

    core.add_commit_push([core.status_file], msg)


# ==============================
# > Operations
# ==============================


def create_branch(core: Core, branch: str, folders: List[str]) -> None:
    """Creates branch with folder targets"""
    if len(folders) == 0:
        raise errors.UnspecifiedFoldersError()

    for folder in folders:
        if (
            folder == "."
            or "/" in folder
            or "\\" in folder
            or "," in folder
            or ";" in folder
        ):
            raise errors.InvalidFolderError()

    remote_branches = core.get_remote_branches()
    entries = get_entries(core, remote_branches)
    local_branches = core.get_local_branches()

    if branch in remote_branches:
        raise errors.DuplicateRemoteBranchError()

    if branch in local_branches:
        raise errors.DuplicateLocalBranchError()

    entries.append((branch, folders, ""))

    with SaveBranch(core):
        save_entries(core, entries, f"Add branch {branch}")
        core.to_branch("main")
        core.pull()

        core.create_remote_branch(branch)

    update_perms_using_entries(
        core.platform, core.get_user_name(), entries, core.get_working_branch()
    )


def checkin_branch(core: Core, branch: str) -> None:
    """Check-in branch"""
    entries, (_, folders, owner) = get_filtered_entries(core, branch)

    user_email = core.get_user_name()

    check_ownership(user_email, owner, OwnershipType.CLAIMED)

    entries.append((branch, folders, ""))

    with SaveBranch(core):
        save_entries(core, entries, f"Checkin {branch} by {user_email}")

    update_perms_using_entries(
        core.platform, user_email, entries, core.get_working_branch()
    )


def checkout_branch(core: Core, branch: str) -> None:
    """Checkout branch"""
    entries, (_, folders, owner) = get_filtered_entries(core, branch)

    user_email = core.get_user_name()

    check_ownership(user_email, owner, OwnershipType.UNCLAIMED)

    entries.append((branch, folders, user_email))

    with SaveBranch(core):
        save_entries(core, entries, f"Checkout {branch} by {user_email}")

    update_perms_using_entries(
        core.platform, user_email, entries, core.get_working_branch()
    )


def save_branch(core: Core, msg: str) -> None:
    """Commit to current branch"""
    _, (_, folders, owner) = get_filtered_entries(core, core.get_working_branch())

    user_email = core.get_user_name()

    check_ownership(user_email, owner, OwnershipType.CLAIMED)

    for folder in folders:
        if not os.path.exists(folder):
            raise errors.MissingFolderError()

    core.add_commit_push(folders, msg)


def branch_status(core: Core) -> List[Entry]:
    """Get status of all branches"""
    return get_entries(core, core.get_remote_branches())


def move_branch(core: Core, branch: str) -> None:
    """Switch to branch"""
    remote_branches = core.get_remote_branches()
    entries = get_entries(core, remote_branches)

    core.to_branch(branch)

    update_perms_using_entries(core.platform, core.get_user_name(), entries, branch)
