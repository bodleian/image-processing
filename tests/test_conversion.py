import filecmp
import logging
import os
import sys
from image_processing import conversion, derivative_files_generator, validation, exceptions, kakadu
import pytest
from .test_utils import temporary_folder, filepaths

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_kakadu():
    return kakadu.Kakadu(kakadu_base_path=filepaths.KAKADU_BASE_PATH)


class TestImageFormatConverter(object):
    def test_converts_jpg_to_tiff_pil(self):
        with temporary_folder() as output_folder:
            tiff_file = os.path.join(output_folder, 'test.tif')
            conversion.convert_to_tiff(filepaths.STANDARD_JPG, tiff_file)
            assert os.path.isfile(tiff_file)
            assert filecmp.cmp(tiff_file, filepaths.TIF_FROM_STANDARD_JPG)

    def test_converts_tif_to_jpeg2000(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.jp2')
            get_kakadu().kdu_compress(filepaths.STANDARD_TIF, output_file,
                                      kakadu_options=kakadu.DEFAULT_OPTIONS + kakadu.LOSSLESS_OPTIONS)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF)

    def test_converts_tif_to_jpeg(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.jpg')
            conversion.convert_to_jpg(filepaths.STANDARD_TIF, output_file, resize=None,
                                      quality=derivative_files_generator.DEFAULT_JPG_HIGH_QUALITY_VALUE)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.HIGH_QUALITY_JPG_FROM_STANDARD_TIF)

    def test_converts_tif_to_lossy_jpeg2000(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.jp2')
            get_kakadu().kdu_compress(filepaths.STANDARD_TIF, output_file,
                                      kakadu_options=kakadu.DEFAULT_OPTIONS + kakadu.LOSSY_OPTIONS)
            assert os.path.isfile(output_file)
            validation.validate_jp2(output_file)
            # lossy conversions to jp2 don't seem to produce deterministic results, even if we only look at the pixels
            # validation.check_visually_identical(output_file, filepaths.LOSSY_JP2_FROM_STANDARD_TIF)

    def test_kakadu_errors_are_raised(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.jp2')
            with pytest.raises(exceptions.KakaduError):
                get_kakadu().kdu_compress(filepaths.INVALID_TIF, output_file,
                                          kakadu_options=kakadu.DEFAULT_OPTIONS + kakadu.LOSSLESS_OPTIONS)
