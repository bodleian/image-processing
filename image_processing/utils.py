import os


def cmd_is_executable(cmd):
    """
    :param cmd: filepath
    :return: True if the cmd exists (including if it's on the user's PATH) and can be executed
    """
    if os.path.isabs(cmd):
        paths = [""]
    else:
        paths = [""] + os.environ["PATH"].split(os.pathsep)
    cmd_paths = [os.path.join(path, cmd) for path in paths]
    return any(
        os.path.isfile(cmd_path) and os.access(cmd_path, os.X_OK) for cmd_path in cmd_paths
    )