

# adobe rgb 1998 8 bit tiff file (our most common input format) + expected derivatives
INPUT_TIF = 'tests/data/standard_adobe_tif.tif'
INPUT_TIF_SINGLE_LAYER = 'tests/data/standard_adobe_tif_single_layer.tif'  # same tif but without thumbnail
LOSSY_JP2_FROM_INPUT_TIF = 'tests/data/standard_adobe_tif_lossy.jp2'
LOSSLESS_JP2_FROM_INPUT_TIF = 'tests/data/standard_adobe_tif.jp2'
RESIZED_JPG_FROM_INPUT_TIF = 'tests/data/standard_adobe_tif_resized.jpg'
HIGH_QUALITY_JPG_FROM_INPUT_TIF = 'tests/data/standard_adobe_tif_hq.jpg'

# adobe rgb 1998 8 bit jpg file + expected derivatives
INPUT_JPG = 'tests/data/adobe_jpg.jpg'
TIF_FROM_INPUT_JPG = 'tests/data/adobe_jpg.tif'
LOSSLESS_JP2_FROM_INPUT_JPG = 'tests/data/adobe_jpg.jp2'
LOSSLESS_JP2_FROM_INPUT_JPG_D = 'tests/data/adobe_jpg_d.jp2'


# should be VALID_JPG file transformed
# just a truncated jp2 file
INVALID_JP2 = 'tests/data/invalid.jp2'
# extracted from the JP2 version of VALID_JPG
VALID_XMP = 'tests/data/valid_xmp.xml'
# image with ill-formed metadata
BAD_METADATA_JPG = 'tests/data/bad_metadata.jpg'
INVALID_TIF = 'tests/data/invalid.tif'
MONOCHROME_JPG = 'tests/data/monochrome.jpg'
MONOCHROME_LOSSY_JP2 = 'tests/data/monochrome_lossy.jp2'
MONOCHROME_LOSSLESS_JP2 = 'tests/data/monochrome_lossless.jp2'


KAKADU_BASE_PATH = '/opt/kakadu'
DEFAULT_IMAGE_MAGICK_PATH = '/usr/bin/'

