import os


def cmd_is_executable(cmd):
    """
    :param cmd: filepath to an executable.
    :return: True if the command exists (including if it is on the PATH) and can be executed
    """
    if os.path.isabs(cmd):
        paths = [""]
    else:
        paths = [""] + os.environ["PATH"].split(os.pathsep)
    cmd_paths = [os.path.join(path, cmd) for path in paths]
    return any(
        os.path.isfile(cmd_path) and os.access(cmd_path, os.X_OK) for cmd_path in cmd_paths
    )