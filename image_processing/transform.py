from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import shutil

import logging
import tempfile
import io

from uuid import uuid4

from image_processing import format_converter, validation
import libxmp

TIFF_FILENAME = 'full.tiff'
XMP_FILENAME = 'xmp.xml'
JPG_FILENAME = 'full.jpg'
LOSSLESS_JP2_FILENAME = 'full_lossless.jp2'
LOSSY_JP2_FILENAME = 'full_lossy.jp2'

ICC_PROFILE = "/opt/kakadu/sRGB_v4_ICC_preference.icc"


def generate_derivatives_from_jpg(jpg_file, output_folder, strip_embedded_metadata=False, save_xmp=False):
    """
    Creates a copy of the jpg file and a validated jpeg2000 file and stores both in the given folder
    :param jpg_file:
    :param output_folder: the folder where the related dc.xml will be stored, with the dataset's uuid as foldername
    :param strip_embedded_metadata: True if you want to remove the embedded image metadata during the tiff conversion process. (no effect if image is already a tiff)
    :param save_xmp: If true, metadata will be extracted from the image file and preserved in a separate xmp file
    :return: filepaths of created images
    """

    scratch_output_folder = tempfile.mkdtemp(prefix='image_ingest_')
    try:

        jpeg_filepath = os.path.join(output_folder, JPG_FILENAME)
        shutil.copy(jpg_file, jpeg_filepath)
        generated_files = [jpeg_filepath]

        if save_xmp:
            xmp_file_path = os.path.join(output_folder, XMP_FILENAME)
            extract_xmp(jpeg_filepath, xmp_file_path)
            generated_files += [xmp_file_path]

        scratch_tiff_filepath = os.path.join(scratch_output_folder, str(uuid4()) + '.tif')
        tif_conversion_options = ['-strip'] if strip_embedded_metadata else []
        format_converter.convert_to_tiff(jpeg_filepath, scratch_tiff_filepath, tif_conversion_options)

        generated_files += generate_jp2_derivatives_from_tiff(scratch_tiff_filepath, output_folder)

        return generated_files
    finally:
        if scratch_output_folder:
            shutil.rmtree(scratch_output_folder, ignore_errors=True)


def generate_derivatives_from_tiff(tiff_file, output_folder, include_tiff=True, save_xmp=False, repage_image=False):
    """
    Creates a copy of the jpg fil and a validated jpeg2000 file and stores both in the given folder
    :param jpg_file:
    :param output_folder: the folder where the related dc.xml will be stored, with the dataset's uuid as foldername
    :param include_tiff: Include copy of source tiff file in derivatives
    :param repage_image: True if you want to remove the embedded image metadata during the tiff conversion process. (no effect if image is already a tiff)
    :param save_xmp: If true, metadata will be extracted from the image file and preserved in a separate xmp file
    :return: filepaths of created images
    """

    scratch_output_folder = tempfile.mkdtemp(prefix='image_ingest_')
    try:

        jpeg_filepath = os.path.join(output_folder, JPG_FILENAME)
        format_converter.convert_to_jpg(tiff_file, jpeg_filepath)
        logging.debug('jpeg file {0} generated'.format(jpeg_filepath))
        generated_files = [jpeg_filepath]

        if save_xmp:
            xmp_file_path = os.path.join(output_folder, XMP_FILENAME)
            extract_xmp(tiff_file, xmp_file_path)
            generated_files += [xmp_file_path]

        if include_tiff:
            tiff_filepath = os.path.join(output_folder, TIFF_FILENAME)
            shutil.copy(tiff_file, tiff_filepath)
            generated_files += [tiff_filepath]

        scratch_tiff_filepath = os.path.join(scratch_output_folder, str(uuid4()) + '.tiff')
        shutil.copy(tiff_file, scratch_tiff_filepath)

        if repage_image:
            # remove negative offsets by repaging the image. (It's the most common error during conversion)
            format_converter.repage_image(scratch_tiff_filepath, scratch_tiff_filepath)

        generated_files += generate_jp2_derivatives_from_tiff(scratch_tiff_filepath, output_folder)

        return generated_files

    finally:
        if scratch_output_folder:
            shutil.rmtree(scratch_output_folder, ignore_errors=True)


def generate_jp2_derivatives_from_tiff(scratch_tiff_file, output_folder):
    lossless_filepath = os.path.join(output_folder,LOSSLESS_JP2_FILENAME)
    format_converter.convert_to_jpeg2000(scratch_tiff_file, lossless_filepath, lossless=True)
    validation.validate_jp2(lossless_filepath)
    logging.debug('Lossless jp2 file {0} generated'.format(lossless_filepath))

    lossy_filepath = os.path.join(output_folder, LOSSY_JP2_FILENAME)
    #todo: should be mogrify
    format_converter.convert_tiff_colour_profile(scratch_tiff_file, scratch_tiff_file, ICC_PROFILE)
    format_converter.convert_colour_to_jpeg2000(scratch_tiff_file, lossy_filepath, lossless=False)
    validation.validate_jp2(lossy_filepath)
    logging.debug('Lossy jp2 file {0} generated'.format(lossy_filepath))

    return [lossless_filepath, lossy_filepath]


def extract_xmp(image_file, xmp_file_path):

    image_xmp_file = libxmp.XMPFiles(file_path=image_file)
    try:
        xmp = image_xmp_file.get_xmp()

        # using io.open for unicode compatibility
        with io.open(xmp_file_path, 'a') as output_xmp_file:
            output_xmp_file.write(xmp.serialize_to_unicode())
    finally:
        image_xmp_file.close_file()