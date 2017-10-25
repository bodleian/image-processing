import os
import shutil

import logging
import tempfile

from uuid import uuid4

import format_converter, validation
from exempi import Exempi

def transform_jpg_to_ingest_format(jpg_file, output_uuid_folder, strip_embedded_metadata=False, exempi_app=None):
    """
    Creates a copy of the jpg fil and a validated jpeg2000 file and stores both in the given folder
    :param jpg_file:
    :param output_uuid_folder: the folder where the related dc.xml will be stored, with the dataset's uuid as foldername
    :param strip_metadata: True if you want to remove the embedded image metadata during the tiff conversion process. (no effect if image is already a tiff)
    :param exempi_app: the filepath to the exempi exe. If none, metadata will not be extracted and preserved from the image file
    :return: filepaths of created images
    """

    return transform_image_to_ingest_format(jpg_file, output_uuid_folder, 'jpg', strip_embedded_metadata, exempi_app)

def transform_image_to_ingest_format(image_file, output_uuid_folder, source_filetype, strip_embedded_metadata=False, exempi_app=None):
    """
    Creates a copy of the image_file and a validated lossy and lossless jpeg2000 file and stores both in the given folder
    :param image_file:
    :param output_uuid_folder: the folder where the related dc.xml will be stored, with the dataset's uuid as foldername
    :param source_filetype: 
    :param strip_metadata: True if you want to remove the embedded image metadata during the tiff conversion process. (no effect if image is already a tiff)
    :param exempi_app: the filepath to the exempi exe. If none, metadata will not be extracted and preserved from the image file
    :return: filepaths of created images
    """

    scratch_output_folder = tempfile.mkdtemp(prefix='image_ingest_')
    try:
        _, image_ext = os.path.splitext(image_file)
        working_source_file = os.path.join(scratch_output_folder, str(uuid4()) + image_ext)
        shutil.copy(image_file, working_source_file)

        files = generate_images(working_source_file, output_uuid_folder, source_filetype,scratch_output_folder,
                                strip_embedded_metadata=strip_embedded_metadata)

        if exempi_app:
            files.append(extract_xmp(working_source_file, output_uuid_folder, exempi_app))

        return files
    finally:
        if scratch_output_folder:
            shutil.rmtree(scratch_output_folder, ignore_errors=True)

def extract_xmp(image_file, output_folder, exempi_app):
    if exempi_app is None:
        raise Exception('Exempi exe file path is needed to extract xmp metadata')
    xmp_file = os.path.join(output_folder, 'xmp.xml')
    xmp_extractor = Exempi(exempi_app)
    success = xmp_extractor.generate(image_file, xmp_file)
    if not success:
        raise Exception("Exempi error while extracting xmp data")
    return xmp_file

def generate_images(source_file, output_folder, source_filetype, scratch_output_folder, strip_embedded_metadata=False):

    jpeg_filepath = os.path.join(output_folder, 'full.jpg')

    generated_files = [jpeg_filepath]

    if source_filetype == 'jpg':
        shutil.copy(source_file, jpeg_filepath)
        tiff_filepath = os.path.join(scratch_output_folder, 'full.tiff')
        format_converter.convert_to_tiff(source_file,tiff_filepath,strip_embedded_metadata)
    elif source_filetype == 'tif':
        format_converter.convert_to_format_with_library_choice(source_filetype, jpeg_filepath, 'jpeg')
        tiff_filepath = source_file
        #todo: should tiff file be copied over too?
    else:
        raise Exception('unrecognised source filetype {0}'.format(source_filetype))

    logging.debug('jpeg file {0} generated'.format(jpeg_filepath))
    generated_files += generate_jp2_images(tiff_filepath, output_folder, scratch_output_folder)
    return generated_files



def generate_jp2_images(tiff_file, output_folder, scratch_output_folder, repage_image=False):
    """
    Alters the given tiff file
    :param tiff_file:
    :param output_folder:
    :param scratch_output_folder:
    :param repage_image:
    :return:
    """
    lossless_filepath = os.path.join(output_folder, 'full_lossless.jp2')
    tiff_is_monochrome = format_converter.is_monochrome(tiff_file)
    if repage_image:
        # remove negative offsets by repaging the image. (It's the most common error during conversion)
        format_converter.repage_image(tiff_file, tiff_file)

    if tiff_is_monochrome:
        format_converter.convert_monochrome_to_lossless_jpeg2000(tiff_file, lossless_filepath)
    else:
        format_converter.convert_to_jpeg2000(tiff_file, lossless_filepath)

    valid = validation.verify_jp2(lossless_filepath)
    if not valid:
        raise Exception('Lossless JP2 file is invalid')
    logging.debug('Lossless jp2 file {0} generated'.format(lossless_filepath))

    lossy_filepath = os.path.join(output_folder, 'full_lossy.jp2')
    converted_tiff_file = os.path.join(scratch_output_folder, str(uuid4()) + '.tiff')
    try:
        format_converter.convert_tiff_colour_profile(tiff_file, converted_tiff_file, input_is_monochrome=tiff_is_monochrome)
        format_converter.convert_to_jpeg2000(converted_tiff_file, lossy_filepath, lossless=False)
        valid = validation.verify_jp2(lossy_filepath)
        if not valid:
            raise Exception('Lossy JP2 file is invalid')
        logging.debug('Lossy jp2 file {0} generated'.format(lossy_filepath))

        generated_files = [lossless_filepath, lossy_filepath]
        return generated_files
    finally:
        try:
            if os.path.isfile(converted_tiff_file):
                os.remove(converted_tiff_file)
        except (IOError, OSError) as e:
            logging.error(str(e))
