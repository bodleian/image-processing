import filecmp
import logging
import os
import shutil
import sys
import pytest
from pytest import mark

from image_processing import derivative_files_generator, validation, exceptions
from image_processing.utils import cmd_is_executable
from .test_utils import temporary_folder, filepaths, image_files_match, xmp_files_match

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_derivatives_generator():
    return derivative_files_generator.DerivativeFilesGenerator(kakadu_base_path=filepaths.KAKADU_BASE_PATH)


@mark.skipif(not cmd_is_executable('/opt/kakadu/kdu_compress'), reason="requires kakadu installed")
class TestDerivativeGenerator(object):

    def test_creates_high_quality_jpg(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF, output_folder,
                                                                       create_jpg_as_thumbnail=False,
                                                                       check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'full.xmp')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3
            assert image_files_match(jpg_file, filepaths.HIGH_QUALITY_JPG_FROM_STANDARD_TIF)
            assert image_files_match(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF_XMP)

    def test_creates_correct_files(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF, output_folder,
                                                                       check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'full.xmp')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3
            assert image_files_match(jpg_file, filepaths.RESIZED_JPG_FROM_STANDARD_TIF)
            assert image_files_match(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF_XMP)

    def test_creates_correct_files_without_default_names(self):
        with temporary_folder() as output_folder:
            orig_filepath = os.path.join(output_folder, 'test_tiff_filepath.tif')
            shutil.copy(filepaths.STANDARD_TIF, orig_filepath)
            d = derivative_files_generator.DerivativeFilesGenerator(kakadu_base_path=filepaths.KAKADU_BASE_PATH,
                                                                    use_default_filenames=False)
            d.generate_derivatives_from_tiff(orig_filepath, output_folder, check_lossless=True, include_tiff=True)

            os.remove(orig_filepath)

            jpg_file = os.path.join(output_folder, 'test_tiff_filepath.jpg')
            jp2_file = os.path.join(output_folder, 'test_tiff_filepath.jp2')
            xmp_file = os.path.join(output_folder, 'test_tiff_filepath.xmp')
            tif_file = os.path.join(output_folder, 'test_tiff_filepath.tiff')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert os.path.isfile(tif_file)
            assert len(os.listdir(output_folder)) == 4
            assert image_files_match(jpg_file, filepaths.RESIZED_JPG_FROM_STANDARD_TIF)
            assert image_files_match(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF_XMP)
            assert filecmp.cmp(tif_file, filepaths.STANDARD_TIF)
            assert xmp_files_match(xmp_file, filepaths.STANDARD_TIF_XMP)

    def test_creates_correct_files_with_awful_filename(self):
        with temporary_folder() as output_folder:
            awful_filepath = os.path.join(output_folder, 'te.s-t(1)_[2]a')
            shutil.copy(filepaths.STANDARD_TIF, awful_filepath)
            get_derivatives_generator().generate_derivatives_from_tiff(awful_filepath, output_folder,
                                                                       check_lossless=True)
            os.remove(awful_filepath)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'full.xmp')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3
            assert image_files_match(jpg_file, filepaths.RESIZED_JPG_FROM_STANDARD_TIF)
            assert image_files_match(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF_XMP)

    def test_includes_tiff(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF,
                                                                       output_folder, include_tiff=True,
                                                                       check_lossless=True)
            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            tiff_file = os.path.join(output_folder, 'full.tiff')
            xmp_file = os.path.join(output_folder, 'full.xmp')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(tiff_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 4
            assert filecmp.cmp(tiff_file, filepaths.STANDARD_TIF)

    def test_creates_correct_files_greyscale_without_profile(self):
        with pytest.raises(exceptions.ValidationError):
            validation.check_image_suitable_for_jp2_conversion(filepaths.GREYSCALE_NO_PROFILE_TIF,
                                                               require_icc_profile_for_greyscale=True)
        with temporary_folder() as output_folder:

            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.GREYSCALE_NO_PROFILE_TIF,
                                                                       output_folder, check_lossless=True,
                                                                       save_embedded_metadata=False)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert image_files_match(jpg_file, filepaths.RESIZED_JPG_FROM_GREYSCALE_NO_PROFILE_TIF)
            assert image_files_match(jp2_file, filepaths.LOSSLESS_JP2_FROM_GREYSCALE_NO_PROFILE_TIF_XMP)

    def test_creates_correct_files_greyscale(self):
        validation.check_image_suitable_for_jp2_conversion(filepaths.GREYSCALE_TIF,
                                                           require_icc_profile_for_greyscale=True)
        with temporary_folder() as output_folder:

            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.GREYSCALE_TIF,
                                                                       output_folder, check_lossless=True,
                                                                       save_embedded_metadata=False)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert image_files_match(jpg_file, filepaths.RESIZED_JPG_FROM_GREYSCALE_TIF)
            assert image_files_match(jp2_file, filepaths.LOSSLESS_JP2_FROM_GREYSCALE_TIF_XMP)

    def test_creates_correct_files_bilevel_monochrome(self):
        with temporary_folder() as output_folder:

            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.BILEVEL_TIF,
                                                                       output_folder, check_lossless=True,
                                                                       save_embedded_metadata=False)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert image_files_match(jpg_file, filepaths.RESIZED_JPG_FROM_BILEVEL_TIF)
            assert image_files_match(jp2_file, filepaths.LOSSLESS_JP2_FROM_BILEVEL_TIF_XMP)

    def test_does_not_generate_embedded_metadata_file(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF, output_folder,
                                                                       save_embedded_metadata=False,
                                                                       check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert not os.path.isfile(os.path.join(output_folder, 'full.xmp'))

    def test_generates_embedded_metadata_file(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF, output_folder,
                                                                       save_embedded_metadata=True, check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            embedded_metadata_file = os.path.join(output_folder, 'full.xmp')

            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(embedded_metadata_file)
            assert len(os.listdir(output_folder)) == 3

            assert image_files_match(jpg_file, filepaths.RESIZED_JPG_FROM_STANDARD_TIF)
            assert image_files_match(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF_XMP)
            assert xmp_files_match(embedded_metadata_file, filepaths.STANDARD_TIF_XMP)

    def test_fails_without_icc_profile(self):
        with temporary_folder() as output_folder:
            with pytest.raises(exceptions.ValidationError):
                get_derivatives_generator().generate_derivatives_from_tiff(filepaths.NO_PROFILE_TIF, output_folder,
                                                                           check_lossless=True)

    def test_allows_tif_without_icc_profile(self):
        with temporary_folder() as output_folder:
            d = derivative_files_generator.DerivativeFilesGenerator(
                kakadu_base_path=filepaths.KAKADU_BASE_PATH, require_icc_profile_for_colour=False)
            d.generate_derivatives_from_tiff(filepaths.NO_PROFILE_TIF, output_folder, check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            embedded_metadata_file = os.path.join(output_folder, 'full.xmp')

            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(embedded_metadata_file)
            assert len(os.listdir(output_folder)) == 3

    def test_creates_correct_files_from_jpg(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_jpg(filepaths.STANDARD_JPG, output_folder,
                                                                      check_lossless=True)
            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            embedded_metadata_file = os.path.join(output_folder, 'full.xmp')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(embedded_metadata_file)
            assert len(os.listdir(output_folder)) == 3
            assert image_files_match(jpg_file, filepaths.STANDARD_JPG)
            assert image_files_match(jp2_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_JPG_XMP)
            assert xmp_files_match(embedded_metadata_file, filepaths.STANDARD_JPG_XMP)
