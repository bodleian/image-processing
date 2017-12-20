from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from jpylyzer.jpylyzer import checkOneFile
from PIL import Image
from numbers import Number
from image_processing import exceptions
import logging


def validate_jp2(image_file):
    logger = logging.getLogger(__name__)
    jp2_element = checkOneFile(image_file)
    success = jp2_element.findtext('isValidJP2') == 'True'
    if not success:
        logger.error('{0} failed jypylzer validation'.format(image_file))
        logger.error(str(jp2_element))
        raise exceptions.ValidationError('{0} failed jypylzer validation'.format(image_file))
    logger.debug('{0} is a valid jp2 file'.format(image_file))


def check_conversion_was_lossless(source_filepath, converted_filepath, allow_monochrome_to_rgb=False):
    """
    Visually compare the source file to the converted file, and throw an exception if they don't match.
    :param source_filepath:
    :param converted_filepath:
    :param allow_monochrome_to_rgb: allow conversions where the monochrome source has been converted losslessly to rgb
    :return:
    """

    logger = logging.getLogger(__name__)
    logger.debug("Comparing pixel values and colour profile of {0} and {1}".format(source_filepath, converted_filepath))

    with Image.open(source_filepath) as source_image:
        with Image.open(converted_filepath) as converted_image:

            if allow_monochrome_to_rgb:
                monochrome_to_rgb = source_image.mode in ['1', 'L'] and converted_image.mode == 'RGB'
            else:
                monochrome_to_rgb = False

            if not monochrome_to_rgb:
                if source_image.mode != converted_image.mode:
                    raise exceptions.ValidationError(
                        'Converted file {0} has different colour mode from {1}'
                            .format(converted_filepath, source_filepath)
                    )

                source_icc = source_image.info.get('icc_profile')
                converted_icc = converted_image.info.get('icc_profile')
                if source_icc != converted_icc:
                    raise exceptions.ValidationError(
                        'Converted file {0} has different colour profile from {1}'
                            .format(converted_filepath, source_filepath)
                    )

            logger.debug('Loading pixels of images into memory to compare. If this crashes, the machine probably needs more memory')
            source_pixels = list(source_image.getdata())
            converted_pixels = list(converted_image.getdata())

            if monochrome_to_rgb:
                logger.debug('Adjusting pixels of monochrome image to RGB before comparison')
                source_pixels = _adjust_pixels_for_monochrome(source_pixels)

            if not source_pixels == converted_pixels:
                raise exceptions.ValidationError(
                    'Converted file {0} does not visually match original {1}'
                        .format(converted_filepath, source_filepath)
                )
            logger.debug('{0} and {1} are equivalent'.format(source_filepath, converted_filepath))


def _adjust_pixels_for_monochrome(pixels_list):
    if isinstance(pixels_list[0], Number):
        return [(a, a, a) for a in pixels_list]
    else:
        return pixels_list
