"""Types used in operations and cli"""

from enum import Enum
from typing import Tuple, List


# In status.txt that contains (branch, folders, owner)
Entry = Tuple[str, List[str], str]


class Color(Enum):
    """Special color character"""

    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLACK = "\033[90m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


class Platform(Enum):
    """Enum for different operating systems"""

    LINUX = 0
    DARWIN = 1
    WINDOWS = 2


class Perm(Enum):
    """Enum for file permissions"""

    READ_WRITE = 0
    READ_ONLY = 1


class OwnershipType(Enum):
    """Enum for mapping allowed owner and email for operation"""

    CLAIMED = 0
    UNCLAIMED = 1


# (regular, read only)
file_flags = {
    Platform.LINUX: (0o666, 0o444),
    Platform.DARWIN: (0o666, 0o444),
    Platform.WINDOWS: (0o600, 0o400),
}
