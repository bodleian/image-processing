from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import logging
import subprocess
from PIL import Image
from image_processing.kakadu import DEFAULT_BDLSS_OPTIONS, LOSSLESS_OPTIONS, Kakadu
from image_processing.image_magick import ImageMagick
from image_processing.exceptions import ImageProcessingError, ImageMagickError


DEFAULT_IMAGE_MAGICK_PATH = '/usr/bin/'


class ImageConverter(object):

    def __init__(self, kakadu_base_path, image_magick_path=DEFAULT_IMAGE_MAGICK_PATH):
        self.image_magick_path = image_magick_path
        self.kakadu = Kakadu(kakadu_base_path)
        self.image_magick = ImageMagick(image_magick_path)
        self.log = logging.getLogger(__name__)

    def convert_unsupported_file_to_jpeg2000(self, input_filepath, output_filepath):
        """
        Converts an image file unsupported by kakadu (e.g. jpg) losslessly to jpeg2000 by converting it to tiff first
        Useful for images with badly formed metadata that wouldn't otherwise pass jp2 validation
        """
        tiff_filepath = os.path.splitext(output_filepath)[0] + '.tif'
        self.convert_to_tiff(input_filepath, tiff_filepath)
        self.convert_to_jpeg2000(tiff_filepath, output_filepath)
        os.remove(tiff_filepath)

    def convert_to_jpeg2000(self, input_filepath, output_filepath, lossless=True):
        """
        Converts an image file supported by kakadu to jpeg2000.
        Handles colour conversion of greyscale and bitonal files to 3 colour channels of information.
        """
        image_is_monochrome = self.is_monochrome(input_filepath)

        if image_is_monochrome:
            self.convert_monochrome_to_jpeg2000(input_filepath, output_filepath, lossless=lossless)
        else:
            self.convert_colour_to_jpeg2000(input_filepath, output_filepath, lossless=lossless)

    def convert_colour_to_jpeg2000(self, input_filepath, output_filepath, lossless=True):
        """
        Converts an non-monochrome image file supported by kakadu to jpeg2000
        """
        if lossless:
            extra_options = LOSSLESS_OPTIONS
        else:
            extra_options = ["-rate", "3"]

        kakadu_options = DEFAULT_BDLSS_OPTIONS + extra_options
        self.kakadu.kdu_compress(input_filepath, output_filepath, kakadu_options)

    def repage_image(self, input_filepath, output_filepath):
        """Fix negative image positions unsupported problems"""
        options = ['+repage']

        self.image_magick.convert(input_filepath, output_filepath, post_options=options)

    def is_monochrome(self, input_filepath):
        image_mode = self.get_colourspace(input_filepath)  # colour mode of image
        if image_mode in ['L', '1']:  # greyscale, Bitonal
            return True
        elif image_mode in ['RGB', 'RGBA', 'sRGB']:
            return False
        else:
            raise ImageProcessingError("Could not identify image colour mode of " + input_filepath)

    def get_colourspace(self, image_file):
        if not os.access(image_file, os.R_OK):
            raise IOError("Couldn't access image file {0} to test".format(image_file))
        # get properties of image
        try:
            #todo: consider removing PIL entirely. First need to make sure the imagemagick monotone colour space results are the same.
            colourspace = Image.open(image_file).mode  # colour mode of image
            return colourspace
        except IOError as e:
            # if PIP won't support the file, try imagemagick
            self.log.info("PIP doesn't support {0}: {1}. Trying image magick".format(image_file, e))
            command = "{0} -format %[colorspace] '{1}[0]'".format(os.path.join(self.image_magick_path, 'identify'), image_file)
            try:
                colourspace = subprocess.check_output(command).rstrip()
            except subprocess.CalledProcessError as e:
                raise ImageMagickError('Image magick identify command failed: {0}'.format(command), e)
            return colourspace

    def convert_monochrome_to_jpeg2000(self, input_filepath, output_filepath, lossless=True):
        """
        Converts an bitonal or greyscale image file supported by kakadu to jpeg2000
        The same input is copied to each of the
        three colour channels, with no colour palette applied, to create a 24-bit
        [3 x 8] image
        """
        if lossless:
            extra_options = LOSSLESS_OPTIONS
        else:
            extra_options = ["-rate", "3"]
        kakadu_options = DEFAULT_BDLSS_OPTIONS + extra_options + ["-no_palette"]
        self.kakadu.kdu_compress([input_filepath for i in range(0, 3)], output_filepath, kakadu_options)

    def convert_to_tiff(self, input_filepath, output_filepath, strip_embedded_metadata=False):
        post_options = ['-strip'] if strip_embedded_metadata else []
        return self.convert_image_to_format(input_filepath, output_filepath, img_format='tif',
                                            post_options=post_options)

    def convert_to_jpg(self, input_filepath, output_filepath, resize=None, quality=None):
        initial_options = []
        if resize is not None:
            initial_options += ['-resize', resize]
        if quality is not None:
            initial_options += ['-quality', quality]
        return self.convert_image_to_format(input_filepath, output_filepath, img_format='jpg',
                                            initial_options=initial_options)

    def convert_tiff_colour_profile(self, input_filepath, output_filepath, profile):

        input_is_monochrome = self.is_monochrome(input_filepath)
        options = ['-profile', profile]
        if input_is_monochrome:
            options += ['-compress', 'none',
                        '-depth', '8',
                        '-type', 'truecolor',
                        '-alpha', 'off']

        self.image_magick.convert(input_filepath, output_filepath, initial_options=options)

    def convert_image_to_format(self, input_filepath, output_filepath, img_format,
                                post_options=None, initial_options=None):
        """
        Uses image magick to convert the file to the given format
        :param initial_options: command line arguments which need to go before the input file
        :param post_options: command line arguments which need to go after the input file
        """

        if post_options is None:
            post_options = []
        if initial_options is None:
            initial_options = []

        post_options += ['-format', img_format]

        self.image_magick.convert(input_filepath, output_filepath, post_options=post_options,
                                  initial_options=initial_options)
