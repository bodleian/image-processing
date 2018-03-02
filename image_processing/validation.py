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
MONOTONE_COLOUR_MODES = [GREYSCALE, BITONAL]
ACCEPTED_COLOUR_MODES = ['RGB', 'RGBA', GREYSCALE, BITONAL]


def validate_jp2(image_file):
    """
    Uses jpylzer to validate the jp2 file. Raises a ValidationError if it fails
    :param image_file:
    :return:
    """
    logger = logging.getLogger(__name__)
    jp2_element = checkOneFile(image_file)
    success = jp2_element.findtext('isValidJP2') == 'True'
    if not success:
        logger.error('{0} failed jypylzer validation'.format(image_file))
        logger.error(str(jp2_element))
        raise exceptions.ValidationError('{0} failed jypylzer validation'.format(image_file))
    logger.debug('{0} is a valid jp2 file'.format(image_file))


def _to_bytes_generator(pil_image, min_buffer_size=65536):
    """
    An iterator version of the PIL.Image.tobytes method
    The PIL implementation stores the data in a separate array, doubling the memory usage
    :param pil_image: PIL.Image instance
    :param min_buffer_size:
    :return:
    """
    pil_image.load()
    e = Image._getencoder(pil_image.mode, 'raw', pil_image.mode)
    e.setimage(pil_image.im)

    # This encoder fails if the buffer is not large enough to hold one full line of data - see RawEncode.c
    buffer_size = max(min_buffer_size, pil_image.size[0] * 4)

    # signal is negative for errors, 1 for finished, and 0 otherwise
    length, signal, data = e.encode(buffer_size)
    while signal == 0:
        yield data
        length, signal, data = e.encode(buffer_size)
    if signal > 0:
        yield data
    else:
        raise RuntimeError("encoder error {0} in tobytes when reading image pixel data".format(signal))


def generate_pixel_checksum(image_filepath):
    """
    Generate a checksum unique to this image's pixel values
    :param image_filepath:
    :return:
    """
    with Image.open(image_filepath) as pil_image:
        return generate_pixel_checksum_from_pil_image(pil_image)


def generate_pixel_checksum_from_pil_image(pil_image):
    """
    Generate a checksum unique to this image's pixel values
    :param pil_image: PIL.Image instance
    :return:
    """
    logger = logging.getLogger(__name__)
    logger.debug('Loading pixels of image into memory. If this crashes, the machine probably needs more memory')

    hash_alg = sha256()
    for data in _to_bytes_generator(pil_image):
        hash_alg.update(data)
    return hash_alg.hexdigest()


def check_visually_identical(source_filepath, converted_filepath, source_pixel_checksum=None):
    """
    Visually compare the files (i.e. that the pixel values are identical)
    Raises ValidationError if they don't match
    Doesn't check technical metadata beyond colour profile and mode
    :param source_filepath:
    :param converted_filepath:
    :param source_pixel_checksum: if not None, uses this to compare against instead of reading out the
    source pixels again. Should be one generated using generate_pixel_checksum
    :return:
    """

    logger = logging.getLogger(__name__)
    logger.debug("Comparing pixel values and colour profile of {0} and {1}".format(source_filepath, converted_filepath))

    check_colour_profiles_match(source_filepath, converted_filepath)

    with Image.open(source_filepath) as source_image:
        if not source_pixel_checksum:
            source_pixel_checksum = generate_pixel_checksum_from_pil_image(source_image)
        source_is_bitonal = source_image.mode == BITONAL

    if source_is_bitonal:
        # we need to handle bitonal images differently, as they're converted into 8 bit greyscale.
        # No information is lost in the conversion, but the tobytes
        #  method used by the pixel checksum picks up the difference
        with Image.open(converted_filepath) as converted_image:
            bitonal_converted_image = converted_image.convert('1')
            converted_pixel_checksum = generate_pixel_checksum_from_pil_image(bitonal_converted_image)
    else:
        converted_pixel_checksum = generate_pixel_checksum(converted_filepath)

    if not converted_pixel_checksum == source_pixel_checksum:
        raise exceptions.ValidationError(
            'Converted file {0} does not visually match original {1}'
            .format(converted_filepath, source_filepath)
        )

    logger.debug('{0} and {1} are equivalent'.format(source_filepath, converted_filepath))


def check_colour_profiles_match(source_filepath, converted_filepath):
    """
    Check the icc profile and colour mode match.
    Allows greyscale and bitonal images to match, as that's how kakadu expands JP2s which were originally bitonal
    Raises ValidationError if they don't match
    :param source_filepath:
    :param converted_filepath:
    :return:
    """
    logger = logging.getLogger(__name__)

    with Image.open(source_filepath) as source_image:
        with Image.open(converted_filepath) as converted_image:
            if source_image.mode != converted_image.mode:
                if source_image.mode == BITONAL and converted_image.mode == GREYSCALE:
                    logger.info('Converted image is greyscale, not bitonal. This is expected')
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
                    .format(converted_filepath, source_filepath))


def check_image_suitable_for_jp2_conversion(image_filepath, require_icc_profile_for_greyscale=False,
                                            require_icc_profile_for_colour=True):
    """
    Check over the image and make sure it's in a supported and tested format for conversion to jp2
    Raises ValidationError if there are problems
    :param image_filepath:
    :param require_icc_profile_for_greyscale: raise an error if a greyscale image doesn't have an icc profile
    note: bitonal images don't need icc profiles even if this is true
    :param require_icc_profile_for_colour: raise an error if a colour image doesn't have an icc profile
    :return:
    """

    logger = logging.getLogger(__name__)
    with Image.open(image_filepath) as image_pil:

        colour_mode = image_pil.mode

        if colour_mode not in ACCEPTED_COLOUR_MODES:
            raise exceptions.ValidationError("Unsupported colour mode {0} for {1}".format(colour_mode, image_filepath))

        if colour_mode == 'RGBA':
            # In some cases alpha channel data is stored in a way that means it would be lost in the conversion back to
            # tiff from jp2.
            # "Kakadu Warning:
            # Alpha channel cannot be identified in a TIFF file since it is of the unassociated
            # (i.e., not premultiplied) type, and these are not supported by TIFF.
            # You can save this to a separate output file."

            # As we rarely encounter RGBA files, and mostly ones without any alpha channel data, we just warn here
            # the visually identical check should pick up any problems
            logger.warn("You must double check the jp2 conversion is lossless. "
                        "{0} is an RGBA image, and the resulting jp2 may convert back to an RGB tiff "
                        "if the alpha channel is unassociated".format(image_filepath))

        icc_needed = (require_icc_profile_for_greyscale and colour_mode == GREYSCALE) \
            or (require_icc_profile_for_colour and colour_mode not in MONOTONE_COLOUR_MODES)

        icc = image_pil.info.get('icc_profile')
        if icc is None:
            logger.warn('No icc profile embedded in {0}'.format(image_filepath))
            if icc_needed:
                raise exceptions.ValidationError('No icc profile embedded in {0}.'.format(image_filepath))

        frames = len(list(ImageSequence.Iterator(image_pil)))
        if frames > 1:
            logger.warn('File has multiple layers: only the first one will be converted')
