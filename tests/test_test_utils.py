from .test_utils import filepaths, image_files_match, xmp_files_match


class TestTestUtils(object):

    def test_image_files_match_allows_different_exiftool_versions(self):
        assert image_files_match(filepaths.RESIZED_JPG_FROM_BILEVEL_TIF,
                                 filepaths.RESIZED_JPG_FROM_BILEVEL_TIF_DIFFERENT_EXIFTOOL)

    def test_image_files_match_allows_different_kakadu_versions(self):
        assert image_files_match(filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF,
                                 filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF_DIFFERENT_KAKADU)

    def test_image_files_match_fails_on_different_images(self):
        assert not image_files_match(filepaths.LOSSLESS_JP2_FROM_STANDARD_TIF,
                                     filepaths.LOSSLESS_JP2_FROM_STANDARD_JPG)
        assert not image_files_match(filepaths.SMALL_TIF, filepaths.SMALL_TIF_WITH_CHANGED_METADATA)
        assert not image_files_match(filepaths.SMALL_TIF, filepaths.SMALL_TIF_WITH_CHANGED_PIXELS)

    def test_xmp_files_match_allows_different_exiftool_versions(self):
        assert xmp_files_match(filepaths.STANDARD_TIF_XMP, filepaths.STANDARD_TIF_XMP_DIFFERENT_EXIFTOOL)

    def test_xmp_files_match_fails_on_different_xmp(self):
        assert not xmp_files_match(filepaths.STANDARD_TIF_XMP, filepaths.STANDARD_JPG_XMP)
