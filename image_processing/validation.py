from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from jpylyzer.jpylyzer import checkOneFile
from PIL import Image, ImageSequence
from numbers import Number
from image_processing import exceptions
import logging
from hashlib import sha256
from image_processing.exceptions import ImageProcessingError


def validate_jp2(image_file):
    logger = logging.getLogger(__name__)
    jp2_element = checkOneFile(image_file)
    success = jp2_element.findtext('isValidJP2') == 'True'
    if not success:
        logger.error('{0} failed jypylzer validation'.format(image_file))
        logger.error(str(jp2_element))
        raise exceptions.ValidationError('{0} failed jypylzer validation'.format(image_file))
    logger.debug('{0} is a valid jp2 file'.format(image_file))


def generate_pixel_checksum(image_filepath, normalise_to_rgb=False):
    logger = logging.getLogger(__name__)
    with Image.open(image_filepath) as pil_image:
        logger.debug('Loading pixels of image into memory. If this crashes, the machine probably needs more memory')
        pixels = repr(list(pil_image.getdata()))
        if normalise_to_rgb:
            pixels = _adjust_pixels_for_monochrome(pixels)
        return sha256(pixels).hexdigest()


def check_visually_identical(source_filepath, converted_filepath,
                             source_pixel_checksum=None, allow_monochrome_to_rgb=False):
    """
    Visually compare the files, and throw an exception if they don't match.
    :param source_filepath:
    :param converted_filepath:
    :param source_pixel_checksum: if not None, uses this instead of reading out the source pixels again
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

            if source_pixel_checksum:
                pixels_identical = generate_pixel_checksum(converted_filepath) == source_pixel_checksum
            else:
                logger.debug('Loading pixels of images into memory to compare. '
                             'If this crashes, the machine probably needs more memory')
                source_pixels = list(source_image.getdata())
                converted_pixels = list(converted_image.getdata())

                if monochrome_to_rgb:
                    logger.debug('Adjusting pixels of monochrome image to RGB before comparison')
                    source_pixels = _adjust_pixels_for_monochrome(source_pixels)

                pixels_identical = source_pixels == converted_pixels

            if not pixels_identical:
                raise exceptions.ValidationError(
                    'Converted file {0} does not visually match original {1}'
                        .format(converted_filepath, source_filepath)
                )

            logger.debug('{0} and {1} are equivalent'.format(source_filepath, converted_filepath))


def check_image_suitable_for_jp2_conversion(image_filepath):
    """
    Check over the image and make sure it's in a supported and tested format for conversion to jp2
    Raises exception if there are problems
    :param image_filepath:
    :return: must_check_lossless: if true, there are unsupported edge cases where this format doesn't convert
    losslessly, so the jp2 must be checked against the source image after conversion
    """

    logger = logging.getLogger(__name__)

    # todo: remove these errors once I've implemented and tested these cases, and add monochrome to accepted modes
    ACCEPTED_COLOUR_MODES = ['RGB', 'RGBA']
    must_check_lossless = False
    with Image.open(image_filepath) as image_pil:
        frames = len(list(ImageSequence.Iterator(image_pil)))
        if frames > 1:
            logger.warn('File has multiple layers: only the first one will be converted')
        icc = image_pil.info.get('icc_profile')
        if icc is None:
            logger.warn('No icc profile embedded in {0}'.format(image_filepath))
            raise NotImplementedError('No icc profile embedded in {0}. Unsupported case.'.format(image_filepath))

        colour_mode = image_pil.mode

        if colour_mode not in ACCEPTED_COLOUR_MODES:
            raise ImageProcessingError("Unsupported colour mode {0} for {1}".format(colour_mode, image_filepath))

        if colour_mode == 'RGBA':
            # In some cases alpha channel data is lost during jp2 conversion
            # As we rarely encounter these, we just put in a check to see if it was lossless and error otherwise
            logger.warn("{0} is an RGBA image, and may not be converted correctly into jp2. "
                          "The result should be checked to make sure it's lossless".format(image_filepath))
            must_check_lossless = True

    return must_check_lossless


def _adjust_pixels_for_monochrome(pixels_list):
    if isinstance(pixels_list[0], Number):
        return [(a, a, a) for a in pixels_list]
    else:
        return pixels_list
