from contextlib import contextmanager
import os
import uuid
import shutil
from image_processing import conversion, validation, exceptions
import filecmp
import tempfile
import re


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


def image_files_match(image_filepath1, image_filepath2):
    """
    Avoids problems with filecmp.cmp, which will return false if the exiftool version used to transfer metadata is
    different, as that's encoded in the embedded xmp, or if the kakadu version is different

    :param image_filepath1:
    :param image_filepath2:
    :return: True if the two image files are visually identical and have identical xmp metadata when extracted
    """
    try:
        validation.check_visually_identical(image_filepath1, image_filepath2)
    except exceptions.ValidationError as e:
        print(e)
        return False
    return image_metadata_matches(image_filepath1, image_filepath2)


def image_metadata_matches(image_filepath1, image_filepath2):
    """
    Extracts xmp files for each file and compares them

    :param image_filepath1:
    :param image_filepath2:
    :return: True if the xmp files match
    """
    with tempfile.NamedTemporaryFile(suffix='.xmp') as xmp_file1_obj:
        with tempfile.NamedTemporaryFile(suffix='.xmp') as xmp_file2_obj:
            conversion.Converter().extract_xmp_to_sidecar_file(image_filepath1, xmp_file1_obj.name)
            conversion.Converter().extract_xmp_to_sidecar_file(image_filepath2, xmp_file2_obj.name)
            return filecmp.cmp(xmp_file1_obj.name, xmp_file2_obj.name)


def xmp_files_match(xmp_filepath1, xmp_filepath2):
    """
    File comparison which ignores the exiftool version

    :param xmp_filepath1:
    :param xmp_filepath2:
    :return: True if the xmp files match, ignoring the exiftool version
    """
    return files_match(xmp_filepath1, xmp_filepath2, r"Image::ExifTool \d+\.\d+")


def files_match(filepath1, filepath2, regex_to_ignore):
    """

    :param filepath1:
    :param filepath2:
    :param regex_to_ignore: A regex pattern that will be replaced with the same value in both files before comparing
    :return: True if the files match, ignoring the regex_to_ignore
    """
    with open(filepath1) as file1_obj:
        file1_str = "'/n".join(file1_obj.readlines())
    with open(filepath2) as file2_obj:
        file2_str = "'/n".join(file2_obj.readlines())
    file1_str = re.sub(regex_to_ignore, 'IGNORED_VALUE', file1_str)
    file2_str = re.sub(regex_to_ignore, 'IGNORED_VALUE', file2_str)
    return file1_str == file2_str
