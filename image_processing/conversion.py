from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import subprocess
import logging

import os
from PIL import Image
from libxmp import XMPFiles

from image_processing import utils
from image_processing.exceptions import ImageProcessingError


class Converter(object):
    """
    Convert tiff to/from jpg while preserving technical metadata and icc profiles
    """

    def __init__(self, exiftool_path='exiftool'):
        if not utils.cmd_is_executable(exiftool_path):
            raise OSError("Could not find executable {0}. Check exiftool is installed and exists at the configured path"
                          .format(exiftool_path))
        self.exiftool_path = exiftool_path
        self.logger = logging.getLogger(__name__)

    def convert_to_tiff(self, input_filepath, output_filepath):
        """
        Convert an image file to tif, preserving ICC profile and embedded metadata
        :param input_filepath:
        :param output_filepath:
        """
        with Image.open(input_filepath) as input_pil:
            # this seems to use no compression by default. Specifying compression='None' means no icc is saved
            input_pil.save(output_filepath, "TIFF")
        self.copy_over_embedded_metadata(input_filepath, output_filepath)

    def convert_to_jpg(self, input_filepath, output_filepath, resize=None, quality=None):
        """
        Convert an image file to jpg, preserving ICC profile and embedded metadata
        :param input_filepath:
        :param output_filepath:
        :param resize: if present, resize by this amount to make a thumbnail. e.g. 0.5 to make a thumbnail half the size
        :param quality: quality of created jpg: either None, or 1-95
        """
        with Image.open(input_filepath) as input_pil:
            icc_profile = input_pil.info.get('icc_profile')
            if input_pil.mode == 'RGBA':
                self.logger.warning(
                    'Image is RGBA - the alpha channel will be removed from the JPEG derivative image')
                input_pil = input_pil.convert(mode="RGB")
            if resize:
                thumbnail_size = tuple(int(i * resize) for i in input_pil.size)
                input_pil.thumbnail(thumbnail_size, Image.LANCZOS)
            if quality:
                input_pil.save(output_filepath, "JPEG", quality=quality, icc_profile=icc_profile)
            else:
                input_pil.save(output_filepath, "JPEG", icc_profile=icc_profile)
        self.copy_over_embedded_metadata(input_filepath, output_filepath)

    def copy_over_embedded_metadata(self, input_image_filepath, output_image_filepath):
        """
        Copy embedded image metadata from the input_image_filepath to the output_image_filepath
        """
        if not os.access(output_image_filepath, os.W_OK):
            raise IOError("Couldn't write to output path {0}".format(output_image_filepath))

        command_options = [self.exiftool_path, '-tagsFromFile', input_image_filepath, '-overwrite_original',
                           output_image_filepath]
        self.logger.debug(' '.join(command_options))
        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ImageProcessingError('Exiftool at {0} failed to copy from {1}. Command: {2}, Error: {3}'.
                                       format(self.exiftool_path, input_image_filepath, ' '.join(command_options), e))

    def extract_xmp_to_sidecar_file(self, image_filepath, output_xmp_filepath):
        """
        Extract embedded image metadata from the image_filepath to an xmp file
        """
        if os.path.isfile(output_xmp_filepath):
            os.remove(output_xmp_filepath)
        if not os.access(os.path.dirname(output_xmp_filepath), os.W_OK):
            raise IOError("Couldn't write to output path {0}".format(output_xmp_filepath))
        if not os.path.splitext(output_xmp_filepath)[1] == ".xmp":
            raise IOError("Xmp output file {0} needs an xmp extension".format(output_xmp_filepath))

        command_options = [self.exiftool_path, '-tagsFromFile', image_filepath, '-all',
                           '-ICC_Profile:ProfileDescription>ICCProfileName',  # map icc profile name to photoshop:ICCProfile
                           '-o', output_xmp_filepath]  # must not exist already

        self.logger.debug(' '.join(command_options))
        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ImageProcessingError('Exiftool at {0} failed to extract metadata from {1}. Command: {2}, Error: {3}'.
                                       format(self.exiftool_path, image_filepath, ' '.join(command_options), e))