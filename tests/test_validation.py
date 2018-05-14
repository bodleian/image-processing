from image_processing import validation, exceptions
from .test_utils import filepaths
import pytest
import logging
import sys
from PIL import Image


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class TestValidation(object):
    def test_verifies_valid_jpeg2000(self):
        validation.validate_jp2(filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF_XMP)

    def test_verifies_valid_lossy_jpeg2000(self):
        validation.validate_jp2(filepaths.LOSSY_JP2_FROM_STANDARD_TIF)

    def test_recognises_invalid_jpeg2000(self):
        with pytest.raises(exceptions.ValidationError):
            validation.validate_jp2(filepaths.INVALID_JP2)

    def test_pixel_checksum_matches_visually_identical_files(self):
        tif_checksum = validation.generate_pixel_checksum(filepaths.STANDARD_TIF)
        assert tif_checksum == validation.generate_pixel_checksum(filepaths.STANDARD_TIF)

        assert tif_checksum == validation.generate_pixel_checksum(filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF_XMP)

        assert validation.generate_pixel_checksum(filepaths.SMALL_TIF) == \
            validation.generate_pixel_checksum(filepaths.SMALL_TIF_WITH_CHANGED_METADATA)

    def test_pixel_checksum_doesnt_match_different_files(self):
        tif_checksum = validation.generate_pixel_checksum(filepaths.STANDARD_TIF)
        assert not tif_checksum == validation.generate_pixel_checksum(filepaths.TIF_FROM_STANDARD_JPG)

        assert not validation.generate_pixel_checksum(filepaths.SMALL_TIF) == \
            validation.generate_pixel_checksum(filepaths.SMALL_TIF_WITH_CHANGED_PIXELS)

    def test_to_bytes_generator(self):
        """
        Test the to_bytes_generator method gives same result as tobytes in the PIL library
        :return:
        """
        with Image.open(filepaths.SMALL_TIF) as pil_image:
            assert b"".join(list(validation._to_bytes_generator(pil_image))) == pil_image.tobytes()

    def test_pixel_checksum_stays_constant(self):
        SMALL_TIF_CHECKSUM = "a7cef053fa4b9ec518e44d465050b9f564adf4f6597d027c97acfaca6647262a"
        assert validation.generate_pixel_checksum(filepaths.SMALL_TIF) == SMALL_TIF_CHECKSUM
        with Image.open(filepaths.SMALL_TIF) as pil_image:
            assert validation.generate_pixel_checksum_from_pil_image(pil_image) == SMALL_TIF_CHECKSUM
