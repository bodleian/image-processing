import filecmp
import os
import shutil

from image_processing import format_converter, transform, validation
from test_utils import filepaths
from test_utils.filepaths import temporary_folder


class ImageFormatConverterTest:
    def converts_jpg_to_tiff_test(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'test.jpg')
            tiff_file = os.path.join(output_folder,'test.tif')
            shutil.copy(filepaths.VALID_JPG, jpg_file)

            format_converter.convert_to_tiff(jpg_file, tiff_file)
            assert os.path.isfile(tiff_file)


    def converts_jpg_to_tiff_image_magick_test(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'test.jpg')
            tiff_file = os.path.join(output_folder,'test.tif')
            shutil.copy(filepaths.VALID_JPG, jpg_file)

            format_converter.convert_to_tiff_with_library_choice(jpg_file, tiff_file, use_graphics_magick=False)
            assert os.path.isfile(tiff_file)


    # def converts_jpg_to_tiff_graphics_magick_test(self):
    #     with temporary_folder() as output_folder:
    #         jpg_file = os.path.join(output_folder,'test.jpg')
    #         tiff_file = os.path.join(output_folder,'test.tif')
    #         shutil.copy(filepaths.VALID_JPG, jpg_file)
    #
    #         format_converter.convert_to_tiff_with_library_choice(jpg_file, tiff_file, use_graphics_magick=True)
    #         assert os.path.isfile(tiff_file)


    def converts_jpg_to_jpeg2000_test(self):
        with temporary_folder() as output_folder:
            jpg_file = os.path.join(output_folder,'test.jpg')
            output_file = os.path.join(output_folder,'output.jp2')
            shutil.copy(filepaths.VALID_JPG, jpg_file)

            format_converter.convert_unsupported_file_to_jpeg2000(jpg_file, output_file)
            assert os.path.isfile(output_file)
            #assert filecmp.cmp(output_file, filepaths.VALID_LOSSLESS_JP2)


class ImageValidationTest:
    def verifies_valid_jpeg2000_test(self):
        assert validation.verify_jp2(filepaths.VALID_LOSSLESS_JP2)

    def verifies_valid_lossy_jpeg2000_test(self):
        assert validation.verify_jp2(filepaths.VALID_LOSSY_JP2)

    def recognises_invalid_jpeg2000_test(self):
        assert not validation.verify_jp2(filepaths.INVALID_JP2)


class ImageTransformTest:
    def creates_correct_files_test(self):
        with temporary_folder() as output_folder:
            transform.transform_jpg_to_ingest_format(filepaths.VALID_JPG, output_folder)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            jp2_lossy_file = os.path.join(output_folder,'full_lossy.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(jp2_lossy_file)
            assert filecmp.cmp(jpg_file, filepaths.VALID_JPG)
            #assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)
            #assert filecmp.cmp(jp2_lossy_file, filepaths.VALID_LOSSY_JP2)


    def does_not_generate_xmp_test(self):
        with temporary_folder() as output_folder:
            transform.transform_jpg_to_ingest_format(filepaths.VALID_JPG, output_folder, exempi_app=None)

            jpg_file = os.path.join(output_folder,'full.jpg')
            jp2_file = os.path.join(output_folder,'full_lossless.jp2')
            jp2_lossy_file = os.path.join(output_folder,'full_lossy.jp2')
            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(jp2_lossy_file)
            assert not os.path.isfile(os.path.join(output_folder,'xmp.xml'))
            assert filecmp.cmp(jpg_file, filepaths.VALID_JPG)
            #assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)

    def generates_xmp_test(self):
        with temporary_folder() as output_folder:
            transform.transform_jpg_to_ingest_format(filepaths.VALID_JPG, output_folder, exempi_app=filepaths.EXEMPI_FILE)

            jpg_file = os.path.join(output_folder, 'full.jpg')
            jp2_file = os.path.join(output_folder, 'full_lossless.jp2')
            xmp_file = os.path.join(output_folder, 'xmp.xml')

            assert os.path.isfile(jpg_file)
            assert os.path.isfile(jp2_file)
            assert os.path.isfile(xmp_file)

            assert filecmp.cmp(jpg_file, filepaths.VALID_JPG)
            #assert filecmp.cmp(jp2_file, filepaths.VALID_LOSSLESS_JP2)
            assert filecmp.cmp(xmp_file, filepaths.VALID_XMP)

    def bad_image_metadata_input_test(self):
        """"
        Tests that input images with invalid metadata can be valid once transformed. Transformed with metadata intact they create invalid jp2s
        """
        with temporary_folder() as output_folder:
            transform.transform_jpg_to_ingest_format(filepaths.BAD_METADATA_JPG, output_folder, strip_embedded_metadata=True)
