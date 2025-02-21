from nextgeninfrastructure import exceptions

class Color:
    PURPLE = '\033[1;35;48m'
    CYAN = '\033[1;36;48m'
    BOLD = '\033[1;37;48m'
    BLUE = '\033[1;34;48m'
    GREEN = '\033[1;32;48m'
    YELLOW = '\033[1;33;48m'
    RED = '\033[1;31;48m'
    BLACK = '\033[1;30;48m'
    UNDERLINE = '\033[4;37;48m'
    END = '\033[1;37;0m'


def info(message: str) -> None:
    print(f"{Color.GREEN}[INFO] {message}{Color.END}")


def warning(message: str) -> None:
    print(f"{Color.YELLOW}[WARNING] {message}{Color.END}")


def fatal(message: str) -> None:
    print(f"{Color.RED}[FATAL] {message}{Color.END}")
    raise exceptions.ExamplesException(message)
