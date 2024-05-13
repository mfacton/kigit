"""Core functionality to interact with git and os"""

from typing import List

import platform
import git

from model.kitypes import Platform
from model.errors import (
    InvalidRepositoryError,
    UnknownPlatformError,
    UnsavedError,
)


class Core:
    """Git core abstraction"""

    def __init__(self, branch, file):
        self.status_branch = branch
        self.status_file = file
        try:
            self.repo = git.Repo("")
        except git.exc.InvalidGitRepositoryError as e:
            raise InvalidRepositoryError() from e

        try:
            self.platform = Platform[platform.system().upper()]
        except KeyError as e:
            raise UnknownPlatformError() from e

    def pull(self) -> None:
        """Runs git pull"""
        self.repo.remotes.origin.pull()

    def add(self, items: List[str]) -> None:
        """Adds all items to be committed"""
        self.repo.git.add(items)

    def commit(self, msg: str) -> None:
        """Commits with message"""
        self.repo.git.commit("-m", msg)

    def push(self) -> None:
        """Runs git push"""
        self.repo.remotes.origin.push()

    def add_commit_push(self, folders: List[str], msg: str) -> None:
        """Combined add, commit, push"""
        self.add(folders)
        self.commit(msg)
        self.push()

    def show_file_from_origin(self, branch: str, file: str) -> str:
        """Gets file contents from remote origin"""
        self.repo.git.fetch("origin", branch)
        try:
            return self.repo.git.show(f"origin/{branch}:{file}")
        except git.exc.GitCommandError:
            return ""

    def get_working_branch(self) -> str:
        """Returns current branch name"""
        return str(self.repo.active_branch)

    def get_remote_branches(self) -> List[str]:
        """Returns remote branch list"""
        self.repo.git.remote("update", "origin", "--prune")
        res = []
        remote_refs = self.repo.remote().refs
        for ref in remote_refs:
            if ref.name.startswith("origin/HEAD"):
                continue
            res.append(ref.name.split("/", maxsplit=1)[1])

        return res

    def get_local_branches(self) -> List[str]:
        """Returns local branch list"""
        return [str(br) for br in self.repo.branches]

    def to_branch(self, branch: str) -> None:
        """Changes to branch"""
        try:
            self.repo.git.checkout(branch)
        except git.exc.GitCommandError as e:
            raise UnsavedError() from e

    def get_user_name(self) -> str:
        """Gets email of current user"""
        return self.repo.config_reader().get_value("user", "name")

    def push_upstream_origin(self, branch: str) -> None:
        """Pushes and sets upstream origin"""
        self.repo.git.push("--set-upstream", "origin", branch)

    def create_remote_branch(self, branch: str) -> None:
        """Creates new branch and moves to it"""
        self.repo.create_head(branch).checkout()
        self.push_upstream_origin(branch)

    def create_orphan_branch(self, branch: str) -> None:
        """Creates new branch and cleans all filed"""
        self.repo.git.checkout("--orphan", branch)
        self.repo.git.reset(".")
        self.repo.git.clean("-fxfd")

    def stash_untracked(self) -> bool:
        """Stashes tracked and untracked files but not ignored files returns if stashed"""
        return self.repo.git.stash("-u") != "No local changes to save"

    def stash_pop(self) -> None:
        """Applies changes back into branch"""
        self.repo.git.stash("pop")
