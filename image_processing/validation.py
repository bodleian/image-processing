from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from jpylyzer.jpylyzer import checkOneFile
from PIL import Image, ImageSequence
from image_processing import exceptions
import logging
from hashlib import sha256


GREYSCALE = 'L'
BITONAL = '1'
ACCEPTED_COLOUR_MODES = ['RGB', 'RGBA', GREYSCALE, BITONAL]


def validate_jp2(image_file):
    logger = logging.getLogger(__name__)
    jp2_element = checkOneFile(image_file)
    success = jp2_element.findtext('isValidJP2') == 'True'
    if not success:
        logger.error('{0} failed jypylzer validation'.format(image_file))
        logger.error(str(jp2_element))
        raise exceptions.ValidationError('{0} failed jypylzer validation'.format(image_file))
    logger.debug('{0} is a valid jp2 file'.format(image_file))


def generate_pixel_checksum(image_filepath):
    logger = logging.getLogger(__name__)
    with Image.open(image_filepath) as pil_image:
        logger.debug('Loading pixels of image into memory. If this crashes, the machine probably needs more memory')
        pixels = repr(list(pil_image.getdata()))
        return sha256(pixels).hexdigest()


def check_visually_identical(source_filepath, converted_filepath,
                             source_pixel_checksum=None):
    """
    Visually compare the files, and throw an exception if they don't match.
    :param source_filepath:
    :param converted_filepath:
    :param source_pixel_checksum: if not None, uses this instead of reading out the source pixels again
    :return:
    """

    logger = logging.getLogger(__name__)
    logger.debug("Comparing pixel values and colour profile of {0} and {1}".format(source_filepath, converted_filepath))

    with Image.open(source_filepath) as source_image:
        with Image.open(converted_filepath) as converted_image:

            if source_image.mode != converted_image.mode:
                if source_image.mode == BITONAL and converted_image.mode == GREYSCALE:
                    logger.debug('Converted image is greyscale, not bitonal. This is expected')
                else:
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

                pixels_identical = source_pixels == converted_pixels

            if not pixels_identical:
                raise exceptions.ValidationError(
                    'Converted file {0} does not visually match original {1}'
                    .format(converted_filepath, source_filepath)
                )

            logger.debug('{0} and {1} are equivalent'.format(source_filepath, converted_filepath))


def check_image_suitable_for_jp2_conversion(image_filepath, allow_no_icc_profile_for_greyscale=True,
                                            allow_no_icc_profile=False):
    """
    Check over the image and make sure it's in a supported and tested format for conversion to jp2
    Raises exception if there are problems
    :param image_filepath:
    :param allow_no_icc_profile_for_greyscale: don't throw an error if a greyscale image doesn't have an icc profile
    note: bitonal images don't need icc profiles
    :param allow_no_icc_profile: don't throw an error if an image doesn't have an icc profile
    :return: must_check_lossless: if true, there are unsupported edge cases where this format doesn't convert
    losslessly, so the jp2 must be checked against the source image after conversion
    """

    logger = logging.getLogger(__name__)

    must_check_lossless = False

    with Image.open(image_filepath) as image_pil:

        colour_mode = image_pil.mode

        if colour_mode not in ACCEPTED_COLOUR_MODES:
            raise exceptions.ValidationError("Unsupported colour mode {0} for {1}".format(colour_mode, image_filepath))

        if colour_mode == 'RGBA':
            # In some cases alpha channel data is lost during jp2 conversion
            # As we rarely encounter these, we just put in a check to see if it was lossless and error otherwise
            logger.warn("{0} is an RGBA image, and may not be converted correctly into jp2. "
                        "The result should be checked to make sure it's lossless".format(image_filepath))
            must_check_lossless = True

        icc_not_needed = allow_no_icc_profile or colour_mode == BITONAL or \
                         (allow_no_icc_profile_for_greyscale and colour_mode == GREYSCALE)

        icc = image_pil.info.get('icc_profile')
        if icc is None:
            logger.warn('No icc profile embedded in {0}'.format(image_filepath))
            if not icc_not_needed:
                raise exceptions.ValidationError('No icc profile embedded in {0}.'.format(image_filepath))

        frames = len(list(ImageSequence.Iterator(image_pil)))
        if frames > 1:
            logger.warn('File has multiple layers: only the first one will be converted')

    return must_check_lossless
