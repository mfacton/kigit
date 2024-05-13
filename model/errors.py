"""Errors that arise from core and operations"""


class ProgramError(Exception):
    """Base error fore all errors"""


# ==============================
# > Core Errors
# ==============================


class UnsavedError(ProgramError):
    """Try to change branch but is unsaved"""


class InvalidRepositoryError(ProgramError):
    """Working directory is not repository base"""


class UnknownPlatformError(ProgramError):
    """Unknown operating system"""


# ==============================
# > Operation Errors
# ==============================


class InvalidFolderError(ProgramError):
    """User does not use relative folder path"""


class UnspecifiedFoldersError(ProgramError):
    """Did not specify folders in branch creation"""


class MissingFolderError(ProgramError):
    """Entry folder missing"""


class ApplyPermissionsError(ProgramError):
    """Entry folder missing to apply permisions"""


class AlreadyOwnedError(ProgramError):
    """Branch already has owner"""


class BranchError(ProgramError):
    """Base error for branch errors"""


class DuplicateRemoteBranchError(BranchError):
    """Remote branch already exists"""


class DuplicateLocalBranchError(BranchError):
    """Local branch already exists"""


class DuplicateStatusBranchError(BranchError):
    """Branch status only exists locally"""


class MissingBranchError(BranchError):
    """Branch does not exist"""


class UnassociatedBranchError(BranchError):
    """Branch is not associated in status.txt"""


class UnownedBranchError(BranchError):
    """Branch has no owner"""


class ProtectedBranchError(BranchError):
    """Branch has other owner"""
