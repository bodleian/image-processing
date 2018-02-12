from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import logging
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
        Converts an image file unsupported by kakadu (e.g. jpg) as losslessly as is possible to jpeg2000
         by converting it to tiff first
        """
        tiff_filepath = os.path.splitext(output_filepath)[0] + '.tif'
        self.convert_to_tiff(input_filepath, tiff_filepath)
        self.convert_to_jpeg2000(tiff_filepath, output_filepath)
        os.remove(tiff_filepath)

    def convert_to_jpeg2000(self, input_filepath, output_filepath, lossless=True,
                            kakadu_options=DEFAULT_BDLSS_OPTIONS):
        """
        Converts an image file supported by kakadu to jpeg2000
        Bitonal or greyscale image files are converted to a single channel jpeg2000 file
        """
        if lossless:
            extra_options = LOSSLESS_OPTIONS
        else:
            extra_options = ["-rate", "3"]

        kakadu_options = kakadu_options + extra_options
        self.kakadu.kdu_compress(input_filepath, output_filepath, kakadu_options)

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
