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
                input_pil.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            if quality:
                input_pil.save(output_filepath, "JPEG", quality=quality, icc_profile=icc_profile)
            else:
                input_pil.save(output_filepath, "JPEG", icc_profile=icc_profile)
        self.copy_over_embedded_metadata(input_filepath, output_filepath)

    def copy_over_embedded_metadata(self, input_image_filepath, output_image_filepath, write_only_xmp=False):
        """
        Copy embedded image metadata from the input_image_filepath to the output_image_filepath
        :param input_image_filepath: input filepath
        :param output_image_filepath: output filepath
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
        """
        Convert the image to a new icc profile. This is lossy, so should only be done when necessary (e.g. if jp2 doesn't support the colour profile)
        Doesn't support 16bit images due to limitations of Pillow

        Uses the perceptual rendering intent, as it's the recommended one for general photographic purposes, and loses less information on out-of-gamut colours than relative colormetric
        However, if we're converting to a matrix profile like AdobeRGB, this will use relative colormetric instead, as perceptual intents are only supported by lookup table colour profiles
        In practise, we should be converting to a wide gamut profile, so out-of-gamut colours will be limited anyway
        :param image_filepath:
        :param output_filepath:
        :param icc_profile_filepath:
        :param new_colour_mode:
        :return:
        """
        with Image.open(image_filepath) as input_pil:
            # BitsPerSample is 258 (see PIL.TiffTags.TAGS_V2). tag_v2 is populated when opening an image, but not when saving
            orig_bit_depths = input_pil.tag_v2[258]

            if orig_bit_depths not in [(8, 8, 8, 8), (8, 8, 8), (8,), (1,)]:
                raise ImageProcessingError("ICC profile conversion was unsuccessful for {0}: unsupported bit depth {1} "
                                           "Note: Pillow does not support 16 bit image profile conversion."
                                           .format(image_filepath, orig_bit_depths))

            input_icc_obj = input_pil.info.get('icc_profile')

            if input_icc_obj is None:
                raise ImageProcessingError("Image doesn't have a profile")

            input_profile = ImageCms.getOpenProfile(io.BytesIO(input_icc_obj))
            output_pil = ImageCms.profileToProfile(input_pil, input_profile, icc_profile_filepath,
                                                   renderingIntent=ImageCms.Intent.PERCEPTUAL,
                                                   outputMode=new_colour_mode, inPlace=0)
            output_pil.save(output_filepath)
        self.copy_over_embedded_metadata(image_filepath, output_filepath)
