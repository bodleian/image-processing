from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import io
import subprocess
import logging

import os
from PIL import Image, ImageCms

from image_processing import utils
from image_processing.exceptions import ImageProcessingError


class Converter(object):
    """
    Convert TIFF to and from JPEG while preserving technical metadata and ICC profiles
    """

    def __init__(self, exiftool_path='exiftool'):
        if not utils.cmd_is_executable(exiftool_path):
            raise OSError("Could not find executable {0}. Check exiftool is installed and exists at the configured path"
                          .format(exiftool_path))
        self.exiftool_path = exiftool_path
        self.logger = logging.getLogger(__name__)

    def convert_to_tiff(self, input_filepath, output_filepath):
        """
        Convert an image file to TIFF, preserving ICC profile and embedded metadata
        :param input_filepath:
        :param output_filepath:
        """
        with Image.open(input_filepath) as input_pil:
            # this seems to use no compression by default. Specifying compression='None' means no ICC is saved
            input_pil.save(output_filepath, "TIFF")
        self.copy_over_embedded_metadata(input_filepath, output_filepath)

    def convert_to_jpg(self, input_filepath, output_filepath, resize=None, quality=None):
        """
        Convert an image file to JPEG, preserving ICC profile and embedded metadata
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

    def copy_over_embedded_metadata(self, input_image_filepath, output_image_filepath, write_only_xmp=False):
        """
        Copy embedded image metadata from the input_image_filepath to the output_image_filepath

        :param write_only_xmp: Copy all information to the same-named tags in XMP (if they exist). With JP2 it's safest to only use xmp tags, as other ones may not be supported by all software
        """
        if not os.access(input_image_filepath, os.R_OK):
            raise IOError("Could not read input image path {0}".format(input_image_filepath))
        if not os.access(output_image_filepath, os.W_OK):
            raise IOError("Could not write to output path {0}".format(output_image_filepath))

        command_options = [self.exiftool_path, '-tagsFromFile', input_image_filepath, '-overwrite_original']
        if write_only_xmp:
            command_options += ['-xmp:all<all']
        command_options += [output_image_filepath]
        self.logger.debug(' '.join(command_options))
        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ImageProcessingError('Exiftool at {0} failed to copy from {1}. Command: {2}, Error: {3}'.
                                       format(self.exiftool_path, input_image_filepath, ' '.join(command_options), e))

    def extract_xmp_to_sidecar_file(self, image_filepath, output_xmp_filepath):
        """
        Extract embedded image metadata from the image_filepath to an xmp file.
        Includes the ICC profile description.
        """
        if os.path.isfile(output_xmp_filepath):
            os.remove(output_xmp_filepath)
        if not os.access(image_filepath, os.R_OK):
            raise IOError("Could not read input image path {0}".format(image_filepath))
        if not os.access(os.path.abspath(os.path.dirname(output_xmp_filepath)), os.W_OK):
            raise IOError("Could not write to output path {0}".format(output_xmp_filepath))
        if not os.path.splitext(output_xmp_filepath)[1] == ".xmp":
            raise IOError("XMP output file {0} needs an xmp extension".format(output_xmp_filepath))

        command_options = [self.exiftool_path, '-tagsFromFile', image_filepath, '-all',
                           '-ICC_Profile:ProfileDescription>ICCProfileName',  # map icc profile name to photoshop:ICCProfile
                           '-o', output_xmp_filepath]  # must not exist already

        self.logger.debug(' '.join(command_options))
        try:
            subprocess.check_call(command_options, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise ImageProcessingError('Exiftool at {0} failed to extract metadata from {1}. Command: {2}, Error: {3}'.
                                       format(self.exiftool_path, image_filepath, ' '.join(command_options), e))

    def convert_icc_profile(self, image_filepath, output_filepath, icc_profile_filepath, new_colour_mode=None):
        with Image.open(image_filepath) as input_pil:
            input_icc_obj = input_pil.info.get('icc_profile')
            if input_icc_obj is None:
                raise ImageProcessingError("Image doesn't have a profile")
            input_profile = ImageCms.getOpenProfile(io.BytesIO(input_icc_obj))

            output_pil = ImageCms.profileToProfile(input_pil, input_profile, icc_profile_filepath,
                                                   outputMode=new_colour_mode, inPlace=0)
            output_pil.save(output_filepath)
        self.copy_over_embedded_metadata(image_filepath, output_filepath)


def _get_bit_depths(pil_image):
    """
    Returns in base 10 for simplicity
    :param pil_image:
    :return: [255, 255, 255] or [255]
    """
    extrema = pil_image.getextrema()
    # above returns either (0, 255) (for monochrome) or ((0, 255), (0,255), (0,255)) for RGB
    if len(pil_image.getbands()) == 1:
        extrema = extrema,
    return [max_val for (min_val, max_val) in list(extrema)]


# todo: errors or pass back false
def _check_no_data_lost(orig_bit_depths, new_bit_depths):
    if len(new_bit_depths) < len(orig_bit_depths):
        # what about rgba?
        pass
    for i in range(0, min(len(orig_bit_depths), len(new_bit_depths))):
        if new_bit_depths[i] < orig_bit_depths[i]:
            pass