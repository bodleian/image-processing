import filecmp
import os
import shutil
import pytest

from image_processing import format_converter, transform, validation, exceptions
from .test_utils import temporary_folder, filepaths, assert_lines_match

KAKADU_BASE_PATH = '/opt/kakadu'


def get_image_converter():
    return format_converter.FormatConverter(kakadu_base_path=KAKADU_BASE_PATH)


def get_transform():
    return transform.Transform(kakadu_base_path=KAKADU_BASE_PATH)


class TestImageFormatConverter:
    def test_converts_jpg_to_tiff(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'test.jpg')
            tiff_file = os.path.join(output_folder,'test.tif')
            shutil.copy(filepaths.VALID_JPG, jpg_file)

            get_image_converter().convert_to_tiff(jpg_file, tiff_file)
            assert os.path.isfile(tiff_file)

    def test_converts_jpg_to_tiff_image_magick(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'test.jpg')
            tiff_file = os.path.join(output_folder,'test.tif')
            shutil.copy(filepaths.VALID_JPG, jpg_file)

            get_image_converter().convert_to_tiff(jpg_file, tiff_file)
            assert os.path.isfile(tiff_file)

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


    def test_converts_tif_to_jpeg2000(self):
        with temporary_folder() as output_folder:
            tif_file = os.path.join(output_folder,'test.tif')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.VALID_TIF, tif_file)

            get_image_converter().convert_colour_to_jpeg2000(tif_file, output_file)
            assert os.path.isfile(output_file)
            assert filecmp.cmp(output_file, filepaths.VALID_LOSSLESS_JP2)

    def test_kakadu_errors_are_raised(self):
        with temporary_folder() as output_folder:
            tif_file = os.path.join(output_folder,'test.tif')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.INVALID_TIF, tif_file)

            with pytest.raises(exceptions.KakaduError):
                get_image_converter().convert_colour_to_jpeg2000(tif_file, output_file)

class TestImageValidation:
    def test_verifies_valid_jpeg2000(self):
        validation.validate_jp2(filepaths.VALID_LOSSLESS_JP2)

    def test_verifies_valid_lossy_jpeg2000(self):
        validation.validate_jp2(filepaths.VALID_LOSSY_JP2)

    def test_recognises_invalid_jpeg2000(self):
        with pytest.raises(exceptions.ValidationError):
            validation.validate_jp2(filepaths.INVALID_JP2)


class TestImageTransform:
    def test_creates_correct_files(self):
        with temporary_folder() as output_folder:
            get_transform().generate_derivatives_from_jpg(filepaths.VALID_JPG, output_folder)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            jp2_lossy_file = os.path.join(output_folder,'full_lossy.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(jp2_lossy_file)
            assert filecmp.cmp(jpg_file, filepaths.VALID_JPG)
            assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)
            assert filecmp.cmp(jp2_lossy_file, filepaths.VALID_LOSSY_JP2)

    def test_creates_correct_files_from_tiff(self):
        with temporary_folder() as output_folder:
            get_transform().generate_derivatives_from_tiff(filepaths.VALID_TIF, output_folder)

            jpg_file = os.path.join(output_folder,'full.jpg')
            tiff_file = os.path.join(output_folder,'full.tiff')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            jp2_lossy_file = os.path.join(output_folder,'full_lossy.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(tiff_file)
            assert os.path.isfile(jp2_lossy_file)
            #assert filecmp.cmp(jpg_file, filepaths.VALID_JPG) #todo: get appropriate test image
            assert filecmp.cmp(tiff_file, filepaths.VALID_TIF)
            assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)
            assert filecmp.cmp(jp2_lossy_file, filepaths.VALID_LOSSY_JP2)

    def test_handles_monochrome_jpg(self):
        with temporary_folder() as output_folder:

            assert get_image_converter().is_monochrome(filepaths.MONOCHROME_JPG)

            get_transform().generate_derivatives_from_jpg(filepaths.MONOCHROME_JPG, output_folder)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            jp2_lossy_file = os.path.join(output_folder,'full_lossy.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(jp2_lossy_file)
            assert filecmp.cmp(jpg_file, filepaths.MONOCHROME_JPG)
            assert filecmp.cmp(jp2_file, filepaths.MONOCHROME_LOSSLESS_JP2)
            assert filecmp.cmp(jp2_lossy_file, filepaths.MONOCHROME_LOSSY_JP2)

    def test_does_not_generate_xmp(self):
        with temporary_folder() as output_folder:
            get_transform().generate_derivatives_from_jpg(filepaths.VALID_JPG, output_folder, save_xmp=False)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            jp2_lossy_file = os.path.join(output_folder,'full_lossy.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(jp2_lossy_file)
            assert not os.path.isfile(os.path.join(output_folder,'xmp.xml'))
            assert filecmp.cmp(jpg_file, filepaths.VALID_JPG)
            assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)

    def test_generates_xmp(self):
        with temporary_folder() as output_folder:
            get_transform().generate_derivatives_from_jpg(filepaths.VALID_JPG, output_folder, save_xmp=True)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')

            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)

            assert filecmp.cmp(jpg_file, filepaths.VALID_JPG)
            assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)
            assert_lines_match(xmp_file, filepaths.VALID_XMP)

    def test_bad_image_metadata_input_with_strip(self):
        """"
        Tests that input images with invalid metadata can be valid once transformed. Transformed with metadata intact they create invalid jp2s
        """
        with temporary_folder() as output_folder:
            get_transform().generate_derivatives_from_jpg(filepaths.BAD_METADATA_JPG, output_folder, strip_embedded_metadata=True)
            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
