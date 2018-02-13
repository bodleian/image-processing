from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import shutil
import logging
import tempfile
import io

from image_processing import image_converter, validation
from image_processing.kakadu import Kakadu, DEFAULT_BDLSS_OPTIONS, LOSSLESS_OPTIONS

DEFAULT_TIFF_FILENAME = 'full.tiff'
DEFAULT_XMP_FILENAME = 'xmp.xml'
DEFAULT_JPG_FILENAME = 'full.jpg'
DEFAULT_LOSSLESS_JP2_FILENAME = 'full_lossless.jp2'

DEFAULT_JPG_THUMBNAIL_RESIZE_VALUE = 0.6
DEFAULT_JPG_HIGH_QUALITY_VALUE = 92


class DerivativeFilesGenerator(object):
    """
    Given a source image file, generates the derivative files (preservation/display image formats, extracted
    technical metadata etc.) we store in our repository
    """

    def __init__(self, kakadu_base_path,
                 jpg_high_quality_value=DEFAULT_JPG_HIGH_QUALITY_VALUE,
                 jpg_thumbnail_resize_value=DEFAULT_JPG_THUMBNAIL_RESIZE_VALUE,
                 tiff_filename=DEFAULT_TIFF_FILENAME,
                 xmp_filename=DEFAULT_XMP_FILENAME,
                 jpg_filename=DEFAULT_JPG_FILENAME,
                 lossless_jp2_filename=DEFAULT_LOSSLESS_JP2_FILENAME,
                 allow_no_icc_profile=False):
        self.tiff_filename = tiff_filename
        self.xmp_filename = xmp_filename
        self.jpg_filename = jpg_filename
        self.lossless_jp2_filename = lossless_jp2_filename

        self.jpg_high_quality_value = jpg_high_quality_value
        self.jpg_thumbnail_resize_value = jpg_thumbnail_resize_value
        self.allow_no_icc_profile = allow_no_icc_profile

        self.kakadu = Kakadu(kakadu_base_path=kakadu_base_path)

        self.log = logging.getLogger(__name__)

    def generate_derivatives_from_jpg(self, jpg_filepath, output_folder, save_xmp=True,
                                      check_lossless=False):
        """
        Creates a copy of the jpg file and a validated jpeg2000 file and stores both in the given folder
        :param jpg_filepath:
        :param output_folder: the folder where the related dc.xml will be stored
        :param save_xmp: If true, metadata will be extracted from the image file and preserved in a separate xmp file
        :param check_lossless: If true, check the created jpg2000 file is visually identical to the tiff
        created from the source file
        :return: filepaths of created images
        """
        self.log.debug("Processing {0}".format(jpg_filepath))
        self.log.info("There may be some loss in converting from jpg to jpg2000, as jpg compression is lossy. "
                      "The lossless check is against the tiff created from the jpg")

        must_check_lossless = validation.check_image_suitable_for_jp2_conversion(
            jpg_filepath, allow_no_icc_profile=self.allow_no_icc_profile)

        check_lossless = must_check_lossless or check_lossless

        output_jpg_filepath = os.path.join(output_folder, self.jpg_filename)
        shutil.copy(jpg_filepath, output_jpg_filepath)
        generated_files = [output_jpg_filepath]

        if save_xmp:
            xmp_file_path = os.path.join(output_folder, self.xmp_filename)
            self.extract_xmp(jpg_filepath, xmp_file_path)
            generated_files += [xmp_file_path]

        with tempfile.NamedTemporaryFile(prefix='image-processing_', suffix='.tif') as scratch_tiff_file_obj:
            scratch_tiff_filepath = scratch_tiff_file_obj.name
            image_converter.convert_to_tiff(jpg_filepath, scratch_tiff_filepath)

            validation.check_colour_profiles_match(jpg_filepath, scratch_tiff_filepath)

            generated_files.append(self.generate_jp2_from_tiff(scratch_tiff_filepath, output_folder))

            lossless_filepath = self.generate_jp2_from_tiff(scratch_tiff_filepath, output_folder)
            generated_files.append(lossless_filepath)

            if check_lossless:
                self.check_conversion_was_lossless(scratch_tiff_filepath, lossless_filepath)

        self.log.debug("Successfully generated derivatives for {0} in {1}".format(jpg_filepath, output_folder))

        return generated_files

    def generate_derivatives_from_tiff(self, tiff_filepath, output_folder, include_tiff=False, save_xmp=True,
                                       create_jpg_as_thumbnail=True, check_lossless=False):
        """
        Creates a copy of the jpg fil and a validated jpeg2000 file and stores both in the given folder
        :param create_jpg_as_thumbnail: create the jpg as a resized thumbnail, not a high quality image
        Parameters for resize and quality are set on a class level
        :param tiff_filepath:
        :param output_folder: the folder where the related dc.xml will be stored
        :param include_tiff: Include copy of source tiff file in derivatives
        (It's a common error during conversion)
        :param save_xmp: If true, metadata will be extracted from the image file and preserved in a separate xmp file
        :param check_lossless: If true, check the created jpg2000 file is visually identical to the source file
        :return: filepaths of created images
        """
        self.log.debug("Processing {0}".format(tiff_filepath))

        must_check_lossless = validation.check_image_suitable_for_jp2_conversion(
            tiff_filepath, allow_no_icc_profile=self.allow_no_icc_profile)
        check_lossless = must_check_lossless or check_lossless

        with tempfile.NamedTemporaryFile(prefix='image-processing_', suffix='.tif') as temp_tiff_file_obj:
            # only work from a temporary file if we need to - e.g. if the tiff filepath is invalid,
            # or if we need to normalise the tiff. Otherwise just use the original tiff
            temp_tiff_filepath = temp_tiff_file_obj.name
            if os.path.splitext(tiff_filepath)[1].lower() not in ['tif', 'tiff']:
                shutil.copy(tiff_filepath, temp_tiff_filepath)
                normalised_tiff_filepath = temp_tiff_filepath
            else:
                normalised_tiff_filepath = tiff_filepath

            jpeg_filepath = os.path.join(output_folder, self.jpg_filename)

            jpg_quality = None if create_jpg_as_thumbnail else self.jpg_high_quality_value
            jpg_resize = self.jpg_thumbnail_resize_value if create_jpg_as_thumbnail else None

            image_converter.convert_to_jpg(normalised_tiff_filepath, jpeg_filepath,
                                           quality=jpg_quality, resize=jpg_resize)
            self.log.debug('jpeg file {0} generated'.format(jpeg_filepath))
            generated_files = [jpeg_filepath]

            if save_xmp:
                xmp_file_path = os.path.join(output_folder, self.xmp_filename)
                self.extract_xmp(tiff_filepath, xmp_file_path)
                generated_files += [xmp_file_path]

            if include_tiff:
                output_tiff_filepath = os.path.join(output_folder, self.tiff_filename)
                shutil.copy(tiff_filepath, output_tiff_filepath)
                generated_files += [output_tiff_filepath]

            lossless_filepath = self.generate_jp2_from_tiff(normalised_tiff_filepath, output_folder)
            generated_files.append(lossless_filepath)

            if check_lossless:
                self.check_conversion_was_lossless(tiff_filepath, lossless_filepath)

            self.log.debug("Successfully generated derivatives for {0} in {1}".format(tiff_filepath, output_folder))

            return generated_files

    def generate_jp2_from_tiff(self, tiff_file, output_folder):
        lossless_filepath = os.path.join(output_folder, self.lossless_jp2_filename)
        self.kakadu.kdu_compress(tiff_file, lossless_filepath, kakadu_options=DEFAULT_BDLSS_OPTIONS + LOSSLESS_OPTIONS)
        validation.validate_jp2(lossless_filepath)
        self.log.debug('Lossless jp2 file {0} generated'.format(lossless_filepath))

        return lossless_filepath

    def extract_xmp(self, image_file, xmp_file_path):
        xmp = image_converter.get_xmp(image_file)
        # using io.open for unicode compatibility
        with io.open(xmp_file_path, 'w') as output_xmp_file:
            output_xmp_file.write(xmp.serialize_to_unicode())
        self.log.debug('XMP file {0} generated'.format(xmp_file_path))

    def check_conversion_was_lossless(self, source_file, lossless_jpg_2000_file):
        """
        Visually compare the source file to the tiff generated by expanding the lossless jp2,
        and throw an exception if they don't match.
        :param source_file: Must be tiff - can't seem to convert completely losslessly from jpg to tiff
        :param lossless_jpg_2000_file:
        :return:
        """
        self.log.debug('Checking conversion from source file {0} to jp2 file {1} was lossless'
                       .format(source_file, lossless_jpg_2000_file))
        with tempfile.NamedTemporaryFile(prefix='jp2_reconvert_', suffix='.tif') as reconverted_tiff_file_obj:
            reconverted_tiff_filepath = reconverted_tiff_file_obj.name
            self.kakadu.kdu_expand(lossless_jpg_2000_file, reconverted_tiff_filepath, kakadu_options=['-fussy'])
            validation.check_visually_identical(source_file, reconverted_tiff_filepath)
        self.log.info('Conversion from source file {0} to jp2 file {1} was lossless'
                      .format(source_file, lossless_jpg_2000_file))
