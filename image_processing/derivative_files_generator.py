from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import shutil
import logging
import tempfile

from image_processing import conversion, validation, kakadu
from image_processing.kakadu import Kakadu
from PIL import Image

DEFAULT_TIFF_FILENAME = 'full.tiff'
DEFAULT_EMBEDDED_METADATA_FILENAME = 'full.xmp'
DEFAULT_JPG_FILENAME = 'full.jpg'
DEFAULT_LOSSLESS_JP2_FILENAME = 'full_lossless.jp2'

DEFAULT_JPG_THUMBNAIL_RESIZE_VALUE = 0.6
DEFAULT_JPG_HIGH_QUALITY_VALUE = 92

DEFAULT_EXIFTOOL_PATH = "exiftool"
DEFAULT_KAKADU_BASE_PATH = ""


class DerivativeFilesGenerator(object):
    """
    Given a source image file, generates the derivative files (preservation/display image formats, 
    extracted technical metadata etc.) we store in our repository
    """

    def __init__(self, kakadu_base_path=DEFAULT_KAKADU_BASE_PATH,
                 jpg_high_quality_value=DEFAULT_JPG_HIGH_QUALITY_VALUE,
                 jpg_thumbnail_resize_value=DEFAULT_JPG_THUMBNAIL_RESIZE_VALUE,
                 kakadu_compress_options=kakadu.DEFAULT_LOSSLESS_COMPRESS_OPTIONS,
                 use_default_filenames=True,
                 require_icc_profile_for_greyscale=False,
                 require_icc_profile_for_colour=True,
                 exiftool_path=DEFAULT_EXIFTOOL_PATH):
        """

        :param kakadu_base_path: the location of the kdu_compress and kdu_expand executables
        :param jpg_high_quality_value: between 0 and 95
        :param jpg_thumbnail_resize_value: between 0 and 1
        :param kakadu_compress_options: options for kdu_compress to create a lossless jp2 file
        :param use_default_filenames: use the filenames specified in this module instead of using the original filename
        :param require_icc_profile_for_greyscale: raise an error if a greyscale image doesn't have an ICC profile.
            Note: bitonal images do not need ICC profiles even if this is true
        :param require_icc_profile_for_colour: raise an error if a colour image does not have an ICC profile
        :param exiftool_path: path to the exiftool executable
        """

        self.jpg_high_quality_value = jpg_high_quality_value
        self.jpg_thumbnail_resize_value = jpg_thumbnail_resize_value
        self.require_icc_profile_for_greyscale = require_icc_profile_for_greyscale
        self.require_icc_profile_for_colour = require_icc_profile_for_colour
        self.use_default_filenames = use_default_filenames
        self.kakadu_compress_options = kakadu_compress_options
        self.converter = conversion.Converter(exiftool_path=exiftool_path)

        self.kakadu = Kakadu(kakadu_base_path=kakadu_base_path)

        self.log = logging.getLogger(__name__)

    def generate_derivatives_from_jpg(self, jpg_filepath, output_folder, save_embedded_metadata=True,
                                      check_lossless=True):
        """
        Extracts the embedded metadata, creates a copy of the JPEG file and a validated JPEG2000 file.
        Stores all in the given folder.

        :param jpg_filepath: The path to the source JPEG file.
        :param output_folder: The folder where the derivatives will be stored
        :param save_embedded_metadata: If true, metadata will be extracted from the image file and preserved in a separate xml file
        :param check_lossless: If true, check the created JPEG2000 file is visually identical to the TIFF created from the source file
        :return: filepaths of created files
        """
        self.log.debug("Processing {0}".format(jpg_filepath))
        self.log.info("There may be some loss in converting from jpg to jpg2000, as jpg compression is lossy. "
                      "The lossless check is against the tiff created from the jpg")
        source_file_name = os.path.basename(jpg_filepath)

        validation.check_image_suitable_for_jp2_conversion(
            jpg_filepath, require_icc_profile_for_colour=self.require_icc_profile_for_colour,
            require_icc_profile_for_greyscale=self.require_icc_profile_for_greyscale)

        output_jpg_filepath = os.path.join(output_folder, self._get_filename(DEFAULT_JPG_FILENAME, source_file_name))
        shutil.copy(jpg_filepath, output_jpg_filepath)
        generated_files = [output_jpg_filepath]

        if save_embedded_metadata:
            embedded_metadata_file_path = os.path.join(output_folder,
                                                       self._get_filename(DEFAULT_EMBEDDED_METADATA_FILENAME, source_file_name))
            self.converter.extract_xmp_to_sidecar_file(jpg_filepath, embedded_metadata_file_path)
            self.log.debug('Extracted metadata file {0} generated'.format(embedded_metadata_file_path))
            generated_files += [embedded_metadata_file_path]

        with tempfile.NamedTemporaryFile(prefix='image-processing_', suffix='.tif') as scratch_tiff_file_obj:
            scratch_tiff_filepath = scratch_tiff_file_obj.name
            self.converter.convert_to_tiff(jpg_filepath, scratch_tiff_filepath)

            validation.check_colour_profiles_match(jpg_filepath, scratch_tiff_filepath)

            lossless_filepath = os.path.join(output_folder,
                                             self._get_filename(DEFAULT_LOSSLESS_JP2_FILENAME, source_file_name))
            self.generate_jp2_from_tiff(scratch_tiff_filepath, lossless_filepath)
            self.validate_jp2_conversion(scratch_tiff_filepath, lossless_filepath, check_lossless=check_lossless)
            generated_files.append(lossless_filepath)

        self.log.debug("Successfully generated derivatives for {0} in {1}".format(jpg_filepath, output_folder))

        return generated_files

    def generate_derivatives_from_tiff(self, tiff_filepath, output_folder, include_tiff=False, save_embedded_metadata=True,
                                       create_jpg_as_thumbnail=True, check_lossless=True):
        """
        Extracts the embedded metadata, creates a JPEG file and a validated JPEG2000 file.
        Stores all in the given folder.

        :param create_jpg_as_thumbnail: create the JPG as a resized thumbnail, not a high quality image.
            Parameters for resize and quality are set on a class level
        :param tiff_filepath:
        :param output_folder: the folder where the related dc.xml will be stored
        :param include_tiff: Include copy of source tiff file in derivatives
        :param save_embedded_metadata: If true, metadata will be extracted from the image file and preserved in a separate xml file
        :param check_lossless: If true, check the created jpg2000 file is visually identical to the source file
        :return: filepaths of created files
        """
        self.log.debug("Processing {0}".format(tiff_filepath))
        source_file_name = os.path.basename(tiff_filepath)

        validation.check_image_suitable_for_jp2_conversion(
            tiff_filepath, require_icc_profile_for_colour=self.require_icc_profile_for_colour,
            require_icc_profile_for_greyscale=self.require_icc_profile_for_greyscale)

        with Image.open(tiff_filepath) as tiff_pil:
            if tiff_pil.mode == 'RGBA':
                # some RGBA tiffs don't convert properly back from jp2 - kakadu warns about unassociated alpha channels
                check_lossless = True

        with tempfile.NamedTemporaryFile(prefix='image-processing_', suffix='.tif') as temp_tiff_file_obj:
            # only work from a temporary file if we need to - e.g. if the tiff filepath is invalid,
            # or if we need to normalise the tiff. Otherwise just use the original tiff
            temp_tiff_filepath = temp_tiff_file_obj.name
            if os.path.splitext(tiff_filepath)[1].lower() not in ['.tif', '.tiff']:
                shutil.copy(tiff_filepath, temp_tiff_filepath)
                normalised_tiff_filepath = temp_tiff_filepath
            else:
                normalised_tiff_filepath = tiff_filepath

            jpeg_filepath = os.path.join(output_folder, self._get_filename(DEFAULT_JPG_FILENAME, source_file_name))

            jpg_quality = None if create_jpg_as_thumbnail else self.jpg_high_quality_value
            jpg_resize = self.jpg_thumbnail_resize_value if create_jpg_as_thumbnail else None

            self.converter.convert_to_jpg(normalised_tiff_filepath, jpeg_filepath,
                                      quality=jpg_quality, resize=jpg_resize)
            self.log.debug('jpeg file {0} generated'.format(jpeg_filepath))
            generated_files = [jpeg_filepath]

            if save_embedded_metadata:
                embedded_metadata_file_path = os.path.join(output_folder,
                                                           self._get_filename(DEFAULT_EMBEDDED_METADATA_FILENAME, source_file_name))
                self.converter.extract_xmp_to_sidecar_file(tiff_filepath, embedded_metadata_file_path)
                self.log.debug('Extracted metadata file {0} generated'.format(embedded_metadata_file_path))
                generated_files += [embedded_metadata_file_path]

            if include_tiff:
                output_tiff_filepath = os.path.join(output_folder,
                                                    self._get_filename(DEFAULT_TIFF_FILENAME, source_file_name))
                shutil.copy(tiff_filepath, output_tiff_filepath)
                generated_files += [output_tiff_filepath]

            lossless_filepath = os.path.join(output_folder,
                                             self._get_filename(DEFAULT_LOSSLESS_JP2_FILENAME, source_file_name))
            self.generate_jp2_from_tiff(normalised_tiff_filepath, lossless_filepath)
            self.validate_jp2_conversion(normalised_tiff_filepath, lossless_filepath, check_lossless=check_lossless)
            generated_files.append(lossless_filepath)

            self.log.debug("Successfully generated derivatives for {0} in {1}".format(tiff_filepath, output_folder))

            return generated_files

    def generate_jp2_from_tiff(self, tiff_file, jp2_filepath):
        """
        Creates lossless JPEG2000 at jp2_filepath


        :param tiff_file: The source TIFF file.
        :param jp2_filepath: The output filepath
        """
        kakadu_options = list(self.kakadu_compress_options)

        with Image.open(tiff_file) as tiff_pil:
            if tiff_pil.mode == 'RGBA':
                if kakadu.ALPHA_OPTION not in kakadu_options:
                    kakadu_options += [kakadu.ALPHA_OPTION]

        self.kakadu.kdu_compress(tiff_file, jp2_filepath, kakadu_options=kakadu_options)
        self.log.debug('Lossless jp2 file {0} generated'.format(jp2_filepath))
        # as of v7.10.4, kakadu doesn't copy over a lot of the technical metadata, so we do that separately
        self.converter.copy_over_embedded_metadata(tiff_file, jp2_filepath, write_only_xmp=True)

    def validate_jp2_conversion(self, tiff_file, jp2_filepath, check_lossless=True, jpylyzer_output_filepath=None):
        """
        Validate the jp2 file using jpylyzer, and check that the conversion from tif to jp2 was lossless
        Raises a :class:`~image_processing.exceptions.ValidationError` if either check fails.

        :param tiff_file:
        :param jp2_filepath:
        :param check_lossless: if false, don't check the conversion from tif to jp2 was lossless
        :param jpylyzer_output_filepath: write the jpylyzer xml output to this file if given
        """
        validation.validate_jp2(jp2_filepath, jpylyzer_output_filepath)
        if check_lossless:
            self.check_conversion_was_lossless(tiff_file, jp2_filepath)

    def check_conversion_was_lossless(self, source_file, lossless_jpg_2000_file):
        """
        Visually compare the source file to the TIFF generated by expanding the lossless JPEG2000,
        and raise a :class:`~image_processing.exceptions.ValidationError` if they do not match.
        Does not check technical metadata beyond colour profile and mode.

        :param source_file: Must be TIFF - cannot convert losslessly from JPEG to TIFF
        :param lossless_jpg_2000_file: The JPEG2000 file to compare.
        """
        self.log.debug('Checking conversion from source file {0} to jp2 file {1} was lossless'
                       .format(source_file, lossless_jpg_2000_file))
        with tempfile.NamedTemporaryFile(prefix='jp2_reconvert_', suffix='.tif') as reconverted_tiff_file_obj:
            reconverted_tiff_filepath = reconverted_tiff_file_obj.name
            self.kakadu.kdu_expand(lossless_jpg_2000_file, reconverted_tiff_filepath, kakadu_options=['-fussy'])
            validation.check_visually_identical(source_file, reconverted_tiff_filepath)
        self.log.info('Conversion from source file {0} to jp2 file {1} was lossless'
                      .format(source_file, lossless_jpg_2000_file))

    def _get_filename(self, default_filename, source_file_name):
        """
        Get a filename for the derivative file specified by default_filename
        If use_default_filenames is set, just use the default value provided
        Otherwise, create one from the original filename

        :param default_filename:
        :param source_file_name:
        """
        if self.use_default_filenames:
            return default_filename

        orig_filename_base = os.path.splitext(source_file_name)[0]
        if default_filename == DEFAULT_TIFF_FILENAME:
            return "{0}.tiff".format(orig_filename_base)
        elif default_filename == DEFAULT_JPG_FILENAME:
            return "{0}.jpg".format(orig_filename_base)
        elif default_filename == DEFAULT_EMBEDDED_METADATA_FILENAME:
            return "{0}.xmp".format(orig_filename_base)
        elif default_filename == DEFAULT_LOSSLESS_JP2_FILENAME:
            return "{0}.jp2".format(orig_filename_base)
