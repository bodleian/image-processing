import filecmp
import logging
import os
import shutil
import sys
import pytest
from image_processing import derivative_files_generator, validation, exceptions
from .test_utils import temporary_folder, filepaths, assert_lines_match

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_derivatives_generator():
    return derivative_files_generator.DerivativeFilesGenerator(kakadu_base_path=filepaths.KAKADU_BASE_PATH)


class TestDerivativeGenerator(object):

    def test_creates_high_quality_jpg(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF, output_folder,
                                                                       create_jpg_as_thumbnail=False,
                                                                       check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3
            assert filecmp.cmp(jpg_file, filepaths.HIGH_QUALITY_JPG_FROM_STANDARD_TIF)
            assert filecmp.cmp(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF)

    def test_creates_correct_files(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF, output_folder,
                                                                       check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3
            assert filecmp.cmp(jpg_file, filepaths.RESIZED_JPG_FROM_STANDARD_TIF)
            assert filecmp.cmp(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF)

    def test_creates_correct_files_with_awful_filename(self):
        with temporary_folder() as output_folder:
            awful_filepath = os.path.join(output_folder, 'te.s-t(1)_[2]a')
            shutil.copy(filepaths.STANDARD_TIF, awful_filepath)
            get_derivatives_generator().generate_derivatives_from_tiff(awful_filepath, output_folder,
                                                                       check_lossless=True)
            os.remove(awful_filepath)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3
            assert filecmp.cmp(jpg_file, filepaths.RESIZED_JPG_FROM_STANDARD_TIF)
            assert filecmp.cmp(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF)

    def test_includes_tiff(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF,
                                                                       output_folder, include_tiff=True,
                                                                       check_lossless=True)
            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            tiff_file = os.path.join(output_folder, 'full.tiff')
            xmp_file = os.path.join(output_folder, 'xmp.xml')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(tiff_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 4
            assert filecmp.cmp(tiff_file, filepaths.STANDARD_TIF)

    def test_creates_correct_files_greyscale_without_profile(self):
        with pytest.raises(exceptions.ValidationError):
            validation.check_image_suitable_for_jp2_conversion(filepaths.GREYSCALE_NO_PROFILE_TIF,
                                                               allow_no_icc_profile_for_greyscale=False)
        with temporary_folder() as output_folder:

            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.GREYSCALE_NO_PROFILE_TIF,
                                                                       output_folder, check_lossless=True,
                                                                       save_xmp=False)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert filecmp.cmp(jpg_file, filepaths.RESIZED_JPG_FROM_GREYSCALE_NO_PROFILE_TIF)
            assert filecmp.cmp(jp2_file, filepaths.LOSSLESS_JP2_FROM_GREYSCALE_NO_PROFILE_TIF)

    def test_creates_correct_files_greyscale(self):
        validation.check_image_suitable_for_jp2_conversion(filepaths.GREYSCALE_TIF,
                                                           allow_no_icc_profile_for_greyscale=False)
        with temporary_folder() as output_folder:

            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.GREYSCALE_TIF,
                                                                       output_folder, check_lossless=True,
                                                                       save_xmp=False)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert filecmp.cmp(jpg_file, filepaths.RESIZED_JPG_FROM_GREYSCALE_TIF)
            assert filecmp.cmp(jp2_file, filepaths.LOSSLESS_JP2_FROM_GREYSCALE_TIF)

    def test_creates_correct_files_bilevel_monochrome(self):
        with temporary_folder() as output_folder:

            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.BILEVEL_TIF,
                                                                       output_folder, check_lossless=True,
                                                                       save_xmp=False)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert filecmp.cmp(jpg_file, filepaths.RESIZED_JPG_FROM_BILEVEL_TIF)
            assert filecmp.cmp(jp2_file, filepaths.LOSSLESS_JP2_FROM_BILEVEL_TIF)

    def test_does_not_generate_xmp(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF, output_folder,
                                                                       save_xmp=False, check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert not os.path.isfile(os.path.join(output_folder, 'xmp.xml'))

    def test_generates_xmp(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF, output_folder,
                                                                       save_xmp=True, check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')

            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3

            assert filecmp.cmp(jpg_file, filepaths.RESIZED_JPG_FROM_STANDARD_TIF)
            assert filecmp.cmp(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF)
            assert_lines_match(xmp_file, filepaths.STANDARD_TIF_XMP)

    def test_fails_without_icc_profile(self):
        with temporary_folder() as output_folder:
            with pytest.raises(exceptions.ValidationError):
                get_derivatives_generator().generate_derivatives_from_tiff(filepaths.NO_PROFILE_TIF, output_folder,
                                                                           check_lossless=True)

    def test_allows_tif_without_icc_profile(self):
        with temporary_folder() as output_folder:
            d = derivative_files_generator.DerivativeFilesGenerator(
                kakadu_base_path=filepaths.KAKADU_BASE_PATH, allow_no_icc_profile=True)
            d.generate_derivatives_from_tiff(filepaths.NO_PROFILE_TIF, output_folder, check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')

            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3

    def test_creates_correct_files_from_jpg(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_jpg(filepaths.STANDARD_JPG, output_folder,
                                                                      check_lossless=True)
            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3
            assert filecmp.cmp(jpg_file, filepaths.STANDARD_JPG)
            assert filecmp.cmp(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_JPG)
            assert_lines_match(xmp_file, filepaths.STANDARD_JPG_XMP)
