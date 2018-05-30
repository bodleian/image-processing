from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


class ImageProcessingError(Exception):
    pass


class KakaduError(ImageProcessingError):
    pass


class KakaduUnrestrictedICCError(KakaduError):
    """
    Raised if the kdu_compress return code is 255 - usually implying a ICC profile that doesn't fit the JP2 retrictions
    """
    pass


class ValidationError(ImageProcessingError):
    pass
