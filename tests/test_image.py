import filecmp
import os, sys, logging
import shutil
import pytest

from image_processing import image_converter, derivative_files_generator, validation, exceptions, image_magick
from .test_utils import temporary_folder, filepaths, assert_lines_match

KAKADU_BASE_PATH = '/opt/kakadu'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_image_converter():
    return image_converter.ImageConverter(kakadu_base_path=KAKADU_BASE_PATH)


def get_derivatives_generator():
    return derivative_files_generator.DerivativeFilesGenerator(kakadu_base_path=KAKADU_BASE_PATH)


class TestImageFormatConverter(object):
    def test_converts_jpg_to_tiff(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'test.jpg')
            tiff_file = os.path.join(output_folder,'test.tif')
            shutil.copy(filepaths.VALID_JPG, jpg_file)

            get_image_converter().convert_to_tiff(jpg_file, tiff_file)
            assert os.path.isfile(tiff_file)
            assert filecmp.cmp(tiff_file, filepaths.VALID_TIF)

    def test_converts_jpg_to_tiff_without_extension(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'testj')
            tiff_file = os.path.join(output_folder,'testt')
            shutil.copy(filepaths.VALID_JPG, jpg_file)

            get_image_converter().convert_to_tiff(jpg_file, tiff_file)
            assert os.path.isfile(tiff_file)
            assert filecmp.cmp(tiff_file, filepaths.VALID_TIF)

    def test_converts_jpg_to_jpeg2000(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'test.jpg')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.VALID_JPG, jpg_file)

            get_image_converter().convert_unsupported_file_to_jpeg2000(jpg_file, output_file)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.VALID_LOSSLESS_JP2)

    def test_converts_jpg_to_jpeg2000_with_awful_filename(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'te.s-t(1)_[2]')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.VALID_JPG, jpg_file)

            get_image_converter().convert_unsupported_file_to_jpeg2000(jpg_file, output_file)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.VALID_LOSSLESS_JP2)

    def test_converts_monochrome_jpg_to_jpeg2000(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'test.jpg')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.MONOCHROME_JPG, jpg_file)

            assert get_image_converter().is_monochrome(jpg_file)
            get_image_converter().convert_unsupported_file_to_jpeg2000(jpg_file, output_file)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.MONOCHROME_LOSSLESS_JP2)

    def test_converts_tif_to_jpeg2000(self):
        with temporary_folder() as output_folder:
            tif_file = os.path.join(output_folder,'test.tif')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.VALID_TIF, tif_file)

            get_image_converter().convert_colour_to_jpeg2000(tif_file, output_file)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.VALID_LOSSLESS_JP2)

    def test_converts_tif_to_lossy_jpeg2000(self):
        with temporary_folder() as output_folder:
            tif_file = os.path.join(output_folder,'test.tif')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.VALID_TIF, tif_file)

            get_image_converter().convert_colour_to_jpeg2000(tif_file, output_file, lossless=False)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.VALID_LOSSY_JP2)

    def test_kakadu_errors_are_raised(self):
        with temporary_folder() as output_folder:
            tif_file = os.path.join(output_folder,'test.tif')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.INVALID_TIF, tif_file)

            with pytest.raises(exceptions.KakaduError):
                get_image_converter().convert_colour_to_jpeg2000(tif_file, output_file)


class TestImageMagick(object):
    def test_mogrify_tif(self):
        with temporary_folder() as output_folder:
            file_to_mogrify = os.path.join(output_folder,'test.tif')
            shutil.copy(filepaths.VALID_JPG, file_to_mogrify)

            magick = image_magick.ImageMagick('/usr/bin')
            magick.mogrify(file_to_mogrify, initial_options=['-format', 'tif'])
            assert filecmp.cmp(file_to_mogrify, filepaths.VALID_TIF)


class TestImageValidation(object):
    def test_verifies_valid_jpeg2000(self):
        validation.validate_jp2(filepaths.VALID_LOSSLESS_JP2)

    def test_verifies_valid_lossy_jpeg2000(self):
        validation.validate_jp2(filepaths.VALID_LOSSY_JP2)

    def test_recognises_invalid_jpeg2000(self):
        with pytest.raises(exceptions.ValidationError):
            validation.validate_jp2(filepaths.INVALID_JP2)


class TestDerivativeGenerator(object):
    def test_creates_correct_files(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_jpg(filepaths.VALID_JPG, output_folder)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert filecmp.cmp(jpg_file, filepaths.VALID_JPG)
            assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)

    def test_creates_high_quality_jpg(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.VALID_TIF, output_folder,
                                                                       create_jpg_as_thumbnail=False)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert filecmp.cmp(jpg_file, filepaths.HIGH_QUALITY_JPG)
            assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)

    def test_creates_correct_files_from_tiff(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.VALID_TIF, output_folder)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert filecmp.cmp(jpg_file, filepaths.RESIZED_JPG)
            assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)

    def test_includes_tiff(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_tiff(filepaths.VALID_TIF, output_folder, include_tiff=True)
            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            tiff_file = os.path.join(output_folder,'full.tiff')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(tiff_file)
            assert len(os.listdir(output_folder)) == 3
            assert filecmp.cmp(tiff_file, filepaths.VALID_TIF)

    def test_handles_monochrome_jpg(self):
        with temporary_folder() as output_folder:

            assert get_image_converter().is_monochrome(filepaths.MONOCHROME_JPG)

            get_derivatives_generator().generate_derivatives_from_jpg(filepaths.MONOCHROME_JPG, output_folder)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert filecmp.cmp(jpg_file, filepaths.MONOCHROME_JPG)
            assert filecmp.cmp(jp2_file, filepaths.MONOCHROME_LOSSLESS_JP2)

    def test_does_not_generate_xmp(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_jpg(filepaths.VALID_JPG, output_folder, save_xmp=False)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert len(os.listdir(output_folder)) == 2
            assert not os.path.isfile(os.path.join(output_folder,'xmp.xml'))
            assert filecmp.cmp(jpg_file, filepaths.VALID_JPG)
            assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)

    def test_generates_xmp(self):
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_jpg(filepaths.VALID_JPG, output_folder, save_xmp=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')

            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)
            assert len(os.listdir(output_folder)) == 3

            assert filecmp.cmp(jpg_file, filepaths.VALID_JPG)
            assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)
            assert_lines_match(xmp_file, filepaths.VALID_XMP)

    def test_bad_image_metadata_input_with_strip(self):
        """"
        Tests that input images with invalid metadata can be valid once transformed. Transformed with metadata intact they create invalid jp2s
        """
        with temporary_folder() as output_folder:
            get_derivatives_generator().generate_derivatives_from_jpg(filepaths.BAD_METADATA_JPG, output_folder, strip_embedded_metadata=True)
            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
