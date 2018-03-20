
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