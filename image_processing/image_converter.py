from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import logging
from image_processing.kakadu import DEFAULT_BDLSS_OPTIONS, LOSSLESS_OPTIONS, Kakadu
from PIL import Image
from libxmp import XMPFiles


class ImageConverter(object):

    def __init__(self, kakadu_base_path):
        self.kakadu = Kakadu(kakadu_base_path)
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

    def convert_to_tiff(self, input_filepath, output_filepath):
        with Image.open(input_filepath) as input_pil:
            # this seems to use no compression by default. Specifying compression='None' means no icc is saved
            input_pil.save(output_filepath, "TIFF")
        self.copy_over_xmp(input_filepath, output_filepath)

    def convert_to_jpg(self, input_filepath, output_filepath, resize=None, quality=None):
        with Image.open(input_filepath) as input_pil:
            icc_profile = input_pil.info.get('icc_profile')
            if input_pil.mode == 'RGBA':
                self.log.warning('Image is RGBA - the alpha channel will be removed from the JPEG derivative image')
                input_pil = input_pil.convert(mode="RGB")
            if resize:
                thumbnail_size = tuple(int(i * resize) for i in input_pil.size)
                input_pil.thumbnail(thumbnail_size, Image.LANCZOS)
            if quality:
                input_pil.save(output_filepath, "JPEG", quality=quality, icc_profile=icc_profile)
            else:
                input_pil.save(output_filepath, "JPEG", icc_profile=icc_profile)
        self.copy_over_xmp(input_filepath, output_filepath)

    def copy_over_xmp(self, input_image_filepath, output_image_filepath):
        original_xmp = self.get_xmp(input_image_filepath)
        self.set_xmp(output_image_filepath, original_xmp)

    def get_xmp(self, image_filepath):
        image_xmp_file = XMPFiles(file_path=image_filepath)
        xmp = image_xmp_file.get_xmp()
        image_xmp_file.close_file()
        return xmp

    def set_xmp(self, image_filepath, xmp):
        xmp_file = XMPFiles(file_path=image_filepath, open_forupdate=True)
        xmp_file.put_xmp(xmp)
        xmp_file.close_file()
