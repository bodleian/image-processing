
from contextlib import contextmanager
import os
import uuid
import shutil


@contextmanager
def temporary_folder(name='test'):
    """
    Create unique temporary folder, yields the folderpath and deletes it after use. Will not delete if error occurs
    :param name: Added to filepath as extra identifier.
    """
    path = 'tests/output/{}{}'.format(name, uuid.uuid4())
    print('output folder: ' + path)
    os.makedirs(path)
    yield path
    shutil.rmtree(path)


def assert_lines_match(file1, file2, strip=True):
    with open(file1) as file1_ptr:
        with open(file2) as file2_ptr:
            lines1 = file1_ptr.readlines()
            lines2 = file2_ptr.readlines()
            assert(len(lines1) == len(lines2))
            for i in range(0, len(lines1)):
                if strip:
                    assert(lines1[i].strip() == lines2[i].strip())
                else:
                    assert(lines1[i] == lines2[i])
