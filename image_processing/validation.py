from jpylyzer.jpylyzer import checkOneFile
from image_processing.exceptions import ValidationError


def validate_jp2(image_file):
    jp2_element = checkOneFile(image_file)
    success = jp2_element.findtext('isValidJP2') == 'True'
    if not success:
        raise ValidationError('{0} failed jypylzer validation: {1}'.format(image_file, jp2_element))
