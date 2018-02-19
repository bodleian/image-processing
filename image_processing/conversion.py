from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import logging
from PIL import Image
from libxmp import XMPFiles

"""
Convert tiff to/from jpg while preserving technical metadata and icc profiles
"""


def convert_to_tiff(input_filepath, output_filepath):
    """
    Convert an image file to tif, preserving ICC profile and xmp data
    :param input_filepath:
    :param output_filepath:
    :return:
    """
    with Image.open(input_filepath) as input_pil:
        # this seems to use no compression by default. Specifying compression='None' means no icc is saved
        input_pil.save(output_filepath, "TIFF")
    copy_over_xmp(input_filepath, output_filepath)


def convert_to_jpg(input_filepath, output_filepath, resize=None, quality=None):
    """
    Convert an image file to jpg, preserving ICC profile and xmp data
    :param input_filepath:
    :param output_filepath:
    :param resize: if present, resize by this amount to make a thumbnail. e.g. 0.5 to make a thumbnail half the size
    :param quality: quality of created jpg: either None, or 1-95
    :return:
    """
    with Image.open(input_filepath) as input_pil:
        icc_profile = input_pil.info.get('icc_profile')
        if input_pil.mode == 'RGBA':
            logging.getLogger(__name__).warning(
                'Image is RGBA - the alpha channel will be removed from the JPEG derivative image')
            input_pil = input_pil.convert(mode="RGB")
        if resize:
            thumbnail_size = tuple(int(i * resize) for i in input_pil.size)
            input_pil.thumbnail(thumbnail_size, Image.LANCZOS)
        if quality:
            input_pil.save(output_filepath, "JPEG", quality=quality, icc_profile=icc_profile)
        else:
            input_pil.save(output_filepath, "JPEG", icc_profile=icc_profile)
    copy_over_xmp(input_filepath, output_filepath)


def copy_over_xmp(input_image_filepath, output_image_filepath):
    original_xmp = get_xmp(input_image_filepath)
    set_xmp(output_image_filepath, original_xmp)


def get_xmp(image_filepath):
    image_xmp_file = XMPFiles(file_path=image_filepath)
    xmp = image_xmp_file.get_xmp()
    image_xmp_file.close_file()
    return xmp


def set_xmp(image_filepath, xmp):
    xmp_file = XMPFiles(file_path=image_filepath, open_forupdate=True)
    xmp_file.put_xmp(xmp)
    xmp_file.close_file()
