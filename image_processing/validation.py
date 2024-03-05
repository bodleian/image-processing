from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from jpylyzer.jpylyzer import checkOneFile
from xml.etree import ElementTree
from xml.dom import minidom
from PIL import Image, ImageSequence
from image_processing import exceptions
import logging
from hashlib import sha256


GREYSCALE = 'L'
BITONAL = '1'
MONOTONE_COLOUR_MODES = [GREYSCALE, BITONAL]
ACCEPTED_COLOUR_MODES = ['RGB', 'RGBA', 'RGBX', 'I;16', GREYSCALE, BITONAL]


def validate_jp2(image_file, output_file=None):
    """
    Uses jpylyzer (:func:`jpylyzer.jpylzer.checkOneFile`) to validate the jp2 file.
    Raises a :class:`~image_processing.exceptions.ValidationError` if it is invalid

    :param image_file:
    :param output_file: if not None, write the jpylyzer xml output to this file
    :type image_file: str
    """
    logger = logging.getLogger(__name__)
    jp2_element = checkOneFile(image_file)
    is_valid_element = jp2_element.find('isValid')
    # elements are falsey if they have no children, so we explicitly check `is None`
    if is_valid_element is None:
        # isValid is only in post-2.0.0 jyplyzer output. legacy output has isValidJP2 instead
        is_valid_element = jp2_element.find('isValidJP2')
    success = is_valid_element is not None and is_valid_element.text == 'True'
    output_string = minidom.parseString(ElementTree.tostring(jp2_element)).toprettyxml(encoding='utf-8')
    if output_file:
        with open(output_file, 'wb') as f:
            f.write(output_string)
    if not success:
        logger.error('{0} failed jypylzer validation'.format(image_file))
        raise exceptions.ValidationError('{0} failed jypylzer validation'.format(image_file))
    logger.debug('{0} is a valid jp2 file'.format(image_file))


def _to_bytes_generator(pil_image, min_buffer_size=65536):
    """
    An iterator version of the :func:`PIL.Image.tobytes` method
    .. note:: The PIL implementation stores the data in a separate array, doubling the memory usage.
    This is implemented as a generator to be a more efficient way of processing the data.

    :param pil_image: :class:`PIL.Image` instance
    :param min_buffer_size:
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
    Generate a format-independent checksum based on the image's pixel values.

    :param image_filepath:
    """
    with Image.open(image_filepath) as pil_image:
        return generate_pixel_checksum_from_pil_image(pil_image)


def generate_pixel_checksum_from_pil_image(pil_image):
    """
    Generate a format-independent checksum based on this image's pixel values

    :param pil_image: :class:`PIL.Image` instance
    """
    logger = logging.getLogger(__name__)
    logger.debug('Loading pixels of image into memory. If this crashes, the machine probably needs more memory')

    hash_alg = sha256()
    for data in _to_bytes_generator(pil_image):
        hash_alg.update(data)
    return hash_alg.hexdigest()


def check_visually_identical(source_filepath, converted_filepath, source_pixel_checksum=None):
    """
    Visually compare the files (i.e. that the pixel values are identical).
    Raises a :class:`~image_processing.exceptions.ValidationError` if they don't match.

    .. note:: Does not check technical metadata beyond colour profile and mode.

    :param source_filepath:
    :param converted_filepath:
    :param source_pixel_checksum: if not None, uses this to compare against instead of reading out the
        source pixels again. Should be one generated using generate_pixel_checksum
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
    Check the ICC profile and colour mode match.
    Allows greyscale and bitonal images to match, as that is how kakadu expands JP2s which were originally bitonal.
    Raises :class:`~image_processing.exceptions.ValidationError` if they do not match.

    :param source_filepath:
    :param converted_filepath:
    """
    logger = logging.getLogger(__name__)

    with Image.open(source_filepath) as source_image:
        with Image.open(converted_filepath) as converted_image:
            if source_image.mode != converted_image.mode:
                if source_image.mode == BITONAL and converted_image.mode == GREYSCALE:
                    logger.info('Converted image is greyscale, not bitonal. This is expected')
                elif source_image.mode == 'RGBX' and converted_image.mode == 'RGBA':
                    logger.info('Converted image in RGBA space, but was converted from RGBX. This is expected.')
                else:
                    raise exceptions.ValidationError(
                        f'Converted file {converted_filepath} has different colour mode ({converted_image.mode}) from {source_filepath} ({source_image.mode})'
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
    Check over the image and checks if it is in a supported and tested format for conversion to jp2.
    Raises :class:`~image_processing.exceptions.ValidationError` if it is not

    :param image_filepath:
    :param require_icc_profile_for_greyscale: raise an error if a greyscale image doesn't have an icc profile.
        Note: bitonal images don't need icc profiles even if this is true
    :param require_icc_profile_for_colour: raise an error if a colour image doesn't have an icc profile
    """

    logger = logging.getLogger(__name__)
    with Image.open(image_filepath) as image_pil:

        colour_mode = image_pil.mode

        if colour_mode not in ACCEPTED_COLOUR_MODES:
            raise exceptions.ValidationError("Unsupported colour mode {0} for {1}".format(colour_mode, image_filepath))

        if colour_mode == 'RGBX':
            logger.warning("{0} is RGBX and will convert to a RGBA jp2, preserving the pixel information but losing the colour mode".format(image_filepath))

        if colour_mode in ['RGBA', 'RGBX']:
            # In some cases alpha channel data is stored in a way that means it would be lost in the conversion back to
            # tiff from jp2.
            # "Kakadu Warning:
            # Alpha channel cannot be identified in a TIFF file since it is of the unassociated
            # (i.e., not premultiplied) type, and these are not supported by TIFF.
            # You can save this to a separate output file."

            # As we rarely encounter RGBA files, and mostly ones without any alpha channel data, we just warn here
            # the visually identical check should pick up any problems
            logger.warning("You must check the jp2 conversion is lossless. "
                            "{0} will convert to a RGBA jp2, and may convert back to an RGB tiff "
                            "if the alpha channel is unassociated."
                           "The usual visually identical check will detect this if run".format(image_filepath))

        icc_needed = (require_icc_profile_for_greyscale and colour_mode == GREYSCALE) \
            or (require_icc_profile_for_colour and colour_mode not in MONOTONE_COLOUR_MODES)

        icc = image_pil.info.get('icc_profile')
        if icc is None:
            logger.warning('No icc profile embedded in {0}'.format(image_filepath))
            if icc_needed:
                raise exceptions.ValidationError('No icc profile embedded in {0}.'.format(image_filepath))

        frames = len(list(ImageSequence.Iterator(image_pil)))
        if frames > 1:
            logger.warning('File has multiple layers: only the first one will be converted')
