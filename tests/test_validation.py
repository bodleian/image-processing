from image_processing import validation, exceptions
from .test_utils import filepaths
import pytest
import logging
import sys


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class TestValidation(object):
    def test_verifies_valid_jpeg2000(self):
        validation.validate_jp2(filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF)

    def test_verifies_valid_lossy_jpeg2000(self):
        validation.validate_jp2(filepaths.LOSSY_JP2_FROM_STANDARD_TIF)

    def test_recognises_invalid_jpeg2000(self):
        with pytest.raises(exceptions.ValidationError):
            validation.validate_jp2(filepaths.INVALID_JP2)

    def test_pixel_checksum_matches_visually_identical_files(self):
        tif_checksum = validation.generate_pixel_checksum(filepaths.STANDARD_TIF)
        assert tif_checksum == validation.generate_pixel_checksum(filepaths.STANDARD_TIF)

        assert tif_checksum == validation.generate_pixel_checksum(filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF)

        assert validation.generate_pixel_checksum(filepaths.SMALL_TIF) == \
            validation.generate_pixel_checksum(filepaths.SMALL_TIF_WITH_CHANGED_METADATA)

    def test_pixel_checksum_doesnt_match_different_files(self):
        tif_checksum = validation.generate_pixel_checksum(filepaths.STANDARD_TIF)
        assert not tif_checksum == validation.generate_pixel_checksum(filepaths.TIF_FROM_STANDARD_JPG)

        assert not validation.generate_pixel_checksum(filepaths.SMALL_TIF) == \
            validation.generate_pixel_checksum(filepaths.SMALL_TIF_WITH_CHANGED_PIXELS)
