
import os
import logging
import subprocess
from PIL import Image
from kakadu import DEFAULT_BDLSS_OPTIONS, LOSSLESS_OPTIONS, Kakadu
from image_magick import ImageMagick
from image_processing.exceptions import ImageProcessingError, ImageMagickError


# todo: make configurable
KAKADU_BASE_PATH = '/opt/kakadu'
IMAGE_MAGICK_PATH = '/usr/bin/'
ICC_PROFILE = "/opt/kakadu/sRGB_v4_ICC_preference.icc"


def convert_unsupported_file_to_jpeg2000(input_filepath, output_filepath):
    """
    Converts an image file unsupported by kakadu (e.g. jpg) losslessly to jpeg2000 by converting it to tiff first
    Useful for images with badly formed metadata that wouldn't otherwise pass jp2 validation
    """
    tiff_filepath = os.path.splitext(output_filepath)[0] + '.tif'
    convert_to_tiff(input_filepath, tiff_filepath)
    convert_colour_to_jpeg2000(tiff_filepath, output_filepath)
    os.remove(tiff_filepath)


def convert_to_jpeg2000(input_filepath, output_filepath, lossless=True):
    """
    Converts an image file supported by kakadu to jpeg2000. Has special handling for monochrome images
    """
    image_is_monochrome = is_monochrome(input_filepath)

    if image_is_monochrome:
        convert_monochrome_to_jpeg2000(input_filepath, output_filepath, lossless=lossless)
    else:
        convert_colour_to_jpeg2000(input_filepath, output_filepath, lossless=lossless)


def convert_colour_to_jpeg2000(input_filepath, output_filepath, lossless=True):
    """
    Converts an non-monochrome image file supported by kakadu to jpeg2000
    """
    if lossless:
        extra_options = LOSSLESS_OPTIONS
    else:
        extra_options = ["-rate", "3"]

    kakadu_options = DEFAULT_BDLSS_OPTIONS + extra_options
    kakadu = Kakadu(KAKADU_BASE_PATH)
    kakadu.kdu_compress(input_filepath, output_filepath, kakadu_options)


def repage_image(input_filepath, output_filepath):
    """Fix negative image positions unsupported problems"""
    options = ['+repage']

    magick = ImageMagick(IMAGE_MAGICK_PATH)
    magick.convert(input_filepath, output_filepath, post_options=options)


def is_monochrome(input_filepath):
    image_mode = get_colourspace(input_filepath)  # colour mode of image
    if image_mode in ['L', '1']:  # greyscale, Bitonal
        return True
    elif image_mode in ['RGB', 'RGBA', 'sRGB']:
        return False
    else:
        raise ImageProcessingError("Could not identify image colour mode of " + input_filepath)


def get_colourspace(image_file):
    if not os.access(image_file, os.R_OK):
        raise IOError("Couldn't access image file {0} to test".format(image_file))
    # get properties of image
    try:
        #todo: consider removing PIL entirely. First need to make sure the imagemagick monotone colour space results are the same.
        colourspace = Image.open(image_file).mode  # colour mode of image
        return colourspace
    except IOError as e:
        # if PIP won't support the file, try imagemagick
        logging.info("PIP doesn't support {0}: {1}. Trying image magick".format(image_file, e))
        command = "{0} -format %[colorspace] '{1}[0]'".format(os.path.join(IMAGE_MAGICK_PATH, 'identify'), image_file)
        try:
            colourspace = subprocess.check_output(command).rstrip()
        except subprocess.CalledProcessError as e:
            raise ImageMagickError('Image magick identify command failed: {0}'.format(command), e)
        return colourspace


def convert_monochrome_to_jpeg2000(input_filepath, output_filepath, lossless=True):
    """
    Converts an bitonal or greyscale image file supported by kakadu to jpeg2000
    """
    if lossless:
        extra_options = LOSSLESS_OPTIONS
    else:
        extra_options = ["-rate", "3"]
    kakadu_options = DEFAULT_BDLSS_OPTIONS + extra_options + ["-no_palette"]
    kakadu = Kakadu(KAKADU_BASE_PATH)
    kakadu.kdu_compress([input_filepath for i in range(0,3)], output_filepath, kakadu_options)


def convert_to_tiff(input_filepath, output_filepath, extra_options=None):
    return convert_image_to_format(input_filepath, output_filepath, img_format='tif', extra_options=extra_options)


def convert_to_jpg(input_filepath, output_filepath, extra_options=None):
    return convert_image_to_format(input_filepath, output_filepath, img_format='jpg', extra_options=extra_options)


def convert_tiff_colour_profile(input_filepath, output_filepath):

    input_is_monochrome = is_monochrome(input_filepath)
    options = ['-profile', ICC_PROFILE]
    if input_is_monochrome:
        options += ['-compress', 'none',
                    '-depth', '8',
                    '-type', 'truecolor',
                    '-alpha', 'off']

    magick = ImageMagick(IMAGE_MAGICK_PATH)
    magick.convert(input_filepath, output_filepath, initial_options=options)


def convert_image_to_format(input_filepath, output_filepath, img_format, extra_options=None):
    """
    Uses image magick to convert the file to the given format
    """

    options = ['-format', img_format]
    if extra_options:
        options += ['-strip']

    magick = ImageMagick(IMAGE_MAGICK_PATH)
    magick.convert(input_filepath, output_filepath, post_options=options)
