import io
import logging
import os
import sys
from image_processing import conversion, derivative_files_generator, validation, exceptions, kakadu
import pytest
from .test_utils import temporary_folder, filepaths, image_files_match
from PIL import Image, ImageCms

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_kakadu():
    return kakadu.Kakadu(kakadu_base_path=filepaths.KAKADU_BASE_PATH)


class TestImageFormatConverter(object):
    def test_converts_jpg_to_tiff(self):
        with temporary_folder() as output_folder:
            tiff_file = os.path.join(output_folder, 'test.tif')
            conversion.Converter().convert_to_tiff(filepaths.STANDARD_JPG, tiff_file)
            assert os.path.isfile(tiff_file)
            assert image_files_match(tiff_file, filepaths.TIF_FROM_STANDARD_JPG)

    def test_converts_tif_to_jpeg2000(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.jp2')
            get_kakadu().kdu_compress(filepaths.STANDARD_TIF, output_file,
                                      kakadu_options=kakadu.DEFAULT_COMPRESS_OPTIONS + kakadu.LOSSLESS_OPTIONS)
            assert os.path.isfile(output_file)
            assert image_files_match(output_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF)

    def test_converts_tif_to_jpeg(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.jpg')
            conversion.Converter().convert_to_jpg(filepaths.STANDARD_TIF, output_file, resize=None,
                                                  quality=derivative_files_generator.DEFAULT_JPG_HIGH_QUALITY_VALUE)
            assert os.path.isfile(output_file)
            assert image_files_match(output_file, filepaths.HIGH_QUALITY_JPG_FROM_STANDARD_TIF)

    def test_converts_tif_to_lossy_jpeg2000(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.jp2')
            get_kakadu().kdu_compress(filepaths.STANDARD_TIF, output_file,
                                      kakadu_options=kakadu.DEFAULT_COMPRESS_OPTIONS + kakadu.LOSSY_OPTIONS)
            assert os.path.isfile(output_file)
            validation.validate_jp2(output_file)
            # lossy conversions to jp2 don't seem to produce deterministic results, even if we only look at the pixels
            # validation.check_visually_identical(output_file, filepaths.LOSSY_JP2_FROM_STANDARD_TIF)

    def test_kakadu_errors_are_raised(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.jp2')
            with pytest.raises(exceptions.KakaduError):
                get_kakadu().kdu_compress(filepaths.INVALID_TIF, output_file,
                                          kakadu_options=kakadu.DEFAULT_COMPRESS_OPTIONS + kakadu.LOSSLESS_OPTIONS)

    def test_icc_conversion(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.tif')
            conversion.Converter().convert_icc_profile(filepaths.STANDARD_TIF, output_file, filepaths.SRGB_ICC_PROFILE)
            assert os.path.isfile(output_file)

            with Image.open(filepaths.STANDARD_TIF) as input_pil:
                old_icc = input_pil.info.get('icc_profile')
                f = io.BytesIO(old_icc)
                prf = ImageCms.ImageCmsProfile(f)
                assert prf.profile.profile_description == "Adobe RGB (1998)"

            with Image.open(output_file) as output_pil:
                new_icc = output_pil.info.get('icc_profile')
                f = io.BytesIO(new_icc)
                prf = ImageCms.ImageCmsProfile(f)
                assert prf.profile.profile_description == "sRGB v4 ICC preference perceptual intent beta"

    def test_icc_conversion_catches_16_bit_errors(self):
        with temporary_folder() as output_folder:
            output_file = os.path.join(output_folder, 'output.tif')

            with pytest.raises(exceptions.ImageProcessingError):
                conversion.Converter().convert_icc_profile(filepaths.TIF_16_BIT, output_file, filepaths.SRGB_ICC_PROFILE)

            assert not os.path.isfile(output_file)
