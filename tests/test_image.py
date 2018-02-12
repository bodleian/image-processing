import filecmp
import os, sys, logging
import shutil
import pytest

from image_processing import image_converter, derivative_files_generator, validation, exceptions, image_magick
from .test_utils import temporary_folder, filepaths, assert_lines_match

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_image_converter():
    return image_converter.ImageConverter(kakadu_base_path=filepaths.KAKADU_BASE_PATH,
                                          image_magick_path=filepaths.DEFAULT_IMAGE_MAGICK_PATH)


def get_derivatives_generator():
    return derivative_files_generator.DerivativeFilesGenerator(kakadu_base_path=filepaths.KAKADU_BASE_PATH,
                                                               image_magick_path=filepaths.DEFAULT_IMAGE_MAGICK_PATH)


class TestImageFormatConverter(object):
    def test_converts_jpg_to_tiff(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder, 'test.jpg')
            tiff_file = os.path.join(output_folder, 'test.tif')
            shutil.copy(filepaths.STANDARD_JPG, jpg_file)

            get_image_converter().convert_to_tiff(jpg_file, tiff_file)
            assert os.path.isfile(tiff_file)
            assert filecmp.cmp(tiff_file, filepaths.TIF_FROM_STANDARD_JPG)

    def test_converts_jpg_to_jpeg2000(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'test.jpg')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.STANDARD_JPG, jpg_file)

            get_image_converter().convert_unsupported_file_to_jpeg2000(jpg_file, output_file)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_JPG)

    def test_converts_jpg_to_jpeg2000_with_awful_filename(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder, 'te.s-t(1)_[2]s')
            output_file = os.path.join(output_folder, 'output.jp2')
            shutil.copy(filepaths.STANDARD_JPG, jpg_file)

            get_image_converter().convert_unsupported_file_to_jpeg2000(jpg_file, output_file)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_JPG)

#todo: monochrome isn't supported yet
    # def test_converts_monochrome_jpg_to_jpeg2000(self):
    #     with temporary_folder() as output_folder:
    #         jpg_file = os.path.join(output_folder, 'test.jpg')
    #         output_file = os.path.join(output_folder, 'output.jp2')
    #         shutil.copy(filepaths.MONOCHROME_JPG, jpg_file)
    #
    #         assert get_image_converter().is_monochrome(jpg_file)
    #         get_image_converter().convert_unsupported_file_to_jpeg2000(jpg_file, output_file)
    #         assert os.path.isfile(output_file)
    #         assert filecmp.cmp(output_file, filepaths.MONOCHROME_LOSSLESS_JP2)

    def test_converts_tif_to_jpeg2000(self):
        with temporary_folder() as output_folder:
            tif_file = os.path.join(output_folder,'test.tif')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.STANDARD_TIF, tif_file)

            get_image_converter().convert_colour_to_jpeg2000(tif_file, output_file)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF)

    def test_converts_tif_to_lossy_jpeg2000(self):
        with temporary_folder() as output_folder:
            tif_file = os.path.join(output_folder,'test.tif')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.STANDARD_TIF, tif_file)

            get_image_converter().convert_colour_to_jpeg2000(tif_file, output_file, lossless=False)
            assert os.path.isfile(output_file)
            validation.validate_jp2(output_file)
            #lossy conversions to jp2 don't seem to produce deterministic results, even if we only look at the pixels
            #validation.check_visually_identical(output_file, filepaths.LOSSY_JP2_FROM_STANDARD_TIF)

    def test_kakadu_errors_are_raised(self):
        with temporary_folder() as output_folder:
            tif_file = os.path.join(output_folder,'test.tif')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.INVALID_TIF, tif_file)

            with pytest.raises(exceptions.KakaduError):
                get_image_converter().convert_colour_to_jpeg2000(tif_file, output_file)


class TestImageValidation(object):
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

    #todo: once we have monochrome enabled
    # def test_monochrome_to_rgb_pixel_checksums(self):
    #     pass


class TestJpegInput(object):

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


class TestDerivativeGeneratorTiff(object):

    def test_creates_high_quality_jpg(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.STANDARD_TIF, output_folder,
                                                                       create_jpg_as_thumbnail=False,
                                                                       check_lossless=True)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
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

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
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

    # todo: bilevel conversion doesn't work yet
    # def test_creates_correct_files_bilevel_monochrome(self):
    #     with temporary_folder() as output_folder:
    #
    #         get_derivatives_generator().generate_derivatives_from_tiff(filepaths.BILEVEL_TIF,
    #                                                                    output_folder, check_lossless=True,
    #                                                                    save_xmp=False)
    #
    #         jpg_file = os.path.join(output_folder, 'full.jpg')
    #         jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
    #         assert os.path.isfile(jpg_file)
    #         assert os.path.isfile(jp2_file)
    #         assert len(os.listdir(output_folder)) == 2
    #         assert filecmp.cmp(jpg_file, filepaths.RESIZED_JPG_FROM_GREYSCALE_NO_PROFILE_TIF)
    #         assert filecmp.cmp(jp2_file, filepaths.LOSSLESS_JP2_FROM_GREYSCALE_NO_PROFILE_TIF)

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
            d = derivative_files_generator.DerivativeFilesGenerator(kakadu_base_path=filepaths.KAKADU_BASE_PATH,
                                                                image_magick_path=filepaths.DEFAULT_IMAGE_MAGICK_PATH,
                                                                    allow_no_icc_profile=True)
            d.generate_derivatives_from_tiff(filepaths.NO_PROFILE_TIF, output_folder, check_lossless=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')

            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3
