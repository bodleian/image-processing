from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import logging
from PIL import Image
from image_processing.kakadu import DEFAULT_BDLSS_OPTIONS, LOSSLESS_OPTIONS, Kakadu
from image_processing.image_magick import ImageMagick


DEFAULT_IMAGE_MAGICK_PATH = '/usr/bin/'


class ImageConverter(object):

    def __init__(self, kakadu_base_path, image_magick_path=DEFAULT_IMAGE_MAGICK_PATH):
        self.image_magick_path = image_magick_path
        self.kakadu = Kakadu(kakadu_base_path)
        self.image_magick = ImageMagick(image_magick_path)
        self.log = logging.getLogger(__name__)

    def convert_unsupported_file_to_jpeg2000(self, input_filepath, output_filepath):
        """
        Converts an image file unsupported by kakadu (e.g. jpg) mostly losslessly to jpeg2000 by converting it to tiff first
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

    def convert_colour_to_jpeg2000(self, input_filepath, output_filepath, lossless=True,
                                   kakadu_options=DEFAULT_BDLSS_OPTIONS):
        """
        Converts an non-monochrome image file supported by kakadu to jpeg2000
        """
        if lossless:
            extra_options = LOSSLESS_OPTIONS
        else:
            extra_options = ["-rate", "3"]

        kakadu_options = kakadu_options + extra_options
        self.kakadu.kdu_compress(input_filepath, output_filepath, kakadu_options)

    @staticmethod
    def is_monochrome(input_filepath):
        with Image.open(input_filepath) as input_pil:
            image_mode = input_pil.mode  # colour mode of image
            return image_mode in ['L', '1']  # greyscale, Bitonal

    def convert_monochrome_to_jpeg2000(self, input_filepath, output_filepath, lossless=True,
                                       kakadu_options=DEFAULT_BDLSS_OPTIONS):
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
        # todo: should this be left without jp2_space?
        kakadu_options = kakadu_options + extra_options + ["-no_palette", '-jp2_space', 'sRGB']
        self.kakadu.kdu_compress([input_filepath for _ in range(0, 3)], output_filepath, kakadu_options)

    def convert_to_tiff(self, input_filepath, output_filepath_with_tif_extension):
        post_options = ['-compress', 'None']
        return self.image_magick.convert(input_filepath, output_filepath_with_tif_extension,
                                         post_options=post_options)

    def convert_to_jpg(self, input_filepath, output_filepath_with_jpg_extension, resize=None, quality=None):
        initial_options = []
        if resize is not None:
            initial_options += ['-resize', resize]
        if quality is not None:
            initial_options += ['-quality', quality]
        return self.image_magick.convert('{0}[0]'.format(input_filepath), output_filepath_with_jpg_extension,
                                         initial_options=initial_options)
