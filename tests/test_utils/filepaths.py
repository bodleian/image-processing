

# adobe rgb 1998 8 bit tiff file (our most common input format) + expected derivatives
STANDARD_TIF = 'tests/data/standard_adobe.tif'
DEPTHMAP_TIF = 'tests/data/depth_map.tif'
NORMALMAP_TIF = 'tests/data/normal_map.tif'
STANDARD_TIF_SINGLE_LAYER = 'tests/data/standard_adobe_tif_single_layer.tif'  # same tif but without thumbnail
LOSSY_JP2_FROM_STANDARD_TIF = 'tests/data/standard_adobe_tif_lossy.jp2'
LOSSLESS_JP2_FROM_STANDARD_TIF_XMP = 'tests/data/standard_adobe_tif_xmp.jp2'
LOSSLESS_JP2_FROM_STANDARD_TIF = 'tests/data/standard_adobe_tif.jp2' # hasn't had xmp copied over using exiftool
RESIZED_JPG_FROM_STANDARD_TIF = 'tests/data/standard_adobe_tif_resized.jpg'
HIGH_QUALITY_JPG_FROM_STANDARD_TIF = 'tests/data/standard_adobe_tif_hq.jpg'
STANDARD_TIF_XMP = 'tests/data/standard_adobe_tif.xmp'


# Monochrome tifs

# tif with grayscale gamma 2.2 icc profile
GREYSCALE_TIF = 'tests/data/greyscale_gamma.tif'
RESIZED_JPG_FROM_GREYSCALE_TIF = 'tests/data/greyscale_gamma_tif_resized.jpg'
LOSSLESS_JP2_FROM_GREYSCALE_TIF_XMP = 'tests/data/greyscale_gamma_tif_xmp.jp2'

BILEVEL_TIF = 'tests/data/bilevel.tif'
LOSSLESS_JP2_FROM_BILEVEL_TIF_XMP = 'tests/data/bilevel_tif_xmp.jp2'
RESIZED_JPG_FROM_BILEVEL_TIF = 'tests/data/bilevel_tif_resized.jpg'

GREYSCALE_NO_PROFILE_TIF = 'tests/data/greyscale_without_profile.tif'
RESIZED_JPG_FROM_GREYSCALE_NO_PROFILE_TIF = 'tests/data/greyscale_without_profile_tif_resized.jpg'
LOSSLESS_JP2_FROM_GREYSCALE_NO_PROFILE_TIF_XMP = 'tests/data/greyscale_without_profile_tif_xmp.jp2'

# adobe rgb 1998 8 bit jpg file (converted from tif) + expected derivatives
STANDARD_JPG = 'tests/data/standard_adobe.jpg'
TIF_FROM_STANDARD_JPG = 'tests/data/standard_adobe_jpg.tif'
LOSSLESS_JP2_FROM_STANDARD_JPG_XMP = 'tests/data/standard_adobe_jpg_xmp.jp2'
STANDARD_JPG_XMP = 'tests/data/standard_adobe_jpg.xmp'

# misc tiffs
# for testing the pixel checksum
SMALL_TIF = 'tests/data/small.tif'
SMALL_TIF_WITH_CHANGED_PIXELS = 'tests/data/small_different_pixel.tif'
SMALL_TIF_WITH_CHANGED_METADATA = 'tests/data/small_different_metadata.tif'

TIF_16_BIT = 'tests/data/16_bit.tif'

# a jpg where the metadata was transferred over using a different version of exiftool and so won't match on filecmp.cmp
RESIZED_JPG_FROM_BILEVEL_TIF_DIFFERENT_EXIFTOOL = 'tests/data/bilevel_tif_resized_different_exiftool.jpg'
# xmp extracted using a different version of exiftool, which won't match on filecmp.cmp
STANDARD_TIF_XMP_DIFFERENT_EXIFTOOL = 'tests/data/standard_adobe_tif_different_exiftool.xmp'
# a jp2 created using a different version of kakadu, which won't match using filecmp.cmp
LOSSLESS_JP2_FROM_STANDARD_TIF_DIFFERENT_KAKADU = 'tests/data/standard_adobe_tif_kakadu_10.jp2'

NO_PROFILE_TIF = 'tests/data/no_profile.tif'

# just truncated files
INVALID_JP2 = 'tests/data/invalid.jp2'
INVALID_TIF = 'tests/data/invalid.tif'

KAKADU_BASE_PATH = '/opt/kakadu'
DEFAULT_IMAGE_MAGICK_PATH = '/usr/bin/'

SRGB_ICC_PROFILE = 'tests/data/sRGB_v4_ICC_preference.icc'
