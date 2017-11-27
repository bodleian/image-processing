from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from jpylyzer.jpylyzer import checkOneFile
from image_processing.exceptions import ValidationError
from PIL import Image
from numbers import Number


def validate_jp2(image_file):
    jp2_element = checkOneFile(image_file)
    success = jp2_element.findtext('isValidJP2') == 'True'
    if not success:
        raise ValidationError('{0} failed jypylzer validation: {1}'.format(image_file, jp2_element))


def compare_images_visually(image_file1, image_file2, adjust_for_monochrome=True):
    pixels1 = list(Image.open(image_file1).getdata())
    pixels2 = list(Image.open(image_file2).getdata())
    if adjust_for_monochrome:
        return _adjust_pixels_for_monochrome(pixels1) == _adjust_pixels_for_monochrome(pixels2)
    else:
        return pixels1 == pixels2


def _adjust_pixels_for_monochrome(pixels_list):
    if isinstance(pixels_list[0], Number):
        return [(a, a, a) for a in pixels_list]
    else:
        return pixels_list
